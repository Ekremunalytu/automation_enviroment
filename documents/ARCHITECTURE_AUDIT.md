# Architecture Audit

`Last Updated: 2026-04-14`

This audit reflects the repository as it exists today, not the initial
post-refactor snapshot.

## Executive Summary

The architecture is materially better than the old router/core/scanner
concentration:

- shared infrastructure is isolated in `appcore/`
- business flows are grouped in `workflows/`
- executor control is separated from executor runtime
- the React UI is split by route and adapter surface

The main architectural risk is no longer module placement. It is operational
truthfulness around sandbox execution, trigger coverage, and file-backed
analysis state.

## What Improved

### Shared vs workflow boundaries are now real

- `appcore/` owns settings, DB wiring, ORM models, CRUD, and contracts
- `workflows/` owns routing and business orchestration
- `executor/` owns Docker exec and Playwright sandbox mechanics
- `ui/` owns the analyst-facing web console

### Analysis orchestration is more explicit

Marketplace analysis is no longer a single opaque path. It is split across:

- `router.py` for API surface
- `analysis_service.py` for step orchestration
- `job_store.py` for snapshot persistence
- `trigger_service.py` and `triggers.py` for layered stimulus planning

### Report semantics are now a first-class concern

The executor no longer emits only raw telemetry. It also produces:

- automation and log health
- attribution summaries
- risk signals and verdicts
- official vs heuristic capability coverage summaries

## Current Architectural Strengths

- `main.py` stays small and composes routers cleanly.
- Catalog writes still funnel through `appcore.storage.crud`.
- Pydantic validation occurs before persistence in the catalog flow.
- Async analysis jobs expose named steps instead of a single opaque status.
- The UI mirrors the backend flow cleanly: marketplace -> simulation -> reports.

## Current Risks

### Dynamic-analysis state is still artifact-first

Reports and job snapshots live in `output/`, not PostgreSQL.

That is acceptable for the current single-operator model, but it still means:

- retention is operational rather than schema-driven
- cross-run querying is limited
- report/job consistency depends on filesystem conventions

### Executor reliability defines product truthfulness

The highest-risk path still depends on:

- Docker exec success
- VS Code startup and reload behavior
- trigger payload generation and loading
- Playwright timing
- monitor/report finalization after partial failures

### Coverage can drift if docs are not kept aligned

The trigger system now distinguishes official activation coverage from heuristic
workflow coverage. That is stronger than the earlier model, but it also means
documentation can become stale quickly if it collapses those tracks into a
single yes/no matrix.

## Recommendations

### Near-term

- Keep executor failure states explicit in job snapshots and report health.
- Expand tests around restart interruption and degraded-run semantics.
- Keep documentation synchronized with the real trigger and report contract.

### Mid-term

- Define retention/cleanup expectations for `output/activation_report_*.json`
  and `output/analysis_jobs/*.json`.
- Persist more structured run metadata only if analyst querying genuinely
  becomes painful.
- Keep compatibility or historical surfaces out of new implementation work.

### Long-term

- Version report contracts deliberately as evidence semantics evolve.
- Retire dormant compatibility surfaces once callers are truly gone.
- Revisit DB-backed run history only if the single-operator model changes.

## Verdict

The architecture is coherent and maintainable. The remaining hard problems are
runtime reliability, evidence truthfulness, and documentation discipline, not
another major package reshuffle.
