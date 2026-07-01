import json
from lemma_sdk import Pod

pod = Pod.from_env()

print("ALL RECENT DEBATE SESSIONS:")
sessions = pod.records.list("debate_sessions", limit=10)
items = getattr(sessions, 'items', [])
print(f"Total sessions: {len(items)}")
for s in items:
    s_dict = s.to_dict() if hasattr(s, 'to_dict') else (s if isinstance(s, dict) else s.__dict__)
    print(f"Session {s_dict.get('id')}: client_id={s_dict.get('client_id')}, status={s_dict.get('status')}, task_input={s_dict.get('task_input')[:60] if s_dict.get('task_input') else 'None'}")
