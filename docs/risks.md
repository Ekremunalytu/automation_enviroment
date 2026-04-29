# Risk Register

`Last Updated: 2026-04-29`

This register reflects the current post-W8-0 architecture and the remaining
post-PoC hardening risks.

## Active Risks

### P1 - Executor truthfulness remains a critical reliability boundary

Files:

- `executor/flows/playwright/entrypoint_runner.py`
- `executor/flows/playwright/health_summary.py`
- `packages/analysis_contracts/report_invariants.py`
- `workflows/marketplace/analysis_service.py`

Why it matters:

- The product promise depends on requested scenarios being reported honestly as
  executed, failed, or skipped with an explainable reason.
- W6 closes the silent-dropout bug class, but future planner/runtime/report
  drift would immediately mislead analysts if this surface regresses.

### P1 - Runtime capture remains intentionally bounded

Files:

- `executor/flows/playwright/runtime_capture/network.py`
- `executor/flows/playwright/runtime_capture/extension_host.py`
- `packages/analysis_contracts/contracts.py`

Why it matters:

- HTTP body capture is limited to cleartext HTTP previews and hashes, and
  child-process tracking is scoped to the observed extension-host tree.
- That keeps artifacts safe and bounded, but it also means TLS payloads and
  out-of-scope process activity remain intentionally unseen.

### P2 - Activation reports are artifact-first while jobs are DB-backed by design

Files:

- `workflows/activation_reports/router.py`
- `workflows/marketplace/router.py`
- `output/`

Why it matters:

- Activation reports remain filesystem artifacts while async job metadata now
  lives in PostgreSQL.
- This split limits report queryability and historical comparison, but it keeps
  the current single-user sandbox model operationally simple.

### P2 - Coverage remains partial even though unsupported surfaces now fail closed

Files:

- `executor/flows/playwright/stimulus_materializers.py`
- `executor/flows/playwright/stimulus_passes.py`
- `workflows/marketplace/trigger_service.py`

Why it matters:

- W6 makes unsupported activation families and failed materialization explicit,
  which is safer than optimistic fallbacks.
- The tradeoff is that fixture/matrix gaps now surface as degraded coverage
  instead of being papered over.

### P2 - Security-fixture CI hardening now depends on runner firewall controls

Files:

- `tests/security/`
- `Makefile`
- `.github/workflows/ci.yml`
- `documents/adrs/0004-malicious-fixture-policy.md`

Why it matters:

- The CI lane now disables outbound egress before `make test-security` and
  asserts that `make test-security-live` fails under `CI=true`.
- This is the intended posture, but it still relies on GitHub runner support
  for the firewall step and does not replace the remaining install-guard work.

### P2 - Host-facing services still need ADR 0007 enforcement

Files:

- `.env.example`
- `docker-compose.yml`
- `appcore/api/config.py`
- `documents/adrs/0007-local-network-binding.md`

Why it matters:

- ADR 0007 is Accepted, but current defaults still include `0.0.0.0`,
  wildcard CORS, and host-mapped noVNC/CDP ports.
- Until W8-7 lands the loopback defaults, CORS allow-list, CDP debug profile,
  and architecture test, operators must treat LAN exposure as an active
  environment risk.

### P2 - API container mounts the host Docker socket (deliberate, scope-bounded)

Files:

- `docker-compose.yml`
- `executor/host.py`
- `documents/adrs/0001-single-host-appliance.md`

Why it matters:

- The API container needs `docker exec` to drive the executor; the socket
  mount is the chosen mechanism. Per ADR 0001 the appliance is single-host
  single-operator, so the blast radius is the operator's own machine.
- The trade-off becomes load-bearing the moment LAN exposure is opened: any
  RCE-equivalent on the API would inherit host-wide container control. This
  risk therefore tracks W8-7 closely — once loopback is enforced, the
  exposure is bounded back to its design assumption.
- Not currently planned to gate with a docker-socket-proxy; revisit only if
  the threat model shifts (e.g., exposing the API for remote operator use).

### P2 - Executor container runs with NET_RAW + SYS_PTRACE (deliberate, observation-side trade-off)

Files:

- `docker-compose.yml`
- `executor/container/Dockerfile`
- `executor/flows/playwright/runtime_capture/network.py`
- `executor/flows/playwright/runtime_capture/extension_host.py`

Why it matters:

- `NET_RAW` is required by the tshark/tcpdump capture pipeline; `SYS_PTRACE`
  is required by strace-based extension-host observation.
- The threat model assumes the extension under analysis can execute
  arbitrary code inside the executor container. Combined with these caps,
  an in-sandbox attacker can sniff sibling-process traffic and ptrace other
  in-container processes — i.e. evade or pollute observation rather than
  escape the container.
- Accepted because the observation pipeline depends on these caps; document
  the trade-off here so the next reviewer doesn't have to re-derive it.

### P2 - Background analysis thread can drop uncaught exception types silently

Files:

- `workflows/marketplace/router.py`
- `workflows/marketplace/analysis_service.py`

Why it matters:

- `run_analysis_job` enumerates the exception types it converts into
  `fail_job` calls. Any other exception (e.g. a future `RuntimeError`,
  `httpx.HTTPError`, `ConnectionResetError`) propagates out of the daemon
  thread and the job row stays in `running` until process restart triggers
  `recover_interrupted_jobs`.
- Cancellation, single-active-job enforcement, and UI status all rely on
  the row being moved out of `running` promptly; a silent drop blocks the
  next analysis until restart.
- Tracked for follow-up in `POST_POC_BACKLOG.md` under
  `[FOLLOWUP analysis-thread-supervisor]` (structural complement to the
  existing `7.1.4 narrow the broad except` item).

## Accepted Risks

### Local noVNC exposure after W8-7

- noVNC is intended for local operator access, not public deployment.
- This remains accepted only after ADR 0007 loopback/default-profile
  enforcement lands; until then, see the active host-facing services risk.

### Single active analysis

- The background analysis flow is intentionally serialized.
- This matches the one-user sandbox deployment and avoids unnecessary queue
  infrastructure.

## Priority Mitigations

- keep executor failure reporting explicit in marketplace responses
- keep report semantics and health metadata honest when a run is degraded
- expand bounded capture without storing unsafe raw payloads
- keep CI egress hardening observable and fail-closed
- land ADR 0007 W8-7 binding defaults before treating localhost-only exposure
  as mechanically enforced
