"""Unit tests for KnowledgeGraph and KnowledgeStore."""

import pytest
import tempfile
from pathlib import Path
from src.knowledge.store import KnowledgeStore
from src.knowledge.graph import KnowledgeGraph
from src.knowledge.models import SkillNode


@pytest.fixture
def temp_graph():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_kg.db"
        store = KnowledgeStore(db_path=db_path)
        kg = KnowledgeGraph(store=store)
        yield kg


def test_knowledge_graph_seeded(temp_graph):
    # Knowledge graph should have default taxonomy seeded
    snapshot = temp_graph.get_snapshot()
    assert snapshot.total_skills > 5
    assert temp_graph.graph.has_node("c-pointers")
    assert temp_graph.graph.has_node("c-pointer-deref")


def test_prerequisite_gap_detection(temp_graph):
    # In default seeding, c-pointer-deref has weak prerequisites
    gaps = temp_graph.find_prerequisite_gaps("c-null-pointers", gap_threshold=0.60)
    assert len(gaps) >= 1
    gap_ids = [g.skill_id for g in gaps]
    assert "c-pointers" in gap_ids or "c-pointer-deref" in gap_ids


def test_record_evidence_and_persist(temp_graph):
    node = temp_graph.get_skill("c-pointer-deref")
    assert node is not None
    orig_conf = node.confidence

    updated = temp_graph.record_evidence(
        skill_id="c-pointer-deref",
        evidence_type="error_resolved",
        source_episode_id="test-ep-1",
    )
    assert updated is not None
    assert updated.confidence > orig_conf
    assert updated.evidence_count == node.evidence_count + 1
