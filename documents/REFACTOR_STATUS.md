# Refactor Status

`Last Updated: 2026-04-29`

Active status board for current closure state. **Slim canonical** — full
phase closure history (W4 → W5 → W6 → W7 + post-W7 hardening + W8-0..W8-3
detail blocks) frozen under
[`archive/status/REFACTOR_STATUS_full_2026-04-29.md`](archive/status/REFACTOR_STATUS_full_2026-04-29.md).

## Current State

- **W0-W7 PoC stabilization/security window closed `2026-04-23`** —
  `REFACTOR_OPTIMIZATION.md` §10.7 PoC acceptance bar 11/11 green.
- **PR345 target activation lifecycle complete `2026-04-27`** — closure
  evidence in archive under "PR345 Complete".
- **W8-0 deterministic harness readiness gate landed `2026-04-27`** —
  capture pipeline + reason-code rollup live.
- **W8-1 VSIX zip-bomb + entry-count guard landed `2026-04-27`**.
- **W8-2 marketplace identity helper + reviewer-feedback gap closure
  landed `2026-04-27`** —
  `packages/marketplace_identity/safe_marketplace_slug` live with
  architecture regression test.
- **W8-3 URI trigger argv-form invocation landed `2026-04-28`** —
  `executor/flows/playwright/uri_validation.py` helper live; AST-based
  architecture detector pins shell-template pattern from re-appearing.
- **UI v3 redesign minimal-completion landed `2026-04-29`** — orphan v3
  components pruned, Inspector drawer + event-scoped `RuleDraftSection`
  on Reports, Run health + Coverage summary panels on Simulation,
  `design_handoff_extrace_console/` prototype retired.
- **W8-4 absolute binary paths landed `2026-04-29`** —
  `executor/binary_paths.py` constants + lazy `docker_path()` resolver;
  `host.py` 6 invocation sites switched to absolute paths; AST gate
  `tests/architecture/test_absolute_binary_paths.py` pins discipline.
- **W8-5 router regex consolidation landed `2026-04-29`** —
  `appcore/contracts/validators.py` re-imports W8-2's
  `MARKETPLACE_SLUG_TOKEN_RE`; activation-report router uses FastAPI
  `Path(..., pattern=...)` gate; AST drift gate prevents duplicate slug
  regex literals.

W8 is in progress. Active checklist:
[`active-work/W8-security.md`](active-work/W8-security.md). Remaining
items: W8-6 (content-sample redaction), W8-7 (ADR 0007 local network
binding), W8-8 (manifest log sanitization).

## Subsystem Posture

- Async marketplace job state durable in PostgreSQL via `analysis_jobs`.
- Activation reports artifact-first under `output/activation_report_*.json`.
- Workflow code reaches sandbox through `executor.control` only.
- W5 detection surfaces wired:
  `packages/analysis_contracts/detection/`,
  `packages/analysis_engine/rules/` (A1/A2/A4/A6 with target-only
  attribution), `extensions/malicious/` (T1 canaries with `LABEL.yaml`),
  `tests/security/`, plus `make test-security` and
  `make test-security-live`.
- Legacy directories (`routers/`, `scanner/`, `core/`, `database/`,
  `crud/`, `models/`, `schemas/`) and dormant placeholders (`apps/`,
  `legacy_ui/`) removed from canonical surface.
- Canonical runtime tree: `appcore/`, `packages/`, `workflows/`,
  `executor/`, `ui/`, `tests/`.

## Open Deferrals

Authoritative open list lives in
[`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md). Highlights:

- `[FOLLOWUP w8-0-capture-pipeline]` — W8-3 live smoke (2026-04-28)
  closed acceptance signal (a); typed harness-readiness reason codes
  (signal b) remain unconfirmed live.
- `tests/workflows/marketplace/test_router.py` 3 pre-existing
  `test_run_analysis_job_*` failures (missing `requires_db` marker;
  hygiene PR).
- `make test-security` lane composition — W8-1 + W8-3 tests live in
  subsystem-local lanes; either extend Makefile target or update
  `active-work/W8-security.md` exit criterion to count broader tally.
- Docker-based smoke (`make exec-up && make sim-target`) user-side.
- UI v3 follow-ups: see `[CLEANUP ui-v3-9/14]`, `[ADD ui-v3-10/11/12]`,
  `[BACKLOG ui-v3-13]` in `POST_POC_BACKLOG.md`.

## Read Order (When Updating This File)

1. `AGENTS.md`
2. `documents/AGENT_CONTEXT.md`
3. this file
4. `documents/agent-lanes/<matching-lane>.md`
5. subsystem doc only when the lane doc points to it

When a closure entry would expand this file past ~300 lines, drop a new
dated full snapshot under `archive/status/` and re-trim — see
`agent-lanes/docs-maintenance.md` invariants.

## Archive

Full phase closure history (W4 → W5 → W6 → W7 acceptance, post-W7
hardening, PR345 + W8-0/W8-1/W8-2/W8-3 verbose closures, change
diffs, verification matrices):
[`archive/status/REFACTOR_STATUS_full_2026-04-29.md`](archive/status/REFACTOR_STATUS_full_2026-04-29.md).
