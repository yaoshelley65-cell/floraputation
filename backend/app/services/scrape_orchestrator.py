"""
Scrape orchestrator for Floraputation.

Coordinates all scrapers (Reddit, YouTube, Firecrawl, Xiaohongshu, Garden Centers, TikTok)
and stores results in Supabase for data accumulation over time.
"""

from __future__ import annotations

import os
from typing import List, Optional, Dict, Any

from app.core.database import get_supabase_admin_client
from app.core.logging import get_logger
from app.services.data_store import DataStore

# Import all scrapers
from app.scrapers.reddit_scraper import RedditScraper
from app.scrapers.youtube_scraper import YouTubeScraper
from app.scrapers.firecrawl_scraper import FirecrawlScraper
from app.scrapers.xiaohongshu_scraper import XiaohongshuScraper
from app.scrapers.garden_centers_scraper import GardenCentersScraper
from app.scrapers.tiktok_scraper import TikTokScraper

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
        
        # 1. Reddit (Optimized)
        self.reddit = RedditScraper()
        
        # 2. YouTube
        self.youtube = YouTubeScraper()
        
        # 3. Firecrawl (General Web)
        try:
            self.firecrawl = FirecrawlScraper()
        except Exception:
            logger.warning("Firecrawl not configured, web scraping disabled.")
            self.firecrawl = None
            
        # 4. Xiaohongshu (MCP based, with Firecrawl fallback)
        try:
            self.xhs = XiaohongshuScraper()
        except Exception as e:
            logger.warning("Xiaohongshu scraper init failed: %s", str(e))
            self.xhs = None
        
        # 5. Garden Centers (Firecrawl based) — graceful degradation
        try:
            self.garden_centers = GardenCentersScraper()
        except Exception as e:
            logger.warning("Garden Centers scraper not available (Firecrawl key required): %s", str(e))
            self.garden_centers = None
        
        # 6. TikTok (Bright Data based) — graceful degradation
        try:
            self.tiktok = TikTokScraper()
            if not self.tiktok.api_key:
                logger.info("TikTok scraper initialised but BRIGHTDATA_API_KEY not set; will skip TikTok.")
        except Exception as e:
            logger.warning("TikTok scraper init failed: %s", str(e))
            self.tiktok = None

    def scrape_variety(
        self,
        variety_name: str,
        crop_name: str = "",
        series_name: str = "",
        search_query: str = "",
        platforms: Optional[List[str]] = None,
        max_posts_per_platform: int = 5,
        max_comments_per_post: int = 10,
    ) -> dict:
        """
        Run a full scraping pipeline for a plant variety across multiple platforms.
        """
        if platforms is None:
            platforms = ["reddit", "youtube"]
            if self.xhs:
                platforms.append("xhs")
            if self.garden_centers:
                platforms.append("garden_centers")
            if self.tiktok and self.tiktok.api_key:
                platforms.append("tiktok")
            if self.firecrawl:
                platforms.append("firecrawl")

        if not search_query:
            search_query = build_search_query(crop_name, variety_name, series_name)

        variety_query = search_query
        results = {
            "crop": crop_name,
            "series": series_name,
            "variety": variety_name,
            "query": search_query,
            "platforms": {},
            "totals": {"posts": 0, "comments": 0, "errors": 0},
        }

        # Mapping of platform names to their scraper instances
        platform_map = {
            "reddit": self.reddit,
            "youtube": self.youtube,
            "xhs": self.xhs,
            "garden_centers": self.garden_centers,
            "tiktok": self.tiktok,
            "firecrawl": self.firecrawl,
        }

        for platform in platforms:
            scraper = platform_map.get(platform)
            if not scraper:
                logger.info("[%s] Scraper not available, skipping.", platform)
                continue
                
            try:
                logger.info("[%s] Scraping for '%s'...", platform, search_query)
                
                if platform == "firecrawl":
                    # Firecrawl has its own search_and_scrape method
                    data = scraper.search_and_scrape(search_query, max_results=max_posts_per_platform)
                    posts = data.get("posts", [])
                    comments = []
                elif platform == "garden_centers":
                    # Garden centers search_posts returns ScrapedPost objects
                    raw_posts = scraper.search_posts(search_query, limit=max_posts_per_platform, crop=crop_name)
                    posts = [p.to_dict() for p in raw_posts]
                    comments = []
                elif platform == "tiktok":
                    # TikTok needs special handling: pass URL to get_comments
                    raw_posts = scraper.search_posts(search_query, limit=max_posts_per_platform)
                    posts = [p.to_dict() for p in raw_posts]
                    all_comments = []
                    for post in raw_posts:
                        try:
                            post_comments = scraper.get_comments(
                                post.source_id,
                                limit=max_comments_per_post,
                                url=post.url,
                            )
                            for c in post_comments:
                                c.variety_query = search_query
                                c.post_title = post.title
                            all_comments.extend(post_comments)
                        except Exception as e:
                            logger.warning("[tiktok] Failed to get comments for post %s: %s", post.source_id, str(e))
                    comments = [c.to_dict() for c in all_comments]
                else:
                    # Standard search_and_collect for Reddit, YouTube, XHS
                    data = scraper.search_and_collect(
                        search_query, 
                        max_posts=max_posts_per_platform,
                        max_comments_per_post=max_comments_per_post
                    )
                    posts = data.get("posts", [])
                    comments = data.get("comments", [])

                # Store results
                post_stats = self.store.store_posts_batch(posts)
                comment_stats = self.store.store_comments_batch(comments)

                self.store.log_scrape_job(
                    variety_query=variety_query,
                    platform=platform,
                    posts_found=len(posts),
                    comments_found=len(comments),
                )

                results["platforms"][platform] = {
                    "posts_found": len(posts),
                    "comments_found": len(comments),
                    "posts_stored": post_stats,
                    "comments_stored": comment_stats,
                }
                results["totals"]["posts"] += len(posts)
                results["totals"]["comments"] += len(comments)

            except Exception as e:
                logger.error("[%s] Scraping failed: %s", platform, str(e))
                results["platforms"][platform] = {"error": str(e)}
                results["totals"]["errors"] += 1
                self.store.log_scrape_job(
                    variety_query=variety_query,
                    platform=platform,
                    posts_found=0,
                    comments_found=0,
                    status="failed",
                    error_message=str(e),
                )

        results["db_stats"] = self.store.get_scrape_stats()
        return results

    def scrape_variety_with_aliases(
        self,
        variety_id: int,
        platforms: list = None,
        max_posts_per_platform: int = 3,
        max_comments_per_post: int = 5,
    ) -> dict:
        """
        Scrape a variety using ALL its known names (primary + community aliases).

        Fetches the variety and its aliases from the database, then runs
        scrape_variety for each name, combining all results.
        """
        client = get_supabase_admin_client()

        # Get variety info
        variety = (
            client.table("varieties")
            .select("id, variety, crop, series")
            .eq("id", variety_id)
            .execute()
        )
        if not variety.data:
            return {"error": f"Variety with id={variety_id} not found", "status": "failed"}

        v = variety.data[0]
        primary_name = v["variety"]
        crop_name = v.get("crop", "")
        series_name = v.get("series", "")

        # Get aliases
        aliases = (
            client.table("variety_aliases")
            .select("alias_name, language")
            .eq("variety_id", variety_id)
            .execute()
        )

        all_names = [{"name": primary_name, "language": "en", "is_primary": True}]
        for a in aliases.data or []:
            all_names.append({
                "name": a["alias_name"],
                "language": a.get("language", ""),
                "is_primary": False,
            })

        # Scrape for each name
        combined_results = []
        total_posts = 0
        total_comments = 0

        for name_info in all_names:
            try:
                result = self.scrape_variety(
                    variety_name=name_info["name"],
                    crop_name=crop_name,
                    series_name=series_name if name_info["is_primary"] else "",
                    platforms=platforms,
                    max_posts_per_platform=max_posts_per_platform,
                    max_comments_per_post=max_comments_per_post,
                )
                total_posts += result["totals"]["posts"]
                total_comments += result["totals"]["comments"]
                combined_results.append({
                    "name": name_info["name"],
                    "language": name_info["language"],
                    "is_primary": name_info["is_primary"],
                    "result": result,
                })
            except Exception as e:
                logger.error("Alias scrape failed for '%s': %s", name_info["name"], str(e))
                combined_results.append({
                    "name": name_info["name"],
                    "language": name_info["language"],
                    "is_primary": name_info["is_primary"],
                    "error": str(e),
                })

        return {
            "variety_id": variety_id,
            "primary_name": primary_name,
            "crop": crop_name,
            "total_names_searched": len(all_names),
            "total_posts": total_posts,
            "total_comments": total_comments,
            "results_by_name": combined_results,
        }

    def scrape_varieties_batch(
        self,
        varieties: List[dict],
        platforms: Optional[List[str]] = None,
        max_posts_per_platform: int = 3,
    ) -> List[dict]:
        """
        Scrape multiple varieties in batch.

        Args:
            varieties: List of dicts with 'crop', 'variety', and optional 'series'
            platforms: Platforms to scrape
            max_posts_per_platform: Max posts per platform per variety

        Returns:
            List of scrape results for each variety
        """
        results = []
        for v in varieties:
            crop = v.get("crop", "")
            variety = v.get("variety", "")
            series = v.get("series", "")

            if not crop or not variety:
                results.append({
                    "crop": crop,
                    "variety": variety,
                    "status": "skipped",
                    "error": "Both crop and variety are required",
                })
                continue

            try:
                result = self.scrape_variety(
                    variety_name=variety,
                    crop_name=crop,
                    series_name=series,
                    platforms=platforms,
                    max_posts_per_platform=max_posts_per_platform,
                )
                results.append(result)
            except Exception as e:
                logger.error("Batch scrape failed for %s %s: %s", crop, variety, str(e))
                results.append({
                    "crop": crop,
                    "variety": variety,
                    "status": "failed",
                    "error": str(e),
                })

        return results
