# Risk Register

`Last Updated: 2026-03-06`

This register reflects the post-refactor architecture.

## Active Risks

### P1 - Analysis success can outreport real executor failure

Files:

- `workflows/marketplace/router.py`
- `executor/host.py`

Why it matters:

- The marketplace workflow depends on install, reset, reload, trigger generation, and Playwright execution all behaving correctly.
- If reload or follow-up executor steps are treated as soft failures, analysis may complete with a misleading report.

### P1 - Dynamic-analysis state is still file-backed

Files:

- `workflows/activation_reports/router.py`
- `workflows/marketplace/router.py`
- `output/`

Why it matters:

- Activation reports and job snapshots are not persisted as first-class DB records.
- This limits queryability, retention discipline, and historical comparison.

### P2 - Trigger generation and workspace alignment remain fragile

Files:

- `workflows/marketplace/router.py`
- `executor/flows/playwright/workspace.py`
- `executor/flows/playwright/entrypoint.py`

Why it matters:

- If generated trigger files do not land in the actual mounted workspace, some activation scenarios will silently fail to execute.

### P2 - End-to-end executor coverage is still limited

Files:

- `tests/executor/`
- `tests/workflows/marketplace/`

Why it matters:

- Unit coverage is present, but the most failure-prone path is the integrated flow from API request to sandbox output.

## Accepted Risks

### Local noVNC exposure

- noVNC is intended for local operator access, not public deployment.

## Priority Mitigations

- Introduce DB-backed `analysis_runs`
- Make executor failures explicit in marketplace responses
- Expand workflow tests for background analysis jobs
- Keep all internal callers on canonical imports
