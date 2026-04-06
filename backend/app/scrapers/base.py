"""
Base scraper interface for Floraputation data pipeline.

All platform-specific scrapers inherit from BaseScraper and implement
the search_variety() and get_comments() methods.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


def _safe_timestamp(ts) -> Optional[str]:
    """Safely convert a timestamp to ISO format string."""
    if ts is None:
        return None
    try:
        if isinstance(ts, (int, float)):
            return datetime.utcfromtimestamp(ts).isoformat()
        if isinstance(ts, str):
            return datetime.utcfromtimestamp(float(ts)).isoformat()
    except (ValueError, TypeError, OSError):
        pass
    return None


@dataclass
class ScrapedComment:
    """Standardised comment data from any platform."""

    platform: str  # "reddit", "youtube", "instagram"
    source_id: str  # platform-specific unique ID
    post_id: str  # parent post/video ID
    post_title: str  # title of the parent post/video
    author: str
    body: str
    score: int = 0  # upvotes, likes, etc.
    created_utc: Optional[float] = None
    url: Optional[str] = None
    variety_query: str = ""  # the search query that found this comment
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "platform": self.platform,
            "source_id": self.source_id,
            "post_id": self.post_id,
            "post_title": self.post_title,
            "author": self.author,
            "body": self.body,
            "score": self.score,
            "created_utc": self.created_utc,
            "created_at": _safe_timestamp(self.created_utc),
            "url": self.url,
            "variety_query": self.variety_query,
            "extra": self.extra,
        }


@dataclass
class ScrapedPost:
    """Standardised post/video data from any platform."""

    platform: str
    source_id: str
    title: str
    body: str = ""
    author: str = ""
    score: int = 0
    num_comments: int = 0
    created_utc: Optional[float] = None
    url: Optional[str] = None
    subreddit: str = ""  # Reddit-specific
    variety_query: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "platform": self.platform,
            "source_id": self.source_id,
            "title": self.title,
            "body": self.body,
            "author": self.author,
            "score": self.score,
            "num_comments": self.num_comments,
            "created_utc": self.created_utc,
            "created_at": _safe_timestamp(self.created_utc),
            "url": self.url,
            "subreddit": self.subreddit,
            "variety_query": self.variety_query,
            "extra": self.extra,
        }


class BaseScraper(ABC):
    """Abstract base class for all platform scrapers."""

    platform_name: str = "unknown"

    # Rate limiting
    _min_request_interval: float = 1.0  # seconds between requests
    _last_request_time: float = 0.0

    def _rate_limit(self):
        """Enforce rate limiting between API requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            logger.debug("Rate limiting: sleeping %.2fs", sleep_time)
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    @abstractmethod
    def search_posts(
        self, query: str, limit: int = 25, **kwargs
    ) -> List[ScrapedPost]:
        """
        Search for posts/videos related to a plant variety.

        Args:
            query: Search term (e.g., variety name, crop name)
            limit: Maximum number of posts to return
            **kwargs: Platform-specific parameters

        Returns:
            List of ScrapedPost objects
        """
        ...

    @abstractmethod
    def get_comments(
        self, post_id: str, limit: int = 100, **kwargs
    ) -> List[ScrapedComment]:
        """
        Get comments for a specific post/video.

        Args:
            post_id: Platform-specific post/video identifier
            limit: Maximum number of comments to return
            **kwargs: Platform-specific parameters

        Returns:
            List of ScrapedComment objects
        """
        ...

    def search_and_collect(
        self,
        query: str,
        max_posts: int = 10,
        max_comments_per_post: int = 50,
        **kwargs,
    ) -> dict:
        """
        Full pipeline: search for posts, then collect comments from each.

        Returns:
            dict with 'posts' and 'comments' lists
        """
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
                    post.source_id, limit=max_comments_per_post, **kwargs
                )
                # Tag comments with the variety query
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
