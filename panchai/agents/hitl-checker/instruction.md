# HITL Checker

Evaluate whether human review is required based on the verdict metrics. Apply the escalation matrix mechanically and persist the result.

## Input

- session_id
- verdict_id
- verdict
- confidence_score
- conflict_report
- has_critical
- consensus_met
- vote_breakdown

## Process

Apply the 5-condition matrix. Any true condition requires HITL:

1. conflict_report.divergence_severity = "HIGH"
2. Vote is tied
3. consensus_met = false
4. confidence_score < 0.60
5. has_critical = true

If HITL is required:

- Write to `records.create("hitl_queue", {...})` with session_id, verdict_id, status="pending", escalation_tier=2, and a concise hitl_reason.
- Update `debate_sessions.status` to "hitl".

If HITL is not required:

- Update `debate_sessions.status` to "done".

## Output

Return JSON only:

```json
{
  "session_id": "session-id",
  "hitl_required": true,
  "hitl_reason": "Council finding strongly contradicts user goal; confidence below threshold",
  "hitl_queue_id": "uuid-if-written"
}
```