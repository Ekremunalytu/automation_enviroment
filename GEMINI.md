# GEMINI.md

`Last Updated: 2026-04-23`

Read `AGENTS.md` before doing anything substantial. It contains the
authoritative rules.

## Current Phase

- Week 4 stabilization closed `2026-04-20`.
- W5 detection foundations landed `2026-04-20` (contracts under
  `packages/analysis_contracts/detection/`, A1/A2/A4/A6 rules in
  `packages/analysis_engine/rules/`, T1 canaries under
  `extensions/malicious/`, `tests/security/`, `make test-security`).
- W6 automation reliability + capture hardening landed `2026-04-21`; the W6
  correctness follow-up (target-only attribution, `tls_client_hello` in
  `TLS_EVENT_TYPES`, `RuleExecutionStatus.ERROR` dominance, security-fixtures
  CI lane) closed on `2026-04-23`. **W6 closed.**
- **W7 (acceptance + buffer):** open as of `2026-04-23`.
- Use `documents/REFACTOR_STATUS.md` for current closure state and
  `documents/REFACTOR_OPTIMIZATION.md` §10 for the W0-W7 window.

## Context-Safe Workflow

- Never expand to the whole repository unless the task truly spans multiple
  systems.
- Start from the narrowest entrypoint and the matching tests.
- Treat `docs/` and `documents/` as secondary references; verify against code.
- Skip `extensions/`, `output/`, `node_modules/`, `legacy_ui/`, and
  `__pycache__/` unless directly needed.

## Task Routing

- API/bootstrap:
  - `main.py`
  - `appcore/api/`
  - `appcore/db/`
  - `tests/platform/`
- Extension catalog:
  - `workflows/extension_catalog/`
  - `appcore/contracts/`
  - `appcore/storage/`
  - `tests/workflows/extension_catalog/`
- Activation reports:
  - `workflows/activation_reports/router.py`
  - `tests/workflows/activation_reports/`
- Marketplace and analysis:
  - `workflows/marketplace/`
  - `tests/workflows/marketplace/`
  - `tests/smoke/`
- Executor:
  - `executor/control.py`
  - `executor/host.py`
  - `executor/container/`
  - `executor/flows/playwright/`
  - `tests/executor/`
- UI:
  - `ui/src/app/`
  - `ui/src/features/`
  - `ui/src/components/`
  - `ui/src/lib/`
- Security:
  - `documents/adrs/0002-threat-model.md`
  - `documents/adrs/0003-detection-taxonomy.md`
  - `documents/adrs/0004-malicious-fixture-policy.md`
  - `extensions/malicious/`
  - `tests/security/`

## Canonical Structure

- `appcore/`: shared platform code
- `packages/`: framework-agnostic contracts and planner logic
- `workflows/`: business workflows
- `executor/`: Docker-isolated sandbox runtime
- `ui/`: Vite + React analyst console
- `tests/`: backend, security, and executor test suites

Do not add new business logic to top-level legacy directories such as
`routers/`, `scanner/`, `core/`, `database/`, `crud/`, `models/`, or
`schemas/`.

## Invariants

- Preserve `(publisher, name, version)` uniqueness.
- All DB writes go through `appcore/storage/crud.py`.
- Pydantic validation is required before insert.
- SQLAlchemy 2.0 only.
- Pydantic v2 only.
- Alembic migration required for schema changes.
- Keep executor logic isolated in Docker.

## Verified API Shape

- Root/catalog routes stay on root paths.
- Activation report routes are under `/api/activations`.
- Marketplace routes are under `/api/marketplace`.

## Useful Commands

```bash
make dev
make test-local
make check-all
make test-security
make migrate
make exec-up
make exec-run
make ui-up
```
