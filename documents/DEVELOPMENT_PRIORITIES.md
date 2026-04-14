# Development Priorities

`Last Updated: 2026-04-14`

The refactor and first-pass detection/reporting work are in place. Current
priorities should focus on operational reliability, coverage fidelity, and
keeping the analyst-facing contract honest.

These priorities still assume ExTrace remains a single-user sandbox product on
one machine or one Docker host.

## Priority 1: Executor Reliability and Failure Honesty

The most important work is still making sandbox outcomes truthful.

Focus areas:

- reset/install/reload failures must surface clearly in jobs and reports
- trigger payload load/apply failures must not look like clean runs
- interrupted async jobs must remain obvious after API restarts
- executor timing brittleness should fail closed, not blur into success

## Priority 2: Trigger Coverage Fidelity

The layered trigger system is now richer than the old scenario-only model. The
next priority is making its coverage claims precise.

Focus areas:

- keep official activation coverage separate from heuristic workflow coverage
- close remaining support gaps for `chat`, `comments`, `testing`, and
  `workspace_trust`
- tighten `scm` and `settings` verification on the official track
- keep per-event attempt ledgers readable for analysts and maintainers

## Priority 3: Report Contract Stability and Signal Calibration

Risk signals and verdicts now exist; the next work is calibration, not merely
adding more labels.

Focus areas:

- preserve sharp semantics for `degraded` vs `inconclusive`
- keep attribution summary, risk signals, and verdict reasons aligned
- avoid letting correlative activity overstate confidence
- keep the JSON report contract stable enough for the UI to evolve safely

## Priority 4: Test Depth Around the Real Risk Path

The highest-value tests are still the ones that defend the marketplace to
executor to report path.

Focus areas:

- background job lifecycle coverage
- restart interruption coverage
- smoke validation against pinned real fixtures
- UI adapter coverage for live report and job payload changes

## Priority 5: Controlled Persistence and Retention

Dynamic-analysis data is intentionally file-backed today. That is acceptable,
but it needs operational discipline.

Focus areas:

- define retention expectations for reports and job snapshots
- keep persistence lightweight unless cross-run queries become a real need
- avoid speculative schema work for analysis history

## Explicit Non-Priorities

- queue-backed distributed workers
- multi-tenant accounts or session management
- broad architectural rewrites without a concrete product problem
- new dependencies without a strong and explicit need
