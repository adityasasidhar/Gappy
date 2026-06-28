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
    catalog_table = pod.get_table("agent_catalog")
    rows = await catalog_table.query(
        filters={"client_id": data.client_id}
    )

    if not rows:
        # No agents registered for this client — return empty council
        return Output(selected_agents=[], council_size=0)

    # Tokenize the task
    task_keywords = _tokenize(data.stripped_task)

    # Score each agent
    scored: list[tuple[int, dict]] = []
    for row in rows:
        score = _score_agent(task_keywords, row.get("capabilities", "[]"))
        scored.append((score, row))

    # Sort descending by score, then by agent_id for deterministic ordering
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("agent_id", "")))

    # If no agent has any keyword overlap, still return the first N agents
    # (ensures the debate always has a council)
    selected_rows = scored[:max_council]

    # Build output
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
