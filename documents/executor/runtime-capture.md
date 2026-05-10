# Runtime Capture

`Last Updated: 2026-05-07`

`executor/flows/playwright/runtime_capture/` — monitor-owned event
parsing and capture helpers. Top-level executor doc:
[`../EXECUTOR_PLAYWRIGHT.md`](../EXECUTOR_PLAYWRIGHT.md). Module map:
[`playwright-flow.md`](playwright-flow.md).

## Subpackage Layout

```text
executor/flows/playwright/runtime_capture/
  _shared.py          shared parser primitives + epoch helpers
  events.py           runtime event normalization
  extension_host.py   extension-host log discovery + parsing
  filesystem.py       inotify-driven filesystem capture
  log_summary.py      log summarization for report assembly
  network.py          network capture (libpcap / tshark wrappers)
```

All modules are re-exported through the `monitor/` package facade
(`monitor/__init__.py`, post-W12-1) for backwards compatibility; do
not import them directly from outside the `monitor/` package unless
you are inside another `runtime_capture/` module.

## What Each Capture Helper Owns

### `network.py`

- Network capture from libpcap / tshark.
- `tls_client_hello` matching (covered by
  `make test-security-live`; user-side, the most fragile detection
  surface).
- Ingestion produces normalized records consumed by
  `attribution/events.py::_annotate_network_events`.

### `filesystem.py`

- inotify-driven filesystem event stream.
- Annotated against activation windows by
  `attribution/events.py::_annotate_file_events`.
- Handles bait-file artifact paths planted by `workspace/seed_*`.

### `extension_host.py`

- Discovery + parsing of Extension Host logs.
- Module-level `_LAST_EXTHOST_LOG_COUNT: int = -1` rate-limits the
  `"Found N Extension Host log file(s)"` emit to state changes only
  (post-W7 cosmetic fix; signal still appears when a new exthost log
  shows up mid-run).

### `events.py`

- Normalizes runtime event payloads (network + filesystem +
  extension-host) into the shared record shape consumed by attribution
  and the scenario ledger.

### `log_summary.py`

- Summarization for report assembly: count caps, time-bounded windows,
  scenario alignment.
- Consumed by `report_builder.py` and `health/summary.py`.

### `_shared.py`

- Shared epoch helpers (`_resolve_event_epoch`, `_format_epoch_timestamp`,
  `_relative_time`).
- Parser primitives reused across the four domain modules.

## Capture / Replay Discipline

- All capture artifacts are **observed at runtime**; nothing is replayed
  from a recorded file. Capture state is reset between scans by
  `reset_executor_state` (see
  [`host-wrapper.md`](host-wrapper.md) §"Scan-Between Restart").
- Captured network/filesystem events carry epoch timestamps; activation
  windows are derived in `attribution/events.py` from extension-host
  log entries, not from capture-side metadata.
- The `attribution/` subpackage is the **only** consumer of raw
  `events.py` output; rules and verdict logic live in `packages/`.

## Test Hooks

- `tests/executor/test_playwright_monitor_runtime.py` — runtime loop
  exercise.
- `tests/executor/test_playwright_monitor_lifecycle.py` — scenario
  ledger sequencing across capture sources.
- `tests/security/test_canary_end_to_end.py` — wires a canary fixture
  through the rule runner; covers the network + filesystem capture
  surfaces against pinned T1 fixtures.
- `make test-security-live` (T2/T3) — the only path that exercises
  real `tls_client_hello` matching.

## Known Fragility

Live capture (`make test-security-live`) is the most fragile detection
surface. tshark / runtime-capture changes can silently regress
`tls_client_hello` matching even though `make test-security` (offline)
stays green. Docker-based A1 canary structural diff
(`make exec-up && make exec-run` against
`t1-a1-credential-read-to-network-canary`) is the canonical user-side
smoke gate.

## W8 Items Touching Capture

- **W8-6** — content-sample secret redaction. **Closed** —
  - harness-marker channel: W10-7 (`2026-05-04`)
  - extension-host log tail companion: W11-6 (`2026-05-05`)
  - file-backed output-signals channel: W12-0 (`22eb836`, `2026-05-07`)
  - channel/summary fields: W12-0 dolgusu (`b642af7`, `2026-05-07`)

  Helper: `packages/analysis_contracts/evidence.py::ContentSample.redact_secrets`
  with five secret classes (aws, bearer, private_key, api_key, db_url).
  Broader structural enforcement is tracked under
  `[FOLLOWUP w8-6-content-sample-structural-test]` for W13.
- **W8-8** — manifest field log-injection sanitization. **Deferred
  `2026-04-29` under named triggers A/B**, not abandoned. No production
  call site currently emits attacker-controlled manifest fields
  (`displayName`, `description`, `repository.url`, `categories[]`,
  `homepage`, `bugs`, `qna`, `license`). Reactivation conditions and
  the planned helper at `appcore/contracts/sanitize.py::sanitize_for_log`
  are documented in `documents/active-work/W8-security.md` and
  `[FOLLOWUP w8-8-manifest-emit-when-needed]` in
  `POST_POC_BACKLOG.md`.

Detail: [`../active-work/W8-security.md`](../active-work/W8-security.md)
items W8-6 and W8-8.
