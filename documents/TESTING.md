# Testing Guide

`Last Updated: 2026-04-15`

The test suite mirrors the refactored architecture: platform tests validate
shared `appcore/` code, workflow tests validate business slices, executor tests
cover sandbox helpers, and smoke coverage exercises the full marketplace to
report pipeline.

## Test Layout

```text
tests/
  conftest.py
  test_health.py
  executor/
    conftest.py
    test_playwright_automation.py
    test_playwright_commands.py
    test_playwright_entrypoint.py
    test_playwright_monitor.py
    test_playwright_stimulus.py
    test_reset_state.py
    test_workspace.py
  platform/
    api/
      test_config.py
      test_deps.py
    contracts/
      test_schemas.py
    storage/
      test_crud.py
    test_canonical_imports.py
  scanner/
    test_executor.py
  smoke/
    test_marketplace_analysis_smoke.py
  workflows/
    activation_reports/
      test_router.py
    extension_catalog/
      test_package_parser.py
      test_router.py
      test_service.py
    marketplace/
      test_client.py
      test_router.py
      test_triggers.py
```

UI tests live in:

```text
ui/src/**/*.test.ts(x)
```

UI smoke coverage currently lives in:

```text
ui/smoke/
```

## Database Strategy

- Python tests use PostgreSQL, not SQLite.
- `tests/conftest.py` builds the test URL from `DATABASE_URL` first, then falls
  back to `postgresql://postgres:postgres@localhost:5434/test_db`.
- The `test_engine` fixture creates tables once per test session and drops them
  afterward.
- The `db_session` fixture opens a transaction per test and rolls it back for
  isolation.

## Main Fixtures

- `test_engine`
  - session-scoped SQLAlchemy engine
- `db_session`
  - per-test transactional session
- `client`
  - FastAPI `TestClient` with `get_db` override
- `sample_extension_data`
  - reusable extension payload for storage and API tests

## Commands

```bash
make test
make test-cov
make test-local
make test-ci
.venv/bin/pytest
.venv/bin/pytest tests/workflows/marketplace/test_router.py -v
.venv/bin/pytest tests/smoke/test_marketplace_analysis_smoke.py -v -m smoke
cd ui && npm run test
cd ui && npm run test:smoke
```

Notes:

- Default `pytest` excludes the smoke suite via `pyproject.toml`.
- `make test-local` starts `postgres_test` and then runs the Python suite.
- `make test-ci` also builds and waits for the executor container so the smoke
  path can run.
- `npm run test:smoke` maps to `ui/smoke/run-smoke.mjs`.

## Smoke Acceptance

Smoke acceptance currently lives in
`tests/smoke/test_marketplace_analysis_smoke.py`.

It validates:

- `/api/marketplace/download`
- `/api/marketplace/analyze/start`
- async job polling via `/api/marketplace/analyze/{job_id}`
- report retrieval via `/api/activations/{name}`
- target-observed and automation-health semantics in the exported report

The smoke fixture is currently pinned to `ms-python.python` and uses the
executor container directly.

## Coverage Focus

### Platform

- settings and dependency injection
- Pydantic contracts
- storage CRUD behavior and uniqueness protection
- canonical import surface

### Workflows

- extension catalog parsing and persistence orchestration
- activation report file listing/reading behavior
- marketplace search/download/analyze routes
- trigger selection and failure handling

### Executor

- Docker exec wrapper behavior
- Playwright automation helpers
- monitor/report generation and workspace reset
- entrypoint flag behavior

### UI

- route pages under `ui/src/features/`
- shared evidence and simulation widgets
- adapters and rule-draft helpers under `ui/src/lib/`

## Current Gaps

- Smoke coverage is still centered on the pinned `ms-python.python` fixture.
- Executor reliability is the most failure-prone path, so unit coverage still
  needs periodic backing from real-container smoke runs.
- Dynamic-analysis runs are artifact-first and file-backed, so tests assert JSON
  snapshots rather than DB-backed run history.
- The SPA has route-level coverage, but API-contract drift still matters because
  there is no generated client.

## Expectations for New Work

- New shared module in `appcore/`: add or update tests under `tests/platform/`.
- New workflow behavior: add tests under the matching `tests/workflows/<name>/`.
- New executor helper: add or update `tests/executor/` and, when needed,
  `tests/scanner/test_executor.py`.
- New end-to-end analysis reliability behavior: extend `tests/smoke/`.
- Database schema changes require an Alembic migration plus updated tests.
