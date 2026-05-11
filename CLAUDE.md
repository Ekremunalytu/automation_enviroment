# CLAUDE.md

`Last Updated: 2026-05-11 (W12 closed via PR #18; W13 — Test Expansion + Observability open; W13-1..W13-7 closed — acceptance bar cleared, ready for close-out PR)`

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
- W8-W13 planning is owned by `documents/REFACTOR_OPTIMIZATION.md` section 11.
  W11 closed `2026-05-05` and merged via PR #14; W12 closed `2026-05-10`
  and merged into `main` via PR #18 (`33a0852`). Active phase:
  **W13 — Test Expansion + Observability** (REFACTOR_OPTIMIZATION
  §11.10; tracker
  `documents/active-work/W13-test-expansion-observability.md`).
  W13-1..W13-7 closed — every MEDIUM/HIGH Codex Cloud audit
  acceptance-bar item (H3/H4/H5/H6/M1/M9) landed. Next step is the
  W13 end-of-phase close-out PR `week13 → main` (W12 PR #18 pattern).
  Past trackers (stable-ID reference only):
  `documents/active-work/W12-executor-subpackaging.md`
  (W12-0..W12-5);
  `documents/active-work/W11-monitor-lifecycle.md`
  (W11-1..W11-8);
  `documents/active-work/W8-security.md` (closed `2026-04-29`).
- `documents/archive/` is frozen reference; not on the default read path.
  Open only when a slim canonical explicitly points there.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
