# Executor Runtime Lane

`Last Updated: 2026-05-11`

Use this lane for Docker executor behavior, Playwright automation, the harness
extension, runtime capture, reset/reload behavior, and executor runbooks.

## Start Here

- `executor/control.py`
- `executor/host.py`
- `executor/container/`
- `executor/flows/harness_extension/`
- `executor/flows/playwright/`
- `tests/executor/`
- `tests/executor/scanner/test_executor.py`
- `documents/EXECUTOR_PLAYWRIGHT.md`

## Invariants

- Sandbox execution stays isolated in Docker.
- Harness readiness must be explicit; W8-0 added epoch/pid-aware marker
  validation and typed `harness_*` failure reasons.
- Fatal UI crashes degrade automation health to `inconclusive` and stop the
  scenario loop unless retry-on-crash is explicitly enabled.
- Runtime capture is bounded; do not add raw body, raw argv, or environment
  dumps.
- noVNC/CDP/API LAN exposure is bounded by ADR 0007 W8-7 (landed
  `2026-04-29`): default-profile compose ports carry `127.0.0.1:`
  prefixes and host-side CDP exposure runs only under the `debug`
  compose profile via the `executor-cdp` sidecar. LAN exposure is opt-in via
  `EXTRACE_ALLOW_LAN=1` (host-side uvicorn/CORS) plus manual compose
  port editing per `documents/runbooks/lan-exposure.md`.

## Tests And Checks

- `.venv/bin/pytest tests/executor/`
- `.venv/bin/pytest tests/executor/scanner/test_executor.py`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
- `make demo-canary`

## Open Subsystem Doc Only If Needed

- `EXECUTOR_PLAYWRIGHT.md` (slim) → open one split based on the area
  you touch:
  - `executor/host-wrapper.md` for `executor/host.py`,
    `executor/control.py`, container boot, scan-between restart, API
    integration.
  - `executor/playwright-flow.md` for analysis phases, trigger payload,
    `executor/flows/playwright/` modules, fatal-UI-crash handling,
    reload behavior, entrypoint flags.
  - `executor/runtime-capture.md` for `runtime_capture/` subpackage,
    network/filesystem/extension-host capture.
- `runbooks/scan-between-restart-failure.md`,
  `runbooks/fatal-ui-crash.md`,
  `runbooks/live-capture-regression.md` — open the matching one when
  the failure mode is in flight.
- `active-work/W8-security.md` items W8-3, W8-4 (URI trigger +
  absolute paths) and W8-7 (ADR 0007 enforcement).
- `testing/executor-tests.md` for the executor-side test map.

## Avoid

- Generic catch-all recovery that hides root cause.
- Unbounded waits or treating sleeps as proof of success.
- Adding new host-facing exposure without ADR 0007 follow-through.
