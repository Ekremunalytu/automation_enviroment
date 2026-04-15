# Architecture Audit

`Last Updated: 2026-04-15`

This is the short health summary for the current architecture. Use
`ARCHITECTURE.md` for structure and flows; use `docs/risks.md` for the live risk
register.

## What Is Healthy

- Ownership boundaries are clear:
  - `appcore/` for shared platform code
  - `workflows/` for business orchestration
  - `executor/` for sandbox runtime
  - `ui/` for the analyst console
- Catalog persistence still has one write boundary through
  `appcore/storage/crud.py`.
- Async analysis is decomposed into router, analysis service, trigger planning,
  and job storage instead of one opaque path.
- The UI mirrors the backend flow cleanly: marketplace -> simulation -> reports.

## What Still Carries Risk

- Executor reliability still defines product truthfulness.
- Dynamic-analysis state is still artifact-first in `output/`.
- Coverage semantics can drift if trigger docs and report docs are not kept in
  sync with code.

## Recommended Reading By Problem Type

- Architecture question: `ARCHITECTURE.md`
- Placement question: `PROJECT_STRUCTURE.md`
- Runtime reliability question: `EXECUTOR_PLAYWRIGHT.md` + `docs/risks.md`
- Coverage or report-semantics question:
  - `VSCODE_API_COVERAGE_AUDIT.md`
  - `DETECTION_SEMANTICS.md`
