# Post-PoC Backlog

`Last Updated: 2026-04-27 (target activation lifecycle complete: PR3 + PR4 + ADR 0006 + PR5 landed on feat/pr345-completion; W8 entry gate green)`

Work items that do not block PoC acceptance (`REFACTOR_OPTIMIZATION.md`
§10.7) and were intentionally deferred from W0-W7 for scope management.
Each entry names a stable trigger and a rough size so a future iteration
can pull it back without re-deriving context.

The PoC acceptance bar is met as of 2026-04-23. Anything below this line
is value-add, not a gate.

## External review integration window (W8-W13, scheduled 2026-04-24)

Two independent external reviews landed 2026-04-24
([`documents/claude_code_review.md`](claude_code_review.md),
[`documents/codex_project_review.md`](codex_project_review.md)). Their
findings have been triaged and scheduled into a six-week post-PoC
window in [`REFACTOR_OPTIMIZATION.md §11`](REFACTOR_OPTIMIZATION.md)
(W8 Güvenlik sıkılaştırma → W13 Test expansion + observability).

**Entry gate for W8 (REFACTOR_OPTIMIZATION.md §11.1):** **MET as of
2026-04-27.** PRs 1-2 landed 2026-04-24 (`1b62434`); PR3
(`c59762d`), PR4 (`c5e400b`), ADR 0006 (`b737529`), and PR5
(`8453fb2`) landed 2026-04-27 on branch `feat/pr345-completion`.
See `REFACTOR_STATUS.md` "PR345 Complete" section for the full closure
checklist. W8 (`REFACTOR_OPTIMIZATION.md §11.5`) is now eligible to
open.

**Promoted from this backlog into W8-W13:** the two "Next iteration"
entries that were left as `[NEXT]` pulls — target activation lifecycle
PRs 3-5 (W8 entry gate blocker) and review-surfaced items
(`signal_policy.py` relocation → W9-2; `registry.py` split → W10-3;
`monitor_lifecycle.py` split → W11; `executor/flows/playwright/`
subpackaging → W12). Items not yet promoted stay in this file under
their current sections.

**Rejected from W8-W13 (stay in this file with promotion rationale
in §11.12):** UI component split (7.3.1/7.3.2), axe-core, mypy strict
promotion, documentation consolidation, monorepo tooling migration,
async executor runtime refactor, OpenAPI frontend client generation.
Each is annotated "Evaluated 2026-04-24, not promoted — see
REFACTOR_OPTIMIZATION.md §11.12" below.

## Next iteration (pull first)

- **[NEXT] Target activation lifecycle + target log instrumentation.**
  Post-W7 review (2026-04-24) found that the current
  `EventAttemptRecord.status` state machine is effectively binary in the
  verification path: `planned → running → (attempted_only | verified |
  blocked | failed)`. That collapses three distinct observation
  milestones into one `verified` flip, which hides the failure-mode
  where harness stimulus fired, the target extension activated, but
  **no target-owned log/output-signal evidence was emitted**. Fix
  lands in five incremental PRs, each self-contained + independently
  testable:
  1. **[LANDED 2026-04-24] Lifecycle vocabulary + validator.** Extended
     `EventAttemptRecord.status` allowed values to
     `planned | running | attempted_only | activation_seen |
     target_log_seen | verified | blocked | failed` via the
     `EVENT_ATTEMPT_LIFECYCLE_STATES` frozenset in
     [`packages/analysis_contracts/contracts.py`](../packages/analysis_contracts/contracts.py)
     and a Pydantic `field_validator` on `EventAttemptRecord.status`.
     Transition graph documented as a module comment adjacent to the
     constant. Re-exported through `packages.analysis_contracts.__init__`.
     Coverage: parametrized acceptance test over every documented
     state + rejection test for unknown values + runtime-emitter
     coverage assertion in
     [`tests/platform/contracts/test_analysis_fixture_baselines.py`](../tests/platform/contracts/test_analysis_fixture_baselines.py).
  2. **[LANDED 2026-04-24] Emit intermediate transitions.**
     `reconcile_event_attempts` in
     [`executor/flows/playwright/health_reconciliation.py`](../executor/flows/playwright/health_reconciliation.py)
     now upgrades non-harness attempts whose planner activation event
     matches a `target_id`-scoped `ActivationEntry`: to `target_log_seen`
     when at least one `log_streams` entry with
     `is_target_extension=True` AND `extension_id == target_id`
     correlates to the attempt, otherwise to `activation_seen`.
     Harness attempts continue to route through
     `_mark_unverified_harness_attempt` so they keep their
     `harness_verification_unconfirmed` signal — the new states only
     apply to target-side observation.
     `attempt_has_runtime_evidence` in
     [`executor/flows/playwright/health_runtime_facts.py`](../executor/flows/playwright/health_runtime_facts.py)
     accepts both new states as runtime evidence so coverage rollups
     do not regress. Coverage: 8 new tests across upgrade paths,
     harness-exclusion guard, target-attribution requirement,
     `extension_id` mismatch defense, 5-entry summary cap, and direct
     `attempt_has_runtime_evidence` lifecycle-state assertion.
  3. **[LANDED 2026-04-27 `c59762d`] exthost.log parser lifecycle markers.**
     `_LIFECYCLE_MARKER_PATTERNS` added to
     [`extension_host.py`](../executor/flows/playwright/runtime_capture/extension_host.py)
     covering activate function entry/exit, command registration, and
     provider registration. `ActivationEntry.marker_type` field
     extended (default `""` preserves PR1+PR2 behavior). Five new
     parser tests in
     [`test_playwright_monitor_runtime.py`](../tests/executor/test_playwright_monitor_runtime.py).
     Pydantic mirror + UI contract regen'd.
  4. **[LANDED 2026-04-27 `c5e400b`] Deterministic `log_streams["target_extension_host"]`.**
     `_assert_target_stream_invariant` build-path guard added to
     [`monitor_lifecycle.py`](../executor/flows/playwright/monitor_lifecycle.py)
     `_append_activation_log_entries` and `record_automation_event`;
     serialization-time demote in
     [`monitor_types.log_streams`](../executor/flows/playwright/monitor_types.py)
     handles legacy/manual-construction leaks via one-shot warning +
     `other_extension_host` reassignment.
     New invariant test in
     [`test_playwright_monitor_lifecycle.py`](../tests/executor/test_playwright_monitor_lifecycle.py).
  5. **[LANDED 2026-04-27 `8453fb2`, ADR 0006 `b737529`] Target-owned output-signal capture.**
     ADR 0006 selected Option (a). Harness-side hook in
     [`extension.js`](../executor/flows/harness_extension/extension.js)
     wraps `vscode.window.createOutputChannel` and emits each
     append/appendLine via the new `emitHarnessEvent` helper in
     [`markers.js`](../executor/flows/harness_extension/markers.js).
     Python parser
     [`output_signals.py`](../executor/flows/playwright/output_signals.py)
     converts markers to `OutputSignalEvent` (new dataclass in
     [`runtime_capture/events.py`](../executor/flows/playwright/runtime_capture/events.py));
     attribution helper marks events within
     `ATTRIBUTION_WINDOW_S=5.0` of a target activation as target-owned.
     `_build_evidence_bundle` routes them to
     `EvidenceEvent(kind="output_channel_appendline",
     collector="harness_extension", actor="harness")`.
     `target_extension_observed` extended with an OR clause for
     target-attributed output signals. Five new tests in
     [`test_output_signal_capture.py`](../tests/executor/test_output_signal_capture.py).
     ADR 0006 §5 full conjunction tightening deferred (see "Deferred"
     in REFACTOR_STATUS PR345 Complete section).

  Once (1)-(5) are in, tighten the `target_extension_observed=true`
  decision (`signal_policy.py`, `health_summary.py`): currently
  derived from the activation-entry list alone, which mis-credits
  background extensions whose activation coincidentally overlaps the
  monitoring window. The tighter rule: target is observed **iff**
  at least one attempt reached status ≥ `activation_seen` AND at
  least one target-owned log or output-signal event exists on the
  evidence chain. This removes a known false-positive class surfaced
  during the W7 `sim-all` review.

  Triggers for pulling this back: a `make sim-target` run that
  reports `target_extension_observed=true` but contains zero
  target-owned network / file / log / output events; a verification
  that short-circuits because "activation == observation" is assumed.
  Size: 1-2 weeks across five PRs. Depends on: PRs 1-2 landed
  2026-04-24; PRs 3-5 still pending (PR 5 needs an ADR before code).
  Blocks: no PoC gate, but every detection rule that reads
  `target_extension_observed` gets sharper once this lands.

- **[LANDED 2026-04-24] Split `executor/flows/playwright/monitor_attribution.py`**
  into a dedicated `attribution/` subpackage. Implemented per the W7
  Phase 3b plan: the 1122 LoC module is now three files, each with a
  single responsibility and the exact same private-underscore API:
  - [`executor/flows/playwright/attribution/events.py`](../executor/flows/playwright/attribution/events.py)
    — event annotation + classification (`_annotate_network_events`,
    `_annotate_file_events`, `_annotate_process_events`,
    `_classify_event_attribution`, `_upgrade_inotify_correlations`,
    `_matches_extension_signature`, `_scenario_name_for_timestamp`,
    plus the shared helpers
    `_actor_from_file_source` / `_actor_from_network_event` /
    `_artifact_class_for_path` / `_nearest_activation_matches` /
    `_format_epoch_timestamp` / `_resolve_event_epoch` /
    `_relative_time`).
  - [`executor/flows/playwright/attribution/links.py`](../executor/flows/playwright/attribution/links.py)
    — evidence-bundle + link builders (`_build_evidence_bundle`,
    `_build_scenario_links`, `_build_temporal_links`,
    `_build_duplicate_file_links`, `_build_noise_links`,
    `_nearest_activation`, `_temporal_confidence`,
    `_dedupe_evidence_links`); pulls shared helpers from `.events`.
  - [`executor/flows/playwright/attribution/__init__.py`](../executor/flows/playwright/attribution/__init__.py)
    — flat re-export facade. Preserves the dual-import pattern
    (paket mode vs top-level executor mode where `playwright/` sits on
    `sys.path`) and the signal-layer shims (`_indexed_target_*`,
    `_build_risk_signals`, `_build_risk_summary`,
    `_build_signal_summary`); type-only imports sit under
    `if TYPE_CHECKING:` to keep ruff F401 quiet. The 29 names in
    `__all__` are identical to the pre-split module's public-for-internal
    surface so the three callers (`monitor.py`, `monitor_types.py`,
    `monitor_lifecycle.py`) only needed the module path updated
    (`monitor_attribution` → `attribution`).
    Verification: `make check-all` → 627 passed /
    5 skipped; `make test-security` → 41 passed; demo acceptance
    (`.venv/bin/python scripts/demo_acceptance.py`) → `DEMO GREEN`.
    **Docker-based A1 canary structural diff remains user-side**
    (`make exec-up && make exec-run` against
    `t1-a1-credential-read-to-network-canary`) — the pipeline regression
    risk flagged in the deferral note can only be fully closed with a
    live executor smoke.

- **[LANDED 2026-04-24] Fatal UI-crash classification + fail-fast (with
  `ScenarioTrace` failure metadata).** Implemented per the plan:
  `is_fatal_ui_error` classifier (substring markers + `page.is_closed()`
  - `context.is_closed()` + ≤1.5 s liveness probe, all explicit positive
  assertions; default non-fatal) in
  [`executor/flows/playwright/automation.py`](../executor/flows/playwright/automation.py);
  `_run_scenario_sequence` breaks the loop on fatal errors, opt-in
  `--retry-on-crash` routes through `vscode.reload_workbench_window`
  with page rebinding; `ScenarioTrace`
  ([`monitor_records.py`](../executor/flows/playwright/monitor_records.py))
  gained `failure_reason_code` + `error_detail` (≤500 char);
  `record_scenario_event`
  ([`monitor_lifecycle.py`](../executor/flows/playwright/monitor_lifecycle.py))
  reads them off the existing `metadata` channel (no signature churn);
  `health_summary.py` recognises `fatal_ui_crash` as a dominant reason
  that forces `automation_health.status = "inconclusive"` per ADR 0003
  §5; Pydantic mirror lock-stepped in
  [`packages/analysis_contracts/contracts.py`](../packages/analysis_contracts/contracts.py)
  with `extra="forbid"` guard; UI `contracts.ts` regen'd. New test
  coverage: `tests/executor/test_playwright_crash_classifier.py` (11
  tests including false-positive guard for transient timeouts),
  extended `test_playwright_automation.py`,
  `test_playwright_monitor_lifecycle.py`, and new
  `test_playwright_health_summary.py`. Verified via `make typecheck` +
  `make check-all` (627 passed / 5 skipped).

- **[LANDED 2026-04-24] Scan-between VS Code restart (ESLint
  `onStartupFinished` install race fix).** First scan after a fresh
  container boot always succeeded; the **second** scan's
  `code --install-extension <eslint>.vsix` reliably failed with rc=1
  because the previous scan's extension host left a stale IPC socket +
  Chromium `SingletonLock` that collided with the new install. Only
  ESLint hit it consistently (`onStartupFinished` + `extensionKind:
  workspace` + `untrustedWorkspaces.supported: false` all worsen the
  race). Fix: `reset_executor_state` in
  [`executor/flows/playwright/reset_state.py`](../executor/flows/playwright/reset_state.py)
  now orchestrates workspace setup → `terminate_vscode` (SIGTERM +
  5 s grace, SIGKILL fallback on survivors) → clear
  `extensions/` + `logs/` → `cleanup_singleton_locks` (remove
  `SingletonLock` / `SingletonCookie` / `SingletonSocket` under
  `~/.config/Code`) → `launch_vscode` (new shared
  [`executor/container/launch_vscode.sh`](../executor/container/launch_vscode.sh)
  script, also used by `start.sh` at boot — single source of truth for
  the CDP launch command, uses `setsid` for lifetime decoupling).
  Summary dict now carries `terminated_vscode_processes`,
  `removed_singleton_locks`, `relaunched_vscode_pid`. Defense-in-depth
  on the app side:
  [`executor/host.py::install_extension_in_executor`](../executor/host.py)
  retries once through `reload_vscode_window` on transient IPC
  markers (`connection refused`, `ipc hook`, `singleton`, `renderer
  process gone`, `target crashed`, …) and
  [`workflows/marketplace/analysis_execution.py::install_failure_message`](../workflows/marketplace/analysis_execution.py)
  appends the last 500 chars of stderr to the failure line so the next
  regression of this class is diagnosable from the report alone (no
  more "Command failed (rc=1)" blind spots). New test coverage:
  rewritten `tests/executor/test_reset_state.py` (11 tests covering
  terminate / SIGKILL escalation / singleton cleanup / launch script
  success+failure + orchestration order), extended
  `tests/scanner/test_executor.py` (retry-after-reload, non-transient
  no-retry guard, reload-failure preserves original error), new
  `tests/workflows/marketplace/test_analysis_execution_helpers.py`
  (5 tests for the install/monitoring failure formatters).

- **[LANDED 2026-04-24] Split `sim-all` (UI stress) from target-extension smoke.**
  New [`Makefile`](../Makefile) target `sim-target` runs
  `entrypoint.py --monitor --target-extension-id $(TARGET)` with
  optional `TRIGGERS=/path/to/payload.json` and `SCENARIO=<name>`
  passthrough, so operators can answer "did a normal extension
  activate cleanly?" without reading through a `sim-all`
  inconclusive-by-design report. Usage:
  `make sim-target TARGET=publisher.name [TRIGGERS=…] [SCENARIO=…]`.
  The `make help` section and the `sim-all` echo banner were updated
  to make the split explicit — `sim-all` is now labelled "UI-stimulus
  stress: scenarios w/o target ext." and `sim-target` is the target
  smoke. The `TARGET` argument is required; missing it exits non-zero
  with a usage hint. Verified with `make -n sim-target
  TARGET=ms-python.python` (dry-run shows the correct docker exec
  expansion).

- **[LANDED 2026-04-24] `sim-all` report-semantics + retry-on-crash
  correctness pass.** Six follow-ups that fell out of a deep review
  of a post-fail-fast `sim-all` report:
  - **Legacy `verdict` → `signal_summary` migration validator.** The
    W7-entry rename (`build_verdict` → `build_signal_summary`) ships
    under `extra="forbid"`, which meant any `ActivationReport`
    produced by an older runner or stored on disk from before the
    rename would raise on load. Added a
    `model_validator(mode="before")` on
    [`packages/analysis_contracts/contracts.py::ActivationReport`](../packages/analysis_contracts/contracts.py)
    that re-maps a legacy `verdict` field to `signal_summary` during
    parse, so round-trip survives and the rename stays
    backward-compatible. Test:
    [`tests/platform/contracts/test_analysis_fixture_baselines.py::test_activation_report_accepts_legacy_verdict_field`](../tests/platform/contracts/test_analysis_fixture_baselines.py).
  - **`on_page_reloaded` callback threading (retry-on-crash fix).**
    Previously `--retry-on-crash` called
    `vscode.reload_workbench_window` but kept the *old* `Page`
    reference, so every subsequent scenario hit the dead handle and
    re-crashed. `_run_scenario_sequence`
    ([`executor/flows/playwright/automation.py`](../executor/flows/playwright/automation.py))
    now accepts `on_page_reloaded: Callable[[Page], None]`;
    `entrypoint_runner` wires it to a `nonlocal` closure that
    rebinds both its own `page` and `mon.page`. Coverage:
    `test_retry_on_crash_invokes_on_page_reloaded_callback`,
    `test_on_page_reloaded_not_called_on_reload_failure` in
    [`tests/executor/test_playwright_automation.py`](../tests/executor/test_playwright_automation.py).
  - **`aborted_after_fatal_ui_crash` skipped-scenario records.**
    Fail-fast used to leave `summary.skipped_scenarios` empty — a
    crash at scenario #2 of 5 silently dropped scenarios 3-5 from
    the report.
    `_mark_remaining_scenarios_aborted` now emits a
    `SkippedScenarioRecord` for each unrun scenario with
    `reason="aborted_after_fatal_ui_crash"`, so the report faithfully
    shows how many scenarios the run intended vs. actually attempted.
    Fires both on the plain fail-fast path and on the reload-failure
    branch when `--retry-on-crash` is opted in. Coverage:
    `test_fail_fast_marks_remaining_scenarios_as_aborted`,
    `test_fail_fast_aborts_on_reload_failure_when_retry_requested`.
  - **UI blocker probe before each scenario.** A dismissal dialog
    left over from a previous scenario could freeze the next
    scenario's first keystroke indefinitely with no evidence line.
    `_run_scenario_sequence` now accepts an optional
    `ui_blocker_probe(page, scenario_name)` kwarg which
    `entrypoint_runner` wires to `editor._dismiss_notification`;
    when a blocker is detected, both `ui_blocker_detected` and
    `ui_blocker_dismissed` automation events are recorded on `mon`.
    Exceptions scoped explicitly to
    `(PlaywrightError, RuntimeError, ValueError)` — no bare
    `except Exception`. Coverage:
    `test_ui_blocker_probe_invoked_before_each_scenario`,
    `test_ui_blocker_probe_failure_does_not_break_loop`,
    `test_main_wires_ui_blocker_probe_and_page_reload_callbacks`.
  - **Trimmed `scenario_terminal_usage` stimulus.**
    [`executor/flows/playwright/scenarios/runtime.py`](../executor/flows/playwright/scenarios/runtime.py)
    removed `cat .env`, `pip list`, `npm ls --depth=0`:
    high-output commands that (a) collided with target-owned
    secret-read + network-reconnaissance signals in attribution and
    (b) combined with aggressive keyboard typing were a repeatable
    `terminal_usage → Keyboard.type: Target crashed` trigger.
    Kept: `ls -la`, `git status`, `python --version`,
    `node --version`, `echo $PATH`, `pwd`. 250 ms warm-up added
    before each `type_in_terminal` call. Adversarial stimulus
    belongs on the fixture lane, not the benign path — the rule of
    thumb is now spelled out in the scenario's docstring.
  - **Monitor discovery-log rate-limit (cosmetic item below).**
    Closed in this same pass — see the "Monitor discovery-log
    rate-limit" entry under *Executor / capture hygiene*.
  Verification across all six: 636 pytest passes (+9 new tests,
  including the legacy `verdict` migration round-trip and the two
  retry-callback paths), `make test-security` → 41 passed,
  `make typecheck` clean, demo acceptance → `DEMO GREEN`.

## Executor / capture hygiene

- **T2 declawed samples + T3 handling + `make test-security-live`
  hardening.** ADR 0004 already covers the policy; operational plumbing
  (encrypted sample lane, rotation, per-sample license ledger) waits
  until there is an engagement that actually produces T2 data.

- **[LANDED 2026-04-24] Monitor discovery-log rate-limit (cosmetic).**
  `find_exthost_logs()` in
  [`executor/flows/playwright/monitor_sources.py`](../executor/flows/playwright/monitor_sources.py)
  and [`executor/flows/playwright/runtime_capture/extension_host.py`](../executor/flows/playwright/runtime_capture/extension_host.py)
  now keep a module-level `_LAST_EXTHOST_LOG_COUNT: int = -1` and
  only emit `"Found N Extension Host log file(s)"` when the count
  changes from the previously-seen value. `make sim-all` scenario
  progress is readable again; the state-change guard means noise
  reappears automatically if a new exthost log shows up mid-run
  (i.e. we still have the signal when it matters).

## Workflow / platform cleanups

- **[FOLLOWUP runner-status-contract] First-class runner status field on
  `ActivationReport`.** Today `executor/host.py` already tracks
  `result.returncode` (and `executor/host.py:308` even branches on the
  `nonzero exit AND report exists` case so the failure mode is observed
  at runtime), but the contract surface in
  `packages/analysis_contracts/contracts.py::ActivationReport` does not
  carry a first-class field for it. ADR 0003 §5 covers the *effect*
  (verdict rolls up to `inconclusive` when analysis is incomplete) and
  `automation_health.reasons` carries categorical reason codes
  (`fatal_ui_crash`, `rule_execution_errors`, `verification_gap`, …),
  but a partial-finalization runner crash that still leaves a report
  on disk reads as "verdict inconclusive, reasons list short" without
  surfacing the runner exit code that drove it. Operators can only
  recover the signal from the executor stderr tail
  (`workflows/marketplace/analysis_execution.py::install_failure_message`
  appends 500 chars on install failures, but not on the analysis path).
  - **Change:** add `ActivationReport.runner_exit_code: int | None`
    and `ActivationReport.runner_status: Literal["clean_exit",
    "nonzero_with_report", "timeout", "crashed", "cancelled"]` (or a
    typed enum). `report_builder.py` (today) and the W11
    `ReportAssembler` (planned) populate them from the host wrapper's
    `ExecutorError.returncode` + the `AnalysisCancelledError` path
    introduced by the 2026-04-25 cancel branch. ADR 0003 §5 picks up
    a short addendum noting that `runner_status` is informational and
    does **not** override verdict rollup — `inconclusive` remains the
    dominant verdict whenever the runner did not exit cleanly. UI
    adapter renders a `runner_status` chip beside the Automation
    Health chip on the report workspace.
  - **Triggers for pulling this back:** a `make sim-target` run that
    completes "successfully" on the surface (verdict `clean`,
    automation_health `ok`) but whose container actually exited
    nonzero mid-finalization; an operator who needs to distinguish a
    user-cancelled job (`AnalysisCancelledError`) from a
    timeout-killed job in the report alone.
  - **Natural landing point:** W11 (`ReportAssembler` extraction,
    `REFACTOR_OPTIMIZATION.md` §11.8) — the new field belongs in the
    assembler's output contract. Pulling it earlier means touching the
    report builder twice; later means another `[FOLLOWUP]` round.
  - **Surfaced by:** supplementary review 2026-04-25 (Codex
    "Runner exit status semantics" gap) + the post-fail-fast review
    that surfaced the underlying `executor/host.py:308` branch.

- **[FOLLOWUP simulation-progress-cancel] Run heartbeat sandbox-reset off
  the heartbeat thread.** [`workflows/marketplace/analysis_execution.py`](../workflows/marketplace/analysis_execution.py)
  `_heartbeat_on_cancel()` calls `executor_control.reset_sandbox(reload_window=True)`
  synchronously from the daemon heartbeat. If the reset blocks, no further
  cancel checks fire and the heartbeat thread is wedged. Spin the reset on
  a short-lived worker thread (or future) so the heartbeat returns immediately.
- **[FOLLOWUP simulation-progress-cancel] Dedupe / document
  `AnalysisJobStepProgress` (storage, `extra="forbid"`) vs
  `AnalyzeJobStepProgress` (API, no extra config).** Two near-identical
  schemas in [`appcore/contracts/schema_defs/analysis_jobs.py`](../appcore/contracts/schema_defs/analysis_jobs.py)
  and [`appcore/contracts/schema_defs/marketplace.py`](../appcore/contracts/schema_defs/marketplace.py)
  with subtly different validation. Either pick a canonical one and adapt,
  or leave a comment in both pointing at the deliberate split.
- **[FOLLOWUP simulation-progress-cancel] `is_job_cancelled` session
  churn.** [`workflows/marketplace/job_service.py:308`](../workflows/marketplace/job_service.py)
  opens a fresh DB session every 5 s on the heartbeat. Acceptable today;
  fold into a longer-lived session or batch with the report-payload read
  if profiling shows it.
- **[FOLLOWUP simulation-progress-cancel] Heartbeat refactor.**
  [`_run_monitoring_heartbeat`](../workflows/marketplace/analysis_execution.py)
  now juggles cancel polling, on_cancel firing, JSON file reads, scenario-
  trace counting, and emit. Lift into a `MonitoringHeartbeat` helper so
  the trace-counting branch can be unit-tested in isolation.
- **[FOLLOWUP simulation-progress-cancel] Cancel-after-finish race test.**
  Add a unit test asserting `cancel_job` called after the job has reached
  a terminal status server-side returns 409 (covered by `JobNotCancellableError`,
  but no explicit test for the in-flight race).
- **[FOLLOWUP simulation-progress-cancel] Verify heartbeat 30 s → 5 s
  load.** Interval was tightened in
  [`analysis_execution.py:82`](../workflows/marketplace/analysis_execution.py)
  for cancel responsiveness; confirm executor + DB absorb 6× more ticks
  on long runs (read report JSON + open DB session per tick).
- `workflows/marketplace/analysis_service._open_job_session` → move the
  `SessionLocal` import back to module top (7.1.2). Currently inlined to
  break a startup import cycle; revisit after the cycle source is split.
- Narrow the broad `except (FileNotFoundError, ExecutorError,
  TriggerPlanError, OSError, SQLAlchemyError, ValueError)` in
  `run_analysis_job` (7.1.4) once the individual handlers diverge enough
  to warrant distinct recovery paths.
- Tighten `search_marketplace` return type (7.1.5) so the UI adapter
  stops re-shaping loosely-typed dicts.
- Pull the "domain service" pattern (`workflows.extension_catalog`,
  `workflows.marketplace`) into the remaining router surfaces (2.8).
- `make migrate` pre-check for destructive Alembic operations (7.4.6);
  Alembic reversibility audit for every revision on `main` (7.4.7).

## Workflow / platform cleanups (promoted to W8-W10)

- **[PROMOTED → W8-2]** `safe_marketplace_slug` helper + architecture-test
  enforcement. `workflows/marketplace/client.py:94-103` raw
  publisher/name/version path concat bulgusu
  (`REFACTOR_OPTIMIZATION.md §11.5` item 2).
- **[PROMOTED → W8-5]** Activation-report router path-traversal
  regex hardening + `appcore/contracts/validators.py::valid_extension_slug`
  merkezi helper (`REFACTOR_OPTIMIZATION.md §11.5` item 5).

## UI

- **[FOLLOWUP simulation-progress-cancel] Replace `window.confirm()` on
  Stop simulation.** [`SimulationPage.tsx:108`](../ui/src/features/simulation/SimulationPage.tsx)
  uses the browser-native confirm — non-stylable, not keyboard-friendly,
  inconsistent with the design system. Build a custom `role="alertdialog"`
  with focus trap + ESC-to-cancel.
- **[FOLLOWUP simulation-progress-cancel] Cancel mutation timeout +
  retry.** No `AbortSignal` / timeout on the cancel mutation in
  [`SimulationPage.tsx:93`](../ui/src/features/simulation/SimulationPage.tsx);
  if the request hangs, the button stays disabled showing "Stopping…"
  until page reload. Add a timeout and surface a retry path on `isError`.
- **[FOLLOWUP simulation-progress-cancel] Cancel-during-completion race
  test.** [`SimulationPage.tsx:99`](../ui/src/features/simulation/SimulationPage.tsx)
  uses `setQueryData(...)` with the cancel response — if the job
  completes server-side mid-cancel, the completed status is briefly
  overwritten with cancelled until the 2 s refetch heals it. Add a unit
  test that asserts the refetch path corrects the UI.
- Split `ReportsWorkspace` / `DetectionPanel` into smaller components
  (7.3.1, 7.3.2) once the evidence-deep-link feature settles.
  > **Evaluated 2026-04-24, not promoted to W8-W13** — evidence-deep-link
  > behavior still settling; premature split would ossify incorrect
  > component boundaries. See `REFACTOR_OPTIMIZATION.md §11.12`.
- Replace the `window.__EXTRACE_CONFIG__` global with a React context
  provider (7.3.3).
- Wire `AbortController` cancellation through the polling helpers
  (7.3.4).
- Add a feature-boundary ESLint rule that prevents `features/*` from
  importing sibling `features/*` internals (7.3.5).
- Axe-core accessibility lane (deferred W7; re-plan when UI is
  stakeholder-facing).
  > **Evaluated 2026-04-24, not promoted to W8-W13** — UI is not
  > stakeholder-facing yet; accessibility bar without real users is
  > premature. See `REFACTOR_OPTIMIZATION.md §11.12`.
- OpenAPI-generated frontend API client.
  > **Evaluated 2026-04-24, not promoted to W8-W13** — UI surface not
  > stabilized; OpenAPI snapshot churns every PR without delivering
  > value until post-PoC UI stabilizes. See `REFACTOR_OPTIMIZATION.md
  > §11.12`.

## Detection engine stretch

- **Adversary classes A5 + A7** — stretch canaries + rules (ADR 0002
  §4). A3 landed in W7 Phase 3a (`extrace.a3.typosquat`); A5 and A7 are
  the remaining stretch entries.
  > **Evaluated 2026-04-24, not promoted to W8-W13** — W8-W13 focuses
  > on hardening + modularization of existing rule surface; adversary
  > coverage expansion is orthogonal and stays in this section.
- Promote allowlists (`benign_domains.txt`, `popular_extensions.txt`) to
  a versioned data artifact once the lists grow past the current
  hand-curated ~15-20 entries.
  > **Evaluated 2026-04-24, not promoted to W8-W13** — list growth
  > trigger not met; revisit when entries exceed ~50.

## Detection engine + contract hygiene (promoted to W10-W12)

- **[PROMOTED → W10-1]** `ActivationReport.schema_version` field +
  DeprecationWarning migration emitter (`REFACTOR_OPTIMIZATION.md
  §11.7` item 1).
- **[PROMOTED → W10-2]** `_TriggerPayloadDraft` elimination from
  `packages/analysis_planner/__init__.py` (`REFACTOR_OPTIMIZATION.md
  §11.7` item 2).
- **[PROMOTED → W10-3]** `packages/analysis_planner/registry.py` 669
  LoC → `capabilities.py` + `scenarios.py` + `event_scenario_index.py`
  - `pass_order.py` + facade split (`REFACTOR_OPTIMIZATION.md §11.7`
  item 3).
- **[PROMOTED → W10-4, W10-5]** `automation_health` +
  `coverage_*` typed Pydantic models (`AutomationHealth`,
  `CoverageSummary`) replacing `dict[str, Any]`
  (`REFACTOR_OPTIMIZATION.md §11.7` items 4-5).
- **[PROMOTED → W11-3]** `ActivationReport.activation_discovery_strategies`
  report field (`REFACTOR_OPTIMIZATION.md §11.8` item 3).
- **[PROMOTED → W12-3]** `raw_context` per-event-type typing
  (`NetworkRawContext` / `FileRawContext` / `ProcessRawContext`
  discriminated union) (`REFACTOR_OPTIMIZATION.md §11.9` item 3).

## Executor modularization + boundary (promoted to W9-W12)

- **[PROMOTED → W8-0]** Deterministic harness readiness gate.
  `_ensure_harness_ready`
  (`executor/flows/playwright/stimulus_attempts.py:28-50`) bugün yalnızca
  dosya varlığı kontrol ediyor. Marker payload'una `epoch_run_id`,
  `pid` ve `marker_version` eklenmeli (atomic write,
  `executor/flows/harness_extension/markers.js:33-40`); Python tarafı
  parse + epoch karşılaştırmalı; yeni tipli kodlar
  (`harness_ready_marker_missing`, `harness_ready_marker_stale`,
  `harness_ready_marker_invalid`, `harness_activation_timeout`); tek
  controlled-recovery retry; harness `activate()` enter/exit + marker-write
  `console.log` + dedicated output channel diagnostic capture (PR345 PR5
  altyapısını kullanır); test genişletmesi
  `tests/executor/test_playwright_stimulus.py`. Tetikleyici:
  `output/activation_report_ms-python.python-2026.5.2026042602-cba16dba0258.json`
  (9 attempt × `harness_command_unavailable`,
  `target_extension_observed=true`). W8-1 + W8-3 öncesi sırala.
  `failure_reason_code` enum hareketi W10 contracts hygiene ile koordine
  edilecek. Detection rule **değişikliği değil** — automation health
  sıkılaştırma. Lower-level kök sebep mevcut raporla **kanıtlanamıyor**
  (extension_host_output gappy); diagnostic capture düzeltmeden **önce**
  landlanmalı ki yeniden tarama kök sebebi doğrulayabilsin.
- **[PROMOTED → W8-1]** VSIX zip-bomb + ZipSlip guard in
  `packages/analysis_engine/static/vsix.py` (`REFACTOR_OPTIMIZATION.md
  §11.5` item 1).
- **[PROMOTED → W8-3]** URI trigger argv-form invocation in
  `executor/flows/playwright/entrypoint_triggers.py:142` +
  `stimulus_attempts.py:136` (`REFACTOR_OPTIMIZATION.md §11.5` item 3).
- **[PROMOTED → W8-4]** Absolute binary paths discipline across
  executor shell invocations (`REFACTOR_OPTIMIZATION.md §11.5` item 4).
- **[PROMOTED → W8-6]** `ContentSample.value` secret redaction +
  ADR 0003 §6 addendum (`REFACTOR_OPTIMIZATION.md §11.5` item 6).
- **[PROMOTED → W9-1]** ADR 0006 — Container packaging (paket mode vs
  top-level) (`REFACTOR_OPTIMIZATION.md §11.6` item 1).
- **[PROMOTED → W9-2]** `executor/flows/playwright/signal_policy.py`
  485 LoC → `packages/analysis_engine/signals/policy.py` relocation +
  `sys.path.insert(0, _PROJECT_ROOT)` removal
  (`REFACTOR_OPTIMIZATION.md §11.6` item 2).
- **[PROMOTED → W9-3]** Dual-import `except ImportError` fallback sweep
  across 17 executor files (`REFACTOR_OPTIMIZATION.md §11.6` item 3;
  count corrected from 14 to 17 in 2026-04-24 plan review).
- **[PROMOTED → W9-4]** `sys.path.insert` audit + removal outside
  `scripts/`, `tests/`, `alembic/`. 5 runtime hits identified:
  `signal_policy.py:33`, `reload_vscode.py:19`, `triggers.py:27`,
  `report_builder.py:17`, `entrypoint.py:18` (`REFACTOR_OPTIMIZATION.md
  §11.6` item 4; scope expanded from single hit to 5 in 2026-04-24
  plan review).
- **[PROMOTED → W9-5]** Container import-mode CI test
  (`REFACTOR_OPTIMIZATION.md §11.6` item 5).
- **[PROMOTED → W11]** `executor/flows/playwright/monitor_lifecycle.py`
  834 LoC → `MonitorRuntime` + `ReportAssembler` + `ScenarioAccountant`
  - `ExtensionMonitor` facade split; per-strategy `_stop_*` helper
  extraction (`REFACTOR_OPTIMIZATION.md §11.8`).
- **[PROMOTED → W12-4]** `entrypoint_runner.py` 487 LoC → ≤200 LoC
  dispatch extraction; dispatch logic `entrypoint/dispatch.py` yeni
  subpackage içinde oturur (`REFACTOR_OPTIMIZATION.md §11.9` item 4).
  Moved from W11 to W12 in 2026-04-24 plan review: co-located with
  its containing `entrypoint/` subpackage — tek operasyon, iki
  dokunma turu yerine.
- **[PROMOTED → W12-1]** `executor/flows/playwright/` 54 flat dosya →
  `{monitor, stimulus, workspace, health, entrypoint}/` subpackage
  split (`REFACTOR_OPTIMIZATION.md §11.9` item 1).
- **[PROMOTED → W12-2]** `attribution/__init__.py` 29-name
  underscore-prefixed API → public/private cleanup
  (`REFACTOR_OPTIMIZATION.md §11.9` item 2).
- Async executor runtime refactor (`asyncio.Event` → `threading.Event`).
  > **Evaluated 2026-04-24, not promoted to W8-W13** — executor
  > Playwright sync; async boundary only on `appcore/` side. Change
  > benefit/cost ratio low; potential deadlock vector. See
  > `REFACTOR_OPTIMIZATION.md §11.12`.

## Engineering quality

- Promote mypy to `strict = true` once the remaining `ignore_errors`
  overrides (scripts, tests, alembic) are either typed or actually
  moved outside the source set.
  > **Evaluated 2026-04-24, not promoted to W8-W13** — strict promotion
  > requires each `ignore_errors` override to be lifted first; W8-W13
  > bandwidth doesn't cover that surface. See `REFACTOR_OPTIMIZATION.md
  > §11.12`.
- Documentation consolidation pass: dedupe `REFACTOR_STATUS.md`,
  `REFACTOR_EXECUTION_PLAN.md`, `REFACTOR_OPTIMIZATION.md` once W7 is
  more than a few weeks old and the living-doc cadence has settled.
  > **Evaluated 2026-04-24, not promoted to W8-W13** — W7 closure <4
  > weeks old; living-doc cadence not yet settled — early merge would
  > lose audit trail. See `REFACTOR_OPTIMIZATION.md §11.12`.
- Monorepo tooling migration (`uv` / `poetry`).
  > **Evaluated 2026-04-24, not promoted to W8-W13** — "no new
  > dependency without approval" AGENTS.md rule blocks this without
  > an ADR; no ADR exists. See `REFACTOR_OPTIMIZATION.md §11.12`.
- Executor-wide Bandit scope expansion (`pyproject.toml` exclude
  removal).
  > **Evaluated 2026-04-24, not promoted to W8-W13** — Codex §7
  > flag; but Codex's own recommendation is "targeted security tests
  > - narrow excludes, not blanket enable". W8-1 (zip-bomb), W8-3
  > (URI argv), W8-4 (absolute binary paths) already close the
  > concrete subprocess/path injection vectors with targeted tests;
  > Bandit-wide enable noise/benefit ratio low (subprocess calls are
  > all list-form + `# nosec`-annotated). Post-W13 mechanical
  > cleanup. See `REFACTOR_OPTIMIZATION.md §11.12`.

## Test + observability (promoted to W13)

- **[PROMOTED → W13-1]** Benign silence baseline expansion 3 → 5
  fixtures (+ vscode-eslint, + github-copilot-chat)
  (`REFACTOR_OPTIMIZATION.md §11.10` item 1).
- **[PROMOTED → W13-2]** Stale `SingletonLock` cleanup regression test
  (W7 post-hardening fix regression guard)
  (`REFACTOR_OPTIMIZATION.md §11.10` item 2).
- **[PROMOTED → W13-3]** `.gitignore` contract test (`.env`,
  `extensions/*/node_modules/`, `output/`, `__pycache__/` pattern
  assertions) (`REFACTOR_OPTIMIZATION.md §11.10` item 3).
- **[PROMOTED → W13-4]** `extrace.executor.*` logger hierarchy
  consolidation; all `print(...)` call sites → logger
  (`REFACTOR_OPTIMIZATION.md §11.10` item 4).
- **[PROMOTED → W13-5]** Run-ID (UUIDv7) stamping across all log
  records + report outputs via logger filter
  (`REFACTOR_OPTIMIZATION.md §11.10` item 5).

## How to pull an item back

1. Confirm the item is still relevant (some may be obsoleted by newer
   ADRs or prior deferrals).
2. Re-derive a scoped plan (small implementation plan, not a whole
   weekly cycle) and attach it in
   `documents/REFACTOR_EXECUTION_PLAN.md` as a new section.
3. Update this file when the item lands — move it to a completion log
   rather than deleting it, so future readers can trace when the
   deferral unwound.
