import json
import asyncio
from aiohttp import web
from tutor_ui.services.assistance import AssistanceService
from tutor_ui.services.recommendation import RecommendationService
from tutor_ui.services.notification import NotificationManager

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
    """SSE endpoint for real-time notifications to the browser."""
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
            # Wait for the next event in the queue
            msg = await queue.get()
            
            if msg.get("type") == "_shutdown":
                queue.task_done()
                break
                
            # Format as Server-Sent Events standard
            data_str = json.dumps(msg)
            event_payload = f"data: {data_str}\n\n"
            
            await response.write(event_payload.encode('utf-8'))
            queue.task_done()
    except (ConnectionResetError, asyncio.CancelledError):
        pass
    except Exception as e:
        request.app.logger.error(f"SSE error: {e}")
    finally:
        nm.unregister_client(queue)
        
    return response

def setup_api_routes(app: web.Application) -> None:
    app.router.add_get('/api/context', get_context)
    app.router.add_get('/api/friction', get_friction)
    app.router.add_get('/api/episodes', get_episodes)
    app.router.add_get('/api/session', get_session)
    app.router.add_get('/api/knowledge-graph', get_knowledge_graph)
    app.router.add_get('/api/recommendations', get_recommendations)
    app.router.add_get('/api/stream', stream_events)
