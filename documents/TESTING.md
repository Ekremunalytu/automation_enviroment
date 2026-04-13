# Testing Guide

`Last Updated: 2026-04-13`

The test suite now mirrors the refactored architecture. Platform tests validate shared modules in `appcore/`, workflow tests cover the canonical business packages, and executor tests cover Playwright sandbox helpers.

The default test workflow is optimized for fast local iteration in a single-user sandbox project, not for full end-to-end smoke execution on every run.

## Test Layout

```text
tests/
  conftest.py
  test_health.py
  executor/
    conftest.py
    test_playwright_automation.py
    test_playwright_monitor.py
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

## Database Strategy

- Tests use PostgreSQL, not SQLite.
- Default local test database:
  - `postgresql://postgres:postgres@localhost:5434/test_db`
- Start `postgres_test` via `make test-local` before running the full suite locally.
- `tests/conftest.py` creates all tables once per session and rolls back each test transaction.

## Main Fixtures

- `test_engine`
  - Session-scoped SQLAlchemy engine.
- `db_session`
  - Function-scoped transactional session with rollback.
- `client`
  - FastAPI `TestClient` with `get_db` override.
- `sample_extension_data`
  - Reusable extension payload for storage and API tests.

## Commands

```bash
make test
make test-cov
make test-local
make test-ci
.venv/bin/pytest
.venv/bin/pytest -m smoke
.venv/bin/pytest tests/workflows/marketplace/test_router.py -v
cd ui && npm run test
```

Default `pytest` excludes the smoke suite through `pyproject.toml`.

Smoke acceptance lives in `tests/smoke/test_marketplace_analysis_smoke.py`.
Those tests use the pinned local `ms-python.python` VSIX fixture under `extensions/`
and require the `automation_executor` container to be running and healthy.
Run smoke explicitly when you need end-to-end confidence across API, Docker exec,
Playwright automation, and report generation.

When executor Python code changes, rebuild that container first so smoke runs against
the current Playwright monitor implementation:

```bash
docker-compose up -d --build executor
```

Useful examples:

```bash
.venv/bin/pytest tests/platform/test_canonical_imports.py -v
.venv/bin/pytest tests/workflows/marketplace/test_router.py -v
.venv/bin/pytest tests/smoke/test_marketplace_analysis_smoke.py -v
```

## Coverage Focus

### Platform

- `appcore.api.config`
- `appcore.api.deps`
- `appcore.contracts.schemas`
- `appcore.storage.crud`
- canonical import surfaces

### Workflows

- Extension catalog router, service, and parser
- Activation report router and file reading behavior
- Marketplace client, router, and trigger selection

### Executor

- Playwright orchestration helpers
- Monitor/report assembly
- Workspace and reset behavior
- Explicit smoke acceptance for `download -> analyze/start -> executor -> report`
  - Baseline `ms-python.python` smoke run now pins the executor to `coding_session`
    so local acceptance stays fast while still exercising the end-to-end path.

### UI

- `ui/src/features/**/*.test.tsx`
- `ui/src/components/**/*.test.tsx`
- `ui/src/lib/**/*.test.ts`

## Current Gaps

- Smoke coverage is currently mandatory only for the pinned `ms-python.python` fixture.
- Additional real-fixture coverage for `ms-vscode.cpptools` and `ms-toolsai.jupyter` is still pending.
- Activation report ingestion remains filesystem-driven, so those tests focus on JSON files rather than DB fixtures.
- Some executor-facing tests can still be slower than typical unit tests because they preserve sandbox-oriented behavior.

## Expectations for New Work

- New shared module: add tests under `tests/platform/` if it lives in `appcore/`.
- New workflow behavior: add tests under the matching `tests/workflows/<name>/`.
- New sandbox helper: add or update tests under `tests/executor/`.
- New end-to-end automation reliability behavior: add or update smoke coverage under `tests/smoke/`.
- If a change alters the database schema, include an Alembic migration and update tests accordingly.
