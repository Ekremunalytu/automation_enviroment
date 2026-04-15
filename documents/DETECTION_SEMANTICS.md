# Detection Semantics

`Last Updated: 2026-04-15`

This document defines the meaning of the current exported report contract.
Its purpose is to keep report generation, API responses, UI adapters, and
analyst interpretation aligned.

Open this only when changing report JSON fields, UI report adapters, health or
verdict logic, or exported evidence semantics.

## Raw Evidence Sources

The current report is built from five evidence layers:

- activation evidence
  - parsed from Extension Host logs, output-channel text, and running-extension
    snapshots
- file evidence
  - captured from filesystem monitors and annotated against activation windows
- network evidence
  - captured from network monitors and annotated against activation windows
- trigger and execution ledger data
  - selected scenarios, stimulus passes, event attempts, prerequisites, and
    extra-trigger outcomes
- runtime quality signals
  - trigger-plan load/apply state, log presence, UI blockers, scenario failures,
    and verification gaps

These layers are assembled primarily in:

- `executor/flows/playwright/monitor.py`
- `executor/flows/playwright/health.py`
- `executor/flows/playwright/signals.py`
- `executor/flows/playwright/report_builder.py`

## Core Contract Fields

### `report_version`

- Meaning:
  - Contract version for the exported JSON report.
- Current behavior:
  - defaults to `2` in `report_builder.py`.
- Analyst interpretation:
  - Treat contract changes as additive unless explicitly documented otherwise.

### `target_extension_expected`

- Meaning:
  - The `publisher.name` identifier of the extension under analysis.
- Raw source:
  - analysis request and trigger payload target metadata.
- Calculation:
  - copied from the target identifier passed into the executor.
- Analyst interpretation:
  - This is the ownership anchor. If it is empty, attribution confidence is
    fundamentally reduced.

### `target_extension_observed`

- Meaning:
  - Whether the target extension was actually seen during the run.
- Raw source:
  - activation entries, running-extension snapshots, and strongly attributed
    file/network events.
- Calculation:
  - `true` when the target appears in any of those sources.
- Analyst interpretation:
  - `false` means the run must not be treated as a clean clearance.

### `trigger_plan_requested`

- Meaning:
  - Whether the analysis run expected a trigger payload.
- Raw source:
  - marketplace trigger planning.
- Analyst interpretation:
  - This distinguishes "no trigger plan was needed" from "a trigger plan was
    requested but failed."

### `trigger_plan_loaded`

- Meaning:
  - Whether the executor successfully loaded the trigger payload file.
- Raw source:
  - container-side trigger loader.
- Analyst interpretation:
  - `false` on a requested trigger plan is a hard reliability degradation.

### `trigger_plan_applied`

- Meaning:
  - Whether the run successfully applied the trigger plan.
- Raw source:
  - executor runtime and report assembly.
- Calculation:
  - `true` when the requested plan was applied.
  - also treated as effectively `true` when no trigger payload was requested.
- Analyst interpretation:
  - `false` means the planned activation surface was not exercised as intended.

### `automation_health`

- Meaning:
  - High-level operational truthfulness summary for the run.
- Important fields:
  - `status`
  - `reasons`
  - `trigger_requested`
  - `trigger_loaded`
  - `trigger_applied`
  - `extension_host_log_present`
  - `extension_host_output_present`
  - `target_stream_present`
  - `target_activation_count`
  - `failed_scenarios`
- Status meanings:
  - `healthy`
    - target was observed, trigger plan is complete when requested, logs are
      present, and no major degraders remain
  - `degraded`
    - the run completed, but logs, UI flow, or verification quality are partial
  - `inconclusive`
    - target context or target observation is missing, or the trigger plan was
      incomplete when required
- Analyst interpretation:
  - Read this before reading the verdict.

### `log_health`

- Meaning:
  - Narrow summary of log presence and target log visibility.
- Important fields:
  - `extension_host_log_found`
  - `extension_host_log_present`
  - `extension_host_output_present`
  - `target_extension_log_entries`
  - `total_activation_entries`
- Analyst interpretation:
  - Use this to distinguish "the run was quiet" from "the logging surface
    itself was weak."

### `attempted_capabilities` and `verified_capabilities`

- Meaning:
  - Runtime capability truth derived from executed event attempts.
- Raw source:
  - `event_attempts` with populated `attempted_passes`, supported
    `capability_tags`, and final statuses.
- Calculation:
  - `attempted_capabilities`
    - includes supported capabilities from official event attempts whose status
      is `verified`, `attempted_only`, or `failed`
  - `verified_capabilities`
    - includes supported capabilities from official event attempts whose status
      is `verified`
- Analyst interpretation:
  - These fields answer "what did the executor actually try and verify during
    this run?"
  - They no longer mirror the full static trigger payload. For planned breadth,
    read `coverage_tracks`, `coverage_matrix`, and `coverage_summary`.

### `verification_gap`

- Meaning:
  - Gap between officially attempted capabilities and officially verified
    capabilities.
- Raw source:
  - runtime event-attempt reconciliation in `monitor.py` and health grading in
    `health.py`.
- Calculation:
  - `max(len(official_attempted_capabilities) - len(official_verified_capabilities), 0)`
- Analyst interpretation:
  - Higher values mean more of the runtime-attempted activation surface failed
    to produce a verified target reaction.

### `heuristic_verification_gap`

- Meaning:
  - Gap between heuristically attempted and heuristically verified capabilities.
- Analyst interpretation:
  - This is useful context, but the official gap carries more weight when
    judging runtime coverage of declared activation events.

### `run_quality`

- Meaning:
  - Overall reliability grade used for analyst interpretation.
- Allowed values:
  - `high`
  - `medium`
  - `low`
  - `inconclusive`
- Calculation:
  - derived from `automation_health.status`, trigger-plan completeness,
    scenario/log degraders, and unresolved official coverage
- Analyst interpretation:
  - `high`: report can support stronger conclusions
  - `medium`: usable, but read with caution
  - `low`: suspicious output may matter, but verification strength is limited
  - `inconclusive`: do not treat a quiet run as proof of safety

## Coverage and Execution Ledger Fields

### `official_event_coverage`

- Meaning:
  - Summary of coverage driven by declared activation events.
- Important fields:
  - `declared`
  - `verified`
  - `attempted_only`
  - `failed`
  - `blocked`
  - `unresolved`
  - `declared_events`
- Analyst interpretation:
  - This is the best summary of how well the declared activation contract was
    exercised.

### `heuristic_workflow_coverage`

- Meaning:
  - Summary of workflow coverage inferred from contributes metadata and broader
    scenario planning.
- Analyst interpretation:
  - Useful for breadth, but weaker than the official activation track for
    hard verification claims.

### `coverage_tracks`

- Meaning:
  - Full per-track structure for `official` and `heuristic` coverage.
- Track fields:
  - `source`
  - `selected_scenarios`
  - `summary`
  - `matrix`
- Analyst interpretation:
  - Use this when you need to explain why one capability is marked attempted,
    verified, or unresolved in the plan, even if the runtime top-level
    capability fields are narrower.

### `event_attempts`

- Meaning:
  - Per-event execution ledger for target activation attempts.
- Important fields:
  - `activation_event`
  - `track`
  - `selected_by`
  - `capability_tags`
  - `status`
  - `verification_status`
  - `trigger_method_used`
  - `failure_reason_code`
  - `blocked_reason_code`
  - `result_details`
- Analyst interpretation:
  - This is the lowest-friction explanation for "what did the executor actually
    try for this declared event?"

### `stimulus_passes`

- Meaning:
  - Timing and status for each layered execution pass.
- Current pass family:
  - workspace/bootstrap
  - UI-first user session
  - target-specific activation
  - unresolved-event backfill
  - post-run verification
- Analyst interpretation:
  - Use this to understand where the run spent time and where a failure
    happened.

### `prerequisite_results`

- Meaning:
  - Materialization state for prerequisites such as task configs, debug launch
    configs, bait files, and harness context.
- Analyst interpretation:
  - Helpful when a scenario failed because the workspace could not be prepared
    correctly.

## Attribution Fields

### Per-event attribution fields

These fields remain the basis for ownership and downstream risk scoring.

#### `attribution_status`

- Allowed values:
  - `target_attributed`
  - `near_target_activation`
  - `competing_candidate`
  - `unattributed`
  - `automation_noise`
  - `corroboration`
- Analyst interpretation:
  - Only `target_attributed` is strong ownership.
  - `near_target_activation` is correlative, not definitive.

#### `attribution_basis`

- Meaning:
  - Human-readable explanation for why the event received that attribution.
- Analyst interpretation:
  - Inspect this first when an event looks suspicious but ownership is unclear.

#### `attribution_confidence`

- Meaning:
  - Normalized confidence score from `0.0` to `1.0`.
- Interpretation bands:
  - `>= 0.80`: strong attribution
  - `0.50 - 0.79`: moderate attribution
  - `< 0.50`: weak or correlative attribution

#### `is_target_extension_event`

- Meaning:
  - Convenience boolean for strong target attribution.
- Analyst interpretation:
  - Fast filter only; do not use it as a substitute for reading the basis and
    confidence fields.

### `attribution_summary`

- Meaning:
  - Aggregate ownership summary for the run.
- Important fields:
  - `target_activation_count`
  - `strong_target_file_event_count`
  - `strong_target_network_event_count`
  - `correlated_only_event_count`
  - `background_activation_count`
  - `competing_candidate_count`
  - `ui_blocker_count`
- Analyst interpretation:
  - This tells you whether the report rests on strong target ownership or
    mostly on timing correlation.

## Risk Output

### `risk_signals[]`

- Meaning:
  - Explicit suspicious-behavior findings linked to evidence ids.
- Required fields:
  - `signal_id`
  - `category`
  - `severity`
  - `confidence`
  - `evidence_event_ids`
  - `summary`

#### Current categories

- `background_sensitive_file_access`
- `background_outbound_network`
- `credential_or_secret_access`
- `multiple_sensitive_artifacts`
- `sensitive_file_and_network_combo`
- `correlative_suspicious_activity`
- `ui_blocker_verification_gap`

#### Confidence guidance

- high confidence
  - strong target attribution plus matching behavior pattern
- medium confidence
  - strong suspicious pattern with degraded verification quality
- low confidence
  - correlative or weak ownership

### `risk_summary`

- Meaning:
  - Aggregate counts derived from `risk_signals[]`.
- Fields:
  - `total_signals`
  - `critical`
  - `high`
  - `medium`
  - `low`
  - `categories`
- Analyst interpretation:
  - Triage shortcut only; not the final decision.

## Verdict Semantics

### `verdict.level`

- Allowed values:
  - `benign`
  - `needs_review`
  - `suspicious`
  - `likely_malicious`
- Current guardrails:
  - `benign` is not appropriate when the target was not observed
  - `benign` is not appropriate when the run is inconclusive
  - `likely_malicious` requires strong attribution
  - correlative suspicious activity can elevate to `needs_review` or
    `suspicious`, but not `likely_malicious`

### `verdict.score`

- Meaning:
  - Heuristic score currently normalized into the `8-96` range.
- Main inputs:
  - background activation context
  - sensitive target file access
  - strong target network activity
  - combined file and network behavior
  - degraded verification quality

### `verdict.reasons`

- Meaning:
  - Short analyst-facing explanations for the score and label.
- Analyst interpretation:
  - This is the bridge between raw evidence and the top-level decision.

## Analyst Reading Order

When reviewing a report, use this order:

1. `target_extension_expected`
2. `target_extension_observed`
3. `automation_health`
4. `run_quality`
5. `official_event_coverage`
6. `heuristic_workflow_coverage`
7. `attribution_summary`
8. `risk_signals`
9. `verdict`
10. raw evidence, logs, and attempt ledgers

This order prevents two recurring mistakes:

- treating a quiet but inconclusive run as benign
- over-trusting heuristic or correlative coverage as hard target verification
