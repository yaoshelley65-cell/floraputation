"""
Scheduler service for Floraputation.

Provides automated periodic scraping and analysis for tracked varieties.
Uses APScheduler for background job scheduling.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from app.core.config import get_settings
from app.core.database import get_supabase_admin_client
from app.core.logging import get_logger
from app.services.scrape_orchestrator import ScrapeOrchestrator
from app.services.reputation_service import ReputationService

logger = get_logger(__name__)
settings = get_settings()


class SchedulerService:
    """Manages automated scraping and analysis jobs."""

    def __init__(self):
        self.client = get_supabase_admin_client()
        self.orchestrator = ScrapeOrchestrator()
        self.reputation = ReputationService()

    def get_varieties_to_scrape(self, limit: int = 10) -> list:
        """
        Select varieties that need scraping based on:
        1. Never been scraped before (no matching scrape_jobs)
        2. Not scraped recently (oldest first)

        Returns list of dicts with crop, variety, series info.
        """
        try:
            # Get recently scraped variety queries (last 24h)
            cutoff = (datetime.utcnow() - timedelta(hours=settings.scrape_interval_hours)).isoformat()
            recent_jobs = (
                self.client.table("scrape_jobs")
                .select("variety_query")
                .gte("created_at", cutoff)
                .execute()
            )
            recently_scraped = {j["variety_query"] for j in (recent_jobs.data or [])}

            # Get varieties from the DB
            result = (
                self.client.table("varieties")
                .select("id, variety, crop, score")
                .order("score", desc=False)  # Lowest score first (may need update)
                .limit(limit * 3)  # Fetch extra to filter
                .execute()
            )

            candidates = []
            for v in result.data or []:
                crop = v.get("crop", "")
                variety = v.get("variety", "")
                if not crop or not variety:
                    continue

                # Build query to check if recently scraped
                query = f"{crop} {variety}"
                if query not in recently_scraped:
                    candidates.append({
                        "id": v["id"],
                        "crop": crop,
                        "variety": variety,
                        "series": "",
                        "current_score": v.get("score", 0),
                    })

                if len(candidates) >= limit:
                    break

            return candidates

        except Exception as e:
            logger.error("Error getting varieties to scrape: %s", str(e))
            return []

    def run_auto_scrape(self, max_varieties: int = None) -> dict:
        """
        Run automated scraping for varieties that need updating.

        Selects varieties that haven't been scraped recently,
        scrapes them, and runs AI analysis.
        """
        if max_varieties is None:
            max_varieties = settings.max_varieties_per_batch

        logger.info("Starting auto-scrape for up to %d varieties...", max_varieties)

        varieties = self.get_varieties_to_scrape(limit=max_varieties)
        logger.info("Found %d varieties to scrape", len(varieties))

        results = []
        for v in varieties:
            try:
                logger.info("Auto-scraping: %s %s", v["crop"], v["variety"])

                # Scrape
                scrape_result = self.orchestrator.scrape_variety(
                    variety_name=v["variety"],
                    crop_name=v["crop"],
                    platforms=["reddit", "youtube"],  # Skip firecrawl to save credits
                    max_posts_per_platform=3,
                    max_comments_per_post=5,
                )

                # Analyze
                analysis_result = self.reputation.analyze_variety(
                    variety_name=v["variety"],
                    crop_name=v["crop"],
                    max_comments=15,
                    generate_report=True,
                )

                results.append({
                    "variety": v["variety"],
                    "crop": v["crop"],
                    "status": "completed",
                    "posts_found": scrape_result["totals"]["posts"],
                    "comments_found": scrape_result["totals"]["comments"],
                    "new_score": analysis_result.get("report", {}).get("reputation_score"),
                    "old_score": v["current_score"],
                })

            except Exception as e:
                logger.error("Auto-scrape failed for %s: %s", v["variety"], str(e))
                results.append({
                    "variety": v["variety"],
                    "crop": v["crop"],
                    "status": "failed",
                    "error": str(e),
                })

        summary = {
            "total_varieties": len(varieties),
            "completed": sum(1 for r in results if r["status"] == "completed"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Auto-scrape complete: %d/%d succeeded",
            summary["completed"],
            summary["total_varieties"],
        )

        return summary

    def run_incremental_scrape(self, variety_name: str, crop_name: str, series_name: str = "") -> dict:
        """
        Run incremental scraping — only fetch new content since last scrape.

        Checks the last scrape time and only fetches newer posts.
        """
        parts = [crop_name.strip()]
        if series_name and series_name.strip():
            parts.append(series_name.strip())
        parts.append(variety_name.strip())
        query = " ".join(parts)

        # Check last scrape time
        try:
            last_job = (
                self.client.table("scrape_jobs")
                .select("created_at")
                .eq("variety_query", query)
                .eq("status", "completed")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            last_scrape = None
            if last_job.data:
                last_scrape = last_job.data[0]["created_at"]

            logger.info(
                "Incremental scrape for '%s', last scraped: %s",
                query, last_scrape or "never",
            )

        except Exception:
            last_scrape = None

        # Run scrape (the dedup mechanism in DataStore handles incremental naturally)
        scrape_result = self.orchestrator.scrape_variety(
            variety_name=variety_name,
            crop_name=crop_name,
            series_name=series_name,
            search_query=query,
            max_posts_per_platform=5,
            max_comments_per_post=10,
        )

        return {
            "query": query,
            "last_scrape": last_scrape,
            "is_incremental": last_scrape is not None,
            "scrape_result": scrape_result,
        }
