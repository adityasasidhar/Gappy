const { spawnSync } = require('child_process');

const pod = 'panchai';

const agents = [
  {"agent_name":"Policy Analyst", "agent_id":"policy_analyst","client_id":"yesmadam","capabilities":["policy_check", "compliance_review", "rule_interpretation", "return_policy"],"reasoning_bias":"rule-following","model":"claude-3-haiku"},
  {"agent_name":"Customer Advocate", "agent_id":"customer_advocate","client_id":"yesmadam","capabilities":["customer_sentiment", "satisfaction_analysis", "retention_strategy", "consumer_rights"],"reasoning_bias":"empathetic","model":"claude-3-haiku"},
  {"agent_name":"Fraud Risk Assessor", "agent_id":"fraud_risk_assessor","client_id":"yesmadam","capabilities":["risk_scoring", "fraud_detection", "transaction_analysis", "refund_abuse"],"reasoning_bias":"conservative","model":"claude-3-haiku"},
  {"agent_name":"Supply Chain Analyst", "agent_id":"supply_chain_analyst","client_id":"binocs","capabilities":["supply_chain_optimization", "logistics_analysis", "demand_forecasting", "inventory_management"],"reasoning_bias":"operational-efficiency","model":"claude-3-haiku"},
  {"agent_name":"Financial Risk", "agent_id":"financial_risk","client_id":"binocs","capabilities":["risk_scoring", "cash_flow_analysis", "financial_modeling", "vendor_risk"],"reasoning_bias":"risk-averse","model":"claude-3-haiku"},
  {"agent_name":"Procurement Specialist", "agent_id":"procurement_specialist","client_id":"binocs","capabilities":["vendor_management", "cost_optimization", "procurement_analysis", "order_management"],"reasoning_bias":"cost-optimization","model":"claude-3-haiku"}
];

function runCmd(table, data) {
  console.log(`Inserting into ${table}...`);
  const cmd = process.platform === 'win32' ? 'lemma.exe' : 'lemma';
  const args = ['--pod', pod, 'records', 'create', table, '--data', JSON.stringify(data)];
  const result = spawnSync(cmd, args, { stdio: 'inherit' });
  if (result.error) {
    console.error("Error executing command:", result.error);
  }
}

for (const a of agents) {
  runCmd('agent_catalog', a);
}
console.log("Done!");
