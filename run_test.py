"""Test the debate workflow by calling functions directly."""
import io
import json
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from lemma_sdk import Pod

pod = Pod.from_env()
pod._transport.generated._timeout = 600.0
task = "Should we approve a refund for a customer who bought the wrong subscription tier?"

# Step 1: goal_strip
print("Calling goal_strip...")
t0 = time.time()
gs = pod.functions.run("goal_strip", {
    "task_input": task,
    "task_context": json.dumps({"customer_type": "premium", "account_age_months": 24}),
})
elapsed = time.time() - t0
output = gs.output_data.to_dict() if hasattr(gs.output_data, 'to_dict') else (gs.output_data if isinstance(gs.output_data, dict) else {})
print(f"goal_strip OK in {elapsed:.1f}s")
print(f"  session_id: {output.get('session_id')}")
print(f"  stripped_task: {str(output.get('stripped_task', ''))[:60]}...")
print(f"  user_goal: {output.get('user_goal')}")
print(f"  stakes_level: {output.get('stakes_level')}")

# Step 2: fast_pipeline
session_id = output["session_id"]
print(f"\nCalling fast_pipeline (session_id={session_id})...")
print("This may take up to 5 minutes...")
t0 = time.time()
try:
    result = pod.functions.run("fast_pipeline", {
        "session_id": session_id,
        "stripped_task": output["stripped_task"],
        "user_goal": output["user_goal"],
        "client_id": output.get("client_id"),
        "stakes_level": output.get("stakes_level", "STANDARD"),
        "council_size": 2,
    })
    elapsed = time.time() - t0
    print(f"fast_pipeline completed in {elapsed:.1f}s")
    print(f"Status: {result.status}")
    print(f"Error: {result.error}")
    print(f"Output type: {type(result.output_data).__name__}")
    od = result.output_data
    r = od.to_dict() if hasattr(od, 'to_dict') else (od if isinstance(od, dict) else {})
    verdict = r.get('verdict', {})
    print(f"  verdict: {verdict.get('verdict', 'N/A')}")
    print(f"  confidence: {verdict.get('confidence_score', 'N/A')}")
    print(f"  consensus_met: {verdict.get('consensus_met', 'N/A')}")
    print(f"  hitl_required: {verdict.get('hitl_required', 'N/A')}")
    print(f"  mode: {r.get('mode')}")
    print(f"  council_responses ({len(r.get('council_responses', []))}):")
    for cr in r.get("council_responses", []):
        print(f"    {cr.get('agent_id')}: {cr.get('position')} (conf={cr.get('confidence')})")
        print(f"      argument: {str(cr.get('argument', ''))[:200]}")
except Exception as e:
    elapsed = time.time() - t0
    print(f"fast_pipeline FAILED after {elapsed:.1f}s: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
