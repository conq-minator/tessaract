"""Integration tests for Member 5 REST API routes."""

import pytest
from aiohttp.test_utils import TestClient, TestServer
from src.api.app import create_app
from src.config import settings


@pytest.mark.asyncio
async def test_health_endpoint():
    app = create_app(mock_mode=True)
    async with TestClient(TestServer(app)) as cli:
        resp = await cli.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "member-5_ai-knowledge"


@pytest.mark.asyncio
async def test_model_status_endpoint():
    app = create_app(mock_mode=True)
    async with TestClient(TestServer(app)) as cli:
        resp = await cli.get("/api/v1/models/status")
        assert resp.status == 200
        data = await resp.json()
        assert data["mode"] == "mock"


@pytest.mark.asyncio
async def test_knowledge_graph_endpoint():
    app = create_app(mock_mode=True)
    async with TestClient(TestServer(app)) as cli:
        headers = {"Authorization": f"Bearer {settings.shared_secret}"}
        resp = await cli.get("/api/v1/knowledge/graph", headers=headers)
        assert resp.status == 200
        data = await resp.json()
        assert "nodes" in data
        assert "edges" in data
        assert data["total_skills"] > 0


@pytest.mark.asyncio
async def test_inference_complete_endpoint():
    app = create_app(mock_mode=True)
    async with TestClient(TestServer(app)) as cli:
        headers = {"Authorization": f"Bearer {settings.shared_secret}"}
        payload = {"prompt": "What is memory allocation in C?", "task_type": "reason"}
        resp = await cli.post("/api/v1/inference/complete", json=payload, headers=headers)
        assert resp.status == 200
        data = await resp.json()
        assert "content" in data
        assert data["source"] == "mock"


@pytest.mark.asyncio
async def test_tutor_hint_endpoint():
    app = create_app(mock_mode=True)
    async with TestClient(TestServer(app)) as cli:
        headers = {"Authorization": f"Bearer {settings.shared_secret}"}
        payload = {"topic": "c-pointer-deref", "level": 1, "friction_score": 0.75}
        resp = await cli.post("/api/v1/tutor/hint", json=payload, headers=headers)
        assert resp.status == 200
        data = await resp.json()
        assert data["level"] == 1
        assert "content" in data


@pytest.mark.asyncio
async def test_tutor_roadmap_endpoint():
    app = create_app(mock_mode=True)
    async with TestClient(TestServer(app)) as cli:
        headers = {"Authorization": f"Bearer {settings.shared_secret}"}
        payload = {"subject": "C Programming", "available_time": "1_hour_per_day"}
        resp = await cli.post("/api/v1/tutor/roadmap", json=payload, headers=headers)
        assert resp.status == 200
        data = await resp.json()
        assert "roadmap" in data
        assert data["roadmap"]["subject"] == "C Programming"
