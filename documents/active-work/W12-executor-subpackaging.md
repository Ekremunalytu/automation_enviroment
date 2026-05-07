# W12 — Executor Subpackaging + Attribution Cleanup (Active Work Tracker)

`Last Updated: 2026-05-07 (W12 active prep; W12-0 precursor surfaced by 2026-05-07 audit pass)`

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

- **W12 active prep.** Initial scaffold landed `2026-05-07` on the
  `chore/pre-w12-prep` branch alongside the §11.9.1 plan addendum.
  W11 closed `2026-05-05` and merged via PR #14. W12-1 has not started
  because W12-0 must land first — see "Entry Conditions" below.
- **Pre-W12 attribution precursor tests landed.**
  `[FOLLOWUP w12-precursor-tests-attribution-links]` and
  `[FOLLOWUP w12-precursor-tests-attribution-events]` both closed in
  commit `5ae0d32` on `2026-05-07`; tests now live at
  `tests/executor/test_playwright_attribution_links.py` and
  `tests/executor/test_playwright_attribution_events.py`. Companion
  plan-level item `[FOLLOWUP w12-extension-host-split-scoping]` closed
  by the §11.9.1 addendum on PR #15 (no code change).
- **W12-0 (precursor — security pull-forward).**
  `[FOLLOWUP w8-6-output-signals-file-backed-redaction]`
  (`POST_POC_BACKLOG.md` Detection / Contracts) is an active W8-6
  perimeter regression — the file-backed
  `read_output_channel_logs` path at `output_signals.py:205` builds
  `OutputSignalEvent` without `redact_secrets`. Land as a standalone
  pre-W12 PR (single-line fix + sibling redaction test) **before**
  W12-1 starts; not eligible to ride a refactor PR. Companion
  comment update at `output_signals.py:117` to acknowledge both the
  harness-marker and file-backed paths. Surfaced 2026-05-07 audit
  pass.
- **W12-1** — pending. Executor subpackaging:
  `executor/flows/playwright/` 54 flat files → 5 subpackage
  ({`monitor/`, `stimulus/`, `workspace/`, `health/`, `entrypoint/`})
  - `attribution/` (W7) + remaining flat ≤10. Import-graph rule:
  `monitor/` and `stimulus/` cannot import each other; cross-talk only
  via shared helpers. Architecture gate test added per W11-7 pattern.
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
- W12-0 security pull-forward landed (✗ pending —
  `[FOLLOWUP w8-6-output-signals-file-backed-redaction]`, single-line
  fix + regression test before W12-1 starts)
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
- `[FOLLOWUP w8-6-output-signals-file-backed-redaction]`
  (`POST_POC_BACKLOG.md` Detection / Contracts) — **W12-0 precursor.
  MUST land before W12-1.** Active W8-6 perimeter regression; one-line
  fix at `output_signals.py:205` + redaction test extension. Surfaced
  2026-05-07 audit pass.
- `[FOLLOWUP arch-gate-network-body-preview-redaction]`
  (`POST_POC_BACKLOG.md` Engineering Quality, **P2**) — optional
  W12-1 companion (defense-in-depth structural gate sibling to
  the existing AST-gate suite). Land if W12-1 has spare review
  capacity; otherwise defer to W13.

## Detailed Item Notes (filled as items land)

(Empty until first item lands. Use the same per-item structure as
`active-work/W11-monitor-lifecycle.md`: scope, target metric,
implementation notes, test additions, live-scan validation snapshot
where applicable.)

### W12-1 — Executor Subpackaging

(pending)

### W12-2 — Attribution Facade Underscore Cleanup

(pending)

### W12-3 — `raw_context` Discriminated Union Typing

(pending)

### W12-4 — `entrypoint_runner.main` Dispatch Extraction

(pending)
