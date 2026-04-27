# Dynamic Analysis Backlog

`Last Updated: 2026-04-27`

This is the short actionable backlog for the sandbox pipeline. It complements
`DEVELOPMENT_PRIORITIES.md`, `PIPELINE_ROADMAP.md`, and the canonical
deferred-work source `POST_POC_BACKLOG.md` rather than repeating them.

W5 detection foundations (2026-04-20), W6 automation reliability plus
capture hardening (2026-04-21 plus correctness follow-up 2026-04-23),
and W7 acceptance plus buffer (2026-04-23) are all closed. Post-W7
hardening on 2026-04-24 landed fatal UI-crash fail-fast, scan-between
VS Code restart, `attribution/` subpackage split, and the `sim-target`
Makefile lane. The 2026-04-25 simulation-progress-cancel branch then
landed weighted simulation progress, the full-stack analysis cancel
flow, the VNC harness ready-marker fix, and the
`t1-demo-runnable-canary` + rule + `make demo-canary` /
`make demo-canary-offline` Makefile lanes; review follow-ups are
tagged `[FOLLOWUP simulation-progress-cancel]` in
`POST_POC_BACKLOG.md`. PR345 target activation lifecycle and W8-0
deterministic harness readiness gate both landed on 2026-04-27; W8 is
now eligible to open.

## Now (next-iteration pull)

Source of truth: `POST_POC_BACKLOG.md` "Next iteration (pull first)" and
`REFACTOR_STATUS.md` for landed closure evidence. The W7 `[NEXT]` items
(attribution split + sim-target lane), simulation progress/cancel/VNC/demo
canary work, PR345 PRs 1-5, and W8-0 are all landed. The next pull-first
candidates from the backlog are:

+ **W8 (`REFACTOR_OPTIMIZATION.md` §11.5) security hardening.** First PR
  candidates: W8-1 VSIX zip-bomb guard, W8-2 marketplace identity helper,
  W8-3 URI trigger shell-safe invocation. W8-0 no longer blocks these; it
  landed 2026-04-27 (`REFACTOR_STATUS.md` "W8-0 Landed").
+ Docker-based A1 canary structural diff smoke (`make exec-up && make
  exec-run` against `t1-a1-credential-read-to-network-canary`); closes
  the capture-pipeline regression risk flagged in the attribution-split
  deferral note. `make demo-canary` exercises the same surface against
  the new declawed fixture and is a faster smoke for routine work.
  Now also worth running against the new harness output-channel hook
  (PR5) once the next executor smoke happens.
+ Code-review follow-ups from the simulation-progress-cancel branch
  (custom `role="alertdialog"` for Stop simulation, cancel-mutation
  timeout/retry, heartbeat sandbox-reset off-thread, schema
  duplication, `is_job_cancelled` session churn, heartbeat refactor,
  cancel-after-finish race test, heartbeat 30 s → 5 s load
  verification) — see `POST_POC_BACKLOG.md`
  `[FOLLOWUP simulation-progress-cancel]` entries.
+ ADR 0006 §5 full `target_extension_observed` conjunction tightening
  (currently only the additive OR clause landed in PR5). Deferred so
  baseline fixtures don't churn; planned as a focused follow-up before
  W8-W13 closes.

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
