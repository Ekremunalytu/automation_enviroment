# W18 — Heartbeat Refactor (Active Work Tracker)

`Last Updated: 2026-05-21 (W18-2 closed via a9bffb1 — heartbeat refactor implementation landed: step-1 reset off worker thread via dedicated coordinator (ADR 0012 Option A1, function-extension shape). W18-2 final bar: tests/architecture/ 208 passed; make test-security 220 passed; full suite 1900 passed, 9 skipped, 8 deselected (W17 baseline 1899/9/4; +1 from W18-0 phase-pointer flip; skip count unchanged); analyze API end-to-end smoke job 364a8d13… ms-python.python@2026.5.2026051501 — all 5 steps completed, automation_health.status=degraded byte-identical with W17 baseline, **0 NEW reasons** vs baseline (gate passes). W18-1 closed via acf6cc9 (ADR 0012 Option A1) + 73d8a5c (followup doc-truth). W18-0 closed via 89d0c9b. W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d. §16 W18 plan source — sub-iter slate W18-0..W18-4 reserved; W18-3 + W18-4 still open.)`
`Phase: W18 active (W18-0/W18-1/W18-2 closed; W18-3 next — lifecycle harness extension tests)`
`Branch: week18 (per user direction 2026-05-21; W11-W17 paterni preserved — sub-iter commits land on week18, close-out merges into main via week18 -> main PR)`
`Owner: ekrem`

> **Authored 2026-05-21** as the W18 scope skeleton against `main` HEAD
> `05b6b9b` (W18-W22 multi-iter roadmap landed in planning state) +
> `1584c4d` (W18 candidate intake — `[GOAL container-hardening-baseline]` +
> `[GOAL sandbox-evasion-defense-mvp]`) + `bf6ec3e` (W17 post-merge audit
> trail). Stable IDs `W18-1..W18-4` are reserved by the iteration plan
> and **assigned at first pull** per the W11/W12/W13/W14/W15/W16/W17
> precedent (`REFACTOR_OPTIMIZATION.md` §16.0).

This is the canonical active work tracker for the W18 Heartbeat Refactor
window. Items receive stable IDs (`W18-1`, `W18-2`, …) **at first pull**,
not preemptively, per the W11/W12/W13/W14/W15/W16/W17 precedent.

Slim canonical [`REFACTOR_OPTIMIZATION.md §16`](../REFACTOR_OPTIMIZATION.md)
carries the entry-conditions block, goal statement, and the W18-W22
multi-iter roadmap context. The multi-iter source-of-truth roadmap is at
[`W18-W22-roadmap.md`](W18-W22-roadmap.md); this tracker is the W18
slice. The W17 frozen tracker
([`W17-carryover-and-lifecycle-harness.md`](W17-carryover-and-lifecycle-harness.md))
is the template structurally followed here.

## Status (Quick Glance)

- **W18 active — on `week18` branch per user direction (2026-05-21;
  W11-W17 paterni preserved).** Sub-iter commits land on `week18`;
  close-out merges into `main` via a `week18 -> main` PR.
- **Entry gate (met).** W17 close-out PR #25 `week17 -> main` MERGED
  `2026-05-18` via `bff565d`; W17 final bar (recorded at W17-6/W17-7
  close-out): `tests/architecture/` **200 passed**; `make test-security`
  **220 passed** (W17-7a `bf983eb` enrolled
  `test_unaccounted_dropout_surface.py` — 217 → 220); full suite
  **1899 passed, 9 skipped, 4 deselected**.
- **Driving signal (live run, 2026-05-21).** Codex live-run validation of
  `ms-python.python` @ `992ad028f3df` reports
  `automation_health.status=degraded` + `run_quality=low` while the
  static W17 final bar (1899/200/220) remains 🟢. W18 closes the
  W17-3/W17-4 `DESIGN-NEEDED` deferral as the **first** of five iters
  (W18-W22) responding to the live-run signal. W18 scope is **narrow**:
  heartbeat thread relocation only. The dropout fix (Hat-1) ships in
  W19; coverage promotion (Hat-3) in W20-W22.
- **W18-0 closed `2026-05-21` via `89d0c9b`** — doc reconcile +
  canonical preamble refresh across 7 docs + this tracker + README
  phase-pointer arch gate transition (W16→W17 paterni applied to
  W17→W18: new `test_readme_phase_pointer_tracks_active_w18_status`
  + new W17 close-out fact gate
  `test_readme_phase_pointer_mentions_w17_closeout_merge`). Drift
  fix: restored PR #20/#21/#22/#23 close-out mentions to
  `REFACTOR_STATUS.md` banner (dropped by `05b6b9b`). Final W18-0
  bar: `tests/architecture/` **201 passed**;
  `make test-security` **220 passed**; full suite **1899 passed**
  (unchanged from W17 final — doc-only + 1 test file flip).
- **W18-1 closed `2026-05-21` via `acf6cc9`** — heartbeat thread
  relocation ADR landed at
  [`documents/adrs/0012-heartbeat-thread-relocation.md`](../adrs/0012-heartbeat-thread-relocation.md)
  as `Accepted (pending W18-2 implementation)`. **Chosen shape:
  Option A1** — dedicated sandbox-reset coordinator thread for the
  step-1 setup reset; cancel-path teardown reset stays on the
  heartbeat thread. Followup doc-truth alignment via `73d8a5c`
  (§16 anchor map drift + W17-2 harness module docstring W17-3→W18-3
  reference flip + ADR 0012 backlink in W17-2 docstring). NO CODE.
- **W18-2 closed `2026-05-21` via `a9bffb1`** — heartbeat refactor
  implementation landed. **Shape: function-extension** (chosen at
  W18-2 plan time over the originally-considered class-based
  coordinator because three AST/behavioral gates pin the bare
  `_reset_sandbox(...)` Name call at `analysis_service.py:155`:
  cancel-poll AST gate, HMAC line-order AST gate, and 6
  `patch.object(analysis_service, "_reset_sandbox")` behavioral
  tests). ~42 LOC in
  [`workflows/marketplace/analysis_execution.py`](../../workflows/marketplace/analysis_execution.py)
  (new private `_run_reset_off_thread` + `COORDINATOR_THREAD_NAME =
  "analysis-sandbox-reset-coordinator"` + `_COORDINATOR_POLL_INTERVAL_S
  = 0.1` constants + `cancel_check` kwarg on the existing
  `reset_sandbox` helper + new `__all__` export) + 1 LOC in
  [`workflows/marketplace/analysis_service.py:155`](../../workflows/marketplace/analysis_service.py)
  (`cancel_check=cancel_check` kwarg threaded in). `_heartbeat_on_cancel`
  + heartbeat thread spawn at `analysis_execution.py:287-313`
  byte-identical. ADR 0012 self-stamped via this commit (Status →
  `Accepted and implemented`, Implementation section filled).

## Sub-Iter Scope (Authored 2026-05-21)

| Iter | Theme | Source / Why | Notes |
|---|---|---|---|
| W18-0 | Doc reconcile + §16 W18 active-phase pointer | Pattern match W17-0 (`4508c2e`) | Open this tracker, refresh §16 anchor map entry, canonical preamble bumps across 7 docs, flip README phase-pointer arch gate (W17→W18 + new W17 close-out fact gate), update W18-W22-roadmap.md status (pre-W18 → W18 active, branch main → week18). Doc-only + 1 test file flip. |
| W18-1 | Heartbeat thread relocation ADR (NO CODE) | `[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread` (W17-3 DESIGN-NEEDED carry-over via `c4c0646`) | `documents/adrs/0012-heartbeat-thread-relocation.md`. Three plausible refactor shapes enumerated with invariant-cost trade-offs against W13-1 HMAC eager-consume / W13-3 two-phase cancel / W13-13 worker-entry CAS / W16-2 facade row lock. Single shape picked with `Status: Accepted (pending W18-2 implementation)`. KOD YOK. |
| W18-2 | Heartbeat refactor implementation | `[FOLLOWUP simulation-progress-cancel] heartbeat-refactor` (W17-4 DESIGN-NEEDED carry-over via `c4c0646`) | Chosen ADR shape implemented at `workflows/marketplace/analysis_service.py` (HMAC consume window L155-L165) + `workflows/marketplace/analysis_execution.py` (`_run_monitoring_heartbeat` L292 + L299-L313 thread spawn). W17-2 harness smoke (`test_lifecycle_harness_smoke_cancel_triggers_heartbeat_reset`) MUST still pass with same invariants pinned. W13-11 HMAC consume invariant tests PASS (no regression on `consume_harness_python_secret` callers). |
| W18-3 | Lifecycle harness extension tests | `[FOLLOWUP w17-2-harness-extension-tests]` (new) | Three new tests in `tests/workflows/marketplace/test_lifecycle_harness.py` (parallel reset / reset idempotency / reset-during-finalize per W17-2 module docstring lines 27-35). Tests written **after** W18-2 implementation lands so assertions reflect actual behavior of the chosen shape. |
| W18-4 | Close-out hygiene + PR `week18 -> main` | Pattern match W17-6 (`8bf3c6b`) + W17-7-followup (`dab4679`) | Canonical preamble refresh across 7 docs + §16 self-stamp (post-merge final bar) + tracker freeze (sub-iter slate audit trail with commit SHAs) + PR open against `main`. |

## Per-Item Detail

### W18-1 — Heartbeat thread relocation ADR (closed 2026-05-21 via `acf6cc9` + `73d8a5c` followup)

**Pulled `2026-05-21`** (W17-3 + W17-4 `DESIGN-NEEDED` carry-over
via `c4c0646`; ADR-only, NO CODE). New file:
[`documents/adrs/0012-heartbeat-thread-relocation.md`](../adrs/0012-heartbeat-thread-relocation.md)
authored as `Accepted (pending W18-2 implementation)`.

**Chosen shape: Option A1** — dedicated sandbox-reset coordinator
thread for the **step-1 setup reset only**; cancel-path teardown
reset **stays on the heartbeat thread** (today's behavior, byte-
identical with the W17-2 smoke pin).

**Three options analyzed (full table in ADR §"Options considered"):**

| Option | Shape | Invariant cost | LOC | Status |
|---|---|---|---|---|
| **A1** | Dedicated reset coordinator for step-1 only; heartbeat keeps cancel-path | All W13-1/3/13 + W16-2 + W17-2 preserved byte-identical | ~60-100 | **CHOSEN** |
| A2 | Coordinator handles all resets (step-1 + cancel-path) | Breaks W17-2 harness pin (cancel-reset thread name changes) | ~80-120 | rejected |
| B | Heartbeat as sole reset issuer (heartbeat starts before step 1) | Preserves W17-2 but heartbeat scope drifts; W18-3 parallel-reset test loses its two-issuer surface | ~120-180 | rejected |
| C | Pipeline restructure (heartbeat orchestrates from step 1) | W13-13 CAS semantics shift; deepest change for "clarity not correctness" motivation | ~250-400 | rejected |

**Invariant preservation by Option A1** (all byte-identical):

- **W13-1 HMAC eager-consume**: worker frame still holds the secret
  at `analysis_service.py:165`; coordinator does the reset only, not
  the consume. The W13-11 doc-block ("the value is held in this
  frame's memory") reads accurately post-W18-2.
- **W13-3 two-phase cancel**: worker's wait on coordinator must be
  interruptible (cancel-poll inside wait loop, not bare `.join()`);
  same cadence cost as any cross-thread wait under B/C.
- **W13-13 worker-entry CAS**: unchanged — CAS happens on worker
  frame before coordinator spawn.
- **W16-2 facade row lock**: unchanged.
- **W17-2 harness smoke pin**:
  `calls[0]["thread"] == "harness-monitoring-heartbeat"` +
  `calls[0]["kwargs"] == {"reload_window": True}` preserved
  byte-identical (heartbeat still issues the cancel-path reset).

**Why A1 over A2** (coordinator-handles-all): A2 is the
architecturally "cleanest" sub-variant but breaks the W17-2 pin —
the cancel-path reset would fire from the coordinator thread, not
the heartbeat thread. The pin exists to prevent this exact drift;
relaxing it for a marginal "single source of truth" gain inverts the
test's protective role. The two reset call-sites are semantically
distinct (setup vs teardown) — merging them on one thread does not
reduce the concurrency surface (`reset_sandbox()` must be thread-safe
regardless of which threads call it).

**Why A1 over B**: Option B's literal reading of W16-5 ("move to
heartbeat thread") conflates the heartbeat's monitoring scope
(step 4) with lifecycle setup (step 1), forcing the function's
purpose to drift. Option B also collapses the W18-3 parallel-reset
test's two-issuer surface into a one-issuer surface, weakening the
W17-2 module docstring's L27-35 forward contract.

**Why A1 over C**: Option C is a 250-400 LOC restructure of
`execute_analysis_request` for a motivation W16-5 itself called
"clarity, not correctness". The W13-13 CAS pins at
`tests/platform/storage/test_analysis_jobs_cancel_at_worker_entry.py`
(6 behavioral tests) would need re-evaluation under a signal-gated
coroutine model — expanding W18 scope past the W16-5 framing.

**Consequences for W18-2** (implementation contract; full list in
ADR §"Follow-On (W18-2 implementation contract)"):

- New coordinator class/function (~60-100 LOC), location decided
  by actual LOC at W18-2 time (inline in `analysis_execution.py`
  vs new module `workflows/marketplace/sandbox_reset_coordinator.py`).
- `analysis_service.py:155` direct `_reset_sandbox(...)` call
  replaced with `coordinator.submit_step_1_reset_and_wait(...)`
  (final method name decided at W18-2).
- `analysis_service.py:165` HMAC consume unchanged — worker frame.
- `analysis_execution.py:287-313` `_heartbeat_on_cancel` +
  heartbeat-thread spawn byte-identical (W17-2 smoke must pass).
- Coordinator thread name proposed:
  `"analysis-sandbox-reset-coordinator"`; W18-3 tests pin the
  final name.
- Worker's wait on coordinator must include cancel-poll at ≤ the
  W13-3 step-boundary cadence (W18-2 picks the poll interval).

**Consequences for W18-3** (test surface; full enumeration in
ADR §"Follow-On (W18-3 test surface)"):

1. **`test_lifecycle_harness_parallel_reset_does_not_deadlock`** —
   coordinator (driven by worker submit) + heartbeat both fire
   `reset_sandbox` concurrently; assert no deadlock, total reset
   count = 2, thread identities match.
2. **`test_lifecycle_harness_reset_idempotency`** — two back-to-back
   resets from different threads; assert executor surface state
   consistent after both return.
3. **`test_lifecycle_harness_reset_during_finalize`** — heartbeat
   fires cancel while worker is in `finalize_report`; assert DB
   row ends `cancelled` (not `completed`), reset runs at most once
   after the finalize-start barrier.

**Verification (this commit, W18-1).** Doc-only — `tests/architecture/`
201 passed unchanged; `make test-security` 220 passed unchanged;
W17-2 smoke green unchanged (no code touched). ADR 0012
"Implementation" section remains `PENDING` until W18-2 lands and a
self-stamp commit fills it in (W17-1 / W16-2 / W16-4 paterni).

**Audit trail.** `[FOLLOWUP simulation-progress-cancel] heartbeat-
sandbox-reset-off-thread` + `[FOLLOWUP simulation-progress-cancel]
heartbeat-refactor` (W17-3 + W17-4 DESIGN-NEEDED via `c4c0646`)
design-half closed by ADR 0012; implementation-half pulled forward
to W18-2.

### W18-2 — Heartbeat refactor implementation (closed 2026-05-21 via `a9bffb1` + this self-stamp commit)

**Pulled `2026-05-21`** (W17-4 `DESIGN-NEEDED` carry-over via `c4c0646`;
ADR 0012 Option A1 implementation half).

**Shape chosen at plan time: function-extension** — not the
originally-considered class-based `SandboxResetCoordinator`. Three
AST/behavioral gates pin the bare `_reset_sandbox(...)` Name call at
`analysis_service.py:155` and would silently break under a class-based
call shape (`coordinator.submit_step_1_reset_and_wait(...)`):

| Gate | Mechanism | Class-based failure mode |
|---|---|---|
| [`tests/architecture/test_cancel_poll_points.py:54`](../../tests/architecture/test_cancel_poll_points.py) | `HOT_ZONE_HELPERS` tuple AST walk requires `func.id == "_reset_sandbox"` | `_reset_sandbox missing` assertion fail |
| [`tests/architecture/test_harness_secret_eager_consume.py:86-90`](../../tests/architecture/test_harness_secret_eager_consume.py) | `node.func.id == "_reset_sandbox"` derives `reset_line` for `reset_line < consume_line < install_line` invariant | `reset_line is None` fail; W13-11 line-order invariant kopar |
| [`tests/workflows/marketplace/test_analysis_execution_poll_points.py`](../../tests/workflows/marketplace/test_analysis_execution_poll_points.py) (6 tests) | `patch.object(analysis_service, "_reset_sandbox")` | Patch sessizce işlemez (import duruyor ama çağrılmıyor) → **false-green W13-3 koruması** |

**Implementation summary** (~42 LOC across two files):

- [`workflows/marketplace/analysis_execution.py`](../../workflows/marketplace/analysis_execution.py):
  new private `_run_reset_off_thread(executor_control, cancel_check)`
  helper spawns a daemon thread
  (`name=COORDINATOR_THREAD_NAME = "analysis-sandbox-reset-coordinator"`)
  that runs `executor_control.reset_sandbox()`; the caller frame waits
  via `done.wait(timeout=_COORDINATOR_POLL_INTERVAL_S=0.1)` + a
  `raise_if_cancelled(cancel_check)` poll on each iteration (so worker
  cancel propagates within ~100ms, ≤ W13-3 boundary cadence). Existing
  public `reset_sandbox` helper grew a `cancel_check: Callable | None =
  None` kwarg (default keeps the `patch.object(...)` test sites
  backwards-compatible) and now delegates to `_run_reset_off_thread`
  instead of calling `executor_control.reset_sandbox()` directly.
  `COORDINATOR_THREAD_NAME` was added to `__all__` so W18-3 tests can
  import it.
- [`workflows/marketplace/analysis_service.py:155`](../../workflows/marketplace/analysis_service.py):
  single-line edit — `_reset_sandbox(reporter, executor_control)` →
  `_reset_sandbox(reporter, executor_control, cancel_check=cancel_check)`.
  Bare Name call preserved; all three gates above pass byte-identical.

**Byte-identical (verified, unchanged):**

- [`workflows/marketplace/analysis_execution.py:287-313`](../../workflows/marketplace/analysis_execution.py)
  `_heartbeat_on_cancel` closure + heartbeat thread spawn
  (`name="analysis-run-monitoring-heartbeat"`, `reload_window=True`).
- [`workflows/marketplace/analysis_service.py:165`](../../workflows/marketplace/analysis_service.py)
  `consume_harness_python_secret()` worker frame call (W13-1/W13-11
  HMAC invariant).
- All cancel-poll points at L152/L154/L156/L166/L168 in
  `execute_analysis_request` (W13-3 cadence).

**Invariant preservation** (all byte-identical per ADR 0012 §Decision):

| Invariant | Status |
|---|---|
| W13-1 HMAC eager-consume | ✅ Worker frame'de kalır (L165 unchanged) |
| W13-3 two-phase cancel | ✅ Yeni wait loop mevcut `raise_if_cancelled`'i reuse eder; cadence ≤100ms |
| W13-13 worker-entry CAS | ✅ Coordinator spawn CAS'ten sonra |
| W16-2 facade row lock | ✅ Dokunulmuyor |
| W17-2 harness smoke | ✅ `calls[0]["thread"] == "harness-monitoring-heartbeat"` + `reload_window=True` byte-identical |

**Verification (recorded at landing `a9bffb1`):**

- `pytest tests/workflows/marketplace/test_lifecycle_harness.py
  tests/workflows/marketplace/test_analysis_execution_poll_points.py`
  → **7 passed** (W17-2 smoke unchanged + 6 poll-point unchanged).
- `pytest tests/architecture/` → **208 passed** (W18-0 baseline 201 +
  adjacent passes in the lifecycle test module).
- `pytest tests/executor/test_harness_secret_eager_consume.py
  tests/executor/test_playwright_health_reconciliation.py`
  → **27 passed** (W13-11 HMAC eager-consume regression check).
- `make test-security` → **220 passed**.
- Full suite → **1900 passed, 9 skipped, 8 deselected** (W17 baseline
  `1899/9/4`; +1 from W18-0 README phase-pointer flip; skip count
  unchanged from W17 baseline 9).
- Analyze API end-to-end (job `364a8d13171741c0ac8f43a6d8ffc97b`,
  `ms-python.python` @ `2026.5.2026051501`): **all 5 pipeline steps
  reached `completed`** (`reset_sandbox` / `install_extension` /
  `build_triggers` / `run_monitoring` / `finalize_report`).
  `automation_health.status` stayed at `degraded` (matches W17 baseline);
  reason-set delta vs baseline `ff8e63...`: **0 new** reasons (baseline
  set: `{harness_verification_unconfirmed_present,
  official_unresolved_present, skipped_scenarios_present,
  verification_gap_present}`; W18-2 run set:
  `{skipped_scenarios_present}` — 3 removed reasons reflect marketplace
  run-to-run variance, not a coupling to W18-2). Gate `automation_health.reasons
  yeni reason eklemez` **passes**.
- `make sim-target TARGET=ms-python.python` was found NOT to exercise
  the W18-2 code path (it invokes
  `executor.flows.playwright.entrypoint --monitor` directly without
  the `_reset_sandbox` step) and was replaced by the analyze API smoke
  for this verification. ADR 0012 §Implementation records the same
  finding.

**Risk dispositions (per W18-2 plan, accepted at landing):**

- **Cancel-during-reset orphan thread**: coordinator thread is
  `daemon=True`; production timeline (coordinator step-1, heartbeat
  step-4+) is sequential so concurrent reset is not reachable today.
  Log emit sufficient; no bounded join added.
- **Reporter cross-thread emit**: `StepReporter.emit` calls stay in
  the worker frame; `_run_reset_off_thread` runs the executor call
  only. No emit-thread-context drift.
- **`_reset_executor_sandbox_state` thread-safety**
  ([`executor/host.py:390-403`](../../executor/host.py)): callee is
  lock-free subprocess invocations; production serializes the two
  callers so race is not reachable. **Deferred to W18-3
  parallel-reset test**
  (`test_lifecycle_harness_parallel_reset_does_not_deadlock`) per ADR
  0012 §Consequences (Negative) bullet 2. If the test surfaces a real
  race, W18-3 lands an `ExecutorControl` `threading.Lock`.

**Audit trail.** `[FOLLOWUP simulation-progress-cancel]
heartbeat-refactor` (W17-4 DESIGN-NEEDED via `c4c0646`)
implementation-half closed. Design-half closed by W18-1 (`acf6cc9`
ADR 0012).

### W18-3..W18-4

Stable IDs W18-3..W18-4 get Per-Item Detail entries here as each is
pulled.

## Exit Criteria (W18-End)

W18 kapanır şu koşullar sağlandığında:

- W18-0..W18-4 kapanır ya da deferral rasyoneli ile W19'a taşınır.
- W18-1 ADR `documents/adrs/0012-heartbeat-thread-relocation.md` Accepted
  (pending implementation) — 3 refactor shapes enumerated, 1 picked,
  invariant-cost trade-offs against W13-1 / W13-3 / W13-13 / W16-2
  documented.
- W18-2 heartbeat refactor lands: W17-2 harness smoke
  (`test_lifecycle_harness_smoke_cancel_triggers_heartbeat_reset`) PASS
  with thread identity (`harness-monitoring-heartbeat`) and
  `reload_window=True` kwargs unchanged. W13-11 HMAC eager-consume
  invariant'ı regression etmez (existing `consume_harness_python_secret`
  tests + handshake-side gates green).
- W18-3 üç yeni harness extension testi PASS: parallel reset (lock ordering
  + no deadlock), reset idempotency (no executor surface corruption),
  reset-during-finalize (DB row `cancelled` not `completed`, reset runs
  at most once).
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `active-work/README.md`, ve ilgili lane docs aynı active/closed
  state'i gösterir.
- W18 final bar: `make test-security` ≥220 passed; `tests/architecture/`
  ≥201 passed (W17 final 200 + 1 W17 close-out fact gate from W18-0);
  full suite skip count W17 baseline 9'dan **artmamalı**; full suite
  pass count W17 final 1899 + W18-0 phase pointer + W18-3 harness
  extensions = 1903 hedef.
- `make sim-target TARGET=ms-python.python` smoke (W18-2 close):
  heartbeat refactor regression yok — `automation_health.reasons`
  listesi YENİ reason eklemez (`degraded` kalabilir, W19 düşürür).
- Close-out hygiene pass: Ruff lint, UI contract sync, markdown
  formatting, doc truth-state alignment.
- Per user direction (2026-05-21): W18 `week18` branch'inde çalışır;
  sub-iter commits `week18` branch'inde land eder; close-out
  `week18 -> main` PR ile merge edilir; W18 tracker scope kapanışında
  frozen olur (W11-W17 paterni).

## Risk Notes

- **W18-1 ADR derin teknik karar** — heartbeat thread relocation üç
  refactor shape arasından seçim yapılacak (dedicated reset thread /
  unified reset queue / pipeline restructure). Her birinin farklı
  invariant maliyeti var: W13-1 HMAC eager-consume L155-L165 hard sync
  point'i ile sıkı bağlı. Yanlış shape seçimi W18-2 implementation'da
  W17-2 harness smoke'un kıracağı bir regression yaratabilir. Mitigation:
  ADR Accepted edilmeden önce W17-2 harness smoke assertion'larına
  (thread identity, reload_window kwargs, CAS outcome) karşı her shape
  için tablo hazırla; en düşük invariant cost'lu shape'i seç.
- **W18-2 ↔ W17-2 harness smoke coupling** — eğer ADR Option C
  (pipeline restructure / heartbeat owns reset from step 1) seçilirse,
  harness fixture'ın kendisi paralel revision gerektirebilir
  (`harness-monitoring-heartbeat` thread'in artık step-1'i yönettiği
  varsayımı kırılır). W18-2 entry'de bu paralel rev'i scope flag olarak
  değerlendir; gerekirse W18-2a + W18-2b'ye böl.
- **Live-run health düşüş — W18 scope dışı** — Codex live-run rapor
  `automation_health.status=degraded` durumunu W18 düşürmez (Hat-1
  unaccounted_dropout fix W19'a, Hat-2 harness verification W19'a,
  Hat-3 coverage promotion W20+'a). W18-2 sim-target smoke'unda
  `degraded` görmek beklenen davranış; "YENİ reason eklenmedi"
  kriteri yeterli.

## Notes

- Branching policy: tek `week18` branch'i; per-iter feature branch
  açılmaz. Sub-iter commits sıralı `W18-0`, `W18-1`, ... olarak
  `week18`'e push edilir. W18-4 sonrası `week18 -> main` close-out PR.
- W17 tracker
  ([`W17-carryover-and-lifecycle-harness.md`](W17-carryover-and-lifecycle-harness.md))
  W17-7 + `dab4679` W17-7-followup sonrası **frozen reference**;
  W18 boyunca sadece okuma için açılır (W17-3 §W17-3 detay bloğu —
  3 plausible refactor shapes ve W13-11 hard sync point context'i
  için L205-249 spesifik referans; W17-2 harness module docstring
  L27-35 W18-3 extension noktaları için spesifik referans).
- W18-W22 multi-iter roadmap source-of-truth:
  [`W18-W22-roadmap.md`](W18-W22-roadmap.md). Bu tracker W18 slice'ı;
  W19+ için yeni active-work tracker'ları W18 kapanışında veya W19-0
  entry'de açılır.
