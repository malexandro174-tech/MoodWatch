import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import RPCError
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged

from telegram_storage import normalize_channel_username, save_channel_comments


DEFAULT_CHANNEL_NAME = "Veles_Dubov"
DEFAULT_POST_LIMIT = 10
OUTPUT_PATH = Path("data") / "telegram_comments.json"
MIN_RAW_SCAN_LIMIT = 50
MAX_RAW_SCAN_LIMIT = 500


def get_logical_post_key(message):
    """Return a stable key for a Telegram post or media album."""
    return message.grouped_id or message.id


def iso_datetime(value):
    if not value:
        return ""
    return value.isoformat()


def read_post_limit():
    raw_limit = input(f"Enter number of latest posts to scan [{DEFAULT_POST_LIMIT}]: ").strip()
    if not raw_limit:
        return DEFAULT_POST_LIMIT

    try:
        limit = int(raw_limit)
    except ValueError:
        print(f"Invalid number of posts. Using default: {DEFAULT_POST_LIMIT}")
        return DEFAULT_POST_LIMIT

    if limit <= 0:
        print(f"Number of posts must be positive. Using default: {DEFAULT_POST_LIMIT}")
        return DEFAULT_POST_LIMIT

    return limit


def calculate_max_raw_messages(requested_posts: int) -> int:
    """Return the bounded raw Telegram message scan limit."""
    return min(max(requested_posts * 10, MIN_RAW_SCAN_LIMIT), MAX_RAW_SCAN_LIMIT)


def build_client(api_id, api_hash):
    client = TelegramClient(
        "telegram_test_session",
        api_id,
        api_hash,
        connection=ConnectionTcpAbridged,
        use_ipv6=False,
        device_model="Desktop PC",
        system_version="Windows 11",
        app_version="5.2.3",
        lang_code="en",
        system_lang_code="en-US",
    )

    client.session.set_dc(2, "149.154.167.50", 443)
    return client


async def collect_logical_posts(client, channel, limit: int) -> tuple[list[dict], int]:
    """Collect latest logical posts, grouping media albums by grouped_id."""
    logical_posts = {}
    logical_order = []
    raw_messages_scanned = 0
    max_raw_messages = calculate_max_raw_messages(limit)

    async for message in client.iter_messages(channel):
        if raw_messages_scanned >= max_raw_messages:
            break

        raw_messages_scanned += 1
        post_key = get_logical_post_key(message)
        if post_key not in logical_posts:
            logical_order.append(post_key)
            replies_count = message.replies.replies if message.replies else 0
            logical_posts[post_key] = {
                "post_key": str(post_key),
                "post": message,
                "post_text": message.message or "",
                "post_date": message.date,
                "message_ids": [],
                "grouped_id": str(message.grouped_id) if message.grouped_id else "",
                "replies_count": replies_count,
            }

        logical_post = logical_posts[post_key]
        logical_post["message_ids"].append(message.id)

        replies_count = message.replies.replies if message.replies else 0
        if replies_count > logical_post["replies_count"]:
            logical_post["replies_count"] = replies_count
            logical_post["post"] = message

        if message.message and not logical_post["post_text"]:
            logical_post["post_text"] = message.message
            logical_post["post_date"] = message.date

        if len(logical_order) >= limit:
            break

    return [logical_posts[post_key] for post_key in logical_order], raw_messages_scanned


async def fetch_comments_for_post(client, channel, channel_name, logical_post):
    comments = []
    post = logical_post["post"]

    try:
        async for comment in client.iter_messages(channel, reply_to=post.id):
            if not comment.message:
                continue

            comments.append(
                {
                    "channel_name": channel_name,
                    "post_id": post.id,
                    "post_message_ids": logical_post["message_ids"],
                    "post_grouped_id": logical_post["grouped_id"],
                    "post_text": logical_post["post_text"],
                    "post_date": iso_datetime(logical_post["post_date"]),
                    "comment_id": comment.id,
                    "comment_text": comment.message,
                    "comment_date": iso_datetime(comment.date),
                    "comment_author_id": str(comment.sender_id) if comment.sender_id else "",
                }
            )
    except RPCError as error:
        print(f"Could not fetch comments for post {post.id}: {error.__class__.__name__}: {error}")

    return comments


async def collect_telegram_comments_async(channel_name: str, post_limit: int) -> dict:
    """Collect Telegram comments and save them to JSON."""
    load_dotenv()
    normalized_channel = normalize_channel_username(channel_name)

    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    client = build_client(api_id, api_hash)

    try:
        print("Connecting to Telegram DC2...")
        await client.connect()

        if not await client.is_user_authorized():
            raise RuntimeError("Telegram session is not authorized. Run src/telegram_test.py first.")

        print(f"Scanning latest {post_limit} posts from {normalized_channel}...")
        channel = await client.get_entity(normalized_channel)
        results = []
        logical_posts, raw_messages_scanned = await collect_logical_posts(
            client,
            channel,
            post_limit,
        )
        posts_with_comments = 0
        seen_comment_ids = set()

        for logical_post in logical_posts:
            replies_count = logical_post["replies_count"]
            post = logical_post["post"]

            print(f"Post ID: {post.id}")
            print(f"Related message IDs: {logical_post['message_ids']}")
            print(f"Replies/comments count: {replies_count}")

            if replies_count <= 0:
                print("Skipping comments fetch.")
                print("===")
                continue

            comments = await fetch_comments_for_post(
                client,
                channel,
                normalized_channel,
                logical_post,
            )
            unique_comments = []
            for comment in comments:
                if comment["comment_id"] in seen_comment_ids:
                    continue
                seen_comment_ids.add(comment["comment_id"])
                unique_comments.append(comment)

            if unique_comments:
                posts_with_comments += 1
                results.extend(unique_comments)

            print(f"Fetched comments: {len(unique_comments)}")
            print("===")

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        channel_output_path = save_channel_comments(
            normalized_channel,
            results,
            {
                "requested_logical_posts": post_limit,
                "raw_telegram_messages_scanned": raw_messages_scanned,
                "logical_posts_scanned": len(logical_posts),
                "posts_with_comments": posts_with_comments,
                "saved_items": len(results),
            },
        )

        return {
            "requested_logical_posts": post_limit,
            "raw_messages_scanned": raw_messages_scanned,
            "logical_posts_scanned": len(logical_posts),
            "posts_with_comments": posts_with_comments,
            "saved_comments": len(results),
            "channel_username": normalized_channel,
            "output_file": str(OUTPUT_PATH),
            "channel_output_file": str(channel_output_path),
        }
    finally:
        await client.disconnect()


def collect_telegram_comments(channel_username: str, limit: int) -> dict:
    """Synchronous wrapper for Streamlit."""
    return asyncio.run(collect_telegram_comments_async(channel_username, limit))


async def main():
    channel_name = input(
        f"Enter Telegram channel username [{DEFAULT_CHANNEL_NAME}]: "
    ).strip() or DEFAULT_CHANNEL_NAME
    post_limit = read_post_limit()

    result = await collect_telegram_comments_async(channel_name, post_limit)

    print("Final summary:")
    print(f"Requested logical posts: {result['requested_logical_posts']}")
    print(f"Raw Telegram messages scanned: {result['raw_messages_scanned']}")
    print(f"Logical posts scanned: {result['logical_posts_scanned']}")
    print(f"Posts with comments: {result['posts_with_comments']}")
    print(f"Saved comments: {result['saved_comments']}")
    print(f"Channel username: {result['channel_username']}")
    print(f"Output file: {result['output_file']}")


if __name__ == "__main__":
    asyncio.run(main())
