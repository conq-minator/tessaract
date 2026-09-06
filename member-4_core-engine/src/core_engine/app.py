"""
Core Engine Application Orchestrator.
Glues together the WebSocket event server, REST API, alert stream,
session builder, episode grouper, stuck detector, event store, and AI client.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time

from aiohttp import web

from .ai_client import AIClient
from .alert_stream import AlertStreamManager
from .config import CoreConfig
from .episode_grouper import EpisodeGrouper
from .event_server import EventServer
from .event_store import EventStore
from .intent_classifier import IntentClassifier
from .models import ContextState, Episode, TesseractEvent, utc_now_iso
from .normalizer import EventNormalizer
from .rest_api import RestApiHandler
from .session_builder import SessionBuilder
from .stuck_detector import StuckDetector

logger = logging.getLogger("tesseract.core_engine.app")


class CoreEngineApp:
    def __init__(self, config: CoreConfig, mock_ai: bool = False):
        self.config = config
        self.mock_ai = mock_ai

        # 1. Persistence & Clients
        self.event_store = EventStore(config.db_path)
        self.ai_client = AIClient(base_url=config.ai_base_url, mock_mode=mock_ai)

        # 2. Engines & Classifiers
        self.normalizer = EventNormalizer(dedup_window_ms=config.dedup_window_ms)
        self.intent_classifier = IntentClassifier(ai_client=self.ai_client)
        self.session_builder = SessionBuilder(
            event_store=self.event_store,
            idle_timeout_s=config.session_idle_timeout_s,
        )
        self.stuck_detector = StuckDetector(config=config)
        self.episode_grouper = EpisodeGrouper(
            event_store=self.event_store,
            stuck_detector=self.stuck_detector,
            gap_timeout_s=config.episode_gap_timeout_s,
            on_episode_completed=self._on_episode_completed,
        )

        # 3. Alert Streaming & Web Handlers
        self.alert_stream = AlertStreamManager()
        self.event_server = EventServer(
            config=config,
            normalizer=self.normalizer,
            process_event_callback=self.process_event,
        )
        self.rest_api = RestApiHandler(
            event_store=self.event_store,
            session_builder=self.session_builder,
            stuck_detector=self.stuck_detector,
            normalizer=self.normalizer,
            get_current_context=self.get_current_context,
            process_event_callback=self.process_event,
        )

        # Current context tracking
        self._current_topic: str = "general"
        self._current_subtopic: str = ""
        self._current_concepts: list[str] = []
        self._current_intent: str = "working"
        self._active_tools: set[str] = set()
        self._last_alert_time: dict[str, float] = {}

        # Background tasks
        self._background_tasks: list[asyncio.Task] = []
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None

    def get_current_context(self) -> ContextState:
        """Construct current real-time user context."""
        friction = self.stuck_detector.compute_friction_score(self._current_topic)
        active_session = self.session_builder.current_session
        active_episode = self.episode_grouper.active_episode

        display_topic = (
            f"{self._current_topic.capitalize()} ({self._current_subtopic})"
            if self._current_subtopic
            else self._current_topic
        )

        return ContextState(
            topic=display_topic,
            intent=self._current_intent,
            active_tools=list(self._active_tools),
            friction_level=friction.level,
            active_session_id=active_session.session_id if active_session else None,
            active_episode_id=active_episode.episode_id if active_episode else None,
            updated_at=utc_now_iso(),
        )

    async def process_event(self, event: TesseractEvent) -> None:
        """
        Main pipeline processing for a normalized incoming event:
        0. Video/Media Privacy Gate: Topic extraction & study-only filtering
        1. Persist raw event to SQLite
        2. Update session
        3. Classify intent
        4. Update active tools & topic
        5. Update friction scorer & check for stuck detection
        6. Correlate with learning episode
        7. Broadcast alerts if thresholds or context changes occur
        """
        # 0. Video & Media Privacy Gate
        if event.source == "browser" and (
            "youtube" in event.event_type.lower()
            or "youtube.com" in str(event.payload.get("url", "")).lower()
            or "youtu.be" in str(event.payload.get("url", "")).lower()
        ):
            title = event.payload.get("title") or event.payload.get("video_title", "")
            channel = event.payload.get("channel", "")
            description = event.payload.get("description", "")

            # Query AI Layer for topic extraction & study relevance
            analysis = await self.ai_client.classify_video(
                title=title, channel=channel, description=description
            )
            is_study = analysis.get("is_study_related", False)
            extracted_topic = analysis.get("topic", title)
            domain = analysis.get("domain", "general")

            if not is_study:
                logger.info(
                    "Non-study video event discarded: '%s' (Extracted Topic: %s)",
                    title,
                    extracted_topic,
                )
                return  # Privacy gate: Discard event, do not store or process

            # Enrich event payload with extracted study topic
            event.payload["extracted_topic"] = extracted_topic
            event.payload["domain"] = domain
            event.payload["is_study_related"] = True
            logger.info(
                "Observed study video: '%s' -> Topic: '%s' (%s)",
                title,
                extracted_topic,
                domain,
            )

        # 1. Persist (only allowed/study events reach here)
        self.event_store.insert_event(event)

        # 2. Session update
        session = self.session_builder.process_event(event)

        # 3. Intent Classification (rule-based)
        old_intent = self._current_intent
        old_topic = self._current_topic
        intent, confidence, rationale = self.intent_classifier.classify_event(event)
        self._current_intent = intent

        # 4. Extract Topic and fine-grained concepts from code and payload
        import re
        from .concept_extractor import extract_code_concepts

        event_file = event.payload.get("file_path") or ""
        cmd_str = event.payload.get("command") or ""
        snippet = event.payload.get("code_snippet") or ""


        # Extract file path from command line if not present
        if not event_file and cmd_str:
            matches = re.findall(r'([^\r\n]+\.(?:py|c|h|cpp|js|ts|java))', cmd_str)
            if matches:
                for cand in matches:
                    cand = cand.strip().strip('"\'')
                    if os.path.exists(cand) or any(cand.endswith(ext) for ext in ('.py', '.js', '.c', '.ts')):
                        event_file = cand
                        break

        extracted = extract_code_concepts(file_path=event_file, code=snippet)
        domain = extracted["domain"]
        primary_topic = extracted["primary_topic"]
        detected_concepts = extracted["concepts"]

        self._current_topic = domain
        self._current_subtopic = primary_topic
        self._current_concepts = detected_concepts

        # Asynchronously update Knowledge Graph in Member 5 immediately with detected concepts!
        if detected_concepts:
            exit_code = event.payload.get("exit_code", 0)
            asyncio.create_task(self.ai_client.update_knowledge_graph({
                "domain": domain,
                "topic": primary_topic,
                "concepts": detected_concepts,
                "file_path": event_file,
                "outcome": "success" if exit_code == 0 else "friction",
                "confidence_delta": 0.12 if exit_code == 0 else -0.15,
            }))

        self._active_tools.add(event.source)

        # 5. Stuck Detection & Friction Scoring
        friction_score = self.stuck_detector.update_with_event(event, topic=self._current_topic)
        self.event_store.record_friction_score(self._current_topic, friction_score)

        # Only trigger friction alerts when an actual execution/run with errors occurred
        is_error_run = False
        if event.event_type in ("command_executed", "terminal_command", "test_failed", "runtime_error", "execution_failed"):
            exit_code = event.payload.get("exit_code")
            if exit_code is not None and exit_code != 0:
                is_error_run = True
            elif event.payload.get("error_message") or event.payload.get("stderr"):
                is_error_run = True
        elif event.event_type in ("error_detected", "syntax_error", "build_failed", "diagnostic_error"):
            is_error_run = True
        elif event.event_type == "code_edited" and event.payload.get("had_error"):
            is_error_run = True

        now_ts = time.time()
        last_alert = self._last_alert_time.get(self._current_topic, 0.0)
        cooldown_s = 2.0

        if is_error_run and (now_ts - last_alert >= cooldown_s):
            self._last_alert_time[self._current_topic] = now_ts
            logger.warning(
                "Execution error detected for topic '%s'! Event: %s, Exit Code: %s",
                self._current_topic,
                event.event_type,
                event.payload.get("exit_code"),
            )
            err_msg = event.payload.get("error_message") or event.payload.get("command") or ""
            err_line = event.payload.get("error_line", "")
            err_file = event.payload.get("file_path", "")
            code_snippet = event.payload.get("code_snippet", "")

            if not code_snippet and err_file:
                candidate_paths = [err_file, os.path.join(os.getcwd(), err_file)]
                for p in candidate_paths:
                    if os.path.exists(p) and os.path.isfile(p):
                        try:
                            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                                all_lines = f.readlines()
                                if str(err_line).isdigit() and int(err_line) > 0:
                                    ln = int(err_line)
                                    s = max(0, ln - 4)
                                    e = min(len(all_lines), ln + 3)
                                    code_snippet = "".join(all_lines[s:e])
                                else:
                                    code_snippet = "".join(all_lines[:25])
                            break
                        except Exception:
                            pass

            run_id = f"run_{event.event_id}"
            await self.alert_stream.broadcast(
                alert_type="stuck_detected",
                payload={
                    "run_id": run_id,
                    "friction_score": friction_score.score,
                    "level": friction_score.level,
                    "topic": self._current_topic,
                    "signals": friction_score.signals,
                    "error_message": err_msg,
                    "error_line": err_line,
                    "file_path": err_file,
                    "code_snippet": code_snippet,
                    "episode_id": (
                        self.episode_grouper.active_episode.episode_id
                        if self.episode_grouper.active_episode
                        else None
                    ),
                },
            )

        # 6. Episode Grouping
        self.episode_grouper.process_event(
            event=event,
            session_id=session.session_id,
            inferred_intent=intent,
            inferred_topic=self._current_topic,
        )

        # 7. Context Changed Alert
        if old_intent != self._current_intent or old_topic != self._current_topic:
            await self.alert_stream.broadcast(
                alert_type="context_changed",
                payload={
                    "old_context": {"topic": old_topic, "intent": old_intent},
                    "new_context": {"topic": self._current_topic, "intent": self._current_intent},
                },
            )

    def _on_episode_completed(self, episode: Episode) -> None:
        """Callback invoked when an episode completes."""
        asyncio.create_task(self._handle_episode_completion(episode))

    async def _handle_episode_completion(self, episode: Episode) -> None:
        # Request summary from AI Layer or mock
        summary = await self.ai_client.summarize_episode(episode.to_dict())

        # Update Knowledge Graph via Member 5 AI service
        await self.ai_client.update_knowledge_graph(
            {
                "topic": episode.topic,
                "outcome": episode.outcome,
                "events_count": episode.events_count,
                "signals": episode.signals,
                "friction_score": episode.friction_score,
            }
        )

        # Broadcast completion alert to UI
        await self.alert_stream.broadcast(
            alert_type="episode_completed",
            payload={
                "episode_id": episode.episode_id,
                "topic": episode.topic,
                "outcome": episode.outcome,
                "summary": summary,
            },
        )

        # Reset friction for resolved topics
        if episode.outcome == "resolved":
            self.stuck_detector.reset_topic(episode.topic)

    async def _friction_decay_loop(self) -> None:
        """Periodic background task to apply friction decay."""
        while True:
            try:
                await asyncio.sleep(60)  # Decay tick every 60 seconds
                if self._current_topic:
                    self.stuck_detector.decay_friction(self._current_topic)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in friction decay loop: %s", e)

    async def _retention_purge_loop(self) -> None:
        """Periodic background task to auto-purge expired database entries."""
        while True:
            try:
                await asyncio.sleep(3600 * 6)  # Run every 6 hours
                self.event_store.purge_expired_data(
                    raw_retention_days=self.config.raw_event_retention_days
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in retention purge loop: %s", e)

    def create_web_application(self) -> web.Application:
        """Build and configure aiohttp web Application with routes."""
        app = web.Application()

        # Inbound sensor WebSocket: ws://localhost:9700/events
        app.router.add_get("/events", self.event_server.handle_ws_events)
        app.router.add_get("/ws/events", self.event_server.handle_ws_events)

        # Outbound UI alert WebSocket: ws://localhost:9700/alerts
        app.router.add_get("/alerts", self.alert_stream.handle_ws_alerts)
        app.router.add_get("/ws/alerts", self.alert_stream.handle_ws_alerts)

        # Outbound REST API: http://localhost:9700/api/v1/...
        self.rest_api.register_routes(app)

        return app

    async def start(self) -> None:
        """Start the Core Engine server and background tasks."""
        self._app = self.create_web_application()
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()

        site = web.TCPSite(self._runner, self.config.host, self.config.port)
        await site.start()

        # Launch background maintenance tasks
        self._background_tasks.append(asyncio.create_task(self._friction_decay_loop()))
        self._background_tasks.append(asyncio.create_task(self._retention_purge_loop()))

        logger.info("==================================================")
        logger.info("  Tesseract Core Engine running on port %d", self.config.port)
        logger.info("  Sensor WebSocket: ws://%s:%d/events", self.config.host, self.config.port)
        logger.info("  UI Alert Stream : ws://%s:%d/alerts", self.config.host, self.config.port)
        logger.info("  REST API Base   : http://%s:%d/api/v1", self.config.host, self.config.port)
        logger.info("  Mock AI Mode    : %s", self.mock_ai)
        logger.info("==================================================")

    async def stop(self) -> None:
        """Gracefully stop all services, web sockets, and tasks."""
        logger.info("Stopping Core Engine...")
        for task in self._background_tasks:
            task.cancel()

        await self.event_server.close_all()
        await self.alert_stream.close_all()
        await self.ai_client.close()

        if self._runner:
            await self._runner.cleanup()
        logger.info("Core Engine stopped.")
