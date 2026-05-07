# Runbook: Fatal UI Crash During Scan

`Last Updated: 2026-04-24`

## Symptom

Analysis job completes (or marks itself failed quickly) with a report that
flags the VS Code renderer died mid-run:

- `ActivationReport.automation_health.status = "inconclusive"` (not `ok` or
  `degraded`).
- At least one `ScenarioTrace` carries
  `failure_reason_code = "fatal_ui_crash"` and an `error_detail` string
  that was truncated to 500 chars.
- `summary.skipped_scenarios` contains one or more entries with
  `reason = "aborted_after_fatal_ui_crash"`, indicating the loop aborted
  the remaining scenarios on purpose.
- Executor stdout shows a line of the form: `FATAL: <scenario_name> -> ...`.
- In noVNC (`http://localhost:6080/vnc.html`) the workbench is a white/blank
  page or shows "Target crashed" / "renderer process gone".

This is **by design** since the post-W7 hardening on `2026-04-24`. Before
that change, the loop would keep trying to drive scenarios against a dead
Page and flood the report with cascading noise.

## Immediate Triage

```bash
# 1. Confirm the report actually flagged a fatal UI crash
# (replace <path> with the report file path)
jq '{
  health: .automation_health.status,
  failures: [.scenarios[] | select(.failure_reason_code=="fatal_ui_crash") | .name],
  aborted: [.summary.skipped_scenarios[]? | select(.reason=="aborted_after_fatal_ui_crash") | .name]
}' output/activation_report_*.json | tail -20

# 2. Is VS Code still running in-container?
docker exec automation_executor pgrep -fa 'code --remote-debugging-port' || echo 'NO VSCODE'

# 3. Extension host log tail (usually has the actual Chromium/Node crash)
docker exec automation_executor bash -c \
  'ls -t /home/executor/.vscode/logs/*/exthost*.log 2>/dev/null | head -1 | xargs tail -100'
```

## Diagnose

**What counts as a fatal UI error** (source: [executor/flows/playwright/automation.py:223-265](../../executor/flows/playwright/automation.py)):

`is_fatal_ui_error(exc, page)` returns `(True, "fatal_ui_crash")` on any of:

- The exception message contains one of these substrings:
  `Target crashed`, `renderer process gone`, `Target closed`,
  `Target page, context or browser has been closed`, `Connection closed`,
  `page has been closed`.
- `page.is_closed()` is true (or raises `PlaywrightError`).
- `page.context.is_closed()` is true.
- A 1500 ms liveness probe `page.wait_for_function("1 === 1")` raises.

When `is_fatal_ui_error` returns `True`:

- `_run_scenario_sequence` **fail-fasts**: no further scenarios run
  (source: [automation.py:268-329](../../executor/flows/playwright/automation.py)).
- `_mark_remaining_scenarios_aborted` populates
  `summary.skipped_scenarios` with `reason = "aborted_after_fatal_ui_crash"`
  (source: [automation.py:331-356](../../executor/flows/playwright/automation.py)).
- `automation_health.status` degrades to `inconclusive` in the health
  summary rollup (source: [executor/flows/playwright/health/summary.py](../../executor/flows/playwright/health/summary.py)).

**Where to read the crash detail:**

```bash
# Extract the exact exception string that triggered the classifier
jq -r '.scenarios[]
       | select(.failure_reason_code=="fatal_ui_crash")
       | "\(.name): \(.error_detail)"' \
   output/activation_report_*.json

# Playwright/Chromium stderr often logged to the executor stdout
docker logs automation_executor --tail 500 | grep -E 'FATAL:|renderer|Target crashed'

# Extension host crash log
docker exec automation_executor bash -c \
  'ls -t /home/executor/.vscode/logs/*/exthost*.log | head -1 | xargs cat' | tail -200
```

## Recover

**Step 1 — Full executor reset:**

```bash
make exec-down
make exec-up
```

This clears extensions, logs, Chromium singleton locks, and relaunches VS
Code. The new renderer gets a clean slate.

**Step 2 — Rerun the analysis:**

Call `POST /api/marketplace/analyze/start` with the same request body.

**Step 3 (optional) — Opt-in retry-on-crash for the rerun:**

If the failure is intermittent (e.g. OOM on a specific scenario),
`_run_scenario_sequence` supports a `retry_on_crash` mode that calls
[vscode.reload_workbench_window()](../../executor/flows/playwright/vscode/__init__.py)
once after a fatal. The flag is opt-in at the entrypoint runner and is
threaded through to `on_page_reloaded` so monitoring state rebinds to the
new Page handle (source: [automation.py:274](../../executor/flows/playwright/automation.py)).
This is a deliberate operator choice — the default path is still fail-fast
because a crashed renderer usually means corrupted state downstream.

## Root-Cause Classes

- **Extension-driven renderer OOM.** A target extension allocated enough
  memory to kill the Chromium renderer. The A1/A4 rule surface will still
  fire on any evidence captured *before* the crash; trust those signals.
- **Scenario stimulus too aggressive on a borderline workspace.** The
  `scenario_terminal_usage` stimulus was trimmed on `2026-04-24`
  specifically because `cat .env` / `pip list` / `npm ls --depth=0`
  repeatedly triggered `terminal_usage → Keyboard.type: Target crashed`
  (source: CLAUDE.md post-W7 continuation item 5). If your rerun also
  crashes on the same scenario, consider whether the stimulus itself is
  the culprit.
- **Stale UI blocker dialog from a prior scenario.** The per-scenario
  UI blocker probe ([automation.py:279-283](../../executor/flows/playwright/automation.py))
  tries to dismiss these before they freeze the next scenario. If you see
  `ui_blocker_detected` events before a fatal, the probe was trying.
- **Unrelated crash (Chromium bug, host OOM).** Rare; check
  `dmesg | grep -i oom` on the host and Docker resource limits.

## Code References

- [executor/flows/playwright/automation.py](../../executor/flows/playwright/automation.py)
  — `is_fatal_ui_error`, `_FATAL_UI_ERROR_MARKERS`, `FATAL_UI_CRASH_REASON`,
    `_run_scenario_sequence`, `_mark_remaining_scenarios_aborted`
- [executor/flows/playwright/health/summary.py](../../executor/flows/playwright/health/summary.py)
  — `automation_health.status` rollup logic
- [executor/flows/playwright/vscode/**init**.py](../../executor/flows/playwright/vscode/__init__.py)
  — `reload_workbench_window` (used by `retry_on_crash`)
- [packages/analysis_contracts/contracts.py](../../packages/analysis_contracts/contracts.py)
  — `ScenarioTrace`, `SkippedScenarioRecord`, `automation_health` contract
- [tests/executor/test_playwright_automation.py](../../tests/executor/test_playwright_automation.py)
  — `test_retry_on_crash_invokes_on_page_reloaded_callback`,
    `test_fail_fast_marks_remaining_scenarios_as_aborted`
