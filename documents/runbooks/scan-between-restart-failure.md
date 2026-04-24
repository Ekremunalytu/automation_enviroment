# Runbook: Scan-Between VS Code Restart Failure

`Last Updated: 2026-04-24`

## Symptom

The first analysis in a fresh executor runs cleanly. The **second** analysis
in the same container fails at the `install_extension` step:

- Job `error_code` / `error_detail`: `install_extension` step failed with
  `rc=1` from `code --install-extension ...`.
- `automation_output` in the job record contains a tail (last ~500 chars)
  with markers like: `ipc handle`, `could not connect`,
  `extension host`, `singleton`, `lock file`, `already running`,
  `renderer process gone`.
- This happens even though the VSIX file is present and valid.

This failure mode is **already classified** as retryable in code
(see `_INSTALL_EXTENSION_RETRYABLE_MARKERS` below). If you are seeing it
after both the automatic retry and the automatic reset, something else is
wrong.

## Immediate Triage

```bash
# 1. Is VS Code alive inside the container?
docker exec automation_executor pgrep -fa 'code --remote-debugging-port' \
  || echo 'NO VSCODE (scan-between restart should have relaunched it)'

# 2. Any stale Chromium singleton lock files?
docker exec automation_executor bash -c \
  'ls -la /home/executor/.config/Code/SingletonLock \
                      /home/executor/.config/Code/SingletonCookie \
                      /home/executor/.config/Code/SingletonSocket 2>&1' \
  || echo 'none (good)'

# 3. Last 200 lines of executor output — install stderr tail lives here
docker logs automation_executor --tail 200 | grep -iE \
  'install-extension|singleton|ipc|lock file|extension host'
```

## Diagnose

**Scan-between restart flow** (source: [executor/flows/playwright/reset_state.py:171-189](../../executor/flows/playwright/reset_state.py)):

`reset_executor_state()` runs between analyses:

1. Prepare workspace
2. `terminate_vscode()` — SIGTERM to PIDs matching
   `--remote-debugging-port`, then up to 5s grace, then SIGKILL
   ([reset_state.py:101-127](../../executor/flows/playwright/reset_state.py))
3. Clear `/home/executor/.vscode/extensions/`
4. Clear `/home/executor/.vscode/logs/`
5. `cleanup_singleton_locks()` — remove these three files from
   `/home/executor/.config/Code/` (source: [reset_state.py:29-30](../../executor/flows/playwright/reset_state.py)):
   - `SingletonLock`
   - `SingletonCookie`
   - `SingletonSocket`
6. Launch VS Code via [executor/container/launch_vscode.sh](../../executor/container/launch_vscode.sh)

**Automatic install retry** (source: [executor/host.py:141-183](../../executor/host.py)):

`install_extension_in_executor()` tries the VSIX install once. On failure
with any marker from `_INSTALL_EXTENSION_RETRYABLE_MARKERS` (host.py:118-133):

```text
connection refused, econnrefused, could not connect, ipc handle, ipc hook,
singleton, already running, extension host, lock file, exited unexpectedly,
timed out, timeout, renderer process gone, target crashed
```

it calls `reload_vscode_window()`, waits 2 seconds, and retries once.
If the retry still fails, the full error — including the first attempt's
stderr tail — propagates to the job log.

**What to read if both auto-retry and reset failed:**

```bash
# Full install stderr for the failed job (in the DB)
psql -c "SELECT automation_output FROM analysis_jobs \
         WHERE job_id='<job_id>' AND current_step='install_extension';"

# Inspect what survived the reset (should be empty)
docker exec automation_executor ls -la \
  /home/executor/.vscode/extensions/ \
  /home/executor/.config/Code/ 2>&1 | head -30

# Can VS Code even start? Look for recent launch log
docker logs automation_executor --tail 500 | grep -E 'launch_vscode|VSCode PID'
```

## Recover

> The reset script is designed to be safe to call repeatedly. If a reset
> didn't clear the problem, going straight to a container recreate is
> usually faster than debugging in place.

**Step 1 — Manual in-container reset (non-destructive for host state):**

```bash
docker exec automation_executor python3 \
  /home/executor/flows/playwright/reset_state.py
```

This invokes the same `reset_executor_state()` path the workflow uses
between analyses.

**Step 2 — Verify the reset actually cleaned up:**

```bash
# Should be empty or missing
docker exec automation_executor bash -c \
  'ls /home/executor/.config/Code/SingletonLock 2>&1 || echo ok'

# Should show a *new* VS Code PID (not the one from before reset)
docker exec automation_executor pgrep -fa 'code --remote-debugging-port'
```

**Step 3 — If reset did not help, full container rebuild:**

```bash
make exec-down
make exec-up
```

This recreates the container entirely. `make exec-down && make exec-up` is
safe — it does not touch the PostgreSQL `analysis_jobs` table or `output/`
reports.

**Step 4 — Rerun the analysis.**

## Root-Cause Classes

- **Stale `SingletonLock` from a killed VS Code process.** Chromium keeps
  this file to enforce one-instance-per-data-dir. When the previous scan
  left it behind, the next VS Code launch thinks another instance owns the
  profile and refuses to start cleanly. This is the case the reset script
  specifically fixes.
- **Dead IPC socket (`SingletonSocket`).** `code --install-extension` talks
  to any running VS Code over IPC; a dangling socket from the previous
  process causes rc=1 with no useful stderr. Also fixed by the reset.
- **Extension host still shutting down at install time.** Handled by the
  2-second settle delay in the retry path; if it is still failing after
  that, the extension host may be wedged on an un-ejected workspace
  extension (look for `extrace.harness-extension` checksum errors earlier
  in the log).
- **Host Docker daemon under memory pressure.** If VS Code's Chromium can
  not start at all after the reset, check the host side:
  `docker stats automation_executor` and `dmesg | grep -i oom`.

## Code References

- [executor/flows/playwright/reset_state.py](../../executor/flows/playwright/reset_state.py)
  — `reset_executor_state`, `terminate_vscode`, `cleanup_singleton_locks`,
    lock-name constants
- [executor/container/launch_vscode.sh](../../executor/container/launch_vscode.sh)
  — shared launch script used by both `start.sh` (boot) and `reset_state.py`
    (scan-between)
- [executor/host.py](../../executor/host.py)
  — `install_extension_in_executor`, `_INSTALL_EXTENSION_RETRYABLE_MARKERS`,
    `_is_retryable_install_error`, `_AUTOMATION_TIMEOUT`
- [workflows/marketplace/analysis_execution.py](../../workflows/marketplace/analysis_execution.py)
  — surfaces the install stderr tail into the job message
- [workflows/marketplace/analysis_service.py](../../workflows/marketplace/analysis_service.py)
  — calls `executor_control.reset_sandbox()` before each analysis
- [executor/control.py](../../executor/control.py)
  — `reset_sandbox()` boundary
