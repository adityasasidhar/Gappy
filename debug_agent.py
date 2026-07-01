"""Debug agent call directly."""
import json, time, sys
from lemma_sdk import Pod

pod = Pod.from_env()
pod._transport.generated._timeout = 120.0

agent_id = "policy-analyst"
print(f"1. Testing create_for_agent('{agent_id}')...")
t0 = time.time()
try:
    conv = pod.conversations.create_for_agent(agent_id, title="debug-test")
    conv_id = str(conv.to_dict()["id"])
    print(f"   OK in {time.time()-t0:.1f}s, conv_id={conv_id}")
except Exception as e:
    print(f"   FAILED: {type(e).__name__}: {e}")
    sys.exit(1)

print(f"2. Testing send_stream...")
t0 = time.time()
try:
    resp = pod.conversations.send_stream(conv_id, "Return just the word hello and nothing else.")
    print(f"   send_stream returned in {time.time()-t0:.1f}s")
    for raw in resp.iter_lines():
        line = raw.decode() if isinstance(raw, bytes) else raw
        if line.startswith("data: "):
            try:
                event = json.loads(line[6:])
                print(f"   SSE event type={event.get('type')}")
                if event.get("type") == "completed":
                    data = event.get("data", {}) or {}
                    output = data.get("output_data") or {}
                    print(f"   output_data={json.dumps(output, indent=2)[:500]}")
                    break
            except json.JSONDecodeError:
                pass
    print(f"   Done in {time.time()-t0:.1f}s")
except Exception as e:
    print(f"   FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
