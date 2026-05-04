# Agent Context

`Last Updated: 2026-05-04`

Thin routing map for coding agents after `AGENTS.md`. **Stays short.**
Do not copy phase history here; use `REFACTOR_STATUS.md` (slim canonical).

## Source Of Truth

- Current closure state: `REFACTOR_STATUS.md` (slim canonical; full
  history under `archive/status/`).
- Deferred/pull-next work: `POST_POC_BACKLOG.md` (slim canonical;
  full backlog under `archive/backlog/`).
- W8-W13 plan: `REFACTOR_OPTIMIZATION.md` section 11 (slim canonical;
  full text under `archive/plans/`).
- **Past W8 work tracker (closed `2026-04-29`):**
  `active-work/W8-security.md` (stable IDs W8-1..W8-9; code/tests
  still reference items by ID — keep IDs stable when reorganizing).
  W9 closed `2026-05-04`; W10 closed `2026-05-04` via PR #11. **Active
  phase:** W11 monitor lifecycle split — tracker at
  `active-work/W11-monitor-lifecycle.md` (stable IDs W11-1..W11-8);
  entry gate met `2026-05-04` after `[FOLLOWUP w11-precursor-tests]`
  safety net landed. For current closure state always defer to
  `REFACTOR_STATUS.md`.
- Architecture: `ARCHITECTURE.md` (slim) + `architecture/` splits.
- Placement rules: `PROJECT_STRUCTURE.md` (slim) + `structure/` splits.
- Test lanes: `TESTING.md` (slim) + `testing/` splits.

## Current Snapshot

For current phase state, see [`REFACTOR_STATUS.md`](REFACTOR_STATUS.md).

## Task Decision Tree

Each "open if needed" entry names the **trigger** that justifies
opening that doc. If the trigger does not match, do not open it.

| If the task touches... | Open this lane first | Then open only if the trigger matches |
|---|---|---|
| FastAPI config, DB, schemas, CRUD, migrations | `agent-lanes/platform-storage.md` | `ARCHITECTURE.md` (new boundary/dependency line); `PROJECT_STRUCTURE.md` (new top-level package); `TESTING.md` (new test layer / fixture pattern) |
| Marketplace search/download/analyze jobs, trigger planning | `agent-lanes/marketplace-analysis.md` | `PIPELINE_ROADMAP.md` (staged pipeline direction); `VSCODE_API_COVERAGE_AUDIT.md` (capability/coverage question); `testing/marketplace-tests.md` |
| Docker executor, Playwright, harness, runtime capture | `agent-lanes/executor-runtime.md` | `EXECUTOR_PLAYWRIGHT.md` slim → `executor/host-wrapper.md` / `executor/playwright-flow.md` / `executor/runtime-capture.md` (whichever sub-area you touch); relevant runbook |
| Detection rules, malicious fixtures, ADR security posture | `agent-lanes/security-detection.md` | ADRs 0002-0005 (only the one that governs the touched boundary); `DETECTION_SEMANTICS.md` slim → `detection/evidence-fields.md` / `detection/health-signals.md` / `detection/rule-lifecycle.md` |
| React/Vite UI or generated TS contracts | `agent-lanes/ui.md` | `ui/README.md`, UI tests |
| Documentation drift, README, runbooks, ADR text | `agent-lanes/docs-maintenance.md` | `documents/README.md`; current code/tests; archive only when retracing why a thing changed |
| W8/W9 closure history (stable IDs in code/tests) | (lane above) | `active-work/W8-security.md` for W8-1..W8-9 IDs; `REFACTOR_STATUS.md` for W9 closure evidence |

If a task touches a slim canonical's domain but does not match any of
the listed triggers, open the slim canonical itself, **not** its
splits. Splits are only opened on a trigger.

## Core Paths

- Entry point: `main.py`.
- Backend: `appcore/`, `workflows/`, `executor/`.
- Framework-agnostic packages: `packages/`.
- Frontend: `ui/`.
- Tests: `tests/`.
- Docs: `documents/`, with lane docs under `documents/agent-lanes/`,
  active work under `documents/active-work/`, frozen history under
  `documents/archive/` (off default path).

## Minimal Rules Reminder

- DB writes go through `appcore/storage/crud.py`.
- Pydantic validation happens before insert.
- Sandbox execution stays Docker-isolated.
- `packages/` remains framework-agnostic.
- Detection rules consume contracts only.
- Matching tests should be opened early.

## Useful Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make exec-run`
- `make sim-target TARGET=publisher.name`
- `make demo-canary`
