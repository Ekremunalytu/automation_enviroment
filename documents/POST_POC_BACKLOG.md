# Post-PoC Backlog

`Last Updated: 2026-05-04` (audit-pass additions)

Open work items deferred from W0-W7 PoC scope. **Slim canonical** — full
verbose item descriptions, landed-evidence detail, and review triage
blocks are frozen under dated snapshots in `archive/backlog/` (latest:
[`archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md)).

PoC acceptance bar (`REFACTOR_OPTIMIZATION.md` §10.7) was met `2026-04-23`;
items below are value-add, not gates.

## Stable IDs Are A Contract

Test/code comments reference items here by stable ID
(e.g. `[FOLLOWUP simulation-progress-cancel]`). **Do not rename** existing
IDs; new items get fresh IDs. Where multiple sub-items share a parent ID
(`[FOLLOWUP simulation-progress-cancel] heartbeat refactor` vs
`[FOLLOWUP simulation-progress-cancel] is_job_cancelled session churn`),
the trailing phrase is part of the contract and must be preserved.

Inbound code references — keep these stable:

- `tests/platform/storage/test_analysis_jobs.py:183` →
  `[FOLLOWUP analysis-jobs-race]` (in-flight race gap)
- `tests/workflows/marketplace/test_router.py:2009` →
  `[FOLLOWUP simulation-progress-cancel]` parent
- `tests/workflows/marketplace/test_analysis_execution_helpers.py:238` →
  `[FOLLOWUP simulation-progress-cancel] cancel-after-finish race test`
  (LANDED 2026-04-27, evidence in archive + `REFACTOR_STATUS.md`)
- `packages/analysis_contracts/contracts.py:142` → filename mention
  (kararlı)

---

## External Review Integration Window (W8-W13)

Two external reviews landed `2026-04-24`:

- [`archive/reviews/claude_code_review.md`](archive/reviews/claude_code_review.md)
- [`archive/reviews/codex_project_review.md`](archive/reviews/codex_project_review.md)

Findings triaged into `REFACTOR_OPTIMIZATION.md §11` weekly split (W8
Güvenlik sıkılaştırma → W13 Test expansion + observability). Active W8
tracker: [`active-work/W8-security.md`](active-work/W8-security.md).

W8 entry gate (`§11.1`) **MET as of 2026-04-27**. PR345 closure
(`REFACTOR_STATUS.md` "PR345 Complete"). W8 (`§11.5`) is open; items
W8-1 (2026-04-27), W8-2 (2026-04-27), and W8-3 (2026-04-28) landed.

**Promoted into W8-W13** (no longer pull-next here): target activation
lifecycle (landed), `signal_policy.py` relocation → W9, `registry.py`
split → W10, `monitor_lifecycle.py` split → W11,
`executor/flows/playwright/` subpackaging → W12.

**Rejected from W8-W13** (stay here, see archive §11.12 for promotion
rationale): UI component split (7.3.1/7.3.2), axe-core, mypy strict
promotion, documentation consolidation, monorepo tooling migration,
async executor runtime refactor, OpenAPI frontend client generation.

---

## Open Items By Area

Items are listed with stable ID + short trigger. Detail (file refs,
acceptance criteria, surfaced-by review §) lives in archive — open it
when picking an item up.

### Workflow / Platform

- **`[FOLLOWUP runner-status-contract]`** First-class
  `ActivationReport.runner_exit_code` + `runner_status` enum. Natural
  landing: W11 `ReportAssembler`. Surfaced by 2026-04-25 supplementary
  review (Codex "Runner exit status semantics").
- **`[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread`**
  `_heartbeat_on_cancel()` calls `executor_control.reset_sandbox`
  synchronously from the daemon heartbeat; spin reset on a worker.
- **`[FOLLOWUP simulation-progress-cancel] dedupe-step-progress-schemas`**
  `AnalysisJobStepProgress` vs `AnalyzeJobStepProgress` — pick canonical
  or document the deliberate split.
- **`[FOLLOWUP simulation-progress-cancel] is-job-cancelled-session-churn`**
  `job_service.py:308` opens a fresh DB session every 5 s; fold into a
  longer-lived session if profiling shows pressure.
- **`[FOLLOWUP simulation-progress-cancel] heartbeat-refactor`**
  Lift `_run_monitoring_heartbeat` cancel/poll/JSON-read mix into
  `MonitoringHeartbeat` helper for unit-testability.
- **`analysis_service._open_job_session`** — move `SessionLocal` import
  back to module top (7.1.2; inlined to break startup cycle).
- Narrow the broad `except` in `run_analysis_job` (7.1.4).
- **`[FOLLOWUP analysis-thread-supervisor]`** Structural complement to
  7.1.4: wrap the daemon-thread `target` (`router.py:186` →
  `run_analysis_job`) in a `BaseException`-catching supervisor that always
  calls `job_service.fail_job(job_id, reason=str(exc))` before re-raising,
  so future un-enumerated exception types cannot leave the row in
  `running`. AGENTS.md exception for the broad catch documented at the
  supervisor site only. Surfaced by 2026-04-29 audit pass.
- **`[FOLLOWUP analysis-thread-error-detail-leakage]`** — *CLOSED
  2026-05-03 on `feat/w9-executor-detection-boundary`* (W8-7
  LAN-exposure trigger). `analysis_service.map_executor_error()`
  redacts paths/env from public HTTP detail, suffixes an 8-char
  `error_id`, retains raw text in `logger.warning`. Regression:
  `tests/workflows/marketplace/test_router.py::
  test_map_executor_error_redacts_internal_paths_and_env`. Detail in
  `archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md`.
- **`[FOLLOWUP sqlalchemy-error-subtype-logging]`**
  `appcore/storage/crud_ops/analysis_jobs.py` (and the wider `crud_ops/`
  surface) catches `SQLAlchemyError` broadly without distinguishing
  `IntegrityError` (constraint), `OperationalError` (connection), or
  `ProgrammingError` (schema). Distinguish for incident triage; rolling
  back/raising semantics stay the same.
- Tighten `search_marketplace` return type (7.1.5).
- Pull "domain service" pattern into remaining router surfaces (2.8).
- `make migrate` pre-check for destructive Alembic operations (7.4.6);
  Alembic reversibility audit (7.4.7).
- **`[FOLLOWUP job-service-typevar-audit]`** —
  `workflows/marketplace/job_service.py:48` declares `T = TypeVar("T")`;
  immediate re-check found it is used by `_run_in_session()` to preserve
  the return type of `Callable[[Session], T]`. Treat as low-priority:
  keep if mypy/reader clarity benefits from the generic, or remove only
  if the helper is simplified. Surfaced by 2026-05-04 audit pass.
- **`[FOLLOWUP scripts-seed-test-rewrite]`** — `scripts/seed_test.py`
  carries four AGENTS hard-rule violations in one file: `:55`
  `sys.path.insert`, `:119` `Extension(...)` ORM creation bypassing
  Pydantic (rule 3), `:154` `db.add` bypassing CRUD facade (rule 2),
  `:164` generic `except Exception` (rule 6 — explicit). Either
  delete (if obsolete) or rewrite through `appcore/storage/crud.py`
  with Pydantic + narrow exception types. Surfaced by 2026-05-04
  second-pass review.
- **`[FOLLOWUP triggers-private-helper-import]`** —
  `workflows/marketplace/triggers.py:14` imports
  `_glob_to_bait_filename` from `packages.analysis_planner.io`,
  violating ADR 0005 §3 (public API through package roots). Either
  promote a public re-export through
  `packages/analysis_planner/__init__.py` or rename/promote the helper
  inside `packages.analysis_planner`; do not duplicate planner logic in
  `workflows/`. Surfaced by 2026-05-04 second-pass review.
- **`[CLEANUP httpx-runtime-dependency-metadata]`** — `httpx` is
  imported in production at `workflows/marketplace/{client,router}.py`
  and installed by `docker/api/requirements.txt:9`, but absent from
  `pyproject.toml [project].dependencies` (`:15-24`); only
  `[project.optional-dependencies].dev:33` lists it. Move to base
  dependencies — no new dep, packaging metadata fix. Surfaced by
  2026-05-04 second-pass review.

### Executor / Capture Hygiene

- **T2 declawed samples + T3 handling** + `make test-security-live`
  hardening — ADR 0004 covers policy; operational plumbing waits on
  real T2 engagement.
- **`[FOLLOWUP w11-precursor-tests]`** — Two playwright god-modules
  are tested mostly through the `monitor` facade today rather than
  direct module-owned tests:
  `executor/flows/playwright/runtime_capture/extension_host.py`
  (679 LOC, strace parsing + PID discovery) and
  `executor/flows/playwright/health_reconciliation.py` (533 LOC,
  activation verification + cross-imports `health_summary`). Both are
  scheduled for refactor (`§11.8` W11 lifecycle split, `§11.9` W12
  subpackaging). Land minimal direct tests covering the public
  parse/reconcile surface as a safety net **before** the splits land,
  so the refactor is not over-dependent on facade/integration coverage.
  Surfaced by 2026-05-04 audit pass.
- **`[FOLLOWUP w12-attribution-naming-overlap]`** —
  `attribution_summary.background_activation_count` and
  `attribution_summary.competing_candidate_count` describe overlapping
  populations but the values diverge by orders of magnitude. Observed
  2026-05-04 manual UI scan with 25 unique extensions / 22 activations
  / 1 target: `background_activation_count: 0` while
  `competing_candidate_count: 54`. Reconcile category definitions (or
  rename one) so operators can reason about non-target activity from
  the report alone. Natural landing: W12 attribution facade cleanup
  (`§11.9`). Surfaced by 2026-05-04 manual UI scan.

### Detection / Contracts

- A5 + A7 adversary-class T1/T2 canary + rule (stretch).
- Allow-list (`benign_domains.txt`, `popular_extensions.txt`) versioned
  data artifact promotion.
- Domain service pattern genişletmesi (2.8 — W7'de ertelendi).
- **`[FOLLOWUP report-invariants-runtime-evidence-drift]`** —
  `packages/analysis_contracts/report_invariants.py:55`
  (`_attempt_has_runtime_evidence`) counts only `{attempted_only,
  verified, failed}`, but the runtime equivalent at
  `executor/flows/playwright/health_runtime_facts.py:31`
  (`attempt_has_runtime_evidence`) counts `{attempted_only,
  activation_seen, target_log_seen, verified, failed}` and includes
  an explicit comment justifying the broader set
  (`activation_seen`/`target_log_seen` are intermediate observation
  states emitted by `reconcile_event_attempts` when the target
  activated but full verification did not close). Contract invariant
  lags runtime; align both helpers and add a contract-level
  regression test pinning the broader set. Natural landing: W10
  contract hygiene. Surfaced by 2026-05-04 second-pass review.
- **`[FOLLOWUP planner-executor-action-enum]`** — Planner emits
  string actions (e.g. `extra:uri_trigger`,
  `scenario:<scenario_name>`) at
  `packages/analysis_planner/attempts.py`; executor dispatches over
  raw action strings at
  `executor/flows/playwright/stimulus_attempts.py:308`. Typos or
  unhandled action names become runtime behaviour bugs rather than
  contract validation failures. Add an enum or narrow Pydantic
  contract for executor action names so dispatch becomes total.
  Natural landing: W10 contract hygiene (alongside the existing
  `_TriggerPayloadDraft` elimination in `§11.7`). Keep dispatch
  explicit — no generic event framework. Surfaced by 2026-05-04
  second-pass review.
- **`[FOLLOWUP w8-6-output-signals-redaction]`** — Three
  extension-derived text surfaces escape `ContentSample`/redaction:
  (a) `executor/flows/playwright/output_signals.py:115` truncates but
  does not redact, and the contract field
  `OutputSignalEvent.text` (`packages/analysis_contracts/contracts.py
  :258`) is plain `str`; (b) `workflows/marketplace/
  analysis_execution.py:71-74` appends raw executor stderr/stdout
  500-byte tail to job progress; (c)
  `workflows/marketplace/analysis_service.py:155`
  (`map_executor_error`) preserves raw exception text in
  `logger.warning` for triage. Migrate to `ContentSample` (or pipe
  through `redact_secrets()` at construction) and append the
  affected fields to `_PENDING_MIGRATION` in
  `tests/platform/security/test_content_sample_typing.py`.
  Companion to
  `[FOLLOWUP w8-6-content-sample-structural-test]`; landing both
  together as W10 contract hygiene closes the W8-6 broader sweep.
  Surfaced by 2026-05-04 second-pass review.
- **`[FOLLOWUP coverage-summary-attempted-drift]`** —
  `coverage_summary.attempted_capabilities` (7 entries including
  `uri_walkthrough`), the parallel `summary.attempted_capabilities`
  alongside top-level `attempted_capabilities` (6 entries, no
  `uri_walkthrough`), and `event_attempts[]` (zero attempts of
  `uri_walkthrough` family) all describe the same run's attempted
  capabilities but disagree. Producer paths diverge — likely
  `analysis_planner.coverage` vs the reconcile path under
  `executor/flows/playwright/health_*`. Reduce to a single source so
  UI components reading either alias see the same number. Natural
  landing: W12 attribution cleanup (`§11.9`); pull earlier as a
  surgical fix if any UI surface reads both fields and renders
  diverging counts. Surfaced by 2026-05-04 manual UI scan.
- **`[FOLLOWUP target-log-lifecycle-instrumentation]`** —
  W10-6 pinned `RUNTIME_EVIDENCE_STATES = {attempted_only,
  activation_seen, target_log_seen, verified, failed}` as a shared
  frozenset across contract + executor helpers, but no reconciler
  currently transitions attempts into the intermediate
  `activation_seen`/`target_log_seen` states. On a 2026-05-04 UI scan
  all 9 unresolved attempts collapsed to `attempted_only` and
  `log_streams.target_extension_host` carried only 1 entry for a
  22-activation run; the lifecycle ledger has alphabet but no
  vocabulary. Wire `reconcile_event_attempts` (or its W11 successor
  `ScenarioAccountant`/`ReportAssembler`) to emit the intermediate
  states whenever target-owned log/output evidence exists short of
  full verification, and broaden target log capture so
  `target_extension_host` does not collapse to 1 entry per run. The
  contracts.py:166 lifecycle comment already references this
  workstream; this entry makes it trackable. Natural landing: W11
  monitor lifecycle split (`§11.8`) **as an acceptance sub-task** +
  W12 reconciler updates (`§11.9`). Surfaced by 2026-05-04 manual UI
  scan.
- **`[FOLLOWUP signal-summary-needs-review-categories]`** —
  `signal_summary.level` can land on `"needs_review"` with
  `score>0` while `risk_signals == []` and
  `risk_summary.categories == []`. Observed 2026-05-04 manual UI scan:
  `level=needs_review`, `score=22`, single human-readable reason in
  `signal_summary.note` (`"Sensitive file activity exists near target
  activations, but attribution is only correlative."`) but no
  structured category for the UI to badge. Either populate
  `risk_summary.categories` from the `signal_summary` derivation path
  or downgrade the level to a more honest `"inconclusive"` when no
  risk signal supports it. Tied to ADR 0003 verdict rollup semantics
  — `§11` brief flagged ADR 0003 changes as W10 non-goal; natural
  landing is W13+ external-review window where verdict semantics can
  be revised holistically. Surfaced by 2026-05-04 manual UI scan.

### UI

UI v3 redesign minimal-completion landed `2026-04-29` (see
`REFACTOR_STATUS.md`). Open follow-ups:

- **`[BACKLOG ui-v3-1]` … `[BACKLOG ui-v3-8]`** — pre-minimal-completion
  backend gaps (rule-save endpoint scaffolding, contract drift edges).
- **`[BACKLOG ui-v3-13]`** rule-save endpoint (post-minimal-completion).
- **`[CLEANUP ui-v3-9]`** orphan v3 component prune (LANDED 2026-04-28).
- **`[CLEANUP ui-v3-14]`** `design_handoff_extrace_console/` retired
  (LANDED 2026-04-29).
- **`[ADD ui-v3-10/11/12]`** Inspector drawer + RuleDraftSection on
  Reports, Run health + Coverage summary on Simulation, Ledger Scenario
  tab (LANDED 2026-04-28).
- UI component split (7.3.1, 7.3.2, 7.3.3, 7.3.4, 7.3.5) + axe-core —
  surface not stabilized; rejected from W8-W13.

### Engineering Quality

- mypy strict promotion (rejected from W8-W13; revisit W13 sonrası).
- Monorepo tooling migration (uv / poetry).
- OpenAPI frontend client generation.
- Documentation consolidation pass (`REFACTOR_STATUS` /
  `REFACTOR_EXECUTION_PLAN` / `REFACTOR_OPTIMIZATION` dedupe) —
  living-doc cadence not settled yet.
- **`[FOLLOWUP ci-reintroduction]`** — `ci.yml` and `docs-check.yml`
  workflows were retired on `2026-04-30` after persistent flakiness in
  the `security-fixtures` job (iptables egress sandbox on GitHub
  runners). Local equivalents (`make check-all`, `make test-security`,
  `make test-local`, plus the new `pre-push` pre-commit stage) cover
  the same checks. `security.yml` (weekly Trivy + Bandit) was kept.
  Reintroduce a remote pipeline if any of the following triggers fire:
  (a) a second contributor joins, (b) PyPI/Docker-registry release
  starts, (c) T2 fixtures land that genuinely need ambient egress
  isolation. Before reintroduction, diagnose the original
  `security-fixtures` breakage (likely runner-image iptables / sudo
  drift) so the new lane does not inherit the same flake. See ADR 0004
  addendum (2026-04-30).

### Repo Hygiene (surfaced 2026-04-29 audit pass)

- **`[CLEANUP repo-tracked-scratch-files]`** — *LANDED 2026-05-03 on
  `feat/w9-executor-detection-boundary`*. `problems.md` + `todo.md`
  untracked + `.gitignore`'d (root scope); canonical status owned by
  `REFACTOR_STATUS.md` + `automation_todo.md`.
- **`[CLEANUP tests-scanner-rename]`** — *LANDED 2026-05-03 on
  `feat/w9-executor-detection-boundary`*. `git mv tests/scanner
  tests/executor/scanner` (34 tests preserved); no inbound imports
  to update. pytest collection unchanged.
- **`[CLEANUP report-builder-naming]`** — Two "report" modules with
  similar names live in different layers:
  `executor/flows/playwright/report_builder.py` (in-container, builds
  the on-disk `ActivationReport`) and
  `workflows/marketplace/analysis_reports.py` (host, loads + validates
  reports from disk). A grep for "report builder" or "analysis report"
  matches both and confuses navigation. Rename one when convenient
  (suggest `analysis_reports.py` → `report_loader.py` since its job
  is read-side); keep cosmetic, not urgent.
- **`[CLEANUP env-example-extrace-vars]`** — Two operator-relevant
  `EXTRACE_*` env vars are read in code but absent from `.env.example`:
  `EXTRACE_VSCODE_SETTINGS_JSON`
  (`executor/flows/playwright/settings.py:42`, settings override) and
  `EXTRACE_SKIP_JOB_RECOVERY` (`main.py:28`, boot-time job-recovery
  toggle). `EXTRACE_ALLOW_LAN` is documented; these two are not.
  `EXTRACE_EPOCH_RUN_ID` is internal — set by
  `executor/container/start.sh:25-26` — and stays undocumented.
  Append commented entries with one-sentence purpose strings.
  Surfaced by 2026-05-04 audit pass.
- **`[CLEANUP agent-context-phase-snapshot-stale]`** — *LANDED
  2026-05-04 on `feat/w10-contract-hygiene`*. Refreshed `AGENTS.md`
  Current State + `AGENT_CONTEXT.md` Source-of-Truth list to current
  phase (W8 closed `2026-04-29`, W9 closed `2026-05-04`, W10 in
  flight on `feat/w10-contract-hygiene`); ADR 0007 documented as
  implemented (W8-7 landed). The W8 tracker is preserved with a
  "past tracker" framing because code/tests still reference items
  by stable W8-N IDs.
- **`[CLEANUP postgres-version-fact-drift]`** — `docker-compose.yml:3`
  runs `image: postgres:16-alpine`, while external audit prompts /
  project-fact handoffs have still referenced PostgreSQL 15. Current
  repo docs searched in the 2026-05-04 pass did not show a live
  PostgreSQL 15 claim, and README already states PostgreSQL 16.
  Compose is ground truth for runtime; keep future prompts/handoffs
  aligned with PG 16 unless compose is intentionally pinned back.
  Surfaced by 2026-05-04 second-pass review.
- **`[CLEANUP adr-0007-runbook-wording-drift]`** —
  `documents/adrs/0007-local-network-binding.md:86` says a compose
  selector substitutes the wildcard binding when `EXTRACE_ALLOW_LAN=1`
  is set; `documents/runbooks/lan-exposure.md:91` says the operator
  must edit `docker-compose.yml` ports manually. Code is on the safer
  side (compose binds `127.0.0.1:` literally and post-init only
  swaps API HOST to `0.0.0.0` inside the process), but the two docs
  describe different operator paths. Reconcile wording. Surfaced by
  2026-05-04 second-pass review.
- **`[CLEANUP session-docstring-except-exception]`** —
  `appcore/db/session.py:137` is a docstring example that teaches
  `except Exception: db.rollback()` as the canonical session
  pattern, even though AGENTS rule 6 forbids it in production code.
  Not executable, but the example will mislead future authors and
  conflict with the planned `[FOLLOWUP arch-gate-no-bare-except]`
  AST gate. Replace the docstring example with narrow exception
  types (`SQLAlchemyError`, `IntegrityError`). Surfaced by
  2026-05-04 second-pass review.

### Test + Observability (Promoted To W13)

These now live in `REFACTOR_OPTIMIZATION.md §11.10`; tracked here only as
a pointer:

- Benign silence fixture 3 → 5; stale singleton-lock + `.env` gitignore
  regression tests; `extrace.executor.*` logger consolidation; run-ID
  stamping.

### Codex Automation Flow Review (2026-04-27)

Numbered triage (codex-automation-{1..8}). Detail in archive
("§Codex automation flow review"). Open:

- **`[FOLLOWUP codex-automation-5]`** Executor runtime fingerprint in
  report.
- **`[FOLLOWUP codex-automation-6]`** UI failure taxonomy.

Landed (evidence in `REFACTOR_STATUS.md` archive):
codex-automation-3, 7, 8.

### Live-Scan Findings (2026-04-27, post-W8-0 smoke)

- **`[FOLLOWUP capability-verification-gap]`** `debug` +
  `terminal_tasks` capability verification (read in archive for the
  `ms-python.python` `degraded` health debrief).
- **`[FOLLOWUP w8-0-capture-pipeline]`** — partial close: signal (a)
  closed by W8-3 live smoke 2026-04-28; signal (b) typed
  harness-readiness reason codes still unconfirmed live.
- **`[FOLLOWUP make-test-security-lane-composition]`** — *FULL CLOSE
  2026-04-30 via W9-6d*. `make test-security` now unions fixture
  hygiene + architecture defaults + W8 subsystem security lanes
  (`tests/security/`, `tests/platform/security/`,
  `tests/architecture/test_default_bindings.py`,
  `tests/workflows/marketplace/test_vsix_hardening.py`,
  `tests/executor/security/test_uri_trigger_injection.py`,
  `tests/workflows/activation_reports/test_router_path_traversal.py`).
  W9-5 container import-mode test stays under
  `make test-arch-import-mode` (smoke marker; default pytest config
  filters smoke out, so folding would silently deselect).
- **`[FOLLOWUP w8-4-broader-executor]`** — W8-4 absolute-binary-path
  discipline applied to `executor/host.py` + `uri_validation.py` only
  (tracker scope). Bare-name `subprocess.run`/`Popen` literals remain
  in `editor.py` (xdotool x3), `monitor_runtime.py` (ps),
  `reset_state.py` (pgrep, bash), and
  `runtime_capture/extension_host.py` (inotifywait); each carries a
  `# arch-allow: bare-binary-path` pragma so the
  `tests/architecture/test_absolute_binary_paths.py` gate stays green.
  Three additional sites use a `cmd = [...]; subprocess.Popen(cmd)`
  variable-indirect form that the AST gate intentionally skips
  (`runtime_capture/network.py:268` `tshark`,
  `runtime_capture/filesystem.py:203` `inotifywait`,
  `runtime_capture/extension_host.py:504` `strace`); the followup must
  cover these too because the gate cannot enforce them today.
  Pull-next: extend `binary_paths.py` with `XDOTOOL_PATH`, `PS_PATH`,
  `PGREP_PATH`, `BASH_PATH`, `INOTIFYWAIT_PATH`, **`STRACE_PATH`**, and
  **`TSHARK_PATH`** (container Linux paths), migrate both pragma'd
  literal sites and the variable-indirect cmd lists, then remove the
  pragmas. POST_POC because it is uniformly `# nosec`-annotated already
  and not on the W8 stakeholder bar.
- **`[FOLLOWUP w8-1-extract-rejection-logging]`** —
  *Logging half closed 2026-04-30 via W9-6a*:
  `_extract_vsix_to_dir` emits per-entry `vsix_entry_rejected
  reason={path_traversal,symlink_escape}` + aggregate
  `vsix_extraction_rejections total=...` and returns rejection count;
  regression in `tests/workflows/marketplace/test_vsix_hardening.py`.
  *Count propagation pending*: tuple the count out of
  `download_and_extract_vsix`, persist on the marketplace job state
  row, fold into `ActivationReport` (new `vsix_rejection_count: int =
  0` field). Surfaced by 2026-04-29 audit pass.
- **`[FOLLOWUP w8-1-archive-count-bypass]`** —
  `workflows/marketplace/client.py:172` skips entries whose name does
  not start with `extension/` **before** `:188` increments
  `file_count`, so the W8-1 `MAX_FILE_COUNT` guard never fires for
  archives that pad the central directory with non-`extension/`
  members. Bounded blast radius (the `zipfile` central directory is
  already in memory; the loop does no per-entry disk I/O), but a
  defense-in-depth closure is `len(zf.infolist()) > MAX_FILE_COUNT`
  early-reject + a regression fixture in
  `tests/workflows/marketplace/test_vsix_hardening.py` that posts a
  VSIX with thousands of `pad/<n>` members and one valid
  `extension/package.json`. Companion to
  `[FOLLOWUP w8-1-extract-rejection-logging]`. Surfaced by 2026-05-04
  second-pass review.
- **`[FOLLOWUP w8-3-harness-js-scheme]`** —
  `executor/flows/harness_extension/stimulus_dispatch.js:41` calls
  `vscode.env.openExternal(vscode.Uri.parse(payload.uri_trigger))`
  without re-validating the URI scheme; the W8-3 allow-list
  (`vscode`, `vscode-insiders`, `http`, `https`) is enforced only on
  the Python `executor/flows/playwright/uri_validation.py` host-side
  path. If any orchestration path can supply a non-validated
  `payload.uri_trigger` to the harness, schemes outside the allow-list
  reach `openExternal` unchecked. Defense-in-depth options: (a)
  re-validate scheme in `stimulus_dispatch.js` against the same
  allow-list; or (b) prove via test that every producer of
  `payload.uri_trigger` flows through `uri_validation` first, and add
  a JS-side AST gate
  (`tests/architecture/test_uri_trigger_open_external_validation.py`)
  forbidding raw `openExternal(Uri.parse(...))` outside that path.
  Surfaced by 2026-05-04 second-pass review.
- **`[FOLLOWUP w8-5-list-endpoint-name-filter]`** — *CLOSED 2026-04-30
  via W9-6b*. `_list_report_files` filters glob hits through
  `ACTIVATION_REPORT_NAME_RE`. Regression: `tests/workflows/
  activation_reports/test_router_path_traversal.py
  ::test_list_endpoint_filters_malformed_names`.
- **`[FOLLOWUP w8-6-content-sample-structural-test]`** — *Partial close
  2026-04-30 via W9-6c*: `tests/platform/security/test_content_sample_typing.py`
  pins `ContentSample` shape invariants (`extra="forbid"`,
  `validate_assignment=True`, redaction validator on `value`) and locks
  a `_PENDING_MIGRATION` allow-list snapshot — currently
  `EvidenceEvent.raw_context` is the registered placeholder. When a
  field's annotation flips to `ContentSample`, the test fails (XPASS-
  equivalent) and the allow-list must be trimmed. **Audit gap remains**:
  the comprehensive sweep of every extension-derived string field on
  the `ActivationReport` subtree (`NetworkEvent.request_body_preview`,
  `NetworkEvent.response_body_preview`, `EvidenceEvent.summary`,
  `ProcessEvent.command`/`arguments_preview`, `FileEvent.summary`, etc.)
  is *not* enumerated yet — the `_PENDING_MIGRATION` list is a baseline
  placeholder, not a complete inventory. Pickup procedure: walk the
  contract surface, append every extension-controlled string field to
  `_PENDING_MIGRATION`, then plan the per-field migration to
  `ContentSample`. Surfaced by 2026-04-29 audit pass; structural-test
  half closed by W9-6c on 2026-04-30.
- **`[FOLLOWUP w8-8-manifest-emit-when-needed]`** — DEFERRED 2026-04-29
  (W8-7 audit pass). No production logger emits manifest fields raw
  today; only the W8-2-validated `publisher`/`name`/`version` slug
  reaches loggers. **Canonical body lives in
  `active-work/W8-security.md` W8-8** (threat statement, two reopen
  triggers, four-artifact set, pickup procedure — do not delete).
  Triggers in short: (A) first feature PR adding a `logger.*` call
  that references a raw manifest field (`displayName`, `description`,
  `repository.url`, `categories[]`, `homepage`, `bugs`, `qna`,
  `license`); (B) proactive security pull from external review or
  stakeholder gate. Either trigger ships
  `appcore/contracts/sanitize.py::sanitize_for_log`,
  `tests/platform/security/test_manifest_log_sanitization.py`,
  `tests/architecture/test_manifest_field_log_emit.py`, and ADR 0002
  §7 addendum in one PR; flip W8-security.md marker to landed and
  retire this ID.

### Architecture Audit (2026-04-27)

Detail in archive. Open audit gaps:

- §7 untrusted-input → logging gap closed by W8-8 (manifest
  log-injection sanitization, `active-work/W8-security.md`).
- Remaining audit deltas tracked in archive; consolidate after W13.
- **`[FOLLOWUP arch-gate-no-bare-except]`** — AGENTS rule 6 (no
  generic `try/except Exception`) is enforced verbally only; no AST
  gate exists. Production code is currently clean (the only
  `except Exception` hit is inside a docstring at
  `appcore/db/session.py:137`), but the rule has no machine guard
  against re-introduction. Several AGENTS hard rules already have
  architecture gates under `tests/architecture/`; add the same style of
  narrow gate for this rule:
  `tests/architecture/test_no_bare_except_exception.py` that AST-walks
  `appcore/`, `workflows/`, `executor/`, `packages/` (excluding tests,
  alembic, scripts) and rejects `ExceptHandler(type=Name(id="Exception"))`
  and `ExceptHandler(type=None)`. Allowlist the future
  `[FOLLOWUP analysis-thread-supervisor]` site via
  `# arch-allow: thread-supervisor` when that lands. Surfaced by
  2026-05-04 audit pass.

---

## How To Pull An Item Back

1. Pick the item by stable ID.
2. Open the archive entry for the full trigger / file refs / acceptance.
3. If the work landing point matches a `REFACTOR_OPTIMIZATION.md §11`
   week, promote it there with a one-line rationale; otherwise open a
   focused branch and update the item to `[LANDED <date>]` with the
   commit SHA + branch name.
4. Drop the verbose closure evidence into `REFACTOR_STATUS.md` (slim
   canonical or archive depending on size budget).

When this file exceeds 300 lines / 3,000 tokens, drop a new dated full
snapshot under `archive/backlog/` and re-trim — see
`agent-lanes/docs-maintenance.md` invariants.

## Archive

Full historical backlog (verbose item descriptions, all landed evidence,
review triage blocks, architecture audit body):

- Latest audit snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md)
- Pre-trim baseline snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-04-29.md`](archive/backlog/POST_POC_BACKLOG_full_2026-04-29.md)
