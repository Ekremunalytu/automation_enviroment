# Risk Radar Data Derivation

`Last Updated: 2026-06-02`

How the Reports **Risk Radar** panel (composite gauge + six-axis breakdown)
derives every value it renders. Open this when changing the radar scoring,
adding a detection category, or auditing whether the panel invents data.

Source files:

- `ui/src/lib/adapters/report.ts` — `buildRiskRadarAxes`, `buildRiskRadar`,
  `computeAxisScores`, `CATEGORY_AXIS`, `SEVERITY_WEIGHT`.
- `ui/src/components/evidence/RiskRadarPanel.tsx` — presentational only.
- `ui/src/features/reports/ReportsPage.tsx` — passes
  `axes={buildRiskRadarAxes(report)}`.

Detection category source of truth:
[`../../packages/analysis_engine/signals/policy.py`](../../packages/analysis_engine/signals/policy.py).
Top-level detection map: [`../DETECTION_SEMANTICS.md`](../DETECTION_SEMANTICS.md).

## Core Principle

**Every rendered number is derived from the real report — nothing is random
or hardcoded.** Axis scores reflect the detection engine's actual
`risk_signals`; if the engine fired nothing, the threat axes are honestly
zero. A clean / `needs_review` run with no signals shows an empty radar, not
fabricated HIGH values.

This replaced an earlier heuristic that scored axes from raw event-kind counts
(e.g. `processCount / totalSignals * 90`), which inflated to 100 on clean
reports, and decorative constants for trend / benchmark / weight.

## What Is Real vs Derived

| Element | Source |
| --- | --- |
| Composite score (gauge) | `report.summary.signalSummaryScore` — real backend field |
| Composite tier badge / counts | derived from the six axis scores (tier bands) |
| Axis score | aggregated from real `risk_signals` (severity × confidence) |
| Defense gap axis | real `coverage_summary` shortfall (+ verification-gap signals) |
| Signal count column | count of real signals mapped to the axis |
| Trend sparkline | cumulative replay of real detections over run time |
| Benchmark marker ("run average") | mean of the six real axis scores |

Total events / sensitive / network counts shown above the radar come straight
from `report.summary`.

## Axis Scoring

`computeAxisScores(signals, coverageFraction, report)` returns the 0-100 score
for each axis:

- Each signal contributes `SEVERITY_WEIGHT[severity] × confidence` to the axis
  its `category` maps to. Unknown severity falls back to `35`.
- `SEVERITY_WEIGHT`: `critical=100`, `high=75`, `medium=45`, `low=25`.
- `confidence` is the engine's per-signal value, clamped to `0..1`.
- Per-axis contributions are summed and clamped to `0..100`.
- An axis with no mapped signal stays `0`.

`buildRiskRadar` is the flat-key wrapper (kept for back-compat and tests);
`buildRiskRadarAxes` is the per-axis view model the panel consumes.

## Category → Axis Mapping

`CATEGORY_AXIS` maps each real backend signal category to one radar axis. Keep
it in sync with `policy.py`.

| Axis (label) | Backend category |
| --- | --- |
| Exfiltration | `background_outbound_network`, `sensitive_file_and_network_combo` |
| Threat surface | `credential_or_secret_access` |
| Persistence | `background_sensitive_file_access` (startup-triggered) |
| Process spawn | `correlative_suspicious_activity` |
| Filesystem scope | `multiple_sensitive_artifacts` |
| Defense gap | `ui_blocker_verification_gap` + coverage shortfall |

### Defense gap

`Defense gap` is the one axis with a non-signal component. It reflects measured
coverage shortfall independent of any fired signal:

```text
coverageGap = ((missing + 0.5 × partial) / max(covered + partial + missing, 1)) × 100
```

scaled by `coverageFraction` (used only by the trend; `1` for the final score),
plus any `ui_blocker_verification_gap` signal contributions.

## Trend, Benchmark, Signal Count

- **Trend** (6-point sparkline): each signal is placed at the `relTimeS` of its
  earliest evidence event. Bucket `i` (fraction `f = i/6`) includes signals
  whose time `≤ f × runEnd`; the coverage contribution is scaled by `f`. The
  last bucket uses `f = 1` and includes signals with no resolvable evidence
  time, so **`trend[last] === score`** always holds — the sparkline ends
  exactly at the displayed value.
- **Benchmark** (`run average`): the rounded mean of the six final axis scores.
  Identical across rows — a reference line, not a per-axis population baseline
  (no such dataset exists for a single report).
- **Signal count**: number of `risk_signals` whose category maps to the axis.
  `Defense gap` reads `0` here when its value is coverage-driven.

## Invariants

- `trend[trend.length - 1] === score` for every axis.
- An axis is non-zero only if a mapped signal fired, except `Defense gap`
  (coverage) — so zero detections ⇒ zero threat axes.
- The radar never reports a HIGH tier without a backing detection.

## Known Limitation

The engine emits seven signal categories; the radar has six axes, so the
mapping is best-fit (e.g. `Persistence` borrows the startup-triggered file
signal). A category **not** present in `CATEGORY_AXIS` contributes to no axis
and is silently dropped from the radar. When `policy.py` adds or renames a
category, update `CATEGORY_AXIS` (and consider whether the axis labels still
fit). Tests: `ui/src/lib/adapters/report.test.ts` (`buildRiskRadar`,
`buildRiskRadarAxes`).
