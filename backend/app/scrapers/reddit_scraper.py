"""
Reddit scraper for Floraputation — uses PullPush.io API.

PullPush.io is a free, public Reddit archive API that provides access to
Reddit submissions and comments without requiring authentication.
"""

from __future__ import annotations

from typing import List, Optional

import requests

from app.core.logging import get_logger
from app.scrapers.base import BaseScraper, ScrapedComment, ScrapedPost

logger = get_logger(__name__)

# Relevant subreddits for plant variety discussions
DEFAULT_SUBREDDITS = [
    "gardening",
    "flowers",
    "plants",
    "landscaping",
    "horticulture",
    "botany",
    "IndoorGarden",
    "succulents",
    "orchids",
    "Roses",
    "vegetablegardening",
]


class RedditScraper(BaseScraper):
    """Reddit scraper using PullPush.io archive API."""

    platform_name = "reddit"
    _min_request_interval = 1.5  # Be respectful to PullPush

    BASE_URL = "https://api.pullpush.io/reddit"
    SEARCH_SUBMISSIONS = f"{BASE_URL}/search/submission/"
    SEARCH_COMMENTS = f"{BASE_URL}/search/comment/"

    def __init__(self, subreddits: Optional[List[str]] = None):
        """
        Initialize Reddit scraper.

        Args:
            subreddits: List of subreddits to search. Defaults to plant-related subs.
        """
        self.subreddits = subreddits or DEFAULT_SUBREDDITS
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Floraputation/1.0 (Plant Variety Reputation Analysis)",
            "Accept": "application/json",
        })

    def search_posts(
        self,
        query: str,
        limit: int = 25,
        subreddit: Optional[str] = None,
        sort: str = "desc",
        sort_type: str = "score",
        **kwargs,
    ) -> List[ScrapedPost]:
        """
        Search Reddit submissions for a plant variety query.

        Args:
            query: Search term (variety name, crop name, etc.)
            limit: Max posts to return (per subreddit if searching multiple)
            subreddit: Specific subreddit to search; if None, searches all default subs
            sort: Sort direction ("asc" or "desc")
            sort_type: Sort field ("score", "created_utc", "num_comments")

        Returns:
            List of ScrapedPost objects
        """
        all_posts: List[ScrapedPost] = []
        subs_to_search = [subreddit] if subreddit else self.subreddits

        for sub in subs_to_search:
            try:
                self._rate_limit()

                params = {
                    "q": query,
                    "subreddit": sub,
                    "size": min(limit, 100),
                    "sort": sort,
                    "sort_type": sort_type,
                }

                response = self.session.get(
                    self.SEARCH_SUBMISSIONS,
                    params=params,
                    timeout=15,
                )

                if response.status_code != 200:
                    logger.warning(
                        "Reddit search failed for r/%s: HTTP %d",
                        sub,
                        response.status_code,
                    )
                    continue

                data = response.json()
                submissions = data.get("data", [])

                for s in submissions:
                    post = ScrapedPost(
                        platform="reddit",
                        source_id=s.get("id", ""),
                        title=s.get("title", ""),
                        body=s.get("selftext", "") or "",
                        author=s.get("author", "[deleted]"),
                        score=s.get("score", 0),
                        num_comments=s.get("num_comments", 0),
                        created_utc=s.get("created_utc"),
                        url=f"https://reddit.com{s.get('permalink', '')}",
                        subreddit=s.get("subreddit", sub),
                        variety_query=query,
                        extra={
                            "upvote_ratio": s.get("upvote_ratio"),
                            "link_flair_text": s.get("link_flair_text"),
                            "is_self": s.get("is_self"),
                        },
                    )
                    all_posts.append(post)

                logger.info(
                    "Reddit: found %d posts in r/%s for '%s'",
                    len(submissions),
                    sub,
                    query,
                )

            except requests.RequestException as e:
                logger.warning("Reddit request error for r/%s: %s", sub, str(e))
            except Exception as e:
                logger.error("Reddit unexpected error for r/%s: %s", sub, str(e))

        # Deduplicate by source_id
        seen = set()
        unique_posts = []
        for p in all_posts:
            if p.source_id not in seen:
                seen.add(p.source_id)
                unique_posts.append(p)

        return unique_posts

    def get_comments(
        self,
        post_id: str,
        limit: int = 100,
        **kwargs,
    ) -> List[ScrapedComment]:
        """
        Get comments for a specific Reddit post.

        Args:
            post_id: Reddit post ID (e.g., "ndtezj")
            limit: Maximum number of comments to return

        Returns:
            List of ScrapedComment objects
        """
        try:
            self._rate_limit()

            params = {
                "link_id": post_id,
                "size": min(limit, 100),
                "sort": "desc",
                "sort_type": "score",
            }

            response = self.session.get(
                self.SEARCH_COMMENTS,
                params=params,
                timeout=15,
            )

            if response.status_code != 200:
                logger.warning(
                    "Reddit comments fetch failed for post %s: HTTP %d",
                    post_id,
                    response.status_code,
                )
                return []

            data = response.json()
            raw_comments = data.get("data", [])

            comments = []
            for c in raw_comments:
                body = c.get("body", "")
                author = c.get("author", "[deleted]")

                # Skip deleted/removed comments
                if body in ("[deleted]", "[removed]", ""):
                    continue

                comment = ScrapedComment(
                    platform="reddit",
                    source_id=c.get("id", ""),
                    post_id=post_id,
                    post_title="",  # Will be filled by search_and_collect
                    author=author,
                    body=body,
                    score=c.get("score", 0),
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

            logger.info(
                "Reddit: fetched %d comments for post %s",
                len(comments),
                post_id,
            )
            return comments

        except requests.RequestException as e:
            logger.warning("Reddit comments request error for %s: %s", post_id, str(e))
            return []
        except Exception as e:
            logger.error("Reddit comments unexpected error for %s: %s", post_id, str(e))
            return []

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
        subs = [subreddit] if subreddit else self.subreddits[:5]  # Limit to top 5

        for sub in subs:
            try:
                self._rate_limit()

                params = {
                    "q": query,
                    "subreddit": sub,
                    "size": min(limit, 100),
                    "sort": "desc",
                    "sort_type": "score",
                }

                response = self.session.get(
                    self.SEARCH_COMMENTS,
                    params=params,
                    timeout=15,
                )

                if response.status_code != 200:
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
                        score=c.get("score", 0),
                        created_utc=c.get("created_utc"),
                        url=f"https://reddit.com{c.get('permalink', '')}",
                        variety_query=query,
                        extra={
                            "subreddit": c.get("subreddit", sub),
                        },
                    )
                    all_comments.append(comment)

                logger.info(
                    "Reddit direct search: %d comments in r/%s for '%s'",
                    len(raw_comments),
                    sub,
                    query,
                )

            except Exception as e:
                logger.warning("Reddit direct comment search error: %s", str(e))

        return all_comments
