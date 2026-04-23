# Documents Guide

`Last Updated: 2026-04-23`

This folder is intentionally split into a small canonical core plus a few
specialized reference docs. Do not preload the entire folder unless the task
really spans multiple subsystems.

If an older note conflicts with the current refactor direction, prefer
`REFACTOR_STATUS.md` for current closure state, `REFACTOR_EXECUTION_PLAN.md`
for the historical Week 1-4 plan, and `REFACTOR_OPTIMIZATION.md` §10 for the
7-week stabilization-then-security window (W0-W7). Use
`REFACTOR_EXPANSION_NOTES.md` only as a deferred reference, not as a binding
delivery plan.

Current status lives in `REFACTOR_STATUS.md`. Week 4 closure validated
`2026-04-20`. W5 detection foundations (contracts, A1/A2/A4/A6 rules, T1
canaries, `make test-security`) landed `2026-04-20`. W6 automation hardening
landed `2026-04-21`, and the W6 correctness follow-up (target-only
attribution, TLS vocabulary, error dominance, security-fixtures CI) closed
on `2026-04-23`. **W7 (acceptance + buffer) is now open.**

Security posture (threat model, detection taxonomy, malicious fixture policy,
package-boundary charter) is fixed by ADRs 0002-0005. Those ADRs already
govern the current detection scaffold under `packages/`,
`extensions/malicious/`, and `tests/security/`.

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
  - exported `ActivationReport` JSON fields, health/signal-summary
    semantics, evidence interpretation
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
  - historical Week 1-4 execution plan and implementation snapshots
- `REFACTOR_STATUS.md`
  - phase closure history (W4 → W5 → W6) with closure evidence and the
    current W7 entry rule
- `REFACTOR_OPTIMIZATION.md`
  - plan critique (Opus 4.6, Opus 4.7 passes) + 7-week stabilization->security
    window (§10); GPT-5.4 uses this as an implementation spec
- `REFACTOR_EXPANSION_NOTES.md`
  - still-deferred candidates that are intentionally not committed yet
- `adrs/0001-single-host-appliance.md`
  - appliance-model decision that anchors the current deployment scope
- `adrs/0002-threat-model.md`
  - in-scope adversary classes (A1-A7), trust boundaries, capability
    assumptions; fixes the security scope before rule authoring
- `adrs/0003-detection-taxonomy.md`
  - MITRE ATT&CK alignment, severity/confidence, `DetectionReport` contract,
    verdict rollup, rule lifecycle
- `adrs/0004-malicious-fixture-policy.md`
  - T1/T2/T3 isolation tiers, `LABEL.yaml` manifest, current malicious-fixture
    scaffold, and remaining CI/guardrail gaps
- `adrs/0005-packages-charter.md`
  - allowed dependency direction and public API rules for `packages/`
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
