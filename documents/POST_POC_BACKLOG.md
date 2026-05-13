# Post-PoC Backlog

`Last Updated: 2026-05-13 (W14 active on week14; W14-1 in progress (BLOCKER -> HIGH); W14-2 closed via bde17be; W14-3 closed via 941250d; off-roadmap hygiene candidates added: rule-registry-side-effect-loader, compose-image-mutable-ref-pin, gh-action-trivy-version-pin, test-import-graph-policy-dump-split, report-finalize-top-level-field-sync-drift)`

Open deferred work after the W0-W7 PoC acceptance bar. **Slim canonical** —
verbose descriptions, evidence, and older triage notes are frozen in dated
snapshots:

- latest full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-11.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-11.md)
- previous full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-07.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-07.md)

W8, W9, W10, W11, W12, and W13 are closed. W13 acceptance bar + §11.10 GOAL pulls
closed; close-out PR #20 `week13 -> main` **MERGED** `2026-05-13` via `772deb3`. Next active phase: **W14
Codex M-class Acceptance + Observability**, staged in
[`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md);
predecessor tracker
[`active-work/W13-test-expansion-observability.md`](active-work/W13-test-expansion-observability.md)
is now archived in-place (close-evidence retained for audit-trail).

## Stable IDs Are A Contract

Do not rename existing IDs. Current code/tests reference at least:

- `[FOLLOWUP analysis-jobs-race]`
- `[FOLLOWUP simulation-progress-cancel]`
- `[FOLLOWUP simulation-progress-cancel] cancel-after-finish race test`
- this filename from `packages/analysis_contracts/contracts.py`

Use stable IDs in new references; do not cite canonical doc line numbers.

## W13 Pull-Forward Acceptance Bar

| Stable ID | Status | Note |
|---|---|---|
| ~~`[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]`~~ | closed via W13-5 | Path A recipe-fix: `Makefile:172` `--host $${API_HOST:-0.0.0.0}` + 6 architecture gates landed (`tests/architecture/test_makefile_dev_recipes.py`) + `lan-exposure.md` §Host-mode caveat removed |
| `[FOLLOWUP codex-2026-05-10-H4-cancel-concurrent-race]` | closed via W13-3 | two-phase `cancelling` state + worker poll points |
| `[FOLLOWUP codex-2026-05-10-H5-writable-vscode-launcher]` | closed via W13-2 | `launch_vscode.sh` root-owned 0750 |
| `[FOLLOWUP codex-2026-05-10-H6-spoofable-harness-markers]` | closed via W13-1 | per-launch HMAC marker verification |
| ~~`[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]`~~ | closed via W13-7 | bounded scanner `_redact_private_key_bounded()` for private_key cross-line span in `redact_multiline_secrets()` + 16 KB BEGIN→END window cap; pre-fix 361 ms → post-fix 1.29 ms on 200 BEGIN + 1 KB body adversarial input (~280× speedup); W12-0 4 PEM regression cases intact (identical replacement semantics) |
| ~~`[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]`~~ | closed via W13-6 | factory-internal redaction at `_bounded_arguments_preview()` + new replica architecture gate `tests/architecture/test_arguments_preview_redaction.py` (2/2 ✓ — factory body invariant + routing invariant) + parametrized regression covering aws/bearer/api_key/db_url/private_key (5/5 ✓) |
| `[FOLLOWUP w13-3-close-pass-cancellation-test-hardening]` | closed via W13-4 | behavioral coverage + `analysis-job-stuck` runbook update |
| `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` | deferred | needs fresh-DB-per-test Alembic fixture |
| ~~`[CLOSE-GATE codex-second-opinion-F1-hmac-python-secret-target-install-race]`~~ (W13-11) | **closed `2026-05-12`** (6/6 sub-commits) | Close-pass for W13-1 H6. Codex Cloud second-opinion `2026-05-11`. Path A host-side eager-consume + env var passthrough; `executor_control.consume_harness_python_secret()` between `_reset_sandbox` and `_install_extension`; `EXECUTOR_HARNESS_PYTHON_SECRET_VALUE` env threading + E4 docker exec argv mask. W13-12 immediate follow-up closed `2026-05-12` (see W13-12 row below). |
| ~~`[CLOSE-GATE codex-second-opinion-F2-fail-closed-harness-handshake]`~~ (W13-12) | **closed `2026-05-12`** (5/5 sub-commits + post-landing: 3a89c09 self-stamp · 9c80f25 drift sweep · 0d3e343 behavioral pins) | Close-pass for W13-1 H6. Codex Cloud second-opinion `2026-05-11`. `harness_handshake_required: bool` on internal monitor ActivationReport dataclass + `setup_monitor` stamps True + fail-closed branch in `_attempt_has_harness_completion_trace` + 3-fact AST gate + 3 post-landing behavioral pins (signature priority / malformed trace fail-closed / e2e attestation). Final bar: test-local 1537 → 1539 (+2 main) → 1542 (+3 post-landing); tests/architecture/ 112 → 115 (+3); W13-1 regression suite zero-diff. Close-out PR merge blocker reduces to W13-13 only. |
| ~~`[CLOSE-GATE codex-second-opinion-F3-worker-start-cancel-race-CAS]`~~ (W13-13) | **closed `2026-05-13`** (5/5 sub-commits + post-landing — `d2ba495` docs lockdown · `02c4374` RED behavioral · `33deb46` feat impl · `60bb0cd` arch gate · `8912596` close evidence + 10-site drift sweep; post-landing: `826f91c` self-stamp · `26a2025` post-landing behavioral pins (vanished row + finalize idempotency + failed/cancelled terminal)) | Close-pass for W13-3 H4 (F4 README drift sweep + regex pin already landed in W13-11 push `2026-05-12`). Codex Cloud second-opinion `2026-05-11`. Path B worker-entry `select(AnalysisJob).where(...).with_for_update()` snapshot lock in `workflows/marketplace/analysis_service.py::run_analysis_job` closes the cancel-race seam at the router → worker-thread boundary. Entry block branches: row missing → log + return; terminal → log + return; `cancelling` → `finalize_cancelled_analysis_job(db, ...)` via lifecycle helper directly (wrapper would deadlock against held row lock) + return; `queued` → atomic transition + commit + proceed. 3 new RED→GREEN behavioral cases + 2-fact AST gate (INV1 first-DB-action is the lock; INV2 lifecycle helper called before `execute_analysis_request`) + 4 post-landing behavioral pins (vanished row + finalize idempotency under race + parametrized terminal short-circuit for ``failed`` + ``cancelled``). W13-4 `update_job.assert_called_once()` flipped to `assert_not_called()` (Path B contract). Final bar: test-local 1542 → **1547** (+5 main) → **1551** (+4 post-landing); tests/architecture/ 115 → **117** (+2; unchanged post-landing); W13-3 + W13-4 + W13-1/W13-11/W13-12 regression suites zero-diff. Production smoke `2026-05-13`: UI scan `9d327b30b60f...` (`ms-python.python@2026.5.2026050801`) completed cleanly via Path B happy-path (reserve→start 35ms; 22 activations; Target observed=True). Close-out PR `week13 → main` merge blocker **CLEARED**. |

## W14 Pull-Forward Acceptance Bar

Skeleton scope authored `2026-05-11` alongside W13 close-out preparation;
entry was triggered by PR #20 `week13 -> main` merge on `2026-05-13`.
Stable IDs `W14-N` are assigned at first pull (W11/W12/W13 precedent). Full per-iter detail lives in
[`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md).

| Iter | Stable ID(s) | Status | Note |
|---|---|---|---|
| W14-1 | `[BUG scenario-dropout-upstream-root-cause]` | in progress — downgraded HIGH `2026-05-13` | BLOCKER triage landed on `week14` (deterministic repro matrix at `tests/security/test_scenario_dropout_repro.py` covers 5 known dropout vectors; conservation guard at `scenario_accountant.py:392-438` is the deterministic fix-of-record). Upstream emit-site work tracked under `[FOLLOWUP scenario-accountant-conservation-split]` |
| W14-2 | `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` + `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` | **closed** `2026-05-13` | Input validation cluster landed on `week14`: M4-M7 via `_coerce_safe_epoch_s` chokepoint at `executor/flows/playwright/signals/output.py`; M11 via `_safe_int_coerce` helper at `workflows/marketplace/analysis_reports.py`. 2 arch gates + 51 behavioral regression cases. |
| W14-3 | `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` + `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` + `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` | **closed** `2026-05-13` | External surface hardening cluster landed on `week14`: M13 via `redact_secrets()` routing for `NetworkEvent.path` + `summary` at `runtime_capture/network.py`; M14b via empty default + conditional CDP flag across `launch_vscode.sh`/`start.sh`/`docker-compose.yml`/`Makefile up-debug` (posture: opt-in `EXECUTOR_CDP_PORT`); U4-U12 via validation + quoted expansion in `Makefile` `sim-target`/`sim-run`. 3 arch gates + 10 behavioral cases. |
| W14-4 | `[FOLLOWUP analysis-jobs-race]` + `[FOLLOWUP evidence-event-kind-raw-context-invariant]` | **closed** `2026-05-13` | Doğruluk + concurrency cluster landed on `week14`. analysis-jobs-race: `complete_analysis_job` + `fail_analysis_job` now acquire `select(...).with_for_update()` and gate against `_TERMINAL_JOB_STATUSES` (W13-3 lock-discipline mirror). evidence-event-kind: `EvidenceEvent` carries a closed 9-kind allowlist (`_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS`) + `@model_validator(mode='after')` raising on mismatch or unknown kind. 2 arch gates (+4 cases) + 65 behavioral cases (9 positive + 54 mismatch + 1 unknown + 1 default-rc edge) + 3 new concurrency cases + 5 drifted fixtures repaired. |
| W14-5 | `[GOAL w14-logger-consolidation]` + `[GOAL w14-run-id-stamping]` (yeni stable ID'ler) + `[FOLLOWUP codex-automation-5]` | scoped — not started | §11.10 GOAL devamı W13'ten devreden + automation runtime fingerprint (sibling tema); M5 (`epoch-docker-exec-propagation`) doğal yan ürün adayı |
| W14-6 | `[FOLLOWUP arch-gate-executor-control-outbound]` + `[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]` + `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]` | scoped — not started | §11.10 GOAL devamı — W8-W12 regression lock-in umbrella; AST-tabanlı 3 yeni arch gate |

## Codex Cloud Audit Backlog

### Post-W13 Candidates

Items annotated `(W14-N)` are pulled into the W14 acceptance bar above;
remaining items iter into W15+.

- ~~`[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]`~~ — **closed
  `2026-05-13`** via W14-2 on `week14`. `_coerce_safe_epoch_s` chokepoint added
  to `executor/flows/playwright/signals/output.py`; ``_format_epoch_ms`` now
  sanitizes every extension-controlled ``ts`` (including ``inf`` / ``NaN`` /
  out-of-window finites) before calling ``datetime.fromtimestamp()``. Gated by
  `tests/architecture/test_output_signal_ts_guard.py`; behavioral coverage in
  `tests/security/test_output_signal_ts_range.py`.
- `[FOLLOWUP codex-2026-05-10-M5-epoch-docker-exec-propagation]` —
  propagate `EXTRACE_EPOCH_RUN_ID` through `executor/host.py` docker exec.
  Doğal yan ürün adayı W14-5 (logger consolidation + run-ID stamping);
  çekilmezse W15'e düşer.
- `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]` —
  align sync `/api/marketplace/analyze` error catch with async path. W15+.
- ~~`[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]`~~ — **closed
  `2026-05-13`** via W14-2 on `week14`. `_safe_int_coerce` helper added to
  `workflows/marketplace/analysis_reports.py`; `build_report_messages` now
  routes ``automation_health.get("target_activation_count")`` through it,
  defaulting to ``0`` on every coercion failure (``TypeError`` / ``ValueError``
  / ``OverflowError``). Gated by
  `tests/architecture/test_report_messages_int_guard.py`; behavioral coverage
  in `tests/security/test_report_messages_malformed_types.py`.
- `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]` —
  delete or fix orphan `clean_workspace()` symlink handling. W15+.
- ~~`[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]`~~ — **closed
  `2026-05-13`** via W14-3 on `week14`. `NetworkEvent.path` and
  `NetworkEvent.summary` now route through ``redact_secrets()`` at the
  same chokepoint that already covers ``*_body_preview`` (W12-5) and
  ``arguments_preview`` (W13-6). Gated by
  `tests/architecture/test_network_uri_summary_redaction.py`; behavioral
  coverage in `tests/security/test_network_uri_summary_redaction.py`.
- ~~`[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]`~~ — **closed
  `2026-05-13`** via W14-3 on `week14`. Posture decision formalized as
  [`ADR 0009: CDP Default-Disabled in the Executor Container`](adrs/0009-cdp-default-disabled.md)
  (container-internal complement to ADR 0007 §4 which already gated
  host→container exposure). Opt-in via `EXECUTOR_CDP_PORT` env var.
  Empty default propagates through `launch_vscode.sh`, `start.sh`, and
  the executor service entry in `docker-compose.yml`; the launch
  wrapper appends the `--remote-debugging-port` flag only when the
  value is non-empty. `make up-debug` explicitly sets
  `EXECUTOR_CDP_PORT=9222` before invoking compose so the debug
  profile UX stays unchanged. Gated by
  `tests/architecture/test_cdp_port_default.py`.
- `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]` — W15+;
  cap UI event density/timeline spread operations.
- `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]` — W15+; cap relations
  graph nodes/edges.
- ~~`[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]`~~ — **closed
  `2026-05-13`** via W14-3 on `week14`. Both `sim-target` and `sim-run`
  recipes now (a) validate operator-supplied `TARGET` / `SCENARIO` /
  `TRIGGERS` against strict character classes before any expansion
  reaches the shell, and (b) double-quote every Make-variable
  interpolation inside the `docker exec` command line. Gated by
  `tests/architecture/test_makefile_sim_quoting.py`.
- `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]` — W15+; cap activation
  event strings/list size and migrate DB field length.

### Quick Fixes

- ~~`[FOLLOWUP codex-2026-05-10-I1-env-example-truthy-drift]`~~ — closed
  `2026-05-11`; `.env.example` now lists only `1/true/yes`, matching
  `main.py`.
- `[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]` — UI client `/health`
  path may bypass nginx `/api/*` proxy.
- `[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]` — tighten
  lifecycle `"for <id>"` regex capture.

### Posture Decisions

- `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]` — decide
  whether unauthenticated catalog endpoints stay PoC-accepted posture or get
  auth before W14.

### Verified Closed Audit Trail

H1, H7, M3, M6, M8, U5, U7, U9, I3, M14a, plus H4/H5/H6 are closed or
WONT-FIX as recorded in the full snapshot. Do not re-open without fresh code
evidence.

## Current Open Items By Area

### Workflow / Platform

- `[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread`
- `[FOLLOWUP simulation-progress-cancel] dedupe-step-progress-schemas`
- ~~`[FOLLOWUP simulation-progress-cancel] is-job-cancelled-session-churn`~~ —
  closed via W13-3.
- `[FOLLOWUP simulation-progress-cancel] heartbeat-refactor`
- ~~`[FOLLOWUP analysis-jobs-race]`~~ **closed via W14-4 `2026-05-13`** —
  W13-4.4 documented the `complete_analysis_job` race window (CRITICAL).
  W14-4 closes by extending the W13-3 lock discipline:
  `complete_analysis_job` (`lifecycle.py:319`) and `fail_analysis_job`
  (`lifecycle.py:260`) now acquire `select(...).with_for_update()` and
  raise `JobNotCancellableError` on any `_TERMINAL_JOB_STATUSES` source
  state in addition to the existing `cancelling` guard. Concurrent
  writers serialize through the lock and exactly one commits the
  terminal transition.
- `[FOLLOWUP analysis-thread-supervisor]`
- `[FOLLOWUP job-service-typevar-audit]`
- `[FOLLOWUP sqlalchemy-error-subtype-logging]`
- `[FOLLOWUP w11-8-companion-workflow-orm-bleed]`

### Contracts / Reports / Detection

- `[BUG scenario-dropout-upstream-root-cause]` **(W14-1; downgraded BLOCKER → HIGH
  `2026-05-13`)** — W14-1 BLOCKER triage on `week14` landed the deterministic
  repro matrix at `tests/security/test_scenario_dropout_repro.py` (5 vectors:
  `vec_ms_python_python`, `vec_stimulus_collapse`, `vec_all_accounted`,
  `vec_all_explicit_skip`, `vec_partial_failed`). The last-mile conservation
  guard at `executor/flows/playwright/monitor/scenario_accountant.py:392-438`
  (`_validate_scenario_conservation`) is the fix-of-record: every dropout is
  caught and labelled `unaccounted_dropout` so the W7 §10.7 honesty invariant
  holds end-to-end. Upstream emit-site work (planner / `stimulus_passes` /
  `dispatch._normalize_execution_result`) is **stochastic-bound** and tracked
  separately under `[FOLLOWUP scenario-accountant-conservation-split]`.
- `[BUG silent-scenario-dropout-regression]`
- `[FOLLOWUP scenario-accountant-conservation-split]` — W14-1 close-out
  recategorized this as the canonical follow-up for upstream emit-site work
  (planner / `stimulus_passes` / `dispatch._normalize_execution_result`
  scenario-level trace + reason-code propagation). Separate pull, not in any
  W14 sub-iter. Candidate W15+ depending on operator-observability priority.
- `[FOLLOWUP report-finalize-top-level-field-sync-drift]` — production
  scan output (`activation_report_*.json`) carries `null` for several
  top-level `ActivationReport` fields even when the underlying evidence is
  present: `target_extension_id` (file name carries the id),
  `monitoring_start` / `monitoring_end` (per-event `started_at` /
  `ended_at` epochs are populated in `scenario_traces`), `scenarios_run`
  (despite `scenario_traces` being filled and
  `_synchronize_scenario_truth` deriving the list per
  `executor/flows/playwright/monitor/scenario_accountant.py:441-452`), and
  `harness_handshake_required` (W13-12 invariant; `setup_monitor` stamps
  `True` at `executor/flows/playwright/entrypoint/dispatch.py:137` but
  the persisted JSON shows `null`). Pre-W14 W13 close-out smoke scan
  (`activation_report_ms-python.python-2026.5.2026050801-9d327b30b60f.json`,
  `2026-05-13` 00:46) exhibits the same nulls — **not a W14 regression**,
  a finalize / `report.save()` drift surfaced during the W14-3 post-pull
  scan review (current scan: `c71107e2ff84`, `2026-05-13` 15:36).
  Same-scan UI flow unaffected (consumes derived `automation_health`
  which populates correctly: status, target_activation_count,
  skipped_scenarios all present); downstream analyzers reading top-level
  fields directly are the blocked surface. Investigation hook: trace
  `ExtensionMonitor.stop()` → `report.save()` ordering relative to
  `_synchronize_scenario_truth` and the `setup_monitor` flag writes; the
  Pydantic v2 model also defaults each of these to `None`, so a
  pre-save synchronization pass is the likely fix shape. Lane:
  `[contracts]` `[platform-storage]`. W15+ hygiene; not a W14 sub-iter
  candidate.
- ~~`[FOLLOWUP evidence-event-kind-raw-context-invariant]`~~ **closed via
  W14-4 `2026-05-13`** — `EvidenceEvent` now carries a
  `@model_validator(mode='after')` enforcing a closed 9-kind allowlist
  (`_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS` in
  `packages/analysis_contracts/contracts.py`): 7 strict 1:1 producer
  kinds + 2 alias kinds (`extension_host` → `activation`,
  `log` → `scenario`). Mismatched pairs and unknown kinds raise
  `ValueError` at ingest; downstream rule helpers in
  `_common.py` no longer mask silent drift via getattr defaults. RED
  stub `test_evidence_event_rejects_kind_event_class_mismatch` plus
  positive / unknown / default-rc edge cases (65 total) landed at
  `tests/platform/contracts/test_raw_context_discriminated.py`. 5
  drifted fixtures repaired in-PR (3 malicious-canary
  `activation_report.json` + 2 inline test builders) — the same drift
  surface the audit flagged.
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
- `[CLEANUP rule-registry-side-effect-loader]` — `packages/analysis_engine/rules/registry.py`
  carries a `_REGISTRY` global dict + `importlib.import_module()` side-effect
  loader + `_BUILTINS_LOADED` flag + `clear_registry()` test helper for the
  six builtin rules (A1/A2/A3/A4/A6 + `demo_runnable_canary`). Each rule
  module top-level-calls `register(...)`. A flat
  `RULES: tuple[DetectionRule, ...] = (...)` would suffice for the current
  cardinality and avoid global mutable state plus test-side `clear_registry()`
  churn; the auto-register pattern only earns its weight when ADR 0003
  deferred rules (A5 update / A7 VS Code API abuse) are pulled in from the
  backlog. Low-Medium risk: overengineering relative to current scope, not a
  defect. W15+ hygiene candidate.

### UI / Settings

- `[FOLLOWUP ui-raw-context-discriminator-parity]`
- `[FOLLOWUP ui-supplemental-types-retire]`
- `[FOLLOWUP vsix-integrity-in-activation-report]`
- `[FOLLOWUP vsix-thresholds-extra-keys]`
- `[BACKLOG ui-v3-5]` — Settings persistence API is partially closed for
  Security thresholds; other localStorage sections remain client-only.
- `[CLEANUP ui-v3-9]`
- `[CLEANUP ui-v3-14]`

### Engineering Quality

- `[FOLLOWUP ci-reintroduction]`
- `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]` **(W14-6)** —
  W8-W12 regression lock-in umbrella üyesi.
- `[FOLLOWUP arch-gate-executor-control-outbound]` **(W14-6)** — W8-W12
  regression lock-in umbrella üyesi.
- `[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]` **(W14-6)** — W8-W12
  regression lock-in umbrella üyesi.
- `[CLEANUP report-builder-naming]`
- `[CLEANUP monitor-runtime-naming-overlap]`
- `[CLEANUP env-example-extrace-vars]`
- `[CLEANUP postgres-version-fact-drift]`
- `[CLEANUP adr-0007-runbook-wording-drift]`
- ~~`[CLEANUP appcore-config-stale-docstring]`~~ — closed `2026-05-11`.
- ~~`[CLEANUP session-docstring-except-exception]`~~ — closed `2026-05-11`.
- ~~`[CLEANUP uri-validation-stale-sys-path-comment]`~~ — closed
  `2026-05-11`.
- `[CLEANUP pre-commit-python-version-alignment]`
- `[FOLLOWUP compose-image-mutable-ref-pin]` — `docker-compose.yml:121`
  `image: alpine/socat:latest` mutable tag on the `executor-cdp` debug
  sidecar. The sidecar lives under `profiles: ["debug"]` so the default
  `docker compose up` does not start it; supply-chain hygiene argument is
  reproducibility, not active exploit. `tests/architecture/test_dockerfile_digest_pin.py`
  walks `DOCKERFILE_ROOTS = (docker, executor/container, ui)` and pins
  `FROM` lines via `@sha256:` only — compose image refs are out of that
  gate's scope. Pin to a digest (`alpine/socat@sha256:...`) and extend the
  gate to cover compose `image:` keys when this is pulled. Low-Medium risk;
  W15+ hygiene.
- `[FOLLOWUP gh-action-trivy-version-pin]` — `.github/workflows/security.yml:71`
  `uses: aquasecurity/trivy-action@master` mutable ref. Same file's other
  actions are version-pinned: `actions/checkout@v4`, `actions/setup-python@v5`,
  `actions/upload-artifact@v4`. Pin Trivy to a tag or SHA (`@0.20.0` /
  `@<sha>`). Distinct from `[FOLLOWUP ci-reintroduction]` (which gates
  broader CI expansion); this is hygiene for an already-active workflow.
  Low-Medium risk; W15+ hygiene.
- `[CLEANUP test-import-graph-policy-dump-split]` —
  `tests/architecture/test_import_graph.py` carries 18 distinct architectural
  test functions in 767 LoC (`test_packages_remain_framework_agnostic`,
  `test_executor_avoids_workflow_and_appcore_imports`,
  `test_workflows_use_only_executor_control_boundary`,
  `test_no_dual_import_fallback_in_executor`,
  `test_no_sys_path_manipulation_in_runtime`,
  `test_executor_imports_signals_from_packages`,
  `test_extension_catalog_service_stays_a_thin_facade`,
  `test_extension_catalog_service_reexports_match_canonical_modules`,
  `test_analysis_jobs_facade_stays_thin`,
  `test_analysis_jobs_facade_reexports_match_canonical_modules`,
  `test_monitor_facade_does_not_eagerly_import_attribution`,
  `test_monitor_and_stimulus_subpackages_do_not_cross_import`,
  `test_monitor_lazy_proxy_completeness`,
  `test_executor_playwright_flat_file_count_limit`,
  `test_attribution_does_not_eagerly_import_monitor`,
  `test_python_m_playwright_invocations_have_main_module`,
  `test_runtime_capture_extension_host_stays_a_thin_facade`,
  `test_runtime_capture_extension_host_reexports_match_canonical_modules`).
  Beyond pure "import graph" — facade locks, package-mode invocation, monitor
  lazy proxy, flat-file budget all live here. W14-6 adds three more AST gates
  to this surface. Thematic split into e.g.
  `test_import_isolation.py` / `test_facade_locks.py` /
  `test_executor_invocation.py` / `test_monitor_stimulus_boundary.py`
  improves discoverability when a new gate is added. Low risk; W15+ hygiene.

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
- `[FOLLOWUP codex-automation-5]` **(W14-5)** — executor runtime
  fingerprint in automation output; run-ID stamping ile sibling tema,
  aynı PR ailesinde çekilir.
- `[FOLLOWUP codex-automation-6]` — UI failure taxonomy for operator
  clarity; W14 temasıyla örtüşmüyor, W15+.
- `[FOLLOWUP capability-verification-gap]` — W15+; triyajda `NEEDS-DESIGN`,
  W14-6'nın AST-tabanlı arch gate ritmine girmiyor.
- `[FOLLOWUP adr-0002-vsix-extraction-section-missing]`

## Closed/Archived Groups

Full close evidence is in the latest archive snapshot for:

- W8/W9/W10/W11/W12 closure work.
- Closed W12 companion items: attribution precursor tests, attribution facade
  cleanups, marketplace installer-tail redaction, generated UI contract
  coverage, Settings copy drift, security-settings ownership, API/UI Docker
  digest pins, and W12 close-out gates.
- Repo hygiene items already closed:
  `[CLEANUP repo-tracked-scratch-files]`,
  `[CLEANUP tests-scanner-rename]`,
  `[CLEANUP agent-context-phase-snapshot-stale]`,
  `[CLEANUP httpx-runtime-dependency-metadata]`,
  `[FOLLOWUP scripts-seed-test-rewrite]`, and
  `[FOLLOWUP triggers-private-helper-import]`.

## How To Pull An Item Back

1. Search by stable ID in this file and the latest full archive snapshot.
2. Confirm code/tests still match the recorded premise.
3. Add or update tests first when the item describes a regression risk.
4. Close by preserving the stable ID and adding the landing date/commit.
