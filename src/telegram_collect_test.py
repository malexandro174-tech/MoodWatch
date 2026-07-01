import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged

from telegram_storage import normalize_channel_username, save_channel_posts


OUTPUT_PATH = Path("data") / "telegram_messages.json"


def get_logical_post_key(message):
    """Return a stable key for a Telegram post or media album."""
    return message.grouped_id or message.id


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


async def collect_logical_posts(client, channel_username: str, limit: int) -> tuple[list[dict], int]:
    """Collect latest logical posts, grouping media albums by grouped_id."""
    logical_posts = {}
    logical_order = []
    raw_messages_scanned = 0

    async for message in client.iter_messages(channel_username):
        post_key = get_logical_post_key(message)
        if post_key not in logical_posts:
            if len(logical_order) >= limit:
                break

            logical_order.append(post_key)
            logical_posts[post_key] = {
                "channel_name": channel_username,
                "message_id": message.id,
                "message_ids": [],
                "message_text": "",
                "message_date": message.date.date().isoformat(),
                "grouped_id": str(message.grouped_id) if message.grouped_id else "",
            }

        raw_messages_scanned += 1
        logical_post = logical_posts[post_key]
        logical_post["message_ids"].append(message.id)

        if message.message and not logical_post["message_text"]:
            logical_post["message_text"] = message.message
            logical_post["message_id"] = message.id
            logical_post["message_date"] = message.date.date().isoformat()

    messages = [
        logical_posts[post_key]
        for post_key in logical_order
        if logical_posts[post_key]["message_text"]
    ]
    return messages, raw_messages_scanned


async def collect_telegram_posts_async(channel_username: str, limit: int) -> dict:
    """Collect latest Telegram channel posts and save them to JSON."""
    load_dotenv()
    normalized_channel = normalize_channel_username(channel_username)

    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    client = build_client(api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            raise RuntimeError("Telegram session is not authorized. Run src/telegram_test.py first.")

        messages, raw_messages_scanned = await collect_logical_posts(
            client,
            normalized_channel,
            limit,
        )

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(
            json.dumps(messages, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        channel_output_path = save_channel_posts(
            normalized_channel,
            messages,
            {
                "requested_logical_posts": limit,
                "raw_telegram_messages_scanned": raw_messages_scanned,
                "logical_posts_scanned": len(messages),
                "posts_with_comments": 0,
                "saved_items": len(messages),
            },
        )

        return {
            "requested_logical_posts": limit,
            "raw_messages_scanned": raw_messages_scanned,
            "logical_posts_scanned": len(messages),
            "saved_posts": len(messages),
            "channel_username": normalized_channel,
            "output_file": str(OUTPUT_PATH),
            "channel_output_file": str(channel_output_path),
        }
    finally:
        await client.disconnect()


def collect_telegram_posts(channel_username: str, limit: int) -> dict:
    """Synchronous wrapper for Streamlit and simple scripts."""
    return asyncio.run(collect_telegram_posts_async(channel_username, limit))


async def main():
    channel = input("Enter channel username: ")
    limit = int(input("Enter message limit: "))

    result = await collect_telegram_posts_async(channel, limit)
    print("Final summary:")
    print(f"Raw Telegram messages scanned: {result['raw_messages_scanned']}")
    print(f"Logical posts scanned: {result['logical_posts_scanned']}")
    print(f"Saved posts: {result['saved_posts']}")
    print(f"Output file: {result['output_file']}")



if __name__ == "__main__":
    asyncio.run(main())
