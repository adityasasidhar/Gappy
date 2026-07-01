"""Quick test of create_for_agent + send_stream."""
import json
import time
from lemma_sdk import Pod

pod = Pod.from_env()
pod._transport.generated._timeout = 120.0

# Test 1: policy-analyst
print("=== Testing policy-analyst ===")
t0 = time.time()
conv = pod.conversations.create_for_agent("policy-analyst", title="test-pa")
conv_id = str(conv.to_dict()["id"])
print(f"create_for_agent OK in {time.time()-t0:.1f}s, conv_id={conv_id}")

t0 = time.time()
resp = pod.conversations.send_stream(conv_id, "Return just the word hello and nothing else.")
found = False
for raw in resp.iter_lines():
    line = raw.decode() if isinstance(raw, bytes) else raw
    if not line.startswith("data: "):
        continue
    try:
        event = json.loads(line[6:])
        if event.get("type") == "completed":
            found = True
            data = event.get("data", {}) or {}
            output = data.get("output_data") or {}
            print(f"completed output: {json.dumps(output, indent=2)[:500]}")
    except json.JSONDecodeError:
        continue
print(f"send_stream completed in {time.time()-t0:.1f}s, found_completed={found}")

# Test 2: customer-advocate
print("\n=== Testing customer-advocate ===")
t0 = time.time()
conv2 = pod.conversations.create_for_agent("customer-advocate", title="test-ca")
conv_id2 = str(conv2.to_dict()["id"])
print(f"create_for_agent OK in {time.time()-t0:.1f}s, conv_id={conv_id2}")

t0 = time.time()
resp2 = pod.conversations.send_stream(conv_id2, "Return just the word hello and nothing else.")
found2 = False
for raw in resp2.iter_lines():
    line = raw.decode() if isinstance(raw, bytes) else raw
    if not line.startswith("data: "):
        continue
    try:
        event = json.loads(line[6:])
        if event.get("type") == "completed":
            found2 = True
            data = event.get("data", {}) or {}
            output = data.get("output_data") or {}
            print(f"completed output: {json.dumps(output, indent=2)[:500]}")
    except json.JSONDecodeError:
        continue
print(f"send_stream completed in {time.time()-t0:.1f}s, found_completed={found2}")
