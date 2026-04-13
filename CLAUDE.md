# CLAUDE.md

This repository now uses a canonical `appcore/` + `workflows/` architecture. Prefer those paths over the legacy compatibility wrappers.

## Summary

ExTrace catalogs VS Code extensions, downloads Marketplace artifacts, and runs executor-backed sandbox analysis. The main runtime surfaces are:

- FastAPI API in `main.py`
- shared platform modules in `appcore/`
- business workflows in `workflows/`
- sandbox runtime in `executor/`
- Vite + React + Tailwind UI in `ui/`

## Commands

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
```

## Canonical Paths

- `appcore/api/config.py`
- `appcore/api/deps.py`
- `appcore/db/session.py`
- `appcore/storage/models.py`
- `appcore/storage/crud.py`
- `appcore/contracts/schemas.py`
- `workflows/extension_catalog/`
- `workflows/activation_reports/`
- `workflows/marketplace/`
- `executor/container/`
- `executor/flows/playwright/`
- `ui/src/app/`
- `ui/src/features/`
- `ui/src/lib/`

## Compatibility Paths

These still exist but are transitional:

- `routers/`
- `scanner/`
- `core/`
- `database/`
- `crud/`
- `models/`
- `schemas/`

Do not add new business logic to those wrappers.

## Key Rules

- Preserve the `(publisher, name, version)` uniqueness rule.
- Use SQLAlchemy 2.0 style only.
- Use Pydantic v2 methods only.
- Route all DB writes through CRUD.
- Keep sandbox execution inside Docker.

## Tests

Test layout mirrors the refactor:

- `tests/platform/`
- `tests/workflows/`
- `tests/executor/`

Compatibility exports are verified by `tests/platform/test_compat_wrappers.py`.
