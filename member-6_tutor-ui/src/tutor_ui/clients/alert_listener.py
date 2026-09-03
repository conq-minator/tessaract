import asyncio
import json
import logging
import websockets
from typing import Optional

from tutor_ui.services.notification import NotificationManager

logger = logging.getLogger(__name__)

class AlertListener:
    """
    Connects to Member 4's websocket to listen for real-time alerts 
    (e.g., high friction detected, stuck status).
    """
    def __init__(self, ws_url: str, notification_mgr: NotificationManager):
        self.ws_url = ws_url
        self.notification_mgr = notification_mgr
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def start(self):
        """Start the listener task."""
        self._stop_event.clear()
        self._task = asyncio.create_task(self._listen_loop())
        logger.info(f"AlertListener started connecting to {self.ws_url}")

    async def stop(self):
        """Stop the listener task."""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AlertListener stopped")

    async def _listen_loop(self):
        retry_delay = 1.0
        while not self._stop_event.is_set():
            try:
                async with websockets.connect(self.ws_url) as ws:
                    logger.info("Successfully connected to Member 4 websocket")
                    retry_delay = 1.0 # reset on success
                    
                    while not self._stop_event.is_set():
                        message = await ws.recv()
                        await self._handle_message(message)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Websocket connection lost or failed: {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30.0) # exponential backoff

    async def _handle_message(self, raw_message: str):
        try:
            data = json.loads(raw_message)
            event_type = data.get("type")
            payload = data.get("payload", {})
            
            logger.debug(f"Received WS event: {event_type}")
            
            if event_type in ("friction_alert", "stuck_detected"):
                score = payload.get("score") or payload.get("friction_score", 0.8)
                topic = payload.get("topic", "your code")
                hint = payload.get("hint") or f"High cognitive friction detected in {topic}. Would you like an AI assistance hint?"
                await self.notification_mgr.notify_friction_alert(
                    score=score,
                    hint=hint
                )
            else:
                # Generic pass-through
                await self.notification_mgr.broadcast(event_type, payload)
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse websocket message: {raw_message}")
        except Exception as e:
            logger.error(f"Error handling websocket message: {e}")
