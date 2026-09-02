from typing import Dict, Any, List
from tutor_ui.clients.ai_client import AIClient
from tutor_ui.mock.mock_ai import get_mock_recommendations, get_mock_knowledge_graph

class RecommendationService:
    def __init__(self, ai_client: AIClient, mock_mode: bool):
        self.ai_client = ai_client
        self.mock_mode = mock_mode
        
    async def get_recommendations(self, context_id: str = "current") -> List[Dict[str, Any]]:
        if self.mock_mode:
            return get_mock_recommendations()
        return await self.ai_client.get_recommendations(context_id)

    async def get_knowledge_graph(self) -> Dict[str, Any]:
        if self.mock_mode:
            return get_mock_knowledge_graph()
        
        kg = await self.ai_client.get_knowledge_graph()
        if kg:
            return kg
            
        # Fallback if connection fails
        return {"nodes": [], "links": []}
