# Executor Risk Assessment

Date: 2026-02-19

## Scope Clarifications

- noVNC will not be exposed for remote/public access.
- CodeQL is intentionally out of scope.
- Executor modules are in active scope and will be used to simulate behavior after extension installation.

## Active Risks

### P1 - Process Supervision Gap

File: `executor/start.sh`

Critical processes (`Xvfb`, `openbox`, `x11vnc`, VS Code, noVNC) are started in the background, but the container is kept alive with `tail -f /dev/null`.  
If one of the critical processes exits, the container may still look healthy while analysis is effectively broken.

### P1 - Flaky Playwright Connection Sequence

File: `executor/playwright/vscode.py`

The current connection flow directly accesses `browser.contexts[0]` and `context.pages[0]`.  
In startup race conditions, this can fail and make behavior simulation flaky.

### P2 - Limited Executor Integration Coverage

Files: `executor/playwright/*.py`, `tests/executor/*`

Executor now has dedicated unit tests (`tests/executor/test_playwright_automation.py` and
`tests/executor/test_playwright_monitor.py`), but end-to-end integration coverage is still
missing for the full flow:
`extension installed -> trigger commands/actions -> behavior simulation/collection`.

## Closed / Accepted Items

### Closed - noVNC Remote Exposure Risk

Accepted context: access is local only, not remote.

### Closed - CodeQL Removal Concern

Accepted context: CodeQL is intentionally outside current scope.
