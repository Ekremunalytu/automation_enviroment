# W11 — Monitor Lifecycle Split (Active Work Tracker)

`Last Updated: 2026-05-04`

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
- **W11-1** — pending. `MonitorRuntime` extraction
  (`executor/flows/playwright/monitor_runtime.py`, new).
- **W11-2** — pending. `ReportAssembler` extraction
  (`executor/flows/playwright/monitor_report_assembler.py`, new).
- **W11-3** — pending. `ActivationReport.activation_discovery_strategies`
  field (`packages/analysis_contracts/contracts.py`); `schema_version`
  minor bump; `tests/platform/contracts/test_activation_discovery_strategies.py`.
- **W11-4** — pending. `ScenarioAccountant` extraction
  (`executor/flows/playwright/monitor_scenario_accountant.py`, new).
- **W11-5** — pending. `ExtensionMonitor` composition facade —
  `monitor_lifecycle.py` 852 → ≤200 LoC (current size 852, archive
  §11.8 cited 834 — module grew between W8 and W10).
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
  Natural landing: W11-2 `ReportAssembler` (the assembler's signature is
  the right place to make the runner status a structured field).
  Surfaced 2026-04-25 (Codex supplementary review).
- **`[FOLLOWUP target-log-lifecycle-instrumentation]`** —
  Wire `reconcile_event_attempts` (or its W11 successor
  `ScenarioAccountant`/`ReportAssembler`) to emit the intermediate
  `activation_seen` / `target_log_seen` states the W10-6 frozenset
  already pinned. The W10-6 lifecycle has alphabet but no vocabulary —
  W11-4 closes the producer side. Companion W12 reconciler updates pick
  up the broader target-log capture widening. Surfaced 2026-05-04
  (manual UI scan).

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

- `monitor_lifecycle.py` is **852 LoC** as of `2026-05-04`; archive plan
  cited 834 LoC. The drift is post-W7 + W8/W9 hardening; the W11-5
  ≤200 LoC target stays unchanged.
- The W11 entry table in
  `archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md` lines 2478–
  2485 is the canonical W11-N→file mapping. If split granularity
  changes during execution, update both this tracker and the archive
  table at the same time.
