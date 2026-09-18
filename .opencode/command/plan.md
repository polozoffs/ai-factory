---
description: Run the consolidated feature-planner and produce the planning package — no implementation.
agent: factory
---

Run only the `feature-planner` stage against this request or spec file and stop
after producing the brief, spec, technical plan, and QA plan. Do not implement
or validate:

$ARGUMENTS

If no path is given, accept the raw request. Return artifact paths, ordered
chunk ids, criterion mapping, checkpoint state, and assumptions as described in
`.opencode/agent/feature-planner.md`.

Record the planner invocation into plan §8 `usage_reporting` and end the handoff
with the `USAGE` block (see `.opencode/agent/factory.md`).
