#input_type_name: ProcessHitlInput
#output_type_name: ProcessHitlOutput
#function_name: process_hitl

import json
import os
import re
import uuid
import urllib.request
import ssl
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod, RecordData
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError


OLLAMA_API_KEY = "dd0d6a4161864b4c967f2f8a5e807b59.WOynu1rNk33PgQMSSvkInkwp"
OLLAMA_BASE_URL = "https://ollama.com/v1/chat/completions"
OLLAMA_MODEL = "ministral-3:3b"


AGENT_SYSTEM_PROMPTS = {
    "policy-analyst": (
        "You are the Policy Analyst on the PANCHAI deliberation council. "
        "Evaluate tasks strictly against documented policies, compliance frameworks, and precedent risk. "
        "Default stance: AGAINST unless an explicit policy exception applies.\n\n"
        "Return EXACTLY ONE JSON object with fields:\n"
        '  "position": "FOR" | "AGAINST" | "ABSTAIN" | "REFRAME"\n'
        '  "argument": "<detailed policy reasoning with specific citations>"\n'
        '  "confidence": <0.0 to 1.0>\n'
        '  "key_evidence": "<single most critical policy provision>"\n'
        "No markdown. No extra text. One JSON object only."
    ),
    "customer-advocate": (
        "You are the Customer Advocate on the PANCHAI deliberation council. "
        "Champion the customer perspective — satisfaction, retention, and consumer rights. "
        "Default stance: FOR the customer when claim is reasonable and documented.\n\n"
        "Return EXACTLY ONE JSON object with fields:\n"
        '  "position": "FOR" | "AGAINST" | "ABSTAIN" | "REFRAME"\n'
        '  "argument": "<detailed customer-centric reasoning>"\n'
        '  "confidence": <0.0 to 1.0>\n'
        '  "key_evidence": "<single most critical customer factor>"\n'
        "No markdown. No extra text. One JSON object only."
    ),
    "fraud-risk-assessor": (
        "You are the Fraud Risk Assessor on the PANCHAI deliberation council. "
        "Identify fraud patterns, risk signals, abuse indicators, and quantify financial exposure. "
        "Default stance: AGAINST when any risk signals are present.\n\n"
        "Return EXACTLY ONE JSON object with fields:\n"
        '  "position": "FOR" | "AGAINST" | "ABSTAIN" | "REFRAME"\n'
        '  "argument": "<detailed risk assessment with abuse indicators>"\n'
        '  "confidence": <0.0 to 1.0>\n'
        '  "key_evidence": "<single most critical risk indicator>"\n'
        "No markdown. No extra text. One JSON object only."
    ),
    "supply-chain-analyst": (
        "You are the Supply Chain Analyst on the PANCHAI deliberation council. "
        "Evaluate operational continuity, logistics, demand forecasting, and inventory risk. "
        "Default stance: lean toward operational stability, flag risks proactively.\n\n"
        "Return EXACTLY ONE JSON object with fields:\n"
        '  "position": "FOR" | "AGAINST" | "ABSTAIN" | "REFRAME"\n'
        '  "argument": "<detailed supply chain reasoning>"\n'
        '  "confidence": <0.0 to 1.0>\n'
        '  "key_evidence": "<single most critical operational factor>"\n'
        "No markdown. No extra text. One JSON object only."
    ),
    "financial-risk": (
        "You are the Financial Risk advisor on the PANCHAI deliberation council. "
        "Analyze cash flow, financial exposure, vendor risk, and monetary impact. "
        "Default stance: conservative — preserve capital, flag financial risks.\n\n"
        "Return EXACTLY ONE JSON object with fields:\n"
        '  "position": "FOR" | "AGAINST" | "ABSTAIN" | "REFRAME"\n'
        '  "argument": "<detailed financial risk analysis>"\n'
        '  "confidence": <0.0 to 1.0>\n'
        '  "key_evidence": "<single most critical financial indicator>"\n'
        "No markdown. No extra text. One JSON object only."
    ),
    "procurement-specialist": (
        "You are the Procurement Specialist on the PANCHAI deliberation council. "
        "Evaluate vendor relationships, cost optimization, and order management strategy. "
        "Default stance: preserve vendor relationships while optimising cost.\n\n"
        "Return EXACTLY ONE JSON object with fields:\n"
        '  "position": "FOR" | "AGAINST" | "ABSTAIN" | "REFRAME"\n'
        '  "argument": "<detailed procurement reasoning>"\n'
        '  "confidence": <0.0 to 1.0>\n'
        '  "key_evidence": "<single most critical procurement factor>"\n'
        "No markdown. No extra text. One JSON object only."
    ),
}

_DEFAULT_SYSTEM_PROMPT = (
    "You are an expert deliberation council member. "
    "Evaluate the task objectively and return EXACTLY ONE JSON object with fields: "
    '"position" (FOR/AGAINST/ABSTAIN/REFRAME), "argument" (detailed reasoning), '
    '"confidence" (0.0-1.0), "key_evidence" (single most important factor). '
    "No markdown, no extra text."
)


class ProcessHitlInput(BaseModel):
    session_id: str
    decision: str
    decision_reason: str
    verdict: str
    confidence_score: float


class ProcessHitlOutput(BaseModel):
    session_id: str
    verdict: str
    confidence_score: float
    summary: str
    success: bool


class RedeBateResult(BaseModel):
    round_number: int
    responses: list


# ── JSON parsing ────────────────────────────────────────

def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"```$", "", text.rstrip()).rstrip()
    text = text.strip()
    if text.startswith("["):
        bs = text.find("{")
        be = text.rfind("}")
        if bs >= 0 and be > bs:
            text = text[bs : be + 1]
    bs = text.find("{")
    be = text.rfind("}")
    if bs >= 0 and be > bs:
        text = text[bs : be + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    pos  = re.search(r'"position"\s*:\s*"(FOR|AGAINST|ABSTAIN|REFRAME)"', text)
    conf = re.search(r'"confidence"\s*:\s*([0-9.]+)', text)
    arg  = re.search(r'"argument"\s*:\s*"([^"]*)"', text)
    return {
        "position":    pos.group(1)  if pos  else "ABSTAIN",
        "confidence":  float(conf.group(1)) if conf else 0.5,
        "argument":    arg.group(1)  if arg  else "",
    }


# ── Ollama Cloud direct call ────────────────────────────

def _call_ollama(system_prompt: str, user_prompt: str) -> dict:
    body = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 800,
    }
    payload = json.dumps(body).encode("utf-8")
    req = urllib_request.Request(
        OLLAMA_BASE_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        ctx = ssl.create_default_context()
        resp = urllib_request.urlopen(req, context=ctx, timeout=120)
        data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return _parse_json(content)
    except Exception:
        return {
            "position":    "ABSTAIN",
            "argument":    "Agent unavailable during re-debate.",
            "confidence":  0.5,
        }


def _call_ollama_text(prompt: str, system_prompt: str = "") -> str:
    body = {
        "model": OLLAMA_MODEL,
        "messages": [],
        "stream": False,
        "temperature": 0.3,
        "max_tokens": 512,
    }
    if system_prompt:
        body["messages"].append({"role": "system", "content": system_prompt})
    body["messages"].append({"role": "user", "content": prompt})
    data = json.dumps(body).encode()
    req = urllib_request.Request(
        OLLAMA_BASE_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        resp = urllib_request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode())
        return result["choices"][0]["message"]["content"].strip()
    except (HTTPError, URLError, Exception):
        return ""


# ── Verdict computation ─────────────────────────────────

def _compute_verdict(responses: List[dict]) -> dict:
    votes = {"FOR": 0, "AGAINST": 0, "ABSTAIN": 0, "REFRAME": 0}
    total_conf = 0.0
    for r in responses:
        p = r.get("position", "ABSTAIN").upper()
        if p in votes:
            votes[p] += 1
        total_conf += float(r.get("confidence", 0.5))
    n = max(len(responses), 1)
    avg_conf = total_conf / n
    majority = max(votes, key=votes.get)
    max_votes = votes[majority]
    if max_votes == 0 or majority == "ABSTAIN":
        verdict, consensus = "ESCALATED", False
    elif majority == "FOR" and max_votes > n / 2:
        verdict, consensus = "APPROVED", True
    elif majority == "AGAINST" and max_votes > n / 2:
        verdict, consensus = "REJECTED", True
    elif majority == "REFRAME" and max_votes > n / 2:
        verdict, consensus = "REFRAMED", True
    elif votes.get("FOR", 0) == votes.get("AGAINST", 0):
        verdict, consensus = "ESCALATED", False
    else:
        verdict, consensus = majority, True
    confidence = min(1.0, max(0.0, avg_conf * (max_votes / n)))
    hitl = confidence < 0.6 or not consensus
    return {
        "verdict":          verdict,
        "confidence_score": round(confidence, 2),
        "consensus_met":    consensus,
        "vote_breakdown":   votes,
        "hitl_required":    hitl,
    }


# ── Database helpers ────────────────────────────────────

def _safe_create(pod: Pod, table: str, data: dict) -> Optional[str]:
    try:
        rec = pod.records.create(table, RecordData(**data))
        return getattr(rec, "id", None) or (rec.get("id") if isinstance(rec, dict) else None)
    except Exception:
        return None


def _safe_update(pod: Pod, table: str, record_id: str, data: dict):
    try:
        pod.records.update(table, record_id, RecordData(**data))
    except Exception:
        pass


# ── Re-debate logic ─────────────────────────────────────

def _run_redebat(pod: Pod, session_id: str) -> dict:
    """Run a new debate round for the session. Returns the new verdict dict."""
    # 1. Load session to get task context
    try:
        session_recs = pod.records.list("debate_sessions", filter=[{"field": "id", "op": "eq", "value": session_id}])
        if not session_recs.items:
            return None
        session = session_recs.items[0].to_dict()
    except Exception:
        return None

    stripped_task = session.get("stripped_task", "")
    client_id = session.get("client_id", "")
    stakes_level = session.get("stakes_level", "STANDARD")

    if not stripped_task:
        return None

    # 2. Load existing debate messages to determine agents and provide context
    existing_agents = []
    previous_rounds_text = ""
    try:
        msg_recs = pod.records.list("debate_messages", filter=[{"field": "session_id", "op": "eq", "value": session_id}])
        if msg_recs.items:
            agent_set = set()
            lines = []
            for m in msg_recs.items:
                d = m.to_dict()
                aid = d.get("agent_name", d.get("agent_id", ""))
                if aid:
                    agent_set.add(aid)
                rn = d.get("round_number", 0)
                pos = d.get("position", "")
                arg = d.get("argument", "")[:200]
                lines.append(f"Round {rn} — {aid} ({pos}): {arg}")
            existing_agents = [a for a in agent_set if a]
            previous_rounds_text = "\n".join(lines)
    except Exception:
        pass

    if not existing_agents:
        existing_agents = ["policy-analyst", "customer-advocate"]

    # 3. Determine next round number
    next_round = 2
    try:
        round_recs = pod.records.list("debate_rounds", filter=[{"field": "session_id", "op": "eq", "value": session_id}])
        if round_recs.items:
            max_rn = 1
            for r in round_recs.items:
                d = r.to_dict()
                rn = int(d.get("round_number", 0))
                if rn > max_rn:
                    max_rn = rn
            next_round = max_rn + 1
    except Exception:
        pass

    # 4. Build re-debate prompt with previous context
    re_debate_prompt = (
        f"Task: {stripped_task}\n\n"
        f"Previous debate rounds:\n{previous_rounds_text}\n\n"
        f"The HITL reviewer sent this case back for further deliberation.\n"
        f"HITL reason: the previous verdict confidence was too low or consensus was not met.\n\n"
        f"Respond with your updated position on the original task. Consider the previous "
        f"arguments carefully and either affirm or adjust your stance. "
        f"Return your response in the required JSON format."
    )

    # 5. Call each agent via Ollama
    responses = []
    for agent_id in existing_agents:
        sys_prompt = AGENT_SYSTEM_PROMPTS.get(agent_id, _DEFAULT_SYSTEM_PROMPT)
        result = _call_ollama(sys_prompt, re_debate_prompt)
        responses.append({
            "agent_id":    agent_id,
            "position":    result.get("position", "ABSTAIN"),
            "argument":    result.get("argument", ""),
            "confidence":  float(result.get("confidence", 0.5)),
        })

    # 6. Create new debate round and messages
    round_id = str(uuid.uuid4())
    _safe_create(pod, "debate_rounds", {
        "id":           round_id,
        "session_id":   session_id,
        "round_number": next_round,
        "round_type":   "re_debate",
        "status":       "complete",
    })

    for r in responses:
        meta = AGENT_SYSTEM_PROMPTS.get(r["agent_id"], {})
        _safe_create(pod, "debate_messages", {
            "session_id":    session_id,
            "round_id":      round_id,
            "agent_id":      r["agent_id"],
            "agent_name":    r["agent_id"],
            "position":      r["position"],
            "argument":      r["argument"],
            "round_number":  next_round,
        })

    # 7. Compute new verdict
    verdict = _compute_verdict(responses)
    verdict_id = str(uuid.uuid4())

    conflict_report = {
        "council_finding": verdict["verdict"],
        "divergence_severity": "HIGH" if not verdict["consensus_met"] else "LOW",
        "explanation": (
            f"Re-debate round {next_round} reached {verdict['verdict']} with "
            f"{verdict['confidence_score']:.0%} confidence. "
        ),
    }

    _safe_create(pod, "verdicts", {
        "id":                  verdict_id,
        "session_id":          session_id,
        "verdict":             verdict["verdict"],
        "confidence_score":    verdict["confidence_score"],
        "council_vote_for":    json.dumps([r["agent_id"] for r in responses if r["position"] == "FOR"]),
        "council_vote_against": json.dumps([r["agent_id"] for r in responses if r["position"] == "AGAINST"]),
        "council_vote_abstain": json.dumps([r["agent_id"] for r in responses if r["position"] == "ABSTAIN"]),
        "council_vote_reframe": json.dumps([r["agent_id"] for r in responses if r["position"] == "REFRAME"]),
        "conflict_report":     json.dumps(conflict_report),
        "hitl_required":       verdict["hitl_required"],
        "hitl_reason":         "Re-debate still below confidence threshold." if verdict["hitl_required"] else "",
    })

    # 8. Create fresh HITL queue entry if needed
    final_status = "hitl" if verdict["hitl_required"] else "done"
    _safe_update(pod, "debate_sessions", session_id, {"status": final_status})

    if verdict["hitl_required"]:
        _safe_create(pod, "hitl_queue", {
            "session_id":      session_id,
            "verdict_id":      verdict_id,
            "status":          "pending",
            "escalation_tier": 2,
            "hitl_reason":     "Re-debate still below confidence threshold.",
        })

    return verdict


# ── Main entry point ────────────────────────────────────

async def process_hitl(ctx: FunctionContext, data: ProcessHitlInput) -> ProcessHitlOutput:
    pod = Pod.from_env()
    session_id = data.session_id
    decision = data.decision
    decision_reason = data.decision_reason
    final_verdict = data.verdict if decision != "reject" else "REJECTED"

    if decision == "send_back":
        # Run a full re-debate round
        new_verdict = _run_redebat(pod, session_id)
        if new_verdict:
            final_verdict = new_verdict["verdict"]
            final_conf = new_verdict["confidence_score"]
            summary = f"Re-debate completed. Council reached: {final_verdict} ({final_conf:.0%} confidence). HITL reason: {decision_reason}"
            return ProcessHitlOutput(
                session_id=session_id,
                verdict=final_verdict,
                confidence_score=final_conf,
                summary=summary,
                success=True,
            )
        # If re-debate failed, fall through to basic handling

    final_status = "done" if decision != "send_back" else "debating"

    try:
        prompt = (
            f"The HITL reviewer made the following decision on a deliberation session:\n"
            f"- Council verdict: {data.verdict}\n"
            f"- Confidence score: {data.confidence_score}\n"
            f"- HITL decision: {decision}\n"
            f"- Reason: {decision_reason}\n\n"
            f"Write a 1-sentence summary of this HITL resolution."
        )
        summary = _call_ollama_text(prompt)
    except Exception:
        summary = f"HITL decision: {decision}. Reason: {decision_reason}."
    if not summary:
        summary = f"HITL decision: {decision}. Reason: {decision_reason}."

    try:
        hitl_records = pod.records.list("hitl_queue", filter=[{"field": "session_id", "op": "eq", "value": session_id}])
        if hitl_records.items:
            hitl_id = hitl_records.items[0].to_dict()["id"]
            pod.records.update("hitl_queue", hitl_id, RecordData(**{
                "status": "resolved",
                "decision": decision,
                "decision_reason": decision_reason,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
            }))
    except Exception:
        pod.records.create("hitl_queue", RecordData(**{
            "session_id": session_id,
            "status": "resolved",
            "decision": decision,
            "decision_reason": decision_reason,
            "escalation_tier": 2,
        }))

    try:
        pod.records.update("debate_sessions", session_id, RecordData(**{
            "status": final_status,
        }))
    except Exception:
        pass

    return ProcessHitlOutput(
        session_id=session_id,
        verdict=final_verdict,
        confidence_score=data.confidence_score,
        summary=summary,
        success=True,
    )
