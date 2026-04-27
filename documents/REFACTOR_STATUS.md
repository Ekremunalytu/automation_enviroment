# Refactor Status

`Last Updated: 2026-04-27 (W8-1 landed; W8-0 capture-pipeline + automation_health reason propagation gap fixes)`

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

- Week 4 closure (2026-04-20), W5 detection foundations (2026-04-20), W6
  automation reliability + capture hardening (closed 2026-04-23 after the
  correctness follow-up), and **W7 acceptance + buffer (closed
  2026-04-23)** are all green. PoC acceptance bar
  (`REFACTOR_OPTIMIZATION.md` §10.7) is satisfied; stretch rule A3
  (typosquat impersonation) landed as a W7 Phase 3a buffer item. See
  the "W7 Closure" section below and
  [`documents/POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md) for the deferred
  work items.
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
- **`monitor_attribution.py` split landed (2026-04-24, post-W7).**
  The ~1100 LoC module is now the `attribution/` subpackage
  (`events.py` + `links.py` + `__init__.py` facade) per ADR 0002 §4
  and the POST_POC_BACKLOG `[NEXT]` plan. Private-underscore API
  preserved verbatim so callers only needed the module path updated
  (`monitor_attribution` → `attribution`). Docker-based A1 canary
  structural diff remains user-side to fully close the capture
  regression risk flagged in the deferral note.
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

## W7 Acceptance Validation (2026-04-23)

Phase 1 of the W7 plan: each `REFACTOR_OPTIMIZATION.md` §10.7 checklist
item re-verified against current `week7` branch state. All items except
the demo scenario doc are green; that single gap is the scope of Phase 2.

### Stabilization side (5/5 green)

| # | Item | Evidence |
|---|---|---|
| S1 | Legacy folders removed | `routers/`, `scanner/`, `core/`, `database/`, `crud/`, `models/`, `schemas/`, `apps/`, `legacy_ui/` absent from repo surface. |
| S2 | `packages/` import-graph test in CI | `tests/architecture/test_import_graph.py` (3 tests: `test_packages_remain_framework_agnostic`, `test_executor_avoids_workflow_and_appcore_imports`, `test_workflows_use_only_executor_control_boundary`) — all pass. `.github/workflows/ci.yml:150` carries the `security-fixtures` job that runs `make test-security`. |
| S3 | VS Code pinned + harness checksum verified | `executor/container/Dockerfile:14-20,118-121` declares `EXECUTOR_VSCODE_VERSION` build-arg (default `1.116.0` via `docker-compose.yml`) and writes the harness sha256 manifest; `executor/container/start.sh:17-83` verifies it before VS Code starts. |
| S4 | `monitor.py` split into capture/ subpackage | `executor/flows/playwright/runtime_capture/` holds `events.py`, `extension_host.py`, `filesystem.py`, `log_summary.py`, `network.py`, `__init__.py`; `monitor.py` is a thin re-export facade. |
| S5 | `ExecutorControl` wrapper in place | `executor/control.py:19-50` defines the dataclass; `tests/architecture/test_import_graph.py:79-82` enforces that workflows only import from `executor.control`. No direct `docker` imports found under `workflows/`. |

### Detection side (6/7 green)

| # | Item | Evidence |
|---|---|---|
| D1 | A1/A2/A4/A6 rules + T1 canaries fire at ≥medium/≥high | `packages/analysis_engine/rules/a{1,2,4,6}_*.py` + `extensions/malicious/t1-a{1,2,4,6}-*-canary/`. Per-rule tests (`tests/security/rules/test_a{1,2,4,6}_*.py` + `test_rule_attribution.py`) — 14 pass. A1 rule reports `Severity.CRITICAL` / `Confidence.HIGH`. |
| D2 | Benign baseline silence | `tests/security/test_benign_silence.py` (2 pass: chat + theme); `tests/platform/contracts/test_analysis_fixture_baselines.py:33,95` covers ms-python + asserts `correlative_suspicious_activity` absent. |
| D3 | Scenario-dropout honesty | `workflows/marketplace/analysis_reports.py:193-196` and `executor/flows/playwright/report_builder.py:107,115,154-172` populate `failed_scenarios` / `skipped_scenarios`; invariant covered at `tests/platform/contracts/test_analysis_fixture_baselines.py:82-83`. |
| D4 | Verdict rollup marks inconclusive correctly | `packages/analysis_contracts/detection/rollup.py:16-19` routes `automation_health == "inconclusive"` to `Verdict.INCONCLUSIVE`; `tests/platform/engine/test_rule_runner.py::test_error_in_rule_forces_inconclusive_verdict` and `::test_all_rules_error_cannot_produce_clean_verdict` — both pass. |
| D5 | UI DetectionReport rendered + evidence deep-link + invariant | `ui/src/features/reports/DetectionPanel.tsx`, `FindingCard.tsx:11,65-72` wire `onShowEvidence(eventId)`. `tests/security/test_detection_report_invariants.py` — 9 pass (resolution + dangling + quantization thresholds). |
| D6 | `make test-security` green | **32 passed, 0 failed** on 2026-04-23 (see lane details below). |
| D7 | **Demo scenario written** | ✅ [`documents/DEMO_SCENARIO.md`](DEMO_SCENARIO.md) (offline + live UI flavors); [`scripts/demo_acceptance.py`](../scripts/demo_acceptance.py) headless smoke asserts the 6-point contract and exits 0 (verified 2026-04-23). |

### Local verification lanes (2026-04-23)

Ran on macOS darwin, Python 3.12.10, `.venv`. Docker daemon not running
locally → `make test-local` and `make test-smoke` deferred to CI.

| Lane | Outcome |
|---|---|
| `make test-security` | 32 passed, 0 failed (0.08s). |
| `make lint-check` (ruff) | 1 pre-existing error in `packages/analysis_contracts/detection/enums.py:12` (UP042 on the Python-<3.11 `StrEnum` fallback); fixed in this pass with an inline `# noqa: UP042` — the block intentionally defines what the rule recommends as a fallback. Re-run: clean. |
| `make typecheck` (mypy) | 201 source files, no issues. |
| `make security` (bandit) | 0 high, 0 medium, 2 low, 1 intentionally skipped (`#nosec`). |
| `make ui-types-check` | No contract drift. |
| `make ui-boundaries` | Clean. |
| `make test-unit` (no-DB lane) | 537 passed, 4 skipped (canaries with no `must_not_fire`), 37 deselected (requires-DB). |
| `tests/architecture/` | 3 passed. |
| `tests/platform/engine/test_rule_runner.py` | 5 passed (error dominance + inconclusive cases). |
| `tests/security/test_detection_report_invariants.py` | 9 passed (evidence resolution + quantization thresholds). |
| `make test-local` (integration lane) | **Deferred to CI** — Docker daemon unavailable locally; last CI run (`security-fixtures` + full `test-ci`) on branch `week7` was green. |

### Phase 2 outcome (2026-04-23)

- [`documents/DEMO_SCENARIO.md`](DEMO_SCENARIO.md) written with two
  runnable flavors: **Offline** (`python scripts/demo_acceptance.py`,
  framework-agnostic, ~30 s, CI-safe) and **Live UI** (`make dev` +
  `make exec-up` + `make ui-up` walkthrough for stakeholder audiences).
- [`scripts/demo_acceptance.py`](../scripts/demo_acceptance.py) exercises
  `packages.analysis_engine.runner.run_detection` end-to-end against the
  T1 A1 canary and asserts 7 contract lines: verdict ∈
  {malicious, suspicious}, single finding fired from
  `extrace.a1.credential_read_then_network`, severity=critical +
  confidence=high, evidence carries both `filesystem_read` and
  `network_request` refs, `detection_report_invariant_issues(...) == []`,
  no rule execution errors, A1 rule status=fired. Last local run:
  **DEMO GREEN**.
- `pyproject.toml` gained a `scripts/*.py` ruff per-file-ignores row
  matching the existing `alembic/` and `executor/` entries (T20, E501,
  I001, E402) so CLI scripts can print output and perform `sys.path`
  bootstrap without noqa spam.

### Phase 3 scope (optional buffer)

Per user selection (2026-04-23): A3 typosquat stretch canary + rule,
then `monitor_attribution.py` split. Faz 1+2 remain hard prerequisites;
Phase 3 only starts when this section is fully green.

## W7 Phase 3a Landed — A3 Typosquat (2026-04-23)

Stretch adversary class A3 (ADR 0002 §4 — impersonation /
brand-name typosquat, MITRE `T1036`) is now wired end-to-end.

| Layer | Artefact |
|---|---|
| Allow-list | [`packages/analysis_engine/allowlists/popular_extensions.txt`](../packages/analysis_engine/allowlists/popular_extensions.txt) — 18 curated publisher.name entries (ms-python.python, github.copilot, etc.). |
| Rule | [`packages/analysis_engine/rules/a3_typosquat.py`](../packages/analysis_engine/rules/a3_typosquat.py) — pure-Python Levenshtein, fires when `0 < d ≤ 2` against the allow-list; severity `high`, confidence `medium`, categories `["attack.T1036", "extrace.ext.typosquat"]`; lifecycle `production`. Activation event is attached as evidence (falls back to an `extension_identity` ref if the report has no activation log). |
| Registry | [`packages/analysis_engine/rules/registry.py`](../packages/analysis_engine/rules/registry.py) `_BUILTIN_RULE_MODULES` extended; `get_production_rules()` now returns 5 rules. |
| Canary | [`extensions/malicious/t1-a3-typosquat-canary/`](../extensions/malicious/t1-a3-typosquat-canary/) — `LABEL.yaml` declares `must_fire: ["extrace.a3.typosquat"]`, `activation_report.json` targets `ms-pyhton.python` (distance 2 from `ms-python.python`). |
| Rule test | [`tests/security/rules/test_a3_typosquat.py`](../tests/security/rules/test_a3_typosquat.py) — 7 cases: canary fires, chat/theme benign fixtures silent, exact-match of legit popular extension stays silent, distance-1 typo fires with correct severity/confidence/evidence, unrelated identifier silent, empty/malformed identifier silent. |
| Coverage test | [`tests/security/test_rule_coverage.py`](../tests/security/test_rule_coverage.py) `EXPECTED_PRODUCTION_RULE_IDS` extended; `test_get_production_rules_returns_all_four_poc_rules` (still named for historical reasons) now asserts the 5-element set. `test_canary_must_fire_rule_ids_match_registered_rules` auto-picks up the new canary. |

Verification: `make test-security` → 41 passed (previously 32).
`make check-all` → ruff, mypy, bandit, ui-types-check, ui-boundaries,
and `make test-unit` (548 passed + 39 DB/smoke skipped) all green on
2026-04-23 against `week7`.

## W7 Phase 3b Deferred — `monitor_attribution.py` Split (2026-04-23)

Deferred to [`documents/POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md) and
**flagged as `[NEXT]` — first item to pull in the next iteration per
user direction (2026-04-23).** Rationale: the current 1122-line module
is a known concern tracked in "Known Concerns" above, but the split's
benefit is rule-author friction — not a PoC gate. The plan (Faz 3b
risk note) explicitly allows this deferral when §10.7 is already
green and a full executor smoke against the A1 canary is unavailable
locally (Docker daemon down). Pulling the refactor in at W7 close
would risk silently invalidating the capture pipeline; the detection
lane has no way to observe that kind of regression without
`make exec-up`. Next session should open
[`documents/POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md) and start from
the "Next iteration (pull first)" section.

## W7 Closure (2026-04-23)

W7 (acceptance + buffer) closes with the PoC acceptance bar met and
one stretch rule (A3) landed. No open W7 items.

### §10.7 checklist final state (11/11)

| # | Item | State |
|---|---|---|
| S1-S5 | Stabilization (legacy folders, import-graph, VS Code pin, capture split, `ExecutorControl`) | ✅ green, evidence above. |
| D1 | A1/A2/A4/A6 rules + T1 canaries fire at ≥medium/≥high | ✅; A3 added as stretch (not a §10.7 gate). |
| D2 | Benign baseline silence | ✅. |
| D3 | Scenario-dropout honesty | ✅. |
| D4 | Verdict rollup marks inconclusive correctly | ✅. |
| D5 | UI DetectionReport rendered + evidence deep-link + invariant | ✅. |
| D6 | `make test-security` green | ✅ (41 passed post-A3). |
| D7 | Demo scenario written | ✅ [`documents/DEMO_SCENARIO.md`](DEMO_SCENARIO.md) + [`scripts/demo_acceptance.py`](../scripts/demo_acceptance.py). |

### Final verification lanes (2026-04-23, week7)

| Lane | Outcome |
|---|---|
| `make test-security` | 41 passed, 0 failed. |
| `make check-all` | ✅ Linting · ✅ Type checking · ✅ Security · ✅ 548 tests passed + 39 skipped (DB/smoke) + 3 deselected. |
| Demo smoke | `python scripts/demo_acceptance.py` → `DEMO GREEN`. |

### Known deferrals (tracked in POST_POC_BACKLOG.md)

- `[LANDED 2026-04-24]` `monitor_attribution.py` split into the
  `attribution/` subpackage (`events.py` + `links.py` +
  `__init__.py` facade). Private-underscore API preserved verbatim;
  `make check-all` 627 passed / 5 skipped. **Docker-based A1 canary
  smoke still user-side** (`make exec-up && make exec-run`).
- `[LANDED 2026-04-24]` Fatal UI-crash classification + fail-fast +
  `ScenarioTrace` failure metadata (`failure_reason_code`,
  `error_detail`). See Post-W7 Hardening section in
  `CLAUDE.md` / `POST_POC_BACKLOG.md`.
- `[LANDED 2026-04-24]` `sim-target` Makefile lane (target-extension
  smoke) separated from `sim-all` (UI-stimulus stress). Usage:
  `make sim-target TARGET=publisher.name [TRIGGERS=…] [SCENARIO=…]`.
- `[LANDED 2026-04-24]` `sim-all` report-semantics + retry-on-crash
  correctness pass (legacy `verdict` migration validator,
  `on_page_reloaded` callback threading,
  `aborted_after_fatal_ui_crash` skipped records, UI blocker probe,
  trimmed `scenario_terminal_usage` stimulus, discovery-log
  rate-limit). See Post-W7 Continuation section below.
- T2 declawed samples + T3 operational plumbing +
  `make test-security-live` hardening.
- `[LANDED 2026-04-24]` Monitor discovery-log rate-limit (cosmetic).
- Workflow/platform cleanups: `SessionLocal` top-of-module, narrow
  `except` in `run_analysis_job`, typed `search_marketplace`.
- UI component splits, `window.__EXTRACE_CONFIG__` context, `AbortController`
  cancellation, feature-boundary ESLint, axe-core.
- Stretch adversary classes A5, A7 (A3 delivered).
- mypy `strict = true` promotion, refactor-doc consolidation.

## Post-W7 Hardening (2026-04-24)

Two `[NEXT]` items from `POST_POC_BACKLOG.md` landed on 2026-04-24
(plus the fatal UI-crash + scan-between restart fixes captured in
CLAUDE.md):

- **`attribution/` subpackage split.** `monitor_attribution.py` (1122
  LoC, single-file evidence/annotation/link/signal blend) was split
  into:
  - [`executor/flows/playwright/attribution/events.py`](../executor/flows/playwright/attribution/events.py)
    — event annotation + classification helpers (`_annotate_*_events`,
    `_classify_event_attribution`, `_upgrade_inotify_correlations`,
    `_matches_extension_signature`, actor/artifact helpers, epoch +
    scenario-timestamp helpers).
  - [`executor/flows/playwright/attribution/links.py`](../executor/flows/playwright/attribution/links.py)
    — evidence-bundle + link builders (`_build_evidence_bundle`,
    `_build_scenario_links`, `_build_temporal_links`,
    `_build_duplicate_file_links`, `_build_noise_links`,
    `_nearest_activation`, `_temporal_confidence`,
    `_dedupe_evidence_links`), sharing helpers from `.events`.
  - [`executor/flows/playwright/attribution/__init__.py`](../executor/flows/playwright/attribution/__init__.py)
    — flat re-export facade. Preserves the dual-import pattern
    (paket mode vs top-level executor mode where `playwright/` is on
    `sys.path`) and the signal-layer shims (`_indexed_target_*`,
    `_build_risk_signals`, `_build_risk_summary`,
    `_build_signal_summary`) exactly as they were. Type-only imports
    sit under `if TYPE_CHECKING:`. 29 names in `__all__` match the
    pre-split surface so the three callers (`monitor.py`,
    `monitor_types.py`, `monitor_lifecycle.py`) only needed the
    module path updated (`monitor_attribution` → `attribution`).
  Pre-existing ruff UP042 warning on
  [`packages/analysis_contracts/detection/enums.py:12`](../packages/analysis_contracts/detection/enums.py)
  (the Python-<3.11 `StrEnum` fallback) was suppressed with
  `# noqa: UP042 - intentional <3.11 fallback`. Verification:
  `make check-all` → 627 passed / 5 skipped; `make test-security` →
  41 passed; demo acceptance → `DEMO GREEN`. **Docker-based A1 canary
  structural diff (`make exec-up && make exec-run` against
  `t1-a1-credential-read-to-network-canary`) remains user-side** — the
  capture-pipeline regression risk flagged in the original deferral
  note can only be closed by a live executor smoke.
- **`sim-target` Makefile lane.** New target in
  [`Makefile`](../Makefile): `make sim-target TARGET=publisher.name
  [TRIGGERS=/path/to/payload.json] [SCENARIO=<name>]` runs
  `entrypoint.py --monitor --target-extension-id $(TARGET)` with
  optional trigger-payload + scenario passthrough. `sim-all` is now
  explicitly labelled "UI-stimulus stress: scenarios w/o target ext."
  in `make help` and in the echo banner, so operators no longer
  mistake an inconclusive `sim-all` report for evidence that a normal
  extension path is green. `TARGET` is required; missing it exits
  non-zero with a usage hint. Verified with `make -n sim-target
  TARGET=ms-python.python` (dry-run).

## Post-W7 Continuation (2026-04-24)

Six follow-ups landed on the back of `sim-all` review findings from
the post-fail-fast report. Four close report-semantics and
loop-honesty gaps that the fail-fast hardening surfaced; one closes a
contract backward-compat risk introduced by the `verdict` →
`signal_summary` rename; one closes the monitor discovery-log spam
entry on POST_POC_BACKLOG. None change architecture; each was
required for `sim-all` / `sim-target` reports to be honest artefacts.

- **Legacy `verdict` → `signal_summary` migration validator.** The
  W7-entry rename (`build_verdict` → `build_signal_summary`) ships
  under `extra="forbid"`, which meant any `ActivationReport` produced
  by an older runner or stored on disk from before the rename would
  raise on load. A new `model_validator(mode="before")` on
  [`packages/analysis_contracts/contracts.py::ActivationReport`](../packages/analysis_contracts/contracts.py)
  re-maps a legacy `verdict` field to `signal_summary` during parse,
  so round-trip survives. Test:
  [`tests/platform/contracts/test_analysis_fixture_baselines.py::test_activation_report_accepts_legacy_verdict_field`](../tests/platform/contracts/test_analysis_fixture_baselines.py)
  copies the ms-python fixture, renames `signal_summary` → `verdict`,
  validates, dumps, and re-parses.

- **`on_page_reloaded` callback threading (retry-on-crash fix).**
  Previously `--retry-on-crash` called
  `vscode.reload_workbench_window` but the caller kept using the
  *old* `Page` reference, so every scenario after the reload hit the
  dead handle and re-crashed. `_run_scenario_sequence`
  ([`executor/flows/playwright/automation.py`](../executor/flows/playwright/automation.py))
  now accepts an `on_page_reloaded: Callable[[Page], None]` kwarg.
  [`entrypoint_runner.py`](../executor/flows/playwright/entrypoint_runner.py)
  wires it to a `nonlocal` closure that rebinds both its own `page`
  and `mon.page`. Coverage:
  `test_retry_on_crash_invokes_on_page_reloaded_callback`,
  `test_on_page_reloaded_not_called_on_reload_failure`.

- **`aborted_after_fatal_ui_crash` skipped-scenario records.**
  Fail-fast used to leave `summary.skipped_scenarios` empty — a
  renderer crash at scenario #2 of 5 silently dropped scenarios 3-5
  from the report. `_mark_remaining_scenarios_aborted` in
  `automation.py` now emits a `SkippedScenarioRecord` for each unrun
  scenario with `reason="aborted_after_fatal_ui_crash"`, so the
  report faithfully shows how many scenarios the run intended vs.
  actually attempted. Fires both on the plain fail-fast path and on
  the reload-failure branch when `--retry-on-crash` is opted in.
  Coverage: `test_fail_fast_marks_remaining_scenarios_as_aborted`,
  `test_fail_fast_aborts_on_reload_failure_when_retry_requested`.

- **UI blocker probe before each scenario.** A dismissal dialog left
  over from a previous scenario could freeze the next scenario's
  first keystroke indefinitely with no evidence line.
  `_run_scenario_sequence` now accepts an optional
  `ui_blocker_probe(page, scenario_name)` kwarg;
  `entrypoint_runner.py` wires it to
  `editor._dismiss_notification`. When a blocker is detected, both
  `ui_blocker_detected` and `ui_blocker_dismissed` automation events
  are recorded on `mon`. Exceptions scoped explicitly to
  `(PlaywrightError, RuntimeError, ValueError)` — the probe never
  throws into the scenario loop. Coverage:
  `test_ui_blocker_probe_invoked_before_each_scenario`,
  `test_ui_blocker_probe_failure_does_not_break_loop`,
  `test_main_wires_ui_blocker_probe_and_page_reload_callbacks`.

- **Trimmed `scenario_terminal_usage` stimulus.**
  [`executor/flows/playwright/scenarios/runtime.py`](../executor/flows/playwright/scenarios/runtime.py)
  removed `cat .env`, `pip list`, `npm ls --depth=0` — high-output
  commands that (a) collided with target-owned secret-read +
  network-reconnaissance signals in attribution and (b) combined
  with aggressive keyboard typing were a repeatable
  `terminal_usage → Keyboard.type: Target crashed` trigger. Kept:
  `ls -la`, `git status`, `python --version`, `node --version`,
  `echo $PATH`, `pwd`. 250 ms warm-up added before each
  `type_in_terminal` call. Adversarial stimulus belongs on the
  fixture lane, not the benign path — now spelled out in the
  scenario's docstring. Updated
  [`tests/executor/test_playwright_helpers.py::test_scenario_terminal_usage_runs_expected_commands`](../tests/executor/test_playwright_helpers.py)
  accordingly.

- **Monitor discovery-log rate-limit (POST_POC_BACKLOG cosmetic item
  landed).** `find_exthost_logs()` in
  [`executor/flows/playwright/monitor_sources.py`](../executor/flows/playwright/monitor_sources.py)
  and [`executor/flows/playwright/runtime_capture/extension_host.py`](../executor/flows/playwright/runtime_capture/extension_host.py)
  now keep a module-level `_LAST_EXTHOST_LOG_COUNT: int = -1` and
  only emit `"Found N Extension Host log file(s)"` when the count
  changes from the previously-seen value. `make sim-all` scenario
  progress is readable again; the state-change guard means the
  signal reappears automatically if a new exthost log shows up
  mid-run.

Verification across all six: 636 pytest passes (+9 new tests,
including the legacy `verdict` migration round-trip, the two
retry-callback paths, the fail-fast skipped-record semantics, and
the two UI-blocker-probe wiring tests). `make test-security` → 41
passed, `make typecheck` clean (207 source files), demo acceptance
(`.venv/bin/python scripts/demo_acceptance.py`) → `DEMO GREEN`.

## Simulation Progress + Cancel + VNC Harness Fix (2026-04-25)

Branch `feat/simulation-progress-cancel` landed four loosely-coupled
tracks plus a focused code-review pass:

- **Realistic progress reporting.** Replaced
  `completed_steps / total_steps` with weighted phase distribution
  (reset_sandbox=5, install_extension=10, build_triggers=10,
  run_monitoring=70, finalize_report=5) in
  [`ui/src/lib/adapters/job.ts`](../ui/src/lib/adapters/job.ts) plus
  per-scenario sub-progress on the run_monitoring phase. Heartbeat in
  [`workflows/marketplace/analysis_execution.py`](../workflows/marketplace/analysis_execution.py)
  reads the in-flight report's `scenario_traces` and emits
  `progress={completed, total}` to the UI every 5 s. The bar now climbs
  monotonically through realistic phase weights instead of jumping in
  20 % chunks.

- **Cancel flow (full stack).** New `cancel_analysis_job` CRUD with
  `with_for_update()` pessimistic lock and `JobNotCancellableError`
  guard against racing complete-vs-cancel
  ([`appcore/storage/crud_ops/analysis_jobs.py`](../appcore/storage/crud_ops/analysis_jobs.py)).
  New `POST /api/marketplace/analyze/{job_id}/cancel` endpoint
  ([`workflows/marketplace/router.py`](../workflows/marketplace/router.py))
  returns the snapshot, 404 on missing, 409 on terminal-state. The
  monitoring heartbeat polls `is_job_cancelled` every tick, calls a
  `_heartbeat_on_cancel` that triggers `executor_control.reset_sandbox`,
  and the main thread converts the resulting `ExecutorError` into
  `AnalysisCancelledError` so `run_analysis_job` returns silently
  without clobbering the cancel state. UI adds a Stop simulation button
  (`useMutation` + `setQueryData`) gated by `isJobActive`.
  `ANALYSIS_JOB_STATUSES` extended with `cancelled`; no Alembic
  migration needed (status is plain `String` with no CHECK constraint).

- **VNC harness crash fix.** The user-reported crash signature was
  `extract_harness automation crashes on VNC` mid-scenario.
  Root cause: the harness extension wrote a ready marker at activate()
  but the marker was never deleted, so after a workbench reload polling
  saw the stale marker and let `commands.run_command(...)` race ahead
  before the new activation re-registered the command.
  [`vscode.py:reload_workbench_window`](../executor/flows/playwright/vscode.py)
  now `unlink()`s `_HARNESS_READY_PATH` before dispatching the reload;
  `extension.js:activate()` is now `async` and `await`s
  `writeHarnessReadyMarker()` so a write failure fails activation
  loudly and the Python polling sees a clean
  `HarnessUnavailableError` timeout instead of stale-marker confusion.

- **Demo runnable canary fixture.** New T1 `t1-demo-runnable-canary`
  under [`extensions/malicious/`](../extensions/malicious/) with
  declawed payload (localhost-only POST to 127.0.0.1:8787 with 500 ms
  timeout, workspace-local file write, explicit `onCommand`
  activation). New rule
  [`packages/analysis_engine/rules/demo_runnable_canary.py`](../packages/analysis_engine/rules/demo_runnable_canary.py)
  with `target_extension_expected` gate so it can't false-positive on
  real extensions. New `make demo-canary` and `make demo-canary-offline`
  Makefile lanes for end-to-end and offline-fixture validation.

- **Code review pass (this session).** Critical fixes applied inline:
  the stale-marker bug, the fire-and-forget marker write,
  `progressLabel` realignment from "3/5 steps complete" → context-aware
  "Step N of 5 · scenario X/Y", ARIA attributes (`role="progressbar"`,
  `aria-valuenow/min/max`, `aria-label`) on both progress bars
  ([`SimulationPage.tsx`](../ui/src/features/simulation/SimulationPage.tsx)
  and [`RunActivityRail.tsx`](../ui/src/components/simulation/RunActivityRail.tsx)),
  and narrowed the bare `except Exception` in the heartbeat to
  `(ExecutorError, RuntimeError, OSError, ValueError, AttributeError)`.
  Suggestions deferred to
  [`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md): custom `role="alertdialog"`
  to replace `window.confirm`, cancel-mutation timeout/retry, heartbeat
  sandbox-reset off-thread, schema duplication doc/dedup,
  `is_job_cancelled` session churn, heartbeat refactor, cancel-after-finish
  - cancel-during-completion race tests, heartbeat 30 s → 5 s load
  verification (all tagged `[FOLLOWUP simulation-progress-cancel]`).

Verification: 114 backend tests
([`workflows/marketplace`](../workflows/marketplace/),
[`platform/storage`](../tests/platform/storage/),
[`platform/contracts`](../tests/platform/contracts/),
[`security`](../tests/security/)) + 33 executor stimulus tests + 76
vscode reload tests + 18 UI tests pass; `tsc --noEmit` clean,
ESLint clean on touched files; `make demo-canary-offline` test
passes.

## PR345 Complete — Target Activation Lifecycle (2026-04-27)

W8 entry gate (`REFACTOR_OPTIMIZATION.md §11.1`) closes with PR345
complete. PR1+PR2 landed 2026-04-24 (commit `1b62434`); PR3+PR4 +
ADR 0006 + PR5 landed 2026-04-27 on branch `feat/pr345-completion`.

### Commits

| Stage | Commit | Scope |
|---|---|---|
| PR1 | `1b62434` | `EVENT_ATTEMPT_LIFECYCLE_STATES` + `EventAttemptRecord.status` field validator |
| PR2 | `1b62434` | `reconcile_event_attempts` upgrades to `activation_seen` / `target_log_seen`; `attempt_has_runtime_evidence` accepts both states |
| PR3 | `c59762d` | `extension_host.py` `_LIFECYCLE_MARKER_PATTERNS` (activate fn entry/exit + command/provider register) + `ActivationEntry.marker_type` field |
| PR4 | `c5e400b` | `_assert_target_stream_invariant` build-path guard in `monitor_lifecycle.py`; serialization-time demote in `monitor_types.log_streams` |
| ADR 0006 | `b737529` | [`documents/adrs/0006-target-output-channel-capture.md`](adrs/0006-target-output-channel-capture.md) — Status: Accepted, Option (a) baseline |
| PR5 | `8453fb2` | Harness `createOutputChannel` hook + `OutputSignalEvent` dataclass + `output_signals.py` parser/attribution + `_build_evidence_bundle` integration + `target_extension_observed` OR-clause extension |

### Verification (2026-04-27, branch `feat/pr345-completion`)

| Lane | Outcome |
|---|---|
| `make test-security` | 45 passed (gate ≥ 41 satisfied) |
| `tests/executor + tests/security + tests/platform/contracts` | 387 passed, 6 skipped (canary `must_not_fire` gaps unchanged) |
| `tests/executor/test_output_signal_capture.py` (new, PR5) | 5 passed |
| `tests/executor/test_playwright_monitor_lifecycle.py` (PR4 invariant test added) | 11 passed |
| `tests/executor/test_playwright_monitor_runtime.py` (PR3 5 new tests) | 27 passed |
| `.venv/bin/python scripts/demo_acceptance.py` | `DEMO GREEN` |
| ruff + mypy on touched modules | clean |
| UI contract regen (`scripts/generate_ui_contracts.py`) | `marker_type?` + `OutputSignalEventDto` + `output_signal_events?` propagated to `ui/src/lib/types/contracts.ts` |

### W8 entry-gate checklist (`REFACTOR_OPTIMIZATION.md §11.1`)

- [x] PR345 PRs 1-5 landed
- [x] PR5 ADR (`0006-target-output-channel-capture.md`) merged with
      Status: Accepted
- [x] `make check-all` green (executor/security/contracts lanes verified;
      Docker-based smoke deferred to user-side)
- [x] `make test-security` 45 ≥ 41
- [x] `scripts/demo_acceptance.py` → `DEMO GREEN`
- [x] `REFACTOR_STATUS.md` "PR345 Complete" closure block (this section)

### Followup landed (2026-04-27, post-PR345)

Codex review surfaced two semantic gaps in the PR345 surface; both
closed in a single follow-up commit and are reflected here.

- **Bug 1 — output_signal_events were not lifecycle evidence.** PR5
  wired Output channel writes into `evidence_events` and into the
  `target_extension_observed` OR clause, but
  `health_reconciliation._target_log_stream_summaries` only read
  `log_streams`, so an attempt with a target-owned output signal but
  no separate log entry stayed at `activation_seen` instead of
  upgrading to `target_log_seen`. Now harvested.
- **Bug 2 — activation entries were collapsing the lifecycle.**
  Every target activation is mirrored into `target_extension_host`
  by `_append_activation_log_entries` with `kind="activation"`, and
  reconciliation didn't ignore `kind="activation"` rows — so
  any target activation auto-upgraded to `target_log_seen`,
  defeating the `activation_seen` ↔ `target_log_seen` distinction
  PR2 introduced. `_target_log_stream_summaries` now skips
  `kind == "activation"`.
- **Doc — ADR 0006 §5 was over-promising.** §5 read "after PR3-PR5
  land, the rule tightens to (conjunction)", but the conjunction at
  the `target_extension_observed` level is deferred. ADR rewritten
  to split the lifecycle landing (done in PR5 + followup) from the
  top-level conjunction tightening (deferred), with a 2026-04-27
  Amended note in the header.

New tests:
`tests/executor/test_playwright_monitor_attribution.py` —
`test_reconcile_event_attempts_activation_log_entry_alone_keeps_activation_seen`,
`test_reconcile_event_attempts_target_output_signal_upgrades_to_target_log_seen`.
389 passed, 6 skipped on the executor + security + contracts lane;
`make test-security` 45 passed; demo acceptance `DEMO GREEN`.

### Deferred

- ADR 0006 §5 full conjunction tightening of the **top-level**
  `target_extension_observed` predicate (lifecycle-level evidence
  consumption is closed; the property still uses additive OR).
  Full `(activation_seen AND (target_log OR target_output_signal))`
  rule needs broad fixture/tests churn. Post-W8 follow-up.
- Docker-based A1 canary structural diff smoke (`make exec-up && make
  exec-run` against `t1-a1-credential-read-to-network-canary`) remains
  user-side; capture pipeline regression risk only fully closed by a
  live executor run.

## W8-0 Landed — Deterministic Harness Readiness Gate (2026-04-27)

W8-0 (POST_POC_BACKLOG `[PROMOTED]`, ordered before W8-1 + W8-3) closes
on `feat/pr345-completion` with three sequential commits. Trigger
report:
`output/activation_report_ms-python.python-2026.5.2026042602-cba16dba0258.json`
— 21 `event_attempts`, 9× `harness_command_unavailable`,
`target_extension_observed=true`, `output_signal_events=0`. Root cause
hypothesis: harness ready marker payload was a 2-field stub
(`ready_at_unix`, `command`); Python side polled only `path.exists()`.
A stale or partially-written marker from a previous container life
satisfied that gate and tricked every stimulus attempt into firing
before the harness command was registered.

### Commits

| Stage | Commit | Scope |
|---|---|---|
| PR-A | `9c2e2d9` | `ExTrace Harness` Output Channel + diagnostic emit on `activate()` enter/exit + marker-write phases. PR345 PR5 hook captures every appendLine as `OutputSignalEvent(kind=output_channel_appendline)`; no parser change. |
| PR-B | `9eb4aaf` | Marker payload widened with `marker_version`, `epoch_run_id`, `pid`; atomic tmp+rename. `start.sh` exports `EXTRACE_EPOCH_RUN_ID` per boot. New `parse_harness_ready_marker` (frozen dataclass) + four typed `HarnessUnavailableError.reason_code` sub-codes. `_ensure_harness_ready` accepts `expected_epoch_run_id`. |
| PR-C | `d39a612` | `_ensure_harness_ready_with_recovery` wraps the wait with one controlled retry on `MISSING`/`TIMEOUT`; `STALE`/`INVALID` non-recoverable. `automation.py` `HarnessUnavailableError` catch block reads `exc.reason_code` instead of the legacy generic constant. `health_summary._REASON_LABELS` gains 4 human-readable sentences. |

### Verification (2026-04-27, branch `feat/pr345-completion`)

| Lane | Outcome |
|---|---|
| `make test-security` | 45 passed (gate ≥ 41 satisfied) |
| `tests/executor/test_playwright_stimulus.py` | 25 passed (W8-0 alone adds 12 new tests) |
| `tests/executor/test_output_signal_capture.py` | 6 passed (PR-A adds 1 lifecycle case) |
| `tests/executor/test_playwright_automation.py` | 19 passed (no regression on the harness-skip path) |
| `tests/executor + tests/security + tests/platform/contracts` | 401 passed, 6 skipped |
| `make typecheck` | 213 source files, no issues |
| `make lint-check` | clean |

### Reason code rollup

| Code | When raised | Recoverable? |
|---|---|---|
| `harness_ready_marker_missing` | Deadline passed, marker never appeared. | Yes (one retry) |
| `harness_ready_marker_invalid` | Marker exists but JSON unparseable / required field missing. | No |
| `harness_ready_marker_stale` | Payload `epoch_run_id` ≠ container `EXTRACE_EPOCH_RUN_ID` (only checked when both non-empty). | No |
| `harness_activation_timeout` | Marker arrived after the deadline (race observed mid-poll). | Yes (one retry) |

### Deferred / open

- **Docker-based smoke ran 2026-04-27 14:57** (report
  `output/activation_report_ms-python.python-2026.5.2026042602-80f070c03e9c.json`).
  Acceptance signal (a) — `output_signal_events` carrying
  `ExTrace Harness` lifecycle entries — **failed live**: the
  PR-A-deployed image emitted the four phase events to disk but
  the parser was reading `exthost.log` rather than the
  `output_logging_*/<idx>-<channel>.log` files VS Code 1.105+
  actually persists Output channel content to. Closed by the
  capture-pipeline fix below. Acceptance signal (b) — typed
  harness-readiness reason codes — **still unconfirmed**: the
  smoke surfaced 9 attempts with `harness_verification_unconfirmed`,
  none with the W8-0 PR-B/PR-C typed sub-codes. Stays user-side
  until a follow-up `make sim-target` produces an attempt that
  trips the typed marker path.
- **`failure_reason_code` formal enum migration** stays under
  `[PROMOTED → W10-1]`. The four new strings reserve a non-colliding
  namespace (`harness_*_marker_*` + `harness_activation_timeout`) so
  the W10 PR can promote them without touching call sites.
- W8-1 landed (see "W8-1 Landed" section below); W8-3 (URI argv-form)
  remains unblocked — the entry-gate ordering in POST_POC_BACKLOG
  `[PROMOTED → W8-0]` is satisfied.

## PR345 / W8-0 Closeout Tail (2026-04-27)

Two follow-up commits closed audit-trail gaps that surfaced after the
W8-0 closeout block was written:

- **`9a90880` — `PR345 closeout: regenerate UI contracts + harness
  shim event surface`**. Three loosely-coupled fixes in one commit:
  (a) `scripts/generate_ui_contracts.py` extended with
  `OutputSignalEvent` so `ui/src/lib/types/contracts.ts` actually
  carries `OutputSignalEventDto` + `ActivationReport.output_signal_events`
  (the PR345 PR5 closure note had claimed this propagation; the
  generator hadn't been re-run); (b)
  `executor/flows/harness_extension/providers.js` — `LocalAuthProvider`
  and new `LocalFileSystemProvider` now expose VS Code's required
  `EventEmitter.event` surface (`onDidChangeSessions` /
  `onDidChangeFile`) and emit change events on
  `writeFile`/`rename`/`delete`; (c) new
  `tests/executor/test_harness_extension_contract.py` runs a Node-level
  shim contract check that mocks the `vscode` module and asserts the
  event surface fires; UI test
  `ui/src/features/simulation/SimulationPage.test.tsx` tightens the
  `resolveCancel` mock signature to `AnalyzeJobStatusDto`.
- **`5e16c7a` — `Executor: cleanup stale entrypoint on automation
  timeout`**. When `_docker_exec_allow_partial` raises
  `ExecutorError` with `returncode=None` (timeout / signal kill, no
  exit code captured), the in-container Python entrypoint can survive
  past the host-side timeout and leave a stale process owning the
  report directory. `executor/host.py:303-310` now calls
  `_cleanup_stale_entrypoint_processes()` before re-raising so the
  next run starts from a clean container state. Coverage:
  `tests/scanner/test_executor.py::test_run_automation_timeout`
  asserts the cleanup is invoked exactly once on the timeout path.

Verification (2026-04-27, branch `feat/pr345-completion`):
`make test-security` 45 ≥ 41 stable; `make check-all` 726 passed,
6 skipped; ruff + mypy + bandit + ui-types-check + ui-boundaries all
green.

## W8-1 Landed — VSIX Zip-Bomb + Entry-Count Guard (2026-04-27)

W8-1 (`REFACTOR_OPTIMIZATION.md §11.5` item 1) closes on
`feat/w8-1-vsix-hardening`. Adversarial VSIX archives now fail closed
before extraction can saturate disk or memory.

### Change

`workflows/marketplace/client.py` gained three module-level extraction
limits and a typed `VSIXUnpackError`:

| Limit | Value | Trigger |
|---|---|---|
| `MAX_UNCOMPRESSED_SIZE` | `256 * 1024 * 1024` (256 MiB) | Sum of `ZipInfo.file_size` over `extension/` members exceeds the cap. |
| `MAX_COMPRESSION_RATIO` | `100` | Cumulative `file_size / compress_size` ratio exceeds the cap (zip-bomb signal). |
| `MAX_FILE_COUNT` | `2_000` | More than 2 000 entries under `extension/`. |

`_extract_vsix_to_dir` accumulates the three counters per accepted
member and raises `VSIXUnpackError` on first violation. The pre-W8-1
path-traversal guards (`..` reject + `target.resolve().relative_to`)
remain unchanged. `download_and_extract_vsix` extends its except
tuple to include `VSIXUnpackError` so the partial extraction directory
is cleaned up on failure.

### Verification

| Lane | Outcome |
|---|---|
| `tests/workflows/marketplace/test_vsix_hardening.py` (new) | 5 passed: normal vsix extracts, oversize rejects, ratio rejects, file-count rejects, path-traversal regression guard. |
| `tests/workflows/marketplace/` (full) | 126 passed (no regression). |
| `make check-all` | ✅ ruff · mypy (214 source files) · bandit · ui-types-check · ui-boundaries · 726 passed + 6 skipped. |
| `make test-security` | 45 passed (baseline preserved — W8-1 tests live under `tests/workflows/marketplace/`, not `tests/security/`). |

### Deferred / open

- ADR 0002 §7.2.6 (supply-chain hardening) does not yet pin the three
  numeric limits. A short addendum is appropriate when bundling the
  W8 ADR / runbook closeout (low priority; the limits live in code).
- W8-2 (`safe_marketplace_slug` identity helper) is the natural next
  W8 task and shares the regex disiplini target with W8-5.

## W8-0 Follow-up Fixes (2026-04-27)

Two fixes landed on `fix/w8-0-capture-and-health-reasons` to close
the capture-pipeline gap exposed by the live smoke and the
long-tracked `[FOLLOWUP codex-automation-3]` item that the same
report surfaced as live evidence.

### Fix #1 — Output channel capture pipeline reads VS Code 1.105+ persistence files

`output_signal_events=0` despite W8-0 PR-A `ExTrace Harness`
diagnostic emits being correctly deployed. Root cause: VS Code
1.105 stopped piping extension `console.log` into `exthost.log`;
each Output channel persists its content to
`<user-data>/logs/<session>/window<N>/exthost/output_logging_<ts>/<idx>-<channel>.log`
instead. The `[extrace-harness]` marker stream the parser scans
exthost.log for never lands there.

- New
  [`output_signals.read_output_channel_logs(logs_dir)`](../executor/flows/playwright/output_signals.py)
  walks the per-channel persistence files, parses each line
  (JSON-with-`ts` field preferred; file mtime fallback for plain
  text), and emits one `OutputSignalEvent` per appendLine.
- New
  [`output_signals.merge_output_signal_events(*sources)`](../executor/flows/playwright/output_signals.py)
  deduplicates the merged stream by `(channel, text, timestamp)`
  so the legacy exthost-output marker source remains compatible
  for older fixtures.
- [`monitor_lifecycle.py`](../executor/flows/playwright/monitor_lifecycle.py)
  `_build_run_report` now reads both sources and merges them
  before attribution.
- Coverage: 5 new tests in
  [`tests/executor/test_output_signal_capture.py`](../tests/executor/test_output_signal_capture.py)
  pin the new reader against a synthetic
  `output_logging_*/<idx>-<channel>.log` tree (JSON-with-ts +
  plain-text mtime fallback + filename filter + missing-dir
  noop + dedup).

### Fix #2 — `automation_health` propagates partial-evidence reason codes regardless of execution mode

`[FOLLOWUP codex-automation-3]` (POST_POC_BACKLOG L594-625): the
W7 entry "layered run_quality label" patch closed
`official_unresolved_present` only inside the `run_quality`
reason text builder. `automation_health.reasons` stayed empty
for layered runs even when `run_quality` correctly dropped to
`medium`, leaving operators reading the health chip with
misplaced confidence. The 2026-04-27 smoke produced
`automation_health.status="healthy"`, `reasons=[]` while
`run_quality="medium"`, `run_quality_reasons=[2 entries]` —
exactly the gap the FOLLOWUP describes.

- [`health_summary.py::build_automation_health`](../executor/flows/playwright/health_summary.py)
  now appends all four FOLLOWUP-listed reason codes regardless of
  layered/non-layered mode and demotes status `healthy` →
  `degraded` whenever any of them fires:
  - `verification_gap_present` (run-level: `verification_gap > 0`)
  - `chat_tool_verification_incomplete` (run-level: helper match)
  - `official_unresolved_present` (run-level:
    `official_event_coverage.unresolved > 0`)
  - **`harness_verification_unconfirmed_present`** (attempt-level:
    any `event_attempts[].failure_reason_code ==
    "harness_verification_unconfirmed"`).
- [`health_summary.py::build_run_quality`](../executor/flows/playwright/health_summary.py)
  layered branch refined: a `degraded` run whose reasons are
  *only* partial-evidence codes returns `medium`, not `low` —
  partial evidence is not a run failure. The
  ``partial_evidence_reason_codes`` set tracks all four codes so
  the heuristic stays consistent across new propagations.
  Real-failure degradations (extension_host_log_missing,
  scenario_failures, trigger_plan_not_loaded/applied, etc.) still
  drop to `low`.
- Pinned existing test
  [`test_layered_harness_chat_tool_attempt_degrades_health_and_keeps_quality_medium`](../tests/executor/test_playwright_monitor_attribution.py)
  (renamed from `keeps_health_healthy_and_quality_medium`) and
  added 4 dedicated cases in
  [`tests/executor/test_playwright_health_summary.py`](../tests/executor/test_playwright_health_summary.py)
  for layered + non-layered + clean-run regression guard +
  attempt-level harness propagation.

### Verification

| Lane | Outcome |
|---|---|
| `tests/executor/test_output_signal_capture.py` | 11 passed (5 new). |
| `tests/executor/test_playwright_health_summary.py` | 7 passed (3 new). |
| `tests/executor/test_playwright_monitor_attribution.py` | 76 passed (1 renamed + assertion flipped per FOLLOWUP). |
| `make test-security` | 45 passed. |
| `make check-all` | green (recorded at commit time). |

### Live live-scan-derived backlog entries (2026-04-27)

The same 14:57 scan surfaced the `[FOLLOWUP capability-verification-gap]`
(`debug` + `terminal_tasks` capability verification) backlog entry
recorded under `POST_POC_BACKLOG.md` "Live-scan findings" section.
W12-fingerprint stale-image regression class
(`[FOLLOWUP codex-automation-5]`) was ruled out for this run — the
deployed image carried the PR-A code; the gap was capture-side, not
build-side.

## Week 5 Start Rule

Week 5 begins only after the Week 4 exit criteria above are green. Detection
work does not reopen Week 4 refactors except to fix a blocking regression.
