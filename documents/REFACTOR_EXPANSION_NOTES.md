# Refactor Expansion Notes

`Last Updated: 2026-04-15`

These notes intentionally do not define a binding delivery plan. They exist so
the heavier follow-on work is visible without overcommitting before Weeks 1-4
are complete.

## Why These Items Are Deferred

- Week 1-4 already cover the highest-value boundary cleanup.
- The remaining topics touch runtime trust boundaries, container ergonomics, or
  reproducibility and are easier to sequence once the contract/planner/job
  layers are cleaner.
- Deferring them reduces the risk of mixing architectural cleanup with runtime
  rewiring in the same cycle.

## Reopen Conditions

Turn one of these notes into a committed plan only after:

- Week 4 is implemented and stable
- the baseline fixtures still reflect reality
- fast test lanes are healthy
- there is a concrete product or operability reason to spend the extra risk
  budget

## Candidate Expansion Topics

### Executor Reporting Semantics Alignment

- align layered-pass execution reporting so `stimulus_passes`,
  `event_attempts`, `scenario_traces`, and `summary.scenarios_run` do not
  describe overlapping runtime facts with different semantics
- make layered stimulus execution emit canonical scenario lifecycle records
  whenever it invokes scenario helpers directly instead of routing through the
  higher-level scenario runner
- keep requested scenarios from the trigger plan separate from scenarios
  actually executed as automation flows
- keep per-event attempts and per-pass execution truth separate from
  higher-level scenario summaries
- treat this as a post-Week-4 runtime observability and reporting correctness
  item unless it starts blocking interpretation of baseline scan quality
- the current layered executor path is operationally correct enough to keep the
  Week 1-4 boundary refactor moving
- the most reliable execution truth is already present in `stimulus_passes`
  plus `event_attempts`
- the remaining gap is consistency of reporting semantics rather than a core
  planner or contract failure
- a fresh post-Week-2 `ms-python.python` scan produced a contract-valid
  activation report while still showing `summary.scenarios_run` entries that
  were not mirrored in `scenario_traces`; keep treating this as deferred
  reporting-semantics cleanup unless it starts confusing scan review

### Executor Control Boundary

- replace API-side Docker host control with a narrower executor control
  interface
- keep Docker sandbox isolation, but remove broad daemon control from the API
  path

### Stack-Scoped Compose Runtime

- remove fixed `container_name` assumptions
- make ports and state roots stack-scoped from env alone
- improve multi-worktree and parallel AI ergonomics

### Deterministic Executor Runtime

- pin VS Code/runtime inputs more tightly
- pin Playwright/browser behavior more explicitly
- reduce “same commit, different runner” drift

### AI-Safe Ownership Map

- define package ownership boundaries after planner/control-plane extraction
- publish safe task lanes for contracts, planner, engine, UI adapters, and
  storage

### Expanded Smoke Matrix

- keep `ms-python.python` as the primary acceptance baseline
- add at least one additional extension fixture after the core boundaries are
  stable

## Operating Rule

Do not treat these notes as an implied Week 5 commitment. Promote them into the
execution plan only when Week 4 is done and the repo is ready for the extra
change surface.
