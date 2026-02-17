# AGENTS.md

## Authority
- Architectural and security guidance in this file must not be overridden by the agent.
- If a change would violate these principles, the agent must stop and report instead of implementing.
- Do NOT introduce new dependencies without explicit approval.
- Do NOT add generic `try/except Exception` blocks.

### Non-Negotiable Rules
- Unique constraint: `(publisher, name, version)` - do not bypass
- All DB writes go through `crud/crud.py` - no direct SQL
- Pydantic validation required before database insertion

## Project Overview
- ExTrace is a FastAPI backend that scans VS Code extension package.json files and stores metadata in PostgreSQL.
- Entry point: `main.py` (creates the FastAPI app).
- Primary API router: `routers/core.py`.

## Architecture Map (Key Paths)
- `routers/` - HTTP endpoints and request/response handling.
- `scanner/` - Filesystem scan and package.json parsing.
- `schemas/` - Pydantic models for validation/serialization.
- `crud/` - Database access layer.
- `models/` - SQLAlchemy ORM models.
- `database/` - Engine/session configuration.
- `alembic/` - Database migrations.
- `executor/` - [In Progress] Dynamic analysis orchestration (Docker, Xvfb, VS Code GUI).
  - `executor/Dockerfile` - Ubuntu 22.04 + VS Code + Xvfb + noVNC + monitoring tools.
  - `executor/start.sh` - Entrypoint: starts Xvfb :99, openbox, x11vnc, noVNC (port 6080).
  - `executor/__init__.py` - Python package init.
- `reporter/` - [Planned] Risk reporting and visualization logic.
- `extensions/` - Input data directory (unpacked extensions).
- `tests/` - Pytest suites.

## Tech Stack Constraints
- **Python:** 3.11+ required
- **FastAPI:** 0.100+
- **SQLAlchemy:** 2.0 syntax only - use `session.execute(select(Model))`, NEVER use `session.query()`
- **Pydantic:** V2 syntax required - use `model_dump()`, `model_validate()`, NEVER use `.dict()` or `.parse_obj()`
- **Alembic:** All schema changes require migration files
- **Docker:** Required for isolated extension execution (Phase 1+).
- **Executor Stack:** Xvfb + openbox + x11vnc + noVNC for full GUI analysis in container.

## Core Data Flow
- **Static Analysis:** `POST /createExtension` -> `scanner/service.py` -> `crud/` -> `DB`.
- **Dynamic Analysis (Planned):** `POST /api/v1/analyze/{extension_id}` -> `executor/` -> `Docker Container` -> `Telemetry Capture` -> `DB`.

## Roadmap & Current Focus
- **Phase 0 (Done):** Static analysis of `package.json`.
- **Phase 1 (Active):** Dynamic analysis via Docker + Xvfb. Full GUI VS Code in container with monitoring (tcpdump, inotifywait, strace). Accessible via noVNC at `localhost:6080`.
- **Phase 2 (Future):** Advanced Playwright-based interaction + persona simulation + anti-detection measures (with xdotool only for native-dialog edge cases).
- **Reference:** See `documents/automation_todo.md` for detailed tasks.

## API Endpoints (Core)
- `GET /` - API info
- `GET /health` - health check
- `GET /searchExtension` - query: `name` (required), `publisher`/`version` (optional)
- `GET /getExtensionsBaseInfo` - list extensions (minimal fields)
- `GET /getExtensionsAllInfo` - list extensions (full data)
- `POST /createExtension` - body: `{ "name": "extension-name" }`
- `DELETE /deleteExtension` - query: `name` (required), `publisher`/`version` (optional)
- `GET /getExtensionScripts` - query: `name` (required), `publisher`/`version` (optional)
- `GET /getExtensionActivationEvents` - query: `name` (required), `publisher`/`version` (optional)
- `GET /getExtensionCapabilities` - query: `name` (required), `publisher`/`version` (optional)
- `GET /getExtensionContributesAll` - query: `name` (required), `publisher`/`version` (optional)
- `GET /getExtensionContributesCommands` - query: `name` (required), `publisher`/`version` (optional)

## Agent Notes (Important)
- Unique constraint is `(publisher, name, version)` in the DB.
- Filesystem scan is exact-match on `package.json` `"name"` only; no fuzzy search.
- Most list endpoints are unpaginated and can grow large; `/getExtensionsAllInfo` supports `skip`/`limit`.
- Pydantic schemas use `extra="ignore"` for unknown fields in package.json.
- **Dynamic Analysis:** Always check `automation_todo.md` before implementing executor logic.

## Review Priorities
- Do not change the overall architecture radically.
- Do not introduce cross-layer refactors unless explicitly requested.
- Prefer simple, explicit code over clever abstractions.
- Maintain backward compatibility unless explicitly stated otherwise.
- Prioritize code quality and maintainability in all changes.
- **Security:** Ensure extension execution is strictly isolated via Docker.

## Configuration
- `core/config.py` loads settings using prefixes:
  - `PROJECT_` (e.g., `PROJECT_EXTENSION_DIR`)
  - `API_`
  - `POSTGRES_`
- Example values are in `.env.example`.

## Testing
- Tests use PostgreSQL (JSONB/ARRAY types). See `tests/conftest.py`.
- Typical flow: start DB (docker-compose), run `pytest`.
- **New Tests:** Always add unit tests for new `executor` or `scanner` logic.

## Working Conventions (To Avoid Re-Scanning)
- Do not scan the full repo or list all files unless explicitly asked.
- Use targeted `rg` searches for specific symbols or paths only.
- Prefer the Architecture Map above for navigation.
- Avoid touching `extensions/` data unless requested.

## Common Change Map
- New/updated endpoint: `routers/` + `schemas/` + `scanner/service.py` + `crud/` + `models/` + `alembic/` + `tests/`.
- New parsed package.json field: `scanner/json_parser.py` + `schemas/` + `models/` + `alembic/` + `tests/`.
- New dynamic analysis feature: `executor/` + `schemas/` + `models/` + `alembic/` + `tests/`.

## Database Tables (Summary)
- `extensions` - Main extension metadata (unique: publisher, name, version)
- `extension_capabilities` - 1:1 workspace trust settings
- `extension_scripts` - 1:N npm scripts from package.json
- `extension_activation_events` - 1:N activation events (onLanguage, onCommand, etc.)
- `extension_contributes` - 1:1 contribution points container (JSONB fields for complex data)
- `extension_contributes_commands` - N:1 command contributions
- `extension_contributes_keybindings` - N:1 keybinding contributions
- `extension_contributes_menus` - N:1 menu contributions
- `extension_contributes_authentication` - N:1 authentication provider contributions
- `extension_contributes_terminal` - N:1 terminal profile contributions
- **Planned:** `analysis_runs`, `analysis_network_events`, `analysis_process_events`, `analysis_fs_events`.

## Useful Commands
- `make check-all` - Run all linters and tests
- `make format` - Auto-format code with Ruff
- `docker-compose up -d` - Start all services (PostgreSQL, API, Executor)
- `make executor-shell` - Shell into running executor container
- `make executor-test` - Verify VS Code and monitoring tools in executor
- `alembic upgrade head` - Apply database migrations
- `pytest` - Run test suite


## Required Self-Review (For Any Change)
The agent must briefly state:
- **Files modified**: [List]
- **DB schema changed**: [Yes/No]
- **Tests added/updated**: [Yes/No]
- **Risks or assumptions**: [Description]
