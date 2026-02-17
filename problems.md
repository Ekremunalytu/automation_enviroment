# Project Analysis - Bugs & Missing Pieces

## Findings (by priority)

1. High: Test infrastructure "skip if no DB" flow is broken.
   - `tests/conftest.py:75` runs `Base.metadata.create_all(bind=engine)` before DB connection is checked.
   - `tests/conftest.py:167` skip control comes after this step, making it ineffective.
   - Result: Even DB-independent tests fail during setup.

2. High: `createExtension` flow has ambiguous extension selection (risk of selecting wrong record).
   - `schemas/schemas.py:455` and `scanner/service.py:235` accept only `name`.
   - `scanner/json_parser.py:207` and `scanner/json_parser.py:216` return the first matching directory.
   - If the same `name` exists with different `publisher/version`, the result is non-deterministic.

3. High: Some read endpoints lack multi-match validation.
   - `crud/crud.py:477`, `crud/crud.py:508`, `crud/crud.py:546`, `crud/crud.py:585`, `crud/crud.py:622` use `.first()`.
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
   - `scanner/json_parser.py:737`, `scanner/json_parser.py:804`
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

1. Critical planned modules for dynamic analysis are not implemented yet:
   - `documents/automation_todo.md:141` (extension installer)
   - `documents/automation_todo.md:147` (trigger engine)
   - `documents/automation_todo.md:159` (process/network/fs monitor modules)
   - Files `executor/extension_manager.py`, `executor/triggers.py`, `executor/monitors/*` do not exist.

2. DB structures for storing analysis results are not created yet:
   - `documents/automation_todo.md:186`
   - Tables `analysis_runs`, `analysis_network_events`, `analysis_process_events`, `analysis_fs_events` do not exist.

3. Analyze API endpoints are not implemented yet:
   - `documents/automation_todo.md:211`
   - No `/analyze/...` endpoints found under `routers/`.

4. Bug items listed in documentation are still open:
   - `documents/automation_todo.md:121`

## Checks Performed

1. `ruff check .` -> passed.
2. `pytest -q tests/executor` -> 3/3 passed.
3. `pytest -q` -> failed at setup due to no DB access.
4. `pytest -q tests/scanner/test_json_parser.py::TestParseNpmFields::test_parse_standard_npm_fields` -> failed at setup for the same reason.
