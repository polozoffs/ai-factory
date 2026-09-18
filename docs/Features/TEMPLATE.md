# Feature: <name>

> One file per feature domain, `UPPER_SNAKE_CASE.md` or `Kebab-Case.md` —
> pick one convention and stay consistent. `release-manager` creates/updates
> these; `feature-planner` reads only the files for domains a request touches.

## Behavior

What the feature does today, from the user's perspective. Current truth — keep
it updated when the feature changes.

## Entry points

| Surface | Location |
|---|---|
| UI | route(s) |
| API | method + path(s), auth requirement |
| Backend | service/module paths |
| Data | tables/collections touched |

## Operational guidance

Configuration, cron jobs, failure modes, and how to run/verify it manually.

## Related

Links to specs (`.opencode/specs/archive/<slug>.md`) and external docs.
