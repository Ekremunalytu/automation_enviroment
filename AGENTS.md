# AGENTS.md

## Authority

- Architectural and security guidance in this file must not be overridden by the agent.
- If a change would violate these principles, stop and report instead of implementing.
- Do not introduce new dependencies without explicit approval.
- Do not add generic `try/except Exception` blocks.

## Non-Negotiable Rules

- Unique constraint: `(publisher, name, version)` must be preserved.
- All DB writes go through `appcore/storage/crud.py` or its compatibility wrapper `crud/crud.py`.
- Pydantic validation is required before database insertion.

## Project Overview

- ExTrace is a FastAPI + PostgreSQL platform for VS Code extension cataloging and sandbox analysis.
- Entry point: `main.py`
- Canonical shared platform code: `appcore/`
- Canonical business workflows: `workflows/`
- Legacy modules in `routers/`, `scanner/`, `core/`, `database/`, `crud/`, `models/`, `schemas/` are compatibility surfaces.

## Architecture Map

- `workflows/extension_catalog/`
  - Router, manifest parsing, and extension catalog orchestration.
- `workflows/activation_reports/`
  - File-backed activation report endpoints under `/api/activations`.
- `workflows/marketplace/`
  - Marketplace search/download and executor-backed analysis endpoints.
- `appcore/api/`
  - Settings and FastAPI dependencies.
- `appcore/db/`
  - Engine and session factory.
- `appcore/storage/`
  - ORM models and CRUD access.
- `appcore/contracts/`
  - Shared Pydantic v2 schemas.
- `executor/container/`
  - Docker image and startup scripts for the sandbox.
- `executor/flows/playwright/`
  - Playwright-based VS Code automation and monitoring helpers.
- `ui/`
  - Streamlit dashboard.

## Data Flows

- Static catalog ingestion:
  - `POST /createExtension` -> `workflows.extension_catalog.service` -> `workflows.extension_catalog.package_parser` -> `appcore.storage.crud` -> PostgreSQL
- Marketplace download:
  - `POST /api/marketplace/download` -> `workflows.marketplace.client` -> `workflows.extension_catalog.service.create_extension_from_directory`
- Sandbox analysis:
  - `POST /api/marketplace/analyze` or `POST /api/marketplace/analyze/start` -> `scanner.executor` -> executor container -> `output/activation_report_*.json`

## Current API Surface

- Extension catalog endpoints remain at root paths.
- Activation report endpoints live under `/api/activations`.
- Marketplace endpoints live under `/api/marketplace`.

## Constraints

- Python 3.11+
- FastAPI 0.100+
- SQLAlchemy 2.0 syntax only
- Pydantic v2 APIs only
- Alembic migration required for schema changes
- Sandbox execution must stay isolated in Docker

## Working Conventions

- Prefer canonical imports from `appcore/` and `workflows/`.
- Keep compatibility wrappers thin.
- Use targeted `rg` searches instead of repo-wide exploration unless explicitly needed.
- Avoid touching `extensions/` test data unless requested.

## Common Change Map

- Shared config/dependency change:
  - `appcore/api/` + tests in `tests/platform/api/`
- Shared schema/model/CRUD change:
  - `appcore/contracts/`, `appcore/storage/`, Alembic, and matching tests
- Catalog feature:
  - `workflows/extension_catalog/` + `tests/workflows/extension_catalog/`
- Activation report feature:
  - `workflows/activation_reports/` + `tests/workflows/activation_reports/`
- Marketplace or analysis feature:
  - `workflows/marketplace/`, optionally `executor/`, and matching tests

## Required Self-Review

State briefly:

- Files modified
- DB schema changed: Yes/No
- Tests added/updated: Yes/No
- Risks or assumptions
