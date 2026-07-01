#input_type_name: Input
#output_type_name: Output
#function_name: registry_lookup

"""
registry_lookup — PANCHAI council assembly function.

Reads agent_catalog filtered by client_id, scores each agent by keyword
overlap between the stripped_task and the agent's capabilities, and returns
a council of agents sized by stakes level (3 for STANDARD, up to 5 for HIGH).

Pure Python — no LLM calls.
"""

import json
import re
from typing import List

from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


# ── Pydantic models ──────────────────────────────────────────────────────────

class Input(BaseModel):
    stripped_task: str
    client_id: str
    stakes_level: str  # "STANDARD" | "HIGH"


class SelectedAgent(BaseModel):
    agent_id: str
    agent_name: str
    reasoning_bias: str


class Output(BaseModel):
    selected_agents: List[SelectedAgent]
    council_size: int


# ── Helpers ──────────────────────────────────────────────────────────────────

# Common English stop words to ignore during keyword matching
_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "as", "be", "was", "are",
    "this", "that", "these", "those", "do", "does", "did", "will", "would",
    "can", "could", "should", "may", "might", "shall", "not", "no", "so",
    "if", "then", "than", "also", "very", "just", "about", "up", "out",
    "all", "has", "have", "had", "been", "being", "its", "our", "we",
    "they", "he", "she", "me", "my", "your", "his", "her", "their",
})


def _tokenize(text: str) -> set:
    """Lowercase, split on non-alphanumeric chars, drop stop words & short tokens."""
    tokens = set(re.split(r"[^a-z0-9]+", text.lower()))
    return {t for t in tokens if len(t) > 2 and t not in _STOP_WORDS}


# Synonym mapping dictionary for semantic routing helper
SYNONYMS = {
    "cash": {"capital", "funds", "budget", "finance", "monetary", "financial", "treasury", "liquidity"},
    "capital": {"cash", "funds", "budget", "finance", "monetary", "financial", "treasury", "liquidity"},
    "funds": {"cash", "capital", "budget", "finance", "monetary", "financial", "treasury", "liquidity"},
    "budget": {"cash", "capital", "funds", "finance", "monetary", "financial", "treasury", "liquidity"},
    "financial": {"cash", "capital", "funds", "budget", "finance", "monetary", "treasury", "liquidity"},
    "finance": {"cash", "capital", "funds", "budget", "financial", "monetary", "treasury", "liquidity"},
    
    "refund": {"return", "reimbursement", "chargeback", "defect", "abuse", "fraud", "policy"},
    "return": {"refund", "reimbursement", "chargeback", "defect", "abuse", "fraud", "policy"},
    "reimbursement": {"refund", "return", "chargeback", "defect", "abuse", "fraud", "policy"},
    
    "inventory": {"stock", "supply", "vendor", "procurement", "order", "replenishment", "warehouse"},
    "stock": {"inventory", "supply", "vendor", "procurement", "order", "replenishment", "warehouse"},
    "vendor": {"supplier", "inventory", "stock", "supply", "procurement", "order", "replenishment", "warehouse"},
    "supplier": {"vendor", "inventory", "stock", "supply", "procurement", "order", "replenishment", "warehouse"},
}


def _expand_synonyms(keywords: set) -> set:
    """Expand keywords with mapped synonyms for semantic matching fallback."""
    expanded = set(keywords)
    for kw in keywords:
        if kw in SYNONYMS:
            expanded.update(SYNONYMS[kw])
    return expanded



def _score_agent(task_keywords: set, capabilities_json: str) -> int:
    """
    Score an agent by counting how many task keywords appear in its
    capabilities list.  Higher score = better match.
    """
    try:
        caps = json.loads(capabilities_json)
    except (json.JSONDecodeError, TypeError):
        caps = []

    # Build a single set of tokens from all capability strings
    cap_tokens: set = set()
    for cap in caps:
        cap_tokens |= _tokenize(str(cap))

    return len(task_keywords & cap_tokens)


# ── Main handler ─────────────────────────────────────────────────────────────

async def registry_lookup(ctx: FunctionContext, data: Input) -> Output:
    """
    1. Query agent_catalog for agents belonging to *client_id*.
    2. Tokenize the *stripped_task* into keywords.
    3. Score each agent by keyword overlap with its capabilities.
    4. Return top-N agents (N = 3 for STANDARD, 5 for HIGH).
    """
    pod = Pod.from_env()

    # Determine council size from stakes level
    max_council = 5 if data.stakes_level == "HIGH" else 3

    # Fetch all agents for this client
    result = pod.records.list(
        "agent_catalog",
        filter=[{"field": "client_id", "op": "eq", "value": data.client_id}]
    )
    rows = result.items
    rows = [r.to_dict() if hasattr(r, 'to_dict') else dict(r) for r in rows]

    if not rows:
        return Output(selected_agents=[], council_size=0)

    # Deduplicate by agent_id — keep the first occurrence per unique agent_id
    seen: set = set()
    unique_rows: list[dict] = []
    for row in rows:
        aid = row.get("agent_id", "")
        if aid not in seen:
            seen.add(aid)
            unique_rows.append(row)

    task_keywords = _tokenize(data.stripped_task)
    expanded_keywords = _expand_synonyms(task_keywords)

    scored: list[tuple[int, dict]] = []
    for row in unique_rows:
        score = _score_agent(expanded_keywords, row.get("capabilities", "[]"))
        scored.append((score, row))

    scored.sort(key=lambda pair: (-pair[0], pair[1].get("agent_id", "")))

    selected_rows = scored[:max_council]

    selected_agents = [
        SelectedAgent(
            agent_id=row.get("agent_id", ""),
            agent_name=row.get("agent_name", ""),
            reasoning_bias=row.get("reasoning_bias", ""),
        )
        for _score, row in selected_rows
    ]

    return Output(
        selected_agents=selected_agents,
        council_size=len(selected_agents),
    )
