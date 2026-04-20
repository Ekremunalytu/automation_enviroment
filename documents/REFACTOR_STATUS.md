# Refactor Status

`Last Updated: 2026-04-20`

This is the active status board for the Week 1-4 stabilization work. Use this
file for current closure state; use `REFACTOR_EXECUTION_PLAN.md` for sequence
and rationale.

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

## Week 4 Exit Criteria

- Repo-wide import graph checks pass.
- Executor retry / cleanup / monotonic timing work is in place.
  Harness-extension checksum verification is deferred to Week 5 (see below).
- `monitor.py` capture concerns are separated into the `runtime_capture/`
  subpackage; full split is not required.
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
- UI eslint no longer has hard errors (non-null-assertion on optional
  chain removed, non-component helper moved to
  `features/simulation/telemetry.ts`). One pre-existing
  `react-hooks/exhaustive-deps` warning remains and is tracked for the
  UI follow-up lane, not Week 4.
- `.venv/bin/ruff check .`, `make ui-types-check`, `make ui-boundaries`,
  `pytest tests/` (unit+integration+architecture+security lanes) all
  green on 2026-04-20.

## Deferred to Week 5

- **Harness-extension checksum verification.** Implementing sha256
  attestation over `executor/flows/harness_extension/*.js` before the
  executor trusts a bundle is a security-posture property (ADR 0002
  §7.2.6 supply-chain integrity). It belongs in the W5 security
  implementation pass alongside detection rules and malicious-fixture
  wiring, not in the Week 4 stabilization pass. Track it as the first
  supply-chain task in the W5 checklist.

## Week 5 Start Rule

Week 5 begins only after the Week 4 exit criteria above are green. Detection
work does not reopen Week 4 refactors except to fix a blocking regression.
