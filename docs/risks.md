# Risk Register

`Last Updated: 2026-04-21`

This register reflects the current post-Week-4 architecture.

## Active Risks

### P1 - Executor truthfulness remains a critical reliability boundary

Files:

- `executor/flows/playwright/entrypoint_runner.py`
- `executor/flows/playwright/health_summary.py`
- `packages/analysis_contracts/report_invariants.py`
- `workflows/marketplace/analysis_service.py`

Why it matters:

- The product promise depends on requested scenarios being reported honestly as
  executed, failed, or skipped with an explainable reason.
- W6 closes the silent-dropout bug class, but future planner/runtime/report
  drift would immediately mislead analysts if this surface regresses.

### P1 - Runtime capture remains intentionally bounded

Files:

- `executor/flows/playwright/runtime_capture/network.py`
- `executor/flows/playwright/runtime_capture/extension_host.py`
- `packages/analysis_contracts/contracts.py`

Why it matters:

- HTTP body capture is limited to cleartext HTTP previews and hashes, and
  child-process tracking is scoped to the observed extension-host tree.
- That keeps artifacts safe and bounded, but it also means TLS payloads and
  out-of-scope process activity remain intentionally unseen.

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

### P2 - Coverage remains partial even though unsupported surfaces now fail closed

Files:

- `executor/flows/playwright/stimulus_materializers.py`
- `executor/flows/playwright/stimulus_passes.py`
- `workflows/marketplace/trigger_service.py`

Why it matters:

- W6 makes unsupported activation families and failed materialization explicit,
  which is safer than optimistic fallbacks.
- The tradeoff is that fixture/matrix gaps now surface as degraded coverage
  instead of being papered over.

### P2 - Security-fixture CI hardening now depends on runner firewall controls

Files:

- `tests/security/`
- `Makefile`
- `.github/workflows/ci.yml`
- `documents/adrs/0004-malicious-fixture-policy.md`

Why it matters:

- The CI lane now disables outbound egress before `make test-security` and
  asserts that `make test-security-live` fails under `CI=true`.
- This is the intended posture, but it still relies on GitHub runner support
  for the firewall step and does not replace the remaining install-guard work.

## Accepted Risks

### Local noVNC exposure

- noVNC is intended for local operator access, not public deployment.

### Single active analysis

- The background analysis flow is intentionally serialized.
- This matches the one-user sandbox deployment and avoids unnecessary queue
  infrastructure.

## Priority Mitigations

- keep executor failure reporting explicit in marketplace responses
- keep report semantics and health metadata honest when a run is degraded
- expand bounded capture without storing unsafe raw payloads
- keep CI egress hardening observable and fail-closed
