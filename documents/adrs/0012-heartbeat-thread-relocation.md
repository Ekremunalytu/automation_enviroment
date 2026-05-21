# ADR 0012: Heartbeat Thread Relocation (Sandbox Reset Off Worker Thread)

- Status: Accepted and implemented (`2026-05-21`)
- Date: 2026-05-21
- Accepted + Implemented: W18-2 landed on the `week18` branch at
  [`a9bffb1`](https://github.com/Ekremunalytu/automation_enviroment/commit/a9bffb1)
  (2026-05-21). The ADR + implementation are split per the W17-3
  `DESIGN-NEEDED` deferral rationale: the design decision landed first
  as W18-1 (`acf6cc9`) so the W18-2 code change was reviewed against a
  stated contract rather than a moving target.
- Related: ADR 0008 (Container Packaging — the sandbox surface being
  reset); the W13-1 HMAC anchor + W13-3 two-phase cancel + W13-13
  worker-entry CAS + W16-2 facade row lock are code-anchored (no
  dedicated ADR) but are load-bearing for this decision.

## Context

W16-5 (`e21a05c`) deferred
`[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread`
to W17+ pending a lifecycle harness. W17-2 (`ff98235`) landed the
harness at
[`tests/workflows/marketplace/test_lifecycle_harness.py`](../../tests/workflows/marketplace/test_lifecycle_harness.py)
with `LifecycleHarness` + `lifecycle_harness` fixture +
cancel-via-heartbeat smoke. W17-3 and W17-4 (`c4c0646`) were then
scope-reduced to doc-only with a `DESIGN-NEEDED` note: the W16-5
deferral framed the work as "move sandbox-reset call from worker
thread to monitoring heartbeat thread", but on close inspection the
worker-thread step-1 reset is a **hard sync point** before the W13-11
HMAC secret consume, and the heartbeat thread starts only at step 4
— several plausible refactor shapes exist with different invariant
costs.

This ADR names the chosen refactor shape, the invariant preservation
strategy, and the surface the W18-2 implementation must respect.

### The hard sync point

Today the analysis pipeline runs as a linear sequence on the worker
thread (`workflows/marketplace/analysis_service.py:124-205`,
`execute_analysis_request`):

| Step | Call | Frame |
|---|---|---|
| 0 | `_raise_if_cancelled(cancel_check)` | worker |
| 0 | `ensure_vsix_exists(request)` | worker |
| **1** | **`_reset_sandbox(reporter, executor_control)`** (L155) | **worker** |
| 2 | `_raise_if_cancelled(cancel_check)` (L156) | worker |
| 2 | **`harness_python_secret = executor_control.consume_harness_python_secret()`** (L165) | **worker** |
| 3 | `_install_extension(...)` (L167) | worker |
| 3 | `_build_triggers(...)` (L169) | worker |
| **4** | **`_run_monitoring(...)`** (L178) — spawns heartbeat thread | **worker spawns heartbeat** |

The W13-11 doc-block at
[`analysis_service.py:157-164`](../../workflows/marketplace/analysis_service.py)
explains the constraint: `_reset_sandbox` restarts VS Code, which
causes `launch_vscode.sh` to write a fresh per-launch HMAC python
secret to `/results/_extrace_harness_python_secret` (mode `0600`,
owned `executor:executor`). The Python frame **must** read + unlink
that file **before** the analyzed VSIX is admitted (step 3), because
the same-UID target extension would otherwise be able to read the
file during the install → `setup_monitor` window. The value is held
in the worker frame's memory and threaded into `_run_monitoring`
(step 4) via the `harness_python_secret` kwarg.

The monitoring heartbeat thread itself is spawned only inside
`_run_monitoring` at
[`analysis_execution.py:299-313`](../../workflows/marketplace/analysis_execution.py)
(`heartbeat_thread = threading.Thread(target=_run_monitoring_heartbeat, ..., name="analysis-run-monitoring-heartbeat", daemon=True).start()`).
Its cancel-path closure `_heartbeat_on_cancel`
(`analysis_execution.py:287-297`) fires
`executor_control.reset_sandbox(reload_window=True)` when the
cancel-poll loop trips — so the **cancel-path reset already runs off
the worker thread today**, on the heartbeat thread.

The W16-5 framing "move sandbox-reset off worker thread" therefore
applies only to the **step-1 setup reset**. The **cancel-path
teardown reset** is already off-worker.

### W17-2 harness invariants (must not relax)

The smoke test
[`test_lifecycle_harness_smoke_cancel_triggers_heartbeat_reset`](../../tests/workflows/marketplace/test_lifecycle_harness.py)
at `test_lifecycle_harness.py:268-307` pins:

- Exactly one cancel-driven `reset_sandbox` call (`len(calls) == 1`).
- The call originates from the heartbeat thread:
  `calls[0]["thread"] == "harness-monitoring-heartbeat"`. The
  harness's `HEARTBEAT_THREAD_NAME` mirrors production's
  `"analysis-run-monitoring-heartbeat"` name; renaming the production
  thread breaks this pin.
- Production kwargs: `calls[0]["kwargs"] == {"reload_window": True}`.
- Worker-entry CAS outcome: `WorkerEntryOutcome.CLAIMED` (queued →
  running transition is atomic, lock-held by the CAS).

Any W18 refactor that changes the **thread that fires the cancel-path
reset** breaks this pin. Any refactor that changes
`reload_window=True` breaks this pin. Any refactor that moves the CAS
elsewhere breaks W13-13 + the W16-2 facade boundary.

### Decision drivers

The chosen shape must preserve, in priority order:

1. **W13-1 HMAC marker integrity** — secret consume + unlink runs in
   the same host process, in a frame whose lifetime brackets the
   install → `setup_monitor` window. The file must not exist on disk
   after install begins.
2. **W13-3 two-phase cancel contract** — cancel-check at every step
   boundary; a cancel must propagate within milliseconds of the
   cancel API call, not block on the duration of `_reset_sandbox` /
   `_install_extension` / `_build_triggers`. Any new cross-thread
   wait the worker performs must be interruptible (cancel-poll
   inside the wait loop, not a `.join()` with no timeout).
3. **W13-13 worker-entry CAS** — `queued → running` happens atomically
   under the row lock on the worker thread frame before any
   sub-thread spawns. Sub-threads must not race the CAS.
4. **W16-2 facade row lock** — `claim_queued_analysis_job_at_worker_entry`
   remains the sole CRUD primitive that owns the row-lock-aware
   lifecycle CRUD path; sub-threads must not issue parallel
   `SELECT … FOR UPDATE`.
5. **W17-2 harness invariants** — thread identity, kwargs, and CAS
   outcome above. The smoke test must remain byte-identical green
   after W18-2 lands.
6. **W16-5 motivation** — step-1 reset moves off the worker thread.

## Options considered

### Option A — Dedicated reset coordinator thread

A new thread (call it the **sandbox-reset coordinator**) handles the
step-1 setup reset. The worker thread submits a reset request to the
coordinator and blocks on a `Future`-style synchronization primitive
(or a `threading.Event` + return-value channel). The cancel-path
reset stays on the heartbeat thread (today's behavior).

Two sub-variants:

- **A1 — Coordinator handles step-1 reset only; heartbeat continues
  to issue cancel-path reset directly.** Three threads total in
  steady-state during run_monitoring: worker, coordinator (lived for
  step 1, terminates after; or pooled), heartbeat.
- **A2 — Coordinator handles ALL `reset_sandbox` calls; heartbeat
  delegates its cancel-path reset to the coordinator.** Two
  long-lived threads (worker, coordinator) plus the short-lived
  heartbeat. The cancel-path reset now fires from the coordinator
  thread, not the heartbeat thread.

**Invariant cost (A1):**

| Invariant | Status |
|---|---|
| W13-1 HMAC | ✅ Preserved exactly — coordinator does reset only; the worker thread still calls `executor_control.consume_harness_python_secret()` in its own frame at the existing call site (`analysis_service.py:165`). |
| W13-3 cancel | ⚠ Worker's wait on the coordinator's completion must be interruptible — a `.join()` with `timeout=` + cancel-check poll, not a bare `.join()`. Equal cost to other options (any cross-thread wait needs this). |
| W13-13 CAS | ✅ Unchanged — CAS happens in worker before coordinator spawns. |
| W16-2 facade | ✅ Unchanged. |
| W17-2 harness pin | ✅ **Preserved byte-identical** — cancel-path reset still fires from the heartbeat thread. The smoke test's `calls[0]["thread"] == "harness-monitoring-heartbeat"` assertion is untouched. |
| W16-5 motivation | ✅ Step-1 reset is off the worker thread. |

**Invariant cost (A2):**

Same as A1 **except** W17-2 harness pin: cancel-path reset now fires
from the coordinator thread (`"sandbox-reset-coordinator"`, or
whatever the chosen name). The harness smoke would fail
(`"harness-monitoring-heartbeat" != "sandbox-reset-coordinator"`).
A2 would force a parallel revision of the harness fixture and the
smoke assertion. Breaks the "byte-identical pin preservation"
property of A1.

**LOC estimate (A1):** ~60-100 LOC new code (new module or inline
helper in `analysis_execution.py`), one call-site edit in
`analysis_service.py` (replace `_reset_sandbox(...)` with
`coordinator.submit_step_1_reset(...)`), one new fixture method
in `LifecycleHarness` for W18-3 parallel-reset tests.

### Option B — Unified reset queue (heartbeat as sole reset issuer)

The heartbeat thread starts **before** step 1 (its lifecycle is
extended from "step 4 only" to "step 1 onward"). The worker thread
submits a step-1 reset request via a queue/event to the heartbeat;
the heartbeat processes the request, signals back; worker proceeds
with HMAC consume + install + … . Cancel-path reset is unchanged
(still on heartbeat). The heartbeat is the **sole issuer** of all
`reset_sandbox` calls.

**Invariant cost:**

| Invariant | Status |
|---|---|
| W13-1 HMAC | ✅ Preserved — heartbeat does reset, worker reads + unlinks secret after heartbeat signals "done". |
| W13-3 cancel | ⚠ Same wait-interruptibility constraint as A1. |
| W13-13 CAS | ✅ Unchanged. |
| W16-2 facade | ✅ Unchanged. |
| W17-2 harness pin | ✅ Preserved — cancel-path reset still on heartbeat thread (same thread name, expanded scope). |
| W16-5 motivation | ✅ Step-1 reset is off the worker thread (it's on the heartbeat thread). |
| **Scope drift** | ⚠ The heartbeat thread's name `"analysis-run-monitoring-heartbeat"` becomes misleading — it no longer "monitors the run" exclusively; it's a lifecycle coordinator that also monitors. Renaming the thread function (`_run_monitoring_heartbeat` → e.g., `_run_lifecycle_heartbeat`) would break the W17-2 pin string-match. Keeping the name preserves the pin but introduces a documentation tax. |
| **W18-3 surface** | ⚠ The W17-2 module docstring (L27-35) enumerates W18-3 as three tests: parallel reset / idempotency / reset-during-finalize. Under Option B, only one thread issues resets, so "parallel reset (worker + heartbeat concurrently)" loses its literal meaning and would need to be rewritten as "heartbeat handles two concurrent reset events" — a different surface than the W17-2 docstring described. |

**LOC estimate:** ~120-180 LOC. Heartbeat thread's lifecycle
extends from "spawned at step 4" to "spawned before step 1 and
joined after finalize", which restructures the `run_monitoring`
function signature and the surrounding `execute_analysis_request`
control flow.

### Option C — Pipeline restructure (heartbeat owns reset lifecycle from step 1)

Heartbeat starts at step 1 (or before), acts as the orchestrator,
and gates subsequent steps (install, build_triggers, run_monitoring)
via `threading.Event` signals. The worker thread becomes a "step
executor" that waits for heartbeat's "ready" signals at each step
boundary.

**Invariant cost:**

| Invariant | Status |
|---|---|
| W13-1 HMAC | ⚠ Secret consume must be threaded carefully — either heartbeat consumes (changes "this frame's memory" doc-block) or worker consumes (after heartbeat signal). Same end-state security as today but the wiring shifts. |
| W13-3 cancel | ⚠ Worker's wait on each step boundary must be interruptible. |
| W13-13 CAS | ⚠ CAS semantics shift — "claimed → running" was a single step from worker's perspective; under Option C the worker doesn't drive the steps imperatively, so "claimed" is just the entry gate to a signal-driven coroutine. The CAS still happens on the worker frame, but downstream logic changes. |
| W16-2 facade | ⚠ Facade boundary is unchanged but the **callers** of facade methods change — the worker now calls `claim_queued_analysis_job_at_worker_entry` then immediately enters a signal-wait loop instead of an imperative step sequence. |
| W17-2 harness pin | ✅ Preserved (heartbeat still issues cancel-path reset). |
| W16-5 motivation | ✅ Step-1 reset is off the worker thread. |
| **Architectural shift** | ⚠ The linear imperative pipeline at `analysis_service.execute_analysis_request` becomes a signal-driven coroutine. Reviewers familiar with the existing W11/W12/W13/W14/W15/W16 pipeline shape must rebuild their mental model. |

**LOC estimate:** ~250-400 LOC. `execute_analysis_request` is
restructured; new signal/wait wiring across the step boundaries;
heartbeat function scope expands substantially; W17-2 harness
fixture likely needs a parallel revision to model the signal-gated
lifecycle.

## Decision

**Option A1 — Dedicated sandbox-reset coordinator thread for the
step-1 setup reset; cancel-path teardown reset stays on the heartbeat
thread (today's behavior).**

Rationale:

1. **Lowest invariant cost.** A1 preserves W13-1 + W13-3 + W13-13 +
   W16-2 + W17-2 byte-identical. Options B and C each introduce at
   least one ⚠ on the invariant table; A1 has zero.

2. **W17-2 harness pin preserved without parallel revision.** The
   smoke test's `calls[0]["thread"] == "harness-monitoring-heartbeat"`
   assertion stays green because the heartbeat thread continues to
   issue the cancel-path reset. The W18-2 implementation can be
   verified against the existing harness without rewriting the
   fixture.

3. **W18-3 surface matches the W17-2 docstring's enumeration.** The
   W17-2 module docstring at
   [`test_lifecycle_harness.py:27-35`](../../tests/workflows/marketplace/test_lifecycle_harness.py)
   describes three concurrency extensions: **parallel reset (both
   worker thread + heartbeat issue `reset_sandbox` concurrently)**,
   reset idempotency, and reset-during-finalize. Option A1 produces
   exactly this surface — the coordinator (driven by the worker via
   submit/wait) and the heartbeat are two distinct reset issuers, so
   "parallel reset (both threads concurrently)" is the natural test
   shape. Options B and C collapse to a single issuer and would
   require rewriting the W18-3 test descriptions.

4. **Semantic separation honored.** Step-1 reset is **setup**
   (prepare a fresh sandbox for an analysis). Cancel-path reset is
   **teardown** (wipe the sandbox to abort an analysis). These
   semantics are different even though they share the same
   `executor_control.reset_sandbox()` call. Option A1 keeps the
   semantically distinct call-sites on threads whose names match
   their roles (coordinator for setup; heartbeat for teardown).
   Option B forces both through the heartbeat, conflating the
   semantics on one thread for a marginal "single source of truth"
   gain that is not justified by the threat model or the test
   surface.

5. **Lowest code-change footprint.** ~60-100 LOC versus ~120-180 LOC
   (B) or ~250-400 LOC (C). For a refactor explicitly framed as
   "clarity, not correctness" (W16-5 description called the
   `heartbeat-refactor` half a "clarity gain rather than a
   correctness fix"), the cheapest shape that satisfies the
   motivation wins.

### Sub-decisions

- **Coordinator scope.** The coordinator handles step-1 reset
  **only**. It does **not** consume the HMAC secret — that call
  stays in the worker frame at `analysis_service.py:165` so the
  W13-11 doc-block reads accurately. (Worker frame holds the secret;
  worker frame admits the VSIX; same frame for both halves of the
  W13-11 invariant.)
- **Coordinator lifetime.** The coordinator is a per-analysis-run
  thread (`threading.Thread` started before step 1, joined after
  step 1 completes). It is **not** a pool, **not** a long-lived
  daemon. Lifetime ≈ duration of `_reset_sandbox`, typically
  seconds. This keeps the thread topology simple and matches the
  imperative pipeline shape of `execute_analysis_request`.
- **Coordinator thread name.** Proposed:
  `"analysis-sandbox-reset-coordinator"` (or
  `"sandbox-reset-coordinator"` — final name decided at W18-2
  implementation). The harness W18-3 parallel-reset test pins
  whatever name lands.
- **Synchronization primitive.** A `threading.Event` plus a result
  container (single-element list or `dataclass` holder for the
  return value or the raised exception) is sufficient. A
  `concurrent.futures.Future` is permissible but over-engineered
  for a single-shot coordination. W18-2 picks.
- **Cancel-poll cadence inside worker's wait.** The worker's wait on
  the coordinator must include a cancel-check at a cadence ≤ the
  existing W13-3 boundary cadence (every step). Concretely:
  `event.wait(timeout=0.1)` in a loop with `_raise_if_cancelled` at
  each iteration. W18-2 picks the timeout.
- **Cancel-path reset is unchanged.** `_heartbeat_on_cancel` at
  `analysis_execution.py:287-297` keeps its current shape; the
  cancel-path `executor_control.reset_sandbox(reload_window=True)`
  call continues to fire on the heartbeat thread. W17-2 smoke
  passes unchanged.

### Why not Option A2

Option A2 (coordinator handles all resets) is the architecturally
"cleanest" sub-variant — a single thread sees every reset, so race
conditions across resets are eliminated by construction. We reject
A2 because:

1. It breaks the W17-2 harness pin (cancel-path reset thread name
   changes), requiring a parallel revision of the smoke test
   assertion. The pin exists to prevent this exact drift; relaxing
   it for a marginal architectural gain inverts the test's
   protective role.
2. The two reset call-sites are **semantically distinct** (setup vs
   teardown). Merging them on one thread does not actually reduce
   the concurrency surface — `executor_control.reset_sandbox()`
   still must be thread-safe against concurrent calls regardless of
   which threads issue them.
3. The "single source of truth" argument for resets is conjectural;
   the actual safety property is that `reset_sandbox()` is
   internally idempotent and lock-protected — a property of the
   *callee*, not the *caller threads*.

### Why not Option B

Option B (heartbeat as sole reset issuer) is the most literal reading
of W16-5's "move sandbox-reset call to heartbeat thread". We reject
it because:

1. It conflates the heartbeat's monitoring scope (step 4) with
   lifecycle setup (step 1), forcing the thread to start earlier
   and live longer. The function `_run_monitoring_heartbeat` is
   named after its scope; expanding the scope drifts the name.
2. The W17-2 module docstring's three W18-3 tests (parallel reset /
   idempotency / reset-during-finalize) describe a **two-issuer**
   reset surface. Option B collapses this to a one-issuer surface,
   which would force a rewrite of the W18-3 test descriptions and
   weaken the W17-2 enumeration's value as a forward contract.
3. Option B's "fewer threads" argument is real but small — A1's
   coordinator lives ~seconds (only during step 1) so the
   long-lived thread count under A1 in steady state is the same as
   under B (worker + heartbeat) after step 1 completes.

### Why not Option C

Option C (pipeline restructure) is the deepest change. We reject it
because:

1. The motivation (W16-5 "clarity, not correctness") does not
   justify a 250-400 LOC restructure of `execute_analysis_request`.
2. The W13-13 CAS semantics are pinned by 6 behavioral tests at
   `tests/platform/storage/test_analysis_jobs_cancel_at_worker_entry.py`
   (W16-2 audit trail). A signal-gated coroutine shifts the
   semantics of "claimed → running" enough that those pins need
   re-evaluation, which expands W18's scope past the W16-5 framing.
3. The linear imperative pipeline at `execute_analysis_request` is
   the codebase's dominant shape. Diverging one workflow into a
   signal-driven model adds a reviewer-side mental cost
   disproportionate to the gain.

## Consequences

### Positive

- The W16-5 motivation ("step-1 reset off the worker thread") is
  satisfied with the minimum viable refactor.
- W17-2 harness pin preserved byte-identical — W18-2 can land
  without touching the fixture or the smoke assertion.
- W18-3 test surface matches the W17-2 module docstring's
  enumeration (two-issuer reset surface), preserving the W17-2
  forward contract.
- Worker frame continues to hold the HMAC secret per W13-11;
  doc-block remains accurate.
- Semantic separation: coordinator owns setup-reset, heartbeat owns
  teardown-reset — thread names reflect roles.
- Lowest LOC delta among options (60-100 LOC), keeping the W18
  iteration scope tight.

### Negative

- Adds a third thread topology to the worker run path (worker,
  coordinator, heartbeat) — momentarily during step 1, then the
  coordinator joins. Reviewers must track an extra thread spawn +
  join in the worker frame.
- `executor_control.reset_sandbox()` is now reachable from **two**
  distinct call-sites in different threads (coordinator for step 1,
  heartbeat for cancel-path). The callee must be thread-safe; a
  W18-3 idempotency test pins this. (Today's code is single-caller
  per run, so any latent non-idempotency would only surface under
  the new shape — W18-3 catches it.)
- The worker's wait on the coordinator adds one new cancel-poll
  loop site. W13-3 cancel-poll cadence must be respected; W18-2
  must pick the poll interval and document the cancel-latency
  upper bound at the wait site.
- The "off worker" guarantee is only for the duration of
  `executor_control.reset_sandbox()` itself — the worker still
  blocks on the coordinator's completion. The motivation (W16-5
  clarity) holds; the responsiveness motivation (worker can respond
  to cancel during reset) requires the interruptible-wait property
  described above.

### Follow-On (W18-2 implementation contract)

W18-2 lands the chosen shape. The implementation must:

1. **Add a new coordinator class/function.** Proposed location:
   either inline in `workflows/marketplace/analysis_execution.py`
   (alongside `_run_monitoring_heartbeat`) or a new module
   `workflows/marketplace/sandbox_reset_coordinator.py` if the
   surface exceeds ~50 LOC. W18-2 picks based on actual LOC.
2. **Edit `analysis_service.execute_analysis_request`** to replace
   the direct `_reset_sandbox(reporter, executor_control)` call at
   L155 with `coordinator.submit_step_1_reset_and_wait(...)` (final
   name decided at W18-2). The HMAC consume at L165 stays in the
   worker frame, unchanged.
3. **Preserve `_heartbeat_on_cancel` at L287-297** byte-identical
   so the W17-2 smoke passes unchanged.
4. **Keep `_run_monitoring_heartbeat`'s thread name**
   `"analysis-run-monitoring-heartbeat"` (production) /
   `"harness-monitoring-heartbeat"` (test) unchanged.
5. **Wait-interruptibility.** Worker's wait on the coordinator must
   include cancel-poll at ≤ the W13-3 step-boundary cadence. W18-2
   documents the chosen poll interval and the cancel-latency upper
   bound at the call site.
6. **Coordinator-thread name.** W18-2 picks a name (proposed:
   `"analysis-sandbox-reset-coordinator"`); the W18-3
   parallel-reset test pins whatever name lands.
7. **Re-verify the full W17-2 smoke + the W13-11 HMAC handshake
   tests + the W13-3 cancel-poll boundary tests** before the W18-2
   commit ships.

### Follow-On (W18-3 test surface)

W18-3 lands three new tests in
`tests/workflows/marketplace/test_lifecycle_harness.py`:

1. **`test_lifecycle_harness_parallel_reset_does_not_deadlock`** —
   coordinator (driven by worker submit) and heartbeat both fire
   `reset_sandbox` concurrently; assert lock ordering does not
   deadlock within timeout; assert total reset call count = 2 (not
   collapsed); assert thread identities match
   (`"analysis-sandbox-reset-coordinator"` and
   `"harness-monitoring-heartbeat"` in the harness's mirror names).
2. **`test_lifecycle_harness_reset_idempotency`** — two back-to-back
   resets from different threads (or the same thread, twice); assert
   the executor surface state is consistent after both return; pins
   the W18-2-required idempotency property of `reset_sandbox`.
3. **`test_lifecycle_harness_reset_during_finalize`** — heartbeat
   fires cancel while worker is in `finalize_report` (post step 4);
   assert DB worker-entry row ends in `cancelled` (not `completed`);
   assert `reset_sandbox` runs at most once after the finalize-start
   barrier.

### Why ADR + implementation are split

The W17-3 deferral pattern (W17 close at `c4c0646`, doc-only) named
"DESIGN-NEEDED" explicitly. The W18-1 ADR satisfies the design
half; W18-2 lands the code half. Splitting allows the W18-2 review
to evaluate the implementation against a stated design contract
rather than against a moving target — and allows the chosen shape to
be rejected/revised in this ADR before code lands.

## Implementation

Landed on the `week18` branch at
[`a9bffb1`](https://github.com/Ekremunalytu/automation_enviroment/commit/a9bffb1)
(2026-05-21) as the function-extension shape — chosen at W18-2 plan
time over the originally-considered class-based coordinator because
three architecture/behavioral gates pin the bare `_reset_sandbox(...)`
Name call at `analysis_service.py:155`:

- `tests/architecture/test_cancel_poll_points.py` `HOT_ZONE_HELPERS`
  AST walk requires `func.id == "_reset_sandbox"`.
- `tests/architecture/test_harness_secret_eager_consume.py` enforces
  `reset_line < consume_line < install_line` via the same Name
  predicate.
- `tests/workflows/marketplace/test_analysis_execution_poll_points.py`
  has six `patch.object(analysis_service, "_reset_sandbox")` tests
  whose patches would silently bypass (false-green) if the call name
  changed at the call site.

The chosen shape lands ~42 LOC in
[`workflows/marketplace/analysis_execution.py`](../../workflows/marketplace/analysis_execution.py):

- A new private helper `_run_reset_off_thread(executor_control,
  cancel_check)` spawns a daemon thread
  (`name=COORDINATOR_THREAD_NAME = "analysis-sandbox-reset-coordinator"`)
  that runs `executor_control.reset_sandbox()`; the caller frame waits
  via `done.wait(timeout=_COORDINATOR_POLL_INTERVAL_S=0.1)` + a
  `raise_if_cancelled(cancel_check)` poll, so worker cancel propagates
  within ~100ms (≤ the W13-3 boundary cadence).
- The public `reset_sandbox` helper gained a `cancel_check` kwarg
  (default `None` for backwards compatibility with the
  `patch.object(...)` test sites) and now delegates its single
  `executor_control.reset_sandbox()` call to `_run_reset_off_thread`.
- One call-site edit at
  [`workflows/marketplace/analysis_service.py:155`](../../workflows/marketplace/analysis_service.py)
  threads `cancel_check=cancel_check` into the existing
  `_reset_sandbox(...)` call — the bare Name call is preserved, so all
  three gates above pass byte-identical.

`_heartbeat_on_cancel` at
[`analysis_execution.py:287-297`](../../workflows/marketplace/analysis_execution.py)
and the heartbeat thread spawn at L300-313 are **untouched**; the
cancel-path teardown reset still fires from the heartbeat thread with
`reload_window=True`, so the W17-2 smoke pin
(`calls[0]["thread"] == "harness-monitoring-heartbeat"` +
`calls[0]["kwargs"] == {"reload_window": True}`) is preserved byte-
identical.

Verification at landing time:

- `pytest tests/workflows/marketplace/test_lifecycle_harness.py
  tests/workflows/marketplace/test_analysis_execution_poll_points.py`
  — 7 passed (W17-2 smoke unchanged + 6 poll-point unchanged).
- `pytest tests/architecture/` — 208 passed (W18-0 baseline 201 +
  adjacent passes in the lifecycle test module).
- `pytest tests/executor/test_harness_secret_eager_consume.py
  tests/executor/test_playwright_health_reconciliation.py` — 27 passed
  (W13-11 HMAC eager-consume regression check).
- `make test-security` — 220 passed.
- Full suite — 1900 passed, 9 skipped (W17 baseline 1899 + 1 from the
  W18-0 README phase-pointer flip; skip count unchanged from W17
  baseline 9).
- Analyze API end-to-end (job
  `364a8d13171741c0ac8f43a6d8ffc97b`, `ms-python.python` @
  `2026.5.2026051501`): all 5 pipeline steps reached `completed`
  (`reset_sandbox` / `install_extension` / `build_triggers` /
  `run_monitoring` / `finalize_report`). `automation_health.status`
  stayed at `degraded` (matches W17 baseline `ff8e63...`); the
  reason-set delta against baseline was **0 new** reasons (baseline:
  `{harness_verification_unconfirmed_present,
  official_unresolved_present, skipped_scenarios_present,
  verification_gap_present}`; this run:
  `{skipped_scenarios_present}` — the 3 removed reasons reflect
  marketplace / monitoring run-to-run variance, not a coupling to
  W18-2). `make sim-target` was found NOT to exercise the W18-2 code
  path (it invokes `executor.flows.playwright.entrypoint --monitor`
  directly without the `_reset_sandbox` step) and was replaced by the
  analyze API smoke for this verification.

The W18-3 follow-on tests (parallel reset / idempotency /
reset-during-finalize) are the next sub-iter; they will pin
`COORDINATOR_THREAD_NAME` and verify the
`_reset_executor_sandbox_state` thread-safety property the §Consequences
(Negative) bullet 2 raised.

Cross-links:

- W18 active tracker:
  [`documents/active-work/W18-heartbeat-refactor.md`](../active-work/W18-heartbeat-refactor.md).
- W18-W22 multi-iter roadmap source-of-truth:
  [`documents/active-work/W18-W22-roadmap.md`](../active-work/W18-W22-roadmap.md).
- §16 plan entry:
  [`documents/REFACTOR_OPTIMIZATION.md`](../REFACTOR_OPTIMIZATION.md).
- W17-2 harness module:
  [`tests/workflows/marketplace/test_lifecycle_harness.py`](../../tests/workflows/marketplace/test_lifecycle_harness.py).
- W13-11 HMAC eager-consume doc-block:
  [`workflows/marketplace/analysis_service.py:157-164`](../../workflows/marketplace/analysis_service.py).
- Heartbeat cancel-path closure (must remain byte-identical):
  [`workflows/marketplace/analysis_execution.py:287-313`](../../workflows/marketplace/analysis_execution.py).
