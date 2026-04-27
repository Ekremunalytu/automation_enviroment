# Documents Guide

`Last Updated: 2026-04-27`

This folder is intentionally split into a small canonical core plus a few
specialized reference docs. Do not preload the entire folder unless the task
really spans multiple subsystems.

Current status lives in [`REFACTOR_STATUS.md`](REFACTOR_STATUS.md) — treat it
as the single source of phase-state truth. Deferrals:
[`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md). W0-W7 window:
[`REFACTOR_OPTIMIZATION.md` §10](REFACTOR_OPTIMIZATION.md). W8-W13
post-PoC external-review integration window:
[`REFACTOR_OPTIMIZATION.md` §11](REFACTOR_OPTIMIZATION.md). Historical
Week 1-4 execution plan: [`REFACTOR_EXECUTION_PLAN.md`](REFACTOR_EXECUTION_PLAN.md).
Non-binding deferred ideas: [`REFACTOR_EXPANSION_NOTES.md`](REFACTOR_EXPANSION_NOTES.md).

Security posture (threat model, detection taxonomy, malicious fixture policy,
package-boundary charter, local network binding) is fixed by ADRs 0002-0005
plus ADR 0007. Those ADRs already govern the current detection surface under
`packages/`, `extensions/malicious/`, and `tests/security/`. ADR 0007 is
**Accepted** as of `2026-04-27`, but its W8-7 implementation
(`REFACTOR_OPTIMIZATION.md` §11.5) is still the gate that turns its loopback /
`EXTRACE_ALLOW_LAN` discipline from prose into enforced configuration.

## Agent Shortcut

- `AGENT_CONTEXT.md`
  - thin task-routing map for coding agents after reading root `AGENTS.md`
- `agent-lanes/`
  - lazy-load task-lane details; open one lane only after
    `AGENT_CONTEXT.md`

## Read First

Read these in order for most code changes:

1. `AGENT_CONTEXT.md`
   - choose the task lane and avoid preloading the whole doc set
2. `agent-lanes/<matching-lane>.md`
   - source files, invariants, tests, and shortcuts for the touched area
3. `ARCHITECTURE.md`
   - system shape, boundaries, request flows
4. `PROJECT_STRUCTURE.md`
   - where new code should live
5. `TESTING.md`
   - test layout, fixtures, and commands

## Load Only If The Task Needs It

- `EXECUTOR_PLAYWRIGHT.md`
  - executor container, host wrapper, Playwright runtime
- `DETECTION_SEMANTICS.md`
  - exported `ActivationReport` JSON fields, health/signal-summary
    semantics, evidence interpretation
- `DEMO_SCENARIO.md`
  - single-extension A1 canary playbook used by the PoC acceptance demo
- `VSCODE_API_COVERAGE_AUDIT.md`
  - trigger planning, capability support, official vs heuristic coverage
- `docs/risks.md`
  - current risk register and accepted tradeoffs

## Operational Runbooks

Open one of these when a specific failure mode is in flight; do not preload.

- [`runbooks/README.md`](runbooks/README.md) — index + shape all runbooks follow
- [`runbooks/analysis-job-stuck.md`](runbooks/analysis-job-stuck.md)
  - async `analysis_jobs` row stuck in `running` with no step transition
- [`runbooks/fatal-ui-crash.md`](runbooks/fatal-ui-crash.md)
  - `failure_reason_code = "fatal_ui_crash"`,
    `automation_health.status = inconclusive`, aborted scenarios
- [`runbooks/scan-between-restart-failure.md`](runbooks/scan-between-restart-failure.md)
  - second scan fails `code --install-extension` with rc=1 (stale
    Chromium SingletonLock / dead IPC socket)
- [`runbooks/live-capture-regression.md`](runbooks/live-capture-regression.md)
  - `make test-security` green, `make test-security-live` red; A4 TLS
    rules report zero matches on real outbound HTTPS

## Planning And Review Docs

These are intentionally short and should not replace the canonical docs above:

- `DEVELOPMENT_PRIORITIES.md`
  - current product and engineering priorities
- `PIPELINE_ROADMAP.md`
  - staged pipeline direction
- `REFACTOR_EXECUTION_PLAN.md`
  - historical Week 1-4 execution plan and implementation snapshots
- `REFACTOR_STATUS.md`
  - phase closure history (W4 → W5 → W6 → W7) with closure evidence and
    the post-W7 hardening follow-up log
- `POST_POC_BACKLOG.md`
  - deferred items and the "pull first" next-iteration list; source of
    truth for work that passed the PoC acceptance gate
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
- `adrs/0007-local-network-binding.md`
  - loopback-by-default + `EXTRACE_ALLOW_LAN` opt-in + CORS allow-list
    - CDP behind `debug` profile; encodes the ADR 0001 / ADR 0002 §5
    trusted-environment assumption in configuration. Accepted
    2026-04-27; W8-7 implementation still pending in code/config/tests.
- `automation_todo.md`
  - thin pull-next snapshot pointing at `POST_POC_BACKLOG.md` for the
    canonical deferred-work list (use the backlog as source of truth)
- `ARCHITECTURE_AUDIT.md`
  - concise architecture health summary
- `review.md`
  - fast review order for risky changes

## Context-Safe Rule

- Start with one canonical doc, not all of them.
- Open a specialized doc only when the task touches that subsystem.
- Prefer code and tests over docs when any statement becomes ambiguous.
