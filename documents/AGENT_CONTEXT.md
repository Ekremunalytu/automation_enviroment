# Agent Context

`Last Updated: 2026-05-21 (W18 active — phase work complete; W18-0..W18-4 sub-iter slate landed on the week18 branch (per user direction 2026-05-21; W11-W17 paterni preserved); close-out PR week18 -> main not yet opened (branch is pushed). §16 W18 plan source + §17-§20 W19-W22 multi-iter roadmap (split at W18-4 close-out). W18 sub-iter audit trail: W18-0 doc-reconcile (89d0c9b); W18-1 ADR 0012 Option A1 (acf6cc9 + 73d8a5c); W18-2 heartbeat refactor impl (a9bffb1 + 78ed7cc + b5b64b6 + 306d744 with pre-commit install); W18-3 lifecycle harness extension tests (92b310d + 32d9905); W18-4 close-out hygiene this commit. Final W18 bar: tests/architecture/ 201 passed (W17 final 200 + W18-0 README phase-pointer arch gate W17->W18 transition); make test-security 220 passed (unchanged); full suite 1903 passed, 9 skipped, 8 deselected (W17 final 1899 + W18-0 +1 + W18-3 +3). W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. W17-0..W17-7 sub-iter slate complete (frozen): W17-0 doc-reconcile (4508c2e); W17-1 attribution-count-parity (8c26d02 + 0a8f59e); W17-2 lifecycle harness scaffold (ff98235 + 44f96c5); W17-3 + W17-4 scope-reduced (c4c0646 DESIGN-NEEDED — closed via W18-1 ADR + W18-2 implementation); W17-5 hygiene single-item (394d40d + 0cbe1d0); W17-6 close-out (21f7c68); W17-7 post-slate hotfix batch (bf983eb + fc88678 + 326dac8 + 51dba29); W17-7-followup post-PR doc-truth alignment (dab4679). Plan REFACTOR_OPTIMIZATION.md §16 (W18) + §17-§20 (W19-W22 multi-iter roadmap), frozen tracker active-work/W18-heartbeat-refactor.md, roadmap source-of-truth active-work/W18-W22-roadmap.md. Final W17 bar (unchanged): tests/architecture/ 200 passed; make test-security 220 passed; full suite 1899 passed, 9 skipped, 4 deselected (+6 from W16 final 1893). W16-0..W16-7 sub-iter slate complete: W16-1 scenario-accountant emit-site fix (01f910a); W16-2 analysis-job worker-entry CRUD ownership (9d6d110); W16-3 report-finalize null-leakage half (fa430f2; attribution-count-parity split to W17); W16-4 health-reconciliation responsibility split (304b99f); W16-5 simulation-progress-cancel scope reduction (1 rejected, 2 deferred to W17, e21a05c); W16-6 hygiene splits + Alembic fresh-DB fixture (d40bb01); W16-7 close-out hygiene (8bf3c6b) + post-PR unaccounted_dropout surface pin (78f080e). Frozen tracker active-work/W16-regression-and-audit-closeout.md. W15 closed via PR #22 MERGED 2026-05-18 via 6161472; W14 closed via PR #21 MERGED 2026-05-14 via 4e03c8d)`

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
  `REFACTOR_OPTIMIZATION.md` section 14; W17 plan:
  `REFACTOR_OPTIMIZATION.md` section 15; **W18 plan:
  `REFACTOR_OPTIMIZATION.md` section 16; W19-W22 multi-iter roadmap:
  `REFACTOR_OPTIMIZATION.md` sections 17-20** (split out at W18-4
  close-out; source-of-truth tracker
  `active-work/W18-W22-roadmap.md`; slim canonical; full text under
  `archive/plans/`).
- W8-W17 are closed; W13 merged via PR #20 (`772deb3`); W14 merged via
  PR #21 (`4e03c8d`); W15 merged via PR #22 (`6161472`) on
  `2026-05-18`; W16 merged via PR #23 (`1b6d43f`) on `2026-05-18`;
  **W17 merged via PR #25 (`bff565d`) on `2026-05-18`**.
  Past W8/W11/W12/W13/W14/W15/W16/W17/W18 trackers remain only for
  stable IDs referenced by code/tests. **Active phase:** W18 —
  Heartbeat Refactor (**phase work complete 2026-05-21** on the
  `week18` branch per user direction (W11-W17 paterni preserved
  2026-05-21); close-out PR `week18 -> main` not yet opened (branch
  is pushed); sub-iter slate W18-0..W18-4 fully delivered: W18-0
  doc-reconcile (`89d0c9b`) + W18-1 ADR 0012 Option A1 accepted
  (`acf6cc9` + `73d8a5c` followup) + W18-2 heartbeat refactor
  implementation (`a9bffb1` + `78ed7cc` + `b5b64b6` + `306d744`) +
  W18-3 lifecycle harness extension tests (`92b310d` + `32d9905`) +
  W18-4 close-out hygiene this commit). Final W18 bar:
  `tests/architecture/` **201 passed**; `make test-security`
  **220 passed**; full suite **1903 passed, 9 skipped, 8 deselected**.
  Frozen tracker: `active-work/W18-heartbeat-refactor.md`; multi-iter
  roadmap source-of-truth: `active-work/W18-W22-roadmap.md`. For
  current closure state always defer to `REFACTOR_STATUS.md`.
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
