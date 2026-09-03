import logging
from typing import Any, Dict, List, Optional, cast
from aiohttp import ClientSession, ClientTimeout

from tutor_ui.utils.auth import get_auth_headers

logger = logging.getLogger(__name__)


class CoreClient:
    """
    Client for interacting with Member 4 (Core / Port 9700).
    """
    def __init__(self, session: ClientSession, base_url: str = "http://localhost:9700"):
        self.session = session
        self.base_url = base_url.rstrip("/")
        
    async def get_context(self) -> Optional[Dict[str, Any]]:
        """Fetch current user focus/context from Member 4."""
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/context/current", 
                headers=get_auth_headers(),
                timeout=ClientTimeout(total=5.0)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return cast(Dict[str, Any], data)
                logger.warning("Core API returned %s for context/current", response.status)
                return None
        except Exception as e:
            logger.error("Failed to connect to Core API (context): %s", e)
            return None

    async def get_friction(self) -> Optional[Dict[str, Any]]:
        """Fetch current cognitive friction score from Member 4."""
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/friction/current", 
                headers=get_auth_headers(),
                timeout=ClientTimeout(total=2.0)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return cast(Dict[str, Any], data)
                return None
        except Exception as e:
            logger.error("Failed to connect to Core API (friction): %s", e)
            return None

    async def get_episodes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent learning episodes from Member 4."""
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/episodes/recent?limit={limit}",
                headers=get_auth_headers(),
                timeout=ClientTimeout(total=5.0)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    episodes = data.get("episodes", [])
                    return cast(List[Dict[str, Any]], episodes)
                return []
        except Exception as e:
            logger.error("Failed to connect to Core API (episodes): %s", e)
            return []

    async def get_session(self) -> Optional[Dict[str, Any]]:
        """Fetch active session from Member 4."""
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/sessions/active",
                headers=get_auth_headers(),
                timeout=ClientTimeout(total=5.0)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return cast(Dict[str, Any], data)
                return None
        except Exception as e:
            logger.error("Failed to connect to Core API (sessions): %s", e)
            return None
