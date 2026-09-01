import logging
from aiohttp import ClientSession
from typing import Dict, Any, Optional, List

from tutor_ui.utils.auth import get_auth_headers

logger = logging.getLogger(__name__)

class AIClient:
    """
    Client for interacting with Member 5 (AI / Port 9701).
    """
    def __init__(self, session: ClientSession, base_url: str = "http://localhost:9701"):
        self.session = session
        self.base_url = base_url
        
    async def get_recommendations(self, context_id: str) -> List[Dict[str, Any]]:
        """Fetch personalized learning recommendations."""
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/recommendations?context={context_id}", 
                headers=get_auth_headers(),
                timeout=10.0
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("recommendations", [])
                logger.warning(f"AI API returned {response.status} for recommendations")
                return []
        except Exception as e:
            logger.error(f"Failed to connect to AI API (recommendations): {e}")
            return []

    async def get_knowledge_graph(self) -> Optional[Dict[str, Any]]:
        """Fetch user knowledge graph."""
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/knowledge-graph", 
                headers=get_auth_headers(),
                timeout=10.0
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.error(f"Failed to connect to AI API (KG): {e}")
            return None
