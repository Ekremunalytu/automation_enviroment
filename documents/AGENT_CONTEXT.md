# Agent Context

`Last Updated: 2026-05-25 (W19 active — Hat-1 closed + live-verified via W19-2-followup-2 d5de9ca on the week19 branch (per user direction 2026-05-21; W11-W18 paterni preserved); W19-0..W19-2 closed; W19-3..W19-6 pending by §17 plan, stable IDs W19-1..W19-5 reserved at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar. Driving signal: Codex live-run validation 2026-05-21 of ms-python.python @ 992ad028f3df reports automation_health.status=degraded + run_quality=low while W19-2 live re-anchor now satisfies unaccounted_dropout == 0 and static W18 final bar (1907/201/220) remains green. W19 Hat-1 closed + live-verified (executor muhasebe bug → unaccounted_dropout); Hat-2 remains active (harness verification gap → declared ≠ verified); Hat-3 (coverage matrix promotion) deferred to W20-W22 per multi-iter roadmap. §17 W19 plan source + §18-§20 W20-W22 multi-iter roadmap (split at W19-0 from the original §17-§20 combined header). W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; final W18 bar tests/architecture/ 201 / make test-security 220 / full suite 1907 passed, 9 skipped, 8 deselected. W18 sub-iter audit trail (frozen, all closed): W18-0 (89d0c9b); W18-1 ADR 0012 Option A1 (acf6cc9 + 73d8a5c); W18-2 heartbeat refactor impl (a9bffb1 + 78ed7cc + b5b64b6 + 306d744); W18-3 lifecycle harness extension tests (92b310d + 32d9905); W18-4 close-out hygiene (3f4f95a); W18-4-followup (e1043e5). W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. Plan REFACTOR_OPTIMIZATION.md §17 (W19) + §18-§20 (W20-W22 multi-iter roadmap), W18 frozen tracker active-work/W18-heartbeat-refactor.md, W19 active tracker active-work/W19-live-run-root-cause.md, roadmap source-of-truth active-work/W18-W22-roadmap.md. W15 closed via PR #22 MERGED 2026-05-18 via 6161472; W14 closed via PR #21 MERGED 2026-05-14 via 4e03c8d)`

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
  `REFACTOR_OPTIMIZATION.md` section 15; W18 plan:
  `REFACTOR_OPTIMIZATION.md` section 16; **W19 plan:
  `REFACTOR_OPTIMIZATION.md` section 17 (active);
  W20-W22 multi-iter roadmap:
  `REFACTOR_OPTIMIZATION.md` sections 18-20** (split at W19-0
  open from the original §17-§20 combined header;
  source-of-truth tracker `active-work/W18-W22-roadmap.md`;
  slim canonical; full text under `archive/plans/`).
- W8-W18 are closed; W13 merged via PR #20 (`772deb3`); W14 merged via
  PR #21 (`4e03c8d`); W15 merged via PR #22 (`6161472`) on
  `2026-05-18`; W16 merged via PR #23 (`1b6d43f`) on `2026-05-18`;
  W17 merged via PR #25 (`bff565d`) on `2026-05-18`;
  W18 merged via PR #26 (`9874e79`) on `2026-05-21`.
  Past W8/W11/W12/W13/W14/W15/W16/W17/W18 trackers remain only for
  stable IDs referenced by code/tests. **Active phase:** W19 —
  Live-Run Kök Neden: Dropout + Harness Verification (**active
  `2026-05-21`** on the `week19` branch per user direction;
  W11-W18 paterni preserved). W19-0..W19-2 are closed:
  W19-0 doc-reconcile (`72712bd` + `086d7a5`), W19-1 RED
  dropout fixture (`6a21cf3` + `fd02ca4`), and W19-2 emit-site fix
  (`89b64da` + `d9c6262`) plus live re-anchor `d5de9ca`
  satisfying `unaccounted_dropout == 0`. W19-3..W19-6 remain
  pending. **W19 scope**: Hat-1 executor muhasebe bug closed +
  live-verified; Hat-2 harness verification gap (W19-3 schema
  landing + W19-4 onDebug* + W19-5 onTerminal/onLM) remains active.
  Hat-3 coverage matrix promotion deferred to W20-W22. **Previous phase:** W18 —
  Heartbeat Refactor (closed `2026-05-21` via PR #26
  `week18 -> main` MERGED via `9874e79`; W18-0..W18-4 sub-iter
  slate + W18-4-followup fully delivered; final W18 bar
  `tests/architecture/` **201 passed**; `make test-security`
  **220 passed**; full suite **1907 passed, 9 skipped,
  8 deselected**). W18 frozen tracker:
  `active-work/W18-heartbeat-refactor.md`; W19 active tracker:
  `active-work/W19-live-run-root-cause.md`; multi-iter roadmap
  source-of-truth: `active-work/W18-W22-roadmap.md`. For
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
