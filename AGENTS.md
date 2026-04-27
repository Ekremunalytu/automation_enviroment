# AGENTS.md

`Last Updated: 2026-04-27`

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
  with `REFACTOR_OPTIMIZATION.md` section 10.7 green.
- PR345 target activation lifecycle is complete as of `2026-04-27`
  (`REFACTOR_STATUS.md` "PR345 Complete").
- W8-0 deterministic harness readiness gate landed on `2026-04-27`.
- W8-W13 external-review integration is eligible to open; use
  `REFACTOR_OPTIMIZATION.md` section 11 and `POST_POC_BACKLOG.md`.
- ADR 0007 local-network-binding is Accepted, but its loopback /
  `EXTRACE_ALLOW_LAN` enforcement is still W8-7 work until code/config/tests
  land. Do not document it as implemented.

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
4. Read subsystem docs only if the lane doc points to them.
5. Read matching tests early; they usually reveal expected behavior faster
   than broad source scans.

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
