# Technical Plan: &lt;short title&gt;

- **Slug**: `kebab-case-slug` (matches the spec slug)
- **Spec**: `.opencode/specs/active/<slug>.md`
- **Status**: draft | in-progress | done
- **Author**: feature-planner (AI) — reviewed by: &lt;user, if reviewed&gt;

## 1. Summary

One paragraph: the technical strategy for satisfying the spec's acceptance
criteria, and the rough shape of the work.

## 2. Architecture decisions

Key choices made and why (data model, API shape, where logic lives, reuse of
existing services). Reference `docs/development/PROJECT_CONTEXT.md` and
existing `docs/Features/*.md` patterns instead of re-deriving conventions.

- Decision 1 — rationale
- Decision 2 — rationale

## 3. Work chunks (with low-level design)

Ordered list of independently implementable and independently validatable
chunks. Each chunk must be completable in a single `implementer` run and
verifiable on its own. Each chunk embeds the low-level design an implementer
needs — concrete enough that no separate design doc is required.

### Chunk 1: `<slug>-chunk-1` — &lt;title&gt;

- **Goal**: what this chunk delivers.
- **Touches**: files/modules/areas (real paths).
- **Depends on**: none | `chunk-N`.
- **Acceptance hooks**: which spec Section-6 criteria this chunk satisfies.
- **Size**: small | medium | large (split large chunks further).
- **Context**: DIGEST; STANDARDS §<n>; FEATURES <name>; FILES <path>

**Design** (low-level, buildable detail):
- **Backend**: functions/services with signatures, model fields, route handler
  behavior, error handling.
- **Frontend**: components, props/state/hooks, API calls routed through the
  project's API client layer.
- **Data**: exact columns/tables/migration SQL sketch.
- **Contracts**: request/response field names, types, status codes that cross
  chunk boundaries.
- **Auth/security**: public vs protected route, input validation rules.
- **Edge cases**: ...

### Chunk 2: `<slug>-chunk-2` — &lt;title&gt;

- ... (same structure)

## 4. Data / migration plan

Schema changes, migrations under the project's migration directory, backfills,
ordering constraints. "None" if not applicable.

## 5. API / interface changes

New/changed endpoints, request/response shapes, auth exposure (which are
public vs behind the project's auth dependency). "None" if not applicable.

## 6. Sequencing & rollback

Order of chunks, any feature-flag or sequencing constraints, and how to roll
back each chunk safely if validation fails after merge.

## 7. Risks / open questions

- ...

## 8. Checkpoint and traceability

Record the durable checkpoint here. State is recorded, never inferred; nothing
grants an approval except an explicit recorded user statement.

- **slug**: `kebab-case-slug`
- **spec_path**: `.opencode/specs/active/<slug>.md`
- **session_id**: `<slug>-s1` (stable for the whole run)
- **iteration**: 0 (increments only on a correction loop)
- **state**: PLANNING | AWAITING_PLANNING_APPROVAL | IMPLEMENTING | AWAITING_IMPLEMENTATION_APPROVAL | VALIDATING | FIX_REQUESTED | AWAITING_FINAL_SIGNOFF | ESCALATED | DONE
- **completed_chunks**: [] (never re-run a listed chunk)
- **planning_approval**: pending | granted | n/a
- **implementation_approval**: pending | granted | n/a
- **final_approval**: pending | granted | n/a
- **last_handoff_source**: user | feature-planner | implementer | validator — quoted evidence
- **retry_count**: 0
- **retry_limit**: 3
- **safe_rollback_point**: commit/tag or "pre-implementation"; preserve
  artifacts, identity, completed chunks, and approvals on retry
- **scope_boundary**:
  - **in scope**: file set this feature may touch
  - **out of scope**: everything else; unrelated working-tree changes are never
    attributed to, reverted by, or judged as part of this feature
- **criterion_to_chunk**: `criterion-id: [chunk-id, ...]`
- **approval evidence**: quoted user statements per approval field
- **Targeted exceptions**: trigger, exact command, expected result, owner, evidence, or SKIPPED reason
- **Metrics baseline**: invocation count, elapsed time, tokens/reads if available, chunk count
- **Usage reporting**: append-only ledger per `.opencode/rules/workflow.md`
  ("Usage reporting contract"). Reporting-only — never a lifecycle or release gate.

```yaml
usage_reporting:
  schema_version: 1
  records:
    - invocation_id: <unique-id>
      stage: feature-planner | implementer | validator | release-manager
      session_id: <session-id>
      iteration: 0
      started_at: null            # ISO-8601 UTC
      completed_at: null
      input_tokens: null          # null = unknown, never 0
      output_tokens: null
      total_tokens: null
      estimated_usd: null
      currency: null
      telemetry_status: unavailable   # exact | partial | unavailable | conflict
      unavailable_reason: runtime_did_not_expose_usage
      provider: null
      model: null
      pricing_version: null
      pricing_effective_at: null
      input_usd_per_million: null
      output_usd_per_million: null
      pricing_source: unavailable     # table | provider | unavailable
      source: runtime                 # runtime | manual | derived
      recorded_at: <iso-8601-utc>
  totals_by_stage: {}   # stage -> {records, known_tokens, known_estimated_usd,
                        #           unknown_token_records, unknown_cost_records}
  totals_by_iteration: {}
  feature_total:
    records: 0
    known_tokens: 0
    known_estimated_usd: 0
    unknown_token_records: 0
    unknown_cost_records: 0
  known_token_count: 0
  unknown_token_records: 0
  known_estimated_usd: 0
  unknown_cost_records: 0
  last_recorded_invocation_id: null
  report_status: unavailable   # exact | partial | unavailable
```
