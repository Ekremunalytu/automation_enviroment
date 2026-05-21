# Refactor Status

`Last Updated: 2026-05-21 (W18 active — closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; W18-0..W18-4 sub-iter slate (per user direction 2026-05-21; W11-W17 paterni preserved); W18-4-followup post-merge audit landed this commit; §16 W18 plan source + §17-§20 W19-W22 multi-iter roadmap (split at W18-4 close-out). W18 sub-iter audit trail: W18-0 doc-reconcile (89d0c9b); W18-1 ADR 0012 Option A1 (acf6cc9 + 73d8a5c followup); W18-2 heartbeat refactor implementation — step-1 reset off worker thread via dedicated coordinator (a9bffb1 + 78ed7cc ADR self-stamp + b5b64b6 ruff-format + 306d744 full-repo lint sweep with pre-commit install); W18-3 lifecycle harness extension tests — parallel reset / idempotency / reset-during-finalize (92b310d + 32d9905 self-stamp); W18-4 close-out hygiene (3f4f95a) — 8-doc canonical preamble refresh + §16 W18 self-stamp + W18 tracker freeze; W18-4-followup (e1043e5) — 4 W18-2 invariant pins + 2 pre-existing doc drift fixes. Final W18 bar: tests/architecture/ 201 passed (W17 final 200 + W18-0 README phase-pointer arch gate W17->W18 transition); make test-security 220 passed (unchanged from W17); full suite 1907 passed, 9 skipped, 8 deselected (W17 final 1899 + W18-0 +1 + W18-3 +3 + W18-4-followup +4 W18-2 invariant tests via e1043e5). Driving signal: Codex live-run validation 2026-05-21 of ms-python.python @ 992ad028f3df reporting automation_health.status=degraded + run_quality=low while static W17 final bar is green; W18 closes W17-3/W17-4 DESIGN-NEEDED heartbeat thread relocation deferral via ADR 0012 Option A1. Roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md; W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md. §16 W18 plan + §17-§20 W19-W22 plan in REFACTOR_OPTIMIZATION.md; POST_POC_BACKLOG.md W18 Pull-Forward Acceptance Bar (closed) + W19-W22 Roadmap Acceptance Bar (planning). Plan went through 3 review rounds (Codex live-run + GPT × 2). W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f; W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 close-out PR #20 week13 -> main merged 2026-05-13 via 772deb3. Final W17 bar (unchanged): tests/architecture/ 200 passed; make test-security 220 passed; full suite 1899 passed, 9 skipped, 4 deselected. Full W16/W17/W18 sub-iter audit trail in respective frozen trackers; full preamble history pre-2026-05-21 in archive snapshots.)`

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
- **W16 closed `2026-05-18` and merged via PR #23 (`1b6d43f`)** —
  Carry-Over Closeout + Audit Findings + Production Regression
  window. Scope authored
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
  fixture, and close-out hygiene. **Close-out via `week16 -> main`
  PR** (W11-W15 paterni restored 2026-05-18); sub-iter commits land
  on `week16` and the W16 tracker freezes at scope close. **W16-1
  pulled `2026-05-18` via `01f910a`** (dispatch outcome=None emit-site
  closed; `[FOLLOWUP scenario-accountant-conservation-split]` marked
  dispatch-layer-closed in `POST_POC_BACKLOG.md`). **W16-2 pulled
  `2026-05-18` via `9d6d110`** (analysis-job worker-entry CRUD
  ownership facade extracted to
  `appcore/storage/crud_ops/analysis_jobs/lifecycle.claim_queued_analysis_job_at_worker_entry`;
  AGENTS.md:57 compliance restored, W13-13 CAS preserved
  byte-identically; arch gate re-targeted on the facade boundary).
  **W16-3 pulled `2026-05-18` via `fa430f2`** (W14 production-scan
  carry-over; null-leakage half of report-finalize top-level field
  sync drift closed at the strict-forbid contract seam — 5
  additive-optional fields on `ActivationReport` + `build_report_data`
  populates them. Attribution-count-parity half split to
  `[FOLLOWUP attribution-count-parity]`). **W16-4 pulled `2026-05-18`
  via `304b99f`** (W15 mid-iter audit finding;
  `executor/flows/playwright/health/reconciliation.py` 682 LoC split
  into `security.py` (W13-1 HMAC primitives) + `handshake.py` (W13-12
  fail-closed dispatch) + slimmed `reconciliation.py` (event-attempt
  state machine + coverage reconciler); arch gates re-targeted per
  W14-6 extend-not-duplicate; W13-1 + W13-12 behavioral pins all
  green). **W16-5 documented `2026-05-18` (scope reduced, no code
  commit)** — `[FOLLOWUP simulation-progress-cancel]` umbrella's 3
  sub-items re-classified: `dedupe-step-progress-schemas` rejected
  (distinct pydantic surface roles); `heartbeat-sandbox-reset-off-thread`
  + `heartbeat-refactor` deferred to W17+ (lifecycle harness
  prerequisite). **W16-6 closed `2026-05-18` via `d40bb01`** (test
  hygiene splits + Alembic fresh-DB fixture: marketplace router 2374
  LoC → 5 endpoint-grouped files; import-graph 767 LoC → 4 thematic
  files; W13-4.5 skip removed via `fresh_alembic_engine` per-test
  throwaway Postgres DB; ruff clean). **W16-7 closed `2026-05-18`**
  via `8bf3c6b` (canonical preamble refresh across 7 docs + W16
  tracker freeze) + post-PR top-up `78f080e` (three
  `unaccounted_dropout` surface round-trip pins matching the live
  scan shape — security lane 217 → 220). **W16 merged into `main`
  via PR #23 `week16 -> main` on `2026-05-18` at merge commit
  `1b6d43f`.** Frozen tracker:
  [`active-work/W16-regression-and-audit-closeout.md`](active-work/W16-regression-and-audit-closeout.md).
- **W17 closed `2026-05-18` and merged via PR #25 (`bff565d`)** —
  Carry-Over Closeout + Lifecycle Harness Yatırımı + Hygiene Sweep
  window. Scope authored + executed `2026-05-18` in
  [`active-work/W17-carryover-and-lifecycle-harness.md`](active-work/W17-carryover-and-lifecycle-harness.md);
  plan source [`REFACTOR_OPTIMIZATION.md §15`](REFACTOR_OPTIMIZATION.md).
  W17-0..W17-6 sub-iter slate complete: W17-0 doc-reconcile
  (`4508c2e`); W17-1 attribution-count-parity closeout (`8c26d02`
  + `0a8f59e` self-stamp — `build_evidence_bundle` activation
  emit-site stamps `is_target_extension_event` byte-identical with
  `count_target_activations` predicate; 4 invariant tests including
  W17-1 parity contract pin); W17-2 lifecycle harness scaffold
  (`ff98235` + `44f96c5` self-stamp — `LifecycleHarness` +
  `lifecycle_harness` fixture at `tests/workflows/marketplace/test_lifecycle_harness.py`;
  W17-3 enabler with cancel-via-heartbeat smoke pinning thread
  identity and `reload_window=True` kwargs); W17-3 + W17-4
  scope-reduced doc-only (`c4c0646` — DESIGN-NEEDED for
  thread-relocation refactor shape because worker-thread step-1
  reset is a HARD SYNC POINT for W13-11 HMAC secret consume and
  the heartbeat thread starts only at step 4; multiple plausible
  refactor shapes have different invariant cost; deferred to W18
  dedicated sub-iter opening with ADR / §16 plan entry); W17-5
  hygiene single-item (`394d40d` `[CLEANUP postgres-version-fact-drift]`
  closeout at `seed_project_2.py` synthetic-fixture
  `postgres:15 → postgres:16-alpine` stack alignment + `0cbe1d0`
  self-stamp; other 4 cleanup candidates deferred to W18+
  opportunistic pull-as-found — they lack inline scope descriptions
  and need per-item owner discovery); W17-6 close-out hygiene this
  commit (canonical preamble refresh across 7 docs + §15 self-stamp
  + W17 tracker freeze). Final W17 bar: `tests/architecture/`
  **200 passed** (W16 final 199, +1 from W17-0 W16 close-out fact
  gate); `make test-security` **220 passed** (Makefile target list;
  W17-7a `bf983eb` enrolled `test_unaccounted_dropout_surface.py`
  in the hardcoded file list — 217 → 220 recovers the
  W16-7-followup audit-trail count); full suite **1899 passed,
  9 skipped, 4 deselected** (W16 final 1893, +6).
- **W18 closed `2026-05-21` and merged via PR #26 (`9874e79`)** —
  Heartbeat Refactor on the `week18` branch (per user direction
  2026-05-21; W11-W17 paterni preserved). §16 W18 plan source;
  frozen tracker:
  [`active-work/W18-heartbeat-refactor.md`](active-work/W18-heartbeat-refactor.md).
  W18-0..W18-4 sub-iter slate fully delivered: W18-0 doc-reconcile
  (`89d0c9b`) + W18-1 ADR
  `documents/adrs/0012-heartbeat-thread-relocation.md` Option A1
  Accepted (`acf6cc9` + `73d8a5c` followup doc-truth — dedicated
  sandbox-reset coordinator with cancel-path teardown reset staying
  on the heartbeat thread; invariant cost trade-offs against W13-1
  HMAC / W13-3 two-phase cancel / W13-13 CAS / W16-2 facade lock
  all preserved byte-identical) + W18-2 heartbeat refactor
  implementation (`a9bffb1` + `78ed7cc` ADR self-stamp + `b5b64b6`
  ruff-format followup + `306d744` full-repo lint sweep +
  `pre-commit install`) — step-1 reset moved off the worker thread
  via a dedicated `_run_reset_off_thread` coordinator (function-
  extension shape, ~42 LOC; W17-2 harness smoke passes byte-
  identical: thread identity `harness-monitoring-heartbeat` +
  `reload_window=True` kwargs + worker-entry CAS
  `WorkerEntryOutcome.CLAIMED`) + W18-3 lifecycle harness extension
  tests (`92b310d` + `32d9905` self-stamp) — parallel reset / reset
  idempotency / reset-during-finalize tests landed per ADR 0012
  §Follow-On (W17-2 module docstring L27-35 forward contract) +
  W18-4 close-out hygiene (`3f4f95a`) — 8-doc canonical preamble
  refresh + §16 W18 self-stamp + W18 tracker freeze. **W18-4-followup
  (`e1043e5`)** — 4 W18-2 invariant pins (signature default /
  poll-interval bound / cancel-propagation behavior / reporter
  thread-isolation) at
  `tests/workflows/marketplace/test_coordinator_invariants.py` + 2
  pre-existing doc drift fixes. Final W18 bar:
  `tests/architecture/` **201 passed** (W17 final 200 + W18-0 README
  phase-pointer arch gate W17->W18 transition); `make test-security`
  **220 passed** (unchanged from W17); full suite **1907 passed,
  9 skipped, 8 deselected** (W17 final 1899 + W18-0 +1 + W18-3 +3 +
  W18-4-followup +4 W18-2 invariant tests). W18 closed the W17-3/W17-4
  `DESIGN-NEEDED` heartbeat thread relocation deferral via ADR 0012
  Option A1. **W18 merged into `main` via PR #26 `week18 -> main`
  on `2026-05-21` at merge commit `9874e79`.** Frozen tracker:
  [`active-work/W18-heartbeat-refactor.md`](active-work/W18-heartbeat-refactor.md).
- **W19-W22 multi-iter roadmap planning state** (authored
  `2026-05-21`; W18 entered 2026-05-21). Driving signal: Codex
  live-run validation of `ms-python.python` @ `992ad028f3df`
  reports `automation_health.status=degraded` + `run_quality=low`
  while static W17 final bar (1899/200/220) remains 🟢. Plan
  identifies three independent problem hatları (executor
  muhasebe bug → `unaccounted_dropout`; harness verification gap
  → declared ≠ verified; coverage matrix promotion → 6
  capabilities missing in official track) and three capability
  layers (A: 29-entry activation event registry, B: 18-bucket
  taxonomy, C: VSCode manifest capabilities — spec-compliant).
  Five-iter slate: **W18** heartbeat refactor (closed 2026-05-21
  via PR #26 / `9874e79`); **W19** live-run kök neden — dropout
  fix + harness verification
  contract event-level; **W20** coverage promotion round 1
  (easy: `scm` + `settings` official promotion + spec
  crosswalk); **W21** coverage promotion round 2 (mid:
  `testing`, `comments`, `workspace_trust`; container hardening
  stretch); **W22** coverage promotion round 3 (hard: `chat`
  policy ADR + implementation) + attribution depth + sandbox-
  evasion ADR draft. Roadmap source-of-truth:
  [`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md).
  §16-§20 plan at
  [`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md);
  reserved stable IDs at `POST_POC_BACKLOG.md` "W18-W22
  Roadmap Acceptance Bar". Plan went through 3 review rounds
  (Codex live-run + GPT × 2).

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
  `heartbeat-refactor`) — **W16-5 documented `2026-05-18` (scope
  reduced; no code commit)**: `dedupe-step-progress-schemas`
  **rejected** (distinct surface roles between strict storage variant
  and lenient public/UI variant; aliasing would couple them);
  `heartbeat-sandbox-reset-off-thread` + `heartbeat-refactor`
  **deferred to W17+** (lifecycle harness prerequisite).
- `[BUG scenario-dropout-upstream-root-cause]` — **closed** by W14-1 on
  `2026-05-13` via `0c8bd02` (deterministic repro matrix landed + conservation
  guard; severity downgraded BLOCKER -> HIGH same day; upstream emit-site
  split **pulled to W16-1** under `[FOLLOWUP scenario-accountant-conservation-split]`).
- `[FOLLOWUP analysis-job-worker-entry-crud-ownership]` — W15 mid-iter audit
  finding, **closed at W16-2** via `9d6d110` (row-lock-aware lifecycle CRUD
  primitive `claim_queued_analysis_job_at_worker_entry` extracted; W13-13
  CAS preserved; AGENTS.md:57 compliance restored).
- `[FOLLOWUP health-reconciliation-responsibility-split]` — W15 mid-iter
  audit finding, **closed at W16-4** via `304b99f` (responsibility-aligned
  three-way split: security.py + handshake.py + slimmed reconciliation.py;
  W13-1 HMAC + W13-12 fail-closed gates preserved). Pre-W16-4 description
  (behavior-preserving extraction with
  W13-1 HMAC gates preserved).
- `[FOLLOWUP report-finalize-top-level-field-sync-drift]` — W14 production
  scan-driven investigation, **null-leakage half closed at W16-3** via
  `fa430f2` (contract-seam additive fields + build_report_data populates;
  attribution-count-parity half split to a new follow-up). Pre-W16-3
  description (finalize ordering /
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
regression; **on the `week16` branch per user direction 2026-05-18,
W11-W15 paterni restored via W16-0 doc reconcile**) in
`active-work/W16-regression-and-audit-closeout.md`.
