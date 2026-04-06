"""
Analysis API endpoints for Floraputation.

Provides endpoints to trigger AI reputation analysis and view results.
Search uses structured Crop + Series (optional) + Variety fields.
"""

from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.reputation_service import ReputationService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


def build_search_query(crop: str, variety: str, series: str = "") -> str:
    """Build a structured search query from Crop + Series + Variety."""
    parts = [crop.strip()]
    if series and series.strip():
        parts.append(series.strip())
    parts.append(variety.strip())
    return " ".join(parts)


# --- Request Models ---

class AnalyzeRequest(BaseModel):
    """Request to analyze a variety's reputation."""
    crop: str = Field(..., description="Crop name (required), e.g. Petunia, Begonia")
    variety: str = Field(..., description="Variety name (required), e.g. Galaxy, Nonstop")
    series: str = Field("", description="Series name (optional), e.g. Wave, Surfinia")
    max_comments: int = Field(
        30, ge=1, le=100,
        description="Max comments to analyze (more = better accuracy but higher cost)",
    )
    generate_report: bool = Field(
        True, description="Whether to generate a full reputation report"
    )


class FullPipelineRequest(BaseModel):
    """Request to run the full pipeline: scrape + analyze."""
    crop: str = Field(..., description="Crop name (required)")
    variety: str = Field(..., description="Variety name (required)")
    series: str = Field("", description="Series name (optional)")
    platforms: Optional[List[str]] = Field(
        None, description="Platforms to scrape (reddit, youtube, firecrawl)"
    )
    max_posts: int = Field(3, ge=1, le=10, description="Max posts per platform to scrape")
    max_comments_to_analyze: int = Field(
        30, ge=1, le=100, description="Max comments to analyze with AI"
    )


# --- Endpoints ---

@router.post("/analyze")
async def analyze_variety(request: AnalyzeRequest):
    """
    Run AI reputation analysis on accumulated data for a variety.

    Uses structured Crop + Series + Variety fields.
    If no data exists, run /api/scraping/scrape first.
    """
    query = build_search_query(request.crop, request.variety, request.series)

    try:
        service = ReputationService()
        result = service.analyze_variety(
            variety_name=request.variety,
            crop_name=request.crop,
            series_name=request.series,
            search_query=query,
            max_comments=request.max_comments,
            generate_report=request.generate_report,
        )
        return result
    except Exception as e:
        logger.error("Analysis error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/full-pipeline")
async def full_pipeline(request: FullPipelineRequest):
    """
    Run the complete pipeline: scrape data from platforms, then analyze with AI.

    Uses structured Crop + Series + Variety fields.
    1. Scrapes Reddit, YouTube, and web for the variety
    2. Stores all data in the database (accumulates over time)
    3. Runs AI sentiment analysis on the collected comments
    4. Generates a comprehensive reputation report
    """
    from app.services.scrape_orchestrator import ScrapeOrchestrator

    query = build_search_query(request.crop, request.variety, request.series)

    try:
        # Step 1: Scrape
        logger.info("Full pipeline: scraping '%s'...", query)
        orchestrator = ScrapeOrchestrator()
        scrape_result = orchestrator.scrape_variety(
            variety_name=request.variety,
            crop_name=request.crop,
            series_name=request.series,
            search_query=query,
            platforms=request.platforms,
            max_posts_per_platform=request.max_posts,
        )

        # Step 2: Analyze
        logger.info("Full pipeline: analyzing '%s'...", query)
        service = ReputationService()
        analysis_result = service.analyze_variety(
            variety_name=request.variety,
            crop_name=request.crop,
            series_name=request.series,
            search_query=query,
            max_comments=request.max_comments_to_analyze,
            generate_report=True,
        )

        return {
            "crop": request.crop,
            "series": request.series,
            "variety": request.variety,
            "query": query,
            "pipeline_status": "completed",
            "scraping": scrape_result,
            "analysis": analysis_result,
        }

    except Exception as e:
        logger.error("Full pipeline error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


@router.get("/history")
async def get_analysis_history(
    variety: str = Query("", description="Filter by variety name"),
    limit: int = Query(20, ge=1, le=100),
):
    """Get previous analysis results."""
    try:
        service = ReputationService()
        results = service.get_analysis_history(variety, limit)
        return {
            "total": len(results),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
