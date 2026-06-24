import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged


async def main():
    load_dotenv()

    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")

    channel = input("Enter channel username: ")

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

    async for message in client.iter_messages(channel, limit=5):
        text = message.message or ""
        preview = text[:300]

        print(f"Message ID: {message.id}")
        print(f"Date: {message.date}")
        print(f"Text: {preview}")
        print("---")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
