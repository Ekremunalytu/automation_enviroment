# Project Analysis - Bugs & Missing Pieces

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
