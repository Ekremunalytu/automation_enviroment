# packages/analysis_contracts

`Last Updated: 2026-04-23`

This package owns backend-defined analysis contracts that must stay usable
across API, workflow, executor, and UI boundaries.

Current surfaces:

- `contracts.py`
  - authoritative Pydantic v2 models for `ActivationReport`,
    `TriggerPayload`, and related nested record types
- `report_invariants.py`
  - invariant checks used to keep exported activation-report semantics
    aligned, including `detection_report_invariant_issues` for
    cross-layer `event_id` resolution
- `detection/`
  - framework-agnostic `DetectionReport`, `DetectionFinding`, and
    `Confidence` types landed in W5 and shared with `RiskSignal` via
    `quantize_confidence`
- `quantize_confidence`
  - shared confidence-tier vocabulary used by `RiskSignal.confidence_tier`
    and `DetectionFinding`

Rules:

- do not import from `appcore/`, `workflows/`, `executor/`, or `ui/`
- keep public contract exports rooted at the package boundary
- keep framework wiring and persistence adapters outside this package
