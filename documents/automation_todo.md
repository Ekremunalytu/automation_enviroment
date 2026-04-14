# Dynamic Analysis Roadmap

`Last Updated: 2026-04-14`

This roadmap tracks the current state of the dynamic-analysis stack after the
architecture split and layered trigger/report work.

It still assumes:

- single analyst
- same-device or same-host deployment
- one active sandbox analysis at a time
- file-backed reports remain acceptable operator artifacts

## Current State

### Delivered

- canonical split into `appcore/`, `workflows/`, `executor/`, and `ui/`
- marketplace search, download, and validated catalog registration
- synchronous analysis endpoint: `POST /api/marketplace/analyze`
- background analysis endpoint: `POST /api/marketplace/analyze/start`
- persisted background job snapshots under `output/analysis_jobs/`
- layered trigger payload generation from stored activation/contributes metadata
- container-side trigger loading and layered stimulus passes
- report health, attribution summary, risk signals, and verdict output
- activation report browsing under `/api/activations`
- SPA routes for Marketplace, Simulation, and Reports

### Partially Delivered

- official vs heuristic coverage separation
- executor failure messaging and degraded-run guidance
- retention and cleanup discipline for report/job artifacts
- end-to-end smoke depth beyond the pinned `ms-python.python` fixture

### Not Delivered Yet

- first-class support for `chat`, `comments`, `testing`, and
  `workspace_trust`
- durable run-history querying beyond JSON artifacts
- fully closed official-track verification for `scm` and `settings`

## Active Priorities

### 1. Analysis Reliability

- fail closed on reset/install/reload/trigger-load problems
- keep interrupted jobs explicit after API restarts
- expand coverage around async job lifecycle and degraded states

### 2. Coverage Fidelity

- keep official activation coverage separate from heuristic workflow coverage
- improve per-event verification status truthfulness
- close missing capability support without blurring the matrix

### 3. Report Contract Discipline

- keep report JSON stable for the React UI
- preserve sharp semantics for degraded vs inconclusive runs
- keep risk signals and verdict reasons evidence-linked

### 4. Operational Hygiene

- define retention/cleanup behavior for `output/`
- keep one-analysis-at-a-time behavior obvious to operators
- avoid unnecessary persistence layers until query pain is real

## Suggested Next Milestones

### Milestone A: Honest Failure Surfaces

- make all executor failure paths visible in job steps and report health
- keep missing trigger payloads from producing misleadingly clean outcomes

### Milestone B: Coverage Closure

- add support for missing capability families
- tighten official-track verification for `scm` and `settings`

### Milestone C: Artifact Operations

- document retention expectations for reports and job snapshots
- add lightweight cleanup tooling only if operators need it

## Architectural Guardrails

- keep executor-specific code under `executor/`
- keep workflow orchestration in `workflows/marketplace/`
- keep shared persistence and contracts in `appcore/`
- do not add new feature logic to archival or historical surfaces
