# Active Work

`Last Updated: 2026-05-21 (W18 active — closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; W18-0..W18-4 sub-iter slate landed on the week18 branch (per user direction; W11-W17 paterni preserved); W18-4-followup post-merge audit landed this commit. W18 frozen tracker: W18-heartbeat-refactor.md. W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. Final W18 bar: tests/architecture/ 201 passed; make test-security 220 passed; full suite 1907 passed, 9 skipped, 8 deselected.)`

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

- `W15-codex-uclass-bounds-posture.md`
  - **Active phase — W15-1..W15-7 closed `2026-05-17`; `week15 -> main`
    close-out PR pending separate user action.** W15 Codex U-class
    Close-Out + UI Bounds + Posture. 7 sub-iter slate
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
    Retained on the read path as the active tracker until the
    `week15 -> main` close-out PR merges and the next phase opens.
    Slim canonical:
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
