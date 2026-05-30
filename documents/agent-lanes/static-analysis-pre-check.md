# Static Analysis Pre-Check Lane

**Last Updated:** 2026-05-30 (ES-3b — decision gate + orchestrator wiring
landed: 7-step contract + flag-aware `empty_job_steps`, the `rejected_static`
terminal transition, and the flag-gated static stage in `analysis_service`.
Feature flag stays OFF until ES-5).

Use this lane for the pre-execution static analysis stage: static
detection contracts, in-house static rules, the Semgrep runner, the
hardened `automation_static_analyzer` container, and the block-and-warn
decision gate that fronts the dynamic sandbox.

## Start Here

- `documents/adrs/0016-static-analysis-pre-check-stage.md`
- `documents/active-work/static-analysis-pre-check-stream.md`
- `documents/active-work/extrace-static-stream-handoff.md` (frozen
  design-intent source; field-level spec for every sub-iter)
- `packages/analysis_contracts/static_detection/` (landed ES-1)
- `static_runtime/rules/` + `static_runtime/static_runner.py` (landed ES-3a;
  rules live in the container-native package, NOT `packages/analysis_engine/`,
  so the hardened image stays minimal)
- `packages/analysis_contracts/typosquat_match.py` (landed ES-3a; shared
  stdlib-only matcher + `data/popular_extensions.txt`, reused by the dynamic
  `a3_typosquat` and the static `s2` rule — one allowlist copy, no engine import)
- `workflows/marketplace/static_analysis.py` (landed ES-3b — gate logic +
  container runner + `StaticAnalysisBlockedError`)
- `workflows/marketplace/analysis_service.py` (`_run_static_gate`) +
  `appcore/storage/crud_ops/analysis_jobs/static_gate.py`
  (`reject_analysis_job_static`) + `appcore/api/config.py`
  (`StaticAnalysisSettings`) (landed ES-3b — orchestrator wiring, the
  `rejected_static` transition, the feature flag)

## Invariants

- **Schema-first.** Pydantic contracts land before any tool runner; tools
  map into the schema, never the reverse.
- **Enum reuse by identity.** `Severity` / `Confidence` / `RuleLifecycle`
  / `AdversaryClass` come from `packages.analysis_contracts`, not parallel
  clones (ADR 0005 packages charter).
- **Minimal-image import boundary.** The static rules + runner live in
  `static_runtime/` and import only the standard library +
  `packages.analysis_contracts` — never `workflows`, `executor`, `appcore`,
  `ui`, or `packages.analysis_engine` (whose `__init__` eagerly imports the
  dynamic engine, which would bloat the hardened image). Pinned by
  `tests/architecture/test_static_runtime_import_boundary.py`.
- **Block-and-warn.** CRITICAL → terminal `rejected_static`; the only
  promoted HIGH blocker is `extrace.s2.typosquat` via a frozenset, not
  config. Everything else warns or allows.
- **Container isolation.** The static analyzer runs with `network_mode:
  none`, `cap_drop: [ALL]`, `no-new-privileges`, non-root, no
  `docker.sock` — never inline on the host or in the executor.
- **Feature-flagged.** `settings.static_analysis.ENABLED` is OFF until the
  ES-5 close-out flips it after smoke evidence passes.

## Tests And Checks

- `make check-all` with `postgres_test` up (the strict per-sub-iter gate).
- `make test-security` — enroll new static security tests into the
  explicit file list in the Makefile; it does not auto-discover.
- `make test-smoke` for the container + pipeline sub-iters.
- `make static-up` / `make static-run-fixture` for manual container spot
  checks (land ES-2).

## Open Subsystem Doc Only If Needed

- `extrace-static-stream-handoff.md` — the authoritative field-level spec
  (contract invariant lists, v2 Literal pre-ship sets, the ES-1 →
  ES-3b step-Literal regression mitigation). Open it for any sub-iter
  detail this lane summarizes.
- `documents/agent-lanes/security-detection.md` — the dynamic detection
  lane; the static findings extend its taxonomy (ADR 0003).
- `documents/agent-lanes/platform-storage.md` — for the `rejected_static`
  status + `static_report_path` column + Alembic migration (ES-1).
- `documents/POST_POC_BACKLOG.md` → `[GOAL mitre-coverage-*]` (Contracts /
  Reports / Detection) — the downstream W23 MITRE ATT&CK coverage matrix that
  consumes this lane's rule catalog + static findings (a `/mitre` UI surface +
  `GET /api/mitre/catalog`). The backend catalog is independent of this stream;
  the per-report static overlay depends on ES-3b populating `static_report_path`.

## Avoid

- Bending the static-detection schema to fit a tool's output.
- Importing `packages.analysis_engine` (or `workflows`/`appcore`) from
  `static_runtime/` — it drags the dynamic engine into the hardened image.
- Running the static analyzer inline on the host or in the executor.
- Widening `uq_analysis_jobs_single_active` to include `rejected_static`
  (it is terminal).
- Extending `ANALYSIS_JOB_STEP_NAMES` without updating `empty_job_steps`
  in the same commit (the documented ES-1 regression).
- Any external network from the static container (Semgrep runs offline,
  `--metrics=off`).
