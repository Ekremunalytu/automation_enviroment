# Dynamic Analysis Backlog

`Last Updated: 2026-04-20`

This is the short actionable backlog for the sandbox pipeline. It complements
`DEVELOPMENT_PRIORITIES.md` and `PIPELINE_ROADMAP.md` rather than repeating
them.

## Now

- add an activation confirmation gate with dynamic post-stimulus verification
- keep executor failure states unambiguous in job steps and report health
- keep interrupted jobs explicit after API restarts
- harden the dedicated CI lane for `make test-security` with explicit egress guardrails

## Next

- close runtime capture gaps for HTTP body capture and child-process tracking
- make workspace seeding and materializers extension-aware for declared
  activation events
- add deferred-activation coverage with an idle observation window
- close official-track verification gaps for `scm` and `settings`
- decide which partial scaffolding should advance for `chat`, `comments`,
  `testing`, and `workspace_trust`

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
