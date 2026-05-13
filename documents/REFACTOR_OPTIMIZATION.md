# REFACTOR_OPTIMIZATION

`Last Updated: 2026-05-13 (W13 closed 2026-05-13 — W13-1..W13-13 all GREEN; W13-1..W13-7 closed acceptance bar; W13-8/9/10 closed §11.10 GOAL pulls; W13-11 HMAC python secret target-install race closed 2026-05-12 (6/6 sub-commits) — Path A host-side eager-consume + env var passthrough; W13-12 fail-closed harness handshake closed 2026-05-12 (5/5 sub-commits — `harness_handshake_required: bool` + fail-closed branch + 3-fact AST gate; final bar test-local 1537 → 1539 → 1542 / 112 → 115); W13-13 worker-start cancel-race CAS closed 2026-05-13 (5/5 sub-commits + post-landing — Path B worker-entry `with_for_update()` snapshot lock + lifecycle-helper-not-wrapper deadlock avoidance + 2-fact AST gate + 4 post-landing behavioral pins (vanished row + finalize idempotency + failed/cancelled terminal); final bar test-local 1542 → 1547 (+5 main) → 1551 (+4 post-landing) / 115 → 117 (+2)); close-out PR #20 (week13 → main) MERGED 2026-05-13 via 772deb3 (close-gate cleared pre-merge); §12 W14 staging scope pre-entry, entry gate triggered by close-out merge — awaiting explicit pull)`

W0-W14 plan document: stabilization + security + post-PoC external-review
integration + W14 acceptance + observability continuation. **Slim canonical**
— full historical content is frozen under dated snapshots:

- latest full snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-11.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-11.md)
- older snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md)

## Anchor Map

- §10 / §10.7 → W0-W7 PoC window and acceptance bar.
- §11 / §11.0 - §11.4 → W8-W13 external-review integration frame.
- §11.5 → W8 tracker:
  [`active-work/W8-security.md`](active-work/W8-security.md).
- §11.6 - §11.10 → W9-W13 weekly briefs.
- §11.11 - §11.14 → cross-ref, rejected, lane, and exit criteria summaries.
- §12 → W14 Codex M-class Acceptance + Observability (staging, activates on
  W13 close-out PR merge). Tracker:
  [`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md).

## §10 — W0-W7 PoC Stabilization Window (closed 2026-04-23)

PoC window closed `2026-04-23` with §10.7 acceptance bar 11/11 green.
Detailed W0-W7 plan history lives in the archive.

### §10.7 — PoC acceptance checklist (W7 sonu, closed 2026-04-23)

- [x] Legacy top-level business directories removed.
- [x] `packages/` import-graph enforcement exists.
- [x] VS Code version pinned; harness extension checksum verified.
- [x] Executor control boundary exists.
- [x] A1/A2/A4/A6 canaries and rules landed; A3 landed in the W7 buffer.
- [x] Benign baseline, scenario-dropout honesty, verdict rollup, UI finding
  display, `make test-security`, and demo acceptance were green.

## §11 — W8-W13 External Review Integration Window (2026-04-24+)

§11 integrates the post-PoC external reviews without moving the W0-W7 PoC
acceptance bar. Review snapshots live under `archive/reviews/`.

### §11.0 — Neden §11, §10'a ek satır değil

W8-W13 work is post-PoC hardening and modularization. Keeping it under §11
preserves the audit trail that §10.7 already closed.

### §11.1 — Entry Gate

W8 entry gate was met `2026-04-27`: PR345 PRs 1-5 landed, ADR 0006 accepted,
`make test-security` entry baseline was green, demo acceptance was green, and
W8-0 deterministic harness readiness landed.

Current closure chain: W8 closed `2026-04-29`; W9 closed `2026-05-04` via
PR #9; W10 closed `2026-05-04` via PR #11; W11 closed `2026-05-05` via
PR #14; W12 closed `2026-05-10` via PR #18; W13 is active.

### §11.2 — Haftalık dağılım (W8-W13)

| Hafta | Etiket | Status |
|---|---|---|
| W8 | Security hardening | closed `2026-04-29`; W8-8 deferred |
| W9 | Executor/detection boundary | closed `2026-05-04`; ADR 0008 accepted |
| W10 | Contract hygiene + planner cleanup | closed `2026-05-04`; PR #11 |
| W11 | Monitor lifecycle split | closed `2026-05-05`; PR #14 |
| W12 | Executor subpackaging + attribution cleanup | closed `2026-05-10`; PR #18 |
| W13 | Test expansion + observability | active; W13-1..W13-7 closed (acceptance bar cleared) |

### §11.3 — Haftalar arası bağımlılıklar

- W10 depends on W9 package-mode import discipline.
- W11 depends on W10 typed contracts.
- W12 depends on W11 monitor lifecycle split.
- W13 locks in W8-W12 regression coverage and pulls audit follow-ups.

### §11.4 — Non-goals

Queue-backed distributed workers, multi-tenant accounts, broad run-history
infrastructure, and speculative UI/product expansion remain outside W8-W13
unless pulled from `POST_POC_BACKLOG.md` with a stable ID.

### §11.5 — W8 Güvenlik Sıkılaştırma

Moved to [`active-work/W8-security.md`](active-work/W8-security.md). W8 is
closed for active work; retained for W8-1..W8-9 stable-ID references.

### §11.6 — W9 Executor/Detection Boundary

W9 closed `2026-05-04` via PR #9. ADR 0008 container package-mode invocation
is accepted; dual-import fallback and runtime `sys.path.insert` debt were
removed.

### §11.7 — W10 Contract Hygiene + Planner Cleanup

W10 closed `2026-05-04` via PR #11. `schema_version`, planner registry
cleanup, typed health/coverage models, executor action enum, and W10
contract gates landed.

### §11.8 — W11 Monitor Lifecycle Split

W11 closed `2026-05-05` via PR #14. W11-1..W11-8 split monitor runtime,
report assembly, scenario accounting, monitor facade, workflow service, and
storage CRUD modules. Tracker:
[`active-work/W11-monitor-lifecycle.md`](active-work/W11-monitor-lifecycle.md).

### §11.9 — W12 Executor Subpackaging + Attribution Cleanup

W12 closed `2026-05-10` and merged via PR #18 (`33a0852`). Tracker is frozen:
[`active-work/W12-executor-subpackaging.md`](active-work/W12-executor-subpackaging.md).

Closed scope:

- W12-0 security pull-forward: file-backed output-signal redaction.
- W12-1 executor subpackaging: ≤10 flat Playwright modules, 10 package dirs,
  `python -m` shims, and import-cycle gates.
- W12-2 attribution facade cleanup: public facade trimmed, companion follow-ups
  closed.
- W12-3 `raw_context` discriminated union typing.
- W12-4 entrypoint dispatch extraction: `runner.py::main` under 200 LoC.
- W12-5 `runtime_capture/extension_host.py` split + body-preview redaction
  architecture gate.
- UI/API Dockerfile digest pins, W12 close-out coverage, and Codex CRITICAL
  subprocess-output redaction fix.

Final close evidence is archived at
[`archive/active-work/W12-close-acceptance-completed-2026-05-10.md`](archive/active-work/W12-close-acceptance-completed-2026-05-10.md).

#### §11.9.1 — `runtime_capture/extension_host.py` Split Scoping

§11.9.1 is closed by W12-5. Full scoping detail lives in the W12 tracker and
archive snapshot; current code keeps `extension_host.py` as a thin facade over
focused runtime-capture modules.

### §11.10 — W13 Test Expansion + Observability

Entry conditions were met `2026-05-10`: W12 closed and merged; W12 close
baseline `make check-all` was green at close commit `e8a9926`
(`make test-local` 1452 / `make test-security` 211 /
`tests/architecture/` 76). Active tracker:
[`active-work/W13-test-expansion-observability.md`](active-work/W13-test-expansion-observability.md).

Goal: benign silence fixture breadth, stale singleton-lock and `.env`
regression gates, executor logger/run-ID observability, and W8-W12 regression
lock-in.

Audit pull-forwards:

- W13-1 closed `[FOLLOWUP codex-2026-05-10-H6-spoofable-harness-markers]`.
- W13-2 closed `[FOLLOWUP codex-2026-05-10-H5-writable-vscode-launcher]`.
- W13-3 closed `[FOLLOWUP codex-2026-05-10-H4-cancel-concurrent-race]`.
- W13-4 closed `[FOLLOWUP w13-3-close-pass-cancellation-test-hardening]`.
- W13-5 closed `[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]`.
- W13-6 closed `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]`.
- W13-7 closed `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]`.
- No MEDIUM/HIGH Codex acceptance items remain open. Codex Cloud
  audit (2026-05-10) acceptance bar fully cleared.

§11.10 GOAL pulls (post-acceptance-bar):

- W13-8 closed `[§11.10 GOAL] Benign silence fixture 3→5`. 3 new
  fixture extensions authored under `extensions/`
  (`extrace.fixture-snippet-0.0.1` declarative snippets,
  `extrace.fixture-keybinding-0.0.1` declarative keybindings,
  `extrace.fixture-cmd-0.0.1` `onCommand:` activation), matching
  baseline activation reports added, and `_FIXTURE_REPORTS` /
  `BASELINE_EXTENSION_FIXTURES` / `expected_activation_event_types`
  extended. `tests/security/test_benign_silence.py` 5/5 ✓ (3 RED
  skip decorators removed); `make test-security` 212 → 215 (+3
  passed). Production code untouched.
- W13-9 closed `[§11.10 GOAL] .env gitignore regression test`. New
  architecture gate `tests/architecture/test_env_gitignore.py` 10/10
  ✓ pins the `.env` / `*.env` / virtualenv / `!.env.example` rule
  set via `git check-ignore`. Underlying `.gitignore` was already
  correct; pre-W13-9 there was no architecture gate locking the
  invariant.
- W13-10 closed `[§11.10 GOAL] Stale singleton-lock recovery
  integration test`. 2 new integration cases in
  `tests/executor/test_reset_state.py` (13/13 ✓) exercise
  `cleanup_singleton_locks()` integration inside
  `reset_executor_state()` with real held-lock filesystem state
  (full-set and partial-set variants). Pre-W13-10 unit cases stubbed
  the cleanup; W13-10 covers the integration gap.

Original §11.10 candidates that remain open are tracked in
`POST_POC_BACKLOG.md` and the W13 tracker Candidate Items table. The
close-out PR (`week13 → main`) bundles whichever §11.10 GOAL pulls
have reached GREEN at the cut-off; the remainder iter into W14.

§11.10 close-gate (added `2026-05-11` after Codex Cloud second-opinion
review on `week13`):

- ~~W13-11~~ (`[CLOSE-GATE codex-second-opinion-F1-hmac-python-secret-target-install-race]`)
  — **closed `2026-05-12`** (6/6 sub-commits). Close-pass for W13-1 H6.
  Path A host-side eager-consume + env var passthrough landed:
  `workflows/marketplace/analysis_service.py::execute_analysis_request`
  calls `executor_control.consume_harness_python_secret()` between
  `_reset_sandbox()` and `_install_extension()`, reads bind-mounted
  `Path(settings.project.OUTPUT_DIR) / "_extrace_harness_python_secret"`
  - unlinks, threads through `run_playwright_automation(...,
  harness_python_secret=...)` → docker exec
  `-e EXECUTOR_HARNESS_PYTHON_SECRET_VALUE=<hex>` env var.
  `load_harness_python_secret()` env-priority. E4 docker exec argv
  mask. W13-1 nonce gate intact. W13-12 immediate follow-up closed
  `2026-05-12` (see W13-12 row below + `REFACTOR_STATUS.md` §11.10
  status table row 216).
- ~~W13-12~~ (`[CLOSE-GATE codex-second-opinion-F2-fail-closed-harness-handshake]`)
  — **closed `2026-05-12`** (5/5 sub-commits: 8782630 docs lockdown ·
  d30a50f RED tests · c98f350 feat impl · a2c4aa2 arch gate · e7752a1
  close sweep). Close-pass for W13-1 H6. Internal monitor
  `ActivationReport.harness_handshake_required: bool` field stamped
  `True` by `setup_monitor`; `_attempt_has_harness_completion_trace`
  fail-closed branch fires on empty `expected_nonce` +
  `handshake_required=True` (eager-consume miss in residual failure
  modes — `FileNotFoundError`/`OSError`/bind-mount race). Test path
  default `False` preserves pre-W13-1 phase-only contract for unit
  fixtures. 3-fact AST gate (`test_setup_monitor_handshake_required.py`)
  pins stamp/read/thread invariants. Final bar: `make test-local`
  1537 → 1539 (+2); `tests/architecture/` 112 → 115 (+3). W13-1
  regression suite zero-diff. Close-out PR merge blocker reduces to
  W13-13 only.
- ~~W13-13 (`[CLOSE-GATE codex-second-opinion-F3-worker-start-cancel-race-CAS]`)~~
  — **closed `2026-05-13` (5/5 sub-commits + post-landing — `d2ba495`
  docs lockdown · `02c4374` RED behavioral · `33deb46` feat impl ·
  `60bb0cd` arch gate · `8912596` close evidence + 10-site drift sweep
  · `826f91c` self-stamp · `26a2025` post-landing behavioral pins
  (vanished row + finalize idempotency + failed/cancelled terminal))**. Close-pass for
  W13-3 H4. Path B worker-entry
  `select(AnalysisJob).where(...).with_for_update()` snapshot lock in
  `workflows/marketplace/analysis_service.py::run_analysis_job`
  replaces the unconditional `update_job(status="running")` write.
  Entry block branches: row missing → log + return; terminal → log +
  return; `cancelling` → `finalize_cancelled_analysis_job(db, ...)`
  via the lifecycle CRUD helper directly (the
  `job_service.finalize_cancelled_job` wrapper would deadlock against
  the held row lock — asymmetry documented inline and pinned by INV2
  of the architecture gate) + return; `queued` → atomic mutation +
  commit + proceed with the existing analysis flow. 3 new RED→GREEN
  behavioral cases in
  `tests/platform/storage/test_analysis_jobs_cancel_at_worker_entry.py`
  + 2-fact AST gate in
  `tests/architecture/test_run_analysis_job_entry_snapshot.py` (INV1
  first-DB-action is the lock; INV2 lifecycle helper called before
  `execute_analysis_request`). W13-4
  `tests/workflows/marketplace/test_run_analysis_job_finalize.py`
  `update_job.assert_called_once()` flipped to `assert_not_called()`
  to reflect Path B's contract that the worker entry no longer routes
  the queued → running transition through the wrapper. Post-landing
  pins (`26a2025`) add 4 behavioral cases that close defense-in-depth
  gaps the architecture gate cannot express at AST level: (a)
  vanished-row branch (`if job is None`); (b) finalize idempotency
  under race (`except JobNotCancellableError, KeyError` in cancelling
  branch); (c) + (d) parametrized terminal short-circuit for ``failed``
  + ``cancelled`` (main test only covers ``completed``). Final bar:
  `make test-local` 1542 → **1547** (+5 main) → **1551** (+4
  post-landing); `tests/architecture/` 115 → **117** (+2; unchanged
  post-landing); W13-3 + W13-4 + W13-1/W13-11/W13-12 regression suites
  zero-diff; 2 pre-existing env-only VSIX fixture failures in
  `test_analysis_fixture_baselines.py` unchanged (reproduce on HEAD~5
  = pre-W13-13). Production diff scoped to 1 file
  (`analysis_service.py` +163 -93). **Scope rebased `2026-05-12`** —
  original F4 README phase pointer drift sweep +
  `tests/architecture/test_readme_phase_pointer.py` regex pin landed
  early in the W13-11 push (sub-commits 8 + 12) to keep the README
  sweep paired with its banner-cascade fix-up.

Close-out PR #20 `week13 → main` is **MERGED** `2026-05-13` via
`772deb3` (close-gate cleared pre-merge; W13-11/W13-12 closed
`2026-05-12`, W13-13 closed `2026-05-13`). These items were pulled
in-window (not deferred to W14) because they directly fix bypass
surfaces in the originally W13-claimed H6 + H4 closures — keeping
them in-window preserves audit-trail integrity.

### §11.11 — Cross-Reference

External review findings are tracked by stable IDs in `POST_POC_BACKLOG.md`;
closed W8-W12/W13 items stay visible there only as audit trail summaries.

### §11.12 — Rejected Or Out-Of-Scope Items

Rejected review findings and WONT-FIX decisions live in the archive snapshots.
Current WONT-FIX audit item: M14a, workspace ownership by design.

### §11.13 — Paralel Lane Assignments

Use `documents/AGENT_CONTEXT.md` and the lane docs for routing. Active W13
work generally starts from `security-detection`, `executor-runtime`,
`platform-storage`, or `ui` depending on the stable ID.

### §11.14 — W13-End Overall Exit Criteria

Before W13 closes:

- H3, M1, and M9 are either closed or explicitly deferred with acceptance
  rationale. (H3 closed via W13-5; M9 closed via W13-6; M1 closed via W13-7.)
- W13 tracker has final close evidence and current test counts.
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, `documents/README.md`, and
  relevant lane docs point to the same active/closed state.
- Slim canonicals remain short; verbose evidence is archived first.
- **Close-gate (added `2026-05-11`, cleared `2026-05-13`): W13-11/12/13
  close-pass items all GREEN.** Codex Cloud second-opinion review
  identified 3 P1 bypass surfaces in the originally W13-claimed H6 +
  H4 closures (W13-11 HMAC python secret target-install race —
  **closed `2026-05-12`**; W13-12 fail-closed harness handshake —
  **closed `2026-05-12`**; W13-13 worker-start cancel-race CAS —
  **closed `2026-05-13`**; F4 README drift sweep + regex pin
  originally bundled in W13-13 scope landed early in W13-11 push
  `2026-05-12`). Close-out PR #20 `week13 → main` **MERGED**
  `2026-05-13` via `772deb3` — all fixes in-window preserve audit-trail
  integrity (history shows H6/H4 work as a coherent iteration family
  rather than a deferred follow-up).

## §12 — W14 Codex M-class Acceptance + Observability (2026-05-11 staging)

§12 opens once `week14` is cut from `main` (close-out PR #20 already merged
`2026-05-13` via `772deb3`). Until the branch cut, this section is **read-only
staging scope**; the active tracker
[`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md)
mirrors this scope and activates on explicit pull.

### §12.0 — Neden ayrı §12

§11 W8-W13 external-review integration penceresini sınırlar (W12 close
2026-05-10, W13 acceptance bar 2026-05-11). W14 yeni bir tema: Codex
M-class acceptance-bar pull-forward devamı + §11.10 GOAL umbrella'larının
ertelenen kısmı. §12 ayrı tutuluyor ki §11 audit trail'i (`2026-05-10`
Codex Cloud audit, H/M class çekim sırası) donmuş kalsın.

### §12.1 — Entry Gate (hedef)

W14 entry gate, W13 close-out PR'ı merge edildiğinde tetiklenir:

- `week13 → main` close-out PR merged (W12 PR #18 cut-off pattern).
- `make check-all` ✅ green at W13 close commit; hedef baseline:
  `make test-local` 1521 / `make test-security` 215 /
  `tests/architecture/` 105.
- W14 tracker'da "Entry Conditions Met" checklist tamamlanır.

### §12.2 — W14 alt-iterasyon dağılımı

W13'ün 10 sub-iter ritmi yerine, 6 sub-iter kohezyon kümelerine bölünür.
İlk pull anında `W14-N` stable ID atanır (W11/W12/W13 precedent).

| Iter | Tema | Stable ID(s) |
|---|---|---|
| W14-1 | BLOCKER araştırma — scenario-dropout kök neden | `[BUG scenario-dropout-upstream-root-cause]` |
| W14-2 | Codex M-class — input validation | `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` + `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` |
| W14-3 | Codex M-class — dış yüzey sertleştirme | `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` + `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` + `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` |
| W14-4 | Doğruluk + concurrency | `[FOLLOWUP analysis-jobs-race]` + `[FOLLOWUP evidence-event-kind-raw-context-invariant]` |
| W14-5 | §11.10 GOAL devamı — Logger consolidation + run-ID stamping + executor runtime fingerprint | `[GOAL w14-logger-consolidation]` + `[GOAL w14-run-id-stamping]` + `[FOLLOWUP codex-automation-5]` |
| W14-6 | §11.10 GOAL devamı — W8-W12 regression lock-in umbrella | `[FOLLOWUP arch-gate-executor-control-outbound]` + `[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]` + `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]` |

Sıralama gerekçesi: W14-1 önce — CRITICAL BUG W14 scope'unu genişletebilir
veya HIGH'a indirebilir. Sonra düşük-risk M-class (W14-2), W13-6 redaction
zincirinin devamı (W14-3), correctness/concurrency (W14-4), altyapı GOAL
pulls (W14-5, W14-6). W14-5, W14-6'dan önce gelir çünkü logger
consolidation regression lock-in gate'lerinde test enstrümantasyonuna girdi
olur.

### §12.3 — Non-goals (W14)

Aşağıdaki kalemler W14 scope'unda DEĞİL — W15+'a düşer. Stable ID'leri
[`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md) altında açık kalır:

- Codex M-class: M5 (W14-5 yan ürünü değilse), M10, M12, U1-U3, U6, U8,
  I2, I4
- Posture decision: `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]`
  — W14 öncesi ADR oturumu, plan değil karar
- Watching items: `planner-selection-readability-audit`,
  `attribution-links-build-evidence-bundle-density`,
  `execute-attempt-rebloat-watch`, `dispatch-execution-rebloat-watch` —
  LoC bütçesi aşılana kadar dokunma
- UI follow-up'ları: `ui-raw-context-discriminator-parity`,
  `vsix-integrity-in-activation-report` → W14-4 backend invariant landed
  olunca UI parity ayrı pull
- Refactor: `scenario-accountant-conservation-split` (W14-1 kök neden
  netleştikten sonra ayrı pull adayı; W14-1 PR'ına dahil edilmez)
- Automation/verification: `[FOLLOWUP codex-automation-6]` (UI failure
  taxonomy) + `[FOLLOWUP capability-verification-gap]` — W14 temasıyla
  örtüşmüyor; ikincisi `NEEDS-DESIGN`. `codex-automation-5` ise W14-5'e
  katlandı (run-ID stamping ile sibling)

### §12.4 — Exit Criteria (W14-End)

W14 kapanır şu koşullar sağlandığında:

- W14-1 BLOCKER kalemi ya kapanır ya da HIGH'a indirilip dokümante edilir.
- W14-2..W14-6 ya kapanır ya da slim canonical'da explicit deferral
  rasyoneli ile W15'e taşınır.
- W14 tracker final close evidence + current test counts tutar.
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, `documents/active-work/README.md`
  ve ilgili lane docs aynı active/closed state'i gösterir.
- Slim canonicals kısa kalır; verbose evidence önce arşivlenir.
- `week14 → main` close-out PR W12 PR #18 / W13 close-out cut-off pattern'ini
  izler.
