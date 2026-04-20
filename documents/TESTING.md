# Testing Guide

`Last Updated: 2026-04-20`

The test suite mirrors the refactored architecture: platform tests validate
shared `appcore/` code, workflow tests validate business slices, executor tests
cover sandbox helpers, architecture tests enforce import boundaries, security
tests validate the malicious-fixture scaffold, and smoke coverage exercises the
full marketplace-to-report pipeline.

## Test Layout

```text
tests/
  conftest.py
  test_health.py
  architecture/
    test_import_graph.py
  executor/
    test_container_dockerfile.py
    test_playwright_automation.py
    test_playwright_commands.py
    test_playwright_entrypoint.py
    test_playwright_helpers.py
    test_playwright_monitor.py
    test_playwright_reload.py
    test_playwright_stimulus.py
    test_reset_state.py
    test_workspace.py
  platform/
    api/
      test_app_runtime.py
      test_config.py
      test_deps.py
      test_fixtures.py
    contracts/
      test_analysis_fixture_baselines.py
      test_schemas.py
    storage/
      test_analysis_jobs.py
      test_crud.py
    test_canonical_imports.py
  security/
    test_fixture_hygiene.py
    test_rule_coverage.py
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
      test_analysis_planner.py
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

- DB-backed persistence tests use PostgreSQL; DB-free lanes use mocked sessions.
- `tests/conftest.py` builds the test URL from `DATABASE_URL` first, then falls
  back to `postgresql://postgres:postgres@localhost:5434/test_db`.
- The `test_engine` fixture creates tables once per test session and drops them
  afterward, but only when a test requests DB fixtures.
- The `db_session` fixture opens a transaction per test and rolls it back for
  isolation.

## Main Fixtures

- `test_engine`
  - session-scoped SQLAlchemy engine
- `db_session`
  - per-test transactional session
- `client`
  - FastAPI `TestClient` with `get_db` override
- `db_client`
  - FastAPI `TestClient` that reuses the per-test transactional DB session
- `runtime_client`
  - FastAPI `TestClient` that patches request-time and background-worker
    `SessionLocal` factories to the real test PostgreSQL engine
- `mock_session`
  - reusable `MagicMock(spec=Session)` for DB-free tests
- `sample_extension_data`
  - reusable extension payload for storage and API tests

## Commands

```bash
make test
make test-unit
make test-integration
make test-smoke
make test-cov
make test-local
make test-ci
make test-security
.venv/bin/ruff check .
.venv/bin/python scripts/generate_ui_contracts.py --check
cd ui && npm run lint:boundaries
.venv/bin/pytest
.venv/bin/pytest -m "not smoke and not requires_db and not integration"
.venv/bin/pytest -m "(requires_db or integration) and not smoke"
.venv/bin/pytest -m "requires_db"
.venv/bin/pytest tests/workflows/marketplace/test_router.py -v
.venv/bin/pytest tests/smoke/test_marketplace_analysis_smoke.py -v -m smoke
cd ui && npm run test
cd ui && npm run test:smoke
```

Notes:

- Default `pytest` excludes the smoke suite via `pyproject.toml`.
- Unit lane: `pytest -m "not smoke and not requires_db and not integration"`.
- Integration lane: `pytest -m "(requires_db or integration) and not smoke"`.
- DB lane: `pytest -m "requires_db"`.
- Smoke lane: `pytest -m "smoke"`.
- `make test-unit`, `make test-integration`, and `make test-smoke` map to the
  same lane definitions so failures can be isolated without re-deriving marker
  expressions each time.
- `make test-local` starts `postgres_test` and then runs the default Python
  suite (`not smoke`), which includes DB-backed tests.
- `make test-ci` also builds and waits for the executor container so the smoke
  path can run.
- `make test-security` currently runs the malicious-fixture hygiene and PoC
  canary-coverage contract tests under `tests/security/`.
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

The smoke lane currently covers:

- `ms-python.python`
- layered chat/tool verification honesty on the same `ms-python.python` flow
- `extrace.fixture-chat`

The scenario-zero `extrace.fixture-theme` fixture is currently validated
through contract and executor unit tests rather than smoke acceptance.

The smoke client uses `runtime_client`, so both the request handlers and the
async job worker talk to the real test PostgreSQL database instead of a mocked
session when exercising `analysis_jobs`.

The smoke lane includes executor process and log diagnostics when a job fails
or stops making progress on one step for two minutes. This is aimed at the
recurring `reload_vscode.py` / CDP reconnect stall so the failure mode is
visible before the full poll timeout or immediately when the worker fails.

## Test Lanes

### Unit

- Pure helper logic and mocked orchestration paths.
- Should not require Postgres or the executor container.
- Typical marker expression: `not smoke and not requires_db and not integration`.

### Integration

- Real Postgres persistence and other non-executor infrastructure seams.
- Prefer `@pytest.mark.requires_db` for DB-backed tests; reserve
  `@pytest.mark.integration` for non-smoke infra cases that still need real
  wiring.
- Typical marker expression: `(requires_db or integration) and not smoke`.

### Smoke

- Full marketplace download/analyze/report flow against the real executor
  container.
- Must stay narrow and diagnostic-heavy because runtime hangs are the dominant
  failure mode.
- Marker expression: `smoke`.

### Architecture

- Repo-wide import graph enforcement.
- Ensures `packages/` stay framework-agnostic, `executor/` avoids `appcore/`
  and `workflows/`, and workflows reach sandbox mechanics only through
  `executor.control`.

### Platform

- Settings and dependency injection.
- Pydantic contracts.
- Storage CRUD behavior and uniqueness protection.
- Durable analysis-job lifecycle and recovery.

### Workflows

- Extension catalog parsing and persistence orchestration.
- Activation report file listing/reading behavior.
- Marketplace search/download/analyze routes.
- Trigger selection and failure handling.

### Executor

- Docker exec wrapper behavior.
- Playwright automation helpers.
- Monitor/report generation and workspace reset.
- Entrypoint flag behavior and reload handling.

### Security

- Malicious-fixture manifest hygiene.
- PoC canary coverage contracts for A1/A2/A4/A6.
- CI/local guard expectations around `make test-security` and
  `make test-security-live`.

### UI

- Route pages under `ui/src/features/`.
- Shared evidence and simulation widgets.
- Adapters and rule-draft helpers under `ui/src/lib/`.

## Current Gaps

- Smoke coverage is still centered on `ms-python.python` plus one chat-only
  benign fixture.
- Executor reliability is the most failure-prone path, so unit coverage still
  needs periodic backing from real-container smoke runs.
- Activation reports remain artifact-first and file-backed under `output/`, but
  async marketplace job metadata is now DB-backed and should be exercised
  through the Postgres test lane.
- Reload failures now fail quickly with phase-tagged diagnostics and stale
  process cleanup, but executor-side CDP/workbench stability still needs real
  smoke coverage because it remains the most brittle runtime seam.
- The SPA now has generated TypeScript contracts, but the request client and
  view-model adapters remain hand-written and can still drift if the contract
  generation step is skipped.
- The security lane currently validates fixture manifests and PoC class
  coverage, not production detection evaluation against runnable malicious
  payloads.

## Expectations for New Work

- New shared module in `appcore/`: add or update tests under `tests/platform/`.
- New package-level contract or planner logic: add or update tests under
  `tests/platform/` or `tests/architecture/` as appropriate.
- New workflow behavior: add tests under the matching `tests/workflows/<name>/`.
- New executor helper: add or update `tests/executor/` and, when needed,
  `tests/scanner/test_executor.py`.
- New end-to-end analysis reliability behavior: extend `tests/smoke/`.
- Security-fixture or detection-contract work: extend `tests/security/` and
  keep `make test-security` passing.
- Database schema changes require an Alembic migration plus updated tests.
