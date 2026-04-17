# Development Priorities

`Last Updated: 2026-04-17`

This is the short priority list for current work. It assumes the project
stays a single-user sandbox appliance on one machine or one Docker host.

If any older planning note clashes with the active refactor track, follow
`REFACTOR_EXECUTION_PLAN.md` first for Weeks 1-4B and
`REFACTOR_OPTIMIZATION.md` §10 for the current 7-week window (W0-W7).
Keep changes biased toward cleanliness, stability, and overall code
quality.

## Current Window (7 weeks, 2026-04-17 → ~2026-06-05)

**Acceptance bar: PoC.** The window targets a demonstrable
proof-of-concept that catches basic malicious extensions, not a
full-featured production security product. Full scope stays in the
plan (nothing removed); PoC framing selects Must vs Stretch. See
`REFACTOR_OPTIMIZATION.md` §10 for Must/Stretch split and §10.7 for the
PoC acceptance checklist.

- **W0 (spec, complete):** security foundations written as ADRs
  0002-0004 with PoC-priority annotations.
- **W1-W4:** automation stabilization before security implementation
  (legacy cleanup, import-graph enforcement, executor determinism +
  modularization, sandbox boundary).
- **W5-W7:** security implementation (detection rules per ADR 0003 PoC
  lifecycle mode, malicious fixture corpus per ADR 0004 T1 tier, UI
  detection surface minimum render).

**PoC Must classes (ADR 0002):** A1 credential stealer, A2 cryptominer,
A4 remote-loader, A6 package.json script abuse. **Stretch classes
(still in scope):** A3 typosquat, A5 malicious update, A7 VS Code API
abuse.

The priority list below describes the enduring engineering priorities
inside that window; weekly scope is in `REFACTOR_OPTIMIZATION.md` §10.2.

## Current Priorities

### 1. Executor Failure Honesty

- keep reset, install, reload, and trigger-load failures explicit
- make interrupted async jobs obvious after API restarts
- fail closed when executor timing becomes ambiguous

### 2. Coverage Fidelity

- keep official activation coverage separate from heuristic workflow coverage
- close official-track gaps for `scm` and `settings`
- decide which partial scaffolding should graduate into supported coverage for
  `chat`, `comments`, `testing`, and `workspace_trust`

### 3. Report Contract Stability

- keep report JSON stable for the UI
- preserve sharp semantics for `degraded` vs `inconclusive`
- keep attribution, risk signals, and verdict reasons evidence-linked

### 4. High-Value Test Depth

- expand async job lifecycle coverage
- keep restart interruption coverage healthy
- keep smoke coverage honest against real executor behavior

### 5. Lightweight Artifact Operations

- define retention and cleanup expectations for `output/`
- treat analysis output as semi-trusted (ADR 0002 §6); no automatic
  forwarding without scrubbing; UI renders string fields with escaping
- avoid speculative DB-backed run-history work unless operators need it

### 6. Security Posture Readiness (W5 prerequisite)

- keep the W0 ADRs (0002 threat model, 0003 detection taxonomy, 0004
  malicious fixture policy) synchronized with W1-W4 executor changes;
  if the sandbox boundary (W4) shifts trust assumptions, ADR 0002 §4
  must be updated
- land VS Code version pinning and harness checksum before the malicious
  fixture corpus is exercised; determinism is an attribution property,
  not a convenience
- keep `extensions/malicious/` planning aligned with ADR 0004 tiers; no
  live samples (T3) until the break-glass `make test-security-live`
  target exists

## Non-Priorities

- queue-backed distributed workers
- multi-tenant accounts or session management
- broad package reshuffles without a concrete product problem
- new dependencies without explicit need and approval
