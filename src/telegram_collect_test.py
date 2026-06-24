import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged


async def main():
    load_dotenv()

    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")

    channel = input("Enter channel username: ")
    limit = int(input("Enter message limit: "))

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

    await client.connect()

    if not await client.is_user_authorized():
        print("Telegram session is not authorized. Run src/telegram_test.py first.")
        await client.disconnect()
        return

    messages = []

    async for message in client.iter_messages(channel, limit=limit):
        if not message.message:
            continue

        messages.append(
            {
                "channel_name": channel,
                "message_id": message.id,
                "message_text": message.message,
                "message_date": message.date.date().isoformat(),
            }
        )

    output_path = Path("data") / "telegram_messages.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(messages, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Saved messages: {len(messages)}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
