# ExTrace

`Last Updated: 2026-05-26 (W20-0 doc-reconcile in-flight via this commit — open week20 branch (per user direction; W11-W19 paterni preserved) + new W20 active-work tracker documents/active-work/W20-coverage-promotion-easy-wins.md + §18 W20 plan header doc-open in REFACTOR_OPTIMIZATION.md split from the combined §18-§20 header (W19-0 paterni §17 split from §17-§20) + W20 Pull-Forward Acceptance Bar promoted in POST_POC_BACKLOG.md (from W20-W22 Roadmap Acceptance Bar now W21-W22 Roadmap Acceptance Bar planning) + 9-doc canonical preamble refresh + README phase-pointer arch gate transition W19→W20 (test_readme_phase_pointer.py tracks_active_w20_status + new test_readme_phase_pointer_mentions_w19_closeout_merge pinning PR #28 / week19 -> main / c879603 mirroring W18-0 / W19-0 transition paterni); baseline live-run captured via W20-0 self-stamp (anchor activation_report_ms-python.python-2026.5.2026052501-e89a82ca9ba8.json sha256 4dd788268f7793143351721875d6ccb340bd1e01b2b0205c53a5561ed0256ffe; W19 close-out Hat-1 + Hat-2 live-verified — unaccounted_dropout 0 + harness_verification_unconfirmed_present reason DROPPED). W20 driving signal (same as W19): Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities = [scm, settings, chat, comments, testing, workspace_trust]; W20 easy-wins tier closes scm + settings (heuristic-covered at capabilities.py:36,38; _OFFICIAL_CAPABILITY_SUPPORT missing at :88,90 — single-character flips at W20-1 + W20-2); W21 mid tier; W22 hard tier + sandbox evasion ADR. §18 W20 plan source (active) + §19-§20 W21-W22 planning roadmap (split at W20-0 from W19-0 era §18-§20 combined header). W20-0..W20-5 sub-iter slate: W20-0 doc-reconcile (this commit) + W20-1 [GOAL taxonomy-scm-official-promotion] + W20-2 [GOAL taxonomy-settings-official-promotion] + W20-3 [GOAL coverage-matrix-contract-tests] + W20-4 [DESIGN taxonomy-comments-testing-readiness] + W20-5 close-out hygiene + PR week20 -> main PENDING USER APPROVAL. W19 fully closed synthetically — Hat-1 closed + live-verified via W19-2-followup-2 d5de9ca; Hat-2 HARD GATE W19-3 closed via primary d2e83e7 + self-stamp 39121e4 + W19-3-followup-2 8-doc preamble refresh 9b56e94; W19-4 closed via 7d44b0e + W19-X live-verification close-out via 8b7b7f6 (W19-X primary) + a3e634f (W19-X self-stamp) — closes Bug A planner routing / Bug B marker channel destination / Bug C HMAC secret reactivation race; +15 new behavioral tests; live anchor 8247e05ec9ef.json: 2/2 onDebug* stamped; W19-5 closed via e537ebd + 4fd6ed6; W19-6 close-out hygiene via f17b4b1 + cd82153; W19-6-followup-2 pre-merge hygiene (this commit) closes 6 test gaps (+20 parametrized tests) + corrects stale W19 preamble drift across the 9-doc canonical set + freezes W19 tracker per W17/W18 paterni; final W19 test bar 1995/9/8 (tests/architecture/ 204 / make test-security 220 / full suite 1995 passed) on the week19 branch (per user direction 2026-05-21; W11-W18 paterni preserved); W19-0..W19-6 + W19-X closed on the week19 branch; merged to main via PR #28 2026-05-26 via c879603; live smoke pending; stable IDs W19-1..W19-5 closed at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar, assigned at first pull per W11-W18 precedent. Driving signal: Codex live-run validation 2026-05-21 of ms-python.python @ 992ad028f3df reports automation_health.status=degraded + run_quality=low while W19-2 live re-anchor satisfies unaccounted_dropout == 0 and static W18 final bar (1907/201/220) remains green; post-W19-3 live run 2026-05-25 23:27 (86e0f3646ce9) confirms field landed at "none" on 21/21 event_attempts with no behavior regression. W19 Hat-1 closed + live-verified (executor muhasebe bug → unaccounted_dropout); Hat-2 W19-3 schema landing + W19-4 onDebug* producer (confirmation_source="harness_nonce" stamp at health/reconciliation.py:347-348) + consumer wire (failure_reason_code gated on confirmation_source at reconciliation.py:85-90) + 7 new tests at test_playwright_health_reconciliation.py:813-1090 closed; W19-5 closed via primary e537ebd + self-stamp 4fd6ed6 (onTerminal+onLM log_record stamp at reconciliation.py:347-365 sibling elif to W19-4 onDebug arm); Hat-3 (coverage matrix promotion → 6 capabilities missing) deferred to W20-W22 per multi-iter roadmap. §17 W19 plan source + §18-§20 W20-W22 multi-iter roadmap (split at W19-0 from the original §17-§20 combined header). W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; final W18 bar tests/architecture/ 201 passed; make test-security 220 passed; full suite 1907 passed, 9 skipped, 8 deselected. W18 sub-iter audit trail (frozen, all closed): W18-0 doc-reconcile (89d0c9b); W18-1 ADR 0012 Option A1 (acf6cc9 + 73d8a5c); W18-2 heartbeat refactor implementation (a9bffb1 + 78ed7cc + b5b64b6 + 306d744 with pre-commit install); W18-3 lifecycle harness extension tests (92b310d + 32d9905); W18-4 close-out hygiene (3f4f95a); W18-4-followup (e1043e5). W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f; W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 closed via PR #20 week13 -> main MERGED 2026-05-13 via 772deb3. W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md; W19 frozen tracker: documents/active-work/W19-live-run-root-cause.md (frozen at W19-6-followup-2 per W17/W18 paterni); multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md. Plan REFACTOR_OPTIMIZATION.md §17 (W19) + §18-§20 (W20-W22 multi-iter roadmap). W17-0..W17-7 sub-iter slate complete (frozen); W16-0..W16-7 sub-iter slate complete (frozen); W18-0..W18-4 sub-iter slate fully delivered (frozen))`

ExTrace is a VS Code extension analysis platform built around three runtime
surfaces:

- A FastAPI API for catalog ingestion, activation report access, marketplace
  download, and sandbox analysis.
- A Dockerized executor that runs full VS Code GUI sessions under Xvfb and
  drives them with Playwright.
- A Vite + React + Tailwind analyst console that consumes the API and
  visualizes activation reports and live simulation jobs.

## Operating Model

ExTrace is intentionally designed as a single-user sandbox appliance, not a
multi-tenant web platform.

- Backend, UI, PostgreSQL, and executor are expected to run on the same machine
  or inside the same Docker host.
- The primary deployment shape is a local or lab sandbox where one analyst
  inspects one extension at a time.
- Background analysis is intentionally limited to one active job at a time.
- Activation reports remain file-backed operator artifacts under `output/`,
  while async analysis job metadata is persisted in PostgreSQL.
- If the API process restarts during an active analysis, that job is marked
  failed and should be rerun.
- ADR 0007 local-network-binding is Accepted **and implemented (W8-7,
  `2026-04-29`)** — `appcore/api/config.py` defaults bind `127.0.0.1`,
  CORS allow-list replaces the wildcard, every `docker-compose.yml`
  `ports:` entry carries an explicit `127.0.0.1:` prefix, and host-side
  CDP exposure is gated behind the Compose `debug` profile. To expose
  services on the LAN, follow `documents/runbooks/lan-exposure.md` and set
  `EXTRACE_ALLOW_LAN=1` (host-mode `make dev-lan`) or edit the compose
  file directly.

## Current Phase

- W4 stabilization, W5 detection foundations, W6 automation hardening, and
  W7 PoC acceptance are all closed (last closure `2026-04-23`).
- Post-W7 hardening (`2026-04-24`) landed reliability + modularization
  follow-ups (fatal UI-crash fail-fast, scan-between VS Code restart,
  `attribution/` subpackage split, `sim-target` Makefile lane).
- Post-W7 simulation UX + reliability (`2026-04-25`) landed weighted
  simulation progress, full-stack analysis cancel flow, the VNC harness
  ready-marker fix, and the `t1-demo-runnable-canary` fixture + rule +
  `make demo-canary` lanes.
- PR345 target activation lifecycle is complete as of `2026-04-27`; PRs 1-5
  plus ADR 0006 target output-channel capture landed on
  `feat/pr345-completion`.
- W8-0 deterministic harness readiness gate landed on `2026-04-27`, unblocking
  W8-1 and W8-3.
- **W8 closed for active work `2026-04-29`** (W8-1..W8-7 + W8-9 landed,
  W8-8 deferred); **W9 closed `2026-05-04`** (PR #9); **W10 closed
  `2026-05-04`** (PR #11); **W11 closed `2026-05-05`** and merged via
  PR #14; **W12 closed `2026-05-10`** and merged via PR #18 (`33a0852`).
  **W13 — Test Expansion + Observability closed `2026-05-13`** and
  merged via PR #20 `week13 -> main` (`772deb3`). Frozen tracker:
  [`active-work/W13-test-expansion-observability.md`](documents/active-work/W13-test-expansion-observability.md).
  **W14 — Codex M-class Acceptance + Observability closed `2026-05-14`**
  and merged via PR #21 `week14 -> main` (`4e03c8d`). Frozen tracker:
  [`active-work/W14-codex-acceptance-observability.md`](documents/active-work/W14-codex-acceptance-observability.md).
  **W15 — Codex U-class Close-Out + UI Bounds + Posture closed
  `2026-05-17` and merged via PR #22 `week15 -> main` (`6161472`) on `2026-05-18`**
  — W15-1..W15-7 sub-iter slate + W15-1 post-slate typing hotfix +
  close-out hygiene pass (doc preamble truth-state refresh across 7
  canonical docs + ADR 0011 catalog endpoint posture gate + compose
  image SHA pin + GH action trivy version pin + close-out lint
  hygiene). Frozen tracker:
  [`active-work/W15-codex-uclass-bounds-posture.md`](documents/active-work/W15-codex-uclass-bounds-posture.md).
  **W16 — Carry-Over Closeout + Audit Findings + Production Regression
  closed `2026-05-18`** and merged via PR #23 `week16 -> main`
  (`1b6d43f`). Frozen tracker:
  [`active-work/W16-regression-and-audit-closeout.md`](documents/active-work/W16-regression-and-audit-closeout.md).
  W16-0..W16-7 sub-iter slate complete: W16-1 scenario-accountant
  emit-site fix (`01f910a`); W16-2 analysis-job worker-entry CRUD
  ownership (`9d6d110`); W16-3 report-finalize null-leakage half
  (`fa430f2`; attribution-count-parity split to W17); W16-4
  health-reconciliation responsibility split (`304b99f`); W16-5
  simulation-progress-cancel scope reduction (1 rejected, 2 deferred
  to W17; `e21a05c`); W16-6 hygiene splits + Alembic fresh-DB fixture
  (`d40bb01`); W16-7 close-out hygiene (`8bf3c6b`) + post-PR
  `unaccounted_dropout` surface pin (`78f080e`). Final W16 bar:
  `tests/architecture/` **199 passed**; `make test-security`
  **220 passed**; full suite **1893 passed**.
  **Previous phase: W17 — Carry-Over Closeout + Lifecycle Harness
  Yatırımı + Hygiene Sweep — closed `2026-05-18`** on the `week17`
  branch (per user direction; W11-W16 paterni preserved);
  **W17 closed via PR #25 `week17 -> main` MERGED `2026-05-18`
  via `bff565d`**. Frozen tracker:
  [`active-work/W17-carryover-and-lifecycle-harness.md`](documents/active-work/W17-carryover-and-lifecycle-harness.md).
  W17-0..W17-7 sub-iter slate complete: W17-0 doc-reconcile
  (`4508c2e`); W17-1 attribution-count-parity (`8c26d02`); W17-2
  lifecycle harness scaffold (`ff98235`); W17-3 + W17-4
  scope-reduced doc-only (`c4c0646` — DESIGN-NEEDED for
  thread-relocation refactor shape, deferred to W18 — **closes via
  W18-1 ADR + W18-2 implementation**); W17-5 hygiene
  single-item (`394d40d` `[CLEANUP postgres-version-fact-drift]`;
  other 4 cleanup candidates deferred to W18+); W17-6 close-out
  hygiene (`21f7c68`); W17-7 post-slate hotfix batch
  (`bf983eb` + `fc88678` + `326dac8` + `51dba29`); W17-7-followup
  post-PR doc-truth alignment (`dab4679`). Final W17 bar:
  `tests/architecture/` **200 passed**; `make test-security`
  **220 passed**; full suite **1899 passed, 9 skipped,
  4 deselected**.
  **Previous phase: W18 — Heartbeat Refactor — closed via PR #26
  `week18 -> main` MERGED `2026-05-21` via `9874e79` (per user
  direction; W11-W17 paterni preserved). §16 W18 plan source**.
  W18-0..W18-4 sub-iter slate + W18-4-followup fully delivered:
  W18-0 doc-reconcile (`89d0c9b`); W18-1 ADR
  `documents/adrs/0012-heartbeat-thread-relocation.md` Option A1
  Accepted (`acf6cc9` + `73d8a5c` followup) — dedicated
  sandbox-reset coordinator for the step-1 setup reset; cancel-path
  teardown reset stays on the heartbeat thread; W18-2 heartbeat
  refactor implementation (`a9bffb1` + `78ed7cc` + `b5b64b6` +
  `306d744` with `pre-commit install`) — step-1 reset off the
  worker thread via `_run_reset_off_thread` coordinator
  (function-extension shape; W17-2 harness smoke byte-identical);
  W18-3 lifecycle harness extension tests — parallel reset /
  idempotency / reset-during-finalize (`92b310d` + `32d9905`);
  W18-4 close-out hygiene (`3f4f95a`); W18-4-followup (`e1043e5`).
  Final W18 bar: `tests/architecture/` **201 passed**;
  `make test-security` **220 passed**; full suite **1907 passed,
  9 skipped, 8 deselected**. Frozen tracker:
  [`active-work/W18-heartbeat-refactor.md`](documents/active-work/W18-heartbeat-refactor.md).

  **Previous phase: W19 — Live-Run Kök Neden: Dropout + Harness
  Verification — closed synthetically `2026-05-26` on the `week19`
  branch (per user direction 2026-05-21; W11-W18 paterni preserved);
  PR #28 `week19 -> main` MERGED `2026-05-26` via `c879603`. §17 W19
  plan source**. **W19-0..W19-6 + W19-X all closed**:
  W19-0 doc-reconcile (`72712bd` + `086d7a5`); W19-1
  `[BUG scenario-unaccounted-dropout-regression-fixture]`
  (`6a21cf3` + `fd02ca4`); W19-2
  `[BUG scenario-unaccounted-dropout-debug-refactor]` emit-site fix
  (`89b64da` + `d9c6262`) + W19-2-followup-2 live re-anchor
  (`d5de9ca`) satisfying `unaccounted_dropout == 0`; W19-3
  `[GOAL harness-verification-contract-event-level]` schema landing
  (`d2e83e7` + `39121e4` + `9b56e94`); W19-4
  `[FOLLOWUP harness-verification-debug-events]` `onDebug*` nonce
  producer/consumer wire (`7d44b0e`); W19-X `onDebug*` live close-out
  (`8b7b7f6` + `a3e634f`) closing Bug A/B/C; W19-5
  `[FOLLOWUP harness-verification-terminal-and-lm-tool]`
  onTerminal + onLM log_record stamp (`e537ebd` + `4fd6ed6`); W19-6
  close-out hygiene (`f17b4b1` + `cd82153`) + W19-6-followup-2
  pre-merge hygiene (`800c69f`). Driving signal: Codex live-run validation
  2026-05-21 of `ms-python.python` @ `992ad028f3df` reported
  `automation_health.status=degraded` + `run_quality=low` while
  W19-2 live re-anchor satisfies `unaccounted_dropout == 0`.
  Hat-1 + Hat-2 fully closed; Hat-3 (coverage matrix promotion)
  deferred to W20-W22. W19 acceptance (live-run-driven):
  `unaccounted_dropout == 0` (must-pass) ✓;
  `harness_verification_unconfirmed_present` reason drops
  (must-pass) ✓ synthetic / live-pending-next-run;
  `run_quality: low → medium` (expected); `verification_gap_present`
  drops (stretch); `automation_health.status: degraded` OK (W20
  closes `official_unresolved_present`). Frozen tracker:
  [`active-work/W19-live-run-root-cause.md`](documents/active-work/W19-live-run-root-cause.md);
  W20-W22 follow-on iters per multi-iter roadmap at
  [`active-work/W18-W22-roadmap.md`](documents/active-work/W18-W22-roadmap.md).
  Final W19 bar: `tests/architecture/` **204 passed**;
  `make test-security` **220 passed**; full suite **1995 passed,
  9 skipped, 8 deselected**.

  **Current phase: W20 — Coverage Promotion Round 1: Easy Wins —
  W20-0 in-flight `2026-05-26` on the `week20` branch (per user
  direction; W11-W19 paterni preserved). §18 W20 plan source**.
  Driving signal (same as W19): Codex live-run validation
  `2026-05-21` of `ms-python.python` @ `992ad028f3df` reports
  `coverage_summary.missing_capabilities = [scm, settings, chat,
  comments, testing, workspace_trust]` (Hat-3 coverage matrix
  promotion). W19 closed Hat-1 + Hat-2; W20 opens Hat-3 easy
  tier. Sub-iter slate W20-0..W20-5: W20-0 doc-reconcile (this
  commit) opens `week20` branch + new W20 active-work tracker +
  §18 W20 plan header doc-open (split from combined §18-§20) +
  W20 Pull-Forward Acceptance Bar promotion in
  POST_POC_BACKLOG.md + 9-doc canonical preamble refresh +
  README phase-pointer arch gate transition W19→W20 + new W19
  close-out fact gate
  `test_readme_phase_pointer_mentions_w19_closeout_merge`
  pinning PR #28 / `week19 -> main` / `c879603`; W20-1
  `[GOAL taxonomy-scm-official-promotion]` flip
  `_OFFICIAL_CAPABILITY_SUPPORT["scm"]: "missing" → "covered"`;
  W20-2 `[GOAL taxonomy-settings-official-promotion]` mirror;
  W20-3 `[GOAL coverage-matrix-contract-tests]` invariant set;
  W20-4 `[DESIGN taxonomy-comments-testing-readiness]` (doc-only,
  W21-1 + W21-2 unblocker template); W20-5 close-out hygiene +
  final live-run + PR `week20 -> main` PENDING USER APPROVAL.
  W20 acceptance: live JSON `coverage_summary.missing_capabilities`
  drops `scm` + `settings` (6 → 4) — must-pass; static suite
  green. Active tracker:
  [`active-work/W20-coverage-promotion-easy-wins.md`](documents/active-work/W20-coverage-promotion-easy-wins.md);
  multi-iter roadmap source-of-truth:
  [`active-work/W18-W22-roadmap.md`](documents/active-work/W18-W22-roadmap.md).
- **Canonical source of truth for phase state:**
  [`documents/REFACTOR_STATUS.md`](documents/REFACTOR_STATUS.md).
  Deferred items: [`documents/POST_POC_BACKLOG.md`](documents/POST_POC_BACKLOG.md).
  W8-W13 plan: [`documents/REFACTOR_OPTIMIZATION.md` §11](documents/REFACTOR_OPTIMIZATION.md).
  W14 plan: [`documents/REFACTOR_OPTIMIZATION.md` §12](documents/REFACTOR_OPTIMIZATION.md).
  W15 plan: [`documents/REFACTOR_OPTIMIZATION.md` §13](documents/REFACTOR_OPTIMIZATION.md).
  W16 plan: [`documents/REFACTOR_OPTIMIZATION.md` §14](documents/REFACTOR_OPTIMIZATION.md).
  W17 plan: [`documents/REFACTOR_OPTIMIZATION.md` §15](documents/REFACTOR_OPTIMIZATION.md).
  W18 plan: [`documents/REFACTOR_OPTIMIZATION.md` §16](documents/REFACTOR_OPTIMIZATION.md).
  W19 plan: [`documents/REFACTOR_OPTIMIZATION.md` §17](documents/REFACTOR_OPTIMIZATION.md) (previous).
  W20 plan: [`documents/REFACTOR_OPTIMIZATION.md` §18](documents/REFACTOR_OPTIMIZATION.md) (active).
  W21-W22 plan: [`documents/REFACTOR_OPTIMIZATION.md` §19-§20](documents/REFACTOR_OPTIMIZATION.md) (planning).

## Current Architecture

The refactor introduced a canonical split between shared platform code and
workflow code:

- `appcore/`
  - Shared platform modules.
  - `api/`: settings and FastAPI dependencies.
  - `db/`: SQLAlchemy engine and session factory.
  - `storage/`: ORM models and CRUD helpers.
  - `contracts/`: shared Pydantic v2 schemas.
- `packages/`
  - Framework-agnostic contracts and analysis logic.
  - `analysis_contracts/`: backend-owned analysis contracts, activation
    reports, trigger payloads, and detection DTOs.
  - `analysis_planner/`: trigger planning logic.
  - `analysis_engine/`: reserved extraction surface for shared analysis logic.
- `workflows/`
  - Business workflows grouped by capability.
  - `extension_catalog/`: extension ingestion, parsing, and catalog endpoints.
  - `activation_reports/`: reads JSON activation reports from `output/`.
  - `marketplace/`: Marketplace search/download and sandbox analysis.
- `executor/`
  - Sandbox runtime.
  - `control.py`: workflow-visible sandbox boundary.
  - `container/`: Docker image, entrypoint (`start.sh`), and the shared
    `launch_vscode.sh` script used at boot and by scan-between resets.
  - `flows/playwright/`: Playwright automation helpers, package-mode
    `entrypoint/`, `monitor/` facade, attribution/scenario/runtime-capture
    packages, and focused helper packages for health, stimulus, workspace,
    VS Code UI, and signals.
- `ui/`
  - Primary analyst-facing React SPA built with Vite and Tailwind.
  - `src/app/`: shell and route composition.
  - `src/features/`: `evidence`, `marketplace`, `reports`, `rules`,
    `settings`, `simulation`, `system`.
  - `src/lib/`: API client, adapters, generated contract types, and shared
    frontend helpers.

The repository now uses canonical imports only:

- Shared platform modules live under `appcore/`
- Framework-agnostic analysis logic lives under `packages/`
- Workflow code lives under `workflows/`
- Workflow-visible executor control lives under `executor/control.py`

## Request Flows

### Static Catalog Ingestion

`POST /createExtension`

1. `workflows.extension_catalog.router`
2. `workflows.extension_catalog.service`
3. `workflows.extension_catalog.manifest_reader` +
   `workflows.extension_catalog.manifest_parser`
4. `appcore.contracts.schemas`
5. `appcore.storage.crud`
6. PostgreSQL

### Marketplace Download

`POST /api/marketplace/download`

1. `workflows.marketplace.client` downloads and extracts a `.vsix`
2. `workflows.extension_catalog.service.create_extension_from_directory`
3. `appcore.storage.crud` persists validated manifest data

### Sandbox Analysis

`POST /api/marketplace/analyze` or `POST /api/marketplace/analyze/start`

1. `workflows.marketplace.router`
2. `workflows.marketplace.analysis_service`
3. `workflows.marketplace.job_service`
4. `executor.control` boundary
5. `executor.host` Docker exec wrapper
6. `python -m executor.flows.playwright.entrypoint`
7. Reports written under `output/`
8. Async job metadata persisted in PostgreSQL `analysis_jobs`

Notes:

- `POST /api/marketplace/analyze` is the direct request/response path.
- `POST /api/marketplace/analyze/start` is the background path used by the
  React UI.
- Only one background analysis should run at a time in the intended sandbox
  deployment.
- Startup fails fast if the `analysis_jobs` storage path is unavailable or the
  required migration has not been applied.
- Trigger planning may choose layered execution or a scenario-zero
  `skip_automation` run for non-executable fixtures.

## API Surface

### Extension Catalog

- `GET /`
- `GET /health`
- `GET /searchExtension`
- `GET /getExtensionsBaseInfo`
- `GET /getExtensionsAllInfo`
- `POST /createExtension`
- `DELETE /deleteExtension`
- `GET /getExtensionScripts`
- `GET /getExtensionActivationEvents`
- `GET /getExtensionCapabilities`
- `GET /getExtensionContributesAll`
- `GET /getExtensionContributesCommands`

### Activation Reports

- `GET /api/activations`
- `GET /api/activations/latest`
- `GET /api/activations/{name}`

### Marketplace + Analysis

- `GET /api/marketplace/search`
- `POST /api/marketplace/download`
- `POST /api/marketplace/analyze`
- `POST /api/marketplace/analyze/start`
- `GET /api/marketplace/analyze/{job_id}`
- `POST /api/marketplace/analyze/{job_id}/cancel`

### Operator Settings

- `GET /api/settings/security/thresholds`
- `PUT /api/settings/security/thresholds`

## Local Development

### Prerequisites

- Python 3.11+
- Docker / Docker Compose
- PostgreSQL 16 compatible runtime
- Node 20+ for local UI development

### Common Commands

```bash
make install-dev
make up
make migrate
make dev
make test-local
make check-all
make test-security
make ui-types-check
make ui-boundaries
make exec-up
make exec-run
make ui-up
make sim-target TARGET=publisher.name      # target-extension smoke
make sim-all                                # UI-stimulus stress (no target ext.)
make demo-canary                            # end-to-end demo runnable canary
make demo-canary-offline                    # offline fixture validation
cd ui && npm run dev
cd ui && npm run test
.venv/bin/pytest
.venv/bin/pytest -m "not smoke and not requires_db"
.venv/bin/pytest -m "requires_db"
.venv/bin/pytest -m smoke
```

### Service Endpoints

ADR 0007 — every endpoint below binds loopback only by default. Replace
`127.0.0.1` with the operator-host LAN IP only after the
`documents/runbooks/lan-exposure.md` checklist is applied.

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Web UI: `http://127.0.0.1:3000`
- noVNC executor view: `http://127.0.0.1:6080/vnc.html`
- CDP (debug profile only): `http://127.0.0.1:9222` — start with
  `make up-debug` or `docker compose --profile debug up`. Absent from the
  default `make up` service set.

## Project Layout

```text
appcore/                    Shared platform modules
packages/                   Framework-agnostic contracts and analysis logic
workflows/                  Canonical business workflows
executor/
  control.py               Workflow-visible sandbox boundary
  container/               Sandbox image and startup scripts
  flows/playwright/        VS Code GUI automation packages
ui/                         React + Vite analyst console
tests/
  architecture/            Import-graph and boundary checks
  platform/                Shared platform tests
  workflows/               Workflow tests
  executor/                Playwright runtime tests
    scanner/               Docker exec wrapper tests
  security/                Malicious-fixture scaffold checks
  smoke/                   End-to-end marketplace analysis tests
  ui tests live under ui/src/**/*.test.ts(x)
documents/                  Architecture, roadmap, and testing notes
docs/                       Targeted risk notes
```

## Documentation Index

- `documents/AGENT_CONTEXT.md`: thin task-routing map for coding agents after
  `AGENTS.md`
- `documents/agent-lanes/`: lazy-load task-lane docs for platform/storage,
  marketplace/analysis, executor/runtime, security/detection, UI, and docs
  maintenance
- `documents/README.md`: context-light guide for choosing which project docs to
  load first
- `documents/REFACTOR_STATUS.md`: slim current-state closure board and phase
  handoff history
- `documents/POST_POC_BACKLOG.md`: deferred work items and the pull-next list
- `documents/ARCHITECTURE.md`: canonical architecture and boundaries
- `documents/DETECTION_SEMANTICS.md`: meaning and calculation rules for
  exported `ActivationReport` fields
- `documents/PROJECT_STRUCTURE.md`: placement rules after the refactor
- `documents/TESTING.md`: current test layout and commands
- `documents/EXECUTOR_PLAYWRIGHT.md`: sandbox and Playwright details
- `documents/DEVELOPMENT_PRIORITIES.md`: near-term priorities for the sandbox
  product
- `documents/PIPELINE_ROADMAP.md`: pipeline direction without multi-tenant
  assumptions
- `documents/VSCODE_API_COVERAGE_AUDIT.md`: capability support and
  trigger/verification gaps
- `documents/automation_todo.md`: legacy/off-path backlog notes; current
  pull-next truth is `documents/POST_POC_BACKLOG.md` plus the active tracker
- `docs/risks.md`: current risk register
