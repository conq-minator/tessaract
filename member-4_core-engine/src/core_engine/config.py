"""
Configuration management for Tesseract Core Engine.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load local .env if present
load_dotenv()


@dataclass
class CoreConfig:
    # Server configuration
    host: str = field(default_factory=lambda: os.getenv("TESSERACT_CORE_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("TESSERACT_CORE_PORT", "9700")))
    shared_secret: str = field(default_factory=lambda: os.getenv("TESSERACT_SHARED_SECRET", ""))

    # AI Layer (Member 5)
    ai_host: str = field(default_factory=lambda: os.getenv("TESSERACT_AI_HOST", "localhost"))
    ai_port: int = field(default_factory=lambda: int(os.getenv("TESSERACT_AI_PORT", "9701")))

    # Event Processing
    dedup_window_ms: int = field(
        default_factory=lambda: int(os.getenv("TESSERACT_DEDUP_WINDOW_MS", "2000"))
    )
    session_idle_timeout_s: int = field(
        default_factory=lambda: int(os.getenv("TESSERACT_SESSION_IDLE_TIMEOUT_S", "300"))
    )
    episode_gap_timeout_s: int = field(
        default_factory=lambda: int(os.getenv("TESSERACT_EPISODE_GAP_TIMEOUT_S", "1800"))
    )

    # Stuck Detection & Friction
    friction_threshold_low: float = field(
        default_factory=lambda: float(os.getenv("TESSERACT_FRICTION_THRESHOLD_LOW", "0.3"))
    )
    friction_threshold_medium: float = field(
        default_factory=lambda: float(os.getenv("TESSERACT_FRICTION_THRESHOLD_MEDIUM", "0.5"))
    )
    friction_threshold_high: float = field(
        default_factory=lambda: float(os.getenv("TESSERACT_FRICTION_THRESHOLD_HIGH", "0.7"))
    )
    friction_decay_rate: float = field(
        default_factory=lambda: float(os.getenv("TESSERACT_FRICTION_DECAY_RATE", "0.95"))
    )

    # Data Retention
    raw_event_retention_days: int = field(
        default_factory=lambda: int(os.getenv("TESSERACT_RAW_EVENT_RETENTION_DAYS", "30"))
    )
    structured_event_retention_days: int = field(
        default_factory=lambda: int(os.getenv("TESSERACT_STRUCTURED_EVENT_RETENTION_DAYS", "90"))
    )

    # Database
    db_path_raw: str = field(
        default_factory=lambda: os.getenv("TESSERACT_DB_PATH", "~/.tesseract/data/core.db")
    )

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("TESSERACT_LOG_LEVEL", "DEBUG"))

    @property
    def db_path(self) -> Path:
        resolved = Path(os.path.expanduser(self.db_path_raw)).resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return resolved

    @property
    def ai_base_url(self) -> str:
        return f"http://{self.ai_host}:{self.ai_port}/api/v1"


def get_config() -> CoreConfig:
    return CoreConfig()
