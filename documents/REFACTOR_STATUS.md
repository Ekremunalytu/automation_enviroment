# Refactor Status

`Last Updated: 2026-05-16 (W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d — W14-1..W14-8 sub-iter slate + post-slate hotfixes + close-out hygiene pass; W15 active on week15 branch cut from main HEAD 7cc2921 on 2026-05-14; W15-1 closed via c58c365 — sync analyze error taxonomy parity (M10); W15-2 closed via 765cde7 — clean_workspace is_symlink-before-rmtree (M12); W15-3 closed via 3512a7c — activationEvents bounds + Alembic migration (U8); W15-4 closed via 89e13e3 — UI bounds bundle (U1/U2/U3 + U6); W15-1 post-slate typing hotfix via 976dc96 — ANALYZE_ERROR_TYPES annotation narrowed; W15-5..W15-7 pending; W13 close-out PR #20 week13 -> main merged 2026-05-13 via 772deb3; W15 mid-iter hygiene 2026-05-16: doc-preamble consistency arch gate added + 3 new audit findings in POST_POC_BACKLOG)`

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
- **W14 closed `2026-05-14` and merged via PR #21 (`4e03c8d`).** Tracker:
  [`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md).
  W14-1..W14-8 are all GREEN: W14-1 BLOCKER `[BUG scenario-dropout-upstream-
  root-cause]` triage downgraded to HIGH (`0c8bd02`); W14-2 (M4-M7 + M11
  input validation) `bde17be`; W14-3 (M13 + M14b + U4-U12 external-surface
  hardening) `941250d`; W14-4 (analysis-jobs-race lock symmetry +
  EvidenceEvent kind↔event_class 9-kind allowlist) `03b32bc`; W14-5 (logger
  consolidation + run-ID stamping + executor runtime fingerprint; ADR 0010;
  M5 docker-exec propagation byproduct) `dc79f61` + `9c095d2` + `db25d5f`;
  W14-6 (regression lock-in umbrella: bare-binary pragma ratchet +
  `executor.control` outbound gate + variable-indirect subprocess coverage)
  `2adad43` + `b031803` + `e42a448`; W14-7 post-slate hotfix
  (container-shipping regression + Python 3.10 UTC compat) `df925f8` +
  `c11ebd8`; W14-8 post-slate preventive gate (Python 3.11+ API forbid)
  `5638f82`. Final post-merge bar (re-recorded at W15-1 pull on `week15`):
  `tests/architecture/` 172 passed (171 from W14-8 + 1 ADR code fence gate
  added at close-out hygiene); `make test-security` 215 passed (unchanged
  from W13 final).
- **Active phase: W15 — Codex U-class Close-Out + UI Bounds + Posture**
  (active; `week15` branch cut from `main` HEAD `7cc2921` on `2026-05-14`).
  Scope authored `2026-05-14` in
  [`active-work/W15-codex-uclass-bounds-posture.md`](active-work/W15-codex-uclass-bounds-posture.md);
  plan source [`REFACTOR_OPTIMIZATION.md §13`](REFACTOR_OPTIMIZATION.md).
  7 sub-iter scoped (`W15-1..W15-7`): Codex U-class + I-class acceptance-bar
  pull-forward (close-out of `2026-05-10` audit), unauth catalog endpoints
  posture decision (ADR 0011 pending), and post-W14 regression lock-in
  umbrella (compose image pin + GH-action pin + doc preamble refresh).
  W15-1 closed `2026-05-14` via `c58c365` (sync analyze error taxonomy
  parity, M10 close; `tests/architecture/test_analyze_error_taxonomy_parity.py`
  + behavioral parametrize). W15-2 closed `2026-05-14` via `765cde7`
  (`clean_workspace` is_symlink-before-rmtree, M12 close; path-b fix
  hizalanan `_clear_directory` deseni). W15-3 closed `2026-05-15` via
  `3512a7c` (`activationEvents` bounds + Alembic field-length migration,
  U8 close; +6 arch gates + 8 behavioral cases). W15-4 closed `2026-05-16`
  via `89e13e3` (UI bounds bundle: `EventTimeline` / `EventDensityStrip` /
  `InteractionsSection` caps with truncation indicators, U1/U2/U3 + U6
  close; 21 new vitest cases across 3 files). **W15-1 post-slate typing
  hotfix** landed `2026-05-16` via `976dc96` (`ANALYZE_*_ERROR_TYPES`
  annotation `tuple[type[BaseException], …]` → `tuple[type[Exception], …]`
  narrowing surfaced by W15-4 close-out mypy gate; W14-7 hotfix precedent).
  W15-5..W15-7 pending sequential pull (W15-5: UI `/health` proxy +
  lifecycle `for <id>` regex; W15-6: unauth catalog endpoints posture
  + ADR 0011; W15-7: regression lock-in umbrella — compose image pin +
  GH-action pin + doc preamble refresh). **W15 mid-iter hygiene
  `2026-05-16`:** W15-7 doc-preamble subset pulled forward; six canonical
  doc preambles (this file + `CLAUDE.md` + `AGENTS.md` +
  `documents/AGENT_CONTEXT.md` + `documents/POST_POC_BACKLOG.md` +
  `documents/REFACTOR_OPTIMIZATION.md`, plus `README.md`) refreshed to
  W15 truth-state; `tests/architecture/test_doc_preamble_consistency.py`
  added (cross-doc active-phase consistency gate) and
  `tests/architecture/test_readme_phase_pointer.py` updated from W14 to
  W15 + extended with a W14-close-out-merge tracking test symmetric
  with the existing W13-close-out test (`tests/architecture/` 186 → 188
  passing). Three new audit findings appended to `POST_POC_BACKLOG.md` —
  `[FOLLOWUP health-reconciliation-responsibility-split]`,
  `[CLEANUP marketplace-router-test-suite-split]`,
  `[FOLLOWUP analysis-job-worker-entry-crud-ownership]`. Remaining
  W15-7 items (compose image pin + GH-action pin) still not started.

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
- `[BUG scenario-dropout-upstream-root-cause]` — **closed** by W14-1 on
  `2026-05-13` via `0c8bd02` (deterministic repro matrix landed + conservation
  guard; severity downgraded BLOCKER -> HIGH same day; upstream emit-site
  split deferred under `[FOLLOWUP scenario-accountant-conservation-split]`).

## Read Order

When updating this file, keep it as a slim closure board. Put verbose
evidence in `documents/archive/status/`, keep pull-next detail in
`POST_POC_BACKLOG.md`, keep closed W13 mechanics in
`active-work/W13-test-expansion-observability.md`, keep closed W14
mechanics (sub-iter slate + post-slate hotfixes + close-out hygiene)
in `active-work/W14-codex-acceptance-observability.md`, and keep
active W15 scope (Codex U-class close-out + UI bounds + posture;
W15-1..W15-4 closed, W15-5..W15-7 pending) in
`active-work/W15-codex-uclass-bounds-posture.md`.
