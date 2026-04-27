# Marketplace And Analysis Lane

`Last Updated: 2026-04-27`

Use this lane for marketplace search/download, sandbox analysis orchestration,
async analysis jobs, cancellation, trigger planning, and report handoff.

## Start Here

- `workflows/marketplace/router.py`
- `workflows/marketplace/client.py`
- `workflows/marketplace/analysis_service.py`
- `workflows/marketplace/analysis_execution.py`
- `workflows/marketplace/job_service.py`
- `workflows/marketplace/trigger_service.py`
- `packages/analysis_planner/`
- `tests/workflows/marketplace/`

## Invariants

- Only one background analysis job is expected in the single-user appliance
  model.
- Async job metadata is DB-backed in `analysis_jobs`; activation reports are
  still file-backed artifacts under `output/`.
- Workflow code should reach Docker/executor mechanics through
  `executor.control`.
- Trigger planning must keep unsupported, skipped, failed, and verified states
  explicit in reports.

## Tests And Checks

- `.venv/bin/pytest tests/workflows/marketplace/`
- `.venv/bin/pytest tests/smoke/ -m smoke` when behavior is end-to-end.
- `make sim-target TARGET=publisher.name` for target-extension smoke.
- `make sim-all` only for UI-stimulus stress without target extension.

## Avoid

- Treating `sim-all` as target-aware analysis.
- Equating `target_extension_observed=true` with a healthy scan; inspect
  `automation_health`, `run_quality`, event attempts, and target-owned
  evidence.
- Silent cancellation or heartbeat failures.
