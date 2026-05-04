# W11 — Monitor Lifecycle Split (Active Work Tracker)

`Last Updated: 2026-05-04 (W11-2 landed)`

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
  `tests/executor/test_playwright_monitor_report_assembler.py` (20
  cases, imported at the real module path so the W12 reshuffle cannot
  silently regress this surface; helper stubs cover all eight
  refresh-side collaborators plus the property-derived
  `canonical_evidence_links` read) + 5 new cases in
  `tests/executor/test_extension_monitor_facade.py` pinning the
  `_RecordingAssembler` (parallel to `_RecordingRuntime`) plus the
  runtime→shim→assembler chain. Baseline grew 1102 → 1127.

  **Live-scan validation:** pending operator run against the W11-1
  baseline target (`ms-python.python@2026.5.2026042602`); behavior
  preservation asserted at unit + `make check-all` level so far.
  Operator should run `make exec-up && make sim-target
  TARGET=ms-python.python` and confirm bitwise-equal pre/post pattern
  with the W11-1 baseline (activation count = 22, network events =
  175, file events = 2515, process events = 282, scenario_traces = 3,
  log_entries = 0, run_quality = medium, automation_health =
  degraded) before merge.

  **Acceptance sub-tasks deferred** (see Acceptance Sub-Tasks section
  below for rationale): `[FOLLOWUP runner-status-contract]` rides
  W11-3 (with `activation_discovery_strategies` and the
  `schema_version` bump for one clean contract pass);
  `[FOLLOWUP target-log-lifecycle-instrumentation]` rides W11-4
  (the gap is on the producer signal — `ScenarioAccountant` — not
  the consumer; `health_reconciliation` state machine already emits
  intermediate states).
- **W11-3** — pending. `ActivationReport.activation_discovery_strategies`
  field (`packages/analysis_contracts/contracts.py`); `schema_version`
  minor bump; `tests/platform/contracts/test_activation_discovery_strategies.py`.
- **W11-4** — pending. `ScenarioAccountant` extraction
  (`executor/flows/playwright/monitor_scenario_accountant.py`, new).
- **W11-5** — pending. `ExtensionMonitor` composition facade —
  `monitor_lifecycle.py` ≤200 LoC final target (current size **672**
  after W11-1, down from 852; archive §11.8 cited 834 — module grew
  between W8 and W10). W11-5 must also remove the transitional
  delegation stubs (`_handle_*_event` shims, `_log_offsets` property)
  and inline runtime composition into the facade init.
- **W11-6** — pending. Per-strategy `_stop_<strategy>` helpers in
  `ExtensionMonitor.stop()` (warm-start, command-probe, output-channel,
  log-tail).
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
land *as part of* W11 acceptance, not as separate PRs:

- **`[FOLLOWUP runner-status-contract]`** —
  `ActivationReport.runner_exit_code` + `runner_status` enum first-class.
  Natural landing was originally W11-2 `ReportAssembler`. **Deferred to
  W11-3 `2026-05-04`** because adding fields to the contract requires a
  `schema_version` bump and a contracts-test pin, which the Verification
  Bar below already reserves for W11-3 (`activation_discovery_strategies`
  field + minor bump). Bundling both contract widenings into one pass
  keeps W11-2 a pure code-restructure (W11-1 disipline) and gives
  reviewers one clean contract diff to read. The assembler is still the
  right runtime owner of the new fields; W11-3 wires
  `assembler.set_runner_status(exit_code, status)` (or equivalent) when
  it lands the contract change. Surfaced 2026-04-25 (Codex supplementary
  review).
- **`[FOLLOWUP target-log-lifecycle-instrumentation]`** —
  Wire `reconcile_event_attempts` (or its W11 successor
  `ScenarioAccountant`/`ReportAssembler`) to emit the intermediate
  `activation_seen` / `target_log_seen` states the W10-6 frozenset
  already pinned. The W10-6 lifecycle has alphabet but no vocabulary —
  W11-4 closes the producer side. Companion W12 reconciler updates pick
  up the broader target-log capture widening. **Confirmed W11-4
  landing during W11-2 design pass `2026-05-04`:** the state-machine
  emission already exists in
  `executor/flows/playwright/health_reconciliation.py:175-220`
  (`_mark_attempt_activation_seen`, `_mark_attempt_target_log_seen`)
  and is invoked by `reconcile_event_attempts` itself; the consumer
  side is complete. The remaining gap is the **producer signal** —
  getting attempts to reach the reconciler with enough context to
  promote past `failed/blocked` — which is `ScenarioAccountant`
  territory (W11-4). Surfaced 2026-05-04 (manual UI scan).

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
  after W11-1 it is **672 LoC**; after W11-2 it is **623 LoC**; archive
  plan cited 834 LoC pre-W10. W11-5 ≤200 LoC target unchanged.
- The W11 entry table in
  `archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md` lines 2478–
  2485 is the canonical W11-N→file mapping. If split granularity
  changes during execution, update both this tracker and the archive
  table at the same time.
- **W11-1 filename divergence** (`2026-05-04`): the archive table
  lists the new module as `monitor_runtime.py`, but that filename was
  already taken by a 554-LoC helper module (runtime verification +
  process helpers consumed by the lifecycle module). To avoid name
  collision, the new state-machine class lives in
  `monitor_runtime_state.py`. Downstream items (W11-5, W11-6) should
  reference this module. The archive table will be reconciled when
  W11 closes; until then, this tracker is the source of truth.
