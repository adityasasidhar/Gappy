# MindPod — Claude Code Guide

This is a Lemma SDK pod. Use this file to understand the structure before making changes.

## Pod layout

```
mindpod/
├── pod.json                        # Pod metadata (name, format_version)
├── tables/*/                       # Each table = one directory with <name>.json
├── files/*/                        # Folder configs (.folder.json), not actual files
├── agents/*/                       # Agent JSON + instruction.md sidecar
├── workflows/*/                    # Workflow JSON
├── apps/mindpod-app/html.html      # Single-file no-build app (the main UI)
└── seed/                           # Demo data scripts
```

## How to add a new table

1. Create `tables/<tablename>/<tablename>.json`
2. Follow the schema in an existing table file (e.g. `tables/insights/insights.json`)
3. Add the table to any agents that need it via `permissions.grants`

## How to modify an agent

- Logic lives in `agents/<name>/instruction.md` — edit this for behavior changes
- Toolsets and permissions live in `agents/<name>/<name>.json`
- After editing, re-import: `lemma pods import ./mindpod`

## How to modify the app

Edit `apps/mindpod-app/html.html`. It's a single self-contained HTML file.

The app uses these Lemma REST endpoints:
- `GET /api/v1/pods/{pod_id}/tables/{table}/records` — list table rows
- `POST /api/v1/pods/{pod_id}/conversations` — start a conversation with an agent
- `POST /api/v1/pods/{pod_id}/conversations/{id}/messages` — send a message
- `GET /api/v1/pods/{pod_id}/conversations/{id}/messages` — poll for responses
- `POST /api/v1/pods/{pod_id}/files/upload` (multipart) — upload a file to /knowledge or /data

The env vars `window.__LEMMA_BASE_URL__`, `window.__LEMMA_POD_ID__`, `window.__LEMMA_TOKEN__` are injected by Lemma at runtime.

## Key design decisions

1. **DATASTORE trigger**: The workflow fires automatically on `sessions` table insert. The user never manually triggers the workflow — they just describe a goal and the orchestrator creates the session row.

2. **Built-in RAG on /knowledge**: No embedding pipeline needed. Lemma auto-indexes files uploaded to `/knowledge`. The research-agent and study-agent use `file.search` via the POD toolset to semantically query these docs.

3. **WORKSPACE_CLI for data-agent**: The data-agent needs to run actual Python/pandas. It downloads CSVs from `/data` using `lemma files download`, then runs analysis in the sandbox shell.

4. **Specialists, not one big agent**: The orchestrator stays lightweight — it classifies and delegates. Each specialist agent has a narrow, well-defined job. This keeps instructions short and reduces token waste.

5. **Zero access by default**: Every agent has an explicit `permissions.grants` list. Don't add `WEB_SEARCH` to agents that don't need it (study-agent, data-agent).

## Common tasks

**Add a new insight type**: Edit `tables/insights/insights.json` → update the `insight_type` enum column → update the agent instruction.md files that write insights → update the badge CSS in `html.html`.

**Add a new agent**: Create `agents/<name>/<name>.json` + `<name>/instruction.md` → add `agent.execute` grant in orchestrator → update orchestrator instruction to know when to call it.

**Change workflow trigger**: Edit `workflows/process-goal/process-goal.json` → change the `start.config.on` array (options: insert, update, delete).
