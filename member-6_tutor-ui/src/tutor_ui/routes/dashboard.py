import aiohttp_jinja2
from aiohttp import web

async def index(request: web.Request) -> web.Response:
    """Redirect root to overview."""
    raise web.HTTPFound('/overview')

@aiohttp_jinja2.template('pages/overview.html')
async def overview(request: web.Request) -> dict[str, str]:
    """Overview dashboard page."""
    return {"title": "Overview - Tesseract"}

@aiohttp_jinja2.template('pages/knowledge_graph.html')
async def knowledge_graph(request: web.Request) -> dict[str, str]:
    """Knowledge graph visualization page."""
    return {"title": "Knowledge Graph - Tesseract"}

@aiohttp_jinja2.template('pages/learning.html')
async def learning(request: web.Request) -> dict[str, str]:
    """Learning roadmap page."""
    return {"title": "Learning - Tesseract"}

@aiohttp_jinja2.template('pages/history.html')
async def history(request: web.Request) -> dict[str, str]:
    """History and episodes page."""
    return {"title": "History - Tesseract"}

@aiohttp_jinja2.template('pages/settings.html')
async def settings(request: web.Request) -> dict[str, str]:
    """User settings page."""
    return {"title": "Settings - Tesseract"}

@aiohttp_jinja2.template('pages/data.html')
async def data_management(request: web.Request) -> dict[str, str]:
    """Data management page."""
    return {"title": "Data - Tesseract"}

def setup_dashboard_routes(app: web.Application) -> None:
    """Configure dashboard page routes."""
    app.router.add_get('/', index)
    app.router.add_get('/overview', overview)
    app.router.add_get('/knowledge-graph', knowledge_graph)
    app.router.add_get('/learning', learning)
    app.router.add_get('/history', history)
    app.router.add_get('/settings', settings)
    app.router.add_get('/data', data_management)
