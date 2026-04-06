"""
Scheduler API endpoints for Floraputation.

Provides endpoints to trigger and manage automated scraping jobs.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.scheduler import SchedulerService
from app.services.background_scheduler import (
    start_background_scheduler,
    stop_background_scheduler,
    get_scheduler_status,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/scheduler", tags=["Scheduler"])


class AutoScrapeRequest(BaseModel):
    """Request to run auto-scrape."""
    max_varieties: int = Field(
        5, ge=1, le=50,
        description="Max number of varieties to scrape in this batch",
    )


class IncrementalScrapeRequest(BaseModel):
    """Request to run incremental scrape for a specific variety."""
    crop: str = Field(..., description="Crop name (required)")
    variety: str = Field(..., description="Variety name (required)")
    series: str = Field("", description="Series name (optional)")


@router.post("/auto-scrape")
async def run_auto_scrape(request: AutoScrapeRequest):
    """
    Run automated scraping for varieties that need updating.

    Selects varieties that haven't been scraped recently (based on
    SCRAPE_INTERVAL_HOURS config), scrapes them from Reddit and YouTube,
    and runs AI analysis with score writeback.
    """
    try:
        service = SchedulerService()
        result = service.run_auto_scrape(max_varieties=request.max_varieties)
        return result
    except Exception as e:
        logger.error("Auto-scrape error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Auto-scrape failed: {str(e)}")


@router.post("/incremental-scrape")
async def run_incremental_scrape(request: IncrementalScrapeRequest):
    """
    Run incremental scraping for a specific variety.

    Only fetches new content since the last scrape. Duplicates are
    automatically skipped by the data store's dedup mechanism.
    """
    try:
        service = SchedulerService()
        result = service.run_incremental_scrape(
            variety_name=request.variety,
            crop_name=request.crop,
            series_name=request.series,
        )
        return result
    except Exception as e:
        logger.error("Incremental scrape error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Incremental scrape failed: {str(e)}")


@router.get("/status")
async def scheduler_status():
    """
    Get the background scheduler status.

    Shows whether the scheduler is running, its configuration,
    scheduled jobs, and recent execution history.
    """
    return get_scheduler_status()


@router.post("/start")
async def start_scheduler():
    """
    Start the background scheduler for automated periodic scraping.

    The scheduler will automatically scrape varieties that need updating
    at the configured interval (default: every 24 hours).
    """
    started = start_background_scheduler()
    if started:
        return {"status": "started", "message": "Background scheduler started"}
    status = get_scheduler_status()
    if status["running"]:
        return {"status": "already_running", "message": "Scheduler is already running"}
    return {"status": "disabled", "message": "Scheduler is disabled in settings"}


@router.post("/stop")
async def stop_scheduler():
    """
    Stop the background scheduler.

    Stops all automated scraping jobs. Manual scraping still works.
    """
    stopped = stop_background_scheduler()
    if stopped:
        return {"status": "stopped", "message": "Background scheduler stopped"}
    return {"status": "not_running", "message": "Scheduler was not running"}


@router.get("/candidates")
async def get_scrape_candidates(
    limit: int = Query(10, ge=1, le=50, description="Max candidates to return"),
):
    """
    Get a list of varieties that are candidates for scraping.

    Returns varieties that haven't been scraped recently, sorted by
    lowest score first (most likely to benefit from updated data).
    """
    try:
        service = SchedulerService()
        candidates = service.get_varieties_to_scrape(limit=limit)
        return {
            "total": len(candidates),
            "candidates": candidates,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
