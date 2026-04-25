# CLAUDE.md

`Last Updated: 2026-04-25`

Read `AGENTS.md` first. It is the authoritative source for architecture and
safety rules. This file is the Claude-facing quick map for the current repo
state.

## Current Project Phase

> Phase-state narrative is canonicalized in
> [`documents/REFACTOR_STATUS.md`](documents/REFACTOR_STATUS.md). Do not
> duplicate it here — if a fact contradicts REFACTOR_STATUS, trust
> REFACTOR_STATUS (and fix the drift). Deferred items live in
> [`documents/POST_POC_BACKLOG.md`](documents/POST_POC_BACKLOG.md); the
> W0-W7 weekly plan is [`documents/REFACTOR_OPTIMIZATION.md` §10](documents/REFACTOR_OPTIMIZATION.md);
> the scheduled W8-W13 post-PoC external-review integration window is §11
> (gated on PR345 target activation lifecycle).

**Current state summary (2026-04-25):**

- W4 stabilization, W5 detection foundations, W6 automation hardening,
  W7 PoC acceptance — all **closed**.
- Post-W7 hardening landed `2026-04-24`: fatal UI-crash fail-fast,
  scan-between VS Code restart, `attribution/` subpackage split,
  `sim-target` Makefile lane, legacy-verdict back-compat, retry-on-crash
  page-reload callback threading, `aborted_after_fatal_ui_crash`
  skipped-scenario records, per-scenario UI blocker probe, trimmed
  terminal-usage stimulus, monitor discovery-log rate-limit.
- Branch `feat/simulation-progress-cancel` landed `2026-04-25`:
  weighted simulation progress (UI + heartbeat scenario sub-progress),
  full-stack cancel flow (HTTP + DB pessimistic-lock CRUD + heartbeat
  sandbox tear-down), VNC harness crash fix (delete-before-reload of
  ready marker + async/await activation), and the
  `t1-demo-runnable-canary` declawed fixture + rule + Makefile lanes.
  Code-review follow-ups deferred to POST_POC_BACKLOG under the
  `[FOLLOWUP simulation-progress-cancel]` tag.
- W8-W13 scheduled, not opened. Next action: land PR345 3-5 + ADR.
- **Security scaffolding already present:**
  - `packages/analysis_contracts/detection/`
  - `packages/analysis_engine/rules/`
  - `extensions/malicious/`
  - `tests/security/`
  - `make test-security`
  - `make test-security-live`

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
