# CLAUDE.md

`Last Updated: 2026-05-18 (W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472 — W15-1..W15-7 sub-iter slate + W15-1 post-slate typing hotfix + close-out hygiene pass (doc preamble truth-state refresh across 7 canonical docs, ADR 0011 catalog endpoint posture gate, compose image SHA pin, GH action trivy version pin); W16 active on main branch per user direction — no separate week16 branch; W16 scope: 6+1 sub-iter — scenario-accountant emit-site fix (W16-1, HIGH prod regression W14-1 carry-over), analysis-job-worker-entry CRUD ownership (W16-2, W15 audit finding), report-finalize top-level field sync drift (W16-3, W14 carry-over), health-reconciliation responsibility split (W16-4, W15 audit finding), simulation-progress-cancel family closeout (W16-5, W11+ umbrella 3 sub-items), hygiene splits + Alembic round-trip fixture (W16-6), close-out (W16-7); plan source REFACTOR_OPTIMIZATION.md §14, active tracker active-work/W16-regression-and-audit-closeout.md; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 close-out PR #20 week13 -> main merged 2026-05-13 via 772deb3)`

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
  W14 by section 12; W15 by section 13; W16 by section 14. W13 closed
  `2026-05-13` (PR #20 `772deb3`); W14 closed `2026-05-14` (PR #21
  `4e03c8d`); **W15 closed `2026-05-17` and merged via PR #22 (`6161472`)
  on `2026-05-18`** — W15-1..W15-7 sub-iter slate + W15-1 post-slate
  typing hotfix + close-out hygiene pass (doc preamble truth-state
  refresh across 7 canonical docs, ADR 0011 catalog endpoint posture
  gate, compose image SHA pin, GH action trivy version pin). Frozen
  tracker: `documents/active-work/W15-codex-uclass-bounds-posture.md`.
  **Active phase: W16 — Carry-Over Closeout + Audit Findings +
  Production Regression**, active `2026-05-18` **on `main` per user
  direction — no separate `week16` branch is opened; sub-iter commits
  land directly on `main` and the W16 tracker freezes at scope close**.
  Active tracker:
  `documents/active-work/W16-regression-and-audit-closeout.md`. W16
  scope (6+1 sub-iter, severity-leading): W16-1 scenario-accountant
  upstream emit-site fix (W14-1 root-cause split; HIGH prod regression
  observed `2026-05-14` + `2026-05-15`); W16-2 analysis-job-worker-entry
  CRUD ownership (W15 audit finding; row-lock-aware lifecycle CRUD
  primitive, preserve W13-13 CAS); W16-3 report-finalize top-level
  field sync drift (W14 production scan-driven investigation; couples
  with W16-1); W16-4 health-reconciliation responsibility split (W15
  audit finding; behavior-preserving extraction, W13-1 HMAC gates
  preserved); W16-5 simulation-progress-cancel family closeout (W11+
  umbrella, 3 sub-items: `heartbeat-sandbox-reset-off-thread` +
  `dedupe-step-progress-schemas` + `heartbeat-refactor`); W16-6 hygiene
  splits + Alembic round-trip fixture
  (`marketplace-router-test-suite-split` 2374 LoC +
  `test-import-graph-policy-dump-split` 767 LoC +
  `w13-4-alembic-roundtrip-programmatic` fresh-DB-per-test fixture);
  W16-7 close-out hygiene + canonical preamble refresh (no
  `week16 -> main` PR per main-branch direction). Final W15 post-merge
  bar (re-recorded at W16-1 pull): `tests/architecture/` **198 passed**
  (+26 from W14 final 172); `make test-security` **215 passed**
  (unchanged from W13 final). Past trackers are stable-ID references
  only: W15, W14, W13, W12, W11, and W8.
- `documents/archive/` is frozen reference; not on the default read path.
  Open only when a slim canonical explicitly points there.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
