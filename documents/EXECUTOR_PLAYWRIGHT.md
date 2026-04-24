# Executor Playwright Architecture

`Last Updated: 2026-04-24`

The executor is ExTrace's dynamic-analysis sandbox. It runs a full VS Code GUI
session inside Docker, drives that session with Playwright, and exports
artifact-first analysis results into `output/`.

Open this only when changing executor/container/Playwright behavior or the API
integration points that drive it.

> **Security scope note (2026-04-23):** The executor is the analyzer's primary
> security surface, not merely an operational component. Trust boundary
> decisions are fixed by `adrs/0002-threat-model.md` §4:
>
> - VS Code binary trusted only if pinned.
> - Harness-extension checksum verification is enforced at executor startup
>   (`executor/container/start.sh` verifies
>   `/home/executor/flows/harness_extension.sha256` written by the
>   container Dockerfile). Landed in W5; do not regress.
> - Extension code at runtime is untrusted and never elevated by heuristic.
> - Docker daemon access from the API path is mediated through the
>   `ExecutorControl` boundary.
>
> Changes to executor behavior that affect any of these boundaries must update
> ADR 0002 §4 in the same change set.

> **Post-W7 hardening (2026-04-24):** two executor reliability fixes
> landed: (1) fatal UI-crash classification + fail-fast in
> `_run_scenario_sequence` (see *Fatal UI Crash Handling* below); (2)
> scan-between VS Code restart orchestrated by `reset_executor_state` via
> the shared `executor/container/launch_vscode.sh` script (see
> *Scan-Between Restart* below). The `attribution/` subpackage replaces
> the former `monitor_attribution.py` monolith with a three-file split
> behind a flat re-export facade.

This runtime still assumes:

- one operator
- one sandbox host
- one active background analysis job at a time
- rerun is acceptable recovery after interruption

## Runtime Layout

```text
executor/
  control.py
  host.py
  container/
    Dockerfile
    launch_vscode.sh
    requirements.txt
    start.sh
  flows/
    harness_extension/
      extension.js
      package.json
    playwright/
      annotation.py
      attribution/
        __init__.py
        events.py
        links.py
      automation.py
      capture.py
      commands.py
      debug.py
      editor.py
      entrypoint.py
      entrypoint_cli.py
      entrypoint_runner.py
      entrypoint_triggers.py
      health.py
      health_reconciliation.py
      health_runtime_facts.py
      health_summary.py
      keyboard.py
      language_samples.py
      monitor.py
      monitor_lifecycle.py
      monitor_payload.py
      monitor_records.py
      monitor_runtime.py
      monitor_sources.py
      monitor_support.py
      monitor_types.py
      panel.py
      reload_vscode.py
      report_builder.py
      runtime_capture/
      scenarios/
      reset_state.py
      settings.py
      sidebar.py
      signal_facts.py
      signal_policy.py
      signals.py
      stimulus.py
      stimulus_attempts.py
      stimulus_materializers.py
      stimulus_passes.py
      stimulus_prerequisites.py
      stimulus_types.py
      terminal.py
      triggers.py
      vscode.py
      wait_helpers.py
      workspace.py
      workspace_seed_data.py
      workspace_seed_home.py
      workspace_seed_project_1.py
      workspace_seed_project_2.py
      workspace_seed_project_3.py
```

## Container Boot Sequence

`executor/container/start.sh` boots the sandbox container.

The runtime is expected to:

1. start `Xvfb`
2. start the window manager stack
3. expose VNC/noVNC
4. prepare the workspace and bait files
5. write VS Code baseline settings
6. launch VS Code on `/workspace` via the shared
   `executor/container/launch_vscode.sh` script (also invoked by
   `reset_executor_state` during scan-between resets — single source of
   truth for the CDP launch command; `setsid` decouples VS Code lifetime
   from the invoking shell)

The executor container remains the only place where extension code should run.

## Host Control Surface

The API does not call Playwright modules directly. Workflow code goes through
`executor/control.py`, which delegates to `executor/host.py` and keeps the
workflow-visible boundary narrow.

High-level operations:

- `ExecutorControl.install_extension()`
- `ExecutorControl.reload_window()`
- `ExecutorControl.reset_sandbox()`
- `ExecutorControl.run_automation()`
- `ExecutorControl.cleanup_trigger()`

Current timeout model in `executor/host.py`:

- reload: 90 seconds
- reset: 90 seconds
- automation: 600 seconds

Non-zero automation exit codes are tolerated when a report may still have been
written; install and reset failures are not.

Container-side Playwright code is baked into the executor image via
`executor/container/Dockerfile`. After changing `executor/flows/` or the
container-visible `packages/` code copied into the image, rebuild with:

```bash
docker compose up -d --build executor
```

## Analysis Execution Phases

The marketplace workflow currently drives the executor in this order:

1. reset the sandbox
2. install the target `.vsix`
3. build a trigger payload unless analysis resolves to scenario-zero
   `skip_automation`
4. run `entrypoint.py --monitor`
5. export the report and update async job state

Async job steps are persisted through `workflows.marketplace.job_service` into
the Postgres-backed `analysis_jobs` table:

- `reset_sandbox`
- `install_extension`
- `build_triggers`
- `run_monitoring`
- `finalize_report`

## Trigger Payload Model

Host-side trigger planning is owned by `packages/analysis_planner` and is
surfaced through the compatibility facade in `workflows/marketplace/triggers.py`.
Container-side loading lives in `executor/flows/playwright/triggers.py`.

The payload now carries more than a scenario list. Important fields include:

- `analysis_profile`
  - currently defaults to `layered_deep`
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

- `entrypoint.py`
  - exported CLI surface for monitored runs
- `entrypoint_cli.py`, `entrypoint_runner.py`, `entrypoint_triggers.py`
  - thin split of CLI parsing, runtime loop, and trigger-loading behavior
- `automation.py`
  - built-in user-behavior scenarios such as coding, debug, terminal,
    authentication, and webview probes
- `scenarios/`
  - scenario registry and workbench/editing/runtime helpers for automation
- `stimulus.py`
  - layered pass execution and prerequisite materialization
- `monitor.py`
  - thin facade over the split monitor_* helpers and the `attribution/`
    subpackage; owns activation/file/network/log collection plus canonical
    report assembly
- `monitor_lifecycle.py`, `monitor_payload.py`, `monitor_records.py`,
  `monitor_runtime.py`, `monitor_sources.py`, `monitor_support.py`,
  `monitor_types.py`
  - scenario-event ledger, payload assembly, dataclass records, runtime
    loop, log-source discovery, helper utilities, and shared type exports
- `attribution/`
  - `events.py`: annotation + classification (`_annotate_network_events`,
    `_annotate_file_events`, `_annotate_process_events`,
    `_classify_event_attribution`, `_upgrade_inotify_correlations`,
    `_matches_extension_signature`, `_scenario_name_for_timestamp`, plus
    shared actor/artifact/epoch helpers)
  - `links.py`: evidence-bundle + scenario/temporal/noise/duplicate-file
    link builders (`_build_evidence_bundle`, `_build_scenario_links`,
    `_build_temporal_links`, `_build_duplicate_file_links`,
    `_build_noise_links`, `_nearest_activation`, `_temporal_confidence`,
    `_dedupe_evidence_links`)
  - `__init__.py`: flat re-export facade preserving the 29-name
    underscore-prefixed API + signal-layer shims
    (`_indexed_target_*`, `_build_risk_signals`, `_build_risk_summary`,
    `_build_signal_summary`); dual-import pattern supports both package
    mode and top-level executor mode (`playwright/` on `sys.path`)
- `runtime_capture/`
  - monitor-owned event parsing and capture helpers re-exported via
    `monitor.py` for backwards compatibility
- `report_builder.py`
  - summary construction and JSON serialization
- `health.py`, `health_reconciliation.py`, `health_runtime_facts.py`,
  `health_summary.py`
  - automation health, log health, runtime fact extraction, and coverage
    reconciliation; `health_summary.py` recognises `fatal_ui_crash` as a
    dominant failure-reason code that forces
    `automation_health.status = "inconclusive"` per ADR 0003 §5
- `signals.py`, `signal_facts.py`, `signal_policy.py`
  - risk signal generation and activation-layer signal summary policy
    (the detection-layer `Verdict` rollup lives in
    `packages/analysis_contracts/detection/rollup.py`)
- `annotation.py`
  - attribution helpers and summary logic
- `automation.py`
  - built-in user-behavior scenarios and `_run_scenario_sequence`, which
    routes `PlaywrightError` / `RuntimeError` / `ValueError` through
    `is_fatal_ui_error` (substring markers + `page.is_closed()` +
    `context.is_closed()` + ≤1.5 s liveness probe) and breaks the loop
    with `ScenarioTrace.failure_reason_code = "fatal_ui_crash"` +
    `error_detail`; opt-in `--retry-on-crash` routes through
    `vscode.reload_workbench_window`
- `capture.py`
  - extension-host log summarization
- `wait_helpers.py`
  - shared bounded-wait primitives for automation scenarios
- `workspace.py`, `workspace_seed_*.py`, `language_samples.py`
  - workspace fixture, per-project seed data, and bait-file support
- `commands.py`, `editor.py`, `sidebar.py`, `panel.py`, `terminal.py`,
  `settings.py`, `debug.py`, `keyboard.py`, `vscode.py`
  - focused UI interaction helpers
- `reload_vscode.py`
  - sandbox reload scripts invoked from the host wrapper
- `reset_state.py`
  - scan-between orchestrator: workspace setup → `terminate_vscode`
    (SIGTERM + 5 s grace + SIGKILL fallback on survivors) → clear
    `extensions/` + `logs/` → `cleanup_singleton_locks` (remove
    `SingletonLock` / `SingletonCookie` / `SingletonSocket` under
    `~/.config/Code`) → `launch_vscode` via the shared
    `executor/container/launch_vscode.sh`. Summary carries
    `terminated_vscode_processes`, `removed_singleton_locks`, and
    `relaunched_vscode_pid`.

## Fatal UI Crash Handling

`executor/flows/playwright/automation.py::_run_scenario_sequence` classifies
renderer-death via `is_fatal_ui_error` using explicit positive assertions:

- substring markers (`"target page, context or browser has been closed"`,
  `"renderer process gone"`, `"crashed"`, …)
- `page.is_closed()` / `context.is_closed()` checks
- a ≤1.5 s liveness probe against the page

Default is non-fatal (so transient timeouts do not poison otherwise-healthy
runs). On a fatal classification:

- the scenario loop breaks immediately (fail-fast, no cascading failures
  against a dead renderer)
- `ScenarioTrace` ([`monitor_records.py`](../executor/flows/playwright/monitor_records.py))
  records `failure_reason_code = "fatal_ui_crash"` plus
  `error_detail` (≤500 char) on the existing `metadata` channel
- `health_summary.py` treats `fatal_ui_crash` as a dominant failure reason
  that forces `automation_health.status = "inconclusive"` per ADR 0003 §5
  error dominance
- Opt-in `--retry-on-crash` routes the loop through
  `vscode.reload_workbench_window` with page rebinding (see
  *Retry-on-crash page rebinding* below)
- Fail-fast populates `SkippedScenarioRecord` entries for every
  unrun scenario via `_mark_remaining_scenarios_aborted`
  (`reason="aborted_after_fatal_ui_crash"`), so
  `summary.skipped_scenarios` honestly reflects the intended-vs-run
  scenario delta instead of silently dropping downstream scenarios

Contract mirrors: `packages/analysis_contracts/contracts.py::ScenarioTrace`
carries `failure_reason_code` + `error_detail` with
`extra="forbid"`; UI `contracts.ts` was regenerated.

Coverage lives in `tests/executor/test_playwright_crash_classifier.py` and
the extended `test_playwright_automation.py`,
`test_playwright_monitor_lifecycle.py`, and `test_playwright_health_summary.py`
modules. Fail-fast skipped-record semantics are covered by
`test_fail_fast_marks_remaining_scenarios_as_aborted` and
`test_fail_fast_aborts_on_reload_failure_when_retry_requested`.

### Retry-on-crash page rebinding

When `--retry-on-crash` is opted in, `_run_scenario_sequence`
accepts an `on_page_reloaded: Callable[[Page], None]` kwarg and
invokes it with the fresh `Page` returned from
`vscode.reload_workbench_window`. `entrypoint_runner.py` wires this
to a `nonlocal` closure that rebinds both its own `page` variable
and `mon.page`, so every scenario after the reload uses the live
handle — previously the retry path kept reusing the dead `Page`
and re-crashed every subsequent scenario.

Coverage: `test_retry_on_crash_invokes_on_page_reloaded_callback`
and `test_on_page_reloaded_not_called_on_reload_failure` in
`tests/executor/test_playwright_automation.py`;
`test_main_wires_ui_blocker_probe_and_page_reload_callbacks` in
`tests/executor/test_playwright_entrypoint.py`.

### UI blocker probe

`_run_scenario_sequence` accepts an optional
`ui_blocker_probe: Callable[[Page, str], None]` kwarg and calls it
with `(page, scenario_name)` before each scenario starts.
`entrypoint_runner.py` wires it to
`editor._dismiss_notification`: when a leftover dismissal dialog is
found, both `ui_blocker_detected` and `ui_blocker_dismissed`
automation events are recorded on `mon` with the scenario name in
the payload, and the next scenario's first keystroke proceeds
against a clean viewport.

Exceptions raised by the probe are caught narrowly
(`PlaywrightError, RuntimeError, ValueError`) so a failing probe
never short-circuits the scenario loop.

Coverage: `test_ui_blocker_probe_invoked_before_each_scenario` and
`test_ui_blocker_probe_failure_does_not_break_loop` in
`tests/executor/test_playwright_automation.py`.

### Benign-path stimulus hygiene

`scenario_terminal_usage` no longer issues high-output commands
(`cat .env`, `pip list`, `npm ls --depth=0`) — those collide with
target-owned secret-read + network-reconnaissance signals in
attribution and combined with aggressive keyboard typing were a
repeatable `terminal_usage → Keyboard.type: Target crashed`
trigger. The scenario now runs `ls -la`, `git status`,
`python --version`, `node --version`, `echo $PATH`, `pwd` with a
250 ms warm-up before each `type_in_terminal` call. Adversarial
stimulus belongs on the fixture lane, not the benign path — the
rule is spelled out in the scenario's docstring.

## Scan-Between Restart

After a scan finishes, the extension host can leave stale Chromium
`SingletonLock`/`SingletonCookie`/`SingletonSocket` artifacts plus an IPC
socket the next scan's `code --install-extension` will trip over (the
ESLint `onStartupFinished` + `extensionKind: workspace` +
`untrustedWorkspaces.supported: false` combination reliably hits this
race). `reset_executor_state` now orchestrates:

1. workspace setup (same as before)
2. `terminate_vscode`: SIGTERM + 5 s grace, SIGKILL fallback on survivors
3. clear `extensions/` + `logs/`
4. `cleanup_singleton_locks`: remove
   `SingletonLock` / `SingletonCookie` / `SingletonSocket` under
   `~/.config/Code`
5. `launch_vscode` via `executor/container/launch_vscode.sh` (shared with
   container boot)

The summary dict now carries `terminated_vscode_processes`,
`removed_singleton_locks`, and `relaunched_vscode_pid` for diagnostics.

Defense-in-depth:

- `executor/host.py::install_extension_in_executor` retries once through
  `reload_vscode_window` on transient IPC markers (`connection refused`,
  `ipc hook`, `singleton`, `renderer process gone`, `target crashed`, …)
- `workflows/marketplace/analysis_execution.py::install_failure_message`
  appends the last 500 chars of stderr to the failure line so the next
  regression of this class is diagnosable from the report alone

Coverage lives in `tests/executor/test_reset_state.py`, the extended
`tests/scanner/test_executor.py`, and
`tests/workflows/marketplace/test_analysis_execution_helpers.py`.

## Reload And Reconnect Behavior

- `commands.run_reload_window_command()` dispatches `Developer: Reload Window`
  without waiting for the original quick-input widget to finish tearing down.
- `vscode.py` owns CDP page discovery and `reconnect_to_workbench()`, which
  polls for a ready VS Code workbench page before and after reload.
- The reconnect helper is designed to survive transient post-reload CDP states
  such as detached pages, `chrome-error://chromewebdata/`, and temporary
  DevTools-only page lists.
- Both `entrypoint.py` and `reload_vscode.py` use this reconnect path so
  layered trigger runs do not fail closed just because the first post-reload
  page snapshot is incomplete.

## Entrypoint Flags

`executor/flows/playwright/entrypoint.py` currently supports:

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

## API Integration

Current executor-backed API surface:

- `POST /api/marketplace/analyze`
  - synchronous request/response analysis
- `POST /api/marketplace/analyze/start`
  - async analysis job start
- `GET /api/marketplace/analyze/{job_id}`
  - async job status

Persisted job state lives in:

```text
PostgreSQL `analysis_jobs` rows
```

Reports are written to:

```text
output/activation_report_<publisher>.<name>-<version>-<runid>.json
```

Job snapshots include an `owner_boot_id`; if the API process restarts while a
job is still marked active, the next load converts that job into a failed,
interrupted state.

## UI Integration

The SPA uses the executor pipeline through three routes:

- `/marketplace`
  - search, download, and launch async analysis
- `/simulation`
  - poll job state and inspect the live report
- `/reports`
  - inspect the finalized report artifact

Relevant frontend files:

- `ui/src/features/marketplace/MarketplacePage.tsx`
- `ui/src/features/simulation/SimulationPage.tsx`
- `ui/src/features/reports/ReportsPage.tsx`

## Supported Operational Commands

```bash
make exec-build
make exec-up
make exec-shell
make exec-test
make exec-run
make sim-all                        # UI-stimulus stress: scenarios w/o target ext.
make sim-target TARGET=pub.name \   # target-extension smoke (activation hygiene)
                [TRIGGERS=/path/to/payload.json] \
                [SCENARIO=<name>]
make sim-demo
make sim-list
make sim-run SCENARIO=<name>
```

Note the `sim-all` vs `sim-target` split introduced 2026-04-24:

- `sim-all` is the UI-stimulus stress lane (scenarios w/o a target
  extension). Its reports are **inconclusive by design**; it answers
  "do the scenarios themselves survive a full pass?" not "does this
  extension activate cleanly?"
- `sim-target` (required `TARGET=publisher.name`) runs
  `entrypoint.py --monitor --target-extension-id $(TARGET)` with
  optional `TRIGGERS` / `SCENARIO` passthrough; this is the correct lane
  for "did a normal extension activate cleanly?"
- Missing `TARGET` exits non-zero with a usage hint.

## Current Limitations

- Activation reports remain file-backed while async job metadata is DB-backed.
- The pipeline still depends on Docker exec success and VS Code timing.
- Live capture (`make test-security-live`) is the most fragile detection
  surface; tshark / runtime-capture changes can silently regress
  `tls_client_hello` matching even though `make test-security` (offline)
  stays green. Docker-based A1 canary structural diff (`make exec-up &&
  make exec-run` against `t1-a1-credential-read-to-network-canary`)
  remains the canonical user-side smoke.
- Only one background analysis job is allowed at a time.
- This is not a queue-backed worker system and should not be documented as one.
