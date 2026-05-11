# Refactor Status

`Last Updated: 2026-05-11 (W13 active; W13-1..W13-5 closed; W13-6 in progress — Codex M9 arguments_preview redaction extension, sub-commit 1 docs landing)`

Active status board for current closure state. **Slim canonical** — verbose
phase evidence is frozen under dated snapshots:

- latest full snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-05-11.md`](archive/status/REFACTOR_STATUS_full_2026-05-11.md)
- previous full snapshot:
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
- **Active phase: W13 — Test Expansion + Observability.** Tracker:
  [`active-work/W13-test-expansion-observability.md`](active-work/W13-test-expansion-observability.md).
  W13 acceptance-bar pull-forwards are H3, H4, H5, H6, M1, and M9 from the
  Codex Cloud audit `2026-05-10`; H4/H5/H6 are already closed.
- **W13-5 closed `2026-05-11` (5/5 sub-commits).** dev-lan Makefile
  drift (Codex H3) closed via Path A recipe-fix: `Makefile:172`
  `--host 0.0.0.0` → `--host $${API_HOST:-0.0.0.0}`. New architecture
  gate `tests/architecture/test_makefile_dev_recipes.py` 6/6 ✓.
  `documents/runbooks/lan-exposure.md` §Host-mode drift caveat
  removed. Final bar: `make test-local` 1492 → 1498 (+6 passed);
  `make test-security` 211 unchanged; `tests/architecture/` 87 → 93.
  Production code untouched (`appcore/`, `workflows/`, `executor/`,
  `packages/`, `ui/`, `alembic/` all zero diff over W13-5 range).
- **W13-6 in progress (opened `2026-05-11`).** Codex M9
  `arguments_preview` redaction extension pulled. Design locked-in:
  factory-internal redaction at
  `executor/flows/playwright/runtime_capture/extension_host_strace_parse.py:102-106`
  (`_bounded_arguments_preview()` routes its result through
  `redact_secrets()` before truncation). New architecture gate
  `tests/architecture/test_arguments_preview_redaction.py` replicates
  the W12-5 body-preview AST pattern with
  `TARGET_FIELD_NAMES = {"arguments_preview"}`. Sub-commit Roadmap:
  5 commits (docs + RED + GREEN + close + align). Sub-commit 1
  (docs only) landing now.

## W13 Status

| ID | Stable item | Status |
|---|---|---|
| W13-1 | `[FOLLOWUP codex-2026-05-10-H6-spoofable-harness-markers]` | closed `2026-05-10`; per-launch HMAC handshake; `make test-local` 1452 -> 1458; architecture 76 -> 79 |
| W13-2 | `[FOLLOWUP codex-2026-05-10-H5-writable-vscode-launcher]` | closed `2026-05-10`; `launch_vscode.sh` root-owned 0750; `make test-local` 1458 -> 1460; architecture 79 -> 81 |
| W13-3 | `[FOLLOWUP codex-2026-05-10-H4-cancel-concurrent-race]` | closed `2026-05-10`; two-phase `cancelling` cancel state + 5 worker poll points; `make test-local` 1460 -> 1467; architecture 81 -> 87 |
| W13-4 | `[FOLLOWUP w13-3-close-pass-cancellation-test-hardening]` | closed `2026-05-11`; behavioral cancellation coverage + runbook fix; `make test-local` 1473 -> 1485; `make test-security` 211 unchanged; architecture 87 unchanged |
| W13-5 | `[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]` | closed `2026-05-11`; Path A recipe-fix (`Makefile:172` `$${API_HOST:-0.0.0.0}`); `make test-local` 1492 → 1498 (+6 passed); architecture 87 → 93; production code untouched |
| W13-6 | `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]` | in progress (opened `2026-05-11`); factory-internal redaction at `_bounded_arguments_preview()`; new arch gate `test_arguments_preview_redaction.py` replicates W12-5 pattern |
| TBD | `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]` | W13 acceptance-bar MEDIUM, open; pull-eligible as W13-7 |

## Current Deferrals

- `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` — programmatic Alembic
  upgrade/downgrade test remains deferred pending a fresh-DB-per-test fixture.
- `[FOLLOWUP analysis-jobs-race]` — W13-4.4 documented the
  `complete_analysis_job` / `cancel_analysis_job` race window; pull W14+.
- `[FOLLOWUP simulation-progress-cancel]` remaining subitems:
  `heartbeat-sandbox-reset-off-thread`, `dedupe-step-progress-schemas`, and
  `heartbeat-refactor` iterate after W13-3.
- `[BUG scenario-dropout-upstream-root-cause]` remains W13-oriented unless
  dropout proves stochastic or misses a live threat category.

## Read Order

When updating this file, keep it as a slim closure board. Put verbose
evidence in `documents/archive/status/`, keep pull-next detail in
`POST_POC_BACKLOG.md`, and keep active W13 mechanics in
`active-work/W13-test-expansion-observability.md`.
