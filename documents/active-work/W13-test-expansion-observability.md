# W13 — Test Expansion + Observability (Active Work Tracker)

`Last Updated: 2026-05-12 (W13-11 closed 2026-05-12 (6/6 sub-commits — design+impl+arch gate+regression fix+doc sweep) — Path A host-side eager-consume + env var passthrough; W13-12 in progress 2026-05-12 (sub-commit 1/5 — design lockdown) — `ActivationReport.harness_handshake_required: bool` fail-closed; W13-13 remains CLOSE-GATE not started)`
`Phase: W13 active — CLOSE-GATE HOLD on W13-12 (in progress 1/5) + W13-13 (W13-11 closed)`
`Branch: week13 (single-branch policy precedent; opened 2026-05-10 from cff6455)`
`Owner: ekrem`

> **Trimmed 2026-05-11** alongside the W13-4 close-out documentation sweep: verbose design-rationale prose and per-commit verification minutiae for the closed W13-1..W13-4 sub-commits were lifted out of the active narrative. Stable evidence — sub-commit hashes, deferred follow-ups, test-bar deltas — is retained inline; the full prose remains accessible via `git log` history on the `050317e..01bf761` range.

This is the canonical active work tracker for the W13 Test Expansion +
Observability window. Items receive stable IDs (`W13-1`, `W13-2`, ...)
**at first pull**, not preemptively, per the W11/W12 precedent
(`REFACTOR_OPTIMIZATION.md` §11.10 final paragraph: "tracker is born at
phase entry"). Code comments, tests, and ADR addenda will reference
items by ID — **keep IDs stable** when reorganizing.

This file mirrors the structure of `W11-monitor-lifecycle.md` and
`W12-executor-subpackaging.md`. Slim canonical
`REFACTOR_OPTIMIZATION.md §11.10` carries the entry-conditions block,
goal statement, and current candidate list; full historical detail will
move to `archive/plans/REFACTOR_OPTIMIZATION_full_<date>.md §11.10` as
the section ages.

## Status (Quick Glance)

- **W13 active. W13-1..W13-7 are closed — every MEDIUM/HIGH Codex Cloud
  audit acceptance-bar item is now landed.** Entry baseline was
  established `2026-05-10` after W12 merged via PR #18 (`33a0852`).
  Codex Cloud security audit `2026-05-10` was ingested the same day.
- **W13-1 closed `2026-05-10` (5/5 sub-commits).** Codex H6
  spoofable harness markers closed with a per-launch HMAC-SHA256
  handshake. `make test-local` 1452 → 1458; `tests/architecture/`
  76 → 79; `make test-security` 211 unchanged.
- **W13-2 closed `2026-05-10` (4/4 sub-commits).** Codex H5 writable
  VS Code launcher closed by moving `launch_vscode.sh` to
  `root:executor` 0750 plus static and runtime permission gates.
  `make test-local` 1458 → 1460; `tests/architecture/` 79 → 81.
- **W13-3 closed `2026-05-10` (6/6 sub-commits).** Codex H4 cancel
  concurrent race closed with non-terminal `cancelling`, widened
  active-job lock, two-phase finalize, and 5 worker poll points.
  `make test-local` 1460 → 1467; `tests/architecture/` 81 → 87.
- **W13-4 closed `2026-05-11` (8/8 sub-commits).** Cancellation
  lifecycle hardening added behavioral proof over W13-3's AST gates
  and fixed `analysis-job-stuck.md`. Final bar: `make test-local`
  1473 → 1485, `make test-security` 211 unchanged, `tests/architecture/`
  87 unchanged. One Alembic behavioral round-trip case deferred as
  `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]`.
- **W13-5 closed `2026-05-11` (5/5 sub-commits).** dev-lan Makefile
  drift (Codex H3) closed via Path A recipe-fix: `Makefile:172`
  `--host 0.0.0.0` → `--host $${API_HOST:-0.0.0.0}` so
  `API_HOST=… make dev-lan` narrows the uvicorn bind socket
  alongside the settings layer. New architecture gate
  `tests/architecture/test_makefile_dev_recipes.py` 6/6 ✓
  (`dev` + `run` loopback literals, `dev-lan` `EXTRACE_ALLOW_LAN=1`,
  `dev-lan` `API_HOST` override form, `dev-lan` default-to-wildcard
  fallback, `dev-lan` ADR 0007 banner literal).
  `documents/runbooks/lan-exposure.md` §Host-mode drift caveat
  removed. Final bar: `make test-local` 1492 → 1498 collected
  (+6 passed), `make test-security` 211 unchanged,
  `tests/architecture/` 87 → 93. Production code untouched
  (`appcore/`, `workflows/`, `executor/`, `packages/`, `ui/`,
  `alembic/` all zero diff over W13-5 range `1b637a1..HEAD`).
- **W13-6 closed `2026-05-11` (5/5 sub-commits).** Codex M9
  `arguments_preview` redaction extension closed via factory-internal
  redaction at [`_bounded_arguments_preview()`](../../executor/flows/playwright/runtime_capture/extension_host_strace_parse.py):
  the factory now routes its input through
  [`redact_secrets()`](../../packages/analysis_contracts/evidence.py)
  before whitespace-normalize + truncate, so the 3 assignment sites
  (`extension_host_strace_parse.py:60,70,78`) inherit redaction at a
  single chokepoint. New architecture gate
  `tests/architecture/test_arguments_preview_redaction.py` 2/2 ✓
  (`test_arguments_preview_factory_applies_redact_secrets` — AST walk
  confirms the factory body contains a `redact_secrets` Call;
  `test_arguments_preview_assignments_are_redacted` — every
  `arguments_preview` keyword/attribute/subscript assignment under
  `executor/`, `packages/`, `workflows/` routes through one of the
  allowed sources). New regression case
  `tests/executor/test_playwright_extension_host.py::test_parse_strace_event_arguments_preview_redacts_secrets[*]`
  5/5 ✓ (aws, bearer, api_key, db_url, private_key — strace execve line
  with secret literal → `ProcessEvent.arguments_preview` carries
  `[REDACTED:<class>]` placeholder, raw secret substring absent).
  Final bar: `make test-local` 1498 → 1505 collected, **+7 passed**
  (1505 passed, 7 skipped baseline alembic+canary unchanged);
  `make test-security` 211 unchanged; `tests/architecture/` 93 → 95
  passed. Production code diff scoped to
  `executor/flows/playwright/runtime_capture/extension_host_strace_parse.py`
  (+4 net: 1 import + 1 comment + 2 statements in factory body).
- **W13-7 closed `2026-05-11` (5/5 sub-commits).** Codex M1 PEM regex
  DoS closed via bounded scanner for the `private_key` cross-line span
  in [`redact_multiline_secrets()`](../../packages/analysis_contracts/evidence.py):
  the body now routes through `_redact_private_key_bounded()` (linear
  O(L) scan with a 16 KB BEGIN→END window cap) instead of
  `pattern.sub()` on the lazy `(?:.|\n)*?` regex. New timing test
  `tests/platform/security/test_output_signals_redaction.py::test_redact_multiline_secrets_rejects_catastrophic_pem_pattern`
  pins the post-fix latency budget at <100 ms on adversarial input
  (200 BEGIN markers + 1 KB body each + no END). Empirical measurement:
  pre-fix 361 ms → post-fix 1.29 ms (~280× speedup). W12-0's 4 PEM
  regression cases continue to pass (identical replacement semantics).
  Final bar: `make test-local` 1505 → 1506 collected, **+1 passed**
  (1499 passed total, 7 skipped baseline alembic+canary unchanged);
  `make test-security` 211 → 212 (+1 timing case in the security
  lane); `tests/architecture/` 95 unchanged. Production code diff
  scoped to a single file (+45 net lines in `packages/analysis_contracts/evidence.py`:
  4 new constants, 1 new helper, body refactor).
- **W13 acceptance bar cleared.** H3 closed via W13-5, H4 via W13-3,
  H5 via W13-2, H6 via W13-1, M1 via W13-7, M9 via W13-6. No further
  MEDIUM/HIGH Codex acceptance items remain.
- **W13-8 closed `2026-05-11` (4/4 sub-commits).** §11.10 GOAL
  benign silence fixture 3→5 GREEN landed. Three new fixture
  extensions authored under `extensions/`:
  `extrace.fixture-snippet-0.0.1` (declarative `contributes.snippets`,
  zero-scenario profile), `extrace.fixture-keybinding-0.0.1`
  (declarative `contributes.keybindings`, zero-scenario profile),
  `extrace.fixture-cmd-0.0.1` (`onCommand:` activation + `registerCommand`
  handler, activation-enabled profile). Matching baseline activation
  reports added under
  `tests/platform/contracts/fixtures/activation_reports/` (theme-clone
  for snippet/keybinding, chat-clone for cmd).
  [`tests/security/helpers.py:13-32`](../../tests/security/helpers.py)
  `_FIXTURE_REPORTS` extended +3 entries;
  [`tests/platform/contracts/test_analysis_fixture_baselines.py:37-44`](../../tests/platform/contracts/test_analysis_fixture_baselines.py)
  `BASELINE_EXTENSION_FIXTURES` extended +3 entries and
  `expected_activation_event_types` (line 221-233) extended +3 entries
  (snippet/keybinding: `set()`, cmd: `{"onCommand"}`). The 3
  skip-marked RED cases in
  [`tests/security/test_benign_silence.py`](../../tests/security/test_benign_silence.py)
  are now active (5/5 silence assertions ✓).
  [`.gitignore`](../../.gitignore) extended +3 allow rules for the new
  fixture directories (chat/theme pattern preserved);
  [`scripts/reset_extensions.sh`](../../scripts/reset_extensions.sh)
  `KEEP[]` extended +6 entries (3 dirs + 3 `.vsix`).
  Production code untouched (`appcore/`, `workflows/`, `executor/`,
  `packages/`, `ui/`, `alembic/` zero diff). Final bar:
  `make test-local` 1514 passed / 7 skipped / 8 deselected (3 W13-8
  RED skips removed; baseline alembic+canary 7 skips preserved);
  `make test-security` 212 → 215 (+3 passed);
  `tests/architecture/` 105 unchanged.
  **W13 acceptance bar remains cleared** — benign silence is a
  §11.10 GOAL, not an audit acceptance-bar item.
- **W13-9 closed `2026-05-11`.** §11.10 GOAL `.env` gitignore
  regression test landed via new architecture gate
  [`tests/architecture/test_env_gitignore.py`](../../tests/architecture/test_env_gitignore.py)
  (10/10 ✓). Coverage: `.env` literal and `*.env` wildcard rules
  pinned across repo-root and nested paths (5 cases); virtualenv
  directory rules (`.venv/`, `env/`, `venv/`) pinned via
  inside-the-dir paths (3 cases); `.env.example` negative exception
  pinned (1 case); `.env.example` template presence pinned (1
  case). Underlying `.gitignore` was already correct — pre-W13-9
  there was no architecture gate locking the invariant, so a future
  edit to `.gitignore` lines 5-8 / 45-46 could have landed silently.
  Production code untouched (`appcore/`, `workflows/`, `executor/`,
  `packages/`, `ui/`, `alembic/` zero diff). Final bar:
  `make test-local` 1509 → 1519 collected, +10 passed;
  `tests/architecture/` 95 → 105 collected, +10 passed;
  `make test-security` 212 unchanged.
- **W13-10 closed `2026-05-11`.** §11.10 GOAL stale singleton-lock
  recovery integration test landed via 2 new cases in
  [`tests/executor/test_reset_state.py`](../../tests/executor/test_reset_state.py)
  (13/13 ✓). Pre-W13-10 state: 3 unit cases covered
  `cleanup_singleton_locks()` in isolation, and 1 orchestration case
  asserted call ordering but stubbed `cleanup_singleton_locks` —
  neither exercised the integration (real cleanup inside
  `reset_executor_state()` with held lock files on disk). New cases:
  `test_reset_executor_state_recovers_from_held_singleton_locks_end_to_end`
  (full 3-lock-held → reset → all 3 removed + unrelated file
  preserved) and `test_reset_executor_state_recovery_handles_partial_singleton_lock_set`
  (2-of-3 held → reset → 2 removed + summary reflects partial count).
  Production code untouched (`appcore/`, `workflows/`, `executor/`,
  `packages/`, `ui/`, `alembic/` zero diff). Final bar:
  `make test-local` 1519 → 1521 collected, +2 passed;
  `tests/architecture/` 105 unchanged; `make test-security` 212
  unchanged.
- **CLOSE-GATE HOLD `2026-05-11`.** Codex Cloud second-opinion review
  on `week13` surfaced 3 P1 close-pass items that REOPEN portions of
  the W13-1 H6 and W13-3 H4 close claims. Close-out PR `week13 → main`
  is held until W13-11/12/13 are GREEN. The acceptance-bar closure
  language (W13-1..W13-7) and §11.10 GOAL closure language (W13-8 /
  W13-9 / W13-10) remain literally true at sub-iter granularity, but
  the **W13-end overall exit criteria** (§11.14) require the close-pass
  fixes before merge. The 3 items are pulled as W13 sub-iters (not
  W14) because they directly fix bypass surfaces in the originally
  W13-claimed H6 + H4 closures — keeping them in-window preserves
  audit-trail integrity (history shows the H6/H4 work as a single
  iteration family rather than a deferred follow-up).
- **W13-11 closed `2026-05-12` (6/6 sub-commits).** Codex F1
  HMAC python secret target-install race close-pass for W13-1 H6.
  Path A host-side eager-consume + env var passthrough landed:
  `workflows/marketplace/analysis_service.py::execute_analysis_request`
  now calls `executor_control.consume_harness_python_secret()` between
  `_reset_sandbox()` and `_install_extension()`, reads bind-mounted
  `Path(settings.project.OUTPUT_DIR) / "_extrace_harness_python_secret"`
  with mode guard (0600 expected) + unlinks, holds string in host
  memory, threads through `run_playwright_automation(..., harness_python_secret=...)`
  → docker exec `-e EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=<hex>` env var
  for the entrypoint container. `load_harness_python_secret()` is now
  env-priority (env first, legacy file fallback for test compat;
  defense-in-depth file unlink even on env hit). `setup_monitor` call
  site at `dispatch.py:129` unchanged — W13-1 arch gate intact. E4
  docker exec argv mask added (`_mask_harness_secret_in_message`
  scrubs `EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=<hex>` from
  ExecutorError messages). Final bar: `make test-local` 1521 → 1531
  (+10: 5 behavioral + 3 reconciliation + 1 redaction + 1 new cancel-poll-point);
  `make test-security` 215 unchanged (lane composition excludes new E4
  redaction case in `tests/security/test_executor_host_error_redaction.py`);
  `tests/architecture/` 105 → 110 (+5: 3 W13-11 sequence/threading invariants
  - 2 collateral arch additions). W13-12 (fail-closed
  handshake) immediate follow-up required for full fail-closed semantics;
  W13-11 alone landed worst case = pre-W13-11 status quo (no new
  regression). Per-Item Detail block below preserved as closure
  evidence.
- **W13-12 — Fail-closed harness handshake (close-pass for W13-1).**
  Codex F2:
  [`reconciliation.py:137-146`](../../executor/flows/playwright/health/reconciliation.py:137)
  falls back to legacy phase-only check when `expected_nonce` is
  empty; [`load_harness_python_secret()`](../../executor/flows/playwright/health/reconciliation.py:51)
  returns `""` on any read failure (FileNotFoundError, OSError, perm
  glitch, race with reset_state). Production paths must fail closed
  when handshake is required but missing. Fix direction: add explicit
  `ActivationReport.harness_handshake_required: bool` flag (default
  True at production construction site `setup_monitor` after W13-11
  lands, False in pre-W13-1 unit-test construction); modify
  `_attempt_has_harness_completion_trace` so empty `expected_nonce`
  AND `harness_handshake_required=True` returns False (no verification).
  Legacy phase-only branch retained for tests only.
- **W13-13 — Worker-start cancel-race CAS (close-pass for W13-3; F4 README
  sweep + regex pin moved to W13-11 push `2026-05-12`).**
  Codex F3:
  [`run_analysis_job`](../../workflows/marketplace/analysis_service.py:194)
  unconditionally calls `update_job(status="running")` as its first
  action. If a user cancels between `reserve_job` returning and the
  worker thread entering `run_analysis_job`, `cancel_analysis_job`
  ([`lifecycle.py:128-156`](../../appcore/storage/crud_ops/analysis_jobs/lifecycle.py:128))
  atomically takes the row from `queued` to `cancelling`, then the
  worker's unconditional `running` write regresses the cancel intent
  and the cancel signal is lost. Fix direction (Path B):
  `with_for_update()` snapshot in worker entry before any state
  transition; if `cancelling` or terminal observed → call
  `finalize_cancelled_analysis_job` and return (W13-3 two-phase
  symmetric exit). Path A alternative: add `expected_status` parameter
  to `update_job` for compare-and-set (`UPDATE … WHERE status='queued'`),
  worker returns on 0-row-affected. **Scope rebased `2026-05-12`**:
  Codex F4 README drift ([`README.md:58`](../../README.md:58) stalled
  at "W13-1..W13-4 closed, W13-5 expected") sweep + paired
  `tests/architecture/test_readme_phase_pointer.py` regex pin both
  landed early in the W13-11 push (sub-commits 8 + 12) so the sweep
  stays paired with its banner-cascade fix-up. W13-13 elde kalan iş =
  worker-start cancel-race CAS only.
- **Entry gate met:**
  - W12 closed and merged via PR #18 (`33a0852`); close commit
    `e8a9926`.
  - `make check-all` ✅ green at the W12 close commit (post-Codex-fix
    re-run, postgres_test container active).
  - `make test-local` 1452 passed / 6 skipped / 6 deselected / 75
    warnings.
  - `make test-security` 211 passed / 32 warnings.
  - `tests/architecture/` 76 passed / 2 deselected.
  - Live-scan bitwise-equal baseline on
    `ms-python.python@2026.5.2026050801` (job IDs
    `6fab298e81a14bf8a7a557a13953e57b` /
    `e5e33ec6e34f4993b795664d83e25fd4`); recorded in the archived
    `W12-close-acceptance-completed-2026-05-10.md` §3.4.

## Entry Conditions Met (mirroring `REFACTOR_OPTIMIZATION.md` §11.10)

- [x] W12 closed and merged to `main` via `week12 → main` PR.
  (`PR #18` — `33a0852`.)
- [x] `make check-all` green at the W12 close baseline (commit
  `e8a9926`); test-local 1452 / test-security 211.
- [x] `tests/architecture/` 76 cases green; W12 ratchet gates pinned:
  `test_executor_playwright_flat_file_count_limit` (W12-1, ≤10 flat),
  `test_runner_main_under_loc_budget` (W12-4, ≤200 LoC for `main()`),
  `test_runtime_capture_extension_host_stays_a_thin_facade` and
  `test_runtime_capture_extension_host_reexports_match_canonical_modules`
  (W12-5 facade invariants),
  `test_body_preview_assignments_are_redacted` (W12-5 redaction
  defense), and
  `test_all_runtime_dockerfiles_pin_base_images_by_digest`
  (ADR 0002 §4 trust, `ui/` included).
- [x] Live-scan bitwise-equal baseline established on
  `ms-python.python@2026.5.2026050801`; W13 split candidates may use
  this as the pre-refactor reference.
- [x] W13 lane document (this file) created at W13 official open per
  W11/W12 precedent.

## Goal (per `REFACTOR_OPTIMIZATION.md` §11.10)

Benign silence fixture 3→5; stale singleton-lock + `.env` gitignore
regression tests; `extrace.executor.*` logger consolidation; run-ID
stamping; W8-W12 regression lock-in.

Beyond the original §11.10 goal text, three audit passes surfaced
additional candidates (see "Candidate Items" below): `2026-05-07`
internal audit, `2026-05-09` Codex review, and `2026-05-10` Codex
Cloud security scan. The `2026-05-10` audit pulled four HIGH findings
and two MEDIUM findings into the W13 acceptance bar. H4/H5/H6 are now
closed via W13-3/W13-2/W13-1; H3, M1, and M9 remain open W13
acceptance-bar work.

## Candidate Items (stable IDs assigned at first pull)

Pulled from `POST_POC_BACKLOG.md` §11.10 candidates and
`REFACTOR_OPTIMIZATION.md` §11.10. Status column reflects current
backlog state; `W13-N` IDs filled in as items move from "not started"
to "in progress".

Items prefixed `[§11.10 GOAL]` are sourced from the §11.10 goal
paragraph (`REFACTOR_OPTIMIZATION.md` lines 365-367) and have no
`[FOLLOWUP …]` ID in `POST_POC_BACKLOG.md`; the remaining `[FOLLOWUP
…]` rows are audit-pass candidates (`2026-05-07` / `2026-05-09` /
W12-close Codex). Initial-state evidence for the GOAL rows recorded
`2026-05-10` via Explore survey: see "Per-Item Detail" once the first
GOAL row is pulled.

| ID | Item | Lane | Status |
|---|---|---|---|
| TBD | `[FOLLOWUP scenario-accountant-conservation-split]` (`monitor/scenario_accountant.py` 648 LoC; W11-1 lifecycle split pattern) | `[executor-runtime]` | not started |
| TBD | `[FOLLOWUP evidence-event-kind-raw-context-invariant]` (`EvidenceEvent.kind` ↔ `raw_context.event_class` Pydantic v2 `model_validator`) | `[security-detection]` | not started |
| TBD | `[FOLLOWUP ui-raw-context-discriminator-parity]` (TS `event_class` literal generation + 5 legacy adapter fixups) | `[ui]` `[contracts]` | not started |
| TBD | `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]` (extend `tests/architecture/test_absolute_binary_paths.py` for `tshark`/`strace`/`inotifywait`) | `[security-detection]` | not started |
| **W13-8** | `[§11.10 GOAL]` Benign silence fixture 3→5 | `[security-detection]` | **closed `2026-05-11` (4/4 sub-commits); 3 new fixture extensions (snippet/keybinding/cmd) + baseline JSONs + helpers/baselines registration; `tests/security/test_benign_silence.py` 5/5 ✓; `make test-local` 1514 passed / 7 skipped (RED 3 skips removed); `make test-security` 212 → 215 (+3 passed); `tests/architecture/` 105 unchanged; production code zero diff** |
| **W13-10** | `[§11.10 GOAL]` Stale singleton-lock recovery integration test (`cleanup_singleton_locks()` at `executor/flows/playwright/reset_state.py:131-145`; existing 3 unit cases in `tests/executor/test_reset_state.py:70-168` cover cleanup mechanics but not the lock-held → reset → recovery scenario; orchestration case at lines 223-270 stubs `cleanup_singleton_locks` and asserts only call ordering. W13-10 adds 2 integration cases that exercise the real cleanup inside `reset_executor_state()`: full-set held + partial-set held) | `[executor-runtime]` | **closed (1/1 commit, 2026-05-11)** |
| **W13-9** | `[§11.10 GOAL]` `.env` gitignore regression test (`.gitignore` already pins `*.env` / `.env` / `!.env.example` and `.env.example` is tracked; no architecture gate existed pre-W13-9; new `tests/architecture/test_env_gitignore.py` 10/10 ✓ via `git check-ignore`) | `[security-detection]` | **closed (1/1 commit, 2026-05-11)** |
| TBD | `[§11.10 GOAL]` `extrace.executor.*` logger consolidation (discovery first — initial grep found zero `getLogger("extrace*` / `getLogger('extrace*` matches; W13-6 may scope out if no fragmentation exists, or pull canonical naming if any is found) | `[platform-storage]` | **deferred to W14+** (not started at W13 close-out cut-off `2026-05-11`; W12 PR #18 pattern) |
| TBD | `[§11.10 GOAL]` Run-ID stamping (job_id exists at `appcore/storage/model_defs/analysis_job.py` and `appcore/contracts/schema_defs/analysis_jobs.py:16` but is not propagated as a correlation identifier through log records, `EvidenceEvent`, or DB row chains; multi-lane plumbing) | `[platform-storage]` `[executor-runtime]` `[security-detection]` | **deferred to W14+** (not started at W13 close-out cut-off `2026-05-11`; W12 PR #18 pattern) |
| TBD | `[§11.10 GOAL]` W8-W12 regression lock-in (umbrella for any regression coverage missing on W8-W12 landed work; concrete sub-items pulled from `POST_POC_BACKLOG.md` deferrals as W13 progresses; close-pass evaluates which followups are bundled vs deferred to W14+) | (multi) | **deferred to W14+** (not started at W13 close-out cut-off `2026-05-11`; W12 PR #18 pattern) |
| **W13-5** | `[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]` (`Makefile:170-172` `dev-lan` hard-codes `--host 0.0.0.0` while `runbooks/lan-exposure.md:82-87` documents `API_HOST` override; `tests/architecture/test_default_bindings.py` covers settings layer only — no Makefile gate. Path A recipe-fix landed: `--host $${API_HOST:-0.0.0.0}` + new `tests/architecture/test_makefile_dev_recipes.py` regression gate + lan-exposure §Host-mode drift caveat removal) | `[security-detection]` `[platform-storage]` | **closed (5/5 sub-commits, 2026-05-11)** |
| **W13-4** | `[FOLLOWUP w13-3-close-pass-cancellation-test-hardening]` (W13-3 6 architecture gates pin AST invariants only — no behavioral coverage exists for: 5 poll-point raise paths actually firing inside `execute_analysis_request`, cancel↔complete DB-level race serialization under `with_for_update()`, stuck-`cancelling` boot_id recovery via `recover_interrupted_jobs` (design intent: `cancelling`→`failed` by boot_id mismatch), Alembic `c8a2d4e91f5b` upgrade/downgrade data motion, `run_analysis_job` exception handler driving `finalize_cancelled_job` on both `AnalysisCancelledError` and `is_job_cancelled`-true hard-error paths, finalize negative (absent + already-cancelled idempotency). Plus runbook drift: `documents/runbooks/analysis-job-stuck.md:42` 4-status literal stale post-W13-3, no playbook for stuck-cancelling) | `[platform-storage]` `[executor-runtime]` | **closed (8/8 sub-commits, 2026-05-11)** |
| **W13-3** | `[FOLLOWUP codex-2026-05-10-H4-cancel-concurrent-race]` (cross-ref `[FOLLOWUP simulation-progress-cancel]` 5 sub-items already in POST_POC; `cancelled` was terminal in `appcore/storage/crud_ops/analysis_jobs/lifecycle.py:41` so `reserve_job()` released the lock immediately; cancellation polled only in heartbeat. Option A: `cancelling` non-terminal state added to `ACTIVE_ANALYSIS_JOB_STATUSES` + partial unique index, two-phase cancel via new `finalize_cancelled_analysis_job` helper, `_raise_if_cancelled` poll points at 5 hot-zones) | `[executor-runtime]` `[platform-storage]` | **closed (6/6 sub-commits, 2026-05-10)** |
| **W13-2** | `[FOLLOWUP codex-2026-05-10-H5-writable-vscode-launcher]` (`executor/container/Dockerfile:121-128` chowns `launch_vscode.sh` to `executor:executor` mode 755 — analyzed extension can overwrite, persists across resets via `reset_state.py`. Moved to `chown root:executor` + `chmod 0750`; root-own + executor read+exec only) | `[executor-runtime]` `[security-detection]` | **closed (3/3 sub-commits, 2026-05-10)** |
| **W13-1** | `[FOLLOWUP codex-2026-05-10-H6-spoofable-harness-markers]` (`executor/flows/playwright/health/reconciliation.py:18-50` accepts `[extrace-harness] {json}` from target-writable Extension Host log stream as proof of `automation_trace`; no auth/nonce. Forged `phase:"complete"` markers can satisfy verification → forged clean reports. Monitor-owned side channel (executor-only writable file path) or HMAC nonce stamped in `start.sh` and unavailable to target) | `[executor-runtime]` `[security-detection]` | **closed (5/5 sub-commits, 2026-05-10)** |
| **W13-7** | `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]` (`packages/analysis_contracts/evidence.py:106-121` `redact_multiline_secrets()` private_key regex unanchored + lazy cross-line span `(?:.\|\n)*?` → catastrophic backtracking on many unmatched BEGIN markers; W12-0 added the redaction itself, this is a follow-up DoS vector. Bounded scanner: manual linear pass with 16 KB BEGIN→END window cap — preserves semantic for real PEM keys, prevents pathological scan on adversarial Extension-Host stdout. Empirical 361 ms → 1.29 ms on adversarial input; W12-0 PEM regression intact) | `[security-detection]` | **closed (5/5 sub-commits, 2026-05-11)** |
| **W13-6** | `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]` (W12-5 `tests/architecture/test_network_body_preview_redaction.py` covers `request_body_preview` / `response_body_preview` only; `executor/flows/playwright/runtime_capture/extension_host_strace_parse.py:60,70,78` assigns `arguments_preview` without `redact_secrets()`. Replica architecture gate (new `tests/architecture/test_arguments_preview_redaction.py` — factory body invariant + routing invariant) + factory-internal redaction inside `_bounded_arguments_preview()` so 3 call sites stay GREEN unchanged + parametrized regression covering 5 secret classes) | `[security-detection]` `[executor-runtime]` | **closed (5/5 sub-commits, 2026-05-11)** |
| TBD watch | `[FOLLOWUP planner-selection-readability-audit]` (`analysis_planner/selection.py` 497 LoC; refactor only when activation family or planner bug triggers) | `[security-detection]` | watching |
| TBD watch | `[FOLLOWUP attribution-links-build-evidence-bundle-density]` (`attribution/links.py` 601 LoC; reassess after evidence-event-kind invariant lands) | `[executor-runtime]` | watching |
| TBD watch | `[FOLLOWUP execute-attempt-rebloat-watch]` (`stimulus/attempts.py::execute_attempt` chain growth; refactor only when new action family added) | `[executor-runtime]` | watching |
| TBD watch | `[FOLLOWUP dispatch-execution-rebloat-watch]` (`entrypoint/dispatch.py` 402 LoC W12-4 ratchet; add `test_dispatch_execution_under_loc_budget` only after concrete bloat) | `[executor-runtime]` | watching |
| ~~**W13-11**~~ | `[CLOSE-GATE codex-second-opinion-F1-hmac-python-secret-target-install-race]` close-pass for W13-1 H6 (Path A host-side eager-consume — `workflows/marketplace/analysis_service.py::execute_analysis_request` calls `executor_control.consume_harness_python_secret()` between `_reset_sandbox()` and `_install_extension()`, reads bind-mounted `Path(settings.project.OUTPUT_DIR) / "_extrace_harness_python_secret"` + unlinks, threads through `run_playwright_automation(..., harness_python_secret=...)` → docker exec `-e EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=<hex>` env var. `load_harness_python_secret()` env-priority. `setup_monitor` call unchanged. E4 docker exec argv mask.) | `[executor-runtime]` `[security-detection]` | **closed `2026-05-12`** (6/6 sub-commits) |
| **W13-12** | `[CLOSE-GATE codex-second-opinion-F2-fail-closed-harness-handshake]` close-pass for W13-1 H6 (`reconciliation.py:137-146` legacy phase-only fallback when `expected_nonce` empty; `load_harness_python_secret()` returns `""` on any read failure → production sessizce spoofable mode'a düşer. Fix: `ActivationReport.harness_handshake_required: bool` ayrımı; production paths empty `expected_nonce` + handshake required → False döndürür, harness verification unconfirmed.) | `[security-detection]` `[executor-runtime]` | **in progress `2026-05-12` (sub-commit 1/5 — design lockdown)**; merge blocker for `week13 → main` cleared once W13-12/13 GREEN |
| **W13-13** | `[CLOSE-GATE codex-second-opinion-F3-worker-start-cancel-race-CAS]` close-pass for W13-3 H4 (scope rebased `2026-05-12` — F4 README sweep + regex pin landed in W13-11 push) (`analysis_service.run_analysis_job:194` unconditional `update_job(status="running")` cancelling üzerine yazar → kullanıcı cancel sinyali kaybolur. Path B: worker entry'sinde `with_for_update()` snapshot; `cancelling`/terminal görürse `finalize_cancelled_analysis_job` + return — W13-3 two-phase symmetric exit. README.md:58 `W13-1..W13-4 closed, W13-5 expected` drifti W13-11 push sub-commit 8'de sweep edildi + `tests/architecture/test_readme_phase_pointer.py` regex pin sub-commit 12'de landed.) | `[platform-storage]` `[executor-runtime]` | **CLOSE-GATE — not started** (Codex Cloud second-opinion `2026-05-11`; merge blocker for `week13 → main`) |

## Per-Item Detail

Pattern from `W12-executor-subpackaging.md`: each `W13-N` block
records landing date, commit hashes, module locations new/modified,
LoC changes, tests added/modified at real module import paths,
live-scan validation if applicable.

### W13-1 — Spoofable harness markers (Codex H6)

`Status: closed 2026-05-10 (5/5 sub-commits)` ·
`Source: [FOLLOWUP codex-2026-05-10-H6-spoofable-harness-markers]` ·
`Lane: [executor-runtime] [security-detection]`

**Goal.** `automation_trace` doğrulaması bugün `[extrace-harness]
{phase:"complete"}` markers'ına auth-suz güveniyor. Markers target-writable
Extension Host stdout'undan akıyor (target extension ve harness aynı
`executor:executor` UID'sinde aynı Extension Host process'inde) →
forged "complete" marker → forged clean report. W13-1 nonce-based
auth ekleyerek bu vector'ü kapatır.

**Critical files.**

- `executor/flows/playwright/health/reconciliation.py:18-50` — `_HARNESS_MARKER_RE`, `_harness_trace_records_by_attempt`, `_attempt_has_harness_completion_trace` (`phase=="complete"` tek kontrolü, line 47-49).
- `executor/flows/harness_extension/extension.js:144-179` — `extrace.harness.runCurrentStimulus` command callback; `emitHarnessMarker("complete", {…})` line 162-167.
- `executor/flows/harness_extension/markers.js:15-23` — `emitHarnessMarker` uses `console.log("[extrace-harness] " + JSON.stringify({kind:"stimulus", phase, …details}))`. Auth field eklenecek nokta burası.
- `executor/flows/harness_extension/markers.js:38-52` — `writeHarnessReadyMarker` mevcut atomik file-handshake (W8-0). Sub-commit 3 secret loading bunu emsal alacak.
- `executor/flows/harness_extension/package.json:11-14` — `activationEvents: ["onStartupFinished"]` → harness target VSIX install'dan önce activate olur.
- `executor/container/start.sh:25-27, 116-127` — `EXTRACE_EPOCH_RUN_ID` üretimi + VS Code launch noktası; secret üretimi line 28 civarına eklenecek.
- `executor/container/Dockerfile:97-130` — `USER executor` (line 130). `/run/extrace` dizini için yeni RUN satırı eklenecek (sub-commit 3).
- `tests/executor/test_playwright_health_reconciliation.py:290-364` — mevcut harness test'leri (sadece happy-path + missing-marker; forged scenario yok).

**Discovery — Race Window Analysis (analytical, 2026-05-10).**

Container ölçümü yapılmadı; race window'un Python orchestration
sırası tarafından enforce edildiği analitik olarak doğrulanır:

| Phase | Aktör | Aksiyon | Secret durumu |
|---|---|---|---|
| A | `start.sh` (executor UID, container PID 1) | Container boot, `EXTRACE_EPOCH_RUN_ID` export, VS Code launch (line 116-127) | Secret üretilir + dosyaya yazılır (sub-commit 3 ekleyecek). Target extension dosyada/diskte yok. |
| B | VS Code Extension Host | `onStartupFinished` activation event | Harness `activate()` çağrılır. Target extension hâlâ disk'te yok. |
| C | Harness `extension.js:53-204` | `activate()` çalıştırır, `writeHarnessReadyMarker()` ile `READY_PATH`'e yazar | Harness secret dosyasını **read + unlink** eder (sub-commit 3). Target hâlâ disk'te yok. |
| D | Python (host) | `_ensure_harness_ready_with_recovery()` ile READY_PATH polling | Python kendi secret kopyasını okur (orchestration). Target VSIX hâlâ install edilmemiş. |
| E | Python | `install_extension(target_vsix)` | Target extension diske eklenir. Secret dosyaları zaten silinmiş. |
| F | VS Code Extension Host | Target extension `activate()` (kendi `activationEvents`'ine göre) | Target attempt `node:fs.readFile("/run/extrace/harness-secret")` → `ENOENT`. Secret hafızada sadece harness'ta + Python'da. |

**Bulgu:** `installExtension`'ın `harness ready marker` sonrası
çağrılması Python orchestration tarafında deterministik. Race window
**saniyeler mertebesinde** (VS Code init + Extension Host start +
harness activate ≈ 1-3 sn; Python install_extension RPC roundtrip ≈
hundreds of ms). Dolayısıyla harness'ın secret dosyasını unlink
etmesi ile target'in attach etmesi arasında **sıralı garanti** var.

**Same-UID limit kabul edildi:** `executor:executor` user her ikisini
çalıştırır; mode 0400/0600 dosya izinleri target'a karşı korumaz.
Korumanın temeli **temporal isolation** (dosya silinmiş olduğu için
target erişemez), **path mode izolasyonu değil**. Bu plan'ın
güvenliği için kritik bir invariant: secret dosyası MUTLAKA target
activate olmadan unlink edilmeli.

**Design Decision Locked-In: Option C (file-based ephemeral handshake).**

| Boyut | Karar |
|---|---|
| Secret nereden? | `start.sh` `head -c 32 /dev/urandom \| od -An -tx1 \| tr -d ' \n'` (32 byte hex, 64-char string). EXTRACE_EPOCH_RUN_ID'ye ek; ondan farklı. |
| Container'da nereye yazılır? | `/run/extrace/harness-secret` mode 0400 owned by executor (aynı UID; izin temporal değil dizin yapısal — sub-commit 3 detayı). |
| Python'a nasıl ulaşır? | İkinci dosya `/results/_harness_python_secret` mode 0600 owned by executor; Python `_ensure_harness_ready_with_recovery` içinde READY marker poll'üne paralel okur, **belleğe alır, dosyayı unlink eder.** Python install_extension'ı bu adımdan sonra çağırır. |
| Harness'ta nereye gider? | `extension.js` `activate()` başında `_HARNESS_NONCE_SECRET` constant; sync read + sync unlink. Harness extension dışında bir yerde tutulmaz. Memory-only. |
| Marker auth nasıl? | `emitHarnessMarker(phase, details)` payload'ına `nonce: HMAC-SHA256(canonical_json(details + phase + attempt_id), _HARNESS_NONCE_SECRET).hex()` ekler. Python tarafı aynı HMAC'i hesaplayıp eşleştirir. |
| Stale marker rejection? | Mevcut `epoch_run_id` field korunur (W8-0 kontratı, additive). HMAC computation `epoch_run_id`'yi de input'a alır → cross-container replay attack bağışıklığı. |

**Ayrı bir karar:** Env var path KULLANILMAYACAK (target `process.env`
okuyabildiği için). Sub-commit 3 NO env var injection.

**Out-of-scope:**

- M5 (`executor/host.py:62` docker exec env propagation) bu plan
  tarafından unblock edilmez ama bağımlı değildir; W14 backlog'da
  kalır.
- Target extension UID ayırımı (Option A-strict) major refactor;
  W14+'a iter.

**Sub-commit Roadmap (5 commits — all landed).**

| # | Commit | Touch | Status |
|---|---|---|---|
| 1 | `c7a9ca7` docs(W13-1): assign stable ID + lock in Option C handshake design | Bu Per-Item Detail bloğu + Candidate Items table | ✅ landed |
| 2 | `f31c820` test(W13-1): RED precursor for harness marker auth (forged-marker rejection) | `tests/executor/test_playwright_health_reconciliation.py` 3 yeni `@pytest.mark.skip` test | ✅ landed |
| 3 | `ee7c8fb` feat(W13-1): nonce generation + harness HMAC handshake | `Dockerfile` (`/run/extrace`), `launch_vscode.sh` (secret üretimi), `constants.js`/`extension.js`/`markers.js` (read+unlink+HMAC) | ✅ landed |
| 4 | `2996856` feat(W13-1): reconciliation HMAC verifier + RED → GREEN | `reconciliation.py` (`load_harness_python_secret` + `_verify_harness_marker_signature` + entegrasyon), `monitor/types.py` (`expected_harness_nonce` field), `dispatch.py` (setup_monitor secret stamp), 3 RED test'in skip'i kaldırıldı | ✅ landed |
| 5 | `6a80a87` test(W13-1): architecture gate + close evidence | `tests/architecture/test_harness_marker_auth.py` (2 AST gate), lane tracker close evidence, `REFACTOR_STATUS.md` update | ✅ landed |
| 5+ | pre-push close-out: `setup_monitor` wiring gate | `tests/architecture/test_harness_marker_auth.py::test_setup_monitor_loads_and_stamps_harness_python_secret` (3rd AST gate); doc drift fixes across `POST_POC_BACKLOG.md`, `REFACTOR_OPTIMIZATION.md` §11.10, `REFACTOR_STATUS.md`, this lane tracker | ✅ landed |

**Sub-commit 5 close evidence (bu commit).**

- [x] Architecture gates landed: `test_attempt_has_harness_completion_trace_calls_verifier`, `test_reconcile_event_attempts_threads_expected_harness_nonce`, ve pre-push eklenen `test_setup_monitor_loads_and_stamps_harness_python_secret` — `tests/architecture/` 76 → 79. Üçüncü gate, `dispatch.setup_monitor`'ün `load_harness_python_secret()` çağrısı + `report.expected_harness_nonce` atamasını yitirmesini engeller; aksi takdirde reconciliation sessizce legacy phase-only check'e düşer ve H6 tekrar açılır.
- [x] `make test-local` 1452 → 1458 passed / 6 skipped / 6 deselected (3 W13-1 RED→GREEN reconciliation cases + 3 W13-1 AST gates; architecture testleri `pytest -v` collection'ında zaten test-local'a dahil).
- [x] `make test-security` 211 passed unchanged (verifier reconciliation-side defense; security suite fixture-side rules test eder, büyümedi — semantic OK).
- [x] `tests/architecture/` 76 → 79 (`test_harness_marker_auth.py` × 3 gate).
- [x] **Production smoke (in-container, 2026-05-10):** Container rebuild + restart sonrası
      - `/run/extrace/` boş (harness extension consume + unlink etti — temporal isolation invariant ✓)
      - `/results/_extrace_harness_python_secret` 64-char hex (mode 0600, Python orchestration için hazır)
      - `python3 -c "from executor.flows.playwright.health.reconciliation import _verify_harness_marker_signature, load_harness_python_secret; ..."` smoke 6/6:
        - secret loader 64-char hex okudu, dosyayı sildi ✓
        - valid signature accepted ✓
        - forged signature rejected ✓
        - empty secret all-rejects (fail-closed) ✓
- [x] **Live-scan delta (`e3e729c7e444` post-sub-commit-3 vs baselines):**
      `ms-python.python@2026.5.2026050801` üzerinde 4 tarama bitwise-equal:
      `6fab298e81a1` (W12 close) / `e5e33ec6e34f` (W12 close post-Codex)
      / `f1f2e4813b67` (pre-W13-1, W13 lane açık) / `e3e729c7e444`
      (post-sub-commit-3, HMAC injection live). Hepsi: 21 attempt /
      12 verified / 9 attempted_only / 5 harness attempts attempted_only
      / signal_summary level=needs_review score=28.
      **Semantic-delta:** sub-commit 4 (Python verifier) sonrası ms-
      python.python harness attempts hâlâ `harness_verification_unconfirmed`
      olur çünkü harness completion trace baseline'da zaten emit
      edilmiyor (target Language Model Tool API'sini resolve edemiyor —
      §11.10 GOAL benign silence fixture work'ünde adreslenebilir). Bu
      yüzden post-sub-commit-4 live-scan da bitwise-equal beklenir.
      Davranışsal değişiklik gözlenmesi için harness completion trace
      üreten bir target (`extrace.fixture-chat-0.0.1` veya benzeri)
      gerekecek — sub-commit 5 close-bar bunu gerektirmez (close-
      acceptance bar §3 "or explicit semantic-delta documentation").
- [x] **Threat model kapsama özeti.** Eskiden: `console.log("[extrace-harness] {phase:\"complete\"}")` yazan target → forged clean report.
      Şimdi: target `process.env`'de secret yok (env unset edildi); `/run/extrace/harness-secret` harness boot'ta unlinked + same-UID temporal protection (target VSIX henüz yüklenmediği için target erişemiyor); `/results/_extrace_harness_python_secret` Python `setup_monitor` tarafından consume + unlinked install_extension öncesi. HMAC-SHA256 rejection fail-closed; mismatched signature → `attempted_only` + `harness_verification_unconfirmed`. Test ağı: 3 architecture gate (AST invariant — verifier call, nonce thread, `setup_monitor` wiring) + 3 reconciliation regression (forged-without-nonce / forged-with-invalid-nonce / genuine).
- [x] W12 ratchet gate'leri korundu (W13-1 hiçbirini kırmadı):
      `test_executor_playwright_flat_file_count_limit` ✓,
      `test_runner_main_under_loc_budget` ✓,
      `test_runtime_capture_extension_host_*` (W12-5) ✓,
      `test_body_preview_assignments_are_redacted` ✓,
      `test_all_runtime_dockerfiles_pin_base_images_by_digest` ✓.

### W13-2 — Writable VS Code launcher (Codex H5)

`Status: closed 2026-05-10 (4/4 sub-commits)` ·
`Source: [FOLLOWUP codex-2026-05-10-H5-writable-vscode-launcher]` ·
`Lane: [executor-runtime] [security-detection]`

**Goal.** `executor/container/Dockerfile` `launch_vscode.sh`'i
`executor:executor` 0755 ile bırakıyordu. `reset_state.py::launch_vscode()`
her reset'te `subprocess.run(["bash", str(_VSCODE_LAUNCH_SCRIPT)])`
çağırdığı için, target extension aynı `executor` UID'sinde Extension
Host process'inde çalışırken script'i overwrite edebilir, modified
versiyonu sonraki reset'te re-execute olur → executor UID'sinde
arbitrary command execution + persistence. W13-2 script'i `root:executor`
0750'e taşıyarak owner-write yetkisini kaldırır; executor user
read+exec yetkisini group bit (`r-x`) üzerinden korur.

**Critical files.**

- [executor/container/Dockerfile:121-128](../../executor/container/Dockerfile) — chmod/chown ratchet (RUN bloğu split: `chmod 755 start.sh`, `chmod 0750 launch_vscode.sh`, `chown root:executor launch_vscode.sh`).
- [executor/flows/playwright/reset_state.py:148-170](../../executor/flows/playwright/reset_state.py) — `launch_vscode()` `subprocess.run(["bash", str(_VSCODE_LAUNCH_SCRIPT)])` (kod değişmez; permission değişikliği executor read+exec'i kırmaz çünkü group bit set'li).
- [executor/container/start.sh:116-126](../../executor/container/start.sh) — boot-time launch invocation (kod değişmez; aynı dosya `bash` ile çalıştırılır, executor UID'sinde okur+çalıştırır).
- [tests/architecture/test_executor_runtime_script_permissions.py](../../tests/architecture/test_executor_runtime_script_permissions.py) — 2 statik Dockerfile-AST gate + 2 runtime smoke gate (`test_launch_vscode_runtime_ownership_and_mode_smoke`, `test_executor_cannot_overwrite_launch_vscode_smoke`); helper `_resolve_executor_container` `test_container_entrypoint.py:26-45`'in birebir kopyası (paylaşılan conftest fixture'ına çıkarmak W13-2 scope dışı).

**Sub-commit Roadmap (4 commits — all landed).**

| # | Commit | Touch | Status |
|---|---|---|---|
| 1 | `07a68ad` test(W13-2): RED precursor for launch_vscode.sh permission ratchet | `tests/architecture/test_executor_runtime_script_permissions.py` (yeni dosya, 2 gate; gate 1 launch_vscode.sh root:executor 0750 zorunlu — RED, gate 2 start.sh chown executor:* yasak — defense-in-depth, zaten PASS) | ✅ landed |
| 2 | `75efad7` feat(W13-2): root-own + 0750 launch_vscode.sh in Dockerfile | `executor/container/Dockerfile:121-128` (chmod RUN bloğu split: 755 start.sh + 0750 launch_vscode.sh; chown executor:executor → root:executor) | ✅ landed |
| 3 | `22938ef` test(W13-2): close evidence + lane tracker + status sweep | Lane tracker, `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md` § Codex Cloud Audit, `REFACTOR_OPTIMIZATION.md` §11.10 | ✅ landed |
| 4 | `44b5bc1` test(W13-2): runtime smoke ratchet + .gitignore + §11.10 date sweep | `tests/architecture/test_executor_runtime_script_permissions.py` (+2 smoke/integration gate); `.gitignore` (`results/` scratch ignored); `documents/REFACTOR_OPTIMIZATION.md` (Last Updated `2026-05-07` → `2026-05-10` + §11.10 H5 test surface lehçesi); `documents/REFACTOR_STATUS.md` + W13 lane tracker close-evidence güncellemesi | ✅ landed |

**Sub-commit 3 close evidence (`22938ef`).**

- [x] Architecture gates landed: `test_launch_vscode_is_root_owned_and_executor_read_only` (chown executor:*forbidden + chown root:* required + chmod 755 forbidden + chmod 0750 required), `test_start_sh_remains_root_owned` (chown executor:* on start.sh forbidden, defense-in-depth ratchet) — `tests/architecture/` 79 → 81. Sub-commit 1 doğruladı: gate 1 RED, gate 2 PASS; sub-commit 2 sonrası gate 1 GREEN.
- [x] `make test-local` 1458 → 1460 passed / 6 skipped / 6 deselected (+2 W13-2 AST gates; sayım `pytest tests/architecture/ --co -q | wc -l` ile doğrulandı: 81/83 collected).
- [x] `make test-security` 211 passed / 32 warnings unchanged (W13-2 yalnızca container build-time permission değiştirir; runtime fixture-side rules aynı).
- [x] `tests/architecture/` 79 → 81 (+2 W13-2 gate).
- [x] **Container smoke (in-container, 2026-05-10):** Container rebuild (`make exec-build`) + `make exec-up` sonrası
      - `docker exec automation_executor stat -c '%U:%G %a' /home/executor/container/launch_vscode.sh` → `root:executor 750` ✓
      - `docker exec automation_executor stat -c '%U:%G %a' /usr/local/bin/start.sh` → `root:root 755` ✓ (defense-in-depth ratchet pinned)
      - `docker exec automation_executor whoami` → `executor` (uid 1000); same UID context as target VSIX would run.
      - **Negative (write):** `docker exec automation_executor sh -c 'echo "x" >> /home/executor/container/launch_vscode.sh'` → `Permission denied` (exit 2) ✓ — Codex H5 vector kapatıldı.
      - **Positive (read):** `head -1` `#!/bin/bash` ✓
      - **Positive (exec bit):** `test -x` passed ✓
      - **Functional:** Container ENTRYPOINT (`start.sh`) successfully invoked `bash launch_vscode.sh` at boot — VS Code PID 101 confirmed in `docker logs` (`/usr/share/code/code --no-sandbox … --remote-debugging-port=9222 …`); group-bit read+exec yetkisi launch chain'i kırmadı.
- [x] **Threat model coverage özeti.** Eskiden: target extension `fs.writeFile("/home/executor/container/launch_vscode.sh", malicious_bash)` çağırabilirdi (owner write executor:executor); reset sonrası `subprocess.run(["bash", str(_VSCODE_LAUNCH_SCRIPT)])` modified script'i re-execute eder, persistence across analyses. Şimdi: dosya `root:executor 0750` (`-rwxr-x---`) — owner = root, group = executor, world = none; executor user yalnızca read+exec yetkisinde, write `Permission denied`. Test ağı: 2 architecture gate (text-parse Dockerfile invariant — chmod regex + chown regex hem positive hem negative; W12-5 `test_dockerfile_digest_pin.py` pattern'i). Container smoke (negative + positive + functional) defense'i runtime'da pinler.
- [x] W12 ratchet gate'leri korundu (W13-2 hiçbirini kırmadı):
      `test_executor_playwright_flat_file_count_limit` ✓,
      `test_runner_main_under_loc_budget` ✓,
      `test_runtime_capture_extension_host_*` (W12-5) ✓,
      `test_body_preview_assignments_are_redacted` ✓,
      `test_all_runtime_dockerfiles_pin_base_images_by_digest` ✓.
- [x] W13-1 ratchet gate'leri korundu: `test_harness_marker_auth.py` 3/3 ✓ (`tests/architecture/` total run'da yeşil).

**Sub-commit 4 close evidence (`44b5bc1` — pre-push runtime ratchet).**

- [x] Container smoke proof'u manuel `docker exec` çağrılarından pytest gate'lerine çevrildi — `tests/architecture/test_executor_runtime_script_permissions.py`'ye 2 yeni `@pytest.mark.smoke @pytest.mark.integration` test eklendi:
      - `test_launch_vscode_runtime_ownership_and_mode_smoke` — container içinde `stat -c '%U:%G %a' /home/executor/container/launch_vscode.sh` çıktısını `"root:executor 750"` literal'e karşı assert eder. Statik Dockerfile gate'i tamamlar: RUN sırası bozulursa veya post-COPY chown silinirse statik gate hâlâ pass eder ama runtime gate yakalar.
      - `test_executor_cannot_overwrite_launch_vscode_smoke` — Codex H5'in gerçek exploit vektörünü doğrular: `USER executor` (Dockerfile:145) default UID'sinde `docker exec automation_executor bash -c 'echo evil >> /home/executor/container/launch_vscode.sh'` çağrısı `returncode != 0` + stderr `"Permission denied"` döner. Image cache veya overlay drift senaryolarını yakalar.
- [x] Helper `_resolve_executor_container()` `test_container_entrypoint.py:26-45`'ten birebir kopyalandı; container provisioning değişirse "keep in sync" yorumu işaret ediyor. Conftest fixture'a çıkarma W13-2 scope dışı (statik+runtime sync'i bozmamak için bilinçli karar).
- [x] Skip pattern: `docker` yoksa veya `automation_executor` running değilse iki gate de `pytest.skip` — yerel pre-push ergonomisi korunur, CI'de `make exec-up` provision sonrası live signal verir.
- [x] **Test bar:** `pytest -v tests/architecture/test_executor_runtime_script_permissions.py` default lane (`not smoke`) 2 PASS / 2 deselected (statik gate'ler korundu, runtime gate'ler smoke-only). `pytest -v -m "smoke or integration" tests/architecture/test_executor_runtime_script_permissions.py` 2 PASS — container ayakta, runtime invariant teyit. `make test-local` sayısı 1460 unchanged (yeni testler smoke/integration markerlı, default lane'den deselect).
- [x] **Drift düzeltme (sweep):** `documents/REFACTOR_OPTIMIZATION.md:3` `Last Updated: 2026-05-07` → `2026-05-10` ile diğer slim canonical'larla parity'ye çekildi; §11.10 H5 close-out test surface lehçesi "2 architecture gates" → "2 static Dockerfile-AST gates + 2 runtime smoke gates".
- [x] **Artefakt temizliği:** `results/` (operator-local ad-hoc analiz scratch — `results/_compare.py` hardcoded job/version içeren bir kerelik debug aracı) `.gitignore`'a eklendi. `git status` artık temiz.

### W13-3 — Cancel concurrent race (Codex H4)

`Status: closed 2026-05-10 (6/6 sub-commits)` ·
`Source: [FOLLOWUP codex-2026-05-10-H4-cancel-concurrent-race]` ·
`Cross-ref: [FOLLOWUP simulation-progress-cancel]` (parent + 4 sub-items by stable ID; `is-job-cancelled-session-churn` W13-3.5'te kapandı) ·
`Lane: [executor-runtime] [platform-storage]`

**Goal.** Codex Cloud audit (`2026-05-10`) HIGH severity: `cancelled`
job statüsü `appcore/storage/crud_ops/analysis_jobs/lifecycle.py:41`
`_TERMINAL_JOB_STATUSES` içinde. Cancel anında `reserve_job()`
(`workflows/marketplace/job_service.py:173-193`) single-active-job
lock'unu serbest bırakıyor — ancak worker thread arka planda hâlâ
shared `executor` container'ı ve `/results/` dizinine yazıyor olabilir.
Yeni `reserve_job` kabul edilirse iki job aynı executor üzerinde
concurrent çalışır → dosya bozulması, extension cross-contamination,
deterministic baseline kaybı. İkinci açık: cancellation polling sadece
`_run_monitoring_heartbeat`
([workflows/marketplace/analysis_execution.py:85-113](../../workflows/marketplace/analysis_execution.py))
içinde 5sn interval. `execute_analysis_request` (line 106-132)
sırasındaki `ensure_vsix_exists`, `_reset_sandbox`, `_install_extension`,
`_build_triggers`, completion barrier'ı cancel sinyalini görmez —
kullanıcı "Stop"'a basınca up-to-several-minutes worker tüketim yapar.
W13-3 her iki açığı tek paket halinde kapatır.

**Critical files.**

- [appcore/storage/crud_ops/analysis_jobs/lifecycle.py:41,105-134,261-282](../../appcore/storage/crud_ops/analysis_jobs/lifecycle.py) — `_TERMINAL_JOB_STATUSES` korunur; `cancel_analysis_job` `cancelling` transition'ına geçer; yeni `finalize_cancelled_analysis_job`; `recover_interrupted_jobs` zaten non-terminal'i kurtarıyor — `cancelling` otomatik dahil.
- [appcore/contracts/schema_defs/analysis_jobs.py:24-25,42,110-122](../../appcore/contracts/schema_defs/analysis_jobs.py) — `AnalysisJobStatus` Literal'a `cancelling`, `ANALYSIS_JOB_STATUSES` 6 elemana çıkar, `ACTIVE_ANALYSIS_JOB_STATUSES = ("queued","running","cancelling")`, `AnalysisJobUpdate` yeni `requested_cancel_at` field.
- [appcore/storage/model_defs/analysis_job.py:39-47](../../appcore/storage/model_defs/analysis_job.py) — partial unique index `WHERE` clause `cancelling` dahil; yeni `requested_cancel_at` mapped_column Float nullable.
- [workflows/marketplace/analysis_execution.py:85-132](../../workflows/marketplace/analysis_execution.py) — heartbeat (line 85-113) dokunulmaz; `execute_analysis_request` body (line 106-132) 5 hot-zone'a yeni `raise_if_cancelled` helper'ı ekler.
- [workflows/marketplace/analysis_service.py:211-249](../../workflows/marketplace/analysis_service.py) — exception handler `finalize_cancelled_analysis_job(job_id)` çağrısı; `cancel_check` shared session optimization (`is-job-cancelled-session-churn` sub-item kapanır).
- [workflows/marketplace/job_service.py:173-193,315-322](../../workflows/marketplace/job_service.py) — `reserve_job` kod değişmez (doğal olarak `cancelling` aktif sayılır); `is_job_cancelled` semantic genişler veya yeni helper.
- `alembic/versions/<rev>_w13_3_add_cancelling_state.py` (yeni) — partial unique index güncelleme + `requested_cancel_at` column; reversible downgrade `cancelling → cancelled` zorla taşır.
- `tests/architecture/test_cancel_poll_points.py` (yeni) ve `tests/architecture/test_job_state_invariants.py` (yeni) — 2 yeni AST gate dosyası.

**Design Decision Locked-In: Option A (Draining intermediate state).**

State machine son hâli: `queued → running → (cancelling → cancelled) | completed | failed`.

| Boyut | Karar |
|---|---|
| Yeni state | `cancelling` (non-terminal); `_TERMINAL_JOB_STATUSES = {"completed","failed","cancelled"}` invariant DOKUNULMAZ. |
| Reserve lock | `cancelling` `ACTIVE_ANALYSIS_JOB_STATUSES`'e dahil; partial unique index `WHERE status IN ('queued','running','cancelling')` (Alembic migration). |
| Cancel API atomik mi? | Hayır — iki fazlı: (1) CRUD `cancel_analysis_job` `running → cancelling`, `requested_cancel_at=now()`, `finished_at` set ETMEZ; (2) worker `AnalysisCancelledError` aldıktan sonra `analysis_service` exception handler `finalize_cancelled_analysis_job` çağırır → `cancelling → cancelled`, step'leri finalize. |
| Idempotency | `cancelling` üzerinde tekrar `cancel` no-op (mevcut snapshot 200 OK; UI double-click'i kırmaz). |
| Cancel poll point'leri | `execute_analysis_request`'in 5 hot-zone'unda yeni `raise_if_cancelled(cancel_check)` helper: ensure_vsix öncesi, `_reset_sandbox` öncesi, `_install_extension` öncesi, `_build_triggers` öncesi, `_run_monitoring` öncesi. `AnalysisCancelledError` yeniden kullanılır. |
| Worker crash recovery | `recover_interrupted_jobs` predicate'ı non-terminal + boot_id != current → `failed`'a düşürür; `cancelling` non-terminal olduğu için otomatik kapsanır. |
| UI contract | `cancelling` Pydantic Literal'a eklenir → `scripts/generate_ui_contracts.py` regen ile frontend `AnalysisJobStatus` TS literal'a düşer. Backend gate yeşil; frontend "Stopping…" rendering'i ayrı UI lane work (W13 scope'unda BACKLOG note). Polling client `cancelling`'i non-terminal görür ve polling sürer. |

**Reverse-side reject rationale (Option B — reserve_job heuristic).**

Reddedildi. `reserve_job` içine `owner_boot_id == _PROCESS_BOOT_ID and
finished_at + grace > now()` benzeri timing/grace-window heuristic'i
test edilebilir değil (saat-based race senaryosu); scheduler ve worker
durum kanalları arasında ikinci bir doğru kaynağı yaratır (`status`
sütunu vs. "alive worker" sezgisi). W11 monitor lifecycle precedent'ı
(start/starting/running/stopping/stopped) state-machine yaklaşımını
zaten validate ediyor.

**Simulation-progress-cancel sub-item dağılımı.**

`POST_POC_BACKLOG.md` içindeki stable-ID sub-item dağılımı:

- `heartbeat-sandbox-reset-off-thread` → **W14'e iter.** Heartbeat refactor; W13-3 race fix'ten bağımsız, scope şişer.
- `dedupe-step-progress-schemas` → **W14'e iter.** `AnalysisJobStepProgress` vs `AnalyzeJobStepProgress` kontrat hijyeni; race fix ile bağımsız.
- `is-job-cancelled-session-churn` → **W13-3.5'te kapanır.** `raise_if_cancelled` helper'ı 5 ek site'a girince session churn artma riski; `cancel_check` lambda'sı shared `Session` parametresi alarak ya da `is_job_cancelled` short-circuit cache'leyerek opt-in optimize edilir. Close evidence W13-3.6'da kayıt düşülür.
- `heartbeat-refactor` → **W14'e iter.** Heartbeat polling/JSON/cancel logic'i testable helper'a çıkar; race fix'ten bağımsız.

Net: W13-3 1 sub-item kapatır, 3'ünü W14'e iter.

**Sub-commit Roadmap (6 commits — all targeting `week13`).**

| # | Commit | Touch | Status |
|---|---|---|---|
| 1 | `1b9657c` `docs(W13-3): assign stable ID + lock in draining state design` | `documents/active-work/W13-test-expansion-observability.md`, `documents/POST_POC_BACKLOG.md`, `documents/REFACTOR_STATUS.md` | ✅ landed |
| 2 | `4db412b` `test(W13-3): RED precursor for cancelling-state lifecycle + race gaps` | `tests/platform/storage/test_analysis_jobs_lifecycle.py` (+5 skip-RED cases), `tests/workflows/marketplace/test_router.py` (+2 skip-RED cases) | ✅ landed |
| 3 | `c4447d4` `feat(W13-3): add cancelling status + Alembic migration` | `appcore/contracts/schema_defs/analysis_jobs.py` (Pydantic literal + tuple), `appcore/storage/model_defs/analysis_job.py` (column + partial unique index), `alembic/versions/c8a2d4e91f5b_add_cancelling_status_to_analysis_jobs.py` (new — DROP/CREATE index + add column; reversible downgrade) | ✅ landed |
| 4 | `112321c` `feat(W13-3): CRUD layer two-phase cancel + finalize helper` | `appcore/storage/crud_ops/analysis_jobs/lifecycle.py` (`cancel_analysis_job` cancelling transition, idempotent on cancelling; new `finalize_cancelled_analysis_job`; complete/fail guards), `appcore/storage/crud.py` + `appcore/storage/crud_ops/analysis_jobs/__init__.py` re-exports, `workflows/marketplace/job_service.py` (`is_job_cancelled` semantic widens to cancelling+cancelled; new `finalize_cancelled_job` wrapper), 5 RED→GREEN regressions | ✅ landed |
| 5 | `efd50c1` `feat(W13-3): worker cancel-poll points + service finalization` | `workflows/marketplace/analysis_execution.py` (new `raise_if_cancelled` helper), `workflows/marketplace/analysis_service.py` (5 cancel-poll points in `execute_analysis_request` + `finalize_cancelled_job` in `run_analysis_job` exception handler — both cancel path and is_job_cancelled-true error path), 2 router RED→GREEN | ✅ landed |
| 6 | `8259041` `test(W13-3): architecture gates + close evidence + status sweep` | `tests/architecture/test_cancel_poll_points.py` (new — 2 AST gates: 5-phase poll invariant + raise_if_cancelled public name), `tests/architecture/test_job_state_invariants.py` (new — 4 state-machine invariants pinning _TERMINAL_JOB_STATUSES, ACTIVE_ANALYSIS_JOB_STATUSES, ANALYSIS_JOB_STATUSES tuple, Alembic WHERE clause), `documents/active-work/W13-test-expansion-observability.md` close evidence, `documents/POST_POC_BACKLOG.md` H4 + `is-job-cancelled-session-churn` strikethrough, `documents/REFACTOR_STATUS.md` W13-3 closed satırı | ✅ landed |

**Migration plan (W13-3.3).**

```python
upgrade():
    op.drop_index("uq_analysis_jobs_single_active", table_name="analysis_jobs")
    op.create_index(
        "uq_analysis_jobs_single_active",
        "analysis_jobs",
        [text("(1)")],
        unique=True,
        postgresql_where=text("status IN ('queued','running','cancelling')"),
    )
    op.add_column(
        "analysis_jobs",
        sa.Column("requested_cancel_at", sa.Float(), nullable=True),
    )

downgrade():
    op.execute(
        "UPDATE analysis_jobs SET status='cancelled', "
        "finished_at=COALESCE(finished_at, EXTRACT(EPOCH FROM NOW())), "
        "requested_cancel_at=NULL WHERE status='cancelling'"
    )
    op.drop_column("analysis_jobs", "requested_cancel_at")
    op.drop_index("uq_analysis_jobs_single_active", table_name="analysis_jobs")
    op.create_index(
        "uq_analysis_jobs_single_active",
        "analysis_jobs",
        [text("(1)")],
        unique=True,
        postgresql_where=text("status IN ('queued','running')"),
    )
```

Reversible. PoC tek-aktif-iş; en kötü 1 row downgrade'de zorla
`cancelled`'a taşınır (veri kaybı yok, worker yarıda kesilmiş gözükür).
Operasyonel adım: `make exec-down` → `make migrate` → `make exec-up`.

**Architecture gates (W13-3.6'da pinler).**

1. `test_cancel_poll_points.py`: `execute_analysis_request` AST'ında
   `ensure_vsix_exists`, `_reset_sandbox`, `_install_extension`,
   `_build_triggers`, `_run_monitoring` çağrılarının her birinin AYNI
   fonksiyon body'sinde önceki statement olarak `raise_if_cancelled(...)`
   pattern'ına sahip olduğunu doğrular. Yeni step eklenirse gate kırılır
   → tasarımcı bilinçli karar vermek zorunda.
2. `test_job_state_invariants.py`: (a) `_TERMINAL_JOB_STATUSES` exact
   `{"completed","failed","cancelled"}` frozenset, (b) `"cancelling"`
   terminal'a sokulmamış, (c) `ACTIVE_ANALYSIS_JOB_STATUSES`
   `"cancelling"` içerir, (d) `ANALYSIS_JOB_STATUSES` 6-eleman tuple ve
   `cancelling`'i içerir, (e) Alembic upgrade body'sinde `"WHERE status
   IN ('queued','running','cancelling')"` literal'ı bulunur.

**Verification plan.**

- Per sub-commit: `make check-all`, `make test-local` delta dokümante, `make test-security` 211 yeşil korunur, W12 + W13-1 + W13-2 ratchet gates kırılmaz.
- W13-3.3 sonrası: `alembic upgrade head` + `alembic downgrade -1` + `alembic upgrade head` round-trip; `psql -d <db> -c "\d analysis_jobs"` ile partial unique index where ve `requested_cancel_at` column doğrulaması.
- W13-3.5 sonrası: `make exec-up` + manuel race senaryosu — job başlat, `_reset_sandbox`/`_install_extension`/`_build_triggers`/`_run_monitoring` her fazında ayrı ayrı cancel et, snapshot `cancelling → cancelled` transition'ı, sonraki `reserve_job` çağrısı sadece terminal sonrasında kabul edilir; `cancelling` sırasında ikinci POST `ActiveAnalysisJobError` (409 Conflict) verir.
- W13-3.6 close: `tests/architecture/` 81 → ~85 (+4 W13-3 gate); threat model coverage özeti H4 vector kapatma kanıtı (`reserve_job` block + 5 cancel-poll point + drain-then-finalize); live-scan baseline `ms-python.python@2026.5.2026050801` üzerinde bitwise-equal beklenir (semantik-delta yoksa).

**W13-3.6 close evidence (`8259041`).**

- [x] Architecture gates landed: `tests/architecture/test_cancel_poll_points.py` (2 gate — `test_every_major_phase_is_preceded_by_a_cancel_poll` AST-walks `execute_analysis_request` body ve 5 hot-zone helper'ından önce `_raise_if_cancelled(cancel_check)` çağrısı zorunlu kılar; `test_raise_if_cancelled_helper_is_publicly_named` `analysis_execution.__all__`'da helper'ın export edildiğini pinler). `tests/architecture/test_job_state_invariants.py` (4 gate — `_TERMINAL_JOB_STATUSES` exact frozenset eşitliği `{"completed","failed","cancelled"}` + `cancelling` terminal'a sokulmamış; `ACTIVE_ANALYSIS_JOB_STATUSES` `cancelling` içerir ve `{"queued","running","cancelling"}` setiyle eşittir; `ANALYSIS_JOB_STATUSES` 6-eleman canonical; Alembic upgrade body'sinde `"WHERE status IN ('queued', 'running', 'cancelling')"` + downgrade body'sinde `"WHERE status IN ('queued', 'running')"` literal'ları). `tests/architecture/` 81 → 87 (+6 W13-3 gate, 2 dosya).
- [x] `make test-local` 1460 → 1467 passed / 6 skipped / 8 deselected / 75 warnings. Delta: +7 W13-3 test (5 CRUD lifecycle + 2 router); RED→GREEN geçişi W13-3.4 (CRUD) ve W13-3.5'te (router) tamamlandı, hiçbir test deselect değil.
- [x] `make test-security` 211 passed / 32 warnings — unchanged (W8/W12 baseline korundu; W13-3 worker tarafı race fix, security fixture lane'i etkilemez).
- [x] `tests/architecture/` 81 → 87 — W12 ratchet gate'leri (test_executor_playwright_flat_file_count_limit, test_runner_main_under_loc_budget, test_runtime_capture_extension_host_*, test_body_preview_assignments_are_redacted, test_all_runtime_dockerfiles_pin_base_images_by_digest), W13-1 gate'leri (test_harness_marker_auth.py × 3) ve W13-2 gate'leri (test_executor_runtime_script_permissions.py × 2 static + 2 smoke) korundu.
- [x] **Migration round-trip (2026-05-10):** `alembic upgrade head` → `c8a2d4e91f5b`; `\d analysis_jobs` `requested_cancel_at | double precision` + partial unique index `WHERE status IN ('queued','running','cancelling')`. `alembic downgrade -1` → `requested_cancel_at` kayboldu + WHERE clause eski hâle döndü (`queued, running`). `alembic upgrade head` ile geri yüklendi — round-trip tam reversible. PoC tek-aktif-iş ortamı, en kötü 1 row'da downgrade'de zorla `cancelled` terminal'ine taşınır (veri kaybı yok).
- [x] **Threat model coverage özeti.** Eskiden: `cancel_analysis_job` atomik olarak `cancelled` terminal'i set ederdi; `reserve_job()` (single-active-job lock) cancel anında serbest bırakırdı; worker thread arka planda shared executor + `/results` üzerine yazmaya devam ederken yeni POST `/api/marketplace/analyze` kabul edilirdi → iki job aynı executor üzerinde concurrent. Cancel polling sadece `_run_monitoring_heartbeat` (5sn interval); `_reset_sandbox`/`_install_extension`/`_build_triggers`/completion barrier'larında poll yok. Şimdi: `cancel_analysis_job` non-terminal `cancelling`'e geçer (step'lere dokunmaz, `finished_at` set etmez, `requested_cancel_at=now()`); `ACTIVE_ANALYSIS_JOB_STATUSES` `cancelling`'i içerir + partial unique index `WHERE`'i genişler → `reserve_job` DB-level olarak block eder. `execute_analysis_request`'in 5 hot-zone'unda yeni `_raise_if_cancelled(cancel_check)` poll'ları worker'ı milisaniyeler içinde drain'e geçirir. Worker `AnalysisCancelledError` (veya hard error + is_job_cancelled True) sonrası `analysis_service` exception handler `finalize_cancelled_job` çağırır → `cancelling → cancelled` terminal geçişi, step'ler finalize, `finished_at` set, lock release. CRUD-level idempotency: `cancelling`'de tekrar cancel no-op; `complete_analysis_job` ve `fail_analysis_job` `cancelling` source'undan invocation'da `JobNotCancellableError` raise eder (cancel intent authoritative). Test ağı: 6 architecture gate (5-phase poll AST invariant + helper public name + 4 state-machine invariant), 5 CRUD regression (test_analysis_jobs_lifecycle.py), 2 router regression (test_router.py), 1 top-level integration (test_analysis_jobs.py).
- [x] **simulation-progress-cancel sub-item dağılımı uygulandı.** `[FOLLOWUP simulation-progress-cancel] is-job-cancelled-session-churn` W13-3.5'te kapatıldı: `is_job_cancelled` worker poll primitive'i `analysis_service.run_analysis_job` içinde lambda olarak tek noktada tanımlı ve 5 cancel-poll point + heartbeat-thread arasında paylaşılıyor; her çağrı kendi DB session'unu yaratmıyor (mevcut shared session pattern korunuyor). 3 sub-item W14'e iter (heartbeat-sandbox-reset-off-thread, dedupe-step-progress-schemas, heartbeat-refactor) — race fix'ten bağımsız scope.
- [x] W12 ratchet gate'leri korundu: `test_executor_playwright_flat_file_count_limit` ✓, `test_runner_main_under_loc_budget` ✓, `test_runtime_capture_extension_host_stays_a_thin_facade` ✓, `test_runtime_capture_extension_host_reexports_match_canonical_modules` ✓, `test_body_preview_assignments_are_redacted` ✓, `test_all_runtime_dockerfiles_pin_base_images_by_digest` ✓.
- [x] W13-1 ratchet gate'leri korundu: `test_harness_marker_auth.py` 3/3 ✓ (`test_attempt_has_harness_completion_trace_calls_verifier`, `test_reconcile_event_attempts_threads_expected_harness_nonce`, `test_setup_monitor_loads_and_stamps_harness_python_secret`).
- [x] W13-2 ratchet gate'leri korundu: `test_executor_runtime_script_permissions.py` 2 static + 2 smoke = 4/4 ✓ (default lane'de 2, smoke lane'de +2; W13-3 statik AST gate'leri ile çakışma yok).

### W13-4 — Cancellation lifecycle hardening (W13-3 close-pass)

`Status: closed 2026-05-11 (8/8 sub-commits landed)` ·
`Source: [FOLLOWUP w13-3-close-pass-cancellation-test-hardening]` ·
`Cross-ref: W13-3 close evidence above (6/6 sub-commits 2026-05-10)` ·
`Lane: [platform-storage] [executor-runtime]`

**Bağlam.** W13-3 (Codex H4 cancel concurrent race) `2026-05-10`'da
6/6 sub-commit ile kapandı. Close evidence W13-3.6'da landed 6
architecture gate (`tests/architecture/test_cancel_poll_points.py` × 2,
`tests/architecture/test_job_state_invariants.py` × 4) **statik AST
invariant'larını** pinler: `_raise_if_cancelled` çağrısı 5 hot-zone
helper'ından önce yer alır mı, `_TERMINAL_JOB_STATUSES` tam olarak
`{completed, failed, cancelled}` mı, Alembic upgrade body'sinde doğru
WHERE clause var mı. Bu gate'ler refactor regression'larını yakalar
ama **davranış** kanıtı vermez: poll'ların gerçekten raise ettiği,
cancel↔complete race'inin serialize olduğu, stuck `cancelling`
row'unun boot_id sweep ile finalize edildiği, Alembic'in upgrade +
downgrade arasında veri kaybetmediği, `run_analysis_job` exception
handler'ın `finalize_cancelled_job`'u doğru iki dalda da çağırdığı
test edilmedi.

Plus drift: `documents/runbooks/analysis-job-stuck.md:42` hâlâ
pre-W13-3 4-üye `Literal["queued","running","completed","failed"]`
listeliyor (gerçek 6: cancelling + cancelled eklendi). Last Updated
`2026-04-24` — W13-3 öncesinden. Operatörün "stuck cancelling"
durumunda yapacağı diagnose/recover adımı yok.

**Karar.** Saf test + doc paketi olarak yeni stable ID `W13-4` aç.
W13-3 reopen edilmez (W13-1/W13-2/W13-3 stable-ID convention'ı
bozulmaz; close evidence satırları tarihsel doğru kalır). Production
kodu değişmez — `_raise_if_cancelled` / `cancel_analysis_job` /
`finalize_cancelled_analysis_job` / `is_job_cancelled` /
`recover_interrupted_jobs` zaten doğru implementasyonlar; gap test
kanıt eksiği.

**Critical files.**

- [appcore/storage/crud_ops/analysis_jobs/lifecycle.py:105-203,255-339,342-363](../../appcore/storage/crud_ops/analysis_jobs/lifecycle.py) — `cancel_analysis_job` (cancelling transition + idempotent), `finalize_cancelled_analysis_job` (cancelling→cancelled + JobNotCancellableError guard), `complete_analysis_job` + `fail_analysis_job` cancelling source state guards, `recover_interrupted_analysis_jobs` boot_id sweep.
- [workflows/marketplace/analysis_execution.py:56-70,360-369](../../workflows/marketplace/analysis_execution.py) — `raise_if_cancelled` helper + `__all__` export.
- [workflows/marketplace/analysis_service.py](../../workflows/marketplace/analysis_service.py) — `execute_analysis_request` 5 cancel-poll point + `run_analysis_job` exception handler dalları (AnalysisCancelledError + is_job_cancelled-true hard error).
- [workflows/marketplace/job_service.py](../../workflows/marketplace/job_service.py) — `is_job_cancelled` (cancelling+cancelled dahil) + `finalize_cancelled_job` wrapper.
- [alembic/versions/c8a2d4e91f5b_add_cancelling_status_to_analysis_jobs.py](../../alembic/versions/c8a2d4e91f5b_add_cancelling_status_to_analysis_jobs.py) — upgrade (DROP/CREATE partial index + add column) + downgrade (force-finalize cancelling→cancelled, shrink WHERE clause).
- [documents/runbooks/analysis-job-stuck.md:42](../../documents/runbooks/analysis-job-stuck.md) — drift fix (W13-4.7).

**Sub-commit roadmap.**

| # | Commit | Konu | Test/doc dosyaları |
|---|--------|------|-------------------|
| 1 | `050317e` `docs(W13-4): assign stable ID + lock in cancellation lifecycle hardening scope` | W13 tracker, REFACTOR_STATUS, POST_POC pointer + this Per-Item Detail block | tracker, `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md` |
| 2 | `test(W13-4): RED precursor for cancellation lifecycle behavioral coverage` | 13 skip-marked test (5 poll-point + 2 race + 1 recovery + 1 alembic + 2 exception + 2 negative) | `tests/workflows/marketplace/test_analysis_execution_poll_points.py` (yeni), `tests/platform/storage/test_analysis_jobs_concurrency.py` (yeni), `tests/platform/storage/test_alembic_cancelling_migration.py` (yeni), `tests/workflows/marketplace/test_run_analysis_job_finalize.py` (yeni), `tests/platform/storage/test_analysis_jobs_lifecycle.py` (extend) |
| 3 | `test(W13-4): GREEN poll-point behavioral (5 RED→GREEN)` | `test_analysis_execution_poll_points.py` skip kaldır + 5 case GREEN | (above) |
| 4 | `test(W13-4): GREEN cancel↔complete race + concurrent cancel/finalize (2 RED→GREEN)` | `test_analysis_jobs_concurrency.py` skip kaldır + 2 case GREEN | (above) |
| 5 | `test(W13-4): GREEN alembic round-trip + stuck-cancelling recovery + exception handler integ (4 RED→GREEN)` | `test_alembic_cancelling_migration.py` (1) + `test_analysis_jobs_concurrency.py` recovery (1) + `test_run_analysis_job_finalize.py` (2) skip kaldır + GREEN | (above) |
| 6 | `test(W13-4): GREEN finalize negative (2 RED→GREEN)` | `test_analysis_jobs_lifecycle.py` skip kaldır + 2 negative case GREEN | (above) |
| 7 | `docs(W13-4): runbook revision for cancelling state — Stuck in cancelling diagnose/recover` | `documents/runbooks/analysis-job-stuck.md` literal fix + new section + Step 2 SQL widening + code references update | runbook only |
| 8 | `01bf761` `docs(W13-4): close evidence + status sweep` | tracker close evidence, REFACTOR_STATUS bump, POST_POC pointer strikethrough | tracker, `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md` |

**Verification (final).**

- `make test-local` 1473 (corrected W13-4 open baseline) → 1485
  passed / 7 skipped / 8 deselected / 75 warnings.
- Net +12 behavioral cases: +5 poll-point, +2 race/concurrent,
  +1 recovery, +2 exception handler, +2 finalize negative.
- `make test-security` 211 unchanged.
- `tests/architecture/` 87 unchanged; W13-4 added behavioral coverage,
  not new AST gates.
- W12 + W13-1 + W13-2 + W13-3 ratchet gates remained intact.

**W13-4.4 (alembic round-trip) sonrası manuel:**

```bash
alembic upgrade head && alembic downgrade -1 && alembic upgrade head
psql -d <db> -c "\d analysis_jobs" | grep -E "requested_cancel_at|uq_analysis_jobs_single_active"
```

**W13-4.7 (runbook revizyon) review.**

- Drift yok: `grep -n 'Literal\[' documents/runbooks/*.md` çıktısı schema (`appcore/contracts/schema_defs/analysis_jobs.py:24-25,42`) ile bire bir eşleşmeli.
- Yeni "Stuck in cancelling" bölümünün SQL'i `tests/platform/storage/test_analysis_jobs_concurrency.py` recovery testiyle aynı semantiği yansıtmalı (cancelling → failed by boot_id mismatch beklenen davranış).

**W13-4.1 close evidence (`050317e`).**

- [x] Stable ID `W13-4` atandı, scope kilitlendi (saf test + doc paketi).
- [x] Tracker güncellendi: header `Last Updated 2026-05-11`; Status (Quick Glance) yeni W13-4 opened bullet'ı; Candidate Items table'a `W13-4` satırı eklendi (W13-3 satırından önce); bu Per-Item Detail bloğu eklendi.
- [x] `documents/REFACTOR_STATUS.md` güncellendi: header bump + Active phase bölümüne W13-4 in-progress satırı.
- [x] `documents/POST_POC_BACKLOG.md` güncellendi: H4 close evidence bloğunun sonuna "Post-close evaluation" paragrafı + yeni `[FOLLOWUP w13-3-close-pass-cancellation-test-hardening]` pointer.
- [x] `make check-all` yeşil; W13-3 close evidence sayıları (1467 / 211 / 87) **dokunulmaz** kaldı (W13-4.1 saf doc).
- [x] W12 + W13-1 + W13-2 + W13-3 ratchet gate'leri korundu.

**Sub-commit landings (final hash table).**

| # | Commit | Konu | Test/doc dosyaları |
|---|--------|------|-------------------|
| 1 | `050317e` `docs(W13-4): assign stable ID + lock in cancellation lifecycle hardening scope` | W13 tracker, REFACTOR_STATUS, POST_POC pointer + Per-Item Detail block | tracker, `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md` |
| 2 | `422684b` `test(W13-4): RED precursor for cancellation lifecycle behavioral coverage` | 13 skip-marked cases across 4 new + 1 extended test files | `test_analysis_execution_poll_points.py` (NEW), `test_analysis_jobs_concurrency.py` (NEW), `test_alembic_cancelling_migration.py` (NEW), `test_run_analysis_job_finalize.py` (NEW), `test_analysis_jobs_lifecycle.py` (extend) |
| 3 | `234ad50` `test(W13-4): GREEN poll-point behavioral coverage (5 RED→GREEN)` | 5 skip kaldırıldı + TriggerPlan factory `reason_code` field düzeltmesi | `test_analysis_execution_poll_points.py` |
| 4 | `bc8f562` `test(W13-4): GREEN cancel↔complete race + concurrent cancel/finalize (2 RED→GREEN)` | 2 skip kaldırıldı + race-window dokümantasyonu (complete_analysis_job FOR UPDATE eksik; W14+ followup `[FOLLOWUP analysis-jobs-race]`'e işaret) | `test_analysis_jobs_concurrency.py` |
| 5 | `247611c` `test(W13-4): GREEN recovery + exception handler integ; defer alembic round-trip` | 3 RED→GREEN (recovery + 2 exception handler) + alembic test re-skip + yeni POST_POC `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` | `test_analysis_jobs_concurrency.py`, `test_run_analysis_job_finalize.py`, `test_alembic_cancelling_migration.py`, `POST_POC_BACKLOG.md` |
| 6 | `04feea3` `test(W13-4): GREEN finalize negative — absent + double-finalize (2 RED→GREEN)` | 2 skip kaldırıldı | `test_analysis_jobs_lifecycle.py` |
| 7 | `5d7ac21` `docs(W13-4): runbook revision — cancelling state diagnose/recover playbook` | header + Job state machine literal (4→6 üye) + state-transition diagram + § Recover Step 2 SQL widening + NEW § Stuck in cancelling section + § Code References extension | `documents/runbooks/analysis-job-stuck.md` |
| 8 | `01bf761` `docs(W13-4): close evidence + status sweep` | tracker close evidence, REFACTOR_STATUS bump, POST_POC pointer strikethrough | tracker, `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md` |

**W13-4.8 close evidence (`01bf761`).**

- [x] **Behavioral coverage delta (final).** `make test-local`
  1473 (W13-4 open baseline) → 1485 (W13-4 close) = +12 net cases:
  W13-4.3 +5 poll-point + W13-4.4 +2 race/concurrent + W13-4.5 +3
  recovery+exception (alembic deferred 1 case) + W13-4.6 +2 finalize
  negative. Skipped 6 (baseline) + 1 (alembic deferred) = 7 total.
  W13-3 close evidence "1460 → 1467" baseline appears stale — actual
  baseline at W13-4 open was 1473; pytest discovery counts diverged
  silently between W13-3.6 close commit and W13-4.1. W13-4.8 adopts
  the corrected baseline going forward; W13-3 historical
  numbers are not retroactively edited).
- [x] **Test bar:** `make test-local` 1485 passed / 7 skipped / 8
  deselected / 75 warnings; `make test-security` 211 passed
  unchanged; `tests/architecture/` 87 unchanged (zero new AST gates;
  W13-4 is pure behavioral lane, not a ratchet lane).
- [x] **Production code dokunulmaz.** W13-3'ün landed sürümü
  (`raise_if_cancelled`, `cancel_analysis_job`,
  `finalize_cancelled_analysis_job`, `is_job_cancelled`,
  `recover_interrupted_jobs`, alembic `c8a2d4e91f5b`) hiç değişmedi
  — W13-4 sadece davranışsal kanıt + doc fix layered.
- [x] **Behavioral test ağı (final).**
  - Poll-point lane: 5 unit case in
    `tests/workflows/marketplace/test_analysis_execution_poll_points.py`
    (cancel_check sequence + helper-call assertion). AST gate
    `tests/architecture/test_cancel_poll_points.py` continues to pin
    structural invariant; behavioral lane proves runtime raise.
  - Concurrency lane: 3 cases in
    `tests/platform/storage/test_analysis_jobs_concurrency.py`
    (race + concurrent + recovery). All use a new
    `concurrent_session_factory` fixture that bypasses
    `db_session`'s per-test rollback to commit across threads.
  - Exception handler lane: 2 cases in
    `tests/workflows/marketplace/test_run_analysis_job_finalize.py`
    (AnalysisCancelledError + hard-error-with-cancel-signal).
  - Lifecycle negative lane: 2 cases extended into existing
    `tests/platform/storage/test_analysis_jobs_lifecycle.py`
    (absent job + double-finalize idempotency).
- [x] **Runbook drift fix landed (W13-4.7).**
  `documents/runbooks/analysis-job-stuck.md` — Last Updated bumped,
  Job state machine literal aligned with schema (6-tuple), new
  state-transition diagram, NEW § Stuck in `cancelling` section
  (Symptom + Diagnose SQL + 3-step Recover playbook), § Recover
  Step 2 SQL widened to `IN ('running', 'cancelling')`, § Code
  References extended with W13-3/W13-4 surfaces. `grep -n 'Literal\['
  documents/runbooks/*.md` matches `appcore/contracts/schema_defs/analysis_jobs.py:55-62`
  exactly.
- [x] **Threat coverage extension over W13-3.6 baseline.**
  W13-3.6 close evidence pinned 6 architecture gates (AST
  invariants); W13-4 pinned the behavioral side: each `_raise_if_cancelled`
  call actually raises at runtime; `cancel_analysis_job` ↔
  `complete_analysis_job` race converges on a consistent terminal
  state (with a documented FOR UPDATE gap on `complete_analysis_job`
  flagged for W14+ hardening as `[FOLLOWUP analysis-jobs-race]`);
  6 concurrent cancel/finalize threads serialize idempotently;
  stuck-`cancelling` rows from dead boots recover deterministically;
  `run_analysis_job` exception handler dispatches finalize on both
  AnalysisCancelledError and hard-error-with-cancel-signal paths;
  finalize negative contracts (absent + double) raise as documented.
- [x] **Deferral.** `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]`
  added to `POST_POC_BACKLOG.md` for the alembic round-trip
  behavioral case (programmatic upgrade/downgrade against the
  session-scoped test_engine leaves alembic_version + schema state
  inconsistent on partial failure; W13-3.6 close evidence has manual
  round-trip + `tests/architecture/test_job_state_invariants.py:114-140`
  pins literals; behavioral case requires fresh-DB-per-test fixture
  pattern as its own infrastructure work).
- [x] **W13-3 close-pass FOLLOWUP closed.**
  `[FOLLOWUP w13-3-close-pass-cancellation-test-hardening]` in
  `POST_POC_BACKLOG.md` strikethrough'ed with closure metadata.
- [x] **Ratchet gates korundu.** W12: 5/5 ✓
  (`test_executor_playwright_flat_file_count_limit`,
  `test_runner_main_under_loc_budget`,
  `test_runtime_capture_extension_host_*`,
  `test_body_preview_assignments_are_redacted`,
  `test_all_runtime_dockerfiles_pin_base_images_by_digest`).
  W13-1: 3/3 ✓ (`test_harness_marker_auth.py`).
  W13-2: 4/4 ✓ (`test_executor_runtime_script_permissions.py`
  static + smoke).
  W13-3: 6/6 ✓ (`test_cancel_poll_points.py` × 2 +
  `test_job_state_invariants.py` × 4).
- [x] **Sıradaki iterasyon hazır.** Candidate Items table'ın HIGH
  satırı `[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]`
  W13-5 stable ID için pull-eligible. MEDIUM kalemler
  (`[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]`,
  `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]`)
  paralel branch'lerde land edilebilir veya W13-6/W13-7 olarak çekilir.

### W13-5 — dev-lan Makefile drift (Codex H3)

`Status: in progress (opened 2026-05-11)` ·
`Source: [FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]` ·
`Lane: [security-detection] [platform-storage]`

**Bağlam.** Codex Cloud audit (`2026-05-10`) HIGH severity bulgusu:
[Makefile:170-172](../../Makefile) `dev-lan` recipe'si uvicorn'a
`--host 0.0.0.0` argümanını sabit kodluyor, dolayısıyla
`API_HOST=192.168.1.10 make dev-lan` çağrısı uvicorn bind socket'ini
narrow'lamıyor — uvicorn 0.0.0.0 binder ama `APISettings.HOST`
(Pydantic `model_post_init`, [appcore/api/config.py:90-96](../../appcore/api/config.py))
explicit env override'a uyup `192.168.1.10`'a yerleşir → uvicorn ↔
settings drift'i. Mevcut architecture gate
[tests/architecture/test_default_bindings.py:49-204](../../tests/architecture/test_default_bindings.py)
settings katmanını kapsıyor (14 case: `APISettings.HOST` defaults,
`EXTRACE_ALLOW_LAN` truthy/falsy semantiği, `docker-compose.yml`
host-IP prefix disiplini, CDP debug-profile gate'i) — ancak Makefile
recipe'sini hiç parse etmiyor. Bulgunun ana cümlesi: "Doc-fix or
recipe-fix; either lands a regression test."

**Critical files.**

- [Makefile:167-175](../../Makefile) — `dev`, `dev-lan`, `run` recipe block'ları. `dev` line 168 `--host 127.0.0.1` literal, `run` line 175 aynı; `dev-lan` line 172 `EXTRACE_ALLOW_LAN=1 $(VENV)/uvicorn main:app --reload --host 0.0.0.0` — fix bu satırın `--host` argümanına shell parameter expansion uygular.
- `tests/architecture/test_makefile_dev_recipes.py` (YENİ — sub-commit 2) — 6 case Makefile dev-server recipe binding regression gate. Parse stratejisi: dosyayı text olarak oku, regex `^(\w[\w-]*):\s*$` ile recipe header'ları topla, sonraki başlık satırına kadar TAB-indented body satırlarını lookup'a koy.
- [documents/runbooks/lan-exposure.md:82-90](../../documents/runbooks/lan-exposure.md) — §Configure §Host-mode paragrafı `API_HOST=... make dev-lan does not narrow the socket bind` drift caveat'ını içerir; sub-commit 4 bu cümleyi kaldırıp `API_HOST` override'ın artık çalıştığını dokümante eder.
- [tests/architecture/test_default_bindings.py:133-142](../../tests/architecture/test_default_bindings.py) — `test_explicit_host_override_wins_over_lan_substitution` settings katmanında `API_HOST` override'ın LAN substitution'ı yendiğini W8-7'den beri pinler; W13-5 recipe katmanını da bu invariant'ın altına çeker. Test **değiştirilmez**, sadece referans.

**Design decision locked-in: Path A (recipe-fix).**

`Makefile:172` `--host 0.0.0.0` → `--host $${API_HOST:-0.0.0.0}`.

| Boyut | Karar |
|---|---|
| Recipe fix formu | `$${API_HOST:-0.0.0.0}` — Make `$$` escape'i shell POSIX `${VAR:-default}` parameter expansion'ı yaratır. `API_HOST` env'de varsa onu kullan; yoksa LAN wildcard'ı default kalır. |
| LAN intent korunur mu? | Evet — `API_HOST` set edilmezse recipe yine 0.0.0.0 binder; operatör explicit opt-in (`EXTRACE_ALLOW_LAN=1` env + `make dev-lan` target) ile LAN'a çıkar. |
| `dev` ve `run` davranışı? | Dokunulmaz. `--host 127.0.0.1` literal, env override'sız — loopback'in tüm noktası bu. Bu invariant yeni gate'in 2 case'inde pinlenir (regression koruma). |
| ADR 0007 banner'ı? | Korunur. Recipe `@echo "⚠️  ADR 0007 — LAN binding requested. ..."` literal'i değişmez; yeni gate'in 6. case'i bu literal'i pinler. |
| Production code etkisi | Hiç. `appcore/api/config.py` post-init mantığı zaten doğru (`test_explicit_host_override_wins_over_lan_substitution` W8-7'den beri yeşil). Sadece Makefile recipe + yeni architecture gate + runbook revizyonu. |

**Reverse-side reject rationale (Path B — drift'i mühürle).**

Reddedildi. Path B recipe'yi dokunulmaz kabul edip arch test'inde
"`dev-lan` mutlaka `--host 0.0.0.0` literal" assertion'ı takıyor ve
runbook'un caveat'ını kalıcı hâle getiriyordu. Lehte: production-yakın
hiç dosya değişmez. Aleyhte: (1) operatöre bilinen ergonomik ayağı
kopuk bırakır — `API_HOST` settings katmanında çalışıyor ama recipe'de
çalışmıyor, dokümante edilmiş ama tutarsız semantik; (2) Codex
recommendation'ı temizlik tarafına yatıyor. Path A 1-satırlık
değişiklik ile ekstra regression gate'i tek pakette getirir; her iki
maliyeti de aşağı çeker.

**Sub-commit Roadmap (5 commits — all targeting `week13`).**

| # | Commit | Touch | Status |
|---|---|---|---|
| 1 | `docs(W13-5): assign stable ID + lock in dev-lan recipe scope` | `documents/active-work/W13-test-expansion-observability.md`, `documents/REFACTOR_STATUS.md`, `documents/POST_POC_BACKLOG.md` | in progress (this commit) |
| 2 | `test(W13-5): RED precursor for Makefile dev-recipe binding gate` | `tests/architecture/test_makefile_dev_recipes.py` (new — 6 skip-marked cases) | not started |
| 3 | `feat(W13-5): Makefile dev-lan honors API_HOST override (RED→GREEN)` | `Makefile` (line 172 recipe fix), `tests/architecture/test_makefile_dev_recipes.py` (skip kaldır × 6) | not started |
| 4 | `docs(W13-5): runbook revision — dev-lan API_HOST override semantic` | `documents/runbooks/lan-exposure.md` (§Host-mode caveat removal, Last Updated bump) | not started |
| 5 | `docs(W13-5): close evidence + status sweep` | tracker close evidence, `REFACTOR_STATUS.md` bump, `POST_POC_BACKLOG.md` H3 strikethrough, `REFACTOR_OPTIMIZATION.md` §11.10 W13-5 closed bullet, `CLAUDE.md` + `AGENTS.md` header parity, `documents/active-work/README.md` next-pull pointer | not started |

**Architecture gates (W13-5.2/W13-5.3'te pinler).**

`tests/architecture/test_makefile_dev_recipes.py` (yeni dosya, 6 case):

| # | Case adı | Pin |
|---|---|---|
| 1 | `test_dev_recipe_binds_loopback_literal` | `dev:` recipe body'sinde `--host 127.0.0.1` literal, env override yok |
| 2 | `test_run_recipe_binds_loopback_literal` | `run:` recipe body'sinde `--host 127.0.0.1` literal |
| 3 | `test_dev_lan_recipe_sets_extrace_allow_lan` | `dev-lan:` recipe body'sinde `EXTRACE_ALLOW_LAN=1` set ediliyor |
| 4 | `test_dev_lan_recipe_honors_api_host_override` | `dev-lan:` body'sinde `--host` arg'ı `$${API_HOST:-…}` formunu içeriyor (Make-escape doğru) |
| 5 | `test_dev_lan_recipe_defaults_to_wildcard_host` | `dev-lan:` `${…:-0.0.0.0}` fallback'i `0.0.0.0` (LAN intent preserved) |
| 6 | `test_dev_lan_recipe_emits_adr_0007_warning` | `dev-lan:` `@echo "⚠️  ADR 0007 …"` banner literal'i var (operator signal preserved) |

**Verification plan.**

- W13-5.2 sonrası: `make test-local` 1492 → 1498 collected (+6 skipped); `tests/architecture/` 87 → 93 collected (+6 skipped, 0 yeni passed).
- W13-5.3 sonrası: `make test-local` 1492 → 1498 collected, **+6 passed** (skip kaldırıldı); `tests/architecture/` 87 → 93 passed; manuel smoke (opsiyonel): `API_HOST=127.0.0.2 make dev-lan` uvicorn log satırının `0.0.0.0` yerine `127.0.0.2` göstermesi.
- W13-5.4 sonrası: doc-only commit; sayılar değişmez.
- W13-5.5 sonrası: `make check-all` yeşil; W12 5/5 + W13-1 3/3 + W13-2 4/4 + W13-3 6/6 ratchet gate'leri intact; W13-5 6/6 yeni gate yeşil.
- `make test-security` 211 sabit boyunca (yeni test architecture lane'inde; security lane'i [Makefile:206-216](../../Makefile) test-security path listesinde yok).
- Production code untouched audit: `git diff --stat week13~5..HEAD -- appcore/ workflows/ executor/ packages/` boş çıkmalı.

**W13-5.1 close evidence (`1b637a1`).**

- [x] Stable ID `W13-5` atandı, scope kilitlendi (Path A recipe-fix).
- [x] Tracker güncellendi: header `Last Updated 2026-05-11` (W13-5 opened note); Status (Quick Glance) yeni W13-5 opened bullet'ı; Candidate Items table'da W13-5 satırı `in progress (2026-05-11)`; bu Per-Item Detail bloğu eklendi.
- [x] `documents/REFACTOR_STATUS.md` güncellendi: header bump + W13 Status table'da W13-5 satırı `in progress`.
- [x] `documents/POST_POC_BACKLOG.md` güncellendi: header bump + H3 satırı `in progress as W13-5`.
- [x] Baseline metrikleri yakalandı (W13-4 close evidence ile birebir): `pytest --collect-only -m "not smoke"` 1492 collected / 8 deselected; `tests/architecture/` 87 collected / 4 deselected (smoke); `make test-security` 211 trust (W13-4'te ölçüldü).
- [x] W12 + W13-1 + W13-2 + W13-3 + W13-4 ratchet gate'leri intact kalır (bu commit pure doc).
- [x] Production code dokunulmaz (`appcore/`, `workflows/`, `executor/`, `packages/`).

**Sub-commit landings (final hash table).**

| # | Commit | Konu | Test/doc dosyaları |
|---|--------|------|-------------------|
| 1 | `1b637a1` `docs(W13-5): assign stable ID + lock in dev-lan recipe scope` | Stable ID atama, scope kilitleme (Path A), Per-Item Detail bloğu açma | tracker, `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md` |
| 2 | `e67a2ff` `test(W13-5): RED precursor for Makefile dev-recipe binding gate` | 6 skip-marked case, parser helper (`_recipe_bodies`, `_body_text`) | `tests/architecture/test_makefile_dev_recipes.py` (NEW, 171 lines) |
| 3 | `70bc3d7` `feat(W13-5): Makefile dev-lan honors API_HOST override (RED→GREEN)` | `Makefile:172` 1-line recipe fix + 6 skip kaldırma + ruff hook unused `import pytest` cleanup | `Makefile`, `tests/architecture/test_makefile_dev_recipes.py` |
| 4 | `6aa4c36` `docs(W13-5): runbook revision — dev-lan API_HOST override semantic` | `lan-exposure.md` §Host-mode drift caveat removal + §Code References extension (yeni test dosyası entry'si) + Last Updated parenthetical | `documents/runbooks/lan-exposure.md` |
| 5 | (this) `docs(W13-5): close evidence + status sweep` | Tracker close evidence + final hash table; `REFACTOR_STATUS.md` W13 table closed; `POST_POC_BACKLOG.md` H3 strikethrough; `REFACTOR_OPTIMIZATION.md` §11.10 W13-5 closed bullet; `CLAUDE.md` + `AGENTS.md` header parity; `documents/active-work/README.md` next-pull pointer | tracker, `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, `REFACTOR_OPTIMIZATION.md`, `CLAUDE.md`, `AGENTS.md`, `documents/active-work/README.md` |

**W13-5.5 close evidence (this commit).**

- [x] **Test bar (final).** `make test-local` collect 1492 → 1498
  (+6 passed cases — `test_dev_recipe_binds_loopback_literal`,
  `test_run_recipe_binds_loopback_literal`,
  `test_dev_lan_recipe_sets_extrace_allow_lan`,
  `test_dev_lan_recipe_honors_api_host_override`,
  `test_dev_lan_recipe_defaults_to_wildcard_host`,
  `test_dev_lan_recipe_emits_adr_0007_warning`); 8 deselected
  unchanged. `make test-security` 211 sabit (yeni test
  architecture lane'inde; `make test-security` path listesinde
  yok). `tests/architecture/` 87 → 93 passed / 4 deselected
  (smoke unchanged).
- [x] **Production code dokunulmaz.** `git diff --stat
  week13~4..HEAD -- appcore/ workflows/ executor/ packages/ ui/
  alembic/` boş — yalnız `Makefile` (1 satır), 1 yeni test dosyası
  ve 4 doc dosyası dokundu.
- [x] **Architecture gate'leri korundu.** W12: 5/5 ✓
  (`test_executor_playwright_flat_file_count_limit`,
  `test_runner_main_under_loc_budget`,
  `test_runtime_capture_extension_host_*` × 2,
  `test_body_preview_assignments_are_redacted`,
  `test_all_runtime_dockerfiles_pin_base_images_by_digest`).
  W13-1: 3/3 ✓ (`test_harness_marker_auth.py`).
  W13-2: 4/4 ✓ (`test_executor_runtime_script_permissions.py`
  static + smoke).
  W13-3: 6/6 ✓ (`test_cancel_poll_points.py` × 2 +
  `test_job_state_invariants.py` × 4).
  **W13-5: 6/6 ✓** (`test_makefile_dev_recipes.py`).
- [x] **Threat coverage özeti.** Eskiden:
  `API_HOST=192.168.1.10 make dev-lan` çağrısı uvicorn'u `0.0.0.0`'a
  binder, `APISettings.HOST` ise post-init explicit-override
  branch'inden geçip `192.168.1.10`'a yerleşirdi — uvicorn ↔
  settings drift'i kalıcı, operatör darayım dediği halde wildcard'a
  açık kalır; tek sinyal runbook'taki caveat. Şimdi: Makefile shell
  parameter expansion `${API_HOST:-0.0.0.0}` env override'ı uvicorn
  `--host` argümanına doğrudan iletir; `--host 0.0.0.0` literal'i
  recipe'de yok, drift kapanır. Hem settings (`APISettings.HOST`,
  test_default_bindings.py 14 case) hem recipe
  (`test_makefile_dev_recipes.py` 6 case) katmanları birbirini
  yansıtır.
- [x] **Slim canonical doc sweep.** Tracker (this file),
  `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `REFACTOR_OPTIMIZATION.md` §11.10,
  `documents/active-work/README.md`, `CLAUDE.md`, `AGENTS.md`
  header parity güncellendi. Slim canonical satır sayıları 200
  altında — W13-5 için ayrı archive snapshot zorunlu değil
  (W13-4'ün `2026-05-11` snapshot'ı fresh).
- [x] **Branch policy korundu.** Tüm 5 commit `week13` üzerinde;
  yeni branch açılmadı. W12 patterni (tüm W12-N alt-iterasyonlar
  tek PR #18 ile main'e merge) W13-N için de geçerli — W13 close-out
  PR'ı M1/M9 (veya açıkça defer) sonrasında tek paket olarak açılır.
- [x] **Sıradaki iterasyon hazır.** W13 acceptance-bar'da kalan
  MEDIUM kalemler: `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]`
  (`packages/analysis_contracts/evidence.py:106-121`
  `redact_multiline_secrets()` private_key regex unanchored + lazy
  cross-line span → catastrophic backtracking; bounded scanner /
  size cap),
  `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]`
  (`executor/flows/playwright/runtime_capture/extension_host_strace_parse.py:60,70,78`
  `arguments_preview` `redact_secrets()` route'undan geçmiyor;
  W12-5 architecture gate scope'unu genişlet). Her ikisi de
  paralel branch'lerde land edilebilir veya W13-6/W13-7 olarak
  çekilir.

### W13-6 — `arguments_preview` redaction extension (Codex M9)

`Status: in progress (opened 2026-05-11)` ·
`Source: [FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]` ·
`Lane: [security-detection] [executor-runtime]`

**Bağlam.** Codex Cloud audit (`2026-05-10`) MEDIUM severity bulgusu:
[executor/flows/playwright/runtime_capture/extension_host_strace_parse.py:60,70,78](../../executor/flows/playwright/runtime_capture/extension_host_strace_parse.py)
`ProcessEvent.arguments_preview` alanını üç `clone/clone3/fork/vfork` +
`execve/execveat` + `chdir` callsite'ında set ediyor; her birinde
`_bounded_arguments_preview()` ([line 102-106](../../executor/flows/playwright/runtime_capture/extension_host_strace_parse.py))
factory'sinden geçiyor — ama factory **sadece truncate** ediyor, secret
redact etmiyor. Sonuç: strace tarafından yakalanan komut argümanları
(env-passed token, `-H "Authorization: Bearer …"` curl literali, file
path'inde gömülü API key, vb) `arguments_preview` alanı üzerinden
`ProcessEvent` → `EvidenceEvent.raw_context` → bundle JSON'a sızabilir.
W12-5 redaction architecture gate
[tests/architecture/test_network_body_preview_redaction.py](../../tests/architecture/test_network_body_preview_redaction.py)
yalnızca `request_body_preview` / `response_body_preview` alanlarını
kapsıyor (`TARGET_FIELD_NAMES = {"request_body_preview", "response_body_preview"}`,
[line 34](../../tests/architecture/test_network_body_preview_redaction.py));
`arguments_preview` aynı sıkılığa tabi değil. Bulgunun açık hedefi:
"redact `arguments_preview`; extend W12-5 architecture gate"
([POST_POC_BACKLOG.md:38](../POST_POC_BACKLOG.md)). W8-6 (`2026-04-29`)
`redact_secrets()` helper'ı zaten battle-tested (5 secret class: aws,
bearer, private_key, api_key, db_url; idempotent) — yeniden kullanmaya
hazır.

**Critical files.**

- [executor/flows/playwright/runtime_capture/extension_host_strace_parse.py:53-97](../../executor/flows/playwright/runtime_capture/extension_host_strace_parse.py) — üç callsite'ın `arguments_preview=...` assignment'ları (line 60, 70, 78). Hiçbiri `redact_secrets()` çağırmıyor.
- [executor/flows/playwright/runtime_capture/extension_host_strace_parse.py:102-106](../../executor/flows/playwright/runtime_capture/extension_host_strace_parse.py) — `_bounded_arguments_preview(raw: str) -> str` helper. Mevcut: whitespace-normalize + truncate (`_PROCESS_ARGUMENT_PREVIEW` cap). Fix: önce `redact_secrets()`, sonra truncate (factory-internal redaction).
- [packages/analysis_contracts/evidence.py:84-91](../../packages/analysis_contracts/evidence.py) — `redact_secrets(value: str) -> str` helper. W8-6'dan beri 5 secret class pattern'ini idempotent uygular. Reuse hedefi.
- `tests/architecture/test_arguments_preview_redaction.py` (YENİ — sub-commit 2) — W12-5 gate replikası. Yapı: W12-5 `test_network_body_preview_redaction.py:1-142` AST scan'ini birebir kopyala, `TARGET_FIELD_NAMES = {"arguments_preview"}`, `ALLOWED_FACTORY_CALLS = {"_bounded_arguments_preview"}`, `ALLOWED_PASSTHROUGH_SOURCES = {"process_event", "evidence_event", "event", "payload"}`. Sub-commit 2'de skip-marked, sub-commit 3'te GREEN.
- [tests/architecture/test_network_body_preview_redaction.py:1-142](../../tests/architecture/test_network_body_preview_redaction.py) — W12-5 gate prototipi; **değiştirilmez**, sadece referans.
- [tests/executor/test_playwright_extension_host.py:240-281](../../tests/executor/test_playwright_extension_host.py) — `test_parse_strace_bounded_arguments_preview_truncates_long_args` truncation davranışını pinler; bu sub-iterasyon redaction kuzeni ekler (`test_parse_strace_event_arguments_preview_redacts_secrets`).

**Design decision locked-in: factory-internal redaction.**

`_bounded_arguments_preview()` body'sini değiştir:

| Sıra | Adım | Rasyonalizasyon |
|---|---|---|
| 1 | `redacted = redact_secrets(raw)` | Secret pattern'leri (aws/bearer/api_key/db_url/private_key) önce `[REDACTED:…]` placeholder'ına sweep edilir. Pattern'ler single-line; strace argument string'i single-line olduğu için cross-line risk yok. |
| 2 | `preview = " ".join(redacted.split())` | W8-1 whitespace normalize; placeholder'ları korur (placeholder içinde whitespace yok). |
| 3 | `return preview` veya `preview[: cap-3] + "..."` | Mevcut truncation davranışı korunur; `[REDACTED:…]` literal'i truncation'a tabi (long placeholder + uzun argümanlar). |

| Boyut | Karar |
|---|---|
| Tek chokepoint mu? | Evet — `_bounded_arguments_preview()` 3 callsite tarafından çağrılır; bu fonksiyonun içine girince 3 assignment otomatik kapsanır. Architecture gate `ALLOWED_FACTORY_CALLS = {"_bounded_arguments_preview"}` ile 3 callsite GREEN kalır. |
| Idempotency? | `redact_secrets()` idempotent ([evidence.py:84-91](../../packages/analysis_contracts/evidence.py) `for _class, pattern, replacement in _REDACTION_PATTERNS: redacted = pattern.sub(replacement, redacted)`). Tekrar uygulansa bile placeholder'ları tekrar match-edip bozmaz. |
| Double-redaction riski? | Yok — truncation sonrası `"..."` suffix'i 5 pattern'in hiçbirinin literal'ini match etmez (`...` ne aws ne bearer ne api_key ne db_url ne private_key marker'ı). Truncate sonrası `redact_secrets()` ikinci kez çağrılmaz; sadece factory girişinde 1× uygulanır. |
| Truncation order: pre veya post-redact? | **Pre-redact yasak**. Pre-truncate, secret pattern'in ortasında "..." kesimi sayesinde redaction'ı kaçırabilir (örn. `Bearer abcdef...` truncate edilirse `bearer` regex'i `\b…[A-Za-z0-9._\-+/=]{8,}\b` minimum 8 char threshold'una hâlâ uyabilir ama `...` token'ı kalıntı bırakır). **Post-redact** (önce redact, sonra truncate) güvenli: secret tüm uzunluğuyla yakalanır, placeholder kısalır gerekirse. |
| Schema değişimi var mı? | Yok. `ProcessEvent.arguments_preview` field tipi `str`, max boundary aynı. Consumer code (attribution, evidence bundle JSON) salt-okur — value-layer redaction transparent. |
| Production diff size? | Tek dosya, tek fonksiyon, ~3 satır. `import` ekleniyor (`redact_secrets`). |

**Reverse-side reject rationale (Path B — call-site wrapping).**

Reddedildi. Path B her 3 callsite'a (line 60, 70, 78) `redact_secrets(_bounded_arguments_preview(...))` wrap eder; factory dokunulmaz kalır. Lehte: factory pure stays "şekil-bozma" responsibility'sinde, redaction caller'a düşer (explicit dependency injection diye okunabilir). Aleyhte: (1) Üç callsite, üç bakım noktası — gelecekteki dördüncü `arguments_preview` assignment'ı (ör. yeni syscall variant) wrap'i kolayca unutabilir; gate violation üretir ama o ana kadar prod'da secret leak'i yaşanır. (2) Architecture gate'i daha karmaşık: `ALLOWED_FACTORY_CALLS` `_bounded_arguments_preview`'i kabul etmek için factory'nin kendisi `redact_secrets()` çağırmalı; aksi takdirde gate `_bounded_arguments_preview(...)` callsite'ını ham olarak GREEN sayar ve secret leak'i geçer. Path A (factory-internal) bu zayıflığı kapatır: factory `redact_secrets()` çağırırsa, gate `_bounded_arguments_preview`'i güvenli factory listesine ekleyebilir ve callsite'lar trivially GREEN olur. (3) W12-5 emsalindeki `_bounded_body_metadata()` factory'si zaten redaction'ı içinden uyguluyor ([runtime_capture/network.py:140-158](../../executor/flows/playwright/runtime_capture/network.py)) — Path A bu pattern'i yansıtır, tutarlılık kazanılır.

**Sub-commit Roadmap (5 commits — all targeting `week13`).**

| # | Commit | Touch | Status |
|---|---|---|---|
| 1 | `docs(W13-6): assign stable ID + lock in arguments_preview redaction scope` | `documents/active-work/W13-test-expansion-observability.md`, `documents/REFACTOR_STATUS.md`, `documents/POST_POC_BACKLOG.md` | landed `94f7fa4` |
| 2 | `test(W13-6): RED precursor for arguments_preview redaction gate + regression` | `tests/architecture/test_arguments_preview_redaction.py` (new, 2 invariants — 1 skip-marked), `tests/executor/test_playwright_extension_host.py` (`import pytest` + 5-case parametrized regression skip-marked) | landed `70ad721` |
| 3 | `feat(W13-6): _bounded_arguments_preview applies redact_secrets (RED→GREEN)` | `executor/flows/playwright/runtime_capture/extension_host_strace_parse.py` (factory body fix + `redact_secrets` import), `tests/architecture/test_arguments_preview_redaction.py` (skip + unused `pytest` import kaldır), `tests/executor/test_playwright_extension_host.py` (skip kaldır × 1 parametrize) | landed `9f8ecb4` |
| 4 | `docs(W13-6): close evidence + status sweep` | tracker close evidence + final hash table, `REFACTOR_STATUS.md` W13-6 row → closed, `POST_POC_BACKLOG.md` M9 strikethrough | in progress (this commit) |
| 5 | `docs(W13-6): align lagging canonicals with W13-6 closure` | `REFACTOR_OPTIMIZATION.md` §11.10 W13-6 closed bullet, `documents/active-work/README.md` next-pull pointer, `documents/automation_todo.md` header bump, `CLAUDE.md` + `AGENTS.md` header parity | not started |

**Architecture gates (W13-6.2/W13-6.3'te pinler).**

`tests/architecture/test_arguments_preview_redaction.py` (yeni dosya, 1 case AST scan):

| # | Case adı | Pin |
|---|---|---|
| 1 | `test_arguments_preview_assignments_are_redacted` | `executor/`, `packages/`, `workflows/` ağacında `arguments_preview` keyword/attr/subscript assignment'larının tamamı ya doğrudan `redact_secrets()` çağrısı, ya `_bounded_arguments_preview()` factory subscript'i, ya da whitelisted passthrough source (`process_event`, `evidence_event`, `event`, `payload`) attribute'u olmak zorunda |

`tests/executor/test_playwright_extension_host.py` regression — parametrized:

| # | Case adı | Pin |
|---|---|---|
| 1-N | `test_parse_strace_event_arguments_preview_redacts_secrets[<class>]` | strace line input'unda 5 secret class (aws, bearer, api_key, db_url, private_key — single-line tetikleyici versiyonları) tek tek; her case için `ProcessEvent.arguments_preview` çıktısı `[REDACTED:<class>]` placeholder içermeli, ham secret içermemeli |

**Verification plan.**

- W13-6.2 sonrası: `make test-local` 1498 → 1498+N collected (+ (1 + N) skipped); `tests/architecture/` 93 → 94 collected (+1 skipped, 0 yeni passed).
- W13-6.3 sonrası: `make test-local` 1498+N collected, **+(1 + N) passed** (skip kaldırıldı); `tests/architecture/` 93 → 94 passed; `make test-security` 211 sabit (yeni arch test, security lane'inde değil).
- W13-6.4 sonrası: doc-only commit; sayılar değişmez.
- W13-6.5 sonrası: `make check-all` yeşil; W12 5/5 + W13-1 3/3 + W13-2 4/4 + W13-3 6/6 + W13-5 6/6 ratchet gate'leri intact; W13-6 1 yeni arch gate + N regression case yeşil.
- Production code diff hedefi: yalnızca [extension_host_strace_parse.py](../../executor/flows/playwright/runtime_capture/extension_host_strace_parse.py) (1 import + 1 fonksiyon body). `appcore/`, `workflows/`, `ui/`, `alembic/` zero diff.

**W13-6.1 close evidence (`94f7fa4`).**

- [x] Stable ID `W13-6` atandı, scope kilitlendi (Path A factory-internal redaction).
- [x] Tracker güncellendi: header `Last Updated 2026-05-11` (W13-6 opened note); Status (Quick Glance) yeni W13-6 opened bullet'ı + next-pull pointer M1 → W13-7; Candidate Items table'da M9 satırı `**W13-6**` `in progress (2026-05-11)`; bu Per-Item Detail bloğu eklendi.
- [x] `documents/REFACTOR_STATUS.md` güncellendi: header bump + W13 Status table'da M9 satırı `W13-6 in progress`.
- [x] `documents/POST_POC_BACKLOG.md` güncellendi: header bump + W13 Pull-Forward table'da M9 satırı `in progress as W13-6`.
- [x] Baseline metrikleri (W13-5 close evidence ile birebir): `make test-local` 1498 collected / 8 deselected; `tests/architecture/` 93 collected / 4 deselected (smoke); `make test-security` 211 trust (W13-5'te ölçüldü).
- [x] W12 + W13-1 + W13-2 + W13-3 + W13-4 + W13-5 ratchet gate'leri intact kalır (bu commit pure doc).
- [x] Production code dokunulmaz (`appcore/`, `workflows/`, `executor/`, `packages/`, `ui/`, `alembic/`).

**Sub-commit landings (final hash table).**

| # | Commit | Konu | Test/doc dosyaları |
|---|--------|------|-------------------|
| 1 | `94f7fa4` `docs(W13-6): assign stable ID + lock in arguments_preview redaction scope` | Stable ID atama, scope kilitleme (Path A factory-internal redaction), Per-Item Detail bloğu açma | tracker, `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md` |
| 2 | `70ad721` `test(W13-6): RED precursor for arguments_preview redaction gate + regression` | Yeni `tests/architecture/test_arguments_preview_redaction.py` (2 invariant: factory body Call check skip-marked + routing scan immediately GREEN; 222 satır), `tests/executor/test_playwright_extension_host.py`'a 5-case parametrize skip-marked + `import pytest`. PEM literal'i runtime concat (detect-private-key hook'unu trip etmez). RED state: 30 passed / 6 skipped (1 arch + 5 regression). | `tests/architecture/test_arguments_preview_redaction.py` (NEW), `tests/executor/test_playwright_extension_host.py` |
| 3 | `9f8ecb4` `feat(W13-6): _bounded_arguments_preview applies redact_secrets (RED→GREEN)` | `_bounded_arguments_preview()` body'sine `redact_secrets()` çağrısı eklendi (pre-redact + post-truncate sırası; placeholder kesimini engeller); `from packages.analysis_contracts.evidence import redact_secrets` (sister `network.py:12` import yolu). 2 dosyada `@pytest.mark.skip` kaldırıldı, ruff unused `import pytest`'i temizledi. | `executor/flows/playwright/runtime_capture/extension_host_strace_parse.py`, `tests/architecture/test_arguments_preview_redaction.py`, `tests/executor/test_playwright_extension_host.py` |
| 4 | (this) `docs(W13-6): close evidence + status sweep` | Tracker close evidence + final hash table; `REFACTOR_STATUS.md` W13 table closed; `POST_POC_BACKLOG.md` M9 strikethrough | tracker, `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md` |
| 5 | (next) `docs(W13-6): align lagging canonicals with W13-6 closure` | `REFACTOR_OPTIMIZATION.md` §11.10 W13-6 closed bullet, `CLAUDE.md` + `AGENTS.md` header parity, `documents/active-work/README.md` next-pull pointer, `documents/automation_todo.md` header bump | `REFACTOR_OPTIMIZATION.md`, `CLAUDE.md`, `AGENTS.md`, `documents/active-work/README.md`, `documents/automation_todo.md` |

**W13-6.4 close evidence (this commit).**

- [x] **Test bar (final).** `.venv/bin/pytest -q` → 1498 passed /
  7 skipped / 8 deselected / 75 warnings (`make test-local` equivalent).
  Pre-W13-6 baseline 1491 passed + 7 newly passing W13-6 case
  (`test_arguments_preview_factory_applies_redact_secrets`,
  `test_arguments_preview_assignments_are_redacted`,
  `test_parse_strace_event_arguments_preview_redacts_secrets[aws]`,
  `[bearer]`, `[api_key]`, `[db_url]`, `[private_key]`). 7 skip
  baseline ile aynı: 1 W13-4.5 alembic deferral (`tests/platform/storage/test_alembic_cancelling_migration.py`)
  plus 6 canary baseline (`tests/security/test_canary_end_to_end.py`).
  Collected 1498 → 1505 / 8 deselected (smoke unchanged).
  `make test-security` 211 trust (yeni testler architecture + executor
  lane'lerinde, security lane'inde değil). `tests/architecture/`
  93 → 95 passed / 4 deselected (smoke unchanged) — yeni W13-6 case'lerin
  arch surface'i.
- [x] **Production code diff dar.** `git diff --stat 8856ba0..HEAD -- appcore/ workflows/ executor/ packages/ ui/ alembic/`
  yalnızca `executor/flows/playwright/runtime_capture/extension_host_strace_parse.py`
  döner (+4 net satır: 1 `redact_secrets` import + 1 yorum + 1 redact
  çağrısı + factory body fix). `appcore/`, `workflows/`, `packages/`,
  `ui/`, `alembic/` zero diff.
- [x] **Architecture gate'leri korundu.** W12: 5/5 ✓
  (`test_executor_playwright_flat_file_count_limit`,
  `test_runner_main_under_loc_budget`,
  `test_runtime_capture_extension_host_*` × 2,
  `test_body_preview_assignments_are_redacted`,
  `test_all_runtime_dockerfiles_pin_base_images_by_digest`).
  W13-1: 3/3 ✓ (`test_harness_marker_auth.py`).
  W13-2: 4/4 ✓ (`test_executor_runtime_script_permissions.py` static + smoke).
  W13-3: 6/6 ✓ (`test_cancel_poll_points.py` × 2 +
  `test_job_state_invariants.py` × 4).
  W13-5: 6/6 ✓ (`test_makefile_dev_recipes.py`).
  **W13-6: 2/2 ✓** (`test_arguments_preview_redaction.py`) +
  5 regression cases ✓ (`test_parse_strace_event_arguments_preview_redacts_secrets`).
- [x] **Threat coverage özeti.** Eskiden: strace tarafından yakalanan
  process spawn/exec/chdir argümanları `arguments_preview` üzerinden
  `ProcessEvent.raw_context` → bundle JSON'a sızabilirdi (env-passed
  token, curl `Bearer …` literal'i, file path'inde gömülü API key,
  `postgresql://user:secret@host/db` connection string, single-line
  PEM payload). W12-5 architecture gate ise yalnızca
  `request_body_preview` / `response_body_preview`'i kapsadığı için
  bu yüzey sıkılığa tabi değildi. Şimdi: `_bounded_arguments_preview()`
  factory'si W8-6 `redact_secrets()` helper'ını uygular; 3 çağrı
  sitesi (clone/exec/chdir) tek chokepoint'ten geçer. Yeni
  architecture gate hem routing'i (assignment'lar safe-source'tan
  gelmeli) hem factory body'sini (`redact_secrets` Call mecburi)
  pinler — gelecekteki 4. assignment ya da factory hatasını
  yakalanabilir hâle getirir. Parametrized regression 5 secret class
  pattern'ini end-to-end strace satırı üzerinden doğrular.
- [x] **Slim canonical doc sweep.** Tracker (this file),
  `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md` güncellendi. Slim
  canonical satır sayıları 200 altında kalır — W13-6 için ayrı
  archive snapshot zorunlu değil. `REFACTOR_OPTIMIZATION.md` §11.10,
  `CLAUDE.md`, `AGENTS.md`, `documents/active-work/README.md`,
  `documents/automation_todo.md` sweep'i sub-commit 5'e bırakılır
  (W13-5 5/5 patterninin birebir replikası).
- [x] **Branch policy korundu.** Tüm 4 commit (sub-commit 1-4) `week13`
  üzerinde; yeni branch açılmadı. Sub-commit 5 sonrası W13-6/W13-7
  ratchet'leri ile birlikte tek W13 close-out PR'ı `week13 → main`
  açılır (W12 PR #18 pattern'i).
- [x] **Sıradaki iterasyon hazır.** W13 acceptance-bar'da kalan tek
  MEDIUM kalem: `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]`
  ([packages/analysis_contracts/evidence.py:56-63](../../packages/analysis_contracts/evidence.py))
  `redact_multiline_secrets()` private_key regex unanchored + lazy
  cross-line span `(?:.|\n)*?` → catastrophic backtracking on many
  unmatched BEGIN markers. W13-7 olarak çekilecek (bounded scanner
  veya size cap; W13-5 / W13-6 sub-commit roadmap pattern'i).

### W13-7 — PEM regex DoS bounded scanner (Codex M1)

`Status: in progress (opened 2026-05-11)` ·
`Source: [FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]` ·
`Lane: [security-detection]`

**Bağlam.** Codex Cloud audit (`2026-05-10`) MEDIUM severity bulgusu:
[packages/analysis_contracts/evidence.py:56-63](../../packages/analysis_contracts/evidence.py)
`private_key` regex pattern'i unanchored + lazy `(?:.|\n)*?` cross-line
span içeriyor:

```python
re.compile(
    r"-----BEGIN[ A-Z0-9]*PRIVATE KEY-----"
    r"(?:.|\n)*?"
    r"-----END[ A-Z0-9]*PRIVATE KEY-----",
)
```

Bu pattern, `redact_multiline_secrets()` ([line 106-121](../../packages/analysis_contracts/evidence.py))
içinden `pattern.sub()` ile çağrıldığında, BEGIN marker'ı bulup END
ararken çok sayıda eşleşmemiş BEGIN markerlı adversarial input üzerinde
quadratic O(N×L) tarama yapar. Her BEGIN pozisyonundan ileriye doğru
END ararken `(?:.|\n)*?` lazy quantifier'ı tüm pozisyon
kombinasyonlarını dener. Sonuç: target extension stdout'una
`-----BEGIN PRIVATE KEY-----` literal'leri stuff etmek
`redact_multiline_secrets()` latency'sini sub-saniye seviyesine
çıkarabilir; çağrı 3 yerden geliyor (analysis pipeline başına 3×
sub() çağrısı).

**Empirik latency ölçümü (`2026-05-11`, pre-fix).**

```python
import re, time
pattern = re.compile(
    r"-----BEGIN[ A-Z0-9]*PRIVATE KEY-----"
    r"(?:.|\n)*?"
    r"-----END[ A-Z0-9]*PRIVATE KEY-----"
)
mal = ('-----BEGIN PRIVATE KEY-----\n' + 'x' * 1000) * 200  # 200 BEGIN, no END
elapsed = time.perf_counter(); pattern.sub('[REDACTED:pk]', mal); print(time.perf_counter() - elapsed)
# → 361.21 ms / call
```

500 BEGIN + 5KB/each + no END ölçeklenirse latency saniyeye çıkar.
Production hot-path'te bu, target extension'ın kasıtlı tetiklediği
DoS vector'üdür.

**W12-0 kontekst.** Bu regex W12-0 (`2026-05-07`) altında output-signal
redaction için eklenmişti. Codex Cloud audit (`2026-05-10`) `aynı kodu`
DoS açısından işaretledi; W13-7 follow-up'ı bu vector'ü kapatır.

**Critical files.**

- [packages/analysis_contracts/evidence.py:56-63](../../packages/analysis_contracts/evidence.py) — `_REDACTION_PATTERNS` tuple içindeki `private_key` regex (lazy `(?:.|\n)*?`). Pattern dokümante kalır (single-line single-call davranışı tüketicisiz olduğu için fonksiyonel değil — `_CROSS_LINE_CLASSES`'in tek üyesi).
- [packages/analysis_contracts/evidence.py:106-121](../../packages/analysis_contracts/evidence.py) — `redact_multiline_secrets()` body. Bu fonksiyon yeniden yazılır: private_key sınıfı için bounded scanner ile değiştirilir; diğer single-line pattern'ler `_CROSS_LINE_CLASSES`'da olmadığı için zaten skip.
- [executor/flows/playwright/signals/output.py:39,120,237](../../executor/flows/playwright/signals/output.py) — `redact_multiline_secrets` 2 callsite. **Dokunulmaz** — yalnızca çağrı imzası korunur (`str -> str` davranışı identik, semantik korunur).
- [workflows/marketplace/analysis_execution.py:18,97](../../workflows/marketplace/analysis_execution.py) — `redact_multiline_secrets` 1 callsite. **Dokunulmaz**.
- [tests/platform/security/test_output_signals_redaction.py](../../tests/platform/security/test_output_signals_redaction.py) — mevcut 4 PEM case (W12-0 happy path + cross-line variants) korunur, regression eder. Yeni timing case sub-commit 2'de eklenir.

**Design decision locked-in: bounded scanner (regex'siz cross-line iterasyon).**

`redact_multiline_secrets()` private_key sınıfı için manuel linear scanner kullanılır:

```python
_PRIVATE_KEY_BEGIN_RE = re.compile(r"-----BEGIN[ A-Z0-9]*PRIVATE KEY-----")
_PRIVATE_KEY_END_RE = re.compile(r"-----END[ A-Z0-9]*PRIVATE KEY-----")
_PRIVATE_KEY_MAX_BODY = 16 * 1024  # 16 KB cap — real PEM keys are <4 KB

def _redact_private_key_bounded(value: str) -> str:
    placeholder = "[REDACTED:private_key]"
    out, pos = [], 0
    while True:
        begin = _PRIVATE_KEY_BEGIN_RE.search(value, pos)
        if begin is None:
            out.append(value[pos:])
            break
        out.append(value[pos:begin.start()])
        end_search_start = begin.end()
        end_search_end = min(end_search_start + _PRIVATE_KEY_MAX_BODY, len(value))
        end = _PRIVATE_KEY_END_RE.search(value, end_search_start, end_search_end)
        if end is None:
            out.append(begin.group())
            pos = begin.end()
        else:
            out.append(placeholder)
            pos = end.end()
    return "".join(out)
```

| Boyut | Karar |
|---|---|
| Complexity | O(L) — string'i en fazla 1× tararız; her BEGIN'de en fazla 16 KB window scan. Adversarial input'la quadratic explosion yok. |
| Window cap | 16 KB. Real PEM private keys (RSA 4096, EC, Ed25519) <4 KB; X.509 cert chain'leri <8 KB. 16 KB güvenli marj — gerçek-dünya redaction'ı bozmaz, pathological case'i sınırlar. |
| Semantic drift | Cap dışındaki END'i bulamayan BEGIN, `[REDACTED:private_key]`'a swap edilmez (BEGIN literal kalır). Bu davranış değişikliği — mevcut regex bütün uzaklıktaki END'i de bulurdu (yavaş olsa da). **Trade-off:** real-world key boyutlarında pratik fark yok; adversarial 16 KB+ "spread" key blocks artık partial-redact olur. Audit risk düşük (gerçek 16 KB+ tek-parça PEM yok). |
| Regex pattern tuple | `_REDACTION_PATTERNS` içindeki `private_key` entry'si dokümantasyon amaçlı kalır (signature semantik kayıt); `redact_secrets()` zaten cross-line sınıfını skip eder. `redact_multiline_secrets()` body'sinde regex.sub() değil bounded scanner çağrılır. |
| Public API change? | Yok. `redact_multiline_secrets(value: str) → str` signature ve "no key, no diff" semantiği korunur. |
| Production diff size? | Tek dosya, ~40 satır net (yeni helper + body değişikliği + 2 yeni private regex tanımı). |

**Reverse-side reject rationale (Path B — re.UNICODE flag / atomic group).**

Reddedildi. Python `re` modülü atomic group / possessive quantifier desteklemiyor (Python 3.11+ `re` yeni `*+` syntax'ı var ama runtime semantik test gerek + 3.12 compat audit). Alternative pattern: `(?>.|\n)*?` (atomic non-capturing) Python `re`'de syntax error. `regex` 3rd-party kütüphanesini introduce etmek `pyproject.toml` + dependency policy violation (AGENTS.md "Do not introduce dependencies without explicit approval"). Path A bounded scanner stdlib `re` ile kalır, dependency yok.

**Reverse-side reject rationale (Path C — size cap olarak truncate input).**

Reddedildi. Input boyutunu redaction'dan önce N MB'a cap'lemek (`value[:MAX]`) DoS'u çözer ama legitimate uzun stdout'u (örn. büyük marketplace VSIX install log'u, valid PEM dahil) keser. Bounded scanner yalnızca BEGIN→END window'unu sınırlar, geri kalan stream'i normal işler — daha temiz.

**Sub-commit Roadmap (5 commits — all targeting `week13`).**

| # | Commit | Touch | Status |
|---|---|---|---|
| 1 | `docs(W13-7): assign stable ID + lock in PEM bounded scanner scope` | `documents/active-work/W13-test-expansion-observability.md`, `documents/REFACTOR_STATUS.md`, `documents/POST_POC_BACKLOG.md`, `.pre-commit-config.yaml` (W13-7 tracker → detect-private-key exclude — honeypot/redaction emsali ile aynı muafiyet sınıfı) | landed `bf9f110` |
| 2 | `test(W13-7): RED precursor for PEM regex DoS bounded latency` | `tests/platform/security/test_output_signals_redaction.py` (1 yeni timing case skip-marked, `redact_multiline_secrets` import added) | landed `9844192` |
| 3 | `feat(W13-7): redact_multiline_secrets uses bounded scanner (RED→GREEN)` | `packages/analysis_contracts/evidence.py` (`_PRIVATE_KEY_BEGIN_RE` / `_PRIVATE_KEY_END_RE` / `_PRIVATE_KEY_MAX_BODY` / `_PRIVATE_KEY_PLACEHOLDER` constants + `_redact_private_key_bounded` helper + `redact_multiline_secrets` body refactored), `tests/platform/security/test_output_signals_redaction.py` (skip kaldır × 1) | landed `3b16c01` |
| 4 | `docs(W13-7): close evidence + status sweep` | tracker close evidence + final hash table, `REFACTOR_STATUS.md` W13-7 row → closed, `POST_POC_BACKLOG.md` M1 strikethrough | in progress (this commit) |
| 5 | `docs(W13-7): align lagging canonicals with W13-7 closure` | `REFACTOR_OPTIMIZATION.md` §11.10 W13-7 closed bullet + §11.14 exit criteria, `documents/active-work/README.md` next-pull pointer, `documents/automation_todo.md` header bump, `CLAUDE.md` + `AGENTS.md` header parity | not started |

**Architecture gate (W13-7.2/W13-7.3'te pinler).**

Tek timing-based behavioral test (mevcut `tests/platform/security/test_output_signals_redaction.py` içine eklenir):

| # | Case adı | Pin |
|---|---|---|
| 1 | `test_redact_multiline_secrets_rejects_catastrophic_pem_pattern` | Adversarial input (200 BEGIN markers + 1 KB body each + no END → ~200 KB) → `redact_multiline_secrets()` latency'si <100 ms olmalı; placeholder doğrudan yokluk garantisi (BEGIN→END yok → redaction beklemiyoruz; eğer çıktıda hâlâ BEGIN literal'leri varsa benign — bounded scanner cap'i sebebiyle). Pre-fix: ~361 ms (FAIL). Post-fix bounded scanner: <10 ms (PASS). |

Plus, mevcut 4 PEM case (`test_install_failure_message_redacts_multiline_pem_split_by_tail`,
`test_read_output_channel_logs_redacts_multiline_pem_block`,
`test_read_output_channel_logs_multiline_pem_with_surrounding_lines`,
`test_parse_output_signal_events_redacts_cross_marker_pem_block`,
`test_parse_output_signal_events_single_marker_multiline_pem`)
regression eder — bounded scanner identik replacement semantics yapar, mevcut tests pass.

**Verification plan.**

- W13-7.2 sonrası: `make test-local` 1505 → 1506 collected (+1 skipped); `tests/platform/security/` koleksiyonu +1.
- W13-7.3 sonrası: `make test-local` 1506 collected, **+1 passed** (skip kaldırıldı, 1499 → 1499 net... wait: 1498 passed + 1 newly passed = 1499 passed total post-fix). Mevcut 4 PEM case unchanged.
- W13-7.4 sonrası: doc-only commit; sayılar değişmez.
- W13-7.5 sonrası: `make check-all` yeşil; W12 5/5 + W13-1 3/3 + W13-2 4/4 + W13-3 6/6 + W13-5 6/6 + W13-6 2/2 + 5 regression ratchet gate'leri intact; W13-7 1 yeni timing case yeşil.
- `make test-security` 211 → 212 (yeni case `tests/platform/security/` lane'inde, security path listesinde — [Makefile:206-216](../../Makefile)).
- Production code diff hedefi: yalnızca [evidence.py](../../packages/analysis_contracts/evidence.py) (3 yeni constant + 1 yeni helper + 1 fonksiyon body değişikliği).
- Manuel adversarial smoke: `python -c "from packages.analysis_contracts.evidence import redact_multiline_secrets; import time; mal='-----BEGIN PRIVATE KEY-----\n' + 'x'*1000; mal=mal*200; t=time.perf_counter(); r=redact_multiline_secrets(mal); print(time.perf_counter()-t)"` < 50 ms beklenir.

**W13-7.1 close evidence (`bf9f110`).**

- [x] Stable ID `W13-7` atandı, scope kilitlendi (Path A bounded scanner; Path B atomic-group reddedildi — Python `re` desteklemiyor; Path C input cap reddedildi — legitimate uzun stream'i bozar).
- [x] Tracker güncellendi: header `Last Updated 2026-05-11` (W13-7 opened note); Status (Quick Glance) yeni W13-7 opened bullet'ı + W13-1..W13-6 closed; next-pull = W13 close-out PR; Candidate Items table'da M1 satırı `**W13-7**` `in progress (2026-05-11)`; bu Per-Item Detail bloğu eklendi.
- [x] `documents/REFACTOR_STATUS.md` güncellendi: header bump + W13 Status table'da M1 satırı `W13-7 in progress`.
- [x] `documents/POST_POC_BACKLOG.md` güncellendi: header bump + W13 Pull-Forward table'da M1 satırı `in progress as W13-7`.
- [x] `.pre-commit-config.yaml` `detect-private-key` exclude listesine tracker eklendi (W11-monitor-lifecycle.md ile aynı muafiyet sınıfı — honeypot/redaction emsali pattern paylaşır).
- [x] Empirik pre-fix ReDoS latency ölçüldü (`2026-05-11`): 200 BEGIN markers + 1 KB body each + no END ile `pattern.sub()` 361 ms. Bounded scanner sub-commit 3 sonrası post-fix latency'sini sub-commit 2'nin timing case'i pinler.
- [x] Baseline metrikleri (W13-6 close evidence ile birebir): `make test-local` 1505 collected / 8 deselected; `tests/architecture/` 95 collected / 4 deselected (smoke); `make test-security` 211 sabit (yeni timing case `tests/platform/security/` lane'inde — sub-commit 2 sonrasında 212'ye çıkar).
- [x] W12 + W13-1 + W13-2 + W13-3 + W13-4 + W13-5 + W13-6 ratchet gate'leri intact kalır (bu commit pure doc).
- [x] Production code dokunulmaz (`appcore/`, `workflows/`, `executor/`, `packages/`, `ui/`, `alembic/`).

**Sub-commit landings (final hash table).**

| # | Commit | Konu | Test/doc dosyaları |
|---|--------|------|-------------------|
| 1 | `bf9f110` `docs(W13-7): assign stable ID + lock in PEM bounded scanner scope` | Stable ID atama, scope kilitleme (Path A bounded scanner; Path B atomic-group ve Path C input cap reddedildi), empirik pre-fix latency ölçümü (361 ms) kayıt | tracker, `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, `.pre-commit-config.yaml` (tracker exclude eklendi) |
| 2 | `9844192` `test(W13-7): RED precursor for PEM regex DoS bounded latency` | `tests/platform/security/test_output_signals_redaction.py`'a 1 timing case skip-marked (`test_redact_multiline_secrets_rejects_catastrophic_pem_pattern`). Adversarial: 200 BEGIN + 1 KB body each + no END. Threshold <100 ms. `redact_multiline_secrets` import line 37'ye eklendi. RED state: 24 passed + 1 skipped. | `tests/platform/security/test_output_signals_redaction.py` |
| 3 | `3b16c01` `feat(W13-7): redact_multiline_secrets uses bounded scanner (RED→GREEN)` | `evidence.py`'a 4 yeni constant + `_redact_private_key_bounded(value)` helper eklendi (linear O(L), 16 KB window cap). `redact_multiline_secrets()` body'si yalnızca yeni helper'ı çağırır. Test skip kaldırıldı. Adversarial smoke: 361 ms → 1.29 ms (~280× speedup); happy path identical semantics. | `packages/analysis_contracts/evidence.py`, `tests/platform/security/test_output_signals_redaction.py` |
| 4 | (this) `docs(W13-7): close evidence + status sweep` | Tracker close evidence + final hash table; `REFACTOR_STATUS.md` W13 table closed; `POST_POC_BACKLOG.md` M1 strikethrough | tracker, `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md` |
| 5 | (next) `docs(W13-7): align lagging canonicals with W13-7 closure` | `REFACTOR_OPTIMIZATION.md` §11.10 + §11.14 W13-7 closed bullet, `CLAUDE.md` + `AGENTS.md` header parity, `documents/active-work/README.md` next-pull pointer (W13 close-out PR), `documents/automation_todo.md` header bump | `REFACTOR_OPTIMIZATION.md`, `CLAUDE.md`, `AGENTS.md`, `documents/active-work/README.md`, `documents/automation_todo.md` |

**W13-7.4 close evidence (this commit).**

- [x] **Test bar (final).** `.venv/bin/pytest -q` → 1499 passed / 7
  skipped / 8 deselected / 75 warnings (`make test-local` equivalent).
  Pre-W13-7 baseline 1498 passed + 1 newly passing W13-7 timing case
  (`test_redact_multiline_secrets_rejects_catastrophic_pem_pattern`).
  7 skip baseline ile aynı: 1 W13-4.5 alembic deferral plus 6 canary
  baseline. Collected 1505 → 1506 / 8 deselected (smoke unchanged).
  `tests/platform/security/` 68 → 69 collected, +1 passed.
  `make test-security` 211 → 212 (yeni timing case bu lane'de).
  `tests/architecture/` 95 passed / 4 deselected — değişmedi.
- [x] **Production code diff dar.** `git diff --stat 007e025..HEAD -- appcore/ workflows/ executor/ packages/ ui/ alembic/`
  yalnızca `packages/analysis_contracts/evidence.py` döner (+45 net
  satır: 4 yeni constant — `_PRIVATE_KEY_BEGIN_RE`,
  `_PRIVATE_KEY_END_RE`, `_PRIVATE_KEY_MAX_BODY`,
  `_PRIVATE_KEY_PLACEHOLDER`; 1 yeni helper `_redact_private_key_bounded`;
  `redact_multiline_secrets()` body refactored). `appcore/`,
  `workflows/`, `executor/`, `ui/`, `alembic/` zero diff. 3 çağrı
  sitesi (`output.py:120`, `output.py:237`, `analysis_execution.py:97`)
  dokunulmadı — `redact_multiline_secrets()` signature `str → str`
  korundu.
- [x] **Latency doğrulaması.**
  `python -c "from packages.analysis_contracts.evidence import redact_multiline_secrets; import time; mal = ('-----' + 'BEGIN ' + 'PRIVATE ' + 'KEY-----' + '\n' + 'x' * 1000 + '\n') * 200; t = time.perf_counter(); r = redact_multiline_secrets(mal); print(f'{(time.perf_counter()-t)*1000:.2f}ms')"`
  → 1.29 ms (pre-fix ölçümü 361.21 ms, ~280× speedup).
  Happy path smoke: `before\n<BEGIN>\nbody\n<END>\nafter` →
  `before\n[REDACTED:private_key]\nafter` (semantic identical).
- [x] **Architecture gate'leri korundu.** W12: 5/5 ✓
  (`test_executor_playwright_flat_file_count_limit`,
  `test_runner_main_under_loc_budget`,
  `test_runtime_capture_extension_host_*` × 2,
  `test_body_preview_assignments_are_redacted`,
  `test_all_runtime_dockerfiles_pin_base_images_by_digest`).
  W13-1: 3/3 ✓ (`test_harness_marker_auth.py`).
  W13-2: 4/4 ✓ (`test_executor_runtime_script_permissions.py` static + smoke).
  W13-3: 6/6 ✓ (`test_cancel_poll_points.py` × 2 +
  `test_job_state_invariants.py` × 4).
  W13-5: 6/6 ✓ (`test_makefile_dev_recipes.py`).
  W13-6: 2/2 ✓ (`test_arguments_preview_redaction.py`) +
  5 regression cases ✓ (`test_parse_strace_event_arguments_preview_redacts_secrets`).
  **W13-7: 1/1 ✓** (`test_redact_multiline_secrets_rejects_catastrophic_pem_pattern`)
  plus W12-0 4 PEM regression cases continue to pass
  (`test_install_failure_message_redacts_multiline_pem_split_by_tail`,
  `test_read_output_channel_logs_redacts_multiline_pem_block`,
  `test_read_output_channel_logs_multiline_pem_with_surrounding_lines`,
  `test_parse_output_signal_events_redacts_cross_marker_pem_block`,
  `test_parse_output_signal_events_single_marker_multiline_pem`) —
  bounded scanner identical replacement semantics.
- [x] **Threat coverage özeti.** Eskiden: `redact_multiline_secrets()`
  lazy regex `(?:.|\n)*?` cross-line span'i her BEGIN pozisyonundan
  ileri doğru tüm pozisyon kombinasyonlarını dener; çok sayıda
  eşleşmemiş BEGIN marker'ı O(N×L) tarama'ya yol açar. Target
  extension Extension-Host stdout'una BEGIN literal'leri stuff
  ederek `redact_multiline_secrets` çağrı sitesi başına saniye
  düzeyinde latency ekleyebilir; 3 çağrı sitesi/analiz = analiz
  başına ek 3× saniye DoS. Şimdi: bounded scanner manual linear
  pass + 16 KB BEGIN→END window cap; adversarial latency 280×
  düşürüldü (361 → 1.3 ms). Trade-off: cap dışındaki END'i
  bulamayan BEGIN markerları artık redact edilmiyor (BEGIN literal
  görünür kalır) — real-world PEM <16 KB olduğu için pratik fark
  yok; gerçek tek-parça 16 KB+ PEM key kullanım örneği yok.
- [x] **Slim canonical doc sweep.** Tracker (this file),
  `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md` güncellendi. Slim
  canonical satır sayıları 200 altında kalır — W13-7 için ayrı
  archive snapshot zorunlu değil. `REFACTOR_OPTIMIZATION.md` §11.10
  ve §11.14, `CLAUDE.md`, `AGENTS.md`, `documents/active-work/README.md`,
  `documents/automation_todo.md` sweep'i sub-commit 5'e bırakılır
  (W13-5 + W13-6 5/5 patterninin birebir replikası).
- [x] **Branch policy korundu.** Tüm 4 commit (sub-commit 1-4) `week13`
  üzerinde; yeni branch açılmadı. Sub-commit 5 sonrası W13-1..W13-7
  ratchet'leri ile birlikte tek W13 close-out PR'ı `week13 → main`
  açılır (W12 PR #18 pattern'i).
- [x] **W13 acceptance bar cleared.** H3 (W13-5), H4 (W13-3), H5 (W13-2),
  H6 (W13-1), M1 (W13-7), M9 (W13-6) — Codex Cloud audit (2026-05-10)
  4 HIGH + 2 MEDIUM bulgusu tamamen kapatıldı. Bundan sonra W14+
  planning'e geçilebilir; bu phase end-of-phase manifestoya hazır.

### W13-8 — Benign silence fixture 3→5 (§11.10 GOAL)

`Status: in progress (opened 2026-05-11)` ·
`Source: [§11.10 GOAL] Benign silence fixture 3→5` ·
`Lane: [security-detection]`

**Bağlam.** `REFACTOR_OPTIMIZATION.md` §11.10 GOAL listesinin ilk
sırasında yer alan "Benign silence fixture 3→5" item'ı, W13-1..W13-7
Codex Cloud acceptance-bar closure'undan sonraki ilk GOAL pull'u.
Mevcut benign-silence coverage iki fixture'la sınırlı:

- [`extensions/extrace.fixture-chat-0.0.1/`](../../extensions/extrace.fixture-chat-0.0.1)
  — chat participant katkı noktası, `onChatParticipant:` aktivasyonu
  ile target_extension_observed=true, scenario-running profil
  (mevcut baseline JSON `tests/platform/contracts/fixtures/activation_reports/extrace_fixture_chat.json`
  — 50 satır, `signal_summary.score=6`, `automation_health.target_activation_count=1`).
- [`extensions/extrace.fixture-theme-0.0.1/`](../../extensions/extrace.fixture-theme-0.0.1)
  — color theme katkı noktası, hiçbir aktivasyon event'i yok,
  zero-scenario profil (mevcut baseline JSON
  `tests/platform/contracts/fixtures/activation_reports/extrace_fixture_theme.json`
  — 145 satır, `trigger_execution_mode="skip_automation"`,
  `scenario_traces=[]`, `signal_summary.score=8`).

Bu iki fixture sırasıyla "aktivasyon-enabled + scenario-running" ve
"zero-scenario + skip_automation" uç durumlarını kapsıyor; ama
benign-silence regression coverage'ı yalnızca iki kategoride ratchet
yapıyor. Codex Cloud audit'in W12-0 redaction + W13-6 arguments_preview
redaction + W13-7 PEM bounded scanner zinciri ile yeni eklenen yüksek-
hassasiyet detection kuralları, regression yüzeyi olarak iki fixture'ı
çok dar bırakır: yeni bir false-positive regression nadir bir
contribution kategorisinde patlarsa silence assertion'ı yakalamayabilir.

**Critical files.**

- [tests/security/test_benign_silence.py:6-17](../../tests/security/test_benign_silence.py) — şu an 2 silence assertion (chat + theme). W13-8 sub-commit 2 (RED) bu dosyaya 3 yeni skip-marked test ekler. GREEN sub-commit skip decorator'larını kaldırır.
- [tests/security/helpers.py:13-32](../../tests/security/helpers.py) — `_FIXTURE_REPORTS` fallback dict, 2 entry. **GREEN sub-commit'te güncellenir** (3 yeni entry); RED sub-commit'te dokunulmaz çünkü skip decorator test body'sini çalıştırmaz, helper lookup tetiklenmez.
- [tests/platform/contracts/test_analysis_fixture_baselines.py:37-41](../../tests/platform/contracts/test_analysis_fixture_baselines.py) — `BASELINE_EXTENSION_FIXTURES` tuple, 3 entry (`ms-python.python` + 2 extrace fixture). **GREEN sub-commit'te güncellenir** (3 yeni `_fixture_identity()` entry); RED'de eklense `test_baseline_extension_fixtures_resolve_from_local_artifacts_without_network` fail eder (lokal extension klasörü yok).
- `tests/platform/contracts/fixtures/activation_reports/` — şu an 3 baseline JSON (`ms_python_python.json`, `extrace_fixture_chat.json`, `extrace_fixture_theme.json`). **GREEN sub-commit'te 3 yeni baseline JSON yazılır** (`extrace_fixture_snippet.json`, `extrace_fixture_keybinding.json`, `extrace_fixture_cmd.json`).
- `extensions/extrace.fixture-{snippet,keybinding,cmd}-0.0.1/` — **GREEN sub-commit'te author'lanır**. RED'de yok.

**Fixture seçim gerekçesi (RED scope-lock).**

VS Code katkı noktaları (contribution points) arasından, mevcut chat+theme
çiftiyle birlikte aktivasyon profili çeşitlendirmesi sağlayan üç sınıf
seçildi. Her biri benign silence baseline'ında farklı bir code path tetikler:

| # | Identity (RED placeholder) | Kategori | Activation profili | Beklenen baseline tipi |
|---|---|---|---|---|
| 1 | `extrace.fixture-snippet-0.0.1` | `contributes.snippets` | declarative-only, aktivasyon event yok | zero-scenario (theme'e yakın `trigger_execution_mode=skip_automation`) |
| 2 | `extrace.fixture-keybinding-0.0.1` | `contributes.keybindings` | declarative-only, aktivasyon event yok | zero-scenario (theme'e yakın) |
| 3 | `extrace.fixture-cmd-0.0.1` | `contributes.commands` + `onCommand:` | `onCommand:extrace.fixture-cmd.run` aktivasyonu, registerCommand handler | activation-enabled (chat'e yakın `target_activation_count=1`) |

Bu seçim **RED commit'inde scope-lock**'lanır. GREEN sub-commit'inde
fixture extension'ları gerçek author edilirken adlar revize edilebilir
(skip reason `"names may be revised in GREEN"` notu içerir); ama
çeşitlendirme niyeti (2 declarative zero-scenario + 1 activation-enabled)
korunur. Alternatif sınıflar (status bar, tree view, webview, language
configuration) GREEN audit'inde değerlendirilir; W13-8 yalnızca üç
kategoride ratchet yapar — §11.10 GOAL'ın "3→5" kontratı buna izin verir.

**Reverse-side reject rationale (Path B — 3 fixture'ı tek yeni
extension dizininde toplama).**

Reddedildi. Tek extension'da hem `contributes.snippets` hem
`contributes.keybindings` hem `contributes.commands` + `onCommand:`
tanımlamak teknik olarak geçerlidir; ama benign-silence regression'da
"hangi katkı noktası sessizlik invariant'ını kırdı?" sorusuna cevap
veren ayrı `bundle.detection_report.findings` snapshot'ları gerekir.
Üç ayrı fixture, üç ayrı baseline JSON, üç ayrı assertion — her biri
diğerlerinden bağımsız regression sinyali verir. Tek-fixture
yaklaşımı assertion bulanıklaştırır.

**Reverse-side reject rationale (Path C — `BASELINE_EXTENSION_FIXTURES`
tuple'una RED'de eklemek).**

Reddedildi. Tuple'a şimdi entry eklenirse
`test_baseline_extension_fixtures_resolve_from_local_artifacts_without_network`
([line 207-216](../../tests/platform/contracts/test_analysis_fixture_baselines.py))
collection'da fail eder: test gövdesi `download_and_extract_vsix()`
çağırır, lokal `/extensions/extrace.fixture-snippet-0.0.1/` klasörü
olmadığı için `FileNotFoundError`. Bu test skip-mark'lanmazsa W13-1..W13-7
acceptance-bar ratchet'i kırılır. Tuple güncellemesi GREEN sub-commit'e
geçer; o sub-commit fixture klasörlerini aynı atomic commit'te oluşturur.

**Sub-commit Roadmap (4 commits — all targeting `week13`).**

| # | Commit | Touch | Status |
|---|---|---|---|
| 1 | `docs(W13-8): assign stable ID + scope benign silence fixture 3→5` | `documents/active-work/W13-test-expansion-observability.md` (this file) | closed `2026-05-11` |
| 2 | `test(W13-8): RED precursor for 3 benign silence fixtures (skip-marked)` (`5524646`) | `tests/security/test_benign_silence.py` (3 yeni skip-marked test + `pytest` import) | closed `2026-05-11` |
| 3 | `feat(W13-8): author 3 benign silence fixture extensions + baseline JSONs (RED→GREEN)` (`4d49cbe`) | `extensions/extrace.fixture-{snippet,keybinding,cmd}-0.0.1/` (yeni — package.json + per-category source/manifest), `tests/platform/contracts/fixtures/activation_reports/extrace_fixture_{snippet,keybinding,cmd}.json` (yeni), `tests/security/helpers.py` (`_FIXTURE_REPORTS` 3 yeni entry), `tests/platform/contracts/test_analysis_fixture_baselines.py` (`BASELINE_EXTENSION_FIXTURES` 3 yeni `_fixture_identity()` + `expected_activation_event_types` 3 yeni entry), `tests/security/test_benign_silence.py` (3 skip decorator kaldır), `.gitignore` (3 allow rule), `scripts/reset_extensions.sh` (KEEP[] +6 entry) | closed `2026-05-11` |
| 4 | `docs(W13-8): close evidence + status sweep` | tracker close evidence + final hash table, `REFACTOR_STATUS.md` W13-8 row → closed, `POST_POC_BACKLOG.md` header refresh, `REFACTOR_OPTIMIZATION.md` §11.10 GOAL satır update, `CLAUDE.md` header parity | closed `2026-05-11` (this commit) |

W13-7'nin 5-commit yapısına göre W13-8 4-commit'te biter: §11.10 GOAL
post-acceptance-bar olduğu için ayrı "align lagging canonicals" sweep'i
gerekmez — kapalı acceptance-bar item'larına slim canonical refparity
zaten `2026-05-11` tarihli.

**Architecture gate (W13-8.3'te pinler).**

GREEN sub-commit'te `tests/security/test_benign_silence.py`'a eklenen 3
yeni test (skip decorator'ları kaldırılmış hâliyle):

| # | Case adı | Pin |
|---|---|---|
| 1 | `test_benign_snippet_fixture_remains_silent` | `analyze_fixture(extensions/extrace.fixture-snippet-0.0.1)` → `bundle.detection_report.findings == []` + `verdict == "clean"`. Declarative snippets fixture detection sinyali üretmemeli (zero-scenario semantic'i theme ile aynı kategoride). |
| 2 | `test_benign_keybinding_fixture_remains_silent` | `analyze_fixture(extensions/extrace.fixture-keybinding-0.0.1)` → aynı invariant. Declarative keybindings da zero-scenario; aktivasyon event'i yok. |
| 3 | `test_benign_cmd_fixture_remains_silent` | `analyze_fixture(extensions/extrace.fixture-cmd-0.0.1)` → aynı invariant. `onCommand:` aktivasyonlu fixture; scenario-running profil (chat ile aynı kategoride). |

Plus mevcut 2 case (`test_benign_chat_fixture_remains_silent`,
`test_benign_theme_fixture_remains_silent`) regression eder — yeni
fixture'lar mevcut detection rule'ları tetiklerse bu iki case kırılmaz
ama yeni eklenenler kırılır; yeni rule'lar açılırsa hangi katkı
noktasının fixture'ında patladığını her test ayrı sinyalle bildirir.

**Verification plan.**

- W13-8.1 sonrası (this commit): doc-only commit; sayılar değişmez.
  `make test-local` 1506 collected, `make test-security` 212 collected,
  `tests/architecture/` 95 collected — hepsi aynı.
- W13-8.2 sonrası (RED scaffold): `make test-local` 1506 → 1509 collected
  (+3 skipped). `tests/security/test_benign_silence.py` 2 → 5 collected
  (2 passed + 3 skipped). Skip reason'ları `"W13-8 RED precursor"` prefix'i
  taşır. `make test-security` 212 → 215 collected (+3 skipped; benign
  silence `tests/security/` lane'inde — [Makefile:206-216](../../Makefile)).
  `tests/architecture/` 95 unchanged.
- W13-8.3 sonrası (GREEN): `make test-local` 1509 collected,
  **+3 passed** (1499 → 1502 passed); 7 skip baseline 4'e iner
  (3 W13-8 skip kalkar, baseline alembic+canary 4 kalır). `make test-security`
  212 → 215 (+3 passed). `tests/architecture/` 95 unchanged. Fixture
  extension dizinleri (`extensions/extrace.fixture-{snippet,keybinding,cmd}-0.0.1/`)
  oluşur; 3 yeni baseline JSON eklenir; `_FIXTURE_REPORTS` ve
  `BASELINE_EXTENSION_FIXTURES` 3'er entry artar.
- W13-8.4 sonrası: doc-only; sayılar 8.3'le aynı.
- Production code dokunulmaz tüm sub-commit'lerde (`appcore/`, `workflows/`,
  `executor/`, `packages/`, `ui/`, `alembic/` zero diff). Yalnızca
  fixture extension'lar `extensions/` altında eklenir — bu prod code
  değil, test fixture'ıdır (mevcut chat+theme fixture'ları da
  `extensions/` altındadır).

**W13-8.1 close evidence (this commit).**

- [x] Stable ID `W13-8` atandı, scope kilitlendi (3 placeholder fixture
  identity: snippet/keybinding/cmd; 2 declarative zero-scenario + 1
  activation-enabled axis çeşitlendirmesi).
- [x] Tracker güncellendi: header `Last Updated 2026-05-11` (W13-8 opened
  note); Status (Quick Glance) yeni W13-8 opened bullet'ı; next-pull
  yenilendi (W13-8 GREEN → W13 close-out PR); Candidate Items table'da
  §11.10 GOAL benign silence satırı `**W13-8**` `in progress`; bu
  Per-Item Detail bloğu eklendi.
- [x] Sub-commit roadmap kilitlendi: 4 commit (this docs, RED scaffold,
  RED→GREEN fixture authoring, close-evidence sweep).
- [x] Path B (tek-fixture multi-contribution) ve Path C (`BASELINE_EXTENSION_FIXTURES`
  tuple'unu RED'de güncellemek) reddedildi; gerekçeler kayıt altında.
- [x] W12 + W13-1..W13-7 ratchet gate'leri intact kalır (bu commit pure doc).
- [x] Production code dokunulmaz (`appcore/`, `workflows/`, `executor/`,
  `packages/`, `ui/`, `alembic/`).
- [x] Branch policy korundu: commit `week13` üzerinde; yeni branch
  açılmadı. Sonraki sub-commit'ler de aynı branch'te kalır.

**W13-8.2 close evidence (`5524646`).**

- [x] RED scaffold landed: `tests/security/test_benign_silence.py`'a 3
  yeni skip-marked test eklendi (`test_benign_snippet_fixture_remains_silent`,
  `test_benign_keybinding_fixture_remains_silent`,
  `test_benign_cmd_fixture_remains_silent`); her biri
  `@pytest.mark.skip(reason="W13-8 RED precursor — … not yet authored …")`
  decorator'lu.
- [x] `make test-local` 1506 → 1509 collected (+3 skipped); skip reason
  prefix'i `"W13-8 RED precursor"` tutarlı.
- [x] `make test-security` 212 → 215 collected (+3 skipped — benign
  silence tests/security/ lane'inde).
- [x] `tests/architecture/` 95 unchanged.
- [x] Production code zero diff (yalnız test scaffold).

**W13-8.3 close evidence (`4d49cbe`).**

- [x] Üç fixture extension authored:
  - `extensions/extrace.fixture-snippet-0.0.1/` — `categories: ["Snippets"]`,
    `contributes.snippets: [{language: plaintext, path: ./snippets/extrace-fixture-snippets.json}]`,
    NO `activationEvents`, NO `main`. `snippets/extrace-fixture-snippets.json`
    minimal plaintext snippet body.
  - `extensions/extrace.fixture-keybinding-0.0.1/` — `categories: ["Keymaps"]`,
    `contributes.commands: [{command: extrace.fixture-keybinding.noop, title: …}]`
    - `contributes.keybindings: [{key: ctrl+f12, mac: cmd+f12, when: editorTextFocus,
    command: extrace.fixture-keybinding.noop}]`, NO `activationEvents`, NO `main`
    (declarative-only; aktivasyon event'i yok).
  - `extensions/extrace.fixture-cmd-0.0.1/` — `categories: ["Other"]`,
    `activationEvents: ["onCommand:extrace.fixture-cmd.run"]`, `main: ./extension.js`,
    `contributes.commands: [{command: extrace.fixture-cmd.run, title: …}]`;
    `extension.js` — `vscode.commands.registerCommand("extrace.fixture-cmd.run", …)`
    deterministic noop (chat fixture pattern'i).
- [x] Üç baseline activation report yazıldı (`tests/platform/contracts/fixtures/activation_reports/`):
  `extrace_fixture_snippet.json` ve `extrace_fixture_keybinding.json` —
  `extrace_fixture_theme.json` klonu (`trigger_execution_mode=skip_automation`,
  `scenario_traces=[]`, `signal_summary.score=8`, contribution-spesifik note);
  `extrace_fixture_cmd.json` — `extrace_fixture_chat.json` klonu
  (`target_activation_count=1`, `signal_summary.score=6`,
  evidence_events activation + command handler invocation).
- [x] Üç `.vsix` paket local'de oluşturuldu (`zip -0 -r` ile,
  `extension/` prefix; mevcut chat/theme `.vsix` pattern'i ile aynı
  compression=store yapısı). `.vsix` dosyaları git-tracked değil —
  mevcut chat/theme `.vsix`'leri de gitignored (line 39-40 convention).
- [x] `tests/security/helpers.py:13-56` — `_FIXTURE_REPORTS` dict'ine 3
  yeni entry (snippet/keybinding/cmd → ilgili baseline JSON path).
- [x] `tests/platform/contracts/test_analysis_fixture_baselines.py:37-44` —
  `BASELINE_EXTENSION_FIXTURES` listesine 3 yeni `_fixture_identity()`
  entry. Line 221-233 — `expected_activation_event_types` dict'ine 3
  yeni entry: `snippet: set()`, `keybinding: set()`, `cmd: {"onCommand"}`.
  Bu dict round-trip testinde her `BASELINE_EXTENSION_FIXTURES` entry
  için lookup yapar; eksik key'de `KeyError`. Tracker'ın 8.3 scope'unda
  açıkça çağrılmamıştı; round-trip test invariant'ından çıkarsanan
  zorunlu touch.
- [x] `tests/security/test_benign_silence.py` — 3 `@pytest.mark.skip`
  decorator'u kaldırıldı; `pytest` import'u artık kullanılmıyor,
  pruned. 5/5 silence assertion ✓.
- [x] `.gitignore:43-47` — 3 allow rule (`!extensions/extrace.fixture-{snippet,keybinding,cmd}-0.0.1/`)
  chat/theme pattern'i ile aynı. W13-9 `.env` gitignore architecture
  gate `test_env_gitignore.py` 10/10 ✓ unchanged.
- [x] `scripts/reset_extensions.sh:22-35` — `KEEP[]` listesine 6 yeni
  entry (3 dir adı + 3 `.vsix` adı) — `make extensions-reset` yeni
  fixture'ları silmesin.
- [x] Üç gate green:
  - `make test-local`: 1514 passed / 7 skipped / 8 deselected / 78 warnings.
    Pre-state'ten 3 W13-8 RED skip'i PASS'a geçti; 7 baseline skip
    (alembic 1 + canary 6) korundu.
  - `make test-security`: 215 passed / 35 warnings (212 → 215, +3).
  - `make check-all`: ✅ All checks (including security) passed
    (ruff + ruff-format + mypy + bandit + arch + full pytest).
    `tests/architecture/` 105 unchanged (109 collected, 4 deselected).
- [x] Round-trip testi (`test_baseline_extension_fixtures_round_trip_through_extension_schema`)
  6 fixture (3 mevcut + 3 yeni) için iterasyonda `vsix_path.exists()`
  ve `expected_activation_event_types` lookup'ları geçti. Resolve testi
  (`test_baseline_extension_fixtures_resolve_from_local_artifacts_without_network`)
  3 yeni extension dizini için lokal artifact resolve etti; network
  çağrısı yapılmadı (httpx.Client `side_effect=AssertionError` ile
  patched).
- [x] Production code dokunulmaz (`appcore/`, `workflows/`, `executor/`,
  `packages/`, `ui/`, `alembic/` zero diff).
- [x] Branch policy korundu: `week13` üzerinde; yeni branch açılmadı;
  PR/merge açılmadı.

**W13-8.4 close evidence (this commit).**

- [x] Tracker güncellendi: header `Last Updated 2026-05-11` (W13-8
  closed note); Status (Quick Glance) W13-8 closed bullet'ı + next-pull
  yenilendi (W13 close-out PR `week13 → main`); Candidate Items
  table'da §11.10 GOAL benign silence satırı `**W13-8**` `closed`;
  sub-commit roadmap tablosu hash'lerle doluruldu (8.2 = `5524646`,
  8.3 = `4d49cbe`); W13-8.2/8.3/8.4 close evidence blokları eklendi.
- [x] `REFACTOR_STATUS.md` — W13-8 closed bullet (line ~81), Status
  tablosu W13-8 row'u `closed`, close-out PR pre-condition cümlesi
  "all chosen §11.10 GOAL pulls closed" haline güncellendi.
- [x] `POST_POC_BACKLOG.md` — header status özeti `W13-8 closed`
  yansıtacak şekilde refresh edildi.
- [x] `REFACTOR_OPTIMIZATION.md §11.10` — W13-8 opened bullet'ı
  closed bullet'ına çevrildi.
- [x] `CLAUDE.md` — header `Last Updated` satırı W13-8 closed olarak
  refresh edildi.
- [x] Doc-only commit; test sayıları 8.3'le aynı (1514 passed, 215
  security, 105 architecture).
- [x] Production code zero diff.
- [x] Branch policy korundu: `week13` üzerinde; PR/merge açılmadı —
  W13 close-out PR `week13 → main` kullanıcı onayı bekler.

**W13-8 post-close coverage sweep (`908caac` + `7104eca` doc drift).**

W13-8.4 (`523d626`) kapatma sonrası bir drift hunt'la 4 doc drift
(`AGENT_CONTEXT.md`, `active-work/README.md`, `TESTING.md`,
`agent-lanes/security-detection.md`) ve 3 eksik test invariant'ı
tespit edildi:

- `7104eca docs(W13-8): post-close-out doc drift sweep` — 4 lagging
  canonical reference (AGENT_CONTEXT.md header, active-work/README.md
  W13-8 row, TESTING.md test counts, security-detection lane header)
  W13-8 closed durumuyla parite'ye getirildi.
- `908caac test(W13-8): pin missing W13-8 fixture invariants` — 3
  test gap'i kapatıldı:
  - **Gap 2** (must-have): `extrace.fixture-cmd` için
    `test_baseline_extension_fixtures_round_trip_through_extension_schema`'a
    inline assertion eklendi
    (`activationEvents == ["onCommand:extrace.fixture-cmd.run"]` +
    `contributes.commands[0].command_id == "extrace.fixture-cmd.run"`).
  - **Gap 1** (cheap nice-to-have): theme-only
    `test_color_theme_activation_report_fixture_supports_zero_scenario_semantics`,
    parametrize edilip `test_non_executable_fixtures_support_zero_scenario_semantics`
    olarak yeniden adlandırıldı; theme + snippet + keybinding 3
    parametrize case altında pin'lendi.
  - **Gap 5** (must-have): `BASELINE_EXTENSION_FIXTURES` ↔
    `EXPECTED_ACTIVATION_EVENT_TYPES` parity invariant'ı için yeni
    architecture gate
    `tests/architecture/test_baseline_fixture_manifest_parity.py`
    2/2 ✓ — missing-key + orphan-key drift'lerini named failure ile
    yakalar (W13-8 GREEN authoring'inde bu footgun'a takılmamak için).

Post-sweep final bar: `make test-local` 1514 → 1518 passed (delta of
four cases: two parametrize zero-scenario plus two architecture
parity); `make test-security` 215 unchanged; `tests/architecture/`
105 → 107 collected (two parity cases added). `make check-all`
green. Production code zero diff. Branch policy korundu — `week13`
üzerinde, PR/merge yok.

### W13-9 — `.env` gitignore regression test (§11.10 GOAL)

`Status: closed (2026-05-11, 1/1 commit)` ·
`Source: [§11.10 GOAL] .env gitignore regression test` ·
`Lane: [security-detection]`

**Bağlam.** §11.10 GOAL listesinde "`.env` gitignore regression test"
item'ı. `.gitignore` zaten doğru rule'lara sahip (line 5-7
`.venv/` / `env/` / `venv/` virtualenv dirs, line 8 `*.env` wildcard,
line 45 `.env` literal, line 46 `!.env.example` negative exception)
ve `.env.example` template repo'da tracked, ama hiçbir architecture
gate bu invariant'ı pin'lemiyordu. Bir gelecekte `.gitignore`'a
yapılan kazara bir edit (ör. line 46 `!.env.example`'ı silmek veya
line 8 wildcard'ı daraltmak) onboarding'i sessizce kırabilirdi.

W13-9, `git check-ignore` semantik'ini kullanan tek dosyalık bir
mimari gate ekler. Hiçbir production code'a dokunmaz; underlying
behavior zaten doğru.

**Critical files.**

- [`.gitignore`](../../.gitignore) line 5-8, 45-46 — gate'in
  doğruladığı kural seti. **Dokunulmaz**.
- [`.env.example`](../../.env.example) — negative-exception
  rule'unun anlamlı olabilmesi için repo'da bulunması zorunlu
  template. **Dokunulmaz**.
- [`tests/architecture/test_env_gitignore.py`](../../tests/architecture/test_env_gitignore.py) — **YENİ**. `git check-ignore --no-index <path>` çağırır + exit code (0=ignored, 1=tracked) üzerinden assertion yapar. Parametrized 8 case + 2 standalone case = 10 toplam.

**Test surface (`tests/architecture/test_env_gitignore.py`).**

| # | Test | Pin |
|---|---|---|
| 1-5 | `test_secret_bearing_paths_are_gitignored[.env / foo.env / bar.env / subdir/.env / nested/deeper/.env]` | `.env` literal (line 45) ve `*.env` wildcard (line 8) repo-root ve nested path'lerde |
| 6-8 | `test_secret_bearing_paths_are_gitignored[.venv/lib/python3.12/site-packages/foo.py / env/bin/python / venv/bin/activate]` | Virtualenv dir rules (line 5-7) inside-the-dir path'leri ile (directory-only `xxx/` semantik'i fs-state'e bağımlı olmadan doğrulanır) |
| 9 | `test_dotenv_example_template_is_tracked` | Negative exception (line 46) `*.env` ve `.env` rule'larını override eder |
| 10 | `test_dotenv_example_file_actually_exists_in_tree` | `.env.example` template aslında repo'da; rule doğru olsa bile dosya silinirse onboarding kırılır |

**Reverse-side reject rationale (Path B — pytest `tmp_path` ile yeni
git repo + symlink check).**

Reddedildi. Test temiz bir tmp_path'te yeni bir git repo oluşturup
`.gitignore`'u kopyalayıp orada `git check-ignore` çalıştırabilirdi.
Bu izolasyon iyi olurdu ama karmaşıklık ekler ve aslında repo'nun
kendi `.gitignore`'unu doğrulamıyor. Path A doğrudan REPO_ROOT
üzerinde `git check-ignore --no-index` çağırır — `--no-index`
flag'i index'i bypass eder, `.gitignore` rule'larını saf olarak
değerlendirir. Test deterministik kalır + repo'nun gerçek
`.gitignore`'unu kapsar.

**Reverse-side reject rationale (Path C — pure `pathspec` library
parsing).**

Reddedildi. `pathspec` 3rd-party library `pyproject.toml`'a
dependency eklemeyi gerektirir; AGENTS.md "Do not introduce
dependencies without explicit approval" kuralını ihlal eder.
`git check-ignore` zaten subprocess'le erişilebilir; ek dependency
yok.

**Sub-commit Roadmap (1 commit).**

| # | Commit | Touch | Status |
|---|---|---|---|
| 1 | (this) `test(W13-9): .env gitignore architecture gate (GREEN)` | `tests/architecture/test_env_gitignore.py` (new), `documents/active-work/W13-test-expansion-observability.md` (W13-9 stable ID + Per-Item Detail) | landed |

W13-9 GREEN-immediate olduğu için (underlying `.gitignore` zaten
doğru, test bir gap'i kapatıyor) tek commit yeterli. W13-7 5-commit
yapısı production fix gerektiriyordu; W13-9 yalnızca test coverage
gap'i kapatır.

**Architecture gate (W13-9'da pinler).**

Yukarıdaki test surface tablosu, eklenen 10 case'i tam dokümante eder.
Tüm 10 case W13-9 commit'inde GREEN landlar (pre-existing `.gitignore`
zaten doğru; test sadece invariant'ı doğrular).

**Verification plan.**

- W13-9 sonrası: `make test-local` 1509 → 1519 collected, +10 passed
  (W13-8 RED'in 3 skipped'i sabit). `tests/architecture/` 95 → 105
  collected, +10 passed. `make test-security` 212 unchanged
  (architecture lane ayrı).
- Manuel doğrulama: `git check-ignore -v .env .env.example` döner
  `.gitignore:45:.env .env` (ignored) + `.env.example` (no output,
  exit 1).
- Production code diff sıfır (`appcore/`, `workflows/`, `executor/`,
  `packages/`, `ui/`, `alembic/`).

**W13-9.1 close evidence (this commit).**

- [x] Stable ID `W13-9` atandı, scope kilitlendi (tek commit GREEN).
- [x] Yeni mimari gate `tests/architecture/test_env_gitignore.py`
  10/10 ✓ (`.env` literal/wildcard, virtualenv dirs, negative
  exception, template presence).
- [x] Underlying `.gitignore` dokunulmadı — pre-W13-9 davranışı doğruydu;
  W13-9 invariant'ı pin'ler.
- [x] Production code dokunulmaz (`appcore/`, `workflows/`, `executor/`,
  `packages/`, `ui/`, `alembic/`).
- [x] W12 + W13-1..W13-7 ratchet gate'leri intact; W13-8 RED scaffold
  intact (3 skip-marked case sabit).
- [x] Branch policy korundu: commit `week13` üzerinde; yeni branch
  açılmadı.
- [x] Tracker güncellendi: header `Last Updated 2026-05-11` (W13-9
  closed note); Status (Quick Glance) yeni W13-9 closed bullet'ı +
  next-pull yenilendi (W13-10); Candidate Items table'da §11.10 GOAL
  `.env` gitignore satırı `**W13-9**` `closed`; bu Per-Item Detail
  bloğu eklendi.

### W13-10 — Stale singleton-lock recovery integration test (§11.10 GOAL)

`Status: closed (2026-05-11, 1/1 commit)` ·
`Source: [§11.10 GOAL] Stale singleton-lock recovery integration test` ·
`Lane: [executor-runtime]`

**Bağlam.** §11.10 GOAL listesinde "Stale singleton-lock recovery
integration test" item'ı. Mevcut test surface
[`tests/executor/test_reset_state.py`](../../tests/executor/test_reset_state.py)
şu coverage'a sahipti:

- Lines 137-176: 3 unit case `cleanup_singleton_locks()`'u izole olarak
  doğrular (happy path, missing dir, partial files).
- Lines 19-67: `test_reset_executor_state_clears_extensions_and_logs`
  reset orkestrayonunu test eder ama `cleanup_singleton_locks`
  fonksiyonunu stub'lar (`_stub_vscode_lifecycle` line 14-16,
  `lambda: 0` döndürür).
- Lines 223-270: `test_reset_executor_state_orchestrates_restart_in_correct_order`
  call ordering'i (terminate → cleanup → launch) doğrular ama yine
  `cleanup_singleton_locks`'u stub'lar.

Eksik olan: **integration test** — gerçek lock dosyaları diskte
varken `reset_executor_state()` end-to-end çalışır, lock dosyaları
gerçekten temizlenir, geri kalan reset pipeline normal tamamlanır.

Bu gap önemli çünkü VS Code crash sonrası singleton lock dosyaları
diskte kalır (`/home/executor/.config/Code/SingletonLock`,
`SingletonCookie`, `SingletonSocket`). Bir sonraki `code` invocation
bu dosyaları görürse "Another instance is already running" hatasıyla
bail eder. `reset_executor_state()` bunu önler — ama integration
test'i olmadan, gelecekteki bir refactor (örn. `cleanup_singleton_locks`
çağrısını conditional hale getirmek) sessizce regression çıkarabilirdi.
Unit-test seviyesinde stub'lar tarafından maskelendiği için yakalanmaz.

**Critical files.**

- [`executor/flows/playwright/reset_state.py:131-145`](../../executor/flows/playwright/reset_state.py) — `cleanup_singleton_locks()` helper. **Dokunulmaz** — underlying davranış zaten doğru, W13-10 invariant'ı pin'ler.
- [`executor/flows/playwright/reset_state.py:173-191`](../../executor/flows/playwright/reset_state.py) — `reset_executor_state()` orchestrator. **Dokunulmaz** — call sequence intact (line 182: `removed_locks = cleanup_singleton_locks()` korunur).
- [`tests/executor/test_reset_state.py`](../../tests/executor/test_reset_state.py) — 2 yeni integration test eklenir, mevcut 11 case dokunulmaz (270 → 384 satır, +114 satır net).

**Test surface (eklenen 2 case).**

| # | Test | Pin |
|---|---|---|
| 1 | `test_reset_executor_state_recovers_from_held_singleton_locks_end_to_end` | Setup: tmp_path/Code/ içinde 3 singleton dosyası (SingletonLock/Cookie/Socket) + 1 unrelated dosya (Preferences). Stubs: terminate_vscode + launch_vscode + workspace fonksiyonları (cleanup_singleton_locks **STUB'LANMAZ**). Assert: summary["removed_singleton_locks"] == 3, summary["relaunched_vscode_pid"] == 9999 (stub return), config_dir.iterdir() == ["Preferences"] (sadece unrelated kalır). |
| 2 | `test_reset_executor_state_recovery_handles_partial_singleton_lock_set` | Setup: tmp_path/Code/ içinde 2 singleton dosyası (SingletonLock + SingletonSocket, SingletonCookie eksik). Assert: summary["removed_singleton_locks"] == 2, config_dir boş kaldı (partial set tamamen temizlendi, eksik dosya hata vermedi). |

**Reverse-side reject rationale (Path B — real VS Code process
spawn yapan end-to-end test).**

Reddedildi. Real VS Code spawn etmek (`code` binary subprocess +
`--remote-debugging-port` flag) macOS/Linux/CI'da non-portable; ayrıca
multi-second runtime ekler. W13-10 integration test'in seviyesi
"reset_executor_state() ile real cleanup_singleton_locks() entegrasyonu"
— VS Code lifecycle terminate/launch zaten 11 mevcut case'de
detaylıca cover edilmiş. Stubbing `terminate_vscode` + `launch_vscode`
test scope'unu cleanup_singleton_locks integration'ına daraltır.

**Reverse-side reject rationale (Path C — `cleanup_singleton_locks`
fonksiyonunu `reset_executor_state` içinde inline yapmak).**

Reddedildi. Şu anki ayrılım doğru: `cleanup_singleton_locks()` ayrı
fonksiyon, unit-testable. Inline yapmak unit-test coverage'ını
kaybeder; ayrıca yardımcı fonksiyon olarak başka contexts'de
çağrılabiliyor (örn. CLI `__main__` block line 195'te
`summary["removed_singleton_locks"]` yazdırılır). W13-10 ayrılımı
korur, sadece integration coverage gap'i kapatır.

**Sub-commit Roadmap (1 commit).**

| # | Commit | Touch | Status |
|---|---|---|---|
| 1 | (this) `test(W13-10): stale singleton-lock recovery integration test (GREEN)` | `tests/executor/test_reset_state.py` (+114 satır net, 2 yeni case), `documents/active-work/W13-test-expansion-observability.md` (W13-10 stable ID + Per-Item Detail) | landed |

W13-9 ile aynı pattern: GREEN-immediate olduğu için tek commit
yeterli; production fix gerekmiyor, yalnızca integration test gap'i
kapatılıyor.

**Verification plan.**

- W13-10 sonrası: `make test-local` 1519 → 1521 collected, +2 passed
  (W13-8 RED'in 3 skipped'i sabit). `tests/executor/test_reset_state.py`
  11 → 13 collected, +2 passed. `tests/architecture/` 105 unchanged
  (architecture lane'inde değil — executor lane).
  `make test-security` 212 unchanged.
- Production code diff sıfır (`appcore/`, `workflows/`, `executor/`,
  `packages/`, `ui/`, `alembic/`).

**W13-10.1 close evidence (this commit).**

- [x] Stable ID `W13-10` atandı, scope kilitlendi (tek commit GREEN,
  2 yeni integration case).
- [x] Yeni integration test 2/2 ✓ (full-set held, partial-set held).
  Mevcut 11 case intact — total 13/13 ✓.
- [x] Underlying `reset_state.py` dokunulmadı — pre-W13-10 davranışı
  doğruydu; W13-10 invariant'ı pin'ler.
- [x] Production code dokunulmaz (`appcore/`, `workflows/`, `executor/`,
  `packages/`, `ui/`, `alembic/`).
- [x] W12 + W13-1..W13-7 ratchet gate'leri intact; W13-8 RED scaffold
  intact (3 skip-marked case sabit); W13-9 mimari gate intact (10/10 ✓).
- [x] Branch policy korundu: commit `week13` üzerinde; yeni branch
  açılmadı.
- [x] Tracker güncellendi: header `Last Updated 2026-05-11` (W13-10
  closed note); Status (Quick Glance) yeni W13-10 closed bullet'ı +
  next-pull yenilendi (W13-8 GREEN); Candidate Items table'da §11.10
  GOAL singleton-lock recovery satırı `**W13-10**` `closed`; bu
  Per-Item Detail bloğu eklendi.

### W13-11 — HMAC python secret target-install race (close-gate for W13-1 H6)

`Status: closed 2026-05-12 (6/6 main sub-commits — ccb8aee docs · d87b2ae RED · 68b2259 feat impl · d2f888f arch gate · 9e08fcc regression fix · 135a6b7 doc sweep; + 7 post-landing additions in same push: 9a2ba76 self-stamp · 2a84908 doc fix-up (banner alignment + W13-13 scope rebase) · fe7e19e test (b) integration negative · b1154a0 test (c) env no-leak · c35b7ed test (a) E4 completeness · 723eeeb test (d) README regex pin · TBD tracker test bar update)` ·
`Source: [CLOSE-GATE codex-second-opinion-F1-hmac-python-secret-target-install-race]` ·
`Lane: [executor-runtime] [security-detection]` ·
`Blocks: week13 → main close-out PR`

**Sorun.** W13-1 HMAC handshake'in target-side imza üretimini engellemek
için iki secret üretiyor:

| Path | Mod / sahip | Tüketici | Yaşam süresi |
|---|---|---|---|
| `/run/extrace/harness-secret` | 0400 (executor user) tmpfs | Harness ext `activate()` → okur+unlink immediate | Çok kısa — VS Code boot ↔ harness activate arası |
| `/results/_extrace_harness_python_secret` | 0600 executor:executor (bind-mount) | `setup_monitor()` → okur+unlink | **Geniş — VS Code boot ↔ setup_monitor arası** |

Python verifier secret'ı `setup_monitor()` (`dispatch.py:setup_monitor`)
içinde tüketiliyor, yani install_extension'dan SONRA. Aradaki pencere:

```text
t0  launch_vscode.sh writes /results/_extrace_harness_python_secret (0600)
t1  VS Code starts, harness ext activate() → /run/extrace secret consume + unlink
t2  Workflow → install_extension() admits target VSIX            ← target readable
t3  Target activation event fires (workspace open, onStartupFinished, etc.)
t4  Python dispatch.py:setup_monitor() → /results secret consume + unlink
```

`t2..t4` aralığında target extension executor user UID'siyle koşuyor; aynı
UID 0600 dosyayı okuyabilir. Target dosyayı okuduktan sonra HMAC-signed
sahte `[extrace-harness] {"phase":"complete","nonce":"<calculated>"}`
marker üretebiliyor — W13-1'in tam olarak kapatmak istediği bypass geri
geliyor, sadece bu sefer imzalı.

**Fix yönü (Path A — host-side eager-consume + env var passthrough).**
Secret consume'u container içinden host-side'a çekiyoruz. Host
(`workflows/marketplace/analysis_service.py::execute_analysis_request`)
`_reset_sandbox()` çağrısından SONRA, `_install_extension()` çağrısından
ÖNCE bind-mounted dosyayı (`Path(settings.project.OUTPUT_DIR) /
"_extrace_harness_python_secret"`) okuyup unlink ediyor; secret string
host process memory'sinde tutulup `run_playwright_automation()`'a
`harness_python_secret` kw-arg olarak iletiliyor, oradan docker exec
`-e EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=<hex>` env var olarak entrypoint
container'ına geçiyor. `load_harness_python_secret()` env-priority oluyor
(env önce, file fallback sonra). Bind-mount mapping
`${EXECUTOR_OUTPUT_HOST_PATH:-./output}:${EXECUTOR_OUTPUT_CONTAINER_PATH:-/results}`
([`docker-compose.yml:90-92`](../../docker-compose.yml:90)) doğrulandı;
[`executor/host.py:51-52`](../../executor/host.py:51) `_docker_exec_target_path()`
zaten bu pattern'i production'da kullanıyor.

**Akış değişimi.**

Bugün:

```text
ensure_vsix_exists → _reset_sandbox → _install_extension → _build_triggers → _run_monitoring
                       (secret yazılır)   (target admit)                        (setup_monitor secret okur)
                                          ↑ RACE WINDOW
```

Sonrası:

```text
ensure_vsix_exists → _reset_sandbox → consume_harness_python_secret_eager → _install_extension → _build_triggers → _run_monitoring(harness_python_secret=...)
                       (secret yazılır)   (host-side read+unlink)               (target admit, dosya YOK)         (env var → entrypoint)
```

**Etkilenen yollar.**

- [`executor/host.py`](../../executor/host.py)
  — yeni `consume_harness_python_secret_eager()` helper (mode-guard'lı,
  fail-soft); `_run_docker_exec` imzasına `extra_env: dict[str,str] | None`
  parametresi (kw-only, default-None geriye uyumlu); env-value masking
  helper (E4 mitigation — exception path'inde `' '.join(cmd)` argv'ye
  embed ediliyor, saf hex `_REDACTION_PATTERNS` tarafından yakalanmıyor);
  `run_playwright_automation` imzasına `harness_python_secret: str | None`
  kw-arg.
- [`executor/control.py`](../../executor/control.py)
  — yeni `ExecutorControl.consume_harness_python_secret()` method;
  `run_automation` imzasına kw-arg pass-through.
- [`executor/flows/playwright/health/reconciliation.py:39-58`](../../executor/flows/playwright/health/reconciliation.py:39)
  — `load_harness_python_secret()` env-priority: önce
  `os.environ.get("EXECUTOR_HARNESS_PYTHON_SECRET_VALUE")`, sonra file
  fallback (legacy unit-test compatibility). Env hit'te bile dosya
  unlink edilir (defense-in-depth: eager-consume crash sonrası
  `launch_vscode.sh`'in yazdığı stale dosya bir sonraki cycle'a sızmasın).
- [`workflows/marketplace/analysis_service.py:118-146`](../../workflows/marketplace/analysis_service.py:118)
  — `_reset_sandbox()` sonrası `harness_python_secret = executor_control.consume_harness_python_secret()`
  call site; `_run_monitoring()`'e kw-arg ile threading.
- [`workflows/marketplace/analysis_execution.py:183-207`](../../workflows/marketplace/analysis_execution.py:183)
  — `run_monitoring()` `harness_python_secret` kw-arg pass-through →
  `executor_control.run_automation()`.
- [`executor/container/launch_vscode.sh:39-52`](../../executor/container/launch_vscode.sh:39)
  — **DEĞİŞMEZ** (dual-write korunur; eager-consume sadece dosya yaşam
  süresini kısaltır, atomicity'yi bozmaz).
- [`executor/flows/playwright/entrypoint/dispatch.py:129`](../../executor/flows/playwright/entrypoint/dispatch.py:129)
  — **DEĞİŞMEZ** (`setup_monitor` `load_harness_python_secret()` çağrısı
  korunur; iç davranış değişir ama imza+contract aynı → W13-1
  architecture gate intact).

**Kritik tasarım kararları.**

1. **Mode guard var, ownership guard yok.** `launch_vscode.sh:51` 0600
   yazıyor; eager-consume `stat.S_IMODE != 0o600` ise warn-and-unlink-but-return-None.
   Ownership guard atlanır çünkü macOS Docker Desktop bind-mount UID
   mapping farkı yaratıyor.
2. **`load_harness_python_secret` imzası değişmez.** Sadece iç davranış
   (env önce, file sonra). W13-1 architecture gate
   (`test_harness_marker_auth.py::test_setup_monitor_loads_and_stamps_harness_python_secret`)
   `setup_monitor` body'sinde `load_harness_python_secret()` çağrısı +
   `expected_harness_nonce` stamp invariant'ını pin'liyor — kırılmaz.
3. **Defense-in-depth: env hit'te bile dosyayı unlink et.** Eager-consume
   crash sonrası `launch_vscode.sh`'in yazdığı stale dosya bir sonraki
   cycle'a sızmasın.
4. **E4 docker exec argv leak fix gerekli.**
   [`host.py:74,90,97`](../../executor/host.py:74) `' '.join(cmd)`
   exception mesajına embed ediyor. 64-char saf hex `_REDACTION_PATTERNS`
   (aws/bearer/private_key/api_key/db_url) tarafından **yakalanmaz** —
   yeni env var masking helper'ı sub-commit 3'te.
5. **Race-safety verified.** W13-10 singleton-lock
   ([`appcore/storage/crud_ops/analysis_jobs/lifecycle.py:172`](../../appcore/storage/crud_ops/analysis_jobs/lifecycle.py:172))
   paralel analizi engelliyor → `consume_harness_python_secret_eager`
   race-free; concurrent test gerekmiyor.

**Reddedilen alternatifler.**

- **A.2 container-side bootstrap exec** (6/10) — doğru ama gereksiz
  round-trip + output redaction zorunluluğu; bind-mount path zaten
  production'da çalışıyor.
- **A.3 root-owned 0400 `/run/extrace/python-secret`** (3/10) —
  container USER veya CAP_DAC_READ_SEARCH gerekir, ADR 0008 ile çelişir.
- **A.4 host-only generation** (4/10) — `launch_vscode.sh` dual-write
  atomicity'sini bozar, harness ext `activate()` yarış koşulu açar.

**Test surface (planlanan, 4 dosya / +9 case).**

- Yeni: `tests/architecture/test_harness_secret_eager_consume.py`
  (link path-only; dosya henüz yok, sub-commit 4'te oluşur)
  — 3 AST gate (W13-1 `test_harness_marker_auth.py` pattern referansı):
  Gate 1 `execute_analysis_request` body sequence (`_reset_sandbox` →
  `consume_harness_python_secret` → `_install_extension`); Gate 2
  `run_playwright_automation` body'sinde `"EXECUTOR_HARNESS_PYTHON_SECRET_VALUE"`
  literal + `harness_python_secret` param read; Gate 3
  `load_harness_python_secret` env var read line'ı `path.read_text(...)`
  öncesi (env-priority sequence).
- Yeni: `tests/executor/test_harness_secret_eager_consume.py`
  (link path-only; dosya henüz yok, sub-commit 2 RED + sub-commit 3 GREEN)
  — 5 behavioral case: (1) happy path consume+unlink, (2) race window
  kapalı post-consume `FileNotFoundError`, (3) missing file `None` +
  `extra_env=None`, (4) wrong mode (0644) reject + cleanup, (5) end-to-end
  env var threading mock `_run_docker_exec`.
- Extension: [`tests/executor/test_playwright_health_reconciliation.py`](../../tests/executor/test_playwright_health_reconciliation.py)
  — 3 new case: env-priority over file, legacy file when env absent,
  empty-when-both-absent.
- Extension: [`tests/security/test_executor_host_error_redaction.py`](../../tests/security/test_executor_host_error_redaction.py)
  — 1 new case: `test_run_playwright_automation_redacts_harness_secret_env_var_in_error_message`
  (E4 mitigation pinli).
- Test izolasyonu: [`tests/executor/conftest.py`](../../tests/executor/conftest.py)
  autouse fixture `monkeypatch.delenv("EXECUTOR_HARNESS_PYTHON_SECRET_VALUE", raising=False)`.
- Mevcut W13-1 regression suite (`test_reconcile_w13_1_*`,
  `test_harness_marker_auth.py`) intact kalır — etkilenmez.

**Sub-commit dizisi (landed — 6/6 ana + 6 post-landing fix-up/extension = 12 toplam, W13-1 5-commit deseninden +7).**

1. `ccb8aee` `docs(W13-11): assign stable ID + lock in Path A eager-consume design`
   — bu blok + REFACTOR_STATUS banner + POST_POC_BACKLOG banner. Pure
   docs.
2. `d87b2ae` `test(W13-11): RED precursor — eager-consume behavioral + reconciliation
   env-priority cases` — 4 test dosyası, hepsi `@pytest.mark.skip` ile.
3. `68b2259` `feat(W13-11): host-side eager-consume + env var passthrough (RED →
   GREEN)` — 5 production dosyası; sub-commit 2 skip'leri kaldırılır;
   E4 masking helper dahil.
4. `d2f888f` `test(W13-11): architecture gate — sequence invariants + env var
   threading` — `tests/architecture/test_harness_secret_eager_consume.py`
   skip kaldır.
5. `9e08fcc` `test(W13-11): align cancel poll-point offsets + ScenarioZero
   mock for eager-consume` — `test_analysis_execution_poll_points.py` n=2..n=4
   offset shift + 1 yeni `cancel_before_consume_harness_python_secret` case;
   `test_router.py::ScenarioZeroExecutorControl` mock surface'a
   `consume_harness_python_secret` + `run_automation` kw `harness_python_secret`
   eklendi. Plan'da öngörülmemiş regression — sub-commit 3 yeni poll
   point ekledi, AST gate kapsadı ama bu iki behavioral/mock test'i
   ayrı surface'tan etkilendi.
6. `135a6b7` `docs(W13-11): close evidence + post-close doc drift sweep`
   — 9 doc dosyası (REFACTOR_STATUS, POST_POC_BACKLOG, W13/W14 tracker,
   CLAUDE.md, AGENT_CONTEXT, TESTING, agent-lanes/security-detection,
   REFACTOR_OPTIMIZATION §11.10). W13-12 follow-up required notu eklendi.
7. `9a2ba76` `docs(W13-11): stamp sub-commit 6 hash in tracker (post-landing fix-up)`
   — sub-commit 6 SHA'sının kendi gövdesinde stamp edilememesi nedeniyle
   ayrı bir self-stamp fix-up commit'i.
8. *(SHA stamped in next post-landing fix-up)* `docs(W13-11): banner alignment + W13-13 scope rebase (steal README sweep + regex pin)`
   — push öncesi drift fix-up: AGENTS.md banner W13-10 sonrası
   2026-05-11'de takılmıştı, CLAUDE.md parite hizalandı; README.md L3 +
   L58-61 7 sub-iter geride takılmıştı (W13-1..W13-4 closed dilinde),
   W13-1..W13-11 closure + W13-12/13 hold özetiyle güncellendi; W13-13
   scope rebase cascade — README sweep + paired regex pin originally
   W13-13 scope (F4) idi, sub-commit 8 + 12'de W13-11 push'una çekildi.
   Cascade referansları CLAUDE.md / REFACTOR_STATUS / REFACTOR_OPTIMIZATION
   §11.10 + §11.14 / W13 tracker (bu section + W13-13 section + F4 satırı)
   / W14 tracker entry gate'te güncellendi. Kod / test değişimi yok.
9. *(SHA stamped in next post-landing fix-up)* `test(W13-11): runtime invariant — secret unlinked before _install_extension call (defense-in-depth b)`
   — `tests/executor/test_harness_secret_eager_consume.py` extension:
   AST/sequence arch gate (`test_execute_analysis_request_consumes_secret_before_install`)
   ve mevcut unit-level unlink test'ini (`test_eager_consume_returns_secret_and_unlinks_file`)
   tamamlayan integration-level runtime invariant — `execute_analysis_request`
   mock'unda `_install_extension` çağrı anında secret file ERİŞİLEMEZ
   olduğunu pinler.
10. *(SHA stamped in next post-landing fix-up)* `test(W13-11): env var no-leak on docker exec success path (defense-in-depth c)`
    — `tests/executor/test_harness_secret_eager_consume.py` extension:
    happy-path subprocess.run sonucu (rc=0) için captured stdout/stderr'in
    secret hex değerini içermediğini pinler. Mevcut redaction test sadece
    exception path'i kontrol ediyordu (E4); başarı yolu defensive lock.
11. *(SHA stamped in next post-landing fix-up)* `test(W13-11): E4 redaction completeness across rc != 0 + report-missing paths (defense-in-depth a)`
    — `tests/security/test_executor_host_error_redaction.py` extension:
    `_mask_harness_secret_in_message` mevcut tek case (timeout path) ek
    olarak rc != 0 non-retryable (`host.py:132-139`), rc != 0 retryable
    transport error after retries (`host.py:141-148`), ve
    `run_playwright_automation` report-missing ExecutorError
    (`host.py:456-463`) path'lerinde de redaction'ı pinler.
12. *(SHA stamped in next post-landing fix-up)* `test(W13-11): README phase pointer regex pin (steal-from-W13-13)`
    — yeni `tests/architecture/test_readme_phase_pointer.py`: README'nin
    "Current Phase" section'ı `REFACTOR_STATUS.md`'nin `Last Updated`
    header'ıyla tutarlı kalmak zorunda (W13-N max'i regex extract +
    sweep ile aynı baseline). Original W13-13 F4 plan'ında paired
    sweep test'iydi; sub-commit 8'in sweep'iyle paired olarak burada
    landed.

**Test bar (closed — gerçek delta).**
| Metrik | Önce | 6/6 sonra | Post-landing additions (sub-commits 9-12) | Δ post-landing | Final |
|---|---|---|---|---|---|
| `make test-local` | 1521 | 1531 | +(b) 1 + (c) 1 + (a) 2 + (d) 2 | **+6** | **1537** |
| `make test-security` | 215 | 215 (lane unchanged) | (a)'s 2 cases live in `tests/security/test_executor_host_error_redaction.py` — Makefile `test-security` lane excludes that file, so its 8 cases (6 W10 redaction + 2 W13-11 E4 + 1 prior timeout-path case = 8 toplam) count toward `test-local` only | **0** (lane composition unchanged) | **215** |
| `tests/architecture/` | 105 | 110 | +(d) 2 cases (`test_readme_phase_pointer_not_behind_refactor_status` + `test_readme_phase_pointer_explicitly_mentions_latest_status_w13_n`) | **+2** | **112** |
| Production diff (net LoC) | — | +251 / -101 (host.py +140 / control.py +17 / reconciliation.py +29 / analysis_service.py +11 / analysis_execution.py +2 — `68b2259`) | post-landing zero production diff (test + doc only) | — | unchanged |

**Exit kriterleri (closed 2026-05-12).**

- [x] 6 sub-commit landed (`ccb8aee` docs · `d87b2ae` RED · `68b2259` feat impl · `d2f888f` arch gate · `9e08fcc` regression fix · `135a6b7` doc sweep). Plan W13-1 5-commit deseninden 6'ya genişletildi: W13-11 sub-commit 3 sequence shift'i (consume poll point #3) `test_analysis_execution_poll_points.py` n=2..n=4 offset'lerini ve `test_router.py::ScenarioZeroExecutorControl` mock surface'ını etkiledi; düzeltme `9e08fcc`'de ayrı sub-commit olarak landed (W13-12/13 close-gate öncesi atomic bisection için).
- [x] 9 yeni test case GREEN (3 arch + 5 behavioral + 3 reconciliation +
  1 redaction = 12 collected; 9 production-yeni, 3'ü mevcut dosyalara
  extension)
- [x] E4 redaction regression pinli (`_mask_harness_secret_in_message`
  in `executor/host.py`; arch gate threads `EXECUTOR_HARNESS_PYTHON_SECRET_VALUE`)
- [x] `make test-local` 1521 → 1531 (+10) / `make test-security` 215 unchanged (lane composition; E4 redaction case lives in `tests/security/test_executor_host_error_redaction.py` outside Makefile lane) / `tests/architecture/` 105 → 110 (+5)
- [x] W13-1 regression suite (`test_reconcile_w13_1_*`,
  `test_harness_marker_auth.py`) intact
- [x] W13-12 immediate follow-up not düşüldü (silent fail-closed gap'i W13-12
  kapatacak; W13-11 alone landed worst case = pre-W13-11 status quo, yeni
  regression yok). Close-out PR `week13 → main` W13-12/13 GREEN olmadan
  açılamaz.

**Post-landing additions (sub-commits 7-12, push `2026-05-12`).** Plan
6/6 ana sub-commit (acceptance bar) closed olduktan sonra push öncesi
banner-cascade + defense-in-depth kümesi:

- `9a2ba76` (7) — sub-commit 6 self-stamp fix-up (post-landing doc fix).
- *(SHA TBD)* (8) — `docs(W13-11)` banner alignment + W13-13 scope
  rebase cascade. AGENTS.md / README.md / CLAUDE.md / REFACTOR_STATUS /
  REFACTOR_OPTIMIZATION §11.10 + §11.14 / W13 tracker (bu section +
  W13-13 section + F4 satırı + summary list) / W14 tracker entry gate.
  W13-13 scope'undan F4 README sweep + paired regex pin (sub-commit
  12) çekildi; W13-13 elde kalan iş = cancel-race CAS only.
- *(SHA TBD)* (9) — `test(W13-11)` defense-in-depth (b) integration
  negative: orchestration-level runtime invariant for secret-unlinked-
  before-_install_extension.
- *(SHA TBD)* (10) — `test(W13-11)` defense-in-depth (c) env var
  no-leak on docker exec success path (happy-path stream defensive
  lock).
- *(SHA TBD)* (11) — `test(W13-11)` defense-in-depth (a) E4 redaction
  completeness across rc != 0 non-retryable / retryable / report-
  missing error paths.
- *(SHA TBD)* (12) — `test(W13-11)` README phase pointer regex pin
  paired with sub-commit 8 sweep (steal-from-W13-13).

Post-landing additions zero production diff; sadece test surface +
docs. Bu kümeyi W13-11 acceptance bar exit kriterlerine **eklenmez**
(close 2026-05-12'de zaten karşılandı) — push-time defense-in-depth
polish + W13-13 scope rebase olarak ayrı kategori.

---

### W13-12 — Fail-closed harness handshake (close-gate for W13-1 H6)

`Status: in progress 2026-05-12 (sub-commit 1/5 — design lockdown)` ·
`Source: [CLOSE-GATE codex-second-opinion-F2-fail-closed-harness-handshake]` ·
`Lane: [security-detection] [executor-runtime]` ·
`Blocks: week13 → main close-out PR` ·
`Depends: W13-11 GREEN (closed 2026-05-12 — eager-consume guarantees secret presence)`

**Sorun.**
[`_attempt_has_harness_completion_trace`](../../executor/flows/playwright/health/reconciliation.py:120)
empty `expected_nonce` durumunda legacy phase-only check'e düşüyor
(satır 143-146):

```python
return any(
    str(trace.get("phase", "")).strip() == "complete"
    for trace in traces_by_attempt.get(attempt_id, [])
)
```

Docstring iddiası: production'da `setup_monitor` her zaman secret'ı
populate eder, bu branch sadece unit-test construction'da tetiklenir.
Ancak [`load_harness_python_secret()`](../../executor/flows/playwright/health/reconciliation.py:51)
her okuma hatasında `""` döndürüyor: `FileNotFoundError`,
`OSError`, permission glitch, bind-mount race, eager-consume timing
hatası. Production secret eksikse sistem sessizce eski spoofable
moda düşüyor — fail-open.

**Etkilenen yollar.**

- [`reconciliation.py:120-146`](../../executor/flows/playwright/health/reconciliation.py:120)
  — `_attempt_has_harness_completion_trace`
- [`packages/analysis_contracts/contracts.py`](../../packages/analysis_contracts/contracts.py)
  — `ActivationReport` field eklenir
- [`dispatch.py:setup_monitor`](../../executor/flows/playwright/entrypoint/dispatch.py:112)
  — production construction site flag'i `True` set eder
- Mevcut W13-1 test'leri (`ActivationReport`'u manuel inşa eden) flag'i
  `False` set eder veya default'u test-friendly bırakılır

**Fix yönü.** `ActivationReport.harness_handshake_required: bool` field
(default değer = production-side `setup_monitor` set eder).
`_attempt_has_harness_completion_trace` imzası:

```python
def _attempt_has_harness_completion_trace(
    attempt: Any,
    traces_by_attempt: dict[str, list[dict[str, Any]]],
    expected_nonce: str = "",
    *,
    handshake_required: bool = False,  # production = True, test = False
) -> bool:
    # ...
    if expected_nonce:
        return any(... and _verify_harness_marker_signature(trace, expected_nonce))
    if handshake_required:
        return False  # fail-closed — handshake required but missing
    return any(str(trace.get("phase", "")) == "complete" for trace in ...)
```

`reconcile_event_attempts` callsite report'tan flag'i okur:
`handshake_required=bool(getattr(report, "harness_handshake_required", False))`.

**Test surface (planlanan).**

- Yeni: `tests/security/test_harness_handshake_required.py`
  — production flag set + expected_nonce empty → forged marker reject
  (W13-12 invariant)
- Mevcut W13-1 unit suite: `harness_handshake_required=False`
  default'unda kalmalı; explicit'leştirilmiş construction site flag'i
  ekler.
- Architecture gate: production `setup_monitor`'un her çağrısı
  `harness_handshake_required=True` set etmek zorunda (AST walk).

**Exit kriterleri.**

- Yeni 1 test + 1 arch gate green
- `ActivationReport` schema +1 field
- W13-1 mevcut regression suite zero-diff (default `False` legacy
  behavior'u korur)
- Production `setup_monitor` call site explicit `True` set eder

**Sub-commit dizisi (planned — 5/5, locked in 2026-05-12 sub-commit 1).**

> Implementation file note: `expected_harness_nonce` field aslında
> internal monitor dataclass'ında ([executor/flows/playwright/monitor/types.py:124](../../executor/flows/playwright/monitor/types.py))
> yaşıyor — public Pydantic `ActivationReport`
> ([packages/analysis_contracts/contracts.py:370](../../packages/analysis_contracts/contracts.py))
> ingest contract, runtime handshake invariant'ı internal'da. Yeni
> `harness_handshake_required` field W13-1 deseninin tam takipçisi olarak
> aynı internal dataclass'a eklenir; public Pydantic surface'a değmez.

1. *(SHA TBD)* `docs(W13-12): assign in-progress status + lock in fail-closed handshake design`
   — bu blok (sub-commit dizisi + design lockdown) + tracker header +
   REFACTOR_STATUS banner + POST_POC_BACKLOG banner. Pure docs.
2. *(SHA TBD)* `test(W13-12): RED precursor — production fail-closed + legacy phase-only baseline`
   — yeni `tests/security/test_harness_handshake_required.py` (2 case,
   `@pytest.mark.skip` ile). Sub-commit 3'te skip kaldırılır.
3. *(SHA TBD)* `feat(W13-12): harness_handshake_required field + signature + callsite + dispatch flag (RED → GREEN)`
   — 3 production dosyası:
   ([monitor/types.py:124](../../executor/flows/playwright/monitor/types.py)) +1 field,
   ([reconciliation.py:137,419](../../executor/flows/playwright/health/reconciliation.py)) signature/callsite,
   ([dispatch.py:129](../../executor/flows/playwright/entrypoint/dispatch.py)) `mon.report.harness_handshake_required = True`.
   Sub-commit 2 skip'leri kaldırılır.
4. *(SHA TBD)* `test(W13-12): architecture gate — setup_monitor stamps harness_handshake_required=True`
   — yeni `tests/architecture/test_setup_monitor_handshake_required.py`
   AST walker (`test_harness_marker_auth.py:142` deseni).
5. *(SHA TBD)* `docs(W13-12): close evidence + post-close doc sweep`
   — REFACTOR_STATUS row → closed; W13-12 §status → closed; CLAUDE.md
   banner W13-12 GREEN; POST_POC_BACKLOG W13-12 satırı strike-through;
   final bar numaraları stamp.

**Beklenen test bar deltası.**

| Lane | Pre-W13-12 (post-W13-11) | Post-W13-12 beklenen | Delta nedeni |
|---|---|---|---|
| `make test-local` | 1537 | 1537 (lane unchanged) | yeni 2 security case `tests/security/` altında — `test-local` lane bunları kapsamıyor (W13-11 deseni) |
| `make test-security` | 215 | 217 (+2) | yeni `test_harness_handshake_required.py` 2 case |
| `tests/architecture/` | 112 | 113 (+1) | yeni `test_setup_monitor_handshake_required.py` 1 case |
| `make check-all` | green | green | lint/type/style invariant |

Final stamp sub-commit 5'te yapılır.

---

### W13-13 — Worker-start cancel-race CAS (close-gate for W13-3 H4)

`Status: CLOSE-GATE — not started 2026-05-11 (Codex Cloud second-opinion review); scope rebased 2026-05-12 — F4 README sweep + regex pin landed early in W13-11 push (sub-commits 8 + 12)` ·
`Source: [CLOSE-GATE codex-second-opinion-F3-worker-start-cancel-race-CAS]` ·
`Lane: [platform-storage] [executor-runtime]` ·
`Blocks: week13 → main close-out PR`

**Sorun.** W13-3 iki-fazlı cancel `running → cancelling → cancelled`
state machine'i kuruyor; `cancel_analysis_job` (`lifecycle.py:128-156`)
`with_for_update()` ile atomik `queued/running → cancelling`. Ancak
async start endpoint'i [`router.py:243,255-262`](../../workflows/marketplace/router.py:243)
queued job snapshot döndürdükten sonra worker thread'i ayrı akışta
spawn ediyor. Worker'ın ilk eylemi
[`run_analysis_job:194-200`](../../workflows/marketplace/analysis_service.py:194)
**koşulsuz** `update_job(status="running", started_at=...)`.

Yarış:

```text
t0  POST /analyze/start → reserve_job → status="queued", commit, lock release
t1  threading.Thread(target=run_analysis_job).start()
t2  HTTP response: {"status": "queued", ...}
t3  POST /analyze/<id>/cancel → cancel_analysis_job: queued → cancelling (atomic)
t4  Worker enters run_analysis_job → update_job(status="running")
      ↑ cancelling üzerine yazar; cancel intent kaybolur
t5  cancel_check() → is_job_cancelled → False (status="running")
t6  Worker scan'i tamamlar; user cancel'in farkında değil
```

`update_job` compare-and-set yok — sadece naive assignment. W13-3'ün
"cancel intent authoritative" sözleşmesini bu yarış bozuyor.

**Etkilenen yollar.**

- [`workflows/marketplace/analysis_service.py:187-200`](../../workflows/marketplace/analysis_service.py:187)
  — worker entry
- [`appcore/storage/crud_ops/analysis_jobs/lifecycle.py:128-204`](../../appcore/storage/crud_ops/analysis_jobs/lifecycle.py:128)
  — `cancel_analysis_job` + `finalize_cancelled_analysis_job` zaten
  doğru, sadece worker entry tarafında karşılık eksik
- [`workflows/marketplace/job_service.py`](../../workflows/marketplace/job_service.py)
  — `update_job` (kontrol: compare-and-set ekle veya worker
  entry'sinde manual snapshot check)
- [`README.md:58`](../../README.md:58) — F4 doc drift sweep

**Fix yönü (Path B — worker entry snapshot check).** Worker entry'sinde
`with_for_update()` snapshot:

```python
def run_analysis_job(job_id, request):
    db = _open_job_session()
    with db.begin():
        stmt = select(AnalysisJob).where(AnalysisJob.job_id == job_id).with_for_update()
        job = db.scalars(stmt).first()
        if job is None:
            logger.warning("Job %s vanished before worker entry", job_id)
            return
        if job.status in _TERMINAL_JOB_STATUSES:
            logger.info("Job %s already terminal (%s); worker exits", job_id, job.status)
            return
        if job.status == "cancelling":
            # User cancelled before worker started; finalize directly
            finalize_cancelled_analysis_job(db, job_id, "Cancelled before worker started.")
            return
        # queued → running (atomic under lock)
        job.status = "running"
        job.started_at = time.time()
        # commit happens at with db.begin() exit
    # ... rest of run_analysis_job
```

W13-3'ün two-phase exit deseniyle tam simetri: cancel signal worker
entry'sinde de honored.

**Path A alternatifi (reddedilen).** `update_job` `expected_status`
parametresi compare-and-set yapar (`UPDATE … WHERE status='queued'`).
0-row-affected ise worker erken çıkar. Daha küçük diff ama
`finalize_cancelled_analysis_job` çağrısını mevcut exception handler
path'inden ayrı bir entry-point handler'ına ihtiyaç duyar — code
duplication. Path B daha temiz.

**F4 — README drift sweep — REBASED to W13-11 push `2026-05-12`.**
[`README.md:58`](../../README.md:58) "W13-1..W13-4 closed, W13-5 expected"
drift'i W13-11 push sub-commit 8 (doc fix-up + W13-13 scope rebase
cascade) içinde sweep edildi; paired regex pin
`tests/architecture/test_readme_phase_pointer.py` sub-commit 12'de landed.
Tarihsel kayıt için orijinal W13-13 plan metni aşağıda korunur:
[`README.md:58`](../../README.md:58) hâlâ
"W13-1..W13-4 closed, W13-5 expected" satırını taşıyor. Same commit'te
W13-1..W13-13 close-out state'ine güncellenir; W14 staging pointer'ı da
README ana README'sine eklenir (slim canonical drift örüntüsü).

**Test surface (planlanan).**

- Yeni behavioral: `tests/platform/storage/test_analysis_jobs_cancel_at_worker_entry.py`
  — concurrent fixture: cancel between reserve_job and worker entry;
  invariant: cancel intent honored, worker exits without running scan.
- Yeni architecture gate `tests/architecture/test_run_analysis_job_entry_snapshot.py`
  — AST walk: `run_analysis_job`'un ilk DB action'ı `select(...).with_for_update()`
  veya equivalent guarded transition; unconditional `update_job(status="running")`
  yasak.
- Mevcut W13-3 test suite intact kalır (cancel during running, queued
  reservation, two-phase finalize).
- README literal regression: yeni `tests/architecture/test_readme_phase_pointer.py`
  → README'deki "active phase" satırı `REFACTOR_STATUS.md`'nin
  `Last Updated` header'ıyla tutarlı kalmak zorunda (regex pin).

**Exit kriterleri.**

- 2 yeni behavioral + 2 yeni arch gate green
- Worker entry race kapanır; W13-3 cancel intent authoritative
  sözleşmesi tam korunur
- README ve W13/W14 phase pointer'ları drift-free
- W13-3 mevcut close evidence supplement edilir

---

## W12 Lessons Learned (carry-forward)

From `W12-close-acceptance-completed-2026-05-10.md` §8.3 (now archived).
Three operational
lessons to keep in mind when planning W13 splits and validations:

1. **Container build cache must be reset between W13-N iterations.**
   The W12-5 first live-scan run hit a stale executor container with
   pre-W12-5 code; only the second UI-triggered scan (after
   `make exec-build && make exec-up`) saw the refactored code. Plan
   the live-scan step to require an explicit rebuild + bring-up before
   each detection-relevant comparison.
2. **Tests-driven refactor still requires monkey-patch awareness.**
   The W12-5 split needed a `_resolve_vscode_logs_dir()` lazy-facade
   helper specifically so the 23-case existing safety net's
   `monkeypatch.setattr(extension_host, "VSCODE_LOGS_DIR", tmp_path)`
   pattern would survive after `VSCODE_LOGS_DIR` moved to the new
   module. W13 split candidates should pre-audit similar monkeypatch
   dependencies before relocating module-level constants.
3. **Plan validation pass is high-leverage.** The W12-5 plan
   originally missed three re-export names (`_TIMESTAMP_RE`,
   `_activation_within_monitoring_window`, `VSCODE_LOGS_DIR`); a
   pre-implementation grep audit caught them. Apply the same
   discipline to W13 plans: explicit grep audit for every name that
   moves, before the first refactor commit.

## References

- Plan source: `documents/REFACTOR_OPTIMIZATION.md` §11.10.
- Backlog: `documents/POST_POC_BACKLOG.md` — `[FOLLOWUP …]` items
  marked W13 / W13-X / W13-X watching.
- Predecessor lane (frozen): `W12-executor-subpackaging.md` (stable
  IDs `W12-0`..`W12-5`).
- Older predecessor lanes (frozen, stable-ID-only):
  `W11-monitor-lifecycle.md` (`W11-1`..`W11-8`),
  `W8-security.md` (`W8-1`..`W8-9`).
- W12 close-out evidence (archived):
  `documents/archive/active-work/W12-close-acceptance-completed-2026-05-10.md`.
- Architecture rules entrypoint: `AGENTS.md` (root).
- Task routing: `documents/AGENT_CONTEXT.md`.
- Authoritative current-state pointer: `documents/REFACTOR_STATUS.md`.
