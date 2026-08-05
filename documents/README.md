# Documents Guide

`Last Updated: 2026-08-05 — Last merged weekly: W22 (PR #31 week22 -> main 1399f82).`

`Active named stream: static-analysis-artifact-precision; the SMF foundation plus SAP-0..SAP-4 baseline merged via PR #40, while SAP-5 and SAP-6 are branch-published, implementation complete, and unmerged; tracker: active-work/static-analysis-artifact-precision.md.`

Do not preload this folder. After `AGENTS.md`, use
[`AGENT_CONTEXT.md`](AGENT_CONTEXT.md) to choose one
[`agent-lanes/`](agent-lanes/) file. The lane decides what else to read.

## Sources Of Truth

- State: [`REFACTOR_STATUS.md`](REFACTOR_STATUS.md)
- Machine state: [`phase.json`](phase.json)
- Deferred work: [`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md)
- Last weekly plan: [`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md) §20
- Human entrypoint: [`human-guide.md`](human-guide.md)

## Load On Demand

- Architecture/boundaries: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Placement: [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md)
- Tests: [`TESTING.md`](TESTING.md)
- Detection/report semantics:
  [`DETECTION_SEMANTICS.md`](DETECTION_SEMANTICS.md)
- Executor/Playwright: [`EXECUTOR_PLAYWRIGHT.md`](EXECUTOR_PLAYWRIGHT.md)
- Operations: [`runbooks/README.md`](runbooks/README.md)
- Decisions: [`adrs/`](adrs/)
- Current/frozen trackers: [`active-work/`](active-work/) — stable IDs must not
  be renumbered
- Historical snapshots: [`archive/`](archive/) — off the default read path

Prefer code/tests when a document is ambiguous. Context budgets and archive
rules live in
[`agent-lanes/docs-maintenance.md`](agent-lanes/docs-maintenance.md).
