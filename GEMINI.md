# GEMINI.md

## Project Overview

ExTrace is a refactored VS Code extension analysis platform with:

- `appcore/` for shared platform concerns
- `workflows/` for business workflows
- `executor/` for sandboxed VS Code automation
- `ui/` for the Streamlit dashboard

Legacy module names still exist as compatibility wrappers, but canonical development should target the new packages.

## Core Flows

- Catalog ingestion: root endpoints -> `workflows/extension_catalog/`
- Activation reports: `/api/activations` -> `workflows/activation_reports/`
- Marketplace + analysis: `/api/marketplace/*` -> `workflows/marketplace/`

## Important Constraints

- DB writes go through CRUD
- Validate with Pydantic before insert
- Preserve `(publisher, name, version)` uniqueness
- SQLAlchemy 2.0 and Pydantic v2 only
- Keep executor logic isolated in Docker

## Useful Commands

```bash
make dev
make test-local
make check-all
make exec-up
make exec-run
make ui-up
```

## Canonical Layout

```text
appcore/
workflows/
executor/
ui/
tests/
```
