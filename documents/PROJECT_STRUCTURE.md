# Project Structure

`Last Updated: 2026-04-13`

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
  src/
legacy_ui/
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
- Put current analyst console code into `ui/`.
- Treat `legacy_ui/` as archive-only unless a migration needs to reference it.
- Put tests beside the corresponding architecture slice under `tests/`.

## Canonical Paths

### Canonical

- `appcore/api/config.py`
- `appcore/api/deps.py`
- `appcore/db/session.py`
- `appcore/storage/models.py`
- `appcore/storage/crud.py`
- `appcore/contracts/schemas.py`
- `workflows/*`
- `executor/host.py`

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
  Dockerfile
  vite.config.ts
  tailwind.config.js
  vitest.config.ts
  README.md
legacy_ui/
  app.py
  views/
  api.py
  navigation.py
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
    test_canonical_imports.py
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
- New UI feature page or route: `ui/src/features/`
- New shared UI primitive: `ui/src/components/ui/`
- New UI data adapter or HTTP client logic: `ui/src/lib/`
