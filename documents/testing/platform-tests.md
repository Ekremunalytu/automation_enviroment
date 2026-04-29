# Platform Tests

`Last Updated: 2026-04-29`

`tests/platform/` — shared platform contracts, API runtime, engine,
storage. Lane shape: [`../TESTING.md`](../TESTING.md). Layer file map:
[`../structure/test-layout.md`](../structure/test-layout.md).

## Subdirectories

### `tests/platform/api/`

- `test_app_runtime.py` — FastAPI app boot + route registration.
- `test_config.py` — Pydantic settings (`appcore/api/config.py`).
- `test_deps.py` — dependency injection (`get_db`).
- `test_fixtures.py` — local fixture wiring sanity.

### `tests/platform/contracts/`

- `test_schemas.py` — Pydantic v2 contract round-trips.
- `test_analysis_fixture_baselines.py` — pinned fixture report shape.
- `test_detection_report.py` — `DetectionReport` invariants.
- `test_report_builder_contract.py` — `report_builder.py` output shape.
- `test_verdict_rollup.py` — verdict aggregation
  (clean / suspicious / inconclusive / malicious).

### `tests/platform/engine/`

- `test_rule_runner.py` — detection-engine rule runner against
  fixtures; consumes only contracts.

### `tests/platform/storage/`

- `test_crud.py` — `appcore/storage/crud.py` write paths + uniqueness
  protection on `(publisher, name, version)`.
- `test_analysis_jobs.py` — durable async job lifecycle, recovery,
  in-flight race gap (`[FOLLOWUP analysis-jobs-race]` referenced by
  test comment at line 183).

### `tests/platform/test_canonical_imports.py`

- Top-level guard: each canonical entrypoint
  (`from appcore.storage import crud`,
  `from appcore.contracts.schemas import ...`,
  `from packages.analysis_planner import ...`,
  etc.) imports cleanly.

## DB Marker Discipline

DB-backed tests carry `@pytest.mark.requires_db`; integration tests
needing real wiring beyond DB carry `@pytest.mark.integration`.

Open hygiene gap: three `tests/workflows/marketplace/test_router.py`
tests (`test_run_analysis_job_*`) attempt to bind to postgres without
`requires_db`; flagged in `POST_POC_BACKLOG.md` and
`REFACTOR_STATUS.md` archive.

## Adding A Platform Test

- New shared `appcore/` module → mirror the path under
  `tests/platform/`.
- New schema field → extend `test_schemas.py` and the relevant
  `test_*_baselines.py`.
- New CRUD operation → extend `test_crud.py`; add Alembic migration if
  the storage shape changes.
- New verdict rule → `test_verdict_rollup.py`.
- New canonical import path → `test_canonical_imports.py`.
