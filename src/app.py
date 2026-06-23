"""
Streamlit interface for MoodWatch.
"""

from __future__ import annotations

import streamlit as st

from report import generate_report


DEFAULT_TOPIC = "искусственный интеллект"


def main() -> None:
    """Run the MoodWatch Streamlit application."""
    st.set_page_config(page_title="MoodWatch", page_icon="MW")

    st.title("MoodWatch")
    st.write(
        "MoodWatch анализирует сообщения по выбранной теме и формирует "
        "Markdown-отчёт о распределении тональности."
    )

    st.info(
        "Текущая версия использует тестовые JSON-данные и словарный анализ "
        "тональности. Telegram и DeepSeek будут подключены позже."
    )

    topic = st.text_input("Тема для анализа", value=DEFAULT_TOPIC)

    st.subheader("Отчёт")
    if st.button("Запустить анализ"):
        report = generate_report(topic)
        st.markdown(report)
    else:
        st.caption("Отчёт появится здесь после запуска анализа.")


if __name__ == "__main__":
    main()
