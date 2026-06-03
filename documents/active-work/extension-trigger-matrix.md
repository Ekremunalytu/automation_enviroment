# `extension-trigger-matrix` Branch — Work Tracker

The branch carries three workstreams, all implemented and not yet merged; the
canonical UI lane (`documents/agent-lanes/ui.md`), the executor-runtime lane
(`documents/agent-lanes/executor-runtime.md`), the static-analysis lane
(`documents/agent-lanes/static-analysis-pre-check.md`), and `REFACTOR_STATUS.md`
are reconciled at merge/close-out:

1. **Rule Trigger Matrix (Reports UI)** — a UI-led feature with one additive
   backend contract touch (documented immediately below).
2. **Activation Coverage Promotion (executor + planner)** — makes the harness
   actually exercise ambient-only extensions; live-validated against an
   `ms-python.python` scan. See
   [Activation Coverage Promotion](#activation-coverage-promotion-executor--planner).
3. **Static Rule Expansion + Blacklist Domains** — strengthens the static
   pre-check rule set (`s4`–`s7` + 4 new Semgrep rules), adds the dynamic `a7`
   blacklist rule, and an operator-editable `blacklist_domains` field (DB-backed,
   surfaced in a new Rules → Blacklist tab). See
   [Static Rule Expansion + Blacklist Domains](#static-rule-expansion--blacklist-domains).

**Related:** ADR 0016 (static analysis pre-check stage — produces the static
report folded in here), ADR 0003 (detection taxonomy), `agent-lanes/ui.md`,
`agent-lanes/executor-runtime.md`.

## Rule Trigger Matrix (Reports UI)

**Status:** Implemented on branch `extension-trigger-matrix` (2026-06-01).
UI-led feature with one additive backend contract touch.

### Goal

A MITRE ATT&CK-Navigator-style **matrix of detection rules** on the Reports
screen, in a new **Rule matrix** tab, showing both **static** (pre-check:
`s1`–`s7` + external Semgrep) and **dynamic** (behavioral: `a1`–`a4`/`a6`/`a7`)
rules — making it obvious which rules **fired** vs **stayed silent**
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
  universe isn't enumerable); the in-house `s1`–`s7` universe is fully shown.
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

## Static Rule Expansion + Blacklist Domains

**Status:** Implemented on branch `extension-trigger-matrix` (2026-06-02). Two
parts: (a) a comprehensive expansion of the static pre-check rule set + a new
dynamic blacklist rule; (b) an operator-editable `blacklist_domains` field
surfaced in a new **Rules → Blacklist** tab. Not yet merged. Touches the
static-analysis lane (`agent-lanes/static-analysis-pre-check.md`) — the ES-3a/ES-4
"6 in-house + 4 Semgrep" counts in `static-analysis-pre-check-stream.md` describe
those frozen increments; this is a **post-ES-5 expansion**.

### Rule expansion (additive — existing gate/report contracts unchanged)

In-house static rules grew 6 → 10 (`static_runtime/rules/`, registered in
`_BUILTIN_STATIC_RULE_MODULES`):

- `extrace.s4.blacklisted_domain` (HIGH) — source/manifest references a domain on
  the operator denylist. **Static leg of the blacklist feature.**
- `extrace.s5.suspicious_network_endpoint` (MEDIUM) — routable IPv4 literal /
  cleartext `http://` external host.
- `extrace.s6.obfuscation_indicators` (MEDIUM) — decode-then-execute,
  `String.fromCharCode` chains, oversized base64 blobs, dense `\xNN` runs.
- `extrace.s7.hardcoded_secret` (MEDIUM) — AWS / GitHub / Slack / PEM / bearer
  secret shapes; the raw secret is never quoted into evidence.

Semgrep JS/TS rules grew 4 → 8 (`static_runtime/semgrep_rules/extrace-vsix-js.yml`
plus `_RULE_META`): `outbound_net_module`, `dynamic_require`,
`base64_decode_exec`, `sensitive_file_read`.

Dynamic rule `extrace.a7.blacklisted_domain` (HIGH, `AdversaryClass.A7`) checks
each observed outbound `event.host` against the denylist.

All new findings reuse the existing `StaticDetectionFinding` / `DetectionFinding`
contracts — no schema bump. `s4` is HIGH but NOT in `_PROMOTED_HIGH_BLOCKERS`, so
it **WARNs** (the dynamic stage still runs); the gate code is unchanged.

### Shared denylist + matcher

`packages/analysis_contracts/domain_indicators.py` (stdlib-only, in-image for both
the dynamic engine and the hardened static container, mirroring
`typosquat_match.py`) + the curated seed `data/blacklist_domains.txt`. Host-suffix
matching, registrable-boundary safe (`notevil.example` / `evil.example.org` do not
match `evil.example`). Effective denylist = seed ∪ in-process operator override;
the static container never sets the override → seed-only, DB-free.

### Editable `blacklist_domains` field (DB-backed, live to `a7`)

- DB: `blacklist_domains` table (`appcore/storage/model_defs/blacklist_domain.py`)
  plus Alembic migration `b3d9f1c2e7a4` (head). Operator additions only;
  effective = seed ∪ DB rows.
- Service: `workflows/detection_rules/blacklist_service.py` — domain validation,
  seed-union, `refresh_operator_override` (calls
  `domain_indicators.set_operator_blacklist`).
- Live wiring: `main.py:prime_blacklist_override` loads operator rows at startup
  (best-effort — swallows a missing DB); every write refreshes the override. The
  analysis worker is a thread in the same `automation_api` process
  (`API_WORKERS=1`), so `a7` sees edits on the next analysis with no restart.
  Static `s4` picks up the same list once the currently-dormant static stage is
  wired into the live pipeline; the matcher is override-ready.
- API: `appcore/api/rules_router.py` — `GET` (seed/operator/effective) · `POST`
  (add, 422 on invalid) · `DELETE /{domain}` (operator-only, 404). Outside any
  report contract; read-only of the bundle.
- UI: new **Blacklist** tab in `ui/src/features/rules/RulesPage.tsx` — a Domain ·
  Source · Action table (add input, removable `operator` rows, `fixed` seed rows),
  names the matched domains when a blacklist rule fired in the latest report.
  `ui/src/lib/api/client.ts` add/remove methods; `features/reports/ruleCatalog.ts`
  entries for `s4`–`s7` + `a7` (matrix labels).

### Tests

- `tests/static_runtime/test_{s4_blacklisted_domain,s5_network_indicators,
  s6_obfuscation_indicators,s7_secret_exposure}.py` — fire/silent per rule.
- `tests/static_runtime/test_rule_coverage.py` — exact static production rule-id
  set + PRODUCTION-lifecycle guard.
- `tests/platform/contracts/test_{domain_indicators,secret_detection}.py` —
  host-suffix/boundary matching + operator override + secret detectors.
- `tests/security/rules/test_a7_blacklisted_domain.py` — dynamic fire/silent.
- `tests/security/test_semgrep_js_rules.py` +
  `tests/static_runtime/test_semgrep_runner.py` — the 8-rule set + the mapper.
- `tests/workflows/detection_rules/test_blacklist_service.py` +
  `tests/platform/api/test_rules_router.py` — validation (no-DB) +
  add/list/remove/effective + endpoint GET/POST/DELETE/422/404 (`requires_db`;
  live-validated against `postgres_test`).
- `ui/src/features/rules/RulesPage.test.tsx` — tab, table render, add/remove,
  matched-domain naming.

### Verify

1. `make test-security` · `make test-local` (the `requires_db` blacklist tests) ·
   `make check-all` (ruff/mypy/bandit/ui-types-check/vitest).
2. `alembic upgrade` on the dev/prod DB (the new table); the `make test-local`
   lane is `create_all`-managed so it needs no migration.
3. `docker compose build api && up -d api` (api bakes `main.py` + routers);
   browser-verify via the vite UI preview (`/api`→:8000) on `/rules?tab=blacklist`:
   add a domain → it appears as an `operator` row with Remove and applies to the
   next analysis's `a7` rule.
