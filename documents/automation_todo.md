# Dynamic Analysis Roadmap

`Last Updated: 2026-03-06`

This roadmap tracks the current state of the post-refactor dynamic-analysis stack.

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
- Streamlit pages for `Dashboard`, `Simulation`, `Marketplace`, `Theme`
- Canonical import coverage in `tests/platform/test_canonical_imports.py`

### Partially Delivered

- Smart trigger selection based on stored activation events and contributes metadata
- Sandbox reset and reload orchestration
- Executor monitoring/report generation

### Not Delivered Yet

- Database schema for dynamic-analysis runs and telemetry events
- Risk scoring engine
- Automated ingestion of analysis reports into PostgreSQL
- End-to-end orchestration beyond file-backed activation reports

## Active Priorities

### 1. Analysis Reliability

- Treat required VS Code reload failures as hard analysis failures where appropriate
- Remove broad fallback paths that hide trigger-generation errors
- Close workspace-path mismatches that can prevent some triggers from firing
- Expand end-to-end tests around `POST /api/marketplace/analyze/start`

### 2. Results Persistence

Add Alembic-backed tables for:

- `analysis_runs`
- `analysis_network_events`
- `analysis_process_events`
- `analysis_fs_events`
- `analysis_risk_signals`

Rule:

- Keep all writes inside `appcore.storage.crud`
- Validate new payloads with Pydantic before insertion

### 3. Telemetry Ingestion

Move from file-only output to a dual model:

- filesystem artifacts remain the raw source of truth
- structured summaries are persisted to PostgreSQL

Planned ingestion stages:

1. parse activation report JSON
2. parse monitor output
3. normalize to appcore contracts
4. persist with CRUD

### 4. Risk Scoring

Implement a first-pass scorer for:

- unexpected outbound traffic
- suspicious filesystem access
- credential harvesting patterns
- unexpected child processes
- always-on or unusually broad activation profiles

## Suggested Next Milestones

### Milestone A: Durable Analysis Runs

- Add DB tables and schemas for analysis runs
- Persist run metadata from marketplace analysis endpoints
- Link report files to a stable run record

### Milestone B: Telemetry Parsers

- Promote monitor output parsing into canonical workflow code
- Add tests for normalization of network/process/filesystem events

### Milestone C: UI Enrichment

- Show run history, not only live file-backed reports
- Add per-run risk summary and drill-downs

## Architectural Guardrails

- Keep executor-specific code under `executor/`
- Keep workflow orchestration in `workflows/marketplace/`
- Keep shared persistence and contracts in `appcore/`
- Do not add new logic to legacy compatibility modules
