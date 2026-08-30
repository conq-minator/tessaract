"""Inference endpoints for Member 5 REST API."""

import base64
from aiohttp import web
from src.models.registry import registry


async def handle_complete(request: web.Request) -> web.Response:
    """POST /api/v1/inference/complete"""
    data = await request.json()
    prompt = data.get("prompt", "")
    if not prompt:
        return web.json_response({"error": "missing_parameter", "message": "prompt is required"}, status=400)

    task_type = data.get("task_type", "reason")
    system = data.get("system")
    max_tokens = int(data.get("max_tokens", 512))
    temperature = float(data.get("temperature", 0.2))

    result = await registry.complete(
        prompt=prompt,
        task_type=task_type,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return web.json_response(result.model_dump())


async def handle_classify(request: web.Request) -> web.Response:
    """POST /api/v1/inference/classify"""
    data = await request.json()
    text = data.get("text", "")
    labels = data.get("labels", [])
    if not text or not labels:
        return web.json_response(
            {"error": "missing_parameter", "message": "'text' and 'labels' are required"},
            status=400,
        )

    context = data.get("context")
    result = await registry.classify(text=text, labels=labels, context=context)
    return web.json_response(result.model_dump())


async def handle_embed(request: web.Request) -> web.Response:
    """POST /api/v1/inference/embed"""
    data = await request.json()
    texts = data.get("texts", [])
    if not texts:
        return web.json_response(
            {"error": "missing_parameter", "message": "'texts' array is required"},
            status=400,
        )

    result = await registry.embed(texts=texts)
    return web.json_response(result.model_dump())


async def handle_vision(request: web.Request) -> web.Response:
    """POST /api/v1/inference/vision"""
    data = await request.json()
    image_b64 = data.get("image_base64", "")
    prompt = data.get("prompt", "Describe this image.")
    if not image_b64:
        return web.json_response(
            {"error": "missing_parameter", "message": "'image_base64' is required"},
            status=400,
        )

    try:
        image_bytes = base64.b64decode(image_b64)
    except Exception:
        return web.json_response({"error": "invalid_base64", "message": "Could not decode image_base64"}, status=400)

    provider = registry.get_provider("vision")
    result = await provider.vision(image_bytes=image_bytes, prompt=prompt)
    return web.json_response(result.model_dump())


def setup_inference_routes(app: web.Application):
    app.router.add_post("/api/v1/inference/complete", handle_complete)
    app.router.add_post("/api/v1/inference/classify", handle_classify)
    app.router.add_post("/api/v1/inference/embed", handle_embed)
    app.router.add_post("/api/v1/inference/vision", handle_vision)
