# Project Analysis - Current Issues

`Last Updated: 2026-03-06`

This file tracks known issues against the refactored architecture.

## High Priority

1. Analysis reliability still depends on executor reload correctness.
   - Relevant paths:
     - `workflows/marketplace/router.py`
     - `scanner/executor.py`
   - Risk:
     - a run can appear successful even if the installed extension never reached a clean activation state.

2. Some trigger scenarios remain sensitive to workspace path mismatches.
   - Relevant paths:
     - `executor/flows/playwright/entrypoint.py`
     - `executor/flows/playwright/workspace.py`
     - `executor/container/start.sh`
   - Risk:
     - trigger bait files may not land where VS Code is actually operating.

3. Dynamic-analysis results are not yet modeled in PostgreSQL.
   - Relevant paths:
     - `workflows/marketplace/router.py`
     - `workflows/activation_reports/router.py`
     - `appcore/storage/models.py`
   - Risk:
     - no durable run history, weak queryability, and limited comparisons across versions.

## Medium Priority

1. Broad fallback behavior can hide orchestration errors.
   - Relevant path:
     - `workflows/marketplace/router.py`
   - Risk:
     - reduced observability when trigger selection or analysis preparation fails.

2. Async analysis coverage is thinner than the synchronous path.
   - Relevant paths:
     - `tests/workflows/marketplace/test_router.py`
     - `workflows/marketplace/router.py`
   - Risk:
     - regressions in job snapshot status handling may go unnoticed.

3. Compatibility wrappers are still a maintenance surface.
   - Relevant paths:
     - `routers/`
     - `scanner/`
     - `core/`
     - `database/`
     - `crud/`
     - `models/`
     - `schemas/`
   - Risk:
     - new changes may accidentally target wrappers instead of canonical modules.

## Lower Priority

1. File-backed report retention and cleanup policy is still implicit.
   - Relevant path:
     - `output/`

2. The UI is still split between file-backed reports and live job polling instead of a unified run model.
   - Relevant paths:
     - `ui/api.py`
     - `ui/views/dashboard.py`
     - `ui/views/simulation.py`

## Validation Notes

- The architecture references in this file use canonical paths introduced by the refactor.
- Compatibility wrappers remain intentional for now and are tested.
