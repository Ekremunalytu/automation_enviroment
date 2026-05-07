# Documentation Maintenance Lane

`Last Updated: 2026-05-07`

Use this lane for README, ADR, runbook, roadmap, testing-guide, and
agent-doc updates.

## Start Here

- `AGENTS.md`
- `documents/AGENT_CONTEXT.md`
- `documents/README.md`
- the specific doc being updated
- code/tests/config that prove each claim

## Invariants

### Canonical Discipline

- `AGENTS.md` stays short and authoritative.
- `documents/AGENT_CONTEXT.md` stays a thin routing map; never copy
  phase history or weekly detail into preload files.
- `REFACTOR_STATUS.md` (slim canonical) owns current phase state.
- `POST_POC_BACKLOG.md` (slim canonical) owns deferred and pull-next
  work; **stable item IDs** (`[FOLLOWUP <id>]`) are a contract — code
  comments and tests reference them. Do not rename.
- `REFACTOR_OPTIMIZATION.md` section 11 owns W8-W13 planning. Active
  W12 tracker: `documents/active-work/W12-executor-subpackaging.md`.
  Past W8/W11 trackers remain only for stable IDs. Inbound references:
  - `executor/flows/playwright/uri_validation.py:9` →
    `active-work/W8-security.md` item W8-3.
  - `tests/security/test_canary_end_to_end.py:8` → preserves the
    `REFACTOR_OPTIMIZATION.md §10.7` heading (W7 PoC acceptance bar,
    not a W8 ID).
- ADR 0007 enforcement landed `2026-04-29` via W8-7 — loopback
  defaults plus `EXTRACE_ALLOW_LAN` opt-in are pinned by
  `tests/architecture/test_default_bindings.py`. Do not regress to
  wildcard binds or wildcard CORS without an updated ADR.

### Archive + Active-Work Discipline

- Historical content goes under `documents/archive/` and is off the
  default read path.
- Active in-flight work goes under `documents/active-work/<file>.md`;
  open only when a lane points there.
- Review snapshots live directly under `documents/archive/reviews/`.
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
- Drift grep:

  ```bash
  rg -n "PR345-blocked|PR5-ADR-blocked|ADR-0007-Proposed|ADR-0006-as-container-packaging" \
    AGENTS.md CLAUDE.md README.md documents docs \
    --glob '!documents/agent-lanes/docs-maintenance.md'
  ```

- Anchor / line-ref guard:

  ```bash
  rg -n "POST_POC_BACKLOG\.md[ :]+[L]?[0-9]+" \
    AGENTS.md CLAUDE.md README.md documents docs \
    --glob '!documents/archive/**'  # must be empty outside archive snapshots
  rg -n "documents/(claude_code_review|codex_project_review)\.md|\]\((claude_code_review|codex_project_review)\.md\)" \
    --type md --glob '!documents/archive/**'
  # → bad legacy review paths only; archive/reviews/* links are allowed
  ```

- Budget sanity (slim canonical):

  ```bash
  for f in documents/REFACTOR_OPTIMIZATION.md \
           documents/REFACTOR_STATUS.md \
           documents/POST_POC_BACKLOG.md \
           documents/ARCHITECTURE.md \
           documents/PROJECT_STRUCTURE.md \
           documents/TESTING.md \
           documents/DETECTION_SEMANTICS.md \
           documents/EXECUTOR_PLAYWRIGHT.md \
           documents/active-work/W8-security.md \
           documents/active-work/W12-executor-subpackaging.md; do
    printf "%-55s %d words ~%d tokens\n" \
      "$f" "$(wc -w < $f)" "$(($(wc -w < $f) * 13 / 10))"
  done
  ```

## Avoid

- Broad rewrites that do not reduce drift or context cost.
- Copying long phase summaries into multiple files.
- Adding a new top-level doc under `documents/` when an existing slim
  canonical can absorb it, or when a subdir split is the right home.
- Reverting the README "Read First" list to send agents into
  `ARCHITECTURE.md` / `PROJECT_STRUCTURE.md` / `TESTING.md` by default —
  those moved to "Load Only If The Task Needs It" intentionally.
- Changing runtime code during a docs-only pass.
