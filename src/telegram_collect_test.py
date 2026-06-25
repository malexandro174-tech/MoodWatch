import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged


OUTPUT_PATH = Path("data") / "telegram_messages.json"


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


async def collect_telegram_posts_async(channel_username: str, limit: int) -> int:
    """Collect latest Telegram channel posts and save them to JSON."""
    load_dotenv()

    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    client = build_client(api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            raise RuntimeError("Telegram session is not authorized. Run src/telegram_test.py first.")

        messages = []

        async for message in client.iter_messages(channel_username, limit=limit):
            if not message.message:
                continue

            messages.append(
                {
                    "channel_name": channel_username,
                    "message_id": message.id,
                    "message_text": message.message,
                    "message_date": message.date.date().isoformat(),
                }
            )

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(
            json.dumps(messages, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return len(messages)
    finally:
        await client.disconnect()


def collect_telegram_posts(channel_username: str, limit: int) -> int:
    """Synchronous wrapper for Streamlit and simple scripts."""
    return asyncio.run(collect_telegram_posts_async(channel_username, limit))


async def main():
    channel = input("Enter channel username: ")
    limit = int(input("Enter message limit: "))

    saved_count = await collect_telegram_posts_async(channel, limit)
    print(f"Saved messages: {saved_count}")



if __name__ == "__main__":
    asyncio.run(main())
