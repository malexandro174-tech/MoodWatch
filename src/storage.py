"""
SQLite storage module for MoodWatch.

This module creates and works with the local database used to store raw
messages before filtering or analysis.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "moodwatch.db"


def create_database() -> None:
    """Create the SQLite database file and application tables if needed."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_name TEXT,
                message_id INTEGER,
                message_text TEXT,
                message_date TEXT,
                collected_at TEXT,
                UNIQUE(channel_name, message_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                run_date TEXT,
                total_messages INTEGER,
                positive_count INTEGER,
                neutral_count INTEGER,
                negative_count INTEGER,
                dominant_sentiment TEXT
            )
            """
        )


def create_analysis_runs_table() -> None:
    """Create the analysis_runs table if needed."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                run_date TEXT,
                total_messages INTEGER,
                positive_count INTEGER,
                neutral_count INTEGER,
                negative_count INTEGER,
                dominant_sentiment TEXT
            )
            """
        )


def insert_analysis_run(
    topic: str,
    total_messages: int,
    positive_count: int,
    neutral_count: int,
    negative_count: int,
    dominant_sentiment: str,
    run_date: str | None = None,
) -> None:
    """Insert one analysis run into the history table."""
    if run_date is None:
        run_date = datetime.now(timezone.utc).isoformat()

    create_analysis_runs_table()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO analysis_runs (
                topic,
                run_date,
                total_messages,
                positive_count,
                neutral_count,
                negative_count,
                dominant_sentiment
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                topic,
                run_date,
                total_messages,
                positive_count,
                neutral_count,
                negative_count,
                dominant_sentiment,
            ),
        )


def get_analysis_runs() -> list[dict[str, object]]:
    """Return analysis runs ordered from newest to oldest."""
    create_analysis_runs_table()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            """
            SELECT
                id,
                topic,
                run_date,
                total_messages,
                positive_count,
                neutral_count,
                negative_count,
                dominant_sentiment
            FROM analysis_runs
            ORDER BY id DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def get_last_runs(limit: int = 2) -> list[dict[str, object]]:
    """Return the latest analysis runs ordered from newest to oldest."""
    create_analysis_runs_table()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            """
            SELECT
                id,
                topic,
                run_date,
                total_messages,
                positive_count,
                neutral_count,
                negative_count,
                dominant_sentiment
            FROM analysis_runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_analysis_runs_by_topic(topic: str) -> list[dict[str, object]]:
    """Return analysis runs for a topic ordered from oldest to newest."""
    create_analysis_runs_table()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            """
            SELECT
                id,
                topic,
                run_date,
                total_messages,
                positive_count,
                neutral_count,
                negative_count,
                dominant_sentiment
            FROM analysis_runs
            WHERE topic = ?
            ORDER BY run_date ASC, id ASC
            """,
            (topic,),
        )
        return [dict(row) for row in cursor.fetchall()]


def insert_raw_message(
    channel_name: str,
    message_id: int,
    message_text: str,
    message_date: str,
    collected_at: str | None = None,
) -> None:
    """Insert one raw message into the database if it does not already exist."""
    if collected_at is None:
        collected_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO raw_messages (
                channel_name,
                message_id,
                message_text,
                message_date,
                collected_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                channel_name,
                message_id,
                message_text,
                message_date,
                collected_at,
            ),
        )


def clear_raw_messages() -> None:
    """Remove loaded raw messages without touching analysis history."""
    create_database()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("DELETE FROM raw_messages")


def message_exists(channel_name: str, message_id: int) -> bool:
    """Return True if a message already exists for the channel and message ID."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            SELECT 1
            FROM raw_messages
            WHERE channel_name = ? AND message_id = ?
            LIMIT 1
            """,
            (channel_name, message_id),
        )
        return cursor.fetchone() is not None


def get_raw_messages() -> list[dict[str, object]]:
    """Return all raw messages ordered by their database ID."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            """
            SELECT
                id,
                channel_name,
                message_id,
                message_text,
                message_date,
                collected_at
            FROM raw_messages
            ORDER BY id
            """
        )
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    create_database()
    print(f"Database created successfully: {DATABASE_PATH}")
