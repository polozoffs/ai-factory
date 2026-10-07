---
description: Show the AI-factory usage report for a run's active plan checkpoint.
agent: factory
---

Render the usage report for this run:

$ARGUMENTS

The optional argument is the slug or the plan path. If none is given, look in
`.opencode/plans/active/` and ask the user which run to report on.

Run, read-only:

```bash
python3 .opencode/scripts/usage_recorder.py report --plan .opencode/plans/active/<slug>.md
```

Return the report output unchanged, then a one-line per-stage summary and the
feature total. Report unknown token counts and costs as `unknown`, never as `0`;
`telemetry_status: unavailable` means the runtime did not expose usage, not that
usage was zero. `estimated_usd` is an approximate estimate from the recorded
pricing snapshot (`provider`, `model`, `pricing_version`,
`pricing_effective_at`, `pricing_source`) and is not billing data.

Do not record, edit the checkpoint, run a stage, or make provider calls.
