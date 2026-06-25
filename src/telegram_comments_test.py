import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import RPCError
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged


DEFAULT_CHANNEL_NAME = "Veles_Dubov"
POST_LIMIT = 10
OUTPUT_PATH = Path("data") / "telegram_comments_test.json"


def preview_text(text, limit=120):
    text = (text or "").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


def iso_datetime(value):
    if not value:
        return ""
    return value.isoformat()


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
                }
            )
    except RPCError as error:
        print(f"Could not fetch comments for post {post.id}: {error.__class__.__name__}: {error}")

    return comments


async def main():
    load_dotenv()

    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    channel_name = input(
        f"Enter Telegram channel username [{DEFAULT_CHANNEL_NAME}]: "
    ).strip() or DEFAULT_CHANNEL_NAME

    client = build_client(api_id, api_hash)

    print("Connecting to Telegram DC2...")
    await client.connect()

    if not await client.is_user_authorized():
        print("Telegram session is not authorized. Run src/telegram_test.py first.")
        await client.disconnect()
        return

    print(f"Fetching latest {POST_LIMIT} posts from {channel_name}...")
    channel = await client.get_entity(channel_name)
    results = []

    async for post in client.iter_messages(channel, limit=POST_LIMIT):
        post_preview = preview_text(post.message)
        replies_count = post.replies.replies if post.replies else 0
        has_comments = bool(post.replies and replies_count > 0)

        print(f"Post ID: {post.id}")
        print(f"Post text: {post_preview}")
        print(f"Replies/comments count: {replies_count}")

        if not has_comments:
            print("No replies/comments reported for this post; skipping comments fetch.")
            print("===")
            continue

        comments = await fetch_comments_for_post(client, channel, channel_name, post)
        for comment in comments:
            print(f"Parent post ID: {comment['post_id']}")
            print(f"Comment ID: {comment['comment_id']}")
            print(f"Comment text: {preview_text(comment['comment_text'])}")
            print(f"Comment date: {comment['comment_date']}")
            print("---")

        results.extend(comments)
        print("===")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if not results:
        print("No comments found for latest posts.")

    print(f"Saved comments: {len(results)}")
    print(f"Output file: {OUTPUT_PATH}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
