"""Configuration management for Member 5 (AI & Knowledge Layer)."""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Locate member directories and load .env from multiple potential locations
MEMBER_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = MEMBER_DIR.parent

# Load from member-5 .env, member-4 .env, or root .env
for env_candidate in [MEMBER_DIR / ".env", ROOT_DIR / "member-4_core-engine" / ".env", ROOT_DIR / ".env"]:
    if env_candidate.exists():
        load_dotenv(env_candidate, override=False)


def resolve_gemini_api_key() -> str:
    """Resolve Gemini API key from environment or any configured .env file."""
    key = os.getenv("TESSERACT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    if not key:
        for env_candidate in [MEMBER_DIR / ".env", ROOT_DIR / "member-4_core-engine" / ".env", ROOT_DIR / ".env"]:
            if env_candidate.exists():
                load_dotenv(env_candidate, override=True)
                key = os.getenv("TESSERACT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
                if key:
                    break
    return key.strip()


class Settings(BaseModel):
    # Server Binding
    ai_host: str = Field(default_factory=lambda: os.getenv("TESSERACT_AI_HOST", "127.0.0.1"))
    ai_port: int = Field(default_factory=lambda: int(os.getenv("TESSERACT_AI_PORT", "9701")))
    shared_secret: str = Field(default_factory=lambda: os.getenv("TESSERACT_SHARED_SECRET", ""))

    # Ollama Local Runtime
    ollama_host: str = Field(default_factory=lambda: os.getenv("TESSERACT_OLLAMA_HOST", "127.0.0.1"))
    ollama_port: int = Field(default_factory=lambda: int(os.getenv("TESSERACT_OLLAMA_PORT", "11434")))
    model_idle_timeout_s: int = Field(
        default_factory=lambda: int(os.getenv("TESSERACT_MODEL_IDLE_TIMEOUT_S", "300"))
    )

    # Model Assignments
    model_classify: str = Field(
        default_factory=lambda: os.getenv("TESSERACT_MODEL_CLASSIFY", "smollm2:1.7b")
    )
    model_reason: str = Field(
        default_factory=lambda: os.getenv("TESSERACT_MODEL_REASON", "gemma4:e2b")
    )
    model_vision: str = Field(
        default_factory=lambda: os.getenv("TESSERACT_MODEL_VISION", "gemma4:e2b")
    )
    model_embed: str = Field(
        default_factory=lambda: os.getenv("TESSERACT_MODEL_EMBED", "all-minilm:l6-v2")
    )

    # Cloud Fallback & Video Search Grounding
    cloud_enabled: bool = Field(
        default_factory=lambda: (
            os.getenv("TESSERACT_CLOUD_ENABLED", "false").lower() == "true"
            or bool(resolve_gemini_api_key())
        )
    )
    gemini_api_key: str = Field(default_factory=resolve_gemini_api_key)
    openai_api_key: str = Field(default_factory=lambda: os.getenv("TESSERACT_OPENAI_API_KEY", ""))

    # Database & Storage Paths
    kg_db_path: Path = Field(
        default_factory=lambda: MEMBER_DIR / os.getenv("TESSERACT_KG_DB_PATH", "data/knowledge.db")
    )
    vector_db_path: Path = Field(
        default_factory=lambda: MEMBER_DIR / os.getenv("TESSERACT_VECTOR_DB_PATH", "data/vectors.db")
    )
    benchmark_dir: Path = Field(
        default_factory=lambda: MEMBER_DIR / os.getenv("TESSERACT_BENCHMARK_DIR", "data/benchmarks")
    )

    # Logging
    log_level: str = Field(default_factory=lambda: os.getenv("TESSERACT_LOG_LEVEL", "INFO"))

    @property
    def ollama_base_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}"


# Global settings singleton
settings = Settings()

# Ensure data directories exist
settings.kg_db_path.parent.mkdir(parents=True, exist_ok=True)
settings.vector_db_path.parent.mkdir(parents=True, exist_ok=True)
settings.benchmark_dir.mkdir(parents=True, exist_ok=True)
