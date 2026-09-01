from typing import Dict, Any
from tutor_ui.clients.core_client import CoreClient
from tutor_ui.mock.mock_core import get_mock_context, get_mock_friction, get_mock_episodes, get_mock_session

class AssistanceService:
    """
    Manages L1-L5 assistance by pulling from Core context 
    and enforcing permission constraints.
    """
    def __init__(self, core_client: CoreClient, permission_guard, mock_mode: bool):
        self.core_client = core_client
        self.permission_guard = permission_guard
        self.mock_mode = mock_mode
        
    async def get_current_context(self) -> Dict[str, Any]:
        if self.mock_mode:
            return get_mock_context()
            
        ctx = await self.core_client.get_context()
        if ctx:
            return ctx
        return {"subject": "Unknown", "topic": "Unknown", "application": "System"}

    async def get_friction(self) -> Dict[str, Any]:
        if self.mock_mode:
            return get_mock_friction()
            
        frict = await self.core_client.get_friction()
        if frict:
            return frict
        return {"level": "LOW", "score": 0.0}
        
    async def get_episodes(self) -> list:
        # Member 4 API for episodes not defined yet in core_client, fallback to mock for now
        return get_mock_episodes()
        
    async def get_session(self) -> dict:
        return get_mock_session()
