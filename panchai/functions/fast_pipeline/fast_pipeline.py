#input_type_name: FastPipelineInput
#output_type_name: FastPipelineOutput
#function_name: fast_pipeline

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


OLLAMA_API_KEY = "cdc48c82f5ba485db083e41d0d04eceb.ZjWzBuHQMqi8Fg3F9P5S2M8E"
OLLAMA_BASE = "https://ollama.com/v1/chat/completions"
MODEL = "ministral-3:3b"

COUNCIL = [
    {
        "id": "policy-analyst",
        "system": "You are a Policy Analyst. Return a SINGLE JSON object with: position (FOR/AGAINST/ABSTAIN), argument (1 sentence), confidence (0-1). Never return arrays.",
    },
    {
        "id": "customer-advocate",
        "system": "You are a Customer Advocate. Return a SINGLE JSON object with: position (FOR/AGAINST/ABSTAIN), argument (1 sentence), confidence (0-1). Never return arrays.",
    },
    {
        "id": "fraud-risk-assessor",
        "system": "You are a Fraud Risk Assessor. Return a SINGLE JSON object with: position (FOR/AGAINST/ABSTAIN), argument (1 sentence), confidence (0-1). Never return arrays.",
    },
]


class FastPipelineInput(BaseModel):
    session_id: str
    stripped_task: str
    user_goal: str = ""
    client_id: Optional[str] = None
    stakes_level: str = "STANDARD"
    council_size: int = 3


class AgentVote(BaseModel):
    agent_id: str
    position: str
    argument: str
    confidence: float


class VerdictResult(BaseModel):
    verdict: str
    confidence_score: float
    consensus_met: bool
    vote_breakdown: dict
    hitl_required: bool


class FastPipelineOutput(BaseModel):
    session_id: str
    elapsed: float
    council_responses: List[AgentVote]
    verdict: VerdictResult


def _call_llm(system_prompt: str, user_prompt: str) -> dict:
    import urllib.request

    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "max_tokens": 200,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }).encode()

    req = urllib.request.Request(
        OLLAMA_BASE,
        data=payload,
        headers={
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    content = data["choices"][0]["message"]["content"]
    return _parse_json(content)


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    if text.startswith("["):
        end = text.rfind("]")
        if end > 0:
            text = text[1:end]
        bs = text.find("{")
        be = text.rfind("}")
        if bs >= 0 and be > bs:
            text = text[bs : be + 1]
    else:
        bs = text.find("{")
        be = text.rfind("}")
        if bs >= 0 and be > bs:
            text = text[bs : be + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    import re

    pos = re.search(r'"position"\s*:\s*"(FOR|AGAINST|ABSTAIN)"', text)
    conf = re.search(r'"confidence"\s*:\s*([0-9.]+)', text)
    arg = re.search(r'"argument"\s*:\s*"([^"]*)"', text)
    return {
        "position": pos.group(1) if pos else "ABSTAIN",
        "confidence": float(conf.group(1)) if conf else 0.5,
        "argument": arg.group(1) if arg else "",
    }


def _compute_verdict(responses: List[dict]) -> dict:
    votes = {"FOR": 0, "AGAINST": 0, "ABSTAIN": 0}
    total_conf = 0.0
    for r in responses:
        pos = r.get("position", "ABSTAIN").upper()
        if pos in votes:
            votes[pos] += 1
        total_conf += r.get("confidence", 0.5)

    n = len(responses)
    avg_conf = total_conf / n if n > 0 else 0.5
    majority = max(votes, key=votes.get)
    max_votes = votes[majority]

    if max_votes == 0:
        verdict = "ESCALATED"
        consensus = False
    elif majority == "FOR" and max_votes > n / 2:
        verdict = "APPROVED"
        consensus = True
    elif majority == "AGAINST" and max_votes > n / 2:
        verdict = "REJECTED"
        consensus = True
    elif majority == "ABSTAIN":
        verdict = "ESCALATED"
        consensus = False
    else:
        if votes.get("FOR", 0) == votes.get("AGAINST", 0):
            verdict = "ESCALATED"
            consensus = False
        else:
            verdict = majority
            consensus = True

    confidence = min(1.0, max(0.0, avg_conf * (max_votes / n)))
    hitl = confidence < 0.6 or not consensus

    return {
        "verdict": verdict,
        "confidence_score": round(confidence, 2),
        "consensus_met": consensus,
        "vote_breakdown": votes,
        "hitl_required": hitl,
    }


async def fast_pipeline(ctx: FunctionContext, data: FastPipelineInput) -> FastPipelineOutput:
    pod = Pod.from_env()
    t0 = time.time()

    user_prompt = f"Task: {data.stripped_task}"

    # Run 3 council agents in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(_call_llm, a["system"], user_prompt): a["id"]
            for a in COUNCIL[: data.council_size]
        }
        for future in as_completed(futures):
            aid = futures[future]
            results[aid] = future.result()

    # Build ordered responses
    responses = []
    for agent in COUNCIL[: data.council_size]:
        r = results.get(agent["id"], {"position": "ABSTAIN", "argument": "", "confidence": 0.5})
        responses.append({
            "agent_id": agent["id"],
            "position": r.get("position", "ABSTAIN"),
            "argument": r.get("argument", ""),
            "confidence": r.get("confidence", 0.5),
        })

    # Compute verdict
    verdict = _compute_verdict(responses)
    elapsed = time.time() - t0

    # Persist records for dashboard
    from lemma_sdk import RecordData

    verdict_id = str(uuid.uuid4())

    # Create debate_round record
    try:
        pod.records.create("debate_rounds", RecordData(
            session_id=data.session_id,
            round_number=0,
            round_type="pre_mortem",
            status="completed",
        ))
    except Exception:
        pass

    try:
        pod.records.create("verdicts", RecordData(
            session_id=data.session_id,
            verdict=verdict["verdict"],
            confidence_score=verdict["confidence_score"],
            council_vote_for=json.dumps([r["agent_id"] for r in responses if r["position"] == "FOR"]),
            council_vote_against=json.dumps([r["agent_id"] for r in responses if r["position"] == "AGAINST"]),
            council_vote_abstain=json.dumps([r["agent_id"] for r in responses if r["position"] == "ABSTAIN"]),
            conflict_report=json.dumps({
                "user_goal": data.user_goal,
                "council_finding": verdict["verdict"],
                "divergence_severity": "HIGH" if not verdict["consensus_met"] else "LOW",
                "explanation": f"Council {verdict['verdict']} with confidence {verdict['confidence_score']}",
            }),
            reasoning_trail=json.dumps([
                {"round": 1, "agent": r["agent_id"], "position": r["position"], "argument_summary": r["argument"][:100]}
                for r in responses
            ]),
            pre_mortem_summary=json.dumps([]),
            hitl_required=verdict["hitl_required"],
            hitl_reason="Low confidence or no consensus" if verdict["hitl_required"] else "",
        ))
    except Exception:
        pass

    try:
        pod.records.create("hitl_queue", RecordData(
            session_id=data.session_id,
            verdict_id=verdict_id,
            status="pending" if verdict["hitl_required"] else "resolved",
            escalation_tier=2 if verdict["hitl_required"] else 0,
            hitl_reason="Low confidence or no consensus" if verdict["hitl_required"] else "",
        ))
    except Exception:
        pass

    try:
        pod.records.update("debate_sessions", data.session_id, RecordData(
            status="done" if not verdict["hitl_required"] else "hitl",
        ))
    except Exception:
        pass

    return FastPipelineOutput(
        session_id=data.session_id,
        elapsed=round(elapsed, 2),
        council_responses=[AgentVote(**r) for r in responses],
        verdict=VerdictResult(**verdict),
    )
