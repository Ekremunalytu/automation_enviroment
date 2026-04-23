# Project Analysis - Current Issues

`Last Updated: 2026-04-23`

This file tracks known issues against the current refactored architecture
(post-W6 closure, W7 acceptance + buffer open).

## High Priority

1. Analysis reliability still depends on executor reload correctness.
   - Relevant paths:
     - `executor/host.py`
     - `executor/flows/playwright/reload_vscode.py`
     - `executor/flows/playwright/vscode.py`
   - Risk:
     - a run can still appear operationally healthy until the VS Code workbench
       and extension-host surfaces fully reconnect.

2. Live capture (`make test-security-live`) is the most fragile detection
   path and is load-bearing for W7 acceptance.
   - Relevant paths:
     - `executor/flows/playwright/runtime_capture/`
     - `tests/security/`
     - `Makefile`
   - Risk:
     - tshark and runtime-capture changes can silently regress
       `tls_client_hello` / `TLS_EVENT_TYPES` matching even though
       `make test-security` (offline) stays green.

3. Dynamic-analysis reports are still file-backed.
   - Relevant paths:
     - `workflows/activation_reports/router.py`
     - `output/`
     - `workflows/marketplace/job_service.py`
   - Risk:
     - jobs are durable in Postgres, but report history and comparisons remain
       artifact-first.

## Medium Priority

1. Some trigger scenarios remain sensitive to workspace path mismatches.
   - Relevant paths:
     - `executor/flows/playwright/entrypoint.py`
     - `executor/flows/playwright/workspace.py`
     - `executor/container/start.sh`
   - Risk:
     - trigger bait files may not land where VS Code is actually operating.

2. UI request/client logic is still thinner than the generated contract layer.
   - Relevant paths:
     - `scripts/generate_ui_contracts.py`
     - `ui/src/lib/api/client.ts`
     - `ui/src/lib/adapters/`
   - Risk:
     - generated DTOs reduce drift, but request composition and view-model
       adapters can still drift from backend semantics.

3. T3 fixture handling is still deferred.
   - Relevant paths:
     - `documents/adrs/0004-malicious-fixture-policy.md`
     - `tests/security/`
   - Risk:
     - real-world malicious samples remain break-glass-only via
       `make test-security-live`; full T3 lifecycle (storage, attestation,
       cleanup) is post-PoC scope.

## Lower Priority

1. File-backed report retention and cleanup policy is still implicit.
   - Relevant path:
     - `output/`

## Resolved Since 2026-04-20

- Harness-extension integrity checksumming landed in W5 (`Dockerfile`
  writes `/home/executor/flows/harness_extension.sha256`; `start.sh`
  verifies before VS Code launches).
- Security-fixtures CI lane runs `make test-security` against tracked T1
  canaries and benign baselines (W6 correctness follow-up, 2026-04-23).
- Historical `apps/` and `legacy_ui/` placeholders were removed from the
  repo surface (pre-W6 cleanup, 2026-04-20).

## Validation Notes

- The architecture references in this file use canonical paths.
- This file assumes a single-user sandbox deployment, not a shared SaaS app.
- W5 detection foundations and W6 hardening + correctness follow-up are
  complete; remaining open scope is W7 PoC acceptance per
  `REFACTOR_OPTIMIZATION.md` §10.7.
