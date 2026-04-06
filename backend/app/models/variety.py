"""Pydantic models for plant variety data."""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class VarietyBase(BaseModel):
    """Base variety model with common fields."""
    variety: Optional[str] = None
    crop: Optional[str] = None
    series: Optional[str] = None
    company: Optional[str] = None
    source_url: Optional[str] = None
    score: Optional[float] = None
    consumer: Optional[float] = None
    grower: Optional[float] = None
    retailer: Optional[float] = None
    trend: Optional[float] = None
    positive: Optional[float] = None
    neutral: Optional[float] = None
    negative: Optional[float] = None
    confidence: Optional[float] = None
    mentions: Optional[str] = None
    mentions_raw: Optional[int] = None
    cg_gap: Optional[float] = None
    decision: Optional[str] = None
    opportunity: Optional[str] = None
    tags: Optional[list] = None
    created_at: Optional[str] = None
    original_series: Optional[str] = None
    original_variety: Optional[str] = None


class VarietyResponse(VarietyBase):
    """Variety response model with id."""
    id: int

    class Config:
        from_attributes = True


class VarietyListResponse(BaseModel):
    """Paginated list response for varieties."""
    data: List[VarietyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class VarietySearchParams(BaseModel):
    """Search and filter parameters for varieties."""
    query: Optional[str] = Field(None, description="Search term for variety, crop, series, or company")
    crop: Optional[str] = Field(None, description="Filter by crop type")
    company: Optional[str] = Field(None, description="Filter by company")
    decision: Optional[str] = Field(None, description="Filter by decision category")
    min_score: Optional[float] = Field(None, description="Minimum score filter")
    max_score: Optional[float] = Field(None, description="Maximum score filter")
    sort_by: Optional[str] = Field("score", description="Field to sort by")
    sort_order: Optional[str] = Field("desc", description="Sort order: asc or desc")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


# ========== Day 4: Write operation models ==========

class VarietyCreate(BaseModel):
    """Model for creating a new variety. Requires at least variety name and crop."""
    variety: str = Field(..., min_length=1, max_length=500, description="Variety name (required)")
    crop: str = Field(..., min_length=1, max_length=200, description="Crop type (required)")
    series: Optional[str] = Field(None, max_length=200, description="Series name")
    company: Optional[str] = Field(None, max_length=200, description="Company name")
    source_url: Optional[str] = Field(None, description="Source URL")
    score: Optional[float] = Field(None, ge=0, le=100, description="Overall reputation score (0-100)")
    consumer: Optional[float] = Field(None, ge=0, le=100, description="Consumer score (0-100)")
    grower: Optional[float] = Field(None, ge=0, le=100, description="Grower score (0-100)")
    retailer: Optional[float] = Field(None, ge=0, le=100, description="Retailer score (0-100)")
    trend: Optional[float] = Field(None, description="Trend value")
    positive: Optional[float] = Field(None, ge=0, le=100, description="Positive sentiment percentage")
    neutral: Optional[float] = Field(None, ge=0, le=100, description="Neutral sentiment percentage")
    negative: Optional[float] = Field(None, ge=0, le=100, description="Negative sentiment percentage")
    confidence: Optional[float] = Field(None, ge=0, le=100, description="Confidence score")
    mentions: Optional[str] = Field(None, description="Formatted mentions count (e.g., '36.7K')")
    mentions_raw: Optional[int] = Field(None, ge=0, description="Raw mentions count")
    cg_gap: Optional[float] = Field(None, description="Consumer-Grower gap")
    decision: Optional[str] = Field(None, description="Decision category (e.g., push, phase_out, raise_price, elite_only)")
    opportunity: Optional[str] = Field(None, description="Opportunity type")
    tags: Optional[list] = Field(None, description="Tags list")
    original_series: Optional[str] = Field(None, description="Original series name")
    original_variety: Optional[str] = Field(None, description="Original variety name")

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v):
        if v is not None:
            valid_decisions = ["push", "phase_out", "raise_price", "elite_only", "monitor", "maintain"]
            if v.lower() not in valid_decisions:
                raise ValueError(f"Decision must be one of: {', '.join(valid_decisions)}")
            return v.lower()
        return v


class VarietyUpdate(BaseModel):
    """Model for updating an existing variety. All fields are optional."""
    variety: Optional[str] = Field(None, min_length=1, max_length=500, description="Variety name")
    crop: Optional[str] = Field(None, min_length=1, max_length=200, description="Crop type")
    series: Optional[str] = Field(None, max_length=200, description="Series name")
    company: Optional[str] = Field(None, max_length=200, description="Company name")
    source_url: Optional[str] = Field(None, description="Source URL")
    score: Optional[float] = Field(None, ge=0, le=100, description="Overall reputation score (0-100)")
    consumer: Optional[float] = Field(None, ge=0, le=100, description="Consumer score (0-100)")
    grower: Optional[float] = Field(None, ge=0, le=100, description="Grower score (0-100)")
    retailer: Optional[float] = Field(None, ge=0, le=100, description="Retailer score (0-100)")
    trend: Optional[float] = Field(None, description="Trend value")
    positive: Optional[float] = Field(None, ge=0, le=100, description="Positive sentiment percentage")
    neutral: Optional[float] = Field(None, ge=0, le=100, description="Neutral sentiment percentage")
    negative: Optional[float] = Field(None, ge=0, le=100, description="Negative sentiment percentage")
    confidence: Optional[float] = Field(None, ge=0, le=100, description="Confidence score")
    mentions: Optional[str] = Field(None, description="Formatted mentions count")
    mentions_raw: Optional[int] = Field(None, ge=0, description="Raw mentions count")
    cg_gap: Optional[float] = Field(None, description="Consumer-Grower gap")
    decision: Optional[str] = Field(None, description="Decision category")
    opportunity: Optional[str] = Field(None, description="Opportunity type")
    tags: Optional[list] = Field(None, description="Tags list")
    original_series: Optional[str] = Field(None, description="Original series name")
    original_variety: Optional[str] = Field(None, description="Original variety name")

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v):
        if v is not None:
            valid_decisions = ["push", "phase_out", "raise_price", "elite_only", "monitor", "maintain"]
            if v.lower() not in valid_decisions:
                raise ValueError(f"Decision must be one of: {', '.join(valid_decisions)}")
            return v.lower()
        return v


class VarietyDeleteResponse(BaseModel):
    """Response model for delete operation."""
    message: str
    deleted_id: int


class VarietyBatchDeleteRequest(BaseModel):
    """Request model for batch delete operation."""
    ids: List[int] = Field(..., min_length=1, max_length=50, description="List of variety IDs to delete (max 50)")
