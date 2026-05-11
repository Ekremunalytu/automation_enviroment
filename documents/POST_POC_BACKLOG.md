# Post-PoC Backlog

`Last Updated: 2026-05-11 (W13-6 opened — Codex M9 arguments_preview redaction extension in progress; factory-internal redaction at _bounded_arguments_preview(); M1 remains W13 acceptance-bar open; W13-5 closed prior)`

Open deferred work after the W0-W7 PoC acceptance bar. **Slim canonical** —
verbose descriptions, evidence, and older triage notes are frozen in dated
snapshots:

- latest full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-11.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-11.md)
- previous full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-07.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-07.md)

W8, W9, W10, W11, and W12 are closed. Active phase: **W13 test expansion +
observability**, tracked in
[`active-work/W13-test-expansion-observability.md`](active-work/W13-test-expansion-observability.md).

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
| `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]` | open | replace catastrophic multiline private-key regex with bounded scanner/window |
| `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]` | in progress as W13-6 | factory-internal redaction at `_bounded_arguments_preview()` + new replica architecture gate `tests/architecture/test_arguments_preview_redaction.py` (W12-5 pattern) |
| `[FOLLOWUP w13-3-close-pass-cancellation-test-hardening]` | closed via W13-4 | behavioral coverage + `analysis-job-stuck` runbook update |
| `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` | deferred | needs fresh-DB-per-test Alembic fixture |

## Codex Cloud Audit Backlog

### Post-W13 Candidates

- `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` —
  guard extension-controlled timestamps before `datetime.fromtimestamp()`.
- `[FOLLOWUP codex-2026-05-10-M5-epoch-docker-exec-propagation]` —
  propagate `EXTRACE_EPOCH_RUN_ID` through `executor/host.py` docker exec.
- `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]` —
  align sync `/api/marketplace/analyze` error catch with async path.
- `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` —
  type-guard `automation_health` report-message conversion.
- `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]` —
  delete or fix orphan `clean_workspace()` symlink handling.
- `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` —
  redact network URI/path/summary fields; pair with M9.
- `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` —
  disable in-container CDP by default or require explicit opt-in.
- `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]` —
  cap UI event density/timeline spread operations.
- `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]` — cap relations
  graph nodes/edges.
- `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` — quote or
  validate Makefile operator variables.
- `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]` — cap activation
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
- `[FOLLOWUP analysis-jobs-race]` — W13-4.4 documented the remaining
  `complete_analysis_job` race window; pull W14+.
- `[FOLLOWUP analysis-thread-supervisor]`
- `[FOLLOWUP job-service-typevar-audit]`
- `[FOLLOWUP sqlalchemy-error-subtype-logging]`
- `[FOLLOWUP w11-8-companion-workflow-orm-bleed]`

### Contracts / Reports / Detection

- `[BUG scenario-dropout-upstream-root-cause]`
- `[BUG silent-scenario-dropout-regression]`
- `[FOLLOWUP scenario-accountant-conservation-split]`
- `[FOLLOWUP evidence-event-kind-raw-context-invariant]`
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
- `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]`
- `[FOLLOWUP arch-gate-executor-control-outbound]`
- `[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]`
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
- `[FOLLOWUP codex-automation-5]`
- `[FOLLOWUP codex-automation-6]`
- `[FOLLOWUP capability-verification-gap]`
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
