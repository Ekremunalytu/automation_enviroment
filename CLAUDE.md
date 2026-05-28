# CLAUDE.md

`Last Updated: 2026-05-28`

`Active phase: W22 — closed synthetically on the week22 branch; PR week22 -> main PENDING USER APPROVAL (memory feedback_pr_push_approval standing).`

`Previous phase: W21 closed and merged via PR #30 week21 -> main 2026-05-28 via 5dc18aa.`

`Active tracker: documents/active-work/W22-coverage-promotion-hard-tier.md · Sources of truth: documents/REFACTOR_STATUS.md (state) · documents/POST_POC_BACKLOG.md (deferred) · documents/REFACTOR_OPTIMIZATION.md §20 (W22 plan).`

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
- Phase plans live in `documents/REFACTOR_OPTIMIZATION.md`:
  W8-W13 §11 · W14 §12 · W15 §13 · W16 §14 · W17 §15 · W18 §16 ·
  W19 §17 · W20 §18 · W21 §19 · **W22 §20** (active, closed
  synthetically; PR `week22 -> main` pending approval).
- Multi-iter roadmap source-of-truth:
  `documents/active-work/W18-W22-roadmap.md`. Past frozen trackers
  (`active-work/W{8,11,12,13,14,15,16,17,18,19,20,21}-*.md`) stay on
  the read path only because code/tests reference items by stable
  ID — do not renumber.
- `documents/archive/` is frozen reference; not on the default read
  path. Open only when a slim canonical explicitly points there.

## Quick Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make sim-target TARGET=publisher.name`
