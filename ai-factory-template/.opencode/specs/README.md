# .opencode/specs/

Living specification documents for the AI factory pipeline (see
`.opencode/rules/workflow.md`).

- `TEMPLATE.md` — copy this when feature-planner drafts a new spec.
- `active/` — specs currently being implemented/validated.
- `archive/` — specs that passed validation and were shipped. Kept as a
  historical record of intent + acceptance criteria.

`feature-planner` is the single planning stage. It emits the brief, spec,
technical plan, QA plan, and optional checkpoint in one resumable context.
After approval, the normal flow is implementer → validator → final approval →
release-manager. See `.opencode/agent/` and `.opencode/command/` for contracts.
