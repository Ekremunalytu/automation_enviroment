# Refactor Status

`Last Updated: 2026-04-21`

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

- Week 4 closure is green and remains the active gate before any broader Week 5
  detection work.
- Async marketplace job state is durable in PostgreSQL via `analysis_jobs`.
- Activation reports remain artifact-first under `output/activation_report_*.json`.
- Workflow code now depends on the sandbox through `executor.control`.
- Initial W5 scaffold exists under `packages/analysis_contracts/detection/`,
  `extensions/malicious/`, and `tests/security/`.
- Root legacy directories (`routers/`, `scanner/`, `core/`, `database/`,
  `crud/`, `models/`, `schemas/`) are removed from the canonical repo surface.
- Dormant root placeholders `apps/` and `legacy_ui/` are removed from the repo
  surface; the canonical runtime tree is now `appcore/`, `packages/`,
  `workflows/`, `executor/`, `ui/`, and `tests/`.

## Week 4 Exit Criteria

- Repo-wide import graph checks pass.
- Executor retry / cleanup / monotonic timing work is in place.
  Harness-extension checksum verification is deferred to Week 5 (see below).
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
- Automation reliability now fails closed at the verdict layer: missing
  target observation or activation yields `inconclusive` instead of a
  silent `clean`. The execution side is still not fully hardened,
  though; stimulus runs still rely on fixed waits, static workspace
  seeding, and no dedicated idle-observation pass.
- Week 5 closes as PoC-complete, but not hardening-complete. Remaining
  W6/W7 priorities:
  - activation confirmation gate and dynamic post-stimulus verification
  - extension-aware workspace seeding and materializer completeness
  - deferred-activation coverage via an idle observation window
  - runtime capture gap closure for HTTP body capture / child-process tracking
  - explicit CI egress hardening for the security-fixture lane
  - scenario-dropout honesty: scenarios skipped by name mismatch or
    missing handler must surface in `failed_scenarios` (or a new
    `skipped_scenarios` bucket) with a reason code and must demote
    `run_quality` / `automation_health` — silent drops violate
    `DEVELOPMENT_PRIORITIES.md` §1 "Executor Failure Honesty"
    (observed 2026-04-21 on ms-python baseline: 5 requested / 3 run
    / 0 failed)
  - correlative-signal false-positive floor: `signal_policy`
    `correlative_suspicious_activity` must require a minimum
    evidence count and a tightened time window so benign baselines
    (ms-python, chat, theme) do not raise a medium signal — precondition
    for the W7 §10.7 acceptance clause "no benign fixture triggers a
    production rule"

## W6 Ready State (2026-04-20)

- Pre-W6 structural cleanup is complete.
- W6 starts directly with automation reliability and capture hardening work.
- Structural tree cleanup, legacy trigger-plan compatibility, and `monitor.py`
  modularization are no longer open W6 scope items unless a regression is
  found.

## Week 5 Start Rule

Week 5 begins only after the Week 4 exit criteria above are green. Detection
work does not reopen Week 4 refactors except to fix a blocking regression.
