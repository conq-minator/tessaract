"""Security and error-handling middleware for the Member 5 REST API."""

import logging
from aiohttp import web
from src.config import settings

logger = logging.getLogger(__name__)


@web.middleware
async def auth_and_error_middleware(request: web.Request, handler):
    """Authenticate bearer token if configured, and handle uncaught exceptions."""
    # Health checks or root paths bypass auth
    if request.path in ["/", "/health", "/api/v1/models/status"]:
        pass
    elif settings.shared_secret:
        auth_header = request.headers.get("Authorization", "")
        expected_bearer = f"Bearer {settings.shared_secret}"
        if auth_header != expected_bearer:
            return web.json_response(
                {"error": "unauthorized", "message": "Invalid or missing Bearer token"},
                status=401,
            )

    try:
        response = await handler(request)
        return response
    except web.HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unhandled error processing request to %s", request.path)
        return web.json_response(
            {"error": "internal_error", "message": str(exc)},
            status=500,
        )
