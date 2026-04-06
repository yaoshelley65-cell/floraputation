"""
Data accumulation service for Floraputation.

Stores scraped posts and comments into Supabase tables, ensuring
data accumulates over time with deduplication by source_id.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from app.core.database import get_supabase_admin_client
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataStore:
    """Manages persistent storage of scraped data in Supabase."""

    def __init__(self):
        """Initialize with Supabase admin client."""
        self.client = get_supabase_admin_client()

    def ensure_tables_exist(self):
        """
        Verify that the required tables exist in Supabase.
        Tables should be created via Supabase dashboard or migration:

        - scraped_posts: stores posts/videos found during scraping
        - scraped_comments: stores comments/content from posts
        - scrape_jobs: tracks scraping job history
        """
        # Check if tables exist by attempting a query
        tables_status = {}
        for table in ["scraped_posts", "scraped_comments", "scrape_jobs"]:
            try:
                self.client.table(table).select("id", count="exact").limit(0).execute()
                tables_status[table] = "exists"
            except Exception:
                tables_status[table] = "missing"

        logger.info("Tables status: %s", tables_status)
        return tables_status

    def store_post(self, post_data: dict) -> Optional[dict]:
        """
        Store a scraped post, deduplicating by platform + source_id.

        Args:
            post_data: Dict with post fields (from ScrapedPost.to_dict())

        Returns:
            The stored/existing record, or None on error
        """
        try:
            platform = post_data.get("platform", "")
            source_id = post_data.get("source_id", "")

            if not platform or not source_id:
                logger.warning("Post missing platform or source_id, skipping")
                return None

            # Check if already exists
            existing = (
                self.client.table("scraped_posts")
                .select("id")
                .eq("platform", platform)
                .eq("source_id", source_id)
                .execute()
            )

            if existing.data:
                logger.debug(
                    "Post already exists: %s/%s",
                    platform,
                    source_id,
                )
                # Update with latest data
                result = (
                    self.client.table("scraped_posts")
                    .update({
                        "score": post_data.get("score", 0),
                        "num_comments": post_data.get("num_comments", 0),
                        "updated_at": datetime.utcnow().isoformat(),
                    })
                    .eq("platform", platform)
                    .eq("source_id", source_id)
                    .execute()
                )
                return result.data[0] if result.data else None

            # Insert new post
            insert_data = {
                "platform": platform,
                "source_id": source_id,
                "title": post_data.get("title", "")[:500],
                "body": (post_data.get("body", "") or "")[:5000],
                "author": post_data.get("author", ""),
                "score": post_data.get("score", 0),
                "num_comments": post_data.get("num_comments", 0),
                "url": post_data.get("url", ""),
                "subreddit": post_data.get("subreddit", ""),
                "variety_query": post_data.get("variety_query", ""),
                "extra": post_data.get("extra", {}),
                "created_at": post_data.get("created_at") or datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = (
                self.client.table("scraped_posts")
                .insert(insert_data)
                .execute()
            )

            if result.data:
                logger.info(
                    "Stored new post: %s/%s - '%s'",
                    platform,
                    source_id,
                    post_data.get("title", "")[:50],
                )
                return result.data[0]

            return None

        except Exception as e:
            logger.error("Error storing post: %s", str(e))
            return None

    def store_comment(self, comment_data: dict) -> Optional[dict]:
        """
        Store a scraped comment, deduplicating by platform + source_id.

        Args:
            comment_data: Dict with comment fields (from ScrapedComment.to_dict())

        Returns:
            The stored/existing record, or None on error
        """
        try:
            platform = comment_data.get("platform", "")
            source_id = comment_data.get("source_id", "")

            if not platform or not source_id:
                logger.warning("Comment missing platform or source_id, skipping")
                return None

            # Check if already exists
            existing = (
                self.client.table("scraped_comments")
                .select("id")
                .eq("platform", platform)
                .eq("source_id", source_id)
                .execute()
            )

            if existing.data:
                logger.debug(
                    "Comment already exists: %s/%s",
                    platform,
                    source_id,
                )
                return existing.data[0]

            # Insert new comment
            insert_data = {
                "platform": platform,
                "source_id": source_id,
                "post_id": comment_data.get("post_id", ""),
                "post_title": (comment_data.get("post_title", "") or "")[:500],
                "author": comment_data.get("author", ""),
                "body": (comment_data.get("body", "") or "")[:10000],
                "score": comment_data.get("score", 0),
                "url": comment_data.get("url", ""),
                "variety_query": comment_data.get("variety_query", ""),
                "extra": comment_data.get("extra", {}),
                "created_at": comment_data.get("created_at") or datetime.utcnow().isoformat(),
            }

            result = (
                self.client.table("scraped_comments")
                .insert(insert_data)
                .execute()
            )

            if result.data:
                logger.debug(
                    "Stored new comment: %s/%s",
                    platform,
                    source_id,
                )
                return result.data[0]

            return None

        except Exception as e:
            logger.error("Error storing comment: %s", str(e))
            return None

    def store_posts_batch(self, posts: List[dict]) -> dict:
        """
        Store multiple posts with deduplication.

        Returns:
            dict with 'new', 'updated', 'errors' counts
        """
        stats = {"new": 0, "updated": 0, "errors": 0}

        for post in posts:
            result = self.store_post(post)
            if result:
                stats["new"] += 1  # Simplified; could track new vs updated
            else:
                stats["errors"] += 1

        logger.info(
            "Batch stored %d posts: %d new, %d errors",
            len(posts),
            stats["new"],
            stats["errors"],
        )
        return stats

    def store_comments_batch(self, comments: List[dict]) -> dict:
        """
        Store multiple comments with deduplication.

        Returns:
            dict with 'new', 'skipped', 'errors' counts
        """
        stats = {"new": 0, "skipped": 0, "errors": 0}

        for comment in comments:
            result = self.store_comment(comment)
            if result:
                stats["new"] += 1
            else:
                stats["errors"] += 1

        logger.info(
            "Batch stored %d comments: %d new, %d errors",
            len(comments),
            stats["new"],
            stats["errors"],
        )
        return stats

    def log_scrape_job(
        self,
        variety_query: str,
        platform: str,
        posts_found: int,
        comments_found: int,
        status: str = "completed",
        error_message: str = "",
    ) -> Optional[dict]:
        """
        Log a scraping job for tracking and auditing.

        Args:
            variety_query: The search query used
            platform: Platform scraped (reddit, youtube, firecrawl)
            posts_found: Number of posts found
            comments_found: Number of comments collected
            status: Job status (completed, failed, partial)
            error_message: Error details if failed

        Returns:
            The job record or None
        """
        try:
            job_data = {
                "variety_query": variety_query,
                "platform": platform,
                "posts_found": posts_found,
                "comments_found": comments_found,
                "status": status,
                "error_message": error_message,
                "created_at": datetime.utcnow().isoformat(),
            }

            result = (
                self.client.table("scrape_jobs")
                .insert(job_data)
                .execute()
            )

            return result.data[0] if result.data else None

        except Exception as e:
            logger.error("Error logging scrape job: %s", str(e))
            return None

    def get_scrape_stats(self) -> dict:
        """
        Get overall scraping statistics.

        Returns:
            dict with counts of posts, comments, and jobs
        """
        stats = {}
        try:
            for table in ["scraped_posts", "scraped_comments", "scrape_jobs"]:
                result = (
                    self.client.table(table)
                    .select("id", count="exact")
                    .limit(0)
                    .execute()
                )
                stats[table] = result.count if result.count is not None else 0
        except Exception as e:
            logger.error("Error getting scrape stats: %s", str(e))
            stats["error"] = str(e)

        return stats

    def get_comments_for_variety(
        self, variety_query: str, limit: int = 100
    ) -> List[dict]:
        """
        Retrieve all accumulated comments for a specific variety.

        Args:
            variety_query: The variety name/query to search for
            limit: Maximum comments to return

        Returns:
            List of comment dicts
        """
        try:
            result = (
                self.client.table("scraped_comments")
                .select("*")
                .ilike("variety_query", f"%{variety_query}%")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("Error fetching comments for '%s': %s", variety_query, str(e))
            return []
