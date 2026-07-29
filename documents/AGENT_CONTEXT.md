# Agent Context

`Last Updated: 2026-07-29`

`Last merged weekly: W22 — closed synthetically on the week22 branch, merged to main via PR #31 week22 -> main 2026-05-28 via 1399f82.`

`Latest merged named stream: verdict-provenance-reproducibility (Stream 3 — B5+B6; week label W26) — merged to main via PR #38 (week26 -> main, bfb2d2d) on 2026-07-27. ADR 0017 is Accepted + Implemented; no successor stream is open. Next execution gate: containment safety from documents/active-work/v1-roadmap.md §4. Tracker: documents/active-work/W26-verdict-provenance-reproducibility.md.`

`Sources of truth: documents/REFACTOR_STATUS.md (state) · documents/POST_POC_BACKLOG.md (deferred) · documents/REFACTOR_OPTIMIZATION.md §20 (last weekly plan) · documents/phase.json (weekly pointer + optional active stream; null when none is open).`

Thin routing map for coding agents after `AGENTS.md`. **Stays short.**
Do not copy phase history here; use `REFACTOR_STATUS.md` (slim canonical).

## Source Of Truth

- Current closure state: `REFACTOR_STATUS.md` (slim canonical; full
  history under `archive/status/`).
- Deferred/pull-next work: `POST_POC_BACKLOG.md` (slim canonical;
  full backlog under `archive/backlog/`).
- Phase plans live in `REFACTOR_OPTIMIZATION.md`:
  W8-W13 §11 · W14 §12 · W15 §13 · W16 §14 · W17 §15 · W18 §16 ·
  W19 §17 · W20 §18 · W21 §19 · **W22 §20** (closed
  synthetically and merged to main via PR #31 `week22 -> main` `1399f82`).
  Multi-iter source-of-truth tracker: `active-work/W18-W22-roadmap.md`.
- **W8-W22 closed and merged** (W22 via PR #31 `week22 -> main` `1399f82`).
  Per-phase merge facts (PR # / SHA) live in `REFACTOR_STATUS.md`'s
  `Last Updated:` banner. Past `active-work/W{8,11,12,13,14,15,16,17,18,19,20,21,22}-*.md`
  trackers stay on the read path only for stable IDs referenced by
  code/tests — do not renumber.
- **No named stream is currently open** (`documents/phase.json` ->
  `active_stream: null`). The latest merged stream is
  `verdict-provenance-reproducibility` (Stream 3 / W26), merged via PR #38
  (`bfb2d2d`) on `2026-07-27`; the next execution gate is containment safety
  from `active-work/v1-roadmap.md` §4. Named streams after W22 do not advance
  the weekly `last_merged_weekly` pointer (still W22).
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
| Detection rules, malicious fixtures, ADR security posture | `agent-lanes/security-detection.md` | `detection-design/README.md` for custom rule stream status; ADRs 0002-0005 (only the one that governs the touched boundary); `DETECTION_SEMANTICS.md` slim → `detection/evidence-fields.md` / `detection/health-signals.md` / `detection/rule-lifecycle.md` |
| Static pre-check stage, in-house/Semgrep static rules, decision gate, `rejected_static`, `automation_static_analyzer` | `agent-lanes/static-analysis-pre-check.md` | ADR 0016; `active-work/static-analysis-pre-check-stream.md` |
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
