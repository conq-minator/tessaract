"""Tutor and pedagogical assistance endpoints."""

from aiohttp import web
from src.tutor.hints import generate_progressive_assistance
from src.tutor.explanations import generate_explanation
from src.tutor.roadmaps import generate_adaptive_roadmap


async def handle_hint(request: web.Request) -> web.Response:
    """POST /api/v1/tutor/hint"""
    data = await request.json()
    topic = data.get("topic", "")
    level = int(data.get("level", 1))
    context = data.get("context")
    code = data.get("code") or ""
    error = data.get("error") or ""
    file_path = data.get("file_path") or ""
    friction = float(data.get("friction_score", 0.5))

    if not topic:
        return web.json_response({"error": "missing_parameter", "message": "'topic' is required"}, status=400)

    res = await generate_progressive_assistance(
        topic=topic,
        level=level,
        context=context,
        friction_score=friction,
        code=code,
        error=error,
        file_path=file_path,
    )
    return web.json_response(res)


async def handle_explain(request: web.Request) -> web.Response:
    """POST /api/v1/tutor/explain"""
    data = await request.json()
    concept = data.get("concept", "")
    user_level = data.get("user_level", "beginner")
    context = data.get("context")

    if not concept:
        return web.json_response({"error": "missing_parameter", "message": "'concept' is required"}, status=400)

    res = await generate_explanation(concept=concept, user_level=user_level, context=context)
    return web.json_response(res)


async def handle_practice(request: web.Request) -> web.Response:
    """POST /api/v1/tutor/practice"""
    data = await request.json()
    topic = data.get("topic", "")
    context = data.get("context")

    if not topic:
        return web.json_response({"error": "missing_parameter", "message": "'topic' is required"}, status=400)

    res = await generate_progressive_assistance(topic=topic, level=4, context=context)
    return web.json_response(res)


async def handle_roadmap(request: web.Request) -> web.Response:
    """POST /api/v1/tutor/roadmap"""
    data = await request.json()
    subject = data.get("subject", "C Programming")
    target_goal = data.get("target_goal")
    available_time = data.get("available_time", "1_hour_per_day")

    res = await generate_adaptive_roadmap(
        subject=subject, target_goal=target_goal, available_time_per_day=available_time
    )
    return web.json_response(res)


async def handle_ask(request: web.Request) -> web.Response:
    """POST /api/v1/tutor/ask"""
    from src.tutor.explanations import answer_user_question
    data = await request.json()
    question = data.get("question", "")
    topic = data.get("topic", "general")
    error = data.get("error", "")
    code = data.get("code", "")
    file_path = data.get("file_path", "")
    history = data.get("history", [])

    if not question:
        return web.json_response({"error": "missing_parameter", "message": "'question' is required"}, status=400)

    res = await answer_user_question(
        question=question, topic=topic, error=error, code=code, file_path=file_path, history=history
    )
    return web.json_response(res)


async def handle_explain_error(request: web.Request) -> web.Response:
    """POST /api/v1/tutor/explain-error"""
    from src.tutor.explanations import explain_runtime_error
    data = await request.json()
    topic = data.get("topic", "general")
    error = data.get("error", "")
    code = data.get("code", "")
    file_path = data.get("file_path", "")

    res = await explain_runtime_error(
        topic=topic, error=error, code=code, file_path=file_path
    )
    return web.json_response(res)


async def handle_chat(request: web.Request) -> web.Response:
    """POST /api/v1/tutor/chat"""
    from src.tutor.explanations import chat_with_tutor
    data = await request.json()
    message = data.get("message", "")
    model_name = data.get("model", None)
    image_base64 = data.get("image", None)
    history = data.get("history", [])

    if not message and not image_base64:
        return web.json_response({"error": "missing_parameter", "message": "'message' or 'image' is required"}, status=400)

    res = await chat_with_tutor(
        message=message,
        model_name=model_name,
        image_base64=image_base64,
        history=history,
    )
    return web.json_response(res)


def setup_tutor_routes(app: web.Application):
    app.router.add_post("/api/v1/tutor/hint", handle_hint)
    app.router.add_post("/api/v1/tutor/explain", handle_explain)
    app.router.add_post("/api/v1/tutor/explain-error", handle_explain_error)
    app.router.add_post("/api/v1/tutor/ask", handle_ask)
    app.router.add_post("/api/v1/tutor/chat", handle_chat)
    app.router.add_post("/api/v1/tutor/practice", handle_practice)
    app.router.add_post("/api/v1/tutor/roadmap", handle_roadmap)


