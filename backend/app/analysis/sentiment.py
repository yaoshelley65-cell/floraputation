"""
AI-powered sentiment analysis engine for Floraputation.

Uses LLM (GPT-4.1-mini) to analyze plant variety comments
and generate reputation scores, sentiment breakdowns, and insights.
"""

from __future__ import annotations

import json
import re
from typing import List, Optional

from openai import OpenAI

from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize OpenAI client (uses env vars automatically)
_client = OpenAI()
MODEL = "gpt-4.1-mini"


def analyze_comment_sentiment(comment_text: str, variety_name: str = "") -> dict:
    """
    Analyze sentiment of a single comment about a plant variety.

    Args:
        comment_text: The comment text to analyze
        variety_name: Optional variety name for context

    Returns:
        dict with sentiment, score, key_topics, and reasoning
    """
    if not comment_text or len(comment_text.strip()) < 5:
        return {
            "sentiment": "neutral",
            "score": 50,
            "key_topics": [],
            "reasoning": "Comment too short to analyze.",
        }

    variety_context = f" about '{variety_name}'" if variety_name else ""

    try:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert plant variety reputation analyst. "
                        "Analyze the sentiment of gardening/horticulture comments. "
                        "Respond with valid JSON only, no markdown formatting."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Analyze this comment{variety_context}:\n\n"
                        f'"{comment_text[:2000]}"\n\n'
                        "Return JSON with:\n"
                        '- "sentiment": "positive", "negative", or "neutral"\n'
                        '- "score": integer 0-100 (0=very negative, 50=neutral, 100=very positive)\n'
                        '- "key_topics": list of key topics mentioned (e.g., bloom quality, disease resistance, color)\n'
                        '- "reasoning": one sentence explaining the sentiment\n'
                        '- "relevance": float 0-1 indicating how relevant this comment is to plant variety reputation'
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=300,
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)

        # Validate and normalize
        result["sentiment"] = result.get("sentiment", "neutral").lower()
        if result["sentiment"] not in ("positive", "negative", "neutral"):
            result["sentiment"] = "neutral"
        result["score"] = max(0, min(100, int(result.get("score", 50))))
        result["key_topics"] = result.get("key_topics", [])[:10]
        result["reasoning"] = result.get("reasoning", "")
        result["relevance"] = max(0.0, min(1.0, float(result.get("relevance", 0.5))))
        result["tokens_used"] = response.usage.total_tokens

        return result

    except json.JSONDecodeError as e:
        logger.warning("Failed to parse LLM response: %s", str(e))
        return {
            "sentiment": "neutral",
            "score": 50,
            "key_topics": [],
            "reasoning": "Failed to parse AI response.",
            "relevance": 0.0,
        }
    except Exception as e:
        logger.error("Sentiment analysis error: %s", str(e))
        return {
            "sentiment": "neutral",
            "score": 50,
            "key_topics": [],
            "reasoning": f"Analysis error: {str(e)}",
            "relevance": 0.0,
        }


def analyze_comments_batch(
    comments: List[dict],
    variety_name: str = "",
) -> dict:
    """
    Analyze a batch of comments and produce aggregate sentiment stats.

    Args:
        comments: List of comment dicts (must have 'body' field)
        variety_name: The variety name for context

    Returns:
        dict with individual results and aggregate statistics
    """
    results = []
    total_score = 0
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    all_topics = {}

    for comment in comments:
        body = comment.get("body", "")
        if not body or len(body.strip()) < 5:
            continue

        result = analyze_comment_sentiment(body, variety_name)
        result["comment_id"] = comment.get("id", "")
        result["source_id"] = comment.get("source_id", "")
        result["platform"] = comment.get("platform", "")
        results.append(result)

        total_score += result["score"]
        sentiment_counts[result["sentiment"]] += 1

        for topic in result.get("key_topics", []):
            topic_lower = topic.lower()
            all_topics[topic_lower] = all_topics.get(topic_lower, 0) + 1

    analyzed_count = len(results)
    avg_score = round(total_score / analyzed_count, 1) if analyzed_count > 0 else 50.0

    # Sort topics by frequency
    top_topics = sorted(all_topics.items(), key=lambda x: x[1], reverse=True)[:15]

    return {
        "variety_name": variety_name,
        "total_comments": len(comments),
        "analyzed_comments": analyzed_count,
        "average_score": avg_score,
        "sentiment_distribution": sentiment_counts,
        "top_topics": [{"topic": t, "count": c} for t, c in top_topics],
        "individual_results": results,
    }


def generate_reputation_report(
    variety_name: str,
    crop_name: str,
    comments: List[dict],
    batch_analysis: Optional[dict] = None,
) -> dict:
    """
    Generate a comprehensive AI reputation report for a plant variety.

    Uses the batch analysis results (or runs analysis if not provided)
    to create a high-level reputation summary with actionable insights.

    Args:
        variety_name: Plant variety name
        crop_name: Crop type
        comments: List of comment dicts
        batch_analysis: Pre-computed batch analysis results

    Returns:
        dict with reputation report including summary, strengths, weaknesses, recommendations
    """
    if batch_analysis is None:
        batch_analysis = analyze_comments_batch(comments, variety_name)

    if batch_analysis["analyzed_comments"] == 0:
        return {
            "variety_name": variety_name,
            "crop_name": crop_name,
            "reputation_score": 50,
            "confidence": "low",
            "summary": "Insufficient data to generate a reputation report.",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "analysis": batch_analysis,
        }

    # Build a summary of the analysis for the LLM
    positive_comments = [
        r["reasoning"]
        for r in batch_analysis["individual_results"]
        if r["sentiment"] == "positive"
    ][:5]
    negative_comments = [
        r["reasoning"]
        for r in batch_analysis["individual_results"]
        if r["sentiment"] == "negative"
    ][:5]

    topics_str = ", ".join(
        [t["topic"] for t in batch_analysis["top_topics"][:10]]
    )

    try:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior horticulture market analyst. "
                        "Generate a professional reputation report for a plant variety "
                        "based on online sentiment analysis. Respond with valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate a reputation report for {crop_name} variety '{variety_name}'.\n\n"
                        f"Data summary:\n"
                        f"- Average sentiment score: {batch_analysis['average_score']}/100\n"
                        f"- Sentiment distribution: {batch_analysis['sentiment_distribution']}\n"
                        f"- Top topics discussed: {topics_str}\n"
                        f"- Sample positive feedback: {positive_comments}\n"
                        f"- Sample negative feedback: {negative_comments}\n"
                        f"- Total comments analyzed: {batch_analysis['analyzed_comments']}\n\n"
                        "Return JSON with:\n"
                        '- "reputation_score": integer 0-100\n'
                        '- "confidence": "high", "medium", or "low" based on data volume\n'
                        '- "summary": 2-3 sentence executive summary\n'
                        '- "strengths": list of 3-5 key strengths\n'
                        '- "weaknesses": list of 0-5 key weaknesses\n'
                        '- "recommendations": list of 2-4 actionable recommendations for growers/breeders\n'
                        '- "market_position": "premium", "standard", or "budget" based on perception\n'
                        '- "trend": "improving", "stable", or "declining"'
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=800,
        )

        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        report = json.loads(raw)
        report["variety_name"] = variety_name
        report["crop_name"] = crop_name
        report["analysis"] = batch_analysis
        report["tokens_used"] = response.usage.total_tokens

        return report

    except Exception as e:
        logger.error("Report generation error: %s", str(e))
        return {
            "variety_name": variety_name,
            "crop_name": crop_name,
            "reputation_score": batch_analysis["average_score"],
            "confidence": "low",
            "summary": f"Auto-generated: Average score {batch_analysis['average_score']}/100 from {batch_analysis['analyzed_comments']} comments.",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "analysis": batch_analysis,
            "error": str(e),
        }
