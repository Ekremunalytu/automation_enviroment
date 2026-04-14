# Pipeline Roadmap

`Last Updated: 2026-04-14`

This roadmap reflects the current pipeline after the refactor and the first
pass of trigger planning, report health, risk signals, and verdict output.

The roadmap still assumes a single-user sandbox appliance, not a distributed
analysis platform.

## Current Pipeline

```mermaid
flowchart LR
    UI["React UI"] --> API["FastAPI marketplace workflow"]
    API --> DL["Marketplace download/extract"]
    DL --> DB["Validated catalog persistence"]
    API --> JOB["Async job store (`output/analysis_jobs`)"]
    API --> PLAN["Trigger planning"]
    PLAN --> HOST["`executor.host`"]
    HOST --> EXEC["Playwright entrypoint"]
    EXEC --> MON["monitor + health + signals + report_builder"]
    MON --> REPORT["`output/activation_report_*.json`"]
```

## Phase A: Tighten Runtime Truthfulness

- keep reset/install/reload failures explicit
- ensure missing or unapplied trigger payloads do not look benign
- make interrupted jobs obvious after API restarts
- define retention and cleanup expectations for job snapshots and reports

## Phase B: Close Coverage Gaps

- keep official activation coverage and heuristic workflow coverage separate
- close missing support for `chat`, `comments`, `testing`, and
  `workspace_trust`
- improve official-track verification for `scm` and `settings`
- keep per-event attempt ledgers readable for analysts

## Phase C: Stabilize the Report Contract

- preserve stable JSON fields for the React adapters
- refine degraded vs inconclusive semantics
- keep attribution summary, risk summary, and verdict reasons aligned
- version the report contract deliberately as semantics evolve

## Phase D: Calibrate Analyst Signal Quality

- tune risk scoring and verdict thresholds against real fixtures
- improve operator guidance when a run is degraded or interrupted
- keep live simulation and final report views consistent

## Design Constraints

- workflow orchestration belongs in `workflows/marketplace/`
- shared contracts and catalog persistence belong in `appcore/`
- sandbox mechanics belong in `executor/`
- dynamic-analysis persistence remains artifact-first unless product needs
  justify more structure
- do not assume queue workers, tenancy, or distributed ownership without an
  explicit product change
