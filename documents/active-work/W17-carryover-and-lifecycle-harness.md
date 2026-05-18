# W17 — Carry-Over Closeout + Lifecycle Harness Yatırımı + Hygiene Sweep (Active Work Tracker)

`Last Updated: 2026-05-18 (W17 active — phase work complete; close-out via week17 -> main PR pending (no push per user direction 2026-05-18). W17-0..W17-6 sub-iter slate complete: W17-0 doc-reconcile (4508c2e); W17-1 attribution-count-parity (8c26d02 + 0a8f59e self-stamp); W17-2 lifecycle harness scaffold (ff98235 + 44f96c5 self-stamp); W17-3 + W17-4 scope-reduced doc-only (c4c0646 DESIGN-NEEDED, deferred to W18); W17-5 hygiene single-item (394d40d + 0cbe1d0 self-stamp; postgres-version-fact-drift closed in seed_project_2; other 4 cleanup candidates deferred to W18+); W17-6 close-out hygiene this commit (canonical preamble refresh across 7 docs + §15 self-stamp + W17 tracker freeze). Final W17 bar: tests/architecture/ 200 passed (W16 final 199, +1); make test-security 217 passed; full suite 1899 passed, 9 skipped, 4 deselected (+6 from W16 final 1893))`
`Phase: W17 active — phase work complete; W17-0..W17-6 all closed or scope-resolved; close-out via week17 -> main PR pending (no push per user direction)`
`Branch: week17 (per user direction 2026-05-18; W11-W16 paterni preserved — sub-iter commits land on week17, close-out merges into main via week17 -> main PR)`
`Owner: ekrem`

> **Authored 2026-05-18** as the W17 scope skeleton against `main` HEAD
> `1b6d43f` (W16 close-out merge commit) + `92eda39` (post-merge backlog
> top-up `[GOAL marketplace-user-scan-and-notify]`). Stable IDs
> `W17-1..W17-6` are reserved by the iteration plan and **assigned at
> first pull** per the W11/W12/W13/W14/W15/W16 precedent
> (`REFACTOR_OPTIMIZATION.md` §15.0).

This is the canonical active work tracker for the W17 Carry-Over Closeout
+ Lifecycle Harness + Hygiene Sweep window. Items receive stable IDs
(`W17-1`, `W17-2`, …) **at first pull**, not preemptively, per the
W11/W12/W13/W14/W15/W16 precedent.

Slim canonical [`REFACTOR_OPTIMIZATION.md §15`](../REFACTOR_OPTIMIZATION.md)
carries the entry-conditions block, goal statement, and current candidate
list. The W16 frozen tracker
([`W16-regression-and-audit-closeout.md`](W16-regression-and-audit-closeout.md))
is the template structurally followed here.

## Status (Quick Glance)

- **W17 active — on `week17` branch per user direction (2026-05-18;
  W11-W16 paterni preserved).** Sub-iter commits land on `week17`;
  close-out merges into `main` via a `week17 -> main` PR.
- **Entry gate (met).** W16 close-out PR #23 `week16 -> main` MERGED
  `2026-05-18` via `1b6d43f`; W16 final post-merge bar (recorded at
  W16-7 close-out + post-PR top-up `78f080e`):
  `tests/architecture/` **199 passed** (+27 from W15 final 172);
  `make test-security` **220 passed** (+5 from W13 final 215, three
  added post-PR as `unaccounted_dropout` surface pins matching the
  live-scan shape); full suite **1893 passed, 9 skipped**.
- **W17-0 closed `2026-05-18` via `4508c2e`** — canonical preamble
  refresh across 7 docs + new W17 tracker + new §15 W17 plan section
  in `REFACTOR_OPTIMIZATION.md` + new W17 Pull-Forward table in
  `POST_POC_BACKLOG.md` + README phase-pointer arch gate transition
  (W14→W15 paterni applied to W16→W17: new
  `test_readme_phase_pointer_mentions_w16_closeout_merge` + bumped
  `test_readme_phase_pointer_tracks_active_w17_status`).
- **W17-1 closed `2026-05-18` via `8c26d02`** — producer-side fix at
  `build_evidence_bundle` activation emit-site
  (`executor/flows/playwright/attribution/links.py`): captures
  `target_extension_id` once at the function entry and stamps
  `is_target_extension_event=bool(target_extension_id and
  activation.extension_id == target_extension_id)` on each
  `EvidenceEvent(kind="activation", ...)`. Mirrors
  `count_target_activations`'s empty-id guard so the two predicates
  are byte-identical at all inputs. 4 new invariant tests in
  `tests/executor/test_playwright_attribution_links.py` including the
  W17-1 contract pin
  (`test_build_evidence_bundle_target_activation_parity_invariant`)
  that drives a mixed activated list (target + non-target + target)
  and asserts evidence-side and attribution_summary counts equal.
- **W17-2 closed `2026-05-18` via `ff98235`** — lifecycle harness
  scaffold landed at
  `tests/workflows/marketplace/test_lifecycle_harness.py`.
  `LifecycleHarness` class composes the session-scoped `test_engine`
  with a per-test UUID-keyed `AnalysisJob` row and a mocked
  `ExecutorControl` whose `reset_sandbox` side_effect records every
  call along with `threading.current_thread().name`. Methods cover
  the W17-3-relevant surface: `persist_queued_job`,
  `claim_worker_entry` (W13-13/W16-2 worker-entry CAS),
  `signal_cancel`, `start_heartbeat`/`stop_heartbeat` (daemon thread
  named `harness-monitoring-heartbeat` running
  `_run_monitoring_heartbeat` with controllable `cancel_check` and
  `on_cancel`), `wait_for_reset_calls`, `reset_calls`,
  `read_job_status`, `cleanup`. `lifecycle_harness` pytest fixture
  binds the rig to `test_engine` and runs cleanup on teardown. Smoke
  test pins (a) cancel-driven `reset_sandbox` fires from the
  heartbeat thread (not the main test thread), (b) call kwargs
  match production wiring (`reload_window=True`), and (c) the
  worker-entry CAS transitioned `queued → running`
  (`WorkerEntryOutcome.CLAIMED`). Intentional scope cuts: harness
  does NOT drive `run_analysis_job` end-to-end and does NOT use
  `fresh_alembic_engine` (W16-6 fixture) — per-test isolation comes
  from UUID-keyed rows + cleanup delete, which is sufficient for
  concurrency assertions and lighter than fresh-DB-per-test.

## Sub-Iter Scope (Authored 2026-05-18)

| Iter | Theme | Source / Why | Notes |
|---|---|---|---|
| W17-0 | Doc reconcile + W17 tracker open | Pattern match W16-0 | Open this tracker, §15 header, canonical preamble bumps, freeze W16 tracker (already self-frozen at W16-7 + `78f080e`). Doc-only. |
| W17-1 | `attribution-count-parity` closeout | Carry-over from W16-3 (W14 production scan) | Producer-side divergence: `target_activation_count = 1` while evidence-kind count = 0. Single subsystem (report-finalize / attribution_summary). Emit-site fix pattern W16-1 (`01f910a` + `a4a050e`); contract-seam pattern W16-3 (`fa430f2` + `e3d4a0c`). |
| W17-2 | Lifecycle harness scaffold | Enabler for W17-3 + W17-4 | `start → reset → cancel → finalize` harness against real Postgres DB (reuse `fresh_alembic_engine` fixture from W16-6 `d40bb01`) + Playwright mock surface (reuse browser-monitor side mock primitives). Likely lives under `tests/integration/lifecycle_harness/`. W17's heaviest sub-iter. |
| W17-3 | `heartbeat-sandbox-reset-off-thread` | Carry-over from W16-5 deferral (W17+ pending lifecycle harness) | Move sandbox-reset call from analysis worker thread to monitoring heartbeat thread. Concurrency-sensitive: lock ordering + reset idempotency + partial-state recovery. W13-1 HMAC + W13-12 fail-closed gates byte-identical (W16-4 pattern `304b99f` + `384d276`). Verified under W17-2 harness. |
| W17-4 | `heartbeat-refactor` | Carry-over from W16-5 deferral (bundled with W17-3) | Clarity refactor of heartbeat shape — behavior byte-identical, hygiene gain not correctness. Builds on W17-3; harness regression catches behavioral drift. |
| W17-5 | Hygiene cleanup batch | Low-risk pull-next from `POST_POC_BACKLOG.md` | 3-5 `[CLEANUP]` items. Aday set (final pick at W17-5 entry): `env-example-extrace-vars`, `postgres-version-fact-drift`, `adr-0007-runbook-wording-drift`, `pre-commit-python-version-alignment`, `report-builder-naming` (alt: `monitor-runtime-naming-overlap`). Pattern W16-6 hygiene splits (`d40bb01`) — separate small commits. |
| W17-6 | Close-out hygiene + canonical preamble refresh | Pattern match W16-7 | Slim canonical 7 doc preamble truth-state refresh + §15 self-stamp post-merge W17 final bar + backlog item statuses (closed items → DONE/CLOSED audit trail). Pattern W16-7 (`8bf3c6b`) + post-merge top-up paterni (`78f080e`). |

## Per-Item Detail

### W17-1 — `attribution-count-parity` closeout

**Pulled `2026-05-18` via `8c26d02`** (W16-3 carry-over; producer-side
emit-site fix). The W14 production scan `2026-05-14` observed
`attribution_summary.target_activation_count = 1` while the
evidence-side counter
(`kind=activation,is_target_extension_event=True`) read 0 for the
same persisted run, even though `target_extension_host` log stream
had the matching `Activated ms-python.python via
workspaceContains:requirements.txt` entry. Both compute paths saw
the same activation but applied different (and inconsistent) target
flags.

**Root cause.** `build_evidence_bundle` in
`executor/flows/playwright/attribution/links.py` walked
`report.activated[]` and emitted one
`EvidenceEvent(kind="activation", ...)` per entry but never stamped
`is_target_extension_event`. Other kinds (network / file / process /
output_channel_appendline) forward the flag from the upstream typed
event (links.py:173/218/264/302); the activation branch was the only
producer-side hole.

**Fix.** Capture `target_extension_id = report.target_extension_id`
at the top of `build_evidence_bundle` and, in the activation loop,
compute `is_target_activation = bool(target_extension_id and
activation.extension_id == target_extension_id)` and pass it as
`is_target_extension_event=is_target_activation` to the
`EvidenceEvent` constructor. The empty-id guard mirrors
`count_target_activations`'s own `if not target_extension_id:
return 0` so the two predicates are byte-identical at the empty-id
boundary as well.

**Tests (Phase 3 invariant).** 4 new tests in
`tests/executor/test_playwright_attribution_links.py`:

- `test_build_evidence_bundle_activation_event_flags_target_extension`
  — target activation → `is_target_extension_event=True`.
- `test_build_evidence_bundle_activation_event_does_not_flag_non_target`
  — non-target activation in a targeted report →
  `is_target_extension_event=False`.
- `test_build_evidence_bundle_activation_event_unflagged_when_no_target_set`
  — empty `target_extension_id` keeps flag False.
- `test_build_evidence_bundle_target_activation_parity_invariant`
  — the W17-1 contract pin: with a mixed activated list (target +
  non-target + target), the count of
  `kind=activation,is_target_extension_event=True` events equals
  `count_target_activations(activated, target_id)`. Both counters
  derive from the same predicate.

**Out-of-scope (intentional).** The downstream `attribution_summary`
producer (`executor/flows/playwright/annotation.py`
`build_attribution_summary`) and `automation_health` producer
(`executor/flows/playwright/health/summary.py`
`build_automation_health`) both call `count_target_activations` and
were already byte-identical at the extension_id predicate level.
W17-1 fixes the evidence-side hole so the *third* counter (evidence
stream) joins the parity. No other emit-sites change.

**Verification.** Full non-smoke suite **1898 passed, 9 skipped, 4
deselected** (W16 final 1893 passed; +4 W17-1 tests + 1 W17-0
W16-close-out-fact gate = +5). `tests/architecture/` 200 passed;
`tests/executor/` + `tests/security/` green; no regression in
W16-3's `tests/security/test_report_finalize_field_sync.py`
strict-forbid contract round-trip pins.

**Audit trail.** `[FOLLOWUP attribution-count-parity]` in
`POST_POC_BACKLOG.md` marked **closed at W17-1** with closure
details. W17-2 (lifecycle harness scaffold) is next.

### W17-2 — Lifecycle harness scaffold

**Pulled `2026-05-18` via `ff98235`** (W17-3 enabler; the W16-5
deferral's lifecycle-harness prerequisite).
`tests/workflows/marketplace/test_lifecycle_harness.py` introduces
`LifecycleHarness` + `lifecycle_harness` fixture + a single
plumbing smoke test that pins the production-wiring shape of the
cancel-driven `reset_sandbox` call: thread identity
(`harness-monitoring-heartbeat`), kwargs (`reload_window=True`),
and the worker-entry CAS state transition
(`queued → running` under `WorkerEntryOutcome.CLAIMED`).

**Extension points for W17-3** (documented in module docstring):

- Parallel reset: both worker thread + heartbeat issue
  `reset_sandbox` concurrently — verify lock ordering does not
  deadlock.
- Reset idempotency: two back-to-back resets from different
  threads do not corrupt the executor surface.
- Reset-during-finalize: heartbeat fires cancel while worker is in
  `finalize_report`; DB row must end in `cancelled` (not
  `completed`) and executor reset must not run twice.

**Composition.** Session-scoped `test_engine` (rolled-back +
re-bootstrapped per session in `tests/conftest.py`) + per-test
UUID-keyed `AnalysisJob` row + `MagicMock(spec=...)`-style
`ExecutorControl` with a side_effect that records every
`reset_sandbox` call with calling-thread name. The session
factory is bound to the engine directly (`sessionmaker(bind=engine,
future=True, autoflush=False, expire_on_commit=False)`) so the
harness can open and close short transactions explicitly without
fighting the `db_session` connection-scoped rollback fixture.

**Verification.** `tests/workflows/` + `tests/architecture/` +
`tests/platform/storage/test_analysis_jobs_lifecycle.py` 554
passed together; full non-smoke suite 1899 passed, 9 skipped, 4
deselected (W17-1 final 1898 passed; +1 new harness smoke).

### W17-3 — `heartbeat-sandbox-reset-off-thread` (scope-reduced 2026-05-18, doc-only)

**Scope reduced.** No code commit ships under W17-3. The W17-2
lifecycle harness prerequisite is now MET, but the W17-3 design
intent surfaced as **DESIGN-NEEDED** mid-pull:

The W16-5 deferral note framed W17-3 as "move sandbox-reset call
from worker thread to monitoring heartbeat thread". On close
inspection of
`workflows/marketplace/analysis_service.execute_analysis_request`
(L155 + L157-164 doc-block), the worker-thread `_reset_sandbox`
call is a **hard sync point** before
`consume_harness_python_secret`: the reset restarts VS Code,
which writes the per-launch HMAC python secret to
`/results/_extrace_harness_python_secret`; the secret MUST be
consumed under the worker frame's memory before the analyzed VSIX
is admitted (W13-11 / Codex F1 close-pass for W13-1 H6). The
monitoring heartbeat thread itself only starts at step 4
(`_run_monitoring`, after install + triggers), so it cannot host
the step-1 reset without a pipeline-ordering refactor.

Several plausible refactor shapes exist:

1. Dedicated reset thread started before step 1 (worker blocks on
   future); pipeline ordering preserved but adds a third
   coordinator thread.
2. Merge heartbeat's cancel-path reset with step-1 reset via a
   queue; heartbeat starts earlier and is the sole reset issuer.
3. Restructure pipeline so heartbeat starts at step 1 and gates
   subsequent steps via signals; deepest change.

Each option has a different invariant cost (W13-1 HMAC marker
wiring vs. W13-3 two-phase cancel vs. W13-13 worker-entry CAS vs.
W16-2 facade row lock). Picking one inside W17 without an
explicit design pass would gamble on a refactor shape whose
constraints the deferral note did not specify.

**Audit trail.** W17-3 (and W17-4, bundled below) deferred to W18
with W16-5 paterni — doc-only commit, audit trail updated in
`POST_POC_BACKLOG.md`. W18 opens with an ADR / §16 plan entry
naming the chosen refactor shape and the invariant preservation
strategy. The W17-2 harness module docstring already enumerates
the three W17-3 extension points (parallel reset / idempotency /
reset-during-finalize) so W18 inherits the rig with zero
bootstrap cost.

### W17-4 — `heartbeat-refactor` (scope-reduced 2026-05-18, doc-only, bundled with W17-3)

**Scope reduced.** Bundled with W17-3 per the original W16-5
bundling. Refactoring the heartbeat shape in isolation before
deciding whether the thread will also host the step-1 reset
would land throw-away work. W18 pulls both together once the
W17-3 refactor shape is named.

### W17-5 — Hygiene cleanup batch (single-item closeout)

**Pulled `2026-05-18` via `394d40d`** (narrow scope —
`[CLEANUP postgres-version-fact-drift]` only).
`executor/flows/playwright/workspace/seed_project_2.py:76` carried
a hardcoded `image: postgres:15` string in its embedded
`docker-compose.yml` synthetic-fixture content while the rest of
the codebase (`CONTRIBUTING.md:24`, `README.md:245`,
`docker-compose.yml`'s db + postgres_test services) all reference
`postgres:16-alpine` (digest-pinned at the production compose level
since W15-7 `54e7a93`). The synthetic compose is written into the
sandbox workspace at runtime as a fake "production project" the
analyzed extension operates on; no test pins the fixture's
postgres tag, so the bump is observation-only and rule helpers
that scan the workspace for compose patterns see a postgres image
string matching the host stack.

**Other four candidate cleanups deferred to W18+ opportunistic
pull-as-found** (`env-example-extrace-vars`,
`adr-0007-runbook-wording-drift`,
`pre-commit-python-version-alignment`, `report-builder-naming` /
alt: `monitor-runtime-naming-overlap`). Each lacks an inline scope
description in `POST_POC_BACKLOG.md` and needs per-item owner
discovery before a safe edit can land — the W17-5 scope cap keeps
the close-out window narrow rather than gambling on multiple
under-specified fixes.

**Verification.** Full non-smoke suite 1899 passed, 9 skipped, 4
deselected (W17-4 final 1899 unchanged — fixture-content edit, no
new tests).

### Remaining (W17-6)

W17-6 close-out hygiene: canonical preamble refresh across 7 docs
+ §15 self-stamp post-merge W17 final bar + backlog item statuses
(closed items → DONE/CLOSED audit trail).

## Exit Criteria (W17-End)

W17 kapanır şu koşullar sağlandığında:

- W17-1..W17-6 kapanır ya da deferral rasyoneli ile W18'ye taşınır.
- W17-1 producer-side parity invariant runtime'da yakalanır
  (`tests/architecture/` veya report-invariants test ailesinde +1 gate).
- W17-2 harness happy-path smoke + cancel-mid-flight +
  reset-during-finalize edge case'leri yeşil; harness'ın kendi smoke
  testi (lifecycle açılıp kapanıyor mu) `make test-local` altında.
- W17-3 davranış paritesi: sandbox-reset thread relocation sonrası
  W13-1 HMAC + W13-12 fail-closed davranışı + W13-13 CAS pattern
  regress etmez; harness altında lock ordering + idempotency yeşil.
- W17-4 byte-identical refactor: heartbeat clarity refactor sonrası
  W17-2 harness'ı tüm edge case'leri yeşil bırakır.
- W17-5 hygiene cleanup: seçilen 3-5 `[CLEANUP]` kalem
  `POST_POC_BACKLOG.md`'de DONE/CLOSED işaretli; ruff clean; arch
  gate'lere yeni regression eklemez.
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `active-work/README.md`, ve ilgili lane docs aynı active/closed
  state'i gösterir.
- W17 final bar: `make test-security` ≥220 passed; `tests/architecture/`
  ≥199 passed + W17-1 invariant + W17-2 harness smoke; full-suite skip
  count W16 baseline 9'dan **artmamalı**.
- Close-out hygiene pass: Ruff lint, UI contract sync, markdown
  formatting, doc truth-state alignment, (varsa) yeni regression gate'ler.
- Per user direction (2026-05-18): W17 `week17` branch'inde çalışır;
  sub-iter commits `week17` branch'inde land eder; close-out
  `week17 -> main` PR ile merge edilir; W17 tracker scope kapanışında
  frozen olur (W11-W16 paterni).

## Risk Notes

- **W17-2 harness en büyük belirsizlik** — Playwright mock surface'inin
  ne kadar iş istediği keşfedilmeden bilinmiyor. Eğer harness W17 ortasında
  balon olursa, W17-3/4 W18'e iter ve W17 attribution-parity + hygiene
  ile kapatılır. Scope reduction kararı W17-2 ortasında verilir
  (W16-5 paterni: doc-only commit + deferral rasyonelinin
  `POST_POC_BACKLOG.md`'ye audit trail'i).
- **W17-1 küçük görünüyor** ama W16-3 split'inde "evidence vs stream
  divergence" derin bir contract sorun çıkarsa büyüyebilir; W17-2
  başlamadan W17-1 kapanmalı (sequencing constraint).

## Notes

- Branching policy: tek `week17` branch'i; per-iter feature branch
  açılmaz. Sub-iter commits sıralı `W17-0`, `W17-1`, ... olarak
  `week17`'e push edilir. W17-6 sonrası `week17 -> main` close-out PR.
- W16 tracker
  ([`W16-regression-and-audit-closeout.md`](W16-regression-and-audit-closeout.md))
  W16-7 + `78f080e` post-PR top-up sonrası **frozen reference**;
  W17 boyunca sadece okuma için açılır (W17-3 file path context'i
  için L526-543 spesifik referans).
