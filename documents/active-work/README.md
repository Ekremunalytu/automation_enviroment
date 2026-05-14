# Active Work

`Last Updated: 2026-05-14`

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
  - **Active phase — scope skeleton authored `2026-05-14`; branch + first
    pull pending.** W15 Codex U-class Close-Out + UI Bounds + Posture.
    7 sub-iter scoped (`W15-1..W15-7`): sync analyze error taxonomy
    alignment (M10), workspace symlink check order / orphan removal
    (M12), `activationEvents` bounds + DB field-length Alembic migration
    (U8), UI bounds bundle (U1-U3 + U6), quick fixes bundle (I2 + I4),
    unauthenticated catalog endpoints posture (ADR 0011 — U10-U11),
    regression lock-in umbrella (compose image pin +
    `aquasecurity/trivy-action` version pin + W14 post-merge doc
    preamble truth-state refresh). Branch cut + W15-1 pull pending;
    `week15` cut from `main` at HEAD `4e03c8d` when W15-1 is pulled.
    W15-1..W15-7 stable ID'leri pull sırasında atanacak (W11/W12/W13/W14
    precedent). Slim canonical:
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
