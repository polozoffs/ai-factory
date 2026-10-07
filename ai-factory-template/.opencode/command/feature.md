---
description: Run feature-planner, approval, implementer, validator, final approval, and release-manager.
agent: factory
---

Run the full AI factory pipeline for this request:

$ARGUMENTS

Follow `.opencode/rules/workflow.md`: feature-planner produces the consolidated
planning package; after planning approval, implementer handles ordered chunks;
validator performs one feature-level validation; release-manager acts only
after final approval. Pause at the planning and final approval gates.

Optional trailing context may supply `session_id`, `iteration`, or a checkpoint
path; otherwise resume them from the plan §8 checkpoint. Never start a new
`session_id` for a slug whose state is not `DONE` or `ESCALATED`. Pending
implementation approval is not a planning reset — validation may run while it
is pending.

Closure gate: a validator PASS moves the run to `AWAITING_FINAL_SIGNOFF` only
and stops for an explicit feature-done statement. Any user-requested fix at that
point invalidates the PASS evidence and the final approval, re-enters the same
session as a `CORRECTION` with `source: user-fix`, and requires a new PASS.
Invoke release-manager only with a `RELEASE` handoff whose PASS evidence and
granted final approval share the same `session_id` and final `iteration`.

Record each stage invocation into plan §8 `usage_reporting` and include the
`USAGE` block in every handoff (see `.opencode/agent/factory.md`). At each
approval gate, show the report from
`python3 .opencode/scripts/usage_recorder.py report --plan
.opencode/plans/active/<slug>.md`. Usage data is informational and never gates
the pipeline.
