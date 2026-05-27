# Agent Context

`Last Updated: 2026-05-27 (Active phase: W21 — W21-3 [GOAL taxonomy-workspace-trust-coverage] closed via primary c744c15 + self-stamp this commit (W21-0 doc-reconcile closed 8434323 + 19bd9c7 before W21-3). W21-3 primary landed _OFFICIAL_CAPABILITY_SUPPORT["workspace_trust"]: "missing" → "covered" at capabilities.py:99 + mirror in _GLOBAL_CAPABILITY_SUPPORT:47 (heuristic derives) + harness vscode.workspace.isTrusted baseline marker + onDidGrantWorkspaceTrust listener via reserved OutputChannel route (W19-X Bug B paterni) + workspace_trust_transition scenario in scenarios.py advertising workspace_trust + 4 invariant tests (W20-1 scm template mirror) at tests/platform/contracts/test_capability_support_invariants.py + dict shape canonical pin update + test_split_did_not_lose_data_volume count bump 13→14 + frozen trigger fixture regen for ms-python.python. Runtime stimulus pass (untrusted → granted exercise) deferred to W22 as [FOLLOWUP workspace-trust-stimulus-pass] — workspace trusted-by-default in container fixture; runtime exercise requires fixture restructuring. Opens week21 branch (per user direction 2026-05-27; W11-W20 paterni preserved — sub-iter commits land on week21, close-out merges via week21 -> main PR PENDING USER APPROVAL). Active W21 tracker documents/active-work/W21-coverage-promotion-mid-tier.md. §19 W21 plan header doc-open in REFACTOR_OPTIMIZATION.md split at W21-0 from §19-§20 W21-W22 planning combined header (W19-0 / W20-0 paterni mirror). W21 Pull-Forward Acceptance Bar promoted in POST_POC_BACKLOG.md at W21-0 (now W22 Roadmap Acceptance Bar planning for the residual W22 lane). 10-doc canonical preamble refresh at W21-0 + W21-3 self-stamp. README phase-pointer arch gate transition W20→W21 at W21-0 (test_readme_phase_pointer.py tracks_active_w21_status + new test_readme_phase_pointer_mentions_w20_closeout_merge pinning PR #29 / week20 -> main / 64a3c3d). W21-0 baseline live-run captured via W21-0 self-stamp (anchor activation_report_ms-python.python-2026.5.2026052501-600d9ecba5eb.json sha256 1db1480551fd90625a5c7c2e474b43c4de3a867d35dab4aacc65e8060bcc4477; W20 close-out invariants live-verified — coverage_summary.missing_capabilities = [chat, comments, testing, workspace_trust] (4 items byte-identical with W20-5 anchor 4e92de149802); W19 Hat-1 unaccounted_dropout_count is null; W19 Hat-2 harness_verification_unconfirmed_present DROPPED from reasons). W21-3 live-run anchor activation_report_ms-python.python-2026.5.2026052501-6fd7b959bd5a.json sha256 fa83017a4de25ea56c078da2bd7f65e2f54f10af5aa5c10e8ed000c92d6f7477 confirms W21-3 acceptance — coverage_summary.missing_capabilities 4 → 3 items [chat, comments, testing] (workspace_trust dropped — must-pass ✓), covered/partial/missing 7/7/4 → 8/7/3, workspace_trust matrix entry status "covered" is_active=true with workspace_trust_transition advertised in supported_scenarios. W20 invariants HOLD post-W21-3 (Hat-1 dropout=null; Hat-2 harness_verification_unconfirmed_present DROPPED). W21-3 live-run drift (non-invariant): extra_trigger_failures_present reason count = 9 (transient — previous failed analyze attempt left stale executor state after rebuild; W21-N close-out final live-run will re-verify on fresh stack) + new chat_tool_verification_incomplete reason (W22 surface — pre-existing matrix gap, not a W21-3 regression). W20 closed and merged via PR #29 week20 -> main MERGED 2026-05-26 via 64a3c3d; final W20 bar tests/architecture/ 240 passed / make test-security 220 passed / full suite 2045 passed, 9 skipped, 8 deselected. W21-3 test bar delta: tests/architecture/ 241 passed (unchanged from W21-0; W21-3 invariants live in contracts tier), tests/platform/contracts/test_capability_support_invariants.py 14 → 18 passed (+4 W21-3 invariants), make test-security 220 passed (unchanged), full suite 2045 → 2050 passed, 9 skipped, 8 deselected (+5 net: W21-0 +1 + W21-3 +4). W21 driving signal (carried over from W19 / W20): same Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities started at [scm, settings, chat, comments, testing, workspace_trust]; W20-5 final live-run 4e92de149802 confirmed missing dropped 6 → 4 [chat, comments, testing, workspace_trust]; W21-3 dropped workspace_trust (missing 4 → 3 [chat, comments, testing]); expected end-state drop 3 → 1 [chat] after W21-1 (testing) + W21-2 (comments) land; W22 closes hard tier (chat) + sandbox evasion ADR draft. §19 W21 plan source (active) + §20 W22 planning. W21 sub-iter slate: W21-0 doc-reconcile closed (8434323 + 19bd9c7) + W21-3 [GOAL taxonomy-workspace-trust-coverage] closed via c744c15 + this commit + W21-1 [GOAL taxonomy-testing-coverage] (next per user-confirmed ordering W21-3 → W21-1 → W21-2) + W21-2 [GOAL taxonomy-comments-coverage] + W21-4 [GOAL container-hardening-baseline] STRETCH (conditional pull only if W21-0..W21-3 closed cleanly; W21-3 now closed — W21-4 candidate stays in conditional-pull window) + W21-N close-out hygiene + PR week21 -> main PENDING USER APPROVAL. [FOLLOWUP sandbox-reset-stale-state-multi-analyze] (filed d163b02 at W20-5-followup-2) opportunistic at W21-N close-out window (user-confirmed); not a sub-iter, not a blocker. [FOLLOWUP workspace-trust-stimulus-pass] (filed c744c15 + this commit) W22 candidate — runtime untrusted → granted transition exercise; needs fixture restructuring. W19 closed and merged via PR #28 week19 -> main MERGED 2026-05-26 via c879603 — Hat-1 closed + live-verified; Hat-2 fully closed synthetically (W19-3 schema landing + W19-4 onDebug* producer/consumer + W19-X live close-out + W19-5 onTerminal+onLM log_record stamp); final W19 bar tests/architecture/ 204 / make test-security 220 / full suite 1995. W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; final W18 bar tests/architecture/ 201 / make test-security 220 / full suite 1907. W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f; W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 closed via PR #20 week13 -> main MERGED 2026-05-13 via 772deb3. W20 frozen tracker: documents/active-work/W20-coverage-promotion-easy-wins.md (frozen at W20-5 + followups per W17/W18/W19 paterni); W19 frozen tracker: documents/active-work/W19-live-run-root-cause.md (frozen at W19-6-followup-2); W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md; W21 active tracker: documents/active-work/W21-coverage-promotion-mid-tier.md; multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md.)`

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
