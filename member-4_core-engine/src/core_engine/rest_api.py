"""
REST API Router for Tesseract Core Engine.
Provides endpoints on http://localhost:9700/api/v1 for downstream consumers (Member 6 — Tutor/UI).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from aiohttp import web

from .event_store import EventStore
from .models import ContextState, TesseractEvent, utc_now_iso
from .normalizer import EventNormalizer
from .session_builder import SessionBuilder
from .stuck_detector import StuckDetector

logger = logging.getLogger("tesseract.core_engine.rest_api")


class RestApiHandler:
    def __init__(
        self,
        event_store: EventStore,
        session_builder: SessionBuilder,
        stuck_detector: StuckDetector,
        normalizer: EventNormalizer,
        get_current_context: Callable[[], ContextState],
        process_event_callback: Callable[[TesseractEvent], Any],
    ):
        self.event_store = event_store
        self.session_builder = session_builder
        self.stuck_detector = stuck_detector
        self.normalizer = normalizer
        self.get_current_context = get_current_context
        self.process_event_callback = process_event_callback

    def register_routes(self, app: web.Application) -> None:
        """Register all REST API endpoints."""
        app.router.add_get("/api/v1/health", self.handle_health)
        app.router.add_get("/api/v1/events/recent", self.handle_get_recent_events)
        app.router.add_post("/api/v1/events", self.handle_post_event)
        app.router.add_get("/api/v1/sessions/active", self.handle_get_active_session)
        app.router.add_get("/api/v1/sessions/{id}", self.handle_get_session_by_id)
        app.router.add_get("/api/v1/episodes/recent", self.handle_get_recent_episodes)
        app.router.add_get("/api/v1/friction/current", self.handle_get_current_friction)
        app.router.add_get("/api/v1/context/current", self.handle_get_current_context)
        app.router.add_get("/api/v1/analytics/summary", self.handle_get_analytics_summary)
        app.router.add_delete("/api/v1/data/all", self.handle_delete_all_data)
        app.router.add_get("/api/v1/browser/activity", self.handle_get_browser_activity)


    async def handle_health(self, request: web.Request) -> web.Response:
        return web.json_response(
            {
                "status": "healthy",
                "service": "tesseract-core-engine",
                "timestamp": utc_now_iso(),
            }
        )

    async def handle_get_recent_events(self, request: web.Request) -> web.Response:
        try:
            limit = int(request.query.get("limit", 50))
        except ValueError:
            limit = 50

        source = request.query.get("source")
        event_type = request.query.get("event_type")
        since_iso = request.query.get("since")

        events = self.event_store.get_recent_events(
            limit=limit, source=source, event_type=event_type, since_iso=since_iso
        )
        return web.json_response({"events": events, "count": len(events)})

    async def handle_post_event(self, request: web.Request) -> web.Response:
        """Allow HTTP ingestion of a TesseractEvent."""
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON body"}, status=400)

        normalized = self.normalizer.normalize(data)
        if not normalized:
            return web.json_response(
                {"status": "filtered", "reason": "deduplicated or rate-limited"}, status=200
            )

        try:
            await self.process_event_callback(normalized)
        except Exception as e:
            logger.error("Error processing POST event: %s", e)
            return web.json_response({"error": str(e)}, status=500)

        return web.json_response(
            {"status": "accepted", "event_id": normalized.event_id}, status=201
        )

    async def handle_get_active_session(self, request: web.Request) -> web.Response:
        active = self.event_store.get_active_session()
        if not active:
            return web.json_response(
                {"active_session": None, "message": "No active session"}, status=200
            )
        return web.json_response({"active_session": active})

    async def handle_get_session_by_id(self, request: web.Request) -> web.Response:
        session_id = request.match_info["id"]
        session = self.event_store.get_session(session_id)
        if not session:
            return web.json_response({"error": "Session not found"}, status=404)
        return web.json_response({"session": session})

    async def handle_get_recent_episodes(self, request: web.Request) -> web.Response:
        try:
            limit = int(request.query.get("limit", 10))
        except ValueError:
            limit = 10

        episodes = self.event_store.get_recent_episodes(limit=limit)
        return web.json_response({"episodes": episodes, "count": len(episodes)})

    async def handle_get_current_friction(self, request: web.Request) -> web.Response:
        topic = request.query.get("topic")
        if not topic:
            context = self.get_current_context()
            topic = context.topic or "general"

        friction = self.stuck_detector.compute_friction_score(topic)
        return web.json_response(friction.to_dict())

    async def handle_get_current_context(self, request: web.Request) -> web.Response:
        context = self.get_current_context()
        return web.json_response(context.to_dict())

    async def handle_get_analytics_summary(self, request: web.Request) -> web.Response:
        summary = self.event_store.get_analytics_summary()
        return web.json_response(summary)

    async def handle_delete_all_data(self, request: web.Request) -> web.Response:
        """DELETE /api/v1/data/all — Wipe all stored events, episodes, sessions."""
        try:
            self.event_store.clear_all_data()
            return web.json_response({"status": "success", "message": "All core engine data wiped"})
        except Exception as e:
            logger.error("Error clearing all data: %s", e)
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def handle_get_browser_activity(self, request: web.Request) -> web.Response:
        """GET /api/v1/browser/activity — Summarize browser sensor telemetry."""
        try:
            summary = self.event_store.get_browser_activity_summary()
            return web.json_response({"status": "success", "data": summary})
        except Exception as e:
            logger.error("Error fetching browser activity: %s", e)
            return web.json_response({"status": "error", "message": str(e)}, status=500)

