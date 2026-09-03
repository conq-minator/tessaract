"""
Session Builder for Tesseract Core Engine.
Groups stream of events into active user sessions based on activity boundaries
and idle timeout heuristics.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from .event_store import EventStore
from .models import Session, TesseractEvent, utc_now_iso

logger = logging.getLogger("tesseract.core_engine.session_builder")


class SessionBuilder:
    def __init__(self, event_store: EventStore, idle_timeout_s: int = 300):
        self.event_store = event_store
        self.idle_timeout_s = idle_timeout_s
        self.current_session: Session | None = None
        self._last_activity_time: datetime | None = None

        # Load active session from database if exists
        self._load_active_session()

    def _load_active_session(self) -> None:
        active_dict = self.event_store.get_active_session()
        if active_dict:
            self.current_session = Session.from_dict(active_dict)
            try:
                # Parse start/end time
                self._last_activity_time = datetime.fromisoformat(
                    self.current_session.end_time or self.current_session.start_time
                )
            except Exception:
                self._last_activity_time = datetime.now(UTC)

    def process_event(self, event: TesseractEvent) -> Session:
        """
        Process an incoming event, associating it with the current session
        or starting a new session if idle timeout expired.
        """
        try:
            event_dt = datetime.fromisoformat(event.timestamp)
        except Exception:
            event_dt = datetime.now(UTC)

        # Check if we should create a new session
        if (
            self.current_session is None
            or not self.current_session.is_active
            or (
                self._last_activity_time
                and (event_dt - self._last_activity_time).total_seconds() > self.idle_timeout_s
            )
        ):
            # Close previous session if open
            if self.current_session and self.current_session.is_active:
                self.close_current_session(
                    end_time=(
                        self._last_activity_time.isoformat()
                        if self._last_activity_time
                        else utc_now_iso()
                    )
                )

            # Start new session
            self.current_session = Session(
                start_time=event.timestamp,
                is_active=True,
                events_count=0,
                sources=[],
                topics=[],
            )
            logger.info("Started new session: %s", self.current_session.session_id)

        # Update session properties
        self.current_session.events_count += 1
        if event.source not in self.current_session.sources:
            self.current_session.sources.append(event.source)

        # Extract topics from event payload
        self._extract_and_add_topics(event)

        # Set session_id on event metadata
        event.metadata.session_id = self.current_session.session_id

        self._last_activity_time = event_dt
        self.current_session.end_time = event.timestamp

        # Persist session update
        self.event_store.insert_or_update_session(self.current_session)
        return self.current_session

    def _extract_and_add_topics(self, event: TesseractEvent) -> None:
        """Extract candidate topic keywords from event payload."""
        assert self.current_session is not None
        payload = event.payload

        candidates: list[str] = []
        if "topic" in payload and isinstance(payload["topic"], str):
            candidates.append(payload["topic"])
        if "file_path" in payload and isinstance(payload["file_path"], str):
            # e.g., main.c -> c-programming, test_pointers.c -> pointers
            fp = payload["file_path"].lower()
            if fp.endswith((".c", ".h", ".cpp")):
                if "pointer" in fp:
                    candidates.append("pointers")
                else:
                    candidates.append("c-programming")
            elif fp.endswith(".py"):
                candidates.append("python")
            elif fp.endswith((".js", ".ts")):
                candidates.append("javascript")
            if "tree" in fp or "list" in fp:
                candidates.append("data-structures")

        if "query" in payload and isinstance(payload["query"], str):
            q = payload["query"].lower()
            for kw in [
                "pointer",
                "segfault",
                "recursion",
                "array",
                "memory",
                "struct",
                "linked list",
                "c ",
            ]:
                if kw in q:
                    candidates.append(kw.strip().replace(" ", "-"))

        for c in candidates:
            c_clean = c.strip().lower()
            if c_clean and c_clean not in self.current_session.topics:
                self.current_session.topics.append(c_clean)

    def close_current_session(self, end_time: str | None = None) -> Session | None:
        """Explicitly close the current active session."""
        if not self.current_session or not self.current_session.is_active:
            return self.current_session

        self.current_session.is_active = False
        self.current_session.end_time = end_time or utc_now_iso()
        self.event_store.insert_or_update_session(self.current_session)
        logger.info("Closed session %s", self.current_session.session_id)
        closed = self.current_session
        self.current_session = None
        self._last_activity_time = None
        return closed
