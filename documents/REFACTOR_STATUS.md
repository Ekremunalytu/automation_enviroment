# Refactor Status

`Last Updated: 2026-05-12 (W13 active; W13-1..W13-10 sub-iters closed; W13-11 closed 2026-05-12 (6/6 sub-commits — design+impl+arch gate+regression fix+doc sweep) — Path A host-side eager-consume + env var passthrough; W13-12 in progress 2026-05-12 (sub-commit 1/5 — design lockdown) — `ActivationReport.harness_handshake_required: bool` fail-closed; W13-13 remains CLOSE-GATE not started; close-out PR week13 → main BLOCKED until W13-12/13 GREEN; W14 staging pre-entry)`

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
- **W13-6 closed `2026-05-11` (5/5 sub-commits).** Codex M9
  `arguments_preview` redaction extension closed via factory-internal
  redaction at
  `executor/flows/playwright/runtime_capture/extension_host_strace_parse.py:102-110`
  (`_bounded_arguments_preview()` routes its input through
  `redact_secrets()` before whitespace-normalize and truncate).
  New architecture gate `tests/architecture/test_arguments_preview_redaction.py`
  2/2 ✓ (factory body invariant + routing invariant). Parametrized
  regression `test_parse_strace_event_arguments_preview_redacts_secrets`
  5/5 ✓ (aws, bearer, api_key, db_url, private_key). Final bar:
  `make test-local` 1498 → 1505 collected, +7 passed; `make test-security`
  211 unchanged; `tests/architecture/` 93 → 95 passed. Production code
  diff scoped to a single file (+4 net lines in the factory body).
- **W13-7 closed `2026-05-11` (5/5 sub-commits).** Codex M1 PEM regex
  DoS closed via bounded scanner for the private_key cross-line span in
  `redact_multiline_secrets()` (`packages/analysis_contracts/evidence.py`).
  New `_redact_private_key_bounded()` helper does a linear O(L) scan
  with a 16 KB BEGIN→END window cap, replacing the lazy regex pattern.
  Empirical latency: pre-fix 361 ms → post-fix 1.29 ms on 200 BEGIN +
  1 KB body adversarial input (~280× speedup). W12-0's 4 PEM regression
  cases continue to pass — bounded scanner is replacement-semantics
  identical for real PEM input. New timing test
  `test_redact_multiline_secrets_rejects_catastrophic_pem_pattern` 1/1 ✓.
  Final bar: `make test-local` 1505 → 1506 collected, +1 passed
  (1499 passed total); `make test-security` 211 → 212; `tests/architecture/`
  95 unchanged. Production code diff scoped to a single file (+45 net
  lines in `evidence.py`).
- **W13 acceptance bar cleared.** H3 closed via W13-5, H4 via W13-3,
  H5 via W13-2, H6 via W13-1, M1 via W13-7, M9 via W13-6. No further
  MEDIUM/HIGH Codex acceptance items remain.
- **W13-8 closed `2026-05-11` (4/4 sub-commits).** First §11.10 GOAL
  pull after the Codex acceptance-bar closure: benign silence fixture
  3→5 GREEN landed. 3 new fixture extensions authored under
  `extensions/` (`extrace.fixture-snippet-0.0.1` declarative snippets,
  `extrace.fixture-keybinding-0.0.1` declarative keybindings,
  `extrace.fixture-cmd-0.0.1` `onCommand:` activation). Matching
  baseline activation reports (theme-clone for snippet/keybinding,
  chat-clone for cmd) added under
  `tests/platform/contracts/fixtures/activation_reports/`.
  `tests/security/helpers.py` `_FIXTURE_REPORTS` +3 entries;
  `tests/platform/contracts/test_analysis_fixture_baselines.py`
  `BASELINE_EXTENSION_FIXTURES` +3 entries and
  `expected_activation_event_types` +3 entries.
  `tests/security/test_benign_silence.py` 5/5 ✓ (3 skip decorators
  removed). `.gitignore` +3 allow rules and `scripts/reset_extensions.sh`
  `KEEP[]` extended. Final bar: `make test-local` 1514 passed /
  7 skipped / 8 deselected (3 W13-8 RED skips removed; baseline
  alembic+canary 7 skips preserved); `make test-security` 212 → 215
  (+3 passed); `tests/architecture/` 105 unchanged. Production code
  untouched (`appcore/`, `workflows/`, `executor/`, `packages/`,
  `ui/`, `alembic/` zero diff).
- **W13-9 closed `2026-05-11` (1/1 commit).** §11.10 GOAL `.env`
  gitignore regression test landed via new architecture gate
  `tests/architecture/test_env_gitignore.py` (10/10 ✓). Coverage:
  `.env` literal + `*.env` wildcard rules + virtualenv dir rules
  via inside-the-dir paths + `.env.example` negative-exception +
  template presence. Production code untouched; underlying
  `.gitignore` already correct (W13-9 pins the invariant). Final
  bar: `make test-local` 1509 → 1519 collected (+10 passed);
  `tests/architecture/` 95 → 105 collected (+10 passed);
  `make test-security` 212 unchanged.
- **W13-10 closed `2026-05-11` (1/1 commit).** §11.10 GOAL stale
  singleton-lock recovery integration test landed via 2 new cases in
  `tests/executor/test_reset_state.py` (13/13 ✓). Pre-W13-10 gap:
  unit cases covered `cleanup_singleton_locks()` in isolation and
  the orchestration case stubbed it; neither exercised the real
  cleanup inside `reset_executor_state()` with held lock files on
  disk. New cases assert end-to-end recovery (full 3-lock-held +
  partial 2-of-3-held variants). Production code untouched. Final
  bar: `make test-local` 1519 → 1521 collected (+2 passed);
  `tests/architecture/` 105 unchanged; `make test-security` 212
  unchanged.
- **CLOSE-GATE HOLD `2026-05-11`.** Codex Cloud second-opinion review
  on `week13` surfaced 3 P1 close-pass items pulled as W13 sub-iters
  (preserving audit-trail integrity for the originally W13-claimed
  H6 + H4 closures):
  - **W13-11** — `[CLOSE-GATE codex-second-opinion-F1-hmac-python-secret-target-install-race]`.
    Close-pass for W13-1 H6. `/results/_extrace_harness_python_secret`
    0600 executor:executor consumed only inside `setup_monitor` after
    `install_extension`; same-UID target reads file during
    install→setup_monitor window → forges HMAC-signed harness markers.
    Fix direction (Path A): eager-consume in executor bootstrap.
  - **W13-12** — `[CLOSE-GATE codex-second-opinion-F2-fail-closed-harness-handshake]`.
    Close-pass for W13-1 H6. `reconciliation.py:137-146` legacy
    phase-only fallback when `expected_nonce` empty; production
    sessizce spoofable mode'a düşer. Fix:
    `ActivationReport.harness_handshake_required: bool` with
    fail-closed production semantics. Depends on W13-11 (eager-consume
    guarantees secret presence).
  - **W13-13** — `[CLOSE-GATE codex-second-opinion-F3-worker-start-cancel-race-CAS]`.
    Close-pass for W13-3 H4. `analysis_service.run_analysis_job:194`
    unconditional `update_job(status="running")` regresses `queued →
    cancelling` to `running` — cancel intent kaybolur. Fix direction
    (Path B): worker entry `with_for_update()` snapshot +
    `finalize_cancelled_analysis_job` if `cancelling` observed.
    **Scope rebased `2026-05-12`** — original F4 README phase pointer
    drift sweep + `tests/architecture/test_readme_phase_pointer.py`
    regex pin were landed early in the W13-11 push (sub-commits 8 +
    12) so the README sweep stays paired with the banner-cascade
    fix-up. W13-13 elde kalan iş = worker-start cancel-race CAS only.
- W13 close-out PR `week13 → main` **BLOCKED** until W13-11/12/13
  GREEN. All chosen §11.10 GOAL pulls (W13-8, W13-9, W13-10) remain
  GREEN; close-out language for W13-1..W13-10 stays literally true at
  sub-iter granularity. The close-gate items are pulled in-window (not
  W14) because they fix bypass surfaces in originally W13-claimed H6 +
  H4 closures. Original §11.10 candidates that remain not-started
  (logger consolidation, run-ID stamping, W8-W12 regression lock-in
  umbrella) iterate into W14.
- **Next phase: W14 — Codex M-class Acceptance + Observability** (staging).
  Scope authored `2026-05-11` in
  [`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md);
  plan source [`REFACTOR_OPTIMIZATION.md §12`](REFACTOR_OPTIMIZATION.md).
  6 sub-iter scoped (`W14-1..W14-6`): BLOCKER scenario-dropout araştırması,
  Codex M-class input validation (M4-M7 + M11), dış yüzey sertleştirme
  (M13 + M14b + U4-U12), correctness/concurrency (analysis-jobs-race +
  evidence-event-kind invariant), §11.10 GOAL devamı (logger consolidation
  - run-ID stamping), W8-W12 regression lock-in umbrella. Entry gate W13
  close-out PR merge'de tetiklenir; stable ID'ler ilk pull'da atanır
  (W11/W12/W13 precedent).

## W13 Status

| ID | Stable item | Status |
|---|---|---|
| W13-1 | `[FOLLOWUP codex-2026-05-10-H6-spoofable-harness-markers]` | closed `2026-05-10`; per-launch HMAC handshake; `make test-local` 1452 -> 1458; architecture 76 -> 79 |
| W13-2 | `[FOLLOWUP codex-2026-05-10-H5-writable-vscode-launcher]` | closed `2026-05-10`; `launch_vscode.sh` root-owned 0750; `make test-local` 1458 -> 1460; architecture 79 -> 81 |
| W13-3 | `[FOLLOWUP codex-2026-05-10-H4-cancel-concurrent-race]` | closed `2026-05-10`; two-phase `cancelling` cancel state + 5 worker poll points; `make test-local` 1460 -> 1467; architecture 81 -> 87 |
| W13-4 | `[FOLLOWUP w13-3-close-pass-cancellation-test-hardening]` | closed `2026-05-11`; behavioral cancellation coverage + runbook fix; `make test-local` 1473 -> 1485; `make test-security` 211 unchanged; architecture 87 unchanged |
| W13-5 | `[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]` | closed `2026-05-11`; Path A recipe-fix (`Makefile:172` `$${API_HOST:-0.0.0.0}`); `make test-local` 1492 → 1498 (+6 passed); architecture 87 → 93; production code untouched |
| W13-6 | `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]` | closed `2026-05-11`; factory-internal redaction at `_bounded_arguments_preview()`; new arch gate `test_arguments_preview_redaction.py` 2/2 ✓ + parametrized regression 5/5 ✓; `make test-local` 1498 → 1505 (+7 passed); architecture 93 → 95; production diff +4 net |
| W13-7 | `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]` | closed `2026-05-11`; bounded scanner for private_key cross-line span in `redact_multiline_secrets()` (16 KB window cap); new timing case 1/1 ✓; `make test-local` 1505 → 1506 (+1 passed); `make test-security` 211 → 212; pre-fix 361 ms → post-fix 1.29 ms (~280× speedup); production diff +45 net |
| W13-8 | `[§11.10 GOAL]` Benign silence fixture 3→5 | closed `2026-05-11` (4/4 sub-commits); 3 new fixture extensions (snippet/keybinding/cmd) authored under `extensions/` + 3 baseline activation reports + helpers/baselines registration; `tests/security/test_benign_silence.py` 5/5 ✓ (RED 3 skips removed); `make test-local` 1514 passed / 7 skipped / 8 deselected; `make test-security` 212 → 215 (+3 passed); `tests/architecture/` 105 unchanged; production code zero diff |
| W13-9 | `[§11.10 GOAL]` `.env` gitignore regression test | closed `2026-05-11`; new architecture gate `tests/architecture/test_env_gitignore.py` 10/10 ✓ (.env literal + *.env wildcard + virtualenv dirs + !.env.example negative exception + template presence via `git check-ignore --no-index`); `make test-local` 1509 → 1519 collected (+10 passed); `tests/architecture/` 95 → 105 collected (+10 passed); production code untouched (`.gitignore` already correct) |
| W13-10 | `[§11.10 GOAL]` Stale singleton-lock recovery integration test | closed `2026-05-11`; 2 new integration cases in `tests/executor/test_reset_state.py` 13/13 ✓ (full 3-lock-held → reset → all removed + unrelated preserved; partial 2-of-3-held → reset → partial removed). Pre-W13-10 unit cases stubbed `cleanup_singleton_locks` inside `reset_executor_state`; W13-10 exercises real cleanup integration; `make test-local` 1519 → 1521 collected (+2 passed); production code untouched |
| W13-11 | `[CLOSE-GATE codex-second-opinion-F1-hmac-python-secret-target-install-race]` close-pass for W13-1 H6 | **closed `2026-05-12` (6/6 sub-commits + 6 post-landing additions in same push: 9a2ba76 self-stamp · doc fix-up · defense-in-depth b/c/a · README regex pin steal-from-W13-13)**; Path A host-side eager-consume + env var passthrough — `workflows/marketplace/analysis_service.py` `_reset_sandbox` → `executor_control.consume_harness_python_secret()` → `_install_extension`; host reads bind-mounted `Path(settings.project.OUTPUT_DIR) / "_extrace_harness_python_secret"` + unlinks, threads through `run_playwright_automation(..., harness_python_secret=...)` → docker exec `-e EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=<hex>` env var. `load_harness_python_secret()` env-priority. `setup_monitor` call unchanged. E4 docker exec argv mask. Final bar: `make test-local` 1521 → **1537** (+16: 10 from 6/6 sub-commits + 6 from defense-in-depth b/c/a + d = 1 + 1 + 2 + 2); `make test-security` 215 unchanged (lane composition; E4 redaction extensions in `tests/security/test_executor_host_error_redaction.py` count toward test-local only); `tests/architecture/` 105 → **112** (+7: 5 from 6/6 + 2 from (d) README regex pin sub-commit 12). W13-12 immediate follow-up required for full fail-closed semantics; merge blocker for `week13 → main` cleared once W13-12/13 also GREEN. |
| W13-12 | `[CLOSE-GATE codex-second-opinion-F2-fail-closed-harness-handshake]` close-pass for W13-1 H6 | **in progress `2026-05-12` (sub-commit 1/5 — design lockdown)**; merge blocker; depends on W13-11 (closed); `ActivationReport.harness_handshake_required: bool` field on internal monitor dataclass ([monitor/types.py:124](../executor/flows/playwright/monitor/types.py)) — W13-1 deseni takipçisi — + `_attempt_has_harness_completion_trace` fail-closed when production handshake required but `expected_nonce` empty. Legacy phase-only branch retained for tests only. Sub-commit map: (1) docs lockdown · (2) RED tests · (3) impl (RED → GREEN) · (4) arch gate · (5) close evidence. |
| W13-13 | `[CLOSE-GATE codex-second-opinion-F3-worker-start-cancel-race-CAS]` close-pass for W13-3 H4 (scope rebased `2026-05-12` — F4 README sweep + regex pin landed in W13-11 push) | **CLOSE-GATE — not started** (Codex Cloud second-opinion `2026-05-11`); merge blocker; Path B worker entry `with_for_update()` snapshot — `cancelling` görürse `finalize_cancelled_analysis_job` + return (W13-3 two-phase symmetric exit). `update_job(status="running")` koşulsuzluğu kapanır. README.md:58 W13 phase pointer drift sweep + `tests/architecture/test_readme_phase_pointer.py` regex pin already landed in the W13-11 push `2026-05-12` (sub-commits 8 + 12) to keep the README sweep paired with its banner-cascade fix-up. |

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
`POST_POC_BACKLOG.md`, keep active W13 mechanics in
`active-work/W13-test-expansion-observability.md`, and W14 staging scope in
`active-work/W14-codex-acceptance-observability.md`.
