# Executor Runtime Lane

`Last Updated: 2026-04-27`

Use this lane for Docker executor behavior, Playwright automation, the harness
extension, runtime capture, reset/reload behavior, and executor runbooks.

## Start Here

- `executor/control.py`
- `executor/host.py`
- `executor/container/`
- `executor/flows/harness_extension/`
- `executor/flows/playwright/`
- `tests/executor/`
- `tests/scanner/test_executor.py`
- `documents/EXECUTOR_PLAYWRIGHT.md`

## Invariants

- Sandbox execution stays isolated in Docker.
- Harness readiness must be explicit; W8-0 added epoch/pid-aware marker
  validation and typed `harness_*` failure reasons.
- Fatal UI crashes degrade automation health to `inconclusive` and stop the
  scenario loop unless retry-on-crash is explicitly enabled.
- Runtime capture is bounded; do not add raw body, raw argv, or environment
  dumps.
- noVNC/CDP/API LAN exposure remains an active risk until ADR 0007 W8-7
  enforcement lands.

## Tests And Checks

- `.venv/bin/pytest tests/executor/`
- `.venv/bin/pytest tests/scanner/test_executor.py`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
- `make demo-canary`

## Avoid

- Generic catch-all recovery that hides root cause.
- Unbounded waits or treating sleeps as proof of success.
- Adding new host-facing exposure without ADR 0007 follow-through.
