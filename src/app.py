"""
Streamlit interface for MoodWatch.
"""

from __future__ import annotations

import streamlit as st

from analyzer import analyze_messages
from collector import load_messages_from_json, save_messages_to_db
from report import build_summary, calculate_sentiment_stats, generate_report


DEFAULT_TOPIC = "искусственный интеллект"
QUICK_TOPICS = [
    "Искусственный интеллект",
    "Экономика",
    "Удалённая работа",
    "Рынок труда",
    "Криптовалюты",
]
SENTIMENT_LABELS = {
    "positive": "Позитив",
    "neutral": "Нейтрально",
    "negative": "Негатив",
}


def localize_sentiment(sentiment: str) -> str:
    """Return a Russian display label for a sentiment value."""
    return SENTIMENT_LABELS.get(sentiment, sentiment)


def build_messages_table(analyzed_messages: list[dict]) -> list[dict]:
    """Build table rows for analyzed messages."""
    return [
        {
            "Канал": message.get("channel_name", ""),
            "ID": message.get("message_id", ""),
            "Тональность": localize_sentiment(str(message.get("sentiment", ""))),
            "Сообщение": message.get("message_text", ""),
        }
        for message in analyzed_messages
    ]


def ensure_sample_data_loaded() -> None:
    """Load JSON sample data into local storage for the MVP demo."""
    messages = load_messages_from_json()
    save_messages_to_db(messages)


def show_sentiment_distribution(stats: dict) -> None:
    """Show a compact horizontal sentiment distribution."""
    total = max(stats["total"], 1)
    rows = [
        ("🟢 Позитив", stats["positive_count"], stats["positive_percent"]),
        ("⚪ Нейтрально", stats["neutral_count"], stats["neutral_percent"]),
        ("🔴 Негатив", stats["negative_count"], stats["negative_percent"]),
    ]

    for label, count, percent in rows:
        st.write(f"{label}: {count} ({percent:.1f}%)")
        st.progress(count / total)


def main() -> None:
    """Run the MoodWatch Streamlit application."""
    st.set_page_config(page_title="MoodWatch", page_icon="📊", layout="wide")

    if "topic" not in st.session_state:
        st.session_state.topic = DEFAULT_TOPIC

    with st.sidebar:
        st.header("MoodWatch")
        st.markdown("**Версия:** v0.1-alpha")
        st.markdown("**Источник данных:** JSON sample data")
        st.markdown("**Анализатор:** dictionary-based sentiment")
        st.markdown("**Статус Telegram:** planned")
        st.markdown("**Статус DeepSeek:** planned")

    st.title("MoodWatch")
    st.write(
        "MoodWatch анализирует сообщения по выбранной теме и формирует "
        "Markdown-отчёт о распределении тональности."
    )

    st.info(
        "Текущая версия использует тестовые JSON-данные и словарный анализ "
        "тональности. Telegram и DeepSeek будут подключены позже."
    )

    with st.expander("Ограничения версии", expanded=True):
        st.markdown(
            "- данные берутся из тестового JSON-файла\n"
            "- анализ тональности словарный\n"
            "- Telegram и DeepSeek пока не подключены"
        )

    st.caption(
        "Примеры тем: искусственный интеллект, экономика, удалённая работа, "
        "рынок труда, криптовалюты."
    )

    st.subheader("Быстрый выбор темы")
    quick_topic_columns = st.columns(len(QUICK_TOPICS))
    for column, quick_topic in zip(quick_topic_columns, QUICK_TOPICS):
        if column.button(quick_topic):
            st.session_state.topic = quick_topic.lower()

    topic = st.text_input("Тема для анализа", key="topic")

    st.subheader("Отчёт")
    if st.button("Запустить анализ"):
        ensure_sample_data_loaded()
        analyzed_messages = analyze_messages(topic)
        stats = calculate_sentiment_stats(analyzed_messages)
        report = generate_report(topic)
        dominant_sentiment = localize_sentiment(stats["dominant_sentiment"])

        st.success(
            f"Обнаружено {stats['total']} релевантных сообщений. "
            f"Доминирующая тональность: {dominant_sentiment}."
        )

        metric_columns = st.columns(4)
        metric_columns[0].metric("Всего сообщений", stats["total"])
        metric_columns[1].metric("🟢 Позитив", stats["positive_count"])
        metric_columns[2].metric("⚪ Нейтрально", stats["neutral_count"])
        metric_columns[3].metric("🔴 Негатив", stats["negative_count"])

        if not analyzed_messages:
            st.warning("По выбранной теме сообщения не найдены.")

        st.subheader("Распределение тональности")
        show_sentiment_distribution(stats)

        st.subheader("Итоговый вывод")
        st.markdown(f"**Найдено сообщений:** {stats['total']}")
        st.markdown(f"**Доминирующая тональность:** {dominant_sentiment}")
        st.markdown(build_summary(stats))

        st.download_button(
            label="Скачать отчёт (.md)",
            data=report,
            file_name="moodwatch_report.md",
            mime="text/markdown",
        )

        st.subheader("Найденные сообщения")
        st.dataframe(
            build_messages_table(analyzed_messages),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.caption("Отчёт появится здесь после запуска анализа.")


if __name__ == "__main__":
    main()
