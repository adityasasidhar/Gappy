# 🏛️ PANCHAI — The Institutional Antidote to AI Overconfidence

> **When AI must decide, PANCHAI makes it deliberate.**

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-panchai.apps.lemma.work-10b981?style=for-the-badge)](https://panchai.apps.lemma.work)
[![Built with Lemma](https://img.shields.io/badge/Built_with-Lemma-6366f1?style=for-the-badge)](https://lemma.work)

---

## 🎯 The Core Problem PANCHAI Solves

AI assistants are trained to be helpful, agreeable, and efficient — creating a dangerous blind spot: **they validate your assumptions instead of challenging them**. This "sycophancy problem" causes:

| Problem | Business Impact |
|---------|-----------------|
| **Assumption Validation** | Approves risky strategies that sound good but fail |
| **No Failure Analysis** | Never asks "how could this go wrong?" before action |
| **No Institutional Memory** | Each decision starts from zero, repeating mistakes |
| **Missing Human Oversight** | High-stakes calls bypass human review automatically |

---

## ✨ PANCHAI's Solution: AI Tribunal in 30 Seconds

A **multi-agent council engine** that forces deliberation before decisions execute:

```
Your Request → Goal Stripped → Pre-Mortem → Council Debate → Verdict or HITL
```

### The 5 Anti-Sycophancy Mechanisms

1. **🎯 Blind Tribunal** — Agents see *only* stripped facts, NEVER your desired outcome
2. **⚠️ Pre-Mortem Forcing** — Each agent predicts failure *before* taking a position
3. **⚖️ Adversarial Debate** — Opposing viewpoints clash head-to-head in real-time
4. **📊 Confidence Scoring** — Verdicts include measurable certainty (0-100%)
5. **👨‍💼 Human Escalation** — Confidence < 60% or no consensus → human review

---

## 🎥 Live Demo Results

### YesMadam HR Scenario
> Should we approve a refund 47 days after the 30-day policy window?

| Agent | Position | Confidence | Key Argument |
|-------|----------|------------|--------------|
| Policy Analyst | ❌ AGAINST | 95% | "Violates documented policy" |
| Customer Advocate | ✅ FOR | 98% | "Retain Gold tier customer" |
| Fraud Risk | ⚠️ AGAINST | 89% | "Pattern matches abuse history" |

**Verdict:** `ESCALATED` — Tie + low confidence triggers human review

### Binocs Supply Chain Scenario  
> Should we pause this vendor order amid tight cash flow?

| Agent | Position | Confidence | Key Argument |
|-------|----------|------------|--------------|
| Supply Chain | ⚖️ REFRAME | 82% | "Partial order preserves continuity" |
| Financial Risk | ❌ AGAINST | 91% | "Cash preservation paramount" |
| Procurement | ⚖️ REFRAME | 87% | "Renegotiate terms instead" |

**Verdict:** `REFRAMED` — Binary pause rejected, strategic alternative proposed

---

## 🚀 Quick Start

```bash
# macOS/Linux
bash panchai/setup.sh

# Windows  
.\panchai\setup.ps1
```

✅ Installs pod • Seeds demo data • Opens live UI

---

## 🧪 Try It

```bash
lemma workflows run debate-pipeline
# Fill form → Watch live debate feed
```

---

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User Form  │ ──→ │ goal_strip  │ ──→ │fast_pipeline│
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                             ┌────────────────┘
                             ▼
                    ┌────────────────────┐
                    │ Verdict + Vote Breakdown │
                    └────────────────────┘
                             │
                    ┌──────┴──────┐
                    ▼             ▼
              APPROVED        HITL Flow
```

### Components

```
tables/       → Sessions, messages, pre-mortems, verdicts
functions/    → goal_strip + fast_pipeline (deliberation engine)
agents/       → 6 council members with distinct biases
workflows/    → debate-pipeline orchestrates the flow
apps/         → Live UI with real-time feed
```

---

## 🤖 Agent Council

| Agent | Bias | Domain |
|-------|------|--------|
| Policy Analyst | Rule-following | Compliance, regulations |
| Customer Advocate | Empathy-first | Retention, satisfaction |
| Fraud Risk | Conservative | Abuse detection |
| Supply Chain Analyst | Operational | Logistics, continuity |
| Financial Risk | Conservative | Cash preservation |
| Procurement Specialist | Relationship | Vendor, costs |

---

## 🛠️ Tech Stack

- **[Lemma](https://lemma.work)** — Agent runtime, Datastore, Files API, WebSocket
- **[Ollama Cloud](https://ollama.com)** — ministral-3:3b model
- **Python** — Pipeline logic (lemma-sdk, pydantic)
- **Vanilla JS + CSS** — Zero-build live UI

---

*PANCHAI — Because AI decisions deserve institutional rigor.*