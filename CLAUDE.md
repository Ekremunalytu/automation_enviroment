# CLAUDE.md

`Last Updated: 2026-05-28 (W22-1 [GOAL taxonomy-chat-policy-adr] closed 906fcd5 + self-stamp (this commit) — ADR 0014 documents/adrs/0014-chat-and-language-model-tool-policy.md Accepted Option C (tool-only coverage via stable vscode.chat.createChatParticipant + vscode.lm.registerTool + vscode.lm.invokeTool APIs, all GA since VS Code 1.90 / no external services / no proposed APIs / no engine bump); markers route via reserved OutputChannel (W19-X Bug B paterni); ephemeral lifecycle on context.subscriptions (W19-X Bug C lesson); alternatives A (proposed-API stub provider via registerChatModelProvider), B (mock invokeTool without registration), D (declare partial with blocker) rejected with gerekçe in ADR §Alternatives Rejected; + 2 architecture invariants at tests/architecture/test_chat_policy_adr.py (existence pin + Option C content marker pin); unblocks W22-2 [GOAL taxonomy-chat-coverage]; test bar delta tests/architecture/ 288 → 290 (+2); make test-security 220 unchanged; no live-run anchor needed (W22-1 doc-only). W22-0 doc-reconcile closed 26bb080 + ff3fbbd opens week22 branch (per user direction 2026-05-28; W11-W21 paterninden bu sefer ayrılma — tek branch week22, sub-iter başına ayrı branch yok); main onayı zorunlu (memory feedback_pr_push_approval standing); paralel statik analiz şeridi ayrı worktree'de extrace-static branch — bu W22 oturumu ile çakışma yok. W21 closed and merged via PR #30 week21 -> main MERGED 2026-05-28 via 5dc18aa (W21-N close-out at dd24f1e); final W21 bar tests/architecture/ 287 passed / make test-security 220 passed / full suite 2104 passed, 9 skipped, 8 deselected. W22 active tracker documents/active-work/W22-coverage-promotion-hard-tier.md per W18-W21 paterni. Earlier-phase audit-trail: W21 final close-out W21-N at dd24f1e (W21 phase fully delivered 2026-05-28) — W21-4 [GOAL container-hardening-baseline] closed via primary 16e2224 + followup-1 2f9cba2 + self-stamp 8c42445 (W21-0 doc-reconcile closed 8434323 + 19bd9c7 + W21-3 closed c744c15 + 4b0a1ed + W21-1 closed 7e87030 + 38b8fd8 + W21-2 [GOAL taxonomy-comments-coverage] closed 8948ea6 + 3088709 before W21-4). W21-4 primary landed docker-compose.yml cap_drop:[ALL] + security_opt:[no-new-privileges:true] on executor/api/ui + ADR 0013 documenting decision + deferred items (read_only + tmpfs + custom seccomp profile → W22 ratchet-down lane) + 12 invariant tests at tests/architecture/test_compose_isolation_invariants.py. W21-4-followup-1 (2f9cba2) restored cap_add SETUID + SETGID on api (gosu user drop) + SETUID + SETGID + CHOWN + DAC_OVERRIDE on ui (nginx cache chown + worker drop) — both surfaced during the primary live-run smoke. executor cap_add NET_RAW + SYS_PTRACE preserved from pre-W21-4 for tcpdump/tshark/strace observability tools. W21-4 live-run anchor activation_report_ms-python.python-2026.5.2026052501-eacea0b6690e.json sha256 5d7c8b974f21e3bf4ad679a41551dd3e7b71d37573f5e7f2b28b87d2ad4a6a84 confirms NO coverage regression vs W21-2 anchor 1ddb3702c0ca (must-pass ✓): coverage_summary.missing_capabilities = [chat] (1 item, byte-identical with W21-2); covered/partial/missing = 8/9/1 (byte-identical); automation_health.status=degraded with 3 reasons (skipped_scenarios_present, verification_gap_present, official_unresolved_present — same shape as W21-2); W20 invariants HOLD post-W21-4 (Hat-1 unaccounted_dropout_count=null; Hat-2 harness_verification_unconfirmed_present DROPPED). Manual kernel-level smoke (docker exec into the executor + grep /proc/self/status for NoNewPrivs) returns NoNewPrivs=1 confirming PR_SET_NO_NEW_PRIVS active at the kernel. W21-2 [GOAL taxonomy-comments-coverage] closed via 8948ea6 + 3088709 before W21-4 hit comments official-track promotion missing → covered + harness CommentController + scenario + 4 invariants + fixture regen, dropping missing_capabilities 2 → 1 [chat]. W21-2 primary landed _OFFICIAL_CAPABILITY_SUPPORT["comments"]: "missing" → "covered" at capabilities.py:96 + mirror in _GLOBAL_CAPABILITY_SUPPORT:44 (heuristic derives) + harness CommentController baseline marker emitted at activate() entry + ensureCommentThread (stimulus_dispatch.js) extended to emit thread_created + thread_disposed markers via emitHarnessEvent through reserved OutputChannel route (W19-X Bug B paterni) with ephemeral thread default (W19-X HMAC reactivation race lesson — created+disposed in-call) + local_comments_controller scenario in scenarios.py advertising comments (mirror W21-3 workspace_trust_transition + W21-1 local_test_controller shape) + 4 invariant tests at tests/platform/contracts/test_capability_support_invariants.py + dict shape canonical pin update + test_split_did_not_lose_data_volume count bump 15→16 + frozen trigger fixture regen for ms-python.python. Runtime stimulus pass implicit — ensureCommentThread already invoked from the existing extrace.harness.runCurrentStimulus command handler, so any stimulus pass exercises the new markers without dedicated pass. Opens week21 branch (per user direction 2026-05-27; W11-W20 paterni preserved — sub-iter commits land on week21, close-out merges via week21 -> main PR PENDING USER APPROVAL). W21 frozen tracker documents/active-work/W21-coverage-promotion-mid-tier.md. §19 W21 plan header doc-open in REFACTOR_OPTIMIZATION.md split at W21-0 from §19-§20 W21-W22 planning combined header (W19-0 / W20-0 paterni mirror). W21 Pull-Forward Acceptance Bar promoted in POST_POC_BACKLOG.md at W21-0 (now W22 Roadmap Acceptance Bar planning for the residual W22 lane). 10-doc canonical preamble refresh at W21-0 + W21-3 + W21-1 + W21-2 self-stamps 26bb080. README phase-pointer arch gate transition W20→W21 at W21-0 (test_readme_phase_pointer.py tracks_active_w21_status + W20 close-out merge gate test pinning PR #29 / week20 -> main / 64a3c3d). W21-0 baseline anchor 600d9ecba5eb sha256 1db1480551fd...c4477; W21-3 anchor 6fd7b959bd5a sha256 fa83017a...d6f7477 confirmed workspace_trust dropped (4→3); W21-1 anchor 0b4998ce31b4 sha256 b7192bc2ff9c...968be4 confirmed testing dropped (3→2). W21-2 live-run anchor activation_report_ms-python.python-2026.5.2026052501-1ddb3702c0ca.json sha256 2dabd15be329bbf1685fe7fc31469355bdc4a5acac2a364d43a196437339cbff confirms W21-2 acceptance — coverage_summary.missing_capabilities 2 → 1 items [chat] (comments dropped — must-pass ✓; W21 mid-tier closure target hit — only chat remains for W22 hard tier), covered/partial/missing 8/8/2 → 8/9/1, comments matrix entry status "partial" support_status "covered" supported_scenarios ["local_comments_controller"]. W20 invariants HOLD post-W21-2 (Hat-1 dropout=null; Hat-2 harness_verification_unconfirmed_present DROPPED). W21-2 live-run drift clean (same shape as W21-1): only 3 reasons remain (skipped_scenarios_present, verification_gap_present, official_unresolved_present). W20 closed and merged via PR #29 week20 -> main MERGED 2026-05-26 via 64a3c3d; final W20 bar tests/architecture/ 240 passed / make test-security 220 passed / full suite 2045 passed, 9 skipped, 8 deselected. W21-3 test bar delta: contracts/test_capability_support_invariants.py 14 → 18 (+4); full suite 2045 → 2050 (+5 net). W21-1 test bar delta: contracts/test_capability_support_invariants.py 18 → 22 (+4); full suite 2050 → 2054 (+4 net). W21-2 test bar delta: tests/architecture/ 241 passed (unchanged from W21-1), tests/platform/contracts/test_capability_support_invariants.py 22 → 26 passed (+4 W21-2 invariants), tests/platform/contracts/test_registry_split_regression.py 8 passed (count pin 15 → 16), tests/workflows/marketplace/test_analysis_planner.py fixture parity green, make test-security 220 passed (unchanged), full suite 2054 → 2058 passed, 9 skipped, 8 deselected (+4 net W21-2 invariants). W21 driving signal (carried over from W19 / W20): same Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities started at [scm, settings, chat, comments, testing, workspace_trust]; W20-5 confirmed missing dropped 6 → 4 [chat, comments, testing, workspace_trust]; W21-3 dropped workspace_trust (4 → 3 [chat, comments, testing]); W21-1 dropped testing (3 → 2 [chat, comments]); W21-2 dropped comments (2 → 1 [chat]); W22 closes hard tier (chat) + sandbox evasion ADR draft. §19 W21 plan source (active) + §20 W22 planning. W21 sub-iter slate: W21-0 doc-reconcile closed (8434323 + 19bd9c7) + W21-3 [GOAL taxonomy-workspace-trust-coverage] closed (c744c15 + 4b0a1ed) + W21-1 [GOAL taxonomy-testing-coverage] closed (7e87030 + 38b8fd8) + W21-2 [GOAL taxonomy-comments-coverage] closed (8948ea6 + 3088709) + W21-4 [GOAL container-hardening-baseline] closed (16e2224 + 2f9cba2 + 8c42445; user-pulled into W21 2026-05-28 per AskUserQuestion after W21-1+W21-2 closed cleanly; baseline only — read_only + tmpfs + custom seccomp profile deferred to W22 ratchet-down per ADR 0013 §Deferred) + W21-N close-out hygiene + PR #30 week21 -> main MERGED 2026-05-28 via 5dc18aa. [FOLLOWUP sandbox-reset-stale-state-multi-analyze] (filed d163b02 at W20-5-followup-2) opportunistic at W21-N close-out window (user-confirmed); not a sub-iter, not a blocker. [FOLLOWUP workspace-trust-stimulus-pass] (filed c744c15 + 4b0a1ed) W22 candidate — runtime untrusted → granted transition exercise; needs fixture restructuring. W19 closed and merged via PR #28 week19 -> main MERGED 2026-05-26 via c879603; W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f; W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 closed via PR #20 week13 -> main MERGED 2026-05-13 via 772deb3. W20 frozen tracker: documents/active-work/W20-coverage-promotion-easy-wins.md (frozen at W20-5 + followups per W17/W18/W19 paterni); W19 frozen tracker: documents/active-work/W19-live-run-root-cause.md (frozen at W19-6-followup-2); W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md; W21 frozen tracker: documents/active-work/W21-coverage-promotion-mid-tier.md (frozen at W21-N close-out dd24f1e per W17/W18/W19/W20 paterni); W22 active tracker: documents/active-work/W22-coverage-promotion-hard-tier.md; multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md.)`

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
  **W19 by section 17 (closed synthetically `2026-05-26` on `week19`
  branch; PR #28 `week19 -> main` MERGED `2026-05-26` via `c879603`);
  W20 by section 18 (closed + merged via PR #29 / `64a3c3d`);
  W21 by section 19 (closed synthetically; PR `week21 -> main`
  PENDING USER APPROVAL); W22 by section 20 (planning);
  source-of-truth tracker
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

  **Previous phase: W19 — Live-Run Kök Neden: Dropout + Harness
  Verification — closed synthetically `2026-05-26` on the `week19`
  branch (per user direction 2026-05-21; W11-W18 paterni preserved);
  PR #28 `week19 -> main` MERGED `2026-05-26` via `c879603`. §17 W19
  plan source in `documents/REFACTOR_OPTIMIZATION.md`. W19-0..W19-6
  + W19-X all closed**: W19-0 doc-reconcile
  (`72712bd` + `086d7a5`); W19-1 RED dropout fixture
  (`6a21cf3` + `fd02ca4`); W19-2 emit-site fix (`89b64da` +
  `d9c6262`) + W19-2-followup-2 live re-anchor (`d5de9ca`)
  satisfying `unaccounted_dropout == 0`; W19-3 schema landing
  (`d2e83e7` + `39121e4` + W19-3-followup-2 `9b56e94`); W19-4
  `onDebug*` harness_nonce producer/consumer wire (`7d44b0e`); W19-X
  `onDebug*` live close-out (`8b7b7f6` + `a3e634f`) closing Bug A
  planner routing / Bug B marker channel destination / Bug C HMAC
  reactivation race; W19-5 onTerminal+onLM log_record stamp
  (`e537ebd` + `4fd6ed6`); W19-6 close-out hygiene (`f17b4b1` +
  `cd82153`); W19-6-followup-2 pre-merge hygiene 26bb080 —
  closes 6 pre-merge test gaps + corrects stale W19 preamble
  drift across 9-doc canonical set + freezes W19 tracker.
  Driving signal: Codex live-run validation of `ms-python.python`
  @ `992ad028f3df` (2026-05-21). Plan identified three independent
  problem hatları; **Hat-1 closed + live-verified, Hat-2 fully
  closed synthetically**: Hat-1 executor muhasebe bug
  (`[BUG scenario-unaccounted-dropout-regression-fixture]` W19-1 +
  `[BUG scenario-unaccounted-dropout-debug-refactor]` W19-2) + Hat-2
  harness verification gap
  (`[GOAL harness-verification-contract-event-level]` W19-3
  schema landing + `[FOLLOWUP harness-verification-debug-events]`
  W19-4 + `[FOLLOWUP harness-verification-terminal-and-lm-tool]`
  W19-5). **Hat-3 coverage matrix promotion deferred to
  W20-W22 per multi-iter roadmap** (§18-§20). W19 acceptance
  (live-run-driven): `unaccounted_dropout == 0` (must-pass) ✓;
  `harness_verification_unconfirmed_present` reason drops
  (must-pass) ✓ synthetic / live-pending-next-run;
  `run_quality: low → medium` (expected); `verification_gap_present`
  drops (stretch); `automation_health.status: degraded` OK (W20 will
  close `official_unresolved_present`). Frozen tracker:
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
