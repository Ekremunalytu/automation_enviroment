# Test Layout

`Last Updated: 2026-06-04`

Layered map of `tests/`. Coordinates with [`../TESTING.md`](../TESTING.md)
(layer purpose, fixtures, commands). This file is the structural skeleton —
where files live; `TESTING.md` is the operational guide — what to run.

## Top-Level Map

```text
tests/
  conftest.py
  test_health.py
  architecture/        repo-wide import graph + AST regression detectors
  executor/            Playwright + executor-host coverage
    scanner/           Docker exec wrapper unit coverage
    security/          W8-3 URI trigger argv-form regression lane
  platform/            shared platform contracts, config, storage
    api/
    contracts/
    engine/
    storage/
    security/          W8-6 and future W8-8 platform security tests
  security/            malicious-fixture hygiene + PoC canary contracts
    rules/             A1-A8 dynamic rule tests
  smoke/               end-to-end marketplace analysis acceptance
  workflows/
    activation_reports/
    extension_catalog/
    marketplace/
      fixtures/
```

UI tests live under `ui/src/**/*.test.ts(x)` (Vitest + Testing Library).

## Layer Responsibilities

- **`tests/architecture/`** — import-graph rules
  (`packages/` → no workflows/executor/ui/appcore), W8-2 marketplace
  identity concat detector, W8-3 shell-template detector. New
  cross-cutting rules land here.
- **`tests/platform/`** — API runtime, deps, fixtures, contracts
  (verdict rollup, detection report, schemas), engine rule runner,
  storage CRUD + analysis_jobs.
- **`tests/executor/`** — Playwright automation, commands, crash
  classifier, entrypoint, helpers, monitor attribution/lifecycle/runtime,
  reload, stimulus, reset_state, signal policy, workspace.
- **`tests/executor/security/`** — adversarial subprocess invocation
  tests for the URI trigger (W8-3); future executor-local security
  regressions land here.
- **`tests/executor/scanner/`** — focused unit coverage for the Docker
  exec wrapper.
- **`tests/security/`** — `LABEL.yaml` hygiene, canary end-to-end
  contracts, `make test-security` lane composition; `rules/` holds the
  A1..A6 rule tests.
- **`tests/smoke/`** — exercises the executor container against
  marketplace analysis; user-side gate.
- **`tests/workflows/`** — router/service/parser/job_service tests for
  each workflow.

## Lane Composition

- `make test-local` — fast in-process suite (most of `tests/platform/`,
  `tests/architecture/`, `tests/workflows/`).
- `make test-security` — `tests/security/`. W8-1 + W8-3 land in
  subsystem-local lanes (`tests/workflows/marketplace/test_vsix_*`,
  `tests/executor/security/test_uri_trigger_*`); cross-tree composition
  landed during W8 acceptance.
- `make check-all` — ruff + mypy + bandit + ui-types-check +
  ui-boundaries + pytest.
- `make test-security-live` — T2/T3 lane; gated by ADR 0004 isolation.

## Where New Tests Go

| Area touched | Test directory |
|---|---|
| Import graph or AST regression | `tests/architecture/` |
| Contract or schema | `tests/platform/contracts/` |
| Storage / migration | `tests/platform/storage/` |
| Detection rule (A1..A7) | `tests/security/rules/` |
| Malicious fixture hygiene | `tests/security/` |
| Executor-side security regression | `tests/executor/security/` |
| Workflow router/service | `tests/workflows/<workflow>/` |
| End-to-end smoke | `tests/smoke/` |
| UI component | colocated `*.test.tsx` next to source |
