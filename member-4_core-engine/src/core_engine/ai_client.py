"""
AI Layer REST Client for Tesseract Core Engine.
Communicates with Member 5's AI & Knowledge service (http://localhost:9701/api/v1).
Provides seamless fallback and mock mode when running standalone.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

logger = logging.getLogger("tesseract.core_engine.ai_client")


class AIClient:
    def __init__(self, base_url: str = "http://localhost:9701/api/v1", mock_mode: bool = False):
        self.base_url = base_url.rstrip("/")
        self.mock_mode = mock_mode
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5.0))
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def classify_intent(
        self, event_data: dict[str, Any], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Request intent classification from Member 5 AI Layer."""
        if self.mock_mode:
            return {"intent": "learning", "confidence": 0.85, "model": "mock-slm"}

        url = f"{self.base_url}/inference/classify"
        payload = {
            "task": "intent_classification",
            "event": event_data,
            "context": context or {},
        }
        try:
            session = await self._get_session()
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict):
                        return data
                logger.warning("AI classify responded with status %d", resp.status)
        except Exception as e:
            logger.debug("AI service unavailable (%s); falling back to default", e)

        return {"intent": "working", "confidence": 0.5, "model": "fallback"}

    async def summarize_episode(self, episode_dict: dict[str, Any]) -> str:
        """Request narrative episode summary from Member 5 AI Layer."""
        if self.mock_mode:
            topic = episode_dict.get("topic", "general")
            return f"User practiced {topic} and successfully completed the task."

        url = f"{self.base_url}/inference/complete"
        payload = {
            "prompt": f"Summarize the following learning episode in 1 sentence: {episode_dict}",
            "task": "episode_summary",
        }
        try:
            session = await self._get_session()
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict):
                        return str(data.get("text", ""))
        except Exception as e:
            logger.debug("AI service unavailable for episode summary (%s)", e)

        return f"Completed learning episode on {episode_dict.get('topic', 'general')}."

    async def update_knowledge_graph(self, knowledge_update_payload: dict[str, Any]) -> bool:
        """Send behavioral signals to Member 5 for Knowledge Graph update."""
        if self.mock_mode:
            logger.debug("[Mock AI] Knowledge graph update acknowledged")
            return True

        url = f"{self.base_url}/knowledge/update"
        try:
            session = await self._get_session()
            async with session.post(url, json=knowledge_update_payload) as resp:
                return resp.status in (200, 201, 202)
        except Exception as e:
            logger.debug("Knowledge graph update to AI layer failed: %s", e)
            return False
