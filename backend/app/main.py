"""Floraputation Backend API — Main Application Entry Point."""

import time
from collections import defaultdict

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.varieties import router as varieties_router
from app.api.health import router as health_router
from app.api.scraping import router as scraping_router
from app.api.analysis import router as analysis_router
from app.api.scheduler import router as scheduler_router
from app.api.aliases import router as aliases_router
from app.api.quality import router as quality_router

settings = get_settings()

app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware — allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Simple rate limiting middleware ---
_request_counts: dict = defaultdict(list)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple in-memory rate limiter per client IP."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60  # 1 minute window
    max_requests = settings.rate_limit_per_minute

    # Clean old entries
    _request_counts[client_ip] = [
        t for t in _request_counts[client_ip] if now - t < window
    ]

    if len(_request_counts[client_ip]) >= max_requests:
        return Response(
            content='{"detail":"Rate limit exceeded. Try again later."}',
            status_code=429,
            media_type="application/json",
        )

    _request_counts[client_ip].append(now)
    response = await call_next(request)
    return response


# Register routers
app.include_router(health_router)
app.include_router(varieties_router)
app.include_router(scraping_router)
app.include_router(analysis_router)
app.include_router(scheduler_router)
app.include_router(aliases_router)
app.include_router(quality_router)


@app.get("/", tags=["Root"])
def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_title,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
