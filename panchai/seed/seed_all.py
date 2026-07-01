import json
import subprocess
import sys
import re

POD = "panchai"

agents = [
    {
        "agent_name": "Policy Analyst",
        "agent_id": "policy-analyst",
        "client_id": "yesmadam",
        "capabilities": json.dumps(["policy_check", "compliance_review", "rule_interpretation", "return_policy"]),
        "reasoning_bias": "rule-following",
        "model": "ministral-3:3b"
    },
    {
        "agent_name": "Customer Advocate",
        "agent_id": "customer-advocate",
        "client_id": "yesmadam",
        "capabilities": json.dumps(["customer_sentiment", "satisfaction_analysis", "retention_strategy", "consumer_rights"]),
        "reasoning_bias": "empathetic",
        "model": "ministral-3:3b"
    },
    {
        "agent_name": "Fraud Risk Assessor",
        "agent_id": "fraud-risk-assessor",
        "client_id": "yesmadam",
        "capabilities": json.dumps(["risk_scoring", "fraud_detection", "transaction_analysis", "refund_abuse"]),
        "reasoning_bias": "conservative",
        "model": "ministral-3:3b"
    },
    {
        "agent_name": "Supply Chain Analyst",
        "agent_id": "supply-chain-analyst",
        "client_id": "binocs",
        "capabilities": json.dumps(["supply_chain_optimization", "logistics_analysis", "demand_forecasting", "inventory_management"]),
        "reasoning_bias": "operational-continuity",
        "model": "ministral-3:3b"
    },
    {
        "agent_name": "Financial Risk",
        "agent_id": "financial-risk",
        "client_id": "binocs",
        "capabilities": json.dumps(["risk_scoring", "cash_flow_analysis", "financial_modeling", "vendor_risk"]),
        "reasoning_bias": "cash-preservation",
        "model": "ministral-3:3b"
    },
    {
        "agent_name": "Procurement Specialist",
        "agent_id": "procurement-specialist",
        "client_id": "binocs",
        "capabilities": json.dumps(["vendor_management", "cost_optimization", "procurement_analysis", "order_management"]),
        "reasoning_bias": "vendor-relationship",
        "model": "ministral-3:3b"
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
        m = re.search(r'"id":\s*"([^"]+)"', out)
        if m:
            return {"id": m.group(1)}
        raise ValueError(f"Could not parse created record ID: {out}")

print("[SEED] Seeding PANCHAI with live-mode demo data...")

print("  -> Creating agent catalog...")
for a in agents:
    create_record("agent_catalog", a)

print("  -> Creating YesMadam pending debate session...")
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

print("  -> Creating Binocs pending debate session...")
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

print("  -> Pre-populating realistic verdict examples for the dashboard...")
create_record("verdicts", {
    "session_id": ym_id,
    "verdict": "ESCALATED",
    "confidence_score": 0.58,
    "council_vote_for": json.dumps(["customer-advocate"]),
    "council_vote_against": json.dumps(["policy-analyst", "fraud-risk-assessor"]),
    "council_vote_abstain": json.dumps([]),
    "council_vote_reframe": json.dumps([]),
    "conflict_report": json.dumps({
        "user_goal": "Approve the refund",
        "council_finding": "Reject or escalate pending defect verification because the request is outside the 30-day return window and has repeat-refund risk.",
        "divergence_severity": "HIGH",
        "explanation": "The council finding directly conflicts with the submitted approval goal."
    }),
    "reasoning_trail": json.dumps([
        {"round": 1, "agent": "policy-analyst", "position": "AGAINST", "argument_summary": "30-day return policy is exceeded without a documented exception."},
        {"round": 1, "agent": "customer-advocate", "position": "FOR", "argument_summary": "Gold-tier customer and defect claim justify service recovery if the defect is verified."},
        {"round": 1, "agent": "fraud-risk-assessor", "position": "AGAINST", "argument_summary": "Two prior refunds in six months raises abuse risk."}
    ]),
    "pre_mortem_summary": json.dumps([]),
    "hitl_required": True,
    "hitl_reason": "High divergence from user goal and low confidence require human review.",
    "recommended_action": "Escalate to a human approver with defect evidence and refund-history context.",
    "minority_dissent": "Customer Advocate: verify the defect before denying a loyal customer."
})

create_record("verdicts", {
    "session_id": binocs_id,
    "verdict": "REFRAMED",
    "confidence_score": 0.72,
    "council_vote_for": json.dumps([]),
    "council_vote_against": json.dumps([]),
    "council_vote_abstain": json.dumps([]),
    "council_vote_reframe": json.dumps(["supply-chain-analyst", "financial-risk", "procurement-specialist"]),
    "conflict_report": json.dumps({
        "user_goal": "Pause the vendor order",
        "council_finding": "Reframe to a partial staggered order with payment renegotiation, preserving supply coverage while easing cash pressure.",
        "divergence_severity": "MEDIUM",
        "explanation": "The council rejects the binary pause but preserves the underlying cash objective."
    }),
    "reasoning_trail": json.dumps([
        {"round": 1, "agent": "supply-chain-analyst", "position": "REFRAME", "argument_summary": "45-day lead time makes a full pause operationally risky."},
        {"round": 1, "agent": "financial-risk", "position": "REFRAME", "argument_summary": "Cash pressure is real, but staged ordering lowers risk."},
        {"round": 1, "agent": "procurement-specialist", "position": "REFRAME", "argument_summary": "Negotiate terms instead of damaging vendor reliability."}
    ]),
    "pre_mortem_summary": json.dumps([]),
    "hitl_required": False,
    "hitl_reason": "Consensus reframe with adequate confidence.",
    "recommended_action": "Proceed with a partial order and renegotiated payment terms.",
    "minority_dissent": ""
})

print("\n[SUCCESS] PANCHAI live-mode seed data loaded successfully!")
print("   6 agent_catalog entries created.")
print("   2 pending sessions created for DATASTORE_EVENT workflow processing.")
print("   2 realistic verdict examples added for immediate dashboard display.")