import os
import logging
from aiohttp import web, ClientSession
import aiohttp_jinja2
import jinja2

from tutor_ui.config import TesseractUIConfig
from tutor_ui.routes.health import setup_health_routes
from tutor_ui.routes.dashboard import setup_dashboard_routes
from tutor_ui.routes.api import setup_api_routes

# Services
from tutor_ui.services.notification import NotificationManager
from tutor_ui.services.permission import PermissionGuard
from tutor_ui.clients.core_client import CoreClient
from tutor_ui.clients.ai_client import AIClient
from tutor_ui.services.assistance import AssistanceService
from tutor_ui.services.recommendation import RecommendationService
from tutor_ui.services.roadmap import RoadmapService
from tutor_ui.clients.alert_listener import AlertListener

logger = logging.getLogger(__name__)

def create_app(config: TesseractUIConfig, mock_mode: bool = False) -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application()
    
    # Store global config and mode
    app["config"] = config
    app["mock_mode"] = mock_mode
    
    # Initialize Core Services
    app["notification_mgr"] = NotificationManager()
    app["permission_guard"] = PermissionGuard()

    # Register startup and cleanup hooks
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    templates_dir = os.path.join(base_dir, "templates")
    static_dir = os.path.join(base_dir, "static")
    
    # Make sure directories exist for startup (even if empty)
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    
    # Setup Jinja2 templates
    aiohttp_jinja2.setup(
        app, 
        loader=jinja2.FileSystemLoader(templates_dir)
    )
    
    # Setup static files
    app.router.add_static('/static/', path=static_dir, name='static')
    
    logger.info("Setting up routes...")
    setup_health_routes(app)
    setup_dashboard_routes(app)
    setup_api_routes(app)
    
    return app

async def on_startup(app: web.Application):
    """Run background tasks on startup."""
    # Shared aiohttp session for our clients
    app["client_session"] = ClientSession()
    
    # Initialize Clients
    app["core_client"] = CoreClient(app["client_session"])
    app["ai_client"] = AIClient(app["client_session"])
    
    # Initialize Business Services
    app["assistance_svc"] = AssistanceService(app["core_client"], app["permission_guard"], app["mock_mode"])
    app["recommendation_svc"] = RecommendationService(app["ai_client"], app["mock_mode"])
    app["roadmap_svc"] = RoadmapService(app["ai_client"], app["mock_mode"])
    
    if not app["mock_mode"]:
        # Only start the alert listener in real mode
        cfg = app["config"]
        ws_url = f"ws://{cfg.core_host}:{cfg.core_port}/alerts"
        app["alert_listener"] = AlertListener(ws_url, app["notification_mgr"])
        await app["alert_listener"].start()
    else:
        logger.info("Mock mode enabled: AlertListener will not be started.")

async def on_cleanup(app: web.Application):
    """Cleanup resources on shutdown."""
    if "notification_mgr" in app:
        await app["notification_mgr"].shutdown()
        
    if "alert_listener" in app:
        await app["alert_listener"].stop()
        
    if "client_session" in app:
        await app["client_session"].close()
