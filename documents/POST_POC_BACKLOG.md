# Post-PoC Backlog

`Last Updated: 2026-04-24 (target activation lifecycle PRs 1-2 landed; PRs 3-5 pending)`

Work items that do not block PoC acceptance (`REFACTOR_OPTIMIZATION.md`
§10.7) and were intentionally deferred from W0-W7 for scope management.
Each entry names a stable trigger and a rough size so a future iteration
can pull it back without re-deriving context.

The PoC acceptance bar is met as of 2026-04-23. Anything below this line
is value-add, not a gate.

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
  3. **exthost.log parser lifecycle markers.** Today
     `runtime_capture/extension_host.py::_ACTIVATION_PATTERNS` only
     captures `"activated X in Nms"` / `"activating extension 'X'"`.
     Extend it to also extract activation-function entry/exit and
     command/provider registration events when present in the exthost
     trace output. Emit as a new dataclass adjacent to
     `ActivationEntry` (or an extended one) so attribution can
     correlate them to `event_attempts` in step (2).
  4. **Deterministic `log_streams["target_extension_host"]`.** Current
     `LogStreamEntry.is_target_extension` gets filled reactively from
     attribution. Promote `target_extension_host` to an explicit
     stream key with an invariant: every entry under that key has
     `is_target_extension=True` and `extension_id == target_id`.
     Other streams (e.g. `extension_host_other`, `automation_output`)
     stay. Report-builder test covers the invariant.
  5. **Target-owned output-signal capture.** Grep confirms zero
     coverage today for `OutputChannel.appendLine`,
     `console.log`, and `command/provider` invocations
     emitted **from inside the target extension**. Architectural
     choice needed before implementation:
     (a) harness-side hook in `executor/flows/harness_extension/` that
     instruments `vscode.window.createOutputChannel` and surfaces
     appendLine calls as `EvidenceEvent` records; or
     (b) mine the exthost Output channel log bundle and correlate
     via timestamp + channel name. (a) is cleaner but requires the
     harness to run alongside the target without polluting
     attribution; (b) is log-only but weaker signal fidelity. Needs
     its own short ADR before code — do not start without one.

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

## UI

- Split `ReportsWorkspace` / `DetectionPanel` into smaller components
  (7.3.1, 7.3.2) once the evidence-deep-link feature settles.
- Replace the `window.__EXTRACE_CONFIG__` global with a React context
  provider (7.3.3).
- Wire `AbortController` cancellation through the polling helpers
  (7.3.4).
- Add a feature-boundary ESLint rule that prevents `features/*` from
  importing sibling `features/*` internals (7.3.5).
- Axe-core accessibility lane (deferred W7; re-plan when UI is
  stakeholder-facing).

## Detection engine stretch

- **Adversary classes A5 + A7** — stretch canaries + rules (ADR 0002
  §4). A3 landed in W7 Phase 3a (`extrace.a3.typosquat`); A5 and A7 are
  the remaining stretch entries.
- Promote allowlists (`benign_domains.txt`, `popular_extensions.txt`) to
  a versioned data artifact once the lists grow past the current
  hand-curated ~15-20 entries.

## Engineering quality

- Promote mypy to `strict = true` once the remaining `ignore_errors`
  overrides (scripts, tests, alembic) are either typed or actually
  moved outside the source set.
- Documentation consolidation pass: dedupe `REFACTOR_STATUS.md`,
  `REFACTOR_EXECUTION_PLAN.md`, `REFACTOR_OPTIMIZATION.md` once W7 is
  more than a few weeks old and the living-doc cadence has settled.

## How to pull an item back

1. Confirm the item is still relevant (some may be obsoleted by newer
   ADRs or prior deferrals).
2. Re-derive a scoped plan (small implementation plan, not a whole
   weekly cycle) and attach it in
   `documents/REFACTOR_EXECUTION_PLAN.md` as a new section.
3. Update this file when the item lands — move it to a completion log
   rather than deleting it, so future readers can trace when the
   deferral unwound.
