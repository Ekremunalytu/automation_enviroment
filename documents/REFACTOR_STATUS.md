# Refactor Status

`Last Updated: 2026-04-23 (W7 entry cleanup: W6 wording drop, SimulationPage exhaustive-deps fix, DetectionPanel snapshot refresh, pre-commit .snap trailing-whitespace exclusion, activation-layer verdict → signal_summary rename)`

This is the active status board for the Week 1-4 stabilization work and the
pre-W6 cleanup handoff. Use this file for current closure state; use
`REFACTOR_EXECUTION_PLAN.md` for sequence and rationale.

## Authoritative Read Order

1. `AGENTS.md`
2. `documents/AGENT_CONTEXT.md`
3. this file
4. `documents/REFACTOR_EXECUTION_PLAN.md`
5. subsystem-specific docs only when the task reaches them

## Current State

- Week 4 closure (2026-04-20), W5 detection foundations (2026-04-20), and W6
  automation reliability + capture hardening (closed 2026-04-23 after the
  correctness follow-up) are all green.
- **W7 (acceptance + buffer)** is now the active gate; entry rule is the PoC
  acceptance checklist in `REFACTOR_OPTIMIZATION.md` §10.7.
- Async marketplace job state is durable in PostgreSQL via `analysis_jobs`.
- Activation reports remain artifact-first under `output/activation_report_*.json`.
- Workflow code depends on the sandbox through `executor.control`.
- W5 detection surfaces are wired:
  `packages/analysis_contracts/detection/` (DTOs, `Confidence`),
  `packages/analysis_engine/rules/` (A1/A2/A4/A6 rules with target-only
  attribution), `extensions/malicious/` (T1 canaries with `LABEL.yaml`),
  `tests/security/`, plus `make test-security` and
  `make test-security-live`.
- Root legacy directories (`routers/`, `scanner/`, `core/`, `database/`,
  `crud/`, `models/`, `schemas/`) are removed from the canonical repo surface.
- Dormant root placeholders `apps/` and `legacy_ui/` are removed from the repo
  surface; the canonical runtime tree is `appcore/`, `packages/`,
  `workflows/`, `executor/`, `ui/`, and `tests/`.

## Week 4 Exit Criteria

- Repo-wide import graph checks pass.
- Executor retry / cleanup / monotonic timing work is in place.
  Harness-extension checksum verification is now enforced in executor startup.
- `monitor.py` is a thin facade over dedicated lifecycle/source/runtime/
  attribution helpers while preserving the flat import surface used by tests
  and the executor entrypoint.
- UI contract generation drift checks and feature-boundary checks are wired into
  CI and local `make check-all`.
- Benign baseline corpus includes:
  - `ms-python.python`
  - `extrace.fixture-chat`
  - `extrace.fixture-theme`
- The color-theme baseline proves scenario-zero semantics through the
  marketplace analysis flow without entering smoke acceptance.
- Smoke acceptance stays focused on `ms-python.python` and
  `extrace.fixture-chat`.

## Week 4 Closure Validation (2026-04-20)

Closure evidence captured while finishing the last open items:

- UI contract drift healed (`scripts/generate_ui_contracts.py` refreshed
  `ui/src/lib/types/contracts.ts`; `AnalyzeJobStatusDto.steps` and
  `ActivationReportDto._metadata` are now optional/nullable and the UI
  adapter layer tolerates the looser shape).
- `executor/flows/playwright/monitor.py` timeout loops migrated from
  `time.time()` to `time.monotonic()` (ADR 7.2.3 compliance); wall-clock
  remains only for reporting timestamps where UTC is desired.
- `executor/flows/playwright/runtime_capture/` carries the network,
  filesystem, and extension-host capture modules; `monitor.py` re-exports
  the parsers/classes so existing tests and the executor entrypoint keep
  their flat import surface.
- Pre-W6 cleanup removed tracked `apps/` and `legacy_ui/`, removed the
  legacy trigger-plan tuple shim from
  `workflows.marketplace.analysis_service`, and completed the `monitor.py`
  facade split without changing external API routes or report wire shape.
- UI eslint no longer has hard errors (non-null-assertion on optional
  chain removed, non-component helper moved to
  `features/simulation/telemetry.ts`). One pre-existing
  `react-hooks/exhaustive-deps` warning remains and is tracked for the
  UI follow-up lane, not Week 4.
- `.venv/bin/ruff check .`, `make ui-types-check`, `make ui-boundaries`,
  `pytest tests/` (unit+integration+architecture+security lanes) all
  green on 2026-04-20.

## Deferred from Week 4 into Week 5

- **Harness-extension checksum verification.** This was deferred at the
  Week 4 close because it is a supply-chain security task (ADR 0002
  §7.2.6), not a stabilization task. It is now implemented in Week 5:
  `executor/container/Dockerfile` writes
  `/home/executor/flows/harness_extension.sha256`, and
  `executor/container/start.sh` verifies that manifest before VS Code
  starts.

## Week 5 Progress (2026-04-20)

- Detection contracts are now materialized under
  `packages/analysis_contracts/detection/` with ADR 0003-aligned
  `DetectionFinding`, `DetectionReport`, 5-state verdict rollup, rule
  lifecycle enums, and ULID-backed finding ids.
- `packages/analysis_engine/` now contains the initial W5 rule runner,
  registry, allowlist support, and four production PoC rules for A1,
  A2, A4, and A6.
- T1 malicious canaries under `extensions/malicious/` now carry offline
  `activation_report.json` fixtures and `LABEL.yaml` expectations that
  point at the production rule ids.
- `workflows.marketplace.analysis_service.run_local_analysis()` provides
  the offline fixture-to-bundle path used by security tests; completed
  marketplace job status responses now expose `detection_report`, and
  activation reports have a new `/api/activations/{name}/bundle`
  endpoint.
- `ui/src/features/reports/` now renders a detection-first analyst view
  using `detection_report.verdict` instead of the legacy heuristic score,
  including finding cards and evidence deep-links into the event tab.
- `make test-security` now exercises fixture hygiene, rule coverage,
  per-rule fire/silence checks, manifest round-trip validation, and
  benign silence coverage. CI runs the same lane in a dedicated
  `security-fixtures` job.

## Week 6 Progress (2026-04-21)

- Scenario truth is now ledger-backed end to end: requested scenarios
  reconcile to executed, failed, or typed `skipped_scenarios`, and the report
  invariant gate rejects drift between requested/executed/skipped state.
- `automation_health` and `run_quality` now degrade or become inconclusive when
  requested scenarios are skipped or when none of the requested scenarios
  execute.
- Trigger-plan-driven flows now use named bounded wait helpers plus an
  idle-observation window instead of treating fixed sleeps as success.
- Workspace seeding/materialization now fails closed for unsupported activation
  surfaces and unsupported fixture generation instead of silently fabricating
  generic placeholders.
- Runtime capture now adds bounded HTTP metadata/body previews and
  extension-host child-process telemetry without storing raw full bodies,
  raw argv, or environment dumps.
- `signal_policy` now suppresses `correlative_suspicious_activity` unless
  there are at least two tightly clustered correlated events and at least one
  of them is network or sensitive-file evidence.
- The `security-fixtures` CI job now disables outbound egress after dependency
  install, verifies that the block is real, and asserts that
  `make test-security-live` refuses to run under `CI=true`.

## W6 Status (2026-04-23, closed)

- Pre-W6 structural cleanup remains complete.
- W6 automation reliability, report honesty, capture hardening, and CI egress
  enforcement are implemented.
- W6 correctness follow-up (2026-04-23) closed the three blocking gaps
  surfaced during the post-W6 review (see §"W6 correctness follow-up"
  below). W6 is now closed; remaining detection improvements move to W7
  buffer or the post-PoC backlog.
- Structural tree cleanup, legacy trigger-plan compatibility, and `monitor.py`
  modularization are no longer open W6 scope items unless a regression is
  found.

## W6 Correctness Follow-up (2026-04-23)

Three detection-engine correctness gaps and one CI-visibility gap landed
between the W6 hardening commits and W7 entry. None change architecture;
each was required for the W7 acceptance bar to mean anything.

- **Attribution gating on A1/A2/A4 (ADR 0002 §4, ADR 0003 §4).** The
  production rules for A1 (credential-read-then-network), A2 (startup
  network beacon), and A4 (workspace exfil) previously keyed on event
  `kind`, path, and host only, ignoring the activation report's own
  `is_target_extension_event` and `attribution_status` fields. On live
  scans carrying automation noise or sibling-extension activity, rules
  could fire for evidence the report explicitly did not attribute to the
  analyzed extension. New helpers in
  `packages/analysis_engine/rules/_common.py` —
  `target_file_events()` and `target_unknown_outbound_network_events()` —
  now admit only events with `is_target_extension_event == True` and
  `attribution_status in {"strong", "direct"}`. A1/A2/A4 route through
  them.
- **TLS vocabulary (`tls_client_hello`).** The live `tshark` capture
  emits TLS sessions as `tls_client_hello`; the production rules only
  accepted the legacy `tls_sni` spelling, so A1/A2/A4 were effectively
  dead on live data. A shared `TLS_EVENT_TYPES` constant and
  `is_tls_event()` helper now cover both spellings, and the three rules
  use the helper.
- **Error dominance in the runner (ADR 0003 §5).** The detection runner
  previously swallowed handled rule exceptions and still returned
  `Verdict.CLEAN` when every rule errored on an otherwise-healthy
  report, making detector failures indistinguishable from clean runs.
  `packages/analysis_engine/runner.py` now checks
  `RuleExecutionStatus.ERROR` before verdict rollup and degrades the
  automation-health input to `inconclusive` with a
  `rule_execution_errors` blocker, so errors dominate the rollup.
- **Security fixtures reach CI.** `extensions/` was wholly gitignored,
  so the T1 internal canaries under `extensions/malicious/` and the
  benign-silence baselines at `extrace.fixture-chat-0.0.1` and
  `extrace.fixture-theme-0.0.1` never reached the `security-fixtures`
  CI job — the lane was green only because it failed to collect the
  tests W5 depended on. `.gitignore` now ignores `extensions/*` with
  explicit exceptions for the fixtures the security and detection
  tests exercise. The canary evidence carries the target-attribution
  fields the updated rule helpers require.
- **Executor test isolation + layered run_quality label.** The
  `monitor` package-import test popped flat module names from
  `sys.modules` without restoring them, which made
  `resolve_monitor_api()` return the package module for later tests
  that monkeypatched the flat module object — suite order decided
  whether runtime tests saw their patches. `sys.modules` is now
  snapshotted and restored around the package import. Separately,
  `build_run_quality` in `executor/flows/playwright/health_summary.py`
  previously returned an empty reason list on layered-medium because
  `build_automation_health` only records `verification_gap` and
  `chat-tool` reasons in non-layered mode; the layered path now
  appends the explicit reason text locally, and
  `official_unresolved_present` is exposed as a reason label so the UI
  can explain why the run landed at medium.

Tests backing this follow-up: `tests/security/rules/test_rule_attribution.py`
(target vs. unattributed evidence plus live `tls_client_hello` vocabulary
across A1/A2/A4); updated `tests/platform/engine/test_rule_runner.py`
(all-errors dominance case; existing error-does-not-abort test now asserts
`inconclusive`); updated executor monitor package-import test.

## Post-W6 Detection Bridge (2026-04-21)

Landed before W7 acceptance to close the two `ActivationReport` ↔
`DetectionReport` gaps surfaced during the W5/W6 review:

- **Shared confidence vocabulary (ADR 0003 §3).** `RiskSignal` now carries a
  `confidence_tier: "high" | "medium" | "low" | ""` field populated via
  `packages.analysis_contracts.quantize_confidence` (thresholds 0.85 / 0.65).
  Activation-layer floats and detection-layer `Confidence` enums now speak the
  same tier vocabulary; `signal_policy.build_risk_signals` emits both the raw
  `confidence` float and the quantized `confidence_tier`.
- **Cross-layer link invariant (ADR 0003 §4).**
  `detection_report_invariant_issues(detection_payload, activation_payload)`
  asserts every `DetectionFinding.evidence[].event_id` resolves to an
  `evidence_events[].event_id` in the paired `ActivationReport`, and every
  `RuleExecutionRecord.finding_ids` references a finding carried in the same
  report. The `ms-python.python` baseline runs `run_detection` end-to-end and
  must report zero invariant issues
  (`tests/platform/contracts/test_analysis_fixture_baselines.py`).
- **UI contract regenerated.** `scripts/generate_ui_contracts.py` refreshed
  `ui/src/lib/types/contracts.ts` so `RiskSignalDto.confidence_tier?` is visible
  to the UI. No view-model shape changes were required; deeper UI deep-link
  rewiring stays in the post-PoC backlog.
- **Tests.** New `tests/security/test_detection_report_invariants.py` covers
  clean resolution, unknown evidence event_id, dangling rule finding_id, and
  quantization thresholds.

## Known Concerns (tracked into W7)

Risk log surfaced during the post-W6 review on `2026-04-21`. None block the
bridge landing, but each is load-bearing for W7 acceptance or for
post-PoC quality.

- **Verdict vocabulary split resolved (W7 entry, 2026-04-23).** The
  activation-layer verdict has been demoted to a presentation-only
  field: `signal_policy.build_signal_summary` (renamed from
  `build_verdict`) now populates `ActivationReport.signal_summary`, and
  the UI consumes it as `ReportSummaryView.signalSummary*`. The
  detection-layer `Verdict` enum
  (`packages.analysis_contracts.detection.rollup.compute_verdict` →
  `malicious / suspicious / clean_with_notes / clean / inconclusive`)
  is the sole authoritative verdict vocabulary. The activation-layer
  signal summary (`likely_malicious / suspicious / needs_review /
  benign`) remains visible in the dashboard-level risk panel as a
  sandbox behavioral heuristic, clearly separated from rule-driven
  verdicts. Reference: ADR 0003 §5.
- **`monitor_attribution.py` is still ~1100 LoC (low, post-PoC).**
  Post-W6 refactor split `monitor.py` and `stimulus.py` cleanly, but the
  attribution module still bundles evidence-link builders and signal
  facts. Not shipping-critical; becomes a rule-author friction point
  after W7. Track in the post-PoC modularization backlog. (Historical
  note: `analysis_service` decomposition 7.1.1 already landed — see
  `analysis_execution.py` and `analysis_reports.py` — so it is no longer
  a sibling of this item.)
- **UI detection surface is minimum-viable (medium for demo).**
  `DetectionPanel` and `FindingCard` render the contract. The
  `react-hooks/exhaustive-deps` warning on `SimulationPage.tsx` was
  cleaned up during W7 entry (2026-04-23) by wrapping `filteredEvents`
  in `useMemo`; a stale snapshot on `DetectionPanel.test.tsx` was also
  refreshed at the same time. Axe-core accessibility coverage still
  missing — if W7 demo is stakeholder-facing, reserve part of the W7
  buffer for axe-core wiring; otherwise this stays on the post-PoC UI
  lane (REFACTOR_OPTIMIZATION.md §10.3).
- **Stretch adversary classes A3/A5/A7 have no rules (low for PoC,
  medium for demo).** PoC bar only requires A1/A2/A4/A6 and that bar is
  met. However a single A3 (typosquat) canary + rule materially
  improves demo readability because the signal is human-obvious. Candidate
  for W7 buffer if acceptance items close early; otherwise hold.

Each item has a single natural owner: modularization is an executor
change, UI polish is a UI change, A3 coverage is a detection-engine
change. (Verdict vocabulary split was resolved at W7 entry — see the
item above.) Pick remaining items by available W7 buffer, not by
novelty.

## Week 5 Start Rule

Week 5 begins only after the Week 4 exit criteria above are green. Detection
work does not reopen Week 4 refactors except to fix a blocking regression.
