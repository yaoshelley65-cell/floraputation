"""
Scrape orchestrator for Floraputation.

Coordinates all scrapers (Reddit, YouTube, Firecrawl) and stores
results in Supabase for data accumulation over time.

Search queries are built from structured Crop + Series + Variety fields.
"""

from __future__ import annotations

from typing import List, Optional

from app.core.database import get_supabase_admin_client
from app.core.logging import get_logger
from app.scrapers.reddit_scraper import RedditScraper
from app.scrapers.youtube_scraper import YouTubeScraper
from app.scrapers.firecrawl_scraper import FirecrawlScraper
from app.services.data_store import DataStore

logger = get_logger(__name__)


def build_search_query(crop: str, variety: str, series: str = "") -> str:
    """Build a structured search query from Crop + Series + Variety."""
    parts = [crop.strip()]
    if series and series.strip():
        parts.append(series.strip())
    parts.append(variety.strip())
    return " ".join(parts)


class ScrapeOrchestrator:
    """Orchestrates scraping across all platforms with data accumulation."""

    def __init__(self):
        """Initialize all scrapers and data store."""
        self.store = DataStore()
        self.reddit = RedditScraper(subreddits=[
            "gardening", "flowers", "plants", "landscaping",
            "horticulture", "IndoorGarden",
        ])
        self.youtube = YouTubeScraper()

        try:
            self.firecrawl = FirecrawlScraper()
        except ValueError:
            logger.warning("Firecrawl not configured, web scraping disabled.")
            self.firecrawl = None

    def scrape_variety(
        self,
        variety_name: str,
        crop_name: str = "",
        series_name: str = "",
        search_query: str = "",
        platforms: Optional[List[str]] = None,
        max_posts_per_platform: int = 5,
        max_comments_per_post: int = 10,
        firecrawl_scrape_content: bool = True,
    ) -> dict:
        """
        Run a full scraping pipeline for a plant variety.

        Args:
            variety_name: The variety name
            crop_name: The crop name
            series_name: Optional series name
            search_query: Pre-built search query. If empty, built from crop+series+variety.
            platforms: List of platforms to scrape
            max_posts_per_platform: Max posts to collect per platform
            max_comments_per_post: Max comments per post (Reddit only)
            firecrawl_scrape_content: Whether to scrape full page content via Firecrawl

        Returns:
            dict with scraping results and statistics
        """
        if platforms is None:
            platforms = ["reddit", "youtube"]
            if self.firecrawl:
                platforms.append("firecrawl")

        # Build search query from structured fields if not provided
        if not search_query:
            search_query = build_search_query(crop_name, variety_name, series_name)

        # variety_query stored in DB for later retrieval
        variety_query = search_query

        results = {
            "crop": crop_name,
            "series": series_name,
            "variety": variety_name,
            "query": search_query,
            "platforms": {},
            "totals": {"posts": 0, "comments": 0, "errors": 0},
        }

        # --- Reddit ---
        if "reddit" in platforms:
            try:
                logger.info("Scraping Reddit for '%s'...", search_query)
                reddit_data = self.reddit.search_and_collect(
                    search_query,
                    max_posts=max_posts_per_platform,
                    max_comments_per_post=max_comments_per_post,
                )
                posts = reddit_data["posts"]
                comments = reddit_data["comments"]

                # Tag posts and comments with variety_query
                for p in posts:
                    p["variety_query"] = variety_query
                for c in comments:
                    c["variety_query"] = variety_query

                post_stats = self.store.store_posts_batch(posts)
                comment_stats = self.store.store_comments_batch(comments)

                self.store.log_scrape_job(
                    variety_query=variety_query,
                    platform="reddit",
                    posts_found=len(posts),
                    comments_found=len(comments),
                )

                results["platforms"]["reddit"] = {
                    "posts_found": len(posts),
                    "comments_found": len(comments),
                    "posts_stored": post_stats,
                    "comments_stored": comment_stats,
                }
                results["totals"]["posts"] += len(posts)
                results["totals"]["comments"] += len(comments)

            except Exception as e:
                logger.error("Reddit scraping failed: %s", str(e))
                results["platforms"]["reddit"] = {"error": str(e)}
                results["totals"]["errors"] += 1
                self.store.log_scrape_job(
                    variety_query=variety_query,
                    platform="reddit",
                    posts_found=0,
                    comments_found=0,
                    status="failed",
                    error_message=str(e),
                )

        # --- YouTube ---
        if "youtube" in platforms:
            try:
                logger.info("Scraping YouTube for '%s'...", search_query)
                yt_posts = self.youtube.search_posts(search_query, limit=max_posts_per_platform)
                yt_post_dicts = [p.to_dict() for p in yt_posts]

                for p in yt_post_dicts:
                    p["variety_query"] = variety_query

                post_stats = self.store.store_posts_batch(yt_post_dicts)

                self.store.log_scrape_job(
                    variety_query=variety_query,
                    platform="youtube",
                    posts_found=len(yt_posts),
                    comments_found=0,
                )

                results["platforms"]["youtube"] = {
                    "posts_found": len(yt_posts),
                    "posts_stored": post_stats,
                }
                results["totals"]["posts"] += len(yt_posts)

            except Exception as e:
                logger.error("YouTube scraping failed: %s", str(e))
                results["platforms"]["youtube"] = {"error": str(e)}
                results["totals"]["errors"] += 1

        # --- Firecrawl ---
        if "firecrawl" in platforms and self.firecrawl:
            try:
                logger.info("Scraping web via Firecrawl for '%s'...", search_query)
                fc_data = self.firecrawl.search_and_scrape(
                    search_query,
                    max_results=max_posts_per_platform,
                    scrape_content=firecrawl_scrape_content,
                )

                for p in fc_data["posts"]:
                    p["variety_query"] = variety_query

                post_stats = self.store.store_posts_batch(fc_data["posts"])

                # Store scraped content as comments
                comments_stored = 0
                for page in fc_data.get("scraped_content", []):
                    comment_data = {
                        "platform": "firecrawl",
                        "source_id": page["url"],
                        "post_id": page["url"],
                        "post_title": page.get("title", ""),
                        "author": "",
                        "body": (page.get("markdown", "") or "")[:10000],
                        "score": 0,
                        "url": page["url"],
                        "variety_query": variety_query,
                        "extra": {"content_type": "scraped_page"},
                    }
                    result = self.store.store_comment(comment_data)
                    if result:
                        comments_stored += 1

                self.store.log_scrape_job(
                    variety_query=variety_query,
                    platform="firecrawl",
                    posts_found=len(fc_data["posts"]),
                    comments_found=comments_stored,
                )

                results["platforms"]["firecrawl"] = {
                    "posts_found": len(fc_data["posts"]),
                    "pages_scraped": len(fc_data.get("scraped_content", [])),
                    "comments_stored": comments_stored,
                    "credits_remaining": fc_data.get("credits_remaining", -1),
                    "posts_stored": post_stats,
                }
                results["totals"]["posts"] += len(fc_data["posts"])
                results["totals"]["comments"] += comments_stored

            except Exception as e:
                logger.error("Firecrawl scraping failed: %s", str(e))
                results["platforms"]["firecrawl"] = {"error": str(e)}
                results["totals"]["errors"] += 1

        # Get overall DB stats
        results["db_stats"] = self.store.get_scrape_stats()

        logger.info(
            "Scraping complete for '%s': %d posts, %d comments across %d platforms",
            search_query,
            results["totals"]["posts"],
            results["totals"]["comments"],
            len(results["platforms"]),
        )

        return results

    def scrape_varieties_batch(
        self,
        varieties: List[dict],
        platforms: Optional[List[str]] = None,
        max_posts_per_platform: int = 3,
    ) -> List[dict]:
        """
        Scrape multiple varieties in batch.

        Each item should have 'crop' + 'variety' (required) and 'series' (optional).
        """
        all_results = []
        for v in varieties:
            crop_name = v.get("crop", "")
            variety_name = v.get("variety", "")
            series_name = v.get("series", "")

            if not variety_name or not crop_name:
                continue

            query = build_search_query(crop_name, variety_name, series_name)

            logger.info(
                "Batch scraping %d/%d: %s",
                len(all_results) + 1,
                len(varieties),
                query,
            )

            result = self.scrape_variety(
                variety_name=variety_name,
                crop_name=crop_name,
                series_name=series_name,
                search_query=query,
                platforms=platforms,
                max_posts_per_platform=max_posts_per_platform,
            )
            all_results.append(result)

        return all_results

    def get_all_names_for_variety(self, variety_id: int) -> list:
        """
        Get all searchable names for a variety (primary + aliases).
        Returns a list of search query strings.
        """
        try:
            client = get_supabase_admin_client()

            # Get primary name
            variety = (
                client.table("varieties")
                .select("id, variety, crop, series")
                .eq("id", variety_id)
                .execute()
            )
            if not variety.data:
                return []

            v = variety.data[0]
            crop = v.get("crop", "")
            primary_name = v.get("variety", "")
            series = v.get("series", "") or ""

            names = [build_search_query(crop, primary_name, series)]

            # Get aliases
            aliases = (
                client.table("variety_aliases")
                .select("alias_name, language")
                .eq("variety_id", variety_id)
                .execute()
            )

            for a in aliases.data or []:
                alias = a["alias_name"].strip()
                if alias:
                    # For non-English aliases, search with just the alias name
                    # For English aliases, combine with crop
                    lang = a.get("language", "").lower()
                    if lang in ("en", "english"):
                        names.append(build_search_query(crop, alias, series))
                    else:
                        names.append(alias)  # e.g. "泡泡菊" searched as-is

            return names

        except Exception as e:
            logger.error("Error fetching aliases for variety %d: %s", variety_id, str(e))
            return []

    def scrape_variety_with_aliases(
        self,
        variety_id: int,
        platforms: list = None,
        max_posts_per_platform: int = 3,
        max_comments_per_post: int = 5,
    ) -> dict:
        """
        Scrape a variety using ALL its known names (primary + community aliases).

        This expands search coverage across languages, collecting data
        from English Reddit, Chinese web sources, etc.
        """
        all_names = self.get_all_names_for_variety(variety_id)
        if not all_names:
            return {"error": f"Variety id={variety_id} not found or has no names"}

        # Get variety info for the result
        client = get_supabase_admin_client()
        variety = (
            client.table("varieties")
            .select("id, variety, crop")
            .eq("id", variety_id)
            .execute()
        )
        v = variety.data[0] if variety.data else {}

        combined_results = {
            "variety_id": variety_id,
            "variety_name": v.get("variety", ""),
            "crop_name": v.get("crop", ""),
            "names_searched": all_names,
            "per_name_results": [],
            "totals": {"posts": 0, "comments": 0, "errors": 0},
        }

        for name in all_names:
            logger.info("Scraping with name: '%s'", name)
            result = self.scrape_variety(
                variety_name=name,
                crop_name=v.get("crop", ""),
                search_query=name,
                platforms=platforms,
                max_posts_per_platform=max_posts_per_platform,
                max_comments_per_post=max_comments_per_post,
            )
            combined_results["per_name_results"].append({
                "name": name,
                "posts": result["totals"]["posts"],
                "comments": result["totals"]["comments"],
            })
            combined_results["totals"]["posts"] += result["totals"]["posts"]
            combined_results["totals"]["comments"] += result["totals"]["comments"]
            combined_results["totals"]["errors"] += result["totals"]["errors"]

        combined_results["db_stats"] = self.store.get_scrape_stats()
        return combined_results
