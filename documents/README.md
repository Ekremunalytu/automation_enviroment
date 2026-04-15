# Documents Guide

`Last Updated: 2026-04-15`

This folder is intentionally split into a small canonical core plus a few
specialized reference docs. Do not preload the entire folder unless the task
really spans multiple subsystems.

If an older note conflicts with the current refactor direction, prefer
`REFACTOR_EXECUTION_PLAN.md`. Use `REFACTOR_EXPANSION_NOTES.md` only as a
deferred reference, not as a binding delivery plan.

## Agent Shortcut

- `AGENT_CONTEXT.md`
  - one-page quickstart for coding agents after reading root `AGENTS.md`

## Read First

Read these in order for most code changes:

1. `ARCHITECTURE.md`
   - system shape, boundaries, request flows
2. `PROJECT_STRUCTURE.md`
   - where new code should live
3. `TESTING.md`
   - test layout, fixtures, and commands

## Load Only If The Task Needs It

- `EXECUTOR_PLAYWRIGHT.md`
  - executor container, host wrapper, Playwright runtime
- `DETECTION_SEMANTICS.md`
  - report JSON fields, health/verdict semantics, evidence interpretation
- `VSCODE_API_COVERAGE_AUDIT.md`
  - trigger planning, capability support, official vs heuristic coverage
- `docs/risks.md`
  - current risk register and accepted tradeoffs

## Planning And Review Docs

These are intentionally short and should not replace the canonical docs above:

- `DEVELOPMENT_PRIORITIES.md`
  - current product and engineering priorities
- `PIPELINE_ROADMAP.md`
  - staged pipeline direction
- `REFACTOR_EXECUTION_PLAN.md`
  - binding Week 1-4 execution plan for the current refactor cycle
- `REFACTOR_EXPANSION_NOTES.md`
  - deferred Week 5+ candidates that are intentionally not committed yet
- `adrs/0001-single-host-appliance.md`
  - appliance-model decision that anchors the current refactor scope
- `automation_todo.md`
  - actionable backlog snapshot
- `ARCHITECTURE_AUDIT.md`
  - concise architecture health summary
- `review.md`
  - fast review order for risky changes

## Context-Safe Rule

- Start with one canonical doc, not all of them.
- Open a specialized doc only when the task touches that subsystem.
- Prefer code and tests over docs when any statement becomes ambiguous.
