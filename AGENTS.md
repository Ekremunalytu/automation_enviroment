# AGENTS.md

`Last Updated: 2026-05-13 (W13 closed via PR #20 -> 772deb3; W14 active on week14 branch cut from main at 69251f1; W14-1 BLOCKER -> HIGH downgraded, W14-2 closed via bde17be, W14-3 closed via 941250d, W14-4 closed, W14-5 closed via dc79f61+9c095d2+db25d5f, W14-6 closed via 2adad43+b031803+e42a448; W14 sub-iter slate complete; W14-7 post-slate hotfix closed via df925f8+c11ebd8 — container-shipping regression + Python 3.10 UTC compat; close-out PR week14 -> main next)`

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

- W0-W7 closed `2026-04-23`; PR345 and W8-0 landed `2026-04-27`.
- **W8 closed `2026-04-29`; W9 closed `2026-05-04` via PR #9; W10
  closed `2026-05-04` via PR #11; W11 closed `2026-05-05` and merged
  via PR #14; W12 closed `2026-05-10` and merged via PR #18
  (`33a0852`); W13 closed `2026-05-13` and merged via PR #20
  (`772deb3`).** Active phase is **W14 — Codex M-class Acceptance +
  Observability** active on the `week14` branch (cut from `main` at
  `69251f1` on `2026-05-13`): plan `documents/REFACTOR_OPTIMIZATION.md`
  §12, tracker `documents/active-work/W14-codex-acceptance-observability.md`.
  W14-1 pulled `2026-05-13` and BLOCKER downgraded to HIGH the same day
  (conservation guard landed). W14-2 (M4-M7 + M11) closed `2026-05-13`
  via `bde17be`. W14-3 (M13 + M14b + U4-U12) closed `2026-05-13` via
  `941250d`. W14-4 (analysis-jobs-race lock symmetry + EvidenceEvent
  kind↔event_class invariant) closed `2026-05-13`. W14-5 (logger
  consolidation + run-ID stamping + executor runtime fingerprint;
  ADR 0010 landed; M5 docker-exec propagation auto-closed) closed
  `2026-05-13` via `dc79f61` + `9c095d2` + `db25d5f`. W14-6 (regression
  lock-in umbrella: bare-binary pragma ratchet + executor.control
  outbound surface gate + variable-indirect subprocess coverage with
  binary_paths migration) closed `2026-05-13` via `2adad43` + `b031803`
  + `e42a448`. W14 sub-iter slate complete. **W14-7 post-slate
  hotfix** closed `2026-05-13` via `df925f8` (Dockerfile COPY for
  `executor/binary_paths.py` + `executor/runtime_fingerprint.py` +
  Python 3.10 `datetime.UTC` compat shim) and `c11ebd8` (regression
  gate `tests/architecture/test_executor_container_shipping.py`).
  Close-out PR `week14 -> main` is the next milestone. Past
  W8/W11/W12/W13 trackers remain stable-ID references only.
- ADR 0007 local-network-binding is **Accepted and implemented**; loopback
  defaults + `EXTRACE_ALLOW_LAN` are pinned by `test_default_bindings.py`.

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
