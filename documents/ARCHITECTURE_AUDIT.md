# Architecture Audit

`Last Updated: 2026-04-20`

This is the short health summary for the current architecture. Use
`ARCHITECTURE.md` for structure and flows; use `docs/risks.md` for the live
risk register.

## What Is Healthy

- Ownership boundaries are now mechanically enforced:
  - `packages/` stays framework-agnostic
  - `executor/` avoids `appcore/` and `workflows/`
  - workflows reach sandbox mechanics through `executor.control`
- Catalog persistence and durable analysis-job state both route through
  `appcore/storage/crud.py`.
- Async analysis is decomposed into router, analysis service, trigger planning,
  executor control, and job storage instead of one opaque path.
- The executor runtime is less monolithic than before:
  `runtime_capture/`, scenario helpers, and health/signal support modules now
  carry part of the surface.
- The UI now has generated backend-owned contract types plus feature-boundary
  checks.

## What Still Carries Risk

- Executor reliability still defines product truthfulness.
- Activation reports remain artifact-first in `output/`.
- Harness-extension checksum verification is still pending as a W5 task.
- The malicious-fixture scaffold exists, but dedicated CI security wiring is
  still incomplete.

## Recommended Reading By Problem Type

- Architecture question: `ARCHITECTURE.md`
- Placement question: `PROJECT_STRUCTURE.md`
- Runtime reliability question: `EXECUTOR_PLAYWRIGHT.md` + `docs/risks.md`
- Coverage or report-semantics question:
  - `VSCODE_API_COVERAGE_AUDIT.md`
  - `DETECTION_SEMANTICS.md`
- Security scaffold question:
  - `documents/adrs/0004-malicious-fixture-policy.md`
  - `tests/security/`
