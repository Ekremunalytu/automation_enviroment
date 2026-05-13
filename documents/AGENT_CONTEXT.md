# Agent Context

`Last Updated: 2026-05-13 (W13 closed 2026-05-13 — W13-1..W13-13 all GREEN; W13-1..W13-7 closed — acceptance bar cleared; W13-8/9/10 §11.10 GOAL pulls closed; W13-11 closed`2026-05-12`(6/6 sub-commits) — Path A host-side eager-consume + env var passthrough close-pass for W13-1 H6; W13-12 closed`2026-05-12`(5/5 sub-commits) — fail-closed harness handshake close-pass for W13-1 H6 (`harness_handshake_required: bool` + fail-closed branch + 3-fact AST gate; test bar 1537 → 1539 → 1542 / 112 → 115); W13-13 closed`2026-05-13`(5/5 sub-commits + post-landing) — Path B worker-entry `with_for_update()` snapshot lock close-pass for W13-3 H4 (entry-block lock + lifecycle-helper-not-wrapper deadlock avoidance + 2-fact AST gate + 4 post-landing behavioral pins; test bar 1542 → 1547 → 1551 / 115 → 117); close-out PR #20 (week13 → main) MERGED 2026-05-13 via 772deb3 (close-gate cleared pre-merge))`

Thin routing map for coding agents after `AGENTS.md`. **Stays short.**
Do not copy phase history here; use `REFACTOR_STATUS.md` (slim canonical).

## Source Of Truth

- Current closure state: `REFACTOR_STATUS.md` (slim canonical; full
  history under `archive/status/`).
- Deferred/pull-next work: `POST_POC_BACKLOG.md` (slim canonical;
  full backlog under `archive/backlog/`).
- W8-W13 plan: `REFACTOR_OPTIMIZATION.md` section 11 (slim canonical;
  full text under `archive/plans/`).
- W8-W12 are closed; W11 merged via PR #14; W12 merged via PR #18
  (`33a0852`). Past W8/W11/W12 trackers remain only for stable IDs
  referenced by code/tests. **Active phase:** W13 — Test Expansion +
  Observability (`REFACTOR_OPTIMIZATION.md` §11.10). Active tracker:
  `active-work/W13-test-expansion-observability.md`. For current
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
