# AGENTS.md

`Last Updated: 2026-05-26 (Active phase: W20 — W20 closed synthetically 2026-05-27 via this commit — W20-0 doc-reconcile (66a8a0b + 5f13757), W20-1 scm official-track promotion (82276cb + a17e595), W20-2 settings official-track promotion (a4343d2 + 7406588), W20-3 coverage matrix contract invariants (d4c03b6 + 2e39230), W20-4 comments+testing readiness DESIGN doc (05f47f3 + b409894), W20-5 close-out hygiene (this commit) delivered on the week20 branch; PR week20 -> main PENDING USER APPROVAL — open week20 branch (per user direction; W11-W19 paterni preserved) + new active-work tracker for W20 documents/active-work/W20-coverage-promotion-easy-wins.md + §18 W20 plan header doc-open in REFACTOR_OPTIMIZATION.md split from the combined §18-§20 header (W19-0 paterni §17 split from §17-§20) + W20 Pull-Forward Acceptance Bar promoted in POST_POC_BACKLOG.md (from W20-W22 Roadmap Acceptance Bar now W21-W22 Roadmap Acceptance Bar planning) + 9-doc canonical preamble refresh + README phase-pointer arch gate transition W19→W20 (test_readme_phase_pointer.py tracks_active_w20_status + new test_readme_phase_pointer_mentions_w19_closeout_merge pinning PR #28 / week19 -> main / c879603 mirroring W18-0 / W19-0 transition paterni); baseline live-run captured via W20-0 self-stamp (anchor activation_report_ms-python.python-2026.5.2026052501-e89a82ca9ba8.json sha256 4dd788268f7793143351721875d6ccb340bd1e01b2b0205c53a5561ed0256ffe; W19 close-out Hat-1 + Hat-2 live-verified — unaccounted_dropout 0 + harness_verification_unconfirmed_present reason DROPPED). W20 driving signal (same as W19): Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities = [scm, settings, chat, comments, testing, workspace_trust]; W20 easy-wins tier closes scm + settings (heuristic-covered at capabilities.py:36,38; _OFFICIAL_CAPABILITY_SUPPORT missing at :88,90 — single-character flips at W20-1 + W20-2); W21 mid tier; W22 hard tier + sandbox evasion ADR. §18 W20 plan source (active) + §19-§20 W21-W22 planning roadmap (split at W20-0 from W19-0 era §18-§20 combined header). W20-0..W20-5 sub-iter slate: W20-0 doc-reconcile (this commit) + W20-1 [GOAL taxonomy-scm-official-promotion] + W20-2 [GOAL taxonomy-settings-official-promotion] + W20-3 [GOAL coverage-matrix-contract-tests] + W20-4 [DESIGN taxonomy-comments-testing-readiness] + W20-5 close-out hygiene + PR week20 -> main PENDING USER APPROVAL. W19 closed and merged — Hat-1 closed + live-verified via W19-2-followup-2 d5de9ca; Hat-2 HARD GATE W19-3 closed via primary d2e83e7 + self-stamp 39121e4 + 8-doc preamble refresh 9b56e94; W19-4 closed via 7d44b0e + W19-X live-verification close-out via 8b7b7f6 (W19-X primary) + a3e634f (W19-X self-stamp) — closes Bug A planner routing / Bug B marker channel destination / Bug C HMAC secret reactivation race; +15 new behavioral tests; live anchor 8247e05ec9ef.json: 2/2 onDebug* stamped; W19-5 closed via e537ebd + 4fd6ed6; W19-6 close-out hygiene via f17b4b1 + cd82153; W19-6-followup-2 pre-merge hygiene (this commit) closes 6 test gaps (+20 parametrized tests) + corrects stale W19 preamble drift across the 9-doc canonical set + freezes W19 tracker per W17/W18 paterni; final W19 test bar 1995/9/8 (tests/architecture/ 204 / make test-security 220 / full suite 1995 passed) on the week19 branch (per user direction 2026-05-21; W11-W18 paterni preserved); W19-0..W19-6 + W19-X closed on the week19 branch; merged to main via PR #28 2026-05-26 via c879603; live smoke pending; stable IDs W19-1..W19-5 closed at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar. Driving signal: Codex live-run validation 2026-05-21 of ms-python.python @ 992ad028f3df reports automation_health.status=degraded + run_quality=low while W19-2 live re-anchor now satisfies unaccounted_dropout == 0 and static W18 final bar (1907/201/220) remains green; post-W19-3 live run 2026-05-25 23:27 (86e0f3646ce9) confirms field landed at "none" on 21/21 event_attempts with no behavior regression. W19 Hat-1 closed + live-verified (executor muhasebe bug → unaccounted_dropout); Hat-2 fully closed (W19-3 schema landing + W19-4 onDebug* producer/consumer + W19-X onDebug* live close-out + W19-5 onTerminal+onLM log_record stamp; entire harness_verification_unconfirmed_present driver synthetically closed; W19-6 close-out hygiene landed via primary f17b4b1 + self-stamp this commit) (onDebug* harness_nonce producer at health/reconciliation.py:347-348 + consumer wire gating failure_reason_code on confirmation_source at reconciliation.py:85-90 + 7 new tests at test_playwright_health_reconciliation.py:813-1090); W19-5 closed via primary e537ebd + self-stamp 4fd6ed6 (onTerminal+onLM log_record stamp at reconciliation.py:347-365 sibling elif to W19-4 onDebug arm); Hat-3 (coverage matrix promotion) deferred to W20-W22. §17 W19 plan source + §18-§20 W20-W22 multi-iter roadmap (split at W19-0 from the original §17-§20 combined header). W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; final W18 bar tests/architecture/ 201 / make test-security 220 / full suite 1907 passed, 9 skipped, 8 deselected. W18 sub-iter audit trail (frozen, all closed): W18-0 (89d0c9b); W18-1 ADR 0012 Option A1 (acf6cc9 + 73d8a5c); W18-2 heartbeat refactor implementation (a9bffb1 + 78ed7cc + b5b64b6 + 306d744); W18-3 lifecycle harness extension tests (92b310d + 32d9905); W18-4 close-out hygiene (3f4f95a); W18-4-followup (e1043e5). W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md; W19 frozen tracker: documents/active-work/W19-live-run-root-cause.md (frozen at W19-6-followup-2 per W17/W18 paterni); multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md (5-iter slate: W18 closed / W19 dropout + harness verification CLOSED / W20 coverage promotion easy / W21 coverage promotion mid / W22 chat policy + sandbox ADR). W15 closed via PR #22 MERGED 2026-05-18 via 6161472; W14 closed via PR #21 MERGED 2026-05-14 via 4e03c8d; W13 closed via PR #20 -> 772deb3 on 2026-05-13)`

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
