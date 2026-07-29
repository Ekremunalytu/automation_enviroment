# Active Work

`Last Updated: 2026-07-29`

`Last merged weekly: W22 — closed synthetically on the week22 branch, merged to main via PR #31 week22 -> main 2026-05-28 via 1399f82.`

`Latest merged named stream: verdict-provenance-reproducibility (Stream 3 — B5+B6; week label W26) — merged to main via PR #38 (week26 -> main, bfb2d2d) on 2026-07-27. No successor stream is open; next execution gate is containment safety. Tracker: documents/active-work/W26-verdict-provenance-reproducibility.md.`

`Sources of truth: documents/REFACTOR_STATUS.md (state) · documents/POST_POC_BACKLOG.md (deferred) · documents/REFACTOR_OPTIMIZATION.md §20 (last weekly plan) · documents/phase.json (weekly pointer + optional active stream; null when none is open).`

Slim canonical files for the forward roadmap, currently active engineering
work (when a stream is open), and recently closed trackers retained as stable
contracts. Code comments and tests reference items here by stable ID. Do not
renumber or restructure items without updating inbound code/test references.

## Distinction From Other Doc Types

- `archive/` — frozen historical content; not on default read path.
- `documents/REFACTOR_OPTIMIZATION.md` — planning narrative (slim canonical).
- `documents/POST_POC_BACKLOG.md` — deferred + pull-next list (open items).
- **`active-work/` — forward roadmap plus open or stable-ID-retained stream
  trackers.**

Open a file here only when the lane doc or AGENT_CONTEXT.md decision tree
points to it.

## Files

- `v1-roadmap.md`
  - **Forward roadmap — the v1.0 arc that turns ExTrace into a real,
    daily-usable single-operator defensive tool.** User direction
    `2026-06-08` after the project report was delivered. Supersedes the
    completed `W18-W22-roadmap.md` window. Carries the v1.0 bar (B1-B10),
    the 11 stable stream IDs plus a non-bar ★ operator-console-honesty
    stream, the completed reliability/provenance spine, the containment-first
    execution-order revision, and the fresh-audit pre-close checklist.
    **Streams 1-3 and operator-console-honesty have shipped; Stream 3
    (`verdict-provenance-reproducibility`) is latest, merged via PR #38
    (`bfb2d2d`) on `2026-07-27`. No successor is open; containment safety is
    the next gate.** New stable IDs are recorded in
    [`POST_POC_BACKLOG.md`](../POST_POC_BACKLOG.md) "Newly Captured
    (v1.0 roadmap intake 2026-06-08)".
- `W22-coverage-promotion-hard-tier.md`
  - **Closed phase — closed synthetically on the `week22` branch
    `2026-05-28` and merged to main via PR #31 `week22 -> main` `1399f82`.** W22
    Coverage Promotion Round 3 (hard tier: `chat`) + Sandbox
    Evasion ADR Draft + Container Hardening Ratchet-Down. Sub-iter
    slate: W22-0 doc-reconcile · W22-1 ADR 0014 chat policy ·
    W22-2 chat coverage (static cut; runtime live-run anchor
    deferred to user) · W22-3 attribution depth · W22-4 ADR 0015
    sandbox evasion · W22-5 evasion canary · W22-N close-out.
    W22-6 container-hardening ratchet-down DEFERRED TO USER
    (Linux required); W22-7 [NO-W22-7] doc-only skip. Final W22
    static bar: `tests/architecture/` **292 passed**;
    `make test-security` **228 passed**; broader sweep
    **631 passed**. Slim canonical:
    [`REFACTOR_OPTIMIZATION.md §20`](../REFACTOR_OPTIMIZATION.md).
- `../detection-design/README.md`
  - **Merged named stream — `security-development`, merged to main via PR #34 (`f1dde63`) on `2026-06-04`.** Custom detection-rule expansion for
    the apollyon / securezeron / kagema / GlassWorm / snyk-labs / nf3xn /
    ecm3401 / nextsecurity / snowshono classes (static rules now `s1`-`s20`,
    dynamic A1-A8). The directory is self-contained and tracks safety policy,
    shipped static/dynamic rules, rule-layer reconciliation, and per-class specs.
- `../../deploy/podman/README.md`
  - **Earlier merged named stream — `podman-airgapped-deploy`, merged to main
    from `feat/podman-airgapped-deploy` (`2026-06-08`).** Air-gapped Podman
    deployment bundle for a headless x86 Fedora Server plus human-readable
    documentation entry points. This stream does not advance the weekly W22
    pointer.
- `extrace-static-stream-handoff.md`
  - **Frozen design-intent reference — branch `extrace-static`
    abandoned `2026-05-28`; the replacement Static Analysis Pre-Check stream
    later closed and merged via PR #33 (`70e4364`) on `2026-06-01`.** Preserves
    the four locked design
    decisions (block-and-warn semantics, separate
    `automation_static_analyzer` Docker service, schema-first
    contract landing, in-house Python rules + Semgrep MVP) and the original
    ES-0..ES-5 sub-iter slate. Final implementation evidence lives in
    [`static-analysis-pre-check-stream.md`](static-analysis-pre-check-stream.md).
- `W20-coverage-promotion-easy-wins.md`
  - **Frozen phase — W20-0..W20-5 all closed on the `week20`
    branch per user direction `2026-05-26`; W11-W19 paterni
    preserved; merged via PR #29 `week20 -> main` / `64a3c3d`.**
    W20 Coverage Promotion Round 1: Easy Wins (Hat-3
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
