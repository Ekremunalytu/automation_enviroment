# W12 — Executor Subpackaging + Attribution Cleanup (Active Work Tracker)

`Last Updated: 2026-05-07 (W12 active; W12-0 + W12-1 landed; W12-2 unblocked)`

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

- **W12 active.** Initial scaffold landed `2026-05-07` on the
  `chore/pre-w12-prep` branch alongside the §11.9.1 plan addendum.
  W11 closed `2026-05-05` and merged via PR #14. W12-0 landed
  `2026-05-07` on `week12` (`22eb836`); W12-1 unblocked. Single-branch
  policy: all W12-0..W12-5 land on `week12` and merge to `main` via a
  single PR at W12 close.
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
  `redact_secrets(_truncate(line))` applied at
  `executor/flows/playwright/output_signals.py:205`; W10-7 source
  comment at `:117` updated to name both harness-marker and
  file-backed paths. Single-branch policy override: W12-0 landed as
  the first commit on `week12` (commit-level isolation in lieu of a
  standalone pre-W12 PR), so the refactor commits that follow can
  still be reverted independently. Surfaced 2026-05-07 audit pass.
- **W12-1** — landed `2026-05-07`. Executor subpackaging:
  `executor/flows/playwright/` 54 flat files → 7 new subpackages
  (`monitor/`, `stimulus/`, `workspace/`, `health/`, `entrypoint/`,
  plus `vscode/` and `signals/` to satisfy ≤10 flat) + existing
  `attribution/` (W7) + 10 flat. Import-graph rule landed:
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
- **W12-2** — pending. Attribution facade underscore cleanup:
  `executor/flows/playwright/attribution/__init__.py` 29 underscore
  re-exports → ~6-7 public names + remaining stay private. Caller
  migration in `monitor_lifecycle.py`,
  `monitor_report_assembler.py`, and `monitor_scenario_accountant.py`.
  Companion backlog items rolled in:
  `[FOLLOWUP w12-attribution-naming-overlap]`,
  `[FOLLOWUP coverage-summary-attempted-drift]`, and
  `[FOLLOWUP activation-discovery-strategy-outcome-detail]` (P3).
- **W12-3** — pending. `raw_context` discriminated union typing:
  `dict[str, Any]` → `NetworkRawContext` / `FileRawContext` /
  `ProcessRawContext` Pydantic variants under
  `RawContext = Annotated[…, Field(discriminator="event_class")]`.
  New test file
  `tests/platform/contracts/test_raw_context_discriminated.py`.
- **W12-4** — pending. `entrypoint_runner.main` dispatch extraction:
  `main()` 324 LoC → ≤200 LoC; CLI parse → config → monitor invocation
  → page-reload callback wiring → UI blocker probe move to new
  `entrypoint/dispatch.py`. File total currently 494 LoC (`main()`
  324 + module-level helpers/imports ~170); only `main()` shrinks
  toward the ≤200 LoC target.

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
  commit `22eb836` on `week12`; one-line fix at `output_signals.py:205`
  plus four file-backed regressions and three harness-marker
  end-to-end regressions in
  `tests/platform/security/test_output_signals_redaction.py`)
- §11.9.1 plan addendum (✓ landed on `chore/pre-w12-prep`) defining
  the `runtime_capture/extension_host.py` split target
- Working tree clean on `main` (TBD at W12-1 entry)
- `make check-all` green (`1274` baseline at W11 close;
  `make test-security` 190 cases)

## Exit Criteria

- [ ] `executor/flows/playwright/` flat file count 54 → ≤10
- [ ] 5-subpackage structure ({`monitor`, `stimulus`, `workspace`,
      `health`, `entrypoint`}/) + `attribution/` (W7) isolated by
      import-graph rule
- [ ] `attribution/__init__.py::__all__` lists ~6-7 public names;
      underscore-prefixed names internal-scoped
- [ ] `raw_context` typed discriminated union; `dict[str, Any]`
      residue = 0 in evidence models
- [ ] `entrypoint_runner.py::main` 324 LoC → ≤200 LoC; dispatch logic
      in `entrypoint/dispatch.py`
- [ ] Import-graph test green (architecture gate); `make check-all`
      green; `make test-security` green (190 cases preserved)
- [ ] Live-scan validation: pre/post bitwise-equal detection-relevant
      fields on a target run (W11-1 / W11-3 / W11-4 pattern)

## Acceptance Sub-Tasks (W12-N picks up these follow-ups)

These `[FOLLOWUP ...]` items in `POST_POC_BACKLOG.md` are scheduled
to land before or during W12 acceptance. Refer by stable ID, not line
number.

- ~~`[FOLLOWUP w12-precursor-tests-attribution-links]`~~ —
  closed `2026-05-07` in commit `5ae0d32`.
- ~~`[FOLLOWUP w12-precursor-tests-attribution-events]`~~ —
  closed `2026-05-07` in commit `5ae0d32`.
- `[FOLLOWUP w12-attribution-naming-overlap]`
  — natural landing W12-2 (`background_activation_count` vs
  `competing_candidate_count` divergence reconcile).
- `[FOLLOWUP w12-extension-host-split-scoping]`
  — plan-level addition to slim canonical §11.9.1; closed by PR #15
  (no code change). Implementation deferred to W12 entry; lands as
  ahtapot pattern.
- `[FOLLOWUP coverage-summary-attempted-drift]`
  — natural landing W12-2; surgical pull-forward acceptable if a UI
  surface reads both fields.
- `[FOLLOWUP activation-discovery-strategy-outcome-detail]`
  (**P3**) — read-side detail loss; W12-2 territory.
- ~~`[FOLLOWUP w8-6-output-signals-file-backed-redaction]`~~ —
  closed `2026-05-07` on `week12` in commit `22eb836` (W12-0
  precursor). One-line fix at `output_signals.py:205` plus seven new
  regression tests (4 file-backed, 3 harness-marker end-to-end) in
  `tests/platform/security/test_output_signals_redaction.py`.
- `[FOLLOWUP arch-gate-network-body-preview-redaction]`
  (`POST_POC_BACKLOG.md` Engineering Quality, **P2**) — optional
  W12-1 companion (defense-in-depth structural gate sibling to
  the existing AST-gate suite). Land if W12-1 has spare review
  capacity; otherwise defer to W13.

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
- **Fix.** Single-line change at
  `executor/flows/playwright/output_signals.py:205`
  (`text = _truncate(line)` → `text = redact_secrets(_truncate(line))`).
  Source comment at `:117` rewritten to name both paths and call
  out the W12-0 precedent so future readers see the symmetry rule.
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
  `__init__.py`) → 8 subpackages + 10 flat. Subpackages
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

### W12-2 — Attribution Facade Underscore Cleanup

(pending)

### W12-3 — `raw_context` Discriminated Union Typing

(pending)

### W12-4 — `entrypoint_runner.main` Dispatch Extraction

(pending)
