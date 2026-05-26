# Active Work

`Last Updated: 2026-05-26 (W20 closed synthetically 2026-05-27 via this commit — W20-0 doc-reconcile (66a8a0b + 5f13757), W20-1 scm official-track promotion (82276cb + a17e595), W20-2 settings official-track promotion (a4343d2 + 7406588), W20-3 coverage matrix contract invariants (d4c03b6 + 2e39230), W20-4 comments+testing readiness DESIGN doc (05f47f3 + b409894), W20-5 close-out hygiene (4665d32 primary + 95b0010 self-stamp; followup-2 d163b02 filed [FOLLOWUP sandbox-reset-stale-state-multi-analyze] for W21) delivered on the week20 branch; PR week20 -> main PENDING USER APPROVAL — open week20 branch (per user direction; W11-W19 paterni preserved) + new W20 active-work tracker documents/active-work/W20-coverage-promotion-easy-wins.md + §18 W20 plan header doc-open in REFACTOR_OPTIMIZATION.md split from the combined §18-§20 header (W19-0 paterni §17 split from §17-§20) + W20 Pull-Forward Acceptance Bar promoted in POST_POC_BACKLOG.md (from W20-W22 Roadmap Acceptance Bar now W21-W22 Roadmap Acceptance Bar planning) + 9-doc canonical preamble refresh + README phase-pointer arch gate transition W19→W20 (test_readme_phase_pointer.py tracks_active_w20_status + new test_readme_phase_pointer_mentions_w19_closeout_merge pinning PR #28 / week19 -> main / c879603 mirroring W18-0 / W19-0 transition paterni); baseline live-run captured via W20-0 self-stamp (anchor activation_report_ms-python.python-2026.5.2026052501-e89a82ca9ba8.json sha256 4dd788268f7793143351721875d6ccb340bd1e01b2b0205c53a5561ed0256ffe; W19 close-out Hat-1 + Hat-2 live-verified — unaccounted_dropout 0 + harness_verification_unconfirmed_present reason DROPPED). W20 driving signal (same as W19): Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities = [scm, settings, chat, comments, testing, workspace_trust]; W20 easy-wins tier closes scm + settings (heuristic-covered at capabilities.py:36,38; _OFFICIAL_CAPABILITY_SUPPORT missing at :88,90 — single-character flips at W20-1 + W20-2); W21 mid tier; W22 hard tier + sandbox evasion ADR. §18 W20 plan source (active) + §19-§20 W21-W22 planning roadmap (split at W20-0 from W19-0 era §18-§20 combined header). W20-0..W20-5 sub-iter slate: W20-0 doc-reconcile (this commit) + W20-1 [GOAL taxonomy-scm-official-promotion] + W20-2 [GOAL taxonomy-settings-official-promotion] + W20-3 [GOAL coverage-matrix-contract-tests] + W20-4 [DESIGN taxonomy-comments-testing-readiness] + W20-5 close-out hygiene + PR week20 -> main PENDING USER APPROVAL. W19 fully closed synthetically — Hat-1 closed + live-verified; Hat-2 fully closed via W19-3 schema landing + W19-4 producer/consumer wire (7d44b0e) + W19-X live-verification close-out (8b7b7f6 + a3e634f) + W19-5 onTerminal+onLM log_record stamp (e537ebd + 4fd6ed6) — all closed on the week19 branch (per user direction; W11-W18 paterni preserved). W19-0 doc-reconcile 2026-05-21 (72712bd + 086d7a5); W19-1 RED dropout regression fixture 2026-05-25 (6a21cf3 + fd02ca4); W19-2 emit-site fix 2026-05-25 (89b64da + d9c6262) — passes.py covered-only branch emits covered_via_layered_attempts; W19-2-followup-2 live re-anchor d5de9ca — Hat-1 GREEN gate SATISFIED 2026-05-25 22:23 (live JSON c2bf28ca9506, sha256 e9e60b2e42..., unaccounted_dropout count = 0); W19-3 schema landing 2026-05-25 (primary d2e83e7 + self-stamp 39121e4) — confirmation_source: str = "none" field landed on EventAttemptRecord (Pydantic + executor dataclass + UI adapter), str + field_validator typing mirroring status pattern, 22 new tests, frozen trigger fixture regenerated via planner replay; post-W19-3 live run 2026-05-25 23:27 (86e0f3646ce9) confirms field landed at "none" on 21/21 event_attempts with no behavior regression. W19-4 onDebug* nonce confirmation + consumer wire closed via 7d44b0e (producer at reconciliation.py:347-348 + consumer wire at reconciliation.py:85-90 + 7 new tests at test_playwright_health_reconciliation.py:813-1090). W19-X live-verification close-out via 8b7b7f6 + a3e634f — closes 3 pre-existing bug classes surfaced by first post-W19-4 live UI analyze: Bug A planner routing, Bug B marker channel destination, Bug C HMAC secret reactivation race; +15 new behavioral tests; live anchor 8247e05ec9ef.json shows 2/2 onDebug* stamped with harness_verification_unconfirmed suppressed on those attempts (Half B confirmed). W19-5 closed via primary e537ebd + self-stamp 4fd6ed6 (onTerminal+onLM log_record stamp); W19-6 close-out hygiene via f17b4b1 + cd82153; W19-6-followup-2 pre-merge hygiene this commit — closes 6 test gaps (+20 parametrized tests) + corrects stale W19 preamble drift across the 9-doc canonical set + freezes W19 tracker; Hat-3 deferred to W20-W22. W19 frozen tracker: W19-live-run-root-cause.md (frozen at W19-6-followup-2 per W17/W18 paterni). W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; W18 frozen tracker: W18-heartbeat-refactor.md. Final W19 test bar: tests/architecture/ 204 passed; make test-security 220 passed; full suite 1995 passed, 9 skipped, 8 deselected.)`

Slim canonical files for **active engineering work tracking**. Each file is
a stable contract: code comments and tests reference items here by stable
ID. Do not renumber or restructure items without updating inbound code/test
references.

## Distinction From Other Doc Types

- `archive/` — frozen historical content; not on default read path.
- `documents/REFACTOR_OPTIMIZATION.md` — planning narrative (slim canonical).
- `documents/POST_POC_BACKLOG.md` — deferred + pull-next list (open items).
- **`active-work/` — currently-in-flight work tracker with stable item IDs.**

Open a file here only when the lane doc or AGENT_CONTEXT.md decision tree
points to it.

## Files

- `W19-live-run-root-cause.md`
  - **Frozen phase — W19-0..W19-6 + W19-X all closed on the
    `week19` branch per user direction; W11-W18 paterni preserved;
    PR #28 `week19 -> main` MERGED `2026-05-26` via `c879603`.**
    W19 Live-Run Kök Neden: Dropout + Harness Verification. Hat-1
    closed + live-verified; Hat-2 fully closed synthetically.
    Audit trail: W19-0 doc-reconcile (`72712bd` + `086d7a5`),
    W19-1 RED dropout fixture (`6a21cf3` + `fd02ca4`), W19-2 emit-site
    fix (`89b64da` + `d9c6262`) + live re-anchor `d5de9ca` satisfying
    `unaccounted_dropout == 0`; W19-3 harness verification contract
    event-level schema landing
    `[GOAL harness-verification-contract-event-level]`;
    onDebug* nonce confirmation
    `[FOLLOWUP harness-verification-debug-events]` (W19-4);
    onTerminal + onLM local-only confirmation
    `[FOLLOWUP harness-verification-terminal-and-lm-tool]` (W19-5);
    close-out hygiene + PR `week19 -> main` (W19-6). Driving signal:
    Codex live-run validation `2026-05-21` of `ms-python.python` @
    `992ad028f3df` reports `automation_health.status=degraded` +
    `run_quality=low`; W19-2 live re-anchor now satisfies
    `unaccounted_dropout == 0`. Hat-1 + Hat-2 fully closed; Hat-3
    (coverage matrix promotion) deferred to W20-W22 per multi-iter
    roadmap. Final W19 bar: tests/architecture/ 204 / make
    test-security 220 / full suite 1995 passed, 9 skipped, 8
    deselected. Slim canonical:
    [`REFACTOR_OPTIMIZATION.md §17`](../REFACTOR_OPTIMIZATION.md).
- `W18-heartbeat-refactor.md`
  - **Past phase — closed `2026-05-21` and merged via PR #26
    `week18 -> main` on `2026-05-21` via `9874e79`** (W18-0..W18-4
    sub-iter slate + W18-4-followup post-merge audit landed; final
    W18 bar `tests/architecture/` **201 passed**; `make test-security`
    **220 passed**; full suite **1907 passed, 9 skipped,
    8 deselected**). W18 Heartbeat Refactor: 5 sub-iter slate
    (`W18-0..W18-4`) + W18-4-followup. Retained on the read path
    because code comments + tests reference items by `W18-<n>` ID
    — do not renumber. Slim canonical:
    [`REFACTOR_OPTIMIZATION.md §16`](../REFACTOR_OPTIMIZATION.md).
- `W18-W22-roadmap.md`
  - **Multi-iter roadmap source-of-truth (planning state for
    W20-W22; W18 + W19 closed).** Authored `2026-05-21` per
    user direction; carries the dropout fix (Hat-1) + harness
    verification (Hat-2) + coverage matrix promotion (Hat-3) plan
    across W18-W22. Slim canonical:
    [`REFACTOR_OPTIMIZATION.md §16 + §17 + §18-§20`](../REFACTOR_OPTIMIZATION.md).
- `W15-codex-uclass-bounds-posture.md`
  - **Past phase — W15-1..W15-7 closed `2026-05-17`; merged via
    PR #22 `week15 -> main` on `2026-05-18` via `6161472`.** W15
    Codex U-class Close-Out + UI Bounds + Posture. 7 sub-iter slate
    (`W15-1..W15-7`): sync analyze error taxonomy alignment
    (M10 via `c58c365`), workspace symlink check order / orphan
    removal (M12 via `765cde7`), `activationEvents` bounds + DB
    field-length Alembic migration (U8 via `3512a7c`), UI bounds
    bundle (U1-U3 + U6 via `89e13e3`), quick fixes bundle
    (I2 + I4 via `43d6438`), unauthenticated catalog endpoints
    posture (ADR 0011 — U10-U11 via `be52520`, Proposed at
    `e41722e`), regression lock-in umbrella (compose image SHA pin
    via `54e7a93` + test extension via `7ebbbfb` +
    `aquasecurity/trivy-action@v0.36.0` via `452f1a1` + canonical
    preamble truth-state refresh via close-out docs commit; W15-7
    early pulls `a7a876e` + `2573e35`; close-out hygiene `7ff31d9`).
    W15-1 post-slate typing hotfix `976dc96`. W15 mid-iter hygiene
    `878da2c` added cross-doc preamble consistency arch gate.
    `week15` cut from `main` at HEAD `7cc2921` on `2026-05-14`
    (W14 close-out merge `4e03c8d` + the W15 scope-skeleton commit
    `7cc2921` carrying this tracker). `tests/architecture/` 171
    baseline → 198 final (+17 sub-iter + 2 mid-iter hygiene + 8
    W15-7 early-pull regression cases on extension paths).
    Retained on the read path for stable-ID references (code
    comments + tests reference items by `W15-<n>` ID — do not
    renumber). Slim canonical:
    [`REFACTOR_OPTIMIZATION.md §13`](../REFACTOR_OPTIMIZATION.md).
- `W14-codex-acceptance-observability.md`
  - **Past phase — closed `2026-05-13` (W14-1..W14-6 closed + W14-7/W14-8
    post-slate hotfixes closed) and merged via close-out PR #21
    `week14 -> main` on `2026-05-14` via `4e03c8d`.** W14 Codex M-class
    Acceptance + Observability. 6 sub-iter scoped
    (`W14-1..W14-6`): BLOCKER scenario-dropout araştırması, Codex
    M-class input validation (M4-M7 + M11), dış yüzey sertleştirme
    (M13 + M14b + U4-U12), correctness/concurrency (analysis-jobs-race
    - evidence-event-kind invariant), §11.10 GOAL devamı (logger
    consolidation + run-ID stamping + codex-automation-5 fingerprint),
    W8-W12 regression lock-in umbrella. Plus post-slate hotfixes:
    `W14-7` (container-shipping regression + Python 3.10 UTC compat),
    `W14-8` (preventive AST gate forbidding Python 3.11+ API imports in
    container-shipped paths). Branch cut completed `2026-05-13` at
    `69251f1`; W14-1..W14-8 stable ID'leri pull sırasında atandı
    (W11/W12/W13 precedent). Retained on the read path because code
    comments reference items by `W14-<n>` ID — do not renumber. Slim
    canonical: [`REFACTOR_OPTIMIZATION.md §12`](../REFACTOR_OPTIMIZATION.md).
- `W13-test-expansion-observability.md`
  - **Past phase — closed `2026-05-13` (W13-1..W13-13 all GREEN).** W13
    test expansion + observability. W13-1..W13-7 closed — every
    MEDIUM/HIGH Codex Cloud audit acceptance-bar item (H3 via W13-5,
    H4 via W13-3, H5 via W13-2, H6 via W13-1, M1 via W13-7, M9 via
    W13-6) landed. §11.10 GOAL pulls: W13-8 closed (benign silence
    fixture 3→5 GREEN, 5/5 ✓), W13-9 closed (`.env` gitignore
    architecture gate 10/10 ✓), W13-10 closed (singleton-lock recovery
    integration test 2/2 ✓). **CLOSE-GATE `2026-05-11`** — Codex Cloud
    second-opinion review surfaced 3 P1 close-pass items: W13-11 HMAC
    python secret target-install race **closed `2026-05-12`**, W13-12
    fail-closed harness handshake **closed `2026-05-12`**, W13-13
    worker-start cancel-race CAS **closed `2026-05-13`** (Path B
    worker-entry `with_for_update()` snapshot lock + 4 post-landing
    behavioral pins; F4 README sweep + regex pin landed early in W13-11
    push). Close-out PR `week13 -> main` **MERGED** `2026-05-13`
    via `772deb3`. Original §11.10
    TBD umbrellas (logger consolidation, run-ID stamping, W8-W12
    regression lock-in) deferred to W14 — see W14 tracker above.
    Retained on the read path because code comments reference items
    by `W13-<n>` ID — do not renumber.
- `W12-executor-subpackaging.md`
  - **Past phase.** W12 executor subpackaging + attribution cleanup
    (W12-0..W12-5) closed `2026-05-10` and merged via PR #18.
    Retained for stable-ID references; do not renumber.
- `W11-monitor-lifecycle.md`
  - **Past phase.** W11 monitor lifecycle split (W11-1..W11-8) closed
    `2026-05-05`, formerly `REFACTOR_OPTIMIZATION.md §11.8`. Retained
    on the read path because code comments reference items by
    `W11-<n>` ID — do not renumber.
- `W8-security.md`
  - W8 security hardening checklist (W8-1..W8-7), formerly
    `REFACTOR_OPTIMIZATION.md §11.5`. Closed for active work
    `2026-04-29` (W8-1..W8-7 + W8-9 landed, W8-8 deferred). Kept on
    the read path because code comments reference items by
    `W8-<n>` ID — do not renumber.
