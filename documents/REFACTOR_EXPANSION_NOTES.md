# Refactor Expansion Notes

`Last Updated: 2026-04-17`

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
- that Week 4A work was revalidated on `2026-04-15` with a passing fast test
  lane and a passing `ms-python.python` layered smoke run after reload/reconnect
  hardening in the executor
- keep this note only as historical context for why Week 4A exists; do not
  treat it as a separate Week 5+ candidate unless it is explicitly descoped
  from the execution plan

## Promoted Into The 7-Week Window (2026-04-17)

The following items were previously Week 5+ candidates. The 7-week
stabilization→security window promoted them into the execution plan via
`REFACTOR_OPTIMIZATION.md` §10. They remain listed here for history; do
not treat them as still-deferred.

### Executor Control Boundary → W4 (Week 4E)

Promoted because this is the sandbox security surface, not an operability
concern. Covered by `REFACTOR_OPTIMIZATION.md` §2.4 and ADR 0002 §4
(trust boundaries).

### Deterministic Executor Runtime → W2 (Week 4D-a)

Promoted because VS Code pinning is an attribution property for detection
(ADR 0002 trust boundaries), not a reproducibility convenience. Covered
by `REFACTOR_OPTIMIZATION.md` §7.2.2 / §7.2.3.

### AI-Safe Ownership Map → W1 (Week 4C)

Partially promoted: `packages/` charter + import-graph test land in W1.
Full ownership map for UI adapters, storage, and engine stays deferred
until after W5 detection contracts stabilize.

### Expanded Smoke Matrix → W1 (benign) + W5 (malicious)

Benign fixture expansion (color-theme, chat-only) is W1. The malicious
fixture corpus (T1/T2/T3 per ADR 0004) is W5.

## Candidate Expansion Topics (still deferred)

### Stack-Scoped Compose Runtime

- remove fixed `container_name` assumptions
- make ports and state roots stack-scoped from env alone
- improve multi-worktree and parallel AI ergonomics
- not promoted: operability gain, not on the stabilization→security
  critical path

## Operating Rule

Do not treat these remaining notes as an implied Week 5 commitment. Promote
them into the execution plan only when Week 4A and Week 4B are done and the
repo is ready for the extra change surface.
