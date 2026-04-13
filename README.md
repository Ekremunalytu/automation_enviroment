# ExTrace

`Last Updated: 2026-04-13`

ExTrace is a VS Code extension analysis platform built around three runtime surfaces:

- A FastAPI API for catalog ingestion, activation report access, marketplace download, and sandbox analysis.
- A Dockerized executor that runs full VS Code GUI sessions under Xvfb and drives them with Playwright.
- A Vite + React + Tailwind analyst console that consumes the API and visualizes activation reports and live simulation jobs.

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
  - React SPA with `Reports`, `Simulation`, and `Marketplace` routes.
- `legacy_ui/`
  - Previous Streamlit implementation retained as a compatibility snapshot during migration.

The repository now uses canonical imports only:

- Shared platform modules live under `appcore/`
- Workflow code lives under `workflows/`
- Host-side executor control lives under `executor/host.py`

## Request Flows

### Static Catalog Ingestion

`POST /createExtension`

1. `workflows.extension_catalog.router`
2. `workflows.extension_catalog.service`
3. `workflows.extension_catalog.package_parser`
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
2. `executor.host` Docker exec wrapper
3. `executor/flows/playwright/entrypoint.py`
4. Reports written under `output/`
5. Job snapshots persisted under `output/analysis_jobs/`

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
documents/                  Architecture, roadmap, and testing notes
docs/                       Targeted risk notes
```

## Documentation Index

- `documents/ARCHITECTURE.md`: canonical architecture and boundaries
- `documents/PROJECT_STRUCTURE.md`: placement rules after the refactor
- `documents/TESTING.md`: current test layout and commands
- `documents/EXECUTOR_PLAYWRIGHT.md`: sandbox and Playwright details
- `documents/automation_todo.md`: active roadmap
- `docs/risks.md`: current risk register
