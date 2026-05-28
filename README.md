# ExTrace

`Last Updated: 2026-05-28 (W22-0 doc-reconcile in-flight (this commit) opens week22 branch (per user direction 2026-05-28; W11-W21 paterninden bu sefer ayrılma — tek branch week22, sub-iter başına ayrı branch yok); main onayı zorunlu (memory feedback_pr_push_approval standing); paralel statik analiz şeridi ayrı worktree'de extrace-static branch — bu W22 oturumu ile çakışma yok. W21 closed and merged via PR #30 week21 -> main MERGED 2026-05-28 via 5dc18aa (W21-N close-out at dd24f1e); final W21 bar tests/architecture/ 287 passed / make test-security 220 passed / full suite 2104 passed, 9 skipped, 8 deselected. W22 active tracker documents/active-work/W22-coverage-promotion-hard-tier.md per W18-W21 paterni. Earlier-phase audit-trail: W21 final close-out W21-N at dd24f1e (W21 phase fully delivered 2026-05-28) — W21-4 [GOAL container-hardening-baseline] closed via primary 16e2224 + followup-1 2f9cba2 + self-stamp 8c42445 (W21-0 doc-reconcile closed 8434323 + 19bd9c7 + W21-3 closed c744c15 + 4b0a1ed + W21-1 closed 7e87030 + 38b8fd8 + W21-2 [GOAL taxonomy-comments-coverage] closed 8948ea6 + 3088709 before W21-4). W21-4 primary landed docker-compose.yml cap_drop:[ALL] + security_opt:[no-new-privileges:true] on executor/api/ui + ADR 0013 documenting decision + deferred items (read_only + tmpfs + custom seccomp profile → W22 ratchet-down lane) + 12 invariant tests at tests/architecture/test_compose_isolation_invariants.py. W21-4-followup-1 (2f9cba2) restored cap_add SETUID + SETGID on api (gosu user drop) + SETUID + SETGID + CHOWN + DAC_OVERRIDE on ui (nginx cache chown + worker drop) — both surfaced during the primary live-run smoke. executor cap_add NET_RAW + SYS_PTRACE preserved from pre-W21-4 for tcpdump/tshark/strace observability tools. W21-4 live-run anchor activation_report_ms-python.python-2026.5.2026052501-eacea0b6690e.json sha256 5d7c8b974f21e3bf4ad679a41551dd3e7b71d37573f5e7f2b28b87d2ad4a6a84 confirms NO coverage regression vs W21-2 anchor 1ddb3702c0ca (must-pass ✓): coverage_summary.missing_capabilities = [chat] (1 item, byte-identical with W21-2); covered/partial/missing = 8/9/1 (byte-identical); automation_health.status=degraded with 3 reasons (skipped_scenarios_present, verification_gap_present, official_unresolved_present — same shape as W21-2); W20 invariants HOLD post-W21-4 (Hat-1 unaccounted_dropout_count=null; Hat-2 harness_verification_unconfirmed_present DROPPED). Manual kernel-level smoke (docker exec into the executor + grep /proc/self/status for NoNewPrivs) returns NoNewPrivs=1 confirming PR_SET_NO_NEW_PRIVS active at the kernel. W21-2 [GOAL taxonomy-comments-coverage] closed via 8948ea6 + 3088709 before W21-4 hit comments official-track promotion missing → covered + harness CommentController + scenario + 4 invariants + fixture regen, dropping missing_capabilities 2 → 1 [chat]. W21-2 primary landed _OFFICIAL_CAPABILITY_SUPPORT["comments"]: "missing" → "covered" at capabilities.py:96 + mirror in _GLOBAL_CAPABILITY_SUPPORT:44 (heuristic derives) + harness CommentController baseline marker emitted at activate() entry + ensureCommentThread (stimulus_dispatch.js) extended to emit thread_created + thread_disposed markers via emitHarnessEvent through reserved OutputChannel route (W19-X Bug B paterni) with ephemeral thread default (W19-X HMAC reactivation race lesson — created+disposed in-call) + local_comments_controller scenario in scenarios.py advertising comments (mirror W21-3 workspace_trust_transition + W21-1 local_test_controller shape) + 4 invariant tests at tests/platform/contracts/test_capability_support_invariants.py + dict shape canonical pin update + test_split_did_not_lose_data_volume count bump 15→16 + frozen trigger fixture regen for ms-python.python. Runtime stimulus pass implicit — ensureCommentThread already invoked from the existing extrace.harness.runCurrentStimulus command handler, so any stimulus pass exercises the new markers without dedicated pass. Opens week21 branch (per user direction 2026-05-27; W11-W20 paterni preserved — sub-iter commits land on week21, close-out merges via week21 -> main PR PENDING USER APPROVAL). W21 frozen tracker documents/active-work/W21-coverage-promotion-mid-tier.md. §19 W21 plan header doc-open in REFACTOR_OPTIMIZATION.md split at W21-0 from §19-§20 W21-W22 planning combined header (W19-0 / W20-0 paterni mirror). W21 Pull-Forward Acceptance Bar promoted in POST_POC_BACKLOG.md at W21-0 (now W22 Roadmap Acceptance Bar planning for the residual W22 lane). 10-doc canonical preamble refresh at W21-0 + W21-3 + W21-1 + W21-2 self-stamps (this commit). README phase-pointer arch gate transition W20→W21 at W21-0 (test_readme_phase_pointer.py tracks_active_w21_status + W20 close-out merge gate test pinning PR #29 / week20 -> main / 64a3c3d). W21-0 baseline anchor 600d9ecba5eb sha256 1db1480551fd...c4477; W21-3 anchor 6fd7b959bd5a sha256 fa83017a...d6f7477 confirmed workspace_trust dropped (4→3); W21-1 anchor 0b4998ce31b4 sha256 b7192bc2ff9c...968be4 confirmed testing dropped (3→2). W21-2 live-run anchor activation_report_ms-python.python-2026.5.2026052501-1ddb3702c0ca.json sha256 2dabd15be329bbf1685fe7fc31469355bdc4a5acac2a364d43a196437339cbff confirms W21-2 acceptance — coverage_summary.missing_capabilities 2 → 1 items [chat] (comments dropped — must-pass ✓; W21 mid-tier closure target hit — only chat remains for W22 hard tier), covered/partial/missing 8/8/2 → 8/9/1, comments matrix entry status "partial" support_status "covered" supported_scenarios ["local_comments_controller"]. W20 invariants HOLD post-W21-2 (Hat-1 dropout=null; Hat-2 harness_verification_unconfirmed_present DROPPED). W21-2 live-run drift clean (same shape as W21-1): only 3 reasons remain (skipped_scenarios_present, verification_gap_present, official_unresolved_present). W20 closed and merged via PR #29 week20 -> main MERGED 2026-05-26 via 64a3c3d; final W20 bar tests/architecture/ 240 passed / make test-security 220 passed / full suite 2045 passed, 9 skipped, 8 deselected. W21-3 test bar delta: contracts/test_capability_support_invariants.py 14 → 18 (+4); full suite 2045 → 2050 (+5 net). W21-1 test bar delta: contracts/test_capability_support_invariants.py 18 → 22 (+4); full suite 2050 → 2054 (+4 net). W21-2 test bar delta: tests/architecture/ 241 passed (unchanged from W21-1), tests/platform/contracts/test_capability_support_invariants.py 22 → 26 passed (+4 W21-2 invariants), tests/platform/contracts/test_registry_split_regression.py 8 passed (count pin 15 → 16), tests/workflows/marketplace/test_analysis_planner.py fixture parity green, make test-security 220 passed (unchanged), full suite 2054 → 2058 passed, 9 skipped, 8 deselected (+4 net W21-2 invariants). W21 driving signal (carried over from W19 / W20): same Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities started at [scm, settings, chat, comments, testing, workspace_trust]; W20-5 confirmed missing dropped 6 → 4 [chat, comments, testing, workspace_trust]; W21-3 dropped workspace_trust (4 → 3 [chat, comments, testing]); W21-1 dropped testing (3 → 2 [chat, comments]); W21-2 dropped comments (2 → 1 [chat]); W22 closes hard tier (chat) + sandbox evasion ADR draft. §19 W21 plan source (active) + §20 W22 planning. W21 sub-iter slate: W21-0 doc-reconcile closed (8434323 + 19bd9c7) + W21-3 [GOAL taxonomy-workspace-trust-coverage] closed (c744c15 + 4b0a1ed) + W21-1 [GOAL taxonomy-testing-coverage] closed (7e87030 + 38b8fd8) + W21-2 [GOAL taxonomy-comments-coverage] closed (8948ea6 + 3088709) + W21-4 [GOAL container-hardening-baseline] closed (16e2224 + 2f9cba2 + 8c42445; user-pulled into W21 2026-05-28 per AskUserQuestion after W21-1+W21-2 closed cleanly; baseline only — read_only + tmpfs + custom seccomp profile deferred to W22 ratchet-down per ADR 0013 §Deferred) + W21-N close-out hygiene + PR #30 week21 -> main MERGED 2026-05-28 via 5dc18aa. [FOLLOWUP sandbox-reset-stale-state-multi-analyze] (filed d163b02 at W20-5-followup-2) opportunistic at W21-N close-out window (user-confirmed); not a sub-iter, not a blocker. [FOLLOWUP workspace-trust-stimulus-pass] (filed c744c15 + 4b0a1ed) W22 candidate — runtime untrusted → granted transition exercise; needs fixture restructuring. W19 closed and merged via PR #28 week19 -> main MERGED 2026-05-26 via c879603; W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f; W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 closed via PR #20 week13 -> main MERGED 2026-05-13 via 772deb3. W20 frozen tracker: documents/active-work/W20-coverage-promotion-easy-wins.md (frozen at W20-5 + followups per W17/W18/W19 paterni); W19 frozen tracker: documents/active-work/W19-live-run-root-cause.md (frozen at W19-6-followup-2); W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md; W21 frozen tracker: documents/active-work/W21-coverage-promotion-mid-tier.md (frozen at W21-N close-out dd24f1e per W17/W18/W19/W20 paterni); W22 active tracker: documents/active-work/W22-coverage-promotion-hard-tier.md; multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md.)`

ExTrace is a VS Code extension analysis platform built around three runtime
surfaces:

- A FastAPI API for catalog ingestion, activation report access, marketplace
  download, and sandbox analysis.
- A Dockerized executor that runs full VS Code GUI sessions under Xvfb and
  drives them with Playwright.
- A Vite + React + Tailwind analyst console that consumes the API and
  visualizes activation reports and live simulation jobs.

## Operating Model

ExTrace is intentionally designed as a single-user sandbox appliance, not a
multi-tenant web platform.

- Backend, UI, PostgreSQL, and executor are expected to run on the same machine
  or inside the same Docker host.
- The primary deployment shape is a local or lab sandbox where one analyst
  inspects one extension at a time.
- Background analysis is intentionally limited to one active job at a time.
- Activation reports remain file-backed operator artifacts under `output/`,
  while async analysis job metadata is persisted in PostgreSQL.
- If the API process restarts during an active analysis, that job is marked
  failed and should be rerun.
- ADR 0007 local-network-binding is Accepted **and implemented (W8-7,
  `2026-04-29`)** — `appcore/api/config.py` defaults bind `127.0.0.1`,
  CORS allow-list replaces the wildcard, every `docker-compose.yml`
  `ports:` entry carries an explicit `127.0.0.1:` prefix, and host-side
  CDP exposure is gated behind the Compose `debug` profile. To expose
  services on the LAN, follow `documents/runbooks/lan-exposure.md` and set
  `EXTRACE_ALLOW_LAN=1` (host-mode `make dev-lan`) or edit the compose
  file directly.

## Current Phase

- W4 stabilization, W5 detection foundations, W6 automation hardening, and
  W7 PoC acceptance are all closed (last closure `2026-04-23`).
- Post-W7 hardening (`2026-04-24`) landed reliability + modularization
  follow-ups (fatal UI-crash fail-fast, scan-between VS Code restart,
  `attribution/` subpackage split, `sim-target` Makefile lane).
- Post-W7 simulation UX + reliability (`2026-04-25`) landed weighted
  simulation progress, full-stack analysis cancel flow, the VNC harness
  ready-marker fix, and the `t1-demo-runnable-canary` fixture + rule +
  `make demo-canary` lanes.
- PR345 target activation lifecycle is complete as of `2026-04-27`; PRs 1-5
  plus ADR 0006 target output-channel capture landed on
  `feat/pr345-completion`.
- W8-0 deterministic harness readiness gate landed on `2026-04-27`, unblocking
  W8-1 and W8-3.
- **W8 closed for active work `2026-04-29`** (W8-1..W8-7 + W8-9 landed,
  W8-8 deferred); **W9 closed `2026-05-04`** (PR #9); **W10 closed
  `2026-05-04`** (PR #11); **W11 closed `2026-05-05`** and merged via
  PR #14; **W12 closed `2026-05-10`** and merged via PR #18 (`33a0852`).
  **W13 — Test Expansion + Observability closed `2026-05-13`** and
  merged via PR #20 `week13 -> main` (`772deb3`). Frozen tracker:
  [`active-work/W13-test-expansion-observability.md`](documents/active-work/W13-test-expansion-observability.md).
  **W14 — Codex M-class Acceptance + Observability closed `2026-05-14`**
  and merged via PR #21 `week14 -> main` (`4e03c8d`). Frozen tracker:
  [`active-work/W14-codex-acceptance-observability.md`](documents/active-work/W14-codex-acceptance-observability.md).
  **W15 — Codex U-class Close-Out + UI Bounds + Posture closed
  `2026-05-17` and merged via PR #22 `week15 -> main` (`6161472`) on `2026-05-18`**
  — W15-1..W15-7 sub-iter slate + W15-1 post-slate typing hotfix +
  close-out hygiene pass (doc preamble truth-state refresh across 7
  canonical docs + ADR 0011 catalog endpoint posture gate + compose
  image SHA pin + GH action trivy version pin + close-out lint
  hygiene). Frozen tracker:
  [`active-work/W15-codex-uclass-bounds-posture.md`](documents/active-work/W15-codex-uclass-bounds-posture.md).
  **W16 — Carry-Over Closeout + Audit Findings + Production Regression
  closed `2026-05-18`** and merged via PR #23 `week16 -> main`
  (`1b6d43f`). Frozen tracker:
  [`active-work/W16-regression-and-audit-closeout.md`](documents/active-work/W16-regression-and-audit-closeout.md).
  W16-0..W16-7 sub-iter slate complete: W16-1 scenario-accountant
  emit-site fix (`01f910a`); W16-2 analysis-job worker-entry CRUD
  ownership (`9d6d110`); W16-3 report-finalize null-leakage half
  (`fa430f2`; attribution-count-parity split to W17); W16-4
  health-reconciliation responsibility split (`304b99f`); W16-5
  simulation-progress-cancel scope reduction (1 rejected, 2 deferred
  to W17; `e21a05c`); W16-6 hygiene splits + Alembic fresh-DB fixture
  (`d40bb01`); W16-7 close-out hygiene (`8bf3c6b`) + post-PR
  `unaccounted_dropout` surface pin (`78f080e`). Final W16 bar:
  `tests/architecture/` **199 passed**; `make test-security`
  **220 passed**; full suite **1893 passed**.
  **Previous phase: W17 — Carry-Over Closeout + Lifecycle Harness
  Yatırımı + Hygiene Sweep — closed `2026-05-18`** on the `week17`
  branch (per user direction; W11-W16 paterni preserved);
  **W17 closed via PR #25 `week17 -> main` MERGED `2026-05-18`
  via `bff565d`**. Frozen tracker:
  [`active-work/W17-carryover-and-lifecycle-harness.md`](documents/active-work/W17-carryover-and-lifecycle-harness.md).
  W17-0..W17-7 sub-iter slate complete: W17-0 doc-reconcile
  (`4508c2e`); W17-1 attribution-count-parity (`8c26d02`); W17-2
  lifecycle harness scaffold (`ff98235`); W17-3 + W17-4
  scope-reduced doc-only (`c4c0646` — DESIGN-NEEDED for
  thread-relocation refactor shape, deferred to W18 — **closes via
  W18-1 ADR + W18-2 implementation**); W17-5 hygiene
  single-item (`394d40d` `[CLEANUP postgres-version-fact-drift]`;
  other 4 cleanup candidates deferred to W18+); W17-6 close-out
  hygiene (`21f7c68`); W17-7 post-slate hotfix batch
  (`bf983eb` + `fc88678` + `326dac8` + `51dba29`); W17-7-followup
  post-PR doc-truth alignment (`dab4679`). Final W17 bar:
  `tests/architecture/` **200 passed**; `make test-security`
  **220 passed**; full suite **1899 passed, 9 skipped,
  4 deselected**.
  **Previous phase: W18 — Heartbeat Refactor — closed via PR #26
  `week18 -> main` MERGED `2026-05-21` via `9874e79` (per user
  direction; W11-W17 paterni preserved). §16 W18 plan source**.
  W18-0..W18-4 sub-iter slate + W18-4-followup fully delivered:
  W18-0 doc-reconcile (`89d0c9b`); W18-1 ADR
  `documents/adrs/0012-heartbeat-thread-relocation.md` Option A1
  Accepted (`acf6cc9` + `73d8a5c` followup) — dedicated
  sandbox-reset coordinator for the step-1 setup reset; cancel-path
  teardown reset stays on the heartbeat thread; W18-2 heartbeat
  refactor implementation (`a9bffb1` + `78ed7cc` + `b5b64b6` +
  `306d744` with `pre-commit install`) — step-1 reset off the
  worker thread via `_run_reset_off_thread` coordinator
  (function-extension shape; W17-2 harness smoke byte-identical);
  W18-3 lifecycle harness extension tests — parallel reset /
  idempotency / reset-during-finalize (`92b310d` + `32d9905`);
  W18-4 close-out hygiene (`3f4f95a`); W18-4-followup (`e1043e5`).
  Final W18 bar: `tests/architecture/` **201 passed**;
  `make test-security` **220 passed**; full suite **1907 passed,
  9 skipped, 8 deselected**. Frozen tracker:
  [`active-work/W18-heartbeat-refactor.md`](documents/active-work/W18-heartbeat-refactor.md).

  **Previous phase: W19 — Live-Run Kök Neden: Dropout + Harness
  Verification — closed synthetically `2026-05-26` on the `week19`
  branch (per user direction 2026-05-21; W11-W18 paterni preserved);
  PR #28 `week19 -> main` MERGED `2026-05-26` via `c879603`. §17 W19
  plan source**. **W19-0..W19-6 + W19-X all closed**:
  W19-0 doc-reconcile (`72712bd` + `086d7a5`); W19-1
  `[BUG scenario-unaccounted-dropout-regression-fixture]`
  (`6a21cf3` + `fd02ca4`); W19-2
  `[BUG scenario-unaccounted-dropout-debug-refactor]` emit-site fix
  (`89b64da` + `d9c6262`) + W19-2-followup-2 live re-anchor
  (`d5de9ca`) satisfying `unaccounted_dropout == 0`; W19-3
  `[GOAL harness-verification-contract-event-level]` schema landing
  (`d2e83e7` + `39121e4` + `9b56e94`); W19-4
  `[FOLLOWUP harness-verification-debug-events]` `onDebug*` nonce
  producer/consumer wire (`7d44b0e`); W19-X `onDebug*` live close-out
  (`8b7b7f6` + `a3e634f`) closing Bug A/B/C; W19-5
  `[FOLLOWUP harness-verification-terminal-and-lm-tool]`
  onTerminal + onLM log_record stamp (`e537ebd` + `4fd6ed6`); W19-6
  close-out hygiene (`f17b4b1` + `cd82153`) + W19-6-followup-2
  pre-merge hygiene (`800c69f`). Driving signal: Codex live-run validation
  2026-05-21 of `ms-python.python` @ `992ad028f3df` reported
  `automation_health.status=degraded` + `run_quality=low` while
  W19-2 live re-anchor satisfies `unaccounted_dropout == 0`.
  Hat-1 + Hat-2 fully closed; Hat-3 (coverage matrix promotion)
  deferred to W20-W22. W19 acceptance (live-run-driven):
  `unaccounted_dropout == 0` (must-pass) ✓;
  `harness_verification_unconfirmed_present` reason drops
  (must-pass) ✓ synthetic / live-pending-next-run;
  `run_quality: low → medium` (expected); `verification_gap_present`
  drops (stretch); `automation_health.status: degraded` OK (W20
  closes `official_unresolved_present`). Frozen tracker:
  [`active-work/W19-live-run-root-cause.md`](documents/active-work/W19-live-run-root-cause.md);
  W20-W22 follow-on iters per multi-iter roadmap at
  [`active-work/W18-W22-roadmap.md`](documents/active-work/W18-W22-roadmap.md).
  Final W19 bar: `tests/architecture/` **204 passed**;
  `make test-security` **220 passed**; full suite **1995 passed,
  9 skipped, 8 deselected**.

  **W20 — Coverage Promotion Round 1: Easy Wins — closed
  synthetically `2026-05-27` on the `week20` branch (per user
  direction `2026-05-26`; W11-W19 paterni preserved); close-out PR
  #29 `week20 -> main` MERGED `2026-05-26 23:10:21Z` via
  `64a3c3d`. §18 W20 plan source**. Driving signal (same as W19): Codex live-run
  validation `2026-05-21` of `ms-python.python` @ `992ad028f3df`
  reports `coverage_summary.missing_capabilities = [scm, settings,
  chat, comments, testing, workspace_trust]` (Hat-3 coverage
  matrix promotion). W19 closed Hat-1 + Hat-2; W20 closed the
  easy tier of Hat-3. **W20-0..W20-5 sub-iter slate fully
  delivered**: W20-0 doc-reconcile (`66a8a0b` + `5f13757`) opens
  `week20` branch + new W20 active-work tracker + §18 W20 plan
  header doc-open (split from combined §18-§20) + W20 Pull-Forward
  Acceptance Bar promotion in `POST_POC_BACKLOG.md` + 9-doc
  canonical preamble refresh + README phase-pointer arch gate
  transition W19→W20 + new W19 close-out fact gate
  `test_readme_phase_pointer_mentions_w19_closeout_merge`
  pinning PR #28 / `week19 -> main` / `c879603` + baseline
  live-run captured (anchor `e89a82ca9ba8`, sha256
  `4dd78826...0256ffe`); W20-1
  `[GOAL taxonomy-scm-official-promotion]` (`82276cb` + `a17e595`) —
  `_OFFICIAL_CAPABILITY_SUPPORT["scm"]: "missing" → "covered"`
  at [`capabilities.py:88`](packages/analysis_planner/capabilities.py:88)
  + 4 invariant tests + fixture regen; W20-2
  `[GOAL taxonomy-settings-official-promotion]` (`a4343d2` +
  `7406588`) — W20-1 paterni byte-identical at
  [`capabilities.py:90`](packages/analysis_planner/capabilities.py:90);
  W20-3 `[GOAL coverage-matrix-contract-tests]` (`d4c03b6` +
  `2e39230`) — 5 invariant set (keyset parity + Official ⊆
  Heuristic + notes ↔ taxonomy + ordering + W20-1/W20-2
  combined post-condition); W20-4
  `[DESIGN taxonomy-comments-testing-readiness]` (`05f47f3` +
  `b409894`) — doc-only readiness şablonu at
  [`documents/architecture/comments-testing-readiness.md`](documents/architecture/comments-testing-readiness.md)
  (W21-1 + W21-2 unblocker template); W20-5 close-out hygiene
  (`4665d32` primary + `95b0010` self-stamp + `d163b02`
  followup-2 filed `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]`
  for W21 + `ae5b7de` followup-3 10-doc preamble `(this commit)`
  placeholder backfill) — 9-doc canonical preamble Active →
  Previous flip + §18 W20 self-stamp + W20 tracker freeze +
  3 new arch invariant tests (GAP-A
  `test_w20_section_18_cross_doc_parity.py` + GAP-B
  `_OFFICIAL_CAPABILITY_SUPPORT` full dict shape pin extension
  + GAP-D `test_w20_4_design_doc_presence.py`) + W20-5 final
  live-run captured `2026-05-27` (anchor `4e92de149802`, sha256
  `3804a5b5...4394c`). **W20 acceptance LIVE-SATISFIED**:
  `coverage_summary.missing_capabilities` dropped from 6 →
  **4** (lost `scm` + `settings`); W19 Hat-1
  (`unaccounted_dropout == 0`) + Hat-2
  (`harness_verification_unconfirmed_present` DROPPED) both
  hold post-W20. Final W20 bar:
  `tests/architecture/` **240 passed**, 4 deselected;
  `make test-security` **220 passed**; full suite **2045
  passed**, 9 skipped, 8 deselected. Frozen tracker:
  [`active-work/W20-coverage-promotion-easy-wins.md`](documents/active-work/W20-coverage-promotion-easy-wins.md);
  multi-iter roadmap source-of-truth:
  [`active-work/W18-W22-roadmap.md`](documents/active-work/W18-W22-roadmap.md).

  **Current phase: W21 — Coverage Promotion Round 2: Mid Tier —
  closed synthetically `2026-05-28` on the `week21` branch (per
  user direction `2026-05-27`; W11-W20 paterni preserved);
  close-out PR `week21 -> main` PENDING USER APPROVAL. §19 W21
  plan source**. **W21 closed the mid tier** (`testing` +
  `comments` + `workspace_trust` all promoted to `covered`).
  Sub-iter slate: **W21-0** (`8434323` + `19bd9c7`) doc-reconcile +
  10-doc preamble refresh + §19 split + baseline anchor
  `600d9ecba5eb`; **W21-3** `[GOAL taxonomy-workspace-trust-coverage]`
  (`c744c15` + `4b0a1ed`) — workspace_trust flip + harness trust
  observability + scenario + 4 invariants + fixture regen, anchor
  `6fd7b959bd5a`; **W21-1** `[GOAL taxonomy-testing-coverage]`
  (`7e87030` + `38b8fd8`) — testing flip + harness Test Controller
  markers + scenario + 4 invariants + fixture regen, anchor
  `0b4998ce31b4`; **W21-2** `[GOAL taxonomy-comments-coverage]`
  (`8948ea6` + `3088709`) — comments flip + harness Comment thread
  markers + scenario + 4 invariants + fixture regen, anchor
  `1ddb3702c0ca`; **W21-4** `[GOAL container-hardening-baseline]`
  (`16e2224` primary + `2f9cba2` followup-1 + `8c42445` self-stamp)
  — STRETCH user-pulled into W21. `docker-compose.yml` `cap_drop:
  [ALL]` on executor/api/ui + audited `cap_add` per service +
  `no-new-privileges:true` + new ADR
  [`documents/adrs/0013-container-isolation-baseline.md`](documents/adrs/0013-container-isolation-baseline.md)
  (`read_only` + tmpfs + custom seccomp deferred to W22 ratchet-
  down) + 12 invariant tests; anchor `eacea0b6690e` confirms NO
  coverage regression. **W21-N close-out hygiene** (`dd24f1e`) —
  10-doc canonical preamble Active → Previous flip + §19 self-stamp
  + W21 tracker freeze + 34 new arch invariant tests
  ([`test_w21_section_19_cross_doc_parity.py`](tests/architecture/test_w21_section_19_cross_doc_parity.py)
  — mirror W20-5 GAP-A cross-doc parity gate). **W21 acceptance
  LIVE-SATISFIED**: `coverage_summary.missing_capabilities` dropped
  from 4 → **1** (only `chat` for W22 hard tier); W19 Hat-1
  (`unaccounted_dropout_count = null`) + Hat-2
  (`harness_verification_unconfirmed_present` DROPPED) both hold
  post-W21. **Final W21 bar**: `tests/architecture/` **287 passed**
  (+46 net from W20-5 baseline 241); `make test-security` **220
  passed** (unchanged); full suite **2104 passed**, 9 skipped, 8
  deselected (+59 net from W20-5 baseline 2045). Frozen tracker:
  [`active-work/W21-coverage-promotion-mid-tier.md`](documents/active-work/W21-coverage-promotion-mid-tier.md);
  multi-iter roadmap source-of-truth:
  [`active-work/W18-W22-roadmap.md`](documents/active-work/W18-W22-roadmap.md).
- **Canonical source of truth for phase state:**
  [`documents/REFACTOR_STATUS.md`](documents/REFACTOR_STATUS.md).
  Deferred items: [`documents/POST_POC_BACKLOG.md`](documents/POST_POC_BACKLOG.md).
  W8-W13 plan: [`documents/REFACTOR_OPTIMIZATION.md` §11](documents/REFACTOR_OPTIMIZATION.md).
  W14 plan: [`documents/REFACTOR_OPTIMIZATION.md` §12](documents/REFACTOR_OPTIMIZATION.md).
  W15 plan: [`documents/REFACTOR_OPTIMIZATION.md` §13](documents/REFACTOR_OPTIMIZATION.md).
  W16 plan: [`documents/REFACTOR_OPTIMIZATION.md` §14](documents/REFACTOR_OPTIMIZATION.md).
  W17 plan: [`documents/REFACTOR_OPTIMIZATION.md` §15](documents/REFACTOR_OPTIMIZATION.md).
  W18 plan: [`documents/REFACTOR_OPTIMIZATION.md` §16](documents/REFACTOR_OPTIMIZATION.md).
  W19 plan: [`documents/REFACTOR_OPTIMIZATION.md` §17](documents/REFACTOR_OPTIMIZATION.md) (closed synthetically).
  W20 plan: [`documents/REFACTOR_OPTIMIZATION.md` §18](documents/REFACTOR_OPTIMIZATION.md) (closed synthetically; PR #29 `week20 -> main` MERGED `2026-05-26` via `64a3c3d`).
  W21 plan: [`documents/REFACTOR_OPTIMIZATION.md` §19](documents/REFACTOR_OPTIMIZATION.md) (closed synthetically; PR `week21 -> main` PENDING USER APPROVAL).
  W22 plan: [`documents/REFACTOR_OPTIMIZATION.md` §20](documents/REFACTOR_OPTIMIZATION.md) (planning).

## Current Architecture

The refactor introduced a canonical split between shared platform code and
workflow code:

- `appcore/`
  - Shared platform modules.
  - `api/`: settings and FastAPI dependencies.
  - `db/`: SQLAlchemy engine and session factory.
  - `storage/`: ORM models and CRUD helpers.
  - `contracts/`: shared Pydantic v2 schemas.
- `packages/`
  - Framework-agnostic contracts and analysis logic.
  - `analysis_contracts/`: backend-owned analysis contracts, activation
    reports, trigger payloads, and detection DTOs.
  - `analysis_planner/`: trigger planning logic.
  - `analysis_engine/`: reserved extraction surface for shared analysis logic.
- `workflows/`
  - Business workflows grouped by capability.
  - `extension_catalog/`: extension ingestion, parsing, and catalog endpoints.
  - `activation_reports/`: reads JSON activation reports from `output/`.
  - `marketplace/`: Marketplace search/download and sandbox analysis.
- `executor/`
  - Sandbox runtime.
  - `control.py`: workflow-visible sandbox boundary.
  - `container/`: Docker image, entrypoint (`start.sh`), and the shared
    `launch_vscode.sh` script used at boot and by scan-between resets.
  - `flows/playwright/`: Playwright automation helpers, package-mode
    `entrypoint/`, `monitor/` facade, attribution/scenario/runtime-capture
    packages, and focused helper packages for health, stimulus, workspace,
    VS Code UI, and signals.
- `ui/`
  - Primary analyst-facing React SPA built with Vite and Tailwind.
  - `src/app/`: shell and route composition.
  - `src/features/`: `evidence`, `marketplace`, `reports`, `rules`,
    `settings`, `simulation`, `system`.
  - `src/lib/`: API client, adapters, generated contract types, and shared
    frontend helpers.

The repository now uses canonical imports only:

- Shared platform modules live under `appcore/`
- Framework-agnostic analysis logic lives under `packages/`
- Workflow code lives under `workflows/`
- Workflow-visible executor control lives under `executor/control.py`

## Request Flows

### Static Catalog Ingestion

`POST /createExtension`

1. `workflows.extension_catalog.router`
2. `workflows.extension_catalog.service`
3. `workflows.extension_catalog.manifest_reader` +
   `workflows.extension_catalog.manifest_parser`
4. `appcore.contracts.schemas`
5. `appcore.storage.crud`
6. PostgreSQL

### Marketplace Download

`POST /api/marketplace/download`

1. `workflows.marketplace.client` downloads and extracts a `.vsix`
2. `workflows.extension_catalog.service.create_extension_from_directory`
3. `appcore.storage.crud` persists validated manifest data

### Sandbox Analysis

`POST /api/marketplace/analyze` or `POST /api/marketplace/analyze/start`

1. `workflows.marketplace.router`
2. `workflows.marketplace.analysis_service`
3. `workflows.marketplace.job_service`
4. `executor.control` boundary
5. `executor.host` Docker exec wrapper
6. `python -m executor.flows.playwright.entrypoint`
7. Reports written under `output/`
8. Async job metadata persisted in PostgreSQL `analysis_jobs`

Notes:

- `POST /api/marketplace/analyze` is the direct request/response path.
- `POST /api/marketplace/analyze/start` is the background path used by the
  React UI.
- Only one background analysis should run at a time in the intended sandbox
  deployment.
- Startup fails fast if the `analysis_jobs` storage path is unavailable or the
  required migration has not been applied.
- Trigger planning may choose layered execution or a scenario-zero
  `skip_automation` run for non-executable fixtures.

## API Surface

### Extension Catalog

- `GET /`
- `GET /health`
- `GET /searchExtension`
- `GET /getExtensionsBaseInfo`
- `GET /getExtensionsAllInfo`
- `POST /createExtension`
- `DELETE /deleteExtension`
- `GET /getExtensionScripts`
- `GET /getExtensionActivationEvents`
- `GET /getExtensionCapabilities`
- `GET /getExtensionContributesAll`
- `GET /getExtensionContributesCommands`

### Activation Reports

- `GET /api/activations`
- `GET /api/activations/latest`
- `GET /api/activations/{name}`

### Marketplace + Analysis

- `GET /api/marketplace/search`
- `POST /api/marketplace/download`
- `POST /api/marketplace/analyze`
- `POST /api/marketplace/analyze/start`
- `GET /api/marketplace/analyze/{job_id}`
- `POST /api/marketplace/analyze/{job_id}/cancel`

### Operator Settings

- `GET /api/settings/security/thresholds`
- `PUT /api/settings/security/thresholds`

## Local Development

### Prerequisites

- Python 3.11+
- Docker / Docker Compose
- PostgreSQL 16 compatible runtime
- Node 20+ for local UI development

### Common Commands

```bash
make install-dev
make up
make migrate
make dev
make test-local
make check-all
make test-security
make ui-types-check
make ui-boundaries
make exec-up
make exec-run
make ui-up
make sim-target TARGET=publisher.name      # target-extension smoke
make sim-all                                # UI-stimulus stress (no target ext.)
make demo-canary                            # end-to-end demo runnable canary
make demo-canary-offline                    # offline fixture validation
cd ui && npm run dev
cd ui && npm run test
.venv/bin/pytest
.venv/bin/pytest -m "not smoke and not requires_db"
.venv/bin/pytest -m "requires_db"
.venv/bin/pytest -m smoke
```

### Service Endpoints

ADR 0007 — every endpoint below binds loopback only by default. Replace
`127.0.0.1` with the operator-host LAN IP only after the
`documents/runbooks/lan-exposure.md` checklist is applied.

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Web UI: `http://127.0.0.1:3000`
- noVNC executor view: `http://127.0.0.1:6080/vnc.html`
- CDP (debug profile only): `http://127.0.0.1:9222` — start with
  `make up-debug` or `docker compose --profile debug up`. Absent from the
  default `make up` service set.

## Project Layout

```text
appcore/                    Shared platform modules
packages/                   Framework-agnostic contracts and analysis logic
workflows/                  Canonical business workflows
executor/
  control.py               Workflow-visible sandbox boundary
  container/               Sandbox image and startup scripts
  flows/playwright/        VS Code GUI automation packages
ui/                         React + Vite analyst console
tests/
  architecture/            Import-graph and boundary checks
  platform/                Shared platform tests
  workflows/               Workflow tests
  executor/                Playwright runtime tests
    scanner/               Docker exec wrapper tests
  security/                Malicious-fixture scaffold checks
  smoke/                   End-to-end marketplace analysis tests
  ui tests live under ui/src/**/*.test.ts(x)
documents/                  Architecture, roadmap, and testing notes
docs/                       Targeted risk notes
```

## Documentation Index

- `documents/AGENT_CONTEXT.md`: thin task-routing map for coding agents after
  `AGENTS.md`
- `documents/agent-lanes/`: lazy-load task-lane docs for platform/storage,
  marketplace/analysis, executor/runtime, security/detection, UI, and docs
  maintenance
- `documents/README.md`: context-light guide for choosing which project docs to
  load first
- `documents/REFACTOR_STATUS.md`: slim current-state closure board and phase
  handoff history
- `documents/POST_POC_BACKLOG.md`: deferred work items and the pull-next list
- `documents/ARCHITECTURE.md`: canonical architecture and boundaries
- `documents/DETECTION_SEMANTICS.md`: meaning and calculation rules for
  exported `ActivationReport` fields
- `documents/PROJECT_STRUCTURE.md`: placement rules after the refactor
- `documents/TESTING.md`: current test layout and commands
- `documents/EXECUTOR_PLAYWRIGHT.md`: sandbox and Playwright details
- `documents/DEVELOPMENT_PRIORITIES.md`: near-term priorities for the sandbox
  product
- `documents/PIPELINE_ROADMAP.md`: pipeline direction without multi-tenant
  assumptions
- `documents/VSCODE_API_COVERAGE_AUDIT.md`: capability support and
  trigger/verification gaps
- `documents/automation_todo.md`: legacy/off-path backlog notes; current
  pull-next truth is `documents/POST_POC_BACKLOG.md` plus the active tracker
- `docs/risks.md`: current risk register
