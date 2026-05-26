# Development Priorities

`Last Updated: 2026-05-26 (W19 closed synthetically — Hat-1 + Hat-2 fully closed; PR #28 week19 -> main MERGED 2026-05-26 via c879603)`

This is the short priority list for current work. It assumes the project stays
a single-user sandbox appliance on one machine or one Docker host.

If any older planning note clashes with the active refactor track, follow
`REFACTOR_STATUS.md` for current closure state and
`REFACTOR_OPTIMIZATION.md` §11 for the closed W8-W13 external-review window,
§12-§16 for closed W14-W18 work, §17 for active W19, and §18-§20 for the
W20-W22 roadmap. Post-PoC deferrals live in `POST_POC_BACKLOG.md`.
Keep changes biased toward cleanliness, stability, and overall code quality.

## Current Window (7 weeks, 2026-04-17 -> 2026-04-23; closed)

**Acceptance bar: PoC.** The window targeted a demonstrable
proof-of-concept that catches basic malicious extensions, not a full-featured
production security product. Full scope stays in the plan; PoC framing selected
Must vs Stretch. See `REFACTOR_OPTIMIZATION.md` §10 for Must/Stretch split and
§10.7 for the PoC acceptance checklist (**11/11 green as of 2026-04-23**).

- **W0 (spec, complete):** security foundations written as ADRs 0002-0004 with
  PoC-priority annotations.
- **W1-W4 (complete, closed 2026-04-20):** automation stabilization before
  security implementation.
- **W5 (detection foundations, complete 2026-04-20):** detection contracts,
  A1/A2/A4/A6 rule scaffolding, T1 canaries under `extensions/malicious/`,
  `tests/security/`, and `make test-security` / `make test-security-live`.
- **W6 (automation reliability + capture hardening, closed 2026-04-23):**
  scenario truth ledger, bounded waits, capture bounds, plus the W6
  correctness follow-up that gated A1/A2/A4 on `ActivationReport` attribution
  (`target_file_events`, `target_unknown_outbound_network_events`), added
  `tls_client_hello` to `TLS_EVENT_TYPES`, enforced
  `RuleExecutionStatus.ERROR` dominance in verdict rollup, and re-narrowed
  `.gitignore` so security fixtures reach the `security-fixtures` CI lane.
- **W7 (acceptance + buffer, closed 2026-04-23):** §10.7 PoC acceptance
  checklist met (11/11); [`DEMO_SCENARIO.md`](DEMO_SCENARIO.md) +
  [`scripts/demo_acceptance.py`](../scripts/demo_acceptance.py) cover the A1
  credential-read → network canary end-to-end. Phase 3a buffer added
  stretch rule `extrace.a3.typosquat`
  ([`packages/analysis_engine/rules/a3_typosquat.py`](../packages/analysis_engine/rules/a3_typosquat.py))
  with canary + `popular_extensions.txt` allow-list. Final
  `make test-security` → 41 passed; `make check-all` → 627 passed / 5
  skipped.
- **Post-W7 hardening (2026-04-24):** four reliability + modularization
  landings: (1) fatal UI-crash fail-fast classifier in
  `_run_scenario_sequence`; (2) scan-between VS Code restart
  (`reset_executor_state` + shared `launch_vscode.sh`) fixing the ESLint
  `onStartupFinished` install race; (3) `attribution/` subpackage split
  (`monitor_attribution.py` → three files, flat re-export facade); (4)
  `sim-target` Makefile lane for single-extension smoke runs.
- **Post-W7 simulation UX + reliability (2026-04-25):** four further
  landings on the `feat/simulation-progress-cancel` branch: (1) weighted
  simulation progress (UI phase weights + heartbeat scenario sub-progress,
  monotonic 0-100 % climb instead of 20 % chunks); (2) full-stack
  analysis cancel flow (later hardened in W13-3 into non-terminal
  `cancelling`, worker poll points, and explicit finalization); (3) VNC
  harness ready-marker fix
  (`vscode.py::reload_workbench_window` deletes the marker before reload;
  harness `activate()` is async and awaits the marker write); (4) the
  `t1-demo-runnable-canary` declawed fixture + `demo_runnable_canary.py`
  rule + `make demo-canary` / `make demo-canary-offline` lanes. Code
  review follow-ups (dialog replacement, cancel-mutation timeout,
  heartbeat off-thread reset, etc.) deferred under
  `[FOLLOWUP simulation-progress-cancel]` in `POST_POC_BACKLOG.md`.
- **PR345 + W8-0 (2026-04-27):** target activation lifecycle PRs 1-5
  landed with ADR 0006 target output-channel capture. W8-0 then hardened the
  harness readiness gate with epoch/pid-aware marker validation and typed
  `harness_*` reason codes. W8 opened on `2026-04-27` and **closed
  `2026-04-29`** (W8-1..W8-7 + W8-9 landed, W8-8 deferred); see
  `REFACTOR_STATUS.md`.
- **Pre-W6 cleanup (complete, 2026-04-20):** dormant root directories removed,
  marketplace trigger planning narrowed to `TriggerPlan`, and
  `executor/flows/playwright/monitor.py` reduced to a facade over split helper
  modules (the flat `monitor.py` later became `monitor/__init__.py` in W12-1,
  2026-05-07).

**PoC Must classes (ADR 0002):** A1 credential stealer, A2 cryptominer, A4
remote-loader, A6 package.json script abuse — **rules landed**. **Stretch
classes:** A3 typosquat landed 2026-04-23; A5 malicious update and A7 VS
Code API abuse remain in `POST_POC_BACKLOG.md`.

The priority list below describes the enduring engineering priorities that
survive past W7 closure. Active iteration scope pulls from
`POST_POC_BACKLOG.md` and the frozen W19 tracker
`active-work/W19-live-run-root-cause.md` (W20 tracker opens at W20-0).

## Current Priorities

### 1. Executor Failure Honesty

- keep reset, install, reload, trigger-load, and monitor failures explicit
- make interrupted async jobs obvious after API restarts
- fail closed when executor timing becomes ambiguous

### 2. Supply-Chain Boundary Tightening

- keep harness-extension checksum verification enforced before trusting helper
  bundles in W5/W6 runs
- keep workflow access to Docker daemon behavior behind `executor.control`
- avoid broadening sandbox trust assumptions without updating ADR 0002

### 3. Coverage Fidelity

- keep official activation coverage separate from heuristic workflow coverage
- close official-track gaps for `scm` and `settings`
- decide which partial scaffolding should graduate into supported coverage for
  `chat`, `comments`, `testing`, and `workspace_trust`

### 4. Report Contract Stability

- keep report JSON stable for the UI
- preserve sharp semantics for `degraded` vs `inconclusive`
- keep attribution, risk signals, and verdict reasons evidence-linked

### 5. Security Scaffold Integrity

- keep malicious-fixture manifests aligned with ADR 0004
- keep `tests/security/` and `make test-security` honest about current PoC
  scope
- separate "fixture scaffold exists" from "detection rules are implemented"

### 6. High-Value Test Depth

- keep async job lifecycle coverage healthy
- keep restart interruption coverage healthy
- keep smoke coverage honest against real executor behavior
- wire the security scaffold into dedicated CI coverage when guardrails are ready

### 7. Lightweight Artifact Operations

- define retention and cleanup expectations for `output/`
- treat analysis output as semi-trusted (ADR 0002 §6); no automatic forwarding
  without scrubbing
- avoid speculative DB-backed run-history work unless operators need it

## Non-Priorities

- queue-backed distributed workers
- multi-tenant accounts or session management
- broad package reshuffles without a concrete product problem
- new dependencies without explicit need and approval
