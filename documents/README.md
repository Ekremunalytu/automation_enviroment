# Documents Guide

`Last Updated: 2026-05-05`

This folder is split into a small canonical core, a few specialized
reference docs (each as a slim canonical + subdir splits), and a frozen
archive. **Do not preload the entire folder.** This README does not
itself send agents into big canonical docs by default — subsystem docs
are opened only when a lane doc says so.

Current status: [`REFACTOR_STATUS.md`](REFACTOR_STATUS.md) (slim).
Deferrals: [`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md) (slim).
W0-W7 history: [`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md) §10.
W8-W13 plan: [`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md) §11.
**Active phase:** W11 monitor lifecycle split — tracker at
[`active-work/W11-monitor-lifecycle.md`](active-work/W11-monitor-lifecycle.md).
**Past W8 tracker (closed `2026-04-29`):**
[`active-work/W8-security.md`](active-work/W8-security.md). Historical
Week 1-4 execution plan:
[`REFACTOR_EXECUTION_PLAN.md`](REFACTOR_EXECUTION_PLAN.md). Non-binding
deferred ideas:
[`REFACTOR_EXPANSION_NOTES.md`](REFACTOR_EXPANSION_NOTES.md).

Security posture (threat model, detection taxonomy, malicious fixture
policy, package-boundary charter, local network binding) is fixed by
ADRs 0002-0005 plus ADR 0007. ADR 0007 is **Accepted and implemented**
`2026-04-29` via W8-7 — loopback defaults plus `EXTRACE_ALLOW_LAN`
opt-in live in `appcore/api/config.py`, `docker-compose.yml`, and the
[`tests/architecture/test_default_bindings.py`](../tests/architecture/test_default_bindings.py)
regression matrix; status owned by
[`REFACTOR_STATUS.md`](REFACTOR_STATUS.md).

## Read First

For most code changes, in order:

1. [`AGENT_CONTEXT.md`](AGENT_CONTEXT.md)
   - choose the task lane and avoid preloading the whole doc set
2. `agent-lanes/<matching-lane>.md`
   - source files, invariants, tests, and shortcuts for the touched area

The lane doc decides whether you need any of the slim canonical
subsystem docs below. **Default preload stops at the lane doc.**

## Load Only If The Task Needs It

Each entry names the **trigger** that justifies opening it. If the lane
doc has not pointed at it and the trigger does not match, leave it
closed.

- [`ARCHITECTURE.md`](ARCHITECTURE.md)
  - **trigger:** new service/component, new boundary line, drawing a
    high-level diagram. Slim canonical; detail under
    [`architecture/`](architecture/).
- [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md)
  - **trigger:** new top-level package, ambiguous code placement.
    Slim canonical; detail under [`structure/`](structure/).
- [`TESTING.md`](TESTING.md)
  - **trigger:** new test layer / fixture pattern, lane composition
    question. Slim canonical; detail under [`testing/`](testing/).
- [`DETECTION_SEMANTICS.md`](DETECTION_SEMANTICS.md)
  - **trigger:** changing `ActivationReport` JSON, UI report adapters,
    health, signal summary, or evidence semantics. Slim canonical;
    detail under [`detection/`](detection/).
- [`EXECUTOR_PLAYWRIGHT.md`](EXECUTOR_PLAYWRIGHT.md)
  - **trigger:** changing executor / container / Playwright behavior or
    the API integration points that drive it. Slim canonical; detail
    under [`executor/`](executor/).
- [`DEMO_SCENARIO.md`](DEMO_SCENARIO.md)
  - **trigger:** updating the A1 canary playbook or
    `make demo-canary` lane.
- [`VSCODE_API_COVERAGE_AUDIT.md`](VSCODE_API_COVERAGE_AUDIT.md)
  - **trigger:** trigger planning, capability support, or
    official-vs-heuristic coverage question.
- `docs/risks.md`
  - **trigger:** documenting an accepted tradeoff.

## Operational Runbooks

Open one of these when a specific failure mode is in flight; do not
preload.

- [`runbooks/README.md`](runbooks/README.md) — index + shape.
- [`runbooks/analysis-job-stuck.md`](runbooks/analysis-job-stuck.md)
- [`runbooks/fatal-ui-crash.md`](runbooks/fatal-ui-crash.md)
- [`runbooks/scan-between-restart-failure.md`](runbooks/scan-between-restart-failure.md)
- [`runbooks/live-capture-regression.md`](runbooks/live-capture-regression.md)

## Planning, Audit, And ADRs

Short and intentionally not on the default read path.

- [`DEVELOPMENT_PRIORITIES.md`](DEVELOPMENT_PRIORITIES.md) — current
  product and engineering priorities.
- [`PIPELINE_ROADMAP.md`](PIPELINE_ROADMAP.md) — staged pipeline
  direction.
- `automation_todo.md` — thin pull-next snapshot pointing at
  `POST_POC_BACKLOG.md`.
- [`ARCHITECTURE_AUDIT.md`](ARCHITECTURE_AUDIT.md) — concise
  architecture health summary.
- [`review.md`](review.md) — fast review order for risky changes.
- ADRs (`adrs/0001`-`0007`) — binding decisions on appliance model,
  threat model, detection taxonomy, malicious-fixture policy,
  packages charter, and local network binding. Read the ADR only when
  the task touches the boundary it governs.

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
