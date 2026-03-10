"""
config.py — Application configuration using Pydantic Settings.

Reads environment variables from .env file and exposes them as typed settings.
Phase 3: Added voice TTS, fulfillment webhook, rate limiting, and upload dir settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All secrets must be provided via .env file or system environment.
    Never hardcode values here.
    """

    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/pharmaagent"

    # JWT Security
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # Google Gemini AI
    gemini_api_key: str = ""

    # LangSmith Observability
    langchain_tracing_v2: str = "true"
    # Accepts LANGSMITH_API_KEY (preferred) or LANGCHAIN_API_KEY (legacy)
    langchain_api_key: str = Field(default="", alias="LANGSMITH_API_KEY", validation_alias="LANGSMITH_API_KEY")
    langchain_project: str = "pharmaagent-ai"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Phase 2: File uploads
    upload_dir: str = "uploads"

    # ---------------------------------------------------------------------------
    # Phase 3: Voice / TTS
    # ---------------------------------------------------------------------------
    # Use browser STT/TTS by default (no server-side processing).
    # Set USE_SERVER_TTS=true to enable backend TTS fallback.
    # TTS_PROVIDER: 'none' | 'gemini' — (ElevenLabs etc. can be added here)
    use_server_tts: bool = False
    tts_provider: str = "none"

    # Allow audio file uploads to backend (for browsers without SpeechRecognition)
    allow_server_audio_upload: bool = True

    # ---------------------------------------------------------------------------
    # Phase 3: Webhook Fulfillment
    # ---------------------------------------------------------------------------
    # Warehouse fulfillment endpoint. Use /webhook/simulate for local testing.
    # IMPORTANT: Change this to your real warehouse URL in production.
    fulfillment_webhook_url: str = "http://localhost:8000/webhook/simulate"

    # Maximum retries before marking fulfillment as failed
    webhook_max_retries: int = 5

    # Base delay in seconds for exponential backoff (actual delay = base * 2^attempt + jitter)
    webhook_base_delay: float = 1.0

    # ---------------------------------------------------------------------------
    # Phase 3: Rate Limiting
    # ---------------------------------------------------------------------------
    # Max agent chat requests per user per minute (0 = disabled)
    rate_limit_per_minute: int = 30

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "populate_by_name": True,
    }

    def get_cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached Settings instance.

    Uses lru_cache so settings are loaded only once at startup.
    """
    return Settings()


# Shared settings instance
settings = get_settings()

