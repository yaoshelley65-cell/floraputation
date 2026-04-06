"""
Firecrawl scraper for Floraputation — uses Firecrawl API.

Firecrawl provides web search + scrape capabilities, converting any webpage
into clean markdown. Used for scraping gardening forums, review sites, and
any web content about plant varieties.
"""

from __future__ import annotations

from typing import List, Optional

from firecrawl import FirecrawlApp

from app.core.config import get_settings
from app.core.logging import get_logger
from app.scrapers.base import BaseScraper, ScrapedComment, ScrapedPost

logger = get_logger(__name__)


class FirecrawlScraper(BaseScraper):
    """Web scraper using Firecrawl API for general web content."""

    platform_name = "firecrawl"
    _min_request_interval = 2.0  # Respect rate limits

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Firecrawl scraper.

        Args:
            api_key: Firecrawl API key. If None, reads from config.
        """
        settings = get_settings()
        self._api_key = api_key or settings.firecrawl_api_key
        if not self._api_key:
            raise ValueError("Firecrawl API key is required. Set FIRECRAWL_API_KEY in .env")
        self.app = FirecrawlApp(api_key=self._api_key)
        logger.info("Firecrawl scraper initialised.")

    def get_remaining_credits(self) -> int:
        """Check remaining Firecrawl API credits."""
        try:
            usage = self.app.get_credit_usage()
            return usage.remaining_credits
        except Exception as e:
            logger.warning("Failed to check Firecrawl credits: %s", str(e))
            return -1

    def search_posts(
        self,
        query: str,
        limit: int = 5,
        **kwargs,
    ) -> List[ScrapedPost]:
        """
        Search the web for plant variety content using Firecrawl.

        Args:
            query: Search term (e.g., "petunia variety review")
            limit: Maximum number of results

        Returns:
            List of ScrapedPost objects with URLs and metadata
        """
        try:
            self._rate_limit()

            # Build search query optimized for plant variety content
            search_query = f"{query} plant variety review opinion"

            result = self.app.search(search_query, limit=limit)

            posts: List[ScrapedPost] = []

            # Process web results
            if result.web:
                for item in result.web:
                    d = item.model_dump()
                    post = ScrapedPost(
                        platform="firecrawl",
                        source_id=d.get("url", ""),
                        title=d.get("title", ""),
                        body=d.get("description", "") or "",
                        author="",
                        score=0,
                        num_comments=0,
                        url=d.get("url", ""),
                        variety_query=query,
                        extra={
                            "category": d.get("category", ""),
                            "source": "firecrawl_search",
                        },
                    )
                    posts.append(post)

            logger.info(
                "Firecrawl: found %d web results for '%s'",
                len(posts),
                query,
            )
            return posts

        except Exception as e:
            logger.error("Firecrawl search error: %s", str(e))
            return []

    def scrape_page(self, url: str) -> Optional[dict]:
        """
        Scrape a single URL and return its content as markdown.

        Args:
            url: The URL to scrape

        Returns:
            dict with 'markdown', 'metadata', etc. or None on failure
        """
        try:
            self._rate_limit()

            result = self.app.scrape(url, formats=["markdown"])

            if result:
                d = result.model_dump()
                metadata = d.get("metadata", {}) or {}
                return {
                    "url": url,
                    "markdown": d.get("markdown", ""),
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                    "language": metadata.get("language", ""),
                    "source_url": metadata.get("sourceURL", url),
                }

            return None

        except Exception as e:
            logger.warning("Firecrawl scrape error for %s: %s", url, str(e))
            return None

    def get_comments(
        self,
        post_id: str,
        limit: int = 100,
        **kwargs,
    ) -> List[ScrapedComment]:
        """
        Get comments by scraping a URL (post_id is the URL for Firecrawl).

        For Firecrawl, we scrape the full page and extract text content
        as a single "comment" representing the page's opinion content.

        Args:
            post_id: URL of the page to scrape
            limit: Not used for Firecrawl (returns full page content)

        Returns:
            List with a single ScrapedComment containing the page content
        """
        try:
            page_data = self.scrape_page(post_id)

            if not page_data or not page_data.get("markdown"):
                return []

            # Create a single comment from the scraped page content
            comment = ScrapedComment(
                platform="firecrawl",
                source_id=post_id,
                post_id=post_id,
                post_title=page_data.get("title", ""),
                author="",
                body=page_data["markdown"],
                score=0,
                url=post_id,
                variety_query="",
                extra={
                    "description": page_data.get("description", ""),
                    "language": page_data.get("language", ""),
                    "content_type": "scraped_page",
                },
            )

            logger.info(
                "Firecrawl: scraped page '%s' (%d chars)",
                page_data.get("title", post_id)[:50],
                len(page_data["markdown"]),
            )

            return [comment]

        except Exception as e:
            logger.error("Firecrawl get_comments error for %s: %s", post_id, str(e))
            return []

    def search_and_scrape(
        self,
        query: str,
        max_results: int = 5,
        scrape_content: bool = True,
    ) -> dict:
        """
        Search for web content and optionally scrape each result page.

        Args:
            query: Search query for plant variety
            max_results: Maximum search results
            scrape_content: Whether to scrape full content of each result

        Returns:
            dict with 'posts' and 'scraped_content' lists
        """
        posts = self.search_posts(query, limit=max_results)

        scraped_content = []
        if scrape_content:
            credits = self.get_remaining_credits()
            logger.info("Firecrawl credits remaining: %d", credits)

            for post in posts:
                if credits <= 10:
                    logger.warning("Low Firecrawl credits (%d), stopping scrape", credits)
                    break

                page = self.scrape_page(post.url)
                if page:
                    scraped_content.append(page)
                    credits -= 1  # Approximate credit usage

        return {
            "posts": [p.to_dict() for p in posts],
            "scraped_content": scraped_content,
            "credits_remaining": self.get_remaining_credits(),
        }
