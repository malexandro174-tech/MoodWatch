import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import RPCError
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged


DEFAULT_CHANNEL_NAME = "Veles_Dubov"
DEFAULT_POST_LIMIT = 10
OUTPUT_PATH = Path("data") / "telegram_comments.json"


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


async def fetch_comments_for_post(client, channel, channel_name, post):
    comments = []

    try:
        async for comment in client.iter_messages(channel, reply_to=post.id):
            if not comment.message:
                continue

            comments.append(
                {
                    "channel_name": channel_name,
                    "post_id": post.id,
                    "post_text": post.message or "",
                    "post_date": iso_datetime(post.date),
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

    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    client = build_client(api_id, api_hash)

    try:
        print("Connecting to Telegram DC2...")
        await client.connect()

        if not await client.is_user_authorized():
            raise RuntimeError("Telegram session is not authorized. Run src/telegram_test.py first.")

        print(f"Scanning latest {post_limit} posts from {channel_name}...")
        channel = await client.get_entity(channel_name)
        results = []
        scanned_posts = 0
        posts_with_comments = 0

        async for post in client.iter_messages(channel, limit=post_limit):
            scanned_posts += 1
            replies_count = post.replies.replies if post.replies else 0

            print(f"Post ID: {post.id}")
            print(f"Replies/comments count: {replies_count}")

            if replies_count <= 0:
                print("Skipping comments fetch.")
                print("===")
                continue

            comments = await fetch_comments_for_post(client, channel, channel_name, post)
            if comments:
                posts_with_comments += 1
                results.extend(comments)

            print(f"Fetched comments: {len(comments)}")
            print("===")

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return {
            "scanned_posts": scanned_posts,
            "posts_with_comments": posts_with_comments,
            "saved_comments": len(results),
            "output_file": str(OUTPUT_PATH),
        }
    finally:
        await client.disconnect()


def collect_telegram_comments(channel_username: str, limit: int) -> int:
    """Synchronous wrapper for Streamlit."""
    result = asyncio.run(collect_telegram_comments_async(channel_username, limit))
    return int(result["saved_comments"])


async def main():
    channel_name = input(
        f"Enter Telegram channel username [{DEFAULT_CHANNEL_NAME}]: "
    ).strip() or DEFAULT_CHANNEL_NAME
    post_limit = read_post_limit()

    result = await collect_telegram_comments_async(channel_name, post_limit)

    print("Final summary:")
    print(f"Scanned posts: {result['scanned_posts']}")
    print(f"Posts with comments: {result['posts_with_comments']}")
    print(f"Saved comments: {result['saved_comments']}")
    print(f"Output file: {result['output_file']}")


if __name__ == "__main__":
    asyncio.run(main())
