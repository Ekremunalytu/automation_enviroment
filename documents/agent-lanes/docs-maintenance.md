# Documentation Maintenance Lane

`Last Updated: 2026-04-27`

Use this lane for README, ADR, runbook, roadmap, testing-guide, and agent-doc
updates.

## Start Here

- `AGENTS.md`
- `documents/AGENT_CONTEXT.md`
- `documents/README.md`
- the specific doc being updated
- code/tests/config that prove each claim

## Invariants

- `AGENTS.md` stays short and authoritative.
- `documents/AGENT_CONTEXT.md` stays a thin routing map.
- Detailed task guidance belongs in `documents/agent-lanes/` or a subsystem
  doc, not in preloaded agent files.
- `REFACTOR_STATUS.md` owns current phase state.
- `POST_POC_BACKLOG.md` owns deferred and pull-next work.
- `REFACTOR_OPTIMIZATION.md` section 11 owns W8-W13 planning.
- Do not document ADR 0007 enforcement as live until code/config/tests land.

## Validation

- `git diff --check -- AGENTS.md CLAUDE.md GEMINI.md README.md documents docs`
- `pre-commit run markdownlint --files <changed markdown files>`
- `pre-commit run markdown-link-check --files <changed markdown files>`
- Drift grep for stale PR345-blocked, PR5-ADR-blocked, ADR-0007-Proposed, and
  ADR-0006-as-container-packaging phrasing.

## Avoid

- Broad rewrites that do not reduce drift or context cost.
- Copying long phase summaries into multiple files.
- Changing runtime code during a docs-only pass.
