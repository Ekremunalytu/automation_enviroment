# Post-PoC Backlog

`Last Updated: 2026-04-24 (fatal UI-crash fail-fast + scan-between VS Code restart landed)`

Work items that do not block PoC acceptance (`REFACTOR_OPTIMIZATION.md`
§10.7) and were intentionally deferred from W0-W7 for scope management.
Each entry names a stable trigger and a rough size so a future iteration
can pull it back without re-deriving context.

The PoC acceptance bar is met as of 2026-04-23. Anything below this line
is value-add, not a gate.

## Next iteration (pull first)

- **[NEXT] Split `executor/flows/playwright/monitor_attribution.py`**
  into a dedicated `attribution/` subpackage (`events.py` for event
  annotation + `_classify_event_attribution` + `_annotate_*_events`,
  `links.py` for `_build_evidence_bundle` + `_build_*_links`,
  `__init__.py` as the flat re-export facade preserving the
  private-underscore API). Size: ~1 day with full executor smoke.
  Risk: capture-pipeline regressions silently zero the detection layer
  — split must be accompanied by `make exec-up && make exec-run`
  against the A1 canary with a structural diff of the produced
  ActivationReport before and after. Deferred from W7 Phase 3b
  (2026-04-23) because Docker daemon was unavailable locally at
  closure; **this is the first item to pull in the next iteration**
  per user direction (2026-04-23).

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

- **[NEXT] Split `sim-all` (UI stress) from target-extension smoke.**
  `make sim-all`
  ([Makefile:386](../Makefile:386)) runs `entrypoint.py --monitor` with
  no target id / trigger payload. The execution plan then falls through
  to `all_scenarios`
  ([entrypoint_triggers.py:20](../executor/flows/playwright/entrypoint_triggers.py:20));
  the resulting report carries `target_extension_observed: false`,
  `automation_health.status: inconclusive`, `run_quality: inconclusive`,
  `event_attempts: 0`. In other words, `sim-all` answers *"did the
  UI-stimulus engine run?"* — **not** *"did a normal extension activate
  cleanly?"*. Add a dedicated `make sim-target TARGET=publisher.name`
  (or equivalent env-driven variant) that feeds a trigger payload +
  extension id through `entrypoint.py`, so operators can distinguish
  UI-engine health from target-activation health. `sim-all` stays as
  the stress lane; the target-smoke lane becomes the answer to
  "is normal extension path still green?". Size: half day.

## Executor / capture hygiene

- **T2 declawed samples + T3 handling + `make test-security-live`
  hardening.** ADR 0004 already covers the policy; operational plumbing
  (encrypted sample lane, rotation, per-sample license ledger) waits
  until there is an engagement that actually produces T2 data.

- **Monitor discovery-log rate-limit (cosmetic).**
  `find_exthost_logs()`
  ([monitor_sources.py:38](../executor/flows/playwright/monitor_sources.py:38))
  and `runtime_capture/extension_host.py:108` print
  `"Found N Extension Host log file(s)"` on **every** invocation.
  During `make sim-all` the real scenario-progress lines get drowned in
  the repetition. Rate-limit to "log once per discovery change" or
  demote to `logging.DEBUG`. Size: <2 h. Cosmetic — not a gate.

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
