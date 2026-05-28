# Agent Context

`Last Updated: 2026-05-28 (W21 closed synthetically 2026-05-28 via W21-N close-out (this commit) — W21-4 [GOAL container-hardening-baseline] closed via primary 16e2224 + followup-1 2f9cba2 + self-stamp 8c42445 (W21-0 doc-reconcile closed 8434323 + 19bd9c7 + W21-3 closed c744c15 + 4b0a1ed + W21-1 closed 7e87030 + 38b8fd8 + W21-2 [GOAL taxonomy-comments-coverage] closed 8948ea6 + 3088709 before W21-4). W21-4 primary landed docker-compose.yml cap_drop:[ALL] + security_opt:[no-new-privileges:true] on executor/api/ui + ADR 0013 documenting decision + deferred items (read_only + tmpfs + custom seccomp profile → W22 ratchet-down lane) + 12 invariant tests at tests/architecture/test_compose_isolation_invariants.py. W21-4-followup-1 (2f9cba2) restored cap_add SETUID + SETGID on api (gosu user drop) + SETUID + SETGID + CHOWN + DAC_OVERRIDE on ui (nginx cache chown + worker drop) — both surfaced during the primary live-run smoke. executor cap_add NET_RAW + SYS_PTRACE preserved from pre-W21-4 for tcpdump/tshark/strace observability tools. W21-4 live-run anchor activation_report_ms-python.python-2026.5.2026052501-eacea0b6690e.json sha256 5d7c8b974f21e3bf4ad679a41551dd3e7b71d37573f5e7f2b28b87d2ad4a6a84 confirms NO coverage regression vs W21-2 anchor 1ddb3702c0ca (must-pass ✓): coverage_summary.missing_capabilities = [chat] (1 item, byte-identical with W21-2); covered/partial/missing = 8/9/1 (byte-identical); automation_health.status=degraded with 3 reasons (skipped_scenarios_present, verification_gap_present, official_unresolved_present — same shape as W21-2); W20 invariants HOLD post-W21-4 (Hat-1 unaccounted_dropout_count=null; Hat-2 harness_verification_unconfirmed_present DROPPED). Manual kernel-level smoke (docker exec into the executor + grep /proc/self/status for NoNewPrivs) returns NoNewPrivs=1 confirming PR_SET_NO_NEW_PRIVS active at the kernel. W21-2 [GOAL taxonomy-comments-coverage] closed via 8948ea6 + 3088709 before W21-4 hit comments official-track promotion missing → covered + harness CommentController + scenario + 4 invariants + fixture regen, dropping missing_capabilities 2 → 1 [chat]. W21-2 primary landed _OFFICIAL_CAPABILITY_SUPPORT["comments"]: "missing" → "covered" at capabilities.py:96 + mirror in _GLOBAL_CAPABILITY_SUPPORT:44 (heuristic derives) + harness CommentController baseline marker emitted at activate() entry + ensureCommentThread (stimulus_dispatch.js) extended to emit thread_created + thread_disposed markers via emitHarnessEvent through reserved OutputChannel route (W19-X Bug B paterni) with ephemeral thread default (W19-X HMAC reactivation race lesson — created+disposed in-call) + local_comments_controller scenario in scenarios.py advertising comments (mirror W21-3 workspace_trust_transition + W21-1 local_test_controller shape) + 4 invariant tests at tests/platform/contracts/test_capability_support_invariants.py + dict shape canonical pin update + test_split_did_not_lose_data_volume count bump 15→16 + frozen trigger fixture regen for ms-python.python. Runtime stimulus pass implicit — ensureCommentThread already invoked from the existing extrace.harness.runCurrentStimulus command handler, so any stimulus pass exercises the new markers without dedicated pass. Opens week21 branch (per user direction 2026-05-27; W11-W20 paterni preserved — sub-iter commits land on week21, close-out merges via week21 -> main PR PENDING USER APPROVAL). Active W21 tracker documents/active-work/W21-coverage-promotion-mid-tier.md. §19 W21 plan header doc-open in REFACTOR_OPTIMIZATION.md split at W21-0 from §19-§20 W21-W22 planning combined header (W19-0 / W20-0 paterni mirror). W21 Pull-Forward Acceptance Bar promoted in POST_POC_BACKLOG.md at W21-0 (now W22 Roadmap Acceptance Bar planning for the residual W22 lane). 10-doc canonical preamble refresh at W21-0 + W21-3 + W21-1 + W21-2 self-stamps (this commit). README phase-pointer arch gate transition W20→W21 at W21-0 (test_readme_phase_pointer.py tracks_active_w21_status + W20 close-out merge gate test pinning PR #29 / week20 -> main / 64a3c3d). W21-0 baseline anchor 600d9ecba5eb sha256 1db1480551fd...c4477; W21-3 anchor 6fd7b959bd5a sha256 fa83017a...d6f7477 confirmed workspace_trust dropped (4→3); W21-1 anchor 0b4998ce31b4 sha256 b7192bc2ff9c...968be4 confirmed testing dropped (3→2). W21-2 live-run anchor activation_report_ms-python.python-2026.5.2026052501-1ddb3702c0ca.json sha256 2dabd15be329bbf1685fe7fc31469355bdc4a5acac2a364d43a196437339cbff confirms W21-2 acceptance — coverage_summary.missing_capabilities 2 → 1 items [chat] (comments dropped — must-pass ✓; W21 mid-tier closure target hit — only chat remains for W22 hard tier), covered/partial/missing 8/8/2 → 8/9/1, comments matrix entry status "partial" support_status "covered" supported_scenarios ["local_comments_controller"]. W20 invariants HOLD post-W21-2 (Hat-1 dropout=null; Hat-2 harness_verification_unconfirmed_present DROPPED). W21-2 live-run drift clean (same shape as W21-1): only 3 reasons remain (skipped_scenarios_present, verification_gap_present, official_unresolved_present). W20 closed and merged via PR #29 week20 -> main MERGED 2026-05-26 via 64a3c3d; final W20 bar tests/architecture/ 240 passed / make test-security 220 passed / full suite 2045 passed, 9 skipped, 8 deselected. W21-3 test bar delta: contracts/test_capability_support_invariants.py 14 → 18 (+4); full suite 2045 → 2050 (+5 net). W21-1 test bar delta: contracts/test_capability_support_invariants.py 18 → 22 (+4); full suite 2050 → 2054 (+4 net). W21-2 test bar delta: tests/architecture/ 241 passed (unchanged from W21-1), tests/platform/contracts/test_capability_support_invariants.py 22 → 26 passed (+4 W21-2 invariants), tests/platform/contracts/test_registry_split_regression.py 8 passed (count pin 15 → 16), tests/workflows/marketplace/test_analysis_planner.py fixture parity green, make test-security 220 passed (unchanged), full suite 2054 → 2058 passed, 9 skipped, 8 deselected (+4 net W21-2 invariants). W21 driving signal (carried over from W19 / W20): same Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities started at [scm, settings, chat, comments, testing, workspace_trust]; W20-5 confirmed missing dropped 6 → 4 [chat, comments, testing, workspace_trust]; W21-3 dropped workspace_trust (4 → 3 [chat, comments, testing]); W21-1 dropped testing (3 → 2 [chat, comments]); W21-2 dropped comments (2 → 1 [chat]); W22 closes hard tier (chat) + sandbox evasion ADR draft. §19 W21 plan source (active) + §20 W22 planning. W21 sub-iter slate: W21-0 doc-reconcile closed (8434323 + 19bd9c7) + W21-3 [GOAL taxonomy-workspace-trust-coverage] closed (c744c15 + 4b0a1ed) + W21-1 [GOAL taxonomy-testing-coverage] closed (7e87030 + 38b8fd8) + W21-2 [GOAL taxonomy-comments-coverage] closed via 8948ea6 + this commit + W21-4 [GOAL container-hardening-baseline] STRETCH (user-pulled into W21 2026-05-27; final pull/defer decision pending after this commit) + W21-N close-out hygiene + PR week21 -> main PENDING USER APPROVAL. [FOLLOWUP sandbox-reset-stale-state-multi-analyze] (filed d163b02 at W20-5-followup-2) opportunistic at W21-N close-out window (user-confirmed); not a sub-iter, not a blocker. [FOLLOWUP workspace-trust-stimulus-pass] (filed c744c15 + 4b0a1ed) W22 candidate — runtime untrusted → granted transition exercise; needs fixture restructuring. W19 closed and merged via PR #28 week19 -> main MERGED 2026-05-26 via c879603; W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f; W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 closed via PR #20 week13 -> main MERGED 2026-05-13 via 772deb3. W20 frozen tracker: documents/active-work/W20-coverage-promotion-easy-wins.md (frozen at W20-5 + followups per W17/W18/W19 paterni); W19 frozen tracker: documents/active-work/W19-live-run-root-cause.md (frozen at W19-6-followup-2); W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md; W21 active tracker: documents/active-work/W21-coverage-promotion-mid-tier.md; multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md.)`

Thin routing map for coding agents after `AGENTS.md`. **Stays short.**
Do not copy phase history here; use `REFACTOR_STATUS.md` (slim canonical).

## Source Of Truth

- Current closure state: `REFACTOR_STATUS.md` (slim canonical; full
  history under `archive/status/`).
- Deferred/pull-next work: `POST_POC_BACKLOG.md` (slim canonical;
  full backlog under `archive/backlog/`).
- W8-W13 plan: `REFACTOR_OPTIMIZATION.md` section 11; W14 plan:
  `REFACTOR_OPTIMIZATION.md` section 12; W15 plan:
  `REFACTOR_OPTIMIZATION.md` section 13; W16 plan:
  `REFACTOR_OPTIMIZATION.md` section 14; W17 plan:
  `REFACTOR_OPTIMIZATION.md` section 15; W18 plan:
  `REFACTOR_OPTIMIZATION.md` section 16; W19 plan:
  `REFACTOR_OPTIMIZATION.md` section 17 (closed synthetically);
  **W20 plan: `REFACTOR_OPTIMIZATION.md` section 18 (closed
  synthetically; PR `week20 -> main` PENDING USER APPROVAL);
  W21-W22 multi-iter roadmap: `REFACTOR_OPTIMIZATION.md`
  sections 19-20** (split at W20-0 open from the original
  §18-§20 combined header — same paterni as the W19-0 split of
  §17-§20; source-of-truth tracker
  `active-work/W18-W22-roadmap.md`; slim canonical; full text
  under `archive/plans/`).
- W8-W20 are closed; W13 merged via PR #20 (`772deb3`); W14 merged via
  PR #21 (`4e03c8d`); W15 merged via PR #22 (`6161472`) on
  `2026-05-18`; W16 merged via PR #23 (`1b6d43f`) on `2026-05-18`;
  W17 merged via PR #25 (`bff565d`) on `2026-05-18`;
  W18 merged via PR #26 (`9874e79`) on `2026-05-21`;
  W19 merged via PR #28 (`c879603`) on `2026-05-26`;
  **W20 closed synthetically `2026-05-27` on the `week20`
  branch — close-out PR `week20 -> main` PENDING USER APPROVAL**.
  Past W8/W11/W12/W13/W14/W15/W16/W17/W18/W19/W20 trackers remain
  only for stable IDs referenced by code/tests. **Previous phase:**
  W20 — Coverage Promotion Round 1: Easy Wins (**closed
  synthetically `2026-05-27`** on the `week20` branch per user
  direction `2026-05-26`; W11-W19 paterni preserved; close-out
  PR `week20 -> main` PENDING USER APPROVAL). W20-0..W20-5 all
  closed: W20-0 doc-reconcile (`66a8a0b` + `5f13757`) + baseline
  live-run capture (anchor `e89a82ca9ba8`, sha256
  `4dd78826...0256ffe`); W20-1
  `[GOAL taxonomy-scm-official-promotion]` (`82276cb` + `a17e595`)
  at `packages/analysis_planner/capabilities.py:88`; W20-2
  `[GOAL taxonomy-settings-official-promotion]` (`a4343d2` +
  `7406588`) at `capabilities.py:90`; W20-3
  `[GOAL coverage-matrix-contract-tests]` (`d4c03b6` + `2e39230`);
  W20-4 `[DESIGN taxonomy-comments-testing-readiness]` (`05f47f3` +
  `b409894`) at
  `documents/architecture/comments-testing-readiness.md`; W20-5
  close-out hygiene (`4665d32` primary + `95b0010` self-stamp +
  `d163b02` followup-2 filed
  `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` for W21 +
  `ae5b7de` followup-3 10-doc preamble `(this commit)` placeholder
  backfill). **W20 scope**: Hat-3 coverage matrix promotion easy
  tier (`scm` + `settings` official-track promotion); W20
  acceptance **LIVE-SATISFIED** on fresh run `4e92de149802`
  (sha256 `3804a5b5...4394c`): `coverage_summary.missing_capabilities`
  6 → 4 (lost `scm` + `settings`); W19 Hat-1 + Hat-2 hold
  post-W20. Hat-3 mid + hard tiers deferred to W21-W22. Final W20
  bar: `tests/architecture/` **240 passed**, 4 deselected;
  `make test-security` **220 passed**; full suite **2045 passed,
  9 skipped, 8 deselected**. **Previous phase:** W19 — Live-Run
  Kök Neden: Dropout + Harness Verification (**closed
  synthetically `2026-05-26`** on the `week19` branch per user
  direction; W11-W18 paterni preserved; PR #28
  `week19 -> main` MERGED `2026-05-26` via `c879603`).
  W19-0..W19-6 + W19-X all closed: W19-0 doc-reconcile
  (`72712bd` + `086d7a5`), W19-1 RED dropout fixture (`6a21cf3` +
  `fd02ca4`), W19-2 emit-site fix (`89b64da` + `d9c6262`) plus
  live re-anchor `d5de9ca` satisfying `unaccounted_dropout == 0`,
  W19-3 schema landing (`d2e83e7` + `39121e4` + `9b56e94`), W19-4
  `onDebug*` nonce producer/consumer wire (`7d44b0e`), W19-X `onDebug*`
  live close-out (`8b7b7f6` + `a3e634f`), W19-5 onTerminal+onLM
  log_record stamp (`e537ebd` + `4fd6ed6`), W19-6 close-out hygiene
  (`f17b4b1` + `cd82153` + `800c69f`). **W19 scope**: Hat-1 executor
  muhasebe bug closed + live-verified; Hat-2 harness verification gap
  fully closed synthetically; Hat-3 coverage matrix promotion
  deferred to W20-W22 (W20 closed easy tier — see above). **Previous
  phase:** W18 — Heartbeat Refactor (closed `2026-05-21` via PR #26
  `week18 -> main` MERGED via `9874e79`; W18-0..W18-4 sub-iter
  slate + W18-4-followup fully delivered; final W18 bar
  `tests/architecture/` **201 passed**; `make test-security`
  **220 passed**; full suite **1907 passed, 9 skipped,
  8 deselected**). W18 frozen tracker:
  `active-work/W18-heartbeat-refactor.md`; W19 frozen tracker:
  `active-work/W19-live-run-root-cause.md`; W20 frozen tracker:
  `active-work/W20-coverage-promotion-easy-wins.md`; multi-iter
  roadmap source-of-truth: `active-work/W18-W22-roadmap.md`. For
  current closure state always defer to `REFACTOR_STATUS.md`.
- Architecture: `ARCHITECTURE.md` (slim) + `architecture/` splits.
- Placement rules: `PROJECT_STRUCTURE.md` (slim) + `structure/` splits.
- Test lanes: `TESTING.md` (slim) + `testing/` splits.

## Task Decision Tree

Open the matching lane first; open the third-column docs only on the listed
trigger.

| If the task touches... | Open this lane first | Then open only if the trigger matches |
|---|---|---|
| FastAPI config, DB, schemas, CRUD, migrations | `agent-lanes/platform-storage.md` | `ARCHITECTURE.md` (new boundary/dependency line); `PROJECT_STRUCTURE.md` (new top-level package); `TESTING.md` (new test layer / fixture pattern) |
| Marketplace search/download/analyze jobs, trigger planning | `agent-lanes/marketplace-analysis.md` | `PIPELINE_ROADMAP.md` (staged pipeline direction); `VSCODE_API_COVERAGE_AUDIT.md` (capability/coverage question); `testing/marketplace-tests.md` |
| Docker executor, Playwright, harness, runtime capture | `agent-lanes/executor-runtime.md` | `EXECUTOR_PLAYWRIGHT.md` slim → `executor/host-wrapper.md` / `executor/playwright-flow.md` / `executor/runtime-capture.md` (whichever sub-area you touch); relevant runbook |
| Detection rules, malicious fixtures, ADR security posture | `agent-lanes/security-detection.md` | ADRs 0002-0005 (only the one that governs the touched boundary); `DETECTION_SEMANTICS.md` slim → `detection/evidence-fields.md` / `detection/health-signals.md` / `detection/rule-lifecycle.md` |
| React/Vite UI or generated TS contracts | `agent-lanes/ui.md` | `ui/README.md`, UI tests |
| Documentation drift, README, runbooks, ADR text | `agent-lanes/docs-maintenance.md` | `documents/README.md`; current code/tests; archive only when retracing why a thing changed |
| W8/W9 closure history (stable IDs in code/tests) | (lane above) | `active-work/W8-security.md` for W8-1..W8-9 IDs; `REFACTOR_STATUS.md` for W9 closure evidence |

If a task touches a slim canonical's domain without matching a split trigger,
open the slim canonical itself, not its splits.

## Core Paths

- Entry point: `main.py`.
- Backend: `appcore/`, `workflows/`, `executor/`.
- Framework-agnostic packages: `packages/`.
- Frontend: `ui/`.
- Tests: `tests/`.
- Docs: `documents/`; archive is off default path.

## Minimal Rules Reminder

- DB writes go through `appcore/storage/crud.py`.
- Pydantic validation happens before insert.
- Sandbox execution stays Docker-isolated.
- `packages/` remains framework-agnostic.
- Detection rules consume contracts only.
- Matching tests should be opened early.
