import json
import os
import httpx

config_path = os.path.expanduser(r"C:\Users\chmur\.lemma\config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

token = config.get("servers", {}).get("cloud", {}).get("token")
pod_id = "019f0e8c-ab84-7588-ac6e-13b7c7643469"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

url = f"https://api.lemma.work/pods/{pod_id}/workflows/debate-pipeline/runs"

resp = httpx.get(url, headers=headers)
print(f"Status: {resp.status_code}")
data = resp.json()
items = data.get("items", [])
print(f"Runs count: {len(items)}")
for r in items[:10]:
    run_id = r.get("id")
    print(f"\nRun {run_id}: status={r.get('status')}, created_at={r.get('created_at')}")
    # Get details
    detail_url = f"https://api.lemma.work/pods/{pod_id}/workflow-runs/{run_id}"
    detail_resp = httpx.get(detail_url, headers=headers)
    detail = detail_resp.json()
    print(f"  Active wait: {detail.get('active_wait')}")
    steps = detail.get("steps", [])
    print(f"  Steps ({len(steps)}):")
    for s in steps:
        print(f"    Node: {s.get('node_id')} | Status: {s.get('status')} | Error: {s.get('error')}")
