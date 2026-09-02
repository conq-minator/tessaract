import pytest

async def test_health_check(cli):
    resp = await cli.get('/health')
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "tutor_ui"

async def test_api_context_mock(cli):
    resp = await cli.get('/api/context')
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "success"
    assert "subject" in data["data"]

async def test_api_knowledge_graph_mock(cli):
    resp = await cli.get('/api/knowledge-graph')
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "success"
    assert "nodes" in data["data"]
    assert "links" in data["data"]

@pytest.mark.parametrize("route", [
    "/overview",
    "/knowledge-graph",
    "/learning",
    "/history",
    "/settings",
    "/data"
])
async def test_dashboard_pages(cli, route):
    resp = await cli.get(route)
    assert resp.status == 200
    text = await resp.text()
    assert "<html" in text
    assert "Tesseract" in text

