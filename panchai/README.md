# 🏛️ PANCHAI
> The Institutional Antidote to AI Overconfidence.

PANCHAI is a universal multi-agent council engine built on the Lemma platform. It forces AI agents to deliberate, challenge assumptions, and debate enterprise tasks *before* taking action.

## Core Mechanisms
1. **Blind Tribunal Protocol**: Agents never see the user's preferred outcome; they only evaluate the raw facts.
2. **Pre-Mortem Forcing Function**: Before arguing for anything, every agent must first predict how the task could fail.
3. **Active Moderation**: The Core Brain dynamically challenges agents to address opposing arguments.

## Quick Start

1. Ensure the Lemma CLI is installed: `npm install -g @lemma/cli`
2. Run the setup script:
   ```bash
   bash setup.sh
   ```
3. When prompted, type `y` to load the demo seed data.
4. The PANCHAI app will open automatically in your browser.

## The Demo Scenarios

The seed data includes two distinct enterprise scenarios running on the exact same engine (proving domain-agnosticity):

1. **YesMadam (HR/Policy)**: A user wants to approve a refund that violates policy. The council (Policy Analyst, Customer Advocate, Fraud Risk) debates it, catches the risk, and escalates to a human (HITL).
2. **Binocs (Supply Chain)**: A user wants to pause a vendor order due to tight cash flow. The council (Supply Chain Analyst, Financial Risk, Procurement) deliberates and reframes the approach to optimize without breaking the supply chain.

## Architecture

- **Council Members**: Domain-specific agents dynamically defined in the client's `agent_catalog`.
- **Goal Stripper (Function)**: Deterministically strips bias and extracts context from user requests.
- **Debate Pipeline (Function)**: The `run_pipeline` function executes the deliberation flow, creating pre-mortems, debate rounds, messages, and final verdicts in the datastore.
- **Institutional Memory**: Automatically archives verdicts as markdown documents using Lemma's Files API, which are retrieved using hybrid vector search for context in future councils.
- **Live UI**: Real-time debate feed powered by Lemma's `watchChanges()` WebSocket API.
