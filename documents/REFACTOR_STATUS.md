# Refactor Status

`Last Updated: 2026-05-28 — W22 closed synthetically on week22 and merged to main via PR #31 week22 -> main 1399f82. W21 closed and merged via PR #30 week21 -> main 2026-05-28 via 5dc18aa. Prior close-outs: W20 PR #29 week20 -> main 64a3c3d · W19 PR #28 week19 -> main c879603 · W18 PR #26 week18 -> main 9874e79 · W17 PR #25 week17 -> main bff565d · W16 PR #23 week16 -> main 1b6d43f · W15 PR #22 week15 -> main 6161472 · W14 PR #21 week14 -> main 4e03c8d · W13 PR #20 week13 -> main 772deb3. Active tracker: documents/active-work/W22-coverage-promotion-hard-tier.md.`

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
- **W19 closed synthetically `2026-05-26` on the `week19` branch
  and merged to main via PR #28 (`c879603`) on `2026-05-26`** (per
  user direction; W11-W18 paterni preserved). §17 W19 plan source in
  [`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md). Frozen
  tracker:
  [`active-work/W19-live-run-root-cause.md`](active-work/W19-live-run-root-cause.md).
  **W19-0..W19-6 + W19-X all closed**. **W19-0 closed `2026-05-21`**
  via doc reconcile (`72712bd` + `086d7a5`). **W19-1 closed
  `2026-05-25`** via RED dropout regression fixture (`6a21cf3` +
  `fd02ca4`). **W19-2 closed `2026-05-25`** via emit-site fix
  (`89b64da` + `d9c6262`) plus live re-anchor `d5de9ca`; live JSON
  `c2bf28ca9506` shows `unaccounted_dropout` count = 0. **W19-3
  closed `2026-05-25`** via schema landing (`d2e83e7` + `39121e4` +
  `9b56e94`). **W19-4 closed `2026-05-26`** via `onDebug*` nonce
  producer/consumer wire (`7d44b0e`). **W19-X closed `2026-05-26`**
  via `onDebug*` live close-out (`8b7b7f6` + `a3e634f`) closing
  Bug A/B/C. **W19-5 closed `2026-05-26`** via onTerminal+onLM
  log_record stamp (`e537ebd` + `4fd6ed6`). **W19-6 closed
  `2026-05-26`** via close-out hygiene (`f17b4b1` + `cd82153` +
  W19-6-followup-2 `800c69f`). Driving signal: Codex live-run
  validation `2026-05-21` of `ms-python.python` @ `992ad028f3df`
  reported `automation_health.status=degraded` + `run_quality=low`
  while W19-2 live re-anchor satisfies `unaccounted_dropout == 0`.
  **Hat-1 + Hat-2 fully closed; Hat-3** coverage matrix promotion
  deferred to W20-W22. W19 acceptance (live-run-driven):
  `unaccounted_dropout == 0` (must-pass) ✓;
  `harness_verification_unconfirmed_present` reason drops
  (must-pass) ✓ synthetic / live-pending-next-run;
  `run_quality: low → medium` (expected); `verification_gap_present`
  drops (stretch); `automation_health.status: degraded` OK (W20
  closes `official_unresolved_present`). Final W19 bar:
  `tests/architecture/` **204 passed**; `make test-security` **220
  passed**; full suite **1995 passed, 9 skipped, 8 deselected**.
- **W20 closed synthetically `2026-05-27` on the `week20` branch**
  (per user direction `2026-05-26`; W11-W19 paterni preserved) and
  merged via PR #29 `week20 -> main` on `2026-05-26` via `64a3c3d`.
  §18 W20 plan source in
  [`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md). Frozen
  tracker:
  [`active-work/W20-coverage-promotion-easy-wins.md`](active-work/W20-coverage-promotion-easy-wins.md).
  **W20-0..W20-5 all closed**. W20-0 doc-reconcile (`66a8a0b` +
  `5f13757`) — `week20` branch + new W20 active-work tracker +
  §18 W20 plan header doc-open (split from combined §18-§20) +
  W20 Pull-Forward Acceptance Bar promotion in
  `POST_POC_BACKLOG.md` + 9-doc canonical preamble refresh +
  README phase-pointer arch gate transition W19→W20 + new W19
  close-out fact gate + baseline live-run capture (anchor
  `e89a82ca9ba8`, sha256 `4dd78826...0256ffe`; W19 close-out
  Hat-1 `unaccounted_dropout == 0` + Hat-2
  `harness_verification_unconfirmed_present` DROPPED both
  live-verified). W20-1
  `[GOAL taxonomy-scm-official-promotion]` (`82276cb` + `a17e595`) —
  `_OFFICIAL_CAPABILITY_SUPPORT["scm"]: "missing" → "covered"` at
  [`capabilities.py:88`](../packages/analysis_planner/capabilities.py)
  + 4 invariant tests + frozen trigger fixture regenerated via
  planner replay. W20-2
  `[GOAL taxonomy-settings-official-promotion]` (`a4343d2` +
  `7406588`) — W20-1 paterni byte-identical at
  [`capabilities.py:90`](../packages/analysis_planner/capabilities.py).
  W20-3 `[GOAL coverage-matrix-contract-tests]` (`d4c03b6` +
  `2e39230`) — 5 contract invariant tests (keyset parity
  official ↔ heuristic ↔ taxonomy + Official ⊆ Heuristic
  subset + `_GLOBAL_CAPABILITY_NOTES` ↔ taxonomy alignment +
  `CAPABILITY_TAXONOMY` ordering pin + W20-1/W20-2 combined
  post-condition). W20-4
  `[DESIGN taxonomy-comments-testing-readiness]` (`05f47f3` +
  `b409894`) — doc-only readiness şablonu at
  [`documents/architecture/comments-testing-readiness.md`](architecture/comments-testing-readiness.md)
  (W21-1 `testing` + W21-2 `comments` unblocker template). W20-5
  close-out hygiene (`4665d32` primary + `95b0010` self-stamp +
  `d163b02` followup-2 filed
  `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` for W21 +
  `ae5b7de` followup-3 10-doc preamble `26bb080` placeholder
  backfill) — 9-doc canonical preamble Active → Previous flip +
  §18 W20 self-stamp + W20 tracker freeze + 3 new arch invariant
  tests (GAP-A `tests/architecture/test_w20_section_18_cross_doc_parity.py`
  cross-doc parity 23 parametrized assertions; GAP-B
  `tests/platform/contracts/test_capability_support_invariants.py`
  extension pinning full 18-entry `_OFFICIAL_CAPABILITY_SUPPORT`
  dict shape; GAP-D `tests/architecture/test_w20_4_design_doc_presence.py`
  3 assertions on the W20-4 readiness doc) + W20-5 final live-run
  captured `2026-05-27` (anchor `4e92de149802`, sha256
  `3804a5b5...4394c`). **W20 acceptance LIVE-SATISFIED**:
  `coverage_summary.missing_capabilities` dropped from 6 → **4**
  (lost `scm` + `settings`); W19 Hat-1 + Hat-2 both hold post-W20;
  `automation_health.status: degraded` remains expected
  (`official_unresolved_present` closes W22-end). Hat-3 mid +
  hard tiers deferred to W21-W22 per multi-iter roadmap. Final
  W20 bar: `tests/architecture/` **240 passed**, 4 deselected
  (W19 final 204 + 36 W20 additions); `make test-security`
  **220 passed** (unchanged); full suite **2045 passed, 9 skipped,
  8 deselected** (W19 baseline 1995 + W20-0..W20-5 +50).
- **W18-W22 multi-iter roadmap state** (authored
  `2026-05-21`; W18-W22 all closed and merged to main).
  Plan identifies three independent
  problem hatları (executor muhasebe bug →
  `unaccounted_dropout`; harness verification gap → declared ≠
  verified; coverage matrix promotion → 6 capabilities missing
  in official track) and three capability layers (A: 29-entry
  activation event registry, B: 18-bucket taxonomy, C: VSCode
  manifest capabilities — spec-compliant). Five-iter slate:
  **W18** heartbeat refactor (closed 2026-05-21 via PR #26
  / `9874e79`); **W19** live-run kök neden (closed synthetically
  2026-05-26 via PR #28 / `c879603`); **W20** coverage promotion
  round 1 (easy: `scm` + `settings` official promotion + spec
  crosswalk forward-ref — closed synthetically `2026-05-27` and
  merged via PR #29 / `64a3c3d`); **W21** coverage promotion
  round 2 (mid: `testing`, `comments`, `workspace_trust` +
  container hardening baseline — closed synthetically `2026-05-28`,
  merged via PR #30 / `5dc18aa`); **W22** coverage promotion
  round 3 (hard: `chat` policy ADR + implementation) +
  attribution depth + sandbox-evasion ADR draft — closed
  synthetically `2026-05-28` and merged via PR #31 / `1399f82`. Roadmap
  source-of-truth:
  [`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md).
  §17 W19 plan + §18 W20 plan + §19-§20 W21-W22 plan at
  [`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md);
  reserved stable IDs at `POST_POC_BACKLOG.md` "W19 Pull-Forward
  Acceptance Bar" (W19 closed) + "W20 Pull-Forward Acceptance
  Bar" (W20 closed) + "W21 Pull-Forward Acceptance Bar" (W21
  closed) + "W22 Roadmap Acceptance Bar" (W22 closed). Plan went
  through 3 review rounds (Codex live-run
  + GPT × 2).

## Post-W22 Feature Streams

These landed on `main` **after** the W22 weekly close-out. They are named
feature streams, **not** weekly (`W<N>`) phases, so they do not advance the
`documents/phase.json` weekly pointer (which stays W22 / PR #31 / `1399f82`) —
the same convention the static stream followed.

- **Static Analysis Pre-Check stream (ES-0..ES-5)** — the ADR 0016
  pre-execution static gate: the hardened `automation_static_analyzer`
  container, in-house static rules + the Semgrep runner, and the block-and-warn
  decision that fronts the dynamic sandbox. **Closed (ES-0..ES-5 DONE) and
  merged via PR #33 (`70e4364`).** Lane:
  [`agent-lanes/static-analysis-pre-check.md`](agent-lanes/static-analysis-pre-check.md);
  stream tracker:
  [`active-work/static-analysis-pre-check-stream.md`](active-work/static-analysis-pre-check-stream.md).
- **`extension-trigger-matrix` stream — merged to main `2026-06-03`.** Three
  workstreams (frozen tracker:
  [`active-work/extension-trigger-matrix.md`](active-work/extension-trigger-matrix.md)):
  1. **Reports Rule matrix tab** — a static + dynamic rule-activation grid
     (fired / silent / error / not-run) with click-for-detail; one additive
     backend touch (`ReportBundle.static_report` folds the sibling static
     report onto the `/bundle` response). UI-led.
  2. **Activation Coverage Promotion (executor + planner)** — the harness now
     exercises ambient-only extensions (`onStartupFinished` / `*`) by
     synthesizing `onCommand` attempts from `contributes.commands`, run safely
     via reload-deferral + inter-command maintenance (terminal-kill +
     renderer-liveness) + a finalize-in-`finally` so activation is parsed even
     on interrupt. Live-validated against an `ms-python.python` scan
     (22 extensions activated, 24/24 `onCommand` verified,
     `command_palette_unavailable` 60 → 0).
  3. **Static Rule Expansion + Blacklist** — in-house static rules 6 → 10
     (`s4`–`s7`), Semgrep JS rules 4 → 8, a dynamic `a7` blacklisted-domain
     rule, and an operator-editable DB-backed `blacklist_domains` denylist
     (seed ∪ operator; Alembic `b3d9f1c2e7a4`). `s4` is HIGH but WARNs (not a
     promoted blocker — gate unchanged).
  Lanes reconciled at this close-out:
  [`ui.md`](agent-lanes/ui.md),
  [`executor-runtime.md`](agent-lanes/executor-runtime.md),
  [`static-analysis-pre-check.md`](agent-lanes/static-analysis-pre-check.md).
  Close-out test bar (`2026-06-03`): full suite **2457 passed, 9 skipped,
  13 deselected** (post-W22 baseline 2450 + **7 merge-gating tests** added at
  close-out: blacklist-CRUD rollback ×2, seed-file `OSError` fallback,
  `prime_blacklist_override` swallow + happy-path, the `b3d9f1c2e7a4`
  migration round-trip, and `close_all_terminals`);
  `tests/architecture/` **318 passed**.
- **`security-development` stream — in progress on branch
  `security-development` (2026-06-04).** GlassWorm / `icon-theme-materiall`
  defensive rule expansion: in-house static production rules 14 → 17 with
  `extrace.s12.invisible_unicode_run`, `extrace.s13.native_node_loader`, and
  `extrace.s14.globalstate_dormancy`; direct-IP GlassWorm C2/stager hosts added
  to the shared `blacklist_domains` seed while shared Google Calendar/Gmail
  fallback hosts are intentionally excluded to avoid broad false positives.
  Design doc:
  [`detection-design/glassworm-detection-spec.md`](detection-design/glassworm-detection-spec.md).

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
keep closed W15 mechanics in
`active-work/W15-codex-uclass-bounds-posture.md`, keep closed W16
mechanics in `active-work/W16-regression-and-audit-closeout.md`,
keep closed W17 mechanics in
`active-work/W17-carryover-and-lifecycle-harness.md`, keep closed
W18 mechanics in `active-work/W18-heartbeat-refactor.md`, keep
closed W19 mechanics in
`active-work/W19-live-run-root-cause.md` (frozen at
W19-6-followup-2), and keep **closed W20 mechanics**
(coverage promotion round 1 easy wins; `scm` + `settings` official
promotion; W20-0..W20-5 sub-iter slate; merged via PR #29
`week20 -> main` / `64a3c3d`) in
`active-work/W20-coverage-promotion-easy-wins.md`, and keep **closed
W21 mechanics** in
`active-work/W21-coverage-promotion-mid-tier.md`. Multi-iter W18-W22
roadmap source-of-truth at `active-work/W18-W22-roadmap.md`
(W18-W22 closed and merged).
