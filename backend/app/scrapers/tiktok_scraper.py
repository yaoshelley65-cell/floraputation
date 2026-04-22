"""
TikTok scraper for Floraputation — uses Bright Data Dataset API.

This scraper uses Bright Data's TikTok Posts and TikTok Comments datasets
to perform keyword-based searches and collect post details and comments.

Graceful degradation: When BRIGHTDATA_API_KEY is not set, all methods
return empty results without raising errors.
"""

from __future__ import annotations

import os
import time
from typing import List, Optional, Dict, Any

import requests

# Try to import from local base.py if it exists (for standalone testing)
try:
    from app.core.logging import get_logger
    from app.scrapers.base import BaseScraper, ScrapedComment, ScrapedPost
except ImportError:
    import sys
    sys.path.append('/home/ubuntu')
    from base import BaseScraper, ScrapedComment, ScrapedPost

    # Mock logger if not available
    class MockLogger:
        def info(self, msg, *args): print(f"INFO: {msg % args if args else msg}")
        def warning(self, msg, *args): print(f"WARNING: {msg % args if args else msg}")
        def error(self, msg, *args): print(f"ERROR: {msg % args if args else msg}")
        def debug(self, msg, *args): print(f"DEBUG: {msg % args if args else msg}")
    
    def get_logger(name): return MockLogger()

logger = get_logger(__name__)

class TikTokScraper(BaseScraper):
    """TikTok scraper using Bright Data Dataset API."""

    platform_name = "tiktok"
    
    # Bright Data Dataset IDs
    POSTS_DATASET_ID = "gd_lu702nij2f790tmv9h"
    COMMENTS_DATASET_ID = "gd_lkf2st302ap89utw5k"
    
    BASE_URL = "https://api.brightdata.com/datasets/v3"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TikTok scraper.

        Args:
            api_key: Bright Data API Key. Defaults to BRIGHTDATA_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("BRIGHTDATA_API_KEY")
        if not self.api_key:
            logger.info("BRIGHTDATA_API_KEY not set. TikTok scraping will be skipped.")
            
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })

    def _trigger_task(self, dataset_id: str, inputs: List[Dict[str, Any]], params: Dict[str, Any] = None) -> Optional[str]:
        """Trigger an asynchronous dataset task."""
        url = f"{self.BASE_URL}/trigger"
        query_params = {"dataset_id": dataset_id, "format": "json"}
        if params:
            query_params.update(params)
            
        try:
            response = self.session.post(url, params=query_params, json=inputs, timeout=30)
            response.raise_for_status()
            data = response.json()
            snapshot_id = data.get("snapshot_id")
            logger.info("[%s] Triggered task for dataset %s, snapshot_id: %s", self.platform_name, dataset_id, snapshot_id)
            return snapshot_id
        except Exception as e:
            logger.error("[%s] Failed to trigger task: %s", self.platform_name, str(e))
            return None

    def _poll_results(self, snapshot_id: str, timeout: int = 300, interval: int = 15) -> List[Dict[str, Any]]:
        """Poll for task completion and return results."""
        progress_url = f"{self.BASE_URL}/progress/{snapshot_id}"
        snapshot_url = f"{self.BASE_URL}/snapshot/{snapshot_id}"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check progress
                resp = self.session.get(progress_url, timeout=15)
                resp.raise_for_status()
                status_data = resp.json()
                status = status_data.get("status")
                
                logger.debug("[%s] Task %s status: %s", self.platform_name, snapshot_id, status)
                
                if status == "ready":
                    # Download data
                    data_resp = self.session.get(snapshot_url, params={"format": "json"}, timeout=60)
                    data_resp.raise_for_status()
                    return data_resp.json()
                elif status in ("failed", "cancelled"):
                    logger.error("[%s] Task %s %s", self.platform_name, snapshot_id, status)
                    return []
                
                time.sleep(interval)
            except Exception as e:
                logger.warning("[%s] Error polling task %s: %s", self.platform_name, snapshot_id, str(e))
                time.sleep(interval)
                
        logger.warning("[%s] Task %s timed out after %ds", self.platform_name, snapshot_id, timeout)
        return []

    def search_posts(
        self, query: str, limit: int = 10, **kwargs
    ) -> List[ScrapedPost]:
        """
        Search TikTok posts using keywords via Bright Data.
        Returns empty list gracefully when API key is not configured.
        """
        if not self.api_key:
            return []

        # Prepare inputs for keyword search
        inputs = [{"search_keyword": query}]
        params = {
            "type": "discover_new",
            "discover_by": "keyword",
            "limit_per_input": limit
        }
        
        snapshot_id = self._trigger_task(self.POSTS_DATASET_ID, inputs, params)
        if not snapshot_id:
            return []
            
        raw_results = self._poll_results(snapshot_id)
        
        posts = []
        for item in raw_results:
            try:
                # Map Bright Data fields to ScrapedPost
                post = ScrapedPost(
                    platform="tiktok",
                    source_id=str(item.get("post_id", "")),
                    title=item.get("description", "") or f"TikTok post by {item.get('profile_username', 'unknown')}",
                    body=item.get("description", "") or "",
                    author=item.get("profile_username", ""),
                    score=int(item.get("digg_count", 0)),
                    num_comments=int(item.get("comment_count", 0)),
                    created_utc=self._parse_iso_date(item.get("create_time")),
                    url=item.get("url"),
                    variety_query=query,
                    extra={
                        "play_count": item.get("play_count"),
                        "share_count": item.get("share_count"),
                        "collect_count": item.get("collect_count"),
                        "hashtags": item.get("hashtags", []),
                        "video_url": item.get("video_url"),
                        "profile_followers": item.get("profile_followers"),
                    }
                )
                posts.append(post)
            except Exception as e:
                logger.warning("[%s] Error parsing post item: %s", self.platform_name, str(e))
                
        return posts

    def get_comments(
        self, post_id: str, limit: int = 20, **kwargs
    ) -> List[ScrapedComment]:
        """
        Get comments for a specific TikTok post via Bright Data.
        Returns empty list gracefully when API key is not configured.
        """
        if not self.api_key:
            return []

        # Bright Data Comments API usually takes the post URL
        post_url = kwargs.get("url")
        if not post_url:
            logger.warning("[%s] get_comments requires 'url' in kwargs for TikTok", self.platform_name)
            return []

        inputs = [{"url": post_url}]
        snapshot_id = self._trigger_task(self.COMMENTS_DATASET_ID, inputs)
        if not snapshot_id:
            return []
            
        raw_results = self._poll_results(snapshot_id)
        
        comments = []
        for item in raw_results:
            try:
                comment = ScrapedComment(
                    platform="tiktok",
                    source_id=str(item.get("comment_id", "")),
                    post_id=post_id,
                    post_title="", # Filled by orchestrator
                    author=item.get("commenter_user_name", "unknown"),
                    body=item.get("comment_text", ""),
                    score=int(item.get("num_likes", 0)),
                    created_utc=self._parse_iso_date(item.get("date_created")),
                    url=item.get("comment_url"),
                    variety_query="",
                    extra={
                        "num_replies": item.get("num_replies"),
                        "commenter_id": item.get("commenter_id"),
                    }
                )
                comments.append(comment)
                if len(comments) >= limit:
                    break
            except Exception as e:
                logger.warning("[%s] Error parsing comment item: %s", self.platform_name, str(e))
                
        return comments

    def search_and_collect(
        self,
        query: str,
        max_posts: int = 10,
        max_comments_per_post: int = 50,
        **kwargs,
    ) -> dict:
        """
        Override BaseScraper.search_and_collect to pass post URL to get_comments.

        TikTok's get_comments requires the post URL, which the base class
        doesn't provide. This override ensures URLs are passed correctly.
        """
        if not self.api_key:
            return {"posts": [], "comments": []}

        logger.info(
            "[%s] Starting search_and_collect for query='%s'",
            self.platform_name,
            query,
        )

        posts = self.search_posts(query, limit=max_posts, **kwargs)
        logger.info("[%s] Found %d posts for '%s'", self.platform_name, len(posts), query)

        all_comments: List[ScrapedComment] = []
        for post in posts:
            try:
                comments = self.get_comments(
                    post.source_id,
                    limit=max_comments_per_post,
                    url=post.url,
                )
                for c in comments:
                    c.variety_query = query
                    c.post_title = post.title
                all_comments.extend(comments)
                logger.info(
                    "[%s] Collected %d comments from post '%s'",
                    self.platform_name,
                    len(comments),
                    post.title[:50],
                )
            except Exception as e:
                logger.warning(
                    "[%s] Failed to get comments for post %s: %s",
                    self.platform_name,
                    post.source_id,
                    str(e),
                )

        logger.info(
            "[%s] Total: %d posts, %d comments for '%s'",
            self.platform_name,
            len(posts),
            len(all_comments),
            query,
        )

        return {
            "posts": [p.to_dict() for p in posts],
            "comments": [c.to_dict() for c in all_comments],
        }

    def _parse_iso_date(self, date_str: Optional[str]) -> Optional[float]:
        """Convert ISO date string to UTC timestamp."""
        if not date_str:
            return None
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.timestamp()
        except Exception:
            return None

if __name__ == "__main__":
    # Simple test harness
    import logging
    logging.basicConfig(level=logging.INFO)
    
    scraper = TikTokScraper(api_key=os.environ.get("BRIGHTDATA_API_KEY", "dummy_key"))
    
    print(f"Testing {scraper.platform_name} scraper...")
    if os.environ.get("BRIGHTDATA_API_KEY"):
        results = scraper.search_posts("petunia flowers", limit=2)
        print(f"Found {len(results)} posts")
        for p in results:
            print(f"- {p.title} ({p.url})")
    else:
        print("Skipping real API test: BRIGHTDATA_API_KEY not set")
