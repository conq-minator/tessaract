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


async def handle_get_models(request: web.Request) -> web.Response:
    """GET /api/v1/models/available"""
    import aiohttp
    available = ["smollm2:1.7b", "gemma2:2b", "gemma4:e2b", "fast-rules"]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=2.0)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                    if models:
                        available = models
    except Exception:
        pass

    current = getattr(registry.get_provider("reason"), "model_name", "smollm2:1.7b")
    return web.json_response({
        "current_model": current,
        "available_models": available,
        "recommended": "smollm2:1.7b"
    })


async def handle_select_model(request: web.Request) -> web.Response:
    """POST /api/v1/models/select"""
    try:
        data = await request.json()
    except Exception:
        data = {}

    model_name = data.get("model_name") or "smollm2:1.7b"
    new_model = registry.set_reason_model(model_name)
    return web.json_response({
        "status": "success",
        "current_model": new_model,
        "message": f"Active AI reasoning model switched to {new_model}"
    })


def setup_model_routes(app: web.Application):
    app.router.add_get("/api/v1/models/status", handle_model_status)
    app.router.add_get("/api/v1/models/available", handle_get_models)
    app.router.add_post("/api/v1/models/select", handle_select_model)
    app.router.add_post("/api/v1/models/benchmark", handle_run_benchmark)
