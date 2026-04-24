# CLAUDE.md

`Last Updated: 2026-04-24`

Read `AGENTS.md` first. It is the authoritative source for architecture and
safety rules. This file is the Claude-facing quick map for the current repo
state.

## Current Project Phase

- **Week 4 stabilization:** closed and validated on `2026-04-20`.
- **W5 (detection foundations):** landed 2026-04-20.
- **W6 (automation reliability + capture hardening):** landed 2026-04-21.
- **Post-W6 bridge (2026-04-21):** shared confidence vocabulary
  (`quantize_confidence` + `RiskSignal.confidence_tier`) and
  `detection_report_invariant_issues` cross-layer link check.
- **W6 correctness follow-up (2026-04-23):** A1/A2/A4 now gate on
  `ActivationReport` attribution (target-only via
  `target_file_events` / `target_unknown_outbound_network_events`);
  `tls_client_hello` added to `TLS_EVENT_TYPES` so live tshark captures
  actually match TLS rules; `RuleExecutionStatus.ERROR` now degrades
  automation health to `inconclusive` before verdict rollup (ADR 0003
  error dominance). `.gitignore` re-narrowed from `extensions/` to
  `extensions/*` with explicit allow-lists so the T1 canaries and the
  chat/theme benign baselines actually reach the `security-fixtures` CI
  job. Executor `monitor_package_import` test no longer leaks
  `sys.modules` state; layered `run_quality` medium now carries an
  `official_unresolved_present` reason label. **W6 closed.**
- **W7 (acceptance + buffer):** closed 2026-04-23. §10.7 PoC acceptance
  checklist met (11/11); [`documents/DEMO_SCENARIO.md`](documents/DEMO_SCENARIO.md)
  - [`scripts/demo_acceptance.py`](scripts/demo_acceptance.py) cover the A1
  credential-read → network canary end-to-end. Phase 3a buffer landed
  stretch rule `extrace.a3.typosquat`
  ([`packages/analysis_engine/rules/a3_typosquat.py`](packages/analysis_engine/rules/a3_typosquat.py),
  canary [`extensions/malicious/t1-a3-typosquat-canary/`](extensions/malicious/t1-a3-typosquat-canary/),
  allow-list [`packages/analysis_engine/allowlists/popular_extensions.txt`](packages/analysis_engine/allowlists/popular_extensions.txt)).
  Phase 3b (`monitor_attribution.py` split) deferred to
  [`documents/POST_POC_BACKLOG.md`](documents/POST_POC_BACKLOG.md)
  **marked `[NEXT]` — first item to pull in the next iteration per
  user direction (2026-04-23)**. Final `make test-security` → 41
  passed; `make check-all` → all green.
- **Post-W7 hardening (2026-04-24):** two reliability fixes landed on
  the back of the `sim-all` crash cascade and the second-scan install
  failures observed at W7 closure:
  1. **Fatal UI-crash classification + fail-fast.**
     `_run_scenario_sequence`
     ([`executor/flows/playwright/automation.py`](executor/flows/playwright/automation.py))
     now routes `PlaywrightError` / `RuntimeError` / `ValueError` through
     `is_fatal_ui_error` (explicit substring + `page.is_closed()` +
     liveness-probe eksen'leri). Renderer ölürse loop **fail-fast** durur;
     `ScenarioTrace.failure_reason_code = "fatal_ui_crash"` +
     `error_detail` set edilir; `automation_health.status` ADR 0003 §5
     error dominance gereği `inconclusive`'e degrade olur. Opt-in
     `--retry-on-crash` bayrağı `vscode.reload_workbench_window` ile
     devam eder. Contract mirror
     ([`packages/analysis_contracts/contracts.py`](packages/analysis_contracts/contracts.py))
     ve UI `contracts.ts` regen edildi. Closes the `[NEXT]` backlog
     item by the same name.
  2. **Scan-between VS Code restart (ESLint `onStartupFinished` race
     fix).** İlk taramada temiz çalışan sistem, ikinci taramada
     `code --install-extension` rc=1 ile düşüyordu — sebep bir önceki
     tarama'nın bıraktığı stale Chromium SingletonLock + ölü IPC
     socket'iydi. [`executor/flows/playwright/reset_state.py`](executor/flows/playwright/reset_state.py)
     artık workspace setup → `terminate_vscode` (SIGTERM + 5 s grace +
     SIGKILL fallback) → extensions/logs temizle →
     `cleanup_singleton_locks` → `launch_vscode` sırasıyla orkestre
     ediyor. Launch komutu
     [`executor/container/launch_vscode.sh`](executor/container/launch_vscode.sh)
     shared script'ine taşındı; `start.sh` boot'ta, `reset_state.py`
     scan-between aynı scripti çağırıyor. Opportunistic defense olarak
     [`executor/host.py`](executor/host.py) `install_extension` transient
     IPC hatalarında `reload_vscode_window` ile bir kere retry ediyor,
     [`workflows/marketplace/analysis_execution.py`](workflows/marketplace/analysis_execution.py)
     install failure emit'inde stderr tail'i (son 500 char) footer olarak
     sergiliyor — gelecekteki aynı sınıf hatalarda diagnostic susma olmasın.
  `make typecheck` temiz (207 source file), `make check-all` → 627
  passed / 5 skipped.
- **Post-W7 backlog burndown (2026-04-24):** two `[NEXT]` items from
  POST_POC_BACKLOG landed the same day, keeping the modularization +
  operator-hygiene debt aligned with the reliability fixes above.
  1. **`attribution/` subpackage split.**
     `executor/flows/playwright/monitor_attribution.py` (1122 LoC)
     split into
     [`attribution/events.py`](executor/flows/playwright/attribution/events.py)
     (event annotation + classification + shared actor/artifact/epoch
     helpers),
     [`attribution/links.py`](executor/flows/playwright/attribution/links.py)
     (evidence-bundle + scenario/temporal/noise link builders), and
     [`attribution/__init__.py`](executor/flows/playwright/attribution/__init__.py)
     (flat re-export facade preserving the 29-name underscore-prefixed
     API + signal-layer shims + dual-import pattern for paket vs
     top-level executor mode). Three callers (`monitor.py`,
     `monitor_types.py`, `monitor_lifecycle.py`) needed only the
     module-path flip (`monitor_attribution` → `attribution`).
     `make check-all` → 627 passed / 5 skipped; `make test-security`
     → 41 passed; demo acceptance → `DEMO GREEN`. **Docker-based A1
     canary structural diff (`make exec-up && make exec-run` against
     `t1-a1-credential-read-to-network-canary`) still user-side** —
     the capture-pipeline regression risk flagged in the deferral
     note closes only with a live executor smoke.
  2. **`sim-target` Makefile lane.** New target in [`Makefile`](Makefile):
     `make sim-target TARGET=publisher.name
     [TRIGGERS=/path/to/payload.json] [SCENARIO=<name>]` runs
     `entrypoint.py --monitor --target-extension-id $(TARGET)` with
     optional trigger-payload + scenario passthrough. `sim-all` is
     now explicitly labelled "UI-stimulus stress: scenarios w/o
     target ext." in `make help` + echo banner, so operators no
     longer mistake an inconclusive `sim-all` report for evidence
     that a normal extension path is green. `TARGET` required;
     missing it exits non-zero with a usage hint.
- **Post-W7 continuation (2026-04-24):** six follow-ups landed on
  the back of `sim-all` review findings. Four close report-semantics
  and loop-honesty gaps that the fail-fast hardening surfaced; one
  closes a contract backward-compat risk introduced by the
  `verdict` → `signal_summary` rename; one closes the monitor
  discovery-log spam entry on POST_POC_BACKLOG.
  1. **Legacy `verdict` → `signal_summary` migration validator.**
     `ActivationReport.model_validator(mode="before")` in
     [`packages/analysis_contracts/contracts.py`](packages/analysis_contracts/contracts.py)
     now re-maps `verdict` → `signal_summary` on the way in, so
     pre-rename fixtures and in-flight reports on disk keep parsing
     under `extra="forbid"`. Round-trip coverage lives in
     [`tests/platform/contracts/test_analysis_fixture_baselines.py::test_activation_report_accepts_legacy_verdict_field`](tests/platform/contracts/test_analysis_fixture_baselines.py).
  2. **`on_page_reloaded` callback threading (retry-on-crash fix).**
     `_run_scenario_sequence`
     ([`executor/flows/playwright/automation.py`](executor/flows/playwright/automation.py))
     now accepts an `on_page_reloaded: Callable[[Page], None]` kwarg.
     After a successful `vscode.reload_workbench_window` the new page
     reference is propagated to the caller, which `entrypoint_runner`
     uses to rebind both its own `page` closure and `mon.page` via a
     `nonlocal` hook — previously the retry path kept hammering the
     dead Page handle until the next fatal. Coverage in
     [`tests/executor/test_playwright_automation.py`](tests/executor/test_playwright_automation.py)
     (`test_retry_on_crash_invokes_on_page_reloaded_callback`,
     `test_on_page_reloaded_not_called_on_reload_failure`).
  3. **`aborted_after_fatal_ui_crash` skipped-scenario records.**
     Fail-fast no longer leaves `summary.skipped_scenarios` empty:
     `_mark_remaining_scenarios_aborted` populates a
     `SkippedScenarioRecord` for every unrun scenario with
     `reason="aborted_after_fatal_ui_crash"`, so a renderer crash at
     scenario #2 of 5 now accurately shows 3 aborted scenarios
     instead of silently dropping them. Also fires on reload-failure
     when `--retry-on-crash` is opted in but the reload itself
     raises. Coverage:
     `test_fail_fast_marks_remaining_scenarios_as_aborted`,
     `test_fail_fast_aborts_on_reload_failure_when_retry_requested`.
  4. **UI blocker probe before each scenario.** `_run_scenario_sequence`
     calls an optional `ui_blocker_probe(page, scenario_name)` kwarg
     before every scenario; `entrypoint_runner` wires it to
     `editor._dismiss_notification` and emits both
     `ui_blocker_detected` + `ui_blocker_dismissed` automation
     events (scoped exceptions: `PlaywrightError, RuntimeError,
     ValueError` — no bare `except Exception`). Previously a
     dismissal dialog left over from a prior scenario could freeze
     the next scenario's first-keystroke indefinitely with no
     evidence line. Coverage:
     `test_ui_blocker_probe_invoked_before_each_scenario`,
     `test_ui_blocker_probe_failure_does_not_break_loop`, plus
     `test_main_wires_ui_blocker_probe_and_page_reload_callbacks`.
  5. **Trimmed `scenario_terminal_usage` stimulus.** Removed
     `cat .env`, `pip list`, `npm ls --depth=0` (high-output
     commands that collided with target-owned secret-read +
     network-reconnaissance signals in attribution and, combined
     with aggressive keyboard typing, reliably triggered the
     `terminal_usage → Keyboard.type: Target crashed` cascade).
     Kept: `ls -la`, `git status`, `python --version`,
     `node --version`, `echo $PATH`, `pwd`. 250 ms warm-up added
     before each `type_in_terminal`. Adversarial stimulus belongs
     on the fixture lane, not the benign path — the rule of thumb
     is spelled out in the updated docstring.
  6. **Monitor discovery-log rate-limit (POST_POC_BACKLOG cosmetic
     item landed).** `find_exthost_logs()` in
     [`executor/flows/playwright/monitor_sources.py`](executor/flows/playwright/monitor_sources.py)
     and `runtime_capture/extension_host.py` now keep a module-level
     `_LAST_EXTHOST_LOG_COUNT` and only emit
     `"Found N Extension Host log file(s)"` when the count changes
     — `make sim-all` scenario-progress output is now readable.
  Verification: 636 pytest passes (+9 new tests),
  `make test-security` → 41 passed, `make typecheck` clean, demo
  acceptance → `DEMO GREEN`.
- **Post-PoC:** work items tracked in
  [`documents/POST_POC_BACKLOG.md`](documents/POST_POC_BACKLOG.md);
  next iteration starts from its "Next iteration (pull first)" block.
- **Security scaffolding already present:**
  - `packages/analysis_contracts/detection/`
  - `packages/analysis_engine/rules/`
  - `extensions/malicious/`
  - `tests/security/`
  - `make test-security`
  - `make test-security-live`

Use `documents/REFACTOR_STATUS.md` for current closure state and
`documents/REFACTOR_OPTIMIZATION.md` §10 for the weekly W0-W7 window.

## Scope First

- Do not load the whole repo.
- Pick one lane and stay inside it until you have enough evidence.
- Open the matching tests early.
- Ignore `extensions/`, `output/`, `node_modules/`, `legacy_ui/`, and
  `__pycache__/` unless the task explicitly depends on them.
- `routers/`, `scanner/`, `core/`, `database/`, `crud/`, `models/`, and
  `schemas/` are not canonical implementation surfaces.

## Start Files By Task

- Platform/config:
  - `main.py`
  - `appcore/api/config.py`
  - `appcore/api/deps.py`
  - `appcore/db/session.py`
  - `tests/platform/`
- Catalog/API:
  - `workflows/extension_catalog/router.py`
  - `workflows/extension_catalog/service.py`
  - `appcore/contracts/schemas.py`
  - `appcore/storage/crud.py`
  - `tests/workflows/extension_catalog/`
- Activation reports:
  - `workflows/activation_reports/router.py`
  - `tests/workflows/activation_reports/test_router.py`
- Marketplace/analysis:
  - `workflows/marketplace/router.py`
  - `workflows/marketplace/client.py`
  - `workflows/marketplace/analysis_service.py`
  - `workflows/marketplace/job_service.py`
  - `workflows/marketplace/trigger_service.py`
  - `tests/workflows/marketplace/`
- Contracts and planner:
  - `packages/analysis_contracts/`
  - `packages/analysis_planner/`
  - `packages/analysis_engine/`
- Executor:
  - `executor/control.py`
  - `executor/host.py`
  - `executor/flows/playwright/`
  - `executor/flows/playwright/runtime_capture/`
  - `tests/executor/`
- UI:
  - `ui/src/app/`
  - relevant `ui/src/features/`
  - `ui/src/lib/api/`
  - colocated `*.test.ts(x)`
- Security:
  - `documents/adrs/0002-threat-model.md`
  - `documents/adrs/0003-detection-taxonomy.md`
  - `documents/adrs/0004-malicious-fixture-policy.md`
  - `extensions/malicious/`
  - `tests/security/`

## Hard Rules

- Preserve `(publisher, name, version)` uniqueness.
- Route DB writes through `appcore/storage/crud.py`.
- Validate with Pydantic v2 before insert.
- Use SQLAlchemy 2.0 and Pydantic v2 only.
- Add Alembic migration for schema changes.
- Keep sandbox execution inside Docker.
- Do not add dependencies without explicit approval.
- No generic `try/except Exception`.
- `packages/` must stay framework-agnostic.
- Workflows reach sandbox mechanics through `executor.control`.

## Useful Commands

```bash
make dev
make test-local
make check-all
make test-security
make migrate
make exec-up
make exec-run
make ui-up
```
