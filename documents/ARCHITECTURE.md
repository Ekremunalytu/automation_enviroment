# ExTrace Architecture

`Last Updated: 2026-04-20`

This document reflects the current codebase shape in `main.py`, `appcore/`,
`packages/`, `workflows/`, `executor/`, and `ui/`.

Open this for system shape and request-flow questions. For placement rules use
`PROJECT_STRUCTURE.md`; for executor or report internals, open the specialized
docs only if the task reaches those layers.

## Product Assumptions

ExTrace is still implemented as a single-operator sandbox appliance, not a
multi-tenant platform.

- one analyst
- same machine or same Docker host deployment
- one active background analysis job at a time
- extension execution stays isolated in Docker
- activation reports remain artifact-first operator artifacts
- async job state is durable in PostgreSQL (`analysis_jobs`)

## Runtime Surfaces

```mermaid
flowchart LR
    UI["React analyst console (`ui/`)"] --> API["FastAPI app (`main.py`)"]
    API --> WF["Workflow routers/services (`workflows/`)"]
    WF --> CORE["Shared platform code (`appcore/`)"]
    WF --> PKG["Framework-agnostic logic (`packages/`)"]
    CORE --> DB[("PostgreSQL")]
    WF --> CTRL["Executor boundary (`executor/control.py`)"]
    CTRL --> HOST["Executor host wrapper (`executor/host.py`)"]
    HOST --> EXEC["Executor container"]
    EXEC --> OUT["`output/` activation reports"]
```

## Canonical Modules

### `appcore/`

Shared platform code used by more than one workflow.

- `appcore/api/config.py`
  - Pydantic settings for project, API, database, and executor runtime.
- `appcore/api/deps.py`
  - FastAPI dependencies such as `get_db`.
- `appcore/db/session.py`
  - SQLAlchemy engine and `SessionLocal`.
- `appcore/storage/models.py`
  - ORM export surface.
- `appcore/storage/crud.py`
  - Canonical CRUD facade; write entrypoint for persisted catalog data and
    analysis-job metadata.
- `appcore/storage/crud_ops/*`
  - Read/write implementation split.
- `appcore/contracts/schema_defs/*`
  - Pydantic v2 request/response contracts.
- `appcore/contracts/schemas.py`
  - Public schema facade used by routers and services.

### `packages/`

Framework-agnostic contracts and analysis logic.

- `packages/analysis_contracts/`
  - backend-owned contracts for `ActivationReport`, `TriggerPayload`, and the
    reserved `detection/` namespace for W5 `DetectionReport` DTOs
- `packages/analysis_planner/`
  - planner registries, selection logic, attempts, coverage accounting, and
    payload serialization
- `packages/analysis_engine/`
  - reserved extraction surface for shared analysis logic that should not stay
    buried in executor-only modules

### `workflows/`

Business behavior organized by capability.

- `workflows/extension_catalog/`
  - manifest lookup, parsing, validation, persistence, and root catalog routes
- `workflows/activation_reports/`
  - file-backed report listing and retrieval under `/api/activations`
- `workflows/marketplace/`
  - marketplace search/download, layered trigger planning, sync analysis,
    async job orchestration, and job snapshot persistence

### `executor/`

Sandbox control and runtime.

- `executor/control.py`
  - public workflow-facing boundary for reset, install, automation run, reload,
    and trigger cleanup
- `executor/host.py`
  - Docker exec implementation details and retry/cleanup behavior
- `executor/container/`
  - Docker image, start script, and sandbox boot configuration
- `executor/flows/playwright/`
  - VS Code automation, trigger loading, the thin `monitor.py` facade, and
    sibling lifecycle/source/runtime/attribution helpers for report building,
    health derivation, and risk/signal-summary calculation (the
    authoritative detection-layer `Verdict` lives in
    `packages/analysis_contracts/detection/`)
- `executor/flows/playwright/runtime_capture/`
  - monitor-owned network, filesystem, extension-host, and log-summary helpers
    re-exported through `monitor.py`
- `executor/flows/harness_extension/`
  - local helper extension used by harness-assisted stimulus paths

### `ui/`

Primary analyst-facing SPA.

- `ui/src/app/`
  - route shell and lazy route composition
- `ui/src/features/marketplace/`
  - search, download, and analysis job launch
- `ui/src/features/simulation/`
  - job polling, live evidence, log streams, and inspector surface
- `ui/src/features/reports/`
  - final report workspace with tabbed evidence slices
- `ui/src/lib/`
  - API client, runtime config, adapters, generated contract types, rules,
    chart helpers, and shared frontend helpers

## Canonical Boundaries

- Shared reusable code belongs in `appcore/`.
- Framework-agnostic contracts and planner logic belong in `packages/`.
- Workflow-specific business logic belongs beside the owning workflow in
  `workflows/`.
- All catalog and analysis-job DB writes go through `appcore/storage/crud.py`.
- Manifest data is validated with Pydantic before insertion.
- The uniqueness constraint remains `(publisher, name, version)`.
- Sandbox execution remains isolated in Docker and is invoked from workflows
  only through `executor/control.py`.

## Request Flows

### 1. Static Catalog Ingestion

`POST /createExtension`

1. `workflows.extension_catalog.router`
2. `workflows.extension_catalog.service.create_extension_by_name`
3. `workflows.extension_catalog.manifest_reader` +
   `workflows.extension_catalog.manifest_parser`
4. `appcore.contracts.schemas`
5. `appcore.storage.crud`
6. PostgreSQL

Notes:

- `ExtensionSchema` and related nested contracts are built before persistence.
- Duplicate inserts fail closed on the `(publisher, name, version)` constraint.

### 2. Marketplace Download

`POST /api/marketplace/download`

1. `workflows.marketplace.client.download_and_extract_vsix`
2. `workflows.extension_catalog.service.create_extension_from_directory`
3. `appcore.storage.crud`

Notes:

- Manifest identity is checked against the requested publisher/name/version.
- Existing catalog entries return a usable success response with the existing DB
  id instead of silently re-inserting.

### 3. Sandbox Analysis

`POST /api/marketplace/analyze` or `POST /api/marketplace/analyze/start`

1. `workflows.marketplace.router`
2. `workflows.marketplace.analysis_service`
3. `workflows.marketplace.trigger_service`
4. `executor.control`
5. `executor.host`
6. `executor/flows/playwright/entrypoint.py`
7. `executor/flows/playwright/monitor.py`
8. `executor/flows/playwright/report_builder.py`
9. `output/activation_report_*.json`

Async job mode persists step-tracked analysis metadata in the PostgreSQL
`analysis_jobs` table through `appcore.storage.crud` and
`workflows.marketplace.job_service`.

Notes:

- The async endpoint serializes work to one active job.
- Persisted jobs carry an `owner_boot_id`; if the API restarts mid-run, the job
  is marked failed on the next load.
- Trigger planning may resolve to layered execution or a scenario-zero
  `skip_automation` run for non-executable fixtures.
- The workflow-side trigger contract is `TriggerPlan` only; the old tuple shim
  is removed.
- Startup fails fast if job recovery or migration state for `analysis_jobs` is
  unavailable.

### 4. Activation Report Browsing

`GET /api/activations`, `GET /api/activations/latest`,
`GET /api/activations/{name}`

1. `workflows.activation_reports.router`
2. `output/activation_report*.json`

Notes:

- Report reads retry transient `OSError` failures.
- Latest-report reads fall back to the next-most-recent valid JSON file if the
  newest file is still being written.

### 5. Analyst UI Loop

1. `/marketplace`
   - search results, download, then launch async analysis
2. `/simulation`
   - poll job state and load the in-progress report by `report_path`
3. `/reports`
   - inspect report slices, attribution, risk signals, and rule draft output

## Data Boundaries

### PostgreSQL-backed state

- extension metadata
- activation events parsed from manifests
- capabilities, scripts, and contributes metadata
- async marketplace job metadata (`analysis_jobs`)

### Filesystem-backed state

- extracted extensions under `extensions/`
- malicious-fixture manifest scaffold under `extensions/malicious/`
- activation reports under `output/`

### In-memory state

- no analysis-job cache is the source of truth; async job state is durable in
  Postgres and loaded per request/job transition

This split is still intentional for the current product shape. The database is
used for extension catalog data and durable async job metadata; dynamic-analysis
artifacts such as reports still remain filesystem-first.

## Testing Structure

- `tests/platform/`
  - shared platform contracts, config, storage, and canonical import checks
- `tests/architecture/`
  - repo-wide import graph enforcement for `packages/`, `executor/`, and
    `workflows/`
- `tests/workflows/`
  - activation reports, extension catalog, and marketplace behavior
- `tests/executor/`
  - Playwright helper and executor-host coverage
- `tests/scanner/`
  - focused unit coverage for the Docker exec wrapper surface
- `tests/security/`
  - malicious-fixture scaffold hygiene and PoC canary coverage contracts
- `tests/smoke/`
  - end-to-end marketplace analysis acceptance against the executor container
- `ui/src/**/*.test.ts(x)`
  - Vitest + Testing Library coverage for the SPA

## Architectural Rules

- Prefer canonical imports from `appcore/`, `packages/`, `workflows/`, and
  `executor/`.
- Use SQLAlchemy 2.0 style only.
- Use Pydantic v2 APIs only.
- Keep compatibility/historical surfaces thin and out of new feature work.
- Keep workflow access to sandbox mechanics behind `executor/control.py`; the
  import graph tests fail if workflows reach into `executor.host` directly.
- Do not introduce queue-backed or multi-tenant infrastructure unless the
  product assumptions change first.
