# Evidence + Coverage + Attribution Fields

`Last Updated: 2026-04-29`

Per-field contract for `ActivationReport`'s evidence, coverage,
execution-ledger, and attribution surfaces. Top-level contract map +
scope note: [`../DETECTION_SEMANTICS.md`](../DETECTION_SEMANTICS.md).

## Identity

### `target_extension_expected`

- The `publisher.name` identifier of the extension under analysis.
- Source: analysis request + trigger payload target metadata.
- If empty, attribution confidence is fundamentally reduced.

### `target_extension_observed`

- Whether the target was actually seen during the run.
- Source: activation entries, running-extension snapshots, strongly
  attributed file/network events.
- `true` when the target appears in any of those sources.

## Trigger Plan

### `trigger_plan_requested`

- Boolean: was a trigger plan asked for during analysis dispatch?

### `trigger_plan_loaded`

- Boolean: did the executor load the requested trigger plan?

### `trigger_plan_applied`

- Boolean: did the executor execute the loaded trigger plan during this
  run?

### `requested_scenarios` / `summary.scenarios_run` / `scenario_traces`

- `requested_scenarios` lists every scenario asked for.
- `summary.scenarios_run` lists scenarios actually executed; the
  difference must always be reflected in `failed_scenarios` or
  `skipped_scenarios` (no silent drop).
- `scenario_traces` keeps per-scenario timing and pass/fail state.

## Operational Truthfulness

### `attempted_capabilities` / `verified_capabilities`

- Runtime capability truth derived from `event_attempts`.
- `attempted_capabilities` includes supported capabilities from
  official event attempts whose status is `verified`,
  `attempted_only`, or `failed`.
- `verified_capabilities` includes supported capabilities from
  official event attempts whose status is `verified`.
- These no longer mirror the full static trigger payload; for planned
  breadth, read `coverage_tracks`, `coverage_matrix`,
  `coverage_summary`.

### `verification_gap`

- Calculation:
  `max(len(official_attempted_capabilities) - len(official_verified_capabilities), 0)`.
- Higher = more of the runtime-attempted activation surface failed to
  produce a verified target reaction.

### `heuristic_verification_gap`

- Same shape but on heuristic capabilities. Useful context, but the
  official gap carries more weight when judging runtime coverage.

## Coverage And Execution Ledger

### `official_event_coverage`

Fields: `declared`, `verified`, `attempted_only`, `failed`, `blocked`,
`unresolved`, `declared_events`. Best summary of how well the declared
activation contract was exercised.

### `heuristic_workflow_coverage`

Inferred from contributes metadata + broader scenario planning. Useful
for breadth, weaker than the official track for hard verification.

### `coverage_tracks`

Per-track structure for `official` and `heuristic`. Fields per track:
`source`, `selected_scenarios`, `summary`, `matrix`. Use this when you
need to explain why a capability is marked attempted/verified/unresolved.

### `event_attempts`

Per-event execution ledger. Fields: `activation_event`, `track`,
`selected_by`, `capability_tags`, `status`, `verification_status`,
`trigger_method_used`, `failure_reason_code`, `blocked_reason_code`,
`result_details`. Lowest-friction explanation for "what did the
executor try for this declared event?"

### `harness_verification_unconfirmed`

Appears in `event_attempts[*].failure_reason_code` for unresolved
harness flows (especially official `onChatParticipant` and
`onLanguageModelTool`). It does **not** mean the trigger was cleanly
verified; check `event_attempts`, `automation_health`, `run_quality`
together.

### `stimulus_passes`

Timing + status for each layered execution pass:

- workspace/bootstrap
- UI-first user session
- target-specific activation
- unresolved-event backfill
- post-run verification

A completed pass means the executor finished that pass stage, not that
each scenario or event attempt inside it produced a verified target
reaction.

### `prerequisite_results`

Materialization state for prerequisites: task configs, debug launch
configs, bait files, harness context. Helpful when a scenario failed
because the workspace could not be prepared correctly.

## Attribution

### Per-event attribution

- `attribution_status` — one of:
  `target_attributed`, `near_target_activation`, `competing_candidate`,
  `unattributed`, `automation_noise`, `corroboration`. Only
  `target_attributed` is strong ownership.
- `attribution_basis` — human-readable explanation. Inspect first when
  an event looks suspicious but ownership is unclear.
- `attribution_confidence` — `0.0`-`1.0`:
  `>= 0.80` strong, `0.50-0.79` moderate, `< 0.50` weak/correlative.
- `is_target_extension_event` — convenience boolean for strong target
  attribution; **fast filter only**, do not substitute for reading
  basis + confidence.

### `attribution_summary`

Aggregate ownership for the run. Fields: `target_activation_count`,
`strong_target_file_event_count`,
`strong_target_network_event_count`, `correlated_only_event_count`,
`background_activation_count`, `competing_candidate_count`,
`ui_blocker_count`. Tells you whether the report rests on strong
target ownership or mostly timing correlation.
