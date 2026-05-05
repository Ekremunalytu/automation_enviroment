# Executor Playwright Architecture

`Last Updated: 2026-05-05`

ExTrace's dynamic-analysis sandbox: full VS Code GUI session inside
Docker, driven by Playwright, exporting artifact-first analysis results
into `output/`. **Slim canonical** — module/operation detail split out:

- [`executor/host-wrapper.md`](executor/host-wrapper.md) — container
  boot, host control surface (`executor/host.py`), scan-between
  restart, API integration details.
- [`executor/playwright-flow.md`](executor/playwright-flow.md) —
  analysis execution phases, trigger payload, Playwright module
  responsibilities, entrypoint flags, fatal-UI-crash handling, reload
  behavior.
- [`executor/runtime-capture.md`](executor/runtime-capture.md) —
  `runtime_capture/` subpackage, network/filesystem/extension-host
  capture, log summarization.

Open this only when changing executor / container / Playwright
behavior or the API integration points that drive it.

## Security Scope (ADR 0002 §4)

The executor is the analyzer's primary security surface, not merely an
operational component.

- VS Code binary trusted only if pinned.
- Harness-extension checksum verification enforced at executor startup
  (`executor/container/start.sh` verifies
  `/home/executor/flows/harness_extension.sha256` written by the
  container Dockerfile). Landed W5; do not regress.
- Extension code at runtime is untrusted and never elevated by
  heuristic.
- Docker daemon access from the API path is mediated through the
  `ExecutorControl` boundary.

Changes to executor behavior that affect any of these boundaries must
update ADR 0002 §4 in the same change set.

## Post-W7 Hardening (2026-04-24 → 2026-04-25)

- Fatal UI-crash classification + fail-fast in `_run_scenario_sequence`
  (`is_fatal_ui_error` substring + closed-checks + ≤1.5 s liveness
  probe). Detail: `playwright-flow.md` §"Fatal UI Crash Handling".
- Scan-between VS Code restart orchestrated by `reset_executor_state`
  via the shared `executor/container/launch_vscode.sh`. Detail:
  `host-wrapper.md` §"Scan-Between Restart".
- `attribution/` subpackage replaced the former
  `monitor_attribution.py` monolith with a three-file split behind a
  flat re-export facade. Detail: `playwright-flow.md`
  §"Playwright Module Responsibilities".
- `vscode.py::reload_workbench_window` now `unlink()`s
  `_HARNESS_READY_PATH` before dispatching the reload (eliminating the
  stale-marker race that crashed the harness extension on VNC after a
  reload); harness extension's `activate()` is `async` and awaits
  `writeHarnessReadyMarker()` so a write failure surfaces a clean
  `HarnessUnavailableError` timeout.
- Monitoring heartbeat in
  `workflows/marketplace/analysis_execution.py` polls
  `is_job_cancelled` every 5 s and triggers
  `executor_control.reset_sandbox(reload_window=True)` on cancel —
  resulting `ExecutorError` converts to `AnalysisCancelledError` so
  `run_analysis_job` returns silently.
- `t1-demo-runnable-canary` fixture exercises a declawed end-to-end
  path (localhost-only POST + workspace-local file write + explicit
  `onCommand` activation) for the new `make demo-canary` lane.

## Product Assumptions

- One operator.
- One sandbox host.
- One active background analysis job at a time.
- Rerun is acceptable recovery after interruption.
- Not a queue-backed worker system; do not document it as one.

## Runtime Layout (Summary)

```text
executor/
  control.py           workflow-facing boundary
  host.py              docker exec + retry/cleanup
  container/
    Dockerfile, start.sh, launch_vscode.sh, requirements.txt
  flows/
    harness_extension/ local helper extension
    playwright/        VS Code automation, attribution/, runtime_capture/, scenarios/
```

Full file inventory: `ls executor/flows/playwright/`. Module
responsibility map: `executor/playwright-flow.md`.

## Operational Commands

```bash
make exec-build
make exec-up
make exec-shell
make exec-test
make exec-run
make sim-all                        # UI-stimulus stress: scenarios w/o target ext.
make sim-target TARGET=pub.name \   # target-extension smoke (activation hygiene)
                [TRIGGERS=/path/to/payload.json] \
                [SCENARIO=<name>]
make sim-demo
make sim-list
make sim-run SCENARIO=<name>
make demo-canary                     # full canary demo
make demo-canary-offline             # <30 s detection-engine sanity
```

`sim-all` vs `sim-target` (split introduced 2026-04-24):

- `sim-all` is the UI-stimulus stress lane (scenarios w/o a target
  extension). Its reports are **inconclusive by design**; answers
  "do the scenarios survive a full pass?" not "does this extension
  activate cleanly?"
- `sim-target` (requires `TARGET=publisher.name`) runs
  `entrypoint.py --monitor --target-extension-id $(TARGET)` with
  optional `TRIGGERS` / `SCENARIO` passthrough; correct lane for
  "did a normal extension activate cleanly?"
- Missing `TARGET` exits non-zero with a usage hint.

## API Integration (Summary)

| Endpoint | Mode |
|---|---|
| `POST /api/marketplace/analyze` | sync |
| `POST /api/marketplace/analyze/start` | async start |
| `GET /api/marketplace/analyze/{job_id}` | async status |
| `POST /api/marketplace/analyze/{job_id}/cancel` | async cancel |

Persisted job state in PostgreSQL `analysis_jobs`. Reports written to
`output/activation_report_<publisher>.<name>-<version>-<runid>.json`.
Job snapshots carry an `owner_boot_id`; if the API process restarts
while a job is active, the next load converts it to a failed
interrupted state.

Detail: `executor/host-wrapper.md` §"API Integration".

## UI Integration

SPA uses the executor pipeline through three routes:

- `/marketplace` — search, download, launch async analysis.
- `/simulation` — poll job state, inspect the live report.
- `/reports` — inspect the finalized report artifact.

Frontend files: `ui/src/features/{marketplace,simulation,reports}/`.

## Current Limitations

- Activation reports remain file-backed; async job metadata is
  DB-backed.
- The pipeline depends on Docker exec success and VS Code timing.
- Live capture (`make test-security-live`) is the most fragile
  detection surface; tshark / runtime-capture changes can silently
  regress `tls_client_hello` matching even though `make test-security`
  (offline) stays green. Docker-based A1 canary structural diff
  (`make exec-up && make exec-run` against
  `t1-a1-credential-read-to-network-canary`) remains the canonical
  user-side smoke.
- Only one background analysis job is allowed at a time.
- ADR 0007 (local network binding) is **Accepted and implemented**
  `2026-04-29` via W8-7 — default-profile compose ports carry the
  `127.0.0.1:` prefix; the CDP port runs only under the `debug`
  compose profile (executor-cdp sidecar); LAN exposure is opt-in via
  `EXTRACE_ALLOW_LAN=1` (host) plus manual compose port editing per
  `documents/runbooks/lan-exposure.md`. Pinned by
  `tests/architecture/test_default_bindings.py`.

## See Also

- ADR 0002 — threat model: `documents/adrs/0002-threat-model.md`.
- ADR 0007 — local network binding:
  `documents/adrs/0007-local-network-binding.md`.
- Detection contract:
  [`DETECTION_SEMANTICS.md`](DETECTION_SEMANTICS.md).
- Test layout: [`testing/executor-tests.md`](testing/executor-tests.md).
- Boundary rules:
  [`architecture/boundary-rules.md`](architecture/boundary-rules.md).
