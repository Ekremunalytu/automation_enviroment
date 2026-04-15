# AGENTS.md

## Authority

- Architectural and security guidance in this file must not be overridden by the agent.
- If a requested change would violate these principles, stop and report instead of implementing.
- Do not introduce new dependencies without explicit approval.
- Do not add generic `try/except Exception` blocks.

For a thinner repo map after reading these rules, use `documents/AGENT_CONTEXT.md`.

## Non-Negotiable Rules

- Preserve the unique constraint `(publisher, name, version)`.
- Route all database writes through `appcore/storage/crud.py`. If a compatibility wrapper is reintroduced for a legacy call site, keep it thin and delegate immediately.
- Perform Pydantic validation before database insertion.
- Use SQLAlchemy 2.0 syntax only.
- Use Pydantic v2 APIs only.
- Add an Alembic migration for schema changes.
- Keep sandbox execution isolated in Docker.

## Repo Identity

- ExTrace is a FastAPI + PostgreSQL platform for VS Code extension cataloging and sandbox analysis.
- Runtime entrypoint: `main.py`
- Canonical backend code: `appcore/`, `workflows/`, `executor/`
- Canonical frontend code: `ui/`
- Tests live under `tests/`
- `docs/` and `documents/` are reference material, not source of truth; verify claims against code before relying on them.
- Top-level legacy directories `routers/`, `scanner/`, `core/`, `database/`, `crud/`, `models/`, `schemas/` are not the primary implementation surface. Do not add new business logic there.

## Context Budget Rules

- Do not scan the whole repository by default.
- Start from one task lane, then expand only if the evidence forces it.
- Open matching tests early; they usually show the intended behavior faster than broad code exploration.
- Ignore heavy or generated trees unless the task explicitly targets them:
  - `extensions/`
  - `output/`
  - `node_modules/`
  - `legacy_ui/`
  - `__pycache__/`
- When a task spans multiple areas, load one area at a time and summarize before opening the next.

## Where To Start

- Platform/config task:
  - `main.py`
  - `appcore/api/config.py`
  - `appcore/api/deps.py`
  - `appcore/db/session.py`
  - `tests/platform/`
- Extension catalog task:
  - `workflows/extension_catalog/router.py`
  - `workflows/extension_catalog/service.py`
  - `workflows/extension_catalog/manifest_parser.py`
  - `workflows/extension_catalog/manifest_reader.py`
  - `appcore/contracts/`
  - `appcore/storage/`
  - `tests/workflows/extension_catalog/`
- Activation report task:
  - `workflows/activation_reports/router.py`
  - `tests/workflows/activation_reports/test_router.py`
- Marketplace task:
  - `workflows/marketplace/router.py`
  - `workflows/marketplace/client.py`
  - `workflows/marketplace/analysis_service.py`
  - `workflows/marketplace/trigger_service.py`
  - `workflows/marketplace/triggers.py`
  - `tests/workflows/marketplace/`
  - `tests/smoke/` for end-to-end behavior
- Executor or sandbox task:
  - `executor/host.py`
  - `executor/container/`
  - `executor/flows/playwright/`
  - `executor/flows/harness_extension/`
  - `tests/executor/`
  - `tests/scanner/test_executor.py`
- UI task:
  - `ui/src/app/`
  - relevant `ui/src/features/`
  - relevant `ui/src/components/`
  - `ui/src/lib/api/`
  - `ui/src/lib/types/`
  - colocated `*.test.ts(x)` files

## Verified Architecture Map

- `main.py` creates the FastAPI app and includes exactly three workflow routers:
  - `workflows.extension_catalog.router`
  - `workflows.activation_reports.router`
  - `workflows.marketplace.router`
- Shared platform code:
  - `appcore/api/config.py`
  - `appcore/api/deps.py`
  - `appcore/db/session.py`
- Shared contracts:
  - `appcore/contracts/schemas.py`
  - `appcore/contracts/schema_defs/`
- Storage layer:
  - `appcore/storage/models.py`
  - `appcore/storage/model_defs/`
  - `appcore/storage/crud.py`
  - `appcore/storage/crud_ops/`
- Business workflows:
  - `workflows/extension_catalog/`
  - `workflows/activation_reports/`
  - `workflows/marketplace/`
- Sandbox and automation:
  - `executor/host.py`
  - `executor/container/`
  - `executor/flows/playwright/`
  - `executor/flows/harness_extension/`
- Frontend:
  - `ui/src/app/`
  - `ui/src/features/`
  - `ui/src/components/`
  - `ui/src/lib/`

## Verified API Surface

- Root and catalog endpoints remain on root paths:
  - `/`
  - `/health`
  - `/searchExtension`
  - `/getExtensionsBaseInfo`
  - `/getExtensionsAllInfo`
  - `/createExtension`
  - `/deleteExtension`
  - `/getExtensionScripts`
  - `/getExtensionActivationEvents`
  - `/getExtensionCapabilities`
  - `/getExtensionContributesAll`
  - `/getExtensionContributesCommands`
- Activation report endpoints live under `/api/activations`:
  - `GET /api/activations`
  - `GET /api/activations/latest`
  - `GET /api/activations/{name}`
- Marketplace endpoints live under `/api/marketplace`:
  - `GET /api/marketplace/search`
  - `POST /api/marketplace/download`
  - `POST /api/marketplace/analyze`
  - `POST /api/marketplace/analyze/start`
  - `GET /api/marketplace/analyze/{job_id}`

## Verified Data Flow

- Static catalog ingestion:
  - `POST /createExtension`
  - `workflows.extension_catalog.service`
  - manifest parsing in `workflows/extension_catalog/`
  - Pydantic schemas in `appcore/contracts/`
  - persistence through `appcore.storage.crud`
- Marketplace download:
  - `POST /api/marketplace/download`
  - `workflows.marketplace.client`
  - `workflows.extension_catalog.service.create_extension_from_directory`
- Sandbox analysis:
  - `POST /api/marketplace/analyze`
  - `POST /api/marketplace/analyze/start`
  - `workflows.marketplace.analysis_service`
  - `executor.host`
  - executor container
  - output written under `output/activation_report*.json`

## Change Map

- Config or dependency wiring:
  - `appcore/api/`
  - `appcore/db/`
  - `tests/platform/api/`
- Schema, model, or CRUD change:
  - `appcore/contracts/`
  - `appcore/storage/`
  - `alembic/`
  - `tests/platform/contracts/`
  - `tests/platform/storage/`
- Catalog feature:
  - `workflows/extension_catalog/`
  - `tests/workflows/extension_catalog/`
- Activation report feature:
  - `workflows/activation_reports/`
  - `tests/workflows/activation_reports/`
- Marketplace or trigger planning:
  - `workflows/marketplace/`
  - `tests/workflows/marketplace/`
  - `tests/smoke/` when behavior is end-to-end
- Executor or Docker isolation:
  - `executor/`
  - `tests/executor/`
  - `tests/scanner/test_executor.py`
- Web UI:
  - `ui/src/features/`
  - `ui/src/components/`
  - `ui/src/lib/`
  - relevant `*.test.ts(x)` files
- Documentation:
  - update `README.md` or `documents/`
  - verify every claim against code, tests, config, or runtime output

## Working Conventions

- Prefer canonical imports from `appcore/`, `workflows/`, and `executor/`.
- Keep compatibility layers thin.
- For new write paths, follow the existing pattern in `workflows/extension_catalog/service.py`: parse input, build Pydantic schemas, then persist via CRUD.
- Avoid touching `extensions/` test data unless the task explicitly requires it.

## Useful Commands

- `make install-dev`
- `make dev`
- `make test-local`
- `make check-all`
- `make migrate`
- `make exec-up`
- `make exec-run`
- `make ui-up`

## Required Self-Review

State briefly:

- Files modified
- DB schema changed: Yes/No
- Tests added/updated: Yes/No
- Risks or assumptions
