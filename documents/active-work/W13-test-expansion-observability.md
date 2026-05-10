# W13 — Test Expansion + Observability (Active Work Tracker)

`Last Updated: 2026-05-10 (W13-1 stable ID assigned + Option C design lock-in; sub-commit 1 / 5 in progress)`
`Phase: W13 active`
`Branch: week13 (single-branch policy precedent; opened 2026-05-10 from cff6455)`
`Owner: ekrem`

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

- **W13 active.** Entry baseline established `2026-05-10` post-W12
  merge to `main` via PR #18 (`33a0852`); Codex Cloud security audit
  `2026-05-10` ingested same day (4 HIGH + 2 MEDIUM pull-forwards
  added to Candidate Items table; full triage in
  `POST_POC_BACKLOG.md` `## Codex Cloud Audit 2026-05-10`).
  Documentation foundation complete: lane tracker rows, POST_POC
  Codex audit section, `REFACTOR_OPTIMIZATION.md` §11.10 audit pass
  entry, `REFACTOR_STATUS.md` audit pass section. Branch `week13`
  opened from `cff6455`. **First item pulled `2026-05-10`:** `W13-1`
  (Codex H6 spoofable harness markers, highest integrity-risk per
  audit triage). Design decision locked: **Option C — file-based
  ephemeral handshake + HMAC-SHA256 nonce on stimulus markers**;
  rationale and 5-sub-commit roadmap in "Per-Item Detail" → W13-1.
  Sub-commit 1 (docs-only stable-ID assignment + design lock-in)
  in progress; production code untouched. Full 12-item revised
  sequencing: `~/.claude/plans/week13-master-plan.md`. Per-iteration
  plan (W13-1 only): `~/.claude/plans/week13-geli-tirmesi-i-in-iterasyona-partitioned-canyon.md`.
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
    `W12-close-acceptance.md` §3.4.

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
Cloud security scan. The `2026-05-10` audit's 4 HIGH OPEN findings
(H3 dev-lan Makefile drift, H4 cancel concurrent race, H5 writable
VS Code launcher, H6 spoofable harness markers) plus 2 MEDIUM
pull-forwards (M1 PEM regex DoS, M9 arguments_preview redaction) are
**W13 acceptance-bar mandates** per `REFACTOR_STATUS.md` `## 2026-05-10
Codex Cloud Audit Pass` — they must close before W13 close.

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
| **TBD HIGH** | `[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]` (`Makefile:170-172` `dev-lan` hard-codes `--host 0.0.0.0` while `runbooks/lan-exposure.md:82-87` documents `API_HOST` override; `tests/architecture/test_default_bindings.py` covers settings layer only — no Makefile gate. Doc-fix or recipe-fix; either lands a regression test) | `[security-detection]` `[platform-storage]` | not started |
| **TBD HIGH** | `[FOLLOWUP codex-2026-05-10-H4-cancel-concurrent-race]` (cross-ref `[FOLLOWUP simulation-progress-cancel]` 5 sub-items already in POST_POC; `cancelled` is terminal in `appcore/storage/crud_ops/analysis_jobs/lifecycle.py:41` so `reserve_job()` releases the lock immediately; cancellation polled only in heartbeat. Add a "draining" intermediate state or block `reserve_job` while a cancelled-but-running worker exists; cover reset/install/trigger gaps with cancel-poll points) | `[executor-runtime]` `[platform-storage]` | not started |
| **TBD HIGH** | `[FOLLOWUP codex-2026-05-10-H5-writable-vscode-launcher]` (`executor/container/Dockerfile:113-115` chowns `launch_vscode.sh` to `executor:executor` mode 755 — analyzed extension can overwrite, persists across resets via `reset_state.py`. Move to `--chown=root:executor` + `chmod 0750`; root-own + executor read+exec only) | `[executor-runtime]` `[security-detection]` | not started |
| **W13-1** | `[FOLLOWUP codex-2026-05-10-H6-spoofable-harness-markers]` (`executor/flows/playwright/health/reconciliation.py:18-50` accepts `[extrace-harness] {json}` from target-writable Extension Host log stream as proof of `automation_trace`; no auth/nonce. Forged `phase:"complete"` markers can satisfy verification → forged clean reports. Monitor-owned side channel (executor-only writable file path) or HMAC nonce stamped in `start.sh` and unavailable to target) | `[executor-runtime]` `[security-detection]` | in progress (sub-commit 1 / 5) |
| TBD | `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]` (`packages/analysis_contracts/evidence.py:106-121` `redact_multiline_secrets()` private_key regex unanchored + lazy cross-line span `(?:.\|\n)*?` → catastrophic backtracking on many unmatched BEGIN markers; W12-0 added the redaction itself, this is a follow-up DoS vector. Bounded state machine or size cap) | `[security-detection]` | not started |
| TBD | `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]` (W12-5 `tests/architecture/test_network_body_preview_redaction.py` covers `request_body_preview` / `response_body_preview` only; `executor/flows/playwright/runtime_capture/extension_host_strace_parse.py:60,70,78` assigns `arguments_preview` without `redact_secrets()`. Extend the W12-5 gate scope and route arguments_preview through `redact_secrets`) | `[security-detection]` | not started |
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

`Status: in progress (sub-commit 1 / 5)` ·
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

**Sub-commit Roadmap (5 commits).**

| # | Commit | Touch | Doğrulama |
|---|---|---|---|
| 1 | docs(W13-1): assign stable ID + design decision lock-in | Bu Per-Item Detail bloğu + Candidate Items table güncellemesi | `make check-all` baseline (1452 / 211 / 76) bozulmaz; production code diff yok |
| 2 | test(W13-1): RED precursor for harness marker auth | `tests/executor/test_playwright_health_reconciliation.py` 3 yeni `@pytest.mark.skip(reason="W13-1 implementation pending sub-commit 4")` test | `make test-local` 1452 → 1452 (skip nedeniyle delta yok) |
| 3 | feat(W13-1): nonce generation + harness handshake | `start.sh` (secret üretimi + iki dosya yaz), `Dockerfile` (`/run/extrace` dizini), `extension.js`/`markers.js` (read+unlink+HMAC) | `make exec-build && make exec-up`; container içinde `ls /run/extrace` boş; harness markers'da `nonce` field görünür |
| 4 | feat(W13-1): reconciliation verifier + RED → GREEN | `reconciliation.py` (`_verify_harness_marker_signature` + entegrasyon), Python tarafında secret okuma; sub-commit 2 skip kaldır | `make test-local` 1452 → ≥1455; `make test-security` 211 → ≥213 |
| 5 | test(W13-1): architecture gate + live-scan delta | `tests/architecture/test_harness_marker_auth.py` (yeni AST gate), live-scan baseline ile karşılaştırma + semantic-delta dokümantasyonu | `tests/architecture/` 76 → 77; `make check-all` ✅; live-scan job ID + delta tracker'a yazılı |

**Sub-commit 1 verification (bu commit).**

- [x] Candidate Items table: H6 satırı `**TBD HIGH**` → `**W13-1**`
- [x] Per-Item Detail W13-1 bloğu yazıldı (scope, files, race
      analysis, design decision, sub-commit roadmap)
- [ ] Production kod / test diff yok (next: `git diff --stat`
      sadece tracker dosyasını göstermeli)
- [ ] `make check-all` baseline bozulmadı (sub-commit 1 sonrası
      sanity check)

## W12 Lessons Learned (carry-forward)

From `W12-close-acceptance.md` §8.3 (now archived). Three operational
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
