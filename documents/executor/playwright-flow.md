# Playwright Flow + Module Responsibilities

`Last Updated: 2026-04-29`

Container-side Playwright orchestration: phases, trigger payload,
module map, fatal-UI-crash handling, reload behavior. Top-level
executor doc: [`../EXECUTOR_PLAYWRIGHT.md`](../EXECUTOR_PLAYWRIGHT.md).
Capture/replay mechanics: [`runtime-capture.md`](runtime-capture.md).

## Analysis Execution Phases

Marketplace workflow drives the executor in this order:

1. reset the sandbox
2. install the target `.vsix`
3. build a trigger payload unless analysis resolves to scenario-zero
   `skip_automation`
4. run `entrypoint.py --monitor`
5. export the report and update async job state

Async job steps persisted through `workflows.marketplace.job_service`
into `analysis_jobs`:

- `reset_sandbox`
- `install_extension`
- `build_triggers`
- `run_monitoring`
- `finalize_report`

## Trigger Payload Model

Host-side trigger planning is owned by `packages/analysis_planner` and
surfaced through `workflows/marketplace/triggers.py`. Container-side
loading lives in `executor/flows/playwright/triggers.py`.

The payload carries:

- `analysis_profile` (defaults to `layered_deep`)
- `selected_scenarios`
- `official_selected_scenarios`
- `heuristic_selected_scenarios`
- `coverage_tracks`, `coverage_matrix`, `coverage_summary`
- `stimulus_passes`
- `event_attempts`
- `prerequisite_results`
- `extra_custom_editor_files`
- `extra_commands`
- `auth_provider_ids`
- `webview_view_ids`
- `uri_trigger`
- `run_task_trigger`
- `run_walkthrough_trigger`

The executor deletes the trigger JSON after loading it.

## Playwright Module Responsibilities

### Entrypoint

- `entrypoint.py` — exported CLI surface for monitored runs.
- `entrypoint_cli.py`, `entrypoint_runner.py`, `entrypoint_triggers.py`
  — thin split of CLI parsing, runtime loop, trigger-loading.

### Automation + Scenarios

- `automation.py` — built-in user-behavior scenarios (coding, debug,
  terminal, authentication, webview probes) and
  `_run_scenario_sequence`. Routes `PlaywrightError` / `RuntimeError` /
  `ValueError` through `is_fatal_ui_error` (see "Fatal UI Crash
  Handling" below).
- `scenarios/` — scenario registry and workbench/editing/runtime
  helpers for automation.
- `stimulus.py` — layered pass execution and prerequisite
  materialization.

### Monitor + Attribution

- `monitor.py` — thin facade over the split `monitor_*` helpers and the
  `attribution/` subpackage. Owns activation/file/network/log
  collection plus canonical report assembly.
- `monitor_lifecycle.py`, `monitor_payload.py`, `monitor_records.py`,
  `monitor_runtime.py`, `monitor_sources.py`, `monitor_support.py`,
  `monitor_types.py` — scenario-event ledger, payload assembly,
  dataclass records, runtime loop, log-source discovery, helper
  utilities, shared type exports.
- `attribution/`:
  - `events.py` — annotation + classification
    (`_annotate_network_events`, `_annotate_file_events`,
    `_annotate_process_events`, `_classify_event_attribution`,
    `_upgrade_inotify_correlations`, `_matches_extension_signature`,
    `_scenario_name_for_timestamp`, plus shared
    actor/artifact/epoch helpers).
  - `links.py` — evidence-bundle + scenario/temporal/noise/
    duplicate-file link builders (`_build_evidence_bundle`,
    `_build_scenario_links`, `_build_temporal_links`,
    `_build_duplicate_file_links`, `_build_noise_links`,
    `_nearest_activation`, `_temporal_confidence`,
    `_dedupe_evidence_links`).
  - `__init__.py` — flat re-export facade preserving the 29-name
    underscore-prefixed API + signal-layer shims (`_indexed_target_*`,
    `_build_risk_signals`, `_build_risk_summary`,
    `_build_signal_summary`); dual-import pattern supports both
    package mode and top-level executor mode (`playwright/` on
    `sys.path`).

### Health + Signals

- `health.py`, `health_reconciliation.py`, `health_runtime_facts.py`,
  `health_summary.py` — automation health, log health, runtime fact
  extraction, coverage reconciliation. `health_summary.py` recognises
  `fatal_ui_crash` as a dominant failure-reason code that forces
  `automation_health.status = "inconclusive"` per ADR 0003 §5.
- `signals.py`, `signal_facts.py`, `signal_policy.py` — risk signal
  generation and activation-layer signal summary policy.
  Detection-layer `Verdict` rollup lives in
  `packages/analysis_contracts/detection/rollup.py`.

### Report + Capture

- `report_builder.py` — summary construction and JSON serialization.
- `runtime_capture/` — see [`runtime-capture.md`](runtime-capture.md).
- `capture.py` — extension-host log summarization.
- `annotation.py` — attribution helpers and summary logic.

### UI Interaction Helpers

`commands.py`, `editor.py`, `sidebar.py`, `panel.py`, `terminal.py`,
`settings.py`, `debug.py`, `keyboard.py`, `vscode.py` — focused UI
interaction helpers. `wait_helpers.py` — shared bounded-wait
primitives.

### Workspace + Reload

- `workspace.py`, `workspace_seed_*.py`, `language_samples.py` —
  workspace fixture, per-project seed data, bait-file support.
- `reload_vscode.py` — sandbox reload scripts invoked from the host
  wrapper.
- `reset_state.py` — scan-between orchestrator (detail in
  `host-wrapper.md` §"Scan-Between Restart").

### URI Trigger (W8-3)

- `uri_validation.py` — argv-form URI trigger launcher with scheme
  allow-list (`vscode`, `vscode-insiders`, `http`, `https`).
  `validate_uri_scheme` + `run_uri_trigger`. Code comment references
  `documents/active-work/W8-security.md` item W8-3.

## Entrypoint Flags

```bash
python3 /home/executor/flows/playwright/entrypoint.py --demo
python3 /home/executor/flows/playwright/entrypoint.py --list
python3 /home/executor/flows/playwright/entrypoint.py --monitor
python3 /home/executor/flows/playwright/entrypoint.py --monitor --scenario coding_session
python3 /home/executor/flows/playwright/entrypoint.py --monitor --triggers /results/triggers.json --report-path /results/report.json
```

Important flags:

- `--demo`
- `--scenario <name>`
- `--list`
- `--shuffle`
- `--monitor`
- `--report-path <path>`
- `--triggers <path>`
- `--reload-before-run`
- `--target-extension-id <publisher.name>`

## Fatal UI Crash Handling

`_run_scenario_sequence` classifies renderer-death via
`is_fatal_ui_error` using explicit positive assertions:

- substring markers (`"target page, context or browser has been closed"`,
  `"renderer process gone"`, `"crashed"`, …)
- `page.is_closed()` / `context.is_closed()` checks
- a ≤1.5 s liveness probe against the page

Default is non-fatal so transient timeouts do not poison
otherwise-healthy runs. On fatal classification:

- the scenario loop breaks immediately (fail-fast, no cascading
  failures against a dead renderer)
- `ScenarioTrace` (`monitor_records.py`) records
  `failure_reason_code = "fatal_ui_crash"` plus `error_detail` (≤500
  char) on the existing `metadata` channel
- `health_summary.py` treats `fatal_ui_crash` as a dominant failure
  reason that forces `automation_health.status = "inconclusive"` per
  ADR 0003 §5 error dominance
- Opt-in `--retry-on-crash` routes the loop through
  `vscode.reload_workbench_window` with page rebinding (see below)
- Fail-fast populates `SkippedScenarioRecord` entries for every unrun
  scenario via `_mark_remaining_scenarios_aborted`
  (`reason="aborted_after_fatal_ui_crash"`), so
  `summary.skipped_scenarios` honestly reflects the intended-vs-run
  scenario delta instead of silently dropping downstream scenarios.

Contract mirrors:
`packages/analysis_contracts/contracts.py::ScenarioTrace` carries
`failure_reason_code` + `error_detail` with `extra="forbid"`; UI
`contracts.ts` regenerated.

Coverage:
`tests/executor/test_playwright_crash_classifier.py`,
`test_playwright_automation.py`,
`test_playwright_monitor_lifecycle.py`,
`test_playwright_health_summary.py`. Fail-fast skipped-record
semantics covered by
`test_fail_fast_marks_remaining_scenarios_as_aborted` and
`test_fail_fast_aborts_on_reload_failure_when_retry_requested`.

### Retry-On-Crash Page Rebinding

When `--retry-on-crash` is opted in, `_run_scenario_sequence` accepts
an `on_page_reloaded: Callable[[Page], None]` kwarg and invokes it
with the fresh `Page` returned from `vscode.reload_workbench_window`.
`entrypoint_runner.py` wires this to a `nonlocal` closure that rebinds
both its own `page` variable and `mon.page`, so every scenario after
the reload uses the live handle. Previously the retry path kept reusing
the dead `Page` and re-crashed every subsequent scenario.

Coverage:
`test_retry_on_crash_invokes_on_page_reloaded_callback`,
`test_on_page_reloaded_not_called_on_reload_failure` in
`tests/executor/test_playwright_automation.py`;
`test_main_wires_ui_blocker_probe_and_page_reload_callbacks` in
`tests/executor/test_playwright_entrypoint.py`.

### UI Blocker Probe

`_run_scenario_sequence` accepts an optional
`ui_blocker_probe: Callable[[Page, str], None]` kwarg and calls it
with `(page, scenario_name)` before each scenario starts.
`entrypoint_runner.py` wires it to `editor._dismiss_notification`:
when a leftover dismissal dialog is found, both `ui_blocker_detected`
and `ui_blocker_dismissed` automation events are recorded on `mon`
with the scenario name in the payload, and the next scenario's first
keystroke proceeds against a clean viewport.

Exceptions raised by the probe are caught narrowly
(`PlaywrightError, RuntimeError, ValueError`) so a failing probe never
short-circuits the scenario loop.

Coverage:
`test_ui_blocker_probe_invoked_before_each_scenario`,
`test_ui_blocker_probe_failure_does_not_break_loop` in
`tests/executor/test_playwright_automation.py`.

### Benign-Path Stimulus Hygiene

`scenario_terminal_usage` no longer issues high-output commands
(`cat .env`, `pip list`, `npm ls --depth=0`) — those collide with
target-owned secret-read + network-reconnaissance signals in
attribution and combined with aggressive keyboard typing were a
repeatable `terminal_usage → Keyboard.type: Target crashed` trigger.
The scenario now runs `ls -la`, `git status`, `python --version`,
`node --version`, `echo $PATH`, `pwd` with a 250 ms warm-up before
each `type_in_terminal` call. Adversarial stimulus belongs on the
fixture lane, not the benign path — the rule is spelled out in the
scenario's docstring.

## Reload And Reconnect Behavior

- `commands.run_reload_window_command()` dispatches
  `Developer: Reload Window` without waiting for the original
  quick-input widget to finish tearing down.
- `vscode.py` owns CDP page discovery and
  `reconnect_to_workbench()`, which polls for a ready VS Code
  workbench page before and after reload.
- The reconnect helper is designed to survive transient post-reload
  CDP states such as detached pages, `chrome-error://chromewebdata/`,
  and temporary DevTools-only page lists.
- Both `entrypoint.py` and `reload_vscode.py` use this reconnect path
  so layered trigger runs do not fail closed just because the first
  post-reload page snapshot is incomplete.
- `vscode.py::reload_workbench_window` `unlink()`s
  `_HARNESS_READY_PATH` before dispatching the reload (post-W7
  hardening 2026-04-25); the harness extension's `activate()` is
  `async` and awaits `writeHarnessReadyMarker()` so a write failure
  surfaces a clean `HarnessUnavailableError` timeout instead of
  stale-marker confusion.
