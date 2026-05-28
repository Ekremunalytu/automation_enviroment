# Active Work

`Last Updated: 2026-05-28 (Active phase: W21 — W21-4 [GOAL container-hardening-baseline] closed via primary 16e2224 + followup-1 2f9cba2 + self-stamp this commit (W21-0 doc-reconcile closed 8434323 + 19bd9c7 + W21-3 closed c744c15 + 4b0a1ed + W21-1 closed 7e87030 + 38b8fd8 + W21-2 [GOAL taxonomy-comments-coverage] closed 8948ea6 + 3088709 before W21-4). W21-4 primary landed docker-compose.yml cap_drop:[ALL] + security_opt:[no-new-privileges:true] on executor/api/ui + ADR 0013 documenting decision + deferred items (read_only + tmpfs + custom seccomp profile → W22 ratchet-down lane) + 12 invariant tests at tests/architecture/test_compose_isolation_invariants.py. W21-4-followup-1 (2f9cba2) restored cap_add SETUID + SETGID on api (gosu user drop) + SETUID + SETGID + CHOWN + DAC_OVERRIDE on ui (nginx cache chown + worker drop) — both surfaced during the primary live-run smoke. executor cap_add NET_RAW + SYS_PTRACE preserved from pre-W21-4 for tcpdump/tshark/strace observability tools. W21-4 live-run anchor activation_report_ms-python.python-2026.5.2026052501-eacea0b6690e.json sha256 5d7c8b974f21e3bf4ad679a41551dd3e7b71d37573f5e7f2b28b87d2ad4a6a84 confirms NO coverage regression vs W21-2 anchor 1ddb3702c0ca (must-pass ✓): coverage_summary.missing_capabilities = [chat] (1 item, byte-identical with W21-2); covered/partial/missing = 8/9/1 (byte-identical); automation_health.status=degraded with 3 reasons (skipped_scenarios_present, verification_gap_present, official_unresolved_present — same shape as W21-2); W20 invariants HOLD post-W21-4 (Hat-1 unaccounted_dropout_count=null; Hat-2 harness_verification_unconfirmed_present DROPPED). Manual kernel-level smoke (docker exec into the executor + grep /proc/self/status for NoNewPrivs) returns NoNewPrivs=1 confirming PR_SET_NO_NEW_PRIVS active at the kernel. W21-2 [GOAL taxonomy-comments-coverage] closed via 8948ea6 + 3088709 before W21-4 hit comments official-track promotion missing → covered + harness CommentController + scenario + 4 invariants + fixture regen, dropping missing_capabilities 2 → 1 [chat]. W21-2 primary landed _OFFICIAL_CAPABILITY_SUPPORT["comments"]: "missing" → "covered" at capabilities.py:96 + mirror in _GLOBAL_CAPABILITY_SUPPORT:44 (heuristic derives) + harness CommentController baseline marker emitted at activate() entry + ensureCommentThread (stimulus_dispatch.js) extended to emit thread_created + thread_disposed markers via emitHarnessEvent through reserved OutputChannel route (W19-X Bug B paterni) with ephemeral thread default (W19-X HMAC reactivation race lesson — created+disposed in-call) + local_comments_controller scenario in scenarios.py advertising comments (mirror W21-3 workspace_trust_transition + W21-1 local_test_controller shape) + 4 invariant tests at tests/platform/contracts/test_capability_support_invariants.py + dict shape canonical pin update + test_split_did_not_lose_data_volume count bump 15→16 + frozen trigger fixture regen for ms-python.python. Runtime stimulus pass implicit — ensureCommentThread already invoked from the existing extrace.harness.runCurrentStimulus command handler, so any stimulus pass exercises the new markers without dedicated pass. Opens week21 branch (per user direction 2026-05-27; W11-W20 paterni preserved — sub-iter commits land on week21, close-out merges via week21 -> main PR PENDING USER APPROVAL). Active W21 tracker documents/active-work/W21-coverage-promotion-mid-tier.md. §19 W21 plan header doc-open in REFACTOR_OPTIMIZATION.md split at W21-0 from §19-§20 W21-W22 planning combined header (W19-0 / W20-0 paterni mirror). W21 Pull-Forward Acceptance Bar promoted in POST_POC_BACKLOG.md at W21-0 (now W22 Roadmap Acceptance Bar planning for the residual W22 lane). 10-doc canonical preamble refresh at W21-0 + W21-3 + W21-1 + W21-2 self-stamps (this commit). README phase-pointer arch gate transition W20→W21 at W21-0 (test_readme_phase_pointer.py tracks_active_w21_status + W20 close-out merge gate test pinning PR #29 / week20 -> main / 64a3c3d). W21-0 baseline anchor 600d9ecba5eb sha256 1db1480551fd...c4477; W21-3 anchor 6fd7b959bd5a sha256 fa83017a...d6f7477 confirmed workspace_trust dropped (4→3); W21-1 anchor 0b4998ce31b4 sha256 b7192bc2ff9c...968be4 confirmed testing dropped (3→2). W21-2 live-run anchor activation_report_ms-python.python-2026.5.2026052501-1ddb3702c0ca.json sha256 2dabd15be329bbf1685fe7fc31469355bdc4a5acac2a364d43a196437339cbff confirms W21-2 acceptance — coverage_summary.missing_capabilities 2 → 1 items [chat] (comments dropped — must-pass ✓; W21 mid-tier closure target hit — only chat remains for W22 hard tier), covered/partial/missing 8/8/2 → 8/9/1, comments matrix entry status "partial" support_status "covered" supported_scenarios ["local_comments_controller"]. W20 invariants HOLD post-W21-2 (Hat-1 dropout=null; Hat-2 harness_verification_unconfirmed_present DROPPED). W21-2 live-run drift clean (same shape as W21-1): only 3 reasons remain (skipped_scenarios_present, verification_gap_present, official_unresolved_present). W20 closed and merged via PR #29 week20 -> main MERGED 2026-05-26 via 64a3c3d; final W20 bar tests/architecture/ 240 passed / make test-security 220 passed / full suite 2045 passed, 9 skipped, 8 deselected. W21-3 test bar delta: contracts/test_capability_support_invariants.py 14 → 18 (+4); full suite 2045 → 2050 (+5 net). W21-1 test bar delta: contracts/test_capability_support_invariants.py 18 → 22 (+4); full suite 2050 → 2054 (+4 net). W21-2 test bar delta: tests/architecture/ 241 passed (unchanged from W21-1), tests/platform/contracts/test_capability_support_invariants.py 22 → 26 passed (+4 W21-2 invariants), tests/platform/contracts/test_registry_split_regression.py 8 passed (count pin 15 → 16), tests/workflows/marketplace/test_analysis_planner.py fixture parity green, make test-security 220 passed (unchanged), full suite 2054 → 2058 passed, 9 skipped, 8 deselected (+4 net W21-2 invariants). W21 driving signal (carried over from W19 / W20): same Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities started at [scm, settings, chat, comments, testing, workspace_trust]; W20-5 confirmed missing dropped 6 → 4 [chat, comments, testing, workspace_trust]; W21-3 dropped workspace_trust (4 → 3 [chat, comments, testing]); W21-1 dropped testing (3 → 2 [chat, comments]); W21-2 dropped comments (2 → 1 [chat]); W22 closes hard tier (chat) + sandbox evasion ADR draft. §19 W21 plan source (active) + §20 W22 planning. W21 sub-iter slate: W21-0 doc-reconcile closed (8434323 + 19bd9c7) + W21-3 [GOAL taxonomy-workspace-trust-coverage] closed (c744c15 + 4b0a1ed) + W21-1 [GOAL taxonomy-testing-coverage] closed (7e87030 + 38b8fd8) + W21-2 [GOAL taxonomy-comments-coverage] closed via 8948ea6 + this commit + W21-4 [GOAL container-hardening-baseline] STRETCH (user-pulled into W21 2026-05-27; final pull/defer decision pending after this commit) + W21-N close-out hygiene + PR week21 -> main PENDING USER APPROVAL. [FOLLOWUP sandbox-reset-stale-state-multi-analyze] (filed d163b02 at W20-5-followup-2) opportunistic at W21-N close-out window (user-confirmed); not a sub-iter, not a blocker. [FOLLOWUP workspace-trust-stimulus-pass] (filed c744c15 + 4b0a1ed) W22 candidate — runtime untrusted → granted transition exercise; needs fixture restructuring. W19 closed and merged via PR #28 week19 -> main MERGED 2026-05-26 via c879603; W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f; W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 closed via PR #20 week13 -> main MERGED 2026-05-13 via 772deb3. W20 frozen tracker: documents/active-work/W20-coverage-promotion-easy-wins.md (frozen at W20-5 + followups per W17/W18/W19 paterni); W19 frozen tracker: documents/active-work/W19-live-run-root-cause.md (frozen at W19-6-followup-2); W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md; W21 active tracker: documents/active-work/W21-coverage-promotion-mid-tier.md; multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md.)`

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

- `W20-coverage-promotion-easy-wins.md`
  - **Frozen phase — W20-0..W20-5 all closed on the `week20`
    branch per user direction `2026-05-26`; W11-W19 paterni
    preserved; close-out PR `week20 -> main` PENDING USER
    APPROVAL.** W20 Coverage Promotion Round 1: Easy Wins (Hat-3
    coverage matrix promotion easy tier). Audit trail: W20-0
    doc-reconcile (`66a8a0b` + `5f13757`), W20-1
    `[GOAL taxonomy-scm-official-promotion]` (`82276cb` +
    `a17e595`) at `packages/analysis_planner/capabilities.py:88`,
    W20-2 `[GOAL taxonomy-settings-official-promotion]`
    (`a4343d2` + `7406588`) at `capabilities.py:90`, W20-3
    `[GOAL coverage-matrix-contract-tests]` (`d4c03b6` +
    `2e39230`), W20-4
    `[DESIGN taxonomy-comments-testing-readiness]` (`05f47f3` +
    `b409894`) at
    `documents/architecture/comments-testing-readiness.md`, W20-5
    close-out hygiene (`4665d32` primary + `95b0010` self-stamp
    + `d163b02` followup-2 + `ae5b7de` followup-3). Driving
    signal: same Codex live-run `2026-05-21` of
    `ms-python.python` @ `992ad028f3df` (W19 baseline). **W20
    acceptance LIVE-SATISFIED** on fresh run `4e92de149802`
    (sha256 `3804a5b5...4394c`): `coverage_summary.missing_capabilities`
    dropped 6 → 4 (lost `scm` + `settings`); W19 Hat-1
    + Hat-2 hold post-W20. Hat-3 mid + hard tiers (`testing`,
    `comments`, `workspace_trust`, `chat`) deferred to W21-W22
    per multi-iter roadmap. Final W20 bar: `tests/architecture/`
    **240 passed**, 4 deselected; `make test-security` **220
    passed**; full suite **2045 passed, 9 skipped, 8
    deselected**. Retained on the read path because code
    comments + tests reference items by `W20-<n>` ID — do not
    renumber. Slim canonical:
    [`REFACTOR_OPTIMIZATION.md §18`](../REFACTOR_OPTIMIZATION.md).
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
