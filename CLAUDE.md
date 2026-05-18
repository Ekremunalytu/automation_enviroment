# CLAUDE.md

`Last Updated: 2026-05-18 (W16 active — phase work complete; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. W16-0..W16-7 sub-iter slate complete: W16-0 doc-reconcile (0e243ca + d78aa9c); W16-1 scenario-accountant emit-site fix (HIGH prod regression W14-1 carry-over, 01f910a + a4a050e); W16-2 analysis-job worker-entry CRUD ownership (W15 audit, 9d6d110 + c8b7811); W16-3 report-finalize null-leakage half (W14 carry-over, fa430f2 + e3d4a0c; attribution-count-parity split to W17+ as [FOLLOWUP attribution-count-parity]); W16-4 health-reconciliation responsibility split (W15 audit, 304b99f + 384d276); W16-5 simulation-progress-cancel scope reduction (1 rejected, 2 deferred to W17+, e21a05c); W16-6 hygiene splits + Alembic fresh-DB fixture (d40bb01); W16-7 close-out hygiene + canonical preamble refresh (8bf3c6b) + post-PR unaccounted_dropout surface pin (78f080e). Final W16 bar: tests/architecture/ 199 passed (W15 final 172, +27); make test-security 220 passed (W13 final 215, +5); full suite 1893 passed. W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 close-out PR #20 week13 -> main merged 2026-05-13 via 772deb3)`

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
  Production Regression**, **phase work complete; W16 closed via PR
  #23 `week16 -> main` MERGED `2026-05-18` via `1b6d43f` (W11-W15
  paterni restored). W16-0..W16-7 sub-iter slate complete:**
  W16-0 doc-reconcile (`0e243ca` + `d78aa9c`); W16-1 scenario-accountant
  upstream emit-site fix (W14-1 root-cause split; HIGH prod regression
  observed `2026-05-14` + `2026-05-15`; `01f910a` + `a4a050e`); W16-2
  analysis-job-worker-entry CRUD ownership (W15 audit finding;
  row-lock-aware lifecycle CRUD primitive, W13-13 CAS preserved
  byte-identically; `9d6d110` + `c8b7811`); W16-3 report-finalize
  null-leakage half (W14 production scan-driven investigation; 5
  contract-seam additive fields + `build_report_data` coercions;
  attribution-count-parity half split to `[FOLLOWUP attribution-count-parity]`
  W17+; `fa430f2` + `e3d4a0c`); W16-4 health-reconciliation
  responsibility split (W15 audit finding; behavior-preserving
  extraction to `health/{security,handshake,reconciliation}.py`,
  W13-1 HMAC + W13-12 fail-closed gates preserved; `304b99f` +
  `384d276`); W16-5 simulation-progress-cancel scope reduction
  (`dedupe-step-progress-schemas` rejected on distinct-surface-roles
  rationale; `heartbeat-sandbox-reset-off-thread` +
  `heartbeat-refactor` deferred to W17+ pending lifecycle harness;
  doc-only `e21a05c`); W16-6 hygiene splits + Alembic fresh-DB fixture
  (`marketplace-router-test-suite-split` 2374 LoC → 5 endpoint-grouped
  files; `test-import-graph-policy-dump-split` 767 LoC → 4 thematic
  files; `w13-4-alembic-roundtrip-programmatic` skip removed + fresh
  Postgres DB per test via `fresh_alembic_engine` fixture; `d40bb01`);
  W16-7 close-out hygiene + canonical preamble refresh (`8bf3c6b`) +
  post-PR `unaccounted_dropout` surface pin (`78f080e`). Frozen tracker:
  `documents/active-work/W16-regression-and-audit-closeout.md`. Final
  W16 bar (recorded at W16-7 close-out, post-merge top-up `78f080e`):
  `tests/architecture/` **199 passed** (W15 final 172, +27);
  `make test-security` **220 passed** (W13 final 215, +5 — three of
  the +5 are the W16-7-followup `unaccounted_dropout` surface pins
  added post-PR on `2026-05-18`); full suite **1893 passed, 9 skipped**.
  Past trackers are stable-ID references only: W16, W15, W14, W13, W12,
  W11, and W8.
- `documents/archive/` is frozen reference; not on the default read path.
  Open only when a slim canonical explicitly points there.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
