"""
Garden Centers scraper for Floraputation — uses Firecrawl API.

Scrapes product pages and reviews from major garden center websites
across the US, Europe, Australia, and Asia.

Supported sites include:
  US: Proven Winners, Monrovia, White Flower Farm, Burpee
  Europe: Thompson & Morgan, Crocus, Bakker
  Australia: Garden Express, Flower Power
  Asia: Various flower/plant e-commerce sites

Uses Firecrawl for:
  1. Targeted site search (site:domain.com query)
  2. Page scraping for product details and reviews
  3. Review extraction with structured parsing
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests

try:
    from app.core.logging import get_logger
    from app.scrapers.base import BaseScraper, ScrapedComment, ScrapedPost
except ImportError:
    import logging
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from base import BaseScraper, ScrapedComment, ScrapedPost

    logging.basicConfig(level=logging.INFO)

    def get_logger(name):
        return logging.getLogger(name)


logger = get_logger(__name__)


# ── Garden Center Registry ─────────────────────────────────────────────

@dataclass
class GardenCenter:
    """Represents a garden center website configuration."""

    name: str
    domain: str
    region: str  # US, EU, AU, ASIA
    search_url_template: str  # URL template for search, {query} placeholder
    review_selectors: Dict[str, str]  # CSS-like hints for review extraction
    language: str = "en"
    priority: int = 1  # 1=high, 2=medium, 3=low


# ── US Garden Centers ──────────────────────────────────────────────────
US_GARDEN_CENTERS = [
    GardenCenter(
        name="Proven Winners",
        domain="provenwinners.com",
        region="US",
        search_url_template="https://www.provenwinners.com/plants?search={query}",
        review_selectors={"reviews": ".review", "rating": ".star-rating"},
        priority=1,
    ),
    GardenCenter(
        name="Monrovia",
        domain="monrovia.com",
        region="US",
        search_url_template="https://www.monrovia.com/search?q={query}",
        review_selectors={"reviews": ".review-content", "rating": ".rating"},
        priority=1,
    ),
    GardenCenter(
        name="White Flower Farm",
        domain="whiteflowerfarm.com",
        region="US",
        search_url_template="https://www.whiteflowerfarm.com/search?q={query}",
        review_selectors={"reviews": ".review", "rating": ".stars"},
        priority=1,
    ),
    GardenCenter(
        name="Burpee",
        domain="burpee.com",
        region="US",
        search_url_template="https://www.burpee.com/search?q={query}",
        review_selectors={"reviews": ".review-text", "rating": ".star-rating"},
        priority=1,
    ),
    GardenCenter(
        name="Park Seed",
        domain="parkseed.com",
        region="US",
        search_url_template="https://www.parkseed.com/search?q={query}",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        priority=2,
    ),
    GardenCenter(
        name="Spring Hill Nurseries",
        domain="springhillnursery.com",
        region="US",
        search_url_template="https://www.springhillnursery.com/search?q={query}",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        priority=2,
    ),
    GardenCenter(
        name="Gardeners Supply",
        domain="gardeners.com",
        region="US",
        search_url_template="https://www.gardeners.com/search?q={query}",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        priority=2,
    ),
]

# ── European Garden Centers ────────────────────────────────────────────
EU_GARDEN_CENTERS = [
    GardenCenter(
        name="Thompson & Morgan",
        domain="thompson-morgan.com",
        region="EU",
        search_url_template="https://www.thompson-morgan.com/search?q={query}",
        review_selectors={"reviews": ".review", "rating": ".star-rating"},
        language="en",
        priority=1,
    ),
    GardenCenter(
        name="Crocus",
        domain="crocus.co.uk",
        region="EU",
        search_url_template="https://www.crocus.co.uk/search/_/{query}/",
        review_selectors={"reviews": ".review-content", "rating": ".rating"},
        language="en",
        priority=1,
    ),
    GardenCenter(
        name="Bakker",
        domain="bakker.com",
        region="EU",
        search_url_template="https://www.bakker.com/en-gb/search?q={query}",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        language="en",
        priority=1,
    ),
    GardenCenter(
        name="Suttons Seeds",
        domain="suttons.co.uk",
        region="EU",
        search_url_template="https://www.suttons.co.uk/search?q={query}",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        language="en",
        priority=2,
    ),
    GardenCenter(
        name="Gardening Express",
        domain="gardeningexpress.co.uk",
        region="EU",
        search_url_template="https://www.gardeningexpress.co.uk/search?q={query}",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        language="en",
        priority=2,
    ),
    GardenCenter(
        name="Jardiland",
        domain="jardiland.com",
        region="EU",
        search_url_template="https://www.jardiland.com/search?q={query}",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        language="fr",
        priority=3,
    ),
]

# ── Australian Garden Centers ──────────────────────────────────────────
AU_GARDEN_CENTERS = [
    GardenCenter(
        name="Garden Express",
        domain="gardenexpress.com.au",
        region="AU",
        search_url_template="https://www.gardenexpress.com.au/search?q={query}",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        language="en",
        priority=1,
    ),
    GardenCenter(
        name="Flower Power",
        domain="flowerpower.com.au",
        region="AU",
        search_url_template="https://www.flowerpower.com.au/search?q={query}",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        language="en",
        priority=1,
    ),
    GardenCenter(
        name="Bunnings",
        domain="bunnings.com.au",
        region="AU",
        search_url_template="https://www.bunnings.com.au/search/products?q={query}&category=garden",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        language="en",
        priority=2,
    ),
]

# ── Asian Garden/Plant Sites ──────────────────────────────────────────
ASIA_GARDEN_CENTERS = [
    GardenCenter(
        name="Taobao Garden",
        domain="taobao.com",
        region="ASIA",
        search_url_template="https://s.taobao.com/search?q={query}+花卉",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        language="zh",
        priority=2,
    ),
    GardenCenter(
        name="Rakuten Garden",
        domain="rakuten.co.jp",
        region="ASIA",
        search_url_template="https://search.rakuten.co.jp/search/mall/{query}+花/",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        language="ja",
        priority=3,
    ),
    GardenCenter(
        name="Huamu.cn",
        domain="huamu.cn",
        region="ASIA",
        search_url_template="https://www.huamu.cn/search/{query}",
        review_selectors={"reviews": ".review", "rating": ".rating"},
        language="zh",
        priority=2,
    ),
]

ALL_GARDEN_CENTERS = (
    US_GARDEN_CENTERS + EU_GARDEN_CENTERS + AU_GARDEN_CENTERS + ASIA_GARDEN_CENTERS
)


class GardenCentersScraper(BaseScraper):
    """
    Scraper for garden center websites using Firecrawl.

    Searches and scrapes product pages, reviews, and plant variety
    information from major garden center websites worldwide.
    """

    platform_name = "garden_centers"
    _min_request_interval = 2.5  # Respect Firecrawl rate limits

    def __init__(
        self,
        firecrawl_api_key: Optional[str] = None,
        regions: Optional[List[str]] = None,
        max_priority: int = 2,
    ):
        """
        Initialize Garden Centers scraper.

        Args:
            firecrawl_api_key: Firecrawl API key
            regions: List of regions to search (US, EU, AU, ASIA). None = all.
            max_priority: Maximum priority level to include (1=high only, 3=all)
        """
        self._api_key = firecrawl_api_key or os.environ.get("FIRECRAWL_API_KEY", "")
        if not self._api_key:
            raise ValueError("Firecrawl API key required. Set FIRECRAWL_API_KEY.")

        self.regions = [r.upper() for r in regions] if regions else ["US", "EU", "AU", "ASIA"]
        self.max_priority = max_priority

        # Filter garden centers by region and priority
        self.garden_centers = [
            gc
            for gc in ALL_GARDEN_CENTERS
            if gc.region in self.regions and gc.priority <= self.max_priority
        ]

        try:
            from firecrawl import FirecrawlApp

            self.firecrawl = FirecrawlApp(api_key=self._api_key)
        except Exception as e:
            logger.error("Firecrawl init failed: %s", str(e))
            self.firecrawl = None

        logger.info(
            "Garden Centers scraper initialised with %d sites across %s",
            len(self.garden_centers),
            ", ".join(self.regions),
        )

    def _firecrawl_search(self, query: str, limit: int = 5) -> List[dict]:
        """Perform a Firecrawl web search."""
        if not self.firecrawl:
            return []
        try:
            self._rate_limit()
            result = self.firecrawl.search(query, limit=limit)
            items = []
            if hasattr(result, "web") and result.web:
                for item in result.web:
                    d = item.model_dump() if hasattr(item, "model_dump") else item
                    items.append(d)
            elif isinstance(result, list):
                items = result
            return items
        except Exception as e:
            logger.warning("Firecrawl search error: %s", str(e))
            return []

    def _firecrawl_scrape(self, url: str) -> Optional[dict]:
        """Scrape a single URL via Firecrawl."""
        if not self.firecrawl:
            return None
        try:
            self._rate_limit()
            result = self.firecrawl.scrape(url, formats=["markdown"])
            if result:
                d = result.model_dump() if hasattr(result, "model_dump") else result
                metadata = d.get("metadata", {}) or {}
                return {
                    "url": url,
                    "markdown": d.get("markdown", ""),
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                    "language": metadata.get("language", ""),
                }
            return None
        except Exception as e:
            logger.warning("Firecrawl scrape error for %s: %s", url, str(e))
            return None

    def search_posts(
        self,
        query: str,
        limit: int = 10,
        regions: Optional[List[str]] = None,
        **kwargs,
    ) -> List[ScrapedPost]:
        """
        Search garden center websites for plant variety content.

        Uses Firecrawl site-specific search for each configured garden center.

        Args:
            query: Plant variety search term
            limit: Max results per garden center
            regions: Override region filter for this search

        Returns:
            List of ScrapedPost objects
        """
        all_posts: List[ScrapedPost] = []
        target_regions = [r.upper() for r in regions] if regions else self.regions

        centers_to_search = [
            gc for gc in self.garden_centers if gc.region in target_regions
        ]

        for gc in centers_to_search:
            try:
                # Site-specific search via Firecrawl
                search_query = f"site:{gc.domain} {query} plant variety"
                results = self._firecrawl_search(search_query, limit=min(limit, 5))

                for item in results:
                    url = item.get("url", "")
                    title = item.get("title", "")
                    description = item.get("description", "") or ""

                    post = ScrapedPost(
                        platform="garden_centers",
                        source_id=hashlib.md5(url.encode()).hexdigest()[:16],
                        title=title,
                        body=description,
                        author=gc.name,
                        score=0,
                        num_comments=0,
                        url=url,
                        variety_query=query,
                        extra={
                            "garden_center": gc.name,
                            "domain": gc.domain,
                            "region": gc.region,
                            "language": gc.language,
                            "source": "firecrawl_site_search",
                        },
                    )
                    all_posts.append(post)

                if results:
                    logger.info(
                        "Garden Centers: found %d results from %s for '%s'",
                        len(results), gc.name, query,
                    )

            except Exception as e:
                logger.warning(
                    "Garden center search error for %s: %s", gc.name, str(e)
                )

        # Also do a general garden center search
        try:
            general_query = f"{query} plant variety review garden center"
            general_results = self._firecrawl_search(general_query, limit=5)

            for item in general_results:
                url = item.get("url", "")
                title = item.get("title", "")
                description = item.get("description", "") or ""

                # Check if URL belongs to a known garden center
                gc_name = self._identify_garden_center(url)

                post = ScrapedPost(
                    platform="garden_centers",
                    source_id=hashlib.md5(url.encode()).hexdigest()[:16],
                    title=title,
                    body=description,
                    author=gc_name or "web",
                    score=0,
                    num_comments=0,
                    url=url,
                    variety_query=query,
                    extra={
                        "garden_center": gc_name or "unknown",
                        "region": "unknown",
                        "source": "firecrawl_general_search",
                    },
                )
                all_posts.append(post)

        except Exception as e:
            logger.warning("General garden search error: %s", str(e))

        # Deduplicate by URL
        seen_urls = set()
        unique_posts = []
        for p in all_posts:
            if p.url and p.url not in seen_urls:
                seen_urls.add(p.url)
                unique_posts.append(p)

        logger.info(
            "Garden Centers: total %d unique results for '%s'",
            len(unique_posts), query,
        )
        return unique_posts

    def get_comments(
        self,
        post_id: str,
        limit: int = 100,
        **kwargs,
    ) -> List[ScrapedComment]:
        """
        Get reviews/comments from a garden center product page.

        Scrapes the page and extracts review content from the markdown.

        Args:
            post_id: URL of the product page
            limit: Max reviews to extract

        Returns:
            List of ScrapedComment objects
        """
        url = post_id  # For garden centers, post_id is the URL
        page_data = self._firecrawl_scrape(url)

        if not page_data or not page_data.get("markdown"):
            return []

        markdown = page_data["markdown"]
        title = page_data.get("title", "")

        # Try to extract individual reviews from the markdown
        reviews = self._extract_reviews_from_markdown(markdown)

        if reviews:
            comments = []
            for i, review in enumerate(reviews[:limit]):
                comment = ScrapedComment(
                    platform="garden_centers",
                    source_id=hashlib.md5(f"{url}_{i}".encode()).hexdigest()[:16],
                    post_id=url,
                    post_title=title,
                    author=review.get("author", ""),
                    body=review.get("text", ""),
                    score=review.get("rating", 0),
                    url=url,
                    variety_query="",
                    extra={
                        "garden_center": self._identify_garden_center(url) or "unknown",
                        "rating": review.get("rating", 0),
                        "date": review.get("date", ""),
                        "content_type": "extracted_review",
                    },
                )
                comments.append(comment)
            return comments

        # Fallback: return full page content as a single comment
        comment = ScrapedComment(
            platform="garden_centers",
            source_id=hashlib.md5(url.encode()).hexdigest()[:16],
            post_id=url,
            post_title=title,
            author="",
            body=markdown[:5000],
            score=0,
            url=url,
            variety_query="",
            extra={
                "garden_center": self._identify_garden_center(url) or "unknown",
                "content_type": "scraped_page",
                "full_length": len(markdown),
            },
        )
        return [comment]

    def _extract_reviews_from_markdown(self, markdown: str) -> List[dict]:
        """
        Extract individual reviews from scraped markdown content.

        Looks for common review patterns in the markdown text.
        """
        reviews = []

        # Pattern 1: Star ratings followed by review text
        # e.g., "★★★★★\n\nGreat plant! Blooms all summer..."
        star_pattern = re.compile(
            r"([★⭐]{1,5}|(\d(?:\.\d)?)\s*(?:out of|/)\s*5)\s*\n+(.*?)(?=\n\n[★⭐]|\n\n\d(?:\.\d)?\s*(?:out of|/)|\Z)",
            re.DOTALL,
        )
        for match in star_pattern.finditer(markdown):
            rating_str = match.group(1)
            text = match.group(3).strip()
            if len(text) > 20:
                rating = rating_str.count("★") + rating_str.count("⭐")
                if not rating:
                    try:
                        rating = int(float(match.group(2) or "0"))
                    except (ValueError, TypeError):
                        rating = 0
                reviews.append({"text": text[:1000], "rating": rating, "author": "", "date": ""})

        # Pattern 2: "Review by <name>" or "Reviewed by <name>"
        review_by_pattern = re.compile(
            r"(?:Review(?:ed)?\s+by|By)\s+([^\n]+)\n+(.*?)(?=(?:Review(?:ed)?\s+by|By)\s+|\Z)",
            re.DOTALL | re.IGNORECASE,
        )
        for match in review_by_pattern.finditer(markdown):
            author = match.group(1).strip()
            text = match.group(2).strip()
            if len(text) > 20:
                reviews.append({"text": text[:1000], "rating": 0, "author": author, "date": ""})

        # Pattern 3: Numbered reviews or bullet-point reviews
        numbered_pattern = re.compile(
            r"(?:^|\n)\s*(?:\d+\.|[-•])\s*(.*?)(?=\n\s*(?:\d+\.|[-•])|\Z)",
            re.DOTALL,
        )
        if not reviews:
            # Only use this if no other patterns matched
            review_section = ""
            for marker in ["review", "testimonial", "customer say", "rating"]:
                idx = markdown.lower().find(marker)
                if idx >= 0:
                    review_section = markdown[idx : idx + 5000]
                    break

            if review_section:
                for match in numbered_pattern.finditer(review_section):
                    text = match.group(1).strip()
                    if len(text) > 30:
                        reviews.append({"text": text[:1000], "rating": 0, "author": "", "date": ""})

        return reviews

    def _identify_garden_center(self, url: str) -> Optional[str]:
        """Identify which garden center a URL belongs to."""
        url_lower = url.lower()
        for gc in ALL_GARDEN_CENTERS:
            if gc.domain in url_lower:
                return gc.name
        return None

    def search_and_scrape_variety(
        self,
        query: str,
        max_sites: int = 5,
        scrape_pages: bool = True,
    ) -> dict:
        """
        Search for a plant variety across garden centers and optionally scrape pages.

        Args:
            query: Plant variety search term
            max_sites: Maximum number of sites to search
            scrape_pages: Whether to scrape full page content

        Returns:
            dict with posts, comments, and metadata
        """
        posts = self.search_posts(query, limit=max_sites)

        all_comments = []
        if scrape_pages:
            for post in posts[:max_sites]:
                try:
                    comments = self.get_comments(post.url)
                    for c in comments:
                        c.variety_query = query
                        c.post_title = post.title
                    all_comments.extend(comments)
                except Exception as e:
                    logger.warning(
                        "Failed to scrape %s: %s", post.url, str(e)
                    )

        # Summarize by region
        region_counts = {}
        for p in posts:
            region = p.extra.get("region", "unknown")
            region_counts[region] = region_counts.get(region, 0) + 1

        return {
            "posts": [p.to_dict() for p in posts],
            "comments": [c.to_dict() for c in all_comments],
            "region_breakdown": region_counts,
            "sites_searched": len(set(p.extra.get("garden_center", "") for p in posts)),
        }

    @staticmethod
    def get_available_centers(region: Optional[str] = None) -> List[dict]:
        """Get list of available garden centers, optionally filtered by region."""
        centers = ALL_GARDEN_CENTERS
        if region:
            centers = [gc for gc in centers if gc.region == region.upper()]
        return [
            {
                "name": gc.name,
                "domain": gc.domain,
                "region": gc.region,
                "language": gc.language,
                "priority": gc.priority,
            }
            for gc in centers
        ]


# ── Standalone test ────────────────────────────────────────────────────
if __name__ == "__main__":
    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not api_key:
        print("ERROR: Set FIRECRAWL_API_KEY environment variable")
        exit(1)

    scraper = GardenCentersScraper(firecrawl_api_key=api_key)

    print("=" * 70)
    print("Testing Garden Centers Scraper")
    print("=" * 70)

    # List available centers
    print("\n--- Available Garden Centers ---")
    for region in ["US", "EU", "AU", "ASIA"]:
        centers = GardenCentersScraper.get_available_centers(region)
        print(f"  {region}: {len(centers)} centers")
        for c in centers:
            print(f"    - {c['name']} ({c['domain']}) [priority={c['priority']}]")

    # Test search
    test_queries = [
        "hydrangea Endless Summer",
        "petunia Supertunia",
        "rose Knock Out",
    ]

    for query in test_queries:
        print(f"\n--- Searching: '{query}' ---")
        posts = scraper.search_posts(query, limit=3)
        print(f"Found {len(posts)} results")
        for p in posts[:5]:
            gc = p.extra.get("garden_center", "?")
            region = p.extra.get("region", "?")
            print(f"  [{gc}/{region}] {p.title[:60]}")
            print(f"    URL: {p.url[:80]}")

    # Test scrape
    if posts:
        print(f"\n--- Scraping first result ---")
        comments = scraper.get_comments(posts[0].url)
        print(f"Extracted {len(comments)} review/content items")
        for c in comments[:2]:
            print(f"  Rating: {c.extra.get('rating', 'N/A')}")
            print(f"  Text: {c.body[:150]}...")

    print("\nDone!")
