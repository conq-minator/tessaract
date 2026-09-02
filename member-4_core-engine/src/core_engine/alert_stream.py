"""
WebSocket Alert Stream for Tesseract Core Engine.
Broadcasts real-time alerts (stuck_detected, episode_completed, context_changed, etc.)
to connected downstream clients (Member 6 — Tutor / UI) on ws://localhost:9700/alerts.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiohttp import WSMsgType, web

from .models import AlertMessage, utc_now_iso

logger = logging.getLogger("tesseract.core_engine.alert_stream")


class AlertStreamManager:
    def __init__(self):
        self._clients: set[web.WebSocketResponse] = set()

    async def handle_ws_alerts(self, request: web.Request) -> web.WebSocketResponse:
        """Handler for WebSocket /alerts endpoint."""
        ws = web.WebSocketResponse(heartbeat=30.0)
        await ws.prepare(request)

        self._clients.add(ws)
        client_ip = request.remote or "unknown"
        logger.info(
            "UI Alert client connected from %s (Total clients: %d)", client_ip, len(self._clients)
        )

        try:
            # Send initial connection confirmation
            welcome = {
                "alert_type": "connected",
                "timestamp": utc_now_iso(),
                "payload": {"message": "Tesseract Core Engine Alert Stream Connected"},
            }
            await ws.send_json(welcome)

            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    # Clients might ping or send ack
                    logger.debug("Received message from alert client: %s", msg.data)
                elif msg.type == WSMsgType.ERROR:
                    logger.error("Alert WS client connection closed with error: %s", ws.exception())
        finally:
            self._clients.discard(ws)
            logger.info("UI Alert client disconnected (Remaining clients: %d)", len(self._clients))

        return ws

    async def broadcast_alert(self, alert: AlertMessage) -> None:
        """Broadcast an alert message to all connected UI clients."""
        if not self._clients:
            logger.debug("No alert clients connected; skipping broadcast for %s", alert.alert_type)
            return

        payload_dict = alert.to_dict()
        tasks = []
        for ws in list(self._clients):
            if not ws.closed:
                tasks.append(ws.send_json(payload_dict))
            else:
                self._clients.discard(ws)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    logger.warning("Failed to send alert to a client: %s", res)

    async def broadcast(self, alert_type: str, payload: dict[str, Any]) -> None:
        """Convenience method to broadcast by type and payload dict."""
        alert = AlertMessage(alert_type=alert_type, payload=payload)  # type: ignore
        await self.broadcast_alert(alert)

    async def close_all(self) -> None:
        """Close all client connections gracefully."""
        for ws in list(self._clients):
            if not ws.closed:
                await ws.close(code=1000, message=b"Core engine shutting down")
        self._clients.clear()
