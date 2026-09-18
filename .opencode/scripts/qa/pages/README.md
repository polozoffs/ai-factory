# .opencode/scripts/qa/pages/

Reusable, page/capability-level QA assets shared across features.

- One directory per page or route, e.g. `pages/<route>/manifest.yaml` +
  `smoke.sh` (+ optional `full.sh`). See `_example-page/` for the shape.
- Each `manifest.yaml` declares: stable id, route, script, owner, revision,
  prerequisites, fixtures, safety class (`read-only` | `mock-only` |
  `dry-run`), modes, criteria/regressions, selector/API dependencies, timeout,
  and last-updated date.
- **Mock-first is non-negotiable**: localhost targets only, read-only GET by
  default, never a live mutating call to external systems.
- `feature-planner` updates only the manifest entries affected by the routes,
  components, or APIs a feature changes, and flags stale references.
- `validator` executes entries as evidence; it never regenerates them.
