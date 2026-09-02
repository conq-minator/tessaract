import pytest
from tutor_ui.app import create_app
from tutor_ui.config import TesseractUIConfig

@pytest.fixture
def mock_config():
    return TesseractUIConfig(
        host="localhost",
        port=9702,
        core_host="localhost",
        core_port=9700,
        ai_host="localhost",
        ai_port=9701,
        shared_secret="test_secret",
        notification_cooldown_s=300,
        default_autonomy_level=2,
        theme="dark",
        log_level="DEBUG",
        desktop_mode=False,
        window_width=1280,
        window_height=850,
    )

@pytest.fixture
async def cli(aiohttp_client, mock_config):
    app = create_app(mock_config, mock_mode=True)
    return await aiohttp_client(app)
