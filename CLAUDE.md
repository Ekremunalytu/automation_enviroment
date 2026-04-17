# CLAUDE.md

`Last Updated: 2026-04-17`

Read `AGENTS.md` first. It is the authoritative source for architecture and
safety rules. This file is the Claude-facing project map; it stays aligned
with the current phase of the refactor.

## Current Project Phase

- **Refactor Weeks 1-4B**: complete (validated 2026-04-16).
- **Week 4C-4E (W1-W4 in the 7-week window)**: stabilization of automation —
  legacy cleanup, import-graph enforcement, executor determinism, executor
  modularization, sandbox boundary.
- **W0 (security foundations, spec-only)**: complete (2026-04-17). Three ADRs
  define threat model, detection taxonomy, and malicious fixture policy.
- **W5-W7**: security implementation phase — detection rules, malicious
  fixture corpus, UI detection surface.

**PoC-priority framing (2026-04-17):** the 7-week window is scoped at a
**proof-of-concept acceptance bar**. Full-product scope is preserved
in the ADRs; the PoC framing selects which parts are Must vs Stretch
without removing anything. PoC must-classes are A1/A2/A4/A6 (ADR 0002);
T1 synthetic canaries are the required fixture tier (ADR 0004); the
rule lifecycle collapses Draft → Production in a single pass during
PoC (ADR 0003 §7). See `documents/REFACTOR_OPTIMIZATION.md` §10 for
the weekly Must/Stretch split and §10.7 for the PoC acceptance
checklist.

The binding execution plan is `documents/REFACTOR_EXECUTION_PLAN.md`; the
critique and 7-week window live in `documents/REFACTOR_OPTIMIZATION.md`
(§10). If this file conflicts with either, trust those.

## Scope First

- Do not load the whole repo.
- Pick one lane and stay inside it until you have enough evidence.
- Open the matching tests early.
- Ignore `extensions/`, `output/`, `node_modules/`, `legacy_ui/`, and
  `__pycache__/` unless the task explicitly depends on them.
- `routers/`, `scanner/`, `core/`, `database/`, `crud/`, `models/`,
  `schemas/` are **legacy leftovers** (only `__pycache__` inside). Do not
  put new code here. Deletion is tracked under W1 (§7.4.3).

## Start Files By Task

- Platform/config:
  - `main.py`
  - `appcore/api/config.py`
  - `appcore/api/deps.py`
  - `appcore/db/session.py`
  - `tests/platform/`
- Catalog/API:
  - `workflows/extension_catalog/router.py`
  - `workflows/extension_catalog/service.py`
  - `appcore/contracts/schemas.py`
  - `appcore/storage/crud.py`
  - `tests/workflows/extension_catalog/`
- Activation reports:
  - `workflows/activation_reports/router.py`
  - `tests/workflows/activation_reports/test_router.py`
- Marketplace/analysis (durable jobs):
  - `workflows/marketplace/router.py`
  - `workflows/marketplace/client.py`
  - `workflows/marketplace/analysis_service.py`
  - `workflows/marketplace/job_service.py` (durable job persistence)
  - `workflows/marketplace/trigger_service.py`
  - `tests/workflows/marketplace/`
- Contracts and planner (shared packages):
  - `packages/analysis_contracts/` (Pydantic v2 contracts; backend-owned)
  - `packages/analysis_planner/` (trigger planner)
  - `packages/analysis_engine/`
- Executor:
  - `executor/host.py`
  - `executor/flows/playwright/`
  - `tests/executor/`
- UI:
  - `ui/src/app/`
  - relevant `ui/src/features/`
  - `ui/src/lib/api/`
  - colocated `*.test.ts(x)`
- Security (W5+):
  - `documents/adrs/0002-threat-model.md`
  - `documents/adrs/0003-detection-taxonomy.md`
  - `documents/adrs/0004-malicious-fixture-policy.md`
  - `extensions/malicious/` (planned, W5)
  - `tests/security/` (planned, W5)

## Canonical Layout

- Shared platform: `appcore/`
- Reusable packages (framework-agnostic): `packages/`
- Business workflows: `workflows/`
- Sandbox runtime: `executor/`
- Analyst UI: `ui/`
- Tests: `tests/`

## Hard Rules

- Preserve `(publisher, name, version)` uniqueness.
- Route DB writes through `appcore/storage/crud.py`.
- Validate with Pydantic v2 before insert.
- Use SQLAlchemy 2.0 and Pydantic v2 only.
- Add Alembic migration for schema changes.
- Keep sandbox execution inside Docker.
- Do not add dependencies without explicit approval (ADR required).
- No generic `try/except Exception`.
- `packages/` must stay framework-agnostic (no imports from `workflows/`,
  `executor/`, `ui/`, `appcore/`). Banned-import boundary test exists for
  `packages.analysis_planner`; W1 extends this to all of `packages/`.

## Security-Specific Rules (W0 ADRs)

These are binding once W5 implementation begins; currently spec-only.

- Detection rules live under `packages/` and see only contracts
  (ADR 0003 §8).
- Every malicious fixture carries a `LABEL.yaml` manifest with tier
  (T1/T2/T3), source SHA256, and expected detections (ADR 0004 §3).
- `make test-security` runs T1+T2 only; T3 live samples use
  `make test-security-live` and refuse to run in CI (ADR 0004 §4).
- `inconclusive` verdict dominates `clean` when verification gaps remain
  (ADR 0003 §5). Never claim cleanliness on incomplete observation.
- Analysis output is semi-trusted; UI must not render `dangerouslySetInnerHTML`
  on report string fields (ADR 0002 §6).

## Verified Runtime Surfaces

- `main.py` includes only:
  - `workflows.extension_catalog.router`
  - `workflows.activation_reports.router`
  - `workflows.marketplace.router`
- Root/catalog endpoints remain on root paths.
- Activation reports live under `/api/activations`.
- Marketplace endpoints live under `/api/marketplace`.
- Durable analysis jobs are persisted through `appcore.storage.crud`
  (Week 4B closure, 2026-04-16). `workflows/marketplace/job_store.py`
  has been removed; only `job_service.py` remains.

## Known Debt (for triage before acting)

- `executor/flows/playwright/monitor.py` — 3993 LOC god-module. Split
  planned in W3 (capture/ subpackage).
- VS Code `stable` channel unpinned in `executor/container/Dockerfile`.
  Pin planned in W2 (determinism + security attribution property).
- Single baseline fixture (`ms-python.python`). Second/third benign
  fixture planned in W1; malicious T1-T3 corpus in W5.
- `apps/api`, `apps/ui` directories contain only `README.md` (half-empty
  skeleton). Decision pending in W1 (delete or populate).
- `tests/architecture/` does not exist; import-graph enforcement is
  `packages.analysis_planner`-only. Full graph enforcement planned in W1.

## Multi-Agent Operation

This project uses both Claude (planning, review, docs) and GPT
(implementation) in parallel. Lane discipline:

- Claude writes under `documents/` by default; code changes only when the
  user explicitly asks.
- GPT owns code changes under `appcore/`, `workflows/`, `executor/`, `ui/`.
- Shared contract: `documents/REFACTOR_OPTIMIZATION.md` (§10.4 lane map).
- Stale findings are marked `⚠ STALE (date)`, not deleted.
- New review passes append `### 9.N (date, agent)` blocks rather than
  rewriting.

## Useful Commands

```bash
make dev
make test-local
make test-unit          # planned (W1): piramit ayrımı
make test-integration   # planned (W1)
make test-smoke
make test-security      # planned (W5): T1+T2 fixtures, no external egress
make check-all
make migrate
make exec-up
make exec-run
make ui-up
```

## Docs Priority

1. `AGENTS.md` — hard rules
2. This file — Claude-facing quickstart
3. `documents/REFACTOR_EXECUTION_PLAN.md` — binding weekly plan (1-4B)
4. `documents/REFACTOR_OPTIMIZATION.md` — plan critique + 7-week window
5. `documents/adrs/` — ADR 0001-0004, binding once accepted
6. Subsystem docs (`ARCHITECTURE.md`, `EXECUTOR_PLAYWRIGHT.md`,
   `DETECTION_SEMANTICS.md`) — load only when the task touches that area
