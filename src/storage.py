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
    """Create the SQLite database file and the raw_messages table if needed."""
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
