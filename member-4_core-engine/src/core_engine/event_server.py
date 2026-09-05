"""
Inbound WebSocket Event Server for Tesseract Core Engine.
Accepts connections from sensors (Members 1, 2, 3) on ws://localhost:9700/events,
authenticates via shared secret, normalizes payloads, and triggers processing.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from aiohttp import WSMsgType, web

from .config import CoreConfig
from .models import TesseractEvent, utc_now_iso
from .normalizer import EventNormalizer

logger = logging.getLogger("tesseract.core_engine.event_server")


class EventServer:
    def __init__(
        self,
        config: CoreConfig,
        normalizer: EventNormalizer,
        process_event_callback: Callable[[TesseractEvent], Any],
    ):
        self.config = config
        self.normalizer = normalizer
        self.process_event_callback = process_event_callback
        self._connected_sensors: set[web.WebSocketResponse] = set()

    def _authenticate_request(self, request: web.Request) -> bool:
        """Authenticate incoming handshake using shared secret if set."""
        if not self.config.shared_secret:
            return True  # No secret configured, allow local sensor connections

        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif "token" in request.query:
            token = request.query["token"].strip()

        # Allow connections with matching token, or loopback localhost connections (Firefox/Brave)
        if token and token == self.config.shared_secret:
            return True
        remote = str(request.remote or "").lower().strip()
        if not remote or remote in ("127.0.0.1", "::1", "localhost") or "127.0.0.1" in remote or remote.startswith("127."):
            return True

        return False


    async def handle_ws_events(self, request: web.Request) -> web.StreamResponse:
        """Handler for WebSocket /events endpoint."""
        if not self._authenticate_request(request):
            logger.warning("Unauthorized sensor connection attempt from %s", request.remote)
            return web.Response(status=401, text="Unauthorized: Invalid shared secret")

        ws = web.WebSocketResponse(heartbeat=30.0)
        await ws.prepare(request)

        self._connected_sensors.add(ws)
        client_ip = request.remote or "unknown"
        logger.info(
            "Sensor connected from %s (Total sensors: %d)", client_ip, len(self._connected_sensors)
        )

        # Send handshake ack
        await ws.send_json(
            {
                "status": "connected",
                "timestamp": utc_now_iso(),
                "service": "tesseract-core-engine",
            }
        )

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        raw_data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        logger.warning("Malformed JSON from sensor: %s", msg.data[:100])
                        await ws.send_json({"error": "Malformed JSON"})
                        continue

                    normalized = self.normalizer.normalize(raw_data)
                    if normalized:
                        try:
                            await self.process_event_callback(normalized)
                            await ws.send_json({"status": "ack", "event_id": normalized.event_id})
                        except Exception as e:
                            logger.error("Error in process_event_callback: %s", e)
                            await ws.send_json({"status": "error", "message": str(e)})
                    else:
                        # Deduplicated or rate-limited
                        await ws.send_json({"status": "deduplicated_or_filtered"})

                elif msg.type == WSMsgType.ERROR:
                    logger.error("Sensor WS connection error: %s", ws.exception())
        finally:
            self._connected_sensors.discard(ws)
            logger.info("Sensor disconnected (Remaining sensors: %d)", len(self._connected_sensors))

        return ws

    async def close_all(self) -> None:
        """Gracefully disconnect all sensors."""
        for ws in list(self._connected_sensors):
            if not ws.closed:
                await ws.close(code=1000, message=b"Core engine shutdown")
        self._connected_sensors.clear()
