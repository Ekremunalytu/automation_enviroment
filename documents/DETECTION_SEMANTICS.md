# Detection Semantics

`Last Updated: 2026-05-28 — W22 active (closed synthetically on week22; PR week22 -> main PENDING USER APPROVAL); W21 closed and merged via PR #30 5dc18aa.`

Exported `ActivationReport` JSON contract. **Slim canonical** — field
detail split out:

- [`detection/evidence-fields.md`](detection/evidence-fields.md) — per-field
  contract: `target_*`, `trigger_plan_*`, scenarios, coverage,
  execution ledger, attribution.
- [`detection/health-signals.md`](detection/health-signals.md) —
  `automation_health`, `log_health`, capabilities, `run_quality`,
  `signal_summary`, `risk_signals[]`, `risk_summary`.
- [`detection/rule-lifecycle.md`](detection/rule-lifecycle.md) — ADR
  0003 cross-ref, rule authoring, `DetectionReport.verdict` vocabulary
  vs activation-layer `signal_summary`.

Open this only when changing report JSON fields, UI report adapters,
health, signal summary, or exported evidence semantics.

## Scope Note

`ActivationReport` is a **quality + verification** contract. The
security **detection** contract (`DetectionReport`, findings, severity,
`Verdict` rollup) is a sibling specified separately by ADR 0003 and
landed during W5/W6. This document does not govern detection output;
do not overload `ActivationReport` with finding fields.

At W7 entry the activation-layer `verdict` was renamed to
`signal_summary` so the authoritative verdict vocabulary lives solely
in `DetectionReport` (ADR 0003 §5).

## Raw Evidence Sources

The current report is built from five evidence layers:

- **activation evidence** — parsed from Extension Host logs,
  output-channel text, running-extension snapshots.
- **file evidence** — captured from filesystem monitors and annotated
  against activation windows.
- **network evidence** — captured from network monitors and annotated
  against activation windows.
- **trigger and execution ledger data** — selected scenarios, stimulus
  passes, event attempts, prerequisites, extra-trigger outcomes.
- **runtime quality signals** — trigger-plan load/apply state, log
  presence, UI blockers, scenario failures, verification gaps.

Assembled primarily in:

- `executor/flows/playwright/monitor/` (facade in `monitor/__init__.py`)
- `executor/flows/playwright/runtime_capture/`
- `executor/flows/playwright/health/`
- `executor/flows/playwright/signals/`
- `executor/flows/playwright/report_builder.py`

## Contract Field Map

| Category | Fields | Detail |
|---|---|---|
| Identity | `target_extension_expected`, `target_extension_observed`, `target_activation_count` | `evidence-fields.md` |
| Trigger plan | `trigger_plan_requested/loaded/applied`, `requested_scenarios`, `summary.scenarios_run`, `scenario_traces`, `failed_scenarios`, `skipped_scenarios` | `evidence-fields.md` |
| Operational health | `automation_health` (status, reasons, …), `log_health`, `run_quality` | `health-signals.md` |
| Capabilities | `attempted_capabilities`, `verified_capabilities`, `verification_gap`, `heuristic_verification_gap` | `evidence-fields.md` |
| Coverage | `official_event_coverage`, `heuristic_workflow_coverage`, `coverage_tracks`, `coverage_summary`, `coverage_matrix` | `evidence-fields.md` |
| Execution ledger | `event_attempts[]`, `harness_verification_unconfirmed`, `stimulus_passes`, `prerequisite_results` | `evidence-fields.md` |
| Attribution | `attribution_status`, `attribution_basis`, `attribution_confidence`, `is_target_extension_event`, `attribution_summary` | `evidence-fields.md` |
| Risk output | `risk_signals[]` (categories + confidence tiers), `risk_summary` | `health-signals.md` |
| Signal summary | `signal_summary.level/score/reasons` | `health-signals.md` |

`report_version` defaults to `2` in `report_builder.py`. Treat contract
changes as additive unless explicitly documented otherwise.

## Analyst Reading Order

When reviewing a report:

1. `target_extension_expected`
2. `target_extension_observed`
3. `automation_health`
4. `run_quality`
5. `official_event_coverage`
6. `heuristic_workflow_coverage`
7. `attribution_summary`
8. `risk_signals`
9. `signal_summary`
10. raw evidence, logs, attempt ledgers

This order prevents two recurring mistakes:

- treating a quiet but inconclusive run as benign,
- over-trusting heuristic or correlative coverage as hard target
  verification.

## See Also

- ADR 0003 detection taxonomy:
  [`adrs/0003-detection-taxonomy.md`](adrs/0003-detection-taxonomy.md).
- Verdict rollup contract: `packages/analysis_contracts/detection/`
  - `tests/platform/contracts/test_verdict_rollup.py`.
- W8-6 content-sample redaction (closed by W10-7 `2026-05-04`,
  `c1e2273`) and ADR 0003 §6 addendum:
  [`active-work/W8-security.md`](active-work/W8-security.md) item W8-6.
