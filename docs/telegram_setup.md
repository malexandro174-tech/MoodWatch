# Telegram Setup (MoodWatch)

## Полученные данные

Используются переменные из .env:

TELEGRAM_API_ID
TELEGRAM_API_HASH

Секретные значения не хранить в репозитории.

---

## Симптом проблемы

После получения API ID и API HASH через my.telegram.org:

- Telethon подключался к серверу
- код авторизации не приходил
- соединение периодически разрывалось
- возникали ошибки:
  - Server closed the connection
  - ConnectionResetError
  - AuthRestartError

---

## Что НЕ помогло

- повторные запросы кода
- VPN
- отключение VPN
- очистка DNS
- изменение hosts
- переустановка Telethon

---

## Что помогло

Использовать TelegramClient с фиксированным fingerprint устройства:

device_model="Desktop PC"
system_version="Windows 11"
app_version="5.2.3"
lang_code="en"
system_lang_code="en-US"

После добавления fingerprint:

- код авторизации начал приходить
- авторизация завершилась успешно
- создалась рабочая session

---

## Проверка подключения

Команда:

python src/telegram_test.py

Ожидаемый результат:

Telegram authorization successful

или

User ID: ...
Username: ...
First name: ...

---

## Рабочая сессия

Файл:

telegram_test_session.session

Не добавлять в GitHub.

---

## Важное

Если проект переносится на другой компьютер:

1. Скопировать .env
2. Скопировать telegram_test_session.session

Либо пройти авторизацию заново.

---

## Статус

Telegram API подключён.
Telethon работает.
Авторизация успешна.
Проект готов к чтению каналов.
