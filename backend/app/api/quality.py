"""
Quality filter API endpoints for Floraputation.

Provides endpoints to test and preview the comment quality filter
before running full analysis.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.database import get_supabase_admin_client
from app.core.logging import get_logger
from app.analysis.quality_filter import (
    filter_comments,
    calculate_relevance_score,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/quality", tags=["Quality Filter"])


class FilterPreviewRequest(BaseModel):
    """Request to preview quality filter results for a variety."""
    variety_query: str = Field(..., description="Variety query to filter comments for")
    variety_context: str = Field("", description="Context for relevance scoring, e.g. 'Petunia Galaxy'")
    min_relevance: float = Field(0.1, ge=0.0, le=1.0, description="Minimum relevance score")
    min_length: int = Field(15, ge=1, le=500, description="Minimum comment length")
    limit: int = Field(100, ge=1, le=500, description="Max comments to fetch from DB")


class TextScoreRequest(BaseModel):
    """Request to score a single text for relevance."""
    text: str = Field(..., description="Text to score")
    variety_context: str = Field("", description="Context for relevance scoring")


@router.post("/preview")
async def preview_filter(request: FilterPreviewRequest):
    """
    Preview quality filter results without running AI analysis.

    Fetches comments from the database, applies the quality filter,
    and shows which comments would be kept vs removed.
    """
    try:
        client = get_supabase_admin_client()

        # Fetch comments
        result = (
            client.table("scraped_comments")
            .select("*")
            .ilike("variety_query", f"%{request.variety_query}%")
            .order("created_at", desc=True)
            .limit(request.limit)
            .execute()
        )

        comments = result.data or []
        if not comments:
            return {
                "variety_query": request.variety_query,
                "total_comments": 0,
                "message": "No comments found for this variety",
            }

        # Apply filter
        filtered, stats = filter_comments(
            comments,
            variety_context=request.variety_context or request.variety_query,
            min_relevance=request.min_relevance,
            min_length=request.min_length,
        )

        # Show top kept and removed for preview
        return {
            "variety_query": request.variety_query,
            "filter_stats": stats,
            "top_kept": [
                {
                    "body": c["body"][:200],
                    "relevance": c.get("_relevance_score", 0),
                    "platform": c.get("platform", ""),
                }
                for c in filtered[:10]
            ],
            "sample_removed_short": stats["removed_too_short"],
            "sample_removed_spam": stats["removed_spam"],
            "sample_removed_low_relevance": stats["removed_low_relevance"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score")
async def score_text(request: TextScoreRequest):
    """
    Score a single text for relevance to plant/garden topics.

    Useful for testing and debugging the relevance scoring algorithm.
    """
    score = calculate_relevance_score(request.text, request.variety_context)
    return {
        "text": request.text[:200],
        "variety_context": request.variety_context,
        "relevance_score": round(score, 3),
        "would_pass": score >= 0.1,
    }
