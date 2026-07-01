"""Test _call_llm locally with detailed error info."""
import json, httpx, os, traceback

OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY") or "dd0d6a4161864b4c967f2f8a5e807b59.WOynu1rNk33PgQMSSvkInkwp"
OLLAMA_BASE_URL = "https://ollama.com/v1/chat/completions"

print(f"API Key present: {bool(OLLAMA_API_KEY)}")
print(f"First 10 chars: {OLLAMA_API_KEY[:10]}...")

headers = {
    "Authorization": f"Bearer {OLLAMA_API_KEY}",
    "Content-Type": "application/json",
}
body = {
    "model": "ministral-3:3b",
    "messages": [
        {"role": "system", "content": "You are a Policy Analyst. Return a SINGLE JSON object with fields: position (FOR/AGAINST/ABSTAIN/REFRAME), argument (string), confidence (0.0-1.0), key_evidence (string). Only one JSON object."},
        {"role": "user", "content": "Task: Customer wants a refund for a late fee.\n\nConduct a pre-mortem analysis, then form your position."},
    ],
    "temperature": 0.7,
    "max_tokens": 1024,
}

try:
    resp = httpx.post(OLLAMA_BASE_URL, json=body, headers=headers, timeout=120.0)
    print(f"\nStatus: {resp.status_code}")
    print(f"Headers: {dict(resp.headers)}")
    if resp.status_code == 200:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        print(f"\nResponse length: {len(content)} chars")
        print(f"Response:\n{content[:500]}")
    else:
        print(f"Error body: {resp.text[:1000]}")
except Exception as e:
    traceback.print_exc()
