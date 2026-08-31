"""
Episode Grouper for Tesseract Core Engine.
Correlates events across tools and sessions into coherent learning and debugging episodes.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from .event_store import EventStore
from .models import Episode, EpisodeOutcome, IntentType, TesseractEvent, utc_now_iso
from .stuck_detector import StuckDetector

logger = logging.getLogger("tesseract.core_engine.episode_grouper")


class EpisodeGrouper:
    def __init__(
        self,
        event_store: EventStore,
        stuck_detector: StuckDetector,
        gap_timeout_s: int = 1800,
        on_episode_completed: Callable[[Episode], Any] | None = None,
    ):
        self.event_store = event_store
        self.stuck_detector = stuck_detector
        self.gap_timeout_s = gap_timeout_s
        self.on_episode_completed = on_episode_completed

        # Active episode cache
        self.active_episode: Episode | None = None
        self._last_event_time: datetime | None = None

    def process_event(
        self,
        event: TesseractEvent,
        session_id: str | None = None,
        inferred_intent: IntentType = "learning",
        inferred_topic: str = "general",
    ) -> Episode:
        """
        Correlate an event into the current learning episode or initiate a new one.
        """
        try:
            event_dt = datetime.fromisoformat(event.timestamp)
        except Exception:
            event_dt = datetime.now(UTC)

        # Check if active episode should be closed due to inactivity or topic divergence
        should_start_new = False
        if self.active_episode is None:
            should_start_new = True
        elif (
            self._last_event_time
            and (event_dt - self._last_event_time).total_seconds() > self.gap_timeout_s
        ):
            # Inactivity timeout -> mark previous as abandoned
            self._complete_active_episode(outcome="abandoned")
            should_start_new = True
        elif (
            inferred_topic != "general"
            and self.active_episode.topic != "general"
            and inferred_topic != self.active_episode.topic
        ):
            # Topic shifted significantly
            self._complete_active_episode(outcome="ongoing")
            should_start_new = True

        if should_start_new:
            self.active_episode = Episode(
                session_ids=[session_id] if session_id else [],
                start_time=event.timestamp,
                topic=inferred_topic,
                intent=inferred_intent,
                outcome="ongoing",
                events_count=0,
            )
            logger.info(
                "Started new episode: %s for topic: %s",
                self.active_episode.episode_id,
                inferred_topic,
            )

        assert self.active_episode is not None

        if session_id and session_id not in self.active_episode.session_ids:
            self.active_episode.session_ids.append(session_id)

        self.active_episode.events_count += 1
        if inferred_topic != "general" and self.active_episode.topic == "general":
            self.active_episode.topic = inferred_topic

        # Update episode behavioral signals
        payload = event.payload
        source = event.source
        event_type = event.event_type.lower()

        if (
            "error" in event_type
            or payload.get("exit_code", 0) not in (0, None)
            or payload.get("error_message")
        ):
            self.active_episode.signals["error_count"] += 1
        elif (
            payload.get("exit_code") == 0
            and ("run" in event_type or "build" in event_type)
            and self.active_episode.signals.get("error_count", 0) > 0
        ):
            # Execution success!
            # Was debugging/troubleshooting and now succeeded
            self.active_episode.signals["execution_attempts"] += 1
            self._last_event_time = event_dt
            self.active_episode.end_time = event.timestamp
            friction = self.stuck_detector.compute_friction_score(self.active_episode.topic)
            self.active_episode.friction_score = friction.score
            self.event_store.insert_or_update_episode(self.active_episode)
            return self._complete_active_episode(outcome="resolved")

        if source == "vscode" and any(
            k in event_type for k in ["run", "execute", "build", "terminal_command"]
        ):
            self.active_episode.signals["execution_attempts"] += 1

        if source == "browser" and ("search" in event_type or "query" in payload):
            self.active_episode.signals["search_count"] += 1

        if source == "browser" and (
            "youtube" in event_type or "youtube.com" in str(payload.get("url", ""))
        ):
            self.active_episode.signals["tutorials_opened"] += 1

        # Friction computation for this episode
        friction = self.stuck_detector.compute_friction_score(self.active_episode.topic)
        self.active_episode.friction_score = friction.score
        self.active_episode.end_time = event.timestamp

        self._last_event_time = event_dt
        self.event_store.insert_or_update_episode(self.active_episode)
        return self.active_episode

    def _complete_active_episode(self, outcome: EpisodeOutcome) -> Episode:
        """Mark the active episode as finished."""
        assert self.active_episode is not None
        self.active_episode.outcome = outcome
        self.active_episode.end_time = self.active_episode.end_time or utc_now_iso()
        self.event_store.insert_or_update_episode(self.active_episode)
        logger.info("Completed episode %s with outcome=%s", self.active_episode.episode_id, outcome)

        completed = self.active_episode
        if self.on_episode_completed:
            try:
                self.on_episode_completed(completed)
            except Exception as e:
                logger.error("Error in on_episode_completed callback: %s", e)

        self.active_episode = None
        self._last_event_time = None
        return completed
