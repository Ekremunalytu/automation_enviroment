# Project Analysis - Bugs & Missing Pieces

## Current General Issues (2026-03-05)

1. High: VS Code reload failure is treated as non-fatal during analyze flow.
   - `routers/marketplace.py:195-200` catches `ExecutorError` and continues.
   - `scanner/executor.py:162-164` states reload is required for activation.
   - Risk: false negatives in dynamic analysis when extension never activates.

2. High: Custom editor bait files are created under the wrong workspace path.
   - `executor/playwright/entrypoint.py:76` writes to `/home/executor/workspace`.
   - Actual opened workspace is `/workspace` (`executor/start.sh:94`, `executor/playwright/workspace.py:15`).
   - Risk: `onCustomEditor` triggers may never fire.

3. Medium: Broad `except Exception` usage in new trigger-building path.
   - `routers/marketplace.py:255-261` swallows all errors and silently falls back.
   - Risk: hidden integration failures and reduced observability.

4. Medium: Test coverage gap for trigger-integrated analyze flow.
   - Missing endpoint-level tests validating trigger payload creation and passing `--triggers`.
   - Related code: `routers/marketplace.py:203-274`, `scanner/executor.py:213-220`.
   - Existing tests cover base analyze flow but not trigger branch (`tests/routers/test_marketplace.py`).

5. Low/Medium: API container no longer bind-mounts full project source.
   - `docker-compose.yml:48-52` now mounts only `extensions`, `output`, `.env`.
   - If hot-reload/dev iteration was expected from container, behavior regresses.
   - If this is intentional hardening/isolation, keep as-is and document explicitly.

6. Environment blocker (local verification): current venv cannot import FastAPI correctly.
   - `fastapi` import fails because `annotated_doc` package appears broken in `.venv`.
   - Impact: local pytest execution cannot be trusted until environment is repaired.

## Findings (by priority)

1. ~~High: Test infrastructure "skip if no DB" flow is broken.~~ (✅ Resolved)
   - *Fix context*: A dedicated testing infrastructure is now available via PostgreSQL test database and fixtures, completely resolving the need for testing without a DB. (See `documents/TESTING.md`).

2. High: `createExtension` flow has ambiguous extension selection (risk of selecting wrong record).
   - `schemas/schemas.py:455` and `scanner/service.py:235` accept only `name`.
   - `scanner/json_parser.py:207` and `scanner/json_parser.py:216` return the first matching directory.
   - If the same `name` exists with different `publisher/version`, the result is non-deterministic.

3. High: Some read endpoints lack multi-match validation.
   - `crud/crud.py:502`, `crud/crud.py:540`, `crud/crud.py:579`, `crud/crud.py:616`, `crud/crud.py:643` use `.first()`.
   - When called with only `name`, incorrect extension data may be returned.

4. Medium: `get_db` may raise `UnboundLocalError` if `SessionLocal()` fails.
   - `core/deps.py:107`, `core/deps.py:118`
   - If `db` variable is not created before `finally` block, `db.close()` raises a second error.

5. Medium: API 500 responses leak internal exception messages.
   - `routers/core.py:225`, `routers/core.py:288`, `routers/core.py:323`, `routers/core.py:402`, `routers/core.py:443`
   - Exposing error details to client creates an information disclosure risk.

6. Medium: All `IntegrityError` cases are mapped as duplicates.
   - `crud/crud.py:314`, `crud/crud.py:318`
   - Non-duplicate integrity problems may also return "Extension already exists".

7. Medium: Pagination parameters lack negative value validation.
   - `routers/core.py:294`
   - `skip=-1` or `limit=-1` requests can produce DB-level errors resulting in 500s.

8. Low: `_VSCODE_FIELDS` is defined but not used in `parse_extra_fields`.
   - `scanner/json_parser.py:738`, `scanner/json_parser.py:804`
   - Some VS Code fields may be incorrectly classified into `extra_fields`.

9. Low: JSON parse layer has broad `except Exception` with silent swallow.
   - `scanner/json_parser.py:99`
   - Reduces error observability.

10. Medium: Race conditions in dynamic analysis startup.
    - VS Code takes variable time to initialize in Xvfb.
    - Playwright scripts may attempt to connect to CDP before the remote debugging port is open.
    - Result: Intermittent test/analysis failures.

11. Low: Telemetry log parsing is manual and decoupled from the DB.
    - `output/` files are produced but not automatically ingested.
    - Requires manual oversight to link PCAP/FS logs to specific extension runs.

## Missing Pieces (per Roadmap)

1. GUI interaction and dynamic analysis modules are mostly completed via Playwright:
   - Playwright automation suite now manages the execution of analysis instead of independent `monitors/*` scripts (See `EXECUTOR_PLAYWRIGHT.md`).
   - Planned modules like `extension installer` and `trigger engine` are currently simulated manually via Playwright or covered by existing startup behavior (See `automation_todo.md`).

2. Production-grade Monitoring is pending:
   - `network_monitor.py` (tcpdump) and `fs_monitor.py` (inotifywait) need to be formalized and integrated.
   - Process monitoring via strace.

3. DB structures for storing analysis results are not created yet:
   - Tables `analysis_runs`, `analysis_network_events`, `analysis_process_events`, `analysis_fs_events`, `analysis_risk_signals` do not exist.

4. Analyze API endpoints are not implemented yet:
   - No `/analyze/...` or `/extensions/{id}/risk-score` endpoints found under `routers/`.

5. Risk Scoring Engine:
   - `analyzer/risk_scorer.py` needs implementation.

## Checks Performed

1. `ruff check .` -> passed.
2. `pytest` test suite -> Can be successfully run using the test infrastructure (`make test-local`). All 148 tests pass.
