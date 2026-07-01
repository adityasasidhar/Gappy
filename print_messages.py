import json
from lemma_sdk import Pod

pod = Pod.from_env()

# Find last session
sessions = pod.records.list("debate_sessions", limit=5)
print("RECENT SESSIONS:")
for s in getattr(sessions, 'items', []):
    s_dict = s.to_dict() if hasattr(s, 'to_dict') else (s if isinstance(s, dict) else s.__dict__)
    print(f"Session: {s_dict}")

# Get all messages
print("\nDEBATE MESSAGES:")
messages = pod.records.list("debate_messages", limit=50)
for m in getattr(messages, 'items', []):
    m_dict = m.to_dict() if hasattr(m, 'to_dict') else (m if isinstance(m, dict) else m.__dict__)
    print(f"Message: {m_dict}")
