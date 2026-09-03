import logging
from typing import Any, Dict, List, Optional, cast
from aiohttp import ClientSession, ClientTimeout

from tutor_ui.utils.auth import get_auth_headers

logger = logging.getLogger(__name__)


class AIClient:
    """
    Client for interacting with Member 5 (AI / Port 9701).
    """
    def __init__(self, session: ClientSession, base_url: str = "http://localhost:9701"):
        self.session = session
        self.base_url = base_url.rstrip("/")
        
    async def get_recommendations(self, context_id: str = "current") -> List[Dict[str, Any]]:
        """Fetch personalized learning roadmap / recommendations from Member 5."""
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/tutor/roadmap", 
                json={"subject": "C Programming", "available_time": "1_hour_per_day"},
                headers=get_auth_headers(),
                timeout=ClientTimeout(total=60.0)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    roadmap = data.get("roadmap", {})
                    milestones = roadmap.get("milestones", [])
                    return cast(List[Dict[str, Any]], milestones)
                return []
        except Exception as e:
            logger.warning("AI API roadmap call timed out or busy: %s", e)
            return []

    async def get_knowledge_graph(self) -> Optional[Dict[str, Any]]:
        """Fetch user knowledge graph from Member 5 and map to frontend D3 format."""
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/knowledge/graph", 
                headers=get_auth_headers(),
                timeout=ClientTimeout(total=10.0)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    raw_nodes = data.get("nodes", [])
                    raw_edges = data.get("edges", [])
                    
                    # Map to D3 format: id, label, status, confidence
                    nodes = [
                        {
                            "id": n.get("skill_id"),
                            "skill_id": n.get("skill_id"),
                            "label": n.get("name"),
                            "name": n.get("name") or n.get("label"),
                            "domain": n.get("domain"),
                            "status": n.get("status"),
                            "confidence": n.get("confidence"),
                            "evidence_count": n.get("evidence_count", 1),
                        }
                        for n in raw_nodes
                    ]
                    links = [
                        {
                            "source": e.get("source"),
                            "target": e.get("target"),
                            "type": e.get("relation", "prerequisite"),
                        }
                        for e in raw_edges
                    ]
                    result: Dict[str, Any] = {
                        "nodes": nodes,
                        "links": links,
                        "total_skills": data.get("total_skills", len(nodes)),
                        "mastered_count": data.get("mastered_count", 0),
                        "weak_count": data.get("weak_count", 0),
                    }
                    return result
                logger.warning("Member 5 AI API returned %s for knowledge/graph", response.status)
                return None
        except Exception as e:
            logger.error("Failed to connect to AI API (KG): %s", e)
            return None
