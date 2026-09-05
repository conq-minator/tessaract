"""In-memory NetworkX Knowledge Graph engine for topological reasoning."""

import networkx as nx
from typing import List, Dict, Optional, Set, Any
from datetime import datetime, timezone
import uuid

from src.knowledge.models import SkillNode, EvidenceRecord, KnowledgeGraphSnapshot
from src.knowledge.store import KnowledgeStore
from src.knowledge.scoring import (
    calculate_new_confidence,
    calculate_status,
    apply_temporal_decay,
)


class KnowledgeGraph:
    """Directed graph maintaining concepts, prerequisite chains, and skill states."""

    def __init__(self, store: Optional[KnowledgeStore] = None):
        self.store = store or KnowledgeStore()
        self.graph = nx.DiGraph()
        self._load_from_store()
        # Brand new empty graph: concepts are added dynamically upon code execution!

    def _load_from_store(self):
        """Load persistent skills and prerequisite edges from SQLite into NetworkX."""
        skills = self.store.get_all_skills()
        if not skills:
            self._seed_default_taxonomies()
            skills = self.store.get_all_skills()
        for skill in skills:

            # Apply temporal decay on reload
            decayed_conf = apply_temporal_decay(skill.confidence, skill.last_updated)
            skill.confidence = decayed_conf
            skill.status = calculate_status(decayed_conf)

            self.graph.add_node(
                skill.skill_id,
                name=skill.name,
                domain=skill.domain,
                parent_id=skill.parent_id,
                confidence=skill.confidence,
                evidence_count=skill.evidence_count,
                status=skill.status,
                last_updated=skill.last_updated,
            )

        # Add prerequisite directed edges: prereq -> skill
        for skill in skills:
            for prereq in skill.prerequisites:
                if self.graph.has_node(prereq):
                    self.graph.add_edge(prereq, skill.skill_id, relation="prerequisite_of")

    def _seed_default_taxonomies(self):
        """Seed starter concept hierarchies for C Programming and Python."""
        default_skills = [
            # C Programming
            ("c-variables", "Variables & Types", "c-programming", None, 0.85, []),
            ("c-loops", "Control Flow & Loops", "c-programming", None, 0.80, ["c-variables"]),
            ("c-functions", "Functions & Scope", "c-programming", None, 0.75, ["c-variables"]),
            ("c-arrays", "Arrays & Strings", "c-programming", None, 0.70, ["c-loops"]),
            ("c-pointers", "Pointers", "c-programming", None, 0.30, ["c-variables", "c-functions"]),
            ("c-pointer-deref", "Pointer Dereferencing", "c-programming", "c-pointers", 0.25, ["c-pointers"]),
            ("c-null-pointers", "NULL Pointer Handling", "c-programming", "c-pointers", 0.45, ["c-pointer-deref"]),
            ("c-pointer-arithmetic", "Pointer Arithmetic", "c-programming", "c-pointers", 0.20, ["c-pointer-deref", "c-arrays"]),
            ("c-linked-lists", "Linked Lists", "c-programming", None, 0.40, ["c-pointers", "c-pointer-deref"]),
            
            # Python
            ("py-syntax", "Python Syntax & Variables", "python", None, 0.90, []),
            ("py-collections", "Lists & Dictionaries", "python", None, 0.85, ["py-syntax"]),
            ("py-functions", "Python Functions", "python", None, 0.80, ["py-syntax"]),
            ("py-oop", "Object Oriented Programming", "python", None, 0.50, ["py-functions", "py-collections"]),
            ("py-numpy", "NumPy Vectorization", "python", None, 0.40, ["py-collections"]),
            ("py-pandas", "Pandas DataFrames", "python", None, 0.35, ["py-numpy"]),
        ]

        now = datetime.now(timezone.utc).isoformat()
        for skill_id, name, domain, parent, conf, prereqs in default_skills:
            node = SkillNode(
                skill_id=skill_id,
                name=name,
                domain=domain,
                parent_id=parent,
                confidence=conf,
                evidence_count=5,
                status=calculate_status(conf),
                last_updated=now,
                prerequisites=prereqs,
            )
            self.upsert_node(node)

    def upsert_node(self, skill: SkillNode):
        """Insert or update node in graph and persistent store."""
        self.graph.add_node(
            skill.skill_id,
            name=skill.name,
            domain=skill.domain,
            parent_id=skill.parent_id,
            confidence=skill.confidence,
            evidence_count=skill.evidence_count,
            status=skill.status,
            last_updated=skill.last_updated,
        )
        for prereq in skill.prerequisites:
            if self.graph.has_node(prereq):
                self.graph.add_edge(prereq, skill.skill_id, relation="prerequisite_of")

        self.store.upsert_skill(skill)

    def record_evidence(
        self,
        skill_id: str,
        evidence_type: str,
        confidence_delta: float = 0.0,
        source_episode_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[SkillNode]:
        """Ingest behavioral evidence, recalculate confidence, and persist updates."""
        if not self.graph.has_node(skill_id):
            # Auto-register newly discovered skill/concept!
            name = (metadata.get("name") if metadata else None) or skill_id.replace("-", " ").replace("_", " ").title()
            domain = (metadata.get("domain") if metadata else None) or "general"
            initial_conf = 0.70 if confidence_delta >= 0 else 0.35

            node = SkillNode(
                skill_id=skill_id,
                name=name,
                domain=domain,
                parent_id=None,
                confidence=initial_conf,
                evidence_count=1,
                status=calculate_status(initial_conf),
                last_updated=datetime.now(timezone.utc).isoformat(),
                prerequisites=[]
            )
            self.upsert_node(node)
            return node

        node_data = self.graph.nodes[skill_id]
        cur_conf = node_data["confidence"]
        ev_count = node_data["evidence_count"] + 1

        new_conf = calculate_new_confidence(cur_conf, evidence_type, confidence_delta, ev_count)
        new_status = calculate_status(new_conf)
        now = datetime.now(timezone.utc).isoformat()

        # Update node in NetworkX
        node_data["confidence"] = new_conf
        node_data["evidence_count"] = ev_count
        node_data["status"] = new_status
        node_data["last_updated"] = now

        # Prereqs from edges
        prereqs = [u for u, v in self.graph.in_edges(skill_id)]

        updated_skill = SkillNode(
            skill_id=skill_id,
            name=node_data["name"],
            domain=node_data["domain"],
            parent_id=node_data.get("parent_id"),
            confidence=new_conf,
            evidence_count=ev_count,
            status=new_status,
            last_updated=now,
            prerequisites=prereqs,
        )

        self.store.upsert_skill(updated_skill)

        # Log evidence record
        evidence = EvidenceRecord(
            evidence_id=str(uuid.uuid4()),
            skill_id=skill_id,
            evidence_type=evidence_type,
            confidence_delta=round(new_conf - cur_conf, 4),
            source_episode_id=source_episode_id,
            timestamp=now,
            metadata=metadata or {},
        )
        self.store.add_evidence(evidence)

        return updated_skill

    def get_skill(self, skill_id: str) -> Optional[SkillNode]:
        """Fetch single skill node."""
        if not self.graph.has_node(skill_id):
            return None
        d = self.graph.nodes[skill_id]
        prereqs = [u for u, v in self.graph.in_edges(skill_id)]
        return SkillNode(
            skill_id=skill_id,
            name=d["name"],
            domain=d["domain"],
            parent_id=d.get("parent_id"),
            confidence=d["confidence"],
            evidence_count=d["evidence_count"],
            status=d["status"],
            last_updated=d["last_updated"],
            prerequisites=prereqs,
        )

    def find_prerequisite_gaps(self, skill_id: str, gap_threshold: float = 0.60) -> List[SkillNode]:
        """Traverse predecessors to detect weak prerequisites causing friction."""
        if not self.graph.has_node(skill_id):
            return []

        # Find all ancestor prerequisites
        ancestors: Set[str] = nx.ancestors(self.graph, skill_id)
        gaps: List[SkillNode] = []

        for anc_id in ancestors:
            anc_node = self.get_skill(anc_id)
            if anc_node and anc_node.confidence < gap_threshold:
                gaps.append(anc_node)

        # Sort with weakest skills first
        gaps.sort(key=lambda s: s.confidence)
        return gaps

    def get_snapshot(self) -> KnowledgeGraphSnapshot:
        """Produce full graph snapshot for visualization and serialization."""
        nodes: List[SkillNode] = []
        edges: List[Dict[str, str]] = []

        for node_id in self.graph.nodes():
            skill = self.get_skill(node_id)
            if skill:
                nodes.append(skill)

        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relation": data.get("relation", "prerequisite_of"),
            })

        mastered = sum(1 for n in nodes if n.status == "mastered")
        weak = sum(1 for n in nodes if n.status == "weak")

        return KnowledgeGraphSnapshot(
            nodes=nodes,
            edges=edges,
            total_skills=len(nodes),
            mastered_count=mastered,
            weak_count=weak,
        )

    def clear_all(self):
        """Wipe the in-memory graph and persistent store."""
        self.graph.clear()
        self.store.clear_all()


# Global knowledge graph singleton
knowledge_graph = KnowledgeGraph()

