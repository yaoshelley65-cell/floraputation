"""
Floraputation Backend — Supabase Database Connection Module

Provides two Supabase client instances:
- anon client: for read-only operations (respects RLS)
- service role client: for write operations (bypasses RLS)
"""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache()
def get_supabase_client() -> Client:
    """
    Create and return a cached Supabase client using the anon key.
    Used for read-only operations that respect Row Level Security.
    """
    settings = get_settings()

    logger.info(
        "Initialising Supabase anon client for project: %s",
        settings.supabase_url.split("//")[1].split(".")[0],
    )

    client: Client = create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_anon_key,
    )

    logger.info("Supabase anon client initialised successfully.")
    return client


@lru_cache()
def get_supabase_admin_client() -> Client:
    """
    Create and return a cached Supabase client using the service_role key.
    Used for write operations that bypass Row Level Security.
    WARNING: This client has full access — use only in backend services.
    """
    settings = get_settings()

    if not settings.supabase_service_role_key:
        logger.warning("No service_role key configured, falling back to anon client for writes.")
        return get_supabase_client()

    logger.info(
        "Initialising Supabase admin client for project: %s",
        settings.supabase_url.split("//")[1].split(".")[0],
    )

    client: Client = create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_role_key,
    )

    logger.info("Supabase admin client initialised successfully.")
    return client


async def verify_connection() -> dict:
    """
    Verify that the Supabase connection is working by performing a
    lightweight query against the `varieties` table.

    Returns a dict with connection status and sample metadata.
    """
    try:
        client = get_supabase_client()

        # Fetch a small sample to verify connectivity
        response = (
            client.table("varieties")
            .select("id, variety, crop, company, score", count="exact")
            .limit(5)
            .execute()
        )

        row_count = response.count if response.count is not None else len(response.data)

        return {
            "status": "connected",
            "table": "varieties",
            "sample_rows": len(response.data),
            "total_rows": row_count,
            "sample_data": response.data,
        }

    except Exception as exc:
        logger.error("Supabase connection verification failed: %s", exc)
        return {
            "status": "error",
            "detail": str(exc),
        }
