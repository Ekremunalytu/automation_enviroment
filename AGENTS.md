# AGENTS.md

`Last Updated: 2026-05-13 (W12 closed via PR #18; W13 — Test Expansion + Observability closed 2026-05-13 (W13-1..W13-13 all GREEN); W13-1..W13-7 closed — acceptance bar cleared; W13-8/9/10 §11.10 GOAL pulls closed (benign silence fixture 3→5 / .env gitignore gate / singleton-lock recovery); W13-11 HMAC python secret target-install race closed 2026-05-12 — Path A host-side eager-consume + env var passthrough (6/6 main sub-commits + 7 post-landing additions in same push); final bar test-local 1521 → 1537 / tests/architecture/ 105 → 112; W13-12 fail-closed harness handshake closed 2026-05-12 (5/5 sub-commits + 3 behavioral pins; final bar 1537 → 1539 → 1542 / 112 → 115); W13-13 worker-start cancel-race CAS closed 2026-05-13 (5/5 sub-commits — Path B worker-entry `with_for_update()` snapshot lock + lifecycle-helper-not-wrapper deadlock avoidance + 2-fact AST gate; final bar 1542 → 1547 / 115 → 117); close-out PR week13 → main READY (close-gate cleared))`

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
  (`33a0852`).** Active phase: **W13 — Test Expansion + Observability**
  (`REFACTOR_OPTIMIZATION.md` §11.10; tracker:
  `active-work/W13-test-expansion-observability.md`). W13-1..W13-7
  closed — every MEDIUM/HIGH Codex Cloud audit acceptance-bar item
  (H3 via W13-5, H4 via W13-3, H5 via W13-2, H6 via W13-1, M1 via
  W13-7, M9 via W13-6) landed. Next step is the W13 end-of-phase
  close-out PR `week13 → main` (W12 PR #18 pattern). Entry baseline:
  post-Codex-fix `make check-all` green at the W12 close commit
  (`make test-local` 1452 passed / 6 skipped / 6 deselected;
  `make test-security` 211 passed; `tests/architecture/` 76 passed).
  W13-5 close (`2026-05-11`): `make test-local` 1492 → 1498 collected
  (+6 passed); `make test-security` 211 unchanged;
  `tests/architecture/` 87 → 93. W13-6 close (`2026-05-11`):
  `make test-local` 1498 → 1505 collected (+7 passed);
  `make test-security` 211 unchanged; `tests/architecture/` 93 → 95;
  production diff scoped to `executor/flows/playwright/runtime_capture/extension_host_strace_parse.py`
  (+4 net lines in the factory body). W13-7 close (`2026-05-11`):
  `make test-local` 1505 → 1506 collected (+1 passed);
  `make test-security` 211 → 212; `tests/architecture/` 95 unchanged;
  production diff scoped to `packages/analysis_contracts/evidence.py`
  (+45 net lines: 4 constants, 1 helper `_redact_private_key_bounded`,
  `redact_multiline_secrets` body refactored to a bounded linear
  scanner with a 16 KB BEGIN→END window cap). Past W8/W11/W12 trackers
  stay available only because code/tests reference stable IDs
  (W8-1..W8-9, W11-1..W11-8, W12-0..W12-5).
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
