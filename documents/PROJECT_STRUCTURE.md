# Project Structure

`Last Updated: 2026-03-06`

This is the canonical project layout after the architecture refactor.

## Top-Level Layout

```text
appcore/
  api/
  contracts/
  db/
  storage/
workflows/
  activation_reports/
  extension_catalog/
  marketplace/
executor/
  container/
  flows/playwright/
ui/
  views/
tests/
  executor/
  platform/
  workflows/
documents/
docs/
```

## Placement Rules

- Put new shared infrastructure into `appcore/`.
- Put workflow-specific routers, services, parsers, and helpers into the matching `workflows/<name>/` package.
- Put sandbox runtime code into `executor/`.
- Put dashboard-only code into `ui/`.
- Put tests beside the corresponding architecture slice under `tests/`.

## Canonical vs Compatibility Paths

### Canonical

- `appcore/api/config.py`
- `appcore/api/deps.py`
- `appcore/db/session.py`
- `appcore/storage/models.py`
- `appcore/storage/crud.py`
- `appcore/contracts/schemas.py`
- `workflows/*`

### Compatibility only

- `routers/`
- `scanner/`
- `core/`
- `database/`
- `crud/`
- `models/`
- `schemas/`

Compatibility modules exist for import stability and current tests. Do not place new business logic there.

## UI Layout

```text
ui/
  app.py
  api.py
  components.py
  config.py
  data_processing.py
  navigation.py
  state.py
  styles.py
  views/
    dashboard.py
    dashboard_tabs.py
    marketplace.py
    simulation.py
    theme.py
```

## Executor Layout

```text
executor/
  container/
    Dockerfile
    requirements.txt
    start.sh
  flows/playwright/
    entrypoint.py
    automation.py
    monitor.py
    workspace.py
    reload_vscode.py
    reset_state.py
    commands.py
    editor.py
    panel.py
    sidebar.py
    terminal.py
    settings.py
    debug.py
    triggers.py
    vscode.py
```

## Test Layout

```text
tests/
  conftest.py
  test_health.py
  executor/
  platform/
    api/
    contracts/
    storage/
    test_compat_wrappers.py
  workflows/
    activation_reports/
    extension_catalog/
    marketplace/
```

## Quick Change Map

- New API setting or dependency: `appcore/api/`
- New DB model or CRUD logic: `appcore/storage/` plus Alembic
- New catalog feature: `workflows/extension_catalog/`
- New activation report behavior: `workflows/activation_reports/`
- New marketplace or analysis behavior: `workflows/marketplace/`
- New sandbox capability: `executor/container/` or `executor/flows/playwright/`
- New dashboard view: `ui/views/`
