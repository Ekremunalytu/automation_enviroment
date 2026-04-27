# CLAUDE.md

`Last Updated: 2026-04-27`

This file is intentionally a thin pointer. Do not duplicate phase summaries or
architecture maps here; that caused drift.

## Read Path

1. `AGENTS.md` — hard architectural and security rules.
2. `documents/AGENT_CONTEXT.md` — task-routing decision tree.
3. One matching `documents/agent-lanes/*.md` file.
4. `documents/REFACTOR_STATUS.md` only when current phase state matters.
5. Subsystem docs only when the lane doc points to them.

## Operating Rules

- Keep context narrow; do not preload `documents/`.
- If docs disagree with code/tests, trust code/tests and update docs.
- Current state is owned by `documents/REFACTOR_STATUS.md`.
- Deferred and pull-next work is owned by `documents/POST_POC_BACKLOG.md`.
- W8-W13 planning is owned by `documents/REFACTOR_OPTIMIZATION.md` section 11.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
