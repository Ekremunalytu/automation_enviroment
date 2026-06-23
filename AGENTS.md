# AGENTS.md

`Last Updated: 2026-06-23`

`Last merged weekly: W22 — closed synthetically on the week22 branch, merged to main via PR #31 week22 -> main 2026-05-28 via 1399f82.`

`Active stream: none currently open — operator-console-honesty (UI-only console-honesty stream) merged to main via PR #36 (week24 -> main, 1e3fba6) on 2026-06-23; it made decorative/dead Settings + System controls honest (no backend/DB/detection/executor). The phase.json active_stream pointer still names operator-console-honesty and repoints at the next stream's H0 (named-stream convention). Prior stream reliability-self-defense merged to main via PR #35 (week23 -> main, 653d807). Tracker: documents/active-work/W24-operator-console-honesty.md.`

`Sources of truth: documents/REFACTOR_STATUS.md (state) · documents/POST_POC_BACKLOG.md (deferred) · documents/REFACTOR_OPTIMIZATION.md §20 (last weekly plan) · documents/phase.json (weekly pointer + active stream).`

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

- **W0-W22 all closed**; per-phase merge facts (PR # / SHA) live in
  `documents/REFACTOR_STATUS.md`'s `Last Updated:` banner. Per-phase
  mechanics are frozen under
  `documents/active-work/W{8,11,12,13,14,15,16,17,18,19,20,21,22}-*.md`
  — these stay on the read path **only** because code/tests reference
  items by stable ID (e.g., `W11-1`, `W17-2`). Do not renumber.
- **W22** is closed synthetically on the `week22` branch and merged
  to main via PR #31 `week22 -> main` `1399f82`. Frozen tracker:
  `documents/active-work/W22-coverage-promotion-hard-tier.md`. Plan:
  `documents/REFACTOR_OPTIMIZATION.md §20`.
- **Post-W22 named streams** do not advance the weekly pointer. Static
  Analysis Pre-Check is closed/merged via PR #33; `extension-trigger-matrix`
  is merged; `security-development` merged via PR #34; and
  `reliability-self-defense` merged via PR #35. The latest merged named stream
  is `reliability-self-defense`, tracked by
  `documents/active-work/W23-reliability-self-defense.md`.
- ADRs live in `documents/adrs/`. ADR 0007 local-network-binding is
  Accepted and implemented (loopback defaults + `EXTRACE_ALLOW_LAN`
  pinned by `test_default_bindings.py`).

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
- Dynamic detection rules live in `packages/analysis_engine/rules/`; static
  pre-check rules live in `static_runtime/rules/`. Both may only consume
  contracts and their allowed stdlib/shared-contract helpers.
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

`make install-dev`, `make dev`, `make test-local`, `make check-all`,
`make migrate`, `make test-security`, `make exec-up`, `make exec-run`,
`make ui-up`, `make sim-target TARGET=publisher.name`, `make sim-all`,
`make demo-canary`, `make demo-canary-offline`.

## Required Self-Review

State briefly:

- Files modified
- DB schema changed: Yes/No
- Tests added/updated: Yes/No
- Risks or assumptions
