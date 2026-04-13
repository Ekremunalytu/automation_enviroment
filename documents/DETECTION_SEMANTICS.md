# Detection Semantics

`Last Updated: 2026-04-13`

This document defines the meaning of the Detection MVP report fields. The goal
is to keep report generation, UI rendering, and analyst interpretation aligned.
Every field below answers four questions:

- What does this field mean?
- Which raw telemetry feeds it?
- How is it calculated?
- How should an analyst interpret it?

## Raw Evidence Sources

The Detection MVP uses three primary telemetry sources plus one runtime-quality
source:

- Activation events
  - Parsed from Extension Host logs and Running Extensions UI snapshots.
- File events
  - Captured from `strace` and `inotify`, then attributed against activation
    windows.
- Network events
  - Captured from `tshark`, then attributed against activation windows.
- Automation quality signals
  - Trigger payload application, scenario lifecycle, UI blockers, and capability
    verification outcomes.

These sources are normalized in
`executor/flows/playwright/monitor.py`.

## Core Run Fields

### `target_extension_expected`

- Meaning:
  - The `publisher.name` identifier of the extension under analysis.
- Raw source:
  - Marketplace analysis request and trigger payload target metadata.
- Calculation:
  - Copy the explicit target ID passed into the executor.
- Analyst interpretation:
  - Use this as the ownership anchor. If this is empty, attribution cannot be
    trusted.

### `target_extension_observed`

- Meaning:
  - Whether the target extension was actually seen during the run.
- Raw source:
  - Activation events, running-extensions snapshot, strongly attributed file
    events, strongly attributed network events.
- Calculation:
  - `true` if any of the following are true:
    - an activation event exists for `target_extension_expected`
    - the extension appears in the running-extensions snapshot
    - a file event has `is_target_extension_event=true`
    - a network event has `is_target_extension_event=true`
  - Otherwise `false`.
- Analyst interpretation:
  - If this is `false`, the run is not conclusive enough to clear the extension
    as benign.

### `trigger_plan_applied`

- Meaning:
  - Whether the executor successfully loaded and applied the smart trigger
    payload.
- Raw source:
  - Trigger payload load result inside the executor.
- Calculation:
  - `true` when a requested trigger payload is loaded and attached to the live
    report.
  - Also treated as effectively `true` when no trigger payload was requested.
  - `false` only when a trigger plan was expected but could not be applied.
- Analyst interpretation:
  - `false` means the run is degraded. Capability coverage and verdict confidence
    should be read conservatively.

### `verification_gap`

- Meaning:
  - The gap between attempted capability coverage and verified capability
    coverage.
- Raw source:
  - Trigger payload coverage matrix
  - Runtime target verification events
  - Derived capability verification from observed target behavior
- Calculation:
  - `max(len(attempted_capabilities) - len(verified_capabilities), 0)`
- Analyst interpretation:
  - Higher values mean more of the intended test surface failed to produce a
    confirmed target reaction.

### `run_quality`

- Meaning:
  - The overall reliability of the run as evidence for this target extension.
- Raw source:
  - Target observation state
  - Trigger plan application
  - UI blocker presence
  - Verification gap
- Calculation:
  - `inconclusive`
    - target extension context is missing, or
    - target extension was not observed
  - `low`
    - trigger plan was requested but not applied, or
    - verification gap is high
  - `medium`
    - target observed, but UI blockers or partial verification remain
  - `high`
    - target observed, no major quality degraders, low verification gap
- Analyst interpretation:
  - `high`: report can support a stronger decision
  - `medium`: usable, but read risk signals with some caution
  - `low`: suspicious behavior can still matter, but confidence is reduced
  - `inconclusive`: do not treat a clean-looking run as proof of safety

## Attribution Fields

### Per-event attribution fields

These fields already exist on file and network events and remain the basis for
all higher-level detection output.

#### `attribution_status`

- Meaning:
  - The ownership category assigned to the event.
- Current categories:
  - `target_attributed`
  - `near_target_activation`
  - `competing_candidate`
  - `unattributed`
  - `automation_noise`
  - `corroboration`
- Analyst interpretation:
  - Only `target_attributed` should be treated as strong ownership.
  - `near_target_activation` is correlative, not definitive.

#### `attribution_basis`

- Meaning:
  - The human-readable explanation for the attribution result.
- Raw source:
  - Attribution rule that matched during event annotation.
- Analyst interpretation:
  - This is the first field to inspect when an event looks suspicious but
    ownership is unclear.

#### `attribution_confidence`

- Meaning:
  - Confidence score for the event-level attribution, normalized to `0.0-1.0`.
- Raw source:
  - Temporal distance from target activation
  - Presence of competing activation
  - Observer type such as `strace` vs `network`
- Interpretation bands:
  - `>= 0.80`: strong attribution
  - `0.50 - 0.79`: moderate attribution
  - `< 0.50`: correlative or weak attribution

#### `is_target_extension_event`

- Meaning:
  - Convenience boolean indicating whether the event is considered owned by the
    target extension.
- Calculation:
  - `true` only for strong target attribution.
- Analyst interpretation:
  - Treat this as a fast ownership filter, not as a replacement for reading the
    basis/confidence fields.

### `attribution_summary`

- Meaning:
  - Aggregate ownership quality for the whole run.
- Raw source:
  - Annotated activation, file, and network events.
- Fields:
  - `target_activation_count`
  - `strong_target_file_event_count`
  - `strong_target_network_event_count`
  - `correlated_only_event_count`
  - `background_activation_count`
  - `competing_candidate_count`
  - `ui_blocker_count`
- Calculation rules:
  - `target_activation_count`
    - count of activation entries whose `extension_id` equals
      `target_extension_expected`
  - `strong_target_file_event_count`
    - count of file events with `attribution_status=target_attributed`
  - `strong_target_network_event_count`
    - count of network events with `attribution_status=target_attributed`
  - `correlated_only_event_count`
    - count of file and network events with
      `attribution_status in {near_target_activation, competing_candidate}`
  - `background_activation_count`
    - count of target activation events on startup/background paths such as
      `*`, `onStartupFinished`, `workspaceContains`, `onView:*` explorer/search/output,
      and `onLanguage*`
  - `competing_candidate_count`
    - count of file and network events explicitly marked as
      `competing_candidate`
- Analyst interpretation:
  - This summary tells you whether the report is built on strong target
    ownership or mostly on temporal correlation.

## Risk Output

### `risk_signals[]`

- Meaning:
  - Explicit, evidence-linked suspicious behaviors derived from normalized
    telemetry.
- Raw source:
  - Background activations
  - Sensitive file events
  - Strongly attributed network events
  - Correlative suspicious events
  - UI blocker events
- Required fields:
  - `signal_id`
  - `category`
  - `severity`
  - `confidence`
  - `evidence_event_ids`
  - `summary`

#### Current v1 categories

- `background_sensitive_file_access`
  - Target extension touched sensitive files after startup/background activation.
- `background_outbound_network`
  - Strong target network activity followed startup/background activation.
- `credential_or_secret_access`
  - Strongly attributed access to `.env`, credential, or secret-bearing paths.
- `multiple_sensitive_artifacts`
  - More than one distinct sensitive artifact was touched with strong
    attribution.
- `sensitive_file_and_network_combo`
  - Sensitive file access and outbound network both strongly belong to the
    target extension.
- `correlative_suspicious_activity`
  - Suspicious behavior exists, but only correlative attribution is available.
- `ui_blocker_verification_gap`
  - UI blockers reduced verification certainty during the run.

#### Signal confidence guidance

- High confidence:
  - Strong target attribution plus matching behavior pattern
- Medium confidence:
  - Strong suspicious pattern but partial runtime quality degradation
- Low confidence:
  - Correlative or weakly owned behavior

- Analyst interpretation:
  - `risk_signals` should answer “why is this run suspicious?” without requiring
    the analyst to scan the full raw timeline first.

### `risk_summary`

- Meaning:
  - Small aggregate view of the `risk_signals` collection.
- Raw source:
  - Derived directly from `risk_signals[]`.
- Fields:
  - `total_signals`
  - `critical`
  - `high`
  - `medium`
  - `low`
  - `categories`
- Calculation:
  - Count signals by severity and collect their categories.
- Analyst interpretation:
  - This is a triage shortcut, not the final decision.

## Verdict Semantics

### `verdict.level`

- Allowed values:
  - `benign`
  - `needs_review`
  - `suspicious`
  - `likely_malicious`
- Rules:
  - `benign` is not allowed when:
    - `target_extension_observed=false`, or
    - `run_quality=inconclusive`
  - `likely_malicious` requires strong attribution.
  - Correlative-only suspicious activity may elevate to `needs_review` or
    `suspicious`, but not `likely_malicious`.
- Analyst interpretation:
  - `benign` means “no strongly attributed high-risk behavior was observed in a
    sufficiently reliable run,” not “this extension is proven safe.”

### `verdict.score`

- Meaning:
  - Heuristic risk score in the `8-96` range.
- Raw source:
  - Sensitive file access
  - Strong target network activity
  - Background activation context
  - Multi-artifact access
  - Combined file+network pattern
  - UI blocker and quality degradation
- Analyst interpretation:
  - Compare this score only with the verdict reasons and risk signals. It should
    not be used alone.

### `verdict.reasons`

- Meaning:
  - Short, analyst-facing explanations for why the score and level were chosen.
- Raw source:
  - Matching verdict rules.
- Analyst interpretation:
  - This is the summary bridge between raw evidence and the final label.

## Analyst Reading Order

When reviewing a report, use this order:

1. `target_extension_expected`
2. `target_extension_observed`
3. `run_quality`
4. `attribution_summary`
5. `risk_signals`
6. `verdict`
7. raw evidence timeline and links

This order prevents two common mistakes:

- treating a clean-looking but inconclusive run as benign
- over-trusting correlative suspicious telemetry as strong ownership
