# AGENTS.md

`Last Updated: 2026-05-05`

## Authority

- This file is the hard-rules entrypoint for agents.
- It is intentionally short because it is frequently preloaded into context.
- For task routing after these rules, read
  `documents/AGENT_CONTEXT.md`.
- For current phase state, trust `documents/REFACTOR_STATUS.md`.
- If docs conflict with code or tests, trust code/tests and update the doc.
- If a requested change violates these principles, stop and report instead of
  implementing.

## Current State

- W0-W7 PoC stabilization/security window closed on `2026-04-23`
  (PoC acceptance bar 11/11 green). Details:
  `documents/REFACTOR_STATUS.md` (slim canonical).
- PR345 target activation lifecycle complete `2026-04-27`; W8-0
  deterministic harness readiness gate landed `2026-04-27`.
- **W8 closed for active work `2026-04-29`** — W8-1..W8-7 + W8-9
  landed; W8-8 manifest log sanitization deferred under named triggers
  (see `active-work/W8-security.md`). **W9 closed `2026-05-04` via
  PR #9.** **W10 closed `2026-05-04` via PR #11** (contract hygiene +
  planner cleanup; W10-1..W10-7 landed). Active phase: **W11 monitor
  lifecycle split** — entry gate met `2026-05-04` after the
  `[FOLLOWUP w11-precursor-tests]` safety net landed (38 direct
  module-owned tests for `runtime_capture/extension_host.py` and
  `health_reconciliation.py`). W11-1..W11-6 landed on `2026-05-04`
  / `2026-05-05`; W11-7 `workflows/extension_catalog/service.py`
  split is now the next structural pull-first. P1 W11 companion
  `[FOLLOWUP w8-6-extension-host-output-redaction]` landed
  `2026-05-05` ahead of W11-6. Tracker:
  `active-work/W11-monitor-lifecycle.md`. Plan navigation:
  `documents/AGENT_CONTEXT.md` → matching lane doc. Past W8/W9/W10
  trackers and stable IDs stay around because code/tests reference
  items by ID (`W8-N`, W9/W10 commit hashes), not because new work is
  being done in those windows.
- ADR 0007 local-network-binding **Accepted and implemented**
  `2026-04-29` via W8-7 (`feat/w8-7-lan-binding-defaults`). Loopback
  defaults + `EXTRACE_ALLOW_LAN` enforcement live in
  `appcore/api/config.py`, `docker-compose.yml`, and the
  `test_default_bindings.py` regression matrix.

## Non-Negotiable Rules

- Preserve the unique constraint `(publisher, name, version)`.
- Route database writes through `appcore/storage/crud.py`; thin compatibility
  wrappers may delegate immediately but must not own write logic.
- Validate with Pydantic before database insertion.
- Use SQLAlchemy 2.0 syntax only.
- Use Pydantic v2 APIs only.
- Add an Alembic migration for schema changes.
- Keep sandbox execution isolated in Docker.
- Do not introduce dependencies without explicit approval.
- Do not add generic `try/except Exception` blocks.
- Do not introduce unsafe behavior: no arbitrary exec, unsafe deserialization,
  or uncontrolled network calls.
- Treat extension input, reports, logs, and VSIX contents as adversarial.
- Keep critical operations observable through logs, report fields, traces, or
  metrics.

## Architecture Boundaries

- Runtime entrypoint: `main.py`.
- Canonical backend code: `appcore/`, `workflows/`, `executor/`.
- Canonical frontend code: `ui/`.
- Framework-agnostic analysis code: `packages/`.
- Tests live under `tests/`; UI tests live under `ui/src/**/*.test.ts(x)`.
- `packages/` must not import `workflows/`, `executor/`, `ui/`, or
  `appcore/`.
- Detection rules live in `packages/analysis_engine/rules/` and may only
  consume contracts.
- Workflows reach sandbox mechanics through `executor.control`.
- Do not recreate legacy top-level business directories such as `routers/`,
  `scanner/`, `core/`, `database/`, `crud/`, `models/`, or `schemas/`.

## Read Path

1. Read this file.
2. Read `documents/AGENT_CONTEXT.md`.
3. Read exactly one matching lane doc under `documents/agent-lanes/`.
4. **Read subsystem docs only when the lane doc explicitly points to
   them. Default preload is forbidden.** Slim canonical subsystem
   docs (`ARCHITECTURE.md`, `PROJECT_STRUCTURE.md`, `TESTING.md`,
   `DETECTION_SEMANTICS.md`, `EXECUTOR_PLAYWRIGHT.md`) link out to
   subdir splits — open the split, not the canonical, for detail.
5. Read `documents/active-work/<file>.md` only when the lane doc
   points to it (e.g. W8 work goes through `active-work/W8-security.md`).
6. Read matching tests early; they usually reveal expected behavior faster
   than broad source scans.
7. Do **not** read `documents/archive/`. Archive is frozen historical
   reference; open it only when a slim canonical doc explicitly says
   "details: archive/...".

## Context Budget

- Do not scan the whole repository by default.
- Start from one task lane and expand only when evidence requires it.
- Ignore heavy/generated trees unless the task explicitly targets them:
  `extensions/`, `output/`, `node_modules/`, `ui/dist/`, `__pycache__/`,
  `.venv/`, `.mypy_cache/`, `.ruff_cache/`.
- Do not preload all of `documents/`.
- Prefer `rg` / `rg --files` for search.

## Common Commands

- `make install-dev`
- `make dev`
- `make test-local`
- `make check-all`
- `make migrate`
- `make test-security`
- `make exec-up`
- `make exec-run`
- `make ui-up`
- `make sim-target TARGET=publisher.name [TRIGGERS=...] [SCENARIO=...]`
- `make sim-all`
- `make demo-canary`
- `make demo-canary-offline`

## Required Self-Review

State briefly:

- Files modified
- DB schema changed: Yes/No
- Tests added/updated: Yes/No
- Risks or assumptions
