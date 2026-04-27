# Agent Context

`Last Updated: 2026-04-27`

This is the thin routing map for coding agents after `AGENTS.md`. It should
stay short. Do not copy phase history here; use `REFACTOR_STATUS.md`.

## Source Of Truth

- Current closure state: `REFACTOR_STATUS.md`.
- Deferred/pull-next work: `POST_POC_BACKLOG.md`.
- W8-W13 plan: `REFACTOR_OPTIMIZATION.md` section 11.
- Architecture: `ARCHITECTURE.md`.
- Placement rules: `PROJECT_STRUCTURE.md`.
- Test lanes: `TESTING.md`.

## Current Snapshot

- W7 PoC acceptance is closed.
- PR345 target activation lifecycle is complete.
- W8-0 harness readiness gate landed.
- W8 is eligible to open.
- ADR 0007 is Accepted, but loopback/`EXTRACE_ALLOW_LAN` enforcement is still
  pending W8-7 implementation.

## Task Decision Tree

| If the task touches... | Open this lane first | Then open only if needed |
|---|---|---|
| FastAPI config, DB, schemas, CRUD, migrations | `agent-lanes/platform-storage.md` | `ARCHITECTURE.md`, `PROJECT_STRUCTURE.md`, `TESTING.md` |
| Marketplace search/download/analyze jobs, trigger planning | `agent-lanes/marketplace-analysis.md` | `PIPELINE_ROADMAP.md`, `VSCODE_API_COVERAGE_AUDIT.md` |
| Docker executor, Playwright, harness, runtime capture | `agent-lanes/executor-runtime.md` | `EXECUTOR_PLAYWRIGHT.md`, relevant runbook |
| Detection rules, malicious fixtures, ADR security posture | `agent-lanes/security-detection.md` | ADRs 0002-0005, `DETECTION_SEMANTICS.md` |
| React/Vite UI or generated TS contracts | `agent-lanes/ui.md` | `ui/README.md`, UI tests |
| Documentation drift, README, runbooks, ADR text | `agent-lanes/docs-maintenance.md` | `documents/README.md`, current code/tests |

## Core Paths

- Entry point: `main.py`.
- Backend: `appcore/`, `workflows/`, `executor/`.
- Framework-agnostic packages: `packages/`.
- Frontend: `ui/`.
- Tests: `tests/`.
- Docs: `documents/`, with lane docs under `documents/agent-lanes/`.

## Minimal Rules Reminder

- DB writes go through `appcore/storage/crud.py`.
- Pydantic validation happens before insert.
- Sandbox execution stays Docker-isolated.
- `packages/` remains framework-agnostic.
- Detection rules consume contracts only.
- Matching tests should be opened early.

## Useful Commands

- `make test-local`
- `make check-all`
- `make test-security`
- `make exec-up`
- `make exec-run`
- `make sim-target TARGET=publisher.name`
- `make demo-canary`
