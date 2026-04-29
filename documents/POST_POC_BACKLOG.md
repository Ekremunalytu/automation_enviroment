# Post-PoC Backlog

`Last Updated: 2026-04-29` (audit-pass refresh)

Open work items deferred from W0-W7 PoC scope. **Slim canonical** — full
verbose item descriptions, landed-evidence detail, and review triage
blocks frozen under
[`archive/backlog/POST_POC_BACKLOG_full_2026-04-29.md`](archive/backlog/POST_POC_BACKLOG_full_2026-04-29.md).

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
- **`[FOLLOWUP analysis-thread-error-detail-leakage]`**
  `analysis_service.map_executor_error()` returns `HTTPException(detail=
  f"Automation failed: {message}")` where `message` is `str(exc)` from an
  `ExecutorError`; sanitize/truncate before returning so internal paths
  and env values do not surface in API responses. Low-impact under
  loopback default, must close before LAN exposure (W8-7).
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

### Executor / Capture Hygiene

- **T2 declawed samples + T3 handling** + `make test-security-live`
  hardening — ADR 0004 covers policy; operational plumbing waits on
  real T2 engagement.

### Detection / Contracts

- A5 + A7 adversary-class T1/T2 canary + rule (stretch).
- Allow-list (`benign_domains.txt`, `popular_extensions.txt`) versioned
  data artifact promotion.
- Domain service pattern genişletmesi (2.8 — W7'de ertelendi).

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

### Repo Hygiene (surfaced 2026-04-29 audit pass)

- **`[CLEANUP repo-tracked-scratch-files]`** — `problems.md` (4.5 KB)
  and `todo.md` (215 B) at repo root are git-tracked but read like local
  scratch (analysis artifacts, ad-hoc notes). `.gitignore` already
  excludes `*.log` / `.coverage` / `htmlcov/`; either `git rm` these
  two and add explicit ignores, or move their content into the
  appropriate canonical doc (`automation_todo.md` or active-work
  tracker).
- **`[CLEANUP tests-scanner-rename]`** — `tests/scanner/test_executor.py`
  (34 tests) tests `docker_exec` / `install_extension` / VS Code
  container harness — i.e. executor-layer concerns. AGENTS.md §62
  retired the legacy `scanner/` top-level; the test directory still
  carries the stale name. `git mv tests/scanner tests/executor/scanner`
  (or merge into `tests/executor/`) and update any pytest path-marker
  references.
- **`[CLEANUP report-builder-naming]`** — Two "report" modules with
  similar names live in different layers:
  `executor/flows/playwright/report_builder.py` (in-container, builds
  the on-disk `ActivationReport`) and
  `workflows/marketplace/analysis_reports.py` (host, loads + validates
  reports from disk). A grep for "report builder" or "analysis report"
  matches both and confuses navigation. Rename one when convenient
  (suggest `analysis_reports.py` → `report_loader.py` since its job
  is read-side); keep cosmetic, not urgent.

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
- **`[FOLLOWUP make-test-security-lane-composition]`** — `make
  test-security` only runs `tests/security/`. W8-1 lives at
  `tests/workflows/marketplace/test_vsix_hardening.py`, W8-3 at
  `tests/executor/security/test_uri_trigger_injection.py`; same
  pattern likely for W8-6 / W8-8. Either extend the Makefile target
  to fold subsystem-local W8 lanes in, or update
  `active-work/W8-security.md` exit criterion to count the broader
  test-suite security tally. **Partial close 2026-04-29:** W8-6
  (content-sample redaction) added `tests/platform/security` to the
  `test-security` target so the new lane runs alongside fixture
  hygiene; W8-1/W8-3/W8-8 paths remain outside the target. Full
  reorganization still deferred to W8 closure pass.
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
  `workflows/marketplace/client.py:_extract_vsix_to_dir` silently
  `continue`s when an entry fails the `..` filter (line 166) or the
  `target.resolve().relative_to(destination_dir.resolve())` check
  (line 197-200). The extraction-limit branches raise `VSIXUnpackError`
  with detail; the path-rejection branches drop the entry without a
  log line, so a malicious VSIX leaves no breadcrumb in the heartbeat
  or analysis report. Add a single `logger.warning("vsix_entry_rejected
  reason=... entry=...", ...)` per branch and surface the count in the
  job report. Surfaced by 2026-04-29 audit pass.
- **`[FOLLOWUP w8-5-list-endpoint-name-filter]`** — W8-5 closed the
  `/{name}` and `/{name}/bundle` path-parameter validation; the list
  endpoint at `workflows/activation_reports/router.py:_list_report_files`
  still globs `activation_report*.json` without filtering results
  through `ACTIVATION_REPORT_NAME_RE`. A locally-writable file named
  e.g. `activation_report_evil.json` would be returned by listing.
  Threat is bounded (requires local FS write to `output/`), defense in
  depth. Surfaced by 2026-04-29 audit pass.
- **`[FOLLOWUP w8-6-content-sample-structural-test]`** — W8-6 redaction
  is correct on construction + assignment, but there is no contract
  test that all extension-derived string fields on `ActivationReport`
  (and its nested types) are typed as `ContentSample` rather than
  plain `str`. A future rule could add a `str` evidence field and
  bypass redaction without any gate failing. Land a Pydantic-introspect
  test under `tests/platform/security/` that walks the schema and
  asserts the typing constraint. Out-of-scope for W8-6 closure pass
  but tracked here so it doesn't get lost. Surfaced by 2026-04-29
  audit pass.
- **`[FOLLOWUP w8-8-manifest-emit-when-needed]`** — The original W8-8
  plan in `active-work/W8-security.md:266` presumed manifest-field log
  emit sites in `workflows/extension_catalog/`, `workflows/marketplace/
  job_service.py`, and `workflows/marketplace/analysis_execution.py`
  that the new `appcore/contracts/sanitize.py::sanitize_for_log` helper
  would retrofit. The audit at the start of W8-7 (`2026-04-29`) found
  zero such sites — only the W8-2-validated `publisher`/`name`/`version`
  slug currently flows to loggers in those modules. The helper, ADR
  0002 §7 addendum, and the AST gate (which would forbid future
  unsanitized manifest-field emits) land in the iteration that
  actually introduces such an emit site, so the helper can land
  alongside its first real caller and the AST gate can be sized
  against real fixtures.

  **Reopen triggers (either is sufficient):**

  - **Trigger A — first real call site appears.** A feature PR adds
    a logger call that references `displayName`,
    `publisher.displayName`, `description`, `repository.url`,
    `categories[]`, `homepage`, `bugs`, `qna`, or `license` from the
    parsed manifest. The same PR ships the four W8-8 artifacts.
  - **Trigger B — proactive security pull.** External review or a
    stakeholder gate requires the defense-in-depth helper before any
    real call site exists. A standalone PR ships the four W8-8
    artifacts; the AST gate is sized against synthetic fixtures
    (mirror `tests/architecture/test_marketplace_identity_concat.py`
    self-test pattern).

  **W8-8 artifact set (four items, all in one PR):**

  1. `appcore/contracts/sanitize.py::sanitize_for_log` helper
     (CR/LF/C0/C1/ANSI escape, NULL-byte reject, length cap;
     re-export from `appcore/contracts/__init__.py`).
  2. `tests/platform/security/test_manifest_log_sanitization.py`
     (parametrized cases for control-char escape, null-byte reject,
     length truncation, unicode pass-through, and idempotence —
     mirroring the W8-6 `test_content_sample_redaction.py` shape).
  3. `tests/architecture/test_manifest_field_log_emit.py` AST gate
     (forbids unsanitized manifest field references inside production
     logger calls; pragma `# arch-allow: untrusted-manifest-log` for
     legitimate exceptions).
  4. `documents/adrs/0002-threat-model.md` §7 "Untrusted Manifest
     Fields as Log Forging Surface" addendum.

  **Pickup procedure:** Walk the DEFERRED block in
  `active-work/W8-security.md` top-to-bottom, add the four artifacts
  in the matching trigger's PR, retire this followup ID with
  `[LANDED <date>]`, and flip the W8-security.md DEFERRED marker to
  `landed`. **Do not delete the W8-8 plan body** in W8-security.md —
  it is the canonical statement of the threat and survives the marker
  flip. Surfaced by 2026-04-29 W8-7 implementation pass.

### Architecture Audit (2026-04-27)

Detail in archive. Open audit gaps:

- §7 untrusted-input → logging gap closed by W8-8 (manifest
  log-injection sanitization, `active-work/W8-security.md`).
- Remaining audit deltas tracked in archive; consolidate after W13.

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
[`archive/backlog/POST_POC_BACKLOG_full_2026-04-29.md`](archive/backlog/POST_POC_BACKLOG_full_2026-04-29.md).
