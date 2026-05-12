# Post-PoC Backlog

`Last Updated: 2026-05-12 (W13-1..W13-10 sub-iters all closed; W13-11 closed 2026-05-12 (6/6 sub-commits — design+impl+arch gate+regression fix+doc sweep) — Path A host-side eager-consume + env var passthrough; W13-12 in progress 2026-05-12 (sub-commit 1/5 — design lockdown) — `ActivationReport.harness_handshake_required: bool` fail-closed; W13-13 remains CLOSE-GATE not started; close-out PR week13 → main BLOCKED until W13-12/13 GREEN)`

Open deferred work after the W0-W7 PoC acceptance bar. **Slim canonical** —
verbose descriptions, evidence, and older triage notes are frozen in dated
snapshots:

- latest full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-11.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-11.md)
- previous full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-07.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-07.md)

W8, W9, W10, W11, and W12 are closed. W13 acceptance bar + §11.10 GOAL pulls
are closed; close-out PR `week13 → main` pending. Next active phase: **W14
Codex M-class Acceptance + Observability**, staged in
[`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md);
predecessor tracker
[`active-work/W13-test-expansion-observability.md`](active-work/W13-test-expansion-observability.md)
remains active until the W13 close-out PR merges.

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
| ~~`[CLOSE-GATE codex-second-opinion-F1-hmac-python-secret-target-install-race]`~~ (W13-11) | **closed `2026-05-12`** (6/6 sub-commits) | Close-pass for W13-1 H6. Codex Cloud second-opinion `2026-05-11`. Path A host-side eager-consume + env var passthrough; `executor_control.consume_harness_python_secret()` between `_reset_sandbox` and `_install_extension`; `EXECUTOR_HARNESS_PYTHON_SECRET_VALUE` env threading + E4 docker exec argv mask. W13-12 immediate follow-up required for full fail-closed semantics. |
| **`[CLOSE-GATE codex-second-opinion-F2-fail-closed-harness-handshake]`** (W13-12) | **in progress `2026-05-12`** (sub-commit 1/5 — design lockdown) | Close-pass for W13-1 H6. Codex Cloud second-opinion `2026-05-11`. Depends on W13-11 (closed). Merge blocker. `ActivationReport.harness_handshake_required: bool` field on internal monitor dataclass + `_attempt_has_harness_completion_trace` fail-closed when handshake required but `expected_nonce` empty. |
| **`[CLOSE-GATE codex-second-opinion-F3-worker-start-cancel-race-CAS]`** (W13-13) | **CLOSE-GATE — not started** | Close-pass for W13-3 H4 + F4 README drift sweep. Codex Cloud second-opinion `2026-05-11`. Merge blocker. |

## W14 Pull-Forward Acceptance Bar

Skeleton scope authored `2026-05-11` alongside W13 close-out preparation;
activates on `week13 → main` PR merge. Stable IDs `W14-N` assigned at
first pull (W11/W12/W13 precedent). Full per-iter detail lives in
[`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md).

| Iter | Stable ID(s) | Status | Note |
|---|---|---|---|
| W14-1 | `[BUG scenario-dropout-upstream-root-cause]` | scoped — not started | BLOCKER triage; deterministik repro fixture + kök neden tespiti; eğer stokastik HIGH'a indir |
| W14-2 | `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` + `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` | scoped — not started | Input validation cluster; W13-6 parametrize regression deseni; bundle pull |
| W14-3 | `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` + `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` + `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` | scoped — not started | Dış yüzey sertleştirme; M13 W13-6 factory-internal redaction deseninin tekrarı; U4-U12 W13-5 recipe-fix deseni |
| W14-4 | `[FOLLOWUP analysis-jobs-race]` + `[FOLLOWUP evidence-event-kind-raw-context-invariant]` | scoped — not started | Doğruluk + concurrency; analysis-jobs-race CRITICAL (W13-4.4 race window dokümante); evidence-event-kind test stub hazır |
| W14-5 | `[GOAL w14-logger-consolidation]` + `[GOAL w14-run-id-stamping]` (yeni stable ID'ler) + `[FOLLOWUP codex-automation-5]` | scoped — not started | §11.10 GOAL devamı W13'ten devreden + automation runtime fingerprint (sibling tema); M5 (`epoch-docker-exec-propagation`) doğal yan ürün adayı |
| W14-6 | `[FOLLOWUP arch-gate-executor-control-outbound]` + `[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]` + `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]` | scoped — not started | §11.10 GOAL devamı — W8-W12 regression lock-in umbrella; AST-tabanlı 3 yeni arch gate |

## Codex Cloud Audit Backlog

### Post-W13 Candidates

Items annotated `(W14-N)` are pulled into the W14 acceptance bar above;
remaining items iter into W15+.

- `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` **(W14-2)** —
  guard extension-controlled timestamps before `datetime.fromtimestamp()`.
- `[FOLLOWUP codex-2026-05-10-M5-epoch-docker-exec-propagation]` —
  propagate `EXTRACE_EPOCH_RUN_ID` through `executor/host.py` docker exec.
  Doğal yan ürün adayı W14-5 (logger consolidation + run-ID stamping);
  çekilmezse W15'e düşer.
- `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]` —
  align sync `/api/marketplace/analyze` error catch with async path. W15+.
- `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` **(W14-2)** —
  type-guard `automation_health` report-message conversion.
- `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]` —
  delete or fix orphan `clean_workspace()` symlink handling. W15+.
- `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` **(W14-3)** —
  redact network URI/path/summary fields; pair with M9.
- `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` **(W14-3)** —
  disable in-container CDP by default or require explicit opt-in.
- `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]` — W15+;
  cap UI event density/timeline spread operations.
- `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]` — W15+; cap relations
  graph nodes/edges.
- `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` **(W14-3)** —
  quote or validate Makefile operator variables.
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
- `[FOLLOWUP analysis-jobs-race]` **(W14-4)** — W13-4.4 documented the
  remaining `complete_analysis_job` race window; CRITICAL race surface.
- `[FOLLOWUP analysis-thread-supervisor]`
- `[FOLLOWUP job-service-typevar-audit]`
- `[FOLLOWUP sqlalchemy-error-subtype-logging]`
- `[FOLLOWUP w11-8-companion-workflow-orm-bleed]`

### Contracts / Reports / Detection

- `[BUG scenario-dropout-upstream-root-cause]` **(W14-1)** — BLOCKER triage;
  W14 entry-point iterasyonu.
- `[BUG silent-scenario-dropout-regression]`
- `[FOLLOWUP scenario-accountant-conservation-split]` — W14-1 kök neden
  tespitinden sonra ayrı pull adayı; W14-1 PR'ına dahil edilmez.
- `[FOLLOWUP evidence-event-kind-raw-context-invariant]` **(W14-4)** — test
  stub hazır: `test_evidence_event_rejects_kind_event_class_mismatch`.
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
