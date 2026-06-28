#!/usr/bin/env bash
set -euo pipefail

echo "🏛️  Seeding PANCHAI with demo data..."

POD="panchai"

# ── Insert YesMadam agent catalog ───────────────────────────────────────────
echo "  → Creating YesMadam agent catalog..."

lemma tables insert "$POD" agent_catalog \
  --data '{"agent_id":"policy_analyst","client_id":"yesmadam","capabilities":["policy_check","compliance_review","rule_interpretation","return_policy"],"reasoning_bias":"rule-following","model":"claude-3-haiku","description":"Evaluates decisions against documented policies and regulatory frameworks. Bias toward strict rule adherence."}'

lemma tables insert "$POD" agent_catalog \
  --data '{"agent_id":"customer_advocate","client_id":"yesmadam","capabilities":["customer_sentiment","satisfaction_analysis","retention_strategy","consumer_rights"],"reasoning_bias":"empathetic","model":"claude-3-haiku","description":"Champions the customer perspective, factoring satisfaction, retention, and consumer rights into deliberation."}'

lemma tables insert "$POD" agent_catalog \
  --data '{"agent_id":"fraud_risk_assessor","client_id":"yesmadam","capabilities":["risk_scoring","fraud_detection","transaction_analysis","refund_abuse"],"reasoning_bias":"conservative","model":"claude-3-haiku","description":"Identifies fraud patterns, risk signals, and abuse indicators. Bias toward conservative risk assessment."}'

# ── Insert Binocs agent catalog ─────────────────────────────────────────────
echo "  → Creating Binocs agent catalog..."

lemma tables insert "$POD" agent_catalog \
  --data '{"agent_id":"supply_chain_analyst","client_id":"binocs","capabilities":["supply_chain_optimization","logistics_analysis","demand_forecasting","inventory_management"],"reasoning_bias":"operational-efficiency","model":"claude-3-haiku","description":"Optimizes supply chain decisions by analyzing logistics, demand signals, and inventory levels."}'

lemma tables insert "$POD" agent_catalog \
  --data '{"agent_id":"financial_risk","client_id":"binocs","capabilities":["risk_scoring","cash_flow_analysis","financial_modeling","vendor_risk"],"reasoning_bias":"risk-averse","model":"claude-3-haiku","description":"Evaluates financial exposure, cash flow impact, and vendor risk. Bias toward capital preservation."}'

lemma tables insert "$POD" agent_catalog \
  --data '{"agent_id":"procurement_specialist","client_id":"binocs","capabilities":["vendor_management","cost_optimization","procurement_analysis","order_management"],"reasoning_bias":"cost-optimization","model":"claude-3-haiku","description":"Manages vendor relationships and procurement decisions. Optimizes for cost efficiency and delivery reliability."}'

# ── Insert demo debate sessions ─────────────────────────────────────────────
echo "  → Creating demo debate sessions..."
echo "    (These INSERTs trigger the debate-pipeline workflow automatically)"

lemma tables insert "$POD" debate_sessions \
  --data '{"client_id":"yesmadam","task_input":"Should we approve this refund for Customer #4821? Customer tier Gold, purchase 47 days ago, policy = 30-day returns, claim = product defect, 2 prior refunds in 6 months.","task_context":"{\"customer_tier\":\"Gold\",\"purchase_days_ago\":47,\"return_policy_days\":30,\"claim_type\":\"product_defect\",\"prior_refunds_6mo\":2}","status":"pending"}'

lemma tables insert "$POD" debate_sessions \
  --data '{"client_id":"binocs","task_input":"Should we pause this vendor order? Inventory 340 units, demand forecast 280 units, vendor reliability 62%, lead time 45 days, cash position tight.","task_context":"{\"inventory_units\":340,\"demand_forecast\":280,\"vendor_reliability_pct\":62,\"lead_time_days\":45,\"cash_position\":\"tight\"}","status":"pending"}'

echo ""
echo "✅ PANCHAI seed data loaded!"
echo "   6 agent_catalog entries (3 YesMadam + 3 Binocs)"
echo "   2 demo debate_sessions (triggers debate-pipeline workflow)"
