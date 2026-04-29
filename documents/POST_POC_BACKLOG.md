# Post-PoC Backlog

`Last Updated: 2026-04-29`

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
  test-suite security tally. Defer to W8 closure pass.

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
