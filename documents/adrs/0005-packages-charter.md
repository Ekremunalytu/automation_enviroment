# ADR 0005: Packages Charter

- Status: Accepted
- Date: 2026-04-17
- Related: ADR 0001 (Single-Host Appliance), ADR 0002 (Threat Model), ADR 0003 (Detection Taxonomy)

## Context

The refactor introduced `packages/` as the framework-agnostic home for
contracts, planning logic, and analysis logic that must survive API, UI, and
executor churn. Without a written charter, that boundary degrades into a
"shared utils" bucket and Week 5 detection code will start depending on runtime
layers it is supposed to stay independent from.

## Decision

### 1. Allowed Dependency Direction

Code under `packages/` may depend on:

- Python standard library
- other modules inside `packages/`
- third-party libraries already approved for the repo

Code under `packages/` may **not** import from:

- `appcore/`
- `workflows/`
- `executor/`
- `ui/`

### 2. Public API Rule

Every package exposes its supported surface through its package root
(`__init__.py`). Internal modules remain importable only inside the same
package unless the root explicitly re-exports them.

### 3. Framework-Agnostic Rule

`packages/` owns contracts and logic, not framework wiring.

- No FastAPI request/response types
- No SQLAlchemy sessions or ORM models
- No Docker control helpers
- No React/UI-specific view models

Adapters live outside `packages/` and translate framework/runtime data into
package-owned contracts.

### 4. Detection Rule Placement

Week 5+ detection rules live under detection-oriented package modules and
consume only contract-level inputs. They do not read the database directly,
call HTTP APIs, or invoke executor helpers.

### 5. App Skeleton Decision

The current repo keeps runtime orchestration in `workflows/`, platform code in
`appcore/`, executor mechanics in `executor/`, and reusable logic in
`packages/`. Historical `apps/` placeholder directories may still exist as
documentation-only stubs, but they are not canonical runtime surfaces.

## Consequences

- Import-graph tests enforce the boundary repo-wide.
- Shared logic moves into `packages/` only when it can stay framework-agnostic.
- Detection work can build on a stable contract layer without inheriting API or
  storage coupling.
