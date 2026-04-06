"""
Background scheduler for Floraputation.

Uses APScheduler to run automated scraping and analysis jobs
at configurable intervals. Integrates with the existing
SchedulerService for the actual work.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Global scheduler state
_scheduler = None
_scheduler_lock = threading.Lock()
_job_history: list = []
MAX_HISTORY = 50


def _record_job(job_type: str, status: str, details: dict = None):
    """Record a job execution in history."""
    entry = {
        "job_type": job_type,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {},
    }
    _job_history.append(entry)
    if len(_job_history) > MAX_HISTORY:
        _job_history.pop(0)


def _run_auto_scrape_job():
    """Background job: auto-scrape varieties that need updating."""
    logger.info("Background auto-scrape job triggered")
    try:
        from app.services.scheduler import SchedulerService
        service = SchedulerService()
        result = service.run_auto_scrape(
            max_varieties=settings.max_varieties_per_batch
        )
        _record_job("auto_scrape", "completed", {
            "total": result.get("total_varieties", 0),
            "completed": result.get("completed", 0),
            "failed": result.get("failed", 0),
        })
        logger.info(
            "Background auto-scrape completed: %d/%d succeeded",
            result.get("completed", 0),
            result.get("total_varieties", 0),
        )
    except Exception as e:
        logger.error("Background auto-scrape failed: %s", str(e))
        _record_job("auto_scrape", "failed", {"error": str(e)})


def start_background_scheduler() -> bool:
    """
    Start the background scheduler if enabled in settings.

    Returns True if scheduler was started, False if disabled or already running.
    """
    global _scheduler

    if not settings.scheduler_enabled:
        logger.info("Background scheduler is disabled in settings")
        return False

    with _scheduler_lock:
        if _scheduler is not None:
            logger.info("Background scheduler is already running")
            return False

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger

            _scheduler = BackgroundScheduler(
                job_defaults={
                    "coalesce": True,  # Combine missed runs into one
                    "max_instances": 1,  # Only one instance at a time
                    "misfire_grace_time": 3600,  # 1 hour grace for missed jobs
                }
            )

            # Add auto-scrape job
            interval_hours = settings.scrape_interval_hours
            _scheduler.add_job(
                _run_auto_scrape_job,
                trigger=IntervalTrigger(hours=interval_hours),
                id="auto_scrape",
                name=f"Auto-scrape every {interval_hours}h",
                replace_existing=True,
            )

            _scheduler.start()
            logger.info(
                "Background scheduler started: auto-scrape every %d hours",
                interval_hours,
            )
            _record_job("scheduler_start", "completed", {
                "interval_hours": interval_hours,
            })
            return True

        except ImportError:
            logger.warning(
                "APScheduler not installed. Background scheduling disabled. "
                "Install with: pip install apscheduler"
            )
            return False
        except Exception as e:
            logger.error("Failed to start background scheduler: %s", str(e))
            _scheduler = None
            return False


def stop_background_scheduler() -> bool:
    """Stop the background scheduler."""
    global _scheduler

    with _scheduler_lock:
        if _scheduler is None:
            return False

        try:
            _scheduler.shutdown(wait=False)
            _scheduler = None
            logger.info("Background scheduler stopped")
            _record_job("scheduler_stop", "completed")
            return True
        except Exception as e:
            logger.error("Error stopping scheduler: %s", str(e))
            return False


def get_scheduler_status() -> dict:
    """Get the current scheduler status and job history."""
    status = {
        "enabled": settings.scheduler_enabled,
        "running": _scheduler is not None,
        "interval_hours": settings.scrape_interval_hours,
        "max_varieties_per_batch": settings.max_varieties_per_batch,
        "jobs": [],
        "recent_history": _job_history[-10:],
    }

    if _scheduler is not None:
        try:
            for job in _scheduler.get_jobs():
                status["jobs"].append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": str(job.next_run_time) if job.next_run_time else None,
                })
        except Exception:
            pass

    return status
