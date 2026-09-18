# AGENTS.md — <PROJECT-NAME>

<!-- INIT: This file is injected into every AI-factory agent session via
     `.opencode/opencode.jsonc` → `instructions`. Keep it short (≤60 lines):
     quick-start commands, architecture in one glance, hard rules. Long-form
     detail belongs in docs/development/. Every section here is paid for in
     tokens by every agent run. -->

## Quick Start

```bash
# Start all services
<command>

# Or dev mode
<command>
```

## Architecture

- **Frontend**: <stack> (port <N>), proxies `/api` → backend:<port>
- **Backend**: <stack> (port <N>)
- **Database**: <engine + how schema initializes>
- **Auth**: <mechanism>
- **External APIs**: <systems> (tokens in `.env`)

## Key Conventions

- **Auth**: All `/api/*` routes require `Authorization: Bearer <JWT>` via
  `<auth-dependency>`.
- **Auth exemption**: The following routes are public:
  - `/api/auth`
  - <!-- INIT: list every existing public route; agents must not add new ones
           without an approved spec exemption -->
- **New public routes**: Require an approved feature-spec exemption and must be
  added to the list above during release.
- **Database**: <sync/async driver rule>. Add migrations under
  `<migrations-dir>/` and update `<fresh-install-schema>` when schema changes
  affect fresh installations.
- **Frontend proxy**: `package.json` proxy → `<backend-url>`
- Run `<lint-command>` for backend changes.
- Mock external integrations in tests. Never trigger live
  <external-systems> mutations through tests, curl, or browser automation.
- **<Test-suite status>** — e.g. "No test suite — manual verification via
  <Swagger UI / frontend> (login: <dev-creds>). Health: `curl localhost:<port>/health`."
- **Prod deploy**: `<command>`

## Documentation Map

- **`docs/development/`** — living architecture reference: `DIGEST.md`
  (condensed, read first), project context, API reference, coding standards
- **`docs/Features/`** — per-feature behavior and operational guidance
- **`docs/deployment/`** — environment variables & deployment secrets
- **`docs/operations/`** — operational runbooks
- **`docs/archive/`** — historical, unmaintained; do not read as truth
- **`.opencode/specs|plans|qa/`** — AI-factory artifacts (see
  `.opencode/rules/workflow.md`)
- **`.opencode/scripts/legacy/`** — superseded scripts, reference only
