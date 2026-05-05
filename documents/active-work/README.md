# Active Work

`Last Updated: 2026-05-05`

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

- `W11-monitor-lifecycle.md`
  - **Active phase.** W11 monitor lifecycle split (W11-1..W11-N),
    formerly `REFACTOR_OPTIMIZATION.md §11.8`. W11-1..W11-6 landed
    `2026-05-04`/`2026-05-05`; W11-7
    (`workflows/extension_catalog/service.py` split) is the next
    pull-first.
- `W8-security.md`
  - W8 security hardening checklist (W8-1..W8-7), formerly
    `REFACTOR_OPTIMIZATION.md §11.5`. Closed for active work
    `2026-04-29` (W8-1..W8-7 + W8-9 landed, W8-8 deferred). Kept on
    the read path because code comments reference items by
    `W8-<n>` ID — do not renumber.
