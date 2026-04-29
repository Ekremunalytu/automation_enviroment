# Host Wrapper + Container Boot

`Last Updated: 2026-04-29`

`executor/host.py`, `executor/control.py`, container boot sequence,
scan-between restart, API integration. Top-level executor doc:
[`../EXECUTOR_PLAYWRIGHT.md`](../EXECUTOR_PLAYWRIGHT.md).

## Container Boot Sequence

`executor/container/start.sh` boots the sandbox container.

1. start `Xvfb`
2. start the window manager stack
3. expose VNC/noVNC
4. prepare the workspace and bait files
5. write VS Code baseline settings
6. launch VS Code on `/workspace` via the shared
   `executor/container/launch_vscode.sh` script (also invoked by
   `reset_executor_state` during scan-between resets — single source of
   truth for the CDP launch command; `setsid` decouples VS Code lifetime
   from the invoking shell).

The executor container remains the only place where extension code
should run.

## Host Control Surface

The API does not call Playwright modules directly. Workflow code goes
through `executor/control.py`, which delegates to `executor/host.py`
and keeps the workflow-visible boundary narrow.

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

Non-zero automation exit codes are tolerated when a report may still
have been written; install and reset failures are not.

Container-side Playwright code is baked into the executor image via
`executor/container/Dockerfile`. After changing `executor/flows/` or
the container-visible `packages/` code copied into the image, rebuild
with:

```bash
docker compose up -d --build executor
```

## Scan-Between Restart

After a scan finishes, the extension host can leave stale Chromium
`SingletonLock` / `SingletonCookie` / `SingletonSocket` artifacts plus
an IPC socket the next scan's `code --install-extension` will trip
over (the ESLint `onStartupFinished` + `extensionKind: workspace` +
`untrustedWorkspaces.supported: false` combination reliably hits this
race).

`reset_executor_state` orchestrates:

1. workspace setup (same as before)
2. `terminate_vscode`: SIGTERM + 5 s grace, SIGKILL fallback on
   survivors
3. clear `extensions/` + `logs/`
4. `cleanup_singleton_locks`: remove
   `SingletonLock` / `SingletonCookie` / `SingletonSocket` under
   `~/.config/Code`
5. `launch_vscode` via `executor/container/launch_vscode.sh` (shared
   with container boot)

Summary dict carries `terminated_vscode_processes`,
`removed_singleton_locks`, `relaunched_vscode_pid` for diagnostics.

### Defense-In-Depth

- `executor/host.py::install_extension_in_executor` retries once
  through `reload_vscode_window` on transient IPC markers
  (`connection refused`, `ipc hook`, `singleton`,
  `renderer process gone`, `target crashed`, …).
- `workflows/marketplace/analysis_execution.py::install_failure_message`
  appends the last 500 chars of stderr to the failure line so the next
  regression of this class is diagnosable from the report alone.

Coverage: `tests/executor/test_reset_state.py`,
`tests/scanner/test_executor.py`,
`tests/workflows/marketplace/test_analysis_execution_helpers.py`.

## API Integration

Current executor-backed API surface:

- `POST /api/marketplace/analyze` — synchronous request/response
  analysis.
- `POST /api/marketplace/analyze/start` — async analysis job start.
- `GET /api/marketplace/analyze/{job_id}` — async job status.
- `POST /api/marketplace/analyze/{job_id}/cancel` — async cancel
  (returns 404 on missing, 409 on terminal-state via
  `cancel_analysis_job` under `with_for_update()` pessimistic lock).

Persisted job state lives in PostgreSQL `analysis_jobs` rows. Reports
are written to:

```text
output/activation_report_<publisher>.<name>-<version>-<runid>.json
```

Job snapshots include an `owner_boot_id`; if the API process restarts
while a job is still marked active, the next load converts that job
into a failed, interrupted state.

### Cancel Heartbeat

The monitoring heartbeat in `analysis_execution.py` polls
`is_job_cancelled` every 5 s and triggers
`executor_control.reset_sandbox(reload_window=True)` on cancel; the
resulting `ExecutorError` is converted to `AnalysisCancelledError` so
`run_analysis_job` returns silently. Open hygiene gaps tracked in
`POST_POC_BACKLOG.md` `[FOLLOWUP simulation-progress-cancel]` parent.
