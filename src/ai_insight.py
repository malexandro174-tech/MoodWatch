"""
DeepSeek AI Insight engine for MoodWatch.
"""

from __future__ import annotations

import json
import os
import urllib.request
from collections import Counter

from dotenv import load_dotenv

from analyzer import analyze_sentiment


DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-flash"
AI_INSIGHT_LIMIT = 50


def calculate_dictionary_sentiment_stats(messages: list[str]) -> dict[str, int]:
    """Calculate dictionary sentiment stats for the analysed AI sample."""
    sentiment_counts = Counter(analyze_sentiment(message) for message in messages)
    return {
        "positive": sentiment_counts["positive"],
        "neutral": sentiment_counts["neutral"],
        "negative": sentiment_counts["negative"],
    }


def build_research_context(
    messages: list[str],
    topic: str | None = None,
    source: str | None = None,
    analysed_message_count: int | None = None,
    positive_count: int | None = None,
    neutral_count: int | None = None,
    negative_count: int | None = None,
) -> dict:
    """Build structured context sent before the analysed comments."""
    analysed_messages = messages[:AI_INSIGHT_LIMIT]
    sentiment_stats = calculate_dictionary_sentiment_stats(analysed_messages)

    return {
        "research_title": "MoodWatch AI Research",
        "topic": topic or "Not specified",
        "source": source or "Not specified",
        "number_of_analysed_messages": (
            analysed_message_count
            if analysed_message_count is not None
            else len(analysed_messages)
        ),
        "dictionary_sentiment_statistics": {
            "Positive": (
                positive_count if positive_count is not None else sentiment_stats["positive"]
            ),
            "Neutral": (
                neutral_count if neutral_count is not None else sentiment_stats["neutral"]
            ),
            "Negative": (
                negative_count if negative_count is not None else sentiment_stats["negative"]
            ),
        },
    }


def build_ai_insight_prompt(
    messages: list[str],
    topic: str | None = None,
    source: str | None = None,
    analysed_message_count: int | None = None,
    positive_count: int | None = None,
    neutral_count: int | None = None,
    negative_count: int | None = None,
) -> str:
    """Build a compact DeepSeek prompt from filtered message text."""
    analysed_messages = messages[:AI_INSIGHT_LIMIT]
    research_context = build_research_context(
        messages=messages,
        topic=topic,
        source=source,
        analysed_message_count=analysed_message_count,
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
    )

    return (
        "Act as a professional public-opinion and discussion analyst. "
        "Analyze the provided research context and comments, then generate a "
        "concise research-style Markdown report. Do not return JSON. "
        "Use exactly these Markdown sections and follow the instructions for each:\n\n"
        "# Executive Summary\n\n"
        "A short overview in 3-5 sentences.\n\n"
        "# Public Temperature\n\n"
        "Return a score from 0 to 100 and a short explanation. "
        "0 means very calm or indifferent, 100 means highly emotional, tense, "
        "or conflict-heavy.\n\n"
        "# Dominant Emotions\n\n"
        "List the strongest emotions visible in the discussion.\n\n"
        "# Main Discussion Topics\n\n"
        "List 3-7 main topics.\n\n"
        "# Arguments Repeated Most Often\n\n"
        "Use a bullet list.\n\n"
        "# Signs of Polarization\n\n"
        "Explain whether opinions are mostly aligned or divided.\n\n"
        "# Interesting Observations\n\n"
        "Identify non-obvious patterns found in the discussion.\n\n"
        "# Final Conclusion\n\n"
        "Give a concise analytical conclusion.\n\n"
        "Research context:\n"
        f"{json.dumps(research_context, ensure_ascii=False, indent=2)}\n\n"
        "Analysed comments:\n"
        f"{json.dumps(analysed_messages, ensure_ascii=False, indent=2)}"
    )


def generate_ai_insight(
    messages: list[str],
    topic: str | None = None,
    source: str | None = None,
    analysed_message_count: int | None = None,
    positive_count: int | None = None,
    neutral_count: int | None = None,
    negative_count: int | None = None,
) -> str:
    """Generate a Markdown AI Insight report with DeepSeek."""
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not found.")

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты аналитик обсуждений. Отвечай только структурированным "
                    "Markdown без JSON и без лишних вступлений. Use ONLY the "
                    "provided comments. Never invent missing facts. Do not "
                    "generalize beyond the analysed sample. Clearly distinguish "
                    "observations from assumptions. If evidence is insufficient, "
                    "explicitly say so. Refer to 'the analysed comments' or "
                    "'the analysed discussion', not 'people' or 'everyone'."
                ),
            },
            {
                "role": "user",
                "content": build_ai_insight_prompt(
                    messages=messages,
                    topic=topic,
                    source=source,
                    analysed_message_count=analysed_message_count,
                    positive_count=positive_count,
                    neutral_count=neutral_count,
                    negative_count=negative_count,
                ),
            },
        ],
        "stream": False,
    }

    request = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        response_body = response.read().decode("utf-8")

    data = json.loads(response_body)
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
