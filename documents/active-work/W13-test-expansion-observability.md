# W13 — Test Expansion + Observability (Active Work Tracker)

`Last Updated: 2026-05-10 (W13 scaffold; entry baseline established post-W12 merge)`
`Phase: W13 active`
`Branch: TBD (single-branch policy precedent: week13)`
`Owner: ekrem`

This is the canonical active work tracker for the W13 Test Expansion +
Observability window. Items receive stable IDs (`W13-1`, `W13-2`, ...)
**at first pull**, not preemptively, per the W11/W12 precedent
(`REFACTOR_OPTIMIZATION.md` §11.10 final paragraph: "tracker is born at
phase entry"). Code comments, tests, and ADR addenda will reference
items by ID — **keep IDs stable** when reorganizing.

This file mirrors the structure of `W11-monitor-lifecycle.md` and
`W12-executor-subpackaging.md`. Slim canonical
`REFACTOR_OPTIMIZATION.md §11.10` carries the entry-conditions block,
goal statement, and current candidate list; full historical detail will
move to `archive/plans/REFACTOR_OPTIMIZATION_full_<date>.md §11.10` as
the section ages.

## Status (Quick Glance)

- **W13 active.** Entry baseline established `2026-05-10` post-W12
  merge to `main` via PR #18 (`33a0852`). No work item pulled yet —
  this tracker is a scaffold; first item pull will assign `W13-1`.
- **Entry gate met:**
  - W12 closed and merged via PR #18 (`33a0852`); close commit
    `e8a9926`.
  - `make check-all` ✅ green at the W12 close commit (post-Codex-fix
    re-run, postgres_test container active).
  - `make test-local` 1452 passed / 6 skipped / 6 deselected / 75
    warnings.
  - `make test-security` 211 passed / 32 warnings.
  - `tests/architecture/` 76 passed / 2 deselected.
  - Live-scan bitwise-equal baseline on
    `ms-python.python@2026.5.2026050801` (job IDs
    `6fab298e81a14bf8a7a557a13953e57b` /
    `e5e33ec6e34f4993b795664d83e25fd4`); recorded in the archived
    `W12-close-acceptance.md` §3.4.

## Entry Conditions Met (mirroring `REFACTOR_OPTIMIZATION.md` §11.10)

- [x] W12 closed and merged to `main` via `week12 → main` PR.
  (`PR #18` — `33a0852`.)
- [x] `make check-all` green at the W12 close baseline (commit
  `e8a9926`); test-local 1452 / test-security 211.
- [x] `tests/architecture/` 76 cases green; W12 ratchet gates pinned:
  `test_executor_playwright_flat_file_count_limit` (W12-1, ≤10 flat),
  `test_runner_main_under_loc_budget` (W12-4, ≤200 LoC for `main()`),
  `test_runtime_capture_extension_host_stays_a_thin_facade` and
  `test_runtime_capture_extension_host_reexports_match_canonical_modules`
  (W12-5 facade invariants),
  `test_body_preview_assignments_are_redacted` (W12-5 redaction
  defense), and
  `test_all_runtime_dockerfiles_pin_base_images_by_digest`
  (ADR 0002 §4 trust, `ui/` included).
- [x] Live-scan bitwise-equal baseline established on
  `ms-python.python@2026.5.2026050801`; W13 split candidates may use
  this as the pre-refactor reference.
- [x] W13 lane document (this file) created at W13 official open per
  W11/W12 precedent.

## Goal (per `REFACTOR_OPTIMIZATION.md` §11.10)

Benign silence fixture 3→5; stale singleton-lock + `.env` gitignore
regression tests; `extrace.executor.*` logger consolidation; run-ID
stamping; W8-W12 regression lock-in.

Beyond the original §11.10 goal text, the `2026-05-07` and `2026-05-09`
audit passes plus the W12-close Codex review surfaced additional
candidates (see "Candidate Items" below).

## Candidate Items (stable IDs assigned at first pull)

Pulled from `POST_POC_BACKLOG.md` §11.10 candidates and
`REFACTOR_OPTIMIZATION.md` §11.10. Status column reflects current
backlog state; `W13-N` IDs filled in as items move from "not started"
to "in progress".

| ID | Item | Lane | Status |
|---|---|---|---|
| TBD | `[FOLLOWUP scenario-accountant-conservation-split]` (`monitor/scenario_accountant.py` 648 LoC; W11-1 lifecycle split pattern) | `[executor-runtime]` | not started |
| TBD | `[FOLLOWUP evidence-event-kind-raw-context-invariant]` (`EvidenceEvent.kind` ↔ `raw_context.event_class` Pydantic v2 `model_validator`) | `[security-detection]` | not started |
| TBD | `[FOLLOWUP ui-raw-context-discriminator-parity]` (TS `event_class` literal generation + 5 legacy adapter fixups) | `[ui]` `[contracts]` | not started |
| TBD | `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]` (extend `tests/architecture/test_absolute_binary_paths.py` for `tshark`/`strace`/`inotifywait`) | `[security-detection]` | not started |
| TBD watch | `[FOLLOWUP planner-selection-readability-audit]` (`analysis_planner/selection.py` 497 LoC; refactor only when activation family or planner bug triggers) | `[security-detection]` | watching |
| TBD watch | `[FOLLOWUP attribution-links-build-evidence-bundle-density]` (`attribution/links.py` 601 LoC; reassess after evidence-event-kind invariant lands) | `[executor-runtime]` | watching |
| TBD watch | `[FOLLOWUP execute-attempt-rebloat-watch]` (`stimulus/attempts.py::execute_attempt` chain growth; refactor only when new action family added) | `[executor-runtime]` | watching |
| TBD watch | `[FOLLOWUP dispatch-execution-rebloat-watch]` (`entrypoint/dispatch.py` 402 LoC W12-4 ratchet; add `test_dispatch_execution_under_loc_budget` only after concrete bloat) | `[executor-runtime]` | watching |

## Per-Item Detail

(Empty until the first item is pulled. Pattern from `W12-executor-subpackaging.md`: each `W13-N` block records landing date, commit hashes, module locations new/modified, LoC changes, tests added/modified at real module import paths, live-scan validation if applicable.)

## W12 Lessons Learned (carry-forward)

From `W12-close-acceptance.md` §8.3 (now archived). Three operational
lessons to keep in mind when planning W13 splits and validations:

1. **Container build cache must be reset between W13-N iterations.**
   The W12-5 first live-scan run hit a stale executor container with
   pre-W12-5 code; only the second UI-triggered scan (after
   `make exec-build && make exec-up`) saw the refactored code. Plan
   the live-scan step to require an explicit rebuild + bring-up before
   each detection-relevant comparison.
2. **Tests-driven refactor still requires monkey-patch awareness.**
   The W12-5 split needed a `_resolve_vscode_logs_dir()` lazy-facade
   helper specifically so the 23-case existing safety net's
   `monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)`
   pattern would survive after `VSCODE_LOGS_DIR` moved to the new
   module. W13 split candidates should pre-audit similar monkeypatch
   dependencies before relocating module-level constants.
3. **Plan validation pass is high-leverage.** The W12-5 plan
   originally missed three re-export names (`_TIMESTAMP_RE`,
   `_activation_within_monitoring_window`, `VSCODE_LOGS_DIR`); a
   pre-implementation grep audit caught them. Apply the same
   discipline to W13 plans: explicit grep audit for every name that
   moves, before the first refactor commit.

## References

- Plan source: `documents/REFACTOR_OPTIMIZATION.md` §11.10.
- Backlog: `documents/POST_POC_BACKLOG.md` — `[FOLLOWUP …]` items
  marked W13 / W13-X / W13-X watching.
- Predecessor lane (frozen): `W12-executor-subpackaging.md` (stable
  IDs `W12-0`..`W12-5`).
- Older predecessor lanes (frozen, stable-ID-only):
  `W11-monitor-lifecycle.md` (`W11-1`..`W11-8`),
  `W8-security.md` (`W8-1`..`W8-9`).
- W12 close-out evidence (archived):
  `documents/archive/active-work/W12-close-acceptance-completed-2026-05-10.md`.
- Architecture rules entrypoint: `AGENTS.md` (root).
- Task routing: `documents/AGENT_CONTEXT.md`.
- Authoritative current-state pointer: `documents/REFACTOR_STATUS.md`.
