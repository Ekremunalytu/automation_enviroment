# Documentation Maintenance Lane

**Last Updated:** 2026-05-25 (W19 active — Hat-1 closed + live-verified via W19-2-followup-2 `d5de9ca`; Hat-2 W19-3..W19-5 and W19-6 close-out pending. Current truth anchors: `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, `REFACTOR_OPTIMIZATION.md` §17, `active-work/W19-live-run-root-cause.md`, and `active-work/W18-W22-roadmap.md`.)

Use this lane for README, ADR, runbook, roadmap, testing-guide, and
agent-doc updates.

## Start Here

Read `AGENTS.md`, `documents/AGENT_CONTEXT.md`, `documents/README.md`, the
target doc, and the code/tests/config proving each claim.

## Invariants

### Canonical Discipline

- `AGENTS.md` stays short and authoritative.
- `documents/AGENT_CONTEXT.md` stays a thin routing map; never copy
  phase history or weekly detail into preload files.
- `REFACTOR_STATUS.md` (slim canonical) owns current phase state.
- `POST_POC_BACKLOG.md` (slim canonical) owns deferred and pull-next
  work; **stable item IDs** (`[FOLLOWUP <id>]`) are a contract — code
  comments and tests reference them. Do not rename.
- `REFACTOR_OPTIMIZATION.md` section 11 owns closed W8-W13 planning;
  sections 12-16 own closed W14-W18 planning; section 17 owns active
  W19 planning; sections 18-20 own the W20-W22 roadmap. Active W19
  tracker: `documents/active-work/W19-live-run-root-cause.md`. Past
  W8/W11/W12/W13/W14/W15/W16/W17/W18 trackers remain only for stable IDs.
- ADR 0007 enforcement landed `2026-04-29` via W8-7 — loopback
  defaults plus `EXTRACE_ALLOW_LAN` opt-in are pinned by
  `tests/architecture/test_default_bindings.py`. Do not regress to
  wildcard binds or wildcard CORS without an updated ADR.

### Archive + Active-Work Discipline

- Historical content goes under `documents/archive/` and stays off the
  default read path. Active work goes under `documents/active-work/<file>.md`.
  Review snapshots live directly under `documents/archive/reviews/`.
- If a slim canonical grows past budget, add a dated full snapshot under
  `documents/archive/<area>/`, then re-trim the canonical.

### Token Budget Targets

Slim canonical doc word counts (×1.3 ≈ tokens). Verify with
`wc -w <file> | awk '{ print $1 * 13 / 10 }'`.

| Doc | Target tokens |
|---|---|
| `REFACTOR_OPTIMIZATION.md` | ≤ 2,500 |
| `REFACTOR_STATUS.md` | ≤ 2,500 |
| `POST_POC_BACKLOG.md` | ≤ 3,000 |
| `ARCHITECTURE.md` | ≤ 2,500 |
| `PROJECT_STRUCTURE.md` | ≤ 2,500 |
| `TESTING.md` | ≤ 3,000 |
| `DETECTION_SEMANTICS.md` | ≤ 3,500 |
| `EXECUTOR_PLAYWRIGHT.md` | ≤ 3,500 |
| Each subdir split file | ≤ 3,000 |
| Entry path total (AGENTS + CLAUDE + AGENT_CONTEXT + documents/README + 1 lane) | ≤ 3,000 |

### Inbound Link Discipline

- Before adding a code/anchor reference to a slim canonical doc,
  confirm the target item has a stable ID (e.g. `[FOLLOWUP …]`,
  `W8-N`).
- Do not add line-number references to canonical docs — line numbers
  drift on every trim.
- Any new doc added under `documents/` root must justify itself
  against the split structure (does it belong as a slim canonical, an
  active-work file, an archive snapshot, or a subdir split?).

## Validation

- `git diff --check -- AGENTS.md CLAUDE.md README.md documents docs`
- `pre-commit run markdownlint --files <changed markdown files>`
- `pre-commit run markdown-link-check --files <changed markdown files>`
- Legacy drift grep: search old status tokens such as `PR345-blocked`,
  `PR5-ADR-blocked`, `ADR-0007-Proposed`, and
  `ADR-0006-as-container-packaging` outside this lane.
- Anchor guard: `POST_POC_BACKLOG.md` line-number links must be empty outside
  archive snapshots; legacy review links must point under `archive/reviews/`.
- Budget sanity: run `wc -w` on changed slim canonicals and multiply by 1.3.

## Avoid

- Broad rewrites or copied phase summaries that do not reduce drift/context cost.
- New root docs when a slim canonical, split, active-work file, or archive
  snapshot is the right home.
- Reverting the README "Read First" lazy-load pattern.
- Changing runtime code during a docs-only pass.
