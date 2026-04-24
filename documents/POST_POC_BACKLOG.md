# Post-PoC Backlog

`Last Updated: 2026-04-24 (attribution/ subpackage split + sim-target Makefile lane landed)`

Work items that do not block PoC acceptance (`REFACTOR_OPTIMIZATION.md`
§10.7) and were intentionally deferred from W0-W7 for scope management.
Each entry names a stable trigger and a rough size so a future iteration
can pull it back without re-deriving context.

The PoC acceptance bar is met as of 2026-04-23. Anything below this line
is value-add, not a gate.

## Next iteration (pull first)

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
