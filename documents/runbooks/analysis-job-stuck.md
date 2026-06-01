# Runbook: Analysis Job Stuck or Failed Unexpectedly

`Last Updated: 2026-05-30 (automation-timeout truth-up: 600→1200s / 10→20 min, host.py:188→:346, recover_interrupted_jobs :315→:384; prior: W13-3 cancelling-state, W13-4 close-pass, W14-4 complete/fail lock symmetry)`

## Symptom

Operator submitted `POST /api/marketplace/analyze/start` and now the
background job is not moving:

- `GET /api/marketplace/analyze/{job_id}` returns `{"status": "running", ...}`
  for > ~22 minutes without `current_step` or `message` changing.
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
automation timeout should fire on its own at 20 minutes (see below).

## Diagnose

**Job state machine** (source: [appcore/contracts/schema_defs/analysis_jobs.py:24-25,42](../../appcore/contracts/schema_defs/analysis_jobs.py)):

```python
AnalysisJobStatus = Literal[
    "queued", "running", "cancelling",
    "completed", "failed", "cancelled",
]
```

**State transitions** (W13-3 two-phase cancel; see ADR §
`active-work/W13-test-expansion-observability.md` Per-Item Detail W13-3):

```text
queued → running → completed
                 ↘ failed
                 ↘ cancelling → cancelled
                              ↘ failed   (recover_interrupted_jobs;
                                          worker died mid-drain)
```

`cancelling` is **non-terminal** — the row holds the partial unique
index lock (`uq_analysis_jobs_single_active`) so `reserve_job` blocks
new analyses until the worker drains and `finalize_cancelled_analysis_job`
promotes the row to terminal `cancelled`. `requested_cancel_at`
records when the drain was signalled (NULL for jobs that complete
normally).

**Canonical job steps** (source: [workflows/marketplace/job_service.py:59](../../workflows/marketplace/job_service.py)):

1. `reset_sandbox`
2. `install_extension`
3. `build_triggers`
4. `run_monitoring`
5. `finalize_report`

**Automation timeout** (source: [executor/host.py:346](../../executor/host.py)):
`_AUTOMATION_TIMEOUT = 1200` (20 min). After this, `executor.host` raises
`ExecutorError`, which [workflows/marketplace/analysis_execution.py](../../workflows/marketplace/analysis_execution.py)
catches and surfaces as a job failure. If more than 22 minutes have passed
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
docker exec automation_executor pkill -f executor.flows.playwright.entrypoint
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
 WHERE job_id='<job_id>' AND status IN ('running', 'cancelling');
```

> The `IN ('running', 'cancelling')` clause is W13-3-aware: a stuck
> job may be in either state. For the cancelling-specific case (worker
> observed cancel signal then died mid-drain), prefer the procedure in
> § Stuck in `cancelling` below — it leaves the row as `cancelled`
> rather than `failed`, which matches the operator's intent and the
> `requested_cancel_at` audit trail.

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

## Stuck in `cancelling`

W13-3 introduced a two-phase cancel: `POST /api/marketplace/analyze/cancel`
flips the job from `running` to non-terminal `cancelling` and signals
the worker thread to drain at the next cancel-poll point (5 sites in
`workflows/marketplace/analysis_service.py::execute_analysis_request`).
The worker exception handler then calls `finalize_cancelled_analysis_job`
to promote the row to terminal `cancelled`. While the row is `cancelling`
it still holds the single-active-job lock, so a new
`POST /api/marketplace/analyze/start` returns 409 Conflict.

### Symptom

- `GET /api/marketplace/analyze/{job_id}` returns
  `{"status": "cancelling", "requested_cancel_at": <epoch>, ...}` for
  more than a few seconds without transitioning to `cancelled`.
- `analysis_jobs` row: `status='cancelling'`, `requested_cancel_at`
  populated, `finished_at = NULL`.
- Operator UI shows "Stopping…" indefinitely.
- Subsequent `POST /api/marketplace/analyze/start` rejected with
  `ActiveAnalysisJobError` (409).

### Diagnose

```bash
# 1. How long has the row been cancelling?
psql -h localhost -U postgres -d automation -c \
  "SELECT job_id, requested_cancel_at, NOW() - to_timestamp(requested_cancel_at) AS draining_for \
     FROM analysis_jobs \
     WHERE status='cancelling' AND requested_cancel_at < EXTRACT(EPOCH FROM (NOW() - INTERVAL '60 seconds'));"

# 2. Is the worker thread still alive? (boot_id matches the live API process)
psql -h localhost -U postgres -d automation -c \
  "SELECT job_id, owner_boot_id FROM analysis_jobs WHERE status='cancelling';"
# If owner_boot_id != the API container's _PROCESS_BOOT_ID, the worker
# died and recover_interrupted_jobs will sweep on the next API boot.

# 3. Is the executor container even responsive?
docker exec automation_executor pgrep -fa 'code --remote-debugging-port' || echo 'NO VSCODE'
```

### Recover

**Step 1 — Wait one phase boundary (preferred).** If the worker is
still alive (boot_id matches), the next cancel-poll point fires within
seconds (worst case = the duration of the currently running phase
helper: `_reset_sandbox` / `_install_extension` / `_build_triggers` /
`_run_monitoring`). The row transitions `cancelling → cancelled`
automatically. If you cannot wait, jump to Step 2.

**Step 2 — Restart the API to trigger boot_id sweep.** If the worker
thread died mid-drain (e.g. API container OOM-killed), the row stays
`cancelling` until `recover_interrupted_jobs` runs at the next API
boot. The sweep predicate
([workflows/marketplace/job_service.py:384-390](../../workflows/marketplace/job_service.py))
catches any non-terminal row whose `owner_boot_id` does not match the
fresh boot's `_PROCESS_BOOT_ID` and routes it through
`_interrupt_job` with `terminal_status='failed'`. Result: the row
ends up `failed` (NOT `cancelled`) — design intent is
"intent-recorded-but-not-delivered". Restart:

```bash
make exec-down && make exec-up   # recreates API container; new boot_id
# OR for an API-only restart:
docker compose restart api
```

The runbook test
[tests/platform/storage/test_analysis_jobs_concurrency.py::test_recover_interrupted_jobs_finalizes_stuck_cancelling_to_failed](../../tests/platform/storage/test_analysis_jobs_concurrency.py)
pins this contract — if the recovery behavior ever changes (e.g. a
status-sweep helper added that finalizes cancelling distinctly to
`cancelled`), update Step 3 below to reflect the new terminal status.

**Step 3 — Manual finalize to `cancelled` (only if Step 1 + 2 are
infeasible).** This bypasses the worker-side step finalization and
forces the row terminal. Use only when you cannot restart the API
(e.g. cancelling row blocks an urgent re-analysis that operator must
launch immediately):

```sql
UPDATE analysis_jobs
   SET status='cancelled',
       finished_at=EXTRACT(EPOCH FROM NOW()),
       error_code='operator_cancel_finalize',
       error_detail='Manual finalize after stuck cancelling state.'
 WHERE job_id='<job_id>' AND status='cancelling';
```

> Step 3 is the equivalent of `lifecycle.finalize_cancelled_analysis_job`
> minus the step-record finalization. The row's `steps` column will
> show `run_monitoring` / etc. as `running` (worker never updated),
> not `cancelled`. Operators reading the UI may see a "stuck running
> step under a cancelled job" cosmetic issue. If that matters, restart
> the API and let the boot_id sweep run instead — it routes through
> `_interrupt_job` which DOES finalize step records.

## Root-Cause Classes

- **API process restart during an active job.** Handled by
  [workflows/marketplace/job_service.py:384 `recover_interrupted_jobs()`](../../workflows/marketplace/job_service.py).
  On API boot, scans `analysis_jobs` for active statuses
  (`queued`, `running`, `cancelling`) with a *different*
  `owner_boot_id` (per-process UUID) and marks them
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

- [appcore/storage/model_defs/analysis_job.py](../../appcore/storage/model_defs/analysis_job.py) — DB schema (W13-3 added `requested_cancel_at` column + widened `uq_analysis_jobs_single_active` partial unique index `WHERE` clause to include `cancelling`)
- [appcore/contracts/schema_defs/analysis_jobs.py](../../appcore/contracts/schema_defs/analysis_jobs.py) — status + step types (W13-3: `AnalysisJobStatus` Literal + `ANALYSIS_JOB_STATUSES` tuple now 6 members; `ACTIVE_ANALYSIS_JOB_STATUSES` includes `cancelling`)
- [appcore/storage/crud_ops/analysis_jobs/lifecycle.py](../../appcore/storage/crud_ops/analysis_jobs/lifecycle.py) — `cancel_analysis_job` (running → cancelling), `finalize_cancelled_analysis_job` (cancelling → cancelled), `complete_analysis_job` + `fail_analysis_job` (W14-4: now acquire `select(...).with_for_update()` and gate against `_TERMINAL_JOB_STATUSES` before mutating, mirroring the W13-3 cancel/finalize lock discipline so concurrent terminal writers serialize exactly-one-winner instead of silently overwriting), `recover_interrupted_analysis_jobs` (boot_id sweep)
- [alembic/versions/c8a2d4e91f5b_add_cancelling_status_to_analysis_jobs.py](../../alembic/versions/c8a2d4e91f5b_add_cancelling_status_to_analysis_jobs.py) — W13-3 migration; downgrade force-finalizes `cancelling` rows to `cancelled` before tightening the partial unique index
- [workflows/marketplace/router.py](../../workflows/marketplace/router.py) — `GET /api/marketplace/analyze/{job_id}` endpoint, `POST /api/marketplace/analyze/{job_id}/cancel`
- [workflows/marketplace/job_service.py](../../workflows/marketplace/job_service.py) — step reporter, boot-id ownership, `is_job_cancelled` (cancelled+cancelling), `finalize_cancelled_job` wrapper, `recover_interrupted_jobs`
- [workflows/marketplace/analysis_service.py](../../workflows/marketplace/analysis_service.py) — end-to-end orchestrator; `execute_analysis_request` 5 cancel-poll points; `run_analysis_job` exception handler dispatches finalize on AnalysisCancelledError + is_job_cancelled-true hard-error path
- [workflows/marketplace/analysis_execution.py](../../workflows/marketplace/analysis_execution.py) — `raise_if_cancelled` helper, ExecutorError → job error mapping
- [executor/control.py](../../executor/control.py) — workflow-visible executor boundary
- [executor/host.py](../../executor/host.py) — docker exec wrapper, timeouts
- [tests/architecture/test_cancel_poll_points.py](../../tests/architecture/test_cancel_poll_points.py) — W13-3.6 AST gate: 5-phase poll invariant + `raise_if_cancelled` public-name pin
- [tests/architecture/test_job_state_invariants.py](../../tests/architecture/test_job_state_invariants.py) — W13-3.6 AST gate: terminal/active state-set invariants + alembic body literal pin
