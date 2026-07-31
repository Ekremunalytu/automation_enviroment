# AGENTS.md

`Last Updated: 2026-07-31`

`Last merged weekly: W22 — closed synthetically on the week22 branch, merged to main via PR #31 week22 -> main 2026-05-28 via 1399f82.`

`Active named stream: static-analysis-artifact-precision (SAP-0..SAP-6), stacked on the unmerged SMF head. Latest merged named stream: verdict-provenance-reproducibility (W26), PR #38 at bfb2d2d. Containment safety remains the next product/release gate in documents/active-work/v1-roadmap.md §4.`

## Authority

- This is the hard-rules entrypoint. Route tasks through
  `documents/AGENT_CONTEXT.md`.
- Current state: `documents/phase.json` (machine-readable) and
  `documents/REFACTOR_STATUS.md` (human-readable).
- Deferred work: `documents/POST_POC_BACKLOG.md`; last weekly plan:
  `documents/REFACTOR_OPTIMIZATION.md` §20.
- If docs conflict with code or tests, trust code/tests and update the doc.
- Stop and report requests that violate these rules.

## Non-Negotiable Rules

- Preserve the unique constraint `(publisher, name, version)`.
- Route writes through `appcore/storage/crud.py`; wrappers may only delegate.
- Validate with Pydantic before database insertion.
- Use SQLAlchemy 2.0 syntax only.
- Use Pydantic v2 APIs only.
- Add an Alembic migration for schema changes.
- Keep sandbox execution isolated in Docker.
- Do not introduce dependencies without explicit approval.
- Do not add generic `try/except Exception` blocks.
- No arbitrary exec, unsafe deserialization, or uncontrolled network calls.
- Treat extension input, reports, logs, and VSIX contents as adversarial.
- Keep critical operations observable.

## Architecture Boundaries

- Runtime entrypoint: `main.py`.
- Backend: `appcore/`, `workflows/`, `executor/`; frontend: `ui/`;
  framework-agnostic analysis: `packages/`.
- Tests live under `tests/`; UI tests live under `ui/src/**/*.test.ts(x)`.
- `packages/` must not import `workflows/`, `executor/`, `ui/`, or
  `appcore/`.
- Dynamic detection rules live in `packages/analysis_engine/rules/`; static
  pre-check rules live in `static_runtime/rules/`. Both may only consume
  contracts and their allowed stdlib/shared-contract helpers.
- Workflows reach sandbox mechanics through `executor.control`.
- Do not recreate legacy top-level business directories such as `routers/`,
  `scanner/`, `core/`, `database/`, `crud/`, `models/`, or `schemas/`.

## Read Path

1. Read `documents/AGENT_CONTEXT.md`.
2. Read exactly one matching `documents/agent-lanes/*.md`.
3. Open subsystem or `active-work` docs only when that lane points to them.
4. Read matching tests early.
5. Keep `documents/archive/` off-path unless a slim canonical explicitly
   links to it.

## Context Budget

- Start from one task lane and expand only when evidence requires it.
- Ignore heavy/generated trees unless the task explicitly targets them:
  `extensions/`, `output/`, `node_modules/`, `ui/dist/`, `__pycache__/`,
  `.venv/`, `.mypy_cache/`, `.ruff_cache/`.
- Prefer `rg` / `rg --files` for search.

## Required Self-Review

State files modified, DB schema change (Yes/No), tests changed (Yes/No), and
risks/assumptions.
