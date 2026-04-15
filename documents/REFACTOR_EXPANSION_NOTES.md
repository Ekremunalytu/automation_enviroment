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

- Week 4A and Week 4B are implemented and stable
- the baseline fixtures still reflect reality
- fast test lanes are healthy
- there is a concrete product or operability reason to spend the extra risk
  budget

## Promoted Into The Execution Plan

### Executor Reporting Semantics Alignment

- this topic has been promoted into `Week 4A` of
  `REFACTOR_EXECUTION_PLAN.md`
- Week 4A now owns layered-pass reporting alignment, runtime verification
  hardening for degraded and attempted-only runs, and chat/tooling verification
  closure for `onChatParticipant` and `onLanguageModelTool`
- keep this note only as historical context for why Week 4A exists; do not
  treat it as a separate Week 5+ candidate unless it is explicitly descoped
  from the execution plan

## Candidate Expansion Topics

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

Do not treat these remaining notes as an implied Week 5 commitment. Promote
them into the execution plan only when Week 4A and Week 4B are done and the
repo is ready for the extra change surface.
