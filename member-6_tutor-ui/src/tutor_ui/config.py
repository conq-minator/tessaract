import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class TesseractUIConfig:
    host: str
    port: int
    core_host: str
    core_port: int
    ai_host: str
    ai_port: int
    shared_secret: str
    notification_cooldown_s: int
    default_autonomy_level: int
    theme: str
    log_level: str
    desktop_mode: bool
    window_width: int
    window_height: int

def load_config() -> TesseractUIConfig:
    """Load configuration from .env file and environment variables."""
    # Find .env in the env/member-6 directory relative to the package root
    # or just rely on load_dotenv to find it in current working directory.
    # We'll try a few common locations.
    
    # Try local directory
    load_dotenv()
    
    # Also try the project root env directory (assuming running from member-6_tutor-ui)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "env", "member-6", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    return TesseractUIConfig(
        host=os.getenv("TESSERACT_UI_HOST", "localhost"),
        port=int(os.getenv("TESSERACT_UI_PORT", "9702")),
        core_host=os.getenv("TESSERACT_CORE_HOST", "localhost"),
        core_port=int(os.getenv("TESSERACT_CORE_PORT", "9700")),
        ai_host=os.getenv("TESSERACT_AI_HOST", "localhost"),
        ai_port=int(os.getenv("TESSERACT_AI_PORT", "9701")),
        shared_secret=os.getenv("TESSERACT_SHARED_SECRET", ""),
        notification_cooldown_s=int(os.getenv("TESSERACT_NOTIFICATION_COOLDOWN_S", "300")),
        default_autonomy_level=int(os.getenv("TESSERACT_DEFAULT_AUTONOMY_LEVEL", "2")),
        theme=os.getenv("TESSERACT_THEME", "dark"),
        log_level=os.getenv("TESSERACT_LOG_LEVEL", "DEBUG"),
        desktop_mode=os.getenv("TESSERACT_DESKTOP_MODE", "true").lower() in ("true", "1", "yes"),
        window_width=int(os.getenv("TESSERACT_WINDOW_WIDTH", "1280")),
        window_height=int(os.getenv("TESSERACT_WINDOW_HEIGHT", "850")),
    )
