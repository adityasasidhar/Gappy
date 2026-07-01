# 🏛️ PANCHAI — The Institutional Antidote to AI Overconfidence

> *When AI must decide, PANCHAI makes it deliberate.*

PANCHAI is a **universal multi-agent council engine** built on the [Lemma](https://lemma.work) platform. It forces AI agents to debate enterprise tasks — with pre-mortem analysis, adversarial cross-examination, and full audit trails — before reaching a verdict.

---

## 🏆 Hackathon Demo

### Two Live Scenarios (same engine, two domains)

| Scenario | Client | Task | Council |
|----------|--------|------|---------|
| **YesMadam** | HR / Customer Service | Approve refund 47 days after 30-day policy window | Policy Analyst · Customer Advocate · Fraud Risk Assessor |
| **Binocs** | Supply Chain / Finance | Pause vendor order amid tight cash flow | Supply Chain Analyst · Financial Risk · Procurement Specialist |

Both run through the **identical** deliberation pipeline — proving domain-agnosticity.

---

## Quick Start

### Prerequisites
- [Lemma CLI](https://docs.lemma.work): `npm install -g @lemma/cli`
- Python 3.10+
- Lemma account with a pod

### One-Command Setup (Windows)
```powershell
cd panchai
.\setup.ps1
```

### One-Command Setup (macOS / Linux)
```bash
cd panchai
bash setup.sh
```

Both scripts will:
1. Import the pod via `lemma pods import ./`
2. Ask if you want to load demo seed data (YesMadam + Binocs scenarios)
3. Open the PANCHAI live UI in your browser

### Manual Deployment
```bash
# Import everything (tables, functions, agents, workflows, app)
lemma pods import ./

# Seed demo data
cd seed && python seed_all.py

# Open the app
lemma apps open panchai

# Trigger the pipeline via the workflow form
lemma workflows run debate-pipeline
```

---

## Architecture

### Deliberation Pipeline

```
User Input (FORM)
       │
       ▼
┌─────────────────────┐
│   goal_strip()      │  ← Blind Tribunal Protocol: strips user_goal from facts
│   (deterministic)   │     Creates debate_sessions record
└────────┬────────────┘
         │  stripped_task (no user_goal)
         ▼
┌─────────────────────┐
│   fast_pipeline()   │  ← Multi-agent deliberation engine
│   (Lemma Function)  │
│                     │
│  1. registry_lookup │  ← Selects council by keyword match on agent_catalog
│  2. Pre-Mortem      │  ← Each agent predicts failure modes first
│  3. Debate Round 1  │  ← Each agent forms position (FOR/AGAINST/REFRAME/ABSTAIN)
│  4. Verdict         │  ← Majority vote with confidence score
│  5. Archive         │  ← Writes verdict markdown to institutional memory
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  HITL Check         │  ← Confidence < 60% or no consensus → human review
│  (DECISION node)    │
└────────┬────────────┘
         │
    ┌────┴────┐
    ▼         ▼
  Done     HITL Form  →  panchai-brain resolves
```

### Core Mechanisms

#### 1. Blind Tribunal Protocol
`goal_strip()` deterministically separates the user's *desired outcome* (`user_goal`) from the *objective facts* (`stripped_task`). **Agents never see `user_goal`** — they only evaluate the stripped facts. This prevents sycophancy.

#### 2. Pre-Mortem Forcing Function
Before forming any position, every agent must predict how the proposed action could **fail** — surfacing assumptions, risks, and harmed stakeholders. Pre-mortem outputs are persisted to `pre_mortems` table for live feed display.

#### 3. Agent Council via Lemma Runtime
Agents are called via `pod.conversations.create_for_agent()` + `pod.conversations.send_stream()`. On quota exhaustion (429), the pipeline transparently falls back to direct Ollama Cloud API calls — same agent personas, same output format.

#### 4. Institutional Memory
- **Retrieval**: At pipeline start, `pod.files.search(query, search_method="HYBRID")` retrieves relevant past verdicts as context.
- **Archival**: After verdict, a markdown summary is written to `/panchai/verdicts/{session_id}.md` via `pod.files.write_text()`. Knowledge compounds over time.

#### 5. Live Feed UI
Real-time debate feed powered by Lemma's `watchChanges()` WebSocket API (polling fallback). Agents' arguments appear as they're written to `debate_messages`, creating a live tribunal experience.

---

## File Structure

```
panchai/
├── pod.json                           # Pod definition
├── setup.sh / setup.ps1               # One-command setup scripts
│
├── tables/                            # Lemma Datastore schemas
│   ├── debate_sessions/               # One row per task submitted
│   ├── debate_rounds/                 # Round tracking (pre_mortem, debate, bonus)
│   ├── debate_messages/               # Every agent argument (live feed source)
│   ├── pre_mortems/                   # Pre-mortem failure predictions
│   ├── verdicts/                      # Final council decisions + audit trail
│   ├── hitl_queue/                    # Human-in-the-loop escalation queue
│   └── agent_catalog/                 # Agent registry with capabilities + bias
│
├── functions/
│   ├── goal_strip/                    # Blind Tribunal: strips user_goal
│   │   ├── goal_strip.py
│   │   └── goal_strip.json
│   ├── fast_pipeline/                 # Main deliberation engine
│   │   ├── fast_pipeline.py           # Sequential 2-agent pipeline (sandbox-safe)
│   │   └── fast_pipeline.json         # Permissions: 6 tables + 3 agents + registry
│   └── registry_lookup/               # Agent selection by task keyword overlap
│       ├── registry_lookup.py
│       └── registry_lookup.json
│
├── agents/
│   ├── policy-analyst/                # Rule-following, policy citations
│   ├── customer-advocate/             # Empathy-first, retention-focused
│   ├── fraud-risk-assessor/           # Conservative, abuse-detection
│   ├── supply-chain-analyst/          # Operational continuity
│   ├── financial-risk/                # Cash preservation
│   └── procurement-specialist/        # Vendor relationship management
│
├── workflows/
│   └── debate-pipeline/               # MANUAL trigger → FORM → goal_strip → fast_pipeline → HITL
│       └── debate-pipeline.json
│
├── apps/
│   └── panchai-app/
│       ├── index.html                 # Live debate feed + verdict dashboard + HITL UI
│       └── panchai-app.json
│
└── seed/
    ├── seed_all.py                    # Seeds agent_catalog + demo sessions + sample verdicts
    ├── seed.sh / seed.ps1
    └── demo-data/
        ├── yesmadam-catalog.json      # YesMadam agent catalog (3 agents, ministral-3:3b)
        └── binocs-catalog.json        # Binocs agent catalog (3 agents, ministral-3:3b)
```

---

## Key Design Decisions

### Why Sequential Agents (not parallel)?
Lemma Cloud's function sandbox provides **1 thread** — `asyncio.to_thread()` runs sequentially. Parallel HTTP calls would block each other. Sequential execution with a 260s budget fits cleanly within the 300s sandbox kill limit.

### Why 2 Agents (not 5)?
- 2 agents × 120s timeout = 240s max
- 40s buffer before sandbox kills at ~300s
- For HIGH stakes tasks, the council can be expanded to 3 via `registry_lookup`

### Why Ollama Cloud Fallback?
Lemma Cloud's account-level LLM quota can be exhausted (HTTP 429). The fallback calls Ollama Cloud's OpenAI-compatible API directly via `httpx` — same models (`ministral-3:3b`), same persona prompts, same output format. The tribunal continues uninterrupted.

### Blind Tribunal Protocol
`user_goal` is present in `fast_pipeline`'s input schema (for `conflict_report` dashboarding) but is **never included in any prompt sent to agents**. The code explicitly uses only `stripped_task` in `task_prompt`. This is PANCHAI's core anti-sycophancy guarantee.

---

## Running the Demo

### Option A: Workflow (recommended for judges)
```bash
lemma workflows run debate-pipeline
# Fill the form with a YesMadam or Binocs scenario
# Watch the live feed in the PANCHAI App
```

### Option B: Direct function call
```bash
# Step 1: Strip the goal
lemma functions call goal_strip --pod panchai --data '{
  "task_input": "Should we approve this refund for Customer #4821? Gold tier, 47 days ago, 30-day policy, product defect claim, 2 prior refunds in 6 months."
}'

# Step 2: Run deliberation (use session_id from step 1)
lemma functions call fast_pipeline --pod panchai --data '{
  "session_id": "<from_step_1>",
  "stripped_task": "<from_step_1>",
  "client_id": "yesmadam",
  "stakes_level": "HIGH",
  "council_size": 2
}'
```

### Demo Scenario Inputs

**YesMadam (Refund Decision):**
```
Should we approve this refund for Customer #4821? Customer tier Gold, purchase 47 days ago, policy = 30-day returns, claim = product defect, 2 prior refunds in 6 months.
```
Expected verdict: `ESCALATED` or `REJECTED` (policy violation + fraud risk)

**Binocs (Supply Chain Decision):**
```
Should we pause this vendor order? Inventory 340 units, demand forecast 280 units, vendor reliability 62%, lead time 45 days, cash position tight.
```
Expected verdict: `REFRAMED` (partial order + renegotiated terms)

---

## Technical Constraints Addressed

| Constraint | Solution |
|-----------|---------|
| Lemma 429 LLM quota | Ollama Cloud API fallback via httpx |
| 300s sandbox kill | 260s time budget + 2-agent cap + 120s per-agent timeout |
| asyncio.to_thread sequential | _call_agent_sync() called directly (no thread wrapper) |
| No files.upload_content() | files.write_text() for archival |
| files.search() permission absent | Wrapped in try/except |
| Private transport attribute | pod._transport.generated._timeout override in try/except |
| debate_sessions no mode column | Removed from all create/update payloads |
| Agent IDs: underscores vs hyphens | agent_catalog uses underscores; agent definitions use hyphens; both handled |

---

## Live Run Evidence

The PANCHAI pipeline produces real AI deliberation records in these tables:

- `debate_sessions` — tracks full lifecycle from `pending` → `debating` → `done`/`hitl`
- `debate_messages` — every agent's argument, visible in real-time feed
- `pre_mortems` — failure predictions before positions are taken
- `verdicts` — final verdict with reasoning trail, conflict report, vote breakdown
- `hitl_queue` — escalation records when human review is required

---

## Built With

- **[Lemma](https://lemma.work)** — Agent runtime, Datastore, Files API, WebSocket live feed
- **[Ollama Cloud](https://ollama.com)** — `ministral-3:3b` model for all council agents
- **Python** (lemma-sdk, httpx, pydantic) — Pipeline functions
- **Vanilla JS + CSS** — Premium live UI (no framework, no build step)
- **Inter / Outfit / JetBrains Mono** — Typography

---

*PANCHAI — Because AI decisions deserve institutional rigor.*
