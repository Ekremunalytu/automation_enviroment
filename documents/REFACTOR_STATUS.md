# Refactor Status

`Last Updated: 2026-05-18 (W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472 — W15-1..W15-7 sub-iter slate + W15-1 post-slate typing hotfix + close-out hygiene pass; W16 active on main branch per user direction — no separate week16 branch; W16 scope: 6+1 sub-iter — scenario-accountant emit-site fix (W16-1, HIGH prod regression W14-1 carry-over), analysis-job-worker-entry CRUD ownership (W16-2), report-finalize top-level field sync drift (W16-3), health-reconciliation responsibility split (W16-4), simulation-progress-cancel family closeout (W16-5), hygiene splits + Alembic round-trip fixture (W16-6), close-out (W16-7); plan source REFACTOR_OPTIMIZATION.md §14; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 close-out PR #20 week13 -> main merged 2026-05-13 via 772deb3)`

Active status board for current closure state. **Slim canonical** — verbose
phase evidence is frozen under dated snapshots:

- latest full snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-05-13.md`](archive/status/REFACTOR_STATUS_full_2026-05-13.md)
- previous full snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-05-11.md`](archive/status/REFACTOR_STATUS_full_2026-05-11.md)
- older full snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-05-07.md`](archive/status/REFACTOR_STATUS_full_2026-05-07.md)
- older W4-W8 snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-04-29.md`](archive/status/REFACTOR_STATUS_full_2026-04-29.md)

## Current State

- **W0-W7 closed `2026-04-23`** — PoC acceptance bar 11/11 green
  (`REFACTOR_OPTIMIZATION.md` §10.7).
- **PR345 + W8-0 closed `2026-04-27`** — target activation lifecycle PRs
  1-5 plus ADR 0006 landed; deterministic harness readiness gate landed.
- **W8 closed `2026-04-29`** — W8-1..W8-7 and W8-9 landed. W8-8 remains
  deferred under `[FOLLOWUP w8-8-manifest-emit-when-needed]`.
- **W9 closed `2026-05-04` via PR #9 (`d67944d`)** — ADR 0008 package-mode
  invocation accepted; dual-import fallback and runtime `sys.path.insert`
  debt removed.
- **W10 closed `2026-05-04` via PR #11 (`25e4c16`)** — contract hygiene,
  planner cleanup, typed report fields, and executor action enum landed.
- **W11 closed `2026-05-05` and merged via PR #14 (`50ca69e`)** — W11-1..W11-8
  monitor/workflow/storage split work landed.
- **W12 closed `2026-05-10` and merged via PR #18 (`33a0852`)** — W12-0..W12-5
  landed, plus UI Dockerfile digest pin, close-out coverage, and the Codex
  audit CRITICAL redaction fix. Final post-Codex-fix baseline at close commit
  `e8a9926`: `make check-all` green; `make test-local` 1452 passed /
  6 skipped / 6 deselected / 75 warnings; `make test-security` 211 passed /
  32 warnings; `tests/architecture/` 76 passed / 2 deselected. Tracker is
  frozen for stable-ID reference:
  [`active-work/W12-executor-subpackaging.md`](active-work/W12-executor-subpackaging.md).
- **W13 — Test Expansion + Observability closed `2026-05-13` and merged via
  PR #20 (`772deb3`).** Tracker:
  [`active-work/W13-test-expansion-observability.md`](active-work/W13-test-expansion-observability.md).
  W13-1..W13-13 are all GREEN. Final/post-merge bar: `make test-local`
  1551 passed / 10 skipped / 8 deselected; `make test-security` 215 passed;
  `tests/architecture/` 117 passed. W13-11/12/13 were pulled in-window from
  the close-gate review to preserve H6/H4 audit-trail integrity; remaining
  §11.10 umbrellas moved to W14.
- **W14 closed `2026-05-14` and merged via PR #21 (`4e03c8d`).** Tracker:
  [`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md).
  W14-1..W14-8 are all GREEN: W14-1 BLOCKER `[BUG scenario-dropout-upstream-
  root-cause]` triage downgraded to HIGH (`0c8bd02`); W14-2 (M4-M7 + M11
  input validation) `bde17be`; W14-3 (M13 + M14b + U4-U12 external-surface
  hardening) `941250d`; W14-4 (analysis-jobs-race lock symmetry +
  EvidenceEvent kind↔event_class 9-kind allowlist) `03b32bc`; W14-5 (logger
  consolidation + run-ID stamping + executor runtime fingerprint; ADR 0010;
  M5 docker-exec propagation byproduct) `dc79f61` + `9c095d2` + `db25d5f`;
  W14-6 (regression lock-in umbrella: bare-binary pragma ratchet +
  `executor.control` outbound gate + variable-indirect subprocess coverage)
  `2adad43` + `b031803` + `e42a448`; W14-7 post-slate hotfix
  (container-shipping regression + Python 3.10 UTC compat) `df925f8` +
  `c11ebd8`; W14-8 post-slate preventive gate (Python 3.11+ API forbid)
  `5638f82`. Final post-merge bar (re-recorded at W15-1 pull on `week15`):
  `tests/architecture/` 172 passed (171 from W14-8 + 1 ADR code fence gate
  added at close-out hygiene); `make test-security` 215 passed (unchanged
  from W13 final).
- **W15 closed `2026-05-17` and merged via PR #22 (`6161472`) on
  `2026-05-18`.** Frozen tracker:
  [`active-work/W15-codex-uclass-bounds-posture.md`](active-work/W15-codex-uclass-bounds-posture.md).
  W15-1..W15-7 all GREEN: W15-1 (`c58c365`, M10 sync analyze error
  taxonomy parity) + post-slate typing hotfix (`976dc96`); W15-2
  (`765cde7`, M12 `clean_workspace` is_symlink-before-rmtree); W15-3
  (`3512a7c`, U8 `activationEvents` bounds + Alembic field-length
  migration); W15-4 (`89e13e3`, UI bounds bundle U1/U2/U3 + U6);
  W15-5 (`43d6438`, I2 UI `/health` proxy + I4 lifecycle `for <id>`
  regex); W15-6 (`be52520`, ADR 0011 unauthenticated catalog endpoints
  posture Accepted + implemented Option A; Proposed at `e41722e`);
  W15-7 (`54e7a93` compose image SHA pin + `7ebbbfb` test extension +
  `452f1a1` trivy version pin + doc preamble truth-state refresh +
  `7ff31d9` close-out lint hygiene; W15-7 early pulls `a7a876e` +
  `2573e35`). W15 mid-iter hygiene `2026-05-16` added cross-doc
  preamble consistency arch gate + three new audit findings appended
  to `POST_POC_BACKLOG.md` —
  `[FOLLOWUP health-reconciliation-responsibility-split]`,
  `[CLEANUP marketplace-router-test-suite-split]`,
  `[FOLLOWUP analysis-job-worker-entry-crud-ownership]` — all defer
  to W16. Final post-merge bar (re-recorded at W16-1 pull):
  `tests/architecture/` **198 passed** (W14 final 172 + W15 sub-iter
  gates +26); `make test-security` **215 passed** (unchanged from W13
  final).
- **Active phase: W16 — Carry-Over Closeout + Audit Findings +
  Production Regression** (active `2026-05-18`; **on `main` per user
  direction — no separate `week16` branch**). Scope authored
  `2026-05-18` in
  [`active-work/W16-regression-and-audit-closeout.md`](active-work/W16-regression-and-audit-closeout.md);
  plan source [`REFACTOR_OPTIMIZATION.md §14`](REFACTOR_OPTIMIZATION.md).
  7 sub-iter scoped (`W16-1..W16-7`): production regression closeout
  (W14-1 carry-over `scenario-accountant-conservation-split` emit-site
  fix), W15 mid-iter audit findings closeout (CRUD ownership +
  health-reconciliation split), W14 carry-over (report-finalize
  top-level field sync drift), W11+ heartbeat umbrella closeout
  (`simulation-progress-cancel` family 3 sub-items), hygiene splits
  (marketplace-router + test-import-graph) + Alembic round-trip
  fixture, and close-out hygiene. **No `week16 -> main` PR per
  main-branch direction**; sub-iter commits land directly on `main`
  and the W16 tracker freezes at scope close.

## W13 Status Summary

| Scope | Status |
|---|---|
| Acceptance bar | W13-1..W13-7 closed H3/H4/H5/H6/M1/M9 from the 2026-05-10 Codex Cloud audit. |
| §11.10 GOAL pulls | W13-8 benign silence fixture 3->5, W13-9 `.env` gitignore gate, and W13-10 singleton-lock recovery closed. |
| Close-gate pulls | W13-11 HMAC python secret target-install race, W13-12 fail-closed harness handshake, and W13-13 worker-start cancel-race CAS closed in-window. |
| Merge | PR #20 `week13 -> main` merged `2026-05-13` via `772deb3`; W13 tracker remains as the stable-ID evidence file. |

## Current Deferrals

- `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` — programmatic Alembic
  upgrade/downgrade test, **pulled to W16-6** (hygiene splits + fresh-DB
  fixture).
- `[FOLLOWUP analysis-jobs-race]` — **closed** by W14-4 on `2026-05-13`;
  `complete_analysis_job` + `fail_analysis_job` now acquire
  `with_for_update()` and gate against `_TERMINAL_JOB_STATUSES`.
- `[FOLLOWUP simulation-progress-cancel]` remaining subitems
  (`heartbeat-sandbox-reset-off-thread`, `dedupe-step-progress-schemas`,
  `heartbeat-refactor`) — **pulled to W16-5** (umbrella closeout).
- `[BUG scenario-dropout-upstream-root-cause]` — **closed** by W14-1 on
  `2026-05-13` via `0c8bd02` (deterministic repro matrix landed + conservation
  guard; severity downgraded BLOCKER -> HIGH same day; upstream emit-site
  split **pulled to W16-1** under `[FOLLOWUP scenario-accountant-conservation-split]`).
- `[FOLLOWUP analysis-job-worker-entry-crud-ownership]` — W15 mid-iter audit
  finding, **pulled to W16-2** (row-lock-aware lifecycle CRUD primitive).
- `[FOLLOWUP health-reconciliation-responsibility-split]` — W15 mid-iter
  audit finding, **pulled to W16-4** (behavior-preserving extraction with
  W13-1 HMAC gates preserved).
- `[FOLLOWUP report-finalize-top-level-field-sync-drift]` — W14 production
  scan-driven investigation, **pulled to W16-3** (finalize ordering /
  `report.save()` drift).
- `[CLEANUP marketplace-router-test-suite-split]` + `[CLEANUP test-import-graph-policy-dump-split]`
  — **pulled to W16-6** (hygiene splits bundle).

## Read Order

When updating this file, keep it as a slim closure board. Put verbose
evidence in `documents/archive/status/`, keep pull-next detail in
`POST_POC_BACKLOG.md`, keep closed W13 mechanics in
`active-work/W13-test-expansion-observability.md`, keep closed W14
mechanics in `active-work/W14-codex-acceptance-observability.md`,
keep closed W15 mechanics (Codex U-class close-out + UI bounds +
posture; W15-1..W15-7 closed; merged via PR #22 on `2026-05-18`) in
`active-work/W15-codex-uclass-bounds-posture.md`, and keep active
W16 scope (carry-over closeout + W15 audit findings + production
regression; **on `main` per user direction, no separate week16
branch**) in `active-work/W16-regression-and-audit-closeout.md`.
