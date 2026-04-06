"""Application configuration management."""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    firecrawl_api_key: str = os.getenv("FIRECRAWL_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    app_env: str = os.getenv("APP_ENV", "development")
    app_debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    app_title: str = "Floraputation Backend API"
    app_description: str = "Backend data pipeline for the Floraputation plant variety reputation analysis platform."
    app_version: str = "0.2.0"

    # Pagination defaults
    default_page_size: int = 20
    max_page_size: int = 100

    # Scheduler settings
    scheduler_enabled: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    scrape_interval_hours: int = int(os.getenv("SCRAPE_INTERVAL_HOURS", "24"))
    max_varieties_per_batch: int = int(os.getenv("MAX_VARIETIES_PER_BATCH", "10"))

    # Rate limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
