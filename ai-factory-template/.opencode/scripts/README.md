# .opencode/scripts/

Automation owned by the AI factory (not shipped application code).

| Path | Contents |
|---|---|
| `check_lifecycle_contract.py` | Offline static assertions that the lifecycle contracts (`rules/workflow.md`, `agent/*.md`, `command/*.md`) still declare every state, checkpoint field, transition, gate, and safety rule; reads markdown only, writes nothing (`python3 .opencode/scripts/check_lifecycle_contract.py`) |
| `usage_recorder.py` | Records/normalizes AI-factory usage records into plan §8 `usage_reporting` and renders the operator report (`record`, `report`); reporting-only, never a gate |
| `test_usage_recorder.py` | Local `unittest` suite for the recorder (`python3 -m unittest .opencode.scripts.test_usage_recorder` or run the file directly); no network, no external calls |
| `qa/pages/` | Reusable per-page QA manifests and smoke/full scripts (see its README) |
| `qa/archive/` | Per-feature QA scripts archived with their feature slug |
| `shareable/` | Standalone, dependency-light utilities runnable outside the app; must be confirmation-gated and never import application code |
| `legacy/` | Superseded scripts kept for reference only — not wired into the app |

Rules:

- Mock-first: no script may trigger live external mutations without an
  explicit confirmation gate or dry-run mode.
- Offline-first: factory tooling here must run with no network access and must
  not import application code.
- Add a `README.md` to any new subfolder explaining purpose and safety class.
