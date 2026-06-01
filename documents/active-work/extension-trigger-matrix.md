# Rule Trigger Matrix — Reports UI

**Status:** Implemented on branch `extension-trigger-matrix` (2026-06-01).
UI-led feature with one additive backend contract touch. Not yet merged; the
canonical UI lane (`documents/agent-lanes/ui.md`) and `REFACTOR_STATUS.md` are
reconciled at merge/close-out.

**Related:** ADR 0016 (static analysis pre-check stage — produces the static
report folded in here), ADR 0003 (detection taxonomy), `agent-lanes/ui.md`.

## Goal

A MITRE ATT&CK-Navigator-style **matrix of detection rules** on the Reports
screen, in a new **Rule matrix** tab, showing both **static** (pre-check:
`s1`/`s2`/`s3` + external Semgrep) and **dynamic** (behavioral: `a1`/`a2`/`a3`/
`a4`/`a6`) rules — making it obvious which rules **fired** vs **stayed silent**
(also `error` / `not run`). Clicking a cell opens a small detail dialog (rule id,
version, lifecycle, MITRE technique chips, severity, finding text + evidence,
mitigation). Theme matches the existing v3 dark design system.

## Data availability (why a small backend touch)

The Reports `/bundle` route already computed the **dynamic** detection live, so
`detection.rules_executed` carries one record per registered rule with an explicit
`fired` / `silent` / `error` status — the dynamic half is fully data-driven.

The **static** half was *not* in the Reports payload: static analysis runs in a
separate flow (ADR 0016) and is persisted as standalone
`output/static_report_{job_id}.json` files (a `CombinedAnalysisBundle`), surfaced
only on the Analyze/Simulation screen. To make the static half real (not
decorative), the bundle response now folds in the sibling static report.

Linking is deterministic and filesystem-only: `create_job_snapshot` names the
activation report `activation_report_{slug}-{job_id[:12]}.json` and the static
file `static_report_{job_id}.json`, so the shared 12-hex `job_id` prefix maps one
to the other. Absent / ambiguous / unreadable siblings degrade to `null` (e.g.
direct executor runs and fixtures that never ran the static gate).

## Backend (additive — existing `AnalysisBundle` consumers unaffected)

- `appcore/contracts/schema_defs/report_bundle.py` — new `ReportBundle(AnalysisBundle)`
  adds optional `static_report: StaticAnalysisReport | None = None` (subclassing
  avoids the `analysis_bundle ↔ static_analysis_bundle` import cycle).
- `workflows/activation_reports/router.py` — `_resolve_static_sibling(name)` globs
  `static_report_{token}*.json`, loads the single match as `CombinedAnalysisBundle`,
  returns its `static_report`; the `/bundle` route returns `ReportBundle`.
- `scripts/generate_ui_contracts.py` — `ReportBundle` added to `TARGET_SCHEMAS` +
  `NAME_OVERRIDES`; `AnalysisBundle` re-added to the contract providers (it is no
  longer a route response_model, so OpenAPI inlines the subclass). `make ui-types`
  regenerates `ui/src/lib/types/contracts.ts` (`ReportBundleDto`), guarded by
  `make ui-types-check`.

## Frontend (`ui/`)

- `lib/api/client.ts` bundle methods return `ReportBundleDto`; `ActivationReportView`
  gains `staticReport`; `adaptBundle` folds `dto.static_report` via the existing
  `adaptStaticReport` (`lib/adapters/job.ts`).
- `features/reports/ruleCatalog.ts` — presentation metadata (label, threat family,
  MITRE techniques, severity, blurb) for the known rule ids, so *silent* cells render
  meaningful labels (the payload carries titles for fired rules only). Drift-guarded
  by test.
- `features/reports/buildRuleMatrix.ts` — pure transform: dynamic cells from
  `rules_executed` enriched by fired findings; static cells from the in-house catalog
  universe (fired by finding membership, silent by exclusion) plus fired external tool
  rules; per-tool coverage cells. No activation data is fabricated.
- `features/reports/RuleMatrixSection.tsx` — two-band grid (Dynamic / Static) grouped
  by threat family with a status legend; cell click opens a detail dialog (v3 `Dialog`).
  Wired as the `matrix` tab in `features/reports/ReportsPage.tsx`.

## Tests

- `tests/workflows/activation_reports/test_bundle_static_sibling.py` — sibling
  attach / absent-null / ambiguous-null / unreadable-null.
- `ui/src/features/reports/buildRuleMatrix.test.ts` — fired/silent/error mapping,
  static-by-exclusion, external-tool surfacing, catalog drift guard.
- `ui/src/features/reports/RuleMatrixSection.test.tsx` — both bands render, cell→dialog,
  no-static empty state.
- `ui/src/lib/adapters/report.test.ts` — `adaptBundle` folds `static_report` (and null).

## Verify

1. `make ui-types-check` (additive diff only) · ruff/mypy · `cd ui && npm run test`.
2. `docker compose build api && docker compose up -d api` (api bakes source).
3. Browser-verify via a vite dev server (UI preview proxies `/api`→:8000):
   open `/reports?report=<file>&tab=matrix`. A report with a static sibling shows
   live fired/silent in both bands and a working cell dialog; a sibling-less report
   shows the static empty state with the dynamic band still rendering.

## Follow-ups / notes

- External Semgrep/YARA/Trivy rules: only *fired* ones are shown (their silent
  universe isn't enumerable); the in-house `s1`/`s2`/`s3` universe is fully shown.
- The frontend rule catalog mirrors the engine rule definitions for silent-cell
  labels; the drift-guard test flags additions/renames.
