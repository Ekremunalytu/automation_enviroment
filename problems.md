# Project Analysis - Current Issues

`Last Updated: 2026-04-13`

This file tracks known issues against the refactored architecture.

## High Priority

1. Analysis reliability still depends on executor reload correctness.
   - Relevant paths:
     - `workflows/marketplace/router.py`
     - `executor/host.py`
   - Risk:
     - a run can appear successful even if the installed extension never reached a clean activation state.

2. Some trigger scenarios remain sensitive to workspace path mismatches.
   - Relevant paths:
     - `executor/flows/playwright/entrypoint.py`
     - `executor/flows/playwright/workspace.py`
     - `executor/container/start.sh`
   - Risk:
     - trigger bait files may not land where VS Code is actually operating.

3. Dynamic-analysis artifacts are still file-backed.
   - Relevant paths:
     - `workflows/marketplace/router.py`
     - `workflows/activation_reports/router.py`
     - `output/`
   - Risk:
     - weaker queryability and comparisons across versions, although this is currently acceptable for the single-user sandbox model.

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

2. The UI is still split between file-backed reports and live job polling instead of a tighter single-run review loop.
   - Relevant paths:
     - `ui/src/lib/api/client.ts`
     - `ui/src/features/reports/ReportsPage.tsx`
     - `ui/src/features/simulation/SimulationPage.tsx`

## Validation Notes

- The architecture references in this file use canonical paths introduced by the refactor.
- Compatibility wrappers remain intentional for now and are tested.
- This file assumes a single-user sandbox deployment, not a shared SaaS app.
