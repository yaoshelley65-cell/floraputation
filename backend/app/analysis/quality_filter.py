"""
Comment quality filter for Floraputation.

Filters out low-quality, irrelevant, or spam comments before
AI analysis to improve accuracy and reduce API costs.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)

# Minimum comment length (characters) to be considered meaningful
MIN_COMMENT_LENGTH = 15

# Maximum comment length — truncate very long content
MAX_COMMENT_LENGTH = 3000

# Keywords that indicate plant/garden relevance
RELEVANCE_KEYWORDS = {
    # General gardening
    "plant", "grow", "garden", "flower", "bloom", "petal", "leaf", "leaves",
    "seed", "soil", "pot", "container", "water", "sun", "shade", "prune",
    "fertilize", "compost", "mulch", "transplant", "propagate", "cutting",
    "root", "stem", "bud", "harvest", "yield", "season", "annual", "perennial",
    # Plant health
    "disease", "pest", "fungus", "mildew", "rot", "wilt", "blight", "aphid",
    "resistant", "tolerant", "hardy", "vigor", "healthy", "stress",
    # Commercial/variety
    "variety", "cultivar", "hybrid", "series", "breed", "strain", "selection",
    "nursery", "greenhouse", "grower", "supplier", "catalog", "trial",
    "performance", "color", "colour", "size", "height", "compact", "dwarf",
    "fragrance", "scent", "aroma",
    # Sentiment indicators
    "love", "hate", "beautiful", "gorgeous", "amazing", "terrible", "awful",
    "recommend", "favorite", "favourite", "best", "worst", "excellent", "poor",
    "impressive", "disappointing", "stunning", "ugly",
    # Chinese keywords
    "品种", "花卉", "种植", "园艺", "花园", "开花", "生长", "播种",
    "施肥", "浇水", "修剪", "病虫害", "抗性", "颜色", "香味",
    "推荐", "漂亮", "美丽", "好看",
}

# Spam indicators
SPAM_PATTERNS = [
    r"(?i)buy\s+now",
    r"(?i)click\s+here",
    r"(?i)free\s+shipping",
    r"(?i)discount\s+code",
    r"(?i)check\s+my\s+profile",
    r"(?i)subscribe\s+to\s+my",
    r"(?i)follow\s+me",
    r"(?i)dm\s+me",
    r"(?i)www\.\S+\.(com|net|org)\S*",
    r"(?i)(viagra|casino|crypto|bitcoin|nft|forex)",
]


def calculate_relevance_score(text: str, variety_context: str = "") -> float:
    """
    Calculate a relevance score (0.0 - 1.0) for a comment.

    Higher score = more relevant to plant/garden topics.

    Args:
        text: The comment text
        variety_context: Optional context like "Petunia Galaxy" for boosting

    Returns:
        Float between 0.0 and 1.0
    """
    if not text or len(text.strip()) < MIN_COMMENT_LENGTH:
        return 0.0

    text_lower = text.lower()
    words = set(re.findall(r'\w+', text_lower))

    # Count relevance keyword matches
    keyword_matches = len(words & RELEVANCE_KEYWORDS)

    # Boost if variety context words appear in the text
    context_boost = 0
    if variety_context:
        context_words = variety_context.lower().split()
        for cw in context_words:
            if cw in text_lower and len(cw) > 2:
                context_boost += 0.15

    # Base score from keyword density
    total_words = max(len(words), 1)
    keyword_density = keyword_matches / total_words

    # Score components
    score = 0.0
    score += min(keyword_density * 5, 0.4)  # Keyword density (max 0.4)
    score += min(keyword_matches * 0.05, 0.3)  # Absolute keyword count (max 0.3)
    score += min(context_boost, 0.3)  # Context boost (max 0.3)

    # Length bonus: longer comments tend to be more substantive
    if len(text) > 100:
        score += 0.05
    if len(text) > 300:
        score += 0.05

    return min(score, 1.0)


def is_spam(text: str) -> bool:
    """Check if a comment is likely spam."""
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def filter_comments(
    comments: List[dict],
    variety_context: str = "",
    min_relevance: float = 0.1,
    min_length: int = MIN_COMMENT_LENGTH,
    remove_spam: bool = True,
) -> Tuple[List[dict], dict]:
    """
    Filter comments for quality and relevance.

    Args:
        comments: List of comment dicts (must have 'body' field)
        variety_context: Context string for relevance scoring
        min_relevance: Minimum relevance score to keep (0.0-1.0)
        min_length: Minimum comment length in characters
        remove_spam: Whether to filter out spam

    Returns:
        Tuple of (filtered_comments, filter_stats)
    """
    stats = {
        "total_input": len(comments),
        "kept": 0,
        "removed_too_short": 0,
        "removed_spam": 0,
        "removed_low_relevance": 0,
        "removed_empty": 0,
    }

    filtered = []

    for comment in comments:
        body = comment.get("body", "") or ""

        # Remove empty
        if not body.strip():
            stats["removed_empty"] += 1
            continue

        # Remove too short
        if len(body.strip()) < min_length:
            stats["removed_too_short"] += 1
            continue

        # Remove spam
        if remove_spam and is_spam(body):
            stats["removed_spam"] += 1
            continue

        # Calculate relevance
        relevance = calculate_relevance_score(body, variety_context)

        # Remove low relevance
        if relevance < min_relevance:
            stats["removed_low_relevance"] += 1
            continue

        # Truncate very long comments
        if len(body) > MAX_COMMENT_LENGTH:
            comment = dict(comment)  # Don't mutate original
            comment["body"] = body[:MAX_COMMENT_LENGTH] + "..."

        # Add relevance score to comment for sorting
        comment = dict(comment)
        comment["_relevance_score"] = round(relevance, 3)
        filtered.append(comment)

    # Sort by relevance (highest first)
    filtered.sort(key=lambda c: c.get("_relevance_score", 0), reverse=True)

    stats["kept"] = len(filtered)
    stats["filter_rate"] = (
        round(1 - len(filtered) / max(len(comments), 1), 2)
    )

    logger.info(
        "Comment filter: %d -> %d (kept %.0f%%, removed: %d short, %d spam, %d low-relevance)",
        stats["total_input"],
        stats["kept"],
        (1 - stats["filter_rate"]) * 100,
        stats["removed_too_short"],
        stats["removed_spam"],
        stats["removed_low_relevance"],
    )

    return filtered, stats
