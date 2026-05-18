# CLAUDE.md

`Last Updated: 2026-05-18 (W17 active — authoring on week17 branch per user direction; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. W17-0 doc-reconcile in progress; W17-1..W17-6 reserved: attribution-count-parity closeout (W16-3 carry-over), lifecycle harness scaffold (enabler), heartbeat-sandbox-reset-off-thread (W16-5 carry-over), heartbeat-refactor (W16-5 carry-over), hygiene cleanup batch, close-out hygiene + §15 self-stamp. Entry gate post-merge bar: tests/architecture/ 199 passed; make test-security 220 passed; full suite 1893 passed, 9 skipped. W16-0..W16-7 sub-iter slate complete: W16-0 doc-reconcile (0e243ca + d78aa9c); W16-1 scenario-accountant emit-site fix (01f910a + a4a050e); W16-2 analysis-job worker-entry CRUD ownership (9d6d110 + c8b7811); W16-3 report-finalize null-leakage half (fa430f2 + e3d4a0c; attribution-count-parity split to W17); W16-4 health-reconciliation responsibility split (304b99f + 384d276); W16-5 simulation-progress-cancel scope reduction (1 rejected, 2 deferred to W17, e21a05c); W16-6 hygiene splits + Alembic fresh-DB fixture (d40bb01); W16-7 close-out hygiene (8bf3c6b) + post-PR unaccounted_dropout surface pin (78f080e). W15 closed via PR #22 MERGED 2026-05-18 via 6161472; W14 closed via PR #21 MERGED 2026-05-14 via 4e03c8d; W13 close-out PR #20 merged 2026-05-13 via 772deb3)`

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
  Yatırımı + Hygiene Sweep**, **on the `week17` branch per user
  direction `2026-05-18` (W11-W16 paterni preserved)**. Sub-iter
  slate `W17-0..W17-6` reserved: W17-0 doc-reconcile (in progress);
  W17-1 `attribution-count-parity` closeout (W16-3 carry-over); W17-2
  lifecycle harness scaffold (enabler for W17-3/4 — real Postgres DB
  via `fresh_alembic_engine` + Playwright mock surface; W17's heaviest
  parça); W17-3 `heartbeat-sandbox-reset-off-thread` (W16-5 carry-over,
  harness-gated; W13-1 HMAC + W13-12 fail-closed + W13-13 CAS pattern
  byte-identical); W17-4 `heartbeat-refactor` (W16-5 carry-over,
  W17-3 üzerine, byte-identical); W17-5 hygiene cleanup batch (3-5
  low-risk `[CLEANUP]` items); W17-6 close-out hygiene + canonical
  preamble refresh + §15 self-stamp. Active tracker:
  `documents/active-work/W17-carryover-and-lifecycle-harness.md`.
  Close-out via `week17 -> main` PR; sub-iter commits land on
  `week17` and the W17 tracker freezes at scope close. Past trackers
  are stable-ID references only: W16, W15, W14, W13, W12, W11, and W8.
- `documents/archive/` is frozen reference; not on the default read path.
  Open only when a slim canonical explicitly points there.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
