# Security Tests

`Last Updated: 2026-06-04`

`tests/security/`, `tests/executor/security/`, and
`tests/platform/security/` (the last two for subsystem-local W8 work).

Lane shape and overall test guide:
[`../TESTING.md`](../TESTING.md). Layer file map:
[`../structure/test-layout.md`](../structure/test-layout.md).

## `tests/security/`

- `test_fixture_hygiene.py` — `LABEL.yaml` schema + manifest hygiene
  for malicious fixtures (`extensions/malicious/`).
- `test_rule_coverage.py` — dynamic production registry coverage for A1-A8
  plus the demo canary; PoC T1 classes still cover A1/A2/A4/A6.
- `test_canary_end_to_end.py` — wires a canary fixture through the rule
  runner. Code comment references the archived
  [`REFACTOR_OPTIMIZATION.md` §10.7](../archive/plans/REFACTOR_OPTIMIZATION_full_2026-06-15.md)
  PoC acceptance bar; that retired subsection lives in the full snapshot.
- `test_detection_report_invariants.py` — cross-layer evidence-link
  contract: `DetectionFinding.evidence.event_id` ↔
  `ActivationReport.evidence_events[]`.
- `test_rule_validation.py` — rule loader / shape assertions.
- `test_benign_silence.py` — benign baselines stay zero-finding
  (post-W6 `signal_policy` thresholds).
- `rules/test_a{1,2,3,4,5,6,7,8}_*.py` — per-class rule detection tests.
- `rules/test_rule_attribution.py` — target-only attribution gating.

## `tests/executor/security/`

- `test_uri_trigger_injection.py` — W8-3 URI trigger argv-form
  invocation (26 adversarial cases). Layered as: `validate_uri_scheme`
  allow-list (parametrized 4 happy + 9 reject), `run_uri_trigger`
  argv-form proof, call-site integration on
  `entrypoint.triggers.run_extra_triggers` and
  `stimulus.attempts.execute_attempt(extra:uri_trigger)`.

## `tests/platform/security/`

(W8-6 closed by W10-7 `2026-05-04`; W8-8 deferred — see
`active-work/W8-security.md`.)

- `test_content_sample_redaction.py` (W8-6 closed by W10-7
  `2026-05-04`, `c1e2273`) — secret-class redaction for
  `ContentSample.value` and adjacent extension-controlled text
  surfaces. See also
  `tests/platform/security/test_output_signals_redaction.py` (the
  W10-7 regression net for `OutputSignalEvent.text`, executor
  stderr/stdout tail, and `map_executor_error` exception text). W12
  follow-ups extend that file to file-backed/harness-marker output
  signals and marketplace installer-tail multiline PEM boundaries.
- W8-8 manifest-field log sanitization is deferred, so there is no
  current `test_manifest_log_sanitization.py`. When
  `[FOLLOWUP w8-8-manifest-emit-when-needed]` reopens, land the
  sanitizer helper, platform security test, AST gate, and ADR 0002
  addendum in the same PR.

## Test Lanes

- **`make test-security`** runs the cross-tree W5 + W8 perimeter lane:
  - W5 malicious-fixture hygiene + rule coverage:
    `tests/security/test_fixture_hygiene.py`,
    `tests/security/test_rule_coverage.py`,
    `tests/security/rules/`,
    `tests/security/test_rule_validation.py`,
    `tests/security/test_benign_silence.py`
  - W8-6 + W11-6 + W12-0 redaction lanes: `tests/platform/security/`
  - W8-7 ADR 0007 binding gates: `tests/architecture/test_default_bindings.py`
  - ADR 0002 Docker base-image pinning:
    `tests/architecture/test_dockerfile_digest_pin.py`
  - W8-1 VSIX zip-bomb hardening: `tests/workflows/marketplace/test_vsix_hardening.py`
  - W8-3 URI trigger injection: `tests/executor/security/test_uri_trigger_injection.py`
  - W8-5 router path traversal: `tests/workflows/activation_reports/test_router_path_traversal.py`

  Cross-tree composition landed during W8 acceptance;
  `[FOLLOWUP make-test-security-lane-composition]` is closed in
  `POST_POC_BACKLOG.md`.
- **`make test-security-live`** — T2/T3 fixture lane, gated by ADR
  0004; user-side because operational T2 plumbing waits on a real
  engagement.
- **Docker-based A1 canary structural diff** —
  `make exec-up && make exec-run` against
  `t1-a1-credential-read-to-network-canary`. User-side regression gate
  for the capture pipeline.

## Adding A Security Test

- New rule for an adversary class → `tests/security/rules/test_<name>.py`,
  paired with the rule under `packages/analysis_engine/rules/`.
- New malicious fixture → `extensions/malicious/<name>/` with
  `LABEL.yaml`; hygiene auto-validated by `test_fixture_hygiene.py`.
- New executor-side adversarial defense → `tests/executor/security/`.
- New platform-side defense → `tests/platform/security/`.
- New cross-cutting architecture detector → `tests/architecture/`.
