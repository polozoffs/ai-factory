# QA Test Plan: &lt;short title&gt;

- **Slug**: `kebab-case-slug` (matches spec/plan slug)
- **Spec**: `.opencode/specs/active/<slug>.md`
- **Plan**: `.opencode/plans/active/<slug>.md`
- **Status**: draft | in-progress | done
- **Author**: feature-planner (AI) — reviewed by: &lt;user, if reviewed&gt;

## 1. Scope

What is and isn't covered by this test plan, mapped back to the spec's
acceptance criteria.

## 2. Test matrix (per chunk)

Concrete, executable checks. Each row must be verifiable by the validator or a
human: exact commands, requests, or UI steps plus the expected result.

<!-- INIT: name this project's live external systems and local endpoints below. -->
> **Mock-first (non-negotiable).** Never cause real network I/O or a live
> mutating call to external systems. Backend unit tests mock the HTTP client
> seam; frontend tests mock the API client module; API `curl` rows target local
> services and default to read-only GET; Playwright rows must not click live
> trigger/promote/submit actions. For behavior that only a live mutation would
> exercise, specify a mocked test or the app's dry-run path and mark the row
> "manual/mock-only".

### Chunk 1: `<slug>-chunk-1`

| # | Type | Steps / command | Expected result | Maps to spec criterion |
|---|------|-----------------|-----------------|------------------------|
| 1 | API  | `curl -X GET http://localhost:<port>/api/.../<id>` with missing id | `404` + error body | Criterion 2 |
| 2 | UI   | Open &lt;page&gt;, trigger action X | spinner shows while in flight | Criterion 3 |
| 3 | unit | targeted compile/import/lint command | no error | Criterion 1 |

### Chunk 2: `<slug>-chunk-2`

| # | Type | Steps / command | Expected result | Maps to spec criterion |
|---|------|-----------------|-----------------|------------------------|
| 1 |      |                 |                 |                        |

## 3. Negative / edge cases

Invalid input, auth-boundary, not-found, conflict, and failure-path checks.

- ...

## 4. Regression checks

Existing behavior that must not break (adjacent endpoints/pages, shared
components).

- ...

## 5. Verification environment notes

What must be running (db, backend, frontend), required env vars / tokens, and
any checks that can only be done manually (and why).
