# Executor Tests

`Last Updated: 2026-05-05`

`tests/executor/` and `tests/scanner/`. Lane shape:
[`../TESTING.md`](../TESTING.md). Layer file map:
[`../structure/test-layout.md`](../structure/test-layout.md). Executor
subsystem reference: [`../EXECUTOR_PLAYWRIGHT.md`](../EXECUTOR_PLAYWRIGHT.md).

## `tests/scanner/`

- `test_executor.py` — Docker exec wrapper:
  retry-after-reload, non-transient no-retry guard, reload-failure
  preserves original error.

## `tests/executor/`

### Automation + Helpers

- `test_playwright_automation.py` — automation orchestration.
- `test_playwright_commands.py` — VS Code command dispatch.
- `test_playwright_helpers.py` — common helpers.
- `test_playwright_entrypoint.py` — entrypoint flag + reload behavior;
  updated for W8-3 argv-form invocation
  (`("run_uri_trigger", "vscode://...")` in the call-order list).

### Crash + Health

- `test_playwright_crash_classifier.py` — `is_fatal_ui_error` (11
  tests including transient-timeout false-positive guard).
- `test_playwright_health_summary.py` — `fatal_ui_crash` dominance in
  `automation_health.status`.

### Monitor (Split Across 4 Files)

- `test_playwright_monitor_attribution.py` — `attribution/`
  subpackage (events.py, links.py, facade re-export).
- `test_playwright_monitor_lifecycle.py` — scenario-event ledger.
- `test_playwright_monitor_package_import.py` — paket vs top-level
  executor import mode (W9 closed `2026-05-04` via PR #9).
- `test_playwright_monitor_runtime.py` — runtime loop.

### Reset + Reload

- `test_reset_state.py` — terminate / SIGKILL escalation / singleton
  cleanup / launch-script success+failure / orchestration order
  (11 tests; rewritten post-W7).
- `test_playwright_reload.py` — reload handling + the post-2026-04-25
  marker delete-before-reload fix.

### Runtime Bits

- `test_signal_policy.py` — signal aggregation and post-W6 thresholds.
- `test_workspace.py` — workspace seeding/reset.

## `tests/executor/security/`

- `test_uri_trigger_injection.py` — W8-3, 26 adversarial cases.
  Detail in [`security-tests.md`](security-tests.md).

## Architecture Tests Touching Executor

- `tests/architecture/test_uri_trigger_shell_pattern.py` (W8-3) —
  AST detector for `xdg-open '<f-string>'` shell-template pattern,
  excluding `executor/flows/playwright/uri_validation.py` and `tests/`.

## Adding An Executor Test

- New Playwright helper → `tests/executor/test_playwright_<area>.py`.
- New monitor sub-area → match the four-way split
  (attribution / lifecycle / package-import / runtime).
- New reset orchestration step → `test_reset_state.py`.
- New executor-side adversarial defense → `tests/executor/security/`.
- New Docker exec wrapper change → `tests/scanner/test_executor.py`.
- New cross-cutting architecture detector → `tests/architecture/`.
