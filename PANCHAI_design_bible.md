# 🏛️ PANCHAI — Design Bible
> *The Institutional Antidote to AI Overconfidence*
> *Last updated: 2026-06-27 | Status: **Design fully locked. Ready to build.***

---

## The One-Line Pitch
> **"Every AI you use today is trained to tell you you're right. PANCHAI is built to tell you when you're wrong."**

---

## Hackathon Context

**Event**: Gappy AI Hackathon — June 24–30, 2026
**Deadline**: June 30, 2026 (3 days remaining from design lock)
**Platform**: Lemma SDK (Python + TypeScript)

**Judging Criteria** (use these weights to prioritize demo and messaging):

| Criterion | Weight | PANCHAI Strength |
|---|---|---|
| **Problem clarity** | 35% | ✅ $67.4B market problem, sycophancy framing, 3 pain points |
| **Product judgment** | 25% | ✅ Blind Tribunal, Pre-Mortem, domain-agnostic engine |
| **Execution quality** | 25% | ⚠️ Must nail Live Feed + Verdict Dashboard |
| **SDK utilization** | 15% | ✅ DATASTORE trigger, watchChanges, Files HYBRID search |

> The demo must **lead with the problem**, not the technology. Problem clarity is 35% of the score.

---

## Core Philosophy

PANCHAI (inspired by the Indian **Panchayat** system) is a **universal multi-agent council engine** for enterprises. Just as a Panchayat brings together a council of wise members to deliberate on community disputes before issuing a verdict — PANCHAI assembles a dynamic council of AI agents to deliberate on any enterprise task before acting.

**It is not a task executor. It is a deliberation engine.**

The three business problems it solves:

| # | Problem | What PANCHAI Does |
|---|---|---|
| 🔴 1 | **"The Confident Wrong Answer"** — AI validates bad premises | Council debates the *premise* before the *plan* |
| 🔴 2 | **"Shadow AI Governance"** — No audit trail, legal blocks deployment | Structured debate produces complete, explainable reasoning trail |
| 🔴 3 | **"Pilot-to-Production Graveyard"** — AI built per domain, doesn't generalize | One engine, any domain via Capability Registry |

**The market reality**: $67.4B lost globally in 2024 from AI hallucinations. 4.3 hrs/week per employee verifying AI outputs. 34% more likely — LLMs use confident language precisely when they are most wrong. PANCHAI is the institutional firewall.

---

## Architecture

```
Enterprise Client A ──┐
Enterprise Client B ──┼──► CORE BRAIN (Frontier Model)
Enterprise Client C ──┘         │
                                 │
                    ┌────────────▼─────────────────┐
                    │   DEBATE SESSION PIPELINE     │
                    │                               │
                    │  Phase 0: Goal Stripping      │ ← Blind Tribunal prep
                    │  Phase 1: Pre-Mortem Forcing  │ ← Independent, passive mode
                    │  Phase 2: Registry Lookup     │ ← Capability → Agent selection
                    │  Phase 3: Blind Debate        │ ← Active Moderator, 3 rounds max
                    │  Phase 4: Verdict Synthesis   │ ← Brain synthesizes
                    │  Phase 5: HITL (if triggered) │ ← Workflow form node
                    └───────────────────────────────┘
                                 │
             ┌───────────────────┼───────────────────┐
             ▼                   ▼                   ▼
        Agent-1              Agent-2             Agent-N
    [from registry]       [from registry]    [from registry]
             │                   │                   │
             └───────────────────┼───────────────────┘
                              DEBATE
                         (Active Moderator)
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             Verdict JSON   Debate Feed   HITL Trigger
                    │            │
                    ▼            ▼
             Dashboard UI   Live Stream UI
```

**Trigger**: A `debate_sessions` table insert fires the entire pipeline automatically via **DATASTORE trigger** — no manual workflow start needed.

---

## Anti-Sycophancy: The Two Core Mechanisms

### Mechanism 1 — The Blind Tribunal Protocol
> Agents never see the user's desired outcome. They only receive the raw problem.

**Flow:**
1. User submits goal: *"Launch this feature in 2 days"*
2. Core Brain runs **Goal Stripper** (Function, deterministic) — separates task facts from user's preferred outcome
3. Agents receive ONLY: *"Feature X needs launch readiness evaluation. Constraints: [specs, risks, data]"*
4. Agents form independent verdicts with zero anchoring to user preference
5. Brain compares: **User Goal ←→ Council Verdict**
6. If divergence exists → mandatory `conflict_report` field in output (cannot be empty or skipped)

**Why this works**: Agents literally cannot be sycophantic toward an outcome they don't know exists.

---

### Mechanism 2 — The Pre-Mortem Forcing Function
> Before arguing FOR anything, every agent must complete failure analysis first.

**Runs in passive mode** — agents submit pre-mortems independently, never seeing each other's responses. Independence here is structural.

**Mandatory template every agent fills BEFORE Round 1:**
```
"If this goal fails, it will fail because: ___"
"The assumption most likely to be wrong is: ___"
"The stakeholder most harmed by failure is: ___"
```

Only after ALL pre-mortems are submitted does Round 1 begin. Agents are structurally committed to finding failure before arguing for success.

**Inspired by**: Gary Klein's Pre-Mortem technique (NASA, military planning). Empirically proven to surface risks that forward-looking discussion misses.

---

## Agent Spawning — The Capability Registry

The Brain does NOT create agents from scratch. It **selects** from agents pre-configured in each client's Lemma Pod. The Registry IS the Pod's agent set.

**Agent Registry Card Schema:**
```json
{
  "agent_id": "financial_risk_analyst",
  "capabilities": ["risk_scoring", "compliance_check", "cash_flow_analysis"],
  "input_schema": ["transaction_data", "policy_rules"],
  "output_schema": ["risk_verdict", "confidence_score", "flags"],
  "reasoning_bias": "conservative",
  "model": "claude-3-haiku"
}
```

**Spawning Logic:**
1. Brain reads the stripped task (not the user's goal)
2. Brain maps required capabilities from task semantics
3. Brain selects N agents from the pod's registry (max 3 standard / max 5 complex)
4. Brain creates a conversation with each selected agent dynamically

**Why this is powerful**: Deterministic, auditable, reproducible. You can always show exactly why each agent was chosen. Every council is a verifiable selection from a known catalog.

---

## Debate Mechanics — LOCKED

### Consensus Threshold (Tiered)
| Task Type | Threshold | Who Decides Stakes Level |
|---|---|---|
| Standard | Simple majority (2 of 3) | Brain classifies during Phase 0 |
| High-stakes | Supermajority (unanimous 3 of 3, or 3 of 4) | Same Brain classification |

### Round Structure
- **Hard cap**: 3 rounds maximum
- **Round 1**: All agents respond independently to stripped task + their own pre-mortem
- **Round 2**: Brain identifies core disagreement → sends targeted challenge prompt to each agent
- **Round 3**: Final positions locked

### Brain ↔ Agent Communication — Active Moderator Pattern
The Brain does NOT send the same message to all agents and wait. After each round:
1. Brain reads ALL agent outputs from the table
2. Brain identifies the **core disagreement** (what specifically do agents disagree on?)
3. Brain sends each agent a **targeted challenge** naming the opposing argument they must address

This forces genuine deliberation — agents must engage with opposing evidence, not just restate positions.

**Exception**: Pre-Mortem phase uses **Passive mode** — agents get the task, submit independently, no cross-visibility.

### New Evidence Mid-Debate
If a dissenting agent surfaces new evidence in any round:
- **1 bonus round** is triggered (beyond the 3-round cap)
- Round counter does NOT reset
- Maximum 1 bonus round per debate, regardless of how many agents dissent

### Tie-Breaking
A tie = machine epistemic ceiling. **Auto-escalate to HITL immediately.** No algorithmic tie-breaking — that would be sycophancy in disguise.

### Council Size
- Standard tasks: 3 agents
- Complex tasks: 5 agents (Brain decides at Phase 0)
- Hard maximum: 5 agents, never more

---

## The Contradiction Sentinel — Resolved & Retired

The Contradiction Sentinel was originally conceived as a dedicated watchdog agent. Through design evolution, its three responsibilities were found to be better handled by existing components:

| Original Sentinel Job | Absorbed By |
|---|---|
| "Is debate still productive?" | Brain's Active Moderator role — reads disagreements, generates targeted challenges |
| "Has consensus been reached?" | Voting threshold rules — deterministic, no AI needed |
| "Is this irresolvable?" | 5-condition HITL trigger matrix — fires escalation automatically |

**The Sentinel as a standalone concept is retired.** Its function lives on — distributed across the right layers. Adding a dedicated Sentinel agent would duplicate the Brain's reasoning with no additional value.

---

## HITL Trigger Matrix — LOCKED

HITL fires if **ANY** of these conditions are true:

```
✦ conflict_report.divergence_severity = HIGH
  (council verdict meaningfully contradicts user's stated goal)

✦ Vote result = TIE
  (genuine machine epistemic ceiling)

✦ Round limit reached (3 rounds + 1 bonus) with no consensus

✦ Confidence score < 0.60 on final verdict

✦ Any pre-mortem flagged severity = CRITICAL
  (an agent predicted a catastrophic failure mode)
```

All thresholds are universal — no domain-specific logic. Thresholds are configurable per client (e.g., a hospital may set confidence threshold at 0.80).

---

## HITL Form Design — LOCKED

Three zones. Self-contained. Approver needs no other system to decide.

### Zone 1 — Context
```
TASK SUBMITTED       "Should we approve this refund for Customer #4821?"
SUBMITTED BY         YesMadam Operations
STAKES LEVEL         HIGH
```

### Zone 2 — Council Finding
```
COUNCIL VERDICT      REJECTED (2–1)
CONFIDENCE SCORE     61% ← below threshold, triggered HITL

✅ Policy Analyst     AGAINST  "47-day purchase exceeds 30-day return window"
✅ Fraud Risk Agent   AGAINST  "Customer has 2 refunds in 6 months — risk flag"
❌ Customer Advocate  FOR      "Defect claim is a legally distinct scenario"

CONFLICT REPORT
User Goal:       Approve the refund
Council Finding: Reject — policy + risk flags override
Divergence:      HIGH

MINORITY DISSENT (Customer Advocate)
"A product defect claim is legally distinct from a standard return.
Rejecting without exception review may create consumer protection liability."
```

### Zone 3 — Decision
```
◉ APPROVE — Override council, proceed
◉ REJECT  — Council verdict stands
◉ SEND BACK — Trigger one more debate round with my note:
  ┌─────────────────────────────────┐
  │                                 │
  └─────────────────────────────────┘

                        [ SUBMIT DECISION ]
```

### Timeout Handling
```
T + 0 hr  → HITL sent to primary approver
T + 4 hr  → Reminder sent
T + 12 hr → Escalated to secondary approver
T + 24 hr → AUTO-EXECUTE: conservative option (inaction / status quo)
             Logged as HUMAN_TIMEOUT in verdict
```

**Principle**: Safe default is always inaction. PANCHAI never auto-approves on timeout.

### Re-Debate on Rejection
- Human rejects AND provides reason → reason injected as new evidence → ONE additional round
- Human rejects again → session closed, flagged UNRESOLVED for manual review
- Maximum one re-debate. No infinite loops.

---

## Pod Structure — LOCKED

**One Lemma Pod per enterprise client.**

```
PANCHAI Org
│
├── Pod: YesMadam
│     ├── Agents: policy_analyst, customer_advocate, fraud_risk_assessor
│     ├── Tables: debate_sessions, debate_rounds, debate_messages...
│     └── Files: /memory/...
│
└── Pod: Binocs
      ├── Agents: supply_chain_analyst, financial_risk, procurement_specialist
      ├── Tables: (same schema as YesMadam)
      └── Files: /memory/...
```

Every pod uses **identical table schemas**. Only the pod ID and agent catalog differ per client. Same PANCHAI engine code runs against any pod without modification — this IS the domain-agnosticity proof.

Data privacy is enforced at the pod boundary by Lemma — no access control logic needed in PANCHAI code.

---

## Lemma Primitive Mapping — LOCKED

```
PANCHAI CONCEPT              LEMMA PRIMITIVE
────────────────────────────────────────────────────────────
Client Workspace         →   Pod (one per enterprise client)
Debate Session           →   Workflow Run (DATASTORE triggered)
Core Brain               →   Agent ("panchai-brain") + Conversation
Council Member           →   Agent (pre-defined in pod) invoked via
                             create_for_agent() — dynamic, per round
Pre-Mortem Phase         →   Agent Conversation (needs real reasoning)
Goal Stripping           →   Function (deterministic, no LLM)
Registry Lookup          →   Function (deterministic, maps task → agents)
Debate Round State       →   Tables (Brain reads all prior rows each round)
Live Debate Feed         →   TypeScript watchChanges() on debate_messages
                             (fires on every insert — no polling needed)
HITL Approval            →   Workflow form-node + submit_form()
Verdict Storage          →   Table row (verdicts)
Institutional Memory     →   Files API (verdicts as .md files)
Memory Retrieval         →   pod.files.search(HYBRID) — semantic + text
Workflow Start Trigger   →   DATASTORE trigger on debate_sessions insert
```

---

## Table Schema — LOCKED

Eight tables. Flat rows, no nesting, clean joins.

| Table | Purpose |
|---|---|
| `debate_sessions` | One row per task — session metadata, status, client |
| `debate_rounds` | One row per round — round number, status, bonus flag |
| `pre_mortems` | One row per agent pre-mortem submission |
| `debate_messages` | **The live feed table** — one row per agent argument per round |
| `verdicts` | Final structured verdict per session |
| `hitl_queue` | Pending approvals — status, tier, timestamps, timeout |
| `agent_catalog` | Capability registry for each client's agents |
| `universal_patterns` | Anonymized cross-client behavioral patterns (future) |

**Key design**: `debate_messages` is append-only. The TypeScript `watchChanges()` subscription fires on every insert, powering the Live Debate Feed in real-time.

---

## Institutional Memory — Federated Silo Architecture

```
Client A Raw Silo      Client B Raw Silo      Client C Raw Silo
[debate logs]          [debate logs]          [debate logs]
[verdicts .md]         [verdicts .md]         [verdicts .md]
      │                      │                      │
      └──────────────────────┼──────────────────────┘
                             ▼
                 PANCHAI UNIVERSAL PATTERN LAYER
             (anonymized behavioral patterns — no raw data)
        "task_type=compliance_audit + split=2-1 + domain=HR
         → HITL escalation was correct 89% of the time"
                             │
                 Informs future registry lookups
                 WITHOUT exposing any client data
```

- Raw debates, pre-mortems, verdicts → stay in client pod (Files API)
- Memory retrieval for new councils → `pod.files.search(query, method="HYBRID")`
- Anonymized patterns → contribute to universal layer (future roadmap, not hackathon scope)

---

## Output Schema — Structured Verdict

```json
{
  "task_id": "uuid",
  "verdict": "APPROVED | REJECTED | ESCALATED | REFRAMED",
  "confidence_score": 0.87,
  "council_vote": {
    "for": ["agent_risk_analyst", "agent_advocate"],
    "against": ["agent_domain_expert"],
    "abstain": []
  },
  "conflict_report": {
    "user_goal": "Launch in 2 days",
    "council_finding": "Launch in 2 days is not feasible without security risk",
    "divergence_severity": "HIGH"
  },
  "reasoning_trail": [
    {"round": 1, "agent": "agent_risk_analyst", "position": "AGAINST", "argument": "..."},
    {"round": 2, "agent": "agent_risk_analyst", "position": "AGAINST", "argument": "Addressed advocate's point: ..."}
  ],
  "pre_mortems": [
    {"agent": "agent_risk_analyst", "failure_reason": "...", "weak_assumption": "...", "harmed_stakeholder": "..."}
  ],
  "hitl_required": true,
  "hitl_reason": "Confidence 0.61 < threshold + HIGH divergence",
  "recommended_action": "..."
}
```

---

## Demo Strategy — Two Scenarios, One Engine

**The proof point**: Run both on the SAME workflow, SAME engine, ZERO code changes. Only the pod and task input differ.

| | YesMadam Demo | Binocs Demo |
|---|---|---|
| **Domain** | HR / Customer Service | Inventory / Supply Chain |
| **Task** | "Should we approve this refund?" | "Should we pause this vendor order?" |
| **Agents** | Policy Analyst, Customer Advocate, Fraud Risk | Supply Chain Analyst, Financial Risk, Procurement Specialist |
| **Council split** | 2-1 AGAINST → HITL triggered | Unanimous REFRAME → workflow trigger |
| **Demo hook** | Council challenges sycophantic request | Council prevents costly false positive |

**Fabricated demo data:**

*YesMadam*: Customer tier Gold, purchase 47 days ago, policy = 30-day returns, claim = product defect, 2 prior refunds in 6 months.

*Binocs*: Inventory 340 units, demand forecast 280 units, vendor reliability 62%, lead time 45 days, cash position tight.

**What judges see:**
1. **Live Debate Feed** — real-time stream, agents argue round by round, positions appear as rows land
2. **Verdict Dashboard** — vote breakdown, dissent map, confidence score, conflict report, HITL status

---

## Competitive Positioning

| Competitor | Gap PANCHAI Fills |
|---|---|
| Microsoft AutoGen | No debate mechanic, no sycophancy fix |
| CrewAI | Agents collaborate, not challenge — still sycophantic |
| LangGraph | Infrastructure only, no council ideology |
| Crucible | No HITL, no memory, no cultural universality |
| Salesforce Agentforce | Task execution, NOT deliberation |
| Microsoft Copilot | Always validates user intent, never challenges it |

**PANCHAI's unique position**: The ONLY enterprise decision engine designed to challenge the user's premise before executing.

---

## The Panchayat Mapping (Conceptual Anchor)

| Panchayat | PANCHAI |
|---|---|
| Panch members | AI Agents (from capability registry) |
| Sarpanch | Core Brain (frontier model, Active Moderator) |
| Sabha (session) | Debate Round |
| Pre-mortem | Failure analysis phase before Sabha |
| Faiyasal (verdict) | Structured JSON output |
| Andolan (unresolved escalation) | HITL trigger |
| Precedent | Institutional Memory (Files + HYBRID search) |
| Blind justice | Blind Tribunal Protocol |
| Sarpanch moderating cross-talk | Active Moderator targeted challenges |

---

## All Design Decisions — Status

| Decision | Status | Choice Made |
|---|---|---|
| Core philosophy | ✅ Locked | Antidote to AI overconfidence |
| 3 business pain points | ✅ Locked | Confident Wrong Answer, Shadow Governance, Pilot Graveyard |
| Architecture | ✅ Locked | Brain + Registry + Dynamic Spawning |
| Blind Tribunal | ✅ Locked | Goal stripped before agents see task |
| Pre-Mortem | ✅ Locked | Passive mode, mandatory, before Round 1 |
| Consensus threshold | ✅ Locked | Tiered: majority standard, supermajority high-stakes |
| Round limits | ✅ Locked | 3 rounds + 1 bonus for new evidence |
| Tie-breaking | ✅ Locked | Auto-HITL, no algorithmic break |
| Brain ↔ Agent comm | ✅ Locked | Active Moderator — targeted challenge per round |
| Council size | ✅ Locked | 3 standard, 5 complex, never more |
| Contradiction Sentinel | ✅ Retired | Distributed: Brain + voting rules + HITL matrix |
| HITL trigger | ✅ Locked | 5-condition matrix, any one fires escalation |
| HITL form | ✅ Locked | 3-zone form, 3 options, reason required |
| Timeout handling | ✅ Locked | Tiered T+0/4/12/24hr, conservative default |
| Re-debate on rejection | ✅ Locked | One re-debate, UNRESOLVED if rejected again |
| Pod structure | ✅ Locked | One pod per client, identical schema |
| Lemma primitive mapping | ✅ Locked | Full table above |
| DATASTORE trigger | ✅ Locked | sessions insert fires entire pipeline |
| Table schema | ✅ Locked | 8 tables, flat rows |
| Real-time UI | ✅ Locked | watchChanges() on debate_messages |
| Institutional memory | ✅ Locked | Files API + HYBRID search |
| Brain model | ✅ Locked | Configurable per client, default provided |
| Demo scenarios | ✅ Locked | YesMadam refund + Binocs vendor order |
| Demo data | ✅ Locked | Fabricated above |

---
*Design fully locked 2026-06-27. All 24 decisions resolved. Ready for planning-and-task-breakdown.*
