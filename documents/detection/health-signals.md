# Health + Signal Summary + Risk Output

`Last Updated: 2026-04-29`

`automation_health`, `log_health`, `run_quality`, `signal_summary`, and
`risk_signals[]` semantics. Top-level contract map:
[`../DETECTION_SEMANTICS.md`](../DETECTION_SEMANTICS.md).

## `automation_health`

High-level operational truthfulness summary for the run.

Fields: `status`, `reasons`, `trigger_requested`, `trigger_loaded`,
`trigger_applied`, `extension_host_log_present`,
`extension_host_output_present`, `target_stream_present`,
`target_activation_count`, `failed_scenarios`.

### `automation_health.status`

- **`healthy`** — target observed, trigger plan complete when
  requested, logs present, no major degraders.
- **`degraded`** — run completed, but logs, UI flow, or verification
  quality are partial.
- **`inconclusive`** — target context or target observation missing,
  or trigger plan incomplete when required.

Notable degrader: unresolved official `onChatParticipant` /
`onLanguageModelTool` attempts keep the run out of `healthy` even when
the rest of the runtime looks complete.

**Read `automation_health` before reading `signal_summary`.**

## `log_health`

Narrow summary of log presence + target log visibility. Fields:
`extension_host_log_found`, `extension_host_log_present`,
`extension_host_output_present`, `target_extension_log_entries`,
`total_activation_entries`. Use this to distinguish "the run was
quiet" from "the logging surface itself was weak."

## `run_quality`

Allowed values: `high`, `medium`, `low`, `inconclusive`. Derived from
`automation_health.status`, trigger-plan completeness, scenario/log
degraders, unresolved official coverage, unresolved official chat/tool
attempts.

- `high` — report can support stronger conclusions.
- `medium` — usable, but read with caution.
- `low` — suspicious output may matter, but verification strength is
  limited.
- `inconclusive` — do not treat a quiet run as proof of safety.

## `signal_summary`

> **Naming note (W7 entry, 2026-04-23):** This was formerly
> "Verdict Semantics" / `verdict`. Renamed to `signal_summary` when the
> authoritative verdict vocabulary was consolidated into
> `DetectionReport.verdict` (ADR 0003 §5). Activation-layer
> `signal_summary` is a sandbox **behavioral heuristic**, not a final
> verdict — surfaced in the dashboard separately from rule-driven
> detection verdicts.

### `signal_summary.level`

Allowed values: `benign`, `needs_review`, `suspicious`,
`likely_malicious`. Guardrails:

- `benign` is **not** appropriate when the target was not observed.
- `benign` is **not** appropriate when the run is inconclusive.
- `likely_malicious` requires strong attribution.
- Correlative suspicious activity can elevate to `needs_review` or
  `suspicious`, **never** `likely_malicious`.

### `signal_summary.score`

Heuristic score normalized into the `8-96` range. Main inputs:
background activation context, sensitive target file access, strong
target network activity, combined file+network behavior, degraded
verification quality.

### `signal_summary.reasons`

Short analyst-facing explanations for the score and label. Bridge
between raw evidence and the activation-layer behavioral heuristic —
**not** the final detection verdict.

## `risk_signals[]`

Explicit suspicious-behavior findings linked to evidence ids.

Required fields: `signal_id`, `category`, `severity`, `confidence`
(float attribution score), `confidence_tier` (`high` / `medium` /
`low`, derived from `confidence` via
`packages.analysis_contracts.quantize_confidence`; shares vocabulary
with `DetectionFinding.confidence`), `evidence_event_ids`, `summary`.

### Current categories

- `background_sensitive_file_access`
- `background_outbound_network`
- `credential_or_secret_access`
- `multiple_sensitive_artifacts`
- `sensitive_file_and_network_combo`
- `correlative_suspicious_activity`
- `ui_blocker_verification_gap`

### Confidence guidance

- **High** — strong target attribution + matching behavior pattern.
- **Medium** — strong suspicious pattern with degraded verification
  quality.
- **Low** — correlative or weak ownership.

## `risk_summary`

Aggregate counts derived from `risk_signals[]`. Fields:
`total_signals`, `critical`, `high`, `medium`, `low`, `categories`.
**Triage shortcut only**, not the final decision.
