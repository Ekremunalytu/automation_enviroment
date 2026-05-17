# ExTrace

`Last Updated: 2026-05-17 (W15 active — W15-1..W15-6 closed; W15-7 closed 2026-05-17 — compose image SHA pin (54e7a93) + test extension (7ebbbfb) + GH action trivy version pin (452f1a1; aquasecurity/trivy-action@v0.36.0) + final preamble refresh)`

ExTrace is a VS Code extension analysis platform built around three runtime
surfaces:

- A FastAPI API for catalog ingestion, activation report access, marketplace
  download, and sandbox analysis.
- A Dockerized executor that runs full VS Code GUI sessions under Xvfb and
  drives them with Playwright.
- A Vite + React + Tailwind analyst console that consumes the API and
  visualizes activation reports and live simulation jobs.

## Operating Model

ExTrace is intentionally designed as a single-user sandbox appliance, not a
multi-tenant web platform.

- Backend, UI, PostgreSQL, and executor are expected to run on the same machine
  or inside the same Docker host.
- The primary deployment shape is a local or lab sandbox where one analyst
  inspects one extension at a time.
- Background analysis is intentionally limited to one active job at a time.
- Activation reports remain file-backed operator artifacts under `output/`,
  while async analysis job metadata is persisted in PostgreSQL.
- If the API process restarts during an active analysis, that job is marked
  failed and should be rerun.
- ADR 0007 local-network-binding is Accepted **and implemented (W8-7,
  `2026-04-29`)** — `appcore/api/config.py` defaults bind `127.0.0.1`,
  CORS allow-list replaces the wildcard, every `docker-compose.yml`
  `ports:` entry carries an explicit `127.0.0.1:` prefix, and host-side
  CDP exposure is gated behind the Compose `debug` profile. To expose
  services on the LAN, follow `documents/runbooks/lan-exposure.md` and set
  `EXTRACE_ALLOW_LAN=1` (host-mode `make dev-lan`) or edit the compose
  file directly.

## Current Phase

- W4 stabilization, W5 detection foundations, W6 automation hardening, and
  W7 PoC acceptance are all closed (last closure `2026-04-23`).
- Post-W7 hardening (`2026-04-24`) landed reliability + modularization
  follow-ups (fatal UI-crash fail-fast, scan-between VS Code restart,
  `attribution/` subpackage split, `sim-target` Makefile lane).
- Post-W7 simulation UX + reliability (`2026-04-25`) landed weighted
  simulation progress, full-stack analysis cancel flow, the VNC harness
  ready-marker fix, and the `t1-demo-runnable-canary` fixture + rule +
  `make demo-canary` lanes.
- PR345 target activation lifecycle is complete as of `2026-04-27`; PRs 1-5
  plus ADR 0006 target output-channel capture landed on
  `feat/pr345-completion`.
- W8-0 deterministic harness readiness gate landed on `2026-04-27`, unblocking
  W8-1 and W8-3.
- **W8 closed for active work `2026-04-29`** (W8-1..W8-7 + W8-9 landed,
  W8-8 deferred); **W9 closed `2026-05-04`** (PR #9); **W10 closed
  `2026-05-04`** (PR #11); **W11 closed `2026-05-05`** and merged via
  PR #14; **W12 closed `2026-05-10`** and merged via PR #18 (`33a0852`).
  **W13 Test Expansion + Observability closed `2026-05-13`**
  (W13-1..W13-13 all GREEN). Close-out PR #20 `week13 -> main` **MERGED**
  `2026-05-13` via `772deb3` (close-gate cleared pre-merge). Past
  tracker:
  [`active-work/W13-test-expansion-observability.md`](documents/active-work/W13-test-expansion-observability.md).
  **W14 — Codex M-class Acceptance + Observability closed `2026-05-14`**
  (W14-1..W14-6 sub-iter slate + W14-7/W14-8 post-slate hotfixes +
  close-out hygiene pass landed: Ruff lint, UI contract sync, markdown
  formatting, doc truth-state alignment, `make markdownlint` regression
  gate, ADR code fence arch test). Close-out PR #21 `week14 -> main`
  **MERGED** `2026-05-14` via `4e03c8d`. Frozen tracker:
  [`active-work/W14-codex-acceptance-observability.md`](documents/active-work/W14-codex-acceptance-observability.md).
  **Active phase: W15 — Codex U-class Close-Out + UI Bounds + Posture**
  is active on the `week15` branch (cut from `main` HEAD `7cc2921` on
  `2026-05-14`); see
  [`active-work/W15-codex-uclass-bounds-posture.md`](documents/active-work/W15-codex-uclass-bounds-posture.md).
  W15-1 closed `2026-05-14` via `c58c365` (sync analyze error taxonomy
  parity, M10 close); W15-2 closed `2026-05-14` via `765cde7`
  (`clean_workspace` is_symlink-before-rmtree, M12 close); W15-3 closed
  `2026-05-15` via `3512a7c` (`activationEvents` bounds + Alembic
  field-length migration, U8 close); W15-4 closed `2026-05-16` via
  `89e13e3` (UI bounds bundle: timeline / density strip / relations
  graph caps with truncation indicators, U1/U2/U3 + U6 close);
  **W15-1 post-slate typing hotfix** landed `2026-05-16` via `976dc96`
  (`ANALYZE_*_ERROR_TYPES` annotation narrowed `BaseException` →
  `Exception` after the W15-4 close-out `make typecheck` surfaced the
  mismatch). W15-5..W15-7 pending sequential pull. **W15 mid-iter
  hygiene `2026-05-16`** refreshed six canonical doc preambles to W15
  truth-state, added `tests/architecture/test_doc_preamble_consistency.py`,
  and appended three new audit findings to `POST_POC_BACKLOG.md`
  (`health-reconciliation-responsibility-split`,
  `marketplace-router-test-suite-split`,
  `analysis-job-worker-entry-crud-ownership`).
- **Canonical source of truth for phase state:**
  [`documents/REFACTOR_STATUS.md`](documents/REFACTOR_STATUS.md).
  Deferred items: [`documents/POST_POC_BACKLOG.md`](documents/POST_POC_BACKLOG.md).
  W8-W13 plan: [`documents/REFACTOR_OPTIMIZATION.md` §11](documents/REFACTOR_OPTIMIZATION.md).
  W14 plan: [`documents/REFACTOR_OPTIMIZATION.md` §12](documents/REFACTOR_OPTIMIZATION.md).
  W15 plan: [`documents/REFACTOR_OPTIMIZATION.md` §13](documents/REFACTOR_OPTIMIZATION.md).

## Current Architecture

The refactor introduced a canonical split between shared platform code and
workflow code:

- `appcore/`
  - Shared platform modules.
  - `api/`: settings and FastAPI dependencies.
  - `db/`: SQLAlchemy engine and session factory.
  - `storage/`: ORM models and CRUD helpers.
  - `contracts/`: shared Pydantic v2 schemas.
- `packages/`
  - Framework-agnostic contracts and analysis logic.
  - `analysis_contracts/`: backend-owned analysis contracts, activation
    reports, trigger payloads, and detection DTOs.
  - `analysis_planner/`: trigger planning logic.
  - `analysis_engine/`: reserved extraction surface for shared analysis logic.
- `workflows/`
  - Business workflows grouped by capability.
  - `extension_catalog/`: extension ingestion, parsing, and catalog endpoints.
  - `activation_reports/`: reads JSON activation reports from `output/`.
  - `marketplace/`: Marketplace search/download and sandbox analysis.
- `executor/`
  - Sandbox runtime.
  - `control.py`: workflow-visible sandbox boundary.
  - `container/`: Docker image, entrypoint (`start.sh`), and the shared
    `launch_vscode.sh` script used at boot and by scan-between resets.
  - `flows/playwright/`: Playwright automation helpers, package-mode
    `entrypoint/`, `monitor/` facade, attribution/scenario/runtime-capture
    packages, and focused helper packages for health, stimulus, workspace,
    VS Code UI, and signals.
- `ui/`
  - Primary analyst-facing React SPA built with Vite and Tailwind.
  - `src/app/`: shell and route composition.
  - `src/features/`: `evidence`, `marketplace`, `reports`, `rules`,
    `settings`, `simulation`, `system`.
  - `src/lib/`: API client, adapters, generated contract types, and shared
    frontend helpers.

The repository now uses canonical imports only:

- Shared platform modules live under `appcore/`
- Framework-agnostic analysis logic lives under `packages/`
- Workflow code lives under `workflows/`
- Workflow-visible executor control lives under `executor/control.py`

## Request Flows

### Static Catalog Ingestion

`POST /createExtension`

1. `workflows.extension_catalog.router`
2. `workflows.extension_catalog.service`
3. `workflows.extension_catalog.manifest_reader` +
   `workflows.extension_catalog.manifest_parser`
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
4. `executor.control` boundary
5. `executor.host` Docker exec wrapper
6. `python -m executor.flows.playwright.entrypoint`
7. Reports written under `output/`
8. Async job metadata persisted in PostgreSQL `analysis_jobs`

Notes:

- `POST /api/marketplace/analyze` is the direct request/response path.
- `POST /api/marketplace/analyze/start` is the background path used by the
  React UI.
- Only one background analysis should run at a time in the intended sandbox
  deployment.
- Startup fails fast if the `analysis_jobs` storage path is unavailable or the
  required migration has not been applied.
- Trigger planning may choose layered execution or a scenario-zero
  `skip_automation` run for non-executable fixtures.

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
- `POST /api/marketplace/analyze/{job_id}/cancel`

### Operator Settings

- `GET /api/settings/security/thresholds`
- `PUT /api/settings/security/thresholds`

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
make test-security
make ui-types-check
make ui-boundaries
make exec-up
make exec-run
make ui-up
make sim-target TARGET=publisher.name      # target-extension smoke
make sim-all                                # UI-stimulus stress (no target ext.)
make demo-canary                            # end-to-end demo runnable canary
make demo-canary-offline                    # offline fixture validation
cd ui && npm run dev
cd ui && npm run test
.venv/bin/pytest
.venv/bin/pytest -m "not smoke and not requires_db"
.venv/bin/pytest -m "requires_db"
.venv/bin/pytest -m smoke
```

### Service Endpoints

ADR 0007 — every endpoint below binds loopback only by default. Replace
`127.0.0.1` with the operator-host LAN IP only after the
`documents/runbooks/lan-exposure.md` checklist is applied.

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Web UI: `http://127.0.0.1:3000`
- noVNC executor view: `http://127.0.0.1:6080/vnc.html`
- CDP (debug profile only): `http://127.0.0.1:9222` — start with
  `make up-debug` or `docker compose --profile debug up`. Absent from the
  default `make up` service set.

## Project Layout

```text
appcore/                    Shared platform modules
packages/                   Framework-agnostic contracts and analysis logic
workflows/                  Canonical business workflows
executor/
  control.py               Workflow-visible sandbox boundary
  container/               Sandbox image and startup scripts
  flows/playwright/        VS Code GUI automation packages
ui/                         React + Vite analyst console
tests/
  architecture/            Import-graph and boundary checks
  platform/                Shared platform tests
  workflows/               Workflow tests
  executor/                Playwright runtime tests
    scanner/               Docker exec wrapper tests
  security/                Malicious-fixture scaffold checks
  smoke/                   End-to-end marketplace analysis tests
  ui tests live under ui/src/**/*.test.ts(x)
documents/                  Architecture, roadmap, and testing notes
docs/                       Targeted risk notes
```

## Documentation Index

- `documents/AGENT_CONTEXT.md`: thin task-routing map for coding agents after
  `AGENTS.md`
- `documents/agent-lanes/`: lazy-load task-lane docs for platform/storage,
  marketplace/analysis, executor/runtime, security/detection, UI, and docs
  maintenance
- `documents/README.md`: context-light guide for choosing which project docs to
  load first
- `documents/REFACTOR_STATUS.md`: slim current-state closure board and phase
  handoff history
- `documents/POST_POC_BACKLOG.md`: deferred work items and the pull-next list
- `documents/ARCHITECTURE.md`: canonical architecture and boundaries
- `documents/DETECTION_SEMANTICS.md`: meaning and calculation rules for
  exported `ActivationReport` fields
- `documents/PROJECT_STRUCTURE.md`: placement rules after the refactor
- `documents/TESTING.md`: current test layout and commands
- `documents/EXECUTOR_PLAYWRIGHT.md`: sandbox and Playwright details
- `documents/DEVELOPMENT_PRIORITIES.md`: near-term priorities for the sandbox
  product
- `documents/PIPELINE_ROADMAP.md`: pipeline direction without multi-tenant
  assumptions
- `documents/VSCODE_API_COVERAGE_AUDIT.md`: capability support and
  trigger/verification gaps
- `documents/automation_todo.md`: legacy/off-path backlog notes; current
  pull-next truth is `documents/POST_POC_BACKLOG.md` plus the active tracker
- `docs/risks.md`: current risk register
