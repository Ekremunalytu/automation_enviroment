# Testing Guide

`Last Updated: 2026-05-26 (W19 closed synthetically — final W19 bar: tests/architecture/ 204 passed; make test-security 220 passed; full suite 1995 passed, 9 skipped, 8 deselected. PR #28 week19 -> main MERGED 2026-05-26 via c879603.)`

Test layers, fixtures, and commands. **Slim canonical** — per-domain
deep dives split out:

- [`testing/security-tests.md`](testing/security-tests.md) —
  malicious-fixture hygiene, A1..A6 rule tests, canary E2E.
- [`testing/platform-tests.md`](testing/platform-tests.md) — API,
  contracts, engine, storage, canonical imports.
- [`testing/marketplace-tests.md`](testing/marketplace-tests.md) —
  routers, services, planners, hardening (W8-1 VSIX).
- [`testing/executor-tests.md`](testing/executor-tests.md) — Playwright,
  monitor, reset, signal policy, W8-3 URI trigger.

Layer-by-layer file map:
[`structure/test-layout.md`](structure/test-layout.md). Architecture
boundary tests:
[`architecture/boundary-rules.md`](architecture/boundary-rules.md).

## Test Lanes

| Lane | Marker | Command |
|---|---|---|
| Unit | `not smoke and not requires_db and not integration` | `make test-unit` |
| Integration | `(requires_db or integration) and not smoke` | `make test-integration` |
| Smoke | `smoke` | `make test-smoke` |
| Security | n/a (path-based) | `make test-security` |
| Live security | n/a (T2/T3) | `make test-security-live` |
| Local default | `not smoke` | `make test-local` |
| CI default | `smoke or not smoke` | `make test-ci` |
| Full + lint + types | mixed | `make check-all` |

`make test-security` lane composition note: W8-1 + W8-3 remain in
subsystem-local lanes (`tests/workflows/marketplace/test_vsix_*`,
`tests/executor/security/test_uri_trigger_*`). The old
`[FOLLOWUP make-test-security-lane-composition]` item is closed in
[`testing/security-tests.md`](testing/security-tests.md); current W19
test-count claims should state whether a case is inside the Makefile
security lane or only in `make test-local`.

## Database Strategy

- DB-backed tests use PostgreSQL; DB-free lanes use mocked sessions.
- `tests/conftest.py` builds the test URL from `DATABASE_URL` first,
  then falls back to
  `postgresql://postgres:postgres@localhost:5434/test_db`.
- `test_engine` fixture creates tables once per session and drops them
  afterward, only when a test requests DB fixtures.
- `db_session` fixture opens a transaction per test and rolls it back
  for isolation.
- `make test-local` starts `postgres_test` and runs the default Python
  suite (`not smoke`) including DB-backed tests.

## Main Fixtures

| Fixture | Scope | Purpose |
|---|---|---|
| `test_engine` | session | SQLAlchemy engine |
| `db_session` | per-test | transactional session |
| `client` | per-test | FastAPI `TestClient` with `get_db` override |
| `db_client` | per-test | TestClient that reuses the per-test transactional session |
| `runtime_client` | per-test | TestClient that patches request-time + worker `SessionLocal` factories to the real test PostgreSQL engine |
| `mock_session` | per-test | reusable `MagicMock(spec=Session)` for DB-free tests |
| `sample_extension_data` | per-test | reusable extension payload |

## Commands (Quick Reference)

```bash
make test-local                      # default Python suite (1913 passed / 9 skipped / 8 deselected / 0 xfailed after W19-2 live re-anchor), with postgres_test
make test-security                   # cross-tree security lane (220 passed after W19-2 live re-anchor)
make check-all                       # ruff + mypy + bandit + ui-types-check + ui-boundaries + pytest
make sim-target TARGET=publisher.name [TRIGGERS=...] [SCENARIO=...]
make demo-canary                     # full canary demo
make demo-canary-offline             # offline fixture validation (<30 s)
make exec-up && make exec-run        # docker-based A1 canary smoke (user-side)
.venv/bin/pytest tests/<area> -v     # focused lane run
```

UI tests:

```bash
cd ui && npm run test
cd ui && npm run test:smoke          # ui/smoke/run-smoke.mjs
```

## Smoke Acceptance

`tests/smoke/test_marketplace_analysis_smoke.py` validates:

- `/api/marketplace/download`
- `/api/marketplace/analyze/start`
- async job polling via `/api/marketplace/analyze/{job_id}`
- report retrieval via `/api/activations/{name}`
- target-observed and automation-health semantics in the exported
  report

Currently covers: `ms-python.python` (+ layered chat/tool verification
on the same flow), `extrace.fixture-chat`. Scenario-zero
`extrace.fixture-theme` validated via contract + executor unit tests
rather than smoke.

The smoke client uses `runtime_client`, so request handlers + the async
job worker talk to the real test PostgreSQL when exercising
`analysis_jobs`. Failure-mode diagnostics (process + log dumps) trigger
when a job stalls on one step for two minutes (`reload_vscode.py` /
CDP reconnect stalls are the dominant failure mode).

## Test Layers (Quick Map)

| Layer | Path | Detail file |
|---|---|---|
| Architecture | `tests/architecture/` | `architecture/boundary-rules.md` |
| Platform | `tests/platform/` | `testing/platform-tests.md` |
| Workflows (marketplace) | `tests/workflows/marketplace/` | `testing/marketplace-tests.md` |
| Workflows (other) | `tests/workflows/{activation_reports,extension_catalog}/` | `testing/marketplace-tests.md` |
| Executor | `tests/executor/` including `tests/executor/scanner/` | `testing/executor-tests.md` |
| Security | `tests/security/`, `tests/executor/security/`, `tests/platform/security/` | `testing/security-tests.md` |
| Smoke | `tests/smoke/` | (this file, "Smoke Acceptance") |
| UI | `ui/src/**/*.test.ts(x)`, `ui/smoke/` | (Vitest + Testing Library; no detail doc) |

## Current Gaps

- Smoke coverage centered on `ms-python.python` + one chat-only benign
  fixture.
- Executor reliability remains failure-prone; unit coverage needs
  periodic backing from real-container smoke.
- Reload failures fail quickly with phase-tagged diagnostics; CDP /
  workbench stability still needs real smoke.
- SPA TypeScript contracts are generated, but request client + adapters
  hand-written — drift if generation is skipped.
- `make test-security` → 220 cases green as of the W19-2 live re-anchor
  baseline. The
  45-case figure was the entry-gate baseline at `2026-04-27`
  (post-PR345 + W8-0 lock-in). Live `make test-security-live` +
  Docker-based A1 canary structural diff are user-side regression
  gates for the capture pipeline.
- `make test-local` → full suite 1913 passed / 9 skipped / 8 deselected /
  0 xfailed as of the W19-2 live re-anchor baseline. The
  platform baseline fixture contract currently resolves
  `ms-python.python@2026.5.2026050801` plus the five benign-silence
  fixtures (`extrace.fixture-{chat,theme,snippet,keybinding,cmd}-0.0.1`)
  from local artifacts without network access.

## Expectations For New Work

- New shared module in `appcore/` → tests under `tests/platform/`.
- New package-level contract or planner logic →
  `tests/platform/contracts/` or `tests/architecture/` as appropriate.
- New workflow behavior → `tests/workflows/<name>/`.
- New executor helper → `tests/executor/` (and
  `tests/executor/scanner/test_executor.py` if it touches the docker exec
  wrapper).
- New end-to-end reliability behavior → `tests/smoke/`.
- Security-fixture or detection-contract work → `tests/security/`;
  keep `make test-security` passing.
- DB schema changes require an Alembic migration + updated tests.
