"""
Markdown report generation module for MoodWatch.

This module builds a simple text report from MVP sentiment analysis results.
It does not use DeepSeek, Telegram, or external APIs.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from analyzer import analyze_messages


def calculate_sentiment_stats(analyzed_messages: list[dict]) -> dict:
    """Calculate sentiment counts, percentages, and dominant sentiment."""
    total = len(analyzed_messages)
    sentiment_counts = Counter(
        message.get("sentiment", "neutral") for message in analyzed_messages
    )

    positive_count = sentiment_counts["positive"]
    neutral_count = sentiment_counts["neutral"]
    negative_count = sentiment_counts["negative"]

    if total == 0:
        positive_percent = 0.0
        neutral_percent = 0.0
        negative_percent = 0.0
    else:
        positive_percent = positive_count / total * 100
        neutral_percent = neutral_count / total * 100
        negative_percent = negative_count / total * 100

    if positive_count > neutral_count and positive_count > negative_count:
        dominant_sentiment = "positive"
    elif negative_count > positive_count and negative_count > neutral_count:
        dominant_sentiment = "negative"
    else:
        dominant_sentiment = "neutral"

    return {
        "total": total,
        "positive_count": positive_count,
        "neutral_count": neutral_count,
        "negative_count": negative_count,
        "positive_percent": positive_percent,
        "neutral_percent": neutral_percent,
        "negative_percent": negative_percent,
        "dominant_sentiment": dominant_sentiment,
    }


def build_summary(stats: dict) -> str:
    """Build a short Russian conclusion for the report."""
    dominant_sentiment = stats["dominant_sentiment"]

    if stats["total"] == 0:
        return "По выбранной теме не найдено сообщений для анализа."

    if dominant_sentiment == "positive":
        return "В обсуждении преобладает позитивная тональность."

    if dominant_sentiment == "negative":
        return "В обсуждении преобладает негативная тональность."

    return "В обсуждении преобладает нейтральная тональность."


def generate_report(topic: str) -> str:
    """Generate a human-readable Markdown report for a topic."""
    analyzed_messages = analyze_messages(topic)
    stats = calculate_sentiment_stats(analyzed_messages)
    summary = build_summary(stats)

    lines = [
        "# MoodWatch Report",
        "",
        f"## Тема: {topic}",
        "",
        f"Найдено сообщений: {stats['total']}",
        "",
        "## Распределение тональности",
        "",
        f"- Positive: {stats['positive_count']} ({stats['positive_percent']:.1f}%)",
        f"- Neutral: {stats['neutral_count']} ({stats['neutral_percent']:.1f}%)",
        f"- Negative: {stats['negative_count']} ({stats['negative_percent']:.1f}%)",
        "",
        f"Доминирующая тональность: {stats['dominant_sentiment']}",
        "",
        "## Итоговый вывод",
        "",
        summary,
        "",
        "## Первые 5 сообщений",
        "",
    ]

    if not analyzed_messages:
        lines.append("Сообщения не найдены.")
    else:
        for message in analyzed_messages[:5]:
            lines.append(
                f"- [{message['sentiment']}] "
                f"[{message['channel_name']} #{message['message_id']}] "
                f"{message['message_text']}"
            )

    return "\n".join(lines)


def save_report_to_file(report_text: str, filename: str = "reports/report.md") -> None:
    """Save report text to a Markdown file."""
    report_path = Path(filename)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")


def run_report(topic: str) -> None:
    """Generate, print, and save a report for a topic."""
    report_text = generate_report(topic)
    print(report_text)
    save_report_to_file(report_text)


if __name__ == "__main__":
    run_report("искусственный интеллект")
