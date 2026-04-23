# Development Priorities

`Last Updated: 2026-04-23`

This is the short priority list for current work. It assumes the project stays
a single-user sandbox appliance on one machine or one Docker host.

If any older planning note clashes with the active refactor track, follow
`REFACTOR_STATUS.md` for current closure state and
`REFACTOR_OPTIMIZATION.md` §10 for the active 7-week window (W0-W7). Keep
changes biased toward cleanliness, stability, and overall code quality.

## Current Window (7 weeks, 2026-04-17 -> ~2026-06-05)

**Acceptance bar: PoC.** The window targets a demonstrable
proof-of-concept that catches basic malicious extensions, not a full-featured
production security product. Full scope stays in the plan; PoC framing selects
Must vs Stretch. See `REFACTOR_OPTIMIZATION.md` §10 for Must/Stretch split and
§10.7 for the PoC acceptance checklist.

- **W0 (spec, complete):** security foundations written as ADRs 0002-0004 with
  PoC-priority annotations.
- **W1-W4 (complete, closed 2026-04-20):** automation stabilization before
  security implementation.
- **W5 (detection foundations, complete 2026-04-20):** detection contracts,
  A1/A2/A4/A6 rule scaffolding, T1 canaries under `extensions/malicious/`,
  `tests/security/`, and `make test-security` / `make test-security-live`.
- **W6 (automation reliability + capture hardening, closed 2026-04-23):**
  scenario truth ledger, bounded waits, capture bounds, plus the W6
  correctness follow-up that gated A1/A2/A4 on `ActivationReport` attribution
  (`target_file_events`, `target_unknown_outbound_network_events`), added
  `tls_client_hello` to `TLS_EVENT_TYPES`, enforced
  `RuleExecutionStatus.ERROR` dominance in verdict rollup, and re-narrowed
  `.gitignore` so security fixtures reach the `security-fixtures` CI lane.
- **W7 (acceptance + buffer, open as of 2026-04-23):** drive PoC acceptance
  per `REFACTOR_OPTIMIZATION.md` §10.7, validate live capture against T1
  canaries, and absorb leftover correctness items.
- **Pre-W6 cleanup (complete, 2026-04-20):** dormant root directories removed,
  marketplace trigger planning narrowed to `TriggerPlan`, and
  `executor/flows/playwright/monitor.py` reduced to a facade over split helper
  modules.

**PoC Must classes (ADR 0002):** A1 credential stealer, A2 cryptominer, A4
remote-loader, A6 package.json script abuse. **Stretch classes (still in
scope):** A3 typosquat, A5 malicious update, A7 VS Code API abuse.

The priority list below describes the enduring engineering priorities inside
that window; weekly scope is in `REFACTOR_OPTIMIZATION.md` §10.2. W7 focuses
on acceptance validation against the PoC checklist and buffer for leftover
W6 follow-ups, not new structural work.

## Current Priorities

### 1. Executor Failure Honesty

- keep reset, install, reload, trigger-load, and monitor failures explicit
- make interrupted async jobs obvious after API restarts
- fail closed when executor timing becomes ambiguous

### 2. Supply-Chain Boundary Tightening

- keep harness-extension checksum verification enforced before trusting helper
  bundles in W5/W6 runs
- keep workflow access to Docker daemon behavior behind `executor.control`
- avoid broadening sandbox trust assumptions without updating ADR 0002

### 3. Coverage Fidelity

- keep official activation coverage separate from heuristic workflow coverage
- close official-track gaps for `scm` and `settings`
- decide which partial scaffolding should graduate into supported coverage for
  `chat`, `comments`, `testing`, and `workspace_trust`

### 4. Report Contract Stability

- keep report JSON stable for the UI
- preserve sharp semantics for `degraded` vs `inconclusive`
- keep attribution, risk signals, and verdict reasons evidence-linked

### 5. Security Scaffold Integrity

- keep malicious-fixture manifests aligned with ADR 0004
- keep `tests/security/` and `make test-security` honest about current PoC
  scope
- separate "fixture scaffold exists" from "detection rules are implemented"

### 6. High-Value Test Depth

- keep async job lifecycle coverage healthy
- keep restart interruption coverage healthy
- keep smoke coverage honest against real executor behavior
- wire the security scaffold into dedicated CI coverage when guardrails are ready

### 7. Lightweight Artifact Operations

- define retention and cleanup expectations for `output/`
- treat analysis output as semi-trusted (ADR 0002 §6); no automatic forwarding
  without scrubbing
- avoid speculative DB-backed run-history work unless operators need it

## Non-Priorities

- queue-backed distributed workers
- multi-tenant accounts or session management
- broad package reshuffles without a concrete product problem
- new dependencies without explicit need and approval
