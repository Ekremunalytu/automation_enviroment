# packages/analysis_contracts

`Last Updated: 2026-04-20`

This package owns backend-defined analysis contracts that must stay usable
across API, workflow, executor, and UI boundaries.

Current surfaces:

- `contracts.py`
  - authoritative Pydantic v2 models for `ActivationReport`,
    `TriggerPayload`, and related nested record types
- `report_invariants.py`
  - invariant checks used to keep exported activation-report semantics aligned
- `detection/`
  - reserved framework-agnostic namespace for W5 `DetectionReport` DTOs and
    detection-owned helpers

Rules:

- do not import from `appcore/`, `workflows/`, `executor/`, or `ui/`
- keep public contract exports rooted at the package boundary
- keep framework wiring and persistence adapters outside this package
