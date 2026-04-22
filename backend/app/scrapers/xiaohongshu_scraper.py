"""
Xiaohongshu (小红书 / RedNote) scraper for Floraputation.

Implements two strategies:
  1. MCP-based: Uses the xiaohongshu-mcp server (xpzouying/xiaohongshu-mcp)
     via HTTP JSON-RPC calls or manus-mcp-cli.
  2. Web-based fallback: Uses Firecrawl to search and scrape xiaohongshu.com
     content from the public web.

The MCP server provides:
  - search_feeds(keyword, filters) → search XHS notes
  - get_feed_detail(feed_id, xsec_token) → get note detail + comments
  - list_feeds() → get homepage recommendations

Reference: https://github.com/xpzouying/xiaohongshu-mcp
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from typing import Any, Dict, List, Optional

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


# ── Plant-related Chinese search terms ─────────────────────────────────
PLANT_SEARCH_TERMS_ZH = {
    "petunia": ["矮牵牛", "碧冬茄", "Petunia"],
    "rose": ["月季", "玫瑰", "蔷薇", "Rose"],
    "hydrangea": ["绣球花", "八仙花", "Hydrangea"],
    "orchid": ["兰花", "蝴蝶兰", "石斛兰", "Orchid"],
    "dahlia": ["大丽花", "天竺牡丹", "Dahlia"],
    "lavender": ["薰衣草", "Lavender"],
    "succulent": ["多肉植物", "多肉", "Succulent"],
    "chrysanthemum": ["菊花", "Chrysanthemum"],
    "lily": ["百合花", "百合", "Lily"],
    "tulip": ["郁金香", "Tulip"],
    "peony": ["牡丹", "芍药", "Peony"],
    "sunflower": ["向日葵", "Sunflower"],
    "jasmine": ["茉莉花", "茉莉", "Jasmine"],
    "camellia": ["山茶花", "茶花", "Camellia"],
    "bonsai": ["盆景", "Bonsai"],
    "cactus": ["仙人掌", "Cactus"],
    "fern": ["蕨类", "蕨", "Fern"],
    "begonia": ["秋海棠", "海棠", "Begonia"],
    "zinnia": ["百日草", "Zinnia"],
    "marigold": ["万寿菊", "金盏花", "Marigold"],
    "geranium": ["天竺葵", "Geranium"],
    "clematis": ["铁线莲", "Clematis"],
    "wisteria": ["紫藤", "Wisteria"],
    "plumeria": ["鸡蛋花", "Plumeria"],
    "gardenia": ["栀子花", "Gardenia"],
}


class XiaohongshuScraper(BaseScraper):
    """
    Xiaohongshu scraper using MCP protocol + web fallback.

    The scraper attempts to connect to a running xiaohongshu-mcp server.
    If unavailable, it falls back to Firecrawl-based web scraping of
    xiaohongshu content indexed by search engines.
    """

    platform_name = "xiaohongshu"
    _min_request_interval = 2.0

    def __init__(
        self,
        mcp_server_url: Optional[str] = None,
        firecrawl_api_key: Optional[str] = None,
        use_mcp_cli: bool = True,
    ):
        """
        Initialize Xiaohongshu scraper.

        Args:
            mcp_server_url: URL of xiaohongshu-mcp server (e.g., http://localhost:18060/mcp)
            firecrawl_api_key: Firecrawl API key for web fallback
            use_mcp_cli: Whether to try manus-mcp-cli first
        """
        self.mcp_server_url = mcp_server_url or os.environ.get(
            "XHS_MCP_URL", "http://localhost:18060/mcp"
        )
        self.firecrawl_api_key = firecrawl_api_key or os.environ.get(
            "FIRECRAWL_API_KEY", ""
        )
        self.use_mcp_cli = use_mcp_cli
        self._mcp_available = None  # Lazy check
        self._firecrawl_app = None

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "Floraputation/2.0",
            }
        )
        logger.info("Xiaohongshu scraper initialised.")

    # ── MCP Communication ──────────────────────────────────────────────

    def _check_mcp_available(self) -> bool:
        """Check if the xiaohongshu-mcp server is reachable."""
        if self._mcp_available is not None:
            return self._mcp_available

        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {},
                "id": 1,
            }
            resp = self.session.post(
                self.mcp_server_url, json=payload, timeout=5
            )
            self._mcp_available = resp.status_code == 200
        except Exception:
            self._mcp_available = False

        logger.info("XHS MCP server available: %s", self._mcp_available)
        return self._mcp_available

    def _call_mcp_tool(self, tool_name: str, arguments: dict) -> Optional[dict]:
        """
        Call a tool on the xiaohongshu-mcp server via JSON-RPC.

        Args:
            tool_name: MCP tool name (e.g., "search_feeds")
            arguments: Tool arguments

        Returns:
            Tool result dict or None on failure
        """
        if not self._check_mcp_available():
            return None

        try:
            self._rate_limit()
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments,
                },
                "id": int(time.time() * 1000),
            }
            resp = self.session.post(
                self.mcp_server_url, json=payload, timeout=30
            )
            if resp.status_code == 200:
                result = resp.json()
                if "result" in result:
                    return result["result"]
                if "error" in result:
                    logger.warning("MCP tool error: %s", result["error"])
            return None
        except Exception as e:
            logger.warning("MCP call failed for %s: %s", tool_name, str(e))
            return None

    def _call_mcp_cli(self, tool_name: str, arguments: dict) -> Optional[dict]:
        """
        Call MCP tool via manus-mcp-cli command line.

        Args:
            tool_name: MCP tool name
            arguments: Tool arguments as dict

        Returns:
            Tool result dict or None
        """
        try:
            args_json = json.dumps(arguments, ensure_ascii=False)
            cmd = [
                "manus-mcp-cli",
                "--server", "xiaohongshu-mcp",
                "tool", "call",
                tool_name,
                args_json,
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout.strip())
            return None
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            logger.debug("MCP CLI call failed: %s", str(e))
            return None

    # ── Firecrawl Web Fallback ─────────────────────────────────────────

    def _get_firecrawl(self):
        """Lazy-init Firecrawl client."""
        if self._firecrawl_app is None and self.firecrawl_api_key:
            try:
                from firecrawl import FirecrawlApp

                self._firecrawl_app = FirecrawlApp(api_key=self.firecrawl_api_key)
            except Exception as e:
                logger.warning("Firecrawl init failed: %s", str(e))
        return self._firecrawl_app

    def _search_via_firecrawl(self, query: str, limit: int = 10) -> List[dict]:
        """
        Search for Xiaohongshu content via Firecrawl web search.

        Searches for XHS content indexed by search engines.
        """
        fc = self._get_firecrawl()
        if not fc:
            return []

        try:
            self._rate_limit()
            # Search specifically for xiaohongshu.com content
            search_query = f"site:xiaohongshu.com {query}"
            result = fc.search(search_query, limit=limit)

            items = []
            if hasattr(result, "web") and result.web:
                for item in result.web:
                    d = item.model_dump() if hasattr(item, "model_dump") else item
                    items.append(d)
            elif isinstance(result, list):
                items = result

            logger.info(
                "XHS Firecrawl search: found %d results for '%s'",
                len(items), query,
            )
            return items

        except Exception as e:
            logger.warning("XHS Firecrawl search error: %s", str(e))
            return []

    def _scrape_xhs_page(self, url: str) -> Optional[dict]:
        """Scrape a Xiaohongshu page via Firecrawl."""
        fc = self._get_firecrawl()
        if not fc:
            return None

        try:
            self._rate_limit()
            result = fc.scrape(url, formats=["markdown"])
            if result:
                d = result.model_dump() if hasattr(result, "model_dump") else result
                metadata = d.get("metadata", {}) or {}
                return {
                    "url": url,
                    "markdown": d.get("markdown", ""),
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                }
            return None
        except Exception as e:
            logger.warning("XHS page scrape error for %s: %s", url, str(e))
            return None

    # ── Query Building ─────────────────────────────────────────────────

    @staticmethod
    def get_chinese_terms(crop: str, variety: str = "") -> List[str]:
        """
        Get Chinese search terms for a plant variety.

        Args:
            crop: English crop name
            variety: English variety name

        Returns:
            List of Chinese search terms
        """
        crop_lower = crop.lower().strip()
        terms = []

        # Look up Chinese names
        for key, zh_terms in PLANT_SEARCH_TERMS_ZH.items():
            if key in crop_lower or crop_lower in key:
                terms.extend(zh_terms)
                break

        # Add variety name (often used in Chinese posts too)
        if variety:
            terms.append(f"{variety}")
            # Combine Chinese crop + English variety
            if terms:
                terms.append(f"{terms[0]} {variety}")

        # If no mapping found, use English with common Chinese gardening terms
        if not terms:
            terms = [
                f"{crop} {variety}".strip(),
                f"{crop} 品种 {variety}".strip(),
            ]

        return terms

    # ── BaseScraper Interface ──────────────────────────────────────────

    def search_posts(
        self,
        query: str,
        limit: int = 10,
        sort_by: str = "综合",
        note_type: str = "不限",
        **kwargs,
    ) -> List[ScrapedPost]:
        """
        Search Xiaohongshu for plant variety content.

        Tries MCP server first, then falls back to Firecrawl web search.

        Args:
            query: Search keyword (Chinese or English)
            limit: Maximum results
            sort_by: Sort method (综合/最新/最多点赞/最多评论/最多收藏)
            note_type: Note type filter (不限/视频/图文)

        Returns:
            List of ScrapedPost objects
        """
        posts: List[ScrapedPost] = []

        # Strategy 1: MCP Server
        mcp_result = self._call_mcp_tool(
            "search_feeds",
            {
                "keyword": query,
                "filters": {
                    "sort_by": sort_by,
                    "note_type": note_type,
                },
            },
        )

        if mcp_result:
            posts = self._parse_mcp_search_results(mcp_result, query)
            if posts:
                logger.info("XHS MCP search: found %d posts for '%s'", len(posts), query)
                return posts[:limit]

        # Strategy 2: Firecrawl web search
        web_results = self._search_via_firecrawl(query, limit=limit)
        for item in web_results:
            url = item.get("url", "")
            title = item.get("title", "")
            description = item.get("description", "") or ""

            # Extract note ID from URL
            note_id = self._extract_note_id(url)

            post = ScrapedPost(
                platform="xiaohongshu",
                source_id=note_id or hashlib.md5(url.encode()).hexdigest()[:16],
                title=title,
                body=description,
                author="",
                score=0,
                num_comments=0,
                url=url,
                variety_query=query,
                extra={
                    "source": "firecrawl_web_search",
                    "note_id": note_id,
                    "language": "zh",
                },
            )
            posts.append(post)

        logger.info(
            "XHS search: found %d posts for '%s' (via %s)",
            len(posts),
            query,
            "firecrawl" if web_results else "none",
        )
        return posts[:limit]

    def get_comments(
        self,
        post_id: str,
        limit: int = 100,
        **kwargs,
    ) -> List[ScrapedComment]:
        """
        Get comments for a Xiaohongshu note.

        Args:
            post_id: Note ID or URL
            limit: Maximum comments

        Returns:
            List of ScrapedComment objects
        """
        # Strategy 1: MCP get_feed_detail
        xsec_token = kwargs.get("xsec_token", "")
        if xsec_token:
            mcp_result = self._call_mcp_tool(
                "get_feed_detail",
                {
                    "feed_id": post_id,
                    "xsec_token": xsec_token,
                    "load_all_comments": limit > 10,
                    "limit": min(limit, 50),
                },
            )
            if mcp_result:
                return self._parse_mcp_comments(mcp_result, post_id)

        # Strategy 2: Scrape the page via Firecrawl
        url = post_id if post_id.startswith("http") else f"https://www.xiaohongshu.com/explore/{post_id}"
        page_data = self._scrape_xhs_page(url)

        if page_data and page_data.get("markdown"):
            comment = ScrapedComment(
                platform="xiaohongshu",
                source_id=hashlib.md5(url.encode()).hexdigest()[:16],
                post_id=post_id,
                post_title=page_data.get("title", ""),
                author="",
                body=page_data["markdown"][:5000],
                score=0,
                url=url,
                variety_query="",
                extra={
                    "content_type": "scraped_page",
                    "language": "zh",
                    "source": "firecrawl_scrape",
                },
            )
            return [comment]

        return []

    # ── Parsing Helpers ────────────────────────────────────────────────

    def _parse_mcp_search_results(
        self, mcp_result: Any, query: str
    ) -> List[ScrapedPost]:
        """Parse MCP search_feeds result into ScrapedPost list."""
        posts = []
        try:
            # MCP result may contain content array with text items
            content = mcp_result if isinstance(mcp_result, list) else mcp_result.get("content", [])
            if isinstance(content, list):
                for item in content:
                    text = item.get("text", "") if isinstance(item, dict) else str(item)
                    # Try to parse as JSON
                    try:
                        data = json.loads(text) if isinstance(text, str) else text
                        if isinstance(data, list):
                            for note in data:
                                post = self._mcp_note_to_post(note, query)
                                if post:
                                    posts.append(post)
                        elif isinstance(data, dict):
                            # Could be a single note or a wrapper
                            notes = data.get("notes", data.get("items", [data]))
                            if isinstance(notes, list):
                                for note in notes:
                                    post = self._mcp_note_to_post(note, query)
                                    if post:
                                        posts.append(post)
                    except (json.JSONDecodeError, TypeError):
                        pass
        except Exception as e:
            logger.warning("MCP search result parse error: %s", str(e))
        return posts

    @staticmethod
    def _mcp_note_to_post(note: dict, query: str) -> Optional[ScrapedPost]:
        """Convert a single MCP note dict to ScrapedPost."""
        if not isinstance(note, dict):
            return None

        note_id = note.get("id", note.get("note_id", note.get("noteId", "")))
        title = note.get("title", note.get("display_title", ""))
        desc = note.get("desc", note.get("description", note.get("content", "")))

        if not (note_id or title):
            return None

        # Extract engagement metrics
        likes = note.get("likes", note.get("liked_count", 0))
        comments_count = note.get("comments", note.get("comment_count", 0))

        return ScrapedPost(
            platform="xiaohongshu",
            source_id=str(note_id),
            title=title,
            body=desc or "",
            author=note.get("user", {}).get("nickname", note.get("author", "")),
            score=int(likes) if likes else 0,
            num_comments=int(comments_count) if comments_count else 0,
            url=f"https://www.xiaohongshu.com/explore/{note_id}" if note_id else "",
            variety_query=query,
            extra={
                "source": "mcp",
                "language": "zh",
                "xsec_token": note.get("xsec_token", ""),
                "note_type": note.get("type", note.get("note_type", "")),
                "cover_image": note.get("cover", note.get("image_list", [{}])[0].get("url", ""))
                if note.get("image_list")
                else note.get("cover", ""),
            },
        )

    def _parse_mcp_comments(
        self, mcp_result: Any, post_id: str
    ) -> List[ScrapedComment]:
        """Parse MCP get_feed_detail result for comments."""
        comments = []
        try:
            content = mcp_result if isinstance(mcp_result, list) else mcp_result.get("content", [])
            if isinstance(content, list):
                for item in content:
                    text = item.get("text", "") if isinstance(item, dict) else str(item)
                    try:
                        data = json.loads(text) if isinstance(text, str) else text
                        if isinstance(data, dict):
                            raw_comments = data.get("comments", [])
                            for rc in raw_comments:
                                comment = ScrapedComment(
                                    platform="xiaohongshu",
                                    source_id=rc.get("id", rc.get("comment_id", "")),
                                    post_id=post_id,
                                    post_title="",
                                    author=rc.get("user", {}).get("nickname", ""),
                                    body=rc.get("content", rc.get("text", "")),
                                    score=rc.get("likes", rc.get("like_count", 0)),
                                    url="",
                                    variety_query="",
                                    extra={
                                        "language": "zh",
                                        "source": "mcp",
                                    },
                                )
                                comments.append(comment)
                    except (json.JSONDecodeError, TypeError):
                        pass
        except Exception as e:
            logger.warning("MCP comments parse error: %s", str(e))
        return comments

    @staticmethod
    def _extract_note_id(url: str) -> str:
        """Extract note ID from a Xiaohongshu URL."""
        patterns = [
            r"xiaohongshu\.com/explore/([a-f0-9]+)",
            r"xiaohongshu\.com/discovery/item/([a-f0-9]+)",
            r"xhslink\.com/([a-zA-Z0-9]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    # ── Convenience Methods ────────────────────────────────────────────

    def search_plant_variety(
        self,
        crop: str,
        variety: str = "",
        series: str = "",
        limit: int = 10,
    ) -> dict:
        """
        Search Xiaohongshu for a plant variety using Chinese terms.

        Args:
            crop: Crop name in English (e.g., "petunia")
            variety: Variety name (e.g., "Supertunia Vista Bubblegum")
            series: Optional series name
            limit: Max results per search term

        Returns:
            dict with 'posts' and 'comments' lists
        """
        chinese_terms = self.get_chinese_terms(crop, variety)
        all_posts: List[ScrapedPost] = []
        all_comments: List[ScrapedComment] = []
        seen_ids = set()

        for term in chinese_terms[:3]:  # Limit to top 3 terms
            posts = self.search_posts(term, limit=limit)
            for p in posts:
                if p.source_id not in seen_ids:
                    seen_ids.add(p.source_id)
                    all_posts.append(p)

            # Try to get comments for top posts
            for p in posts[:2]:
                xsec_token = p.extra.get("xsec_token", "")
                comments = self.get_comments(
                    p.source_id, xsec_token=xsec_token
                )
                for c in comments:
                    c.variety_query = f"{crop} {variety}".strip()
                    c.post_title = p.title
                all_comments.extend(comments)

        return {
            "posts": [p.to_dict() for p in all_posts],
            "comments": [c.to_dict() for c in all_comments],
            "search_terms_used": chinese_terms[:3],
        }


# ── Standalone test ────────────────────────────────────────────────────
if __name__ == "__main__":
    scraper = XiaohongshuScraper(
        firecrawl_api_key=os.environ.get("FIRECRAWL_API_KEY", "")
    )

    print("=" * 70)
    print("Testing Xiaohongshu Scraper — Plant Variety Search")
    print("=" * 70)

    # Test Chinese term generation
    test_crops = ["petunia", "hydrangea", "rose", "orchid", "succulent"]
    print("\n--- Chinese Term Mapping ---")
    for crop in test_crops:
        terms = XiaohongshuScraper.get_chinese_terms(crop, "test variety")
        print(f"  {crop}: {terms}")

    # Test search
    test_queries = ["绣球花 品种", "月季 推荐", "多肉植物 新品种"]
    for query in test_queries:
        print(f"\n--- Searching XHS: '{query}' ---")
        posts = scraper.search_posts(query, limit=5)
        print(f"Found {len(posts)} posts")
        for p in posts[:3]:
            print(f"  [{p.platform}] {p.title[:60]}  url={p.url[:60]}")

    # Test variety search
    print("\n--- Variety Search: hydrangea ---")
    result = scraper.search_plant_variety("hydrangea", "Endless Summer")
    print(f"Posts: {len(result['posts'])}, Comments: {len(result['comments'])}")
    print(f"Search terms used: {result['search_terms_used']}")

    print("\nDone!")
