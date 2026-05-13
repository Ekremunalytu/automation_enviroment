# Refactor Status

`Last Updated: 2026-05-13 (W14 active; W14-1 BLOCKER -> HIGH downgraded; W14-2 closed via bde17be; W14-3 closed via 941250d; W14-4 closed; W14-5 closed via dc79f61+9c095d2+db25d5f; W14-6 closed via 2adad43+b031803+e42a448; week14 branch cut from main at 69251f1; W13 close-out PR #20 week13 -> main merged via 772deb3; W14 sub-iter slate complete, close-out PR week14 -> main next)`

Active status board for current closure state. **Slim canonical** — verbose
phase evidence is frozen under dated snapshots:

- latest full snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-05-13.md`](archive/status/REFACTOR_STATUS_full_2026-05-13.md)
- previous full snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-05-11.md`](archive/status/REFACTOR_STATUS_full_2026-05-11.md)
- older full snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-05-07.md`](archive/status/REFACTOR_STATUS_full_2026-05-07.md)
- older W4-W8 snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-04-29.md`](archive/status/REFACTOR_STATUS_full_2026-04-29.md)

## Current State

- **W0-W7 closed `2026-04-23`** — PoC acceptance bar 11/11 green
  (`REFACTOR_OPTIMIZATION.md` §10.7).
- **PR345 + W8-0 closed `2026-04-27`** — target activation lifecycle PRs
  1-5 plus ADR 0006 landed; deterministic harness readiness gate landed.
- **W8 closed `2026-04-29`** — W8-1..W8-7 and W8-9 landed. W8-8 remains
  deferred under `[FOLLOWUP w8-8-manifest-emit-when-needed]`.
- **W9 closed `2026-05-04` via PR #9 (`d67944d`)** — ADR 0008 package-mode
  invocation accepted; dual-import fallback and runtime `sys.path.insert`
  debt removed.
- **W10 closed `2026-05-04` via PR #11 (`25e4c16`)** — contract hygiene,
  planner cleanup, typed report fields, and executor action enum landed.
- **W11 closed `2026-05-05` and merged via PR #14 (`50ca69e`)** — W11-1..W11-8
  monitor/workflow/storage split work landed.
- **W12 closed `2026-05-10` and merged via PR #18 (`33a0852`)** — W12-0..W12-5
  landed, plus UI Dockerfile digest pin, close-out coverage, and the Codex
  audit CRITICAL redaction fix. Final post-Codex-fix baseline at close commit
  `e8a9926`: `make check-all` green; `make test-local` 1452 passed /
  6 skipped / 6 deselected / 75 warnings; `make test-security` 211 passed /
  32 warnings; `tests/architecture/` 76 passed / 2 deselected. Tracker is
  frozen for stable-ID reference:
  [`active-work/W12-executor-subpackaging.md`](active-work/W12-executor-subpackaging.md).
- **W13 — Test Expansion + Observability closed `2026-05-13` and merged via
  PR #20 (`772deb3`).** Tracker:
  [`active-work/W13-test-expansion-observability.md`](active-work/W13-test-expansion-observability.md).
  W13-1..W13-13 are all GREEN. Final/post-merge bar: `make test-local`
  1551 passed / 10 skipped / 8 deselected; `make test-security` 215 passed;
  `tests/architecture/` 117 passed. W13-11/12/13 were pulled in-window from
  the close-gate review to preserve H6/H4 audit-trail integrity; remaining
  §11.10 umbrellas moved to W14.
- **Active phase: W14 — Codex M-class Acceptance + Observability** (active;
  `week14` branch cut from `main` at `69251f1` on `2026-05-13`). Scope
  authored `2026-05-11` in
  [`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md);
  plan source [`REFACTOR_OPTIMIZATION.md §12`](REFACTOR_OPTIMIZATION.md).
  6 sub-iter scoped (`W14-1..W14-6`): BLOCKER scenario-dropout araştırması,
  Codex M-class input validation (M4-M7 + M11), dış yüzey sertleştirme
  (M13 + M14b + U4-U12), correctness/concurrency (analysis-jobs-race +
  evidence-event-kind invariant), §11.10 GOAL devamı (logger consolidation
  - run-ID stamping), W8-W12 regression lock-in umbrella. W14-1 pulled
  `2026-05-13`; BLOCKER `[BUG scenario-dropout-upstream-root-cause]`
  triage landed deterministic repro matrix
  (`tests/security/test_scenario_dropout_repro.py`) + conservation guard
  (`scenario_accountant.py:392-438`), severity downgraded BLOCKER -> HIGH
  the same day; upstream emit-site split moved to
  `[FOLLOWUP scenario-accountant-conservation-split]`. W14-2 (M4-M7
  output-ts range + M11 report-health malformed types) closed `2026-05-13`
  via `bde17be`. W14-3 (M13 network URI/summary redaction + M14b CDP
  default-disabled + U4-U12 Makefile shell-quoting) closed `2026-05-13`
  via `941250d`. W14-4 (analysis-jobs-race lock symmetry on
  `complete_analysis_job` / `fail_analysis_job` + EvidenceEvent
  kind↔event_class invariant via closed 9-kind allowlist) closed
  `2026-05-13`. W14-5 (`extrace.*` logger consolidation + run-ID
  stamping + executor runtime fingerprint emit) closed `2026-05-13`
  via `dc79f61` + `9c095d2` + `db25d5f`; ADR 0010 landed; M5
  (`epoch-docker-exec-propagation`) auto-closed as natural byproduct
  of sub-commit 2. W14-6 (regression lock-in umbrella:
  bare-binary-path pragma ratchet + `executor.control` outbound
  surface gate + variable-indirect subprocess coverage) closed
  `2026-05-13` via `2adad43` + `b031803` + `e42a448`; pragma baseline
  lowered 7 → 6 in-window via inotifywait/tshark/strace absolute-path
  migration. W14 sub-iter slate complete (W14-1..W14-6); close-out PR
  `week14 -> main` is the next milestone.

## W13 Status Summary

| Scope | Status |
|---|---|
| Acceptance bar | W13-1..W13-7 closed H3/H4/H5/H6/M1/M9 from the 2026-05-10 Codex Cloud audit. |
| §11.10 GOAL pulls | W13-8 benign silence fixture 3->5, W13-9 `.env` gitignore gate, and W13-10 singleton-lock recovery closed. |
| Close-gate pulls | W13-11 HMAC python secret target-install race, W13-12 fail-closed harness handshake, and W13-13 worker-start cancel-race CAS closed in-window. |
| Merge | PR #20 `week13 -> main` merged `2026-05-13` via `772deb3`; W13 tracker remains as the stable-ID evidence file. |

## Current Deferrals

- `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` — programmatic Alembic
  upgrade/downgrade test remains deferred pending a fresh-DB-per-test fixture.
- `[FOLLOWUP analysis-jobs-race]` — **closed** by W14-4 on `2026-05-13`;
  `complete_analysis_job` + `fail_analysis_job` now acquire
  `with_for_update()` and gate against `_TERMINAL_JOB_STATUSES`.
- `[FOLLOWUP simulation-progress-cancel]` remaining subitems:
  `heartbeat-sandbox-reset-off-thread`, `dedupe-step-progress-schemas`, and
  `heartbeat-refactor` iterate after W13-3.
- `[BUG scenario-dropout-upstream-root-cause]` is W14-1 (pulled `2026-05-13`;
  in progress) — BLOCKER triage unless dropout proves stochastic or misses a
  live threat category.

## Read Order

When updating this file, keep it as a slim closure board. Put verbose
evidence in `documents/archive/status/`, keep pull-next detail in
`POST_POC_BACKLOG.md`, keep closed W13 mechanics in
`active-work/W13-test-expansion-observability.md`, and active W14 staging scope
in `active-work/W14-codex-acceptance-observability.md`.
