# Documents Guide

`Last Updated: 2026-06-04 — W22 remains the last merged weekly close-out (PR #31 week22 -> main 1399f82). Active stream: security-development on branch security-development; tracker: detection-design/README.md.`

This folder is split into a small canonical core, specialized reference docs,
and a frozen archive. **Do not preload the entire folder.** Open subsystem
docs only when the lane doc says so.

Current status: [`REFACTOR_STATUS.md`](REFACTOR_STATUS.md). Deferrals:
[`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md). W8-W13 plan:
[`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md) §11; W14-W18 plans:
§12-§16; W19-W22 plans: §17-§20. Last merged weekly: W22 (PR #31,
1399f82). Active stream tracker:
[`detection-design/README.md`](detection-design/README.md).
W18-W22 roadmap:
[`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md).
Closed stable-ID trackers live under [`active-work/`](active-work/).

Security posture is fixed by ADRs 0002-0005 plus ADRs 0007-0012. ADR 0007
loopback defaults are pinned by
[`tests/architecture/test_default_bindings.py`](../tests/architecture/test_default_bindings.py);
status is owned by [`REFACTOR_STATUS.md`](REFACTOR_STATUS.md).

## Read First

For most code changes, in order:

1. [`AGENT_CONTEXT.md`](AGENT_CONTEXT.md)
   - choose the task lane and avoid preloading the whole doc set
2. `agent-lanes/<matching-lane>.md`
   - source files, invariants, tests, and shortcuts for the touched area

The lane doc decides whether you need any of the slim canonical
subsystem docs below. **Default preload stops at the lane doc.**

## Load Only If The Task Needs It

- [`ARCHITECTURE.md`](ARCHITECTURE.md): new service, boundary, or diagram.
- [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md): new top-level package or
  ambiguous placement.
- [`TESTING.md`](TESTING.md): new test layer, fixture pattern, or lane question.
- [`DETECTION_SEMANTICS.md`](DETECTION_SEMANTICS.md): report JSON, UI report
  adapters, health, signal summary, or evidence semantics.
- [`EXECUTOR_PLAYWRIGHT.md`](EXECUTOR_PLAYWRIGHT.md): executor, container,
  Playwright, or executor-driving API behavior.
- [`DEMO_SCENARIO.md`](DEMO_SCENARIO.md): A1 canary playbook or
  `make demo-canary`.
- [`VSCODE_API_COVERAGE_AUDIT.md`](VSCODE_API_COVERAGE_AUDIT.md): trigger
  planning or official-vs-heuristic coverage.
- `docs/risks.md`: accepted tradeoff.

## Operational Runbooks

Open [`runbooks/README.md`](runbooks/README.md) or a specific runbook only
when that failure mode is in flight.

## Planning, Audit, And ADRs

Short and intentionally not on the default read path.

- [`DEVELOPMENT_PRIORITIES.md`](DEVELOPMENT_PRIORITIES.md),
  [`PIPELINE_ROADMAP.md`](PIPELINE_ROADMAP.md), `automation_todo.md`,
  [`ARCHITECTURE_AUDIT.md`](ARCHITECTURE_AUDIT.md), and [`review.md`](review.md)
  stay off the default read path.
- Historical Week 1-4 planning snapshots
  [`REFACTOR_EXECUTION_PLAN.md`](REFACTOR_EXECUTION_PLAN.md) and
  [`REFACTOR_EXPANSION_NOTES.md`](REFACTOR_EXPANSION_NOTES.md) are
  read-only/off-path unless retracing that earlier plan.
- ADRs (`adrs/0001`-`0012`) — binding decisions on appliance model,
  threat model, detection taxonomy, malicious-fixture policy,
  packages charter, local network binding, and container package-mode
  invocation. Read the ADR only when the task touches the boundary it governs.

## Active Work And Archive

- [`active-work/`](active-work/) — slim canonical files for currently
  in-flight work tracking. Items have **stable IDs**; code comments and
  tests reference them. Do not renumber or restructure without
  updating inbound code references.
- [`archive/`](archive/) — frozen historical content
  (`plans/`, `status/`, `backlog/`, `reviews/`). **Off the default
  read path.** Open only when a slim canonical points there or the
  user explicitly requests historical detail.

## Context-Safe Rule

- Start with one canonical doc, not all of them.
- Open a specialized doc only when the task touches that subsystem and
  the lane doc has pointed to it.
- Prefer code and tests over docs when any statement becomes ambiguous.
- Token budget targets and archive discipline are owned by
  [`agent-lanes/docs-maintenance.md`](agent-lanes/docs-maintenance.md).
