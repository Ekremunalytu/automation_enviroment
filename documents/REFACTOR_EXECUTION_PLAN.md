# Refactor Execution Plan

`Last Updated: 2026-04-15`

This is the canonical execution plan for the current refactor. It keeps the
first four weeks decision-complete and intentionally defers heavier Week 5+
ideas into a separate note: `REFACTOR_EXPANSION_NOTES.md`.

## Context

- ExTrace is staying a single-host appliance for this refactor cycle.
- Docker-isolated sandbox execution remains mandatory.
- The catalog/storage path is stable enough to avoid broad churn right now.
- The dynamic-analysis path needs smaller boundaries before deeper runtime
  changes are safe.
- This week is intentionally light: no runtime rewiring, no schema migration,
  no API contract change.

## Locked Decisions

- Keep the first four weeks as the binding execution plan.
- Treat Week 5+ as non-binding expansion notes until Week 4 is complete.
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

## Week 4

### Goal

Move analysis job metadata to durable storage and separate request handling from
job orchestration.

### Scope

- persist analysis job metadata in Postgres
- route all write behavior through the canonical storage layer
- add an Alembic migration for the new job metadata tables
- shrink router responsibility to request/response orchestration

### Entry Criteria

- Week 3 planner extraction is stable
- storage write path design is agreed and testable

### Exit Criteria

- job metadata survives API restarts
- single-active-job guarantees remain explicit
- router no longer owns process-local job state as the source of truth

## Week 5+

Week 5 and later are intentionally deferred. Use
`REFACTOR_EXPANSION_NOTES.md` for candidate follow-on work after Week 4 is
complete and stable.
