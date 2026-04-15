# Agent Context

`Last Updated: 2026-04-15`

This is the thin-context project map for coding agents. Read root `AGENTS.md`
for hard rules first; use this file for fast task routing.

If older docs or task notes conflict with the active refactor direction, check
`documents/REFACTOR_EXECUTION_PLAN.md` first and treat
`documents/REFACTOR_EXPANSION_NOTES.md` as non-binding follow-on guidance.

## Read Path

1. `AGENTS.md`
2. this file
3. only the subsystem docs the task actually touches
4. `documents/REFACTOR_EXECUTION_PLAN.md` when the task touches ongoing
   refactor work or document conflicts

## Core Shape

- Entry point: `main.py`
- Canonical backend: `appcore/`, `workflows/`, `executor/`
- Canonical frontend: `ui/`
- Tests: `tests/`
- Legacy top-level dirs such as `routers/`, `scanner/`, `core/`, `database/`,
  `crud/`, `models/`, `schemas/` are not where new logic should go

## Non-Negotiables

- Preserve `(publisher, name, version)` uniqueness
- All DB writes go through `appcore/storage/crud.py`
- Validate with Pydantic before insert
- Use SQLAlchemy 2.0 and Pydantic v2 only
- Add Alembic migration for schema changes
- Keep sandbox execution isolated in Docker

## Start By Task

- Platform/config:
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
- Marketplace/analysis:
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

## API Shape

- Root/catalog routes stay on root paths
- Activation reports live under `/api/activations`
- Marketplace and analysis live under `/api/marketplace`

## Context Budget

- Do not scan the whole repo by default
- Open matching tests early
- Ignore `extensions/`, `output/`, `node_modules/`, `legacy_ui/`, and
  `__pycache__/` unless needed
- If docs and code disagree, trust code and tests

## Helpful Commands

- `make dev`
- `make test-local`
- `make check-all`
- `make migrate`
- `make exec-up`
- `make exec-run`
- `make ui-up`

## Load Only If Needed

- `documents/ARCHITECTURE.md`
  - system shape and request flows
- `documents/PROJECT_STRUCTURE.md`
  - placement rules
- `documents/TESTING.md`
  - test layout and fixtures
- `documents/EXECUTOR_PLAYWRIGHT.md`
  - executor/runtime details
- `documents/DETECTION_SEMANTICS.md`
  - report JSON semantics
- `documents/VSCODE_API_COVERAGE_AUDIT.md`
  - trigger and coverage semantics
