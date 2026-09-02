from aiohttp import web

async def health_check(request: web.Request) -> web.Response:
    """Simple health check endpoint."""
    return web.json_response({"status": "ok", "service": "tutor_ui"})

def setup_health_routes(app: web.Application) -> None:
    """Configure health routes."""
    app.router.add_get("/health", health_check)
