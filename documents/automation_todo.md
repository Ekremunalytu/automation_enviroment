# Dynamic Analysis Backlog

`Last Updated: 2026-06-15 — consolidated; content moved to the canonical sources below.`

This short backlog previously duplicated closed-phase history and pull-next
notes that now live in the canonical docs. It has been **consolidated** to a
forwarding pointer to remove the drift surface (the full pre-consolidation
content is frozen at
[`archive/plans/automation_todo_2026-05-28.md`](archive/plans/automation_todo_2026-05-28.md)).
Use:

- **Pullable / deferred work:** [`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md)
- **Landed closure state:** [`REFACTOR_STATUS.md`](REFACTOR_STATUS.md)
- **v1.0 forward arc:** [`active-work/v1-roadmap.md`](active-work/v1-roadmap.md)
- **Detection-rule development:** [`detection-design/README.md`](detection-design/README.md)
- **Enduring engineering priorities:** [`DEVELOPMENT_PRIORITIES.md`](DEVELOPMENT_PRIORITIES.md)

## Guardrails

These placement rules are enduring and survive consolidation:

+ executor-specific work stays under `executor/`
+ orchestration stays under `workflows/marketplace/`
+ shared contracts and persistence stay under `appcore/` and `packages/`
+ malicious-fixture work stays aligned with ADR 0004 tiers and Make targets
