"""Test direct Ollama Cloud call with encoding-safe output."""
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
        {"role": "system", "content": "You are a Policy Analyst on a deliberation council. Output ONLY valid JSON with fields: position (FOR/AGAINST/ABSTAIN/REFRAME), argument (string), confidence (0.0-1.0), key_evidence (string). No markdown, no extra text."},
        {"role": "user", "content": "Task: Customer requests a refund for a $50 late fee.\n\nConduct a pre-mortem analysis on this task, then form your position."},
    ],
    "temperature": 0.7,
    "max_tokens": 1024,
}

try:
    resp = httpx.post(OLLAMA_BASE_URL, json=body, headers=headers, timeout=60.0)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        print(f"Response ({len(content)} chars):")
        print(repr(content))
        # Try to parse JSON
        import re
        bs = content.find("{")
        be = content.rfind("}")
        if bs >= 0 and be > bs:
            jstr = content[bs:be+1]
            try:
                parsed = json.loads(jstr)
                print(f"Parsed: {json.dumps(parsed, indent=2)}")
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
        else:
            print("No JSON found in response")
    else:
        print(f"Error: {resp.text[:500]}")
except Exception as e:
    import traceback
    traceback.print_exc()
