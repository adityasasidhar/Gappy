import json
import os
import httpx

config_path = os.path.expanduser(r"C:\Users\chmur\.lemma\config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

token = config.get("servers", {}).get("cloud", {}).get("token")
pod_id = "019f0e8c-ab84-7588-ac6e-13b7c7643469"
run_id = "019f1dc9-0556-7173-a1f0-ce547d186718" # one of the WAITING runs

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

url = f"https://api.lemma.work/pods/{pod_id}/workflow-runs/{run_id}/form"
body = {
    "node_id": "input_form",
    "inputs": {
        "task_input": "Should we approve this refund for Customer #4821? Customer tier Gold, purchase 47 days ago, policy = 30-day returns, claim = product defect, 2 prior refunds in 6 months.",
        "task_context": "{}"
    }
}

resp = httpx.post(url, json=body, headers=headers)
print(f"Status: {resp.status_code}")
try:
    print(json.dumps(resp.json(), indent=2))
except Exception:
    print(resp.text)
