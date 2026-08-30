"""Unit tests for ModelRegistry and MockModelProvider."""

import pytest
from src.models.registry import ModelRegistry


@pytest.mark.asyncio
async def test_mock_registry_completion():
    registry = ModelRegistry(use_mock=True)
    res = await registry.complete(prompt="What is a C pointer?", task_type="reason")
    assert res.content != ""
    assert res.source == "mock"
    assert res.latency_ms >= 0.0


@pytest.mark.asyncio
async def test_mock_registry_classification():
    registry = ModelRegistry(use_mock=True)
    labels = ["c-pointers", "python-loops", "web-dev"]
    res = await registry.classify(text="User is dereferencing NULL in C", labels=labels)
    assert res.label in labels
    assert 0.0 <= res.confidence <= 1.0


@pytest.mark.asyncio
async def test_mock_registry_embedding():
    registry = ModelRegistry(use_mock=True)
    texts = ["Hello world", "Learning C pointers"]
    res = await registry.embed(texts=texts)
    assert len(res.embeddings) == 2
    assert res.dimensions == 384
