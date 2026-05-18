# Agent Context

`Last Updated: 2026-05-18 (W17 active — authoring on week17 branch per user direction; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. W17-0 doc-reconcile in progress; W17-1..W17-6 reserved: attribution-count-parity closeout (W16-3 carry-over), lifecycle harness scaffold (enabler), heartbeat-sandbox-reset-off-thread (W16-5 carry-over), heartbeat-refactor (W16-5 carry-over), hygiene cleanup batch, close-out hygiene + §15 self-stamp. Plan REFACTOR_OPTIMIZATION.md §15, active tracker active-work/W17-carryover-and-lifecycle-harness.md. Entry gate post-merge bar: tests/architecture/ 199 passed; make test-security 220 passed; full suite 1893 passed, 9 skipped. W16-0..W16-7 sub-iter slate complete: W16-1 scenario-accountant emit-site fix (01f910a); W16-2 analysis-job worker-entry CRUD ownership (9d6d110); W16-3 report-finalize null-leakage half (fa430f2; attribution-count-parity split to W17); W16-4 health-reconciliation responsibility split (304b99f); W16-5 simulation-progress-cancel scope reduction (1 rejected, 2 deferred to W17, e21a05c); W16-6 hygiene splits + Alembic fresh-DB fixture (d40bb01); W16-7 close-out hygiene (8bf3c6b) + post-PR unaccounted_dropout surface pin (78f080e). Frozen tracker active-work/W16-regression-and-audit-closeout.md. W15 closed via PR #22 MERGED 2026-05-18 via 6161472; W14 closed via PR #21 MERGED 2026-05-14 via 4e03c8d)`

Thin routing map for coding agents after `AGENTS.md`. **Stays short.**
Do not copy phase history here; use `REFACTOR_STATUS.md` (slim canonical).

## Source Of Truth

- Current closure state: `REFACTOR_STATUS.md` (slim canonical; full
  history under `archive/status/`).
- Deferred/pull-next work: `POST_POC_BACKLOG.md` (slim canonical;
  full backlog under `archive/backlog/`).
- W8-W13 plan: `REFACTOR_OPTIMIZATION.md` section 11; W14 plan:
  `REFACTOR_OPTIMIZATION.md` section 12; W15 plan:
  `REFACTOR_OPTIMIZATION.md` section 13; W16 plan:
  `REFACTOR_OPTIMIZATION.md` section 14; **W17 plan:
  `REFACTOR_OPTIMIZATION.md` section 15** (slim canonical; full text
  under `archive/plans/`).
- W8-W16 are closed; W13 merged via PR #20 (`772deb3`); W14 merged via
  PR #21 (`4e03c8d`); W15 merged via PR #22 (`6161472`) on
  `2026-05-18`; **W16 merged via PR #23 (`1b6d43f`) on `2026-05-18`**.
  Past W8/W11/W12/W13/W14/W15/W16 trackers remain only for stable IDs
  referenced by code/tests. **Active phase:** W17 — Carry-Over
  Closeout + Lifecycle Harness Yatırımı + Hygiene Sweep (active
  `2026-05-18` **on the `week17` branch per user direction (W11-W16
  paterni preserved 2026-05-18)**; sub-iter commits land on `week17`
  and the close-out is merged into `main` via a `week17 -> main` PR).
  Active tracker:
  `active-work/W17-carryover-and-lifecycle-harness.md`. For current
  closure state always defer to `REFACTOR_STATUS.md`.
- Architecture: `ARCHITECTURE.md` (slim) + `architecture/` splits.
- Placement rules: `PROJECT_STRUCTURE.md` (slim) + `structure/` splits.
- Test lanes: `TESTING.md` (slim) + `testing/` splits.

## Task Decision Tree

Open the matching lane first; open the third-column docs only on the listed
trigger.

| If the task touches... | Open this lane first | Then open only if the trigger matches |
|---|---|---|
| FastAPI config, DB, schemas, CRUD, migrations | `agent-lanes/platform-storage.md` | `ARCHITECTURE.md` (new boundary/dependency line); `PROJECT_STRUCTURE.md` (new top-level package); `TESTING.md` (new test layer / fixture pattern) |
| Marketplace search/download/analyze jobs, trigger planning | `agent-lanes/marketplace-analysis.md` | `PIPELINE_ROADMAP.md` (staged pipeline direction); `VSCODE_API_COVERAGE_AUDIT.md` (capability/coverage question); `testing/marketplace-tests.md` |
| Docker executor, Playwright, harness, runtime capture | `agent-lanes/executor-runtime.md` | `EXECUTOR_PLAYWRIGHT.md` slim → `executor/host-wrapper.md` / `executor/playwright-flow.md` / `executor/runtime-capture.md` (whichever sub-area you touch); relevant runbook |
| Detection rules, malicious fixtures, ADR security posture | `agent-lanes/security-detection.md` | ADRs 0002-0005 (only the one that governs the touched boundary); `DETECTION_SEMANTICS.md` slim → `detection/evidence-fields.md` / `detection/health-signals.md` / `detection/rule-lifecycle.md` |
| React/Vite UI or generated TS contracts | `agent-lanes/ui.md` | `ui/README.md`, UI tests |
| Documentation drift, README, runbooks, ADR text | `agent-lanes/docs-maintenance.md` | `documents/README.md`; current code/tests; archive only when retracing why a thing changed |
| W8/W9 closure history (stable IDs in code/tests) | (lane above) | `active-work/W8-security.md` for W8-1..W8-9 IDs; `REFACTOR_STATUS.md` for W9 closure evidence |

If a task touches a slim canonical's domain without matching a split trigger,
open the slim canonical itself, not its splits.

## Core Paths

- Entry point: `main.py`.
- Backend: `appcore/`, `workflows/`, `executor/`.
- Framework-agnostic packages: `packages/`.
- Frontend: `ui/`.
- Tests: `tests/`.
- Docs: `documents/`; archive is off default path.

## Minimal Rules Reminder

- DB writes go through `appcore/storage/crud.py`.
- Pydantic validation happens before insert.
- Sandbox execution stays Docker-isolated.
- `packages/` remains framework-agnostic.
- Detection rules consume contracts only.
- Matching tests should be opened early.
