"""Varieties API endpoints — Day 3 & 4: Read + Write operations."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.database import get_supabase_client, get_supabase_admin_client
from app.core.logging import get_logger
from app.models.variety import (
    VarietyResponse,
    VarietyListResponse,
    VarietyCreate,
    VarietyUpdate,
    VarietyDeleteResponse,
    VarietyBatchDeleteRequest,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/varieties", tags=["Varieties"])


# ==================== READ ENDPOINTS (Day 3) ====================

@router.get(
    "",
    response_model=VarietyListResponse,
    summary="Get varieties list",
    description="Retrieve a paginated list of plant varieties with optional search and filtering.",
)
def list_varieties(
    query: Optional[str] = Query(None, description="Search term for variety, crop, series, or company"),
    crop: Optional[str] = Query(None, description="Filter by crop type"),
    company: Optional[str] = Query(None, description="Filter by company"),
    decision: Optional[str] = Query(None, description="Filter by decision category (e.g., Push & Scale, Phase Out)"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum score filter"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum score filter"),
    sort_by: str = Query("score", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Get a paginated list of varieties with search and filter support."""
    try:
        client = get_supabase_admin_client()

        # Build the query
        db_query = client.table("varieties").select("*", count="exact")

        # Apply text search (ilike for case-insensitive partial match)
        if query:
            search_term = f"%{query}%"
            db_query = db_query.or_(
                f"variety.ilike.{search_term},"
                f"crop.ilike.{search_term},"
                f"series.ilike.{search_term},"
                f"company.ilike.{search_term}"
            )

        # Apply filters
        if crop:
            db_query = db_query.ilike("crop", f"%{crop}%")
        if company:
            db_query = db_query.ilike("company", f"%{company}%")
        if decision:
            db_query = db_query.ilike("decision", f"%{decision}%")
        if min_score is not None:
            db_query = db_query.gte("score", min_score)
        if max_score is not None:
            db_query = db_query.lte("score", max_score)

        # Apply sorting
        valid_sort_fields = [
            "id", "variety", "crop", "series", "company", "score",
            "consumer", "grower", "retailer", "trend", "positive",
            "neutral", "negative", "confidence", "mentions", "mentions_raw",
            "cg_gap", "created_at",
        ]
        if sort_by not in valid_sort_fields:
            sort_by = "score"

        desc = sort_order.lower() == "desc"
        db_query = db_query.order(sort_by, desc=desc)

        # Apply pagination
        offset = (page - 1) * page_size
        db_query = db_query.range(offset, offset + page_size - 1)

        # Execute query
        response = db_query.execute()

        total = response.count if response.count is not None else 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        logger.info(
            "Listed varieties: page=%d, page_size=%d, total=%d, query=%s",
            page, page_size, total, query,
        )

        return VarietyListResponse(
            data=response.data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error("Error listing varieties: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch varieties: {str(e)}")


@router.get(
    "/crops/list",
    summary="Get all crop types",
    description="Retrieve a list of all unique crop types in the database.",
)
def list_crops():
    """Get all unique crop types for filtering."""
    try:
        client = get_supabase_admin_client()

        response = (
            client.table("varieties")
            .select("crop")
            .execute()
        )

        # Extract unique crop values
        crops = sorted(set(
            row["crop"] for row in response.data
            if row.get("crop")
        ))

        return {"crops": crops, "total": len(crops)}

    except Exception as e:
        logger.error("Error listing crops: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch crops: {str(e)}")


@router.get(
    "/companies/list",
    summary="Get all companies",
    description="Retrieve a list of all unique companies in the database.",
)
def list_companies():
    """Get all unique companies for filtering."""
    try:
        client = get_supabase_admin_client()

        response = (
            client.table("varieties")
            .select("company")
            .execute()
        )

        # Extract unique company values
        companies = sorted(set(
            row["company"] for row in response.data
            if row.get("company")
        ))

        return {"companies": companies, "total": len(companies)}

    except Exception as e:
        logger.error("Error listing companies: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch companies: {str(e)}")


@router.get(
    "/{variety_id}",
    response_model=VarietyResponse,
    summary="Get variety details",
    description="Retrieve detailed information for a specific plant variety by ID.",
)
def get_variety(variety_id: int):
    """Get a single variety by its ID."""
    try:
        client = get_supabase_admin_client()

        response = (
            client.table("varieties")
            .select("*")
            .eq("id", variety_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Variety with id {variety_id} not found.",
            )

        logger.info("Retrieved variety id=%d", variety_id)
        return response.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching variety %d: %s", variety_id, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch variety: {str(e)}")


# ==================== WRITE ENDPOINTS (Day 4) ====================

@router.post(
    "",
    response_model=VarietyResponse,
    status_code=201,
    summary="Create a new variety",
    description="Add a new plant variety to the database. Requires at least variety name and crop type.",
)
def create_variety(variety_data: VarietyCreate):
    """Create a new variety entry in the database."""
    try:
        client = get_supabase_admin_client()

        # Convert to dict, exclude None values to let DB handle defaults
        insert_data = variety_data.model_dump(exclude_none=True)

        # Convert float scores to int for DB compatibility
        int_fields = ["score", "consumer", "grower", "retailer", "positive",
                      "neutral", "negative", "confidence", "mentions_raw"]
        for field in int_fields:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = int(insert_data[field])

        logger.info("Creating variety: %s (%s)", insert_data.get("variety"), insert_data.get("crop"))

        response = (
            client.table("varieties")
            .insert(insert_data)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create variety: no data returned.")

        created = response.data[0]
        logger.info("Created variety id=%d: %s", created["id"], created["variety"])
        return created

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating variety: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create variety: {str(e)}")


@router.put(
    "/{variety_id}",
    response_model=VarietyResponse,
    summary="Update a variety",
    description="Update an existing plant variety. Only provided fields will be updated.",
)
def update_variety(variety_id: int, variety_data: VarietyUpdate):
    """Update an existing variety by ID."""
    try:
        client = get_supabase_admin_client()

        # Check if variety exists
        existing = (
            client.table("varieties")
            .select("id")
            .eq("id", variety_id)
            .execute()
        )

        if not existing.data:
            raise HTTPException(
                status_code=404,
                detail=f"Variety with id {variety_id} not found.",
            )

        # Only update fields that were explicitly provided (not None)
        update_data = variety_data.model_dump(exclude_none=True)

        # Convert float scores to int for DB compatibility
        int_fields = ["score", "consumer", "grower", "retailer", "positive",
                      "neutral", "negative", "confidence", "mentions_raw"]
        for field in int_fields:
            if field in update_data and update_data[field] is not None:
                update_data[field] = int(update_data[field])

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update.",
            )

        logger.info("Updating variety id=%d with fields: %s", variety_id, list(update_data.keys()))

        response = (
            client.table("varieties")
            .update(update_data)
            .eq("id", variety_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update variety: no data returned.")

        updated = response.data[0]
        logger.info("Updated variety id=%d: %s", updated["id"], updated["variety"])
        return updated

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating variety %d: %s", variety_id, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update variety: {str(e)}")


@router.patch(
    "/{variety_id}",
    response_model=VarietyResponse,
    summary="Partially update a variety",
    description="Partially update an existing plant variety. Same as PUT but semantically for partial updates.",
)
def patch_variety(variety_id: int, variety_data: VarietyUpdate):
    """Partially update an existing variety by ID (alias for PUT)."""
    return update_variety(variety_id, variety_data)


@router.delete(
    "/{variety_id}",
    response_model=VarietyDeleteResponse,
    summary="Delete a variety",
    description="Delete a plant variety from the database by its ID.",
)
def delete_variety(variety_id: int):
    """Delete a variety by ID."""
    try:
        client = get_supabase_admin_client()

        # Check if variety exists
        existing = (
            client.table("varieties")
            .select("id, variety")
            .eq("id", variety_id)
            .execute()
        )

        if not existing.data:
            raise HTTPException(
                status_code=404,
                detail=f"Variety with id {variety_id} not found.",
            )

        variety_name = existing.data[0].get("variety", "unknown")

        # Delete the variety
        response = (
            client.table("varieties")
            .delete()
            .eq("id", variety_id)
            .execute()
        )

        logger.info("Deleted variety id=%d: %s", variety_id, variety_name)

        return VarietyDeleteResponse(
            message=f"Variety '{variety_name}' (id={variety_id}) deleted successfully.",
            deleted_id=variety_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting variety %d: %s", variety_id, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete variety: {str(e)}")


@router.post(
    "/batch-delete",
    summary="Batch delete varieties",
    description="Delete multiple varieties at once by providing a list of IDs (max 50).",
)
def batch_delete_varieties(request: VarietyBatchDeleteRequest):
    """Delete multiple varieties by their IDs."""
    try:
        client = get_supabase_admin_client()

        # Check which IDs exist
        existing = (
            client.table("varieties")
            .select("id")
            .in_("id", request.ids)
            .execute()
        )

        existing_ids = {row["id"] for row in existing.data}
        not_found_ids = [id for id in request.ids if id not in existing_ids]

        if not existing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"None of the provided IDs were found: {request.ids}",
            )

        # Delete existing varieties
        response = (
            client.table("varieties")
            .delete()
            .in_("id", list(existing_ids))
            .execute()
        )

        logger.info("Batch deleted %d varieties: %s", len(existing_ids), list(existing_ids))

        result = {
            "message": f"Successfully deleted {len(existing_ids)} varieties.",
            "deleted_ids": sorted(existing_ids),
            "deleted_count": len(existing_ids),
        }

        if not_found_ids:
            result["not_found_ids"] = not_found_ids
            result["message"] += f" {len(not_found_ids)} IDs were not found."

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error batch deleting varieties: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to batch delete varieties: {str(e)}")
