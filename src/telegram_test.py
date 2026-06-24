import asyncio
import os
from getpass import getpass

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged


async def main():
    load_dotenv()

    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    proxy_host = os.getenv("TELEGRAM_PROXY_HOST")
    proxy_port = os.getenv("TELEGRAM_PROXY_PORT")
    proxy_username = os.getenv("TELEGRAM_PROXY_USERNAME")
    proxy_password = os.getenv("TELEGRAM_PROXY_PASSWORD")

    proxy = None
    if proxy_host and proxy_port:
        proxy = {
            "proxy_type": "socks5",
            "addr": proxy_host,
            "port": int(proxy_port),
            "username": proxy_username or None,
            "password": proxy_password or None,
        }
        print("Proxy mode: enabled")
    else:
        print("Proxy mode: disabled")

    print("Device fingerprint enabled")

    client = TelegramClient(
        "telegram_test_session",
        api_id,
        api_hash,
        connection=ConnectionTcpAbridged,
        use_ipv6=False,
        proxy=proxy,
        device_model="Desktop PC",
        system_version="Windows 11",
        app_version="5.2.3",
        lang_code="en",
        system_lang_code="en-US",
    )

    client.session.set_dc(2, "149.154.167.50", 443)

    print("Connecting to Telegram DC2...")
    await client.connect()
    print("Connected")

    if not await client.is_user_authorized():
        phone = input("Enter phone: ")
        print("Sending login code...")
        await client.send_code_request(phone)
        print("Login code sent")

        code = input("Enter code: ")
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            print("2FA password required")
            password = getpass("Enter 2FA password: ")
            await client.sign_in(password=password)

    me = await client.get_me()
    print("Telegram connection test successful")
    print(f"User ID: {me.id}")
    print(f"Username: {me.username}")
    print(f"First name: {me.first_name}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
