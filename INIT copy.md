# AI Factory Initialization

Run this once after copying the template into a new repository. It adapts
every project-specific seam of the factory. Until it is done, the agents will
work but will guess at project facts — initialize before the first real
feature run.

**How to run:** either follow the checklist manually, or open the repo in
opencode and say:

> Initialize the AI factory for this repo per INIT.md. Explore the codebase,
> fill in every `INIT:` marker and `<PROJECT-NAME>` placeholder, and replace
> template stubs with real project facts.

The initialization agent must explore the actual code (entrypoints, routers,
package manifests, compose files, CI config) — never invent facts.

---

## Phase 0 — Prerequisites

- [ ] opencode installed and working in this repo (`opencode` runs).
- [ ] Repo is a git repository with at least one commit.
- [ ] Note the model provider(s) available to you — you will set them in
      `.opencode/agent/*.md` frontmatter and optionally `agent/models.json`.

## Phase 1 — Config wiring

- [ ] **`.opencode/opencode.jsonc`** — paths are already correct relative to
      `.opencode/`. Only change if you relocated `AGENTS.md` or `docs/`.
      Optionally enable MCP servers (`playwright` for UI projects; delete the
      commented block otherwise).
- [ ] **`.opencode/agent/*.md`** — in all five files replace `<PROJECT-NAME>`
      with the repo name. If you pin models, set the same `model:` in
      `feature-planner.md`, `implementer.md`, `validator.md`,
      `release-manager.md`; otherwise leave the `model:` line commented out.
- [ ] **`.opencode/agent/models.json`** — optional allowlist of model ids;
      leave `[]` to allow all.

## Phase 2 — Project facts (the files every agent reads)

Fill these by exploring the repo, in this order:

- [ ] **`AGENTS.md`** (repo root) — quick-start commands, architecture,
      auth/exemption list, lint command, test-suite status, mock-first rule
      naming this repo's real external systems. Keep ≤60 lines.
- [ ] **`docs/development/PROJECT_CONTEXT.md`** — full reference: stack table,
      annotated repo tree, startup, config/secrets, external integrations and
      their mock seams, data model, feature map.
- [ ] **`docs/development/CODING_STANDARDS.md`** — real conventions with
      stable `##` numbering (agents cite `STANDARDS §<n>`). Fill §2 backend,
      §3 frontend (delete if N/A), §4 database (delete if N/A), §5
      testing/mocking, §6 security.
- [ ] **`docs/development/API_REFERENCE.md`** — the existing API surface, one
      section per router/domain. Note if it can be generated (e.g. OpenAPI)
      and how.
- [ ] **`docs/development/DIGEST.md`** — the condensed ≤150-line summary of
      the three files above. **This is the file agents read first and usually
      only.** §1 what it is, §2 stack, §3 layout, §4 auth, §5 DB, §6 naming,
      §7 "add a new X" recipes, §8 domain notes, §9 pointers.
- [ ] **`docs/Features/`** — create one doc per existing feature domain using
      `TEMPLATE.md` there. These let the planner ground briefs in current
      behavior instead of re-discovering it.
- [ ] **`docs/deployment/`, `docs/operations/`** — env-var/secrets doc and any
      operational runbooks the project already has.

## Phase 3 — Safety seams (adapt agent contracts to this stack)

- [ ] **`.opencode/agent/implementer.md`** — replace the `INIT:` lines: the
      concrete auth dependency name, migration directory + fresh-install
      schema path, and the exact mock seams (e.g. "mock `aiohttp` /
      `aioresponses`", "mock `src/services/api.js`", "mock `http.Client`").
- [ ] **`.opencode/agent/validator.md`** — replace the `INIT:` lines: name the
      live external systems tests must never hit; name the safe local
      endpoints (health URL); in frontmatter replace the commented permission
      examples with this project's real read-only commands (keep `"*": ask`
      last).
- [ ] **`.opencode/qa/TEMPLATE.md`** — adjust the mock-first callout and the
      sample rows to the real ports/health endpoint.
- [ ] **`.opencode/plans/TEMPLATE.md`** — adjust "migration directory" and
      "auth dependency" wording if your terms differ. Leave the §8
      `usage_reporting` block as-is; it is the checkpoint schema the usage
      recorder reads and rewrites.
- [ ] **`.opencode/specs/TEMPLATE.md`** — adjust the Section-4 area rows to
      the project's layers.

## Phase 4 — Cleanup & first run

- [ ] Delete `docs/Features/TEMPLATE.md`? **No** — keep it; release-manager
      uses it for new feature areas. Delete only templates your stack makes
      meaningless (e.g. `API_REFERENCE.md` for a CLI tool).
- [ ] Delete the `.opencode/scripts/qa/pages/_example-page/` directory once
      the first real page manifest exists — or keep it as a reference.
- [ ] Add project skills to `.opencode/skills/` if useful.
- [ ] **Usage reporting** works out of the box and needs no per-project
      configuration. Verify it with
      `python3 .opencode/scripts/test_usage_recorder.py` (offline, no external
      calls). Keep `.opencode/scripts/usage_recorder.py`,
      `.opencode/command/usage.md`, and the "Usage reporting contract" /
      "Usage checkpoint schema" sections of `.opencode/rules/workflow.md`
      unmodified unless you deliberately change the contract. If you maintain a
      pricing table, version it and keep `pricing_version` /
      `pricing_effective_at` set on every priced record.
- [ ] `git add` the factory files and commit:
      `chore: initialize AI factory (agents, docs skeleton, artifact templates)`
- [ ] **Smoke-test the factory**: run `/plan <one tiny real improvement>` and
      verify the planner reads DIGEST first, produces all four artifacts, and
      stops at the approval gate. Approve, `/implement` the single chunk, then
      `/validate`. Confirm the validator runs your real lint/build commands
      and ends with a `VERDICT:` block.

## Definition of done

- [ ] No `INIT:` markers or `<PROJECT-NAME>` placeholders remain
      (`grep -r "INIT:" .opencode docs AGENTS.md` returns nothing).
- [ ] `/plan` on a trivial request produces a grounded plan that cites real
      files from this repo.
- [ ] `/validate` executes real project commands instead of asking.
- [ ] After a stage run, `.opencode/plans/active/<slug>.md` §8 contains one
      `usage_reporting` record per invocation and `/usage` renders the report;
      unknown telemetry shows as `unknown` / `unavailable`, never `0`, and
      never blocks a transition.
- [ ] This file and `README.md` (the template one) may then be deleted or
      moved to `docs/archive/`.
