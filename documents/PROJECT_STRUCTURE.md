# Project Structure

`Last Updated: 2026-05-28 — W22 closed synthetically on week22 and merged to main via PR #31 week22 -> main 1399f82; W21 closed and merged via PR #30 5dc18aa.`

Top-level layout and placement guidance. **Slim canonical** — full
directory trees for `executor/flows/playwright/`, `ui/src/`, and
`tests/` removed; recover them with `ls` or `find`. Forbidden top-level
directory list (legacy don't-recreate set) lives at
[`structure/legacy-do-not-recreate.md`](structure/legacy-do-not-recreate.md).
Test layer detail lives at
[`structure/test-layout.md`](structure/test-layout.md) (coordinated with
[`TESTING.md`](TESTING.md)).

## Top-Level Layout

```text
alembic/                   Schema migrations
appcore/                   Shared platform code
docker/                    API container build files
documents/                 Canonical project docs + human-readable guides
executor/                  Sandbox host wrapper + container runtime
extensions/                Downloaded/extracted VSIX fixtures and samples
packages/                  Framework-agnostic contracts and analysis logic
output/                    Generated reports and runtime artifacts
scripts/                   Small maintenance helpers
tests/                     Python test suite
ui/                        Primary React analyst console
workflows/                 Canonical business workflows
```

## Placement Rules

- Reusable platform code → `appcore/`.
- Framework-agnostic contracts or planning logic → `packages/`.
- Workflow-specific routers/services/parsers/triggers →
  `workflows/<name>/`.
- Sandbox runtime code → `executor/`.
- Analyst-facing frontend → `ui/`.
- Generated artifacts stay in `output/`; not source code.
- Extension fixtures and downloaded VSIX artifacts → `extensions/`.
- Persisted catalog schema changes pair with Alembic migrations under
  `alembic/versions/`.

## Canonical Paths

- `main.py`
- `appcore/api/config.py`
- `appcore/api/deps.py`
- `appcore/db/session.py`
- `appcore/storage/models.py`
- `appcore/storage/crud.py`
- `appcore/contracts/schemas.py`
- `packages/analysis_contracts/`
- `packages/analysis_planner/`
- `packages/analysis_engine/`
- `packages/marketplace_identity/`
- `workflows/extension_catalog/`
- `workflows/activation_reports/`
- `workflows/marketplace/`
- `executor/control.py`
- `executor/host.py`

## Quick Change Map

| Change kind | Edit |
|---|---|
| Shared config / dependency injection | `appcore/api/` |
| Shared schema / model | `appcore/contracts/`, `appcore/storage/`, `alembic/versions/`, matching tests |
| Framework-agnostic contract or planner | `packages/analysis_contracts/` or `packages/analysis_planner/` |
| Catalog feature | `workflows/extension_catalog/` |
| Activation report behavior | `workflows/activation_reports/` |
| Marketplace download/analysis | `workflows/marketplace/` |
| Sandbox runtime behavior | `executor/control.py`, `executor/host.py`, or `executor/flows/playwright/` |
| UI route or workspace behavior | `ui/src/features/` |
| UI shared primitive | `ui/src/components/` (v3 primitives in `components/v3/`) |
| UI API / adapters / rule logic | `ui/src/lib/` |
| Security scaffold or malicious fixture | `packages/analysis_contracts/detection/`, `extensions/malicious/`, `tests/security/`, ADRs under `documents/adrs/` |

## Workflow Layout (summary)

```text
workflows/
  activation_reports/   router
  extension_catalog/    manifest_*, package_parser, router, service
  marketplace/          analysis_*, client, job_service, router, trigger_*
```

Detail: `ls workflows/<name>/`.

## Executor Layout (summary)

```text
executor/
  control.py            workflow-facing boundary
  host.py               docker exec + retry/cleanup
  container/            Dockerfile, start.sh, launch_vscode.sh
  flows/
    harness_extension/  local helper extension
    playwright/         VS Code automation packages:
      attribution/, entrypoint/, health/, monitor/, runtime_capture/,
      scenarios/, signals/, stimulus/, vscode/, workspace/
```

Full file inventory of `executor/flows/playwright/` lives in code (`ls
executor/flows/playwright/`); the slim canonical lists only package-level
shape and the top level must stay at ≤10 flat `.py` files. Subsystem detail
in [`EXECUTOR_PLAYWRIGHT.md`](EXECUTOR_PLAYWRIGHT.md) and split docs under
`executor/`.

## UI Layout (summary)

```text
ui/src/
  app/                  shell, layout
  components/v3/        shared primitives (Panel, Tabs, MetricCell, …)
  features/             evidence, marketplace, simulation, reports, rules, settings, system
  lib/                  api, adapters, charts, types, rules, helpers
```

UI v3 primitives mirrored in `ui/tailwind.config.js`. Backend gaps
tracked under `[BACKLOG ui-v3-1..8]` and `[BACKLOG ui-v3-13]` in
[`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md). UI adds `Backend pending`
badges or `data-feature-stub` markers where appropriate.

## Generated And Reference Areas

- `extensions/` — downloaded VSIX artifacts, extracted extension dirs,
  pinned test fixtures; `extensions/malicious/` for malicious-fixture
  manifests and canary scaffold metadata.
- `output/` — activation reports and executor-side runtime artifacts.
- `documents/` — canonical project docs plus the human-readable guides
  (`human-guide.md`, `how-it-works.md`, `operator-quickstart.md`,
  `api-and-flows.md`, `risks.md`) (this folder).

## See Also

- Forbidden directories (must not be recreated):
  [`structure/legacy-do-not-recreate.md`](structure/legacy-do-not-recreate.md).
- Test layout detail (coordinates with `TESTING.md`):
  [`structure/test-layout.md`](structure/test-layout.md).
- Boundary/import-graph rules:
  [`architecture/boundary-rules.md`](architecture/boundary-rules.md).
