$ErrorActionPreference = "Stop"

Write-Host "🏛️  Seeding PANCHAI with demo data..." -ForegroundColor Cyan

$POD = "panchai"

# ── Insert YesMadam agent catalog ───────────────────────────────────────────
Write-Host "  → Creating YesMadam agent catalog..." -ForegroundColor Yellow

# Use a hashtable converted to JSON to avoid escaping issues in PowerShell
$policyAnalyst = @{
    agent_id = "policy_analyst"
    client_id = "yesmadam"
    capabilities = @("policy_check", "compliance_review", "rule_interpretation", "return_policy")
    reasoning_bias = "rule-following"
    model = "claude-3-haiku"
    description = "Evaluates decisions against documented policies and regulatory frameworks. Bias toward strict rule adherence."
} | ConvertTo-Json -Compress

lemma tables insert $POD agent_catalog --data $policyAnalyst

$customerAdvocate = @{
    agent_id = "customer_advocate"
    client_id = "yesmadam"
    capabilities = @("customer_sentiment", "satisfaction_analysis", "retention_strategy", "consumer_rights")
    reasoning_bias = "empathetic"
    model = "claude-3-haiku"
    description = "Champions the customer perspective, factoring satisfaction, retention, and consumer rights into deliberation."
} | ConvertTo-Json -Compress

lemma tables insert $POD agent_catalog --data $customerAdvocate

$fraudRiskAssessor = @{
    agent_id = "fraud_risk_assessor"
    client_id = "yesmadam"
    capabilities = @("risk_scoring", "fraud_detection", "transaction_analysis", "refund_abuse")
    reasoning_bias = "conservative"
    model = "claude-3-haiku"
    description = "Identifies fraud patterns, risk signals, and abuse indicators. Bias toward conservative risk assessment."
} | ConvertTo-Json -Compress

lemma tables insert $POD agent_catalog --data $fraudRiskAssessor

# ── Insert Binocs agent catalog ─────────────────────────────────────────────
Write-Host "  → Creating Binocs agent catalog..." -ForegroundColor Yellow

$supplyChainAnalyst = @{
    agent_id = "supply_chain_analyst"
    client_id = "binocs"
    capabilities = @("supply_chain_optimization", "logistics_analysis", "demand_forecasting", "inventory_management")
    reasoning_bias = "operational-efficiency"
    model = "claude-3-haiku"
    description = "Optimizes supply chain decisions by analyzing logistics, demand signals, and inventory levels."
} | ConvertTo-Json -Compress

lemma tables insert $POD agent_catalog --data $supplyChainAnalyst

$financialRisk = @{
    agent_id = "financial_risk"
    client_id = "binocs"
    capabilities = @("risk_scoring", "cash_flow_analysis", "financial_modeling", "vendor_risk")
    reasoning_bias = "risk-averse"
    model = "claude-3-haiku"
    description = "Evaluates financial exposure, cash flow impact, and vendor risk. Bias toward capital preservation."
} | ConvertTo-Json -Compress

lemma tables insert $POD agent_catalog --data $financialRisk

$procurementSpecialist = @{
    agent_id = "procurement_specialist"
    client_id = "binocs"
    capabilities = @("vendor_management", "cost_optimization", "procurement_analysis", "order_management")
    reasoning_bias = "cost-optimization"
    model = "claude-3-haiku"
    description = "Manages vendor relationships and procurement decisions. Optimizes for cost efficiency and delivery reliability."
} | ConvertTo-Json -Compress

lemma tables insert $POD agent_catalog --data $procurementSpecialist

# ── Insert demo debate sessions ─────────────────────────────────────────────
Write-Host "  → Creating demo debate sessions..." -ForegroundColor Yellow
Write-Host "    (These INSERTs trigger the debate-pipeline workflow automatically)" -ForegroundColor DarkGray

$yesMadamSession = @{
    client_id = "yesmadam"
    task_input = "Should we approve this refund for Customer #4821? Customer tier Gold, purchase 47 days ago, policy = 30-day returns, claim = product defect, 2 prior refunds in 6 months."
    task_context = (@{
        customer_tier = "Gold"
        purchase_days_ago = 47
        return_policy_days = 30
        claim_type = "product_defect"
        prior_refunds_6mo = 2
    } | ConvertTo-Json -Compress -Depth 10)
    status = "pending"
} | ConvertTo-Json -Compress

# Workaround for passing JSON strings within JSON properties on command line for lemma CLI in powershell
# We construct the JSON directly or escape it properly.
# Often powershell quoting gets messy, so passing a single well-escaped string is safer.
$ymData = '{"client_id":"yesmadam","task_input":"Should we approve this refund for Customer #4821? Customer tier Gold, purchase 47 days ago, policy = 30-day returns, claim = product defect, 2 prior refunds in 6 months.","task_context":"{\"customer_tier\":\"Gold\",\"purchase_days_ago\":47,\"return_policy_days\":30,\"claim_type\":\"product_defect\",\"prior_refunds_6mo\":2}","status":"pending"}'

lemma tables insert $POD debate_sessions --data $ymData

$binocsData = '{"client_id":"binocs","task_input":"Should we pause this vendor order? Inventory 340 units, demand forecast 280 units, vendor reliability 62%, lead time 45 days, cash position tight.","task_context":"{\"inventory_units\":340,\"demand_forecast\":280,\"vendor_reliability_pct\":62,\"lead_time_days\":45,\"cash_position\":\"tight\"}","status":"pending"}'

lemma tables insert $POD debate_sessions --data $binocsData

Write-Host ""
Write-Host "✅ PANCHAI seed data loaded!" -ForegroundColor Green
Write-Host "   6 agent_catalog entries (3 YesMadam + 3 Binocs)" -ForegroundColor Gray
Write-Host "   2 demo debate_sessions (triggers debate-pipeline workflow)" -ForegroundColor Gray
