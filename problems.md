# Project Analysis - Current Issues

`Last Updated: 2026-04-24`

This file tracks known issues against the current refactored architecture
(post-W7 closure + post-W7 hardening landings on 2026-04-24).

## High Priority

1. Analysis reliability still depends on executor reload correctness.
   - Relevant paths:
     - `executor/host.py`
     - `executor/flows/playwright/reload_vscode.py`
     - `executor/flows/playwright/vscode.py`
     - `executor/flows/playwright/reset_state.py` (scan-between restart)
     - `executor/container/launch_vscode.sh` (shared boot + reset script)
   - Risk:
     - a run can still appear operationally healthy until the VS Code workbench
       and extension-host surfaces fully reconnect.
   - Mitigation delta (2026-04-24): scan-between restart now terminates
     VS Code (SIGTERM + 5 s grace + SIGKILL fallback), clears
     `extensions/`/`logs/`, removes Chromium SingletonLock/Cookie/Socket,
     and relaunches via the shared `launch_vscode.sh`; fatal UI crashes in
     `_run_scenario_sequence` are now classified by `is_fatal_ui_error`
     and fail-fast with `failure_reason_code = "fatal_ui_crash"` degrading
     `automation_health.status` to `inconclusive`.

2. Live capture (`make test-security-live`) remains the most fragile
   detection path.
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
- W7 PoC acceptance checklist closed 11/11 on 2026-04-23;
  `scripts/demo_acceptance.py` replays the A1 credential-read → network
  canary end-to-end.
- Scan-between install races (ESLint `onStartupFinished` rc=1) resolved by
  the 2026-04-24 `reset_executor_state` orchestration + shared
  `launch_vscode.sh`; `install_extension_in_executor` now retries once
  through `reload_vscode_window` on transient IPC markers and surfaces
  stderr-tail diagnostics in the analysis report.
- `executor/flows/playwright/monitor_attribution.py` (1122 LoC) split
  into the `attribution/` subpackage on 2026-04-24 with the 29-name
  underscore-prefixed API preserved verbatim.

## Validation Notes

- The architecture references in this file use canonical paths.
- This file assumes a single-user sandbox deployment, not a shared SaaS app.
- W5-W7 are all closed; post-PoC deferrals live in
  `documents/POST_POC_BACKLOG.md`. The next-iteration pull list is the
  source of truth for what to work on next.
