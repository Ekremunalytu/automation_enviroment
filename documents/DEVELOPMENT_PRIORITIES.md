# Development Priorities

`Last Updated: 2026-04-13`

The architecture refactor is in place. Current priorities should now focus on making the new workflow layout operationally complete.

These priorities assume ExTrace remains a single-user sandbox product running on one machine or one Docker host.

## Priority 1: Dynamic Analysis Robustness

The marketplace workflow now exposes sandbox execution directly. That makes reliability issues higher priority than additional feature breadth.

Focus areas:

- executor reload correctness after extension install
- trigger generation error visibility
- deterministic workspace setup for trigger files
- better failure reporting from async analysis jobs

## Priority 2: Report Quality and Triage Signal Quality

The next value is better sandbox output, not larger infrastructure.

Required next step:

- improve report health explanations
- keep target-observed vs correlated-only semantics sharp
- improve rule draft quality and evidence attribution views

## Priority 3: Workflow Test Depth

The test layout is better, but the most valuable additions now are integration-style tests around:

- `POST /api/marketplace/download`
- `POST /api/marketplace/analyze`
- `POST /api/marketplace/analyze/start`
- `GET /api/marketplace/analyze/{job_id}`

## Priority 4: UI Clarity for the Analyst Loop

The React SPA already covers the main analyst loop. The next goal is to keep that loop clear and predictable:

- marketplace search -> download -> analyze
- live simulation status and evidence
- final report inspection and rule drafting

## Priority 5: Wrapper Retirement Plan

Compatibility wrappers are useful, but they should be considered transitional.

Short-term:

- keep them thin
- keep them tested

Long-term:

- migrate callers to canonical imports
- eventually remove legacy surfaces

## Explicit Non-Priorities

- broad cross-layer rewrites
- new dependencies without a strong need
- queue-backed distributed workers
- multi-tenant account/session features
- speculative DB schemas for analysis history before the product actually needs them
