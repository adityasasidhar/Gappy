#input_type_name: PipelineInput
#output_type_name: PipelineOutput
#function_name: run_pipeline

# PANCHAI fast-path pipeline: deterministic, sub-second demonstration of the
# core loop used by the browser demo.

import json
import re
from typing import Dict, Optional, Tuple
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class PipelineInput(BaseModel):
    session_id: str


class PipelineOutput(BaseModel):
    session_id: str
    status: str
    verdict: Optional[str] = None
    verdict_id: Optional[str] = None
    hitl_required: bool = False
    error: Optional[str] = None


GOAL_PHRASES = [
    r"\bshould\s+we\b", r"\bi\s+want\b", r"\bwe\s+should\b",
    r"\bapprove\b", r"\breject\b", r"\blaunch\b", r"\bpause\b",
    r"\bcancel\b", r"\bproceed\b", r"\bgo\s+ahead\b", r"\blet'?s\b",
    r"\bi\s+think\s+we\s+should\b", r"\bwe\s+need\s+to\b",
]

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


def _extract_financial_amount(text: str) -> Optional[float]:
    matches = FINANCIAL_PATTERN.findall(text)
    if not matches:
        return None

    largest = 0.0
    for match in matches:
        cleaned = match.replace("$", "").replace(",", "").strip()
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
            largest = max(largest, float(cleaned) * multiplier)
        except ValueError:
            continue

    return largest if largest > 0 else None


def _has_keyword_match(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text_lower):
            return True
    return False


def _classify_stakes(text: str) -> str:
    amount = _extract_financial_amount(text)
    if amount is not None and amount > 10_000:
        return "HIGH"
    if _has_keyword_match(text, LEGAL_TERMS):
        return "HIGH"
    if _has_keyword_match(text, SAFETY_TERMS):
        return "HIGH"
    if _has_keyword_match(text, HEALTH_TERMS):
        return "HIGH"
    return "STANDARD"


def _normalize_goal(goal_text: str) -> str:
    text = goal_text.strip().rstrip("?").rstrip(".")
    match = re.match(r"(?:should\s+we|i\s+want\s+to|we\s+should|let'?s)\s+(.+)", text, re.IGNORECASE)
    if match:
        action = match.group(1).strip()
        action = action[0].upper() + action[1:] if action else ""
        action = re.sub(r"\bthis\b", "the", action, count=1)
        return action
    return text[0].upper() + text[1:] if text else ""


def _humanize_key(key: str) -> str:
    key_map = {
        "policy": "Return policy",
        "claim": "Claim type",
        "purchase": "Purchase",
        "customer tier": "Customer tier",
    }
    key_lower = key.lower().strip()
    if key_lower in key_map:
        return key_map[key_lower]
    return key.replace("_", " ").strip().capitalize() if key else key


def _normalize_fact(fact: str) -> str:
    fact = fact.strip()
    if not fact:
        return ""
    match = re.match(r"(.+?)\s*=\s*(.+)", fact)
    if match:
        return f"{_humanize_key(match.group(1).strip())}: {match.group(2).strip()}"
    return fact[0].upper() + fact[1:] if fact else ""


def _reframe_facts(fact_sentences: list[str]) -> str:
    structured = []
    for sentence in fact_sentences:
        for part in re.split(r",\s*", sentence.strip().rstrip(".")):
            normalized = _normalize_fact(part)
            if normalized:
                structured.append(normalized)
    if not structured:
        return "Evaluate the following situation. " + " ".join(fact_sentences)
    return "Evaluate the following situation. " + " ".join(f"{fact}." for fact in structured)


def _extract_facts_from_goal(text: str) -> str:
    cleaned = text
    for pattern in GOAL_PHRASES:
        cleaned = re.sub(pattern, "", cleaned, count=1, flags=re.IGNORECASE)
    cleaned = cleaned.strip().lstrip("?").strip().rstrip("?.").strip()
    cleaned = re.sub(r"\bthis\b", "the", cleaned, count=1, flags=re.IGNORECASE)
    return f"Evaluate the following situation. {cleaned}"


def _extract_goal_and_strip(text: str) -> Tuple[str, str]:
    sentences = re.split(r"(?<=[.!?])\s+|(?<=\?)\s*", text.strip())
    goal_sentences, fact_sentences = [], []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in GOAL_PHRASES):
            goal_sentences.append(sentence)
            embedded_fact = _extract_facts_from_goal(sentence).replace("Evaluate the following situation. ", "").strip()
            if embedded_fact:
                fact_sentences.append(embedded_fact)
        else:
            fact_sentences.append(sentence)
    user_goal = _normalize_goal(goal_sentences[0]) if goal_sentences else ""
    stripped = _reframe_facts(fact_sentences) if fact_sentences else _extract_facts_from_goal(text)
    return stripped, user_goal


def _strip_goal(task_input: str) -> Tuple[str, str, str]:
    if not task_input:
        return "No task input provided.", "", "STANDARD"
    stripped_task, user_goal = _extract_goal_and_strip(task_input)
    return stripped_task, user_goal, _classify_stakes(task_input)


YESMADAM_AGENTS = [
    {
        "id": "customer-advocate",
        "display": "Customer Advocate",
        "bias": "Customer-first",
        "keywords_for": ["defect", "defective", "quality issue", "broken", "customer", "loyal", "gold", "exception", "goodwill", "retention"],
        "keywords_against": ["fraud", "abuse", "pattern", "excessive", "bad faith"],
        "keywords_reframe": [],
        "premortem": (
            "A rigid rejection could turn a legitimate defect complaint into churn and reputational damage.",
            "The defect claim may be more important than the standard return window.",
            "The customer and brand trust.",
            "HIGH",
        ),
    },
    {
        "id": "policy-analyst",
        "display": "Policy Analyst",
        "bias": "Rule-following",
        "keywords_for": ["policy permits", "within policy", "exception allowed"],
        "keywords_against": ["policy", "30-day", "47 days", "outside policy", "expired", "violation", "non-compliant"],
        "keywords_reframe": [],
        "premortem": (
            "Approving the refund could create an undocumented exception to the 30-day policy.",
            "A defect claim may not automatically override the return-window rule.",
            "Operations, compliance, and future customers subject to precedent.",
            "HIGH",
        ),
    },
    {
        "id": "fraud-risk-assessor",
        "display": "Fraud Risk Assessor",
        "bias": "Risk-averse",
        "keywords_for": ["verified", "authentic", "trusted", "low risk", "first time"],
        "keywords_against": ["suspicious", "multiple", "frequent", "history of", "prior refunds", "refunds in", "red flag"],
        "keywords_reframe": [],
        "premortem": (
            "The approval may reward repeat refund behavior without additional verification.",
            "Gold-tier status may be masking an emerging refund-abuse pattern.",
            "The business and legitimate customers affected by policy abuse.",
            "HIGH",
        ),
    },
]

BINOCS_AGENTS = [
    {
        "id": "supply-chain-analyst",
        "display": "Supply Chain Analyst",
        "bias": "Operational continuity",
        "keywords_for": [],
        "keywords_against": ["pause", "lead time", "vendor reliability"],
        "keywords_reframe": ["inventory", "demand forecast", "lead time", "vendor reliability", "pause"],
        "premortem": (
            "A full pause could create a stockout because lead time is 45 days.",
            "Inventory coverage may be overestimated against demand volatility.",
            "Customers and fulfillment operations.",
            "HIGH",
        ),
    },
    {
        "id": "financial-risk",
        "display": "Financial Risk",
        "bias": "Cash preservation",
        "keywords_for": ["cash position tight", "tight cash"],
        "keywords_against": [],
        "keywords_reframe": ["cash position tight", "vendor order", "pause", "inventory"],
        "premortem": (
            "The company may preserve cash short-term but incur higher recovery costs later.",
            "The cash constraint may be real, but a full stop is not the only lever.",
            "Finance, procurement, and revenue teams.",
            "MEDIUM",
        ),
    },
    {
        "id": "procurement-specialist",
        "display": "Procurement Specialist",
        "bias": "Vendor relationship",
        "keywords_for": [],
        "keywords_against": ["pause", "vendor reliability", "lead time"],
        "keywords_reframe": ["vendor", "order", "lead time", "reliability", "cash position"],
        "premortem": (
            "A unilateral pause could damage vendor trust and worsen already-low reliability.",
            "The vendor may not accept a late binary stop without commercial consequences.",
            "Procurement and future supply reliability.",
            "HIGH",
        ),
    },
]


def _select_agents(client_id: str, task_input: str) -> list[Dict]:
    text = f"{client_id} {task_input}".lower()
    if "binocs" in text or any(term in text for term in ["vendor", "inventory", "lead time"]):
        return BINOCS_AGENTS
    return YESMADAM_AGENTS


def _score_position(text: str, agent: Dict) -> str:
    text_lower = text.lower()
    for_kw = sum(1 for kw in agent["keywords_for"] if kw.lower() in text_lower)
    against_kw = sum(1 for kw in agent["keywords_against"] if kw.lower() in text_lower)
    reframe_kw = sum(1 for kw in agent["keywords_reframe"] if kw.lower() in text_lower)
    if reframe_kw >= max(for_kw, against_kw, 1):
        return "REFRAME"
    if for_kw > against_kw:
        return "FOR"
    if against_kw > for_kw:
        return "AGAINST"
    return "ABSTAIN"


def _generate_argument(text: str, position: str, agent: Dict) -> str:
    display = agent["display"]
    lower = text.lower()
    if position == "REFRAME":
        if "vendor" in lower:
            return f"{display}: Do not fully pause the order. Reframe to a partial or staggered order, negotiate payment terms, and preserve supply coverage while cash remains tight."
        return f"{display}: The decision should be reframed before execution."
    if position == "FOR":
        if "defect" in lower or "quality" in lower:
            return f"{display}: The product defect indicates a legitimate quality issue that should be accommodated."
        return f"{display}: The request appears reasonable from this perspective."
    if position == "AGAINST":
        if "prior" in lower or "refund" in lower:
            return f"{display}: Multiple prior refunds and an expired return window create policy and abuse risk."
        if "pause" in lower and "vendor" in lower:
            return f"{display}: A full vendor pause is too blunt given demand, lead time, and vendor reliability constraints."
        return f"{display}: I cannot support this request under current constraints."
    return f"{display}: The evidence is mixed and needs stronger review."


def _compute_confidence(text: str, position: str, agent: Dict) -> float:
    text_lower = text.lower()
    matched = 0
    for key in ["keywords_for", "keywords_against", "keywords_reframe"]:
        matched += sum(1 for kw in agent[key] if kw.lower() in text_lower)
    base = 0.55 if position == "ABSTAIN" else 0.65
    return min(0.95, base + min(matched, 4) * 0.075)


def _verdict_from_position(position: str) -> str:
    return {"FOR": "APPROVED", "AGAINST": "REJECTED", "REFRAME": "REFRAMED", "ABSTAIN": "ESCALATED"}.get(position, "ESCALATED")


def _conflict_report(user_goal: str, verdict: str, stripped_task: str) -> dict:
    goal = user_goal.lower()
    approving_goal = any(term in goal for term in ["approve", "proceed", "go ahead", "launch"])
    rejecting_goal = any(term in goal for term in ["reject", "cancel", "pause"])
    if verdict == "APPROVED" and approving_goal:
        severity = "LOW"
    elif verdict == "REJECTED" and rejecting_goal:
        severity = "LOW"
    elif verdict == "REFRAMED":
        severity = "MODERATE" if user_goal else "LOW"
    elif user_goal:
        severity = "HIGH"
    else:
        severity = "LOW"
    return {"user_goal": user_goal, "council_finding": f"{verdict}: {stripped_task}", "divergence_severity": severity}


def _hitl_reason(confidence_score: float, consensus_met: bool, conflict_report: dict, has_critical: bool, is_tie: bool) -> Tuple[bool, str]:
    reasons = []
    if conflict_report.get("divergence_severity") == "HIGH":
        reasons.append("Council finding strongly contradicts the submitted goal")
    if is_tie:
        reasons.append("Council vote is tied")
    if not consensus_met:
        reasons.append("Council did not reach majority consensus")
    if confidence_score < 0.60:
        reasons.append("Confidence is below the 0.60 escalation threshold")
    if has_critical:
        reasons.append("At least one pre-mortem flagged critical severity")
    return bool(reasons), "; ".join(reasons)


def _record_id(record) -> str:
    if hasattr(record, "to_dict"):
        return str(record.to_dict().get("id", ""))
    if isinstance(record, dict):
        return str(record.get("id", ""))
    return str(getattr(record, "id", record))


def run_pipeline(ctx: FunctionContext, data: PipelineInput) -> PipelineOutput:
    session_id = data.session_id
    pod = Pod.from_env()
    try:
        raw = pod.records.get("debate_sessions", session_id)
        session = raw.to_dict() if hasattr(raw, "to_dict") else dict(raw)
        task_input = session.get("task_input", "")
        client_id = session.get("client_id", "demo")

        if session.get("status") != "pending":
            return PipelineOutput(session_id=session_id, status=session.get("status", "unknown"), error="Already processed")

        stripped_task, user_goal, stakes_level = _strip_goal(task_input)

        # Search Files API for similar historical verdicts (Institutional Memory / RAG)
        historical_context = ""
        try:
            # Create folder if it doesn't exist
            try:
                pod.files.create_folder("/memory")
            except Exception:
                pass
            
            search_res = pod.files.search(query=stripped_task, scope_path="/memory", search_method="HYBRID")
            items = []
            if hasattr(search_res, "items"):
                items = search_res.items
            elif isinstance(search_res, dict) and "items" in search_res:
                items = search_res["items"]
                
            if items:
                context_parts = ["Similar historical verdicts found in memory:"]
                for item in items[:2]:
                    file_path = ""
                    if hasattr(item, "path"):
                        file_path = item.path
                    elif isinstance(item, dict) and "path" in item:
                        file_path = item["path"]
                    
                    if not file_path:
                        continue
                        
                    content = ""
                    try:
                        content_bytes = pod.files.download(file_path)
                        content = content_bytes.decode("utf-8") if isinstance(content_bytes, bytes) else str(content_bytes)
                    except Exception as download_err:
                        print(f"Error downloading memory file {file_path}: {download_err}")
                    
                    if content:
                        lines = [line.strip() for line in content.split("\n") if line.strip() and not line.strip().startswith("#")][:3]
                        context_parts.append(f"- {file_path}: " + " | ".join(lines))
                
                if len(context_parts) > 1:
                    historical_context = "\n".join(context_parts)
        except Exception as search_err:
            print(f"Error performing historical files search: {search_err}")

        if historical_context:
            stripped_task = f"{stripped_task}\n\n[Memory Context]\n{historical_context}"

        agents = _select_agents(client_id, task_input)

        pod.records.update("debate_sessions", session_id, {"status": "pre_mortem", "stripped_task": stripped_task, "user_goal": user_goal, "stakes_level": stakes_level, "council_size": len(agents)})

        pre_round = pod.records.create("debate_rounds", {"session_id": session_id, "round_number": 0, "round_type": "pre_mortem", "status": "active"})
        pre_round_id = _record_id(pre_round)

        pre_mortem_summary = []
        has_critical = False
        for agent in agents:
            failure, assumption, stakeholder, severity = agent["premortem"]
            has_critical = has_critical or severity == "CRITICAL"
            pre_mortem_summary.append({"agent_id": agent["id"], "failure_reason": failure, "weak_assumption": assumption, "harmed_stakeholder": stakeholder, "severity": severity})
            pod.records.create("pre_mortems", {"session_id": session_id, "round_id": pre_round_id, "agent_id": agent["id"], "failure_reason": failure, "weak_assumption": assumption, "harmed_stakeholder": stakeholder, "severity": severity})
            pod.records.create("debate_messages", {"session_id": session_id, "round_id": pre_round_id, "agent_id": agent["id"], "agent_name": agent["display"], "round_number": 0, "position": "ABSTAIN", "argument": f"If this fails: {failure}\nWeak assumption: {assumption}\nMost harmed: {stakeholder}", "reasoning_bias": agent["bias"]})

        pod.records.update("debate_rounds", pre_round_id, {"status": "complete"})
        pod.records.update("debate_sessions", session_id, {"status": "debating"})

        debate_round = pod.records.create("debate_rounds", {"session_id": session_id, "round_number": 1, "round_type": "debate", "status": "active", "challenge_prompt": "Final position after pre-mortem risk surfacing."})
        debate_round_id = _record_id(debate_round)

        votes = {"FOR": [], "AGAINST": [], "ABSTAIN": [], "REFRAME": []}
        reasoning_trail = []
        final_arguments = {}

        for agent in agents:
            position = _score_position(task_input, agent)
            argument = _generate_argument(task_input, position, agent)
            confidence = _compute_confidence(task_input, position, agent)
            votes[position].append(agent["display"])
            final_arguments[agent["display"]] = argument
            reasoning_trail.append({"round": 1, "agent": agent["id"], "position": position, "confidence": confidence, "argument_summary": argument})
            pod.records.create("debate_messages", {"session_id": session_id, "round_id": debate_round_id, "agent_id": agent["id"], "agent_name": agent["display"], "round_number": 1, "position": position, "argument": argument, "reasoning_bias": agent["bias"]})

        pod.records.update("debate_rounds", debate_round_id, {"status": "complete"})
        pod.records.update("debate_sessions", session_id, {"status": "voting"})

        total = sum(len(items) for items in votes.values())
        max_count = max(len(items) for items in votes.values()) if total else 0
        winners = [position for position, items in votes.items() if len(items) == max_count]
        is_tie = len(winners) > 1
        consensus_met = total > 0 and max_count > total / 2 and not is_tie
        winning_position = winners[0] if consensus_met else "ABSTAIN"
        verdict = _verdict_from_position(winning_position)
        confidence_score = max_count / max(total, 1)
        conflict = _conflict_report(user_goal, verdict, stripped_task)
        hitl_required, hitl_reason = _hitl_reason(confidence_score, consensus_met, conflict, has_critical, is_tie)

        minority = ""
        for position, names in votes.items():
            if position != winning_position and names:
                minority = final_arguments.get(names[0], "")
                break

        vd = pod.records.create("verdicts", {"session_id": session_id, "verdict": verdict, "confidence_score": confidence_score, "council_vote_for": json.dumps(votes["FOR"]), "council_vote_against": json.dumps(votes["AGAINST"]), "council_vote_abstain": json.dumps(votes["ABSTAIN"]), "council_vote_reframe": json.dumps(votes["REFRAME"]), "conflict_report": json.dumps(conflict), "reasoning_trail": json.dumps(reasoning_trail), "pre_mortem_summary": json.dumps(pre_mortem_summary), "hitl_required": hitl_required, "hitl_reason": hitl_reason, "recommended_action": "Escalate to a human approver." if hitl_required else f"Council verdict: {verdict.lower()}.", "minority_dissent": minority})
        verdict_id = _record_id(vd)

        # Archiving verdict to Files API for Institutional Memory
        try:
            verdict_md = f"""# Verdict Summary (Session {session_id})
Client ID: {client_id}
Verdict: {verdict}
Stakes Level: {stakes_level}
Confidence Score: {confidence_score:.2f}
Task Input: {task_input}
Stripped Task: {stripped_task}
User Goal: {user_goal}
HITL Required: {hitl_required}
HITL Reason: {hitl_reason}
Recommended Action: {"Escalate to a human approver." if hitl_required else f"Council verdict: {verdict.lower()}."}
"""
            pod.files.write_text(f"/memory/verdict_{session_id}.md", verdict_md)
        except Exception as file_err:
            print(f"Error archiving verdict to Files API: {file_err}")

        if hitl_required:
            pod.records.create("hitl_queue", {"session_id": session_id, "verdict_id": verdict_id, "status": "pending", "escalation_tier": 2})
            pod.records.update("debate_sessions", session_id, {"status": "hitl"})
            return PipelineOutput(session_id=session_id, status="hitl", verdict=verdict, verdict_id=verdict_id, hitl_required=True)

        pod.records.update("debate_sessions", session_id, {"status": "done"})
        return PipelineOutput(session_id=session_id, status="done", verdict=verdict, verdict_id=verdict_id, hitl_required=False)

    except Exception as e:
        try:
            pod.records.update("debate_sessions", session_id, {"status": "failed"})
        except Exception:
            pass
        return PipelineOutput(session_id=session_id, status="failed", error=str(e))