# CLAUDE.md

Read `AGENTS.md` first. It is the authoritative source for architecture and safety rules.

## Scope First

- Do not load the whole repo.
- Pick one lane and stay inside it until you have enough evidence.
- Open the matching tests early.
- Ignore `extensions/`, `output/`, `node_modules/`, `legacy_ui/`, and `__pycache__/` unless the task explicitly depends on them.

## Start Files By Task

- Platform/config:
  - `main.py`
  - `appcore/api/config.py`
  - `appcore/api/deps.py`
  - `appcore/db/session.py`
  - `tests/platform/`
- Catalog/API:
  - `workflows/extension_catalog/router.py`
  - `workflows/extension_catalog/service.py`
  - `appcore/contracts/schemas.py`
  - `appcore/storage/crud.py`
  - `tests/workflows/extension_catalog/`
- Activation reports:
  - `workflows/activation_reports/router.py`
  - `tests/workflows/activation_reports/test_router.py`
- Marketplace/analysis:
  - `workflows/marketplace/router.py`
  - `workflows/marketplace/client.py`
  - `workflows/marketplace/analysis_service.py`
  - `workflows/marketplace/trigger_service.py`
  - `tests/workflows/marketplace/`
- Executor:
  - `executor/host.py`
  - `executor/flows/playwright/`
  - `tests/executor/`
- UI:
  - `ui/src/app/`
  - relevant `ui/src/features/`
  - `ui/src/lib/api/`
  - colocated `*.test.ts(x)`

## Canonical Layout

- Shared platform: `appcore/`
- Business workflows: `workflows/`
- Sandbox runtime: `executor/`
- Analyst UI: `ui/`
- Tests: `tests/`

Top-level legacy directories such as `routers/`, `scanner/`, `core/`, `database/`, `crud/`, `models/`, and `schemas/` are not the place for new logic.

## Hard Rules

- Preserve `(publisher, name, version)` uniqueness.
- Route DB writes through `appcore/storage/crud.py`.
- Validate with Pydantic before insert.
- Use SQLAlchemy 2.0 and Pydantic v2 only.
- Add Alembic migration for schema changes.
- Keep sandbox execution inside Docker.
- Do not add dependencies without explicit approval.

## Verified Runtime Surfaces

- `main.py` includes only:
  - `workflows.extension_catalog.router`
  - `workflows.activation_reports.router`
  - `workflows.marketplace.router`
- Root/catalog endpoints remain on root paths.
- Activation reports live under `/api/activations`.
- Marketplace endpoints live under `/api/marketplace`.

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
