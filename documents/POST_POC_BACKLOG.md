# Post-PoC Backlog

`Last Updated: 2026-05-18 (W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472 — W15-1..W15-7 sub-iter slate + W15-1 post-slate typing hotfix + close-out hygiene pass; W16 active on week16 branch (per user direction 2026-05-18; W11-W15 paterni restored via W16-0 doc reconcile); W16 Pull-Forward planned: scenario-accountant-conservation-split (W16-1, W14-1 carry-over HIGH prod regression), analysis-job-worker-entry-crud-ownership (W16-2, W15 audit finding), report-finalize-top-level-field-sync-drift (W16-3, W14 carry-over), health-reconciliation-responsibility-split (W16-4, W15 audit finding), simulation-progress-cancel family 3 sub-items (W16-5, W11+ umbrella), hygiene splits + w13-4-alembic-roundtrip-programmatic (W16-6); W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d)`

Open deferred work after the W0-W7 PoC acceptance bar. **Slim canonical** —
verbose closure rationales, evidence paragraphs, and per-iter Note columns
are frozen in dated snapshots. Each closed item below is one line with
stable ID + landing commit; full context in the snapshot.

- latest full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-14.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-14.md)
- previous full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-11.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-11.md)

W8-W15 are closed; W13 close-out PR #20 `week13 -> main` **MERGED**
`2026-05-13` via `772deb3`; W14 close-out PR #21 `week14 -> main`
**MERGED** `2026-05-14` via `4e03c8d`; **W15 close-out PR #22
`week15 -> main` MERGED `2026-05-18` via `6161472`**. **W16 active**
on the `week16` branch (per user direction 2026-05-18; W11-W15 paterni
restored via W16-0 doc reconcile); W16-1..W16-7 planned (pull-forward
table below). W14 tracker:
[`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md);
W15 tracker (frozen):
[`active-work/W15-codex-uclass-bounds-posture.md`](active-work/W15-codex-uclass-bounds-posture.md);
W16 tracker (active):
[`active-work/W16-regression-and-audit-closeout.md`](active-work/W16-regression-and-audit-closeout.md).

## Stable IDs Are A Contract

Do not rename existing IDs. Current code/tests reference at least:

- `[FOLLOWUP analysis-jobs-race]`
- `[FOLLOWUP simulation-progress-cancel]`
- `[FOLLOWUP simulation-progress-cancel] cancel-after-finish race test`
- this filename from `packages/analysis_contracts/contracts.py`

Use stable IDs in new references; do not cite canonical doc line numbers.

## W13 Pull-Forward Acceptance Bar

All W13 items closed; full Note column lives in archive snapshot.

| Stable ID | Closed via |
|---|---|
| `[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]` | W13-5 |
| `[FOLLOWUP codex-2026-05-10-H4-cancel-concurrent-race]` | W13-3 |
| `[FOLLOWUP codex-2026-05-10-H5-writable-vscode-launcher]` | W13-2 |
| `[FOLLOWUP codex-2026-05-10-H6-spoofable-harness-markers]` | W13-1 |
| `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]` | W13-7 |
| `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]` | W13-6 |
| `[FOLLOWUP w13-3-close-pass-cancellation-test-hardening]` | W13-4 |
| `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` | deferred (fresh-DB-per-test fixture needed) |
| `[CLOSE-GATE codex-second-opinion-F1-hmac-python-secret-target-install-race]` | W13-11 (2026-05-12) |
| `[CLOSE-GATE codex-second-opinion-F2-fail-closed-harness-handshake]` | W13-12 (2026-05-12) |
| `[CLOSE-GATE codex-second-opinion-F3-worker-start-cancel-race-CAS]` | W13-13 (2026-05-13) |

## W14 Pull-Forward Acceptance Bar

All W14 sub-iters closed (slate + post-slate hotfixes); per-iter Per-Item
Detail evidence in the W14 tracker + archive snapshot.

| Iter | Stable ID(s) | Landing commit |
|---|---|---|
| W14-1 | `[BUG scenario-dropout-upstream-root-cause]` (BLOCKER → HIGH) | `0c8bd02` |
| W14-2 | `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` + `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` | `bde17be` |
| W14-3 | `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` + `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` + `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` | `941250d` |
| W14-4 | `[FOLLOWUP analysis-jobs-race]` + `[FOLLOWUP evidence-event-kind-raw-context-invariant]` | `03b32bc` |
| W14-5 | `[GOAL w14-logger-consolidation]` + `[GOAL w14-run-id-stamping]` + `[FOLLOWUP codex-automation-5]` + `[FOLLOWUP codex-2026-05-10-M5-epoch-docker-exec-propagation]` (byproduct) | `dc79f61` + `9c095d2` + `db25d5f` |
| W14-6 | `[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]` + `[FOLLOWUP arch-gate-executor-control-outbound]` + `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]` | `2adad43` + `b031803` + `e42a448` |
| W14-7 | `[FOLLOWUP w14-container-shipping-regression]` (post-slate hotfix) | `df925f8` + `c11ebd8` |
| W14-8 | `[FOLLOWUP w14-container-python-compat-gate]` (post-slate preventive) | `5638f82` |

## W15 Pull-Forward Acceptance Bar

All W15 sub-iters closed and merged via PR #22 on `2026-05-18` (`6161472`);
per-iter Per-Item Detail evidence in the W15 tracker + archive snapshot.

| Iter | Stable ID(s) | Landing commit |
|---|---|---|
| W15-1 | `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]` + post-slate typing hotfix | `c58c365` + `976dc96` |
| W15-2 | `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]` | `765cde7` |
| W15-3 | `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]` | `3512a7c` |
| W15-4 | `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]` + `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]` | `89e13e3` |
| W15-5 | `[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]` + `[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]` | `43d6438` |
| W15-6 | `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]` (ADR 0011 Accepted + implemented, Option A) | `be52520` (Proposed at `e41722e`) |
| W15-7 | `[FOLLOWUP compose-image-mutable-ref-pin]` + `[FOLLOWUP gh-action-trivy-version-pin]` + close-out hygiene | `54e7a93` + `7ebbbfb` + `452f1a1` + `7ff31d9` (early pulls `a7a876e` + `2573e35`) |

## W16 Pull-Forward Acceptance Bar (planned)

W16 active on the `week16` branch (per user direction 2026-05-18;
W11-W15 paterni restored via W16-0 doc reconcile). Stable IDs reserved
by §14 plan; each row assigned **at first pull** per the
W11/W12/W13/W14/W15 precedent. Close-out merges into `main` via a
`week16 -> main` PR.

| Iter | Stable ID(s) (planned) | Landing commit |
|---|---|---|
| W16-1 | `[FOLLOWUP scenario-accountant-conservation-split]` (W14-1 root-cause split; HIGH prod regression — dispatch-layer outcome=None emit-site closed) | `01f910a` |
| W16-2 | `[FOLLOWUP analysis-job-worker-entry-crud-ownership]` (W15 audit finding; row-lock-aware lifecycle CRUD primitive — closed at facade boundary) | `9d6d110` |
| W16-3 | `[FOLLOWUP report-finalize-top-level-field-sync-drift]` (W14 production scan-driven investigation) | _pending pull_ |
| W16-4 | `[FOLLOWUP health-reconciliation-responsibility-split]` (W15 audit finding; behavior-preserving extraction; W13-1 HMAC gates preserved) | _pending pull_ |
| W16-5 | `[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread` + `dedupe-step-progress-schemas` + `heartbeat-refactor` (W11+ umbrella closeout) | _pending pull_ |
| W16-6 | `[CLEANUP marketplace-router-test-suite-split]` + `[CLEANUP test-import-graph-policy-dump-split]` + `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` | _pending pull_ |
| W16-7 | close-out hygiene + canonical preamble refresh + `week16 -> main` close-out PR (W11-W15 paterni restored) | _pending pull_ |

## Codex Cloud Audit Backlog

### Post-W13 Candidates

W14- and W15-pulled items are below. Remaining for W15+:

_(W15-4 closed both surviving U-class entries on `2026-05-16`; the open
list is empty until the next Codex audit pass.)_

Closed via W14 (one-line audit trail; full rationale in archive):

- `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` — W14-2.
- `[FOLLOWUP codex-2026-05-10-M5-epoch-docker-exec-propagation]` — W14-5.2 (byproduct).
- `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` — W14-2.
- `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` — W14-3.
- `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` — W14-3 (see ADR 0009).
- `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` — W14-3.

Closed via W15 (one-line audit trail; full rationale in W15 tracker Per-Item Detail):

- `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]` — W15-1 (`c58c365`); post-slate typing annotation hotfix follow-up landed `2026-05-16` via `976dc96`.
- `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]` — W15-2 (`765cde7`, path b fix).
- `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]` — W15-3 (`3512a7c`).
- `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]` — W15-4 (`89e13e3`).
- `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]` — W15-4 (`89e13e3`).

### Quick Fixes

- `[FOLLOWUP codex-2026-05-10-I1-env-example-truthy-drift]` — closed `2026-05-11`.
- `[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]` — W15-5 (`43d6438`).
- `[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]` — W15-5 (`43d6438`).

### Posture Decisions

- `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]` — W15-6 (`be52520`, ADR 0011 Accepted; Option A).

### Verified Closed Audit Trail

H1, H7, M3, M6, M8, U5, U7, U9, U10, U11, I1, I2, I3, I4, M14a, plus
H4/H5/H6 are closed or WONT-FIX as recorded in the full snapshot. W15-5
closed I2 + I4 via `43d6438`; W15-6 closed U10 + U11 via `be52520`
(ADR 0011 Accepted; Option A). Do not re-open without fresh code
evidence.

## Current Open Items By Area

### Workflow / Platform

- `[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread` — **pulled to W16-5** (heartbeat umbrella closeout).
- `[FOLLOWUP simulation-progress-cancel] dedupe-step-progress-schemas` — **pulled to W16-5** (heartbeat umbrella closeout).
- `[FOLLOWUP simulation-progress-cancel] heartbeat-refactor` — **pulled to W16-5** (heartbeat umbrella closeout).
- `[FOLLOWUP analysis-thread-supervisor]`
- `[FOLLOWUP job-service-typevar-audit]`
- `[FOLLOWUP sqlalchemy-error-subtype-logging]`
- `[FOLLOWUP w11-8-companion-workflow-orm-bleed]` (W17+; DTO desen kararı ayrı ADR ister).
- `[FOLLOWUP analysis-job-worker-entry-crud-ownership]` — **closed at
  W16-2** via `9d6d110`. New row-lock-aware lifecycle CRUD primitive
  `claim_queued_analysis_job_at_worker_entry` (+ `WorkerEntryOutcome`
  enum + `WorkerEntryClaim` dataclass) extracted to
  `appcore/storage/crud_ops/analysis_jobs/lifecycle.py`;
  `workflows/marketplace/analysis_service.run_analysis_job` body
  refactored to dispatch on the returned outcome instead of issuing
  inline `SELECT ... FOR UPDATE` + branch + `db.commit()`. `AGENTS.md:57`
  hard rule compliance restored. W13-13 CAS pattern preserved
  byte-identically (row-lock-on-entry → branch-on-status → atomic
  finalize-or-promote); the W13-13 lock-asymmetry rationale (direct
  `finalize_cancelled_analysis_job` call vs. wrapper deadlock) moved
  from the caller docstring into the facade docstring. **Architecture
  gate** at `tests/architecture/test_run_analysis_job_entry_snapshot.py`
  re-targeted on the facade boundary per W14-6 "extend, do not
  duplicate" (INV1: claim helper is the first DB action in
  `run_analysis_job`; INV2: claim helper body contains both
  `with_for_update()` and `finalize_cancelled_analysis_job` AST call
  sites). All 6 W13-13 behavioral pins in
  `tests/platform/storage/test_analysis_jobs_cancel_at_worker_entry.py`
  stay green; one monkeypatch target moved from `analysis_service` to
  `lifecycle` because the W16-2 refactor removed the bare-name binding
  from the analysis_service module scope. Lifecycle surface pin
  (`test_module_path_pins_lifecycle_surface`) extended with the three
  new public exports.

Closed (one-line audit trail):

- `[FOLLOWUP simulation-progress-cancel] is-job-cancelled-session-churn` — W13-3.
- `[FOLLOWUP analysis-jobs-race]` — W14-4 (lifecycle.py lock symmetry).

### Contracts / Reports / Detection

- `[BUG scenario-dropout-upstream-root-cause]` — **closed via W14-1
  `2026-05-13`** (BLOCKER → HIGH); conservation guard at
  `scenario_accountant.py:392-438` is the fix-of-record.
- `[BUG silent-scenario-dropout-regression]` — **observation `2026-05-14`:**
  vuran versiyonu UI tarama'da gözlendi
  (`output/activation_report_ms-python.python-2026.5.2026051301-d2e24db709bd.json`,
  `15:15`): 5 requested scenario'dan 2'si (`debug_session`,
  `refactor_workflow`) `unaccounted_dropout` ile `skipped_scenarios`
  listesinde raporlandı; 3'ü (`project_exploration`, `coding_session`,
  `terminal_usage`) `status: completed`. Conservation guard
  (`scenario_accountant.py:392-438`) beklendiği gibi yakaladı; upstream
  emit-site fix hâlâ açık (`[FOLLOWUP scenario-accountant-conservation-split]`).
  **Second confirmation `2026-05-15` 09:51** (`e801c8d9c8b1.json`,
  post-rebuild against `week15` HEAD `c0c6066` which carries W15-1 +
  W15-2): identical drop set — same 2 scenarios, same `reason_code`,
  same downstream symptoms. The dropout is **deterministic** across
  runs and **not** a side effect of the W15-1/W15-2 changes; the
  upstream emit-site bug class is reproducible without retry.
- `[FOLLOWUP scenario-accountant-conservation-split]` — **dispatch
  layer closed at W16-1** via `01f910a` (HIGH prod regression,
  severity-leading W16 item). `dispatch._normalize_execution_result`
  outcome=None branch now emits `dispatch_outcome_none` (`reason_code`
  + non-empty `detail`) for each requested scenario instead of leaving
  them to the downstream
  `ScenarioAccountant._validate_scenario_conservation` last-mile
  guard's `unaccounted_dropout` fallback. Adjacent emit-site audit
  (W16-1 closure context): `executor/flows/playwright/stimulus/passes.py`
  already records specific reasons (`prerequisite_blocked`,
  `unsupported_activation_surface`, `unknown_scenario`) at L102-158
  per W11+; `executor/flows/playwright/automation.py` accounts every
  requested scenario by design (no silent drops at L275-365); planner
  (`executor/flows/playwright/entrypoint/triggers.py:22-38`) does not
  drop. Any new `unaccounted_dropout` surface would indicate an
  undiscovered emit-site, not the dispatch outcome=None bug class
  (now closed). **Observed in production `2026-05-14`:** debug_session
  + refactor_workflow drop edildiğinde `run_quality: low`,
  `automation_health.status: degraded`, `verification_gap: 2`
  (debug + terminal_tasks capability'leri verify edilemedi —
  dropout'un türevi). `signal_summary.level: needs_review` (score 28)
  — extension için risk_signals 0 olmasına rağmen attribution
  korelatif kaldığı için manuel review öneriliyor. **Deterministic
  confirmation `2026-05-15` 09:51** — bir saatlik rebuild + ikinci
  scan aynı state'i raporladı; root cause non-intermittent, repro
  fixture senkron çekilebilir. **W16-1 test pins:**
  `test_dispatch_outcome_none_emits_specific_reason_code` +
  `test_dispatch_outcome_none_emits_nothing_when_no_requested_scenarios`
  (`tests/security/test_scenario_dropout_repro.py`).
- `[FOLLOWUP report-finalize-top-level-field-sync-drift]` — **pulled to W16-3** (couples with W16-1 scenario-accountant fix; finalize ordering). Production
  scan `activation_report_*.json` carries `null` for several top-level
  fields (`target_extension_id`, `monitoring_start`/`monitoring_end`,
  `scenarios_run`, `harness_handshake_required`) despite underlying
  evidence being present. Not a W14 regression — finalize / `report.save()`
  ordering drift. W15+ hygiene. Full investigation hook in archive.
  **Observation `2026-05-14`:** aynı drift sınıfının yeni bir tezahürü
  gözlendi — `attribution_summary.target_activation_count = 1` raporlanırken
  `evidence_events` listesinde `kind=activation, is_target_extension_event=True`
  hiç yok; ancak `target_extension_host` log stream'inde 1 entry mevcut
  (`Activated ms-python.python via workspaceContains:requirements.txt`).
  İki agregasyon kaynağı aynı aktivasyon için farklı target-flag verdiği
  için top-level sayım stream-türevli, evidence-kind sayımı 0 — finalize
  ordering veya target-flag computation drift'i.
- `[FOLLOWUP event-attempt-verification-status-validator]`
- `[FOLLOWUP report-invariants-runtime-evidence-drift]`
- `[FOLLOWUP compute-verdict-table-driven-test]`
- `[FOLLOWUP signal-summary-needs-review-categories]`
- `[FOLLOWUP monitor-types-property-recomputation]`
- `[FOLLOWUP activation-discovery-strategy-outcome-detail]`
- `[FOLLOWUP planner-executor-action-enum]`
- `[FOLLOWUP planner-selection-readability-audit]`
- `[FOLLOWUP attribution-links-build-evidence-bundle-density]`
- `[FOLLOWUP execute-attempt-rebloat-watch]`
- `[FOLLOWUP dispatch-execution-rebloat-watch]`
- `[CLEANUP rule-registry-side-effect-loader]` — `registry.py` carries
  `_REGISTRY` global + `importlib` side-effect loader + `_BUILTINS_LOADED`
  flag for six builtin rules; a flat `RULES` tuple would suffice at current
  cardinality. Earns its weight only when ADR 0003 deferred rules
  (A5/A7) land. W15+ hygiene.

Closed: `[FOLLOWUP evidence-event-kind-raw-context-invariant]` — W14-4
(9-kind allowlist + `@model_validator(mode='after')`).

### UI / Settings

- `[FOLLOWUP ui-raw-context-discriminator-parity]`
- `[FOLLOWUP ui-supplemental-types-retire]`
- `[FOLLOWUP vsix-integrity-in-activation-report]`
- `[FOLLOWUP vsix-thresholds-extra-keys]`
- `[BACKLOG ui-v3-5]` — Settings persistence API partially closed for
  Security thresholds; other localStorage sections client-only.
- `[CLEANUP ui-v3-9]`
- `[CLEANUP ui-v3-14]`

### Engineering Quality

- `[FOLLOWUP ci-reintroduction]`
- `[CLEANUP report-builder-naming]`
- `[CLEANUP monitor-runtime-naming-overlap]`
- `[CLEANUP env-example-extrace-vars]`
- `[CLEANUP postgres-version-fact-drift]`
- `[CLEANUP adr-0007-runbook-wording-drift]`
- `[CLEANUP pre-commit-python-version-alignment]`
- `[CLEANUP test-import-graph-policy-dump-split]` — **pulled to W16-6**
  (hygiene splits bundle). `test_import_graph.py` carries 18 distinct
  architectural test functions in 767 LoC; thematic split
  (`test_import_isolation.py` / `test_facade_locks.py` /
  `test_executor_invocation.py` / `test_monitor_stimulus_boundary.py`)
  improves discoverability.
- `[FOLLOWUP health-reconciliation-responsibility-split]` — **pulled to W16-4**
  (behavior-preserving extraction; W13-1 HMAC gates must not regress).
  `executor/flows/playwright/health/reconciliation.py` (682 LoC) carries
  security-sensitive (HMAC marker verification at :78, fail-closed
  harness handshake decisions, harness Python secret loading at :39) +
  report-accuracy (event-attempt reconciliation at :414, coverage
  reconciliation at :581) decisions in one module. Risk class:
  change-safety drift — the same file owns both fail-closed security
  gates (W13-1 / Codex H6 HMAC anchor) and report-coverage classification.
  A future small edit could regress security or report fidelity without
  the reviewer noticing the cross-concern coupling. Recommendation:
  map responsibility boundaries first (which functions own which risk
  class), validate test coverage on both sides, then do a behavior-
  preserving extraction. **Do not auto-refactor**; W13-1 HMAC gates
  must not regress. W15+ hygiene; new audit finding `2026-05-16`.
- `[CLEANUP marketplace-router-test-suite-split]` — **pulled to W16-6**
  (hygiene splits bundle). `tests/workflows/marketplace/test_router.py` (2374 LoC). Title
  docstring at :5 implies search/download scope but file spans analyze
  (:744), trigger planning (:778), background job persistence (:1581),
  and async job endpoint (:2080). Test-maintenance burden only — no
  runtime risk. Recommended: classify-then-split by domain
  (search/download + sync analyze + trigger planning + background job
  lifecycle + async job endpoint) with behavior-preserving moves.
  Not a W15 priority; W16+ hygiene candidate. New audit finding
  `2026-05-16`.

Closed (one-line audit trail):

- `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]` — W14-6.6 (`e42a448`).
- `[FOLLOWUP arch-gate-executor-control-outbound]` — W14-6.5 (`b031803`).
- `[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]` — W14-6.4 (`2adad43`).
- `[CLEANUP appcore-config-stale-docstring]` — `2026-05-11`.
- `[CLEANUP session-docstring-except-exception]` — `2026-05-11`.
- `[CLEANUP uri-validation-stale-sys-path-comment]` — `2026-05-11`.
- `[FOLLOWUP compose-image-mutable-ref-pin]` — W15-7 (`54e7a93` compose pin + `7ebbbfb` test extension; postgres:16-alpine + alpine/socat:1.8.0.3 manifest digest pin; `tests/architecture/` 196 → 198).
- `[FOLLOWUP gh-action-trivy-version-pin]` — W15-7 (`452f1a1`; `aquasecurity/trivy-action@v0.36.0` version tag pin matching repo `actions/*@vN` precedent).

### Test + Observability

- `[FOLLOWUP w8-0-capture-pipeline]`
- `[FOLLOWUP w8-1-extract-rejection-logging]`
- `[FOLLOWUP w8-1-archive-count-bypass]`
- `[FOLLOWUP w8-1-vsix-compressed-size-limit]`
- `[FOLLOWUP w8-3-harness-js-scheme]`
- `[FOLLOWUP w8-4-broader-executor]`
- `[FOLLOWUP w8-6-content-sample-structural-test]`
- `[FOLLOWUP w8-8-manifest-emit-when-needed]`
- `[FOLLOWUP w8-8-trigger-sweep-as-test]`
- `[FOLLOWUP w8-9-network-body-boundary-split-secret-test]`
- `[FOLLOWUP codex-automation-6]` — UI failure taxonomy for operator
  clarity; W15+.
- `[FOLLOWUP capability-verification-gap]` — `NEEDS-DESIGN`; W15+.
- `[FOLLOWUP adr-0002-vsix-extraction-section-missing]`

Closed: `[FOLLOWUP codex-automation-5]` — W14-5.3 (`db25d5f`); executor
runtime fingerprint module + automation output emit + ActivationReport
`executor_fingerprint` field.

## Closed/Archived Groups

Full close evidence in the latest archive snapshot for:

- W8/W9/W10/W11/W12 closure work.
- Closed W12 companion items: attribution precursor tests, attribution
  facade cleanups, marketplace installer-tail redaction, generated UI
  contract coverage, Settings copy drift, security-settings ownership,
  API/UI Docker digest pins, W12 close-out gates.
- Repo hygiene items already closed:
  `[CLEANUP repo-tracked-scratch-files]`, `[CLEANUP tests-scanner-rename]`,
  `[CLEANUP agent-context-phase-snapshot-stale]`,
  `[CLEANUP httpx-runtime-dependency-metadata]`,
  `[FOLLOWUP scripts-seed-test-rewrite]`, `[FOLLOWUP triggers-private-helper-import]`.

## How To Pull An Item Back

1. Search by stable ID in this file and the latest full archive snapshot.
2. Confirm code/tests still match the recorded premise.
3. Add or update tests first when the item describes a regression risk.
4. Close by preserving the stable ID and adding the landing date/commit.
