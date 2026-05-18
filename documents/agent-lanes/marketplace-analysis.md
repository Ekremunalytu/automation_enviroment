# Marketplace And Analysis Lane

**Last Updated:** 2026-05-17 (W15 close — W15-1 closed 2026-05-14 via c58c365 + typing hotfix 976dc96 on 2026-05-16: sync analyze error taxonomy parity, M10 — `ANALYZE_*_ERROR_TYPES` tuple gates sync `/analyze` exception handling to async worker parity; W15-6 closed 2026-05-17 via be52520 (Proposed at e41722e): ADR 0011 unauthenticated catalog endpoints posture Accepted and implemented, Option A; `tests/architecture/test_catalog_endpoint_posture.py` gate adds 3 AST invariants — module docstring cites ADR 0011, APIRouter has no auth dependency, endpoint count locked at 12 — `tests/architecture/` 188 → 191; ADR 0002 NOT amended.)

Use this lane for marketplace search/download, sandbox analysis orchestration,
async analysis jobs, cancellation, trigger planning, and report handoff.

## Start Here

- `workflows/marketplace/router.py`
- `workflows/marketplace/client.py`
- `workflows/marketplace/analysis_service.py`
- `workflows/marketplace/analysis_execution.py`
- `workflows/marketplace/job_service.py`
- `workflows/marketplace/trigger_service.py`
- `packages/analysis_planner/`
- `tests/workflows/marketplace/`

## Invariants

- Only one background analysis job is expected in the single-user appliance
  model.
- Async job metadata is DB-backed in `analysis_jobs`; activation reports are
  still file-backed artifacts under `output/`.
- Workflow code should reach Docker/executor mechanics through
  `executor.control`.
- Trigger planning must keep unsupported, skipped, failed, and verified states
  explicit in reports.
- The planner→executor action surface is intentionally narrow:
  `packages/analysis_contracts/executor_actions.py::validate_executor_action`
  rejects anything outside `EXTRA_EXECUTOR_ACTIONS` (the 5 closed-set
  `extra:` action names) or the namespaced `EXECUTOR_ACTION_NAMESPACES`
  prefix set (`scenario:`, `command:`, `extra:`, `fixture:`, `harness:`).
  When adding a new executor verb, extend exactly one of those frozensets
  AND add the matching dispatcher branch in
  `executor/flows/playwright/stimulus/attempts.py::_dispatch_action` —
  emitting an unregistered action is a producer-side bug, not a runtime
  fallthrough.

## Tests And Checks

- `.venv/bin/pytest tests/workflows/marketplace/`
- `.venv/bin/pytest tests/smoke/ -m smoke` when behavior is end-to-end.
- `make sim-target TARGET=publisher.name` for target-extension smoke.
- `make sim-all` only for UI-stimulus stress without target extension.

## Open Subsystem Doc Only If Needed

- `PIPELINE_ROADMAP.md` if the staged pipeline direction is the
  question.
- `VSCODE_API_COVERAGE_AUDIT.md` for trigger planning,
  capability support, official-vs-heuristic coverage.
- `DETECTION_SEMANTICS.md` (slim) → `detection/evidence-fields.md`
  for `automation_health`, coverage, attribution interpretation.
- `architecture/data-flow.md` for the end-to-end sandbox analysis
  flow (request → executor → report).
- `testing/marketplace-tests.md` for the marketplace test layer map.
- `active-work/W8-security.md` items W8-1 (VSIX zip-bomb), W8-2
  (marketplace identity), W8-8 (manifest log sanitization).
- `runbooks/analysis-job-stuck.md` when a job is wedged.

## Avoid

- Treating `sim-all` as target-aware analysis.
- Equating `target_extension_observed=true` with a healthy scan; inspect
  `automation_health`, `run_quality`, event attempts, and target-owned
  evidence.
- Silent cancellation or heartbeat failures.
