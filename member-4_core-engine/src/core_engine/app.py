"""
Core Engine Application Orchestrator.
Glues together the WebSocket event server, REST API, alert stream,
session builder, episode grouper, stuck detector, event store, and AI client.
"""

from __future__ import annotations

import asyncio
import logging
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

        return ContextState(
            topic=self._current_topic,
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
        1. Persist raw event to SQLite
        2. Update session
        3. Classify intent
        4. Update active tools & topic
        5. Update friction scorer & check for stuck detection
        6. Correlate with learning episode
        7. Broadcast alerts if thresholds or context changes occur
        """
        # 1. Persist
        self.event_store.insert_event(event)

        # 2. Session update
        session = self.session_builder.process_event(event)

        # 3. Intent Classification (rule-based)
        old_intent = self._current_intent
        old_topic = self._current_topic
        intent, confidence, rationale = self.intent_classifier.classify_event(event)
        self._current_intent = intent

        # 4. Extract Topic from current event payload
        event_topic = None
        if event.payload.get("topic"):
            event_topic = str(event.payload["topic"]).lower()
        elif event.payload.get("language"):
            lang = str(event.payload["language"]).lower()
            if lang in ("python", "javascript", "typescript", "c", "cpp", "java", "rust"):
                event_topic = lang
        elif "command" in event.payload:
            cmd = str(event.payload["command"]).lower()
            if "python" in cmd or ".py" in cmd:
                event_topic = "python"
            elif "node" in cmd or ".js" in cmd or ".ts" in cmd:
                event_topic = "javascript"
            elif any(c_kw in cmd for c_kw in ["gcc", "clang", "g++", ".c ", ".cpp"]):
                event_topic = "pointers" if "pointer" in cmd else "c-programming"

        if not event_topic and "file_path" in event.payload:
            fp = str(event.payload["file_path"]).lower()
            if fp.endswith(".py"):
                event_topic = "python"
            elif fp.endswith((".c", ".h", ".cpp")):
                event_topic = "pointers" if "pointer" in fp else "c-programming"
            elif fp.endswith((".js", ".ts")):
                event_topic = "javascript"

        if event_topic:
            self._current_topic = event_topic
        elif not self._current_topic or self._current_topic == "general":
            if session.topics:
                self._current_topic = session.topics[-1]
        self._active_tools.add(event.source)

        # 5. Stuck Detection & Friction Scoring
        friction_score = self.stuck_detector.update_with_event(event, topic=self._current_topic)
        self.event_store.record_friction_score(self._current_topic, friction_score)

        # Check for Friction Alert (Medium or High) with 60s cooldown per topic
        now_ts = time.time()
        last_alert = self._last_alert_time.get(self._current_topic, 0.0)
        cooldown_s = 60.0

        if (friction_score.score >= self.config.friction_threshold_medium or friction_score.level in ("medium", "high")) and (now_ts - last_alert >= cooldown_s):
            self._last_alert_time[self._current_topic] = now_ts
            logger.warning(
                "Friction threshold reached for topic '%s'! Level: %s, Score: %.2f",
                self._current_topic,
                friction_score.level,
                friction_score.score,
            )
            # Generate AI pedagogical hint tailored to exact runtime error and code snippet
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

            context_str = f"Language: {self._current_topic}\nFile: {err_file}:{err_line}\nError: {err_msg}"
            if code_snippet:
                context_str += f"\nCode Context:\n```\n{code_snippet.strip()}\n```"

            hint_text = await self.ai_client.generate_hint(
                topic=self._current_topic,
                context_str=context_str
            )
            await self.alert_stream.broadcast(
                alert_type="stuck_detected",
                payload={
                    "friction_score": friction_score.score,
                    "level": friction_score.level,
                    "topic": self._current_topic,
                    "hint": hint_text,
                    "signals": friction_score.signals,
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
