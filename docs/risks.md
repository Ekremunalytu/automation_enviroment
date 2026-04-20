# Risk Register

`Last Updated: 2026-04-20`

This register reflects the current post-Week-4 architecture.

## Active Risks

### P1 - Analysis can still fail because executor timing is inherently brittle

Files:

- `executor/flows/playwright/entrypoint.py`
- `executor/flows/playwright/monitor.py`
- `workflows/marketplace/analysis_service.py`

Why it matters:

- The core product promise depends on VS Code startup, extension install,
  reload, trigger application, and monitoring all lining up.
- This remains the most failure-prone part of the system even in a single-user
  deployment.

### P1 - Harness-extension trust is still not checksummed

Files:

- `executor/flows/harness_extension/`
- `documents/REFACTOR_STATUS.md`
- `documents/adrs/0002-threat-model.md`

Why it matters:

- Helper extension integrity is part of the sandbox trust boundary.
- Week 4 explicitly deferred this to W5, so the gap is known but still open.

### P2 - Activation reports are artifact-first while jobs are DB-backed by design

Files:

- `workflows/activation_reports/router.py`
- `workflows/marketplace/router.py`
- `output/`

Why it matters:

- Activation reports remain filesystem artifacts while async job metadata now
  lives in PostgreSQL.
- This split limits report queryability and historical comparison, but it keeps
  the current single-user sandbox model operationally simple.

### P2 - Trigger generation and workspace alignment remain fragile

Files:

- `workflows/marketplace/router.py`
- `executor/flows/playwright/workspace.py`
- `executor/flows/playwright/entrypoint.py`

Why it matters:

- If generated trigger files do not land in the actual mounted workspace, some
  activation scenarios will silently fail to execute.

### P2 - Security scaffold exists, but dedicated CI guardrails are incomplete

Files:

- `tests/security/`
- `Makefile`
- `.github/workflows/ci.yml`

Why it matters:

- The repo now contains malicious-fixture manifests and security tests, but the
  dedicated CI lane and install-guard automation are still thinner than ADR
  0004's full target state.

## Accepted Risks

### Local noVNC exposure

- noVNC is intended for local operator access, not public deployment.

### Single active analysis

- The background analysis flow is intentionally serialized.
- This matches the one-user sandbox deployment and avoids unnecessary queue
  infrastructure.

## Priority Mitigations

- land harness-extension checksum verification
- keep executor failure reporting explicit in marketplace responses
- expand workflow tests for background analysis jobs and restart behavior
- keep report semantics and health metadata honest when a run is degraded
- finish wiring the security scaffold into dedicated CI guardrails
