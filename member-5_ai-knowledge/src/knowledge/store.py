"""SQLite storage adapter for the Personal Knowledge Graph."""

import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from src.knowledge.models import SkillNode, EvidenceRecord
from src.config import settings


class KnowledgeStore:
    """ACID SQLite store for persistent skills, relations, and evidence logs."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.kg_db_path
        self._init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        """Create tables if they do not exist."""
        with self._connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS skills (
                    skill_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    parent_id TEXT,
                    confidence REAL NOT NULL DEFAULT 0.5,
                    evidence_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'developing',
                    last_updated TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS prerequisites (
                    skill_id TEXT NOT NULL,
                    prerequisite_id TEXT NOT NULL,
                    PRIMARY KEY (skill_id, prerequisite_id),
                    FOREIGN KEY (skill_id) REFERENCES skills (skill_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS evidence_log (
                    evidence_id TEXT PRIMARY KEY,
                    skill_id TEXT NOT NULL,
                    evidence_type TEXT NOT NULL,
                    confidence_delta REAL NOT NULL,
                    source_episode_id TEXT,
                    timestamp TEXT NOT NULL,
                    metadata_json TEXT,
                    FOREIGN KEY (skill_id) REFERENCES skills (skill_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS roadmaps (
                    interest_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    standing TEXT NOT NULL DEFAULT 'Beginner',
                    roadmap_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_skills_domain ON skills(domain);
                CREATE INDEX IF NOT EXISTS idx_evidence_skill ON evidence_log(skill_id);
            """)

    def upsert_skill(self, skill: SkillNode):
        """Insert or update a skill node."""
        with self._connection() as conn:
            conn.execute("""
                INSERT INTO skills (skill_id, name, domain, parent_id, confidence, evidence_count, status, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(skill_id) DO UPDATE SET
                    name=excluded.name,
                    domain=excluded.domain,
                    parent_id=excluded.parent_id,
                    confidence=excluded.confidence,
                    evidence_count=excluded.evidence_count,
                    status=excluded.status,
                    last_updated=excluded.last_updated
            """, (
                skill.skill_id,
                skill.name,
                skill.domain,
                skill.parent_id,
                skill.confidence,
                skill.evidence_count,
                skill.status,
                skill.last_updated,
            ))

            # Sync prerequisites
            conn.execute("DELETE FROM prerequisites WHERE skill_id = ?", (skill.skill_id,))
            for prereq in skill.prerequisites:
                conn.execute(
                    "INSERT OR IGNORE INTO prerequisites (skill_id, prerequisite_id) VALUES (?, ?)",
                    (skill.skill_id, prereq)
                )

    def get_skill(self, skill_id: str) -> Optional[SkillNode]:
        """Fetch a skill by ID along with its prerequisites."""
        with self._connection() as conn:
            cur = conn.execute("SELECT * FROM skills WHERE skill_id = ?", (skill_id,))
            row = cur.fetchone()
            if not row:
                return None

            prereq_cur = conn.execute(
                "SELECT prerequisite_id FROM prerequisites WHERE skill_id = ?", (skill_id,)
            )
            prereqs = [r["prerequisite_id"] for r in prereq_cur.fetchall()]

            return SkillNode(
                skill_id=row["skill_id"],
                name=row["name"],
                domain=row["domain"],
                parent_id=row["parent_id"],
                confidence=row["confidence"],
                evidence_count=row["evidence_count"],
                status=row["status"],
                last_updated=row["last_updated"],
                prerequisites=prereqs,
            )

    def get_all_skills(self) -> List[SkillNode]:
        """Fetch all skills in the database."""
        with self._connection() as conn:
            cur = conn.execute("SELECT * FROM skills ORDER BY domain, name")
            skills: List[SkillNode] = []
            for row in cur.fetchall():
                p_cur = conn.execute(
                    "SELECT prerequisite_id FROM prerequisites WHERE skill_id = ?", (row["skill_id"],)
                )
                prereqs = [p["prerequisite_id"] for p in p_cur.fetchall()]
                skills.append(
                    SkillNode(
                        skill_id=row["skill_id"],
                        name=row["name"],
                        domain=row["domain"],
                        parent_id=row["parent_id"],
                        confidence=row["confidence"],
                        evidence_count=row["evidence_count"],
                        status=row["status"],
                        last_updated=row["last_updated"],
                        prerequisites=prereqs,
                    )
                )
            return skills

    def add_evidence(self, evidence: EvidenceRecord):
        """Append an evidence record to the audit log."""
        with self._connection() as conn:
            conn.execute("""
                INSERT INTO evidence_log (
                    evidence_id, skill_id, evidence_type, confidence_delta,
                    source_episode_id, timestamp, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                evidence.evidence_id,
                evidence.skill_id,
                evidence.evidence_type,
                evidence.confidence_delta,
                evidence.source_episode_id,
                evidence.timestamp,
                json.dumps(evidence.metadata),
            ))

    def get_evidence_for_skill(self, skill_id: str, limit: int = 50) -> List[EvidenceRecord]:
        """Fetch evidence history for a given skill."""
        with self._connection() as conn:
            cur = conn.execute("""
                SELECT * FROM evidence_log WHERE skill_id = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (skill_id, limit))
            results = []
            for r in cur.fetchall():
                results.append(
                    EvidenceRecord(
                        evidence_id=r["evidence_id"],
                        skill_id=r["skill_id"],
                        evidence_type=r["evidence_type"],
                        confidence_delta=r["confidence_delta"],
                        source_episode_id=r["source_episode_id"],
                        timestamp=r["timestamp"],
                        metadata=json.loads(r["metadata_json"] or "{}"),
                    )
                )
            return results

    def save_roadmap(self, interest_id: str, title: str, standing: str, roadmap: list) -> dict:
        """Save or update an activated comprehensive learning roadmap."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connection() as conn:
            conn.execute("""
                INSERT INTO roadmaps (interest_id, title, standing, roadmap_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(interest_id) DO UPDATE SET
                    title=excluded.title,
                    standing=excluded.standing,
                    roadmap_json=excluded.roadmap_json,
                    updated_at=excluded.updated_at
            """, (interest_id, title, standing, json.dumps(roadmap), now, now))
        return {
            "interest_id": interest_id,
            "title": title,
            "standing": standing,
            "roadmap": roadmap,
            "updated_at": now
        }

    def get_roadmap(self, interest_id: str) -> Optional[dict]:
        """Fetch saved comprehensive roadmap for an interest if active."""
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM roadmaps WHERE interest_id = ?", (interest_id,)).fetchone()
            if not row:
                return None
            try:
                rm = json.loads(row["roadmap_json"])
            except Exception:
                rm = []
            return {
                "interest_id": row["interest_id"],
                "title": row["title"],
                "standing": row["standing"],
                "roadmap": rm,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    def get_all_roadmaps(self) -> dict:
        """Fetch all activated roadmaps keyed by interest_id."""
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM roadmaps").fetchall()
            result = {}
            for r in rows:
                try:
                    result[r["interest_id"]] = json.loads(r["roadmap_json"])
                except Exception:
                    result[r["interest_id"]] = []
            return result

    def delete_roadmap(self, interest_id: str) -> bool:
        """Remove an activated roadmap for an interest."""
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM roadmaps WHERE interest_id = ?", (interest_id,))
            return cur.rowcount > 0

    def clear_all(self):
        """Wipe all skills, prerequisites, evidence records, and roadmaps from the database."""
        with self._connection() as conn:
            conn.execute("DELETE FROM prerequisites")
            conn.execute("DELETE FROM evidence_log")
            conn.execute("DELETE FROM skills")
            conn.execute("DELETE FROM roadmaps")


