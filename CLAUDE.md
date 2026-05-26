# CLAUDE.md

`Last Updated: 2026-05-26 (W19 active — Hat-1 closed + live-verified via W19-2-followup-2 d5de9ca; Hat-2 fully closed via W19-3 schema landing (primary d2e83e7 + self-stamp 39121e4 + W19-3-followup-2 8-doc preamble refresh 9b56e94) + W19-4 onDebug* harness_nonce producer/consumer wire (7d44b0e at executor/flows/playwright/health/reconciliation.py:347-348 producer + reconciliation.py:85-90 consumer + 7 new tests) + W19-X onDebug* live close-out (8b7b7f6 primary + a3e634f self-stamp — closes Bug A planner routing onDebug → harness:run_current_stimulus, Bug B marker channel destination OutputChannel + parser glob, Bug C HMAC secret reactivation race; live anchor activation_report_ms-python.python-2026.5.2026052501-8247e05ec9ef.json shows 2/2 onDebug* stamped + harness_verification_unconfirmed suppressed; +15 new behavioral tests) + W19-5 onTerminal+onLM log_record stamp (primary e537ebd + this self-stamp — producer arm extension at reconciliation.py:347-365 sibling elif to W19-4 onDebug arm; live-anchor evidence confirmed all 6 unstamped attempts already carried harness_trace:<attempt_id> evidence via existing runCurrentStimulus + harness_fallback="run_current_stimulus" paths → no JS / no new predicate / no planner mapping needed (plan deviation captured in primary commit body); +7 new behavioral tests at test_playwright_health_reconciliation.py:1175-1369; W19-4 scope-discipline parametrize narrowed to onCommand only); test bar tests/architecture/ 202 / make test-security 220 / full suite 1973 passed, 9 skipped, 8 deselected on the week19 branch (per user direction 2026-05-21; W11-W18 paterni preserved); W19-0..W19-5 closed; live smoke + W19-6 close-out pending; stable IDs W19-1..W19-5 reserved at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar, assigned at first pull per W11-W18 precedent. Driving signal: Codex live-run validation 2026-05-21 of ms-python.python @ 992ad028f3df reports automation_health.status=degraded + run_quality=low while W19-2 live re-anchor now satisfies unaccounted_dropout == 0 and static W18 final bar (1907/201/220) remains green. W19 Hat-1 closed + live-verified (executor muhasebe bug → unaccounted_dropout); Hat-2 fully closed synthetically (W19-3 schema + W19-4 onDebug* producer/consumer + W19-X onDebug* live close-out + W19-5 onTerminal+onLM log_record stamp — entire harness_verification_unconfirmed_present reason driver closed); Hat-3 (coverage matrix promotion → 6 capabilities missing) deferred to W20-W22 per multi-iter roadmap. §17 W19 plan source + §18-§20 W20-W22 multi-iter roadmap (split at W19-0 from the original §17-§20 combined header). W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; final W18 bar tests/architecture/ 201 passed; make test-security 220 passed; full suite 1907 passed, 9 skipped, 8 deselected. W19-3 test bar: tests/architecture/ 202 passed, make test-security 220 passed, full suite 1932 passed (W19-2 baseline 1913 + W19-3 +19). W18 sub-iter audit trail (frozen, all closed): W18-0 doc-reconcile (89d0c9b); W18-1 ADR 0012 Option A1 (acf6cc9 + 73d8a5c); W18-2 heartbeat refactor implementation (a9bffb1 + 78ed7cc + b5b64b6 + 306d744); W18-3 lifecycle harness extension tests (92b310d + 32d9905); W18-4 close-out hygiene (3f4f95a); W18-4-followup (e1043e5). W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md; W19 active tracker: documents/active-work/W19-live-run-root-cause.md; multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md. W16-0..W16-7, W17-0..W17-7, W18-0..W18-4 sub-iter slate audit trail in respective frozen trackers; full preamble history pre-2026-05-21 in archive snapshots.)`

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
  W14 by section 12; W15 by section 13; W16 by section 14; W17 by section 15;
  W18 by section 16.
  **W19 by section 17 (active `2026-05-21` on `week19` branch);
  W20-W22 by sections 18-20 (planning state); source-of-truth tracker
  `documents/active-work/W18-W22-roadmap.md`. W18 closed `2026-05-21`
  via PR #26 / `9874e79`.**
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

  **Previous phase: W18 — Heartbeat Refactor — closed via PR #26
  `week18 -> main` MERGED `2026-05-21` via `9874e79` (per user
  direction; W11-W17 paterni preserved). Sub-iter slate
  W18-0..W18-4 + W18-4-followup fully delivered**: W18-0
  doc-reconcile (`89d0c9b`); W18-1 ADR
  `documents/adrs/0012-heartbeat-thread-relocation.md` Option A1
  Accepted (`acf6cc9` + `73d8a5c` followup) — dedicated
  sandbox-reset coordinator for the step-1 setup reset; cancel-path
  teardown reset stays on the heartbeat thread; W18-2 heartbeat
  refactor implementation (`a9bffb1` + `78ed7cc` + `b5b64b6` +
  `306d744`) — step-1 reset off the worker thread via
  `_run_reset_off_thread` coordinator (function-extension shape,
  ~42 LOC; W17-2 harness smoke byte-identical); W18-3 lifecycle
  harness extension tests — parallel reset / idempotency /
  reset-during-finalize (`92b310d` + `32d9905`); W18-4 close-out
  hygiene (`3f4f95a`); W18-4-followup (`e1043e5`) 4 W18-2
  invariant pins + 2 doc drift fixes. Final W18 bar:
  `tests/architecture/` **201 passed**; `make test-security`
  **220 passed**; full suite **1907 passed, 9 skipped, 8
  deselected**. Frozen tracker:
  `documents/active-work/W18-heartbeat-refactor.md`.

  **Active phase: W19 — Live-Run Kök Neden: Dropout + Harness
  Verification — active `2026-05-21` on the `week19` branch (per
  user direction 2026-05-21; W11-W18 paterni preserved). §17 W19
  plan source in `documents/REFACTOR_OPTIMIZATION.md`. W19-0..W19-2
  are closed; W19-3..W19-6 remain pending**: W19-0 doc-reconcile
  (`72712bd` + `086d7a5`); W19-1 RED dropout fixture
  (`6a21cf3` + `fd02ca4`); W19-2 emit-site fix (`89b64da` +
  `d9c6262`) + W19-2-followup-2 live re-anchor (`d5de9ca`)
  satisfying `unaccounted_dropout == 0`. Driving signal: Codex live-run
  validation of `ms-python.python` @ `992ad028f3df` (2026-05-21)
  reports `automation_health.status=degraded` + `run_quality=low`
  while W19-2 live re-anchor now satisfies `unaccounted_dropout == 0`.
  Plan identifies three independent problem hatları; **Hat-1 is closed +
  live-verified; Hat-2 remains active**: Hat-1 executor muhasebe bug
  (`[BUG scenario-unaccounted-dropout-regression-fixture]` W19-1 +
  `[BUG scenario-unaccounted-dropout-debug-refactor]` W19-2) + Hat-2
  harness verification gap
  (`[GOAL harness-verification-contract-event-level]` W19-3
  schema landing + `[FOLLOWUP harness-verification-debug-events]`
  W19-4 onDebug* nonce + consumer wire (closed via `7d44b0e`) +
  `[FOLLOWUP harness-verification-terminal-and-lm-tool]` W19-5
  onTerminal + onLM local-only (pending)). **Hat-3 coverage matrix promotion deferred to
  W20-W22 per multi-iter roadmap** (§18-§20). W19 acceptance
  (live-run-driven): `unaccounted_dropout == 0` (must-pass);
  `harness_verification_unconfirmed_present` reason drops
  (must-pass); `run_quality: low → medium` (expected);
  `verification_gap_present` drops (stretch);
  `automation_health.status: degraded` OK (W20 will close
  `official_unresolved_present`). Active tracker:
  `documents/active-work/W19-live-run-root-cause.md`; multi-iter
  roadmap source-of-truth:
  `documents/active-work/W18-W22-roadmap.md`. §17 W19 plan source
  + §18-§20 W20-W22 multi-iter roadmap:
  `documents/REFACTOR_OPTIMIZATION.md`. W19-W22 stable IDs
  reserved: `POST_POC_BACKLOG.md` W19 Pull-Forward Acceptance Bar
  + W20-W22 Roadmap Acceptance Bar. W19 plan went through 3
  review rounds (Codex live-run + GPT × 2; same plan dosyası
  W18-W22 multi-iter roadmap).
- `documents/archive/` is frozen reference; not on the default read path.
  Open only when a slim canonical explicitly points there.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
