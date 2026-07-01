import json
import os
import httpx

config_path = os.path.expanduser(r"C:\Users\chmur\.lemma\config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

token = config.get("servers", {}).get("cloud", {}).get("token")
pod_id = "panchai"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

url = f"https://api.lemma.work/pods/{pod_id}/workflows"

resp = httpx.get(url, headers=headers)
print(f"Status: {resp.status_code}")
try:
    print(resp.json())
except Exception:
    print(resp.text)
