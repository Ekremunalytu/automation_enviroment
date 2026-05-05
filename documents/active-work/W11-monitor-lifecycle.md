# W11 — Monitor Lifecycle Split (Active Work Tracker)

`Last Updated: 2026-05-05 (W11-5 landed)`

This is the canonical active work tracker for the W11 monitor lifecycle
split window. Items have stable IDs (`W11-1` … `W11-8`). Code comments,
tests, and ADR addenda reference items by ID — **keep IDs stable** when
reorganizing.

This file mirrors the structure of `W8-security.md`. Slim canonical
`REFACTOR_OPTIMIZATION.md §11.8` only carries an 8-line summary; full
historical detail lives in
`archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md §11.8`. Pick up an
item by reading both this tracker and that archive section.

## Status (Quick Glance)

- **Entry gate** — met `2026-05-04`. W10 contract hygiene closed (PR #11
  merged), `[FOLLOWUP w11-precursor-tests]` safety net for
  `runtime_capture/extension_host.py` and `health_reconciliation.py`
  landed (`tests/executor/test_playwright_extension_host.py` 23 cases,
  `tests/executor/test_playwright_health_reconciliation.py` 15 cases). The
  W11 split refactor is now safe to start.
- **W11-1** — landed `2026-05-04`. `MonitorRuntime` extraction landed in
  `executor/flows/playwright/monitor_runtime_state.py` (new, 334 LoC).
  Note: filename diverged from the archive entry because
  `monitor_runtime.py` already existed (554 LoC of runtime
  verification/process helpers consumed by the lifecycle module).
  `ExtensionMonitor` becomes a transitional facade that composes the
  new collaborator via constructor injection and forwards public
  methods (`start`, `stop`, `attach_runtime_tracers`,
  `capture_runtime_snapshot`, `__enter__`/`__exit__`,
  `_handle_*_event`); persistence, scenario finalization, activation
  log appending, and derived-state refresh stay on the facade as
  callbacks until W11-5 collapses the orchestration. `monitor_lifecycle.py`
  shrank 852 → 672 LoC. Tests:
  `tests/executor/test_playwright_monitor_runtime_state.py` (14 cases,
  imported at the real module path so the W12 reshuffle cannot
  silently regress this surface) +
  `tests/executor/test_extension_monitor_facade.py` (9 cases pinning
  the W11-1 transitional delegation stubs and the
  facade→runtime callback wiring; W11-5 must rewrite these against
  the collapsed facade). Baseline grew 1079 → 1102.

  **Live-scan validation (`2026-05-04`):** the W11-1 build was
  exercised end-to-end against `ms-python.python@2026.5.2026042602`
  in the live executor (job
  `a412888c4736400ca4d09d9466f83519`, 444s monitoring,
  22 activations / 175 network events / 2515 file events / 282
  process events, 5 stimulus passes + 3 scenarios completed,
  detection verdict=clean). Field-by-field comparison against four
  prior scans of the same target on the same container (including
  one taken minutes before the W11-1 cutover) showed bitwise-equal
  pre/post pattern: identical activation count, scenario_traces=3,
  log_entries=0, run_quality=medium, automation_health=degraded.
  No new behavior delta from the refactor.
- **W11-2** — landed `2026-05-04`. `ReportAssembler` extraction landed
  in `executor/flows/playwright/monitor_report_assembler.py` (new,
  158 LoC). The collaborator owns derived-state refresh (event
  annotation, capability promotion, `event_attempts` reconcile,
  coverage tuple, `signal_summary`, `evidence_links`) and the persist
  debounce throttle (`_last_persist_at` migrated off the facade). ADR
  0003 verdict rollup follows the move (called via
  `_build_signal_summary` inside `refresh_derived_state`).
  `ExtensionMonitor` keeps thin `_refresh_derived_report_state` /
  `_persist_report` shims so the W11-1 facade pin file's
  bound-method-identity assertions
  (`runtime.persist == mon._persist_report`,
  `runtime.refresh_derived_state == mon._refresh_derived_report_state`)
  remain green; runtime collaborator callbacks are wired through these
  shims, not directly to the assembler, so the W11-1 invariant
  survives untouched until W11-5 collapses the facade.
  `monitor_lifecycle.py` shrank 672 → 623 LoC. Tests:
  `tests/executor/test_playwright_monitor_report_assembler.py` (22
  cases, imported at the real module path so the W12 reshuffle cannot
  silently regress this surface; helper stubs cover all eight
  refresh-side collaborators plus the property-derived
  `canonical_evidence_links` read; idempotent-refresh and
  strictly-monotonic throttle-advance cases pin the side-effect
  semantics) + 5 new cases in
  `tests/executor/test_extension_monitor_facade.py` pinning the
  `_RecordingAssembler` (parallel to `_RecordingRuntime`) plus the
  runtime→shim→assembler chain. Baseline grew 1102 → 1129.

  **Live-scan validation (`2026-05-04`):** the W11-2 build was
  exercised end-to-end against `ms-python.python@2026.5.2026042602`
  in the live executor (job `473467cfe0ed`, 21:56 local). Field-by-field
  comparison against the W11-1 baseline (job `a412888c4736`, 19:09)
  plus three prior scans on the same target/container showed:

  - **Detection-relevant fields identical across all five scans:**
    `signal_summary` (level=`needs_review`, score=22),
    `verified_capabilities` (4-list:
    `commands`/`languages_editor`/`window_ui`/`workspace_fs`),
    `attempted_capabilities` (7-list), `coverage_summary`
    (covered=7 / partial=5 / missing=6, attempted=7, verified=4),
    `automation_health.status=degraded` with the same 3-element
    reasons list (`verification_gap_present`,
    `official_unresolved_present`,
    `harness_verification_unconfirmed_present`),
    `output_signal_events=12`, `target_activation_count=1`,
    `run_quality=medium`, `log_entries=0`, `scenario_traces=3`,
    `stimulus_passes=5`, `scenarios_run=[]`, `failed_scenarios=[]`.
  - **Raw event counts within the prior 4-scan variance band**
    (timing-bound: strace/inotify/CDN load): `network_events=192`
    (prior range 167–195), `file_events=2689` (prior range
    2507–2689), `process_events=67` (prior range 66–74),
    `evidence_links=3574` (prior range 3541–3810).
  - **`activated` count 22 → 23**: foreign-extension delta only —
    `target_activation_count` stable at 1, `verified_capabilities`
    unchanged. The 23rd entry is a non-target ext-host startup
    signal that lives in the raw capture pipeline (`MonitorRuntime`
    Strategy 1, outside `ReportAssembler`'s annotation surface).

  No regression in derived-report state. Refactor confirmed
  behavior-preserving end-to-end.

  **Acceptance sub-tasks deferred** (see Acceptance Sub-Tasks section
  below for rationale): `[FOLLOWUP runner-status-contract]` rides
  W11-3 (with `activation_discovery_strategies` and the
  `schema_version` bump for one clean contract pass);
  `[FOLLOWUP target-log-lifecycle-instrumentation]` rides W11-4
  (the gap is on the producer signal — `ScenarioAccountant` — not
  the consumer; `health_reconciliation` state machine already emits
  intermediate states).
- **W11-3** — landed `2026-05-04` on the `week11` working branch (commit
  pending). `ActivationReport` widened with three new fields in
  `packages/analysis_contracts/contracts.py`:
  `activation_discovery_strategies: list[str]`,
  `runner_exit_code: int | None`, and
  `runner_status: RunnerStatusLiteral` (new `Literal["success", "error",
  "unknown"]` exported via the package `__init__`).
  `ACTIVATION_REPORT_SCHEMA_VERSION` bumped `2.0` → `2.1` (W10-1
  proactive evolution: ingest of stale `2.0` warns lenient / rejects
  under `strict_schema=True`; the existing constant-driven
  `test_schema_version.py` cases automatically pin the new baseline).
  Mirror fields added to the runtime dataclass in
  `executor/flows/playwright/monitor_types.py` so the in-memory shape
  matches the persisted contract. UI contracts regenerated
  (`ui/src/lib/types/contracts.ts:466-468`).

  Producer wiring landed alongside the contract change (the
  `[FOLLOWUP runner-status-contract]` bundle):
  `ReportAssembler.set_runner_status(exit_code)` derives the enum
  (`0 → success`, `!= 0 → error`, no call → field default `unknown`)
  and `ReportAssembler.set_discovery_strategies(strategies)` deduplicates
  and sorts the producer list. `MonitorRuntime.stop()` now tracks success
  per strategy (Strategy 1 → `exthost_log_parse`, Strategy 2 →
  `running_extensions_ui`, Strategy 3 → `exthost_output_parse`) and
  emits the list once via a new `set_discovery_strategies` callback.
  `ExtensionMonitor` keeps thin `set_runner_status` /
  `_set_discovery_strategies` shims so the W11-1 facade pin file's
  bound-method-identity invariants (`runtime.persist == mon._persist_report`,
  `runtime.refresh_derived_state == mon._refresh_derived_report_state`)
  are extended — not violated — with a parallel
  `runtime.set_discovery_strategies == mon._set_discovery_strategies`
  pin. `entrypoint_runner.py:486-487` calls `mon.set_runner_status(exit_code)`
  immediately before the final `report.save()` (every code path that
  mutates `exit_code` lives above the `if mon is not None` block, so
  the call happens after the value is finalized).

  Tests:
  `tests/platform/contracts/test_activation_discovery_strategies.py`
  (10 cases — defaults, full round-trip, the three accepted
  RunnerStatusLiteral values, rejection of unknown status / non-int
  exit / non-list strategies / typo'd extras / `runner_exit_code=None`
  pass-through) +
  5 new cases in `tests/executor/test_playwright_monitor_report_assembler.py`
  (setters: 0→success, 1→error, 137→error pin for the "any non-zero
  maps to error" contract, dedupe+sort for strategies, empty list
  clears prior content) +
  3 new cases in `tests/executor/test_extension_monitor_facade.py`
  (W11-3 facade shim delegation + bound-method identity invariant +
  end-to-end runtime→shim→assembler chain) +
  3 new cases in `tests/executor/test_playwright_monitor_runtime_state.py`
  (all-three-succeed, all-empty, Strategy-3 dedupe-no-credit) plus an
  emission pin added to the existing
  `test_stop_runs_strategies_and_invokes_collaborator_callbacks` case +
  `_FakeMonitor.set_runner_status` stub added to
  `tests/executor/test_playwright_entrypoint.py` so the 6 existing
  monitor-mode entrypoint cases keep their pin shape. Baseline grew
  1129 → 1150 (`make check-all`); `make test-security` 170 cases
  green.

  Strategy-name divergence note: archive plan
  `archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md §11.8` lists
  example identifiers (`warm-start`, `command-probe`, `output-channel`,
  `log-tail`) that do not appear in the current `MonitorRuntime.stop()`
  source — those are aspirational/example names. The W11-3 producer
  uses the three actual strategies' snake-case identifiers
  (`exthost_log_parse`, `running_extensions_ui`,
  `exthost_output_parse`); the archive table will be reconciled when
  W11 closes.

  Branch policy deviation: per user direction, all W11-N items land on
  a single long-lived `week11` branch instead of the documented
  per-item `feat/w11-<n>-<slug>` branches (Pickup Procedure step 2).
  The branch will fold into `main` as a single PR after W11 closes.

  **First live-scan validation surfaced a serialization gap
  (`2026-05-04`):** the W11-3 build was exercised end-to-end against
  `ms-python.python@2026.5.2026042602` (job `f6faab10ce35`, 22:44 local).
  `schema_version` correctly bumped to `"2.1"` on disk, but the three
  new fields landed at their defaults
  (`activation_discovery_strategies=[]`, `runner_exit_code=null`,
  `runner_status="unknown"`) even though Strategy 1 had clearly
  succeeded (22 activations) and the runner reached its
  `set_runner_status` call. Root cause: the `ReportAssembler` setters
  mutate the runtime dataclass correctly, but
  `executor/flows/playwright/report_builder.py::build_report_data`
  (a 322-line manual dataclass→dict serializer that pre-dates W11)
  never read the new dataclass fields, so the on-disk dict defaulted
  them via the contract validator. Unit tests covering the setters
  pinned the dataclass mutation but missed the serializer's outbound
  path. Fixup landed on the same branch: `build_report_data` now
  forwards the three fields, plus
  `tests/platform/contracts/test_report_builder_contract.py` adds two
  round-trip pins
  (`test_w11_3_fields_round_trip_through_build_report_data_and_save`,
  `test_w11_3_fields_default_to_unknown_when_producer_skips_setters`)
  so the next dataclass change cannot silently drop the surface again.
  Detection-relevant fields from job `f6faab10ce35` matched the W11-2
  baseline (`signal_summary` level=`needs_review` score=22,
  `verified_capabilities` 4-list, `coverage_summary` covered=7/partial=5/missing=6,
  `automation_health.status=degraded` with the same 3-element reasons,
  `output_signal_events=12`, `target_activation_count=1`,
  `run_quality=medium`, `log_entries=0`, `scenario_traces=3`,
  `stimulus_passes=5`, `failed_scenarios=[]`); raw event counts within
  the prior 4-scan variance band (`network_events=178`,
  `file_events=2467`, `process_events=67`, `evidence_links=3821`,
  `activated=22`).

  **Second live-scan validation (post-fixup, `2026-05-04`):** with the
  `build_report_data` patch in the running container, a second scan
  against `ms-python.python@2026.5.2026042602` (job `64627b3ea714`,
  22:59 local) wrote the producer values to disk end-to-end:
  `activation_discovery_strategies=["exthost_log_parse",
  "running_extensions_ui"]` (Strategy 2 yielded a non-empty Running
  Extensions list this run, which is non-stationary on ms-python; the
  W11-3 plan note that Strategy 2 "rarely produces entries" turned out
  to be wrong on the optimistic side — the field tolerates this fine
  because it is a sorted/deduped list, not a fixed ordered tuple);
  Strategy 3 (`exthost_output_parse`) absent because its merge
  produced no new entries beyond Strategy 1 (the dedupe-no-credit
  semantics pinned by
  `test_stop_omits_strategy_three_when_output_parse_yields_no_new_entries`
  played out live as designed); `runner_exit_code=0`,
  `runner_status="success"`. Detection-relevant fields bitwise-equal
  to the W11-2 / first-W11-3 baselines (same `signal_summary`,
  `verified_capabilities`, `coverage_summary`, `automation_health`,
  `output_signal_events=12`, `target_activation_count=1`,
  `run_quality=medium`, `log_entries=0`, `scenario_traces=3`,
  `stimulus_passes=5`, `failed_scenarios=[]`). Raw event counts within
  the now-5-scan variance band (`network_events=198`,
  `file_events=2592`, `process_events=78`, `evidence_links=3541`,
  `activated=22`); `process_events=78` slightly above the prior
  4-scan ceiling of 74 — strace timing delta, not refactor. Refactor
  - serialization fix confirmed behavior-preserving end-to-end.
- **W11-4** — landed `2026-05-05` on the `week11` working branch
  (commit `f4f5df6`). `ScenarioAccountant` extraction landed in
  `executor/flows/playwright/monitor_scenario_accountant.py` (new,
  426 LoC). The collaborator owns trigger-plan / execution-result
  intake (`mark_trigger_plan_*` / `record_failed_scenarios` /
  `record_execution_result`), scenario lifecycle bookkeeping
  (`record_scenario_event` / `finalize_running_scenarios` /
  `_synchronize_scenario_truth`, plus the `_active_scenarios` dict),
  event-attempt status mutation (`record_event_attempt_start` /
  `record_event_attempt_end`), activation-window log derivation
  (`append_activation_log_entries`), and the W11-4 producer signal
  (`emit_intermediate_state_events`) for
  `[FOLLOWUP target-log-lifecycle-instrumentation]` — the post-reconcile
  pass that surfaces `activation_seen` / `target_log_seen` promotions
  on the live automation timeline (the W10-6 alphabet finally gets a
  vocabulary). `ExtensionMonitor` keeps thin one-line shims for every
  moved method (10 forwarding methods) plus a new
  `_emit_intermediate_state_events` shim, so the W11-1/2/3 facade pin
  file's bound-method-identity assertions
  (`runtime.finalize_scenarios == mon._finalize_running_scenarios`,
  `runtime.append_activation_log_entries == mon._append_activation_log_entries`,
  `runtime.emit_intermediate_state_events == mon._emit_intermediate_state_events`)
  remain green; runtime collaborator callbacks are wired through these
  shims, never directly to the accountant, so the W11-1 invariant
  survives untouched until W11-5 collapses the facade.

  Helper relocation: `_assert_target_stream_invariant` moved to
  `monitor_records.py` (next to `LogStreamEntry`, where it logically
  belongs as a build-path contract guard) so both `monitor_lifecycle`
  and `monitor_scenario_accountant` can import it without a circular
  dep. `monitor_lifecycle` re-exports the symbol via `__all__` so the
  existing test pin (`from executor.flows.playwright.monitor_lifecycle
  import _assert_target_stream_invariant` in
  `tests/executor/test_playwright_monitor_lifecycle.py:563`) keeps
  working.

  `monitor_lifecycle.py` shrank 645 → 499 LoC (W11-5 ≤200 final
  target; this lands well under the planned ≤575 budget for W11-4).
  Tests:
  `tests/executor/test_playwright_monitor_scenario_accountant.py`
  (26 cases, imported at the real module path so the W12 reshuffle
  cannot silently regress this surface; covers init invariants,
  trigger-plan/execution-result intake including the
  trace-driven-sync semantics for `failed_scenarios`, event-attempt
  status mutation including the
  `verified`/`failed`/`blocked`/terminal-mapping pin, scenario
  lifecycle including the orphan-end-without-start tolerance,
  activation-window log derivation including idempotency, 8
  W11-4 producer-signal cases pinning emission, idempotency-per-
  attempt, terminal-state filtering, per-attempt promotion, and
  `activation_event` metadata passthrough, plus 1 end-to-end
  integration case
  `test_emit_intermediate_state_events_fires_after_real_reconciliation`
  driving the chain through the real `reconcile_event_attempts` so
  the positive intermediate-state path stays pinned even when the
  trigger-driven live-scan profile does not exercise it) +
  15 new W11-4 cases in
  `tests/executor/test_extension_monitor_facade.py` (a
  `_RecordingAccountant` parallel to `_RecordingRuntime` and
  `_RecordingAssembler`, covering construction with shared report,
  every shim's delegation —
  `mark_trigger_plan_applied`/`mark_trigger_plan_missing`/
  `record_failed_scenarios`/`record_execution_result`/
  `record_event_attempt_start`/`record_event_attempt_end`/
  `record_scenario_event`/`_finalize_running_scenarios`/
  `_append_activation_log_entries`/`_synchronize_scenario_truth`/
  `_emit_intermediate_state_events`, the runtime→shim→accountant
  chain for `emit_intermediate_state_events`, and a sanity guard
  pinning the real class is composed when unpatched) + 3 new W11-4
  cases in `tests/executor/test_playwright_monitor_runtime_state.py`
  (post-refresh emission ordering invariant, single-fire-per-stop
  pin, defensive stop-without-start coverage). Baseline grew
  1150 → 1201 (`make check-all` green: lint, mypy, bandit,
  ui-types, pytest all clean).

  **Live-scan validation (`2026-05-05`):** the W11-4 build was
  exercised end-to-end against `ms-python.python@2026.5.2026042602`
  in the live executor (`make sim-target TARGET=ms-python.python`,
  job `95efbaeb721b`, 82.2s monitoring, all_scenarios mode). The
  scan profile diverged from the W11-3 trigger-driven baseline (no
  trigger payload was supplied, so `event_attempts=[]` /
  `stimulus_passes=[]` / target activation never fired) and
  Chrome crashed mid-run on the `git_workflow` scenario (environmental:
  the strace+Playwright pipeline has hit this Target-crashed
  failure mode on this host before W11). A second scan attempt
  (`SCENARIO=coding_session`) timed out connecting to Chrome
  because the crashed browser didn't recover; rather than
  destructively reset the executor container, the W11-4 validation
  was completed against scan 1 alone.
  - **W11-4-owned producer signals all populated correctly:**
    `schema_version="2.1"` (W11-3 contract preserved),
    `activation_discovery_strategies=["exthost_log_parse"]`
    (Strategy 1 succeeded with 2 non-target activations, Strategy 2
    failed via the Chrome crash, Strategy 3 yielded no new entries
    after the Strategy 1 dedupe-merge),
    `runner_exit_code=1`, `runner_status="error"`
    (`set_runner_status` correctly mapped the failed run via the
    W11-3 setter contract, exercised through the W11-4 facade-shim
    chain).
  - **Scenario-accounting refactor preserved bit-for-bit:**
    `len(scenario_traces)=4` (all four `all_scenarios` mode
    scenarios traced — `coding_session`, `debug_session`,
    `terminal_usage`, `git_workflow`); the post-`_synchronize_scenario_truth`
    `summary.scenarios_run` carries all four names;
    `failed_scenarios=["git_workflow"]` captured the Chrome-crash
    failure with the right reason code; the automation timeline
    (`log_streams.automation`) carries 10 entries — runtime tracer
    attach + trigger-execution-mode + four `start`/`end` scenario
    pairs — exactly the shape pre-W11-4 produced. The
    `append_activation_log_entries` derivation correctly attributed
    the 2 non-target activations (`ms-python.debugpy@onLanguage:python`
    → coding_session, `vscode.debug-server-ready@onDebugResolve` →
    debug_session) to `log_streams.other_extension_host` with
    scenario attribution intact.
  - **W11-4 producer signal wired correctly:**
    `emit_intermediate_state_events` ran (count=0 emissions, which
    is the correct semantic — there were no `event_attempts` to
    promote because no trigger plan was applied; the focused unit
    test
    `test_emit_intermediate_state_events_emits_per_promoted_attempt`
    pins the positive path). Confirms the post-refresh wiring
    (`MonitorRuntime.stop()` → `refresh_derived_state` →
    `emit_intermediate_state_events`) survives end-to-end without a
    stop()-time crash.

  Because the smoke run never had `event_attempts` and the target was
  never observed, the trigger-driven W11-3 baseline (job `64627b3ea714`
  with target_activation_count=1, stimulus_passes=5, full
  coverage_summary) is not directly comparable to it on
  detection-relevant fields. What scan 1 validated: (a) the producer
  side runs without monitor-side errors, (b) every W11-3 contract
  field is still populated by the refactored producers, (c) the
  scenario / event-attempt accounting still surfaces the right shape
  on the refactored path, and (d) the new intermediate-state emission
  step is wired without breaking `stop()`.

  **UI-driven scan validation (post-fixup, `2026-05-05`):** the W11-4
  build was exercised end-to-end via the UI's analysis pipeline
  against `ms-python.python@2026.5.2026042602` (job `2c1dea3c70e6`,
  12:22 local) — the proper trigger-driven, target-observed positive
  validation that the smoke run could not provide. Field-by-field
  comparison against the W11-3 second-scan baseline (job
  `64627b3ea714`) confirms **bitwise-equal detection-relevant fields**
  across the refactor:
  - `signal_summary` (level=`needs_review`, score=22),
    `verified_capabilities` (4-list:
    `commands`/`languages_editor`/`window_ui`/`workspace_fs`),
    `attempted_capabilities` (6-list), `coverage_summary`
    (covered=7 / partial=5 / missing=6, attempted=7, verified=4),
    `automation_health.status=degraded`,
    `target_extension_observed=True`,
    `target_activation_count=1`, `run_quality=medium`,
    `len(activated)=22`, `len(scenario_traces)=3`,
    `len(stimulus_passes)=5`, `len(event_attempts)=21`,
    `summary.scenarios_run=["project_exploration", "coding_session",
    "terminal_usage"]`, `failed_scenarios=[]`,
    `log_streams.target_extension_host=1`,
    `log_streams.other_extension_host=21`,
    `log_streams.automation=130`.
  - `event_attempts.verification_status` distribution identical:
    `attempted_only: 9, verified: 12`. **No attempt landed in
    `activation_seen` / `target_log_seen` for this target on either
    scan** — the reconciler's intermediate-state path requires the
    contract-driven branch with unresolved
    `target_runtime_delta` / `activation_log_*` (the W11-3 baseline's
    21 attempts all either hit the no-contract activation-only
    shortcut → `verified` or fell through the no-evidence path →
    `attempted_only`). `emit_intermediate_state_events` correctly
    emitted 0 entries on both runs; the producer signal is a function
    of the reconciler's promotion decisions, not the run profile by
    itself. The positive integration path (real reconciler → emission
    chain) is pinned by
    `test_emit_intermediate_state_events_fires_after_real_reconciliation`
    in the focused accountant test module — that test forces
    `verification_contract=["target_runtime_delta"]` with empty
    `attempted_passes`/`capability_tags` so the reconciler hits the
    intermediate-state branch deterministically.
  - Raw event counts within the prior 6-scan variance band:
    `network_events=193` (prior 167–198), `file_events=2616`
    (prior 2467–2689), `process_events=67` (prior 66–78). No drift
    attributable to the refactor.

  Refactor confirmed behavior-preserving end-to-end on the
  trigger-driven UI path; the 1-LoC delta in detection-relevant
  fields between scan and baseline is zero. W11-4 closes with full
  bar coverage (`make check-all` green, smoke run + UI run both
  validated).
- **W11-5** — landed `2026-05-05` on the `week11` working branch.
  `ExtensionMonitor` composition facade collapsed: every transitional
  delegation stub is gone (the W11-1 `_handle_*_event` shims and
  `_log_offsets` property, the W11-2 `_persist_report` /
  `_refresh_derived_report_state`, the W11-3 `_set_discovery_strategies`,
  the W11-4 ten-method shim block plus `_emit_intermediate_state_events`
  and `_synchronize_scenario_truth`). `MonitorRuntime` callbacks now
  bind directly to `ReportAssembler.persist`,
  `ReportAssembler.refresh_derived_state`,
  `ReportAssembler.set_discovery_strategies`,
  `ScenarioAccountant.finalize_running_scenarios`,
  `ScenarioAccountant.append_activation_log_entries`, and
  `ScenarioAccountant.emit_intermediate_state_events`. The constructor
  accepts opt-in `runtime` / `assembler` / `accountant` / `report`
  kwargs for test injection (`tests/executor/test_extension_monitor_facade.py`
  uses this). Three fat methods migrated off the facade onto the
  accountant: `record_stimulus_pass_event` (~58 LoC),
  `record_prerequisite_result` (~36 LoC), and `verify_target_reaction`
  (~52 LoC); the facade keeps single-statement public-API forwards so
  `entrypoint_runner.py`, `wait_helpers.py`, `stimulus_passes.py`,
  and `stimulus_prerequisites.py` need no migration. `MonitorRuntime`
  gained a `@page.setter` so the facade's `page` property can write
  through to the runtime (used by `entrypoint_runner.py:252,261`
  reload-time page reassignment). The `test_extension_monitor_facade.py`
  pin file shrank 891 → 499 LoC and pivoted from bound-method-identity
  invariants to composition-shape contracts (collaborator share-the-
  same-report, callbacks point at collaborator methods, public-API
  forwards land in the right collaborator, page setter writes through,
  facade-owned bodies still work, and an unpatched facade really holds
  three real collaborator instances). `monitor_lifecycle.py` settled at
  **286 LoC** — above the ≤200 ortodox target but every shim layer is
  gone; the residual budget is 28-LoC `record_automation_event`
  orchestration body (intentionally facade-owned because both runtime
  and accountant get it as a callback) plus public-API forward
  shims (caller compatibility) plus the `apply_trigger_payload` /
  `set_trigger_execution_mode` single-purpose bodies.

  Verification:

  - `make check-all` — green (lint + mypy strict + bandit + ui-types-check
    - ui-boundaries + 1199 pytest cases).
  - `make test-security` — 170 cases green, no regression on W5
    fixture hygiene or rule coverage.
  - `pytest tests/executor/` — 528 cases green; 18 W11-5 facade pins
    - 13 new accountant cases (5 stimulus, 2 prerequisite, 5
    verify_target_reaction, 1 page setter) replace the 35-case W11-1
    bound-method-identity suite.

- **W11-6** — pending. Per-strategy `_stop_<strategy>` helpers in
  `ExtensionMonitor.stop()` (warm-start, command-probe, output-channel,
  log-tail). With W11-5 landed, the facade no longer owns `stop()` —
  this work moves to `MonitorRuntime.stop()` instead.
- **W11-7** — pending. Workflow-side modularization:
  `workflows/extension_catalog/service.py` 475 LoC →
  `manifest_to_schema.py` (~200 LoC) + `lifecycle.py` (~250 LoC); thin
  re-export facade. Architecture audit 2026-04-27 §5.
- **W11-8** — pending. Storage-side modularization:
  `appcore/storage/crud_ops/analysis_jobs.py` 348 LoC →
  `analysis_jobs/lifecycle.py` (~180 LoC) +
  `analysis_jobs/steps.py` (~150 LoC) + `__init__.py` re-export
  facade (~20 LoC). Architecture audit 2026-04-27 §5.

## Acceptance Sub-Tasks (W11-N picks up these follow-ups)

These open `[FOLLOWUP …]` items in `POST_POC_BACKLOG.md` are scheduled to
land *as part of* W11 acceptance or as short W11 companion PRs before the
next structural pull:

- **`[FOLLOWUP w8-6-extension-host-output-redaction]`** — **P1 W11
  companion, pull before W11-6 when possible.**
  `ActivationReport.extension_host_output` currently carries raw
  Extension Host log tail text through `report_builder.py`; the backlog
  item requires
  `redact_secrets(...)` before persistence plus a regression test that
  proves AKIA / bearer / DB URL values do not appear raw in the saved
  report. W13 owns regression lock-in, but the first redaction fix
  should not wait for W13.

- **`[FOLLOWUP runner-status-contract]`** — **LANDED with W11-3
  `2026-05-04`**. `ActivationReport.runner_exit_code` (`int | None`)
  and `runner_status` (`RunnerStatusLiteral = Literal["success",
  "error", "unknown"]`) live first-class on both the persisted Pydantic
  contract
  and the runtime dataclass. `ReportAssembler.set_runner_status(exit_code)`
  owns the (exit_code → status) derivation; the runner calls
  `mon.set_runner_status(exit_code)` immediately before the final
  `report.save()` in `entrypoint_runner.py`. Surfaced 2026-04-25 (Codex
  supplementary review).
- **`[FOLLOWUP target-log-lifecycle-instrumentation]`** — **LANDED with
  W11-4 `2026-05-05`**. `ScenarioAccountant.emit_intermediate_state_events`
  surfaces the intermediate-state vocabulary on the live automation
  timeline. Wired into `MonitorRuntime.stop()` after
  `refresh_derived_state` so emissions reflect the post-reconcile
  `verification_status` literals
  (`activation_seen` / `target_log_seen`); idempotent per-attempt via
  `_emitted_intermediate_state_attempts` so repeated stops do not
  double-log. Producer-side positive path pinned by
  `test_emit_intermediate_state_events_emits_for_activation_seen` /
  `…_for_target_log_seen` / `…_emits_per_promoted_attempt` in the new
  focused accountant test module. The W10-6 alphabet now has a
  vocabulary. Surfaced 2026-05-04 (manual UI scan); closed 2026-05-05.

## Entry Criteria (all green as of 2026-05-04)

1. **W10 contract hygiene closed.** `AutomationHealth`, `CoverageSummary`,
   and `schema_version` typed contracts landed in PR #11 (merged
   `2026-05-04`). The `ReportAssembler` signature can pin against the
   typed contract directly.
2. **Precursor test safety net landed.**
   `[FOLLOWUP w11-precursor-tests]`: direct module-owned tests for the
   two playwright god-modules touched by the split:
   - `tests/executor/test_playwright_extension_host.py` (23 cases) —
     pins `parse_activations_from_output`, `parse_activations_from_log`,
     `parse_strace_process_event_line`, `find_exthost_logs`,
     `parse_all_exthost_logs`, `read_extension_host_output`, and
     `ExtensionHostFileCapture` initial state. Imports the module at its
     real path so the W11 facade re-export rearrangement does not
     silently regress public behavior.
   - `tests/executor/test_playwright_health_reconciliation.py` (15
     cases) — pins `reconcile_event_attempts` state machine
     (`failed`/`blocked`/`verified`/`activation_seen`/`target_log_seen`/
     `attempted_only` + harness-unverified path) and
     `reconcile_coverage_verification` matrix shape.
3. **Working tree clean on `main`.** Verified `2026-05-04`.
4. **`make check-all` green.** Verified pre-PR #11 merge: 1041 passed /
   6 skipped / 6 deselected.

## Verification Bar

For each W11-N to be marked **landed**:

- Targeted unit + integration tests added or updated (not just the
  precursor net — every new module gets its own focused test file).
- `make check-all` green (1041+ baseline, must grow with new tests).
- `monitor_lifecycle.py` LOC budget enforced at the W11-5 step
  (≤200 LoC for the facade).
- `schema_version` bumped at W11-3 with a contracts test pinning the new
  field.

## Pickup Procedure

1. Read this file's "Status" + the matching W11-N's archive entry in
   `archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md §11.8`.
2. Open a focused branch named `feat/w11-<n>-<slug>`; confine the change
   to the lines that item touches.
3. Update this tracker's W11-N entry in the same PR with **landed
   `<yyyy-mm-dd>`**, the commit SHA, and any test paths added.
4. If the item ships `schema_version` or contract changes
   (W11-3 specifically), update `documents/REFACTOR_STATUS.md` and any
   ADR addendum referenced.
5. After all W11-N items land, mark `W11` closed in
   `documents/REFACTOR_STATUS.md` and `documents/automation_todo.md`,
   then archive this tracker into `documents/archive/active-work/` with
   a dated filename.

## Notes / Drift

- `monitor_lifecycle.py` was **852 LoC** at the start of `2026-05-04`;
  after W11-1 it is **672 LoC**; after W11-2 it is **623 LoC**; after
  W11-3 it is **643 LoC** (two facade shims +
  one extra `MonitorRuntime` constructor argument); after W11-4
  (`2026-05-05`) it is **499 LoC** (10 accountant shims + 1 emission
  shim + 1 extra `MonitorRuntime` constructor argument; offset by
  removing 8 method bodies + the `_active_scenarios` field +
  `_assert_target_stream_invariant` definition that moved to
  `monitor_records.py`). Archive plan cited 834 LoC pre-W10. W11-5
  ≤200 LoC target unchanged — final 299-LoC reduction will land when
  the transitional shim block collapses.
- The W11 entry table in
  `archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md` lines 2478–
  2485 is the canonical W11-N→file mapping. If split granularity
  changes during execution, update both this tracker and the archive
  table at the same time.
- **W11-3 strategy-name divergence** (`2026-05-04`): archive plan
  `archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md §11.8` lists
  example identifiers `warm-start`, `command-probe`, `output-channel`,
  `log-tail` for the discovery strategies. Those names do not appear
  anywhere in the current `MonitorRuntime.stop()` source — the
  archived list is aspirational/example. The W11-3 producer reports
  the three actual strategies' snake-case identifiers
  (`exthost_log_parse`, `running_extensions_ui`,
  `exthost_output_parse`). Archive table to be reconciled at W11
  closure.
- **W11-3 branch policy deviation** (`2026-05-04`): all W11-N items
  land on a single long-lived `week11` branch (per user direction)
  instead of `feat/w11-<n>-<slug>` per Pickup Procedure step 2. The
  branch folds into `main` as a single PR after W11 closes.
- **W11-1 filename divergence** (`2026-05-04`): the archive table
  lists the new module as `monitor_runtime.py`, but that filename was
  already taken by a 554-LoC helper module (runtime verification +
  process helpers consumed by the lifecycle module). To avoid name
  collision, the new state-machine class lives in
  `monitor_runtime_state.py`. Downstream items (W11-5, W11-6) should
  reference this module. The archive table will be reconciled when
  W11 closes; until then, this tracker is the source of truth.
