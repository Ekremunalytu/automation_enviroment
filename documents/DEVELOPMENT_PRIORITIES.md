# Development Priorities

`Last Updated: 2026-04-13`

The architecture refactor is in place. Current priorities should now focus on making the new workflow layout operationally complete.

## Priority 1: Dynamic Analysis Robustness

The marketplace workflow now exposes sandbox execution directly. That makes reliability issues higher priority than additional feature breadth.

Focus areas:

- executor reload correctness after extension install
- trigger generation error visibility
- deterministic workspace setup for trigger files
- better failure reporting from async analysis jobs

## Priority 2: Structured Persistence for Dynamic Analysis

The API can already start analysis, but results are still filesystem-centric.

Required next step:

- introduce Alembic migrations and models for run-level analysis state
- define schemas in `appcore/contracts/`
- persist through `appcore/storage/crud`

## Priority 3: Workflow Test Depth

The test layout is better, but the most valuable additions now are integration-style tests around:

- `POST /api/marketplace/download`
- `POST /api/marketplace/analyze`
- `POST /api/marketplace/analyze/start`
- `GET /api/marketplace/analyze/{job_id}`

## Priority 4: UI/Data Convergence

The React SPA currently combines file-backed report browsing with live job polling. After DB-backed run persistence lands, the next goal should be to unify those experiences around a stable run model.

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
- speculative abstractions before dynamic-analysis persistence is in place
