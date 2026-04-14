# Executor Playwright Architecture

`Last Updated: 2026-04-14`

The executor is ExTrace's dynamic-analysis sandbox. It runs a full VS Code GUI
session inside Docker, drives that session with Playwright, and exports
artifact-first analysis results into `output/`.

This runtime still assumes:

- one operator
- one sandbox host
- one active background analysis job at a time
- rerun is acceptable recovery after interruption

## Runtime Layout

```text
executor/
  host.py
  container/
    Dockerfile
    requirements.txt
    start.sh
  flows/
    harness_extension/
      extension.js
      package.json
    playwright/
      annotation.py
      automation.py
      capture.py
      commands.py
      debug.py
      editor.py
      entrypoint.py
      health.py
      keyboard.py
      language_samples.py
      monitor.py
      panel.py
      reload_vscode.py
      report_builder.py
      reset_state.py
      settings.py
      sidebar.py
      signals.py
      stimulus.py
      terminal.py
      triggers.py
      vscode.py
      workspace.py
```

## Container Boot Sequence

`executor/container/start.sh` boots the sandbox container.

The runtime is expected to:

1. start `Xvfb`
2. start the window manager stack
3. expose VNC/noVNC
4. prepare the workspace and bait files
5. write VS Code baseline settings
6. launch VS Code on `/workspace`

The executor container remains the only place where extension code should run.

## Host Control Surface

The API does not call Playwright modules directly. It goes through
`executor/host.py`, which wraps `docker exec`.

High-level operations:

- `install_extension_in_executor()`
- `reload_vscode_window()`
- `reset_executor_sandbox_state()`
- `run_playwright_automation()`

Current timeout model in `executor/host.py`:

- reload: 60 seconds
- reset: 90 seconds
- automation: 600 seconds

Non-zero automation exit codes are tolerated when a report may still have been
written; install and reset failures are not.

## Analysis Execution Phases

The marketplace workflow currently drives the executor in this order:

1. reset the sandbox
2. install the target `.vsix`
3. build a trigger payload unless an explicit scenario was requested
4. run `entrypoint.py --monitor`
5. export the report and update async job state

Async job steps currently tracked in `workflows.marketplace.job_store`:

- `reset_sandbox`
- `install_extension`
- `build_triggers`
- `run_monitoring`
- `finalize_report`

## Trigger Payload Model

Host-side trigger planning lives in `workflows/marketplace/triggers.py`.
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
  - CLI surface for demo mode, named scenarios, shuffled runs, and monitored
    report generation
- `automation.py`
  - built-in user-behavior scenarios such as coding, debug, terminal,
    authentication, and webview probes
- `stimulus.py`
  - layered pass execution and prerequisite materialization
- `monitor.py`
  - activation/file/network/log collection plus canonical report assembly
- `report_builder.py`
  - summary construction and JSON serialization
- `health.py`
  - automation health, log health, run quality, and coverage reconciliation
- `signals.py`
  - risk signal generation and verdict policy
- `annotation.py`
  - attribution helpers and summary logic
- `capture.py`
  - extension-host log summarization
- `workspace.py`, `language_samples.py`
  - workspace fixture and bait-file support
- `commands.py`, `editor.py`, `sidebar.py`, `panel.py`, `terminal.py`,
  `settings.py`, `debug.py`, `keyboard.py`, `vscode.py`
  - focused UI interaction helpers
- `reload_vscode.py`, `reset_state.py`
  - sandbox cleanup and reload scripts invoked from the host wrapper

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

Persisted job state lives at:

```text
output/analysis_jobs/<job_id>.json
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
make sim-all
make sim-demo
make sim-list
make sim-run SCENARIO=<name>
```

## Current Limitations

- Dynamic-analysis persistence is still file-backed rather than DB-backed.
- The pipeline still depends on Docker exec success and VS Code timing.
- Only one background analysis job is allowed at a time.
- This is not a queue-backed worker system and should not be documented as one.
