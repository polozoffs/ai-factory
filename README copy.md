# AI Factory Template

A portable, etalon copy of the AI-factory setup: an orchestrator agent plus
four contracted subagents (planner → implementer → validator → release
manager), slash commands, artifact templates, and the living-docs skeleton the
agents read from. Drop it into any repository, run one initialization pass,
and the full gated feature pipeline works there the same way.

```
feature-planner → approval → implementer → validator → final approval → release-manager
```

## What you get

```
ai-factory-template/
├── AGENTS.md                  # project facts injected into every agent (FILL IN)
├── INIT.md                    # initialization runbook — follow it after copying
├── docs/                      # living-docs skeleton the agents read (FILL IN)
│   ├── README.md
│   ├── development/
│   │   ├── DIGEST.md          # ← most important file; agents read it first
│   │   ├── PROJECT_CONTEXT.md
│   │   ├── CODING_STANDARDS.md
│   │   └── API_REFERENCE.md
│   ├── Features/              # one doc per feature domain (+ TEMPLATE.md)
│   ├── deployment/ operations/ archive/
└── .opencode/
    ├── opencode.jsonc         # entry config: default agent, instructions, references
    ├── agent/                 # 5 agent contracts + models.json
    │   ├── factory.md         # primary orchestrator (never edits code)
    │   ├── feature-planner.md # brief + spec + plan + QA plan; writes only .opencode/*
    │   ├── implementer.md     # implements ONE approved chunk per run
    │   ├── validator.md       # read-only; sole PASS/FAIL authority
    │   ├── release-manager.md # docs + commit + archive, only after final approval
    │   └── models.json        # optional model allowlist
    ├── command/               # /plan /implement /validate /feature /usage
    ├── rules/                 # workflow.md (contracts, token economy, gates)
    ├── specs/ plans/ qa/      # TEMPLATE.md + active/ + archive/ artifact flow
    ├── scripts/               # usage_recorder.py + tests, page-QA assets, shareable utils, legacy
    └── skills/                # drop project-specific skills here
```

## Usage (once initialized)

In the target repo with opencode:

- `/feature <request>` — full pipeline with both approval gates
- `/plan <request>` — planning package only (brief, spec, plan, QA plan)
- `/implement <spec-file> <chunk-id>` — one chunk only
- `/validate [spec-file]` — independent verdict only
- `/usage [slug|plan-path]` — read-only usage report for a run

The pipeline pauses twice: **planning approval** before any code is written,
and **final approval** before docs/commit/archive.

## Usage reporting

Every stage invocation is recorded exactly once as a normalized, append-only
`usage_record` in §8 `usage_reporting` of the run's active plan, keyed by
`session_id` + `iteration` + `invocation_id`. Records carry stage identity,
timestamps, token counts, an approximate `estimated_usd`, provider/model, and a
versioned pricing snapshot. The contract lives in `.opencode/rules/workflow.md`
("Usage reporting contract" and "Usage checkpoint schema"); the ledger shape is
pre-seeded in `.opencode/plans/TEMPLATE.md`.

- `python3 .opencode/scripts/usage_recorder.py record --plan <plan> --input <json>`
  appends/normalizes a record and recomputes totals.
- `python3 .opencode/scripts/usage_recorder.py report --plan <plan>` (or
  `/usage`) renders the read-only operator report.
- Unknown is never zero: when the runtime exposes no telemetry the record is
  kept with `telemetry_status: unavailable`,
  `unavailable_reason: runtime_did_not_expose_usage`, and null numbers that are
  excluded from sums and counted as unknown.
- Reporting-only: usage totals, estimates, and unavailable telemetry never gate
  a transition, a verdict, or a release. Recording is best-effort.
- No prompts, responses, raw provider payloads, or secrets are ever persisted.
- Recorder tests: `python3 .opencode/scripts/test_usage_recorder.py`.

## Applying to a new project

1. Copy everything in this folder into the new repo root (`.opencode/`,
   `AGENTS.md`, `docs/`, excluding this README and `INIT.md` if you prefer —
   but keep `INIT.md` until init is done).
2. Open `INIT.md` in the new repo and run the initialization pass — either
   yourself or by asking the agent: *"Initialize the AI factory for this repo
   per INIT.md."*
3. Commit the result.

See `INIT.md` for the exact checklist.
