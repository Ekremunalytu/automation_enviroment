# Agent Context

`Last Updated: 2026-05-26 (Active phase: W20 — W20 closed synthetically 2026-05-27 via this commit — W20-0 doc-reconcile (66a8a0b + 5f13757), W20-1 scm official-track promotion (82276cb + a17e595), W20-2 settings official-track promotion (a4343d2 + 7406588), W20-3 coverage matrix contract invariants (d4c03b6 + 2e39230), W20-4 comments+testing readiness DESIGN doc (05f47f3 + b409894), W20-5 close-out hygiene (this commit) delivered on the week20 branch; PR week20 -> main PENDING USER APPROVAL — open week20 branch (per user direction; W11-W19 paterni preserved) + new active-work tracker for W20 documents/active-work/W20-coverage-promotion-easy-wins.md + §18 W20 plan header doc-open in REFACTOR_OPTIMIZATION.md split from the combined §18-§20 header (W19-0 paterni §17 split from §17-§20) + W20 Pull-Forward Acceptance Bar promoted in POST_POC_BACKLOG.md (from W20-W22 Roadmap Acceptance Bar now W21-W22 Roadmap Acceptance Bar planning) + 9-doc canonical preamble refresh + README phase-pointer arch gate transition W19→W20 (test_readme_phase_pointer.py tracks_active_w20_status + new test_readme_phase_pointer_mentions_w19_closeout_merge pinning PR #28 / week19 -> main / c879603 mirroring W18-0 / W19-0 transition paterni); baseline live-run captured via W20-0 self-stamp (anchor activation_report_ms-python.python-2026.5.2026052501-e89a82ca9ba8.json sha256 4dd788268f7793143351721875d6ccb340bd1e01b2b0205c53a5561ed0256ffe; W19 close-out Hat-1 + Hat-2 live-verified — unaccounted_dropout 0 + harness_verification_unconfirmed_present reason DROPPED). W20 driving signal (same as W19): Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities = [scm, settings, chat, comments, testing, workspace_trust]; W20 easy-wins tier closes scm + settings (heuristic-covered at capabilities.py:36,38; _OFFICIAL_CAPABILITY_SUPPORT missing at :88,90 — single-character flips at W20-1 + W20-2); W21 mid tier; W22 hard tier + sandbox evasion ADR. §18 W20 plan source (active) + §19-§20 W21-W22 planning roadmap (split at W20-0 from W19-0 era §18-§20 combined header). W20-0..W20-5 sub-iter slate: W20-0 doc-reconcile (this commit) + W20-1 [GOAL taxonomy-scm-official-promotion] + W20-2 [GOAL taxonomy-settings-official-promotion] + W20-3 [GOAL coverage-matrix-contract-tests] + W20-4 [DESIGN taxonomy-comments-testing-readiness] + W20-5 close-out hygiene + PR week20 -> main PENDING USER APPROVAL. W19 closed and merged — Hat-1 closed + live-verified via W19-2-followup-2 d5de9ca; Hat-2 HARD GATE W19-3 closed via primary d2e83e7 + self-stamp 39121e4 + 8-doc preamble refresh 9b56e94; W19-4 closed via 7d44b0e + W19-X live-verification close-out via 8b7b7f6 (W19-X primary) + a3e634f (W19-X self-stamp) — closes Bug A planner routing / Bug B marker channel destination / Bug C HMAC secret reactivation race; +15 new behavioral tests; live anchor 8247e05ec9ef.json: 2/2 onDebug* stamped; W19-5 closed via e537ebd + 4fd6ed6; W19-6 close-out hygiene via f17b4b1 + cd82153; W19-6-followup-2 pre-merge hygiene (this commit) closes 6 test gaps (+20 parametrized tests) + corrects stale W19 preamble drift across the 9-doc canonical set + freezes W19 tracker per W17/W18 paterni; final W19 test bar 1995/9/8 (tests/architecture/ 204 / make test-security 220 / full suite 1995 passed) on the week19 branch (per user direction 2026-05-21; W11-W18 paterni preserved); W19-0..W19-6 + W19-X closed on the week19 branch; merged to main via PR #28 2026-05-26 via c879603; live smoke pending; stable IDs W19-1..W19-5 closed at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar. Driving signal: Codex live-run validation 2026-05-21 of ms-python.python @ 992ad028f3df reports automation_health.status=degraded + run_quality=low while W19-2 live re-anchor now satisfies unaccounted_dropout == 0 and static W18 final bar (1907/201/220) remains green; post-W19-3 live run 2026-05-25 23:27 (86e0f3646ce9) confirms field landed at "none" on 21/21 event_attempts with no behavior regression. W19 Hat-1 closed + live-verified (executor muhasebe bug → unaccounted_dropout); Hat-2 W19-3 schema landing + W19-4 onDebug* producer (confirmation_source="harness_nonce" stamp at health/reconciliation.py:347-348) + consumer wire (failure_reason_code gated on confirmation_source at reconciliation.py:85-90) + 7 new tests at test_playwright_health_reconciliation.py:813-1090 closed; W19-5 closed via primary e537ebd + self-stamp 4fd6ed6 (onTerminal+onLM log_record stamp); W19-6 close-out hygiene landed via primary f17b4b1 + this self-stamp; Hat-3 (coverage matrix promotion) deferred to W20-W22 per multi-iter roadmap. §17 W19 plan source + §18-§20 W20-W22 multi-iter roadmap (split at W19-0 from the original §17-§20 combined header). W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; final W18 bar tests/architecture/ 201 / make test-security 220 / full suite 1907 passed, 9 skipped, 8 deselected. W18 sub-iter audit trail (frozen, all closed): W18-0 (89d0c9b); W18-1 ADR 0012 Option A1 (acf6cc9 + 73d8a5c); W18-2 heartbeat refactor impl (a9bffb1 + 78ed7cc + b5b64b6 + 306d744); W18-3 lifecycle harness extension tests (92b310d + 32d9905); W18-4 close-out hygiene (3f4f95a); W18-4-followup (e1043e5). W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. Plan REFACTOR_OPTIMIZATION.md §17 (W19) + §18-§20 (W20-W22 multi-iter roadmap), W18 frozen tracker active-work/W18-heartbeat-refactor.md, W19 frozen tracker active-work/W19-live-run-root-cause.md (frozen at W19-6-followup-2 per W17/W18 paterni), roadmap source-of-truth active-work/W18-W22-roadmap.md. W15 closed via PR #22 MERGED 2026-05-18 via 6161472; W14 closed via PR #21 MERGED 2026-05-14 via 4e03c8d)`

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
  `REFACTOR_OPTIMIZATION.md` section 16; **W19 plan:
  `REFACTOR_OPTIMIZATION.md` section 17 (active);
  W20-W22 multi-iter roadmap:
  `REFACTOR_OPTIMIZATION.md` sections 18-20** (split at W19-0
  open from the original §17-§20 combined header;
  source-of-truth tracker `active-work/W18-W22-roadmap.md`;
  slim canonical; full text under `archive/plans/`).
- W8-W19 are closed; W13 merged via PR #20 (`772deb3`); W14 merged via
  PR #21 (`4e03c8d`); W15 merged via PR #22 (`6161472`) on
  `2026-05-18`; W16 merged via PR #23 (`1b6d43f`) on `2026-05-18`;
  W17 merged via PR #25 (`bff565d`) on `2026-05-18`;
  W18 merged via PR #26 (`9874e79`) on `2026-05-21`;
  **W19 merged via PR #28 (`c879603`) on `2026-05-26`**.
  Past W8/W11/W12/W13/W14/W15/W16/W17/W18/W19 trackers remain only
  for stable IDs referenced by code/tests. **Previous phase:** W19 —
  Live-Run Kök Neden: Dropout + Harness Verification (**closed
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
  deferred to W20-W22. **Previous phase:** W18 —
  Heartbeat Refactor (closed `2026-05-21` via PR #26
  `week18 -> main` MERGED via `9874e79`; W18-0..W18-4 sub-iter
  slate + W18-4-followup fully delivered; final W18 bar
  `tests/architecture/` **201 passed**; `make test-security`
  **220 passed**; full suite **1907 passed, 9 skipped,
  8 deselected**). W18 frozen tracker:
  `active-work/W18-heartbeat-refactor.md`; W19 frozen tracker:
  `active-work/W19-live-run-root-cause.md`; multi-iter roadmap
  source-of-truth: `active-work/W18-W22-roadmap.md`. For
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
