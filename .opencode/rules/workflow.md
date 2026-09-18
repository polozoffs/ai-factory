
## Contracts

| Stage | Input | Output | Code |
|---|---|---|---|
| feature-planner | Request or brief/spec path | Brief, spec, plan, QA plan, optional checkpoint | No |
| implementer | Approved spec + chunk | Changes + handoff evidence | Yes |
| validator | Completed feature + spec/plan | Verdict + evidence | No |
| release-manager | Final PASS + approval | Docs, commit, archived artifacts | No |

## Token economy

Subagent sessions start cold; every read costs full tokens. All agents must:

- Never re-read `AGENTS.md` — it is injected via `instructions` in
  `.opencode/opencode.jsonc`.
- Treat `docs/development/DIGEST.md` as the default context; read full
  `PROJECT_CONTEXT.md` / `CODING_STANDARDS.md` only by `##` section when the
  DIGEST lacks needed detail. Read only `docs/Features/` files for domains the
  feature touches.
- Plan chunks declare a `Context:` line; implementers read only what it lists.
- Validators review `git diff` hunks first and open full files only when hunks
  are insufficient or the diff adds public routes, auth, or migrations.
- Handoffs are compact structured lists (implementer ≤30 lines); on validator
  FAIL the orchestrator passes only the verdict block back to the implementer,
  not the whole session.
- Edit `AGENTS.md`, this file, and agent frontmatter in batches — the shared
  stable prefix is the main prompt-cache surface.

## Contracts detail

`feature-planner` replaces intake-analyst → spec-writer → tech-planner. Before
request artifacts, read project context per the token-economy rules and
relevant feature guidance. Write only:

- `.opencode/specs/briefs/<slug>.md`
- `.opencode/specs/active/<slug>.md`
- `.opencode/plans/active/<slug>.md`
- `.opencode/qa/active/<slug>-test-plan.md`
- optional checkpoint in `.opencode/plans/active/`

Record ordered chunks, per-chunk `Context:` lines, acceptance-to-chunk
mapping, assumptions, risks, and rollback notes. Resume after clarification or
requested planning changes without discarding completed work. Never implement
or create QA fixtures, metrics evidence, or runtime data.

## Lifecycle states

The factory run is an explicit state machine. State is recorded, never inferred
from prose.

| State | Meaning |
|---|---|
| `PLANNING` | `feature-planner` is producing or revising artifacts |
| `AWAITING_PLANNING_APPROVAL` | artifacts complete; hard stop for explicit planning approval |
| `IMPLEMENTING` | `implementer` is executing an ordered chunk or a correction |
| `AWAITING_IMPLEMENTATION_APPROVAL` | chunks reported complete; paused for user acknowledgement |
| `VALIDATING` | `validator` is running against the current session/iteration |
| `FIX_REQUESTED` | a validator FAIL or a user-requested fix is queued as correction input |
| `AWAITING_FINAL_SIGNOFF` | validator PASS recorded; hard stop for explicit feature-done approval |
| `ESCALATED` | retry limit reached; awaiting user direction |
| `DONE` | `release-manager` completed docs, commit, and archive |

`AWAITING_IMPLEMENTATION_APPROVAL` is **not** a replan state. Once
implementation has begun the run is validation-eligible, and pending
implementation approval never returns the run to `PLANNING`.

## Session and checkpoint identity

A run has a stable `session_id` for its whole lifetime and an `iteration`
counter that increments on every correction loop. Both are carried in every
handoff and recorded in every verdict.

Checkpoint fields (recorded in `.opencode/plans/active/<slug>.md` §8):

`slug`, `spec_path`, `session_id`, `iteration`, `state`, `completed_chunks`,
`planning_approval`, `implementation_approval`, `final_approval`,
`last_handoff_source`, `retry_count`, `retry_limit`, `safe_rollback_point`,
`scope_boundary`.

`scope_boundary` declares the in-scope file set for the feature and the
out-of-scope areas that belong to other work. Unrelated working-tree changes
outside `scope_boundary` are never attributed to the feature: validation judges
only in-scope files, and no agent reverts or deletes out-of-scope user work.

Approval fields are explicit tri-state: `pending`, `granted`, or `n/a`. Nothing
grants an approval except a recorded explicit user statement.

## Usage reporting contract

Every applicable stage invocation produces exactly one normalized usage record.
Records are append-only, allow-listed metadata plus numeric usage; prompts,
responses, raw provider payloads, credentials, and secrets are never persisted.

`usage_record` fields (`schema_version: 1`):

| Field | Type | Notes |
|---|---|---|
| `invocation_id` | string | unique per invocation; idempotency key |
| `stage` | enum | `feature-planner`, `implementer`, `validator`, `release-manager` |
| `session_id` | string | stable for the whole run |
| `iteration` | integer ≥ 0 | correction counter at invocation time |
| `started_at` / `completed_at` | ISO-8601 UTC or null | |
| `input_tokens` / `output_tokens` / `total_tokens` | integer ≥ 0 or null | unknown stays null |
| `estimated_usd` | number ≥ 0 or null | approximate; never billing data |
| `currency` | string or null | ISO-4217, normally `USD` |
| `telemetry_status` | enum | `exact`, `partial`, `unavailable`, `conflict` |
| `unavailable_reason` | enum or null | see reason codes below |
| `provider` / `model` | string or null | retained even when usage is unavailable |
| `pricing_version` | string or null | deterministic, versioned rate table id |
| `pricing_effective_at` | ISO-8601 UTC or null | |
| `input_usd_per_million` / `output_usd_per_million` | number ≥ 0 or null | |
| `pricing_source` | enum or null | `table`, `provider`, `unavailable` |
| `source` | enum | `runtime`, `manual`, `derived` |
| `recorded_at` | ISO-8601 UTC | |

Rules:

- Unknown is not zero. Null numeric fields are excluded from all sums and
  counted separately as unknown records.
- Negative, non-finite, or non-numeric values are rejected; the record is
  downgraded to `telemetry_status: unavailable` with reason
  `malformed_usage_payload`.
- `total_tokens` is provider-supplied when present, otherwise the sum of known
  input and output tokens; it stays null if any needed dimension is unknown.
- `estimated_usd` is computed only when the matching token dimension and rate
  are both known: `tokens * usd_per_million / 1_000_000`. Missing dimensions are
  never extrapolated.
- `telemetry_status: partial` means some but not all token dimensions are known.
- Records are keyed by `session_id` + `iteration` + `invocation_id`. An
  identical repeat is a no-op; a differing payload is a `conflict` that
  preserves the original record.
- Correction loops keep the same `session_id`, attribute new work to the
  incremented `iteration`, and never rewrite or double-count prior records.
- Recording is best-effort: a recorder failure warns and preserves the previous
  checkpoint, and never blocks a lifecycle transition.

Reason codes for `unavailable_reason`: `runtime_did_not_expose_usage`,
`provider_omitted_usage`, `malformed_usage_payload`, `pricing_unavailable`,
`recording_failed`.

## Usage checkpoint schema

Plan §8 carries a `usage_reporting` block rendered from these fields:

`schema_version`, `records` (append-only list of `usage_record`),
`totals_by_stage`, `totals_by_iteration`, `feature_total`,
`known_token_count`, `unknown_token_records`, `known_estimated_usd`,
`unknown_cost_records`, `last_recorded_invocation_id`, `report_status`.

Each totals entry exposes `records`, `known_tokens`, `known_estimated_usd`,
`unknown_token_records`, and `unknown_cost_records`. `report_status` is
`exact` (all records exact), `partial` (mixed), or `unavailable` (no known
numbers). Usage fields are reporting-only: they never alter lifecycle state,
approvals, gates, or release eligibility.

## Transitions

| From | Trigger | To |
|---|---|---|
| `AWAITING_PLANNING_APPROVAL` | explicit planning approval | `IMPLEMENTING` |
| `IMPLEMENTING` | all planned chunks reported | `AWAITING_IMPLEMENTATION_APPROVAL` |
| `IMPLEMENTING` / `AWAITING_IMPLEMENTATION_APPROVAL` | validation requested | `VALIDATING` |
| `VALIDATING` | verdict FAIL | `FIX_REQUESTED` |
| `VALIDATING` | verdict PASS | `AWAITING_FINAL_SIGNOFF` |
| `AWAITING_FINAL_SIGNOFF` | user requests a fix | `FIX_REQUESTED` |
| `AWAITING_FINAL_SIGNOFF` | explicit feature-done approval | release-manager → `DONE` |
| `FIX_REQUESTED` | `retry_count < retry_limit`; `iteration += 1` | `IMPLEMENTING` |
| `FIX_REQUESTED` | `retry_count == retry_limit` | `ESCALATED` |
| any | user states an explicit substantive plan change | `PLANNING` |

Every correction returns to `VALIDATING` before any closure state. Same-session
transitions preserve `session_id`, `completed_chunks`, artifacts, and all
previously granted approvals; a correction loop never resets them.

## Retries and escalation

`retry_limit` is 3 correction loops per run. `retry_count` increments on each
`FIX_REQUESTED → IMPLEMENTING` transition and is never reset by a FAIL verdict.
On exhaustion the run enters `ESCALATED`, records the last verdict and
`safe_rollback_point`, and stops. `ESCALATED` never auto-replans, auto-retries,
releases, commits, or archives; it waits for explicit user direction.

## Gates

Planning approval is required before implementation. Validator failure requires
correction and revalidation. Final PASS and explicit final approval are required
before release. Release requires a validator PASS whose `session_id` and
`iteration` match the recorded final approval. Existing implementer
checkpointing and mock-first, auth, secret, and safety rules remain in force.

Existing active plans and explicit legacy artifacts are historical inputs; do
not silently rewrite them. New runs use `feature-planner`.

## Commands

- `/plan <request-or-spec>` — planner only
- `/implement <spec-file> <chunk-id>` — implementer only; a chunk id is required
  unless a `CORRECTION` envelope is supplied
- `/validate [spec-file]` — validator only
- `/feature <request>` — complete flow
