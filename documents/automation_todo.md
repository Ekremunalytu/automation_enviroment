# Dynamic Analysis Roadmap

`Last Updated: 2026-04-13`

This roadmap tracks the current state of the post-refactor dynamic-analysis stack.

It assumes the current product shape stays the same:

- single analyst
- same-device or same-host deployment
- one active sandbox analysis at a time
- file-backed reports remain acceptable operator artifacts

## Current State

### Delivered

- Canonical workflow split into `appcore/` and `workflows/`
- Marketplace search endpoint and HTTP client
- Marketplace download flow with `.vsix` extraction
- Extension registration from downloaded directories
- Executor container split into `executor/container/` and `executor/flows/playwright/`
- Synchronous analysis endpoint: `POST /api/marketplace/analyze`
- Background analysis endpoint: `POST /api/marketplace/analyze/start`
- Persisted background job snapshots under `output/analysis_jobs/`
- Activation report browsing via `GET /api/activations*`
- React SPA routes for `Reports`, `Simulation`, and `Marketplace`
- Canonical import coverage in `tests/platform/test_canonical_imports.py`

### Partially Delivered

- Smart trigger selection based on stored activation events and contributes metadata
- Sandbox reset and reload orchestration
- Executor monitoring/report generation

### Not Delivered Yet

- Risk scoring engine
- Stronger report truthfulness around degraded runs
- Better operator guidance around interrupted or failed analyses

## Active Priorities

### 1. Analysis Reliability

- Treat required VS Code reload failures as hard analysis failures where appropriate
- Remove broad fallback paths that hide trigger-generation errors
- Close workspace-path mismatches that can prevent some triggers from firing
- Expand end-to-end tests around `POST /api/marketplace/analyze/start`

### 2. Results Persistence

Keep persistence intentionally light:

- preserve clear JSON report artifacts in `output/`
- preserve job snapshots in `output/analysis_jobs/`
- only add DB persistence if the product needs cross-run history badly enough to justify it

### 3. Telemetry Ingestion

Continue normalizing report data for the UI and risk engine without assuming DB-backed storage:

1. parse activation report JSON
2. normalize to appcore-compatible contracts where helpful
3. adapt for UI review surfaces
4. keep the raw JSON artifact as the source of operational truth

### 4. Risk Scoring

Implement a first-pass scorer for:

- unexpected outbound traffic
- suspicious filesystem access
- credential harvesting patterns
- unexpected child processes
- always-on or unusually broad activation profiles

## Suggested Next Milestones

### Milestone A: Durable Analysis Runs

- Make interrupted runs explicit in job snapshots
- Keep one-analysis-at-a-time behavior obvious in the UI
- Improve operator-facing retry guidance when a run is interrupted

### Milestone B: Telemetry Parsers

- Promote monitor output parsing into canonical workflow code
- Add tests for normalization of network/process/filesystem events

### Milestone C: UI Enrichment

- Add stronger per-run risk summary and drill-downs
- Keep live simulation and final report views consistent
- Keep route state URL-driven so drill-down views remain shareable

## Architectural Guardrails

- Keep executor-specific code under `executor/`
- Keep workflow orchestration in `workflows/marketplace/`
- Keep shared persistence and contracts in `appcore/`
- Do not add new logic to legacy compatibility modules
