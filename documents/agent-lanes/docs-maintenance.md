# Documentation Maintenance Lane

**Last Updated:** 2026-07-30. Current state is owned by `phase.json` and
`REFACTOR_STATUS.md`.

Use this lane for README, ADR, runbook, roadmap, and agent-doc changes.
Human guides link to canonical state instead of copying it.

## Start Here

Read `AGENTS.md`, `documents/AGENT_CONTEXT.md`, `documents/README.md`, the
target doc, and the code/tests/config proving each claim.

## Invariants

### Canonical Discipline

- `AGENTS.md` stays short and authoritative.
- `CLAUDE.md` is only a compatibility pointer.
- `AGENT_CONTEXT.md` is only a routing map.
- `REFACTOR_STATUS.md` owns state; `POST_POC_BACKLOG.md` owns deferred work.
- Stable IDs such as `[FOLLOWUP <id>]` and `W<N>-<id>` are contracts; do not
  rename them.
- Reader guides and README link to canonical detail instead of copying it.

### Archive + Active-Work Discipline

- Historical content goes under `documents/archive/` and stays off the
  default read path. Active work goes under `documents/active-work/<file>.md`.
- If a slim canonical grows past budget, add a dated full snapshot under
  `documents/archive/<area>/`, then re-trim the canonical.

### Token Budget Targets

Word count ×1.3 approximates tokens.

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
- New root docs must justify why they are not a split, tracker, or snapshot.

## Validation

- `git diff --check -- AGENTS.md CLAUDE.md README.md documents docs`
- `pre-commit run markdownlint --files <changed markdown files>`
- `pre-commit run markdown-link-check --files <changed markdown files>`
- `pytest tests/architecture/test_doc_token_budget.py -q`
- Run the relevant drift/anchor guards for touched canonical docs.

## Avoid

- Copied phase summaries or implementation detail in preload files.
- New root docs when a slim canonical, split, active-work file, or archive
  snapshot is the right home.
- Turning README into a phase ledger, API reference, or architecture spec.
- Changing runtime code during a docs-only pass.
