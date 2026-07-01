"""Update agent catalog records to use ministral-3:3b model."""
from lemma_sdk import Pod, RecordData

pod = Pod.from_env()
pod._transport.generated._timeout = 30.0

agents = ["policy_analyst", "customer_advocate", "fraud_risk_assessor",
          "supply_chain_analyst", "financial_risk", "procurement_specialist"]

catalog = pod.records.list("agent_catalog")
print(f"Found {len(catalog.items)} items")
count = 0
for item in catalog.items:
    rec = item.to_dict() if hasattr(item, "to_dict") else item
    aid = rec.get("agent_id")
    rid = rec.get("id") or rec.get("_id")
    print(f"  item: agent_id={aid}, id={rid}, model={rec.get('model')}")
    if aid in agents:
        pod.records.update("agent_catalog", rid, RecordData(model="ministral-3:3b"))
        count += 1
        print(f"    -> Updated")

print(f"Total updated: {count}")
