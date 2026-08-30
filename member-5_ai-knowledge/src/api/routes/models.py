"""Model lifecycle, status, and benchmark endpoints."""

from aiohttp import web
from src.models.registry import registry
from src.benchmark.suite import BenchmarkSuite


async def handle_model_status(request: web.Request) -> web.Response:
    """GET /api/v1/models/status"""
    status = await registry.get_status()
    return web.json_response(status)


async def handle_run_benchmark(request: web.Request) -> web.Response:
    """POST /api/v1/models/benchmark"""
    try:
        data = await request.json()
    except Exception:
        data = {}

    model_name = data.get("model_name")
    suite = BenchmarkSuite(provider=registry.get_provider("reason"))
    report = await suite.run_all(model_name=model_name)
    return web.json_response(report)


def setup_model_routes(app: web.Application):
    app.router.add_get("/api/v1/models/status", handle_model_status)
    app.router.add_post("/api/v1/models/benchmark", handle_run_benchmark)
