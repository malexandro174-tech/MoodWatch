"""
MVP sentiment analysis module for MoodWatch.

This module performs simple dictionary-based sentiment analysis for filtered
messages. It does not use DeepSeek, Telegram, or external APIs.
"""

from __future__ import annotations

import re
from collections import Counter

from filter import filter_messages_by_topic


POSITIVE_WORDS = {
    "помогает",
    "улучшает",
    "ускоряет",
    "рост",
    "эффективность",
    "польза",
    "удобно",
    "успешно",
    "развитие",
    "возможности",
}

NEGATIVE_WORDS = {
    "риск",
    "страх",
    "проблема",
    "кризис",
    "сокращение",
    "убыток",
    "угроза",
    "сложно",
    "падение",
    "нестабильность",
}


def extract_words(message_text: str) -> list[str]:
    """Split message text into lowercase words."""
    return re.findall(r"[0-9A-Za-zА-Яа-яЁё]+", message_text.lower())


def analyze_sentiment(message_text: str) -> str:
    """Return positive, negative, or neutral sentiment for a message."""
    words = extract_words(message_text)
    positive_count = sum(1 for word in words if word in POSITIVE_WORDS)
    negative_count = sum(1 for word in words if word in NEGATIVE_WORDS)

    if positive_count > negative_count:
        return "positive"

    if negative_count > positive_count:
        return "negative"

    return "neutral"


def analyze_messages(topic: str) -> list[dict]:
    """Filter messages by topic and add a sentiment field to each result."""
    messages = filter_messages_by_topic(topic)
    analyzed_messages = []

    for message in messages:
        analyzed_message = dict(message)
        analyzed_message["sentiment"] = analyze_sentiment(
            str(analyzed_message.get("message_text", ""))
        )
        analyzed_messages.append(analyzed_message)

    return analyzed_messages


def run_analysis(topic: str) -> None:
    """Run sentiment analysis for a topic and print a short console summary."""
    analyzed_messages = analyze_messages(topic)
    sentiment_counts = Counter(
        message["sentiment"] for message in analyzed_messages
    )

    print(f"Topic: {topic}")
    print(f"Analyzed messages: {len(analyzed_messages)}")
    print(f"Positive: {sentiment_counts['positive']}")
    print(f"Neutral: {sentiment_counts['neutral']}")
    print(f"Negative: {sentiment_counts['negative']}")

    for message in analyzed_messages[:5]:
        print(
            f"- [{message['sentiment']}] "
            f"[{message['channel_name']} #{message['message_id']}] "
            f"{message['message_text']}"
        )


if __name__ == "__main__":
    run_analysis("искусственный интеллект")
