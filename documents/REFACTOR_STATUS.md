# Refactor Status

`Last Updated: 2026-05-05`

Active status board for current closure state. **Slim canonical** — full
phase closure history (W4 → W5 → W6 → W7 + post-W7 hardening + W8-0..W8-3
detail blocks) frozen under
[`archive/status/REFACTOR_STATUS_full_2026-04-29.md`](archive/status/REFACTOR_STATUS_full_2026-04-29.md).

## Current State

- **W0-W7 PoC stabilization/security window closed `2026-04-23`** —
  `REFACTOR_OPTIMIZATION.md` §10.7 PoC acceptance bar 11/11 green.
- **PR345 target activation lifecycle complete `2026-04-27`** — closure
  evidence in archive under "PR345 Complete".
- **W8-0 deterministic harness readiness gate landed `2026-04-27`** —
  capture pipeline + reason-code rollup live.
- **W8-1 VSIX zip-bomb + entry-count guard landed `2026-04-27`**.
- **W8-2 marketplace identity helper + reviewer-feedback gap closure
  landed `2026-04-27`** —
  `packages/marketplace_identity/safe_marketplace_slug` live with
  architecture regression test.
- **W8-3 URI trigger argv-form invocation landed `2026-04-28`** —
  `executor/flows/playwright/uri_validation.py` helper live; AST-based
  architecture detector pins shell-template pattern from re-appearing.
- **UI v3 redesign minimal-completion landed `2026-04-29`** — orphan v3
  components pruned, Inspector drawer + event-scoped `RuleDraftSection`
  on Reports, Run health + Coverage summary panels on Simulation,
  `design_handoff_extrace_console/` prototype retired.
- **W8-4 absolute binary paths landed `2026-04-29`** —
  `executor/binary_paths.py` constants + lazy `docker_path()` resolver;
  `host.py` 6 invocation sites switched to absolute paths; AST gate
  `tests/architecture/test_absolute_binary_paths.py` pins discipline.
- **W8-5 router regex consolidation landed `2026-04-29`** —
  `appcore/contracts/validators.py` re-imports W8-2's
  `MARKETPLACE_SLUG_TOKEN_RE`; activation-report router uses FastAPI
  `Path(..., pattern=...)` gate; AST drift gate prevents duplicate slug
  regex literals.
- **W8-7 LAN binding defaults landed `2026-04-29`** —
  `appcore/api/config.py` defaults `HOST=127.0.0.1`,
  `CORS_ALLOW_ORIGINS=http://localhost:3000`,
  `CORS_ALLOW_CREDENTIALS=False`; `model_post_init` substitutes
  `0.0.0.0` + `*` only when `EXTRACE_ALLOW_LAN` is truthy AND the field
  still holds the loopback default. `docker-compose.yml` carries
  explicit `127.0.0.1:` prefixes on every default-profile `ports:`
  entry; CDP (port `9222`) ships behind a new `executor-cdp` socat
  sidecar gated by `profiles: ["debug"]`. `Makefile` adds `dev-lan`
  and `up-debug` targets. `documents/runbooks/lan-exposure.md` live; ADR 0007
  Implementation section plus ADR 0002 §4 trust-boundary row appended;
  `tests/architecture/test_default_bindings.py` (14 cases) wired into
  the `make test-security` lane.

W8-8 (manifest log sanitization) is **deferred — not abandoned**. Audit
on `2026-04-29` confirmed no production logger call in
`workflows/extension_catalog/` or `workflows/marketplace/` currently
forwards an attacker-controlled manifest field; the four W8-8 artifacts
(`sanitize_for_log` helper, parametrized sanitization test, AST gate,
ADR 0002 §7 addendum) reopen on **either** of two named triggers:

- **Trigger A** — a future feature PR introduces the first real call
  site that logs `displayName` / `description` / `repository.url` /
  `categories[]` / `homepage` / `bugs` / `qna` / `license` from a
  parsed manifest. The W8-8 artifacts ship in the same PR so the
  helper has a real caller and the AST gate locks in the shape.
- **Trigger B** — an external review or stakeholder gate explicitly
  asks for the defense-in-depth helper before any real call site
  exists. A standalone PR ships the four artifacts and the AST gate
  is sized against synthetic fixtures.

Track: `[FOLLOWUP w8-8-manifest-emit-when-needed]` in
`POST_POC_BACKLOG.md` carries the full pickup procedure (artifact
list, file paths, retirement marker). The W8-8 plan body in
`active-work/W8-security.md` carries a `(DEFERRED 2026-04-29)` marker
and a "Deferred — NOT abandoned" callout listing the same triggers;
the threat description below the marker is the canonical statement of
the vector and survives the eventual landing flip.

With W8-7 landed and W8-8 deferred under the named triggers above,
W8 is **closed for active work** pending the optional ADR 0008 draft
on container packaging that the active-work tracker keeps as a single
remaining checkbox before W9 entry.

- **W9-1 container packaging ADR + entrypoint argv pivot landed `2026-04-30`** (`76c0760`) —
  `feat/w9-executor-detection-boundary` umbrella branch opened. ADR 0008
  (`documents/adrs/0008-container-packaging.md`) shipped as Proposed.
  `appcore/api/config.py` and `executor/config.py` migrated `*_PATH`
  literals to `*_MODULE` dotted names (no deprecation alias). `executor/host.py`
  pivoted four call sites to `[PYTHON3_PATH, "-m", <module>]` argv form;
  `pkill -f` cleanup uses dotted module name as pattern (uniqueness invariant
  per ADR 0008 §6). Container `Dockerfile` provisions
  `/home/executor/__init__.py` + `/home/executor/flows/__init__.py` regular
  package markers and sets `ENV PYTHONPATH=/home`. `start.sh` honeypot
  bootstrap pivoted to `python3 -m executor.flows.playwright.workspace`.
  `Makefile` `exec-run`/`sim-*` lanes pivoted to argv form.

- **W9-2 signal_policy relocation landed `2026-04-30`** (`55ee3f7`) —
  pure-logic signal policy moved from `executor/flows/playwright/signal_policy.py`
  into `packages/analysis_engine/signals/policy.py`; executor flows import
  via `from packages.analysis_engine.signals.policy import …`. AST gate
  `test_executor_imports_signals_from_packages`
  (`tests/architecture/test_import_graph.py:173`) regression-guards the
  detection-boundary pull.

- **W9-3 dual-import sweep + sys.path eradication + AST gates landed `2026-04-30`** (`ae0a8a7`) —
  full package-mode pivot completed in one commit (59 files changed,
  604 insertions / 1045 deletions). 39 source files converted to
  package-relative imports; 17 dual-import fallbacks removed (one
  allow-listed: `executor/flows/playwright/monitor_support.py`); 6
  `sys.path.insert` calls eliminated across runtime tree
  (`entrypoint`, `reload_vscode`, `reset_state`, `report_builder`,
  `triggers`, `workspace`). Three AST gates lock the contract in
  `tests/architecture/test_import_graph.py`:
  `test_no_dual_import_fallback_in_executor` (line 123),
  `test_no_sys_path_manipulation_in_runtime` (line 151),
  `test_executor_imports_signals_from_packages` (line 173). The
  originally separate W9-4 `sys.path.insert` audit folded into this
  commit because the AST gate is the binding artifact. ADR 0008 §6
  Outcomes block + Implementation section updated; ADR status flips
  to **Accepted**. Verification: `make check-all` (959 passed / 6
  skipped); smoke 3-test green
  (`test_ms_python_analysis_smoke`, `test_ms_python_layered_analysis_smoke`,
  `test_missing_trigger_payload_never_looks_benign`).

- **W8-7 follow-up `analysis-thread-error-detail-leakage` closed
  `2026-05-03`** on `feat/w9-executor-detection-boundary` — W8-7
  LAN-exposure trigger reached the original deferral guard.
  `workflows/marketplace/analysis_service.py::map_executor_error` now
  returns a generic public detail (`"Failed to install extension in
  executor."` / `"Automation failed in sandbox."`) suffixed with an
  8-char `error_id`; the raw `ExecutorError` text is emitted via
  `logger.warning("executor_error error_id=%s message=%s", ...)` so
  operators can correlate the response handle to the server log without
  internal paths, env values, or stderr tail content surfacing in HTTP
  responses. Regression: `tests/workflows/marketplace/test_router.py
  ::test_map_executor_error_redacts_internal_paths_and_env` (asserts
  `/etc/`, `/home/`, `POSTGRES_PASSWORD`, and the secret value are
  absent from `HTTPException.detail` while still present in the captured
  warning log record).

- **W8-9 external-review follow-up landed `2026-05-02`** on
  `feat/w9-executor-detection-boundary` — two findings closed in one
  pass. P1 workspace fixture path-traversal: new
  `_resolve_within_workspace` helper in
  `executor/flows/playwright/workspace.py` rejects absolute paths and
  `..` segments and asserts `Path.resolve().is_relative_to(WORKSPACE_DIR)`;
  `create_workspace_file` / `create_workspace_dir` / `create_bait_files`
  routed through it; `materialize_workspace_contains_fixture` catches
  the new `ValueError` and reports `prerequisite_blocked` (separate
  reason code from the existing `KeyError → materialization_failed` path).
  P2 HTTP body preview redaction: `runtime_capture/network.py::_bounded_body_metadata`
  now passes the decoded text preview through the W8-6 `redact_secrets`
  filter before assignment to `NetworkEvent.{request,response}_body_preview`;
  raw byte SHA-256 unchanged so sample integrity preserved. New
  regression tests in `tests/executor/test_playwright_stimulus.py`
  (parent-traversal + helper unit tests) and
  `tests/executor/test_playwright_monitor_runtime.py` (AKIA and Bearer
  secrets → `[REDACTED:aws]`/`[REDACTED:bearer]`). Detail block in
  `active-work/W8-security.md` W8-9 entry.

- **W9 closed `2026-05-04`** — `feat/w9-executor-detection-boundary`
  merged into `main` via PR #9 (`d67944d`). All §11.6 items landed:
  W9-1 (`76c0760`), W9-2 (`55ee3f7`), W9-3 (`ae0a8a7`), W9-4 folded
  into W9-3, W9-5 (`a38cb6f`); W9-6a..d follow-ups + W8-7 detail
  leakage close (`842fd07`) + W8-9 external-review P1/P2 (`16d6df4`)
  also rode the branch. ADR 0008 status **Accepted**. Dependency gate
  (§11.3 "W10 ← W9") green. Final exit bar:
  `make check-all` 978 passed / 6 skipped / 6 deselected.

- **W10 closed `2026-05-04`** — `feat/w10-contract-hygiene` merged into
  `main` via PR #11 (`25e4c16`). All §11.7 items landed: W10-1
  schema_version (`b9f4d6c`), W10-2 `_TriggerPayloadDraft` elimination
  (`a4d8cc8`), W10-3 `registry.py` 4-way split (`e48f179`), W10-4
  `automation_health` typing (`22f9915`), W10-5
  `validate_executor_action` enum (`b312d34`), W10-6 runtime-evidence
  state alignment (`c1d58ef`), W10-7 W8-6 output signal redaction
  (`c1e2273`); pre-W11 audit findings closed in `ec2d84c` (UI types
  drift + doc sync) and `3d3e1cd` (PR #11 review fixup — disk
  persistence + automation_health required). Dependency gate
  (§11.3 "W11 ← W10") green: typed AutomationHealth/CoverageSummary +
  schema_version 2.0 ready for the W11 monitor split assembler
  signature. Final exit bar: `make check-all` 1041 passed / 6 skipped /
  6 deselected.

- **W11 entry gate met `2026-05-04`** — `[FOLLOWUP w11-precursor-tests]`
  safety net landed: `tests/executor/test_playwright_extension_host.py`
  (23 cases) and `tests/executor/test_playwright_health_reconciliation.py`
  (15 cases) provide direct module-owned coverage for the two
  playwright god-modules touched by the W11 lifecycle split, so the
  refactor cannot regress public behavior through facade/integration
  coverage alone. W11 active tracker:
  [`active-work/W11-monitor-lifecycle.md`](active-work/W11-monitor-lifecycle.md).

- **W11-1 landed `2026-05-04`** (PR #12, commit `84d51ae`) —
  `MonitorRuntime` extraction; `executor/flows/playwright/monitor_runtime_state.py`
  (new, 334 LoC) owns the capture state machine; `monitor_lifecycle.py`
  shrank 852 → 672 LoC; `ExtensionMonitor` becomes a transitional
  facade with delegation shims pinned by
  `tests/executor/test_extension_monitor_facade.py` (9 cases) and the
  new module is pinned by
  `tests/executor/test_playwright_monitor_runtime_state.py` (14 cases).
  Baseline grew 1079 → 1102.

- **W11-2 landed `2026-05-04`** — `ReportAssembler` extraction;
  `executor/flows/playwright/monitor_report_assembler.py` (new, 158
  LoC) owns derived-state refresh (event annotation, capability
  promotion, `event_attempts` reconcile, coverage tuple,
  `signal_summary`, `evidence_links`) and the persist debounce
  throttle. ADR 0003 verdict rollup (called via
  `_build_signal_summary`) follows the move into the assembler.
  `monitor_lifecycle.py` shrank 672 → 623 LoC; `ExtensionMonitor`
  keeps thin `_refresh_derived_report_state` / `_persist_report` shims
  so the W11-1 facade pin file's bound-method-identity assertions
  remain green. Tests:
  `tests/executor/test_playwright_monitor_report_assembler.py` (22
  cases pinning collaborator stubs + persist debounce + idempotent
  refresh + monotonic throttle advance) + 5 new cases in
  `tests/executor/test_extension_monitor_facade.py` (existing 9 W11-1
  cases unchanged). Baseline grew 1102 → 1129. Acceptance sub-tasks
  deferred: `[FOLLOWUP runner-status-contract]` rides W11-3 (with the
  `schema_version` bump);
  `[FOLLOWUP target-log-lifecycle-instrumentation]` rides W11-4
  (`ScenarioAccountant` producer side; consumer-side state machine
  already lives in `health_reconciliation.py`).

  W11 (§11.8 monitor lifecycle split) **open** — W11-5, W11-6, and
  W11-7 landed `2026-05-05`; W11-8
  (`appcore/storage/crud_ops/analysis_jobs.py` split) is now the
  final structural pull-first before W11 closure. P1 companion
  `[FOLLOWUP w8-6-extension-host-output-redaction]` already landed
  `2026-05-05` ahead of W11-6.

- **W11-3 landed `2026-05-04`** on the `week11` working branch
  (commit `d4f513f`; serializer follow-up `5f4e292`; live-scan
  validation `d9a2a27`). Contract widening: `ActivationReport.activation_discovery_strategies`,
  `runner_exit_code`, and `runner_status` (with new
  `RunnerStatusLiteral = Literal["success", "error", "unknown"]`) added
  to `packages/analysis_contracts/contracts.py`; `schema_version`
  bumped `2.0` → `2.1` (W10-1 evolution discipline: stale `2.0`
  warns lenient / rejects strict). Runtime dataclass mirrors landed in
  `executor/flows/playwright/monitor_types.py`; UI contracts
  regenerated. Producer wiring: `ReportAssembler.set_runner_status` /
  `set_discovery_strategies` setters; `MonitorRuntime.stop()` tracks
  per-strategy success and emits the deduped+sorted list via a new
  callback (`exthost_log_parse`, `running_extensions_ui`,
  `exthost_output_parse`); `ExtensionMonitor` keeps thin shims so the
  W11-1 facade pin file's bound-method-identity invariants hold; the
  entrypoint runner calls `mon.set_runner_status(exit_code)` just
  before the final `report.save()`. Bundled
  `[FOLLOWUP runner-status-contract]` rode the contract bump (single
  clean contracts diff). Tests:
  `tests/platform/contracts/test_activation_discovery_strategies.py`
  (10 cases) + 5 new in
  `test_playwright_monitor_report_assembler.py` + 3 new in
  `test_extension_monitor_facade.py` + 3 new in
  `test_playwright_monitor_runtime_state.py` + `_FakeMonitor.set_runner_status`
  stub in `test_playwright_entrypoint.py`. Baseline grew 1129 → 1150;
  `make test-security` 170 cases green. Strategy-name divergence note
  and branch policy deviation captured in `active-work/W11-monitor-lifecycle.md`
  Notes/Drift section.

- **W11-4 landed `2026-05-05`** on the `week11` working branch
  (commit `f4f5df6`). `ScenarioAccountant` extraction landed in
  `executor/flows/playwright/monitor_scenario_accountant.py` (new,
  426 LoC). The collaborator owns scenario / event-attempt accounting:
  trigger-plan / execution-result intake, scenario lifecycle traces,
  event-attempt status mutation, activation-window log derivation, and
  the W11-4 producer signal (`emit_intermediate_state_events`) that
  surfaces `activation_seen` / `target_log_seen` promotions on the
  live automation timeline after `reconcile_event_attempts`. Bundled
  `[FOLLOWUP target-log-lifecycle-instrumentation]` rode the same
  commit (single producer-side closure for the W10-6 alphabet that
  previously had no vocabulary). `_assert_target_stream_invariant`
  helper relocated from `monitor_lifecycle.py` to `monitor_records.py`
  (logical home next to `LogStreamEntry`); `monitor_lifecycle`
  re-exports the symbol so the existing test pin keeps working.
  `ExtensionMonitor` keeps thin one-line shims for every moved method
  plus a new `_emit_intermediate_state_events` shim so the W11-1/2/3
  facade pin file's bound-method-identity invariants hold.
  `monitor_lifecycle.py` shrank 643 → 499 LoC (W11-5 ≤200 LoC final
  target unchanged). Tests:
  `tests/executor/test_playwright_monitor_scenario_accountant.py`
  (26 cases incl. an end-to-end integration case driving the real
  reconciler → emission chain) + 15 new W11-4 cases in
  `test_extension_monitor_facade.py` + 3 new W11-4 cases in
  `test_playwright_monitor_runtime_state.py`. Baseline grew
  1150 → 1201; `make check-all` green (lint, mypy, bandit,
  ui-types, pytest). Two live-scan validations against
  `ms-python.python@2026.5.2026042602`: the smoke run (job
  `95efbaeb721b`) confirmed the producer chain runs without
  monitor-side errors, and the trigger-driven UI run (job
  `2c1dea3c70e6`) is bitwise-equal to the W11-3 baseline
  (job `64627b3ea714`) on every detection-relevant field — refactor
  confirmed behavior-preserving end-to-end. Full validation notes in
  `active-work/W11-monitor-lifecycle.md`.

- **W11-5 landed `2026-05-05`** on the `week11` working branch.
  `ExtensionMonitor` composition facade collapsed: every transitional
  delegation stub from W11-1/W11-2/W11-3/W11-4 is removed, runtime
  callbacks bind directly to `ReportAssembler` / `ScenarioAccountant`
  methods (no shim layer), and the constructor accepts opt-in
  `runtime` / `assembler` / `accountant` / `report` kwargs for test
  injection. Three fat methods migrated off the facade onto
  `ScenarioAccountant`: `record_stimulus_pass_event`,
  `record_prerequisite_result`, and `verify_target_reaction`
  (`log_offsets` becomes an explicit positional argument so the
  accountant doesn't need a `MonitorRuntime` reference). The facade
  keeps single-statement public-API forwards so production callers
  (`entrypoint_runner.py`, `wait_helpers.py`, `stimulus_passes.py`,
  `stimulus_prerequisites.py`) need no migration. `MonitorRuntime`
  gained a `@page.setter` for the facade's `page` property to write
  through (`entrypoint_runner.py:252,261` reload-time page reassignment).
  `monitor_lifecycle.py` settled at **286 LoC** (852 → 672 → 623 →
  643 → 499 → 286 progression; the residual budget is the
  `record_automation_event` orchestration body kept facade-owned
  because both runtime and accountant get it as a callback, plus
  caller-compatibility forward shims). The `test_extension_monitor_facade.py`
  pin file shrank 891 → 499 LoC and pivoted from
  bound-method-identity invariants to composition-shape contracts;
  18 new pins (composition share-the-same-report, direct callback
  wiring, collaborator injection acceptance, public-API forwards,
  page setter writethrough, facade-owned bodies, sanity guard for
  three real collaborator instances) replace the pre-W11-5 35-case
  bound-method-identity suite. New accountant cases: 5 stimulus-pass
  - 2 prerequisite-result + 5 verify_target_reaction; one new
  runtime-state case for the `@page.setter`. Verification:
  `make check-all` green (1199 pytest cases), `make test-security`
  170 cases green. With W11-5 done, W11-6's per-strategy
  `_stop_<strategy>` helpers move to `MonitorRuntime.stop()` — the
  facade no longer owns that lifecycle.

- **W11-6 landed `2026-05-05`** on the `week11` working branch.
  Per-strategy stop helpers extracted from `MonitorRuntime.stop()`
  into three private methods on the same class —
  `_stop_exthost_log_parse` (Strategy 1),
  `_stop_running_extensions_ui` (Strategy 2, owns the
  Escape recovery branch on `PlaywrightError`), and
  `_stop_exthost_output_parse` (Strategy 3, owns the dedupe-no-credit
  semantics pinned in W11-3). Each helper returns `str | None` (the
  strategy id on a hit, `None` otherwise); `stop()` orchestrates them
  through a small for-loop that preserves the W11-3 strategy-aware
  persist cadence (`self._persist(True)` after each helper) and
  feeds the collected list to `_set_discovery_strategies`. Helpers
  do not persist on their own — pinned by
  `test_stop_exthost_log_parse_returns_name_on_activations`
  (`assert hooks.persist_calls == []` after a direct helper call).
  Per-strategy `except` types are preserved bit-for-bit (S1
  `OSError, ValueError`; S2 `PlaywrightError, OSError, ValueError`
  - inner `PlaywrightError` for the recovery branch; S3 `OSError`).
  `monitor_runtime_state.py` 369 → 429 LoC (the helpers + their
  docstrings + section header add ~60 LoC; the strategy section of
  `stop()` shrank from ~45 LoC of three try-blocks into a 12-line
  for-loop). Also reconciles the W11-3 strategy-name divergence:
  the helper method names carry the actual snake-case identifiers
  (`exthost_log_parse`, `running_extensions_ui`,
  `exthost_output_parse`) so the producer wiring → assembler →
  contract → on-disk dict reads as a single vocabulary end-to-end;
  the archive plan's aspirational names (`warm-start`, etc.) appear
  nowhere in the runtime. Tests:
  `tests/executor/test_playwright_monitor_runtime_state.py` 21 → 33
  cases (12 new per-strategy pins covering each helper's success
  path, empty-result branch, and exception-swallow contract; the
  Strategy 2 Escape recovery branch and its swallowed inner
  `PlaywrightError`; the Strategy 3 dedupe-no-credit semantics; plus
  a module-path pin asserting the three helpers stay attached to
  `MonitorRuntime` so a W12 reshuffle cannot silently move them onto
  free functions). The three pre-existing stop-level regression
  cases (`test_stop_emits_all_three_strategies_when_all_succeed`,
  `..._yield_no_entries`, `..._omits_strategy_three_when_output_parse_yields_no_new_entries`)
  stayed unmodified and green — primary behavior-preservation
  evidence at the orchestration layer. Verification: `make
  check-all` green (1222 → 1234 pytest cases, exactly the planned
  +12); `make test-security` 190 cases green; live-scan validation
  against `ms-python.python` via `make sim-target` (per W11-3/W11-4
  pattern; job `b6b52049804f4ff2a63c98eb93c74691`, 164.9s elapsed)
  — all three helpers fired in for-loop order, Strategy 1 credit
  landed (`activation_discovery_strategies == ["exthost_log_parse"]`),
  Strategy 2 recovery branch + recovery `PlaywrightError` swallow
  exercised live by a `Keyboard.press: Target crashed` macOS
  Docker UI flake (the live counterpart to the new
  `test_stop_running_extensions_ui_swallows_recovery_error`),
  Strategy 3 read 1MB of exthost output but stayed uncredited
  under the dedupe-no-credit semantics. Saved report:
  `schema_version="2.1"`, `runner_status="error"` /
  `runner_exit_code=1` (W11-3 derivation correct given the UI
  crash), `automation_health.fatal_ui_crash=true`,
  `failed_scenarios=["settings_modification"]`. The non-stationary
  delta vs. the W11-4 baseline (`job 2c1dea3c70e6`: target observed,
  S1+S2 strategies, success status) is the UI-crash branch —
  explicitly allowed by the W11-3 contract (sorted/deduped list,
  non-fixed shape) and by the W10 health vocabulary
  (`fatal_ui_crash` is the named outcome). Refactor confirmed
  behavior-preserving end-to-end.

- **W11-7 landed `2026-05-05`** on the `week11` working branch.
  Workflow-side modularization companion to the W11-1..W11-6 monitor
  split, closing audit 2026-04-27 §5 "extension_catalog/service.py
  ahtapot": `workflows/extension_catalog/service.py` (475 LoC, six
  responsibilities — manifest parse call, Pydantic schema hydration,
  ORM object-graph construction, `crud.create_extension` call, search,
  delete + getters) split into two focused modules with a thin
  back-compat facade. **`workflows/extension_catalog/manifest_to_schema.py`**
  (new, 139 LoC) owns the manifest dict → Pydantic schema → ORM
  hydration pipeline (`ExtensionManifestMismatchError`,
  `_validate_manifest_identity`, `_create_extension_from_package_json`).
  **`workflows/extension_catalog/lifecycle.py`** (new, 352 LoC) owns
  the public extension-catalog surface called by the router and the
  marketplace workflow (search/create/delete + 5 getters).
  `service.py` collapsed 475 → 64 LoC into a back-compat re-export
  facade — kept (not deleted) because three external consumers still
  hold the legacy import path: `workflows/marketplace/router.py:28-32`,
  `tests/platform/test_canonical_imports.py`, and any out-of-tree
  caller. The facade uses the mypy `--strict` re-export form
  (`name as name`) consistent with the W11-1..W11-6 facades. Router
  pivoted from `from workflows.extension_catalog import service` to
  `from workflows.extension_catalog import lifecycle`; ~10 call sites
  updated (mechanical diff, no behavioral change). Tests:
  `tests/workflows/extension_catalog/test_service.py` (297 LoC, 13
  cases) split into `test_manifest_to_schema.py` (235 LoC, 10 cases —
  hydration full-pipeline + no-extra-data branch + 6
  `_validate_manifest_identity` mismatch cases + ValueError-subclass
  shape pin + module-path pin) and `test_lifecycle.py` (286 LoC, 16
  cases — `create_extension_by_name` success/not-found,
  `create_extension_from_directory` happy + mismatch + read-error,
  the two listing getters, search + delete passthroughs, all five
  typed getter passthroughs, module-path pin, **and a facade
  back-compat re-export pin** asserting `service.X is lifecycle.X`
  for all 12 re-exported public symbols so a future facade rewrite
  swapping re-exports for shim wrappers fails here). The 23 legacy
  `mock.patch("workflows.extension_catalog.service.X", …)` sites
  were rewritten to anchor at the real execution module — required
  because `mock.patch` semantics intercept name lookup in the module
  where the call site lives, and after the split the parse_* / CRUD
  calls execute inside `manifest_to_schema` / `lifecycle`, not
  inside the `service` facade. Router test migration: ~30 patch
  sites in `tests/workflows/extension_catalog/test_router.py`
  pivoted from `…router.service.X` to `…router.lifecycle.X` to
  match the router's new import. Architecture gates added in
  `tests/architecture/test_import_graph.py`:
  `test_extension_catalog_service_stays_a_thin_facade` (AST-walks
  `service.py` and rejects any top-level statement other than
  `Import` / `ImportFrom` / module docstring / `__all__`
  assignment — the audit §5 ahtapot-closure structural lock) +
  `test_extension_catalog_service_reexports_match_canonical_modules`
  (runtime identity pin: every name in `service.__all__` resolves
  to the same object as the matching attribute on `lifecycle` /
  `manifest_to_schema`). `tests/platform/test_canonical_imports.py`
  extended with both new modules. Verification: `make check-all`
  green (1234 → 1247 pytest cases, +13 net new); `make
  test-security` 190 cases green (no detection rule touched);
  `tests/workflows/extension_catalog/` 101 cases green;
  `tests/platform/test_canonical_imports.py` and
  `tests/workflows/marketplace/test_router.py` both green
  (legacy import path through the facade resolves cleanly). No
  live-scan validation required: W11-7 has zero detection-relevant
  surface area (`schema_version` unchanged at `2.1`; no
  `ActivationReport` field touched; no producer wiring change);
  workflow router endpoints exercised by FastAPI TestClient unit
  tests.

- **`[FOLLOWUP w8-6-extension-host-output-redaction]` landed
  `2026-05-05`** on the `week11` working branch as the P1 W11
  companion ahead of the next structural pull (W11-6).
  `executor/flows/playwright/report_builder.py::build_report_data`
  now applies a **trim-then-expand-then-redact** pipeline: the
  500-line tail window is computed on the **raw** Extension Host
  line stream first, the start index walks backwards to include any
  ``-----BEGIN PRIVATE KEY-----`` marker whose matching ``END`` falls
  inside the retained tail (private helper
  `_expand_window_for_orphaned_pem`), and `redact_secrets(...)`
  (imported from `packages.analysis_contracts`) is applied once on
  the resulting window. **Two layered invariants**: (1) the
  `private_key` pattern in `packages.analysis_contracts.evidence` is
  a multi-line `-----BEGIN ... PRIVATE KEY-----` …
  `-----END ... PRIVATE KEY-----` span; if the head marker falls
  outside the retained tail (long Extension Host log with the BEGIN
  line older than the last 500 lines), the orphaned key body would
  never match a per-line pattern and would persist raw — the
  BEGIN-expansion step closes that hole. Reviewer-flagged regression
  (`Codex review #2`, `2026-05-05`) caught the orphaned-PEM body
  case in the first redact-after-trim landing. (2) An interim
  `redact-before-trim` version fixed (1) but introduced a *tail-
  window inflation* attack: a hostile extension that wraps thousands
  of attacker-controlled `console.log` lines in fake
  `BEGIN/END PRIVATE KEY` markers would see the redaction collapse
  the span to a single token, slip the 500-line cap (then computed
  on redacted lines), and surface older head lines into the
  persisted artifact. Reviewer-flagged regression (`Codex review
  #3`, `2026-05-05`) caught that vector; anchoring the cap on raw
  lines (computed before the BEGIN-expansion step) closes the hole
  while still letting the expansion pull the originating BEGIN into
  the window so the span collapses cleanly to
  `[REDACTED:private_key]`. `extension_host_output_lines` metric
  still counts raw newlines from the original capture so the field
  is not perturbed by the redaction. New regression suite
  `tests/platform/security/test_extension_host_output_redaction.py`
  (20 cases) pins the dict-emission boundary, the on-disk JSON byte
  form, the BEGIN-expansion invariant, the raw-line cap invariant,
  the trailing-newline round-trip invariant across both the short-
  input and truncated branches, and the no-drift invariants. **Pattern-class coverage**:
  AWS / Bearer / DB URL / api_key (parametrized; four of the five
  `SECRET_CLASSES`) plus multi-line `private_key` (dedicated PEM
  cases). **Boundary coverage**: dict-emission (`[REDACTED:*]` tags
  present, raw token bytes absent) plus `tempfile`-backed
  `json.dumps` byte-form pin for AWS/Bearer/DB URL and a separate
  orphaned-PEM byte-form pin (encode/decode cycle preserves
  redaction). **BEGIN-expansion invariant**: three PEM cases —
  orphaned body (BEGIN @line 100, body @101-600, END @601, 50-line
  suffix; raw tail window starts at line 152 so BEGIN drops without
  expansion; reviewer #2's exact scenario), fully-inside-tail
  (sanity), fully-outside-tail (token drops with the head, no raw
  bytes either way). **Tail-window inflation invariant**
  (`test_extension_host_output_tail_window_resists_pem_collapse_inflation`,
  reviewer #3's scenario): 800 attacker-controlled prefix lines +
  5000-line synthetic PEM body + 100-line suffix; pins that no
  `attacker prefix N` reaches the persisted dict while
  `benign suffix N` (inside the original raw tail) does. The
  body-inside-tail orphaned-PEM case also asserts that the head
  prefix lines (lines 0..99) do not slip into the persisted dict
  via collapse-driven inflation. **Metric invariant**:
  `extension_host_output_lines` reports the raw capture's newline
  count (not the redacted form) — pinned so a future "consistency"
  refactor that switches the metric to the persisted text fails
  here, since PEM redaction collapses many lines into one and the
  metric must still reflect the original capture length.
  **Composition invariant**: mixed-secret-classes-in-single-buffer
  pins that AWS + Bearer + DB URL + api_key + PEM all redact in the
  same buffer without one pattern consuming text another needed;
  benign framing lines around the secrets are preserved (no
  over-match). Idempotency, benign-payload preservation, and the
  500-line tail-trim with a trailing-line secret are pinned as
  additional no-drift cases.
  `tests/platform/security/test_content_sample_typing.py`
  `_PENDING_MIGRATION` extended with `(ActivationReport,
  "extension_host_output")` so the W13 `§11.10` contract-level
  migration prompt flips XPASS → fail when the field is typed as
  `ContentSample`. No schema migration (string shape unchanged; only
  content filtered). Verification: `make test-security` green;
  `make check-all` 1222 passed (baseline 1218 → 1222). Closes the
  `extension_host_output` redaction gap; the broader
  `[FOLLOWUP w8-6-content-sample-structural-test]` audit sweep stays
  open as the parent backlog item.

- **CI pipeline retired `2026-04-30`** — `.github/workflows/ci.yml` and
  `.github/workflows/docs-check.yml` removed; `security.yml` (weekly
  Trivy + Bandit) kept. The `security-fixtures` job (iptables egress
  sandbox) was the persistent flake source; its protections are
  Makefile-enforced (`test-security-live` refuses under `CI=true`)
  and the security fixture lane itself runs locally via
  `make test-security` (pure pytest, no network). A new `pre-push`
  pre-commit stage runs `make check-all` before push as the local
  gate. ADR 0004 carries a 2026-04-30 addendum spelling out the
  policy change. Reintroduction trigger logged as
  `[FOLLOWUP ci-reintroduction]` in `POST_POC_BACKLOG.md`.

## Subsystem Posture

- Async marketplace job state durable in PostgreSQL via `analysis_jobs`.
- Activation reports artifact-first under `output/activation_report_*.json`.
- Workflow code reaches sandbox through `executor.control` only.
- W5 detection surfaces wired:
  `packages/analysis_contracts/detection/`,
  `packages/analysis_engine/rules/` (A1/A2/A4/A6 with target-only
  attribution), `extensions/malicious/` (T1 canaries with `LABEL.yaml`),
  `tests/security/`, plus `make test-security` and
  `make test-security-live`.
- Legacy directories (`routers/`, `scanner/`, `core/`, `database/`,
  `crud/`, `models/`, `schemas/`) and dormant placeholders (`apps/`,
  `legacy_ui/`) removed from canonical surface.
- Canonical runtime tree: `appcore/`, `packages/`, `workflows/`,
  `executor/`, `ui/`, `tests/`.

## Open Deferrals

Authoritative open list lives in
[`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md). Highlights:

- `[FOLLOWUP w8-0-capture-pipeline]` — W8-3 live smoke (2026-04-28)
  closed acceptance signal (a); typed harness-readiness reason codes
  (signal b) remain unconfirmed live.
- `make test-security` lane composition — W8-1 + W8-3 tests live in
  subsystem-local lanes; either extend Makefile target or update
  `active-work/W8-security.md` exit criterion to count broader tally.
- Docker-based smoke (`make exec-up && make sim-target`) user-side.
- UI v3 follow-ups: see `[CLEANUP ui-v3-9/14]`, `[ADD ui-v3-10/11/12]`,
  `[BACKLOG ui-v3-13]` in `POST_POC_BACKLOG.md`.

## Read Order (When Updating This File)

1. `AGENTS.md`
2. `documents/AGENT_CONTEXT.md`
3. this file
4. `documents/agent-lanes/<matching-lane>.md`
5. subsystem doc only when the lane doc points to it

When a closure entry would expand this file past ~300 lines, drop a new
dated full snapshot under `archive/status/` and re-trim — see
`agent-lanes/docs-maintenance.md` invariants.

## Archive

Full phase closure history (W4 → W5 → W6 → W7 acceptance, post-W7
hardening, PR345 + W8-0/W8-1/W8-2/W8-3 verbose closures, change
diffs, verification matrices):
[`archive/status/REFACTOR_STATUS_full_2026-04-29.md`](archive/status/REFACTOR_STATUS_full_2026-04-29.md).
