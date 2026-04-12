# Architecture Audit

`Last Updated: 2026-03-06`

This is the post-refactor architecture audit. It evaluates the current codebase as it exists after the move to `appcore/` and `workflows/`.

## Executive Summary

The refactor materially improved structure:

- shared infrastructure is now isolated in `appcore/`
- business behavior is grouped by workflow in `workflows/`
- the executor runtime is split into `container/` and `flows/playwright/`
- the UI has been decomposed into reusable modules and page renderers

The main architectural risk is no longer layering. The main risk is that dynamic-analysis state is still mostly file-backed while the API surface has grown to include background analysis jobs and sandbox orchestration.

## What Improved

### Clearer module boundaries

- `appcore/` owns settings, DB setup, schemas, models, and CRUD
- `workflows/` owns routers and workflow-specific business logic
- `ui/` owns dashboard concerns
- `executor/` owns sandbox runtime concerns

This is a meaningful improvement over the older `routers/scanner/core/crud/models/schemas` concentration.

### Canonical imports enforced

Legacy wrapper modules have been removed, and `tests/platform/test_canonical_imports.py` verifies the supported import surface directly.

### Marketplace workflow is now a first-class slice

Marketplace search, download, and analysis are no longer scattered implementation details. They are modeled as a dedicated workflow with its own router, client, and trigger logic.

## Current Architectural Strengths

- App factory in `main.py` is small and composes routers cleanly.
- Shared settings are centralized in `appcore/api/config.py`.
- CRUD remains the single write boundary.
- Tests now mirror the real architecture, which reduces cognitive overhead.
- UI is modular enough to evolve without turning `ui/app.py` into a monolith.

## Current Risks

### File-backed analysis state

Activation reports and background job snapshots live under `output/`, not in PostgreSQL. That is acceptable for the current stage, but it creates operational gaps:

- run history is harder to query
- retention and cleanup policy is implicit
- correlations between extension metadata and dynamic-analysis output remain weaker than they should be

### Reliability of analysis orchestration

The API now exposes executor-backed analysis flows, but the durability guarantees are limited by Docker exec success, VS Code reload behavior, and filesystem snapshots.

## Recommendations

### Near-term

- Add persistent DB records for analysis runs
- Make reload and trigger-generation failures observable and explicit
- Expand workflow-level tests for async analysis paths

### Mid-term

- Persist normalized telemetry summaries through `appcore.storage.crud`
- Add a run-centric query surface for the UI
- Reduce reliance on implicit filesystem conventions

### Long-term

- Keep downstream code on canonical imports only
- Separate raw artifact retention from structured result persistence

## Verdict

The refactor is directionally correct and significantly improves maintainability. The architecture is now coherent; the remaining work is mostly about operational maturity of the dynamic-analysis pipeline, not structural cleanup.
