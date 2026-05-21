# Contributing to ExTrace

`Last Updated: 2026-04-24`

ExTrace is a single-user sandbox appliance for VS Code extension analysis.
This guide gives human contributors a fast path from clone to green tests.
Agent-facing rules live in [`AGENTS.md`](AGENTS.md) and take precedence over
anything here.

## Before You Change Anything

1. Read [`AGENTS.md`](AGENTS.md). The Non-Negotiable Rules section is not
   advisory — CI enforces the import-graph and boundary checks.
2. Skim [`documents/AGENT_CONTEXT.md`](documents/AGENT_CONTEXT.md) to find
   which files your task actually touches. Avoid loading the whole repo.
3. For the current phase and deferred items, see
   [`documents/REFACTOR_STATUS.md`](documents/REFACTOR_STATUS.md) and
   [`documents/POST_POC_BACKLOG.md`](documents/POST_POC_BACKLOG.md).

## Prerequisites

- Python 3.11+
- Docker / Docker Compose
- PostgreSQL 16 compatible runtime (local or via Docker)
- Node 20+ (for UI work)

## First-Time Setup

```bash
make install-dev        # creates .venv, installs backend + dev deps, UI deps
make up                 # brings up Postgres + app via Docker Compose
make migrate            # applies Alembic migrations
make dev                # runs the FastAPI app locally (alternative to `make up`)
```

Service endpoints (once up):

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Web UI: `http://localhost:3000`
- noVNC executor view: `http://localhost:6080/vnc.html`

## Test Lanes

Run the lane that matches what you touched. `make check-all` is the
pre-push gate.

```bash
make test-local         # fast unit tests (no DB, no smoke)
make test-security      # offline detection + malicious fixture scaffold (T1/T2)
make test-security-live # live tshark capture path (fragile, break-glass)
make check-all          # full lane: type checks, import graph, UI boundary + typecheck, pytest
make ui-types-check     # regenerates + diffs ui/src/lib/types/contracts.ts
make ui-boundaries      # feature-boundary import lints in ui/
.venv/bin/pytest -m smoke           # end-to-end marketplace analysis
.venv/bin/pytest -m "requires_db"   # DB-dependent tests only
```

Executor / sandbox:

```bash
make exec-up                        # bring up the executor container
make exec-run                       # run the entrypoint against a target extension
make sim-target TARGET=publisher.name [TRIGGERS=…] [SCENARIO=…]
make sim-all                        # UI-stimulus stress run (no target extension)
```

UI dev:

```bash
cd ui && npm run dev                # Vite dev server on :3000
cd ui && npm run test               # Vitest
```

## Boundaries That Will Break CI If You Cross Them

These are mechanically enforced. If you are about to import across one of
these lines, the design is probably wrong — reach for the boundary module
listed below instead.

- `packages/` must not import from `workflows/`, `executor/`, `ui/`, or
  `appcore/`. Packages are framework-agnostic.
- Workflows reach sandbox mechanics through `executor/control.py`. Do not
  import `executor.host` or `executor.flows.*` from workflows.
- All DB writes go through `appcore/storage/crud.py`. No bypassing with raw
  `Session.add(...)` in workflow code.
- Top-level legacy dirs (`routers/`, `scanner/`, `core/`, `database/`,
  `crud/`, `models/`, `schemas/`) are not canonical — do not add new code
  there.

## Code Style

- **Python:** Pydantic v2 and SQLAlchemy 2.0 only. No `try/except Exception`
  without a narrower replacement. No generic bare `except`.
- **TypeScript:** regenerate `ui/src/lib/types/contracts.ts` from backend
  schemas (`scripts/generate_ui_contracts.py`) rather than hand-editing.
- **Tests first where possible:** open the matching `tests/` lane early to
  see the intended behavior before touching code.
- **No new dependencies** without explicit approval in the PR description.

## Schema Changes

Any change to `appcore/storage/models.py` or `appcore/contracts/schemas.py`
that affects persisted shape needs:

1. Matching Alembic migration under `alembic/versions/`.
2. `make migrate` applied locally.
3. Updated fixtures / round-trip test coverage.
4. `(publisher, name, version)` uniqueness preserved.

## Commit Message Style

Matches the existing `git log` — imperative mood, capitalized first word,
under ~80 chars. Body explains the *why*, not a diff summary.

Examples from history:

```text
Harden executor against UI crashes and scan-between install races
Close W7: add A3 typosquat rule + demo acceptance, fix settings.json helper
Enforce detection correctness: attribution, TLS vocab, error dominance
```

## Pull Request Expectations

- One coherent change per PR. Mixed refactor + bug-fix PRs are hard to review.
- `make check-all` green locally before pushing.
- Touching the executor? Also run `make test-security` and, if the change
  could affect capture, a live `make exec-up && make exec-run` smoke.
- Touching the detection layer? Verify the T1 canaries under
  `extensions/malicious/` still behave as labelled in their `LABEL.yaml`.
- Touching docs? Verify every factual claim against code, tests, config, or
  runtime output. Stale docs are worse than missing docs.

## Security Posture

Threat model, detection taxonomy, fixture policy, and package charter are
fixed by ADRs 0002-0005 under [`documents/adrs/`](documents/adrs/). Read the
relevant ADR before adding or changing a detection rule. Malicious fixtures
follow ADR 0004: T1 canaries run in CI; T3 live samples never do.

## Where to Ask

- Architecture / placement questions: [`documents/ARCHITECTURE.md`](documents/ARCHITECTURE.md),
  [`documents/PROJECT_STRUCTURE.md`](documents/PROJECT_STRUCTURE.md).
- Test layout: [`documents/TESTING.md`](documents/TESTING.md).
- Executor / sandbox internals: [`documents/EXECUTOR_PLAYWRIGHT.md`](documents/EXECUTOR_PLAYWRIGHT.md).
- Detection semantics: [`documents/DETECTION_SEMANTICS.md`](documents/DETECTION_SEMANTICS.md).
- Current risks: [`docs/risks.md`](docs/risks.md).
- Recovering from a specific failure mode (stuck job, fatal UI crash,
  scan-between install failure, live capture regression):
  [`documents/runbooks/`](documents/runbooks/).
