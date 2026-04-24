# Dynamic Analysis Backlog

`Last Updated: 2026-04-24`

This is the short actionable backlog for the sandbox pipeline. It complements
`DEVELOPMENT_PRIORITIES.md`, `PIPELINE_ROADMAP.md`, and the canonical
deferred-work source `POST_POC_BACKLOG.md` rather than repeating them.

W5 detection foundations (2026-04-20), W6 automation reliability plus
capture hardening (2026-04-21 plus correctness follow-up 2026-04-23),
and W7 acceptance plus buffer (2026-04-23) are all closed. Post-W7
hardening on 2026-04-24 landed fatal UI-crash fail-fast, scan-between
VS Code restart, `attribution/` subpackage split, and the `sim-target`
Makefile lane.

## Now (next-iteration pull)

Source of truth: `POST_POC_BACKLOG.md` "Next iteration (pull first)". The
W7 `[NEXT]` items (attribution split + sim-target lane) landed on
2026-04-24 alongside the fatal-UI-crash + scan-between restart fixes; the
next pull-first candidates from the backlog are:

+ Docker-based A1 canary structural diff smoke (`make exec-up && make
  exec-run` against `t1-a1-credential-read-to-network-canary`); closes
  the capture-pipeline regression risk flagged in the attribution-split
  deferral note
+ monitor discovery-log rate-limit (cosmetic; `find_exthost_logs` + sibling
  call sites; <2h)

## Next (post-PoC value-adds)

+ close official-track verification gaps for `scm` and `settings`
+ decide which partial scaffolding should advance for `chat`, `comments`,
  `testing`, and `workspace_trust`
+ evaluate remaining stretch adversary classes (A5 malicious update, A7 VS
  Code API abuse) — A3 typosquat landed in the W7 Phase 3a buffer
+ pull workflow/platform cleanups from `POST_POC_BACKLOG.md` §Workflow /
  platform cleanups (narrow exceptions, tighten `search_marketplace`
  return type, `make migrate` pre-check)

## Later

+ define retention and cleanup policy for `output/`
+ add lightweight artifact operations only if operators need them
+ revisit richer run history only if JSON artifacts become a real bottleneck
+ evaluate stack-scoped compose/runtime ergonomics if parallel worktrees become
  a real bottleneck
+ promote mypy to `strict = true` once remaining `ignore_errors` overrides
  (scripts, tests, alembic) are resolved
+ documentation consolidation pass across REFACTOR_* docs once W7 is more
  than a few weeks old

## Guardrails

+ executor-specific work stays under `executor/`
+ orchestration stays under `workflows/marketplace/`
+ shared contracts and persistence stay under `appcore/` and `packages/`
+ malicious-fixture work stays aligned with ADR 0004 tiers and Make targets
