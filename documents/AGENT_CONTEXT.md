# Agent Context

`Last Updated: 2026-04-24`

This is the thin-context project map for coding agents. Read root `AGENTS.md`
for hard rules first; use this file for fast task routing.

If older docs or task notes conflict with the active refactor direction, check
`documents/REFACTOR_STATUS.md` first, then
`documents/REFACTOR_EXECUTION_PLAN.md` (historical Week 1-4 plan) and
`documents/REFACTOR_OPTIMIZATION.md` §10 (W0-W7 7-week window). Treat
`documents/REFACTOR_EXPANSION_NOTES.md` as non-binding follow-on guidance.

## Project Phase Snapshot (2026-04-24)

- Week 4 stabilization closed on `2026-04-20` and remains the gate that
  protected detection foundations from runtime-boundary churn.
- W0 (security foundations, spec): complete — ADRs 0002-0004 written.
- W1-W4: automation stabilization (legacy cleanup, import-graph,
  executor determinism + modularization, sandbox boundary).
- W5 (detection foundations): landed 2026-04-20 (contracts, A1/A2/A4/A6
  rules, T1 canaries, `make test-security`).
- W6 (automation reliability + capture hardening): landed 2026-04-21
  (scenario-ledger honesty, bounded waits, capture bounds, CI egress).
- Post-W6 bridge (2026-04-21): `RiskSignal.confidence_tier` via
  `quantize_confidence` + `detection_report_invariant_issues`
  cross-layer link check.
- W6 correctness follow-up (2026-04-23): A1/A2/A4 now consult
  `is_target_extension_event` + `attribution_status ∈ {strong,direct}`
  via `target_file_events` / `target_unknown_outbound_network_events`;
  `tls_client_hello` added to `TLS_EVENT_TYPES`; any
  `RuleExecutionStatus.ERROR` degrades automation health to
  `inconclusive` before verdict rollup; `.gitignore` exception-list so
  T1 canaries + chat/theme benign baselines actually reach the
  `security-fixtures` CI lane. **W6 closed.**
- **W7 (acceptance + buffer):** closed 2026-04-23. §10.7 PoC acceptance
  checklist met (11/11); [`documents/DEMO_SCENARIO.md`](DEMO_SCENARIO.md) +
  [`scripts/demo_acceptance.py`](../scripts/demo_acceptance.py) cover the A1
  credential-read → network canary end-to-end. Phase 3a buffer added stretch
  rule `extrace.a3.typosquat` with canary + `popular_extensions.txt`
  allow-list. Final `make test-security` → 41 passed, `make check-all` →
  627 passed / 5 skipped.
- **Post-W7 hardening (2026-04-24):** four reliability + modularization
  landings on top of W7 closure:
  1. Fatal UI-crash classification + fail-fast in `_run_scenario_sequence`
     ([`executor/flows/playwright/automation.py`](../executor/flows/playwright/automation.py))
     with `failure_reason_code = "fatal_ui_crash"` degrading health to
     `inconclusive`; opt-in `--retry-on-crash` flag.
  2. Scan-between VS Code restart orchestrated by `reset_executor_state`
     ([`executor/flows/playwright/reset_state.py`](../executor/flows/playwright/reset_state.py))
     with shared `launch_vscode.sh` script (fixes ESLint
     `onStartupFinished` install race on second scan).
  3. `attribution/` subpackage split — the 1122-LoC
     `executor/flows/playwright/monitor_attribution.py` is now
     [`attribution/events.py`](../executor/flows/playwright/attribution/events.py),
     [`attribution/links.py`](../executor/flows/playwright/attribution/links.py),
     and a flat re-export facade preserving the 29-name underscore
     API verbatim.
  4. `sim-target` Makefile lane: `make sim-target TARGET=publisher.name
     [TRIGGERS=…] [SCENARIO=…]` separates target-extension smoke from
     the `sim-all` UI-stimulus stress run.
- Post-PoC deferrals tracked in
  [`documents/POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md); next iteration
  starts from its "Next iteration (pull first)" block.

## Read Path

1. `AGENTS.md`
2. this file
3. only the subsystem docs the task actually touches
4. `documents/REFACTOR_STATUS.md` for current closure state and post-W7
   follow-ups
5. `documents/POST_POC_BACKLOG.md` when the task touches a deferred item
6. `documents/REFACTOR_EXECUTION_PLAN.md` when the task touches historical
   refactor scope or document conflicts

## Core Shape

- Entry point: `main.py`
- Canonical backend: `appcore/`, `workflows/`, `executor/`
- Reusable framework-agnostic packages: `packages/` (contracts, planner,
  engine; detection scaffolding lives under `analysis_contracts/detection/`)
- Canonical frontend: `ui/`
- Tests: `tests/`
- Legacy top-level dirs `routers/`, `scanner/`, `core/`, `database/`, `crud/`,
  `models/`, and `schemas/` are removed from the canonical repo surface

## Non-Negotiables

- Preserve `(publisher, name, version)` uniqueness
- All DB writes go through `appcore/storage/crud.py`
- Validate with Pydantic before insert
- Use SQLAlchemy 2.0 and Pydantic v2 only
- Add Alembic migration for schema changes
- Keep sandbox execution isolated in Docker

## Start By Task

- Platform/config:
  - `main.py`
  - `appcore/api/`
  - `appcore/db/`
  - `tests/platform/`
- Extension catalog:
  - `workflows/extension_catalog/`
  - `appcore/contracts/`
  - `appcore/storage/`
  - `tests/workflows/extension_catalog/`
- Activation reports:
  - `workflows/activation_reports/router.py`
  - `tests/workflows/activation_reports/`
- Marketplace/analysis:
  - `workflows/marketplace/` (`analysis_service.py`, `job_service.py`,
    `trigger_service.py`)
  - `tests/workflows/marketplace/`
  - `tests/smoke/`
- Contracts / planner (shared packages):
  - `packages/analysis_contracts/`
  - `packages/analysis_planner/`
  - `packages/analysis_engine/`
- Executor:
  - `executor/control.py`
  - `executor/host.py`
  - `executor/container/`
  - `executor/flows/playwright/`
  - `executor/flows/playwright/runtime_capture/`
  - `tests/executor/`
- UI:
  - `ui/src/app/`
  - `ui/src/features/`
  - `ui/src/components/`
  - `ui/src/lib/`
- Security (W5-W7 security lane closed; PoC acceptance green):
  - `documents/adrs/0002-threat-model.md`
  - `documents/adrs/0003-detection-taxonomy.md`
  - `documents/adrs/0004-malicious-fixture-policy.md`
  - `documents/adrs/0005-packages-charter.md`
  - `packages/analysis_contracts/detection/`
  - `packages/analysis_engine/rules/` (A1/A2/A3/A4/A6)
  - `extensions/malicious/`
  - `tests/security/`

## API Shape

- Root/catalog routes stay on root paths
- Activation reports live under `/api/activations`
- Marketplace and analysis live under `/api/marketplace`

## Context Budget

- Do not scan the whole repo by default
- Open matching tests early
- Ignore `extensions/`, `output/`, `node_modules/`, and `__pycache__/`
  unless needed
- If docs and code disagree, trust code and tests

## Helpful Commands

- `make dev`
- `make test-local`
- `make check-all`
- `make test-security`
- `make migrate`
- `make exec-up`
- `make exec-run`
- `make ui-up`

## Load Only If Needed

- `documents/ARCHITECTURE.md`
  - system shape and request flows
- `documents/PROJECT_STRUCTURE.md`
  - placement rules
- `documents/TESTING.md`
  - test layout and fixtures
- `documents/EXECUTOR_PLAYWRIGHT.md`
  - executor/runtime details
- `documents/DETECTION_SEMANTICS.md`
  - activation report JSON semantics (quality/verification)
- `documents/VSCODE_API_COVERAGE_AUDIT.md`
  - trigger and coverage semantics
- `documents/adrs/0002-threat-model.md`
  - adversary classes (A1-A7), trust boundaries; read before any detection work
- `documents/adrs/0003-detection-taxonomy.md`
  - `DetectionReport` contract, severity/confidence, rule lifecycle
- `documents/adrs/0004-malicious-fixture-policy.md`
  - fixture tiering, CI guardrails, operator responsibilities
- `documents/REFACTOR_OPTIMIZATION.md`
  - 7-week window (§10), GPT-5.4 implementation spec, §9.N agent-audit log
- `documents/POST_POC_BACKLOG.md`
  - deferred items and the "pull first" next-iteration list
