# Post-PoC Backlog

`Last Updated: 2026-05-07 (slimmed after audit pass; full detail archived)`

Open deferred work after the W0-W7 PoC acceptance bar. **Slim canonical** —
verbose descriptions, evidence, and older triage notes are frozen in dated
snapshots:

- latest full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-07.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-07.md)
- previous full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md)

W8, W9, W10, and W11 are closed. Active phase: **W12 executor
subpackaging + attribution cleanup**, tracked in
[`active-work/W12-executor-subpackaging.md`](active-work/W12-executor-subpackaging.md).

## Stable IDs Are A Contract

Do not rename existing IDs. Code/tests currently reference:

- `[FOLLOWUP analysis-jobs-race]`
- `[FOLLOWUP simulation-progress-cancel]`
- `[FOLLOWUP simulation-progress-cancel] cancel-after-finish race test`
- this filename from `packages/analysis_contracts/contracts.py`

Use stable IDs in new references; do not cite canonical doc line numbers.

## W12 Pull-Forward

- **`[FOLLOWUP w8-6-output-signals-file-backed-redaction]`** — **P1,
  W12-0, must land before W12-1.** W10-7 redacted the harness-marker
  output-signal path but missed the file-backed `read_output_channel_logs`
  path, the primary Output channel source on VS Code 1.105+. Pickup:
  apply `redact_secrets(_truncate(line))`, update the W10-7 comment to
  name both paths, and add a file-backed redaction regression.

## W12 Acceptance Items

- **`[FOLLOWUP w12-attribution-naming-overlap]`** — reconcile or rename
  `background_activation_count` vs `competing_candidate_count`.
- ~~**`[FOLLOWUP w12-precursor-tests-attribution-links]`**~~ — closed
  `2026-05-07` in commit `5ae0d32`; 26 link-helper cases landed.
- ~~**`[FOLLOWUP w12-precursor-tests-attribution-events]`**~~ — closed
  `2026-05-07` in commit `5ae0d32`; 34 event-helper cases landed.
- **`[FOLLOWUP w12-extension-host-split-scoping]`** — plan addendum
  closed by PR #15; implementation lands during W12 as the
  `runtime_capture/extension_host.py` ahtapot split.
- **`[FOLLOWUP coverage-summary-attempted-drift]`** — reduce attempted
  capability producer paths to one source of truth.
- **`[FOLLOWUP activation-discovery-strategy-outcome-detail]`** — P3
  read-side detail loss for per-strategy outcome reporting.

## Open Items By Area

### Workflow / Platform

- **`[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread`**
  — move sandbox reset out of the daemon heartbeat thread.
- **`[FOLLOWUP simulation-progress-cancel] dedupe-step-progress-schemas`**
  — reconcile `AnalysisJobStepProgress` vs `AnalyzeJobStepProgress`.
- **`[FOLLOWUP simulation-progress-cancel] is-job-cancelled-session-churn`**
  — revisit fresh DB session polling if profiling shows pressure.
- **`[FOLLOWUP simulation-progress-cancel] heartbeat-refactor`** — extract
  heartbeat polling/JSON/cancel logic into a testable helper.
- **`analysis_service._open_job_session`** — move `SessionLocal` import
  back to module top once the startup-cycle constraint is gone.
- **`run_analysis_job` exception narrowing** — replace broad handling with
  enumerated error paths where possible.
- **`[FOLLOWUP analysis-thread-supervisor]`** — keep daemon-job rows from
  sticking in `running` on unenumerated `BaseException`.
- **`[FOLLOWUP sqlalchemy-error-subtype-logging]`** — distinguish
  `IntegrityError`, `OperationalError`, and `ProgrammingError` for triage.
- **`search_marketplace` return typing** — tighten public return shape.
- **Domain service pattern expansion** — pull remaining router surfaces into
  the established domain-service shape.
- **Migration hardening** — `make migrate` destructive-op precheck plus
  Alembic reversibility audit.
- **`[FOLLOWUP job-service-typevar-audit]`** — keep or remove the generic
  `_run_in_session()` typevar based on mypy/readability value.
- **`[FOLLOWUP w11-8-companion-workflow-orm-bleed]`** — decide DTO
  migration vs documented boundary exception for workflow return types that
  expose storage ORM models.
- **`[FOLLOWUP w8-1-vsix-rejection-log-sanitization]`** — P2; sanitize
  attacker-controlled VSIX entry names before rejection logging.
  Co-tenant of `[FOLLOWUP w8-1-extract-rejection-logging]` (same call
  sites in `workflows/marketplace/client.py`); land jointly in one PR
  to avoid double-touch.

### Executor / Capture

- **T2/T3 live-security plumbing** — harden `make test-security-live`
  around real T2/T3 engagements.
- ~~**`[FOLLOWUP w11-precursor-tests]`**~~ — landed `2026-05-04`.
- ~~**`[BUG silent-scenario-dropout-regression]`**~~ — closed
  `2026-05-07`; last-mile conservation guard reports
  `unaccounted_dropout`.
- **`[BUG scenario-dropout-upstream-root-cause]`** — trace the planner /
  `stimulus_passes` / harness dispatch gap that still drops requested
  scenarios before they reach `ScenarioAccountant`.
- **`[FOLLOWUP monitor-types-property-recomputation]`** — P3; defer until
  profiling shows repeated expensive property access.

### Detection / Contracts

- ~~**`[FOLLOWUP report-invariants-runtime-evidence-drift]`**~~ — closed
  by W10-6.
- ~~**`[FOLLOWUP planner-executor-action-enum]`**~~ — closed by W10-5.
- ~~**`[FOLLOWUP w8-6-output-signals-redaction]`**~~ — parent closed by
  W10-7 for the harness-marker path; file-backed sibling remains W12-0.
- **`[FOLLOWUP signal-summary-needs-review-categories]`** — refine
  category labels for review-oriented verdicts.
- ~~**`[FOLLOWUP target-log-lifecycle-instrumentation]`**~~ — landed with
  W11-4.
- ~~**`[FOLLOWUP w8-6-extension-host-output-redaction]`**~~ — landed with
  the W11 companion.
- **`[FOLLOWUP event-attempt-verification-status-validator]`** — prevent
  drift in runtime-evidence state vocabulary.
- **`[FOLLOWUP compute-verdict-table-driven-test]`** — add table-driven
  coverage for verdict computation.
- **A5/A7 adversary fixtures and allow-list artifacts** — keep deferred
  until the relevant security window.

### UI

- ~~**`[CLEANUP ui-v3-9]`**~~ and ~~**`[CLEANUP ui-v3-14]`**~~ — closed.
- **`[FOLLOWUP ui-supplemental-types-retire]`** — retire supplemental UI
  type shims once generated contracts fully cover them.

### Engineering Quality

- **`[FOLLOWUP ci-reintroduction]`** — restore CI/docs-check after the
  runner-image drift is understood.
- **`[FOLLOWUP arch-gate-network-body-preview-redaction]`** — P2; AST gate
  ensuring body-preview assignments stay behind `redact_secrets`.

### Repo Hygiene

- ~~**`[CLEANUP repo-tracked-scratch-files]`**~~ — landed `2026-05-03`.
- ~~**`[CLEANUP tests-scanner-rename]`**~~ — landed `2026-05-03`.
- **`[CLEANUP report-builder-naming]`** — clarify similarly named report
  builder modules.
- **`[CLEANUP env-example-extrace-vars]`** — align example env names with
  runtime configuration.
- ~~**`[CLEANUP agent-context-phase-snapshot-stale]`**~~ — landed.
- **`[CLEANUP postgres-version-fact-drift]`** — keep documented Postgres
  version aligned with Compose/runtime.
- **`[CLEANUP adr-0007-runbook-wording-drift]`** — keep LAN runbook wording
  synchronized with ADR 0007.
- **`[CLEANUP session-docstring-except-exception]`** — update stale
  docstring language around exception handling.
- **`[CLEANUP uri-validation-stale-sys-path-comment]`** — remove stale
  package-mode comments after W9.
- **`[CLEANUP monitor-runtime-naming-overlap]`** — reduce naming ambiguity
  around monitor runtime modules.
- **`[CLEANUP appcore-config-stale-docstring]`** — replace legacy config
  module wording.
- **`[CLEANUP pre-commit-python-version-alignment]`** — align pre-commit
  Python version with the project/runtime target.
- ~~**`[CLEANUP httpx-runtime-dependency-metadata]`**~~ — verified closed
  `2026-05-06`.
- ~~**`[FOLLOWUP scripts-seed-test-rewrite]`**~~ — closed by file removal.
- ~~**`[FOLLOWUP triggers-private-helper-import]`**~~ — verified resolved.

### Test + Observability

- **`[FOLLOWUP w8-9-network-body-boundary-split-secret-test]`** — P2;
  cover secret patterns split by body-preview truncation.
- **`[FOLLOWUP codex-automation-5]`** — executor runtime fingerprint in
  automation output.
- **`[FOLLOWUP codex-automation-6]`** — UI failure taxonomy.
- **`[FOLLOWUP capability-verification-gap]`** — close remaining debug /
  verification capability gaps.
- **`[FOLLOWUP w8-0-capture-pipeline]`** — preserve capture-pipeline smoke
  coverage beyond the partial W8-0 close.
- ~~**`[FOLLOWUP make-test-security-lane-composition]`**~~ — full close
  recorded after W8 lane composition landed.
- **`[FOLLOWUP w8-4-broader-executor]`** — retire remaining bare-binary
  pragmas when executor helpers move to absolute paths.
- **`[FOLLOWUP w8-1-extract-rejection-logging]`**,
  **`[FOLLOWUP w8-1-archive-count-bypass]`**, and
  **`[FOLLOWUP w8-1-vsix-compressed-size-limit]`** — remaining W8-1 hardening
  and observability follow-ups.
- **`[FOLLOWUP w8-3-harness-js-scheme]`** — extend URI trigger hardening.
- ~~**`[FOLLOWUP w8-5-list-endpoint-name-filter]`**~~ — closed
  `2026-04-30`.
- **`[FOLLOWUP w8-6-content-sample-structural-test]`** — broader
  structural enforcement for content-sample redaction.
- **`[FOLLOWUP w8-8-manifest-emit-when-needed]`** — deferred until the
  first manifest-field log emit site or proactive security gate.
- ~~**`[FOLLOWUP arch-gate-no-bare-except]`**~~ — landed.
- **`[FOLLOWUP w8-8-trigger-sweep-as-test]`** — convert W8-8 trigger sweep
  into test coverage when W8-8 lands.
- **`[FOLLOWUP arch-gate-executor-control-outbound]`** — gate outbound
  executor-control boundaries.
- **`[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]`** — ratchet bare
  binary path pragmas as W8-4 follow-ups land.

## How To Pull An Item Back

1. Search by stable ID in this file and the latest full archive snapshot.
2. Confirm code/tests still match the recorded premise.
3. Add or update tests first when the item describes a regression risk.
4. Close by preserving the stable ID and adding the landing date/commit.
