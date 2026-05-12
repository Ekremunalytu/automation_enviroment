# Active Work

`Last Updated: 2026-05-11`

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

- `W14-codex-acceptance-observability.md`
  - **Staging phase (pre-entry — blocked behind W13 close-gate).** W14
    Codex M-class Acceptance + Observability. 6 sub-iter scoped
    (`W14-1..W14-6`): BLOCKER scenario-dropout araştırması, Codex
    M-class input validation (M4-M7 + M11), dış yüzey sertleştirme
    (M13 + M14b + U4-U12), correctness/concurrency (analysis-jobs-race
    - evidence-event-kind invariant), §11.10 GOAL devamı (logger
    consolidation + run-ID stamping + codex-automation-5 fingerprint),
    W8-W12 regression lock-in umbrella. Entry gate W13-11/12/13
    close-gate clearance + close-out PR merge'de tetiklenir; stable
    ID'ler ilk pull'da atanır (W11/W12/W13 precedent). Slim canonical:
    [`REFACTOR_OPTIMIZATION.md §12`](../REFACTOR_OPTIMIZATION.md).
- `W13-test-expansion-observability.md`
  - **Active phase — CLOSE-GATE HOLD on W13-11/12/13.** W13 test
    expansion + observability. W13-1..W13-7 closed — every MEDIUM/HIGH
    Codex Cloud audit acceptance-bar item (H3 via W13-5, H4 via W13-3,
    H5 via W13-2, H6 via W13-1, M1 via W13-7, M9 via W13-6) landed.
    §11.10 GOAL pulls: W13-8 closed (benign silence fixture 3→5 GREEN,
    5/5 ✓), W13-9 closed (`.env` gitignore architecture gate 10/10 ✓),
    W13-10 closed (singleton-lock recovery integration test 2/2 ✓).
    **CLOSE-GATE `2026-05-11`** — Codex Cloud second-opinion review
    surfaced 3 P1 close-pass items: W13-11 HMAC python secret
    target-install race (close-pass for W13-1 H6) **closed `2026-05-12`**,
    W13-12 fail-closed harness handshake (close-pass for W13-1 H6)
    **closed `2026-05-12`**, W13-13 worker-start cancel-race CAS
    (close-pass for W13-3 H4 — README sweep + regex pin landed early
    in W13-11 push) still pending. Close-out PR `week13 → main` BLOCKED
    until W13-13 GREEN. Original §11.10 TBD umbrellas (logger
    consolidation, run-ID stamping, W8-W12 regression lock-in)
    deferred to W14 — see W14 tracker above.
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
