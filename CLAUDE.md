# CLAUDE.md

`Last Updated: 2026-05-13 (W14 active; W14-1 pulled; week14 branch cut from main at 69251f1; W13 close-out PR #20 week13 -> main merged via 772deb3)`

This file is intentionally a thin pointer. Do not duplicate phase summaries or
architecture maps here; that caused drift.

## Read Path

1. `AGENTS.md` — hard architectural and security rules.
2. `documents/AGENT_CONTEXT.md` — task-routing decision tree.
3. One matching `documents/agent-lanes/*.md` file.
4. `documents/REFACTOR_STATUS.md` (slim canonical) only when current phase
   state matters.
5. Subsystem docs only when the lane doc points to them. Slim canonicals
   link out to `documents/<area>/` splits — open the split, not the full
   canonical, for detail.
6. `documents/active-work/<file>.md` only when the lane doc points to it.

## Operating Rules

- Keep context narrow; start from one lane and do not preload
  `documents/`. Ignore generated or heavy trees unless the task
  explicitly targets them.
- If docs disagree with code/tests, trust code/tests and update the
  stale doc after confirming the drift.
- Current state is owned by `documents/REFACTOR_STATUS.md` (slim canonical).
- Deferred and pull-next work is owned by `documents/POST_POC_BACKLOG.md`
  (slim canonical).
- W8-W13 planning is owned by `documents/REFACTOR_OPTIMIZATION.md` section 11;
  W14 by section 12. W13 closed `2026-05-13`; PR #20 `week13 -> main`
  merged via `772deb3`. **Active phase: W14 — Codex M-class Acceptance +
  Observability** is active on the `week14` branch (cut from `main` at
  `69251f1` on `2026-05-13`); see
  `documents/active-work/W14-codex-acceptance-observability.md`. W14-1
  pulled `2026-05-13`; remaining `W14-N` stable IDs fill in at first pull.
  Past trackers are stable-ID references only: W13, W12, W11, and W8.
- `documents/archive/` is frozen reference; not on the default read path.
  Open only when a slim canonical explicitly points there.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
