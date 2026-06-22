"""
Sample data collection module for MoodWatch.

This module loads test messages from a local JSON file and saves new raw
messages to the SQLite database. It does not connect to Telegram or external
APIs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from storage import create_database, insert_raw_message, message_exists


SAMPLE_MESSAGES_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "sample_data" / "messages.json"
)


def load_messages_from_json(json_path: Path = SAMPLE_MESSAGES_PATH) -> list[dict[str, Any]]:
    """Load test messages from a JSON file and return them as a list."""
    with json_path.open("r", encoding="utf-8") as file:
        messages = json.load(file)

    if not isinstance(messages, list):
        raise ValueError("Sample messages JSON must contain a list of messages.")

    return messages


def save_messages_to_db(messages: list[dict[str, Any]]) -> tuple[int, int]:
    """Save new messages to the database and return new and duplicate counts."""
    create_database()

    new_messages_count = 0
    duplicate_messages_count = 0

    for message in messages:
        channel_name = message["channel_name"]
        message_id = message["message_id"]

        if message_exists(channel_name, message_id):
            duplicate_messages_count += 1
            continue

        insert_raw_message(
            channel_name=channel_name,
            message_id=message_id,
            message_text=message["message_text"],
            message_date=message["message_date"],
        )
        new_messages_count += 1

    return new_messages_count, duplicate_messages_count


def run_collection() -> None:
    """Load sample messages, save new records, and print collection statistics."""
    messages = load_messages_from_json()
    new_messages_count, duplicate_messages_count = save_messages_to_db(messages)

    print(f"Messages in JSON: {len(messages)}")
    print(f"New messages saved: {new_messages_count}")
    print(f"Duplicate messages skipped: {duplicate_messages_count}")


if __name__ == "__main__":
    run_collection()
