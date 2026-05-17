# AGENTS.md

`Last Updated: 2026-05-17 (W13 closed via PR #20 -> 772deb3 on 2026-05-13; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d — W14-1..W14-8 sub-iter slate + post-slate hotfixes + close-out hygiene pass; W15 active on week15 branch cut from main HEAD 7cc2921 on 2026-05-14; W15-1 closed via c58c365 — sync analyze error taxonomy parity (M10); W15-2 closed via 765cde7 — clean_workspace is_symlink-before-rmtree (M12); W15-3 closed via 3512a7c — activationEvents bounds + Alembic migration (U8); W15-4 closed via 89e13e3 — UI bounds bundle (U1/U2/U3 + U6); W15-5 closed 2026-05-17 via 43d6438 — quick fixes bundle (I2 UI /health proxy + I4 lifecycle for <id> regex); W15-6 closed 2026-05-17 via be52520 — ADR 0011 unauthenticated catalog endpoints posture Accepted and implemented (Option A; Proposed at e41722e); W15-1 post-slate typing hotfix via 976dc96 — ANALYZE_ERROR_TYPES annotation narrowed; W15-7 pending — compose image SHA pin + GH action trivy version pin + final preamble refresh; W15 mid-iter hygiene 2026-05-16: doc-preamble consistency arch gate + 3 new audit findings in POST_POC_BACKLOG)`

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
  (`4e03c8d`).** Active phase is **W15 — Codex U-class Close-Out +
  UI Bounds + Posture** active on the `week15` branch (cut from `main`
  HEAD `7cc2921` on `2026-05-14`): plan
  `documents/REFACTOR_OPTIMIZATION.md` §13, tracker
  `documents/active-work/W15-codex-uclass-bounds-posture.md`. W15-1
  closed `2026-05-14` via `c58c365` (sync analyze error taxonomy
  parity, M10 close). W15-2 closed `2026-05-14` via `765cde7`
  (`clean_workspace` is_symlink-before-rmtree, M12 close). W15-3
  closed `2026-05-15` via `3512a7c` (`activationEvents` bounds +
  Alembic field-length migration, U8 close). W15-4 closed `2026-05-16`
  via `89e13e3` (UI bounds bundle: timeline + density strip + relations
  graph caps with truncation indicators; U1/U2/U3 + U6 close).
  **W15-1 post-slate typing hotfix** landed `2026-05-16` via `976dc96`
  (`ANALYZE_*_ERROR_TYPES` annotation `tuple[type[BaseException], …]` →
  `tuple[type[Exception], …]` narrowing surfaced by W15-4 close-out
  mypy gate). W15-5..W15-7 pending sequential pull. **W15 mid-iter
  hygiene `2026-05-16`:** W15-7 doc-preamble subset pulled forward;
  six canonical doc preambles refreshed and
  `tests/architecture/test_doc_preamble_consistency.py` added; three
  new audit findings (`health-reconciliation-responsibility-split`,
  `marketplace-router-test-suite-split`,
  `analysis-job-worker-entry-crud-ownership`) appended to
  `POST_POC_BACKLOG.md`. Remaining W15-7 items (compose image pin +
  GH-action pin) still pending. Past W8/W11/W12/W13/W14 trackers
  remain stable-ID references only.
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
