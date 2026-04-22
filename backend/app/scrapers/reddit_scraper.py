"""
Reddit scraper for Floraputation — uses PullPush.io API + Reddit JSON API.

Enhanced version with:
- Expanded plant/garden subreddit coverage
- Dual API strategy (PullPush.io archive + Reddit JSON fallback)
- Smart query building with botanical terms
- Regional subreddit support (UK, AU, etc.)
- Retry logic and better error handling
"""

from __future__ import annotations

import hashlib
import re
import time
from typing import Dict, List, Optional, Tuple

import requests

try:
    from app.core.logging import get_logger
    from app.scrapers.base import BaseScraper, ScrapedComment, ScrapedPost
except ImportError:
    # Standalone mode for testing
    import logging
    import sys
    import os

    sys.path.insert(0, os.path.dirname(__file__))
    from base import BaseScraper, ScrapedComment, ScrapedPost

    logging.basicConfig(level=logging.INFO)

    def get_logger(name):
        return logging.getLogger(name)


logger = get_logger(__name__)


# ── Comprehensive plant/garden subreddit list ──────────────────────────
# Organized by category for targeted searching

SUBREDDITS_GENERAL_GARDENING = [
    "gardening",
    "garden",
    "flowers",
    "plants",
    "landscaping",
    "horticulture",
    "botany",
    "vegetablegardening",
    "organicgardening",
    "UrbanGardening",
    "BackyardOrchard",
    "permaculture",
    "NoLawns",
]

SUBREDDITS_INDOOR_PLANTS = [
    "houseplants",
    "IndoorGarden",
    "plantclinic",
    "plantidentification",
    "proplifting",
    "terrariums",
]

SUBREDDITS_SPECIFIC_PLANTS = [
    "succulents",
    "orchids",
    "Roses",
    "cactus",
    "Bonsai",
    "dahlias",
    "peonies",
    "hydrangeas",
    "Lavender",
    "SavageGarden",       # carnivorous plants
    "Petunia",
    "ferns",
    "begonias",
    "Chrysanthemum",
    "tulips",
    "Zinnia",
    "Sunflowers",
]

SUBREDDITS_REGIONAL = [
    "GardeningUK",
    "AustralianPlants",
    "GardeningAustralia",
    "JapaneseGardens",
    "EuropeanGardening",
]

SUBREDDITS_COMMERCIAL = [
    "whatsthisplant",
    "PlantedTank",
    "NativePlantGardening",
    "seedswap",
    "GardenWild",
    "Hydroponics",
    "aerogarden",
]

# Default: core subreddits most likely to have variety discussions
DEFAULT_SUBREDDITS = (
    SUBREDDITS_GENERAL_GARDENING
    + SUBREDDITS_INDOOR_PLANTS
    + SUBREDDITS_SPECIFIC_PLANTS[:10]
)

# All subreddits for deep search
ALL_SUBREDDITS = (
    SUBREDDITS_GENERAL_GARDENING
    + SUBREDDITS_INDOOR_PLANTS
    + SUBREDDITS_SPECIFIC_PLANTS
    + SUBREDDITS_REGIONAL
    + SUBREDDITS_COMMERCIAL
)


# ── Crop-to-subreddit mapping for targeted search ─────────────────────
CROP_SUBREDDIT_MAP: Dict[str, List[str]] = {
    "rose": ["Roses", "gardening", "flowers", "landscaping"],
    "orchid": ["orchids", "houseplants", "IndoorGarden"],
    "succulent": ["succulents", "cactus", "houseplants", "proplifting"],
    "petunia": ["Petunia", "gardening", "flowers", "vegetablegardening"],
    "dahlia": ["dahlias", "gardening", "flowers"],
    "peony": ["peonies", "gardening", "flowers"],
    "hydrangea": ["hydrangeas", "gardening", "landscaping", "flowers"],
    "lavender": ["Lavender", "gardening", "flowers", "landscaping"],
    "bonsai": ["Bonsai", "IndoorGarden"],
    "tomato": ["vegetablegardening", "gardening", "organicgardening"],
    "pepper": ["vegetablegardening", "gardening", "HotPeppers"],
    "fern": ["ferns", "houseplants", "IndoorGarden"],
    "begonia": ["begonias", "houseplants", "IndoorGarden"],
    "chrysanthemum": ["Chrysanthemum", "gardening", "flowers"],
    "tulip": ["tulips", "gardening", "flowers"],
    "zinnia": ["Zinnia", "gardening", "flowers"],
    "sunflower": ["Sunflowers", "gardening", "flowers"],
    "cactus": ["cactus", "succulents", "houseplants"],
    "carnivorous": ["SavageGarden", "houseplants"],
    "herb": ["vegetablegardening", "gardening", "Hydroponics"],
    "houseplant": ["houseplants", "IndoorGarden", "plantclinic"],
}


class RedditScraper(BaseScraper):
    """Enhanced Reddit scraper using PullPush.io + Reddit JSON API."""

    platform_name = "reddit"
    _min_request_interval = 1.5  # Be respectful to APIs

    # PullPush.io endpoints
    PULLPUSH_BASE = "https://api.pullpush.io/reddit"
    PULLPUSH_SUBMISSIONS = f"{PULLPUSH_BASE}/search/submission/"
    PULLPUSH_COMMENTS = f"{PULLPUSH_BASE}/search/comment/"

    # Reddit JSON API (no auth needed)
    REDDIT_SEARCH = "https://www.reddit.com/r/{subreddit}/search.json"
    REDDIT_COMMENTS = "https://www.reddit.com/comments/{post_id}.json"

    MAX_RETRIES = 2
    RETRY_DELAY = 3.0

    def __init__(
        self,
        subreddits: Optional[List[str]] = None,
        use_reddit_fallback: bool = True,
        crop_name: Optional[str] = None,
    ):
        """
        Initialize Reddit scraper.

        Args:
            subreddits: List of subreddits to search. If None, auto-selects based on crop.
            use_reddit_fallback: Whether to use Reddit JSON API as fallback.
            crop_name: Optional crop name for targeted subreddit selection.
        """
        if subreddits:
            self.subreddits = subreddits
        elif crop_name:
            self.subreddits = self._get_subreddits_for_crop(crop_name)
        else:
            self.subreddits = DEFAULT_SUBREDDITS

        self.use_reddit_fallback = use_reddit_fallback
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Floraputation/2.0 (Plant Variety Reputation Analysis; "
                "github.com/floraputation)",
                "Accept": "application/json",
            }
        )
        logger.info(
            "Reddit scraper initialised with %d subreddits.", len(self.subreddits)
        )

    @staticmethod
    def _get_subreddits_for_crop(crop_name: str) -> List[str]:
        """Get targeted subreddits for a specific crop type."""
        crop_lower = crop_name.lower().strip()

        # Check direct match
        for key, subs in CROP_SUBREDDIT_MAP.items():
            if key in crop_lower or crop_lower in key:
                # Add general subs that aren't already included
                result = list(subs)
                for s in ["gardening", "flowers", "plants"]:
                    if s not in result:
                        result.append(s)
                return result

        # Fallback to default
        return DEFAULT_SUBREDDITS

    @staticmethod
    def _build_variety_queries(query: str) -> List[str]:
        """
        Build multiple search query variants for better coverage.

        E.g., "petunia Supertunia Vista Bubblegum" ->
            ["petunia Supertunia Vista Bubblegum",
             "Supertunia Vista Bubblegum",
             '"Vista Bubblegum" petunia']
        """
        queries = [query]
        parts = query.strip().split()

        if len(parts) >= 3:
            # Without the crop name (first word)
            queries.append(" ".join(parts[1:]))
            # Quoted variety name with crop
            queries.append(f'"{" ".join(parts[1:])}" {parts[0]}')

        return queries[:3]  # Max 3 variants

    def _request_with_retry(
        self, url: str, params: dict, timeout: int = 15
    ) -> Optional[requests.Response]:
        """Make a request with retry logic."""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=timeout)
                if response.status_code == 200:
                    return response
                if response.status_code == 429:
                    # Rate limited — wait longer
                    wait = self.RETRY_DELAY * (attempt + 2)
                    logger.warning("Rate limited, waiting %.1fs...", wait)
                    time.sleep(wait)
                    continue
                if response.status_code >= 500:
                    logger.warning("Server error %d, retrying...", response.status_code)
                    time.sleep(self.RETRY_DELAY)
                    continue
                # 4xx (not 429) — don't retry
                logger.warning("Request failed: HTTP %d for %s", response.status_code, url)
                return None
            except requests.Timeout:
                logger.warning("Request timeout (attempt %d/%d)", attempt + 1, self.MAX_RETRIES + 1)
                time.sleep(self.RETRY_DELAY)
            except requests.RequestException as e:
                logger.warning("Request error: %s", str(e))
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY)
        return None

    def _search_pullpush(
        self, query: str, subreddit: str, limit: int, sort: str, sort_type: str
    ) -> List[dict]:
        """Search submissions via PullPush.io API."""
        params = {
            "q": query,
            "subreddit": subreddit,
            "size": min(limit, 100),
            "sort": sort,
            "sort_type": sort_type,
        }
        response = self._request_with_retry(self.PULLPUSH_SUBMISSIONS, params)
        if response:
            data = response.json()
            return data.get("data", [])
        return []

    def _search_reddit_json(
        self, query: str, subreddit: str, limit: int, sort: str
    ) -> List[dict]:
        """Fallback: search via Reddit's public JSON API."""
        url = self.REDDIT_SEARCH.format(subreddit=subreddit)
        params = {
            "q": query,
            "restrict_sr": "on",
            "sort": sort,
            "limit": min(limit, 25),
            "t": "all",
        }
        response = self._request_with_retry(url, params, timeout=10)
        if response:
            try:
                data = response.json()
                children = data.get("data", {}).get("children", [])
                return [c.get("data", {}) for c in children]
            except Exception:
                pass
        return []

    def search_posts(
        self,
        query: str,
        limit: int = 25,
        subreddit: Optional[str] = None,
        sort: str = "desc",
        sort_type: str = "score",
        multi_query: bool = True,
        **kwargs,
    ) -> List[ScrapedPost]:
        """
        Search Reddit submissions for a plant variety query.

        Args:
            query: Search term (variety name, crop name, etc.)
            limit: Max posts to return per subreddit
            subreddit: Specific subreddit; if None, searches all configured subs
            sort: Sort direction ("asc" or "desc")
            sort_type: Sort field ("score", "created_utc", "num_comments")
            multi_query: Whether to try multiple query variants

        Returns:
            List of ScrapedPost objects
        """
        all_posts: List[ScrapedPost] = []
        subs_to_search = [subreddit] if subreddit else self.subreddits

        # Build query variants
        queries = self._build_variety_queries(query) if multi_query else [query]

        for sub in subs_to_search:
            sub_posts = []
            for q in queries:
                try:
                    # Primary: PullPush.io
                    submissions = self._search_pullpush(q, sub, limit, sort, sort_type)

                    # Fallback: Reddit JSON API
                    if not submissions and self.use_reddit_fallback:
                        logger.debug("PullPush empty for r/%s, trying Reddit JSON...", sub)
                        submissions = self._search_reddit_json(q, sub, limit, sort)

                    for s in submissions:
                        post = ScrapedPost(
                            platform="reddit",
                            source_id=s.get("id", ""),
                            title=s.get("title", ""),
                            body=s.get("selftext", "") or "",
                            author=s.get("author", "[deleted]"),
                            score=s.get("score", 0) or 0,
                            num_comments=s.get("num_comments", 0) or 0,
                            created_utc=s.get("created_utc"),
                            url=f"https://reddit.com{s.get('permalink', '')}",
                            subreddit=s.get("subreddit", sub),
                            variety_query=query,
                            extra={
                                "upvote_ratio": s.get("upvote_ratio"),
                                "link_flair_text": s.get("link_flair_text"),
                                "is_self": s.get("is_self"),
                                "search_query_used": q,
                            },
                        )
                        sub_posts.append(post)

                except Exception as e:
                    logger.warning("Reddit search error for r/%s query='%s': %s", sub, q, str(e))

                # If we found results with first query, skip variants
                if sub_posts:
                    break

            all_posts.extend(sub_posts)

            if sub_posts:
                logger.info(
                    "Reddit: found %d posts in r/%s for '%s'",
                    len(sub_posts), sub, query,
                )

        # Deduplicate by source_id
        seen = set()
        unique_posts = []
        for p in all_posts:
            if p.source_id and p.source_id not in seen:
                seen.add(p.source_id)
                unique_posts.append(p)

        logger.info(
            "Reddit: total %d unique posts across %d subreddits for '%s'",
            len(unique_posts), len(subs_to_search), query,
        )
        return unique_posts

    def get_comments(
        self,
        post_id: str,
        limit: int = 100,
        **kwargs,
    ) -> List[ScrapedComment]:
        """
        Get comments for a specific Reddit post.

        Uses PullPush.io as primary, Reddit JSON API as fallback.

        Args:
            post_id: Reddit post ID (e.g., "ndtezj")
            limit: Maximum number of comments to return

        Returns:
            List of ScrapedComment objects
        """
        comments = self._get_comments_pullpush(post_id, limit)

        if not comments and self.use_reddit_fallback:
            logger.debug("PullPush comments empty for %s, trying Reddit JSON...", post_id)
            comments = self._get_comments_reddit_json(post_id, limit)

        return comments

    def _get_comments_pullpush(
        self, post_id: str, limit: int
    ) -> List[ScrapedComment]:
        """Get comments via PullPush.io."""
        params = {
            "link_id": post_id,
            "size": min(limit, 100),
            "sort": "desc",
            "sort_type": "score",
        }
        response = self._request_with_retry(self.PULLPUSH_COMMENTS, params)
        if not response:
            return []

        data = response.json()
        raw_comments = data.get("data", [])
        return self._parse_comments(raw_comments, post_id)

    def _get_comments_reddit_json(
        self, post_id: str, limit: int
    ) -> List[ScrapedComment]:
        """Get comments via Reddit JSON API."""
        url = self.REDDIT_COMMENTS.format(post_id=post_id)
        params = {"limit": min(limit, 100), "sort": "top"}
        response = self._request_with_retry(url, params, timeout=10)
        if not response:
            return []

        try:
            data = response.json()
            if isinstance(data, list) and len(data) > 1:
                children = data[1].get("data", {}).get("children", [])
                raw_comments = [c.get("data", {}) for c in children if c.get("kind") == "t1"]
                return self._parse_comments(raw_comments, post_id)
        except Exception as e:
            logger.warning("Reddit JSON comments parse error: %s", str(e))
        return []

    @staticmethod
    def _parse_comments(raw_comments: List[dict], post_id: str) -> List[ScrapedComment]:
        """Parse raw comment data into ScrapedComment objects."""
        comments = []
        for c in raw_comments:
            body = c.get("body", "")
            author = c.get("author", "[deleted]")

            # Skip deleted/removed/bot comments
            if body in ("[deleted]", "[removed]", ""):
                continue
            if author.lower() in ("automoderator", "[deleted]", "bot"):
                continue

            comment = ScrapedComment(
                platform="reddit",
                source_id=c.get("id", ""),
                post_id=post_id,
                post_title="",  # Filled by search_and_collect
                author=author,
                body=body,
                score=c.get("score", 0) or 0,
                created_utc=c.get("created_utc"),
                url=f"https://reddit.com{c.get('permalink', '')}",
                variety_query="",
                extra={
                    "subreddit": c.get("subreddit", ""),
                    "parent_id": c.get("parent_id", ""),
                    "is_submitter": c.get("is_submitter", False),
                },
            )
            comments.append(comment)

        return comments

    def search_comments_directly(
        self,
        query: str,
        limit: int = 100,
        subreddit: Optional[str] = None,
    ) -> List[ScrapedComment]:
        """
        Search comments directly by keyword (not via posts).
        Useful for finding mentions of specific varieties in comments.

        Args:
            query: Search term
            limit: Maximum number of comments
            subreddit: Optional subreddit filter

        Returns:
            List of ScrapedComment objects
        """
        all_comments: List[ScrapedComment] = []
        subs = [subreddit] if subreddit else self.subreddits[:8]  # Limit breadth

        for sub in subs:
            try:
                params = {
                    "q": query,
                    "subreddit": sub,
                    "size": min(limit, 100),
                    "sort": "desc",
                    "sort_type": "score",
                }
                response = self._request_with_retry(self.PULLPUSH_COMMENTS, params)
                if not response:
                    continue

                data = response.json()
                raw_comments = data.get("data", [])

                for c in raw_comments:
                    body = c.get("body", "")
                    if body in ("[deleted]", "[removed]", ""):
                        continue

                    comment = ScrapedComment(
                        platform="reddit",
                        source_id=c.get("id", ""),
                        post_id=c.get("link_id", "").replace("t3_", ""),
                        post_title="",
                        author=c.get("author", "[deleted]"),
                        body=body,
                        score=c.get("score", 0) or 0,
                        created_utc=c.get("created_utc"),
                        url=f"https://reddit.com{c.get('permalink', '')}",
                        variety_query=query,
                        extra={
                            "subreddit": c.get("subreddit", sub),
                        },
                    )
                    all_comments.append(comment)

                if raw_comments:
                    logger.info(
                        "Reddit direct search: %d comments in r/%s for '%s'",
                        len(raw_comments), sub, query,
                    )

            except Exception as e:
                logger.warning("Reddit direct comment search error: %s", str(e))

        return all_comments

    def search_variety_deep(
        self,
        crop: str,
        variety: str,
        series: str = "",
        max_posts: int = 10,
        max_comments_per_post: int = 20,
    ) -> dict:
        """
        Deep search for a specific plant variety across targeted subreddits.

        Automatically selects relevant subreddits based on crop type and
        tries multiple query formulations.

        Args:
            crop: Crop name (e.g., "petunia", "rose")
            variety: Variety name (e.g., "Supertunia Vista Bubblegum")
            series: Optional series name
            max_posts: Max posts to collect
            max_comments_per_post: Max comments per post

        Returns:
            dict with 'posts' and 'comments' lists
        """
        # Get targeted subreddits for this crop
        targeted_subs = self._get_subreddits_for_crop(crop)
        original_subs = self.subreddits
        self.subreddits = targeted_subs

        # Build the full query
        parts = [p for p in [crop, series, variety] if p and p.strip()]
        full_query = " ".join(parts)

        logger.info(
            "Reddit deep search: crop='%s', variety='%s' across %d subreddits",
            crop, variety, len(targeted_subs),
        )

        try:
            result = self.search_and_collect(
                full_query,
                max_posts=max_posts,
                max_comments_per_post=max_comments_per_post,
            )

            # Also search comments directly for the variety name
            direct_comments = self.search_comments_directly(
                variety if len(variety.split()) > 1 else full_query,
                limit=50,
            )

            # Merge direct comments (deduplicate)
            existing_ids = {c["source_id"] for c in result["comments"]}
            for dc in direct_comments:
                d = dc.to_dict()
                if d["source_id"] not in existing_ids:
                    result["comments"].append(d)
                    existing_ids.add(d["source_id"])

            return result

        finally:
            self.subreddits = original_subs


# ── Standalone test ────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    scraper = RedditScraper()

    print("=" * 70)
    print("Testing Reddit Scraper — Plant Variety Search")
    print("=" * 70)

    test_queries = [
        "petunia Supertunia",
        "hydrangea Endless Summer",
        "rose Knock Out",
    ]

    for query in test_queries:
        print(f"\n--- Searching: '{query}' ---")
        posts = scraper.search_posts(query, limit=5)
        print(f"Found {len(posts)} posts")
        for p in posts[:3]:
            print(f"  [{p.subreddit}] {p.title[:80]}  (score={p.score})")

        if posts:
            print(f"\n  Getting comments for first post: {posts[0].source_id}")
            comments = scraper.get_comments(posts[0].source_id, limit=5)
            print(f"  Found {len(comments)} comments")
            for c in comments[:2]:
                print(f"    - {c.author}: {c.body[:100]}...")

    print("\n--- Direct comment search ---")
    direct = scraper.search_comments_directly("Supertunia Vista Bubblegum", limit=10)
    print(f"Found {len(direct)} direct comment matches")
    for c in direct[:3]:
        print(f"  [{c.extra.get('subreddit', '?')}] {c.body[:100]}...")

    print("\nDone!")
