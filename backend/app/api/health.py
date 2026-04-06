"""Health check API endpoint."""

from fastapi import APIRouter

from app.core.database import verify_connection

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
async def health_check():
    """Check the health of the API and database connection."""
    db_status = await verify_connection()
    return {
        "status": "healthy" if db_status["status"] == "connected" else "unhealthy",
        "database": db_status,
    }
