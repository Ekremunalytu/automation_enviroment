# W12 — Executor Subpackaging + Attribution Cleanup (Active Work Tracker)

`Last Updated: 2026-05-10 (W12 closed; merged via PR #18 (33a0852); tracker frozen for stable-ID reference)`

This is the canonical active work tracker for the W12 executor
subpackaging + attribution cleanup window. Items have stable IDs
(`W12-1` … `W12-4`). Code comments, tests, and ADR addenda will
reference items by ID — **keep IDs stable** when reorganizing.

This file mirrors the structure of `W11-monitor-lifecycle.md`. Slim
canonical `REFACTOR_OPTIMIZATION.md §11.9` only carries a 4-line
summary plus the §11.9.1 `runtime_capture/extension_host.py` split
scoping addendum; full historical detail at
`archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md §11.9`. Pick
up an item by reading this tracker, the slim canonical §11.9/§11.9.1,
and that archive section.

## Status (Quick Glance)

- **W12 closed `2026-05-10`.** All seven scope items landed on
  `week12`: W12-0 (security pull-forward), W12-1 (executor
  subpackaging), W12-2 (attribution facade cleanup), W12-3
  (raw_context discriminated union), W12-4 (entrypoint dispatch
  extraction), W12-5 (extension_host ahtapot split + body-preview
  gate), plus UI Dockerfile digest pin, W12 close-out test coverage,
  and Codex audit CRITICAL fix (`executor/host.py` retry/reload
  subprocess-output redaction in commit `e42e79c`). Final exit bar
  (post-Codex-fix re-run): `make check-all` ✅ green; `make test-local`
  1452 passed / 6 skipped / 6 deselected / 75 warnings;
  `make test-security` 211 passed / 32 warnings;
  `tests/architecture/` 76 passed / 2 deselected. Live-scan
  bitwise-equal validation on `ms-python.python@2026.5.2026050801`
  confirmed (17/17 detection-relevant fields, job IDs `6fab298e81a1`
  / `e5e33ec6e34f`). Authoritative current-state pointer:
  [`documents/REFACTOR_STATUS.md`](../REFACTOR_STATUS.md).
  Single-branch policy honored: `week12 → main` merged via PR #18
  (`33a0852`) on `2026-05-10` (W11 PR #14 precedent). Tracker frozen
  for stable-ID (`W12-1`..`W12-5`) reference.
- **Pre-W12 attribution precursor tests landed.**
  `[FOLLOWUP w12-precursor-tests-attribution-links]` and
  `[FOLLOWUP w12-precursor-tests-attribution-events]` both closed in
  commit `5ae0d32` on `2026-05-07`; tests now live at
  `tests/executor/test_playwright_attribution_links.py` and
  `tests/executor/test_playwright_attribution_events.py`. Companion
  plan-level item `[FOLLOWUP w12-extension-host-split-scoping]` closed
  by the §11.9.1 addendum on PR #15 (no code change).
- **W12-0 (precursor — security pull-forward) — landed
  `2026-05-07` (`22eb836`).**
  `[FOLLOWUP w8-6-output-signals-file-backed-redaction]` closed.
  `redact_secrets(_truncate(line))` applied to the file-backed
  `read_output_channel_logs` path (current post-W12-1 path:
  `executor/flows/playwright/signals/output.py`; landing path:
  `output_signals.py`). W10-7 source comment updated to name both
  harness-marker and file-backed paths. Single-branch policy override:
  W12-0 landed as the first commit on `week12` (commit-level isolation
  in lieu of a standalone pre-W12 PR), so the refactor commits that
  follow can still be reverted independently. Surfaced 2026-05-07 audit
  pass.
- **W12-1** — landed `2026-05-07`. Executor subpackaging:
  `executor/flows/playwright/` 54 flat files → 7 new subpackages
  (`monitor/`, `stimulus/`, `workspace/`, `health/`, `entrypoint/`,
  plus `vscode/` and `signals/` to satisfy ≤10 flat) + existing
  `attribution/`, `scenarios/`, and `runtime_capture/` packages + 10
  flat. Import-graph rule landed:
  `monitor/` and `stimulus/` cannot import each other (gate
  `test_monitor_and_stimulus_subpackages_do_not_cross_import`).
  Lazy `__getattr__` in `monitor/__init__.py` breaks the
  attribution↔monitor cycle introduced by `monitor.records`
  becoming a subpackage member; gate
  `test_monitor_facade_does_not_eagerly_import_attribution`
  prevents regression. `__main__.py` shim added at
  `entrypoint/__main__.py` so `python -m
  executor.flows.playwright.entrypoint` keeps working.
  **2026-05-07 follow-up fix:** `workspace/__main__.py` shim was
  missing — `executor/container/start.sh:89` invokes
  `python -m executor.flows.playwright.workspace` to seed the
  honeypot, but the package conversion left only an
  `if __name__ == "__main__"` block in `workspace/__init__.py` which
  is dead code under `-m`, so container boot would fail with
  `No module named ...workspace.__main__`. Added `workspace/__main__.py`
  shim, removed the dead block, and locked the invariant with a new
  architecture gate
  `test_python_m_playwright_invocations_have_main_module` that scans
  `executor/container/*.sh`, `appcore/api/config.py`, and
  `executor/config.py` for `python -m executor.flows.playwright.<X>`
  references and asserts each `<X>` is either flat or has a
  `__main__.py`. Live-scan still deferred to W12 close (Iteration 6).
  See "Detailed Item Notes" below.
- **W12-2** — landed `2026-05-07` across four commits on `week12`:
  `37fcaad` (facade rename + caller migration), `0cef876` (naming-overlap
  rename), `9ebc5b5` (coverage-summary unify), `0981e92` (P3 strategy
  outcome dict). Attribution facade trimmed from 29 underscore re-exports
  to 10 public names; caller migration in `monitor/lifecycle.py`,
  `monitor/report_assembler.py`, `monitor/scenario_accountant.py`,
  `monitor/types.py`. All three companion follow-ups closed:
  `[FOLLOWUP w12-attribution-naming-overlap]` (rename to
  `target_background_activation_count` /
  `competing_extension_event_count`),
  `[FOLLOWUP coverage-summary-attempted-drift]` (assembler collapses
  top-level `attempted_capabilities` to the runtime-derived view before
  coverage reconcile), and
  `[FOLLOWUP activation-discovery-strategy-outcome-detail]` (P3 — field
  upgraded from `list[str]` to
  `activation_discovery_strategy_outcomes: dict[str, str]` with
  outcome literals `succeeded_with_new_activations` /
  `succeeded_no_new_activations` / `failed:<ExcClassName>`).
  See "Detailed Item Notes" below.
- **W12-3** — landed `2026-05-07`. `raw_context` discriminated union typing:
  `EvidenceEvent.raw_context: dict[str, Any]` →
  `RawContext = Annotated[NetworkRawContext | FileRawContext |
  ProcessRawContext | ScenarioRawContext | ActivationRawContext |
  UiBlockerRawContext | OutputChannelRawContext,
  Field(discriminator="event_class")]`. The literal §11.9 plan named only
  the three Network/File/Process variants; the W7+W11 `EvidenceEvent`
  consolidation broadened the live producer surface to seven `kind`s, so
  the union covers all seven (3 named + 4 extra). New test file
  `tests/platform/contracts/test_raw_context_discriminated.py` (8 cases).
  Incidental: `_common.py::event_method` now reads the producer's actual
  `http_method` key (was looking for the never-emitted `method`); a4
  workspace-exfil canary stops misfiring on TLS-only fallback paths.
  Closes the `EvidenceEvent.raw_context` entry of
  `_PENDING_MIGRATION` in
  `tests/platform/security/test_content_sample_typing.py`.
- **Pre-W12-4 hardening pull-forward (added `2026-05-07` audit pass).**
  W12-3 close denetimi iki sertleştirme öğesini açığa çıkardı; ikisi
  de W12-4 dispatch extraction'ından **önce** landlanacak ve W12 close
  acceptance bar'ına dahil:
  - ~~`[FOLLOWUP w12-0-output-signal-multiline-secret-redaction]`~~ —
    **CLOSED `2026-05-08`.** Cross-line `private_key` pattern'i artık
    `redact_multiline_secrets` helper'ı (`evidence.py`'ye eklendi)
    aracılığıyla iki yolda da pre-pass olarak uygulanıyor:
    file-backed (`read_output_channel_logs`) ve harness-marker
    (`parse_output_signal_events`). Single-line pattern'lar (api_key /
    db_url / aws / bearer) per-marker / per-line `redact_secrets`'ta
    kaldı çünkü whole-input uygulama JSON marker yapısını bozabiliyor
    (api_key opsiyonel trailing-quote'u yutar). 4 yeni regression
    `test_output_signals_redaction.py`'de:
    file-backed multi-line PEM block, file-backed PEM with surrounding
    diagnostic lines, harness-marker cross-marker PEM (3 ayrı appendLine),
    harness-marker single-marker embedded-newline PEM. See "Detailed Item
    Notes" below.
  - ~~`[FOLLOWUP api-docker-base-image-digest-pin]`~~ — **CLOSED
    `2026-05-09`.** `docker/api/Dockerfile:2` artık
    `python:3.11-slim-bookworm@sha256:cd67330292a51e2963156f74ff340455d66b2172e9190e99f40dff9357471177`
    formunda; yeni `tests/architecture/test_dockerfile_digest_pin.py`
    gate'i API + executor Dockerfile `FROM` satırlarını pinliyor. See
    "Detailed Item Notes" below.
- **W12-4** — landed `2026-05-10` on `week12`. `entrypoint/runner.py::main`
  dispatch extraction: `main()` **324 LoC → 99 LoC** (limit ≤200, comfortably
  under). New `entrypoint/dispatch.py` (402 LoC) owns: `PageRef`
  mutable page-reference wrapper (replaces `nonlocal page` rebind across
  module boundary), `setup_monitor`, `make_page_callbacks`,
  `dispatch_execution` (the 6-way mode dispatch — `demo` /
  `skip_automation` / `layered_passes` / `selected_scenarios` /
  `single_scenario` / default-all), `apply_extra_triggers_if_needed`,
  `summarize_skipped_scenarios_if_needed`, `finalize_monitor_report`,
  plus the deps-binding helpers `_run_demo_for_deps` /
  `_run_extra_triggers_for_deps` and the execution-result helpers
  `_empty_execution_result` / `_normalize_execution_result` (only
  dispatch path consumes them post-W12-4). `runner.py` total 494 → 196
  LoC. Two new architecture gates in
  `tests/architecture/test_runner_main_loc_budget.py`:
  `test_runner_main_under_loc_budget` (AST gate, 200 LoC ratchet) and
  `test_runner_main_dispatch_helpers_remain_imported` (pins the
  contract that dispatch.py owns the heavy lifting). See
  "Detailed Item Notes" below.

## Entry Conditions

- W11 closed (✓ met `2026-05-05` — all W11-1..W11-8 landed via PR #14)
- W11 precursor tests landed (✓ met `2026-05-04` —
  `tests/executor/test_playwright_extension_host.py` 23 cases +
  `tests/executor/test_playwright_health_reconciliation.py` 15 cases)
- W12 precursor tests landed (✓ met `2026-05-07` —
  `tests/executor/test_playwright_attribution_links.py` 26 cases +
  `tests/executor/test_playwright_attribution_events.py` 34 cases,
  imported at real module path; safety net for W12-2 attribution
  refactor)
- W12-0 security pull-forward landed (✓ met `2026-05-07` —
  `[FOLLOWUP w8-6-output-signals-file-backed-redaction]` closed in
  commit `22eb836` on `week12`; file-backed output-signal redaction
  fix now lives under `signals/output.py` after W12-1, plus four
  file-backed regressions and three harness-marker end-to-end regressions in
  `tests/platform/security/test_output_signals_redaction.py`)
- §11.9.1 plan addendum (✓ landed on `chore/pre-w12-prep`) defining
  the `runtime_capture/extension_host.py` split target
- Single W12 branch policy active on `week12` (commit-level isolation
  for W12-0..W12-4; one PR at W12 close)
- Entry baseline: `make check-all` green at W11 close (`1274`) and
  `make test-security` 190 cases; latest W12-2 check bar is recorded
  in `REFACTOR_STATUS.md`

## Exit Criteria

- [x] `executor/flows/playwright/` flat file count 54 → ≤10
- [x] 7 new subpackages ({`monitor`, `stimulus`, `workspace`, `health`,
      `entrypoint`, `vscode`, `signals`}/) plus existing
      `attribution/`, `scenarios/`, and `runtime_capture/`; import-graph
      rules isolate the sensitive boundaries
- [x] `attribution/__init__.py::__all__` lists 10 public names;
      underscore-prefixed helpers are internal-scoped
- [x] `raw_context` typed discriminated union; `dict[str, Any]`
      residue = 0 in evidence models
- [x] `entrypoint/runner.py::main` 324 LoC → ≤200 LoC; dispatch logic
      in `entrypoint/dispatch.py` (landed `2026-05-10`; `main()` 99 LoC)
- [x] Import-graph gates green; W12-close `make check-all` /
      `make test-security` acceptance bar dry run recorded in
      `documents/archive/active-work/W12-close-acceptance-completed-2026-05-10.md` §3 (final
      `make check-all` tail attached at merge time).
- [x] Live-scan validation: pre/post bitwise-equal detection-relevant
      fields on a target run — completed `2026-05-10` on
      `ms-python.python@2026.5.2026050801` (17/17 fields identical;
      job IDs `6fab298e81a14bf8a7a557a13953e57b` /
      `e5e33ec6e34f4993b795664d83e25fd4`; evidence in
      `W12-close-acceptance-completed-2026-05-10.md` §3.4).

## Acceptance Sub-Tasks (W12-N picks up these follow-ups)

These `[FOLLOWUP ...]` items in `POST_POC_BACKLOG.md` are scheduled
to land before or during W12 acceptance. Refer by stable ID, not line
number.

- ~~`[FOLLOWUP w12-precursor-tests-attribution-links]`~~ —
  closed `2026-05-07` in commit `5ae0d32`.
- ~~`[FOLLOWUP w12-precursor-tests-attribution-events]`~~ —
  closed `2026-05-07` in commit `5ae0d32`.
- ~~`[FOLLOWUP w12-attribution-naming-overlap]`~~ — closed `2026-05-07`
  in commit `0cef876` (rename to `target_background_activation_count`
  / `competing_extension_event_count`).
- `[FOLLOWUP w12-extension-host-split-scoping]`
  — plan-level addition to slim canonical §11.9.1; closed by PR #15
  (no code change). Implementation deferred to W12 entry; lands as
  ahtapot pattern.
- ~~`[FOLLOWUP coverage-summary-attempted-drift]`~~ — closed
  `2026-05-07` in commit `9ebc5b5` (assembler syncs top-level
  `attempted_capabilities` and `heuristic_attempted_capabilities` to the
  runtime-derived `event_attempts` view before coverage reconcile so the
  top-level report fields and `coverage_summary` resolve to one value).
- ~~`[FOLLOWUP activation-discovery-strategy-outcome-detail]` (P3)~~ —
  closed `2026-05-07` in commit `0981e92`. Field upgraded from
  `activation_discovery_strategies: list[str]` to
  `activation_discovery_strategy_outcomes: dict[str, str]`; helpers
  emit per-strategy outcome literals (succeeded_with_new_activations
  / succeeded_no_new_activations / failed:<ExcClassName>).
- ~~`[FOLLOWUP w8-6-output-signals-file-backed-redaction]`~~ —
  closed `2026-05-07` on `week12` in commit `22eb836` (W12-0
  precursor). File-backed redaction fix plus seven new regression
  tests (4 file-backed, 3 harness-marker end-to-end) in
  `tests/platform/security/test_output_signals_redaction.py`.
- `[FOLLOWUP arch-gate-network-body-preview-redaction]`
  (`POST_POC_BACKLOG.md` Engineering Quality, **P2**) — optional
  W12-1 companion (defense-in-depth structural gate sibling to
  the existing AST-gate suite). Land if W12-1 has spare review
  capacity; otherwise defer to W13.
- ~~`[FOLLOWUP ui-docker-base-image-digest-pin]`~~ — closed
  `2026-05-10` on `week12` in commit `a27eb84`. `ui/Dockerfile` stages
  `node:20-alpine` and `nginx:1.27-alpine` now pinned by manifest-list
  digest (`@sha256:fb4cd1...` / `@sha256:65645c...`);
  `tests/architecture/test_dockerfile_digest_pin.py::DOCKERFILE_ROOTS`
  extended with `ROOT / "ui"`. Gate green; ADR 0002 §4 trust table
  now 100% (3/3 runtime images).
- ~~`[FOLLOWUP w12-0-output-signal-multiline-secret-redaction]`~~ —
  closed `2026-05-08` on `week12`. Multi-line PEM redaction landed via a
  new `redact_multiline_secrets` helper applied as a pre-pass on both
  file-backed and harness-marker paths in `signals/output.py`; 4 new
  regressions in `test_output_signals_redaction.py`.
- ~~`[FOLLOWUP api-docker-base-image-digest-pin]`~~
  (`POST_POC_BACKLOG.md` W12 Pull-Forward, **P1, pre-W12-4**) —
  closed `2026-05-09`; ADR 0002 §4 base-image pin drift removed.
- ~~`[FOLLOWUP marketplace-installer-tail-multiline-redaction]`~~
  (`POST_POC_BACKLOG.md` W12 Pull-Forward, **P2, pre-W12-4 / W13-X**) —
  closed `2026-05-09`; `install_failure_message()` now applies
  `redact_multiline_secrets(output)` before tailing, then the existing
  single-line `redact_secrets(...)` pass. Regression:
  `test_install_failure_message_redacts_multiline_pem_split_by_tail`.

## Detailed Item Notes (filled as items land)

### W12-0 — Output-Signals File-Backed Redaction (landed `2026-05-07`)

- **Scope.** Closes
  `[FOLLOWUP w8-6-output-signals-file-backed-redaction]`. The W10-7
  sweep covered the harness-marker `parse_output_signal_events` path
  but missed the file-backed `read_output_channel_logs` path, which
  is the primary OutputChannel source on VS Code 1.105+ (extensions'
  `console.log` no longer reaches `exthost.log`; VS Code persists
  the content directly to
  `<user-data>/logs/<session>/window<N>/exthost/output_logging_<ts>/<idx>-<channel>.log`).
- **Fix.** Single-line change in the file-backed
  `read_output_channel_logs` construction path
  (`text = _truncate(line)` → `text = redact_secrets(_truncate(line))`).
  Current post-W12-1 path:
  `executor/flows/playwright/signals/output.py` (landing path was the
  pre-move `executor/flows/playwright/output_signals.py`). Source
  comment rewritten to name both paths and call out the W12-0 precedent
  so future readers see the symmetry rule.
- **Tests added.** Seven new regressions in
  `tests/platform/security/test_output_signals_redaction.py`:
  - File-backed (`read_output_channel_logs`) bearer / db_url / aws
    (JSON payload) / benign round-trip (4 cases).
  - Harness-marker end-to-end (`parse_output_signal_events`) db_url
    / aws / benign round-trip (3 cases) — closes the unit-only
    coverage gap left by the W10-7 chain test.
- **Live-scan validation.** Pre/post comparison on
  `output/activation_report_ms-python.python-2026.5.2026042602-*.json`
  (13:09 vs 14:53 on `2026-05-07`): runner_status / activated /
  scenario verdicts / output_signal_events count (12) all
  identical; no benign harness-diagnostic content was redacted by
  mistake (no `[REDACTED:*]` tag introduced where none was warranted).
- **Branch policy note.** Per the user-imposed single-branch policy
  for W12, W12-0 landed as the first commit on `week12` rather than
  as a standalone pre-W12 PR (tracker §"W12-0 (precursor)" originally
  required the latter). Commit-level isolation preserves the
  cherry-pick / revert ergonomics the standalone-PR rule was after.

### W12-1 — Executor Subpackaging (landed `2026-05-07`)

- **Scope.** `executor/flows/playwright/` 53 flat `.py` (54 with
  `__init__.py`) → 7 new subpackages + 10 flat. New subpackages
  (`monitor/`, `stimulus/`, `workspace/`, `health/`, `entrypoint/`,
  `vscode/`, `signals/`) plus existing `attribution/` (W7) and
  `scenarios/` (W7) and `runtime_capture/` (W7). Flat leftover
  exactly at the ≤10 budget: `__init__.py`, `annotation.py`,
  `automation.py`, `capture.py`, `reload_vscode.py`,
  `report_builder.py`, `reset_state.py`, `triggers.py`,
  `uri_validation.py`, `wait_helpers.py`. Two extra subpackages
  (`vscode/`, `signals/`) beyond the plan's 5 named were required to
  satisfy Exit Criteria #1 (≤10 flat) — the named 5 alone would have
  left ~22 flat siblings. `vscode/` collects the VS Code UI surface
  (panel, sidebar, editor, keyboard, terminal, commands, settings,
  debug) plus the CDP connection module; `signals/` collects the
  signal facade + facts + output redaction. `reload_vscode` and
  `reset_state` stay flat because `appcore/api/config.py` and
  `executor/config.py` resolve them as runtime subprocess module
  paths (changing those config strings would broaden the blast
  radius unnecessarily).
- **44 file relocations** via `git mv` preserving rename history
  (e.g. `monitor_lifecycle.py` → `monitor/lifecycle.py`,
  `signal_facts.py` → `signals/facts.py`, etc).
- **Import rewrite.** A scoped Python rewriter (kept in
  `/tmp/w12_1_rename_imports.py` during the refactor; not committed)
  walked the whole repo (1852 files scanned) and rewrote three
  forms: absolute `executor.flows.playwright.OLD` →
  `executor.flows.playwright.NEW`, relative `from .OLD import` /
  `from .. OLD import` (location-aware), and aggregator
  `from . import (...)` / `from executor.flows.playwright import
  (...)` blocks (splitting renamed names into per-subpackage import
  lines, preserving local names with `as` aliases where needed).
  ~63 source files plus ~12 test files updated.
- **Circular import resolved (W12-1 design pin).** The W7 attribution
  subpackage and the new monitor subpackage form a bidirectional
  module-load dep: `attribution.events` / `attribution.links` import
  `ScenarioTrace` / `EvidenceEvent` / `EvidenceLink` /
  `RiskSignal` from `..monitor.records`, and `monitor/__init__.py`
  re-exports the historical `_annotate_*` / `_build_*` /
  `_format_epoch_timestamp` surface from `..attribution`. Pre-W12-1
  this was masked because `monitor_records.py` was a flat module —
  loading it did not trigger a `monitor` package init. After W12-1,
  `monitor.records` is a submodule of the `monitor/` package, so any
  load of `monitor.records` runs `monitor/__init__.py` first, which
  re-enters the partially-loaded `attribution` and raises
  `ImportError`. **Fix:** PEP 562 `__getattr__` proxy in
  `monitor/__init__.py` for the attribution surface (15 names) and
  for `.lifecycle` / `.types` (which themselves eagerly import from
  `..attribution`). Plus a lazy `from ..monitor.records import
  RiskSignal` inside `attribution/__init__.py::_build_risk_signals`
  (the only true runtime use; the rest are TYPE_CHECKING-only since
  `from __future__ import annotations` makes annotations strings).
  All callers see the historical flat re-export shape; the cycle is
  broken.
- **Architecture gates added.** Two new tests in
  `tests/architecture/test_import_graph.py`:
  - `test_monitor_facade_does_not_eagerly_import_attribution` —
    AST gate that fails if monitor's `__init__.py` re-introduces a
    top-level `from ..attribution import ...` (would re-create the
    cycle).
  - `test_monitor_and_stimulus_subpackages_do_not_cross_import` —
    enforces the W12-1 topology line: monitor/ and stimulus/ may
    not directly reference each other; share via flat parent
    helpers.
- **Allow-list paths updated.** `_DUAL_IMPORT_ALLOW_LIST` updated
  from `monitor_support.py` to `monitor/support.py`.
  `test_executor_imports_signals_from_packages` repointed at
  `signals/__init__.py`.
- **`__main__.py` shims** required wherever `python -m` invokes a
  newly-converted package. Two such targets exist in the runtime
  tree:
  - `entrypoint/__main__.py` — added in the W12-1 commit so
    `python -m executor.flows.playwright.entrypoint` continues to
    invoke `main()`.
  - `workspace/__main__.py` — **added 2026-05-07 as a follow-up
    fix** after the original W12-1 commit shipped without it.
    `executor/container/start.sh:89` runs
    `python -m executor.flows.playwright.workspace` to seed the
    honeypot at container boot; the bare `if __name__ == "__main__"`
    block left in `workspace/__init__.py` is dead under `-m`
    semantics (Python looks for `__main__.py`), so the container
    would have failed boot with
    `No module named ...workspace.__main__`. The dead `__init__`
    block was removed; the shim delegates to `setup_dev_environment`.
  Reasoning: under `python -m <package>`, Python imports
  `<package>` (running `__init__.py` for side effects only), then
  imports and executes `<package>.__main__`. The
  `if __name__ == "__main__"` guard inside `__init__.py` never
  fires because `__init__` is loaded with `__name__ == "<package>"`,
  not `"__main__"`.
- **Architecture gate for `python -m` invocations** added at
  `tests/architecture/test_import_graph.py::test_python_m_playwright_invocations_have_main_module`.
  Scans `executor/container/*.sh`, `appcore/api/config.py`, and
  `executor/config.py` for every `python -m
  executor.flows.playwright.<X>` reference (shell direct + settings
  defaults consumed by `executor/host.py` `subprocess.run`),
  enumerates the targets, and asserts each is either a flat
  `<X>.py` (case for `reload_vscode`, `reset_state`) or a package
  with `<X>/__main__.py` (case for `entrypoint`, `workspace`). A
  future PR converting another flat module to a package without a
  shim fails this gate before container boot regresses.
- **Tests.** `make check-all` 1345 passed / 6 skipped / 6 deselected
  (was 1342 baseline at W12-0; +3 from the two new architecture
  gates and one rewriter scaffolding update). `make test-security`
  197 passed (unchanged). New 12-test architecture suite all green.
- **Live-scan.** Deferred to W12 close (Iteration 6) verification —
  Docker `automation_executor` container not running locally during
  W12-1 implementation. Sanity-checked instead by invoking
  `python -m executor.flows.playwright.entrypoint --list` which
  enumerates 13 scenarios end-to-end (proves package import +
  scenarios registry resolution survive the relocations).

### W12-2 — Attribution Facade Underscore Cleanup (landed `2026-05-07`)

- **Scope.** Four commits on `week12`: facade rename + caller migration
  (`37fcaad`), naming-overlap reconcile (`0cef876`),
  coverage-summary-attempted-drift unify (`9ebc5b5`), and the P3
  per-strategy outcome dict (`0981e92`). All three companion backlog
  items (`[FOLLOWUP w12-attribution-naming-overlap]`,
  `[FOLLOWUP coverage-summary-attempted-drift]`,
  `[FOLLOWUP activation-discovery-strategy-outcome-detail]`) closed.
- **Facade trim.** `executor/flows/playwright/attribution/__init__.py`
  29 underscore re-exports → 10 public names: `annotate_file_events`,
  `annotate_network_events`, `annotate_process_events`,
  `build_evidence_bundle`, `build_risk_signals`, `build_risk_summary`,
  `build_signal_summary`, `format_epoch_timestamp`, `relative_time`,
  `scenario_name_for_timestamp`. The four `_indexed_*` shim wrappers
  were dropped (callers reach `signals.facts` directly). Internal
  helpers (8 in `events.py`, 7 in `links.py`) stay private. Caller
  migration: `monitor/lifecycle.py`, `monitor/report_assembler.py`,
  `monitor/scenario_accountant.py`, `monitor/types.py`. Lazy proxy
  tuple `_LAZY_ATTRIBUTION_NAMES` in `monitor/__init__.py` shrunk
  15 → 10 (underscore-free); the eager
  `from ..signals import build_risk_signals, build_risk_summary,
  build_signal_summary` was removed so the proxy can route
  `monitor.build_signal_summary` through the attribution wrapper
  (which injects `automation_health` + `run_quality` + the lazy
  `RiskSignal` type).
- **Architecture gates preserved.**
  `test_monitor_facade_does_not_eagerly_import_attribution`,
  `test_monitor_lazy_proxy_completeness`,
  `test_attribution_does_not_eagerly_import_monitor`,
  `test_monitor_and_stimulus_subpackages_do_not_cross_import`,
  `test_executor_playwright_flat_file_count_limit`,
  `test_python_m_playwright_invocations_have_main_module` — all
  green; doc strings updated to public names.
- **Naming overlap (`0cef876`).**
  `attribution_summary.background_activation_count` →
  `target_background_activation_count` (target extension's
  non-foreground activations) and
  `attribution_summary.competing_candidate_count` →
  `competing_extension_event_count` (file/network events attributed
  to other extensions in the target's window). Disjoint populations
  pinned by new regression `tests/executor/test_annotation_summary.py`.
  TS contract regen + UI adapter + view-model + 2 fixtures + 1 doc
  updated; backwards-compat: NONE.
- **Coverage-summary drift (`9ebc5b5`).**
  `ReportAssembler.refresh_derived_state` now collapses the top-level
  `report.attempted_capabilities` and
  `report.heuristic_attempted_capabilities` to
  `runtime_official_attempted_capabilities` and
  `runtime_heuristic_attempted_capabilities` immediately after
  `event_attempts` reconciliation and before coverage reconcile, so
  the runtime-derived attempt view is the single source of truth and
  the UI fallback chain
  (`summary.attempted_capabilities` →
  `official_attempted_capabilities` →
  `attempted_capabilities`) resolves to one value. Producers upstream
  of refresh (payload extraction) can still seed initial values, but
  planned-and-not-attempted capabilities are dropped before reconcile.
  New regression
  `test_refresh_syncs_attempted_capabilities_to_runtime_derived`
  in `test_playwright_monitor_report_assembler.py`.
- **P3 strategy outcome dict (`0981e92`).** Field rename:
  `activation_discovery_strategies: list[str]` →
  `activation_discovery_strategy_outcomes: dict[str, str]`. Helpers
  in `monitor/runtime_state.py` now return
  `tuple[str, str]` (strategy_id, outcome) where outcome is one of
  `"succeeded_with_new_activations"`,
  `"succeeded_no_new_activations"`, or `"failed:<ExcClassName>"`.
  Callback type `SetDiscoveryStrategiesCallback` →
  `SetDiscoveryStrategyOutcomesCallback`; assembler setter
  `set_discovery_strategies` → `set_discovery_strategy_outcomes`.
  JSON export key follows the rename. Pydantic contract field
  rename + `dict[str, str]`. New contract test
  `test_accepts_failed_outcome_with_arbitrary_exception_class`.
  UI adapter does not currently read this field; TS contract regen
  deferred to W13 if a UI consumer is added.
- **Tests.** `make test-local` 1352 passed at W12-2 close (3
  pre-existing postgres-port-5433 DB failures unrelated). `make
  test-security` was 197 passed at W12-2 close and is 204 passed as of
  the `2026-05-07` docs-drift audit. Targeted attribution + assembler +
  contracts + architecture suite ~420 cases green.
- **Live-scan.** Deferred to W12 close (Iteration 6) per W12-1
  precedent — Docker `automation_executor` container not running
  locally during W12-2 implementation. Sanity-checked via
  `python -m executor.flows.playwright.entrypoint --list`
  (13 scenarios enumerate, paket import + scenarios registry
  resolution survive the rename).
- **Schema version.** `ACTIVATION_REPORT_SCHEMA_VERSION` stays
  `"2.1"` — no released report carries the old field names, so the
  rename is internal to the W12 PR window. Bump on the W13 PR if a
  released contract adopts the new names.

### W12-3 — `raw_context` Discriminated Union Typing (landed `2026-05-07`)

- **Scope.** `EvidenceEvent.raw_context` flipped from `dict[str, Any]` to a
  Pydantic discriminated union keyed by `event_class`. Variants live in
  `packages/analysis_contracts/evidence.py` next to the W8-6 `ContentSample`
  helpers; re-exported from `packages.analysis_contracts`. The literal §11.9
  plan named only Network/File/Process; in practice the consolidated
  `EvidenceEvent` carries seven distinct producer kinds (`scenario`,
  `activation`, `ui_blocker`, `network`, `file`, `process`,
  `output_channel_appendline`). The union covers all seven so
  `dict[str, Any]` residue is 0 in evidence models — closing exit-criteria
  bullet 4.
- **Producer migration.** Seven `raw_context={...}` sites in
  `executor/flows/playwright/attribution/links.py` each gained an explicit
  `"event_class": "<kind>"` literal so the Pydantic discriminator resolves
  on validate. Dataclass `executor/flows/playwright/monitor/records.py`
  intentionally stays loose (`dict[str, str | int | float | bool | None]`)
  since the typed boundary is the Pydantic contract; W13 can tighten the
  dataclass annotation as a separate item.
- **Consumer migration.** `packages/analysis_engine/rules/_common.py`
  `event_type` / `event_method` / `event_message` switched from
  `dict.get(...)` to `getattr(event.raw_context, ..., "")`. Three fixture
  payloads updated (test_rule_attribution.py, test_a3_typosquat.py) plus
  the canary `extensions/malicious/t1-*-canary/activation_report.json`
  pre-built reports and the offline fallback fixtures under
  `tests/platform/contracts/fixtures/activation_reports/`. The
  `_PENDING_MIGRATION` list in `test_content_sample_typing.py` lost its
  `(EvidenceEvent, "raw_context")` entry; only the W13
  `extension_host_output` follow-up remains.
- **Incidental fix (event_method key mismatch).** Producer (`links.py`
  network site) writes `http_method`; the reader had been looking for
  `method`, so `event_method()` had collapsed to `""` in production for
  years — surfaced once typed variants pinned the field set. Switched the
  reader to `http_method`. The a4 workspace-exfil and demo-runnable
  canaries now fire on the HTTP-method fallback as the rule comment had
  always claimed.
- **Tests.** `make test-local` 1375 passed (W12-2 baseline 1352 + 8 new
  discriminated cases + 15 latent fixture-aligned passes pulled in via
  `http_method` fix). `make test-security` 204 passed (8736d14 docs-drift
  baseline; **unchanged**). `make check-all` green end-to-end. New test
  `tests/platform/contracts/test_raw_context_discriminated.py` (8 cases)
  pins discriminator dispatch + per-variant `extra='forbid'` + full
  `EvidenceEvent` round-trip.
- **UI contract regen.** `ui/src/lib/types/contracts.ts` regenerated via
  `scripts/generate_ui_contracts.py` (single-line diff: `raw_context`
  emits the typed union shape now).
- **Live-scan.** **Completed `2026-05-10`** as part of the W12 close
  validation pass on `ms-python.python@2026.5.2026050801`: 17/17
  detection-relevant fields bitwise-equal pre/post W12-3 (job IDs
  `6fab298e81a14bf8a7a557a13953e57b` /
  `e5e33ec6e34f4993b795664d83e25fd4`; full evidence in
  `documents/archive/active-work/W12-close-acceptance-completed-2026-05-10.md` §3.4). The
  pre-completion sanity-check via
  `python -m executor.flows.playwright.entrypoint --list`
  (13 scenarios enumerate) is preserved here as the offline shortcut
  used during W12-3 implementation.
- **Schema version.** `ACTIVATION_REPORT_SCHEMA_VERSION` stays `"2.1"`.
  Re-ingest of pre-W12-3 raw reports is **not supported** (per user
  decision 2026-05-07): no `kind`→`event_class` before-validator was
  added; old JSONs will fail validation, which is the expected outcome.
  Bump on the W13 PR if a released contract adopts the typed shape.

### Pre-W12-4 Hardening — Output-Signal Multi-Line Secret Redaction (landed `2026-05-08`)

**Stable ID.** `[FOLLOWUP w12-0-output-signal-multiline-secret-redaction]`
in `POST_POC_BACKLOG.md` "W12 Pull-Forward". Added `2026-05-07` audit
pass during W12-3 close; closed `2026-05-08`.

**Status.** Landed. Severity: **High** (W12-0 scope'una somut bypass;
security-blocker — tek geçişte iki yolda da kapatıldı).

**Scope.** W12-0 (`22eb836`) file-backed yolu
`executor/flows/playwright/signals/output.py:204`'te `content.splitlines()`
ile satır satır okuyup her line'ı izole `redact_secrets(_truncate(line))`
çağrısından geçiriyor (`signals/output.py:223`). `redact_secrets`'in
private-key pattern'i (`packages/analysis_contracts/evidence.py:56-63`):

```python
re.compile(
    r"-----BEGIN[ A-Z0-9]*PRIVATE KEY-----"
    r"(?:.|\n)*?"
    r"-----END[ A-Z0-9]*PRIVATE KEY-----",
)
```

— BEGIN-END çiftini **tek string** içinde görmeyi gerektiriyor; lazy
`(?:.|\n)*?` aralarındaki body satırlarını yutuyor. `splitlines()`
BEGIN, body satırları, ve END'i ayrı string parçalarına böldüğü için
her parça izole redact çağrısı görüyor; hiçbiri tek başına BEGIN-END
eşleşmesi vermiyor; PEM gövdesi (base64) AWS / Bearer / api_key /
db_url desenlerine de uymadığı için **hiç maskelenmiyor**. Adversarial
extension `outputChannel.appendLine("-----BEGIN ... PRIVATE KEY-----")`
gibi line-by-line çağrılarla veya tek `appendLine` içinde gömülü `\n`
ile multi-line PEM yazdığında, persisted `ActivationReport`'a raw
private key gövdesi düşüyor (`OutputSignalEvent.text` üzerinden).

**Why W12-0 didn't catch this.** W12-0 acceptance bar tek-satır
secret pattern'lerini (AKIA, Bearer, AWS env, api_key=, postgres URL)
doğrulayan 4 file-backed + 3 harness-marker testiyle kapatıldı; hiçbir
test multi-line PEM senaryosu çalıştırmıyor. W11-6 extension-host log
tail yolu (`report_builder.py:281-293`) zaten "truncate → expand →
redact" ile multi-line aware; o yapı `signals/output.py`'a taşınmamış.

**Fix landed.**

Whole-content pre-pass yaklaşımı seçildi (state machine yerine), iki
yan kazanım için: (a) `read_text()` zaten content'i tek string'e
yüklüyor — ek bellek yükü minimal; (b) tek geçiş, gelecek cross-line
pattern'leri otomatik kapsama girer.

1. **Yeni helper**: `packages/analysis_contracts/evidence.py`'ye
   `redact_multiline_secrets(value)` eklendi. `_CROSS_LINE_CLASSES =
   frozenset({"private_key"})` üzerinden filtreleyerek `_REDACTION_PATTERNS`
   tablosundaki yalnızca cross-line entry'leri uyguluyor. Single-line
   pattern'lar (api_key / db_url / aws / bearer) bilerek hariç çünkü
   whole-input uygulamak yapılı sarmalları (JSON marker payload'ı)
   bozabiliyor — somut örnek: `api_key` pattern'inin opsiyonel
   trailing-quote tüketimi (`['\"]?`) JSON string'in kapatan tırnağını
   yutar → marker parse edilemez.
2. **`signals/output.py` her iki yolda da pre-pass.**
   `read_output_channel_logs`'da `content = redact_multiline_secrets(content)`
   `splitlines()`'tan önce; `parse_output_signal_events`'da
   `sanitized_output = redact_multiline_secrets(str(extension_host_output))`
   marker iterasyonundan önce. Per-marker / per-line
   `redact_secrets(_truncate(...))` defense-in-depth olarak korundu —
   idempotent.
3. **Cross-marker bypass trade-off** (yorumlarda dokümante edildi):
   3 ayrı `appendLine` ile yayılmış PEM denemesinde, redact span'ı
   ara marker JSON'larını da yutar; o eventler kaybolur. Bu kabul
   edildi çünkü alternatif body satırını sızdırmak.

**Acceptance evidence.**

- 4 yeni regression `tests/platform/security/test_output_signals_redaction.py`'da:
  - `test_read_output_channel_logs_redacts_multiline_pem_block` —
    file-backed, ardışık BEGIN/body/END satırları.
  - `test_read_output_channel_logs_multiline_pem_with_surrounding_lines` —
    file-backed, PEM'in önünde/sonunda noise.
  - `test_parse_output_signal_events_redacts_cross_marker_pem_block` —
    harness-marker, 3 ayrı appendLine ile cross-marker PEM.
  - `test_parse_output_signal_events_single_marker_multiline_pem` —
    harness-marker, tek appendLine içinde embedded `\n` ile multi-line
    PEM (canonical happy path).
- Tüm yeni case'lerde persisted `OutputSignalEvent.text`'te raw PEM
  marker veya base64 body görünmüyor; `[REDACTED:private_key]`
  yerleştiriliyor.
- Existing 20 case (W10-7 + W12-0 file-backed/harness-marker
  redaction + W12-0 channel/summary follow-up) regression olmadan
  geçti — özellikle `test_harness_marker_channel_redaction[api_key=...]`
  helper'ın cross-line-only daraltmasıyla yeniden geçer hale geldi.
- Test runtime ekstra yük: 0.11s (24 case toplam).

**Lane.** `[executor-runtime]` `[security-detection]`.

---

### Operator-Tunable VSIX Hardening (landed `2026-05-09`)

**Stable IDs.** Partial close of `[BACKLOG ui-v3-5]` (Settings
persistence API for the Security section); new follow-up
`[FOLLOWUP vsix-integrity-in-activation-report]` carries the deferred
report-side panel into a future iteration.

**Status.** Landed in commits `bea3bfe` (backend foundation),
`733c3bc` (marketplace structured 422), `f15b6c0` (download metrics
surfacing), `65f741a` (UI). Out of W12 scope strictly speaking — this
landed mid-W12 because the 2026-05-08 Microsoft ms-python release
tripped the original `MAX_FILE_COUNT=2_000` guard on real users (see
`POST_POC_BACKLOG.md` `[FOLLOWUP w8-1-vsix-entry-count-limit-realistic]`)
and the operator needed a way to tune the value without a deploy.

**Surfaces shipped.**

- New `operator_settings` key/value table (alembic migration
  `a1c4f9d2b8e3` → head). Single integer column today; typed sibling
  column will join when the first non-int setting arrives.
- `GET/PUT /api/settings/security/thresholds` with per-key bounds
  validation (`THRESHOLD_BOUNDS`); 422 on out-of-range values.
- Marketplace download path reads operator-tuned thresholds via
  `workflows.security_settings.load_vsix_thresholds(db)` per request;
  module constants stay as the test-friendly fallback for the existing
  `test_vsix_hardening` cases (decoupled by monkeypatch).
- `VSIXUnpackError` carries structured `breach_kind` / `threshold_*` /
  `observed_value` fields; HTTP layer maps to a 422 with a JSON
  detail object the UI consumes.
- `MarketplaceDownloadResponse.vsix_metrics` surfaces post-extract
  metrics (`file_count`, `uncompressed_size`, `compressed_size`,
  `compression_ratio`, `rejected_entry_count`) for fresh extractions.
- UI: generic `Dialog` v3 primitive; threshold-breach popup with
  comparison table + deep-link to `/settings?section=security`;
  post-download integrity banner; Settings → Security section with
  bounds-aware form, "Overridden" badge per row, and inline
  validation error surface.

**Stage-9 deferral.** The Reports-side panel ("VSIX Integrity" on
ReportsPage) is carried over as
`[FOLLOWUP vsix-integrity-in-activation-report]`. It needs an
Extension-entity migration (4 nullable VSIX-metric columns) plus
populate-on-create plus `ActivationReport.vsix_integrity` additive field
plus adapter plus UI subsection. Kept out of this iteration to avoid
contract-side test fixture churn during W12 active work.

**Acceptance evidence.**

- Backend: 6 new `requires_db` cases under
  `tests/workflows/security_settings/test_router.py`; 2 new cases on
  `test_vsix_hardening.py` (structured exception fields, per-call
  thresholds dict override); 2 new cases on `test_router.py`
  (structured 422, legacy fallback). All 150 marketplace +
  security-settings tests green.
- UI: 50/50 vitest cases green including the new deep-link case on
  `SettingsPage.test.tsx`; `tsc --noEmit` clean.
- Live verification: rebuilt API container, pre-existing 80 contracts
  - security cases stay regression-free, browser preview round-trip
  on `ms-python.python@2026.5.2026050801` (download → metrics banner)
  and `vsix_max_file_count=200` synthetic breach (popup with
  Settings deep-link).
- Follow-up closure `2026-05-09`:
  `[FOLLOWUP vsix-threshold-dto-generator-coverage]` closed by moving
  threshold response/request schemas to
  `appcore/contracts/schema_defs/security_settings.py`, adding backend-owned
  `VsixThresholdBreachDetail`, regenerating `ui/src/lib/types/contracts.ts`,
  and adding `tests/scripts/test_generate_ui_contracts.py` plus
  `python scripts/generate_ui_contracts.py --check`. The breach-detail
  contract keeps `observed_value` as `int | float` so compression-ratio
  threshold errors return structured 422s instead of failing validation.
- Follow-up closure `2026-05-09`:
  `[FOLLOWUP settings-page-stale-localstorage-copy]` closed by updating the
  Settings header copy to distinguish browser-local general preferences
  from API-persisted Security thresholds; `SettingsPage.test.tsx` pins it.
- Follow-up closure `2026-05-09`:
  `[FOLLOWUP security-settings-commit-ownership]` closed by moving the
  operator-settings commit into a CRUD facade helper
  (`upsert_operator_settings_bulk_and_commit`); workflow service now owns
  validation/default merge only. Pinned `2026-05-10` by
  `tests/platform/storage/test_operator_settings.py` (happy path,
  empty-payload no-op, rollback-on-`SQLAlchemyError`) and by the
  `ThresholdsResponse`/`ThresholdsUpdateRequest` validation cases appended
  to `tests/platform/contracts/test_schemas.py`.
- Verification cleanup `2026-05-09`: broad `make test-local` initially
  exposed stale platform fixture drift against the partial local
  `ms-python.python@2026.5.2026032701` directory. The baseline contract now
  resolves the complete local `ms-python.python@2026.5.2026050801` artifact;
  the two affected fixture-baseline tests and the full local lane pass
  (`1393 passed / 6 skipped / 6 deselected`).
- Verification refresh `2026-05-10`: added pin tests for the
  `[FOLLOWUP security-settings-commit-ownership]` closure
  (`tests/platform/storage/test_operator_settings.py` ×3 +
  `tests/platform/contracts/test_schemas.py` Threshold cases ×4); broad
  bar advances to `1400 passed / 6 skipped / 6 deselected`,
  `make test-security` 211 passed.

**Lane.** `[settings]` `[ui-v3]` `[security-detection]`.

---

### Pre-W12-4 Hardening — API Docker Base Image Digest Pin

**Stable ID.** `[FOLLOWUP api-docker-base-image-digest-pin]` in
`POST_POC_BACKLOG.md` "W12 Pull-Forward". Added `2026-05-07` audit
pass during W12-3 close.

**Status.** Closed `2026-05-09` on `week12`. Severity at discovery:
**High** (ADR 0002 §4 ihlali; supply-chain drift).

**Scope.**

- `docker/api/Dockerfile:2` — now
  `FROM python:3.11-slim-bookworm@sha256:cd67330292a51e2963156f74ff340455d66b2172e9190e99f40dff9357471177`.
- `executor/container/Dockerfile:8` —
  `FROM ubuntu:22.04@sha256:962f6cadeae0ea6284001009daa4cc9a8c37e75d1f5191cf0eb83fe565b63dd7`
  (digest-pinned, doğru form).
- ADR 0002 §4 trust table (`documents/adrs/0002-threat-model.md:97`)
  her base image için `FROM image@sha256:...` zorunluyor: *"Docker
  base image | Trusted if SHA-pinned | `FROM image@sha256:...`
  required"*.

**Why önemli.** API container FastAPI yüzeyi + Docker socket bridge
olduğu için kritik trust boundary'de. Mutable tag pini, aynı
Dockerfile'ın zamanla farklı base image üretmesine yol açabilir
(upstream `python:3.11-slim-bookworm` tag'i zaman içinde farklı
digest'lere işaret edebilir, hatta hijack edilebilir). Executor
container kuralı doğru uyguluyor; API tarafı uymuyor.

**Fix landed.**

1. **Dockerfile pin.** Digest resolved with
   `docker buildx imagetools inspect python:3.11-slim-bookworm`
   (manifest-list digest
   `sha256:cd67330292a51e2963156f74ff340455d66b2172e9190e99f40dff9357471177`)
   and applied to `docker/api/Dockerfile:2`.
2. **Architecture gate.**
   `tests/architecture/test_dockerfile_digest_pin.py` walks `docker/`
   and `executor/container/`, checking every `Dockerfile` `FROM` line
   for `@sha256:`; `FROM scratch` is the only allow-list.

**Acceptance criteria.**

- `docker/api/Dockerfile` `FROM python:3.11-slim-bookworm@sha256:...`
  formuna geçti.
- `executor/container/Dockerfile` mevcut digest pin korunuyor (regress yok).
- Yeni AST gate tag-only Dockerfile kullanımını yakalar; existing digest
  pins doğrulanır.
- Focused validation:
  `pytest tests/architecture/test_dockerfile_digest_pin.py` yeşil.
- Yeni dependency yok; `pyproject.toml` ve `requirements*.txt` değişmedi.
- ADR 0002 §4 trust table tek satırlık güncelleme gerekiyorsa "API
  Dockerfile pinned" notu eklenebilir (opsiyonel).

**Lane.** `[platform-storage]`.

---

### W12-4 — `entrypoint/runner.py::main` Dispatch Extraction (landed `2026-05-10`)

- **Scope.** `executor/flows/playwright/entrypoint/runner.py::main`
  324 LoC → 99 LoC (limit ≤200). Dispatch logic moved to new
  `executor/flows/playwright/entrypoint/dispatch.py`. Pattern follows
  W11-1 (`monitor_lifecycle.py` 834→split): pure relocation, no
  behavior change, no generic framework / strategy registry / event
  bus introduced. `runner.py` total shrank from 494 LoC → 196 LoC;
  `dispatch.py` is 402 LoC.
- **`runner.py` post-W12-4 surface.** Public functions kept so the
  package `__init__.py` import contract holds: `run_demo`,
  `create_bait_files`, `default_report_path`, `main`. Private
  deps-binding helpers used only by `main()` stay too:
  `_default_report_path_for_deps`, `_create_bait_files_for_deps`,
  `_resolve_execution_plan_for_deps`,
  `_reload_window_under_monitoring_for_deps`. The deps-binding
  helpers consumed only inside the dispatch path
  (`_run_demo_for_deps`, `_run_extra_triggers_for_deps`) and the
  execution-result builders (`_empty_execution_result`,
  `_normalize_execution_result`) moved to `dispatch.py`.
- **`dispatch.py` exports.** `PageRef` (mutable page-reference
  wrapper), `setup_monitor`, `make_page_callbacks`,
  `dispatch_execution`, `apply_extra_triggers_if_needed`,
  `summarize_skipped_scenarios_if_needed`,
  `finalize_monitor_report`. The 6-way execution mode condition
  (`demo` / `skip_automation` / `layered_passes` /
  `selected_scenarios` / `single_scenario` / default-all
  `run_all_scenarios`) lives in `dispatch_execution`; ordering and
  per-mode side effects (`mark_trigger_plan_applied`,
  `wait_for_idle_observation`, exit-code accumulation) preserved
  bytewise.
- **`PageRef` design.** The retry-on-crash callback originally used
  `nonlocal page` to rebind the live page after a window reload so
  later `wait_for_idle_observation(page, ...)` calls saw the new
  page. Crossing module boundaries breaks `nonlocal`; `PageRef.value`
  is a single-attribute mutable wrapper that the
  `make_page_callbacks._on_page_reloaded` closure mutates and the
  rest of `dispatch_execution` reads. Smallest possible abstraction
  — no framework, no plugin shape.
- **Exit-code accumulation.** Original `main()` set `exit_code = 1`
  in five places (one per mode that detected failures, plus the
  extra-trigger and skipped-summary blocks). Refactored shape uses
  `exit_code |= partial` (bitwise OR) at the orchestrator level,
  with `dispatch_execution`, `apply_extra_triggers_if_needed`, and
  `summarize_skipped_scenarios_if_needed` each returning 0 or 1.
  Behavior identical because the only non-zero value is 1.
- **Lazy import in `_run_demo_for_deps`.** `dispatch.py` is loaded
  during `runner.py`'s import (`runner.py` does
  `from .dispatch import ...`). A top-level
  `from .runner import run_demo` in `dispatch.py` would re-enter the
  partially-loaded runner module. The `_run_demo_for_deps` helper
  imports `run_demo` lazily inside its body — standard Python
  cycle-break pattern, documented inline.
- **Architecture gates added.** Two new tests in
  `tests/architecture/test_runner_main_loc_budget.py`:
  - `test_runner_main_under_loc_budget` — AST gate, asserts
    `main()` body span ≤ 200 LoC. Pattern mirrors
    `test_executor_playwright_flat_file_count_limit` (W12-1):
    structural ratchet that fires before the readability hotspot
    re-emerges.
  - `test_runner_main_dispatch_helpers_remain_imported` — pins
    that `runner.py` continues to import the six dispatch helpers
    (`PageRef`, `apply_extra_triggers_if_needed`,
    `dispatch_execution`, `finalize_monitor_report`,
    `setup_monitor`, `summarize_skipped_scenarios_if_needed`).
    Prevents a future inlining that drops imports without bumping
    the LoC test in lockstep.
- **Tests.** `tests/executor/test_playwright_entrypoint.py` 27/27
  cases green (21 in pre-W12-4 baseline + 6 parameterized
  expansions); the fake-`deps` SimpleNamespace harness covers the
  refactor end-to-end without modification because every dispatch
  helper continues to honor the `*, deps`-injection convention.
  Architecture suite (12 cases under
  `tests/architecture/test_import_graph.py` + 1
  `test_container_entrypoint.py` + 2 new gates) all green. Broad
  bar: `make test-local` 1402 passed / 6 skipped / 6 deselected
  (1400 → 1402, the +2 from the new LoC budget gate);
  `make test-security` 211 passed / 32 warnings (unchanged).
- **Live-scan.** **Completed `2026-05-10`** as part of the W12 close
  validation pass — the same scan that closed W12-3 / W12-5 covers
  W12-4 because the dispatch extraction is verbatim relocation and
  the runner package import path is unchanged
  (`ms-python.python@2026.5.2026050801`; 17/17 detection-relevant
  fields identical; evidence in
  `documents/archive/active-work/W12-close-acceptance-completed-2026-05-10.md` §3.4). The
  offline sanity-check
  `python -m executor.flows.playwright.entrypoint --list`
  (13 scenarios enumerate) was used during W12-4 implementation
  itself to confirm package import + scenarios registry resolve.
- **Branch policy note.** Per the W12 single-branch policy, W12-4
  lands as commits on `week12` rather than as a standalone PR.
  Commit-level isolation preserves the cherry-pick / revert
  ergonomics.

---

### W12-5 — Extension Host Ahtapot Split + Body-Preview Redaction Gate (landed `2026-05-10`)

- **Scope.** Two deliverables shipped in one iteration:
  1. **Extension Host split.** `executor/flows/playwright/runtime_capture/extension_host.py`
     679 LoC → 87 LoC thin re-export facade + 3 focused modules
     (`extension_host_log_parse.py` 329 LoC,
     `extension_host_strace_parse.py` 106 LoC,
     `extension_host_capture.py` 264 LoC). Pattern follows W11-7
     (`workflows/extension_catalog/service.py` facade) and W11-8
     (`appcore/storage/crud_ops/analysis_jobs/__init__.py` facade):
     pure relocation, no behavior change, explicit
     `from .X import Y as Y` re-exports + `__all__`.
  2. **Body-preview redaction architecture gate.** New
     `tests/architecture/test_network_body_preview_redaction.py`
     — AST gate that walks every `.py` under `executor/`,
     `packages/`, `workflows/` (excluding tests) and fails if any
     `request_body_preview` / `response_body_preview` assignment
     (kwarg, attribute write, or dict-key assign) is not routed
     through `redact_secrets()` directly, via
     `_bounded_body_metadata()` output, or as a passthrough from
     an already-redacted source (`network_event`, `evidence_event`,
     `event`, `payload`).
- **Public-surface preservation.** The original
  `extension_host.py` was tightly bound to two external consumers
  whose contracts had to survive the split:
  - `executor/flows/playwright/monitor/__init__.py:101-109`
    re-exports 7 names from this path
    (`_ACTIVATION_PATTERNS`, `_TIMESTAMP_RE`,
    `ExtensionHostFileCapture`,
    `_activation_within_monitoring_window`,
    `_parse_activation_lines`, `_poll_exthost_log`,
    `watch_exthost_log`).
  - `executor/flows/playwright/monitor/sources.py:14-17`
    imports 2 names directly
    (`_activation_within_monitoring_window`,
    `_parse_activation_lines`).
  - `tests/executor/test_playwright_extension_host.py` (W11
    precursor, 23 cases) accesses 9 distinct symbols by attribute
    lookup on the imported module (including `VSCODE_LOGS_DIR`
    and `_parse_iso_timestamp`).
  Total facade surface: 17 names. The plan validation pass caught
  three names the initial draft had omitted (`VSCODE_LOGS_DIR`,
  `_TIMESTAMP_RE`, `_activation_within_monitoring_window`) and
  added them before the facade landed; without that pre-flight
  audit the 23-case suite would have failed at first run.
- **Monkey-patch contract preservation.** The 23-case suite uses
  `monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)`
  to redirect file discovery to fixture directories. After the
  split, `find_exthost_logs` and `read_extension_host_output` live
  in `extension_host_log_parse.py` and would normally read the
  module-level `VSCODE_LOGS_DIR` import inside their own
  namespace — which the facade-side monkeypatch cannot reach. The
  fix is a small `_resolve_vscode_logs_dir()` helper inside
  `extension_host_log_parse.py` that does
  `from . import extension_host as _facade` lazily and reads
  `_facade.VSCODE_LOGS_DIR` at call time. Lazy import is safe
  because the facade is fully loaded before any of these
  functions can be invoked. Decoupling the test from
  implementation detail wasn't an option (plan policy: do not
  modify the precursor tests during the split).
- **Capture-side cycle break preserved.** The original
  `ExtensionHostFileCapture.start()` defers
  `from ..monitor import _wait_for_extension_host_pid` inside the
  function body to break the
  `runtime_capture → monitor → runtime_capture` cycle. The split
  moved this method into `extension_host_capture.py` verbatim,
  including the lazy import and the surrounding cycle-break
  comment. Hoisting it to module top would re-introduce the
  cycle.
- **Architecture gates added.**
  - `tests/architecture/test_import_graph.py::test_runtime_capture_extension_host_stays_a_thin_facade`
    — AST shape gate, allows only `Import`, `ImportFrom`, the
    module docstring, and the `__all__` assignment. Prevents the
    facade from re-growing function/class bodies. Mirrors the
    W11-7 / W11-8 pattern verbatim.
  - `tests/architecture/test_import_graph.py::test_runtime_capture_extension_host_reexports_match_canonical_modules`
    — identity gate, asserts `set(extension_host.__all__)` equals
    the union of four expected sets (10 names from
    `extension_host_log_parse`, 2 from `extension_host_strace_parse`,
    3 from `extension_host_capture`, 2 from `_shared`) and that
    every facade symbol resolves by `is` identity to its
    canonical-module counterpart. Catches both orphan re-exports
    and shim-wrapped re-bindings.
  - `tests/architecture/test_network_body_preview_redaction.py::test_body_preview_assignments_are_redacted`
    — body-preview gate; teeth verified by mutating
    `network.py:127` to a plaintext literal (gate fired with
    `network.py:127: request_body_preview=<expr> not routed
    through redact_secrets`); revert + re-run = green.
- **Tests.**
  - `tests/executor/test_playwright_extension_host.py` 23/23
    green (W11 precursor suite preserved).
  - `tests/architecture/` 100 cases green
    (98 prior + 2 new W12-5 facade gates +
    1 new body-preview gate, includes the auto-discovered cases
    from `test_default_bindings.py` parametrization).
  - `make test-local` 1430 passed / 6 skipped / 6 deselected
    (jumped from the 1402 baseline because the pre-W12-5 tally
    already included tests added during W12-4 closure +
    `make test-local` enumerates more lanes; the W12-5
    delta is +3 architecture gates).
  - `make test-security` 211 passed / 32 warnings (unchanged).
- **Live-scan.** **Completed `2026-05-10`.** Pre-W12-5 baseline
  job `6fab298e81a14bf8a7a557a13953e57b` (`2026-05-09 21:47`) and
  post-W12-5 validation job `e5e33ec6e34f4993b795664d83e25fd4`
  (`2026-05-10 14:21`) on `ms-python.python@2026.5.2026050801`:
  **17/17 detection-relevant fields identical** —
  `signal_summary.level=needs_review`, `score=28`,
  `verified_capabilities` (4), `attempted_capabilities` (6),
  `coverage_summary` (covered=7/partial=5/missing=6/attempted=6/
  verified=4), `automation_health.status=degraded` with 4
  reasons, `target_extension_observed=True`, `run_quality=low`,
  `output_signal_events=12`, `len(activated)=22`,
  `len(scenario_traces)=3`, `len(stimulus_passes)=5`,
  `len(event_attempts)=21`,
  `summary.scenarios_run=[project_exploration, coding_session,
  terminal_usage]`, `failed_scenarios=[]`. Tolerance-band fields
  (`network_events`, `file_events`, `process_events`,
  `evidence_links`) all sat within the W11 baseline ranges. Full
  field-by-field table in
  `documents/archive/active-work/W12-close-acceptance-completed-2026-05-10.md` §3.4. The
  pre-validation note about needing an executor image rebuild
  was the trigger for the rebuild + re-scan that produced the
  post-W12-5 job above.
- **Followups closed.**
  - `[FOLLOWUP w12-extension-host-split-scoping]` — the
    P1/P2-priority W12 plan addendum from the 2026-04-27 audit
    pass; original 679-LoC ahtapot retired.
  - `[FOLLOWUP arch-gate-network-body-preview-redaction]` — P2
    audit followup, optional W12-1 companion pulled into W12-5
    as a thematic fit (defense-in-depth around the runtime
    redaction path that already had test coverage at
    `tests/executor/test_playwright_monitor_runtime.py::test_parse_tshark_event_line_redacts_secrets_in_body_preview`
    and the broader output-signal suite).
- **Branch policy note.** Per the W12 single-branch policy,
  W12-5 lands as commits on `week12` (commits `377f0d5` for the
  refactor, `9433ee3` for the body-preview gate, plus this
  documentation commit). Commit-level isolation preserves
  cherry-pick/revert ergonomics for the W12 close PR bundle.
