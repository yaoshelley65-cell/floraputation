"""
Scraping API endpoints for Floraputation.

Provides endpoints to trigger scraping jobs and view accumulated data.
Search uses structured Crop + Series (optional) + Variety fields
to build precise queries and reduce token waste.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.data_store import DataStore
from app.services.scrape_orchestrator import ScrapeOrchestrator

logger = get_logger(__name__)
router = APIRouter(prefix="/api/scraping", tags=["Scraping"])


# --- Helper ---

def build_search_query(crop: str, variety: str, series: str = "") -> str:
    """
    Build a structured search query from Crop + Series + Variety.
    Series is optional. Example: "Petunia Galaxy Star" or "Begonia Nonstop Rose".
    """
    parts = [crop.strip()]
    if series and series.strip():
        parts.append(series.strip())
    parts.append(variety.strip())
    return " ".join(parts)


# --- Request/Response Models ---

class ScrapeRequest(BaseModel):
    """Request to scrape data for a variety using structured fields."""
    crop: str = Field(..., description="Crop name (required), e.g. Petunia, Begonia, Rose")
    variety: str = Field(..., description="Variety name (required), e.g. Galaxy, Nonstop, Iceberg")
    series: str = Field("", description="Series name (optional), e.g. Wave, Surfinia, Knock Out")
    platforms: Optional[List[str]] = Field(
        None,
        description="Platforms to scrape: reddit, youtube, firecrawl. Default: all available.",
    )
    max_posts: int = Field(5, ge=1, le=25, description="Max posts per platform")
    max_comments: int = Field(10, ge=1, le=50, description="Max comments per post")
    scrape_web_content: bool = Field(True, description="Whether to scrape full page content via Firecrawl")


class BatchScrapeRequest(BaseModel):
    """Request to scrape multiple varieties."""
    varieties: List[dict] = Field(
        ...,
        description="List of {crop, variety, series(optional)} dicts",
        min_length=1,
        max_length=20,
    )
    platforms: Optional[List[str]] = None
    max_posts: int = Field(3, ge=1, le=10)


# --- Endpoints ---

@router.post("/scrape")
async def scrape_variety(request: ScrapeRequest):
    """
    Trigger scraping for a single plant variety.

    Uses structured Crop + Series (optional) + Variety fields to build
    a precise search query. Data accumulates over time — running the
    same query again will add new content and skip duplicates.
    """
    query = build_search_query(request.crop, request.variety, request.series)

    try:
        orchestrator = ScrapeOrchestrator()
        result = orchestrator.scrape_variety(
            variety_name=request.variety,
            crop_name=request.crop,
            series_name=request.series,
            search_query=query,
            platforms=request.platforms,
            max_posts_per_platform=request.max_posts,
            max_comments_per_post=request.max_comments,
            firecrawl_scrape_content=request.scrape_web_content,
        )
        return result
    except Exception as e:
        logger.error("Scraping error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


class AliasScrapeRequest(BaseModel):
    """Request to scrape using all known names (primary + community aliases)."""
    variety_id: int = Field(..., description="Variety ID from the varieties table")
    platforms: Optional[List[str]] = Field(
        None, description="Platforms to scrape: reddit, youtube, firecrawl",
    )
    max_posts: int = Field(3, ge=1, le=10, description="Max posts per platform per name")
    max_comments: int = Field(5, ge=1, le=20, description="Max comments per post")


@router.post("/scrape/with-aliases")
async def scrape_with_aliases(request: AliasScrapeRequest):
    """
    Scrape a variety using ALL its known names — primary name + community aliases.

    This leverages the multilingual alias database to search across languages.
    For example, if a variety has aliases in Chinese and Japanese, this will
    search Reddit/YouTube with the English name AND search web sources with
    the Chinese/Japanese names, combining all results.
    """
    try:
        orchestrator = ScrapeOrchestrator()
        result = orchestrator.scrape_variety_with_aliases(
            variety_id=request.variety_id,
            platforms=request.platforms,
            max_posts_per_platform=request.max_posts,
            max_comments_per_post=request.max_comments,
        )
        return result
    except Exception as e:
        logger.error("Alias scraping error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Alias scraping failed: {str(e)}")


@router.post("/scrape/batch")
async def scrape_varieties_batch(request: BatchScrapeRequest):
    """
    Trigger scraping for multiple varieties in batch.
    Each item should have crop + variety (required) and series (optional).
    Limited to 20 varieties per request.
    """
    try:
        orchestrator = ScrapeOrchestrator()
        results = orchestrator.scrape_varieties_batch(
            varieties=request.varieties,
            platforms=request.platforms,
            max_posts_per_platform=request.max_posts,
        )
        return {
            "total_varieties": len(results),
            "results": results,
        }
    except Exception as e:
        logger.error("Batch scraping error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Batch scraping failed: {str(e)}")


@router.get("/stats")
async def get_scraping_stats():
    """Get overall scraping statistics from the database."""
    try:
        store = DataStore()
        stats = store.get_scrape_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comments")
async def get_comments_for_variety(
    variety: str = Query(..., description="Variety name to search for"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Get all accumulated comments for a specific variety.
    Returns comments from all platforms that mention this variety.
    """
    try:
        store = DataStore()
        comments = store.get_comments_for_variety(variety, limit=limit)
        return {
            "variety": variety,
            "total": len(comments),
            "comments": comments,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts")
async def get_posts(
    variety: str = Query("", description="Filter by variety query"),
    platform: str = Query("", description="Filter by platform"),
    limit: int = Query(50, ge=1, le=200),
):
    """Get scraped posts with optional filters."""
    try:
        store = DataStore()
        query = store.client.table("scraped_posts").select("*")

        if variety:
            query = query.ilike("variety_query", f"%{variety}%")
        if platform:
            query = query.eq("platform", platform)

        result = query.order("created_at", desc=True).limit(limit).execute()
        return {
            "total": len(result.data),
            "posts": result.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def get_scrape_jobs(
    limit: int = Query(20, ge=1, le=100),
):
    """Get recent scraping job history."""
    try:
        store = DataStore()
        result = (
            store.client.table("scrape_jobs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {
            "total": len(result.data),
            "jobs": result.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
