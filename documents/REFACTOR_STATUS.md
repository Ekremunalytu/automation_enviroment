# Refactor Status

`Last Updated: 2026-04-17`

This is the active status board for the Week 1-4 stabilization work. Use this
file for current closure state; use `REFACTOR_EXECUTION_PLAN.md` for sequence
and rationale.

## Authoritative Read Order

1. `AGENTS.md`
2. `documents/AGENT_CONTEXT.md`
3. this file
4. `documents/REFACTOR_EXECUTION_PLAN.md`
5. subsystem-specific docs only when the task reaches them

## Current State

- Week 4 closure is the active gate before any Week 5 detection work.
- Async marketplace job state is durable in PostgreSQL via `analysis_jobs`.
- Activation reports remain artifact-first under `output/activation_report_*.json`.
- Workflow code now depends on the sandbox through `executor.control`.
- Root legacy directories (`routers/`, `scanner/`, `core/`, `database/`,
  `crud/`, `models/`, `schemas/`) are removed from the canonical repo surface.

## Week 4 Exit Criteria

- Repo-wide import graph checks pass.
- Executor retry / cleanup / checksum / monotonic timing work is in place.
- UI contract generation drift checks and feature-boundary checks are wired into
  CI and local `make check-all`.
- Benign baseline corpus includes:
  - `ms-python.python`
  - `extrace.fixture-chat`
  - `extrace.fixture-theme`
- The color-theme baseline proves scenario-zero semantics through the
  marketplace analysis flow without entering smoke acceptance.
- Smoke acceptance stays focused on `ms-python.python` and
  `extrace.fixture-chat`.

## Week 5 Start Rule

Week 5 begins only after the Week 4 exit criteria above are green. Detection
work does not reopen Week 4 refactors except to fix a blocking regression.
