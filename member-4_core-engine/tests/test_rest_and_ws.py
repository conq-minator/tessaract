"""
Test REST API and WebSockets.
"""

from pathlib import Path

import pytest

from core_engine.app import CoreEngineApp
from core_engine.config import CoreConfig


@pytest.fixture
def app_instance(tmp_path: Path):
    db_file = tmp_path / "test_app.db"
    config = CoreConfig(
        db_path_raw=str(db_file),
        friction_threshold_high=0.7,
    )
    app = CoreEngineApp(config=config, mock_ai=True)
    return app


async def test_rest_api_health_and_endpoints(aiohttp_client, app_instance):
    web_app = app_instance.create_web_application()
    client = await aiohttp_client(web_app)

    # 1. Health
    resp = await client.get("/api/v1/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "healthy"

    # 2. Context current (initial)
    resp = await client.get("/api/v1/context/current")
    assert resp.status == 200
    ctx = await resp.json()
    assert "topic" in ctx
    assert "friction_level" in ctx

    # 3. Post event
    event_payload = {
        "source": "vscode",
        "event_type": "file_edited",
        "payload": {"file_path": "src/pointers.c"},
    }
    resp = await client.post("/api/v1/events", json=event_payload)
    assert resp.status == 201
    post_data = await resp.json()
    assert post_data["status"] == "accepted"

    # 4. Recent events
    resp = await client.get("/api/v1/events/recent")
    assert resp.status == 200
    ev_data = await resp.json()
    assert ev_data["count"] >= 1

    # 5. Active session
    resp = await client.get("/api/v1/sessions/active")
    assert resp.status == 200
    sess_data = await resp.json()
    assert sess_data["active_session"] is not None

    # 6. Analytics summary
    resp = await client.get("/api/v1/analytics/summary")
    assert resp.status == 200
    summary = await resp.json()
    assert summary["total_events"] >= 1
