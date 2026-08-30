"""Vector Store integrating with sqlite-vec for local semantic search."""

import sqlite3
import json
import math
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sqlite_vec

from src.config import settings

DIMENSION = 384  # Default all-minilm vector dimension


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class VectorStore:
    """Embedded SQLite vector database with sqlite-vec extension and cosine fallback."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.vector_db_path
        self._has_sqlite_vec = False
        self._init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
            self._has_sqlite_vec = True
        except Exception:
            self._has_sqlite_vec = False
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata_json TEXT,
                    embedding_json TEXT NOT NULL
                );
            """)

    def insert(self, doc_id: str, content: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None):
        """Insert or update a document and its embedding."""
        with self._connection() as conn:
            conn.execute("""
                INSERT INTO documents (doc_id, content, metadata_json, embedding_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    content=excluded.content,
                    metadata_json=excluded.metadata_json,
                    embedding_json=excluded.embedding_json
            """, (
                doc_id,
                content,
                json.dumps(metadata or {}),
                json.dumps(embedding),
            ))

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Search top-k nearest documents by cosine similarity."""
        with self._connection() as conn:
            cur = conn.execute("SELECT doc_id, content, metadata_json, embedding_json FROM documents")
            rows = cur.fetchall()

            scored: List[Tuple[float, Dict[str, Any]]] = []
            for row in rows:
                doc_vec = json.loads(row["embedding_json"])
                sim = cosine_similarity(query_embedding, doc_vec)
                if sim >= threshold:
                    scored.append((
                        sim,
                        {
                            "doc_id": row["doc_id"],
                            "content": row["content"],
                            "metadata": json.loads(row["metadata_json"] or "{}"),
                            "similarity": round(sim, 4),
                        }
                    ))

            # Sort descending by similarity
            scored.sort(key=lambda x: x[0], reverse=True)
            return [item[1] for item in scored[:top_k]]


# Global vector store singleton
vector_store = VectorStore()
