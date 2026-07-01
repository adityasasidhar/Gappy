import json
from lemma_sdk import Pod

pod = Pod.from_env()
session_id = "0c6f5a01-26f5-48df-9ac4-2a7d2ae657eb"

print(f"DEBATE MESSAGES FOR SESSION {session_id}:")
messages = pod.records.list("debate_messages", filter=[{"field": "session_id", "op": "eq", "value": session_id}])
items = getattr(messages, 'items', [])
print(f"Total messages: {len(items)}")
for m in items:
    m_dict = m.to_dict() if hasattr(m, 'to_dict') else (m if isinstance(m, dict) else m.__dict__)
    arg = m_dict.get('argument', '')
    cleaned_arg = arg.encode('ascii', 'ignore').decode('ascii')
    print(f"Agent: {m_dict.get('agent_id')} | Position: {m_dict.get('position')} | Round: {m_dict.get('round_number')}")
    print(f"  Argument: {cleaned_arg[:120]}...")
