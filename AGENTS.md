# AGENTS.md

`Last Updated: 2026-05-21 (W18 active — phase work complete; W18-0..W18-4 sub-iter slate landed on the week18 branch (per user direction 2026-05-21; W11-W17 paterni preserved); close-out PR week18 -> main not yet opened (branch is pushed). §16 W18 plan source + §17-§20 W19-W22 multi-iter roadmap (split out at W18-4 close-out). W18 sub-iter audit trail: W18-0 doc-reconcile (89d0c9b); W18-1 ADR 0012 Option A1 accepted (acf6cc9 + 73d8a5c followup doc-truth); W18-2 heartbeat refactor implementation — step-1 reset off worker thread via dedicated coordinator (a9bffb1 + 78ed7cc ADR self-stamp + b5b64b6 ruff-format followup + 306d744 full-repo lint sweep with pre-commit install); W18-3 lifecycle harness extension tests — parallel reset / idempotency / reset-during-finalize (92b310d + 32d9905 self-stamp); W18-4 close-out hygiene this commit — 8-doc canonical preamble refresh + §16 W18 self-stamp + W18 tracker freeze. Final W18 bar: tests/architecture/ 201 passed (W17 final 200 + W18-0 README phase-pointer arch gate W17->W18 transition); make test-security 220 passed (unchanged from W17); full suite 1903 passed, 9 skipped, 8 deselected (W17 final 1899 + W18-0 +1 + W18-3 +3 lifecycle harness extension tests). W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. W17-0..W17-7 sub-iter slate complete (frozen): W17-0 doc-reconcile (4508c2e); W17-1 attribution-count-parity (8c26d02 + 0a8f59e); W17-2 lifecycle harness scaffold (ff98235 + 44f96c5); W17-3 + W17-4 scope-reduced doc-only (c4c0646 DESIGN-NEEDED — closed via W18-1 ADR + W18-2 implementation); W17-5 hygiene single-item (394d40d + 0cbe1d0); W17-6 close-out (21f7c68); W17-7 post-slate hotfix batch (bf983eb + fc88678 + 326dac8 + 51dba29); W17-7-followup post-PR doc-truth alignment (dab4679). Final W17 bar (unchanged): tests/architecture/ 200 passed; make test-security 220 passed; full suite 1899 passed, 9 skipped, 4 deselected (+6 from W16 final 1893). W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md; W18-W22 multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md (5-iter slate: W18 heartbeat refactor / W19 dropout + harness verification / W20 coverage promotion easy / W21 coverage promotion mid / W22 chat policy + sandbox ADR). W16-0..W16-7 sub-iter slate complete (frozen): W16-1 scenario-accountant emit-site fix (01f910a + a4a050e); W16-2 analysis-job worker-entry CRUD ownership (9d6d110 + c8b7811); W16-3 report-finalize null-leakage half (fa430f2 + e3d4a0c; attribution-count-parity split to W17); W16-4 health-reconciliation responsibility split (304b99f + 384d276); W16-5 simulation-progress-cancel scope reduction (1 rejected, 2 deferred to W17, e21a05c); W16-6 hygiene splits + Alembic fresh-DB fixture (d40bb01); W16-7 close-out hygiene (8bf3c6b) + post-PR unaccounted_dropout surface pin (78f080e). W15 closed via PR #22 MERGED 2026-05-18 via 6161472; W14 closed via PR #21 MERGED 2026-05-14 via 4e03c8d; W13 closed via PR #20 -> 772deb3 on 2026-05-13)`

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
  **Active phase: W18 — Heartbeat Refactor — phase work complete on
  the `week18` branch (per user direction 2026-05-21; W11-W17 paterni
  preserved); close-out PR `week18 -> main` not yet opened (branch
  is pushed)**: plan `documents/REFACTOR_OPTIMIZATION.md` §16, frozen
  tracker `documents/active-work/W18-heartbeat-refactor.md`.
  **W18-0..W18-4 sub-iter slate fully delivered:** W18-0
  doc-reconcile (`89d0c9b`); W18-1 ADR 0012 Option A1 accepted
  (`acf6cc9` + `73d8a5c` followup — dedicated sandbox-reset
  coordinator, function-extension shape; invariant cost trade-offs
  against W13-1 HMAC eager-consume / W13-3 two-phase cancel /
  W13-13 CAS / W16-2 facade lock preserved byte-identical); W18-2
  heartbeat refactor implementation — step-1 reset off worker thread
  via dedicated `_run_reset_off_thread` coordinator (`a9bffb1` +
  `78ed7cc` ADR self-stamp + `b5b64b6` ruff-format followup +
  `306d744` full-repo lint sweep + `pre-commit install`; W17-2
  harness smoke passes byte-identical); W18-3 lifecycle harness
  extension tests — parallel reset / idempotency / reset-during-
  finalize (`92b310d` + `32d9905` self-stamp; per ADR 0012
  §Follow-On); W18-4 close-out hygiene this commit — 8-doc canonical
  preamble refresh + §16 W18 self-stamp + W18 tracker freeze. Final
  W18 bar: `tests/architecture/` **201 passed** (W17 final 200, +1
  from W18-0 README phase-pointer arch gate W17->W18 transition);
  `make test-security` **220 passed** (unchanged from W17); full
  suite **1903 passed, 9 skipped, 8 deselected** (W17 final 1899,
  +4: W18-0 README arch gate + 3 W18-3 lifecycle harness extension
  tests). **Previous phase: W17 — Carry-Over Closeout + Lifecycle
  Harness Yatırımı + Hygiene Sweep — closed via PR #25
  `week17 -> main` MERGED `2026-05-18` via `bff565d`** (W17-0..W17-7
  full audit trail in frozen tracker
  `documents/active-work/W17-carryover-and-lifecycle-harness.md`;
  W17-3/W17-4 DESIGN-NEEDED heartbeat thread relocation deferral
  closed via W18-1 ADR + W18-2 implementation). **W16 closed via
  PR #23 `week16 -> main` MERGED `2026-05-18` via `1b6d43f`** —
  Carry-Over Closeout + Audit Findings + Production Regression
  (W16-0..W16-7 audit trail in frozen tracker
  `documents/active-work/W16-regression-and-audit-closeout.md`).
  Past W8/W11/W12/W13/W14/W15/W16/W17/W18 trackers remain stable-ID
  references only.
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
