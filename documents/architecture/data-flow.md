# Request Flows

`Last Updated: 2026-04-29`

Step-by-step traces for the five canonical request flows. Open this when
debugging an end-to-end path or adding a new flow that crosses
`workflows/` ↔ `appcore/` ↔ `executor/`.

Top-level shape and module map:
[`../ARCHITECTURE.md`](../ARCHITECTURE.md).

## 1. Static Catalog Ingestion

`POST /createExtension`

1. `workflows.extension_catalog.router`
2. `workflows.extension_catalog.service.create_extension_by_name`
3. `workflows.extension_catalog.manifest_reader` +
   `workflows.extension_catalog.manifest_parser`
4. `appcore.contracts.schemas`
5. `appcore.storage.crud`
6. PostgreSQL

Notes:

- `ExtensionSchema` and related nested contracts are built before
  persistence.
- Duplicate inserts fail closed on the `(publisher, name, version)`
  constraint.

## 2. Marketplace Download

`POST /api/marketplace/download`

1. `workflows.marketplace.client.download_and_extract_vsix`
2. `workflows.extension_catalog.service.create_extension_from_directory`
3. `appcore.storage.crud`

Notes:

- Manifest identity is checked against the requested
  publisher/name/version.
- Existing catalog entries return a usable success response with the
  existing DB id instead of silently re-inserting.
- W8-1 zip-bomb / entry-traversal guard applies inside
  `_extract_vsix_to_dir`.

## 3. Sandbox Analysis

`POST /api/marketplace/analyze` or `POST /api/marketplace/analyze/start`

1. `workflows.marketplace.router`
2. `workflows.marketplace.analysis_service`
3. `workflows.marketplace.trigger_service`
4. `executor.control`
5. `executor.host`
6. `executor/flows/playwright/entrypoint.py`
7. `executor/flows/playwright/monitor.py` (facade over `attribution/`,
   `runtime_capture/`, `signals.py`, `signal_facts.py`, scenario/health
   helpers)
8. `executor/flows/playwright/report_builder.py`
9. `output/activation_report_*.json`

Async job mode persists step-tracked metadata in PostgreSQL
`analysis_jobs` through `appcore.storage.crud` and
`workflows.marketplace.job_service`.

### Cancel Path

`POST /api/marketplace/analyze/{job_id}/cancel`

- Returns the job snapshot (`404` on missing, `409` on terminal-state)
  via `cancel_analysis_job` under a `with_for_update()` pessimistic
  lock.
- The monitoring heartbeat in `analysis_execution.py` polls
  `is_job_cancelled` every 5 s and triggers
  `executor_control.reset_sandbox` on cancel.
- `run_analysis_job` converts the resulting `ExecutorError` to
  `AnalysisCancelledError` and returns silently.

### Notes

- The async endpoint serializes work to one active job.
- Persisted jobs carry an `owner_boot_id`; if the API restarts mid-run,
  the job is marked failed on the next load.
- Trigger planning may resolve to layered execution or a scenario-zero
  `skip_automation` run for non-executable fixtures.
- The workflow-side trigger contract is `TriggerPlan` only; the old
  tuple shim is removed.
- Startup fails fast if job recovery or migration state for
  `analysis_jobs` is unavailable.
- `ANALYSIS_JOB_STATUSES` includes `cancelled`; the `analysis_jobs.status`
  column is plain `String` (no DB CHECK constraint).

## 4. Activation Report Browsing

`GET /api/activations`, `GET /api/activations/latest`,
`GET /api/activations/{name}`

1. `workflows.activation_reports.router`
2. `output/activation_report*.json`

Notes:

- Report reads retry transient `OSError` failures.
- Latest-report reads fall back to the next-most-recent valid JSON file
  if the newest file is still being written.

## 5. Analyst UI Loop

1. `/marketplace` — search results, download, then launch async
   analysis.
2. `/simulation` — poll job state and load the in-progress report by
   `report_path`.
3. `/reports` — inspect report slices, attribution, risk signals, and
   rule draft output (Inspector drawer + event-scoped
   `RuleDraftSection` since UI v3 minimal-completion 2026-04-29).
