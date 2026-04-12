# Testing Guide

`Last Updated: 2026-03-06`

The test suite now mirrors the refactored architecture. Platform tests validate shared modules in `appcore/`, workflow tests cover the canonical business packages, and executor tests cover Playwright sandbox helpers.

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
```

Useful single-file examples:

```bash
.venv/bin/pytest tests/workflows/marketplace/test_router.py -v
.venv/bin/pytest tests/platform/test_canonical_imports.py -v
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

## Current Gaps

- No end-to-end test currently persists a complete dynamic analysis run into a future DB schema, because that schema does not exist yet.
- Sandbox tests are mostly unit-level and mock the container boundary.
- Activation report ingestion remains filesystem-driven, so those tests focus on JSON files rather than DB fixtures.

## Expectations for New Work

- New shared module: add tests under `tests/platform/` if it lives in `appcore/`.
- New workflow behavior: add tests under the matching `tests/workflows/<name>/`.
- New sandbox helper: add or update tests under `tests/executor/`.
- If a change alters the database schema, include an Alembic migration and update tests accordingly.
