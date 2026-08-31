"""
Tests for WebSocket EventServer, AlertStreamManager, and AIClient.
"""

from pathlib import Path

import aiohttp
import pytest

from core_engine.ai_client import AIClient
from core_engine.app import CoreEngineApp
from core_engine.config import CoreConfig
from core_engine.models import AlertMessage


@pytest.fixture
def app_server(tmp_path: Path):
    db_file = tmp_path / "test_ws_app.db"
    config = CoreConfig(
        db_path_raw=str(db_file),
        shared_secret="test_secret_123",
    )
    app = CoreEngineApp(config=config, mock_ai=True)
    return app


async def test_websocket_sensor_ingestion_and_auth(aiohttp_client, app_server):
    web_app = app_server.create_web_application()
    client = await aiohttp_client(web_app)

    # 1. Reject unauthorized sensor connection
    with pytest.raises(aiohttp.WSServerHandshakeError) as exc_info:
        await client.ws_connect("/events")
    assert exc_info.value.status == 401

    # 2. Connect with valid Bearer auth
    ws = await client.ws_connect(
        "/events",
        headers={"Authorization": "Bearer test_secret_123"},
    )
    assert not ws.closed
    welcome = await ws.receive_json()
    assert welcome["status"] == "connected"

    # 3. Send valid event
    test_event = {
        "source": "vscode",
        "event_type": "diagnostic_error",
        "payload": {"error_message": "Undefined reference to main"},
    }
    await ws.send_json(test_event)
    ack = await ws.receive_json()
    assert ack["status"] == "ack"
    assert "event_id" in ack

    await ws.close()


async def test_websocket_alert_streaming(aiohttp_client, app_server):
    web_app = app_server.create_web_application()
    client = await aiohttp_client(web_app)

    # Connect UI client to /alerts
    ws = await client.ws_connect("/alerts")
    assert not ws.closed
    welcome = await ws.receive_json()
    assert welcome["alert_type"] == "connected"

    # Broadcast an alert
    alert = AlertMessage(
        alert_type="stuck_detected",
        payload={"topic": "pointers", "friction_score": 0.85, "level": "high"},
    )
    await app_server.alert_stream.broadcast_alert(alert)

    # Verify message received by UI client
    received = await ws.receive_json()
    assert received["alert_type"] == "stuck_detected"
    assert received["payload"]["friction_score"] == 0.85

    await ws.close()


async def test_ai_client_mock_mode():
    client = AIClient(mock_mode=True)
    intent_resp = await client.classify_intent({"event_type": "search"})
    assert intent_resp["intent"] == "learning"

    summary_resp = await client.summarize_episode({"topic": "pointers"})
    assert "pointers" in summary_resp

    kg_resp = await client.update_knowledge_graph({"topic": "pointers", "outcome": "resolved"})
    assert kg_resp is True

    await client.close()
