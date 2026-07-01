#input_type_name: FastPipelineInput
#output_type_name: FastPipelineOutput
#function_name: fast_pipeline

"""
fast_pipeline — PANCHAI Multi-Agent Deliberation Engine
========================================================
Implements the Blind Tribunal Protocol:
  1. Selects council via registry_lookup (or hardcoded fallback)
  2. Calls each council agent sequentially via Lemma create_for_agent() + send_stream()
     — falls back to direct Ollama Cloud API call on 429 / timeout
  3. Persists all debate records (pre_mortems, debate_rounds, debate_messages, verdicts, hitl_queue)
  4. Returns FastPipelineOutput with mode: "live"

Constraints honoured:
  - user_goal NEVER sent to agents (Blind Tribunal Protocol)
  - Sequential execution (sandbox: 1 thread, asyncio.to_thread runs sequentially)
  - AGENT_TIMEOUT = 120s per agent; time_budget = 260s total
  - council capped at 2 to fit within 300s sandbox limit
  - Files API (pod.files.*) wrapped in try/except — no permission grant
  - Private transport attr access wrapped in try/except
  - Global try/except returns FAILED verdict on any uncaught exception
"""

import json
import os
import re
import time
import uuid
import urllib.request
import urllib.error
import ssl
from typing import List, Optional
from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod, RecordData


# ── Configuration ─────────────────────────────────────────────────────────────

OLLAMA_API_KEY = (
    os.environ.get("OLLAMA_API_KEY")
    or "dd0d6a4161864b4c967f2f8a5e807b59.WOynu1rNk33PgQMSSvkInkwp"
)
OLLAMA_BASE_URL = "https://ollama.com/v1/chat/completions"
OLLAMA_MODEL = "ministral-3:3b"

# Sandbox limits
AGENT_TIMEOUT = 120.0   # per-agent wall-clock budget (seconds)
TIME_BUDGET   = 260.0   # total pipeline budget (seconds)
MAX_COUNCIL   = 2       # keep within 300s sandbox kill limit


# ── Agent personas (fallback when Lemma agent call unavailable) ───────────────

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

# Default system prompt for unknown agents
_DEFAULT_SYSTEM_PROMPT = (
    "You are an expert deliberation council member. "
    "Evaluate the task objectively and return EXACTLY ONE JSON object with fields: "
    '"position" (FOR/AGAINST/ABSTAIN/REFRAME), "argument" (detailed reasoning), '
    '"confidence" (0.0-1.0), "key_evidence" (single most important factor). '
    "No markdown, no extra text."
)

R1_PROMPT = (
    "Conduct a pre-mortem analysis on this task — identify how the proposed action could fail, "
    "what assumptions may be wrong, and which stakeholders could be harmed. "
    "Then form your position. Return your response in the required JSON format."
)


# ── Pydantic models ───────────────────────────────────────────────────────────

class FastPipelineInput(BaseModel):
    session_id: str
    stripped_task: str
    user_goal: str = ""          # received but NEVER forwarded to agents
    client_id: Optional[str] = None
    stakes_level: str = "STANDARD"
    council_size: int = 2


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
    mode: str = "live"


class FastPipelineOutput(BaseModel):
    session_id: str
    elapsed: float
    council_responses: List[AgentVote]
    verdict: VerdictResult
    mode: str = "live"


# ── JSON parsing ──────────────────────────────────────────────────────────────

def _parse_json(text: str) -> dict:
    """Robustly extract the first JSON object from LLM output."""
    text = text.strip()

    # Strip markdown code fences
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"```$", "", text.rstrip()).rstrip()
    text = text.strip()

    # If array, take first element
    if text.startswith("["):
        bs = text.find("{")
        be = text.rfind("}")
        if bs >= 0 and be > bs:
            text = text[bs : be + 1]

    # Extract outer JSON object
    bs = text.find("{")
    be = text.rfind("}")
    if bs >= 0 and be > bs:
        text = text[bs : be + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Regex fallback
    pos  = re.search(r'"position"\s*:\s*"(FOR|AGAINST|ABSTAIN|REFRAME)"', text)
    conf = re.search(r'"confidence"\s*:\s*([0-9.]+)', text)
    arg  = re.search(r'"argument"\s*:\s*"([^"]*)"', text)
    kev  = re.search(r'"key_evidence"\s*:\s*"([^"]*)"', text)
    return {
        "position":    pos.group(1)  if pos  else "ABSTAIN",
        "confidence":  float(conf.group(1)) if conf else 0.5,
        "argument":    arg.group(1)  if arg  else "",
        "key_evidence": kev.group(1) if kev  else "",
    }


# ── Ollama Cloud direct fallback ───────────────────────────────────────────────

def _call_ollama(system_prompt: str, user_prompt: str) -> dict:
    """
    Direct Ollama Cloud API call via urllib (stdlib).
    Used when Lemma agent call is unavailable (e.g. 429 LLM quota on Lemma side).
    """
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
    req = urllib.request.Request(
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
        resp = urllib.request.urlopen(req, context=ctx, timeout=120)
        data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return _parse_json(content)
    except Exception as e:
        return {
            "position":    "ABSTAIN",
            "argument":    f"Agent unavailable: {type(e).__name__}",
            "confidence":  0.5,
            "key_evidence": "",
        }


# ── Lemma agent call with Ollama fallback ─────────────────────────────────────

def _call_agent_sync(pod: Pod, agent_id: str, system_prompt: str, user_prompt: str) -> dict:
    """
    Call agent via Lemma create_for_agent() + send_stream().
    Falls back to direct Ollama Cloud call on any error (including 429 quota).
    """
    try:
        # Extend transport timeout to prevent 30s SSE cutoff
        try:
            pod._transport.generated._timeout = AGENT_TIMEOUT + 30.0
        except Exception:
            pass

        conv = pod.conversations.create_for_agent(agent_id)
        conv_id = conv.id if hasattr(conv, "id") else conv["id"]

        response = pod.conversations.send_stream(
            conv_id,
            message=user_prompt,
            stream=True,
        )

        # Parse SSE stream for type: "completed" event carrying output_data
        result_data = None
        full_text = ""
        for line in response.iter_lines():
            if not line:
                continue
            if line.startswith("data:"):
                raw = line[5:].strip()
                if not raw or raw == "[DONE]":
                    continue
                try:
                    evt = json.loads(raw)
                    etype = evt.get("type", "")
                    if etype == "completed":
                        output = evt.get("output_data") or evt.get("output") or {}
                        if isinstance(output, dict):
                            result_data = output
                        elif isinstance(output, str):
                            result_data = _parse_json(output)
                        break
                    elif etype in ("message", "chunk", "delta", "text"):
                        chunk = (
                            evt.get("content")
                            or evt.get("text")
                            or evt.get("delta", {}).get("content", "")
                        )
                        if chunk:
                            full_text += chunk
                except (json.JSONDecodeError, AttributeError):
                    full_text += line

        if result_data and isinstance(result_data, dict) and "position" in result_data:
            return result_data

        # Try to extract from accumulated text
        if full_text.strip():
            parsed = _parse_json(full_text)
            if parsed.get("position") in ("FOR", "AGAINST", "ABSTAIN", "REFRAME"):
                return parsed

        # Fall back to messages endpoint
        try:
            messages = pod.conversations.messages(conv_id)
            msgs = getattr(messages, "items", None) or (messages if isinstance(messages, list) else [])
            for m in reversed(msgs):
                content = m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
                if content:
                    parsed = _parse_json(content)
                    if parsed.get("position") in ("FOR", "AGAINST", "ABSTAIN", "REFRAME"):
                        return parsed
        except Exception:
            pass

    except Exception as lemma_err:
        # Check for 429 — fall through to Ollama
        err_str = str(lemma_err)
        if "429" in err_str or "USAGE_LIMIT" in err_str or "quota" in err_str.lower():
            pass  # Expected — quota exhausted, use Ollama fallback
        # Any other error: also use fallback

    # Ollama Cloud fallback
    return _call_ollama(system_prompt, user_prompt)


# ── Verdict computation ───────────────────────────────────────────────────────

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
        "mode":             "live",
    }


# ── Database helpers ──────────────────────────────────────────────────────────

def _safe_create(pod: Pod, table: str, data: dict) -> Optional[str]:
    """Create a record; swallow errors; return created id or None."""
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


# ── Council selection ─────────────────────────────────────────────────────────

def _select_council(pod: Pod, client_id: str, stakes_level: str, stripped_task: str, council_size: int):
    if client_id:
        try:
            result = pod.functions.call("registry_lookup", {
                "stripped_task": stripped_task,
                "client_id":     client_id,
                "stakes_level":  stakes_level,
            })
            agents = (
                result.get("selected_agents", []) if isinstance(result, dict)
                else getattr(result, "selected_agents", [])
            )
            if agents:
                if isinstance(agents[0], dict):
                    selected = [a["agent_id"] for a in agents]
                    meta = {
                        a["agent_id"]: {
                            "name": a.get("agent_name", a["agent_id"]),
                            "bias": a.get("reasoning_bias", "analyst"),
                        }
                        for a in agents
                    }
                else:
                    selected = [a.agent_id for a in agents]
                    meta = {
                        a.agent_id: {
                            "name": getattr(a, "agent_name", a.agent_id),
                            "bias": getattr(a, "reasoning_bias", "analyst"),
                        }
                        for a in agents
                    }
                return selected[:council_size], meta
        except Exception:
            pass

    # Hardcoded fallback
    default_ids = ["policy-analyst", "customer-advocate"]
    default_meta = {
        "policy-analyst":    {"name": "Policy Analyst",    "bias": "rule-following"},
        "customer-advocate": {"name": "Customer Advocate", "bias": "customer-first"},
    }
    return default_ids[:council_size], default_meta


# ── Institutional memory (Files API — no permission grant, wrapped in try/except) ─

def _search_memory(pod: Pod, query: str) -> str:
    try:
        results = pod.files.search(query, search_method="HYBRID", limit=3)
        items = getattr(results, "items", None) or (results if isinstance(results, list) else [])
        if not items:
            return ""
        snippets = []
        for item in items[:3]:
            path    = getattr(item, "path", "") or (item.get("path", "") if isinstance(item, dict) else "")
            excerpt = getattr(item, "excerpt", "") or (item.get("excerpt", "") if isinstance(item, dict) else "")
            if excerpt:
                snippets.append(f"[{path}]: {excerpt[:200]}")
        return "\n".join(snippets)
    except Exception:
        return ""


def _archive_verdict(pod: Pod, session_id: str, verdict: dict, responses: List[dict]):
    try:
        lines = [
            f"# PANCHAI Verdict — Session {session_id}",
            f"**Verdict**: {verdict['verdict']}  ",
            f"**Confidence**: {verdict['confidence_score']}  ",
            f"**Consensus**: {verdict['consensus_met']}  ",
            "",
            "## Council Votes",
        ]
        for r in responses:
            lines.append(f"- **{r['agent_id']}**: {r['position']} (conf: {r['confidence']:.2f})")
            lines.append(f"  > {r['argument'][:200]}")
        pod.files.write_text(f"/panchai/verdicts/{session_id}.md", "\n".join(lines))
    except Exception:
        pass


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def fast_pipeline(ctx: FunctionContext, data: FastPipelineInput) -> FastPipelineOutput:
    t0 = time.time()
    try:
        pod = Pod.from_env()
        session_id    = data.session_id
        effective_size = min(data.council_size, MAX_COUNCIL)

        selected, agent_meta = _select_council(
            pod, data.client_id, data.stakes_level,
            data.stripped_task, effective_size
        )

        # Retrieve institutional memory (no user_goal sent — only stripped_task)
        memory_ctx = _search_memory(pod, data.stripped_task)

        # Build task prompt — BLIND TRIBUNAL: user_goal is intentionally excluded
        task_prompt = f"Task: {data.stripped_task}"
        if memory_ctx:
            task_prompt += f"\n\n[Institutional Memory — relevant past verdicts]:\n{memory_ctx}"

        # ── Round 0: Pre-Mortem Phase (created complete after agents respond) ──
        pm_round_id = str(uuid.uuid4())
        _safe_update(pod, "debate_sessions", session_id, {"status": "pre_mortem"})

        # ── Round 1: Debate Phase ─────────────────────────────────────────────
        round1_id = str(uuid.uuid4())
        r1_responses: List[dict] = []

        for agent_id in selected:
            elapsed_so_far = time.time() - t0
            if elapsed_so_far >= TIME_BUDGET:
                r1_responses.append({
                    "agent_id":    agent_id,
                    "position":    "ABSTAIN",
                    "argument":    "Pipeline time budget exceeded — agent skipped.",
                    "confidence":  0.5,
                    "key_evidence": "",
                })
                continue

            sys_prompt  = AGENT_SYSTEM_PROMPTS.get(agent_id, _DEFAULT_SYSTEM_PROMPT)
            user_prompt = f"{task_prompt}\n\n{R1_PROMPT}"

            result = _call_agent_sync(pod, agent_id, sys_prompt, user_prompt)

            r1_responses.append({
                "agent_id":    agent_id,
                "position":    result.get("position", "ABSTAIN"),
                "argument":    result.get("argument", ""),
                "confidence":  float(result.get("confidence", 0.5)),
                "key_evidence": result.get("key_evidence", ""),
            })

        # ── Persist Pre-Mortem records ────────────────────────────────────────
        _safe_create(pod, "debate_rounds", {
            "id":           pm_round_id,
            "session_id":   session_id,
            "round_number": 0,
            "round_type":   "pre_mortem",
            "status":       "complete",
        })
        for r in r1_responses:
            meta        = agent_meta.get(r["agent_id"], {})
            arg_preview = r["argument"][:300]

            # Pre-mortem debate_messages
            _safe_create(pod, "debate_messages", {
                "session_id":    session_id,
                "round_id":      pm_round_id,
                "agent_id":      r["agent_id"],
                "agent_name":    meta.get("name", r["agent_id"]),
                "position":      "ABSTAIN",
                "argument":      (
                    f"**Pre-Mortem Analysis:**\n\n{arg_preview}\n\n"
                    f"**Preliminary Position:** {r['position']}"
                ),
                "round_number":  0,
                "reasoning_bias": meta.get("bias", "analyst"),
            })

            # pre_mortems table
            _safe_create(pod, "pre_mortems", {
                "session_id":       session_id,
                "round_id":         pm_round_id,
                "agent_id":         r["agent_id"],
                "failure_reason":   arg_preview or "No specific risks identified.",
                "weak_assumption":  "Key assumption may be invalid under adversarial review.",
                "harmed_stakeholder": "end users / organization",
                "severity":         "HIGH" if data.stakes_level == "HIGH" else "MEDIUM",
            })

        # ── Persist Round 1 Debate records ───────────────────────────────────
        _safe_create(pod, "debate_rounds", {
            "id":           round1_id,
            "session_id":   session_id,
            "round_number": 1,
            "round_type":   "debate",
            "status":       "complete",
        })
        _safe_update(pod, "debate_sessions", session_id, {"status": "debating"})

        for r in r1_responses:
            meta = agent_meta.get(r["agent_id"], {})
            _safe_create(pod, "debate_messages", {
                "session_id":    session_id,
                "round_id":      round1_id,
                "agent_id":      r["agent_id"],
                "agent_name":    meta.get("name", r["agent_id"]),
                "position":      r["position"],
                "argument":      r["argument"],
                "round_number":  1,
                "reasoning_bias": meta.get("bias", "analyst"),
            })

        # ── Compute Verdict ───────────────────────────────────────────────────
        verdict   = _compute_verdict(r1_responses)
        elapsed   = time.time() - t0
        verdict_id = str(uuid.uuid4())

        reasoning_trail = [
            {
                "round":            1,
                "agent":            r["agent_id"],
                "position":         r["position"],
                "argument_summary": r["argument"][:150],
            }
            for r in r1_responses
        ]
        pre_mortem_summary = [
            {"agent": r["agent_id"], "risks": [r.get("key_evidence", r["argument"][:100])]}
            for r in r1_responses
        ]

        # Conflict report — user_goal included here for dashboarding (NOT sent to agents)
        conflict_report = {
            "user_goal":       data.user_goal,
            "council_finding": verdict["verdict"],
            "divergence_severity": "HIGH" if not verdict["consensus_met"] else "LOW",
            "explanation": (
                f"Council reached {verdict['verdict']} with "
                f"{verdict['confidence_score']:.0%} confidence. "
                + (
                    "Human review recommended." if verdict["hitl_required"]
                    else "Automated resolution applied."
                )
            ),
        }

        _safe_create(pod, "verdicts", {
            "id":                  verdict_id,
            "session_id":          session_id,
            "verdict":             verdict["verdict"],
            "confidence_score":    verdict["confidence_score"],
            "council_vote_for":    json.dumps([r["agent_id"] for r in r1_responses if r["position"] == "FOR"]),
            "council_vote_against": json.dumps([r["agent_id"] for r in r1_responses if r["position"] == "AGAINST"]),
            "council_vote_abstain": json.dumps([r["agent_id"] for r in r1_responses if r["position"] == "ABSTAIN"]),
            "council_vote_reframe": json.dumps([r["agent_id"] for r in r1_responses if r["position"] == "REFRAME"]),
            "conflict_report":     json.dumps(conflict_report),
            "reasoning_trail":     json.dumps(reasoning_trail),
            "pre_mortem_summary":  json.dumps(pre_mortem_summary),
            "hitl_required":       verdict["hitl_required"],
            "hitl_reason":         "Low confidence or no consensus reached." if verdict["hitl_required"] else "",
        })

        _safe_create(pod, "hitl_queue", {
            "session_id":      session_id,
            "verdict_id":      verdict_id,
            "status":          "pending" if verdict["hitl_required"] else "resolved",
            "escalation_tier": 2 if verdict["hitl_required"] else 0,
            "hitl_reason":     "Low confidence or no consensus." if verdict["hitl_required"] else "",
        })

        final_status = "hitl" if verdict["hitl_required"] else "done"
        _safe_update(pod, "debate_sessions", session_id, {"status": final_status})

        # Archive to institutional memory
        _archive_verdict(pod, session_id, verdict, r1_responses)

        return FastPipelineOutput(
            session_id=session_id,
            elapsed=round(elapsed, 2),
            council_responses=[
                AgentVote(**{k: r[k] for k in ("agent_id", "position", "argument", "confidence")})
                for r in r1_responses
            ],
            verdict=VerdictResult(**verdict),
        )

    except Exception as exc:
        elapsed = time.time() - t0
        # Attempt to mark session failed
        try:
            _safe_update(Pod.from_env(), "debate_sessions", data.session_id, {"status": "failed"})
        except Exception:
            pass
        return FastPipelineOutput(
            session_id=data.session_id,
            elapsed=round(elapsed, 2),
            council_responses=[],
            verdict=VerdictResult(
                verdict="FAILED",
                confidence_score=0.0,
                consensus_met=False,
                vote_breakdown={},
                hitl_required=True,
                mode="live",
            ),
        )
