# Development Priorities

`Last Updated: 2026-04-15`

This is the short priority list for current work. It assumes the project stays a
single-user sandbox appliance on one machine or one Docker host.

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
- avoid speculative DB-backed run-history work unless operators need it

## Non-Priorities

- queue-backed distributed workers
- multi-tenant accounts or session management
- broad package reshuffles without a concrete product problem
- new dependencies without explicit need and approval
