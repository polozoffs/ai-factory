---
description: Implement an already-approved spec, one work chunk at a time.
agent: factory
---

Run only the implementer stage against this spec file and the given work chunk
id from its technical plan. Do not run validator or release-manager:

$ARGUMENTS

The first argument is the spec file path; the second argument is the required
chunk id (e.g. `<slug>-chunk-2`). If no spec file path is given, look in
`.opencode/specs/active/` and ask the user which one to implement. If no chunk
id is given, error and require the user to specify a chunk — do not implement
the whole spec or any default section.

Optional trailing context may supply `session_id`, `iteration`, a checkpoint
path, or a `CORRECTION` envelope (see `.opencode/agent/factory.md`). When
present, resume that session instead of starting a new one and pass the context
through to the implementer. A `CORRECTION` envelope satisfies the chunk-id
requirement, and its `items` define the entire scope. When absent, resume the
run recorded in `.opencode/plans/active/<slug>.md` §8 if its state is not `DONE`
or `ESCALATED`.

Pending implementation approval is never a reason to re-run the planner.

Record the implementer invocation into plan §8 `usage_reporting` and end the
handoff with the `USAGE` block (see `.opencode/agent/factory.md`).
