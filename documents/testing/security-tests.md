# Security Tests

`Last Updated: 2026-04-29`

`tests/security/`, `tests/executor/security/`, and
`tests/platform/security/` (the last two for subsystem-local W8 work).

Lane shape and overall test guide:
[`../TESTING.md`](../TESTING.md). Layer file map:
[`../structure/test-layout.md`](../structure/test-layout.md).

## `tests/security/`

- `test_fixture_hygiene.py` — `LABEL.yaml` schema + manifest hygiene
  for malicious fixtures (`extensions/malicious/`).
- `test_rule_coverage.py` — every Must-class adversary (A1/A2/A3/A4/A6)
  has a dedicated rule + canary.
- `test_canary_end_to_end.py` — wires a canary fixture through the rule
  runner. Code comment references `REFACTOR_OPTIMIZATION.md §10.7`
  (PoC acceptance bar) — anchor preserved in slim canonical.
- `test_detection_report_invariants.py` — cross-layer evidence-link
  contract: `DetectionFinding.evidence.event_id` ↔
  `ActivationReport.evidence_events[]`.
- `test_rule_validation.py` — rule loader / shape assertions.
- `test_benign_silence.py` — benign baselines stay zero-finding
  (post-W6 `signal_policy` thresholds).
- `rules/test_a{1,2,3,4,6}_*.py` — per-class rule detection tests.
- `rules/test_rule_attribution.py` — target-only attribution gating.

## `tests/executor/security/`

- `test_uri_trigger_injection.py` — W8-3 URI trigger argv-form
  invocation (26 adversarial cases). Layered as: `validate_uri_scheme`
  allow-list (parametrized 4 happy + 9 reject), `run_uri_trigger`
  argv-form proof, call-site integration on
  `entrypoint_triggers.run_extra_triggers` and
  `stimulus_attempts.execute_attempt(extra:uri_trigger)`.

## `tests/platform/security/`

(W8-6 + W8-8 land here — see `active-work/W8-security.md`.)

- `test_content_sample_redaction.py` (W8-6 pending) — secret class
  redaction for `ContentSample.value`.
- `test_manifest_log_sanitization.py` (W8-8 pending) — newline / CR /
  ANSI / NULL / overlength manifest-field sanitization for log + job
  emit sites.

## Test Lanes

- **`make test-security`** runs only `tests/security/`. Subsystem-local
  W8 tests (`tests/workflows/marketplace/test_vsix_*` for W8-1,
  `tests/executor/security/test_uri_trigger_*` for W8-3) live in their
  natural lanes. See `POST_POC_BACKLOG.md` `[FOLLOWUP
  make-test-security-lane-composition]` for the open question on
  whether to fold subsystem-local lanes into the Makefile target.
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
