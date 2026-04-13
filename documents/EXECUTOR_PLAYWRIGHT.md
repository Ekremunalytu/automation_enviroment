# Executor Playwright Architecture

`Last Updated: 2026-04-13`

The executor is the dynamic-analysis sandbox. It runs a full VS Code GUI session inside Docker and drives that GUI with Playwright over CDP.

## Runtime Layout

```text
executor/
  container/
    Dockerfile
    requirements.txt
    start.sh
  flows/playwright/
    entrypoint.py
    automation.py
    monitor.py
    workspace.py
    reload_vscode.py
    reset_state.py
    commands.py
    debug.py
    editor.py
    keyboard.py
    language_samples.py
    panel.py
    settings.py
    sidebar.py
    terminal.py
    triggers.py
    vscode.py
```

## Container Boot Sequence

`executor/container/start.sh` is the sandbox entrypoint.

1. Start `Xvfb`
2. Start `openbox`
3. Start `x11vnc`
4. Prepare workspace and honeypot files
5. Write VS Code settings
6. Launch VS Code on `/workspace`
7. Start noVNC on port `6080`

The sandbox is intended to be isolated. Extension code should execute only inside this container.

## Control Surface

The API does not call Playwright modules directly. It goes through `executor/host.py`, which provides the Docker exec control surface configured from `appcore.api.config.settings.executor`.

Available high-level operations:

- install extension `.vsix`
- reload VS Code window
- reset sandbox state
- run Playwright automation entrypoint

## Playwright Modules

- `entrypoint.py`
  - CLI entrypoint used by `make exec-run` and marketplace analysis endpoints.
- `automation.py`
  - Scenario runner.
- `monitor.py`
  - Collects activation evidence and writes JSON reports.
- `workspace.py`
  - Creates bait files and helper workspace content.
- `triggers.py`
  - Trigger payload helpers used during analysis.
- `commands.py`, `editor.py`, `sidebar.py`, `terminal.py`, `panel.py`, `settings.py`, `debug.py`
  - Focused UI interaction helpers.
- `reload_vscode.py`
  - Reloads VS Code after extension installation.
- `reset_state.py`
  - Clears extensions/logs and restores baseline state.

## API Integration

The marketplace workflow currently uses two analysis modes:

- `POST /api/marketplace/analyze`
  - synchronous request/response flow
- `POST /api/marketplace/analyze/start`
  - background job flow

Background job state is persisted to:

```text
output/analysis_jobs/<job_id>.json
```

Activation reports are written as:

```text
output/activation_report_<publisher>.<name>-<version>-<runid>.json
```

## UI Integration

The Vite + React + Tailwind UI uses:

- `/marketplace` to search, download, and start analysis
- `/simulation` to poll job status and surface step-level progress
- `/reports` to inspect generated activation reports

Relevant frontend paths:

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
make sim-list
make sim-run SCENARIO=<name>
```

## Current Limitations

- Dynamic analysis results are file-backed; there is no DB schema yet for analysis runs or telemetry events.
- The marketplace workflow depends on executor/container availability and Docker exec success.
- Full end-to-end reliability still depends on VS Code startup timing and reload behavior.
