# Post-PoC Backlog

`Last Updated: 2026-04-23 (W7 closure + sim-all crash-cascade follow-ups)`

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

- **[NEXT] Fatal UI-crash classification + fail-fast (with
  `ScenarioTrace` failure metadata).** `_run_scenario_sequence`
  ([executor/flows/playwright/automation.py:186](../executor/flows/playwright/automation.py:186))
  catches `(PlaywrightError, RuntimeError, ValueError)` and falls back
  to `_recover_ui_state`
  ([automation.py:131](../executor/flows/playwright/automation.py:131)),
  which only sends `Escape`/`FOCUS_EDITOR` on the **same** page. Once
  the renderer dies (`CodeWindow: renderer process gone, code: 5`) the
  page is dead; every subsequent scenario then cascade-fails with
  `Keyboard.press: Target crashed`. Observed 2026-04-23 on
  `make sim-all`: `settings_modification` crashed VS Code (pre-fix),
  the remaining 8 scenarios all reported the same `Target crashed`.
  Even with the settings.json fix landed, the runner must still
  distinguish fatal page/context conditions from ordinary scenario
  failures. Fix:
  1. Detect `Target crashed`, closed page/context, CDP disconnect in
     `_run_scenario_sequence`; classify as `fatal_ui_crash`.
  2. **Fail-fast** on fatal crash rather than pretending recovery
     succeeded — do not continue to the next scenario with a dead page.
     Automatic reload via `vscode.reload_workbench_window`
     ([vscode.py:176](../executor/flows/playwright/vscode.py:176)) stays
     opt-in behind an explicit `--retry-on-crash` flag; defaulting to
     auto-reload would mask the extension-triggered crash signal and
     violate ADR 0003 §5 error dominance (crash should degrade
     `automation_health` to `inconclusive`, not silently heal).
  3. Extend `ScenarioTrace`
     ([monitor_records.py:20](../executor/flows/playwright/monitor_records.py:20))
     with `failure_reason_code: str = ""` and `error_detail: str = ""`,
     populate them from `record_scenario_event`
     ([monitor_lifecycle.py:534](../executor/flows/playwright/monitor_lifecycle.py:534))
     so the report surfaces root cause on the trace itself instead of
     buried in `log_entries`.
  4. Add a cheap post-scenario liveness probe (e.g. `page.evaluate("1")`
     inside a short timeout) gated on the same fatal-crash codepath —
     avoid the full "is settings.json parseable / is extension host
     alive" battery, which adds flake for no detection value.
  Size: ~1 day. Risk: mis-classifying a transient `PlaywrightError` as
  fatal would abort a real run; keep the classifier narrow
  (explicit error-message / connection-state checks, not a broad
  catch-all).

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
