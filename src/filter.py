"""
Topic filtering module for MoodWatch.

This module filters raw messages from the local database by keyword matches.
Short keywords are matched only as separate words, while long phrases can be
matched inside the normalized message text.
"""

from __future__ import annotations

import re

from storage import get_raw_messages


SHORT_KEYWORDS = {"ии", "ai", "gpt", "llm"}


def get_topic_keywords(topic: str) -> list[str]:
    """Return MVP keyword list for a given topic."""
    normalized_topic = topic.lower()

    if "искусственный интеллект" in normalized_topic or "ии" in normalized_topic:
        return [
            "искусственный интеллект",
            "ии",
            "ai",
            "нейросеть",
            "нейросети",
            "нейронная сеть",
            "нейронные сети",
            "gpt",
            "llm",
            "автоматизация",
        ]

    if "работа" in normalized_topic:
        return [
            "работа",
            "удаленка",
            "удалёнка",
            "офис",
            "сотрудники",
            "занятость",
            "профессия",
        ]

    if "экономика" in normalized_topic:
        return [
            "экономика",
            "рынок",
            "рынки",
            "инфляция",
            "доходы",
            "цены",
            "бизнес",
        ]

    return normalized_topic.split()


def extract_words(text: str) -> set[str]:
    """Split text into lowercase words for exact word matching."""
    return set(re.findall(r"[0-9A-Za-zА-Яа-яЁё]+", text.lower()))


def keyword_matches_message(keyword: str, message_text: str, message_words: set[str]) -> bool:
    """Return True when a keyword matches the message according to MVP rules."""
    normalized_keyword = keyword.lower()

    if normalized_keyword in SHORT_KEYWORDS:
        return normalized_keyword in message_words

    if " " in normalized_keyword:
        return normalized_keyword in message_text

    return normalized_keyword in message_words


def filter_messages_by_topic(topic: str) -> list[dict]:
    """Return raw messages that contain at least one keyword for the topic."""
    messages = get_raw_messages()
    keywords = [keyword.lower() for keyword in get_topic_keywords(topic)]

    filtered_messages = []

    for message in messages:
        message_text = str(message.get("message_text", "")).lower()
        message_words = extract_words(message_text)

        if any(
            keyword_matches_message(keyword, message_text, message_words)
            for keyword in keywords
        ):
            filtered_messages.append(message)

    return filtered_messages


def run_filter(topic: str) -> None:
    """Filter messages by topic and print a short console preview."""
    filtered_messages = filter_messages_by_topic(topic)

    print(f"Topic: {topic}")
    print(f"Found messages: {len(filtered_messages)}")

    for message in filtered_messages[:5]:
        print(
            f"- [{message['channel_name']} #{message['message_id']}] "
            f"{message['message_text']}"
        )


if __name__ == "__main__":
    run_filter("искусственный интеллект")
