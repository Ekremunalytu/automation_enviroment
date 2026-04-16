# Project Structure

`Last Updated: 2026-04-16`

This is the current top-level layout and placement guidance for the refactored
repository.

## Top-Level Layout

```text
alembic/                   Schema migrations
appcore/                   Shared platform code
docker/                    API container build files
docs/                      Narrow risk notes outside the main doc set
documents/                 Canonical project documentation
executor/                  Sandbox host wrapper + container runtime
extensions/                Downloaded/extracted VSIX fixtures and samples
legacy_ui/                 Archived Streamlit UI snapshot
output/                    Generated reports and runtime artifacts
scripts/                   Small maintenance helpers
tests/                     Python test suite
ui/                        Primary React analyst console
workflows/                 Canonical business workflows
```

## Placement Rules

- Put reusable platform code in `appcore/`.
- Put workflow-specific routers, services, parsers, and trigger logic in the
  matching `workflows/<name>/` package.
- Put sandbox runtime code in `executor/`.
- Put analyst-facing frontend code in `ui/`.
- Keep `legacy_ui/` archival unless a migration reference is required.
- Keep generated artifacts in `output/`; do not treat them as source code.
- Keep extension fixtures and downloaded VSIX artifacts in `extensions/`.
- If a change affects persisted catalog schema, pair it with Alembic updates in
  `alembic/versions/`.

## Canonical Paths

- `main.py`
- `appcore/api/config.py`
- `appcore/api/deps.py`
- `appcore/db/session.py`
- `appcore/storage/models.py`
- `appcore/storage/crud.py`
- `appcore/contracts/schemas.py`
- `workflows/extension_catalog/`
- `workflows/activation_reports/`
- `workflows/marketplace/`
- `executor/host.py`

## Workflow Layout

```text
workflows/
  activation_reports/
    router.py
  extension_catalog/
    manifest_parser.py
    manifest_reader.py
    package_parser.py
    router.py
    service.py
  marketplace/
    analysis_service.py
    client.py
    job_service.py
    router.py
    trigger_service.py
    triggers.py
```

## UI Layout

```text
ui/
  src/
    app/
      App.tsx
      layout/
    components/
      evidence/
      marketplace/
      simulation/
      ui/
    features/
      marketplace/
      reports/
      simulation/
    lib/
      adapters/
      api/
      charts/
      rules/
      types/
    main.tsx
    index.css
  smoke/
  Dockerfile
  README.md
```

Notes:

- The routed analyst surfaces are `/marketplace`, `/simulation`, and `/reports`.
- Evidence, inspector, and rule-draft behavior is largely composed from
  `ui/src/components/evidence/` plus adapters and draft helpers in
  `ui/src/lib/`.

## Executor Layout

```text
executor/
  host.py
  container/
    Dockerfile
    requirements.txt
    start.sh
  flows/
    harness_extension/
      extension.js
      package.json
    playwright/
      annotation.py
      automation.py
      capture.py
      commands.py
      debug.py
      editor.py
      entrypoint.py
      health.py
      keyboard.py
      language_samples.py
      monitor.py
      panel.py
      reload_vscode.py
      report_builder.py
      reset_state.py
      settings.py
      sidebar.py
      signals.py
      stimulus.py
      terminal.py
      triggers.py
      vscode.py
      workspace.py
```

## Test Layout

```text
tests/
  conftest.py
  test_health.py
  executor/
    test_playwright_automation.py
    test_playwright_commands.py
    test_playwright_entrypoint.py
    test_playwright_monitor.py
    test_playwright_stimulus.py
    test_reset_state.py
    test_workspace.py
  platform/
    api/
    contracts/
    storage/
    test_canonical_imports.py
  scanner/
    test_executor.py
  smoke/
    test_marketplace_analysis_smoke.py
  workflows/
    activation_reports/
    extension_catalog/
    marketplace/
```

UI tests live under `ui/src/**/*.test.ts(x)`.

## Generated and Reference Areas

- `extensions/`
  - downloaded VSIX artifacts, extracted extension directories, and pinned test
    fixtures
- `output/`
  - activation reports and async analysis job JSON snapshots
- `documents/`
  - architecture, executor, testing, roadmap, and semantics notes
- `docs/`
  - narrower risk notes such as `docs/risks.md`

## Quick Change Map

- Shared config or dependency injection: `appcore/api/`
- Shared schema or model change: `appcore/contracts/`, `appcore/storage/`,
  `alembic/versions/`, matching tests
- Catalog feature: `workflows/extension_catalog/`
- Activation report behavior: `workflows/activation_reports/`
- Marketplace download/analysis feature: `workflows/marketplace/`
- Sandbox runtime behavior: `executor/host.py` or `executor/flows/playwright/`
- UI route or workspace behavior: `ui/src/features/`
- UI shared primitive: `ui/src/components/`
- UI API/adapters/rule logic: `ui/src/lib/`
