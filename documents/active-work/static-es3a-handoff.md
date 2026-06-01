# Static Analysis Pre-Check — ES-3a Session Handoff

`Status: ES-3a (6 in-house static rules s1/s2/s3 + static runner) is COMPLETE, FULLY VERIFIED (static + live + a live UI-scan regression check), and COMMITTED + PUSHED to origin/static (user go-ahead 2026-05-30).`

`Last Updated: 2026-05-30 — ES-3a implemented, verified, committed + pushed; docs reconciled (lane doc + ADR 0016 wording + tracker).`

`Branch: static · ES-3a committed on top of a3b17b8 (ES-2); see git log on static for the hash.`

`Owner: ekrem`

This is a transient session-handoff (mirrors `static-es2-handoff.md`). The
durable record is the stream tracker
[`static-analysis-pre-check-stream.md`](static-analysis-pre-check-stream.md)
(ES-3a stamped DONE there, with full per-item detail) and
[ADR 0016](../adrs/0016-static-analysis-pre-check-stage.md).

## Immediate next action

ES-3a is **done, committed, and pushed** to `origin/static`. The next iteration
is **ES-3b** — the decision gate + orchestrator wiring:

- `workflows/marketplace/static_analysis.py` (new): `run_static_analysis`,
  `evaluate_static_gate` (block-and-warn truth table),
  `_PROMOTED_HIGH_BLOCKERS = frozenset({"extrace.s2.typosquat"})`,
  `StaticAnalysisBlockedError`, `build_combined_bundle`.
- `analysis_service.py`: insert `_run_static_analysis` + `_evaluate_static_gate`
  before `_reset_sandbox`, gated on `settings.static_analysis.ENABLED` (still OFF).
- `job_service.py`: **update `empty_job_steps` to 7 records in the same commit
  as the step-Literal extension** (the documented ES-1 regression mitigation).
- `appcore/storage/crud_ops/analysis_jobs/static_gate.py` (new):
  `reject_analysis_job_static`; add `rejected_static` to `_TERMINAL_JOB_STATUSES`.
- Cancellation via a `_run_static_off_thread` coordinator (mirror W18-2).
- Needs `docker compose build api && up -d api` (executor.host orchestration is
  baked into the api image).

The branch-contamination PR-strategy decision (see `static-es2-handoff.md`
§Open items) stays OPEN and still gates any `static -> main` PR.

## What ES-3a did (summary; full detail in the tracker §ES-3a)

- Swapped the ES-2 empty-report stub for the real in-house rule engine behind
  the unchanged ES-2 flag surface + on-disk `StaticDetectionReport` contract.
- **Placement (Option A, user-approved):** rules live in the container-native
  `static_runtime/rules/`, NOT `packages/analysis_engine/static_rules/` (the
  engine `__init__` eagerly imports `run_detection`, so any engine submodule
  import would drag the whole dynamic engine into the hardened image). The
  typosquat matcher + allowlist moved to
  `packages/analysis_contracts/typosquat_match.py` (+ `data/`), a stdlib-only
  leaf shared by the dynamic `a3_typosquat` and the static `s2` rule. One
  allowlist copy; `a3` behaviour unchanged (its tests are the regression guard).
- Six PRODUCTION rules: `extrace.s1.activation_wildcard` /
  `extrace.s1.suspicious_capabilities` / `extrace.s1.generic_publisher` /
  `extrace.s2.typosquat` (HIGH, the promoted gate blocker) /
  `extrace.s3.embedded_native_binary` / `extrace.s3.unusual_file_signature`.
- `static_runtime/static_runner.py` mirrors `packages.analysis_engine.runner`;
  manifest parsed with stdlib `json` (no `workflows`/`appcore` import); evidence
  snippets routed through `redact_secrets`.

## Verification

- `make check-all` (postgres_test up): **2214 passed, 9 skipped** — lint, mypy,
  bandit, ui-types-check, ui-boundaries, markdownlint all green.
- `make static-build` + `make test-smoke`: static smoke **3/3** — import in the
  minimal image, clean-tree `inhouse` tool record, rules fire live in-container.
- `tests/static_runtime/`: **35 tests** (per-rule fire/silent, runner rollup +
  round-trip + budget, context manifest-fallback/malformed/symlink-skip,
  snippet redaction + length clamp, s3 evidence cap with full-count reporting).
- `tests/architecture/test_static_runtime_import_boundary.py`: pins the
  no-engine/workflows/appcore import boundary.
- **Live UI-scan regression check (ms-python.python, 2026-05-30):** job
  `completed`, all 5 dynamic steps green, `static_report_path` NULL (gate not
  wired yet), no api tracebacks; re-running `run_detection` over the scanned
  report confirmed `extrace.a3.typosquat` runs silent with the moved allowlist
  loading 18 entries — the shared-leaf refactor did not disturb the dynamic
  pipeline.

## Notes / invariants carried forward

- Feature flag `settings.static_analysis.ENABLED` stays OFF until ES-5.
- The frozen `extrace-static-stream-handoff.md` is preserved design intent; its
  ES-3a/ES-4 sections still name `packages/analysis_engine/static_rules/` — the
  Option A deviation is recorded in the tracker + ADR 0016, not by editing the
  frozen doc (the ES-2 precedent).
- New security-lane tests still enroll into the explicit `test-security` file
  list; ES-3a added no security-lane test (the import-boundary test runs in the
  default lane under `make check-all`).
