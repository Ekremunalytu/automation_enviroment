# Risk Register

`Last Updated: 2026-05-13`

This register reflects the current post-W13 close-out architecture and the
remaining post-PoC hardening risks.

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
- W6 added the scenario truth ledger, but the current backlog still tracks
  `[BUG scenario-dropout-upstream-root-cause]` as W14-1 BLOCKER triage.
  Planner/runtime/report drift would immediately mislead analysts if this
  surface regresses.

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

### P2 - Security-fixture hygiene moved off CI after pipeline retirement

Files:

- `tests/security/`
- `Makefile`
- `.github/workflows/security.yml`
- `documents/adrs/0004-malicious-fixture-policy.md`

Why it matters:

- `.github/workflows/ci.yml` and `docs-check.yml` were retired
  `2026-04-30` (`REFACTOR_STATUS.md`); the persistent `security-fixtures`
  egress-sandbox flake source was removed alongside, and CI no longer
  asserts `make test-security-live` fails under `CI=true`.
- The remaining CI surface is `security.yml` (weekly Trivy + Bandit).
  Egress-disabled `make test-security` is now the local-only guard for
  malicious-fixture hygiene; install-guard work remains operator-side.
- Re-introducing a CI lane that runs malicious fixtures must again
  disable outbound egress before `make test-security` and keep
  `make test-security-live` red under `CI=true`.

### P2 - LAN exposure remains an opt-in operator decision

Files:

- `.env.example`
- `docker-compose.yml`
- `appcore/api/config.py`
- `tests/architecture/test_default_bindings.py`
- `documents/adrs/0007-local-network-binding.md`
- `documents/runbooks/lan-exposure.md`

Why it matters:

- ADR 0007 is Accepted and implemented `2026-04-29` via W8-7. Defaults
  bind loopback (`API_HOST=127.0.0.1`,
  `CORS_ALLOW_ORIGINS=http://localhost:3000`,
  `CORS_ALLOW_CREDENTIALS=False`); default-profile compose `ports:`
  entries carry the `127.0.0.1:` prefix; host-side CDP exposure runs
  only under the `debug` compose profile via the `executor-cdp` sidecar.
- LAN exposure now requires both `EXTRACE_ALLOW_LAN=1` (host-side
  uvicorn/CORS substitution in `model_post_init`) **and** manual
  compose port edits per `documents/runbooks/lan-exposure.md`.
- Operators who flip both still inherit the rest of the runbook's
  pre-flight checklist (firewall rules, reverse-proxy auth, explicit
  CORS allow-list, rotated PostgreSQL password) — that responsibility
  did not move to code.

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
  RCE-equivalent on the API would inherit host-wide container control. With
  ADR 0007 / W8-7 enforced (landed `2026-04-29`), the default loopback bind
  keeps this exposure bounded to the design assumption; flipping
  `EXTRACE_ALLOW_LAN=1` plus the manual compose port edit re-introduces the
  load-bearing condition and must be paired with the `lan-exposure.md`
  runbook hardening.
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
- ADR 0007 loopback/default-profile enforcement landed `2026-04-29`
  via W8-7; this risk is therefore accepted in its post-landing form
  (loopback bind plus the `EXTRACE_ALLOW_LAN` + manual compose-edit
  opt-in described above).

### Single active analysis

- The background analysis flow is intentionally serialized.
- This matches the one-user sandbox deployment and avoids unnecessary queue
  infrastructure.

## Priority Mitigations

- keep executor failure reporting explicit in marketplace responses
- keep report semantics and health metadata honest when a run is degraded
- expand bounded capture without storing unsafe raw payloads
- keep CI egress hardening observable and fail-closed
- keep ADR 0007 loopback defaults green; `tests/architecture/test_default_bindings.py`
  is the regression guard and must not be skipped or weakened
