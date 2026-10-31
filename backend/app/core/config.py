"""Core configuration for Munesh AI backend."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "Munesh AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./munesh_ai.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # WhatsApp Cloud API
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v19.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "munesh_ai_verify_token"

    # LLM Configuration
    LLM_PROVIDER: str = "gemini"  # gemini | openai | claude
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # CRM
    DEFAULT_LEAD_STATUS: str = "new"

    # Memory
    MAX_MEMORY_MESSAGES: int = 10

    # Follow-up
    FOLLOW_UP_DELAY_HOURS: int = 24

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
