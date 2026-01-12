"""Application configuration using Pydantic Settings"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .secrets import create_secret_provider


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "LLM MCP Hub"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")

    # Session
    session_ttl: int = Field(default=3600, description="Session TTL in seconds (default: 1 hour)")

    # Claude Provider
    claude_oauth_token: str | None = Field(default=None, description="Claude OAuth token")
    claude_default_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Default Claude model",
    )

    # Gemini Provider
    gemini_auth_path: str | None = Field(default=None, description="Gemini OAuth credentials file path")
    gemini_default_model: str = Field(
        default="gemini-2.5-pro",
        description="Default Gemini model",
    )

    # Timeouts
    provider_timeout: float = Field(default=120.0, description="Provider timeout in seconds")

    def model_post_init(self, __context) -> None:
        """Load secrets after initialization"""
        secret_provider = create_secret_provider()

        # Load Claude OAuth token from secrets if not set
        if not self.claude_oauth_token:
            token = secret_provider.get("CLAUDE_CODE_OAUTH_TOKEN")
            if token:
                object.__setattr__(self, "claude_oauth_token", token)

        # Load Gemini auth path from secrets if not set
        if not self.gemini_auth_path:
            path = secret_provider.get("GEMINI_AUTH_PATH")
            if path:
                object.__setattr__(self, "gemini_auth_path", path)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
