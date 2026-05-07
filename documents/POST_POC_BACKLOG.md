# Post-PoC Backlog

`Last Updated: 2026-05-07` (W12 precursor-test gate items landed 2026-05-07; W12 prep PR carried §11.9.1 plan addendum and W12 tracker scaffold)

Open work items deferred from W0-W7 PoC scope. **Slim canonical** — full
verbose item descriptions, landed-evidence detail, and review triage
blocks are frozen under dated snapshots in `archive/backlog/` (latest:
[`archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md)).

PoC acceptance bar (`REFACTOR_OPTIMIZATION.md` §10.7) was met `2026-04-23`;
items below are value-add, not gates.

## Stable IDs Are A Contract

Test/code comments reference items here by stable ID
(e.g. `[FOLLOWUP simulation-progress-cancel]`). **Do not rename** existing
IDs; new items get fresh IDs. Where multiple sub-items share a parent ID
(`[FOLLOWUP simulation-progress-cancel] heartbeat refactor` vs
`[FOLLOWUP simulation-progress-cancel] is_job_cancelled session churn`),
the trailing phrase is part of the contract and must be preserved.

Inbound code references — keep these stable:

- `tests/platform/storage/test_analysis_jobs.py:183` →
  `[FOLLOWUP analysis-jobs-race]` (in-flight race gap)
- `tests/workflows/marketplace/test_router.py:2009` →
  `[FOLLOWUP simulation-progress-cancel]` parent
- `tests/workflows/marketplace/test_analysis_execution_helpers.py:238` →
  `[FOLLOWUP simulation-progress-cancel] cancel-after-finish race test`
  (LANDED 2026-04-27, evidence in archive + `REFACTOR_STATUS.md`)
- `packages/analysis_contracts/contracts.py:142` → filename mention
  (kararlı)

---

## External Review Integration Window (W8-W13)

Two external reviews landed `2026-04-24`:

- [`archive/reviews/claude_code_review.md`](archive/reviews/claude_code_review.md)
- [`archive/reviews/codex_project_review.md`](archive/reviews/codex_project_review.md)

Findings triaged into `REFACTOR_OPTIMIZATION.md §11` weekly split (W8
security hardening → W13 test expansion + observability). W8, W9, and
W10 are closed; the active tracker is
[`active-work/W11-monitor-lifecycle.md`](active-work/W11-monitor-lifecycle.md).
The W8 tracker is historical only:
[`active-work/W8-security.md`](active-work/W8-security.md).

W8 entry gate (`§11.1`) **MET as of 2026-04-27**; W8 closed for active
work `2026-04-29`. W9 closed `2026-05-04` via PR #9; W10 closed
`2026-05-04` via PR #11. Current closure state is owned by
`REFACTOR_STATUS.md`.

**Promoted into W8-W13** (no longer pull-next here): target activation
lifecycle (landed), `signal_policy.py` relocation → W9, `registry.py`
split → W10, `monitor_lifecycle.py` split → W11,
`executor/flows/playwright/` subpackaging → W12.

**Rejected from W8-W13** (stay here, see archive §11.12 for promotion
rationale): UI component split (7.3.1/7.3.2), axe-core, mypy strict
promotion, documentation consolidation, monorepo tooling migration,
async executor runtime refactor, OpenAPI frontend client generation.

---

## Open Items By Area

Items are listed with stable ID + short trigger. Detail (file refs,
acceptance criteria, surfaced-by review §) lives in archive — open it
when picking an item up.

### Workflow / Platform

- **`[FOLLOWUP runner-status-contract]`** *LANDED with W11-3
  `2026-05-04`*. First-class `ActivationReport.runner_exit_code` (`int |
  None`) + `runner_status` (`RunnerStatusLiteral`) live on the contract;
  `ReportAssembler.set_runner_status` owns the (exit_code → status)
  mapping; `entrypoint_runner` invokes the facade shim immediately
  before the final `report.save()`. Surfaced by 2026-04-25
  supplementary review (Codex "Runner exit status semantics").
- **`[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread`**
  `_heartbeat_on_cancel()` calls `executor_control.reset_sandbox`
  synchronously from the daemon heartbeat; spin reset on a worker.
- **`[FOLLOWUP simulation-progress-cancel] dedupe-step-progress-schemas`**
  `AnalysisJobStepProgress` vs `AnalyzeJobStepProgress` — pick canonical
  or document the deliberate split.
- **`[FOLLOWUP simulation-progress-cancel] is-job-cancelled-session-churn`**
  `job_service.py:308` opens a fresh DB session every 5 s; fold into a
  longer-lived session if profiling shows pressure.
- **`[FOLLOWUP simulation-progress-cancel] heartbeat-refactor`**
  Lift `_run_monitoring_heartbeat` cancel/poll/JSON-read mix into
  `MonitoringHeartbeat` helper for unit-testability.
- **`analysis_service._open_job_session`** — move `SessionLocal` import
  back to module top (7.1.2; inlined to break startup cycle).
- Narrow the broad `except` in `run_analysis_job` (7.1.4).
- **`[FOLLOWUP analysis-thread-supervisor]`** Structural complement to
  7.1.4: wrap the daemon-thread `target` (`router.py:186` →
  `run_analysis_job`) in a `BaseException`-catching supervisor that always
  calls `job_service.fail_job(job_id, reason=str(exc))` before re-raising,
  so future un-enumerated exception types cannot leave the row in
  `running`. AGENTS.md exception for the broad catch documented at the
  supervisor site only. Surfaced by 2026-04-29 audit pass.
- **`[FOLLOWUP analysis-thread-error-detail-leakage]`** — *CLOSED
  2026-05-03 on `feat/w9-executor-detection-boundary`* (W8-7
  LAN-exposure trigger). `analysis_service.map_executor_error()`
  redacts paths/env from public HTTP detail, suffixes an 8-char
  `error_id`, retains raw text in `logger.warning`. Regression:
  `tests/workflows/marketplace/test_router.py::
  test_map_executor_error_redacts_internal_paths_and_env`. Detail in
  `archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md`.
- **`[FOLLOWUP sqlalchemy-error-subtype-logging]`**
  `appcore/storage/crud_ops/analysis_jobs.py` (and the wider `crud_ops/`
  surface) catches `SQLAlchemyError` broadly without distinguishing
  `IntegrityError` (constraint), `OperationalError` (connection), or
  `ProgrammingError` (schema). Distinguish for incident triage; rolling
  back/raising semantics stay the same.
- Tighten `search_marketplace` return type (7.1.5).
- Pull "domain service" pattern into remaining router surfaces (2.8).
- `make migrate` pre-check for destructive Alembic operations (7.4.6);
  Alembic reversibility audit (7.4.7).
- **`[FOLLOWUP job-service-typevar-audit]`** —
  `workflows/marketplace/job_service.py:48` declares `T = TypeVar("T")`;
  immediate re-check found it is used by `_run_in_session()` to preserve
  the return type of `Callable[[Session], T]`. Treat as low-priority:
  keep if mypy/reader clarity benefits from the generic, or remove only
  if the helper is simplified. Surfaced by 2026-05-04 audit pass.
- **`[FOLLOWUP scripts-seed-test-rewrite]`** — *LANDED-via-deletion
  (verified 2026-05-05 audit pass)*. `scripts/seed_test.py` no longer
  exists in the tree; current `scripts/` contents are
  `demo_acceptance.py`, `generate_ui_contracts.py`, and
  `check_ui_boundaries.mjs`. The four hard-rule violations the
  original report enumerated (`sys.path.insert` at `:55`, raw ORM
  `Extension(...)` at `:119` bypassing Pydantic, `db.add` at `:154`
  bypassing CRUD facade, generic `except Exception` at `:164`) are all
  closed by the file's removal. Surfaced 2026-05-04, verified-deleted
  2026-05-05.
- **`[FOLLOWUP triggers-private-helper-import]`** — *RESOLVED 2026-05-05
  (already satisfied; no code change needed)*. Audit verified
  `workflows/marketplace/triggers.py:3` already imports the public
  alias `glob_to_bait_filename` from the `packages.analysis_planner`
  package root (re-exported via `packages/analysis_planner/__init__.py:7,25`);
  no `_glob_to_bait_filename` private import exists. The original
  drift report assumed a private helper import that the W10-3 planner
  split had already made public via the package root. ADR 0005 §3 not
  violated. Surfaced 2026-05-04, verified-resolved 2026-05-05 audit
  pass.
- **`[CLEANUP httpx-runtime-dependency-metadata]`** — *LANDED-via-prior-edit
  (verified 2026-05-06 audit pass)*. `httpx>=0.27.0,<1.0.0` now lives at
  `pyproject.toml:24` inside `[project].dependencies`; absent from
  `[project.optional-dependencies].dev` (`:28-36`). Stable ID retained for
  inbound code/test references. Original surfacing context preserved:
  `httpx` is imported in production at `workflows/marketplace/{client,router}.py`
  and installed by `docker/api/requirements.txt:9`; the metadata fix moved
  it to base dependencies — no new dep. Surfaced 2026-05-04 second-pass
  review; verified-resolved 2026-05-06 audit pass.
- **`[FOLLOWUP w11-8-companion-workflow-orm-bleed]`** —
  `workflows/extension_catalog/service.py:50-57` imports six storage
  ORM models (`Extension`, `ExtensionActivationEvents`,
  `ExtensionCapabilities`, `ExtensionContributes`,
  `ExtensionContributesCommands`, `ExtensionScripts`) from
  `appcore.storage.models` and uses them as public function return
  types (`:172, 199, 228, 282, 309, 380, 400, 418, 435, 454, 466`).
  FastAPI `response_model` auto-converts to Pydantic on the way out
  (docstring `:244-279` documents the pattern as intentional). AGENTS
  rule 2 not violated — writes still go through
  `appcore/storage/crud.py` — but workflow layer carries storage
  internals as a public surface, blurring the boundary. Sister site
  `workflows/marketplace/job_service.py:44` is *not* in scope: there
  `AnalysisJob` is type-hint-only inside the private
  `_persisted_snapshot`/`_public_snapshot` helpers; all public
  functions return `dict[str, Any]`. Pickup: decide DTO migration
  (`ExtensionReadSchema` in `appcore/contracts/schemas.py`) vs
  documenting the auto-conversion pattern as a boundary exception in
  `documents/agent-lanes/platform-storage.md`. **No new
  repository/service abstraction layer** unless it removes a concrete
  current coupling. Natural landing: W11-8 companion (parallel to the
  `crud_ops/analysis_jobs.py` split, not the same scope). Surfaced
  2026-05-05 (Codex review #2, audit pass refined framing).

### Executor / Capture Hygiene

- **T2 declawed samples + T3 handling** + `make test-security-live`
  hardening — ADR 0004 covers policy; operational plumbing waits on
  real T2 engagement.
- **`[FOLLOWUP w11-precursor-tests]`** — *LANDED 2026-05-04* on the W11
  prep branch. Two playwright god-modules now have direct module-owned
  test coverage so the W11 lifecycle split (`§11.8`) and W12
  subpackaging (`§11.9`) cannot regress public behavior through
  facade/integration coverage alone:
  `tests/executor/test_playwright_extension_host.py` (23 cases —
  pins `parse_activations_from_output`, `parse_activations_from_log`,
  `parse_strace_process_event_line`, `find_exthost_logs`,
  `parse_all_exthost_logs`, `read_extension_host_output`,
  `ExtensionHostFileCapture` initial state) covers
  `executor/flows/playwright/runtime_capture/extension_host.py`
  (679 LOC); `tests/executor/test_playwright_health_reconciliation.py`
  (15 cases — pins the W10-6 frozenset state machine
  {`failed`, `blocked`, `verified`, `activation_seen`, `target_log_seen`,
  `attempted_only`} including the harness-unverified path, plus
  `reconcile_coverage_verification` matrix shape) covers
  `executor/flows/playwright/health_reconciliation.py` (533 LOC).
  Both files import their target module by its real path (not via the
  `monitor` facade) so the W11 facade re-export rearrangement cannot
  silently drift. Surfaced by 2026-05-04 audit pass.
- **`[FOLLOWUP w12-attribution-naming-overlap]`** —
  `attribution_summary.background_activation_count` and
  `attribution_summary.competing_candidate_count` describe overlapping
  populations but the values diverge by orders of magnitude. Observed
  2026-05-04 manual UI scan with 25 unique extensions / 22 activations
  / 1 target: `background_activation_count: 0` while
  `competing_candidate_count: 54`. Reconcile category definitions (or
  rename one) so operators can reason about non-target activity from
  the report alone. Natural landing: W12 attribution facade cleanup
  (`§11.9`). Surfaced by 2026-05-04 manual UI scan.
- ~~**`[FOLLOWUP w12-precursor-tests-attribution-links]`**~~ —
  closed by commit `5ae0d32` on the
  `feat/w12-precursor-tests-attribution` branch (`2026-05-07`).
  `tests/executor/test_playwright_attribution_links.py` lands 25
  cases pinning `_temporal_confidence`, `_dedupe_evidence_links`,
  `_nearest_activation`, the four `_build_*_links` builders
  (scenario / temporal / duplicate-file / noise) and a smoke test for
  the `_build_evidence_bundle` orchestrator. Imported at the real
  module path (not via `attribution.__init__`) so the W12-2 facade
  rework cannot silently regress the bound surface. Stable ID
  retained for inbound code/test references.
- ~~**`[FOLLOWUP w12-precursor-tests-attribution-events]`**~~ —
  closed by commit `5ae0d32` on the
  `feat/w12-precursor-tests-attribution` branch (`2026-05-07`, same
  commit as the links sibling).
  `tests/executor/test_playwright_attribution_events.py` lands 35
  cases pinning the timestamp/actor/artifact-class helpers, the five
  `_classify_event_attribution` branches (inotify short-circuit /
  missing target_id / strace tight-window 0.93 / competing demote /
  network far-window near_target), `_upgrade_inotify_correlations`
  paired-strace upgrade, and shape-level pins for the three
  `_annotate_*_events` annotators. Imported at the real module path
  so the W12-2 facade rework cannot silently regress. Stable ID
  retained for inbound code/test references.
- **`[FOLLOWUP w12-extension-host-split-scoping]`** —
  `executor/flows/playwright/runtime_capture/extension_host.py`
  (679 LoC) is the largest single source file in the executor flow
  tree. It owns three independent capture sources (exthost.log
  parser, strace text-mode line parser, harness output capture +
  `ExtensionHostFileCapture` class). `REFACTOR_OPTIMIZATION.md
  §11.9` W12 plan describes a 5-subpackage shape ({monitor, stimulus,
  workspace, health, entrypoint}/) but does not name this file
  specifically; the runtime_capture/ tree's split target is
  ambiguous. Pickup (plan-level work, no code change in the first
  PR): add a subsection to `§11.9` body proposing a 3-way split
  (`extension_host_log_parse.py` ~200 LoC,
  `extension_host_strace_parse.py` ~200 LoC,
  `extension_host_capture.py` ~250 LoC) plus re-export facade.
  `[FOLLOWUP w11-precursor-tests]` (LANDED 2026-05-04, 23-case net)
  is the safety floor for the eventual split. Surfaced 2026-05-05
  audit pass.

### Detection / Contracts

- A5 + A7 adversary-class T1/T2 canary + rule (stretch).
- Allow-list (`benign_domains.txt`, `popular_extensions.txt`) versioned
  data artifact promotion.
- Domain service pattern genişletmesi (2.8 — W7'de ertelendi).
- ~~**`[FOLLOWUP report-invariants-runtime-evidence-drift]`**~~ —
  closed by W10-6 (`c1d58ef`, `2026-05-04`). The
  `RUNTIME_EVIDENCE_STATES` frozenset in
  `packages/analysis_contracts/report_invariants.py` now pins the
  broader `{attempted_only, activation_seen, target_log_seen,
  verified, failed}` set; the contract and runtime helpers share it.
  Stable ID retained for inbound code/test references; see
  `REFACTOR_STATUS.md` W10 entry.
- ~~**`[FOLLOWUP planner-executor-action-enum]`**~~ — closed by
  W10-5 (`b312d34`, `2026-05-04`). `validate_executor_action` and
  `EXTRA_EXECUTOR_ACTIONS` live in
  `packages/analysis_contracts/executor_actions.py`; executor
  dispatch over raw action strings is now guarded by the enum and
  becomes total. Stable ID retained for inbound code/test
  references; see `REFACTOR_STATUS.md` W10 entry.
- ~~**`[FOLLOWUP w8-6-output-signals-redaction]`**~~ — closed by
  W10-7 (`c1e2273`, `2026-05-04`). Extension-controlled text surfaces
  (`OutputSignalEvent.text`, executor stderr/stdout tail in
  `analysis_execution.py`, `map_executor_error` exception text) are
  routed through `redact_secrets` at construction; regression pinned
  by `tests/platform/security/test_output_signals_redaction.py`.
  Stable ID retained for inbound code/test references; see
  `REFACTOR_STATUS.md` W10 entry.
- **`[FOLLOWUP coverage-summary-attempted-drift]`** —
  `coverage_summary.attempted_capabilities` (7 entries including
  `uri_walkthrough`), the parallel `summary.attempted_capabilities`
  alongside top-level `attempted_capabilities` (6 entries, no
  `uri_walkthrough`), and `event_attempts[]` (zero attempts of
  `uri_walkthrough` family) all describe the same run's attempted
  capabilities but disagree. Producer paths diverge — likely
  `analysis_planner.coverage` vs the reconcile path under
  `executor/flows/playwright/health_*`. Reduce to a single source so
  UI components reading either alias see the same number. Natural
  landing: W12 attribution cleanup (`§11.9`); pull earlier as a
  surgical fix if any UI surface reads both fields and renders
  diverging counts. Surfaced by 2026-05-04 manual UI scan;
  re-observed 2026-05-05 manual UI scan
  (`activation_report_ms-python.python-2026.5.2026042602-c0c4f270030c.json`).
- **`[FOLLOWUP activation-discovery-strategy-outcome-detail]`** —
  `ActivationReport.activation_discovery_strategies` lists only the
  strategies that succeeded *and* contributed at least one new
  activation (`executor/flows/playwright/monitor_runtime_state.py`
  appends to `succeeded_strategies` only when
  `len(self._report.activated) > pre_merge_count` for Strategy 3, and
  on raw success for Strategies 1/2). Strategies that ran cleanly but
  contributed no novel activation (the second/third attempt sees a
  superset already populated by an earlier strategy) and strategies
  that raised a caught exception both end up *absent from the
  persisted list with no per-strategy outcome record*. Observed
  2026-05-05 manual UI scan: a 22-activation ms-python.python run
  lists `["exthost_log_parse", "running_extensions_ui"]` only — no
  signal whether `exthost_output_parse` ran-and-was-redundant,
  ran-and-failed, or never reached. Reduces diagnostic value when an
  analyst tries to explain a low `target_activation_count` or
  unattributed events. Pickup options: extend to `dict[str, str]`
  (`{strategy: outcome}` with literals like
  `"succeeded_with_new_activations" / "succeeded_no_new_activations"
  / "failed:<exc-class>"`) — or keep the current shape and add a
  parallel `activation_discovery_diagnostics` field for the failed /
  redundant cases. Tied to the W11-3 producer surface (where the
  field landed) but the read-side detail loss is W12 attribution
  cleanup territory (`§11.9`). **Priority: P3.** Surfaced 2026-05-05
  manual UI scan.
- **`[FOLLOWUP target-log-lifecycle-instrumentation]`** — **LANDED with
  W11-4 `2026-05-05`** (commit `f4f5df6` on the `week11` working
  branch). The producer-side gap closed:
  `ScenarioAccountant.emit_intermediate_state_events` runs after
  `reconcile_event_attempts` and emits an `automation`-stream
  `event_attempt` log entry for every attempt whose
  `verification_status` reached `activation_seen` or
  `target_log_seen` (idempotent per-attempt via
  `_emitted_intermediate_state_attempts`). Wired into
  `MonitorRuntime.stop()` after `refresh_derived_state` so emissions
  reflect the post-reconcile truth; runtime callback routed through
  the `ExtensionMonitor._emit_intermediate_state_events` shim so the
  W11-1/2/3 facade pin file's bound-method-identity invariants stay
  green. Positive path pinned by
  `tests/executor/test_playwright_monitor_scenario_accountant.py`
  (`test_emit_intermediate_state_events_emits_for_activation_seen`,
  `…_for_target_log_seen`, `…_emits_per_promoted_attempt`). The
  consumer-side broadening of target log capture (so
  `log_streams.target_extension_host` does not collapse to 1 entry
  per 22-activation run) stays open as a separate W12 reconciler
  workstream — distinct from the producer-signal closure W11-4
  shipped. Surfaced 2026-05-04; producer side closed 2026-05-05.
- **`[FOLLOWUP signal-summary-needs-review-categories]`** —
  `signal_summary.level` can land on `"needs_review"` with
  `score>0` while `risk_signals == []` and
  `risk_summary.categories == []`. Observed 2026-05-04 manual UI scan:
  `level=needs_review`, `score=22`, single human-readable reason in
  `signal_summary.note` (`"Sensitive file activity exists near target
  activations, but attribution is only correlative."`) but no
  structured category for the UI to badge. Either populate
  `risk_summary.categories` from the `signal_summary` derivation path
  or downgrade the level to a more honest `"inconclusive"` when no
  risk signal supports it. Tied to ADR 0003 verdict rollup semantics
  — `§11` brief flagged ADR 0003 changes as W10 non-goal; natural
  landing is W13+ external-review window where verdict semantics can
  be revised holistically. Surfaced by 2026-05-04 manual UI scan.
- **`[FOLLOWUP w8-6-extension-host-output-redaction]`** — *LANDED on
  `week11` `2026-05-05`* as the P1 W11 companion before the next
  structural pull. `executor/flows/playwright/report_builder.py::build_report_data`
  now applies a **trim-then-expand-then-redact** pipeline: the
  500-line tail window is computed on the **raw** Extension Host
  line stream first, the start index walks backwards to include any
  ``-----BEGIN PRIVATE KEY-----`` marker whose matching ``END`` falls
  inside the retained tail (private helper
  `_expand_window_for_orphaned_pem`), and `redact_secrets(...)`
  (imported from `packages.analysis_contracts`) is applied once on
  the resulting window. **Two layered invariants**: (1) the
  `private_key` pattern in `packages.analysis_contracts.evidence`
  matches the `-----BEGIN ... PRIVATE KEY-----` …
  `-----END ... PRIVATE KEY-----` span as a unit, so a naïve
  trim-then-redact would leave an orphaned body unmatched and persist
  raw key bytes — the BEGIN-expansion step closes that hole. (2) An
  earlier redact-then-trim version (Codex review #2, `2026-05-05`)
  fixed (1) but introduced a *tail-window inflation* attack: an
  extension that wraps thousands of attacker-controlled
  `console.log` lines in fake `BEGIN/END PRIVATE KEY` markers would
  see the redaction collapse the span to a single token, slip the
  500-line cap (computed on redacted lines), and leak older head
  lines into the persisted artifact (Codex review #3,
  `2026-05-05`); anchoring the cap to raw lines closes that hole.
  Regression suite
  `tests/platform/security/test_extension_host_output_redaction.py`
  (20 cases) covers four of the five `SECRET_CLASSES`
  (`aws` / `bearer` / `db_url` / `api_key`) via parametrize plus the
  multi-line `private_key` class via dedicated PEM cases. Pins both
  the dict-emission boundary and the on-disk JSON byte form — AKIA +
  Bearer + Postgres DSN samples flowed through `build_report_data`
  produce `[REDACTED:aws]` / `[REDACTED:bearer]` / `[REDACTED:db_url]`
  while raw token bytes are absent both from the emitted dict and
  from `tempfile`-backed `json.dumps` round-trips; the orphaned-PEM
  scenario gets its own byte-form pin so a future encoding change
  cannot silently re-leak the key body. **Three orphaned-PEM cases
  pin the BEGIN-expansion invariant**
  (BEGIN-outside-tail body-inside-tail, fully-inside-tail,
  fully-outside-tail) plus tail-window assertions on the
  body-inside-tail case so attacker-controlled head lines do not
  ride the collapse past the cap. **Tail-window inflation pin**
  (`test_extension_host_output_tail_window_resists_pem_collapse_inflation`):
  800 attacker-controlled prefix lines + 5000-line synthetic PEM
  body + 100-line suffix; asserts no `attacker prefix N` reaches the
  persisted dict while `benign suffix N` (inside the original raw
  tail) does. **`extension_host_output_lines` metric pin**: the
  field counts raw newlines from the original capture, not the
  redacted text — pinned with a 22-line PEM payload that collapses
  to a 1-line redacted form, asserting the metric still reports the
  raw count. **Composition pin**: a mixed AWS + Bearer + DB URL +
  api_key + PEM buffer asserts every class is redacted without one
  pattern consuming text another needed and benign framing lines
  survive. Idempotency, benign-payload preservation, and the
  500-line tail-truncation interaction case pin the no-drift
  invariants. `tests/platform/security/test_content_sample_typing.py`
  `_PENDING_MIGRATION` extended with `(ActivationReport,
  "extension_host_output")` so the W13 contract-level migration prompt
  flips the test surface XPASS → fail when the field flips to
  `ContentSample`. No schema migration shipped (string shape unchanged;
  only content filtered). W13 `§11.10` owns the contract-layer lock-in
  (flip `extension_host_output: str` → `ContentSample` so redaction is
  enforced by the type rather than the producer). Verification:
  `make test-security` 190 cases green, `make check-all` 1222 passed.
  Original surfacing context preserved for W13 reference:
  `executor/flows/playwright/report_builder.py:237-241,343` writes
  the last 500 lines of raw Extension Host log into
  `ActivationReport.extension_host_output`
  (`packages/analysis_contracts/contracts.py:422`, plain `str = ""`).
  No `redact_secrets()` call in the chain. Extension `console.log`
  output, `OutputChannel.appendLine` writes, runtime exception stacks
  carry AKIA tokens / bearer headers / Postgres DSNs straight to
  disk. Sister to `[FOLLOWUP w8-6-output-signals-redaction]` (closed
  by W10-7; covered output_signals.py / analysis_execution.py /
  analysis_service.py but did **not** name `extension_host_output`)
  and `[FOLLOWUP w8-6-content-sample-structural-test]` (broader sweep
  parent). **Priority: P1.** Surfaced 2026-05-05 (Codex review #1,
  audit pass); reviewer-flagged orphaned-PEM regression caught
  2026-05-05 (Codex review #2, BEGIN-expansion invariant); reviewer-
  flagged tail-window inflation regression caught 2026-05-05 (Codex
  review #3, raw-line cap invariant); closed 2026-05-05.
- **`[FOLLOWUP event-attempt-verification-status-validator]`** —
  `EventAttemptRecord.verification_status: str = "not_attempted"`
  (`packages/analysis_contracts/contracts.py:216`) carries the W10-6
  alphabet (`{not_attempted, attempted_only, activation_seen,
  target_log_seen, verified, failed, blocked}`) but is plain `str`
  with no Pydantic validator. Sibling `status` field (`:212`) is
  pinned to `EVENT_ATTEMPT_LIFECYCLE_STATES` frozenset via
  `field_validator` (`:225-233`). Producer typo (e.g. `"target_seen"`
  vs `"target_log_seen"`) round-trips cleanly through the contract;
  the runtime-evidence helper set is now shared through
  `packages.analysis_contracts.report_invariants.RUNTIME_EVIDENCE_STATES`,
  so this is not a current report-invariant drift bug; the remaining
  gap is that `verification_status` itself accepts arbitrary strings.
  A producer typo silently round-trips through the contract and can
  confuse downstream health/report interpretation. Pickup: add
  `EVENT_ATTEMPT_VERIFICATION_STATES: frozenset[str]` next to
  `EVENT_ATTEMPT_LIFECYCLE_STATES` (`:179`); add
  `@field_validator("verification_status")` mirroring `_validate_status`
  shape; 8-10 case test (each valid value + 2 invalid + casing +
  `None` handling). `[FOLLOWUP report-invariants-runtime-evidence-drift]`
  is already closed by W10-6; this validator is its strictly-narrower
  follow-up rather than a re-open of that older item. Natural landing:
  W11-companion (before W11-5 facade collapse so the contract
  guarantee sits under the new facade). **Priority: P1.** Surfaced
  2026-05-05 audit pass.
- **`[FOLLOWUP compute-verdict-table-driven-test]`** —
  `packages/analysis_contracts/detection/rollup.py::compute_verdict`
  is the ADR 0003 verdict rollup core. Existing
  `tests/platform/contracts/test_verdict_rollup.py` covers the main
  rollup branches, but the audit did not find an explicit
  `(severity, confidence)` cross-product table. Pickup: first verify
  whether a cross-product table already exists under a different name;
  if not, add `tests/platform/contracts/test_compute_verdict_table.py`
  with severity ∈ `{low, medium, high, critical}` × confidence ∈
  `{low, medium, high}` cross-product (12 case minimum), expected
  verdict (`clean` / `suspicious` / `malicious` / `inconclusive`)
  cited from ADR 0003 in test docstring. If the table exists, mark
  this item LANDED-already and close. Natural landing: W13 test
  expansion + observability (`§11.10`). Surfaced 2026-05-05 audit
  pass.

### UI

UI v3 redesign minimal-completion landed `2026-04-29` (see
`REFACTOR_STATUS.md`). Open follow-ups:

- **`[BACKLOG ui-v3-1]` … `[BACKLOG ui-v3-8]`** — pre-minimal-completion
  backend gaps (rule-save endpoint scaffolding, contract drift edges).
- **`[BACKLOG ui-v3-13]`** rule-save endpoint (post-minimal-completion).
- **`[CLEANUP ui-v3-9]`** orphan v3 component prune (LANDED 2026-04-28).
- **`[CLEANUP ui-v3-14]`** `design_handoff_extrace_console/` retired
  (LANDED 2026-04-29).
- **`[ADD ui-v3-10/11/12]`** Inspector drawer + RuleDraftSection on
  Reports, Run health + Coverage summary on Simulation, Ledger Scenario
  tab (LANDED 2026-04-28).
- **`[FOLLOWUP ui-supplemental-types-retire]`** —
  `scripts/generate_ui_contracts.py:115` ships a hardcoded
  `SUPPLEMENTAL_TYPES` TypeScript string for `AutomationHealthDto`,
  `LogHealthDto`, `AttributionSummaryDto`, `RiskSummaryDto`,
  `CoverageSummaryDto`, `CoverageCapabilityDto`, `CoverageTrackDto`,
  `CoverageTracksDto`, `EventCoverageDto`, and `LogStreamsDto` instead
  of introspecting the Pydantic models. `make ui-types-check` cannot
  detect drift because the template is the source of truth on both
  sides of the `--check` comparison. W10-4's three new
  `AutomationHealth` fields (`extension_host_log_found`,
  `extra_trigger_failures`, `extra_trigger_failure_count`) silently
  went missing on the TS side until manual W10 QA caught it. Migrate
  `AutomationHealthDto` and `CoverageSummaryDto` (at minimum) into the
  Pydantic introspect path so future field additions surface through
  `make ui-types-check`. Natural landing: W13 test expansion +
  observability. Surfaced by 2026-05-04 W10 QA pass.
- UI component split (7.3.1, 7.3.2, 7.3.3, 7.3.4, 7.3.5) + axe-core —
  surface not stabilized; rejected from W8-W13.

### Engineering Quality

- mypy strict promotion (rejected from W8-W13; revisit W13 sonrası).
- Monorepo tooling migration (uv / poetry).
- OpenAPI frontend client generation.
- Documentation consolidation pass (`REFACTOR_STATUS` /
  `REFACTOR_EXECUTION_PLAN` / `REFACTOR_OPTIMIZATION` dedupe) —
  living-doc cadence not settled yet.
- **`[FOLLOWUP ci-reintroduction]`** — `ci.yml` and `docs-check.yml`
  workflows were retired on `2026-04-30` after persistent flakiness in
  the `security-fixtures` job (iptables egress sandbox on GitHub
  runners). Local equivalents (`make check-all`, `make test-security`,
  `make test-local`, plus the new `pre-push` pre-commit stage) cover
  the same checks. `security.yml` (weekly Trivy + Bandit) was kept.
  Reintroduce a remote pipeline if any of the following triggers fire:
  (a) a second contributor joins, (b) PyPI/Docker-registry release
  starts, (c) T2 fixtures land that genuinely need ambient egress
  isolation. Before reintroduction, diagnose the original
  `security-fixtures` breakage (likely runner-image iptables / sudo
  drift) so the new lane does not inherit the same flake. See ADR 0004
  addendum (2026-04-30).

### Repo Hygiene (surfaced 2026-04-29 audit pass)

- **`[CLEANUP repo-tracked-scratch-files]`** — *LANDED 2026-05-03 on
  `feat/w9-executor-detection-boundary`*. `problems.md` + `todo.md`
  untracked + `.gitignore`'d (root scope); canonical status owned by
  `REFACTOR_STATUS.md` + `automation_todo.md`.
- **`[CLEANUP tests-scanner-rename]`** — *LANDED 2026-05-03 on
  `feat/w9-executor-detection-boundary`*. `git mv tests/scanner
  tests/executor/scanner` (34 tests preserved); no inbound imports
  to update. pytest collection unchanged.
- **`[CLEANUP report-builder-naming]`** — Two "report" modules with
  similar names live in different layers:
  `executor/flows/playwright/report_builder.py` (in-container, builds
  the on-disk `ActivationReport`) and
  `workflows/marketplace/analysis_reports.py` (host, loads + validates
  reports from disk). A grep for "report builder" or "analysis report"
  matches both and confuses navigation. Rename one when convenient
  (suggest `analysis_reports.py` → `report_loader.py` since its job
  is read-side); keep cosmetic, not urgent.
- **`[CLEANUP env-example-extrace-vars]`** — Two operator-relevant
  `EXTRACE_*` env vars are read in code but absent from `.env.example`:
  `EXTRACE_VSCODE_SETTINGS_JSON`
  (`executor/flows/playwright/settings.py:42`, settings override) and
  `EXTRACE_SKIP_JOB_RECOVERY` (`main.py:28`, boot-time job-recovery
  toggle). `EXTRACE_ALLOW_LAN` is documented; these two are not.
  `EXTRACE_EPOCH_RUN_ID` is internal — set by
  `executor/container/start.sh:25-26` — and stays undocumented.
  Append commented entries with one-sentence purpose strings.
  Surfaced by 2026-05-04 audit pass.
- **`[CLEANUP agent-context-phase-snapshot-stale]`** — *LANDED
  2026-05-04 on `feat/w10-contract-hygiene`*. Refreshed `AGENTS.md`
  Current State + `AGENT_CONTEXT.md` Source-of-Truth list to current
  phase (W8 closed `2026-04-29`, W9 closed `2026-05-04`, W10 in
  flight on `feat/w10-contract-hygiene`); ADR 0007 documented as
  implemented (W8-7 landed). The W8 tracker is preserved with a
  "past tracker" framing because code/tests still reference items
  by stable W8-N IDs.
- **`[CLEANUP postgres-version-fact-drift]`** — `docker-compose.yml:3`
  runs `image: postgres:16-alpine`, while external audit prompts /
  project-fact handoffs have still referenced PostgreSQL 15. Current
  repo docs searched in the 2026-05-04 pass did not show a live
  PostgreSQL 15 claim, and README already states PostgreSQL 16.
  Compose is ground truth for runtime; keep future prompts/handoffs
  aligned with PG 16 unless compose is intentionally pinned back.
  Surfaced by 2026-05-04 second-pass review.
- **`[CLEANUP adr-0007-runbook-wording-drift]`** —
  `documents/adrs/0007-local-network-binding.md:86` says a compose
  selector substitutes the wildcard binding when `EXTRACE_ALLOW_LAN=1`
  is set; `documents/runbooks/lan-exposure.md:91` says the operator
  must edit `docker-compose.yml` ports manually. Code is on the safer
  side (compose binds `127.0.0.1:` literally and post-init only
  swaps API HOST to `0.0.0.0` inside the process), but the two docs
  describe different operator paths. Reconcile wording. Surfaced by
  2026-05-04 second-pass review.
- **`[CLEANUP session-docstring-except-exception]`** —
  `appcore/db/session.py:137` is a docstring example that teaches
  `except Exception: db.rollback()` as the canonical session
  pattern, even though AGENTS rule 6 forbids it in production code.
  Not executable (lives inside a string node, invisible to
  `ast.parse`), so the now-landed
  `tests/architecture/test_no_bare_except_exception.py` gate skips
  it. Still misleading for future authors. Replace the docstring
  example with narrow exception types (`SQLAlchemyError`,
  `IntegrityError`). Surfaced 2026-05-04; gate-relationship clarified
  2026-05-05 audit pass.
- **`[CLEANUP uri-validation-stale-sys-path-comment]`** —
  `executor/flows/playwright/uri_validation.py:21-26` comment block
  asserts the module runs as a path-based script with
  `sys.path` injection. False post-W9-3 / ADR 0008 §1: W9-3 removed
  6 `sys.path.insert` calls from the runtime tree, the AST gate
  `tests/architecture/test_import_graph.py::test_no_sys_path_manipulation_in_runtime`
  forbids re-introduction, and `test_container_entrypoint.py`
  smoke-pins package-mode invocation. The stale comment justifies a
  duplicate `XDG_OPEN_PATH = "/usr/bin/xdg-open"` literal whose
  host-side mirror lives at `executor/binary_paths.py:20`; two
  sources of truth for the same constant (current invariant
  `tests/executor/test_absolute_paths.py` checks they match — this
  invariant becomes redundant after consolidation). Pickup: update
  or delete the stale comment; replace inline literal with
  `from executor.binary_paths import XDG_OPEN_PATH`; simplify or
  delete the absolute-path invariant. Natural landing: W11-companion
  (any time, ~10 LoC code change). Surfaced 2026-05-05 audit pass.
- **`[CLEANUP monitor-runtime-naming-overlap]`** —
  `executor/flows/playwright/monitor_runtime.py` (554 LoC, original
  helper for runtime verification + process helpers) sits next to
  `executor/flows/playwright/monitor_runtime_state.py` (369 LoC,
  W11-1 state machine extraction; +4 LoC in W11-5 for the
  ``@page.setter``). The W11-1 filename divergence is acknowledged in
  `active-work/W11-monitor-lifecycle.md` Notes/Drift but not bound to
  a W-marker. Risk: editing the wrong file is easy; review fatigue
  source. **W11-5 (`2026-05-05`) chose option C** (intentional
  leave-as-is) because the rename adds churn unrelated to the facade
  collapse and the two modules now have clearly distinct surfaces
  (helpers vs state machine). Pickup deferred — rename or merge
  decision now sits standalone (no W-marker dependency); revisit when
  W12 reshuffles `executor/flows/playwright/` into subpackages
  (`monitor/`) where the naming collision can be resolved as a
  side-effect of directory layout. Surfaced 2026-05-05 audit pass.
- **`[CLEANUP appcore-config-stale-docstring]`** —
  `appcore/api/config.py:2-8` module docstring opens with
  `core/config.py` as the section header, but `core/` is in the
  AGENTS rule 10 forbidden top-level directory list (removed pre-W6
  cleanup `2026-04-20`). Aktif kod dosyasının docstring'inde adı
  geçtiği için ileride dosyayı arayan biri yanlış yere bakar.
  Pickup: replace `core/config.py` header with
  `appcore/api/config.py`; one-line docstring touch. Surfaced
  2026-05-05 audit pass.

### Test + Observability (Promoted To W13)

These now live in `REFACTOR_OPTIMIZATION.md §11.10`; tracked here only as
a pointer:

- Benign silence fixture 3 → 5; stale singleton-lock + `.env` gitignore
  regression tests; `extrace.executor.*` logger consolidation; run-ID
  stamping.

### Codex Automation Flow Review (2026-04-27)

Numbered triage (codex-automation-{1..8}). Detail in archive
("§Codex automation flow review"). Open:

- **`[FOLLOWUP codex-automation-5]`** Executor runtime fingerprint in
  report.
- **`[FOLLOWUP codex-automation-6]`** UI failure taxonomy.

Landed (evidence in `REFACTOR_STATUS.md` archive):
codex-automation-3, 7, 8.

### Live-Scan Findings (2026-04-27, post-W8-0 smoke)

- **`[FOLLOWUP capability-verification-gap]`** `debug` +
  `terminal_tasks` capability verification (read in archive for the
  `ms-python.python` `degraded` health debrief).
- **`[FOLLOWUP w8-0-capture-pipeline]`** — partial close: signal (a)
  closed by W8-3 live smoke 2026-04-28; signal (b) typed
  harness-readiness reason codes still unconfirmed live.
- **`[FOLLOWUP make-test-security-lane-composition]`** — *FULL CLOSE
  2026-04-30 via W9-6d*. `make test-security` now unions fixture
  hygiene + architecture defaults + W8 subsystem security lanes
  (`tests/security/`, `tests/platform/security/`,
  `tests/architecture/test_default_bindings.py`,
  `tests/workflows/marketplace/test_vsix_hardening.py`,
  `tests/executor/security/test_uri_trigger_injection.py`,
  `tests/workflows/activation_reports/test_router_path_traversal.py`).
  W9-5 container import-mode test stays under
  `make test-arch-import-mode` (smoke marker; default pytest config
  filters smoke out, so folding would silently deselect).
- **`[FOLLOWUP w8-4-broader-executor]`** — W8-4 absolute-binary-path
  discipline applied to `executor/host.py` + `uri_validation.py` only
  (tracker scope). Bare-name `subprocess.run`/`Popen` literals remain
  in `editor.py` (xdotool x3), `monitor_runtime.py` (ps),
  `reset_state.py` (pgrep, bash), and
  `runtime_capture/extension_host.py` (inotifywait); each carries a
  `# arch-allow: bare-binary-path` pragma so the
  `tests/architecture/test_absolute_binary_paths.py` gate stays green.
  Three additional sites use a `cmd = [...]; subprocess.Popen(cmd)`
  variable-indirect form that the AST gate intentionally skips
  (`runtime_capture/network.py:268` `tshark`,
  `runtime_capture/filesystem.py:203` `inotifywait`,
  `runtime_capture/extension_host.py:504` `strace`); the followup must
  cover these too because the gate cannot enforce them today.
  Pull-next: extend `binary_paths.py` with `XDOTOOL_PATH`, `PS_PATH`,
  `PGREP_PATH`, `BASH_PATH`, `INOTIFYWAIT_PATH`, **`STRACE_PATH`**, and
  **`TSHARK_PATH`** (container Linux paths), migrate both pragma'd
  literal sites and the variable-indirect cmd lists, then remove the
  pragmas. POST_POC because it is uniformly `# nosec`-annotated already
  and not on the W8 stakeholder bar.
- **`[FOLLOWUP w8-1-extract-rejection-logging]`** —
  *Logging half closed 2026-04-30 via W9-6a*:
  `_extract_vsix_to_dir` emits per-entry `vsix_entry_rejected
  reason={path_traversal,symlink_escape}` + aggregate
  `vsix_extraction_rejections total=...` and returns rejection count;
  regression in `tests/workflows/marketplace/test_vsix_hardening.py`.
  *Count propagation pending*: tuple the count out of
  `download_and_extract_vsix`, persist on the marketplace job state
  row, fold into `ActivationReport` (new `vsix_rejection_count: int =
  0` field). Surfaced by 2026-04-29 audit pass.
- **`[FOLLOWUP w8-1-archive-count-bypass]`** —
  `workflows/marketplace/client.py:172` skips entries whose name does
  not start with `extension/` **before** `:188` increments
  `file_count`, so the W8-1 `MAX_FILE_COUNT` guard never fires for
  archives that pad the central directory with non-`extension/`
  members. Bounded blast radius (the `zipfile` central directory is
  already in memory; the loop does no per-entry disk I/O), but a
  defense-in-depth closure is `len(zf.infolist()) > MAX_FILE_COUNT`
  early-reject + a regression fixture in
  `tests/workflows/marketplace/test_vsix_hardening.py` that posts a
  VSIX with thousands of `pad/<n>` members and one valid
  `extension/package.json`. Companion to
  `[FOLLOWUP w8-1-extract-rejection-logging]`. Surfaced by 2026-05-04
  second-pass review.
- **`[FOLLOWUP w8-1-vsix-compressed-size-limit]`** — W8-1 guards bound
  uncompressed size, compression ratio, and extracted entry count,
  but `workflows/marketplace/client.py:306-309` reads `resp.content`
  fully **before** any archive guard runs:

  ```python
  with httpx.Client(timeout=120, follow_redirects=True) as client:
      resp = client.get(url)
      resp.raise_for_status()
      vsix_bytes = resp.content
  ```

  No `Content-Length` precheck, no streaming cap. An adversarial
  marketplace mirror or MITM point sending a 500MB+ compressed body
  pressures memory/disk before extraction limits ever apply.
  Sibling to `[FOLLOWUP w8-1-archive-count-bypass]` (post-extraction)
  and `[FOLLOWUP w8-1-extract-rejection-logging]`; this one closes
  the pre-extraction surface. Pickup: introduce a
  `MAX_VSIX_COMPRESSED_SIZE` constant, with the exact value decided in
  the implementation PR after sampling representative Marketplace
  VSIX sizes; when `Content-Length` header present, reject if
  it exceeds the cap before reading body; when absent, switch to
  `client.stream("GET", url)` with a cumulative byte counter and
  raise `VSIXUnpackError` on cap breach. **No new dependency** —
  httpx already supports streaming. Tests: oversized
  `Content-Length` rejected pre-read; missing `Content-Length` +
  streamed bytes exceeding cap rejected mid-stream; small
  `Content-Length` succeeds; missing `Content-Length` + bytes under
  cap succeeds. Natural landing: W11-companion (DoS surface; not on
  the W8-1 stakeholder bar but real attack vector). **Priority: P2**
  (Codex original P3 → audit raised; pull earlier if marketplace
  ingestion is being touched for any reason). Surfaced 2026-05-05
  (Codex review #3, audit pass).
- **`[FOLLOWUP w8-3-harness-js-scheme]`** —
  `executor/flows/harness_extension/stimulus_dispatch.js:41` calls
  `vscode.env.openExternal(vscode.Uri.parse(payload.uri_trigger))`
  without re-validating the URI scheme; the W8-3 allow-list
  (`vscode`, `vscode-insiders`, `http`, `https`) is enforced only on
  the Python `executor/flows/playwright/uri_validation.py` host-side
  path. If any orchestration path can supply a non-validated
  `payload.uri_trigger` to the harness, schemes outside the allow-list
  reach `openExternal` unchecked. Defense-in-depth options: (a)
  re-validate scheme in `stimulus_dispatch.js` against the same
  allow-list; or (b) prove via test that every producer of
  `payload.uri_trigger` flows through `uri_validation` first, and add
  a JS-side AST gate
  (`tests/architecture/test_uri_trigger_open_external_validation.py`)
  forbidding raw `openExternal(Uri.parse(...))` outside that path.
  Surfaced by 2026-05-04 second-pass review.
- **`[FOLLOWUP w8-5-list-endpoint-name-filter]`** — *CLOSED 2026-04-30
  via W9-6b*. `_list_report_files` filters glob hits through
  `ACTIVATION_REPORT_NAME_RE`. Regression: `tests/workflows/
  activation_reports/test_router_path_traversal.py
  ::test_list_endpoint_filters_malformed_names`.
- **`[FOLLOWUP w8-6-content-sample-structural-test]`** — *Partial close
  2026-04-30 via W9-6c*: `tests/platform/security/test_content_sample_typing.py`
  pins `ContentSample` shape invariants (`extra="forbid"`,
  `validate_assignment=True`, redaction validator on `value`) and locks
  a `_PENDING_MIGRATION` allow-list snapshot — currently
  `EvidenceEvent.raw_context` is the registered placeholder. When a
  field's annotation flips to `ContentSample`, the test fails (XPASS-
  equivalent) and the allow-list must be trimmed. **Audit gap remains**:
  the comprehensive sweep of every extension-derived string field on
  the `ActivationReport` subtree (`NetworkEvent.request_body_preview`,
  `NetworkEvent.response_body_preview`, `EvidenceEvent.summary`,
  `ProcessEvent.command`/`arguments_preview`, `FileEvent.summary`, etc.)
  is *not* enumerated yet — the `_PENDING_MIGRATION` list is a baseline
  placeholder, not a complete inventory. Pickup procedure: walk the
  contract surface, append every extension-controlled string field to
  `_PENDING_MIGRATION`, then plan the per-field migration to
  `ContentSample`. Surfaced by 2026-04-29 audit pass; structural-test
  half closed by W9-6c on 2026-04-30.
- **`[FOLLOWUP w8-8-manifest-emit-when-needed]`** — DEFERRED 2026-04-29
  (W8-7 audit pass). No production logger emits manifest fields raw
  today; only the W8-2-validated `publisher`/`name`/`version` slug
  reaches loggers. **Canonical body lives in
  `active-work/W8-security.md` W8-8** (threat statement, two reopen
  triggers, four-artifact set, pickup procedure — do not delete).
  Triggers in short: (A) first feature PR adding a `logger.*` call
  that references a raw manifest field (`displayName`, `description`,
  `repository.url`, `categories[]`, `homepage`, `bugs`, `qna`,
  `license`); (B) proactive security pull from external review or
  stakeholder gate. Either trigger ships
  `appcore/contracts/sanitize.py::sanitize_for_log`,
  `tests/platform/security/test_manifest_log_sanitization.py`,
  `tests/architecture/test_manifest_field_log_emit.py`, and ADR 0002
  §7 addendum in one PR; flip W8-security.md marker to landed and
  retire this ID.

### Architecture Audit (2026-04-27)

Detail in archive. Open audit gaps:

- §7 untrusted-input → logging gap closed by W8-8 (manifest
  log-injection sanitization, `active-work/W8-security.md`).
- Remaining audit deltas tracked in archive; consolidate after W13.
- **`[FOLLOWUP arch-gate-no-bare-except]`** — *LANDED (verified
  2026-05-05 audit pass)*. AST gate
  `tests/architecture/test_no_bare_except_exception.py` is in tree
  with full implementation: AST-walks `appcore/`, `workflows/`,
  `executor/`, `packages/` (excludes `tests/`, `alembic/versions/`,
  `scripts/`); rejects `ExceptHandler(type=Name(id="Exception"))` and
  `ExceptHandler(type=None)`; allow-lists the planned
  `[FOLLOWUP analysis-thread-supervisor]` site via
  `# arch-allow: thread-supervisor` pragma; ships with self-tests
  (detector flags bare/Exception, ignores narrow types, ignores
  identifier references, pragma escape policy). The only remaining
  `except Exception` literal in production roots is inside the
  docstring at `appcore/db/session.py:137`, which is invisible to
  `ast.parse` and tracked separately as
  `[CLEANUP session-docstring-except-exception]`. Surfaced
  2026-05-04, verified-landed 2026-05-05.
- **`[FOLLOWUP w8-8-trigger-sweep-as-test]`** — W8-8 deferral
  (`[FOLLOWUP w8-8-manifest-emit-when-needed]`) carries two named
  reopen triggers; **Trigger A** = "first feature PR introduces a
  `logger.*` call referencing a raw manifest field
  (`displayName` / `description` / `repository.url` / `categories[]` /
  `homepage` / `bugs` / `qna` / `license`)". Today this trigger is a
  manual grep procedure documented in `active-work/W8-security.md`;
  no re-audit evidence since 2026-04-29. The trigger is mechanically
  enforceable as an AST gate. Pickup: add
  `tests/platform/security/test_manifest_log_emit_audit.py` that
  AST-walks `workflows/extension_catalog/` and
  `workflows/marketplace/`, finds `Call` nodes whose function is
  `logger.{info,warning,error,debug,exception}` and whose argv
  string-literal contains any of the 8 manifest field names; fail
  with `f"W8-8 trigger A fired: {file}:{line} → ship sanitize_for_log
  helper now"`. Default-empty allow-list (becomes the helper-call
  marker once W8-8 ships). Self-tests mirror existing AST gate
  pattern. Verifies green on current codebase (W8-8 deferral
  assumption holds); if it red-fails on first run, ship W8-8 helper
  immediately. AST gate count 8 → 9. Natural landing:
  W11-companion. **Priority: P2.** Surfaced 2026-05-05 audit pass.
- **`[FOLLOWUP arch-gate-executor-control-outbound]`** — Existing
  import-graph gate
  (`tests/architecture/test_import_graph.py::test_workflows_use_only_executor_control_boundary`)
  restricts the `workflows/`→`executor/` direction to
  `executor.control(.*)`. No machine guard prevents `executor.control`
  itself from leaking `docker.*` / `playwright.*` / `aiohttp.*` types
  through its public surface back to workflow callers. No leak today
  (verified by direct read), but no protection against
  re-introduction. Pickup: extend `test_import_graph.py` or add new
  `tests/architecture/test_executor_control_boundary.py` that scans
  `executor/control.py` public functions/classes (and any future
  `executor/control/` package if introduced), AST-walks public
  function signatures and class attribute annotations, fails on any
  reference to
  `docker.*`/`playwright.*`/`aiohttp.*` types. Intentionally strict
  (no pragma escape). AST gate count 9 → 10 (after
  `[FOLLOWUP w8-8-trigger-sweep-as-test]` lands). Natural landing:
  W13 `§11.10`. **Priority: P3.** Surfaced 2026-05-05 audit pass.
- **`[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]`** —
  `# arch-allow: bare-binary-path` pragma (sibling to
  `[FOLLOWUP w8-4-broader-executor]`) currently authorizes known
  pragma-bearing files / call groups (`editor.py` xdotool x3,
  `monitor_runtime.py` ps, `reset_state.py` pgrep+bash,
  `runtime_capture/extension_host.py:602` inotifywait). The same-line
  / line-above pragma policy is correct
  but no count ratchet protects against silent dilution: a reviewer
  could in principle scatter the pragma to suppress real new
  findings. Pickup: extend
  `tests/architecture/test_absolute_binary_paths.py` (or new
  `tests/architecture/test_bare_binary_pragma_count.py`) with a
  baseline file (`tests/architecture/_baselines/bare_binary_pragma.txt`)
  recording line-by-line pragma sites; gate fails if scanned count
  exceeds the baseline with message
  `f"bare-binary-path pragma count grew: was N, now M. Either remove
  pragmas via binary_paths.py migration or update the baseline if
  intentional."`. Self-tests. Once
  `[FOLLOWUP w8-4-broader-executor]` lands and removes the pragmas,
  the baseline target becomes 0. Natural landing: W13 `§11.10`.
  **Priority: P3.** Surfaced 2026-05-05 audit pass.

---

## How To Pull An Item Back

1. Pick the item by stable ID.
2. Open the archive entry for the full trigger / file refs / acceptance.
3. If the work landing point matches a `REFACTOR_OPTIMIZATION.md §11`
   week, promote it there with a one-line rationale; otherwise open a
   focused branch and update the item to `[LANDED <date>]` with the
   commit SHA + branch name.
4. Drop the verbose closure evidence into `REFACTOR_STATUS.md` (slim
   canonical or archive depending on size budget).

When this file exceeds 300 lines / 3,000 tokens, drop a new dated full
snapshot under `archive/backlog/` and re-trim — see
`agent-lanes/docs-maintenance.md` invariants.

## Archive

Full historical backlog (verbose item descriptions, all landed evidence,
review triage blocks, architecture audit body):

- Latest audit snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md)
- Pre-trim baseline snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-04-29.md`](archive/backlog/POST_POC_BACKLOG_full_2026-04-29.md)
