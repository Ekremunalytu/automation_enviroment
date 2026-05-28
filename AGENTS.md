# AGENTS.md

`Last Updated: 2026-05-27 (Active phase: W21 — W21-1 [GOAL taxonomy-testing-coverage] closed via primary 7e87030 + self-stamp this commit (W21-0 doc-reconcile closed 8434323 + 19bd9c7 + W21-3 [GOAL taxonomy-workspace-trust-coverage] closed c744c15 + 4b0a1ed before W21-1). W21-1 primary landed _OFFICIAL_CAPABILITY_SUPPORT["testing"]: "missing" → "covered" at capabilities.py:97 + mirror in _GLOBAL_CAPABILITY_SUPPORT:45 (heuristic derives) + harness Test Controller run/debug profile callbacks emit test_controller_event markers (phases baseline / {run,debug}_invoked / {run,debug}_complete) via emitHarnessEvent through reserved OutputChannel route (W19-X Bug B paterni) with ephemeral TestItem rebuild on every invocation (W19-X HMAC reactivation race lesson) + local_test_controller scenario in scenarios.py advertising testing (mirror W21-3 workspace_trust_transition shape) + 4 invariant tests (W21-3 workspace_trust template mirror) at tests/platform/contracts/test_capability_support_invariants.py + dict shape canonical pin update + test_split_did_not_lose_data_volume count bump 14→15 + frozen trigger fixture regen for ms-python.python. Runtime stimulus pass that drives testing.runAll end-to-end deferred (W21-N or W22 follow-up) — Test Controller callbacks fire on any future run profile invocation without dedicated stimulus pass. Opens week21 branch (per user direction 2026-05-27; W11-W20 paterni preserved — sub-iter commits land on week21, close-out merges via week21 -> main PR PENDING USER APPROVAL). Active W21 tracker documents/active-work/W21-coverage-promotion-mid-tier.md. §19 W21 plan header doc-open in REFACTOR_OPTIMIZATION.md split at W21-0 from §19-§20 W21-W22 planning combined header (W19-0 / W20-0 paterni mirror). W21 Pull-Forward Acceptance Bar promoted in POST_POC_BACKLOG.md at W21-0 (now W22 Roadmap Acceptance Bar planning for the residual W22 lane). 10-doc canonical preamble refresh at W21-0 + W21-3 self-stamp + W21-1 self-stamp (this commit). README phase-pointer arch gate transition W20→W21 at W21-0 (test_readme_phase_pointer.py tracks_active_w21_status + new test_readme_phase_pointer_mentions_w20_closeout_merge pinning PR #29 / week20 -> main / 64a3c3d). W21-0 baseline live-run captured via W21-0 self-stamp (anchor activation_report_ms-python.python-2026.5.2026052501-600d9ecba5eb.json sha256 1db1480551fd90625a5c7c2e474b43c4de3a867d35dab4aacc65e8060bcc4477). W21-3 live-run anchor activation_report_ms-python.python-2026.5.2026052501-6fd7b959bd5a.json sha256 fa83017a4de25ea56c078da2bd7f65e2f54f10af5aa5c10e8ed000c92d6f7477 confirmed W21-3 acceptance (coverage_summary.missing_capabilities 4 → 3 items [chat, comments, testing], workspace_trust dropped). W21-1 live-run anchor activation_report_ms-python.python-2026.5.2026052501-0b4998ce31b4.json sha256 b7192bc2ff9c611f00e9dd806af54e0648c92d9201d78fe9ccb886dcf5968be4 confirms W21-1 acceptance — coverage_summary.missing_capabilities 3 → 2 items [chat, comments] (testing dropped — must-pass ✓), covered/partial/missing 8/7/3 → 8/8/2, testing matrix entry status "partial" support_status "covered" supported_scenarios ["local_test_controller"]. W20 invariants HOLD post-W21-1 (Hat-1 dropout=null; Hat-2 harness_verification_unconfirmed_present DROPPED). W21-1 live-run drift IMPROVEMENT vs W21-3: extra_trigger_failures_present DROPPED from reasons (was count=9 in W21-3 — transient stale executor state confirmed cleared on fresh rebuild) + chat_tool_verification_incomplete DROPPED from reasons (was W21-3 surface; remains W22 [GOAL taxonomy-chat-coverage] candidate); only 3 reasons remain (skipped_scenarios_present, verification_gap_present, official_unresolved_present). W20 closed and merged via PR #29 week20 -> main MERGED 2026-05-26 via 64a3c3d; final W20 bar tests/architecture/ 240 passed / make test-security 220 passed / full suite 2045 passed, 9 skipped, 8 deselected. W21-3 test bar delta: tests/platform/contracts/test_capability_support_invariants.py 14 → 18 (+4 W21-3 invariants); full suite 2045 → 2050 (+5 net). W21-1 test bar delta: tests/architecture/ 241 passed (unchanged from W21-3), tests/platform/contracts/test_capability_support_invariants.py 18 → 22 passed (+4 W21-1 invariants), tests/platform/contracts/test_registry_split_regression.py 8 passed (count pin 14 → 15), tests/workflows/marketplace/test_analysis_planner.py fixture parity green, make test-security 220 passed (unchanged), full suite 2050 → 2054 passed, 9 skipped, 8 deselected (+4 net W21-1 invariants). W21 driving signal (carried over from W19 / W20): same Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities started at [scm, settings, chat, comments, testing, workspace_trust]; W20-5 final live-run 4e92de149802 confirmed missing dropped 6 → 4 [chat, comments, testing, workspace_trust]; W21-3 dropped workspace_trust (missing 4 → 3 [chat, comments, testing]); W21-1 dropped testing (missing 3 → 2 [chat, comments]); expected end-state drop 2 → 1 [chat] after W21-2 (comments) lands; W22 closes hard tier (chat) + sandbox evasion ADR draft. §19 W21 plan source (active) + §20 W22 planning. W21 sub-iter slate: W21-0 doc-reconcile closed (8434323 + 19bd9c7) + W21-3 [GOAL taxonomy-workspace-trust-coverage] closed (c744c15 + 4b0a1ed) + W21-1 [GOAL taxonomy-testing-coverage] closed via 7e87030 + this commit + W21-2 [GOAL taxonomy-comments-coverage] (next sub-iter) + W21-4 [GOAL container-hardening-baseline] STRETCH (user-pulled into W21 2026-05-27; conditional final decision after W21-2 closes) + W21-N close-out hygiene + PR week21 -> main PENDING USER APPROVAL. [FOLLOWUP sandbox-reset-stale-state-multi-analyze] (filed d163b02 at W20-5-followup-2) opportunistic at W21-N close-out window (user-confirmed); not a sub-iter, not a blocker. [FOLLOWUP workspace-trust-stimulus-pass] (filed c744c15 + 4b0a1ed) W22 candidate — runtime untrusted → granted transition exercise; needs fixture restructuring. W19 closed and merged via PR #28 week19 -> main MERGED 2026-05-26 via c879603 — Hat-1 closed + live-verified; Hat-2 fully closed synthetically (W19-3 schema landing + W19-4 onDebug* producer/consumer + W19-X live close-out + W19-5 onTerminal+onLM log_record stamp); final W19 bar tests/architecture/ 204 / make test-security 220 / full suite 1995. W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; final W18 bar tests/architecture/ 201 / make test-security 220 / full suite 1907. W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f; W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 closed via PR #20 week13 -> main MERGED 2026-05-13 via 772deb3. W20 frozen tracker: documents/active-work/W20-coverage-promotion-easy-wins.md (frozen at W20-5 + followups per W17/W18/W19 paterni); W19 frozen tracker: documents/active-work/W19-live-run-root-cause.md (frozen at W19-6-followup-2); W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md; W21 active tracker: documents/active-work/W21-coverage-promotion-mid-tier.md; multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md.)`

## Authority

- This file is the hard-rules entrypoint for agents.
- It is intentionally short because it is frequently preloaded into context.
- For task routing after these rules, read
  `documents/AGENT_CONTEXT.md`.
- For current phase state, trust `documents/REFACTOR_STATUS.md`.
- If docs conflict with code or tests, trust code/tests and update the doc.
- If a requested change violates these principles, stop and report instead of
  implementing.

## Current State

- W0-W7 closed `2026-04-23`; PR345 and W8-0 landed `2026-04-27`.
- **W8 closed `2026-04-29`; W9 closed `2026-05-04` via PR #9; W10
  closed `2026-05-04` via PR #11; W11 closed `2026-05-05` and merged
  via PR #14; W12 closed `2026-05-10` and merged via PR #18
  (`33a0852`); W13 closed `2026-05-13` and merged via PR #20
  (`772deb3`); W14 closed `2026-05-14` and merged via PR #21
  (`4e03c8d`); W15 closed `2026-05-17` and merged via PR #22
  (`6161472`) on `2026-05-18`** — W15-1..W15-7 sub-iter slate +
  W15-1 post-slate typing hotfix + close-out hygiene pass (doc
  preamble truth-state refresh across 7 canonical docs + ADR 0011
  catalog endpoint posture gate + compose image SHA pin + GH action
  trivy version pin + close-out lint hygiene). Frozen tracker:
  `documents/active-work/W15-codex-uclass-bounds-posture.md`.
  **Previous phase: W20 — Coverage Promotion Round 1: Easy Wins —
  closed synthetically `2026-05-27` on the `week20` branch (per
  user direction `2026-05-26`; W11-W19 paterni preserved); close-out
  PR `week20 -> main` PENDING USER APPROVAL**: plan
  `documents/REFACTOR_OPTIMIZATION.md` §18, frozen tracker
  `documents/active-work/W20-coverage-promotion-easy-wins.md`.
  **W20-0..W20-5 all closed**: W20-0 doc-reconcile (`66a8a0b` +
  `5f13757`) + baseline live-run capture (anchor `e89a82ca9ba8`,
  sha256 `4dd78826...0256ffe`); W20-1
  `[GOAL taxonomy-scm-official-promotion]` (`82276cb` + `a17e595`) —
  `_OFFICIAL_CAPABILITY_SUPPORT["scm"]: "missing" → "covered"` at
  `packages/analysis_planner/capabilities.py:88` + 4 invariant tests
  + fixture regen; W20-2
  `[GOAL taxonomy-settings-official-promotion]` (`a4343d2` +
  `7406588`) — W20-1 paterni byte-identical at `capabilities.py:90`;
  W20-3 `[GOAL coverage-matrix-contract-tests]` (`d4c03b6` +
  `2e39230`) — 5 invariant set (keyset parity + Official ⊆
  Heuristic + notes ↔ taxonomy + ordering + W20-1/W20-2 combined
  post-condition); W20-4
  `[DESIGN taxonomy-comments-testing-readiness]` (`05f47f3` +
  `b409894`) — doc-only readiness şablonu at
  `documents/architecture/comments-testing-readiness.md` (W21-1 +
  W21-2 unblocker); W20-5 close-out hygiene (`4665d32` primary +
  `95b0010` self-stamp + `d163b02` followup-2 filed
  `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` for W21 +
  `ae5b7de` followup-3 10-doc preamble `(this commit)` placeholder
  backfill) — 9-doc canonical preamble Active → Previous flip +
  §18 W20 self-stamp + W20 tracker freeze + 3 new arch invariant
  tests (GAP-A `test_w20_section_18_cross_doc_parity.py` + GAP-B
  `_OFFICIAL_CAPABILITY_SUPPORT` dict shape pin extension + GAP-D
  `test_w20_4_design_doc_presence.py`) + W20-5 final live-run
  (anchor `4e92de149802`, sha256 `3804a5b5...4394c`). **W20
  acceptance LIVE-SATISFIED**: `coverage_summary.missing_capabilities`
  6 → 4 (lost `scm` + `settings`); W19 Hat-1 + Hat-2 hold post-W20.
  Hat-3 mid + hard tiers (testing / comments / workspace_trust /
  chat) deferred to W21-W22 per multi-iter roadmap. Final W20 bar:
  `tests/architecture/` **240 passed**, 4 deselected;
  `make test-security` **220 passed**; full suite **2045 passed,
  9 skipped, 8 deselected**.
  **Previous phase: W19 — Live-Run Kök Neden: Dropout + Harness
  Verification — closed synthetically `2026-05-26` on the `week19`
  branch (per user direction 2026-05-21; W11-W18 paterni preserved);
  PR #28 `week19 -> main` MERGED `2026-05-26` via `c879603`**: plan
  `documents/REFACTOR_OPTIMIZATION.md` §17, frozen tracker
  `documents/active-work/W19-live-run-root-cause.md`. **W19-0..W19-6
  + W19-X all closed**: W19-0 doc-reconcile
  (`72712bd` + `086d7a5`); W19-1
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
  pre-merge hygiene (`800c69f`). Driving signal: Codex live-run validation of
  `ms-python.python` @ `992ad028f3df` (2026-05-21) reported
  `automation_health.status=degraded` + `run_quality=low` while
  W19-2 live re-anchor satisfies `unaccounted_dropout == 0`.
  Hat-1 + Hat-2 fully closed; Hat-3 coverage matrix promotion deferred to
  W20-W22 per multi-iter roadmap. Final W19 bar:
  `tests/architecture/` **204 passed**; `make test-security` **220
  passed**; full suite **1995 passed, 9 skipped, 8 deselected**.
  **Previous phase: W18 — Heartbeat Refactor — closed via PR #26
  `week18 -> main` MERGED `2026-05-21` via `9874e79` (per user
  direction; W11-W17 paterni preserved)**: §16 W18 plan source,
  frozen tracker `documents/active-work/W18-heartbeat-refactor.md`.
  W18-0..W18-4 sub-iter slate + W18-4-followup fully delivered;
  final W18 bar: `tests/architecture/` **201 passed**;
  `make test-security` **220 passed**; full suite **1907 passed,
  9 skipped, 8 deselected**. **W17 closed via PR #25
  `week17 -> main` MERGED `2026-05-18` via `bff565d`** (W17-0..W17-7
  full audit trail in frozen tracker
  `documents/active-work/W17-carryover-and-lifecycle-harness.md`;
  W17-3/W17-4 DESIGN-NEEDED heartbeat thread relocation deferral
  closed via W18-1 ADR + W18-2 implementation). **W16 closed via
  PR #23 `week16 -> main` MERGED `2026-05-18` via `1b6d43f`** —
  Carry-Over Closeout + Audit Findings + Production Regression
  (W16-0..W16-7 audit trail in frozen tracker
  `documents/active-work/W16-regression-and-audit-closeout.md`).
  Past W8/W11/W12/W13/W14/W15/W16/W17/W18 trackers remain stable-ID
  references only.
- ADR 0007 local-network-binding is **Accepted and implemented**; loopback
  defaults + `EXTRACE_ALLOW_LAN` are pinned by `test_default_bindings.py`.

## Non-Negotiable Rules

- Preserve the unique constraint `(publisher, name, version)`.
- Route database writes through `appcore/storage/crud.py`; thin compatibility
  wrappers may delegate immediately but must not own write logic.
- Validate with Pydantic before database insertion.
- Use SQLAlchemy 2.0 syntax only.
- Use Pydantic v2 APIs only.
- Add an Alembic migration for schema changes.
- Keep sandbox execution isolated in Docker.
- Do not introduce dependencies without explicit approval.
- Do not add generic `try/except Exception` blocks.
- Do not introduce unsafe behavior: no arbitrary exec, unsafe deserialization,
  or uncontrolled network calls.
- Treat extension input, reports, logs, and VSIX contents as adversarial.
- Keep critical operations observable through logs, report fields, traces, or
  metrics.

## Architecture Boundaries

- Runtime entrypoint: `main.py`.
- Canonical backend code: `appcore/`, `workflows/`, `executor/`.
- Canonical frontend code: `ui/`.
- Framework-agnostic analysis code: `packages/`.
- Tests live under `tests/`; UI tests live under `ui/src/**/*.test.ts(x)`.
- `packages/` must not import `workflows/`, `executor/`, `ui/`, or
  `appcore/`.
- Detection rules live in `packages/analysis_engine/rules/` and may only
  consume contracts.
- Workflows reach sandbox mechanics through `executor.control`.
- Do not recreate legacy top-level business directories such as `routers/`,
  `scanner/`, `core/`, `database/`, `crud/`, `models/`, or `schemas/`.

## Read Path

1. Read this file.
2. Read `documents/AGENT_CONTEXT.md`.
3. Read exactly one matching lane doc under `documents/agent-lanes/`.
4. **Read subsystem docs only when the lane doc explicitly points to
   them. Default preload is forbidden.** Slim canonical subsystem
   docs (`ARCHITECTURE.md`, `PROJECT_STRUCTURE.md`, `TESTING.md`,
   `DETECTION_SEMANTICS.md`, `EXECUTOR_PLAYWRIGHT.md`) link out to
   subdir splits — open the split, not the canonical, for detail.
5. Read `documents/active-work/<file>.md` only when the lane doc
   points to it (e.g. W8 work goes through `active-work/W8-security.md`).
6. Read matching tests early; they usually reveal expected behavior faster
   than broad source scans.
7. Do **not** read `documents/archive/`. Archive is frozen historical
   reference; open it only when a slim canonical doc explicitly says
   "details: archive/...".

## Context Budget

- Do not scan the whole repository by default.
- Start from one task lane and expand only when evidence requires it.
- Ignore heavy/generated trees unless the task explicitly targets them:
  `extensions/`, `output/`, `node_modules/`, `ui/dist/`, `__pycache__/`,
  `.venv/`, `.mypy_cache/`, `.ruff_cache/`.
- Do not preload all of `documents/`.
- Prefer `rg` / `rg --files` for search.

## Common Commands

`make install-dev`, `make dev`, `make test-local`, `make check-all`,
`make migrate`, `make test-security`, `make exec-up`, `make exec-run`,
`make ui-up`, `make sim-target TARGET=publisher.name`, `make sim-all`,
`make demo-canary`, `make demo-canary-offline`.

## Required Self-Review

State briefly:

- Files modified
- DB schema changed: Yes/No
- Tests added/updated: Yes/No
- Risks or assumptions
