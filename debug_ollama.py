"""Test direct Ollama Cloud API call."""
import httpx
import json

OLLAMA_API_KEY = "dd0d6a4161864b4c967f2f8a5e807b59.WOynu1rNk33PgQMSSvkInkwp"
OLLAMA_BASE_URL = "https://ollama.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OLLAMA_API_KEY}",
    "Content-Type": "application/json",
}
body = {
    "model": "ministral-3:3b",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant. Reply in one sentence."},
        {"role": "user", "content": "Say hello"},
    ],
    "temperature": 0.7,
    "max_tokens": 100,
}

try:
    resp = httpx.post(OLLAMA_BASE_URL, json=body, headers=headers, timeout=30.0)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        print(f"Response: {content}")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
