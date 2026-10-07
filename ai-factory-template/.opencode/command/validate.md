---
description: Run the validator subagent against the completed feature and current working diff, without implementing anything.
agent: factory
---

Run only the validator stage of the AI factory against the completed feature and
current git working diff. If a spec file path is given below, validate the
feature against that spec, technical plan, embedded design, and QA test plan;
otherwise infer the most relevant spec from `.opencode/specs/active/`, or
validate purely against the validator's own review gates (in
`.opencode/agent/validator.md`) and `docs/development/CODING_STANDARDS.md` if
no spec applies.

$ARGUMENTS

Run the validator once and return its independent feature-level verdict. Do not
run release-manager.

Optional trailing context may supply `session_id` and `iteration`; otherwise
read them from the plan §8 checkpoint and pass them to the validator so the
verdict is tied to the current run. Validation is allowed while implementation
approval is still pending — do not re-run the planner for that reason.

On FAIL, the orchestrator forms a `CORRECTION` envelope from the verdict's
must-fix items (see `.opencode/agent/factory.md`) and continues in the same
session at the next `iteration`; it does not return to planning.

On PASS, the run moves to `AWAITING_FINAL_SIGNOFF` only. Record the PASS with
its `session_id` and `iteration` as `pass_evidence` and stop for an explicit
feature-done statement. PASS never authorises release-manager, docs updates,
commits, or archiving by itself, and a later user-requested fix invalidates the
PASS evidence and requires revalidation in the same session.

Return the validator's `VERDICT:` block verbatim.

Record the validator invocation into plan §8 `usage_reporting` and append the
`USAGE` block after the verdict (see `.opencode/agent/factory.md`). Usage data
never influences the verdict.
