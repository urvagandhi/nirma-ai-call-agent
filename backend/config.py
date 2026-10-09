"""
Application Configuration Module — Pydantic Settings & Environment Management.

This module loads, validates, and manages all runtime configuration parameters
for the Nirma University AI Call Agent. It enforces externalization of all
carrier secrets, database credentials, AI model endpoints, and institutional domain
bindings via environment variables, strictly adhering to the Twelve-Factor App methodology.

Upstream dependencies:
    - python-dotenv / environment variables (.env)
Downstream dependencies:
    - backend.database.session
    - backend.telephony.plivo_adapter
    - backend.ai_pipeline.*
    - backend.scheduler.*
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application configuration schema loaded from environment variables.

    Attributes:
        app_name: Human-readable service name.
        app_env: Deployment environment ('development', 'staging', 'production').
        debug: Flag enabling verbose diagnostic logging and OpenAPI documentation.
        log_level: Logging severity threshold ('DEBUG', 'INFO', 'WARNING', 'ERROR').
        base_url: Fully qualified institutional domain URL (e.g., 'https://calls.nirmauni.ac.in').
        port: Listening port for the ASGI server.
        allowed_origins: Comma-separated or list of allowed CORS origins.
        database_url: Asynchronous PostgreSQL DSN using asyncpg driver.
        sync_database_url: Synchronous PostgreSQL DSN using psycopg driver for Celery.
        redis_url: Redis DSN for cache, session state, and Celery broker.
        celery_broker_url: Redis broker DSN for Celery tasks.
        celery_result_backend: Redis backend DSN for task execution results.
        plivo_auth_id: Plivo account authentication ID.
        plivo_auth_token: Plivo cryptographic authentication token.
        plivo_caller_id: Registered Indian DID phone number in E.164 format (+91...).
        ollama_base_url: Base endpoint URL for local Ollama LLM inference.
        ollama_model: Tagged model identifier for local LLM inference.
        indic_conformer_model_path: Filesystem path to IndicConformer ASR model checkpoint.
        indic_f5_model_path: Filesystem path to IndicF5 TTS model checkpoint.
        sarvam_api_key: Secret API key for Sarvam AI cloud STT fallback.
        groq_api_key: Secret API key for Groq Cloud LLM fallback.
        jwt_secret_key: Cryptographic symmetric key for JWT signing.
        jwt_algorithm: Hashing algorithm for JWT tokens (default: 'HS256').
        access_token_expire_minutes: Expiration lifetime for JWT access tokens.
        refresh_token_expire_days: Expiration lifetime for JWT refresh tokens.
        audio_cache_dir: Filesystem directory used for caching synthesized TTS audio files.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --------------------------------------------------------------------------
    # Application & Core Runtime
    # --------------------------------------------------------------------------
    app_name: str = Field(default="Nirma AI Call Agent", description="Application service name")
    app_env: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Standard logging level")

    # --------------------------------------------------------------------------
    # Institutional Domain & Networking
    # --------------------------------------------------------------------------
    base_url: str = Field(
        default="https://calls.nirmauni.ac.in",
        description="Institutional domain for reverse proxy and webhook callbacks",
    )
    port: int = Field(default=8000, description="ASGI listening port")
    allowed_origins: str = Field(
        default="http://localhost:3000,https://calls.nirmauni.ac.in",
        description="Comma-separated CORS allowed origins",
    )

    # --------------------------------------------------------------------------
    # Database Configuration (PostgreSQL 15)
    # --------------------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@postgres:5432/ai_calls",
        description="Asynchronous PostgreSQL connection string (asyncpg)",
    )
    sync_database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@postgres:5432/ai_calls",
        description="Synchronous PostgreSQL connection string for Celery workers (psycopg)",
    )

    # --------------------------------------------------------------------------
    # Cache & Task Broker (Redis 7)
    # --------------------------------------------------------------------------
    redis_url: str = Field(
        default="redis://redis:6379/0",
        description="Redis connection URL for caching and state management",
    )
    celery_broker_url: str = Field(
        default="redis://redis:6379/0",
        description="Celery message broker URL",
    )
    celery_result_backend: str = Field(
        default="redis://redis:6379/1",
        description="Celery result backend URL",
    )

    # --------------------------------------------------------------------------
    # Telephony Provider (Plivo)
    # --------------------------------------------------------------------------
    plivo_auth_id: str = Field(default="", description="Plivo Authentication ID")
    plivo_auth_token: str = Field(default="", description="Plivo Authentication Token")
    plivo_caller_id: str = Field(
        default="+917900000000",
        description="Registered E.164 Caller ID matching carrier credentials",
    )

    # --------------------------------------------------------------------------
    # AI Pipeline — Local Infrastructure
    # --------------------------------------------------------------------------
    ollama_base_url: str = Field(
        default="http://ollama:11434",
        description="Base URL for local Ollama server container",
    )
    ollama_model: str = Field(
        default="qwen3:14b",
        description="Model checkpoint name on local Ollama service",
    )
    indic_conformer_model_path: str = Field(
        default="/models/indicconformer.nemo",
        description="Local path to IndicConformer ASR model file",
    )
    indic_f5_model_path: str = Field(
        default="/models/indicf5.pt",
        description="Local path to IndicF5 TTS model checkpoint",
    )

    # --------------------------------------------------------------------------
    # AI Pipeline — Cloud Fallbacks
    # --------------------------------------------------------------------------
    sarvam_api_key: str = Field(default="", description="API key for Sarvam AI cloud STT fallback")
    groq_api_key: str = Field(default="", description="API key for Groq cloud LLM fallback")

    # --------------------------------------------------------------------------
    # Security & JWT Tokens
    # --------------------------------------------------------------------------
    jwt_secret_key: str = Field(
        default="super-secret-key-change-in-production-environment-64-hex",
        description="Cryptographic symmetric key for JWT signing",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT token signing algorithm")
    access_token_expire_minutes: int = Field(default=1440, description="Access token TTL in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token TTL in days")

    # --------------------------------------------------------------------------
    # Static Assets & Audio Cache
    # --------------------------------------------------------------------------
    audio_cache_dir: str = Field(
        default="/app/audio_cache",
        description="Directory for caching synthesized TTS audio files",
    )

    @field_validator("base_url")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        """Ensures base_url does not end with a trailing slash for uniform URL building."""
        return v.rstrip("/")

    @property
    def cors_origins(self) -> List[str]:
        """
        Parses comma-separated allowed origins into a sanitized list of strings.

        Returns:
            List[str]: Parsed and trimmed origin strings for CORS middleware.
        """
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    def build_webhook_url(self, endpoint_path: str) -> str:
        """
        Dynamically constructs an absolute public webhook callback URL.

        Ensures carrier webhooks are always bound to the university's institutional
        domain without hardcoding localhost or static IP addresses.

        Args:
            endpoint_path: Relative URL path (e.g. '/webhook/plivo/answer').

        Returns:
            str: Fully qualified HTTPS URL.
        """
        clean_path = endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"
        return f"{self.base_url}{clean_path}"


# Global singleton instance for settings
settings = Settings()
