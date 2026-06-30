import json
import subprocess
import sys
import re

POD = "panchai"

agents = [
    {
        "agent_name": "Policy Analyst",
        "agent_id": "policy_analyst",
        "client_id": "yesmadam",
        "capabilities": json.dumps(["policy_check", "compliance_review", "rule_interpretation", "return_policy"]),
        "reasoning_bias": "rule-following",
        "model": "claude-3-haiku"
    },
    {
        "agent_name": "Customer Advocate",
        "agent_id": "customer_advocate",
        "client_id": "yesmadam",
        "capabilities": json.dumps(["customer_sentiment", "satisfaction_analysis", "retention_strategy", "consumer_rights"]),
        "reasoning_bias": "empathetic",
        "model": "claude-3-haiku"
    },
    {
        "agent_name": "Fraud Risk Assessor",
        "agent_id": "fraud_risk_assessor",
        "client_id": "yesmadam",
        "capabilities": json.dumps(["risk_scoring", "fraud_detection", "transaction_analysis", "refund_abuse"]),
        "reasoning_bias": "conservative",
        "model": "claude-3-haiku"
    },
    {
        "agent_name": "Supply Chain Analyst",
        "agent_id": "supply_chain_analyst",
        "client_id": "binocs",
        "capabilities": json.dumps(["supply_chain_optimization", "logistics_analysis", "demand_forecasting", "inventory_management"]),
        "reasoning_bias": "operational-efficiency",
        "model": "claude-3-haiku"
    },
    {
        "agent_name": "Financial Risk",
        "agent_id": "financial_risk",
        "client_id": "binocs",
        "capabilities": json.dumps(["risk_scoring", "cash_flow_analysis", "financial_modeling", "vendor_risk"]),
        "reasoning_bias": "risk-averse",
        "model": "claude-3-haiku"
    },
    {
        "agent_name": "Procurement Specialist",
        "agent_id": "procurement_specialist",
        "client_id": "binocs",
        "capabilities": json.dumps(["vendor_management", "cost_optimization", "procurement_analysis", "order_management"]),
        "reasoning_bias": "cost-optimization",
        "model": "claude-3-haiku"
    }
]

def run_lemma(args):
    cmd = ["lemma"] + args
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if res.returncode != 0:
        print(f"Error running lemma command: {cmd}")
        print(f"Stdout: {res.stdout}")
        print(f"Stderr: {res.stderr}")
        sys.exit(1)
    return res.stdout

def create_record(table, data):
    payload = json.dumps(data)
    out = run_lemma(["--pod", POD, "records", "create", table, "--data", payload, "--json"])
    try:
        return json.loads(out)
    except Exception:
        # Fallback to regex ID finder if JSON load fails
        m = re.search(r'"id":\s*"([^"]+)"', out)
        if m:
            return {"id": m.group(1)}
        raise ValueError(f"Could not parse created record ID: {out}")

print("[SEED] Seeding PANCHAI with demo data (Python engine)...")

# 1. Create agent catalog entries
print("  -> Creating agent catalog...")
for a in agents:
    create_record("agent_catalog", a)

# 2. Insert YesMadam session
print("  -> Creating YesMadam debate session...")
ym_data = {
    "client_id": "yesmadam",
    "task_input": "Should we approve this refund for Customer #4821? Customer tier Gold, purchase 47 days ago, policy = 30-day returns, claim = product defect, 2 prior refunds in 6 months.",
    "task_context": json.dumps({
        "customer_tier": "Gold",
        "purchase_days_ago": 47,
        "return_policy_days": 30,
        "claim_type": "product_defect",
        "prior_refunds_6mo": 2
    }),
    "status": "pending"
}
ym_rec = create_record("debate_sessions", ym_data)
ym_id = ym_rec["id"]

print(f"  -> Running pipeline for YesMadam (ID: {ym_id})...")
run_lemma(["--pod", POD, "functions", "run", "run_pipeline", "--data", json.dumps({"session_id": ym_id}), "--no-wait"])

# 3. Insert Binocs session
print("  -> Creating Binocs debate session...")
binocs_data = {
    "client_id": "binocs",
    "task_input": "Should we pause this vendor order? Inventory 340 units, demand forecast 280 units, vendor reliability 62%, lead time 45 days, cash position tight.",
    "task_context": json.dumps({
        "inventory_units": 340,
        "demand_forecast": 280,
        "vendor_reliability_pct": 62,
        "lead_time_days": 45,
        "cash_position": "tight"
    }),
    "status": "pending"
}
binocs_rec = create_record("debate_sessions", binocs_data)
binocs_id = binocs_rec["id"]

print(f"  -> Running pipeline for Binocs (ID: {binocs_id})...")
run_lemma(["--pod", POD, "functions", "run", "run_pipeline", "--data", json.dumps({"session_id": binocs_id}), "--no-wait"])

print("\n[SUCCESS] PANCHAI seed data loaded successfully!")
print("   6 agent_catalog entries created.")
print("   2 debate sessions initialized and processed in the pipeline.")
