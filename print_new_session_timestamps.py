import json
from lemma_sdk import Pod

pod = Pod.from_env()
session_id = "0c6f5a01-26f5-48df-9ac4-2a7d2ae657eb"

messages = pod.records.list("debate_messages", filter=[{"field": "session_id", "op": "eq", "value": session_id}])
items = getattr(messages, 'items', [])
for m in items:
    m_dict = m.to_dict() if hasattr(m, 'to_dict') else (m if isinstance(m, dict) else m.__dict__)
    print(f"Agent: {m_dict.get('agent_id')} | Round: {m_dict.get('round_number')} | Created: {m_dict.get('created_at')}")
