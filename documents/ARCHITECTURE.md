# ExTrace Architecture

`Last Updated: 2026-05-07`

System shape, runtime surfaces, and module map. **Slim canonical** —
detailed request flows under
[`architecture/data-flow.md`](architecture/data-flow.md);
boundary/dependency-direction rules under
[`architecture/boundary-rules.md`](architecture/boundary-rules.md).

Open this file when adding a new service/component, drawing a high-level
diagram, or onboarding to the canonical module set. Use
`PROJECT_STRUCTURE.md` for placement rules; subsystem reference docs
(`EXECUTOR_PLAYWRIGHT.md`, `DETECTION_SEMANTICS.md`) only when the lane
doc points to them.

## Product Assumptions

ExTrace is a single-operator sandbox appliance, not a multi-tenant
platform.

- One analyst, same machine or same Docker host deployment.
- One active background analysis job at a time.
- Extension execution stays Docker-isolated.
- Activation reports are artifact-first operator artifacts.
- Async job state is durable in PostgreSQL (`analysis_jobs`).
- ADR 0007 local-network-binding is **Accepted and implemented**
  `2026-04-29` via W8-7 — loopback defaults are enforced by
  `appcore/api/config.py`, `docker-compose.yml`, and
  `tests/architecture/test_default_bindings.py`.

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

### `appcore/` — shared platform code

API config + deps, DB session, ORM models, CRUD facade and ops split,
Pydantic v2 schema_defs and public schema facade. Write entrypoint for
catalog data + analysis-job metadata is `appcore/storage/crud.py`.

### `packages/` — framework-agnostic contracts and analysis logic

- `analysis_contracts/` — `ActivationReport`, `TriggerPayload`, and
  `detection/` namespace (`DetectionReport`, `DetectionFinding`,
  `Confidence`, `Verdict`, `AdversaryClass`, `RuleLifecycle`,
  `RuleExecutionStatus`, `quantize_confidence`).
- `analysis_planner/` — registries, selection, attempts, coverage
  accounting, payload serialization.
- `analysis_engine/` — detection rules under `rules/` (A1/A2/A3/A4/A6
  live; A5/A7 deferred — see `POST_POC_BACKLOG.md`); allow-lists
  (`benign_domains.txt`, `popular_extensions.txt`). Rules import only
  contracts.
- `marketplace_identity/` — `safe_marketplace_slug` helper (W8-2
  landed).

### `workflows/` — capability-organized business logic

- `extension_catalog/` — manifest lookup, parsing, validation,
  persistence, root catalog routes.
- `activation_reports/` — file-backed listing/retrieval under
  `/api/activations`.
- `marketplace/` — search/download, layered trigger planning, sync +
  async analysis, job snapshot persistence, cancel flow
  (`analysis_execution.py` heartbeat polls cancel + reset_sandbox;
  `cancel_analysis_job` carries pessimistic lock CRUD).

### `executor/` — sandbox control + runtime

- `control.py` — workflow-facing boundary (reset, install, automation
  run, reload, trigger cleanup); install retries once through
  `reload_vscode_window` on transient IPC markers.
- `host.py` — Docker exec, retry/cleanup behavior.
- `container/` — Docker image, `start.sh`, shared `launch_vscode.sh`.
- `flows/playwright/` — VS Code automation, trigger loading, the
  `monitor/` package (facade in `monitor/__init__.py`),
  lifecycle/source/runtime helpers, plus the `stimulus/`, `health/`,
  `entrypoint/`, `vscode/`, `workspace/`, `signals/` subpackages and
  the existing `attribution/` subpackage (W12-1, 2026-05-07). Top
  level keeps ≤10 flat modules. **Detail:** `EXECUTOR_PLAYWRIGHT.md`
  (slim) → `executor/playwright-flow.md` for in-flow specifics.
- `flows/playwright/attribution/` — events.py + links.py + facade
  re-export.
- `flows/playwright/runtime_capture/` — network/filesystem/extension-host
  helpers.
- `flows/harness_extension/` — local helper extension for harness
  stimulus.

### `ui/` — analyst SPA

App shell + features (`evidence`, `marketplace`, `simulation`, `reports`,
`rules`, `settings`, `system`); shared v3 primitives under
`ui/src/components/v3/` mirrored in `ui/tailwind.config.js`. UI v3
redesign minimal-completion landed `2026-04-29` (`REFACTOR_STATUS.md`).

## Canonical Boundaries (summary)

- Shared reusable → `appcore/`.
- Framework-agnostic contracts/logic → `packages/`.
- Workflow-specific business → `workflows/`.
- Catalog and analysis-job DB writes go through
  `appcore/storage/crud.py`.
- Manifest data validated with Pydantic before insertion.
- Uniqueness constraint `(publisher, name, version)`.
- Sandbox execution Docker-isolated, invoked from workflows only
  through `executor/control.py`.

Full boundary rules + import graph enforcement details:
[`architecture/boundary-rules.md`](architecture/boundary-rules.md).

## Request Flows (summary)

| # | Flow | Endpoint | Entry → Exit |
|---|---|---|---|
| 1 | Static catalog ingestion | `POST /createExtension` | `extension_catalog.router` → `crud` → PostgreSQL |
| 2 | Marketplace download | `POST /api/marketplace/download` | `marketplace.client.download_and_extract_vsix` → `extension_catalog.service` → `crud` |
| 3 | Sandbox analysis | `POST /api/marketplace/analyze[/start]` | `marketplace.router` → `analysis_service` → `executor.control` → `executor/flows/playwright/` → `output/activation_report_*.json` |
| 4 | Activation report browsing | `GET /api/activations[/{name}]` | `activation_reports.router` → `output/` |
| 5 | Analyst UI loop | `/marketplace` → `/simulation` → `/reports` | search → analyze → poll → inspect |

Step-by-step trace per flow + cancel/heartbeat/error paths:
[`architecture/data-flow.md`](architecture/data-flow.md).

## Data Boundaries

- **PostgreSQL** — extension metadata, manifest activation events,
  capabilities/scripts/contributes metadata, async job metadata
  (`analysis_jobs`).
- **Filesystem** — extracted extensions under `extensions/`,
  malicious-fixture scaffold under `extensions/malicious/`, activation
  reports under `output/`.
- **In-memory** — none authoritative; async job state is durable in
  Postgres and loaded per request/transition.

The split is intentional for the current product shape: DB for catalog +
durable job metadata; dynamic-analysis artifacts (reports) remain
filesystem-first.

## Testing Structure

See [`TESTING.md`](TESTING.md) for layer/fixture/command detail. Quick
map:

- `tests/platform/` — shared platform contracts, config, storage,
  canonical import checks.
- `tests/architecture/` — repo-wide import graph enforcement.
- `tests/workflows/` — activation reports, extension catalog,
  marketplace.
- `tests/executor/` — Playwright + executor-host.
- `tests/executor/scanner/` — Docker exec wrapper.
- `tests/security/` — malicious-fixture hygiene + PoC canary contracts.
- `tests/smoke/` — end-to-end marketplace analysis against the executor
  container.
- `ui/src/**/*.test.ts(x)` — Vitest + Testing Library.

## Architectural Rules (summary)

Full list with rationale:
[`architecture/boundary-rules.md`](architecture/boundary-rules.md).

- Canonical imports from `appcore/`, `packages/`, `workflows/`,
  `executor/`.
- SQLAlchemy 2.0 style only.
- Pydantic v2 APIs only.
- Workflow access to sandbox mechanics goes through
  `executor/control.py` (import graph tests fail otherwise).
- No queue-backed or multi-tenant infrastructure unless product
  assumptions change first.
