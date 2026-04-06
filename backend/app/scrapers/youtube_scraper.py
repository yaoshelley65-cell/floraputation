"""
YouTube scraper for Floraputation — uses Manus built-in YouTube Search API.

Searches for plant variety related videos and collects video metadata.
Note: Comments are not directly available via this API; Firecrawl can be
used to scrape YouTube video pages for comment content.
"""

from __future__ import annotations

import sys
from typing import List, Optional

from app.core.logging import get_logger
from app.scrapers.base import BaseScraper, ScrapedComment, ScrapedPost

logger = get_logger(__name__)

# Add Manus runtime path for API client
sys.path.append("/opt/.manus/.sandbox-runtime")


class YouTubeScraper(BaseScraper):
    """YouTube scraper using Manus built-in YouTube Search API."""

    platform_name = "youtube"
    _min_request_interval = 1.0

    def __init__(self):
        """Initialize YouTube scraper with Manus API client."""
        try:
            from data_api import ApiClient
            self.client = ApiClient()
            logger.info("YouTube scraper initialised with Manus API client.")
        except ImportError:
            logger.warning(
                "Manus API client not available. YouTube scraper will be disabled."
            )
            self.client = None

    def search_posts(
        self,
        query: str,
        limit: int = 10,
        language: str = "en",
        country: str = "US",
        **kwargs,
    ) -> List[ScrapedPost]:
        """
        Search YouTube for plant variety related videos.

        Args:
            query: Search term (variety name, crop name, etc.)
            limit: Maximum number of videos to return
            language: Language code for results
            country: Country code for results

        Returns:
            List of ScrapedPost objects representing YouTube videos
        """
        if not self.client:
            logger.warning("YouTube API client not available, skipping search.")
            return []

        try:
            self._rate_limit()

            # Build search query optimized for plant variety content
            search_query = f"{query} plant variety review"

            result = self.client.call_api(
                "Youtube/search",
                query={
                    "q": search_query,
                    "hl": language,
                    "gl": country,
                },
            )

            if not result or result.get("code"):
                logger.warning(
                    "YouTube search failed: %s",
                    result.get("message", "unknown error"),
                )
                return []

            contents = result.get("contents", [])
            posts: List[ScrapedPost] = []

            for item in contents:
                if item.get("type") != "video":
                    continue

                video = item.get("video", {})
                video_id = video.get("videoId", "")

                if not video_id:
                    continue

                post = ScrapedPost(
                    platform="youtube",
                    source_id=video_id,
                    title=video.get("title", ""),
                    body=video.get("descriptionSnippet", "") or "",
                    author=video.get("channelTitle", ""),
                    score=0,
                    num_comments=0,
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    variety_query=query,
                    extra={
                        "channel_id": video.get("channelId", ""),
                        "published_time": video.get("publishedTimeText", ""),
                        "duration": video.get("lengthText", ""),
                        "view_count": video.get("viewCountText", ""),
                        "thumbnail": video.get("thumbnail", [{}])[0].get("url", "")
                        if video.get("thumbnail")
                        else "",
                    },
                )
                posts.append(post)

                if len(posts) >= limit:
                    break

            logger.info(
                "YouTube: found %d videos for '%s'",
                len(posts),
                query,
            )
            return posts

        except Exception as e:
            logger.error("YouTube search error: %s", str(e))
            return []

    def get_comments(
        self,
        post_id: str,
        limit: int = 100,
        **kwargs,
    ) -> List[ScrapedComment]:
        """
        Get comments for a YouTube video.

        Note: The Manus YouTube API doesn't support direct comment fetching.
        This method attempts to use Firecrawl as a fallback to scrape comments.

        Args:
            post_id: YouTube video ID
            limit: Maximum number of comments

        Returns:
            List of ScrapedComment objects (may be empty if no comment API available)
        """
        # YouTube comments are not available via the search API
        # Firecrawl can be used as fallback - handled by the orchestrator
        logger.info(
            "YouTube comments not directly available for video %s. "
            "Use Firecrawl scraper for comment extraction.",
            post_id,
        )
        return []
