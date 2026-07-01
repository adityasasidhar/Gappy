#input_type_name: GoalStripInput
#output_type_name: GoalStripOutput
#function_name: goal_strip

"""
Goal Stripper ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Blind Tribunal Protocol
========================================
Deterministic function (no LLM) that:
1. Extracts the user's preference/desired outcome into user_goal
2. Reframes remaining facts as a neutral evaluation request (stripped_task)
3. Classifies stakes_level as HIGH or STANDARD based on keyword detection

Part of PANCHAI's anti-sycophancy architecture: agents never see the user's
desired outcome ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â they only receive the stripped, neutral task.
"""

from typing import Optional

from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod, RecordData
import re
import uuid


class GoalStripInput(BaseModel):
    task_input: str
    session_id: Optional[str] = None
    client_id: Optional[str] = None
    task_context: Optional[str] = None


class GoalStripOutput(BaseModel):
    session_id: Optional[str] = None
    client_id: Optional[str] = None
    task_context: Optional[str] = None
    stripped_task: str
    user_goal: str
    stakes_level: str
    council_size: int = 3


# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Goal-laden phrases that signal user preference ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
GOAL_PHRASES = [
    r"\bshould\s+we\b",
    r"\bi\s+want\b",
    r"\bwe\s+should\b",
    r"\bapprove\b",
    r"\breject\b",
    r"\blaunch\b",
    r"\bpause\b",
    r"\bcancel\b",
    r"\bproceed\b",
    r"\bgo\s+ahead\b",
    r"\blet'?s\b",
    r"\bi\s+think\s+we\s+should\b",
    r"\bwe\s+need\s+to\b",
]

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ HIGH stakes keyword sets ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
FINANCIAL_PATTERN = re.compile(
    r"\$\s*[\d,]+(?:\.\d+)?\s*(?:k|K|m|M|b|B|million|billion|thousand)?",
    re.IGNORECASE,
)

LEGAL_TERMS = [
    "liability", "compliance", "regulation", "regulatory", "legal",
    "contract", "lawsuit", "litigation", "statute", "indemnity",
    "fiduciary", "negligence", "breach", "jurisdiction",
]

SAFETY_TERMS = [
    "risk", "fraud", "security", "breach", "vulnerability", "threat",
    "incident", "hazard", "danger", "unsafe", "violation", "abuse",
    "prior refunds", "refunds in", "multiple refunds", "repeat refunds",
    "refund abuse", "return abuse", "chargeback", "chargebacks",
    "suspicious pattern", "red flag", "red flags",
]

HEALTH_TERMS = [
    "health", "patient", "medical", "clinical", "diagnosis", "treatment",
    "dosage", "adverse", "pharmaceutical", "drug", "therapy", "safety",
    "hipaa", "surgical", "injury",
]


def _extract_financial_amount(text: str):
    """Extract the largest dollar amount from text. Returns None if no match."""
    matches = FINANCIAL_PATTERN.findall(text)
    if not matches:
        return None

    largest = 0.0
    for match in matches:
        # Clean up: remove $, commas, whitespace
        cleaned = match.replace("$", "").replace(",", "").strip()

        # Handle suffixes
        multiplier = 1.0
        lower = cleaned.lower()
        for suffix, mult in [
            ("billion", 1_000_000_000), ("b", 1_000_000_000),
            ("million", 1_000_000), ("m", 1_000_000),
            ("thousand", 1_000), ("k", 1_000),
        ]:
            if lower.endswith(suffix):
                cleaned = cleaned[:len(cleaned) - len(suffix)].strip()
                multiplier = mult
                break

        try:
            value = float(cleaned) * multiplier
            largest = max(largest, value)
        except ValueError:
            continue

    return largest if largest > 0 else None


def _has_keyword_match(text: str, keywords: list[str]) -> bool:
    """Check if any keyword appears in the text (case-insensitive, word boundary)."""
    text_lower = text.lower()
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text_lower):
            return True
    return False


def _classify_stakes(text: str) -> str:
    """Classify stakes level based on content analysis."""
    # Financial amounts > $10K
    amount = _extract_financial_amount(text)
    if amount is not None and amount > 10_000:
        return "HIGH"

    # Legal terms
    if _has_keyword_match(text, LEGAL_TERMS):
        return "HIGH"

    # Safety terms (includes fraud, risk, security)
    if _has_keyword_match(text, SAFETY_TERMS):
        return "HIGH"

    # Health terms
    if _has_keyword_match(text, HEALTH_TERMS):
        return "HIGH"

    return "STANDARD"


def _extract_goal_and_strip(text: str) -> tuple[str, str]:
    """
    Separate user's desired outcome from task facts.

    Returns:
        (stripped_task, user_goal)
    """
    sentences = re.split(r'(?<=[.!?])\s+|(?<=\?)\s*', text.strip())
    if not sentences:
        return text, ""

    goal_sentences = []
    fact_sentences = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        is_goal = False
        for pattern in GOAL_PHRASES:
            if re.search(pattern, sentence, re.IGNORECASE):
                is_goal = True
                break

        if is_goal:
            goal_sentences.append(sentence)
            embedded_fact = _extract_facts_from_goal(sentence).replace("Evaluate the following situation. ", "").strip()
            if embedded_fact:
                fact_sentences.append(embedded_fact)
        else:
            fact_sentences.append(sentence)

    # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Build user_goal ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
    user_goal = ""
    if goal_sentences:
        # Extract the core action from the first goal sentence
        goal_text = goal_sentences[0]
        user_goal = _normalize_goal(goal_text)

    # ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Build stripped_task ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
    if fact_sentences:
        stripped = _reframe_facts(fact_sentences)
    else:
        # If the entire input is a goal sentence, extract facts from it
        stripped = _extract_facts_from_goal(text)

    return stripped, user_goal


def _normalize_goal(goal_text: str) -> str:
    """
    Convert a goal-laden sentence into a clean statement of user intent.
    e.g., "Should we approve this refund?" ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ "Approve the refund"
    """
    text = goal_text.strip().rstrip("?").rstrip(".")

    # Pattern: "Should we <action> this/the <thing>"
    match = re.match(
        r"(?:should\s+we|i\s+want\s+to|we\s+should|let'?s)\s+(.+)",
        text,
        re.IGNORECASE,
    )
    if match:
        action_part = match.group(1).strip()
        # Capitalize first letter, clean up
        action_part = action_part[0].upper() + action_part[1:]
        # Replace "this" with "the" for cleaner phrasing
        action_part = re.sub(r"\bthis\b", "the", action_part, count=1)
        return action_part

    return text[0].upper() + text[1:] if text else ""


def _reframe_facts(fact_sentences: list[str]) -> str:
    """
    Reframe fact sentences as a neutral evaluation request.
    Structures the facts into a clean, evaluative format.
    """
    # Parse key-value pairs from comma/period-separated facts
    structured_facts = []

    for sentence in fact_sentences:
        # Clean up the sentence
        sentence = sentence.strip().rstrip(".")

        # Try to parse "key = value" or "key: value" patterns
        parts = re.split(r',\s*(?!\d{3}\b)', sentence)
        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Normalize common patterns
            part = _normalize_fact(part)
            if part:
                structured_facts.append(part)

    if not structured_facts:
        return "Evaluate the following situation. " + " ".join(fact_sentences)

    return "Evaluate the following situation. " + " ".join(
        f"{fact}." for fact in structured_facts
    )


def _normalize_fact(fact: str) -> str:
    """Normalize a single fact fragment into a neutral statement."""
    fact = fact.strip()
    if not fact:
        return ""

    # "key = value" ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ "Key: value"
    match = re.match(r"(.+?)\s*=\s*(.+)", fact)
    if match:
        key = match.group(1).strip()
        value = match.group(2).strip()
        key = _humanize_key(key)
        return f"{key}: {value}"

    # Already a statement ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â capitalize first letter
    return fact[0].upper() + fact[1:] if fact else ""


def _humanize_key(key: str) -> str:
    """Convert shorthand keys into human-readable labels."""
    key_map = {
        "policy": "Return policy",
        "claim": "Claim type",
        "purchase": "Purchase",
        "customer tier": "Customer tier",
    }

    key_lower = key.lower().strip()
    if key_lower in key_map:
        return key_map[key_lower]

    # General: capitalize, replace underscores
    return key.replace("_", " ").strip().capitalize() if key else key


def _extract_facts_from_goal(text: str) -> str:
    """
    When the entire input is one goal sentence with embedded facts,
    extract and restructure the factual content.
    """
    # Remove the goal-laden prefix
    cleaned = text
    for pattern in GOAL_PHRASES:
        cleaned = re.sub(pattern, "", cleaned, count=1, flags=re.IGNORECASE)

    cleaned = cleaned.strip().lstrip("?").strip().rstrip("?.").strip()

    # Try to identify the subject and reframe
    return f"Evaluate the following situation. {cleaned}"


async def goal_strip(ctx: FunctionContext, data: GoalStripInput) -> GoalStripOutput:
    """
    Main entry point for the Goal Stripper function.

    Implements the Blind Tribunal Protocol's first step:
    - Strips user's desired outcome from the task input
    - Reframes facts as a neutral evaluation request
    - Classifies stakes level for consensus threshold selection
    """
    task_input = data.task_input.strip()
    session_id = data.session_id
    client_id = data.client_id or "yesmadam"
    pod = Pod.from_env()

    if not session_id:
        session_id = str(uuid.uuid4())
        try:
            pod.records.create("debate_sessions", RecordData(
                id=session_id,
                client_id=client_id,
                task_input=task_input,
                task_context=data.task_context or "",
                status="pending",
            ))
        except Exception:
            pass

    if not task_input:
        return GoalStripOutput(
            session_id=session_id,
            client_id=client_id,
            task_context=data.task_context,
            stripped_task="No task input provided.",
            user_goal="",
            stakes_level="STANDARD",
            council_size=3,
        )

    stripped_task, user_goal = _extract_goal_and_strip(task_input)
    stakes_level = _classify_stakes(task_input)

    # Update session with stripped info
    try:
        pod.records.update("debate_sessions", session_id, RecordData(
            stripped_task=stripped_task,
            user_goal=user_goal,
            stakes_level=stakes_level,
            council_size=5 if stakes_level == "HIGH" else 3,
        ))
    except Exception:
        pass

    return GoalStripOutput(
        session_id=session_id,
        client_id=client_id,
        task_context=data.task_context,
        stripped_task=stripped_task,
        user_goal=user_goal,
        stakes_level=stakes_level,
        council_size=5 if stakes_level == "HIGH" else 3,
    )
