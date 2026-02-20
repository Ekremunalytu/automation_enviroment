# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

ExTrace is a FastAPI backend that scans VS Code extension `package.json` files, validates them with Pydantic, and stores metadata in PostgreSQL. It serves a REST API for querying extension data. The project is evolving toward dynamic analysis of extensions in Docker containers.

## Commands

```bash
# Development server (with hot reload)
make dev

# Run all checks: lint + typecheck + security + tests
make check-all

# Individual checks
make lint          # Ruff linter with auto-fix
make format        # Ruff formatter
make typecheck     # mypy
make security      # Bandit

# Testing (requires postgres_test container on port 5434)
make test          # Run pytest
make test-cov      # pytest with coverage report
make test-local    # Starts postgres_test container, then runs tests

# Run a single test
.venv/bin/pytest tests/path/test_file.py::test_function -v

# Database
make up            # Start all containers (PostgreSQL + API + Executor)
make down          # Stop containers
make migrate       # Run alembic upgrade head
make migrate-create  # Create new migration (interactive prompt)

# Executor (Dynamic Analysis)
make exec-build    # Build executor image
make exec-up       # Start executor container only
make exec-down     # Stop executor container
make exec-shell    # Shell into running executor
make exec-test     # Verify VS Code CLI and tools inside executor

# Install
make install-dev   # Install prod + dev dependencies
make install-hooks # Install pre-commit hooks
```

## Architecture

**Layered design:** Router → Schema → Service → CRUD → Model → Database

- `main.py` — App factory (`create_app()`) producing the FastAPI instance
- `core/config.py` — Pydantic Settings with prefixed env vars (`PROJECT_`, `API_`, `POSTGRES_`). Access via `from core.config import settings`
- `core/deps.py` — `get_db()` dependency yielding SQLAlchemy sessions
- `database/session.py` — Engine and `SessionLocal` factory
- `routers/core.py` — All HTTP endpoints (no prefix)
- `scanner/service.py` — Business logic connecting parsing to CRUD
- `scanner/json_parser.py` — Reads `package.json` files from `extensions/` directory
- `crud/crud.py` — All database operations (no direct SQL elsewhere)
- `models/models.py` — SQLAlchemy ORM models, `Base` declarative base
- `schemas/schemas.py` — Pydantic V2 request/response models
- `alembic/` — Database migrations
- `executor/` — [In Progress] Dynamic analysis orchestration (Xvfb + Docker)
  - `executor/Dockerfile` — Ubuntu 22.04 image with VS Code, Xvfb, noVNC, monitoring tools
  - `executor/start.sh` — Container entrypoint: starts Xvfb, openbox, x11vnc, noVNC
  - `executor/__init__.py` — Package init
- `reporter/` — [Planned] Risk reporting

**Data flow for static analysis:**
`POST /createExtension` → `scanner/service.py` scans `extensions/` dir for matching `package.json` by `name` field (exact match) → validates with Pydantic → `crud/crud.py` inserts → PostgreSQL

## Key Constraints

- **Unique constraint:** `(publisher, name, version)` in DB — never bypass
- **SQLAlchemy 2.0 only:** Use `session.execute(select(Model))`, never `session.query()`
- **Pydantic V2 only:** Use `model_dump()`, `model_validate()`, never `.dict()` or `.parse_obj()`
- **All DB writes go through `crud/crud.py`** — no direct SQL
- **Pydantic validation required before any DB insertion**
- All schema changes require Alembic migration files
- Schemas use `extra="ignore"` for unknown `package.json` fields
- Ruff ignores `N815` (camelCase) because VS Code API uses camelCase field names like `displayName`

## Testing

Tests require a running PostgreSQL instance (JSONB/ARRAY types). The test DB runs on port 5434 via `docker-compose up -d postgres_test`. Tests use per-function session rollback for isolation. Fixtures are in `tests/conftest.py`. Test structure mirrors source layout: `tests/crud/`, `tests/routers/`, `tests/scanner/`, `tests/schemas/`.

## Change Patterns

- **New endpoint:** `routers/` + `schemas/` + `scanner/service.py` + `crud/` + `models/` + `alembic/` + `tests/`
- **New package.json field:** `scanner/json_parser.py` + `schemas/` + `models/` + `alembic/` + `tests/`
- **New dynamic analysis feature:** `executor/` + `schemas/` + `models/` + `alembic/` + `tests/` (may also require `executor/Dockerfile` or `executor/start.sh` changes)

## Roadmap Context

- **Phase 0 (Done):** Static analysis of `package.json`
- **Phase 1 (Active):** Dynamic analysis via Docker + Xvfb (full GUI). Executor container runs VS Code with virtual display, monitored by tcpdump/inotifywait/strace. Accessible via noVNC at `localhost:6080`.
- **Phase 2 (Future):** Automated GUI interaction (xdotool, Puppeteer), persona-based simulation, anti-detection
- Check `documents/automation_todo.md` before implementing executor logic
