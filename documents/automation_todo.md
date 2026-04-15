# Dynamic Analysis Backlog

`Last Updated: 2026-04-15`

This is the short actionable backlog for the sandbox pipeline. It complements
`DEVELOPMENT_PRIORITIES.md` and `PIPELINE_ROADMAP.md` rather than repeating
them.

## Now

- make executor failure states unambiguous in job steps and report health
- keep interrupted jobs explicit after API restarts
- tighten tests around async lifecycle and degraded runs

## Next

- close official-track verification gaps for `scm` and `settings`
- decide which partial scaffolding should advance for `chat`, `comments`,
  `testing`, and `workspace_trust`
- keep report JSON and UI adapters in lockstep

## Later

- define retention and cleanup policy for `output/`
- add lightweight artifact operations only if operators need them
- revisit richer run history only if JSON artifacts become a real bottleneck

## Guardrails

- executor-specific work stays under `executor/`
- orchestration stays under `workflows/marketplace/`
- shared contracts and persistence stay under `appcore/`
