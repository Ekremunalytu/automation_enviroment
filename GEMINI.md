# GEMINI.md

`Last Updated: 2026-04-27`

This file is intentionally a thin pointer to reduce duplication drift.

## Read Path

1. `AGENTS.md` — authoritative hard rules.
2. `documents/AGENT_CONTEXT.md` — task-routing decision tree.
3. One matching `documents/agent-lanes/*.md` file.
4. `documents/REFACTOR_STATUS.md` when phase state matters.

## If Docs And Code Disagree

Trust code and tests. Update the stale doc after confirming the drift.

## Context Budget

Do not scan the whole repo. Start from one lane and ignore generated or heavy
trees unless the task explicitly targets them.
