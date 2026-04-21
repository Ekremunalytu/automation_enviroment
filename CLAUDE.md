# CLAUDE.md

`Last Updated: 2026-04-21`

Read `AGENTS.md` first. It is the authoritative source for architecture and
safety rules. This file is the Claude-facing quick map for the current repo
state.

## Current Project Phase

- **Week 4 stabilization:** closed and validated on `2026-04-20`.
- **W5 (detection foundations):** landed 2026-04-20.
- **W6 (automation reliability + capture hardening):** landed 2026-04-21.
- **Post-W6 bridge (2026-04-21):** shared confidence vocabulary
  (`quantize_confidence` + `RiskSignal.confidence_tier`) and
  `detection_report_invariant_issues` cross-layer link check.
- **W7 (acceptance + buffer):** open.
- **Security scaffolding already present:**
  - `packages/analysis_contracts/detection/`
  - `packages/analysis_engine/rules/`
  - `extensions/malicious/`
  - `tests/security/`
  - `make test-security`
  - `make test-security-live`

Use `documents/REFACTOR_STATUS.md` for current closure state and
`documents/REFACTOR_OPTIMIZATION.md` §10 for the weekly W0-W7 window.

## Scope First

- Do not load the whole repo.
- Pick one lane and stay inside it until you have enough evidence.
- Open the matching tests early.
- Ignore `extensions/`, `output/`, `node_modules/`, `legacy_ui/`, and
  `__pycache__/` unless the task explicitly depends on them.
- `routers/`, `scanner/`, `core/`, `database/`, `crud/`, `models/`, and
  `schemas/` are not canonical implementation surfaces.

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
  - `workflows/marketplace/job_service.py`
  - `workflows/marketplace/trigger_service.py`
  - `tests/workflows/marketplace/`
- Contracts and planner:
  - `packages/analysis_contracts/`
  - `packages/analysis_planner/`
  - `packages/analysis_engine/`
- Executor:
  - `executor/control.py`
  - `executor/host.py`
  - `executor/flows/playwright/`
  - `executor/flows/playwright/runtime_capture/`
  - `tests/executor/`
- UI:
  - `ui/src/app/`
  - relevant `ui/src/features/`
  - `ui/src/lib/api/`
  - colocated `*.test.ts(x)`
- Security:
  - `documents/adrs/0002-threat-model.md`
  - `documents/adrs/0003-detection-taxonomy.md`
  - `documents/adrs/0004-malicious-fixture-policy.md`
  - `extensions/malicious/`
  - `tests/security/`

## Hard Rules

- Preserve `(publisher, name, version)` uniqueness.
- Route DB writes through `appcore/storage/crud.py`.
- Validate with Pydantic v2 before insert.
- Use SQLAlchemy 2.0 and Pydantic v2 only.
- Add Alembic migration for schema changes.
- Keep sandbox execution inside Docker.
- Do not add dependencies without explicit approval.
- No generic `try/except Exception`.
- `packages/` must stay framework-agnostic.
- Workflows reach sandbox mechanics through `executor.control`.

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
