"""Unit tests for VectorStore."""

import pytest
import tempfile
from pathlib import Path
from src.embeddings.vector_store import VectorStore, cosine_similarity


def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    assert cosine_similarity(v1, v2) == pytest.approx(1.0)
    assert cosine_similarity(v1, v3) == pytest.approx(0.0)


def test_vector_store_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_vec.db"
        store = VectorStore(db_path=db_path)

        store.insert(
            doc_id="doc1",
            content="C pointer dereferencing explanation",
            embedding=[1.0, 0.5, 0.2],
            metadata={"domain": "c"},
        )
        store.insert(
            doc_id="doc2",
            content="Python loop syntax",
            embedding=[0.0, 0.1, 0.9],
            metadata={"domain": "python"},
        )

        results = store.search(query_embedding=[1.0, 0.5, 0.1], top_k=1)
        assert len(results) == 1
        assert results[0]["doc_id"] == "doc1"
        assert results[0]["metadata"]["domain"] == "c"
