# Agent Context

`Last Updated: 2026-05-17 (W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W15 active on week15 branch cut from main HEAD 7cc2921 on 2026-05-14; W15-1/W15-2/W15-3/W15-4/W15-5/W15-6 closed (M10/M12/U8/U1/U2/U3/U6/I2/I4/U10/U11); W15-5 closed 2026-05-17 via 43d6438 — quick fixes bundle (I2 + I4); W15-6 closed 2026-05-17 via be52520 — ADR 0011 unauthenticated catalog endpoints posture Accepted (Option A; Proposed at e41722e); W15-1 typing hotfix via 976dc96; W15-7 pending — compose image SHA pin + GH action trivy version pin + final preamble refresh; W15 mid-iter hygiene 2026-05-16: doc-preamble consistency arch gate + 3 new audit findings in POST_POC_BACKLOG)`

Thin routing map for coding agents after `AGENTS.md`. **Stays short.**
Do not copy phase history here; use `REFACTOR_STATUS.md` (slim canonical).

## Source Of Truth

- Current closure state: `REFACTOR_STATUS.md` (slim canonical; full
  history under `archive/status/`).
- Deferred/pull-next work: `POST_POC_BACKLOG.md` (slim canonical;
  full backlog under `archive/backlog/`).
- W8-W13 plan: `REFACTOR_OPTIMIZATION.md` section 11; W14 plan:
  `REFACTOR_OPTIMIZATION.md` section 12 (slim canonical; full text under
  `archive/plans/`).
- W8-W14 are closed; W13 merged via PR #20 (`772deb3`); W14 merged via
  PR #21 (`4e03c8d`). Past W8/W11/W12/W13/W14 trackers remain only for
  stable IDs referenced by code/tests. **Active phase:** W15 — Codex
  U-class Close-Out + UI Bounds + Posture (W15-1..W15-4 closed;
  W15-5..W15-7 pending). Active tracker:
  `active-work/W15-codex-uclass-bounds-posture.md`. For current closure
  state always defer to `REFACTOR_STATUS.md`.
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
