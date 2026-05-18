# CLAUDE.md

`Last Updated: 2026-05-18 (W17 active — phase work complete; close-out via week17 -> main PR pending (no push per user direction 2026-05-18); W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. W17-0..W17-6 sub-iter slate complete: W17-0 doc-reconcile (4508c2e); W17-1 attribution-count-parity closeout (8c26d02 + 0a8f59e); W17-2 lifecycle harness scaffold (ff98235 + 44f96c5); W17-3 + W17-4 scope-reduced doc-only (c4c0646 DESIGN-NEEDED deferred to W18); W17-5 hygiene single-item (394d40d postgres-version-fact-drift + 0cbe1d0); W17-6 close-out this commit. Final W17 bar: tests/architecture/ 200 passed; make test-security 220 passed; full suite 1899 passed, 9 skipped, 4 deselected (+6 from W16 final 1893). W16-0..W16-7 sub-iter slate complete: W16-0 doc-reconcile (0e243ca + d78aa9c); W16-1 scenario-accountant emit-site fix (01f910a + a4a050e); W16-2 analysis-job worker-entry CRUD ownership (9d6d110 + c8b7811); W16-3 report-finalize null-leakage half (fa430f2 + e3d4a0c; attribution-count-parity split to W17); W16-4 health-reconciliation responsibility split (304b99f + 384d276); W16-5 simulation-progress-cancel scope reduction (1 rejected, 2 deferred to W17, e21a05c); W16-6 hygiene splits + Alembic fresh-DB fixture (d40bb01); W16-7 close-out hygiene (8bf3c6b) + post-PR unaccounted_dropout surface pin (78f080e). W15 closed via PR #22 MERGED 2026-05-18 via 6161472; W14 closed via PR #21 MERGED 2026-05-14 via 4e03c8d; W13 close-out PR #20 merged 2026-05-13 via 772deb3)`

This file is intentionally a thin pointer. Do not duplicate phase summaries or
architecture maps here; that caused drift.

## Read Path

1. `AGENTS.md` — hard architectural and security rules.
2. `documents/AGENT_CONTEXT.md` — task-routing decision tree.
3. One matching `documents/agent-lanes/*.md` file.
4. `documents/REFACTOR_STATUS.md` (slim canonical) only when current phase
   state matters.
5. Subsystem docs only when the lane doc points to them. Slim canonicals
   link out to `documents/<area>/` splits — open the split, not the full
   canonical, for detail.
6. `documents/active-work/<file>.md` only when the lane doc points to it.

## Operating Rules

- Keep context narrow; start from one lane and do not preload
  `documents/`. Ignore generated or heavy trees unless the task
  explicitly targets them.
- If docs disagree with code/tests, trust code/tests and update the
  stale doc after confirming the drift.
- Current state is owned by `documents/REFACTOR_STATUS.md` (slim canonical).
- Deferred and pull-next work is owned by `documents/POST_POC_BACKLOG.md`
  (slim canonical).
- W8-W13 planning is owned by `documents/REFACTOR_OPTIMIZATION.md` section 11;
  W14 by section 12; W15 by section 13; W16 by section 14; W17 by section 15.
  W13 closed `2026-05-13` (PR #20 `772deb3`); W14 closed `2026-05-14` (PR #21
  `4e03c8d`); W15 closed `2026-05-17` and merged via PR #22 (`6161472`)
  on `2026-05-18`. **W16 closed `2026-05-18` and merged via PR #23
  (`1b6d43f`) on `2026-05-18`** — Carry-Over Closeout + Audit Findings
  + Production Regression. W16-0..W16-7 sub-iter slate complete:
  W16-0 doc-reconcile (`0e243ca` + `d78aa9c`); W16-1 scenario-accountant
  upstream emit-site fix (`01f910a` + `a4a050e`); W16-2 analysis-job
  worker-entry CRUD ownership (`9d6d110` + `c8b7811`); W16-3 report-
  finalize null-leakage half (`fa430f2` + `e3d4a0c`; attribution-count-
  parity split to W17 as `[FOLLOWUP attribution-count-parity]`);
  W16-4 health-reconciliation responsibility split (`304b99f` +
  `384d276`); W16-5 simulation-progress-cancel scope reduction (1
  rejected on distinct-surface-roles rationale, 2 deferred to W17
  pending lifecycle harness; doc-only `e21a05c`); W16-6 hygiene splits
  + Alembic fresh-DB fixture (`d40bb01`); W16-7 close-out hygiene +
  canonical preamble refresh (`8bf3c6b`) + post-PR `unaccounted_dropout`
  surface pin (`78f080e`). Frozen tracker:
  `documents/active-work/W16-regression-and-audit-closeout.md`. Final
  W16 bar: `tests/architecture/` **199 passed** (+27 from W15 final
  172); `make test-security` **220 passed** (+5 from W13 final 215,
  three added post-PR as `unaccounted_dropout` surface pins matching
  the live-scan shape); full suite **1893 passed, 9 skipped**.
  **Active phase: W17 — Carry-Over Closeout + Lifecycle Harness
  Yatırımı + Hygiene Sweep — phase work complete; close-out via
  `week17 -> main` PR pending (no push per user "push yapma"
  direction `2026-05-18`); on the `week17` branch (W11-W16 paterni
  preserved)**. W17-0..W17-6 sub-iter slate complete: W17-0
  doc-reconcile (`4508c2e`); W17-1 `attribution-count-parity`
  closeout (`8c26d02` + `0a8f59e` self-stamp — `build_evidence_bundle`
  activation emit-site stamps `is_target_extension_event`
  byte-identical with `count_target_activations` predicate, 4
  invariant tests including W17-1 parity contract pin); W17-2
  lifecycle harness scaffold (`ff98235` + `44f96c5` self-stamp —
  `LifecycleHarness` + `lifecycle_harness` fixture at
  `tests/workflows/marketplace/test_lifecycle_harness.py`; W17-3
  enabler with cancel-via-heartbeat smoke pinning thread identity
  and `reload_window=True` kwargs; intentional scope cuts — no
  end-to-end `run_analysis_job` drive, no `fresh_alembic_engine`);
  W17-3 + W17-4 scope-reduced doc-only (`c4c0646` — DESIGN-NEEDED
  for thread-relocation refactor shape because worker-thread step-1
  reset is a HARD SYNC POINT for W13-11 HMAC secret consume and
  the heartbeat thread starts only at step 4; multiple plausible
  refactor shapes have different invariant cost; deferred to W18
  dedicated sub-iter opening with ADR / §16 plan entry); W17-5
  hygiene single-item (`394d40d` `[CLEANUP postgres-version-fact-drift]`
  closeout at `seed_project_2.py` synthetic-fixture
  `postgres:15 → postgres:16-alpine` stack alignment + `0cbe1d0`
  self-stamp; other 4 cleanup candidates deferred to W18+
  opportunistic pull-as-found); W17-6 close-out hygiene this commit
  (canonical preamble refresh across 7 docs + §15 self-stamp + W17
  tracker freeze). Active tracker:
  `documents/active-work/W17-carryover-and-lifecycle-harness.md`.
  Final W17 bar: `tests/architecture/` **200 passed** (W16 final
  199, +1 from W17-0 W16 close-out fact gate); `make test-security`
  **220 passed** (Makefile target list; W17-7a `bf983eb` enrolled
  `test_unaccounted_dropout_surface.py` — 217 → 220 recovers the
  W16-7-followup audit-trail count); full suite **1899
  passed, 9 skipped, 4 deselected** (W16 final 1893, +6: 4 W17-1
  invariant tests + 1 W17-0 README phase-pointer gate + 1 W17-2
  harness smoke). Past trackers are stable-ID references only:
  W17, W16, W15, W14, W13, W12, W11, and W8.
- `documents/archive/` is frozen reference; not on the default read path.
  Open only when a slim canonical explicitly points there.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
