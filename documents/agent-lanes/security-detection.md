# Security And Detection Lane

`Last Updated: 2026-05-12 (W13-8 closed — §11.10 GOAL benign silence fixture 3→5 GREEN, 5/5 ✓: 3 new fixture extensions — snippet/keybinding/cmd — under extensions/ + baseline activation reports + helpers/baselines registration; tests/security/test_benign_silence.py 5/5 ✓. W13-11 close-pass closed`2026-05-12` (6/6 sub-commits) — Path A host-side eager-consume + env var passthrough for HMAC python secret target-install race; `executor_control.consume_harness_python_secret()` between `_reset_sandbox` and `_install_extension`,`EXECUTOR_HARNESS_PYTHON_SECRET_VALUE`env threading + E4 docker exec argv mask; W13-1 H6 nonce gate intact. W13-12 fail-closed handshake closed`2026-05-12` (5/5 sub-commits) — `ActivationReport.harness_handshake_required: bool` field stamped True by `setup_monitor` + `_attempt_has_harness_completion_trace` fail-closed branch + 3-fact AST gate; test bar 1537 → 1539 / tests/architecture/ 112 → 115.)`

Use this lane for detection contracts, rule behavior, malicious fixtures, and
security ADR alignment.

## Start Here

- `documents/adrs/0002-threat-model.md`
- `documents/adrs/0003-detection-taxonomy.md`
- `documents/adrs/0004-malicious-fixture-policy.md`
- `documents/adrs/0005-packages-charter.md`
- `packages/analysis_contracts/detection/`
- `packages/analysis_engine/rules/`
- `extensions/malicious/`
- `tests/security/`
- `documents/DETECTION_SEMANTICS.md`

## Invariants

- Detection rules consume contracts only; they do not import runtime, web, UI,
  or storage layers.
- A1/A2/A3/A4/A6 production rules and T1 canaries are live.
- A5 malicious update and A7 VS Code API abuse remain deferred unless pulled
  from `POST_POC_BACKLOG.md`.
- ADR 0006 is target output-channel capture. Do not reuse that number for
  container packaging; the next packaging ADR needs a new number.
- T3 live samples never run in CI.

## Tests And Checks

- `make test-security`
- `make test-security-live` only as a break-glass live lane.
- `.venv/bin/pytest tests/security/`
- `.venv/bin/python scripts/demo_acceptance.py`
- `make demo-canary-offline`

## Open Subsystem Doc Only If Needed

- `DETECTION_SEMANTICS.md` (slim) → open one split based on what you
  touch:
  - `detection/evidence-fields.md` for `target_*`, `trigger_plan_*`,
    scenarios, coverage, execution ledger, attribution.
  - `detection/health-signals.md` for `automation_health`, `log_health`,
    `run_quality`, `signal_summary`, `risk_signals[]`, `risk_summary`.
  - `detection/rule-lifecycle.md` for ADR 0003 cross-ref, rule
    authoring, activation-layer vs detection-layer verdict vocabulary.
- ADRs 0002-0005 — open the one that governs the touched boundary,
  not all four.
- `active-work/W8-security.md` items W8-5 (router regex), W8-6
  (content-sample redaction).
- `testing/security-tests.md` for the security-test layer map.

## Avoid

- Black-box or non-reproducible detection heuristics.
- Expanding detection scope before report-health and attribution semantics are
  trustworthy.
- Running live malicious fixtures in CI.
