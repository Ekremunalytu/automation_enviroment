# Refactor Execution Plan

`Last Updated: 2026-04-16`

This is the canonical execution plan for the current refactor. It keeps the
first four weeks decision-complete and intentionally defers heavier Week 5+
ideas into a separate note: `REFACTOR_EXPANSION_NOTES.md`.

## Context

- ExTrace is staying a single-host appliance for this refactor cycle.
- Docker-isolated sandbox execution remains mandatory.
- The catalog/storage path is stable enough to avoid broad churn right now.
- The dynamic-analysis path needs smaller boundaries before deeper runtime
  changes are safe.
- Weeks 1-3 were intentionally light: no broad runtime rewiring, no schema
  migration, and no API contract change.

## Locked Decisions

- Keep the first four weeks as the binding execution plan.
- Treat Week 5+ as non-binding expansion notes until Week 4A and Week 4B are
  complete.
- Store refactor planning docs under `documents/`.
- Store ADRs under `documents/adrs/`.
- Introduce target package/app directories as visible skeletons first, without
  moving runtime code in Week 1.
- Freeze one sampled activation report and one sampled trigger payload derived
  from current stable artifacts.

## Week 1

### Goal

Create a stable planning baseline inside the repo without changing runtime
behavior.

### Scope

- add this execution plan
- add deferred expansion notes
- add the single-host appliance ADR
- index the new docs in `documents/README.md`
- create visible `apps/` and `packages/` target skeletons
- freeze sampled baseline fixtures for one activation report and one trigger
  payload
- add fixture validation tests

### Non-Goals

- no changes to `main.py`, routers, `analysis_service`, `job_store`,
  `executor/host.py`, or `docker-compose.yml`
- no Alembic migration
- no new authoritative report schema yet
- no UI DTO changes
- no smoke expansion

### Entry Criteria

- current branch is stable enough to freeze artifacts
- `ms-python.python` fixture assets are available locally
- current fast test lanes are green or close enough to use as a baseline

### Exit Criteria

- plan and ADR are committed in-repo
- deferred heavy phases live in a separate note
- target app/package directories are visible
- baseline fixtures parse as JSON objects and expose minimum expected fields
- Week 1 validation tests pass

## Week 2

### Goal

Introduce backend-owned analysis contracts without changing endpoint paths.

### Scope

- add authoritative Pydantic v2 models under `packages/analysis_contracts`
- define `ActivationReport` and `TriggerPayload` as backend-owned contracts
- validate activation report payloads at the API boundary
- keep executor and UI semantics unchanged while contract authority moves

### Entry Criteria

- Week 1 fixtures and docs are in place
- Week 1 baseline tests are green

### Exit Criteria

- activation report routes validate through backend-owned schemas
- sampled fixtures round-trip through the new contract layer
- no endpoint path changes

### Implementation Snapshot

- `packages/analysis_contracts` now owns the authoritative Pydantic v2
  contracts for `ActivationReport`, `TriggerPayload`, and their nested record
  types.
- `workflows/activation_reports/router.py` validates activation report JSON
  objects through `ActivationReport.model_validate(...)` before returning them,
  while keeping the existing `/api/activations` paths unchanged.
- `workflows/marketplace/triggers.py` now finalizes planner output through the
  backend-owned `TriggerPayload` contract instead of a workflow-local payload
  class.
- the Playwright executor path accepts contract-model payloads end to end:
  `executor/flows/playwright/triggers.py` loads trigger files through
  `TriggerPayload.model_validate(...)`, and the monitor/stimulus helpers now
  tolerate nested Pydantic models instead of assuming raw dict payloads
  everywhere.
- the executor container now includes the shared `packages/` tree and
  `pydantic` so the contract package is available inside Docker at runtime.
- validation evidence for this week includes the fixture round-trip tests in
  `tests/platform/contracts/test_analysis_fixture_baselines.py`, the API
  boundary tests in `tests/workflows/activation_reports/test_router.py`, the
  planner serialization tests in `tests/workflows/marketplace/test_triggers.py`,
  the executor contract-consumption tests under `tests/executor/`, and a fresh
  `ms-python.python` activation report produced after the change that validated
  successfully through the same `ActivationReport` contract.

## Week 3

### Goal

Split planner logic into smaller units without semantic redesign.

### Scope

- extract planner-focused modules into `packages/analysis_planner`
- keep `workflows/marketplace/trigger_service.py` as a thin orchestration layer
- add banned-import boundary tests for the planner layer

### Entry Criteria

- Week 2 contract layer exists
- trigger payload baseline fixture is stable

### Exit Criteria

- `workflows/marketplace/triggers.py` is decomposed into smaller planner units
- planner modules avoid web/runtime imports
- existing planner behavior stays equivalent for the baseline fixture

### Implementation Snapshot

- `packages/analysis_planner` now owns the planner-focused implementation split
  across registry, selection, attempts, coverage, and serialization helpers.
- `workflows/marketplace/triggers.py` is reduced to a compatibility facade that
  re-exports the existing trigger-planner API without keeping planner logic in
  the workflow module.
- `workflows/marketplace/trigger_service.py` remains the thin orchestration
  layer: it reads catalog metadata, builds planner inputs, calls the planner
  package, and writes the trigger payload without taking on planner policy.
- planner boundary tests now fail if `packages.analysis_planner` imports web,
  DB, workflow, or executor modules.
- the `ms-python.python` trigger payload fixture remains the primary Week 1-4
  acceptance baseline; keep it frozen as the main broad-coverage reference, but
  do not treat it as the only long-term representative fixture. Plan a second,
  contrast-heavy fixture only after Week 4A and Week 4B are stable.

## Week 4A

### Goal

Close the runtime and reporting correctness gaps that surfaced during Weeks 1-3
without mixing that cleanup into storage or router-state work.

### Scope

- align layered execution reporting so `requested_scenarios`,
  `summary.scenarios_run`, `scenario_traces`, `stimulus_passes`, and
  `event_attempts` describe scenario truth without semantic contradiction
- harden runtime verification semantics so `verification_gap`,
  `automation_health`, attempted-only event attempts, and acceptance-style run
  interpretation stay aligned
- close the current chat/tooling verification gap for `onChatParticipant` and
  `onLanguageModelTool`, including the unresolved
  `harness_verification_unconfirmed` path
- keep this phase focused on runtime/reporting correctness only; do not mix in
  job persistence, migrations, or router/job-state source-of-truth work

### Entry Criteria

- Week 3 planner extraction is stable
- the baseline activation report still reproduces the known reporting and
  verification gaps clearly enough to validate corrections
- executor reporting semantics and chat/tooling verification behavior are
  documented well enough to update without redefining the trigger-planner
  contract

### Exit Criteria

- layered-pass execution exports a consistent scenario lifecycle across
  `requested_scenarios`, `summary.scenarios_run`, `scenario_traces`,
  `stimulus_passes`, and `event_attempts`
- degraded or attempted-only runs no longer read like clean acceptance runs
  when `verification_gap` or related health degraders remain
- `onChatParticipant` and `onLanguageModelTool` attempts have an explicit
  verification closure path, and unresolved cases are reported without
  overstating acceptance completeness

### Status

- Week 4A runtime/reporting work was implemented and revalidated on
  `2026-04-15`.
- layered-pass report invariants are now enforced in
  `packages.analysis_contracts.report_invariants` and covered by
  `tests/platform/contracts/test_analysis_fixture_baselines.py` and
  `tests/executor/test_playwright_monitor.py`.
- executor-side chat/tool verification closure now keeps unresolved official
  `onChatParticipant` and `onLanguageModelTool` attempts out of healthy,
  acceptance-style readings by degrading `automation_health`, capping
  `run_quality`, and preserving the
  `harness_verification_unconfirmed` path when target verification stays open.
- VS Code reload/reconnect handling was hardened in
  `executor/flows/playwright/vscode.py`,
  `executor/flows/playwright/entrypoint.py`, and
  `executor/flows/playwright/reload_vscode.py` so transient CDP states do not
  incorrectly strand layered trigger plans in a not-applied state.
- validation evidence on `2026-04-15` includes a passing `make test` run
  (`422 passed, 3 deselected`) and a passing
  `tests/smoke/test_marketplace_analysis_smoke.py::test_ms_python_layered_analysis_smoke_never_reads_as_clean_when_chat_tool_verification_is_open`
  run after the reload/reconnect hardening.

## Week 4B

### Goal

Move analysis job metadata to durable storage and separate request handling from
job orchestration.

### Scope

- persist analysis job metadata in Postgres
- route all write behavior through the canonical storage layer
- add an Alembic migration for the new job metadata tables
- shrink router responsibility to request/response orchestration
- keep this phase focused on persistence and control-plane cleanup rather than
  runtime/reporting semantics

### Entry Criteria

- Week 4A runtime/reporting correctness work is stable
- storage write path design is agreed and testable

### Exit Criteria

- job metadata survives API restarts
- single-active-job guarantees remain explicit
- router no longer owns process-local job state as the source of truth

### Status

- Week 4B durable-job persistence is now wired through
  `workflows.marketplace.job_service` and `appcore.storage.crud`; the legacy
  `job_store` compatibility layer has been removed.
- Startup now fails fast when `analysis_jobs` storage is unavailable or the
  required migration has not been applied, instead of silently skipping job
  recovery.
- Targeted unit validation passed on `2026-04-16` for the startup/runtime seam
  and marketplace job-worker lane:
  `tests/platform/api/test_app_runtime.py` and the selected
  `tests/workflows/marketplace/test_router.py` job tests.
- DB-backed storage validation also passed on `2026-04-16`:
  `tests/platform/storage/test_analysis_jobs.py`.
- The smoke harness now binds both request-time DB sessions and background
  worker sessions to the real test database via `tests/conftest.py`'s
  `runtime_client` fixture, so `/api/marketplace/analyze/start` no longer
  exercises the `analysis_jobs` path through a mocked `MagicMock` session.
- Week 4B remains `validation pending` until all closure checks pass in an
  environment with Postgres and the executor available.
- Week 4B closure checklist:
  - startup must fast-fail if job storage or migration state is unavailable
  - `tests/platform/storage/test_analysis_jobs.py` must pass against Postgres
  - Alembic upgrade -> downgrade -> upgrade must pass on the test DB
  - `tests/smoke/test_marketplace_analysis_smoke.py::test_ms_python_analysis_smoke`
    must pass with the executor container available
- Current blocker on `2026-04-16`: the smoke acceptance lane reaches the real
  persisted-job path but still fails inside the executor because
  `python3 /home/executor/flows/playwright/reload_vscode.py` hangs during the
  CDP reconnect/reload step and is eventually terminated by the host wrapper
  timeout. Do not mark Week 4B closed until that executor-side smoke failure
  and the Alembic cycle check are both resolved.
- Once the remaining DB-backed and smoke validation is green, the next promoted
  lane stays `Week 4C`; do not mix Week 4C scope into this closure pass.
- Track the remaining post-review follow-ups in
  `documents/REFACTOR_OPTIMIZATION.md`, especially the VSIX re-download
  correctness gap and the broader Week 4C boundary/fixture work.

## Week 5+

Week 5 and later are intentionally deferred. Use
`REFACTOR_EXPANSION_NOTES.md` for candidate follow-on work after Week 4A and
Week 4B are complete and stable. Items promoted into Week 4A are no longer
treated as Week 5+ candidates.
