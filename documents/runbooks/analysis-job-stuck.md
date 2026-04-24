# Runbook: Analysis Job Stuck or Failed Unexpectedly

`Last Updated: 2026-04-24`

## Symptom

Operator submitted `POST /api/marketplace/analyze/start` and now the
background job is not moving:

- `GET /api/marketplace/analyze/{job_id}` returns `{"status": "running", ...}`
  for > ~12 minutes without `current_step` or `message` changing.
- `analysis_jobs` row: `started_at` set, `finished_at = NULL`,
  `error_detail = NULL`, `error_code = NULL`.
- UI simulation page stalls on a step with no new events.

## Immediate Triage

```bash
# 1. Is the executor container alive?
docker ps --filter name=automation_executor --format '{{.Status}}'

# 2. Is VS Code actually running inside the container?
docker exec automation_executor pgrep -fa 'code --remote-debugging-port' || echo 'NO VSCODE'

# 3. Which step did the job stop on?
# (substitute your preferred SQL client)
psql -h localhost -U postgres -d automation -c \
  "SELECT job_id, status, current_step, message, started_at \
     FROM analysis_jobs WHERE status='running' \
     ORDER BY started_at DESC LIMIT 5;"
```

If the executor is dead → skip to **Recover → Full executor reset**.
If VS Code is alive but the job is stuck on `run_monitoring` → the
automation timeout should fire on its own at 10 minutes (see below).

## Diagnose

**Job state machine** (source: [appcore/contracts/schema_defs/analysis_jobs.py:40](../../appcore/contracts/schema_defs/analysis_jobs.py)):

```python
AnalysisJobStatus = Literal["queued", "running", "completed", "failed"]
```

**Canonical job steps** (source: [workflows/marketplace/job_service.py:59](../../workflows/marketplace/job_service.py)):

1. `reset_sandbox`
2. `install_extension`
3. `build_triggers`
4. `run_monitoring`
5. `finalize_report`

**Automation timeout** (source: [executor/host.py:188](../../executor/host.py)):
`_AUTOMATION_TIMEOUT = 600` (10 min). After this, `executor.host` raises
`ExecutorError`, which [workflows/marketplace/analysis_execution.py](../../workflows/marketplace/analysis_execution.py)
catches and surfaces as a job failure. If more than 12 minutes have passed
with no state transition, the executor-side subprocess was likely killed
outside the timeout path.

**What to read:**

```bash
# Full job record
psql -c "SELECT * FROM analysis_jobs WHERE job_id='<job_id>' \G"

# Last 200 lines of executor stdout/stderr
docker logs automation_executor --tail 200

# In-container VS Code process tree
docker exec automation_executor ps auxf | grep -E 'code|playwright|entrypoint'

# Latest activation report (if the monitoring phase reached it)
ls -lt output/activation_report*.json | head -5
```

## Recover

> **Only one background analysis should run at a time.** Never start a new
> job before the stuck one is marked `failed`.

**Step 1 — Kill the hung automation (non-destructive, keeps executor):**

```bash
docker exec automation_executor pkill -f entrypoint_runner
# gives executor.host's subprocess watch a chance to exit cleanly
```

If this clears the `run_monitoring` wedge, the job transitions to
`failed` on its own via the ExecutorError path.

**Step 2 — Force job failure in DB (only if step 1 did not help):**

```sql
UPDATE analysis_jobs
   SET status='failed',
       finished_at=NOW(),
       error_code='operator_timeout',
       error_detail='Job terminated by operator after hang'
 WHERE job_id='<job_id>' AND status='running';
```

**Step 3 — Full executor reset (destructive for in-container state):**

```bash
make exec-down
make exec-up
```

This recreates the container from scratch: clears extensions, clears logs,
removes Chromium singleton locks, relaunches VS Code. It does *not* touch
`output/` reports or the PostgreSQL `analysis_jobs` table.

**Step 4 — Rerun:**

Start a new job via `POST /api/marketplace/analyze/start` with the same
request body. Do not try to "resume" the old `job_id` — jobs are not
resumable by design.

## Root-Cause Classes

- **API process restart during an active job.** Handled by
  [workflows/marketplace/job_service.py:315 `recover_interrupted_jobs()`](../../workflows/marketplace/job_service.py).
  On API boot, scans `analysis_jobs` for `status in ('queued','running')`
  with a *different* `owner_boot_id` (per-process UUID) and marks them
  failed with the message "Analysis job was interrupted by an API restart.
  Start a new run." If you see this message, it means the API was bounced
  while you had a job in flight — the job cannot be salvaged, start a new
  one.
- **Executor docker-exec transient failure.** Handled by
  [executor/control.py](../../executor/control.py): retries up to 3 times
  on docker daemon connection errors before raising.
- **VS Code renderer crash mid-scenario.** Covered by the separate
  [Fatal UI crash runbook](fatal-ui-crash.md).
- **Install hitting a stale IPC socket.** Covered by the separate
  [Scan-between restart failure runbook](scan-between-restart-failure.md).

## Code References

- [appcore/storage/model_defs/analysis_job.py](../../appcore/storage/model_defs/analysis_job.py) — DB schema
- [appcore/contracts/schema_defs/analysis_jobs.py](../../appcore/contracts/schema_defs/analysis_jobs.py) — status + step types
- [workflows/marketplace/router.py](../../workflows/marketplace/router.py) — `GET /api/marketplace/analyze/{job_id}` endpoint
- [workflows/marketplace/job_service.py](../../workflows/marketplace/job_service.py) — step reporter, boot-id ownership, interrupted-job recovery
- [workflows/marketplace/analysis_service.py](../../workflows/marketplace/analysis_service.py) — end-to-end orchestrator
- [workflows/marketplace/analysis_execution.py](../../workflows/marketplace/analysis_execution.py) — ExecutorError → job error mapping
- [executor/control.py](../../executor/control.py) — workflow-visible executor boundary
- [executor/host.py](../../executor/host.py) — docker exec wrapper, timeouts
