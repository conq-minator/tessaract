import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class NotificationManager:
    """
    Manages notifications and Server-Sent Events (SSE) queues for clients.
    """
    def __init__(self):
        # A list of async queues. Each connected UI client gets its own queue.
        self.clients: List[asyncio.Queue] = []
        
    async def register_client(self) -> asyncio.Queue:
        """Create a new queue for a connecting SSE client."""
        queue = asyncio.Queue()
        self.clients.append(queue)
        logger.info(f"SSE Client connected. Total clients: {len(self.clients)}")
        return queue
        
    def unregister_client(self, queue: asyncio.Queue):
        """Remove a client queue when they disconnect."""
        if queue in self.clients:
            self.clients.remove(queue)
            logger.info(f"SSE Client disconnected. Total clients: {len(self.clients)}")

    async def broadcast(self, event_type: str, payload: Dict[str, Any]):
        """Push a message to all connected UI clients."""
        if not self.clients:
            return
            
        message = {
            "type": event_type,
            "data": payload
        }
        
        for queue in self.clients:
            try:
                queue.put_nowait(message)
            except Exception as e:
                logger.error(f"Failed to queue SSE message: {e}")
                
    async def notify_friction_alert(self, score: float, hint: str):
        """Helper to send a specific friction toast notification."""
        await self.broadcast("toast", {
            "title": "High Friction Detected",
            "message": hint,
            "type": "warning"
        })

    async def shutdown(self):
        """Shutdown all active SSE connections gracefully."""
        for queue in list(self.clients):
            try:
                queue.put_nowait({"type": "_shutdown"})
            except Exception:
                pass
