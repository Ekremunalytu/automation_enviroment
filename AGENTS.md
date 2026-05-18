# AGENTS.md

`Last Updated: 2026-05-18 (W16 active — phase work complete; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. W16-0..W16-7 sub-iter slate complete: W16-0 doc-reconcile (0e243ca + d78aa9c); W16-1 scenario-accountant emit-site fix (HIGH prod regression W14-1 carry-over, 01f910a + a4a050e); W16-2 analysis-job worker-entry CRUD ownership (W15 audit, 9d6d110 + c8b7811); W16-3 report-finalize null-leakage half (W14 carry-over, fa430f2 + e3d4a0c; attribution-count-parity split to W17+); W16-4 health-reconciliation responsibility split (W15 audit, 304b99f + 384d276); W16-5 simulation-progress-cancel scope reduction (1 rejected, 2 deferred to W17+, e21a05c); W16-6 hygiene splits + Alembic fresh-DB fixture (d40bb01); W16-7 close-out hygiene + canonical preamble refresh (8bf3c6b) + post-PR unaccounted_dropout surface pin (78f080e). Final W16 bar: tests/architecture/ 199 passed; make test-security 220 passed (W13 final 215, +5 — W16-7-followup +3 unaccounted_dropout surface pins); full suite 1893 passed. W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 closed via PR #20 -> 772deb3 on 2026-05-13)`

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
  (`772deb3`); W14 closed `2026-05-14` and merged via PR #21
  (`4e03c8d`); W15 closed `2026-05-17` and merged via PR #22
  (`6161472`) on `2026-05-18`** — W15-1..W15-7 sub-iter slate +
  W15-1 post-slate typing hotfix + close-out hygiene pass (doc
  preamble truth-state refresh across 7 canonical docs + ADR 0011
  catalog endpoint posture gate + compose image SHA pin + GH action
  trivy version pin + close-out lint hygiene). Frozen tracker:
  `documents/active-work/W15-codex-uclass-bounds-posture.md`.
  **Active phase is W16 — Carry-Over Closeout + Audit Findings +
  Production Regression**, **phase work complete; W16 closed via
  PR #23 `week16 -> main` MERGED `2026-05-18` via `1b6d43f`
  (W11-W15 paterni restored via W16-0 doc reconcile)**: plan
  `documents/REFACTOR_OPTIMIZATION.md` §14, frozen tracker
  `documents/active-work/W16-regression-and-audit-closeout.md`.
  **W16-0..W16-7 sub-iter slate complete:** W16-0 doc-reconcile
  (`0e243ca` + `d78aa9c`); W16-1 scenario-accountant upstream emit-site
  fix (W14-1 root-cause split; HIGH prod regression `2026-05-14` +
  `2026-05-15`; `01f910a` + `a4a050e`); W16-2 analysis-job-worker-entry
  CRUD ownership (W15 audit; W13-13 CAS preserved byte-identically;
  `9d6d110` + `c8b7811`); W16-3 report-finalize null-leakage half
  (W14 carry-over; attribution-count-parity split to W17+ as
  `[FOLLOWUP attribution-count-parity]`; `fa430f2` + `e3d4a0c`); W16-4
  health-reconciliation responsibility split (W15 audit; W13-1 HMAC +
  W13-12 fail-closed gates preserved; `304b99f` + `384d276`); W16-5
  simulation-progress-cancel scope reduction (1 rejected, 2 deferred
  to W17+ pending lifecycle harness; `e21a05c`); W16-6 hygiene splits +
  Alembic fresh-DB fixture (`d40bb01`); W16-7 close-out hygiene +
  canonical preamble refresh (`8bf3c6b`) + post-PR `unaccounted_dropout`
  surface pin (`78f080e`). Final W16 bar: `tests/architecture/`
  **199 passed** (W15 final 172, +27); `make test-security` **220
  passed** (W13 final 215, +5 — W16-7-followup +3 `unaccounted_dropout`
  surface pins); full suite **1893 passed, 9 skipped**.
  Past W8/W11/W12/W13/W14/W15/W16 trackers remain stable-ID references only.
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
