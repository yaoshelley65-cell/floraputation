"""
Reputation analysis service for Floraputation.

Orchestrates the full pipeline: fetch accumulated comments from DB,
run AI sentiment analysis, generate reputation report, store results,
and write back reputation scores to the varieties table.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.core.database import get_supabase_admin_client
from app.core.logging import get_logger
from app.analysis.sentiment import (
    analyze_comments_batch,
    generate_reputation_report,
)
from app.analysis.quality_filter import filter_comments
from app.services.data_store import DataStore

logger = get_logger(__name__)


class ReputationService:
    """Manages variety reputation analysis using accumulated scraped data."""

    def __init__(self):
        self.client = get_supabase_admin_client()
        self.store = DataStore()

    def analyze_variety(
        self,
        variety_name: str,
        crop_name: str = "",
        series_name: str = "",
        search_query: str = "",
        max_comments: int = 50,
        generate_report: bool = True,
    ) -> dict:
        """
        Run a full reputation analysis for a plant variety.

        1. Fetches accumulated comments from Supabase
        2. Runs AI sentiment analysis on each comment
        3. Generates a reputation report with insights
        4. Stores the analysis results back in the DB
        5. Writes back reputation score to the varieties table

        Args:
            variety_name: The variety name to analyze
            crop_name: Crop name for context
            series_name: Optional series name
            search_query: Pre-built search query (Crop + Series + Variety)
            max_comments: Max comments to analyze (controls API cost)
            generate_report: Whether to generate a full reputation report

        Returns:
            dict with analysis results and optional reputation report
        """
        if not search_query:
            parts = [crop_name.strip()]
            if series_name and series_name.strip():
                parts.append(series_name.strip())
            parts.append(variety_name.strip())
            search_query = " ".join(parts)

        logger.info(
            "Starting reputation analysis for '%s' (query: '%s')",
            variety_name, search_query,
        )

        # 1. Fetch accumulated comments
        comments = self._fetch_comments(search_query, variety_name, max_comments)
        logger.info("Found %d comments for '%s'", len(comments), search_query)

        if not comments:
            return {
                "variety": variety_name,
                "crop": crop_name,
                "series": series_name,
                "query": search_query,
                "status": "no_data",
                "message": f"No comments found for '{search_query}'. Run scraping first.",
                "comments_found": 0,
            }

        # 1.5. Quality filter — remove spam, short, and irrelevant comments
        variety_context = f"{crop_name} {series_name} {variety_name}".strip()
        comments, filter_stats = filter_comments(
            comments,
            variety_context=variety_context,
            min_relevance=0.05,  # Low threshold to keep most plant-related content
            min_length=15,
        )
        logger.info(
            "Quality filter: %d -> %d comments (removed %d)",
            filter_stats["total_input"],
            filter_stats["kept"],
            filter_stats["total_input"] - filter_stats["kept"],
        )

        if not comments:
            return {
                "variety": variety_name,
                "crop": crop_name,
                "series": series_name,
                "query": search_query,
                "status": "no_quality_data",
                "message": f"Found comments but none passed quality filter for '{search_query}'.",
                "filter_stats": filter_stats,
            }

        # 2. Run batch sentiment analysis
        batch_analysis = analyze_comments_batch(comments, f"{crop_name} {variety_name}")
        logger.info(
            "Analysis complete: avg_score=%.1f, distribution=%s",
            batch_analysis["average_score"],
            batch_analysis["sentiment_distribution"],
        )

        result = {
            "variety": variety_name,
            "crop": crop_name,
            "series": series_name,
            "query": search_query,
            "status": "completed",
            "filter_stats": filter_stats,
            "batch_analysis": batch_analysis,
        }

        # 3. Generate reputation report
        if generate_report:
            report = generate_reputation_report(
                variety_name, crop_name, comments, batch_analysis
            )
            result["report"] = report
            logger.info(
                "Report generated: reputation_score=%s, confidence=%s",
                report.get("reputation_score"),
                report.get("confidence"),
            )

        # 4. Store analysis results
        self._store_analysis(variety_name, crop_name, series_name, search_query, result)

        # 5. Write back score to varieties table
        reputation_score = (
            result.get("report", {}).get("reputation_score")
            or batch_analysis.get("average_score", 50)
        )
        self._writeback_score(variety_name, crop_name, series_name, reputation_score)

        return result

    def _fetch_comments(self, search_query: str, variety_name: str, limit: int) -> list:
        """Fetch accumulated comments for a variety from all platforms."""
        try:
            # Search in scraped_comments using the full query
            result = (
                self.client.table("scraped_comments")
                .select("*")
                .ilike("variety_query", f"%{search_query}%")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            comments = result.data or []

            # If not enough results with full query, also try variety name alone
            if len(comments) < limit // 2 and variety_name:
                extra = (
                    self.client.table("scraped_comments")
                    .select("*")
                    .ilike("variety_query", f"%{variety_name}%")
                    .order("created_at", desc=True)
                    .limit(limit - len(comments))
                    .execute()
                )
                existing_ids = {c["id"] for c in comments}
                for c in extra.data or []:
                    if c["id"] not in existing_ids:
                        comments.append(c)

            # Also search in scraped_posts body text for additional context
            posts = (
                self.client.table("scraped_posts")
                .select("*")
                .ilike("variety_query", f"%{search_query}%")
                .order("created_at", desc=True)
                .limit(limit // 2)
                .execute()
            )

            # Convert posts with body text to comment-like format
            for post in posts.data or []:
                if post.get("body") and len(post["body"].strip()) > 20:
                    comments.append({
                        "id": f"post_{post['id']}",
                        "source_id": post["source_id"],
                        "platform": post["platform"],
                        "body": post["body"],
                        "variety_query": post.get("variety_query", ""),
                    })

            return comments

        except Exception as e:
            logger.error("Error fetching comments: %s", str(e))
            return []

    def _store_analysis(
        self,
        variety_name: str,
        crop_name: str,
        series_name: str,
        search_query: str,
        result: dict,
    ) -> None:
        """Store analysis results in the analysis_results table."""
        try:
            report = result.get("report", {})
            batch = result.get("batch_analysis", {})

            analysis_data = {
                "variety_query": search_query,
                "crop_name": crop_name,
                "reputation_score": report.get("reputation_score", batch.get("average_score", 50)),
                "confidence": report.get("confidence", "low"),
                "sentiment_distribution": batch.get("sentiment_distribution", {}),
                "top_topics": batch.get("top_topics", []),
                "summary": report.get("summary", ""),
                "strengths": report.get("strengths", []),
                "weaknesses": report.get("weaknesses", []),
                "recommendations": report.get("recommendations", []),
                "market_position": report.get("market_position", ""),
                "trend": report.get("trend", ""),
                "comments_analyzed": batch.get("analyzed_comments", 0),
                "created_at": datetime.utcnow().isoformat(),
            }

            self.client.table("analysis_results").upsert(
                analysis_data,
                on_conflict="variety_query",
            ).execute()

            logger.info("Analysis results stored for '%s'", search_query)

        except Exception as e:
            logger.warning(
                "Could not store analysis results (table may not exist): %s",
                str(e),
            )

    def _writeback_score(
        self,
        variety_name: str,
        crop_name: str,
        series_name: str,
        reputation_score: int,
    ) -> None:
        """
        Write back the AI-generated reputation score to the varieties table.

        Matches by variety name and crop. Updates the 'score' field.
        """
        try:
            # Find matching varieties in the DB
            query = (
                self.client.table("varieties")
                .select("id, variety, crop, score")
                .ilike("variety", f"%{variety_name}%")
            )
            if crop_name:
                query = query.ilike("crop", f"%{crop_name}%")

            result = query.limit(10).execute()
            matched = result.data or []

            if not matched:
                logger.info(
                    "No matching variety found in DB for writeback: %s %s",
                    crop_name, variety_name,
                )
                return

            # Update score for all matched varieties
            updated_count = 0
            for v in matched:
                self.client.table("varieties").update({
                    "score": int(reputation_score),
                }).eq("id", v["id"]).execute()
                updated_count += 1
                logger.info(
                    "Updated score for variety id=%d '%s': %d -> %d",
                    v["id"], v["variety"], v.get("score", 0), reputation_score,
                )

            logger.info(
                "Writeback complete: updated %d varieties with score %d",
                updated_count, reputation_score,
            )

        except Exception as e:
            logger.warning("Score writeback failed: %s", str(e))

    def get_analysis_history(self, variety_name: str = "", limit: int = 20) -> list:
        """Get previous analysis results from the database."""
        try:
            query = self.client.table("analysis_results").select("*")
            if variety_name:
                query = query.ilike("variety_query", f"%{variety_name}%")
            result = query.order("created_at", desc=True).limit(limit).execute()
            return result.data or []
        except Exception as e:
            logger.warning("Could not fetch analysis history: %s", str(e))
            return []
