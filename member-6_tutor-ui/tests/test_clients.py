import pytest
from unittest.mock import AsyncMock, MagicMock
from tutor_ui.clients.core_client import CoreClient
from tutor_ui.clients.ai_client import AIClient

class MockContextManager:
    def __init__(self, response):
        self.response = response
    async def __aenter__(self):
        return self.response
    async def __aexit__(self, exc_type, exc, tb):
        pass

@pytest.mark.asyncio
async def test_core_client_get_context():
    mock_session = MagicMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"subject": "Test", "topic": "Test Topic"}
    
    mock_session.get.return_value = MockContextManager(mock_response)
    
    client = CoreClient(mock_session, "http://test")
    data = await client.get_context()
    
    assert data["subject"] == "Test"
    mock_session.get.assert_called_once()

@pytest.mark.asyncio
async def test_ai_client_get_recommendations():
    mock_session = MagicMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"recommendations": [{"title": "Rec 1"}]}
    
    mock_session.get.return_value = MockContextManager(mock_response)
    
    client = AIClient(mock_session, "http://test")
    data = await client.get_recommendations("ctx_1")
    
    assert len(data) == 1
    assert data[0]["title"] == "Rec 1"
