import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(
    'https://api.ollama.cloud/v1/chat/completions',
    headers={
        'Authorization': 'Bearer dd0d6a4161864b4c967f2f8a5e807b59.WOynu1rNk33PgQMSSvkInkwp',
        'Content-Type': 'application/json'
    },
    data=json.dumps({
        "model": "ministral-3:3b",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 10
    }).encode('utf-8')
)

try:
    with urllib.request.urlopen(req, context=ctx) as res:
        print(res.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
