import logging
from aiohttp import ClientSession
from typing import Dict, Any, Optional

from tutor_ui.utils.auth import get_auth_headers

logger = logging.getLogger(__name__)

class CoreClient:
    """
    Client for interacting with Member 4 (Core / Port 9700).
    """
    def __init__(self, session: ClientSession, base_url: str = "http://localhost:9700"):
        self.session = session
        self.base_url = base_url
        
    async def get_context(self) -> Optional[Dict[str, Any]]:
        """Fetch current user focus/context."""
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/context", 
                headers=get_auth_headers(),
                timeout=5.0
            ) as response:
                if response.status == 200:
                    return await response.json()
                logger.warning(f"Core API returned {response.status} for context")
                return None
        except Exception as e:
            logger.error(f"Failed to connect to Core API (context): {e}")
            return None

    async def get_friction(self) -> Optional[Dict[str, Any]]:
        """Fetch current cognitive friction score."""
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/friction", 
                headers=get_auth_headers(),
                timeout=2.0
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.error(f"Failed to connect to Core API (friction): {e}")
            return None
