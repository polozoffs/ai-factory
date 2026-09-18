# Project Digest (condensed) — planner & validator reference

> **Purpose:** A condensed, token-lean summary of
> `docs/development/PROJECT_CONTEXT.md` and
> `docs/development/CODING_STANDARDS.md` for agents that need
> conventions/architecture awareness but not full implementation detail
> (`feature-planner`, `validator`). `implementer` should still read the full
> source files. If needed detail is absent, read the full files. Keep this
> curated summary in sync when source conventions or domains change.
>
> **THIS IS THE MOST IMPORTANT FILE FOR TOKEN ECONOMY.** Every agent reads it
> first — and usually only it. Fill it in during INIT and keep it under
> ~150 lines. If it grows, move detail into the full docs and reference them.

---

## 1. What this project is

<!-- INIT: 3-6 lines. What the app does, who uses it, the external systems it
     talks to, and where credentials/config live. -->

**<PROJECT-NAME>** — ...

External systems: ... Base URLs and credentials are in `.env` / ...

## 2. Stack

<!-- INIT: one row per layer. -->
| Layer | Tech |
|---|---|
| Frontend | |
| Backend | |
| Database | |
| Auth | |
| Containers | |

## 3. Repo layout (top level)

<!-- INIT: a compact tree of the directories an agent must navigate, with
     one-line annotations. Mark the single registration points (router
     registration, route table, etc.). -->
```text
backend/ or src/ or cmd/
  ...
```

Routes are registered in `...`; frontend routes in `...`.

## 4. Auth & security essentials

<!-- INIT: how requests are authenticated, the exact auth dependency name,
     where public-route exemptions are listed (point at AGENTS.md), and any
     special cases (SSE tokens, webhooks, public endpoints). -->
- All `/api/*` routes require ... via `...`, except routes listed in the
  public-exemption list in `AGENTS.md`.
- New public routes require an approved feature-spec exemption and are added to
  `AGENTS.md` during release.
- Never commit secrets; use parameterized SQL only.

## 5. Database pattern

<!-- INIT: sync vs async driver rule, migration tool or raw-SQL convention,
     where migrations live, and the fresh-install schema file. Delete if the
     project has no database. -->
- ...
- Migrations live in `...`; there is no ORM migration tool / we use <tool>.

## 6. Naming & style conventions

<!-- INIT: adapt rows to the languages in this repo. -->
| Element | Convention | Example |
|---|---|---|
| Backend modules/functions | `snake_case` | |
| Backend classes | `PascalCase` | |
| Backend constants | `UPPER_SNAKE_CASE` | |
| SQL tables/columns | `snake_case` | |
| Frontend components | `PascalCase.js` | |
| Frontend hooks | `useCamelCase` | |
| Frontend vars/functions | `camelCase` | |
| Frontend constants | `UPPER_SNAKE_CASE` | |

- Import ordering: ...
- Lint command: `...` <!-- INIT: the exact command the validator runs -->
- Error handling pattern: ...
- Tests mock external calls; never trigger real external mutations.

## 7. Common "add a new X" patterns

<!-- INIT: the 5-8 recipes agents follow most often, each one line. -->
| Task | Pattern |
|---|---|
| New API endpoint | |
| New DB table | |
| New service | |
| New frontend page | |
| New API call | |

## 8. Domain notes

<!-- INIT: short sections for the project's distinctive domains — anything an
     agent would otherwise have to reverse-engineer. One short paragraph each.
     Add §9, §10 as needed, keeping the whole digest under ~150 lines. -->

## 9. When you need more detail

- Full architecture, service list, tables, and startup sequence →
  `docs/development/PROJECT_CONTEXT.md`
- Full code rules, examples, and review checklist →
  `docs/development/CODING_STANDARDS.md`
- API surface → `docs/development/API_REFERENCE.md`
- Feature behavior → `docs/Features/*.md`
- Public route exemptions and local commands → `AGENTS.md`
