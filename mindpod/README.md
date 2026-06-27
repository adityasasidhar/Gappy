# MindPod — AI Second Brain

> Upload your documents and data → set a goal → get flashcards, deep research synthesis, or EDA insights.

Built for the **Gappy AI Hackathon (June 24-30, 2026)** using the [Lemma SDK](https://lemma.ai).

---

## What it does

| Mode | What happens |
|------|-------------|
| **Learn** | Study-agent reads your PDFs → creates flashcards, quiz questions, weak-area flags, practice problems |
| **Research** | Research-agent searches across all your documents + the web → writes structured insights (findings, patterns, connections, anomalies) |
| **Analyze** | Data-agent downloads your CSVs, runs pandas EDA in a sandboxed shell → surfaces number-backed insights |
| **Auto** | Orchestrator reads the goal + inspects what's in /knowledge and /data → picks the right mode(s) |

The orchestrator is always the entry point. It creates a session row, which triggers the workflow, which fires the right specialist agent(s).

---

## Architecture

```
mindpod/
├── pod.json                        # Pod metadata
├── tables/
│   ├── sessions/                   # Tracks each user goal
│   ├── insights/                   # Structured agent outputs (findings, patterns…)
│   └── study_items/                # Flashcards, quiz questions, weak areas
├── files/
│   ├── knowledge/                  # Upload PDFs/notes here → auto-indexed for RAG
│   └── data/                       # Upload CSVs here → data-agent reads via pandas
├── agents/
│   ├── orchestrator/               # Entry point: classifies goal, delegates
│   ├── study-agent/                # Learning specialist
│   ├── research-agent/             # Synthesis + web search specialist
│   └── data-agent/                 # EDA specialist (WORKSPACE_CLI for Python)
├── workflows/
│   └── process-goal/               # DATASTORE trigger: fires on sessions insert
├── apps/
│   └── mindpod-app/
│       └── html.html               # Single-file app (no build step)
└── seed/
    ├── seed.sh                     # Load demo data
    └── demo-data/
```

---

## Setup

### Prerequisites
- Lemma CLI installed: `npm install -g @lemma/cli`
- Logged in: `lemma auth login`

### One-shot install

```bash
cd mindpod
bash setup.sh
```

This runs `lemma pods import`, then opens the app.

### Manual steps

```bash
# 1. Import the pod
lemma pods import ./mindpod

# 2. (Optional) load demo seed data
bash mindpod/seed/seed.sh

# 3. Open the app
lemma apps open mindpod
```

---

## Running fully local with Ollama

MindPod can run its agents on your **local Ollama** instead of the hosted models.
Ollama speaks the OpenAI-compatible protocol, so we point a **self-hosted Lemma
stack** at it and make it the default provider — no per-agent changes needed.

> The hosted cloud backend (`api.lemma.work`) **cannot** reach `localhost:11434`,
> so local Ollama requires the self-hosted stack (or a public tunnel).

```bash
# 1. Install + start the self-hosted stack
curl -fsSL https://raw.githubusercontent.com/lemma-work/lemma-platform/main/install.sh | bash
lemma-stack start

# 2. Point the stack's default runtime at your Ollama (defaults to nemotron-3-nano:30b-cloud)
bash use-ollama.sh
#   OLLAMA_MODEL=qwen3.5:4b bash use-ollama.sh        # pick a different model
#   OLLAMA_URL=http://172.17.0.1:11434/v1 bash use-ollama.sh   # Linux bridge fallback

# 3. Point the CLI at the local stack, then import the pod
lemma servers add local --base-url http://127-0-0-1.sslip.io:8711 --auth-url http://127-0-0-1.sslip.io:3711
lemma servers use local
lemma pods import ./
```

**Ollama networking:** the stack runs in Docker, so Ollama must be reachable
from containers. Bind it to all interfaces (`OLLAMA_HOST=0.0.0.0`) and use
`host.docker.internal` (or the docker bridge IP `172.17.0.1`) as the host.

**Model choice:** these agents lean on tool-calling + strict JSON `output_schema`.
Small local models (e.g. `qwen3.5:4b`) are often unreliable at that; prefer a
stronger model like `nemotron-3-nano:30b-cloud` for dependable runs.

---

## Usage

1. **Upload files** — drag PDFs into the Knowledge zone, or CSVs into the Data zone
2. **Pick a mode** — Auto, Learn, Research, or Analyze
3. **Type your goal** — e.g. "Help me study neural networks" or "Find patterns in this sales data"
4. **Watch insights appear** — right panel auto-refreshes every 15 seconds

The Insights tab shows structured findings. The Study tab shows flashcards (click to flip). The Sessions tab shows past goals and lets you drill into their insights.

---

## Agent permissions summary

| Agent | Tables | Files | Toolsets |
|-------|--------|-------|----------|
| orchestrator | sessions (rw), insights (r), study_items (r) | /knowledge (r), /data (r) | POD, WEB_SEARCH, USER_INTERACTION |
| study-agent | sessions (r), insights (rw), study_items (rw) | /knowledge (r) | POD |
| research-agent | sessions (r), insights (rw) | /knowledge (r) | POD, WEB_SEARCH |
| data-agent | sessions (r), insights (rw) | /knowledge (r), /data (r) | POD, WORKSPACE_CLI |

---

## Hackathon notes

- Judging: 35% problem clarity, 25% product judgment, 25% execution quality, 15% SDK utilization
- The DATASTORE trigger on `sessions` insert is the core Lemma integration — it fires the entire pipeline automatically
- Built-in RAG on `/knowledge` means no embedding pipeline needed
- WORKSPACE_CLI on data-agent enables real pandas execution in a sandboxed shell
