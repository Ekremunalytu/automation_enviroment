# Refactor Expansion Notes

`Last Updated: 2026-04-20`

These notes intentionally do not define a binding delivery plan. They exist so
the heavier follow-on work is visible without overcommitting after the Week 4
closure.

Week 4 closure is green as of `2026-04-20`; use `REFACTOR_STATUS.md` for the
current gate and `REFACTOR_OPTIMIZATION.md` §10 for the active W0-W7 window.

## Why These Items Are Deferred

- Week 1-4 already covered the highest-value boundary cleanup.
- The remaining topics touch runtime ergonomics or workspace parallelism more
  than they improve the immediate PoC security bar.
- Deferring them reduces the risk of mixing stabilization work with broader
  runtime rewiring in the same cycle.

## Reopen Conditions

Turn one of these notes into a committed plan only after:

- `REFACTOR_STATUS.md` still shows Week 4 closure criteria green
- fast test lanes remain healthy
- there is a concrete product or operability reason to spend the extra risk
  budget

## Historical Promotions

The following items are no longer deferred; they are listed here only so older
notes still have a place to point:

- executor reporting semantics alignment -> Week 4A
- deterministic executor runtime -> W2 (Week 4D-a in the 7-week window)
- AI-safe ownership / import-graph enforcement -> W1 (Week 4C)
- expanded benign smoke/fixture matrix -> W1, while malicious fixtures move to
  W5
- executor control boundary -> W4 (Week 4E)

## Candidate Expansion Topics (still deferred)

### Stack-Scoped Compose Runtime

- remove fixed `container_name` assumptions
- make ports and state roots stack-scoped from env alone
- improve multi-worktree and parallel AI ergonomics
- not promoted: operability gain, not on the stabilization-to-security
  critical path

## Operating Rule

Do not treat these remaining notes as an implied Week 5 commitment. Promote
them into the execution plan only when the repo is stable enough to absorb the
extra change surface.
