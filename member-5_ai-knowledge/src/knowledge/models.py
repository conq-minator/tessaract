"""Data schemas for the Personal Knowledge Graph (PKG)."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class EvidenceRecord(BaseModel):
    """An individual behavioral signal updating a skill's confidence."""
    evidence_id: str
    skill_id: str
    evidence_type: str  # 'error_resolved', 'repeated_error', 'tutorial_watched', 'practice_completed', 'execution_success'
    confidence_delta: float
    source_episode_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SkillNode(BaseModel):
    """A distinct concept/skill node in the Knowledge Graph."""
    skill_id: str
    name: str
    domain: str  # e.g., 'c-programming', 'python', 'data-structures'
    parent_id: Optional[str] = None
    confidence: float = 0.5  # Range [0.0, 1.0]
    evidence_count: int = 0
    status: str = "developing"  # 'weak', 'developing', 'good', 'mastered'
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    prerequisites: List[str] = Field(default_factory=list)


class KnowledgeGraphSnapshot(BaseModel):
    """Full graph snapshot for API transfer and visualization."""
    nodes: List[SkillNode]
    edges: List[Dict[str, str]]  # [{'source': '...', 'target': '...', 'relation': '...'}]
    total_skills: int
    mastered_count: int
    weak_count: int
