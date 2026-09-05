import json
import asyncio
import logging
from aiohttp import web
from tutor_ui.services.assistance import AssistanceService
from tutor_ui.services.recommendation import RecommendationService
from tutor_ui.services.notification import NotificationManager

logger = logging.getLogger(__name__)


async def get_context(request: web.Request) -> web.Response:
    svc: AssistanceService = request.app["assistance_svc"]
    data = await svc.get_current_context()
    return web.json_response({"status": "success", "data": data})


async def get_friction(request: web.Request) -> web.Response:
    svc: AssistanceService = request.app["assistance_svc"]
    data = await svc.get_friction()
    return web.json_response({"status": "success", "data": data})


async def get_episodes(request: web.Request) -> web.Response:
    svc: AssistanceService = request.app["assistance_svc"]
    data = await svc.get_episodes()
    return web.json_response({"status": "success", "data": data})


async def get_session(request: web.Request) -> web.Response:
    svc: AssistanceService = request.app["assistance_svc"]
    data = await svc.get_session()
    return web.json_response({"status": "success", "data": data})


async def get_knowledge_graph(request: web.Request) -> web.Response:
    svc: RecommendationService = request.app["recommendation_svc"]
    data = await svc.get_knowledge_graph()
    return web.json_response({"status": "success", "data": data})


async def get_recommendations(request: web.Request) -> web.Response:
    svc: RecommendationService = request.app["recommendation_svc"]
    data = await svc.get_recommendations()
    return web.json_response({"status": "success", "data": data})


async def stream_events(request: web.Request) -> web.StreamResponse:
    """
    SSE endpoint for real-time notifications to the browser.
    Includes a 1-second keepalive heartbeat to immediately detect client disconnects
    and prevent browser HTTP/1.1 socket exhaustion.
    """
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )
    await response.prepare(request)
    
    nm: NotificationManager = request.app["notification_mgr"]
    queue = await nm.register_client()
    
    try:
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                if msg.get("type") == "_shutdown":
                    queue.task_done()
                    break
                data_str = json.dumps(msg)
                event_payload = f"data: {data_str}\n\n"
                await response.write(event_payload.encode('utf-8'))
                queue.task_done()
            except asyncio.TimeoutError:
                # 1s Keepalive heartbeat — detects closed connections immediately
                await response.write(b": keepalive\n\n")
    except (ConnectionResetError, ConnectionError, asyncio.CancelledError, Exception):
        pass
    finally:
        nm.unregister_client(queue)
        
    return response


async def get_models(request: web.Request) -> web.Response:
    import aiohttp
    url = "http://127.0.0.1:9701/api/v1/models/available"
    headers = {"Authorization": "Bearer rQUSMHvr5MVgVdCH-b8seB7UbRYeykyJYjBzaZeN2Pk"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=2.0)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return web.json_response(data)
    except Exception:
        pass
    return web.json_response({
        "current_model": "smollm2:1.7b",
        "available_models": ["smollm2:1.7b", "gemma2:2b", "gemma4:e2b", "fast-rules"],
        "recommended": "smollm2:1.7b"
    })


async def select_model(request: web.Request) -> web.Response:
    import aiohttp
    try:
        req_data = await request.json()
    except Exception:
        req_data = {}
    url = "http://127.0.0.1:9701/api/v1/models/select"
    headers = {"Authorization": "Bearer rQUSMHvr5MVgVdCH-b8seB7UbRYeykyJYjBzaZeN2Pk"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=req_data, headers=headers, timeout=aiohttp.ClientTimeout(total=3.0)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return web.json_response(data)
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)
    return web.json_response({"status": "error", "message": "Failed to reach AI service"}, status=502)


async def send_chat(request: web.Request) -> web.Response:
    import aiohttp
    try:
        req_data = await request.json()
    except Exception as e:
        logger.error("Failed to parse request JSON in send_chat: %s", e)
        return web.json_response({"error": "invalid_payload", "reply": f"Invalid request payload: {e}"}, status=400)

    url = "http://127.0.0.1:9701/api/v1/tutor/chat"
    headers = {
        "Authorization": "Bearer rQUSMHvr5MVgVdCH-b8seB7UbRYeykyJYjBzaZeN2Pk",
        "Content-Type": "application/json"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=req_data, headers=headers, timeout=aiohttp.ClientTimeout(total=150.0)) as resp:
                data = await resp.json()
                return web.json_response(data, status=resp.status)
    except Exception as e:
        logger.error("Failed to proxy chat message: %s", e)
        return web.json_response({"error": "chat_proxy_failed", "reply": f"Unable to reach AI Tutor: {e}"}, status=500)


def setup_api_routes(app: web.Application) -> None:
    app.router.add_get('/api/context', get_context)
    app.router.add_get('/api/friction', get_friction)
    app.router.add_get('/api/episodes', get_episodes)
    app.router.add_get('/api/session', get_session)
    app.router.add_get('/api/knowledge-graph', get_knowledge_graph)
    app.router.add_get('/api/recommendations', get_recommendations)
    app.router.add_get('/api/stream', stream_events)
    app.router.add_get('/api/models', get_models)
    app.router.add_post('/api/models/select', select_model)
    app.router.add_post('/api/chat', send_chat)

