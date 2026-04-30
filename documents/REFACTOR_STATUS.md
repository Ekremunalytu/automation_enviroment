# Refactor Status

`Last Updated: 2026-04-30`

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
- **W8-7 LAN binding defaults landed `2026-04-29`** —
  `appcore/api/config.py` defaults `HOST=127.0.0.1`,
  `CORS_ALLOW_ORIGINS=http://localhost:3000`,
  `CORS_ALLOW_CREDENTIALS=False`; `model_post_init` substitutes
  `0.0.0.0` + `*` only when `EXTRACE_ALLOW_LAN` is truthy AND the field
  still holds the loopback default. `docker-compose.yml` carries
  explicit `127.0.0.1:` prefixes on every default-profile `ports:`
  entry; CDP (port `9222`) ships behind a new `executor-cdp` socat
  sidecar gated by `profiles: ["debug"]`. `Makefile` adds `dev-lan`
  and `up-debug` targets. `documents/runbooks/lan-exposure.md` live; ADR 0007
  Implementation section plus ADR 0002 §4 trust-boundary row appended;
  `tests/architecture/test_default_bindings.py` (14 cases) wired into
  the `make test-security` lane.

W8-8 (manifest log sanitization) is **deferred — not abandoned**. Audit
on `2026-04-29` confirmed no production logger call in
`workflows/extension_catalog/` or `workflows/marketplace/` currently
forwards an attacker-controlled manifest field; the four W8-8 artifacts
(`sanitize_for_log` helper, parametrized sanitization test, AST gate,
ADR 0002 §7 addendum) reopen on **either** of two named triggers:

- **Trigger A** — a future feature PR introduces the first real call
  site that logs `displayName` / `description` / `repository.url` /
  `categories[]` / `homepage` / `bugs` / `qna` / `license` from a
  parsed manifest. The W8-8 artifacts ship in the same PR so the
  helper has a real caller and the AST gate locks in the shape.
- **Trigger B** — an external review or stakeholder gate explicitly
  asks for the defense-in-depth helper before any real call site
  exists. A standalone PR ships the four artifacts and the AST gate
  is sized against synthetic fixtures.

Track: `[FOLLOWUP w8-8-manifest-emit-when-needed]` in
`POST_POC_BACKLOG.md` carries the full pickup procedure (artifact
list, file paths, retirement marker). The W8-8 plan body in
`active-work/W8-security.md` carries a `(DEFERRED 2026-04-29)` marker
and a "Deferred — NOT abandoned" callout listing the same triggers;
the threat description below the marker is the canonical statement of
the vector and survives the eventual landing flip.

With W8-7 landed and W8-8 deferred under the named triggers above,
W8 is **closed for active work** pending the optional ADR 0008 draft
on container packaging that the active-work tracker keeps as a single
remaining checkbox before W9 entry.

- **W9-1 container packaging ADR + entrypoint argv pivot landed `2026-04-30`** (`76c0760`) —
  `feat/w9-executor-detection-boundary` umbrella branch opened. ADR 0008
  (`documents/adrs/0008-container-packaging.md`) shipped as Proposed.
  `appcore/api/config.py` and `executor/config.py` migrated `*_PATH`
  literals to `*_MODULE` dotted names (no deprecation alias). `executor/host.py`
  pivoted four call sites to `[PYTHON3_PATH, "-m", <module>]` argv form;
  `pkill -f` cleanup uses dotted module name as pattern (uniqueness invariant
  per ADR 0008 §6). Container `Dockerfile` provisions
  `/home/executor/__init__.py` + `/home/executor/flows/__init__.py` regular
  package markers and sets `ENV PYTHONPATH=/home`. `start.sh` honeypot
  bootstrap pivoted to `python3 -m executor.flows.playwright.workspace`.
  `Makefile` `exec-run`/`sim-*` lanes pivoted to argv form.

- **W9-2 signal_policy relocation landed `2026-04-30`** (`55ee3f7`) —
  pure-logic signal policy moved from `executor/flows/playwright/signal_policy.py`
  into `packages/analysis_engine/signals/policy.py`; executor flows import
  via `from packages.analysis_engine.signals.policy import …`. AST gate
  `test_executor_imports_signals_from_packages`
  (`tests/architecture/test_import_graph.py:173`) regression-guards the
  detection-boundary pull.

- **W9-3 dual-import sweep + sys.path eradication + AST gates landed `2026-04-30`** (`ae0a8a7`) —
  full package-mode pivot completed in one commit (59 files changed,
  604 insertions / 1045 deletions). 39 source files converted to
  package-relative imports; 17 dual-import fallbacks removed (one
  allow-listed: `executor/flows/playwright/monitor_support.py`); 6
  `sys.path.insert` calls eliminated across runtime tree
  (`entrypoint`, `reload_vscode`, `reset_state`, `report_builder`,
  `triggers`, `workspace`). Three AST gates lock the contract in
  `tests/architecture/test_import_graph.py`:
  `test_no_dual_import_fallback_in_executor` (line 123),
  `test_no_sys_path_manipulation_in_runtime` (line 151),
  `test_executor_imports_signals_from_packages` (line 173). The
  originally separate W9-4 `sys.path.insert` audit folded into this
  commit because the AST gate is the binding artifact. ADR 0008 §6
  Outcomes block + Implementation section updated; ADR status flips
  to **Accepted**. Verification: `make check-all` (959 passed / 6
  skipped); smoke 3-test green
  (`test_ms_python_analysis_smoke`, `test_ms_python_layered_analysis_smoke`,
  `test_missing_trigger_payload_never_looks_benign`).

- **CI pipeline retired `2026-04-30`** — `.github/workflows/ci.yml` and
  `.github/workflows/docs-check.yml` removed; `security.yml` (weekly
  Trivy + Bandit) kept. The `security-fixtures` job (iptables egress
  sandbox) was the persistent flake source; its protections are
  Makefile-enforced (`test-security-live` refuses under `CI=true`)
  and the security fixture lane itself runs locally via
  `make test-security` (pure pytest, no network). A new `pre-push`
  pre-commit stage runs `make check-all` before push as the local
  gate. ADR 0004 carries a 2026-04-30 addendum spelling out the
  policy change. Reintroduction trigger logged as
  `[FOLLOWUP ci-reintroduction]` in `POST_POC_BACKLOG.md`.

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
