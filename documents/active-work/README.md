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

- `W13-test-expansion-observability.md`
  - **Active phase.** W13 test expansion + observability. W13-1..W13-5
    closed; W13 next-pull is `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]`
    or `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]`
    (MEDIUM acceptance-bar items; W13-6/W13-7 stable IDs pending).
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
