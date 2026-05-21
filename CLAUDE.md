# CLAUDE.md

`Last Updated: 2026-05-21 (W18 active — W18-0 doc-reconcile in progress on the week18 branch per user direction 2026-05-21 (W11-W17 paterni preserved). W18-W22 multi-iter roadmap entered W18 execution phase via this commit; sub-iter slate W18-0..W18-4 reserved per §16 plan: W18-0 doc-reconcile this commit + W18-1 ADR documents/adrs/0012-heartbeat-thread-relocation.md + W18-2 heartbeat refactor implementation + W18-3 lifecycle harness extension tests + W18-4 close-out PR week18 -> main. Driving signal: Codex live-run validation 2026-05-21 of ms-python.python @ 992ad028f3df reports automation_health.status=degraded + run_quality=low while static W17 final bar is green; W18 closes W17-3/W17-4 DESIGN-NEEDED heartbeat thread relocation deferral; W19-W22 carry the dropout fix + harness verification + coverage promotion per multi-iter roadmap. W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d. Final W17 bar (unchanged): tests/architecture/ 200 passed; make test-security 220 passed; full suite 1899 passed, 9 skipped, 4 deselected. W18 active tracker: documents/active-work/W18-heartbeat-refactor.md. W16-0..W16-7, W17-0..W17-7 sub-iter slate audit trail in respective frozen trackers; W18-0 in-progress, W18 final bar TBD; full preamble history pre-2026-05-21 in archive snapshots.)`

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
  **W18-W22 multi-iter roadmap by sections 16-20 (W18 active as of
  2026-05-21; authored 2026-05-21); source-of-truth tracker
  `documents/active-work/W18-W22-roadmap.md`.**
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
  **Previous phase: W17 — Carry-Over Closeout + Lifecycle Harness
  Yatırımı + Hygiene Sweep — closed via PR #25 `week17 -> main`
  MERGED `2026-05-18` via `bff565d`; on the `week17` branch
  (W11-W16 paterni preserved)**. W17-0..W17-6 sub-iter slate complete: W17-0
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

  **Active phase: W18 — Heartbeat Refactor — W18-0 doc-reconcile
  in progress on the `week18` branch (per user direction 2026-05-21;
  W11-W17 paterni preserved). Sub-iter slate W18-0..W18-4 reserved
  per §16 plan**: W18-0 doc-reconcile this commit; W18-1 ADR
  `documents/adrs/0012-heartbeat-thread-relocation.md` (3 plausible
  refactor shapes — dedicated reset thread / unified reset queue /
  pipeline restructure — with invariant-cost trade-offs against
  W13-1 HMAC eager-consume / W13-3 two-phase cancel / W13-13 CAS /
  W16-2 facade lock; NO CODE); W18-2 heartbeat refactor
  implementation (W17-2 harness smoke MUST still pass byte-identically);
  W18-3 lifecycle harness extension tests (parallel reset +
  idempotency + reset-during-finalize, per W17-2 module docstring
  L27-35); W18-4 close-out PR `week18 -> main`. Active tracker:
  `documents/active-work/W18-heartbeat-refactor.md`. Driving signal:
  Codex live-run validation of `ms-python.python` @ `992ad028f3df`
  (2026-05-21) reports `automation_health.status=degraded` +
  `run_quality=low` while static W17 final bar (1899/200/220)
  remains 🟢. Plan identifies three independent problem hatları
  (executor muhasebe bug → unaccounted_dropout; harness verification
  gap → declared ≠ verified; coverage matrix promotion → 6
  capabilities missing in official track) and three capability
  layers (A: activation events 29 entry, B: 18-bucket taxonomy,
  C: VSCode manifest capabilities — spec-compliant). W19-W22
  follow-on iters: **W19** live-run kök neden — dropout fix
  (Hat-1) + harness verification contract event-level (Hat-2);
  **W20** coverage promotion round 1 (easy: `scm` + `settings`
  official); **W21** coverage promotion round 2 (mid:
  `testing` / `comments` / `workspace_trust`; container hardening
  stretch); **W22** coverage promotion round 3 (hard: `chat`
  policy ADR + implementation) + attribution depth + sandbox-evasion
  ADR. Roadmap source-of-truth:
  `documents/active-work/W18-W22-roadmap.md`. §16-§20 plan
  entries: `documents/REFACTOR_OPTIMIZATION.md`. W18-W22 stable
  IDs reserved: `POST_POC_BACKLOG.md` W18-W22 Roadmap
  Acceptance Bar. Plan went through 3 review rounds (Codex
  live-run + GPT × 2).
- `documents/archive/` is frozen reference; not on the default read path.
  Open only when a slim canonical explicitly points there.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
