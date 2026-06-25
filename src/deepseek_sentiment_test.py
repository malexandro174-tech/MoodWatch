import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv


API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-flash"
COMMENTS_PATH = Path("data") / "telegram_comments.json"
OUTPUT_JSON_PATH = Path("data") / "deepseek_sentiment_test.json"
OUTPUT_RAW_PATH = Path("data") / "deepseek_sentiment_raw.txt"
COMMENTS_LIMIT = 20


def load_test_comments():
    with COMMENTS_PATH.open("r", encoding="utf-8") as file:
        comments = json.load(file)

    if not isinstance(comments, list):
        raise ValueError("data/telegram_comments.json must contain a list.")

    test_comments = []
    for comment in comments:
        text = str(comment.get("comment_text", "")).strip()
        if not text:
            continue

        test_comments.append(
            {
                "id": str(comment.get("comment_id", "")),
                "text": text,
            }
        )

        if len(test_comments) >= COMMENTS_LIMIT:
            break

    return test_comments


def build_prompt(comments):
    comments_json = json.dumps(comments, ensure_ascii=False, indent=2)
    return (
        "Классифицируй настроение Telegram-комментариев. "
        "Для каждого комментария выбери только один sentiment: "
        "positive, neutral или negative. "
        "Верни строгий JSON без markdown и пояснений в формате:\n"
        "{\n"
        '  "items": [\n'
        "    {\n"
        '      "id": "...",\n'
        '      "text": "...",\n'
        '      "sentiment": "positive|neutral|negative"\n'
        "    }\n"
        "  ],\n"
        '  "summary": {\n'
        '    "positive": 0,\n'
        '    "neutral": 0,\n'
        '    "negative": 0,\n'
        '    "dominant_sentiment": "..."\n'
        "  }\n"
        "}\n\n"
        f"Комментарии:\n{comments_json}"
    )


def call_deepseek(api_key, comments):
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты классификатор тональности. Отвечай только валидным JSON."
                ),
            },
            {"role": "user", "content": build_prompt(comments)},
        ],
        "response_format": {"type": "json_object"},
        "stream": False,
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        response_body = response.read().decode("utf-8")

    data = json.loads(response_body)
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")


def save_response(raw_response):
    try:
        parsed_response = json.loads(raw_response)
    except json.JSONDecodeError:
        OUTPUT_RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_RAW_PATH.write_text(raw_response, encoding="utf-8")
        print(f"Could not parse JSON. Raw response saved to: {OUTPUT_RAW_PATH}")
        return

    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON_PATH.write_text(
        json.dumps(parsed_response, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Parsed JSON saved to: {OUTPUT_JSON_PATH}")


def main():
    load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not found.")
        return

    try:
        comments = load_test_comments()
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"Could not load comments: {error}")
        return

    if not comments:
        print("No non-empty comments found.")
        return

    try:
        raw_response = call_deepseek(api_key, comments)
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        print(f"Request failed: {error}")
        print(error_body)
        return
    except Exception as error:
        print(f"Request failed: {error}")
        return

    print(raw_response)
    save_response(raw_response)


if __name__ == "__main__":
    main()
