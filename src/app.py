"""
Streamlit interface for MoodWatch.
"""

from __future__ import annotations

import streamlit as st

from analyzer import analyze_messages
from collector import load_messages_from_json, save_messages_to_db
from report import build_summary, calculate_sentiment_stats, generate_report
from storage import (
    get_analysis_runs,
    get_analysis_runs_by_topic,
    get_last_runs,
    insert_analysis_run,
)


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


def build_analysis_history_table(analysis_runs: list[dict]) -> list[dict]:
    """Build table rows for the analysis history."""
    return [
        {
            "Дата": run.get("run_date", ""),
            "Тема": run.get("topic", ""),
            "Всего": run.get("total_messages", 0),
            "Позитив": run.get("positive_count", 0),
            "Нейтрально": run.get("neutral_count", 0),
            "Негатив": run.get("negative_count", 0),
            "Доминирующая тональность": localize_sentiment(
                str(run.get("dominant_sentiment", ""))
            ),
        }
        for run in analysis_runs
    ]


def calculate_run_percentages(analysis_run: dict) -> dict[str, float]:
    """Calculate sentiment percentages for a saved analysis run."""
    total = int(analysis_run.get("total_messages", 0) or 0)
    if total == 0:
        return {
            "positive_percent": 0.0,
            "neutral_percent": 0.0,
            "negative_percent": 0.0,
        }

    return {
        "positive_percent": (
            int(analysis_run.get("positive_count", 0) or 0) / total * 100
        ),
        "neutral_percent": (
            int(analysis_run.get("neutral_count", 0) or 0) / total * 100
        ),
        "negative_percent": (
            int(analysis_run.get("negative_count", 0) or 0) / total * 100
        ),
    }


def build_runs_comparison_table(analysis_runs: list[dict]) -> list[dict]:
    """Build rows for comparing saved analysis runs."""
    rows = []
    for run in analysis_runs:
        percentages = calculate_run_percentages(run)
        rows.append(
            {
                "Тема": run.get("topic", ""),
                "Всего сообщений": run.get("total_messages", 0),
                "Позитив %": f"{percentages['positive_percent']:.1f}%",
                "Нейтрально %": f"{percentages['neutral_percent']:.1f}%",
                "Негатив %": f"{percentages['negative_percent']:.1f}%",
            }
        )
    return rows


def build_topic_trend_table(analysis_runs: list[dict]) -> list[dict]:
    """Build table rows for sentiment trend by topic."""
    rows = []
    for run in analysis_runs:
        percentages = calculate_run_percentages(run)
        rows.append(
            {
                "Дата": run.get("run_date", ""),
                "Позитив %": round(percentages["positive_percent"], 1),
                "Нейтрально %": round(percentages["neutral_percent"], 1),
                "Негатив %": round(percentages["negative_percent"], 1),
            }
        )
    return rows


def build_comparison_summary(analysis_runs: list[dict]) -> str:
    """Build a short automatic comparison summary for two analysis runs."""
    first_run, second_run = analysis_runs[:2]
    first_percentages = calculate_run_percentages(first_run)
    second_percentages = calculate_run_percentages(second_run)
    first_topic = str(first_run.get("topic", "Первый запуск"))
    second_topic = str(second_run.get("topic", "Второй запуск"))

    summaries = []
    if first_percentages["positive_percent"] > second_percentages["positive_percent"]:
        summaries.append(
            f"Обсуждение темы «{first_topic}» воспринимается аудиторией более позитивно."
        )
    elif first_percentages["positive_percent"] < second_percentages["positive_percent"]:
        summaries.append(
            f"Обсуждение темы «{second_topic}» воспринимается аудиторией более позитивно."
        )
    else:
        summaries.append("Доля позитивной реакции в последних запусках одинаковая.")

    if first_percentages["neutral_percent"] > second_percentages["neutral_percent"]:
        summaries.append(f"Тема «{first_topic}» вызывает более нейтральную реакцию.")
    elif first_percentages["neutral_percent"] < second_percentages["neutral_percent"]:
        summaries.append(f"Тема «{second_topic}» вызывает более нейтральную реакцию.")
    else:
        summaries.append("Доля нейтральной реакции в последних запусках одинаковая.")

    if first_percentages["negative_percent"] > second_percentages["negative_percent"]:
        summaries.append(f"Тема «{first_topic}» вызывает больше негативной реакции.")
    elif first_percentages["negative_percent"] < second_percentages["negative_percent"]:
        summaries.append(f"Тема «{second_topic}» вызывает больше негативной реакции.")
    else:
        summaries.append("Доля негативной реакции в последних запусках одинаковая.")

    return "\n\n".join(summaries)


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


def render_home_page() -> None:
    """Render the project overview page."""
    st.title("MoodWatch")
    st.write(
        "MoodWatch анализирует сообщения по выбранной теме и формирует "
        "Markdown-отчёт о распределении тональности."
    )

    st.subheader("Статус интеграций")
    status_columns = st.columns(2)
    status_columns[0].metric("Telegram", "planned")
    status_columns[1].metric("DeepSeek", "planned")

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


def render_analysis_page() -> None:
    """Render topic selection and analysis results."""
    st.title("Анализ")
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
        insert_analysis_run(
            topic=topic,
            total_messages=stats["total"],
            positive_count=stats["positive_count"],
            neutral_count=stats["neutral_count"],
            negative_count=stats["negative_count"],
            dominant_sentiment=stats["dominant_sentiment"],
        )

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


def render_history_page() -> None:
    """Render analysis history, comparison, and topic trend."""
    st.title("История")

    st.subheader("История анализов")
    analysis_runs = get_analysis_runs()[:10]
    if analysis_runs:
        st.dataframe(
            build_analysis_history_table(analysis_runs),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.caption("История появится после первого запуска анализа.")

    topic = st.session_state.topic
    st.caption(f"Текущая тема для динамики: {topic}")
    topic_runs = get_analysis_runs_by_topic(topic)
    if len(topic_runs) >= 2:
        st.subheader("Динамика по выбранной теме")
        topic_trend_table = build_topic_trend_table(topic_runs)
        st.dataframe(
            topic_trend_table,
            hide_index=True,
            use_container_width=True,
        )
        st.line_chart(
            topic_trend_table,
            x="Дата",
            y=["Позитив %", "Нейтрально %", "Негатив %"],
        )
    elif len(topic_runs) == 1:
        st.subheader("Динамика по выбранной теме")
        st.caption(
            "Для построения динамики нужно минимум два запуска анализа по одной теме."
        )

    last_runs = get_last_runs(limit=2)
    if len(last_runs) >= 2:
        st.subheader("Сравнение последних запусков")
        st.dataframe(
            build_runs_comparison_table(last_runs),
            hide_index=True,
            use_container_width=True,
        )
        st.markdown("**Вывод:**")
        st.markdown(build_comparison_summary(last_runs))


def main() -> None:
    """Run the MoodWatch Streamlit application."""
    st.set_page_config(page_title="MoodWatch", page_icon="📊", layout="wide")

    if "topic" not in st.session_state:
        st.session_state.topic = DEFAULT_TOPIC

    with st.sidebar:
        st.header("MoodWatch")
        selected_section = st.radio(
            "Навигация",
            ["Главная", "Анализ", "История"],
        )
        st.divider()
        st.markdown("**Версия:** v0.1-alpha")
        st.markdown("**Источник данных:** JSON sample data")
        st.markdown("**Анализатор:** dictionary-based sentiment")

    if selected_section == "Главная":
        render_home_page()
    elif selected_section == "Анализ":
        render_analysis_page()
    else:
        render_history_page()


if __name__ == "__main__":
    main()
