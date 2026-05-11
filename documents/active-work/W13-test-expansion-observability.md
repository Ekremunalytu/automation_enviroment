# W13 — Test Expansion + Observability (Active Work Tracker)

`Last Updated: 2026-05-11 (W13-6 closed — Codex M9 arguments_preview redaction extension; 3/5 sub-commits landed via 94f7fa4/70ad721/9f8ecb4, this commit is sub-commit 4; factory-internal redaction at _bounded_arguments_preview() routes through redact_secrets() before truncate; new architecture gate test_arguments_preview_redaction.py 2/2 ✓ + parametrized regression 5/5 ✓; W13-5 closed prior — 5/5 sub-commits, dev-lan Makefile drift / Codex H3)`
`Phase: W13 active`
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

- **W13 active. W13-1..W13-6 are closed.** Entry baseline was
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
- **Next pull after W13-6:** M1 PEM regex DoS expected as W13-7 (bounded
  scanner / size cap on `redact_multiline_secrets()` private_key cross-line
  span; [evidence.py:56-63,106-121](../../packages/analysis_contracts/evidence.py)).
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
| TBD | `[§11.10 GOAL]` Benign silence fixture 3→5 (current 2 fixtures: `extrace.fixture-chat-0.0.1`, `extrace.fixture-theme-0.0.1`; consumers `tests/security/test_benign_silence.py:6-17` + `tests/platform/contracts/test_analysis_fixture_baselines.py:38-40`; need 3 new fixture extensions + baseline JSONs) | `[security-detection]` | not started |
| TBD | `[§11.10 GOAL]` Stale singleton-lock recovery integration test (`cleanup_singleton_locks()` at `executor/flows/playwright/reset_state.py:131-145`; existing 3 unit cases in `tests/executor/test_reset_state.py:70-168` cover cleanup mechanics but not the lock-held → reset → recovery scenario) | `[executor-runtime]` | not started |
| TBD | `[§11.10 GOAL]` `.env` gitignore regression test (`.gitignore` already pins `*.env` / `.env` / `!.env.example` and `.env.example` is tracked; no architecture gate exists today — new `tests/architecture/test_env_gitignore.py` via `git check-ignore`) | `[security-detection]` | not started |
| TBD | `[§11.10 GOAL]` `extrace.executor.*` logger consolidation (discovery first — initial grep found zero `getLogger("extrace*` / `getLogger('extrace*` matches; W13-6 may scope out if no fragmentation exists, or pull canonical naming if any is found) | `[platform-storage]` | not started |
| TBD | `[§11.10 GOAL]` Run-ID stamping (job_id exists at `appcore/storage/model_defs/analysis_job.py` and `appcore/contracts/schema_defs/analysis_jobs.py:16` but is not propagated as a correlation identifier through log records, `EvidenceEvent`, or DB row chains; multi-lane plumbing) | `[platform-storage]` `[executor-runtime]` `[security-detection]` | not started |
| TBD | `[§11.10 GOAL]` W8-W12 regression lock-in (umbrella for any regression coverage missing on W8-W12 landed work; concrete sub-items pulled from `POST_POC_BACKLOG.md` deferrals as W13 progresses; close-pass evaluates which followups are bundled vs deferred to W14+) | (multi) | not started |
| **W13-5** | `[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]` (`Makefile:170-172` `dev-lan` hard-codes `--host 0.0.0.0` while `runbooks/lan-exposure.md:82-87` documents `API_HOST` override; `tests/architecture/test_default_bindings.py` covers settings layer only — no Makefile gate. Path A recipe-fix landed: `--host $${API_HOST:-0.0.0.0}` + new `tests/architecture/test_makefile_dev_recipes.py` regression gate + lan-exposure §Host-mode drift caveat removal) | `[security-detection]` `[platform-storage]` | **closed (5/5 sub-commits, 2026-05-11)** |
| **W13-4** | `[FOLLOWUP w13-3-close-pass-cancellation-test-hardening]` (W13-3 6 architecture gates pin AST invariants only — no behavioral coverage exists for: 5 poll-point raise paths actually firing inside `execute_analysis_request`, cancel↔complete DB-level race serialization under `with_for_update()`, stuck-`cancelling` boot_id recovery via `recover_interrupted_jobs` (design intent: `cancelling`→`failed` by boot_id mismatch), Alembic `c8a2d4e91f5b` upgrade/downgrade data motion, `run_analysis_job` exception handler driving `finalize_cancelled_job` on both `AnalysisCancelledError` and `is_job_cancelled`-true hard-error paths, finalize negative (absent + already-cancelled idempotency). Plus runbook drift: `documents/runbooks/analysis-job-stuck.md:42` 4-status literal stale post-W13-3, no playbook for stuck-cancelling) | `[platform-storage]` `[executor-runtime]` | **closed (8/8 sub-commits, 2026-05-11)** |
| **W13-3** | `[FOLLOWUP codex-2026-05-10-H4-cancel-concurrent-race]` (cross-ref `[FOLLOWUP simulation-progress-cancel]` 5 sub-items already in POST_POC; `cancelled` was terminal in `appcore/storage/crud_ops/analysis_jobs/lifecycle.py:41` so `reserve_job()` released the lock immediately; cancellation polled only in heartbeat. Option A: `cancelling` non-terminal state added to `ACTIVE_ANALYSIS_JOB_STATUSES` + partial unique index, two-phase cancel via new `finalize_cancelled_analysis_job` helper, `_raise_if_cancelled` poll points at 5 hot-zones) | `[executor-runtime]` `[platform-storage]` | **closed (6/6 sub-commits, 2026-05-10)** |
| **W13-2** | `[FOLLOWUP codex-2026-05-10-H5-writable-vscode-launcher]` (`executor/container/Dockerfile:121-128` chowns `launch_vscode.sh` to `executor:executor` mode 755 — analyzed extension can overwrite, persists across resets via `reset_state.py`. Moved to `chown root:executor` + `chmod 0750`; root-own + executor read+exec only) | `[executor-runtime]` `[security-detection]` | **closed (3/3 sub-commits, 2026-05-10)** |
| **W13-1** | `[FOLLOWUP codex-2026-05-10-H6-spoofable-harness-markers]` (`executor/flows/playwright/health/reconciliation.py:18-50` accepts `[extrace-harness] {json}` from target-writable Extension Host log stream as proof of `automation_trace`; no auth/nonce. Forged `phase:"complete"` markers can satisfy verification → forged clean reports. Monitor-owned side channel (executor-only writable file path) or HMAC nonce stamped in `start.sh` and unavailable to target) | `[executor-runtime]` `[security-detection]` | **closed (5/5 sub-commits, 2026-05-10)** |
| TBD | `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]` (`packages/analysis_contracts/evidence.py:106-121` `redact_multiline_secrets()` private_key regex unanchored + lazy cross-line span `(?:.\|\n)*?` → catastrophic backtracking on many unmatched BEGIN markers; W12-0 added the redaction itself, this is a follow-up DoS vector. Bounded state machine or size cap) | `[security-detection]` | not started |
| **W13-6** | `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]` (W12-5 `tests/architecture/test_network_body_preview_redaction.py` covers `request_body_preview` / `response_body_preview` only; `executor/flows/playwright/runtime_capture/extension_host_strace_parse.py:60,70,78` assigns `arguments_preview` without `redact_secrets()`. Replica architecture gate (new `tests/architecture/test_arguments_preview_redaction.py` — factory body invariant + routing invariant) + factory-internal redaction inside `_bounded_arguments_preview()` so 3 call sites stay GREEN unchanged + parametrized regression covering 5 secret classes) | `[security-detection]` `[executor-runtime]` | **closed (5/5 sub-commits, 2026-05-11)** |
| TBD watch | `[FOLLOWUP planner-selection-readability-audit]` (`analysis_planner/selection.py` 497 LoC; refactor only when activation family or planner bug triggers) | `[security-detection]` | watching |
| TBD watch | `[FOLLOWUP attribution-links-build-evidence-bundle-density]` (`attribution/links.py` 601 LoC; reassess after evidence-event-kind invariant lands) | `[executor-runtime]` | watching |
| TBD watch | `[FOLLOWUP execute-attempt-rebloat-watch]` (`stimulus/attempts.py::execute_attempt` chain growth; refactor only when new action family added) | `[executor-runtime]` | watching |
| TBD watch | `[FOLLOWUP dispatch-execution-rebloat-watch]` (`entrypoint/dispatch.py` 402 LoC W12-4 ratchet; add `test_dispatch_execution_under_loc_budget` only after concrete bloat) | `[executor-runtime]` | watching |

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
