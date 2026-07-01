"""File storage helpers for Telegram channel datasets."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TELEGRAM_DATA_DIR = DATA_DIR / "telegram"
SAFE_CHANNEL_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


def normalize_channel_username(raw_channel: str) -> str:
    """Normalize a Telegram channel identifier into a safe folder name."""
    channel = str(raw_channel or "").strip()
    channel = re.sub(r"\s+", "", channel)

    if channel.startswith("@"):
        channel = channel[1:]

    if channel.startswith(("http://", "https://")):
        parsed_url = urlparse(channel)
        if parsed_url.netloc.lower() in {"t.me", "telegram.me"}:
            channel = parsed_url.path.strip("/").split("/", 1)[0]
    elif channel.lower().startswith(("t.me/", "telegram.me/")):
        parsed_url = urlparse(f"https://{channel}")
        channel = parsed_url.path.strip("/").split("/", 1)[0]

    channel = channel.lstrip("@")
    safe_channel = SAFE_CHANNEL_PATTERN.sub("_", channel).strip("._-")
    return safe_channel or "unknown_channel"


def get_channel_data_dir(channel_username: str) -> Path:
    """Return the per-channel Telegram data directory."""
    return TELEGRAM_DATA_DIR / normalize_channel_username(channel_username)


def build_channel_meta(channel_username: str, meta: dict | None = None) -> dict:
    """Build normalized metadata for a Telegram collection result."""
    source_meta = dict(meta or {})
    return {
        "channel_username": normalize_channel_username(channel_username),
        "collected_at": source_meta.get(
            "collected_at",
            datetime.now(timezone.utc).isoformat(),
        ),
        "requested_logical_posts": int(
            source_meta.get("requested_logical_posts", 0) or 0
        ),
        "raw_telegram_messages_scanned": int(
            source_meta.get(
                "raw_telegram_messages_scanned",
                source_meta.get("raw_messages_scanned", 0),
            )
            or 0
        ),
        "logical_posts_scanned": int(
            source_meta.get("logical_posts_scanned", 0) or 0
        ),
        "posts_with_comments": int(source_meta.get("posts_with_comments", 0) or 0),
        "saved_items": int(source_meta.get("saved_items", 0) or 0),
        "source_type": "telegram",
    }


def write_json(path: Path, data) -> None:
    """Write JSON with UTF-8 encoding, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ensure_json_list_file(path: Path) -> None:
    """Create an empty JSON list file when it does not exist yet."""
    if not path.exists():
        write_json(path, [])


def load_json_list(path: Path) -> list:
    """Load a JSON list, returning an empty list for missing files."""
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list.")
    return data


def save_channel_posts(
    channel_username: str,
    posts: list,
    meta: dict | None = None,
) -> Path:
    """Save posts and metadata to the per-channel Telegram storage."""
    channel_dir = get_channel_data_dir(channel_username)
    write_json(channel_dir / "posts.json", posts)
    ensure_json_list_file(channel_dir / "comments.json")
    write_json(channel_dir / "meta.json", build_channel_meta(channel_username, meta))
    return channel_dir / "posts.json"


def save_channel_comments(
    channel_username: str,
    comments: list,
    meta: dict | None = None,
) -> Path:
    """Save comments and metadata to the per-channel Telegram storage."""
    channel_dir = get_channel_data_dir(channel_username)
    ensure_json_list_file(channel_dir / "posts.json")
    write_json(channel_dir / "comments.json", comments)
    write_json(channel_dir / "meta.json", build_channel_meta(channel_username, meta))
    return channel_dir / "comments.json"


def load_channel_posts(channel_username: str) -> list:
    """Load posts from the per-channel Telegram storage."""
    return load_json_list(get_channel_data_dir(channel_username) / "posts.json")


def load_channel_comments(channel_username: str) -> list:
    """Load comments from the per-channel Telegram storage."""
    return load_json_list(get_channel_data_dir(channel_username) / "comments.json")
