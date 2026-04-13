# Risk Register

`Last Updated: 2026-04-13`

This register reflects the post-refactor architecture.

## Active Risks

### P1 - Analysis success can outreport real executor failure

Files:

- `workflows/marketplace/router.py`
- `executor/host.py`

Why it matters:

- The marketplace workflow depends on install, reset, reload, trigger generation, and Playwright execution all behaving correctly.
- If reload or follow-up executor steps are treated as soft failures, analysis may complete with a misleading report.

### P1 - Analysis can still fail because executor timing is inherently brittle

Files:

- `executor/flows/playwright/entrypoint.py`
- `executor/flows/playwright/monitor.py`
- `workflows/marketplace/analysis_service.py`

Why it matters:

- The core product promise depends on VS Code startup, extension install, reload, trigger application, and monitoring all lining up.
- This remains the most failure-prone part of the system even in a single-user deployment.

### P2 - Dynamic-analysis state is file-backed by design

Files:

- `workflows/activation_reports/router.py`
- `workflows/marketplace/router.py`
- `output/`

Why it matters:

- Activation reports and job snapshots are not persisted as first-class DB records.
- This limits queryability and historical comparison, but it is currently acceptable for the single-user sandbox model.

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

### Single active analysis

- The background analysis flow is intentionally serialized.
- This matches the one-user sandbox deployment and avoids unnecessary queue infrastructure.

## Priority Mitigations

- Keep executor failure reporting explicit in marketplace responses
- Expand workflow tests for background analysis jobs and restart behavior
- Keep report semantics and health metadata honest when a run is degraded
- Keep all internal callers on canonical imports
