# GEMINI.md

Read `AGENTS.md` before doing anything substantial. It contains the authoritative rules.

## Context-Safe Workflow

- Never expand to the whole repository unless the task truly spans multiple systems.
- Start from the narrowest entrypoint and the matching tests.
- Treat `docs/` and `documents/` as secondary references; verify against code.
- Skip `extensions/`, `output/`, `node_modules/`, `legacy_ui/`, and `__pycache__/` unless directly needed.

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
  - `executor/host.py`
  - `executor/container/`
  - `executor/flows/playwright/`
  - `tests/executor/`
- UI:
  - `ui/src/app/`
  - `ui/src/features/`
  - `ui/src/components/`
  - `ui/src/lib/`

## Canonical Structure

- `appcore/`: shared platform code
- `workflows/`: business workflows
- `executor/`: Docker-isolated sandbox runtime
- `ui/`: Vite + React + Tailwind analyst console
- `tests/`: backend and executor test suites

Do not add new business logic to top-level legacy directories such as `routers/`, `scanner/`, `core/`, `database/`, `crud/`, `models/`, or `schemas/`.

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
make migrate
make exec-up
make exec-run
make ui-up
```
