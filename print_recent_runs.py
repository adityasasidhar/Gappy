import json
from lemma_sdk import Pod

pod = Pod.from_env()

print("\nRECENT DEBATE SESSIONS:")
sessions = pod.records.list("debate_sessions", limit=5)
for s in getattr(sessions, 'items', []):
    s_dict = s.to_dict() if hasattr(s, 'to_dict') else (s if isinstance(s, dict) else s.__dict__)
    print(f"Session {s_dict.get('id')}: status={s_dict.get('status')}, task={s_dict.get('task_input')[:60] if s_dict.get('task_input') else 'N/A'}")

print("\nRECENT DEBATE MESSAGES:")
messages = pod.records.list("debate_messages", limit=20)
for m in getattr(messages, 'items', []):
    m_dict = m.to_dict() if hasattr(m, 'to_dict') else (m if isinstance(m, dict) else m.__dict__)
    arg = m_dict.get('argument', '')
    cleaned_arg = arg.encode('ascii', 'ignore').decode('ascii')
    print(f"Message in session {m_dict.get('session_id')}: Round {m_dict.get('round_number')} | Agent: {m_dict.get('agent_id')} | Position: {m_dict.get('position')} | Argument: {cleaned_arg[:100]}...")
