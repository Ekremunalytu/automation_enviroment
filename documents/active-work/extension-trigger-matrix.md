# `extension-trigger-matrix` Branch — Work Tracker

The branch carries two workstreams, both implemented and not yet merged; the
canonical UI lane (`documents/agent-lanes/ui.md`), the executor-runtime lane
(`documents/agent-lanes/executor-runtime.md`), and `REFACTOR_STATUS.md` are
reconciled at merge/close-out:

1. **Rule Trigger Matrix (Reports UI)** — a UI-led feature with one additive
   backend contract touch (documented immediately below).
2. **Activation Coverage Promotion (executor + planner)** — makes the harness
   actually exercise ambient-only extensions; live-validated against an
   `ms-python.python` scan. See
   [Activation Coverage Promotion](#activation-coverage-promotion-executor--planner).

**Related:** ADR 0016 (static analysis pre-check stage — produces the static
report folded in here), ADR 0003 (detection taxonomy), `agent-lanes/ui.md`,
`agent-lanes/executor-runtime.md`.

## Rule Trigger Matrix (Reports UI)

**Status:** Implemented on branch `extension-trigger-matrix` (2026-06-01).
UI-led feature with one additive backend contract touch.

### Goal

A MITRE ATT&CK-Navigator-style **matrix of detection rules** on the Reports
screen, in a new **Rule matrix** tab, showing both **static** (pre-check:
`s1`/`s2`/`s3` + external Semgrep) and **dynamic** (behavioral: `a1`/`a2`/`a3`/
`a4`/`a6`) rules — making it obvious which rules **fired** vs **stayed silent**
(also `error` / `not run`). Clicking a cell opens a small detail dialog (rule id,
version, lifecycle, MITRE technique chips, severity, finding text + evidence,
mitigation). Theme matches the existing v3 dark design system.

### Data availability (why a small backend touch)

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

### Backend (additive — existing `AnalysisBundle` consumers unaffected)

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

### Frontend (`ui/`)

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

### Tests

- `tests/workflows/activation_reports/test_bundle_static_sibling.py` — sibling
  attach / absent-null / ambiguous-null / unreadable-null.
- `ui/src/features/reports/buildRuleMatrix.test.ts` — fired/silent/error mapping,
  static-by-exclusion, external-tool surfacing, catalog drift guard.
- `ui/src/features/reports/RuleMatrixSection.test.tsx` — both bands render, cell→dialog,
  no-static empty state.
- `ui/src/lib/adapters/report.test.ts` — `adaptBundle` folds `static_report` (and null).

### Verify

1. `make ui-types-check` (additive diff only) · ruff/mypy · `cd ui && npm run test`.
2. `docker compose build api && docker compose up -d api` (api bakes source).
3. Browser-verify via a vite dev server (UI preview proxies `/api`→:8000):
   open `/reports?report=<file>&tab=matrix`. A report with a static sibling shows
   live fired/silent in both bands and a working cell dialog; a sibling-less report
   shows the static empty state with the dynamic band still rendering.

### Follow-ups / notes

- External Semgrep/YARA/Trivy rules: only *fired* ones are shown (their silent
  universe isn't enumerable); the in-house `s1`/`s2`/`s3` universe is fully shown.
- The frontend rule catalog mirrors the engine rule definitions for silent-cell
  labels; the drift-guard test flags additions/renames.

## Activation Coverage Promotion (executor + planner)

**Status:** Implemented on branch `extension-trigger-matrix`, live-validated
against an `ms-python.python` scan (`activation_report_…-85c9ced8425e.json`,
2026-06-01). Not yet merged.

### Goal

Make the harness actually *exercise* extensions that declare only ambient
activation events (`onStartupFinished` / `*`) — e.g. `ms-python.python`. Before
this work such a target produced an abandoned report (`activated: []`,
`monitoring_end: 0.0`) even though its commands visibly ran on noVNC: the
activation sat unparsed in `exthost.log`, and an early window-reload command
blacked out the renderer so the rest of the run cascade-failed with
`command_palette_unavailable`.

### Coverage mechanisms (planner)

- **Synthesize `onCommand` attempts from `contributes.commands`** —
  `_apply_contributes_metadata` (`packages/analysis_planner/selection.py`) now
  registers an `onCommand` attempt per contributed command
  (`selected_by="contributes_command"`), independent of whether the manifest
  declared an `onCommand` activation event. Modern extensions rely on implicit
  command activation and declare only ambient events, so this is what turns a
  contributes-only manifest into real invocations. Already-declared `onCommand`
  ids are skipped (no double-invocation); session-fatal commands
  (`reloadWindow` / `closeWindow` / `quit`) are excluded via
  `_is_session_fatal_command`. (Closes the `onCommand` portion of the
  `[FOLLOWUP activation-event-contributes-implicit-synthesis]` W23 capture.)
- **Passive-observation families** — `onStartupFinished` and `*` are treated as
  *passive* (observed at the target's `activate()`), not `unsupported`. Pinned
  by `test_passive_observation_families_are_not_unsupported`.

### Executor hardening (run all synthesized commands safely)

Running every contributed command (24 for ms-python) without crashing or
flooding the renderer needed four guards:

- **Fix 1a/1b — quieter baseline + filtered capture.** `start.sh` seeds
  `files.watcherExclude` for `**/.extrace-harness/**` and forces
  `window.dialogStyle: custom` so dialogs are DOM-driveable.
  `runtime_capture/_shared.py` drops `.extrace-harness` artifact paths from file
  capture (`_is_harness_artifact_path`) — the harness's own scratch dir is never
  reported as target file activity.
- **Fix 3 — `drain_followup_ui`.** After each command, a bounded Escape-back-out
  (`vscode/commands.py`) clears leftover dialogs / quick-picks so the next
  command starts from a clean palette.
- **Fix 4b/4c — inter-command maintenance** (`stimulus/maintenance.py`). For
  terminal/REPL-spawning commands it kills leftover terminals between attempts
  (`terminal.close_all_terminals`) so they do not pile up; it then probes
  renderer liveness between attempts (`automation.is_renderer_alive`) and, if
  the renderer died from cumulative load, routes into the same graceful abort as
  an in-attempt crash (no keyboard cascade into a black window).

### Finalization safety (Fix A) — activation captured even on interrupt

`mon.stop()` is the *only* place activation is parsed (exthost log +
Running-Extensions UI + exthost output). Previously it ran inside the `try`, so
an interrupt (degraded renderer, or the analysis-timeout SIGTERM) skipped it and
abandoned the report.

- `runner.main` now finalizes in a `finally` (`finalize_monitor_report` —
  idempotent + `execution_result`-tolerant).
- `entrypoint/__main__.py` installs a SIGTERM handler that re-raises
  `SystemExit(128+signum)` so an external timeout unwinds cleanly into that
  `finally` instead of hard-killing mid-parse.
- `extension_host_log_parse.py` resets the read offset to 0 when the log shrank
  below it (a window reload rotates `exthost.log` → `exthost.1.log`), so the
  post-reload activation is still parsed.

### Reload deferral (Fix B / 4a) — no early black-out cascade

`_defer_window_reload_commands` (`selection.py`) reassigns reload-class
synthesized `onCommand` attempts (e.g. `python.clearCacheAndReload`) to the
final executable pass (`unresolved_event_backfill`) and orders them last
(`_is_window_reload_command` in `attempts.py`). The window-reload teardown then
happens only after every other command has run and been observed — purely a
reorder/pass-reassignment, nothing dropped.

### Validation (live `ms-python.python` scan `85c9ced8425e`, 2026-06-01)

| metric | before (root-cause run) | after (A+B) |
|---|---|---|
| `runner_status` | `unknown` | `success` |
| `monitoring_end` | `0.0` | set |
| `target_extension_observed` | `false` | `true` |
| distinct activated extensions | 0 | 22 (incl. `ms-python.python`, pylance, debugpy, python-envs) |
| `onCommand` verified | 0 / 24 | 24 / 24 |
| `command_palette_unavailable` | 60 | 0 |
| reload command pass | `ui_first_user_session` | `unresolved_event_backfill` (last) |
| `.extrace-harness` file events | — | 0 (across 3647 file events) |

Both activation-discovery strategies (`exthost_log_parse`,
`running_extensions_ui`) reported `succeeded_with_new_activations` despite the
window reload, confirming the rotation-robust offsets. Residual
`run_quality: low` is driven by 8 inherently-ambient `attempted_only` events
(`onDebug*`, 5× `onLanguageModelTool`, `onTerminalShellIntegration`) that cannot
be driven by a UI command — the irreducible floor for ms-python
(`missing_capabilities: []`).

### Files

- Planner: `packages/analysis_planner/{selection,attempts}.py`.
- Executor: `executor/container/start.sh`;
  `executor/flows/playwright/{automation.py, vscode/commands.py,
  vscode/terminal.py, stimulus/{attempts,passes,maintenance}.py,
  runtime_capture/{_shared,extension_host_log_parse}.py,
  entrypoint/{__main__,runner,dispatch}.py}`.

### Tests

- Planner: reload-deferral + ordered-last, `_is_window_reload_command`, and the
  frozen ms-python fixture (`tests/workflows/marketplace/test_analysis_planner.py`).
- Executor: harness-artifact file filter, baseline container settings, SIGTERM
  handler, follow-up-UI drain, renderer-liveness classifier, between-attempts
  graceful abort, log-rotation offset reset, and finalize-in-`finally`
  (idempotent / `None`-tolerant / SIGTERM-style interrupt) across
  `tests/executor/test_{runtime_capture_file_filter, container_vscode_settings,
  entrypoint_signal, playwright_commands, playwright_crash_classifier,
  playwright_stimulus, playwright_dispatch, playwright_entrypoint,
  playwright_extension_host}.py`.
