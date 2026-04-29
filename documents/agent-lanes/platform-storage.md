# Platform And Storage Lane

`Last Updated: 2026-04-29`

Use this lane for FastAPI app wiring, settings, dependencies, shared contracts,
SQLAlchemy models, CRUD, and migrations.

## Start Here

- `main.py`
- `appcore/api/config.py`
- `appcore/api/deps.py`
- `appcore/db/session.py`
- `appcore/contracts/`
- `appcore/storage/crud.py`
- `appcore/storage/crud_ops/`
- `tests/platform/`

## Invariants

- Preserve `(publisher, name, version)` uniqueness.
- Route writes through `appcore/storage/crud.py`.
- Validate with Pydantic v2 before DB insertion.
- Use SQLAlchemy 2.0 syntax only.
- Add Alembic migrations for schema changes.
- Keep settings claims aligned with code. ADR 0007 is Accepted, but loopback
  binding is not implemented until W8-7 lands.

## Tests And Checks

- `.venv/bin/pytest tests/platform/`
- `.venv/bin/pytest tests/workflows/extension_catalog/`
- `make migrate` when migrations change.
- `make check-all` before broad platform changes are considered complete.

## Open Subsystem Doc Only If Needed

- `ARCHITECTURE.md` (slim) → `architecture/data-flow.md` for the
  request flow you touch; `architecture/boundary-rules.md` for
  dependency-direction rules.
- `PROJECT_STRUCTURE.md` (slim) → `structure/legacy-do-not-recreate.md`
  if you suspect a forbidden top-level directory is being reintroduced.
- `TESTING.md` (slim) → `testing/platform-tests.md` for the
  per-subdir test layout.
- `active-work/W8-security.md` only if the task is W8-1..W8-8.

## Avoid

- Raw ORM writes from workflows.
- New config defaults documented without checking `appcore/api/config.py` and
  `docker-compose.yml`.
- Reintroducing legacy top-level business directories.
