# Dynamic Analysis Backlog

`Last Updated: 2026-04-23`

This is the short actionable backlog for the sandbox pipeline. It complements
`DEVELOPMENT_PRIORITIES.md` and `PIPELINE_ROADMAP.md` rather than repeating
them.

W5 detection foundations and W6 automation reliability + capture hardening are
both closed (W6 closed `2026-04-23` after the correctness follow-up). The
backlog below is the W7 acceptance + buffer working set plus deferred items.

## Now (W7 acceptance + buffer)

- drive the PoC acceptance checklist in `REFACTOR_OPTIMIZATION.md` §10.7 to
  green: each Must-class adversary (A1/A2/A4/A6) reproducibly fires its rule
  against its T1 canary in `make test-security`
- exercise live capture against T1 canaries via `make test-security-live` and
  confirm `tls_client_hello` plus other `TLS_EVENT_TYPES` events flow through
  attribution and into `DetectionFinding.evidence`
- verify benign baselines under `extensions/` (chat, theme) stay
  zero-finding so the `security-fixtures` CI lane stays honest about false
  positives
- confirm `RuleExecutionStatus.ERROR` paths actually demote
  `automation_health` to `inconclusive` end-to-end (rule error → automation
  health → verdict rollup) on a real fixture, not just unit tests

## Next (post-W7 follow-ups)

- close official-track verification gaps for `scm` and `settings`
- decide which partial scaffolding should advance for `chat`, `comments`,
  `testing`, and `workspace_trust`
- evaluate Stretch adversary classes (A3 typosquat, A5 malicious update, A7
  VS Code API abuse) once Must-class acceptance is green

## Later

- define retention and cleanup policy for `output/`
- add lightweight artifact operations only if operators need them
- revisit richer run history only if JSON artifacts become a real bottleneck
- evaluate stack-scoped compose/runtime ergonomics if parallel worktrees become
  a real bottleneck

## Guardrails

- executor-specific work stays under `executor/`
- orchestration stays under `workflows/marketplace/`
- shared contracts and persistence stay under `appcore/` and `packages/`
- malicious-fixture work stays aligned with ADR 0004 tiers and Make targets
