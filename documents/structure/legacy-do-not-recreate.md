# Legacy Top-Level Directories — Do Not Recreate

`Last Updated: 2026-04-29`

These directories existed in the pre-refactor codebase and were removed
during W4 stabilization. The import-graph and architecture tests reject
their reintroduction; new code must use the canonical runtime tree.

Top-level shape: [`../PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md).

## Removed Business Directories (W4 Stabilization)

- `routers/` — moved into `workflows/<name>/router.py`.
- `scanner/` — replaced by `executor/control.py` + `executor/host.py`
  - `executor/flows/playwright/`.
- `core/` — replaced by `appcore/`.
- `database/` — replaced by `appcore/db/` and `appcore/storage/`.
- `crud/` — replaced by `appcore/storage/crud.py` +
  `appcore/storage/crud_ops/`.
- `models/` — replaced by `appcore/storage/models.py`.
- `schemas/` — replaced by `appcore/contracts/schemas.py` +
  `appcore/contracts/schema_defs/`.

## Removed Dormant Placeholders (Post-W7)

- `apps/` — empty surface kept for a multi-app future that is no longer
  on the roadmap.
- `legacy_ui/` — predecessor to the current `ui/` SPA.

## Why The List Matters

The first reflex of an agent unfamiliar with the post-refactor shape is
to recreate one of these names because the old README or an old issue
mentions it. Architecture tests under `tests/architecture/` reject any
import from these paths; CI fails immediately if a new file lands at
e.g. `routers/foo.py`.

If the canonical runtime tree (`appcore/`, `packages/`, `workflows/`,
`executor/`, `ui/`, `tests/`) does not seem to contain a natural home
for new code, do **not** improvise a new top-level directory — open a
discussion under `documents/agent-lanes/docs-maintenance.md` Validation
or surface the question in the relevant lane doc.
