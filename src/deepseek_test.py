import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv


API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-flash"
PROMPT = "Ответь одним словом: работает."


def main():
    load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not found.")
        return

    print("DeepSeek API key loaded.")

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": PROMPT},
        ],
        "stream": False,
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = response.status
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        print(f"HTTP status: {error.code}")
        print(f"Request failed: {error}")
        print(error_body)
        return
    except Exception as error:
        print(f"Request failed: {error}")
        return

    data = json.loads(response_body)
    assistant_response = data.get("choices", [{}])[0].get("message", {}).get("content", "")

    print(f"HTTP status: {status}")
    print(f"Model: {data.get('model', '')}")
    print(f"Assistant response: {assistant_response}")


if __name__ == "__main__":
    main()
