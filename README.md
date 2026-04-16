# ExTrace

`Last Updated: 2026-04-16`

ExTrace is a VS Code extension analysis platform built around three runtime surfaces:

- A FastAPI API for catalog ingestion, activation report access, marketplace download, and sandbox analysis.
- A Dockerized executor that runs full VS Code GUI sessions under Xvfb and drives them with Playwright.
- A Vite + React + Tailwind analyst console that consumes the API and visualizes activation reports and live simulation jobs.

## Operating Model

ExTrace is intentionally designed as a single-user sandbox appliance, not a multi-tenant web platform.

- Backend, UI, PostgreSQL, and executor are expected to run on the same machine or inside the same Docker host.
- The primary deployment shape is a local or lab sandbox where one analyst inspects one extension at a time.
- Background analysis is intentionally limited to one active job at a time.
- Activation reports remain file-backed operator artifacts under `output/`, while async analysis job metadata is persisted in PostgreSQL.
- If the API process restarts during an active analysis, that job is marked failed and should be rerun.

## Current Architecture

The refactor introduced a canonical split between shared platform code and workflow code:

- `appcore/`
  - Shared platform modules.
  - `api/`: settings and FastAPI dependencies.
  - `db/`: SQLAlchemy engine and session factory.
  - `storage/`: ORM models and CRUD helpers.
  - `contracts/`: shared Pydantic v2 schemas.
- `workflows/`
  - Business workflows grouped by capability.
  - `extension_catalog/`: extension ingestion, parsing, and catalog endpoints.
  - `activation_reports/`: reads JSON activation reports from `output/`.
  - `marketplace/`: Marketplace search/download and sandbox analysis.
- `executor/`
  - Sandbox runtime.
  - `container/`: Docker image, entrypoint, VS Code/Xvfb/noVNC boot logic.
  - `flows/playwright/`: Playwright automation helpers and entrypoint.
- `ui/`
  - Primary analyst-facing React SPA built with Vite and Tailwind.
  - `src/app/`: shell and route composition.
  - `src/features/`: `reports`, `simulation`, `marketplace`.
  - `src/lib/`: API client, adapters, chart helpers, and shared types.
- `legacy_ui/`
  - Previous Streamlit implementation retained as an archival compatibility snapshot.

The repository now uses canonical imports only:

- Shared platform modules live under `appcore/`
- Workflow code lives under `workflows/`
- Host-side executor control lives under `executor/host.py`

## Request Flows

### Static Catalog Ingestion

`POST /createExtension`

1. `workflows.extension_catalog.router`
2. `workflows.extension_catalog.service`
3. `workflows.extension_catalog.manifest_reader` + `workflows.extension_catalog.manifest_parser`
4. `appcore.contracts.schemas`
5. `appcore.storage.crud`
6. PostgreSQL

### Marketplace Download

`POST /api/marketplace/download`

1. `workflows.marketplace.client` downloads and extracts a `.vsix`
2. `workflows.extension_catalog.service.create_extension_from_directory`
3. `appcore.storage.crud` persists validated manifest data

### Sandbox Analysis

`POST /api/marketplace/analyze` or `POST /api/marketplace/analyze/start`

1. `workflows.marketplace.router`
2. `workflows.marketplace.analysis_service`
3. `workflows.marketplace.job_service`
4. `executor.host` Docker exec wrapper
5. `executor/flows/playwright/entrypoint.py`
6. Reports written under `output/`
7. Async job metadata persisted in PostgreSQL `analysis_jobs`

Notes:

- `POST /api/marketplace/analyze` is the direct request/response path.
- `POST /api/marketplace/analyze/start` is the background path used by the React UI.
- Only one background analysis should run at a time in the intended sandbox deployment.
- Startup fails fast if the `analysis_jobs` storage path is unavailable or the required migration has not been applied.

## API Surface

### Extension Catalog

- `GET /`
- `GET /health`
- `GET /searchExtension`
- `GET /getExtensionsBaseInfo`
- `GET /getExtensionsAllInfo`
- `POST /createExtension`
- `DELETE /deleteExtension`
- `GET /getExtensionScripts`
- `GET /getExtensionActivationEvents`
- `GET /getExtensionCapabilities`
- `GET /getExtensionContributesAll`
- `GET /getExtensionContributesCommands`

### Activation Reports

- `GET /api/activations`
- `GET /api/activations/latest`
- `GET /api/activations/{name}`

### Marketplace + Analysis

- `GET /api/marketplace/search`
- `POST /api/marketplace/download`
- `POST /api/marketplace/analyze`
- `POST /api/marketplace/analyze/start`
- `GET /api/marketplace/analyze/{job_id}`

## Local Development

### Prerequisites

- Python 3.11+
- Docker / Docker Compose
- PostgreSQL 16 compatible runtime
- Node 20+ for local UI development

### Common Commands

```bash
make install-dev
make up
make migrate
make dev
make test-local
make check-all
make exec-up
make exec-run
make ui-up
cd ui && npm run dev
cd ui && npm run test
.venv/bin/pytest
.venv/bin/pytest -m "not smoke and not requires_db"
.venv/bin/pytest -m "requires_db"
.venv/bin/pytest -m smoke
```

### Service Endpoints

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Web UI: `http://localhost:3000`
- noVNC executor view: `http://localhost:6080/vnc.html`

## Project Layout

```text
appcore/                    Shared platform modules
workflows/                  Canonical business workflows
executor/
  container/               Sandbox image and startup scripts
  flows/playwright/        VS Code GUI automation
ui/                         React + Vite analyst console
legacy_ui/                  Previous Streamlit UI snapshot
tests/
  platform/                Shared platform tests
  workflows/               Workflow tests
  executor/                Playwright runtime tests
  scanner/                 Docker exec wrapper tests
  smoke/                   End-to-end marketplace analysis tests
  ui tests live under ui/src/**/*.test.ts(x)
documents/                  Architecture, roadmap, and testing notes
docs/                       Targeted risk notes
```

## Documentation Index

- `documents/AGENT_CONTEXT.md`: one-page thin-context map for coding agents after `AGENTS.md`
- `documents/README.md`: context-light guide for choosing which project docs to load first
- `documents/ARCHITECTURE.md`: canonical architecture and boundaries
- `documents/DETECTION_SEMANTICS.md`: meaning and calculation rules for Detection MVP report fields
- `documents/PROJECT_STRUCTURE.md`: placement rules after the refactor
- `documents/TESTING.md`: current test layout and commands
- `documents/EXECUTOR_PLAYWRIGHT.md`: sandbox and Playwright details
- `documents/DEVELOPMENT_PRIORITIES.md`: near-term priorities for the sandbox product
- `documents/PIPELINE_ROADMAP.md`: pipeline direction without multi-tenant assumptions
- `documents/automation_todo.md`: active task backlog
- `docs/risks.md`: current risk register
