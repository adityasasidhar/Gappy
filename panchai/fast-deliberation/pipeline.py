import asyncio, json, os, time
from typing import List, Dict

API_KEY = os.environ.get("OLLAMA_API_KEY") or "cdc48c82f5ba485db083e41d0d04eceb.ZjWzBuHQMqi8Fg3F9P5S2M8E"
BASE_URL = "https://ollama.com/v1/chat/completions"
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

TASK_EXAMPLES = {
    "yesmadam": {
        "task": "Customer #4821, Gold tier, 47 days past 30-day return policy, claims product defect, 2 prior refunds in 6 months.",
        "goal": "Approve the refund",
        "context": "YesMadam customer service - high-value client"
    },
    "binocs": {
        "task": "Inventory 340 units, demand forecast 280 units, vendor reliability 62%, lead time 45 days, cash position tight.",
        "goal": "Pause the vendor order",
        "context": "Binocs supply chain - cost optimization"
    }
}

async def call_llm(session, system_prompt: str, user_prompt: str) -> Dict:
    import aiohttp
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "max_tokens": 200,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    async with session.post(BASE_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
        data = await resp.json()
        content = data["choices"][0]["message"]["content"]
        return parse_json(content)


def parse_json(text: str) -> Dict:
    text = text.strip()
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    if text.startswith("["):
        arr_end = text.rfind("]")
        if arr_end > 0:
            text = text[1:arr_end]
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start >= 0 and brace_end > brace_start:
            text = text[brace_start:brace_end+1]
    else:
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start >= 0 and brace_end > brace_start:
            text = text[brace_start:brace_end+1]

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


async def run_council(session, task: str, context: str = "") -> List[Dict]:
    user_prompt = f"Task: {task}"
    if context:
        user_prompt = f"Context: {context}\n\nTask: {task}"

    tasks = [call_llm(session, a["system"], user_prompt) for a in COUNCIL]
    results = await asyncio.gather(*tasks)

    outputs = []
    for i, agent in enumerate(COUNCIL):
        outputs.append({
            "agent_id": agent["id"],
            "position": results[i].get("position", "ABSTAIN"),
            "argument": results[i].get("argument", ""),
            "confidence": results[i].get("confidence", 0.5),
        })
    return outputs


def compute_verdict(responses: List[Dict], goal: str = "") -> Dict:
    votes = {"FOR": 0, "AGAINST": 0, "ABSTAIN": 0}
    total_conf = 0
    for r in responses:
        pos = r["position"].upper()
        if pos in votes:
            votes[pos] += 1
        total_conf += r["confidence"]

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


async def run_pipeline(task: str, goal: str = "", context: str = "", council_size: int = 3) -> Dict:
    import aiohttp
    t0 = time.time()

    async with aiohttp.ClientSession() as session:
        responses = await run_council(session, task, context)

    verdict = compute_verdict(responses, goal)
    elapsed = time.time() - t0

    return {
        "elapsed": round(elapsed, 2),
        "council_responses": responses,
        "verdict": verdict,
    }


if __name__ == "__main__":
    example = TASK_EXAMPLES["yesmadam"]
    result = asyncio.run(run_pipeline(
        task=example["task"],
        goal=example["goal"],
        context=example["context"],
    ))
    print(json.dumps(result, indent=2))
