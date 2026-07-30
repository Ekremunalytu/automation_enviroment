# Agent Context

`Last Updated: 2026-07-30`

`Last merged weekly: W22 — closed synthetically on the week22 branch, merged to main via PR #31 week22 -> main 2026-05-28 via 1399f82.`

`Latest named stream: verdict-provenance-reproducibility (W26), merged via PR #38 at bfb2d2d; none is open. Next gate: containment safety in active-work/v1-roadmap.md §4.`

Routing map after `AGENTS.md`. State lives in `phase.json` and
`REFACTOR_STATUS.md`; deferred work in `POST_POC_BACKLOG.md`. Do not copy their
history here.

## Task Decision Tree

Open one matching lane. Load third-column docs only on the stated trigger.

| If the task touches... | Open this lane first | Then open only if the trigger matches |
|---|---|---|
| FastAPI config, DB, schemas, CRUD, migrations | `agent-lanes/platform-storage.md` | `ARCHITECTURE.md` (new boundary/dependency line); `PROJECT_STRUCTURE.md` (new top-level package); `TESTING.md` (new test layer / fixture pattern) |
| Marketplace search/download/analyze jobs, trigger planning | `agent-lanes/marketplace-analysis.md` | `PIPELINE_ROADMAP.md` (staged pipeline direction); `VSCODE_API_COVERAGE_AUDIT.md` (capability/coverage question); `testing/marketplace-tests.md` |
| Docker executor, Playwright, harness, runtime capture | `agent-lanes/executor-runtime.md` | `EXECUTOR_PLAYWRIGHT.md` slim → `executor/host-wrapper.md` / `executor/playwright-flow.md` / `executor/runtime-capture.md` (whichever sub-area you touch); relevant runbook |
| Detection rules, malicious fixtures, ADR security posture | `agent-lanes/security-detection.md` | `detection-design/README.md` for custom rule stream status; ADRs 0002-0005 (only the one that governs the touched boundary); `DETECTION_SEMANTICS.md` slim → `detection/evidence-fields.md` / `detection/health-signals.md` / `detection/rule-lifecycle.md` |
| Static pre-check stage, in-house/Semgrep static rules, decision gate, `rejected_static`, `automation_static_analyzer` | `agent-lanes/static-analysis-pre-check.md` | ADR 0016; `active-work/static-analysis-pre-check-stream.md` |
| React/Vite UI or generated TS contracts | `agent-lanes/ui.md` | `ui/README.md`, UI tests |
| Documentation drift, README, runbooks, ADR text | `agent-lanes/docs-maintenance.md` | `documents/README.md`; current code/tests; archive only when retracing why a thing changed |
| Historical stable IDs referenced by code/tests | lane for the subsystem | matching `active-work/W*.md`; do not renumber IDs |

If a task touches a slim canonical's domain without matching a split trigger,
open the slim canonical itself, not its splits.
