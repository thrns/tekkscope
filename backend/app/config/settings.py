"""Typed, centralized application settings.

Environment variables remain the public configuration interface so existing
deployments keep working. The settings object adds validation and gives the
rest of the application one place to read runtime configuration from.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "app/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    deployment_mode: str = "development"
    supabase_url: str = ""
    supabase_api_key: str = ""
    redis_url: str = "redis://localhost:6379/0"
    searxng_url: str = "https://search.tekkscope.com"

    tekk_llm_provider: str = "gemini"
    tekk_llm_model: str = "gemini-2.0-flash"
    tekk_llm_max_tokens: int = Field(default=8000, ge=1, le=100_000)

    tekk_redis_stream_enabled: bool = True
    tekk_redis_readiness_required: bool = False
    tekk_stream_queue_size: int = Field(default=1000, ge=1, le=100_000)
    tekk_search_max_results: int = Field(default=50, ge=1, le=100)
    tekk_scrape_max_sources: int = Field(default=20, ge=1, le=100)
    tekk_scrape_timeout_seconds: float = Field(default=8.0, gt=0, le=300)

    tekk_cors_origins: str = (
        "http://localhost:3000,"
        "http://localhost:3001,"
        "https://tekkscope.com,"
        "https://www.tekkscope.com"
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.tekk_cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""

    return Settings()

