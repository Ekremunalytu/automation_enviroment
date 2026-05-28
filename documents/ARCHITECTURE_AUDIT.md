# Architecture Audit

`Last Updated: 2026-05-28 — W22 active (closed synthetically on week22; PR week22 -> main PENDING USER APPROVAL); W21 closed and merged via PR #30 5dc18aa.`

This is the short health summary for the current architecture. Use
`ARCHITECTURE.md` for structure and flows; use `docs/risks.md` for the live
risk register. Post-PoC deferred items live in `POST_POC_BACKLOG.md`.

## What Is Healthy

- Ownership boundaries are now mechanically enforced:
  - `packages/` stays framework-agnostic
  - `executor/` avoids `appcore/` and `workflows/`
  - workflows reach sandbox mechanics through `executor.control`
- Catalog persistence and durable analysis-job state both route through
  `appcore/storage/crud.py`.
- Async analysis is decomposed into router, analysis service, trigger planning,
  executor control, and job storage instead of one opaque path.
- The executor runtime is less monolithic than before:
  `runtime_capture/`, scenario helpers, health/signal support modules, and
  the `attribution/` subpackage (`events.py` + `links.py` behind a flat
  re-export facade, split out from `monitor_attribution.py` on 2026-04-24)
  now carry part of the surface.
- The UI now has generated backend-owned contract types plus feature-boundary
  checks.
- Scan-between restarts are now orchestrated (`reset_executor_state` +
  shared `launch_vscode.sh`), and renderer-death failures fail-fast with
  `failure_reason_code = "fatal_ui_crash"` rather than cascading through
  downstream scenarios.
- Long-running analyses are observable and interruptible end-to-end:
  the simulation UI reports weighted phase progress + per-scenario
  sub-progress, and `POST /api/marketplace/analyze/{job_id}/cancel`
  uses a W13 two-phase lifecycle (`running -> cancelling -> cancelled`)
  with hot-zone worker poll points instead of leaving the operator to
  kill the process.
- The harness extension's reload path no longer races a stale ready
  marker: `vscode.py::reload_workbench_window` unlinks the marker
  before dispatching the reload and the harness `activate()` awaits
  the marker write, so VNC sessions survive a workbench reload
  without a follow-up `HarnessUnavailableError`.

## What Still Carries Risk

- Executor reliability still defines product truthfulness.
- Activation reports remain artifact-first in `output/`.
- Harness-extension checksum verification is enforced at executor startup
  (W5/W6); regressions in the helper-bundle pipeline would silently
  invalidate runs.
- Live capture (`make test-security-live`) exercises real tshark output and
  is still the most fragile detection path; regressions here would silently
  compromise detection truthfulness even though `make test-security`
  (offline) stays green.
- Docker-based A1 canary structural diff (`make exec-up && make exec-run`
  against `t1-a1-credential-read-to-network-canary`) remains user-side —
  the capture-pipeline regression risk flagged in the `attribution/` split
  deferral note only closes with a live executor smoke.

## Recommended Reading By Problem Type

- Architecture question: `ARCHITECTURE.md`
- Placement question: `PROJECT_STRUCTURE.md`
- Runtime reliability question: `EXECUTOR_PLAYWRIGHT.md` + `docs/risks.md`
- Coverage or report-semantics question:
  - `VSCODE_API_COVERAGE_AUDIT.md`
  - `DETECTION_SEMANTICS.md`
- Security scaffold question:
  - `documents/adrs/0004-malicious-fixture-policy.md`
  - `tests/security/`
