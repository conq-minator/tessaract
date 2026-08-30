"""Member 5 REST API Application Server."""

import sys
import logging
from aiohttp import web

from src.config import settings
from src.api.middleware import auth_and_error_middleware
from src.api.routes.inference import setup_inference_routes
from src.api.routes.knowledge import setup_knowledge_routes
from src.api.routes.tutor import setup_tutor_routes
from src.api.routes.models import setup_model_routes
from src.models.registry import registry

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tesseract.ai_knowledge")


async def handle_health(request: web.Request) -> web.Response:
    """Simple health check endpoint."""
    return web.json_response({
        "status": "healthy",
        "service": "member-5_ai-knowledge",
        "version": "1.0.0",
        "port": settings.ai_port,
    })


def create_app(mock_mode: bool = False) -> web.Application:
    """Build and configure the aiohttp application."""
    if mock_mode:
        registry.set_mock_mode(True)

    app = web.Application(middlewares=[auth_and_error_middleware])

    # Core health & index routes
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)

    # Attach domain routes
    setup_inference_routes(app)
    setup_knowledge_routes(app)
    setup_tutor_routes(app)
    setup_model_routes(app)

    return app


def run_server():
    """Entrypoint to launch server."""
    use_mock = "--mock-models" in sys.argv or "-m" in sys.argv
    app = create_app(mock_mode=use_mock)
    logger.info("Starting Tesseract Member 5 (AI & Knowledge) on %s:%s", settings.ai_host, settings.ai_port)
    logger.info("Mock Mode: %s", use_mock)
    web.run_app(app, host=settings.ai_host, port=settings.ai_port)


if __name__ == "__main__":
    run_server()
