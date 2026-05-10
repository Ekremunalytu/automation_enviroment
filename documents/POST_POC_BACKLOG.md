# Post-PoC Backlog

`Last Updated: 2026-05-10 (W12 close-out items closed; Codex Cloud audit 2026-05-10 ingested — 4 HIGH pulled forward + 2 MEDIUM pull-forward + ~10 backlog + 2 posture + 1 WONT-FIX + 9 verified-closed audit trail; H6 closed via W13-1 same day)`

Open deferred work after the W0-W7 PoC acceptance bar. **Slim canonical** —
verbose descriptions, evidence, and older triage notes are frozen in dated
snapshots:

- latest full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-07.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-07.md)
- previous full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md)

W8, W9, W10, W11, and W12 are closed. Active phase: **W13 test
expansion + observability**, tracked in
[`active-work/W13-test-expansion-observability.md`](active-work/W13-test-expansion-observability.md).

## Stable IDs Are A Contract

Do not rename existing IDs. Code/tests currently reference:

- `[FOLLOWUP analysis-jobs-race]`
- `[FOLLOWUP simulation-progress-cancel]`
- `[FOLLOWUP simulation-progress-cancel] cancel-after-finish race test`
- this filename from `packages/analysis_contracts/contracts.py`

Use stable IDs in new references; do not cite canonical doc line numbers.

## Codex Cloud Audit 2026-05-10

Snapshot of Codex Cloud findings exported `2026-05-10T15:50:38Z`
(38 findings against historical commits Feb-May 2026; triaged against
HEAD `cff6455` on `week13` `2026-05-10`). Audit trail; pull-eligible
items receive `W13-N` IDs at first pull per W11/W12 precedent.

### Pull-forward to W13 (HIGH OPEN — see W13 lane tracker for tabular row)

- **`[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]`** —
  H3. `Makefile` `dev-lan` recipe hard-codes `--host 0.0.0.0`;
  `documents/runbooks/lan-exposure.md` documents `API_HOST` override
  that the recipe ignores; `tests/architecture/test_default_bindings.py`
  covers settings layer only, no Makefile gate. Either fix the recipe
  to honor `API_HOST` or update the runbook + add Makefile gate. Lane:
  `[security-detection]` `[platform-storage]`.
- **`[FOLLOWUP codex-2026-05-10-H4-cancel-concurrent-race]`** — H4.
  Cross-ref existing `[FOLLOWUP simulation-progress-cancel]` 5
  sub-items. Adds Codex evidence: `cancelled` is in
  `_TERMINAL_JOB_STATUSES`, so `reserve_job()` releases the lock
  immediately while a cancelled-but-running worker can still drive the
  shared executor + `/results`. Cancellation polled only inside
  monitoring heartbeat — gaps before/after reset, install, trigger
  building, and just before completion. Add a `draining` intermediate
  state or block `reserve_job` while a cancelled worker exists; cover
  the gaps with cancel-poll points. Lane: `[executor-runtime]`
  `[platform-storage]`.
- **`[FOLLOWUP codex-2026-05-10-H5-writable-vscode-launcher]`** — H5.
  `executor/container/Dockerfile` chowns `launch_vscode.sh` to
  `executor:executor` mode 755 — analyzed extension can overwrite, and
  `reset_state.py` + `start.sh` re-execute the script across resets
  → persistent executor hook. Move to `--chown=root:executor` +
  `chmod 0750` (root-owned, executor read+exec only). Lane:
  `[executor-runtime]` `[security-detection]`.
- ~~**`[FOLLOWUP codex-2026-05-10-H6-spoofable-harness-markers]`**~~ —
  H6. `executor/flows/playwright/health/reconciliation.py` accepts
  `[extrace-harness] {json}` from the target-writable Extension Host
  log stream as proof of `automation_trace`; no auth/nonce. Forged
  `phase:"complete"` markers can satisfy verification → forged clean
  reports. **Closed via W13-1 (`2026-05-10`,
  `c7a9ca7`/`f31c820`/`ee7c8fb`/`2996856`/`6a80a87`):** per-launch
  HMAC-SHA256 handshake (Option C) — `launch_vscode.sh` mints a
  32-byte secret, harness extension reads + unlinks
  `/run/extrace/harness-secret` on activate before the target VSIX
  installs, Python orchestration loads + unlinks
  `/results/_extrace_harness_python_secret` in `setup_monitor` and
  stamps `ActivationReport.expected_harness_nonce`; reconciliation
  rejects unsigned/forged markers via constant-time HMAC compare.
  Test surface: 3 reconciliation regressions in
  `tests/executor/test_playwright_health_reconciliation.py`,
  3 AST gates in `tests/architecture/test_harness_marker_auth.py`.
  Lane: `[executor-runtime]` `[security-detection]`.

### Pull-forward to W13 (MEDIUM OPEN — surfaces where W12 work stopped short)

- **`[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]`** — M1.
  `redact_multiline_secrets()` (`packages/analysis_contracts/evidence.py`)
  private_key regex unanchored + lazy `(?:.|\n)*?` → catastrophic
  backtracking on many unmatched BEGIN markers, stalling final report
  generation until the docker exec automation timeout. W12-0 added
  the redaction itself; Codex new-finding `2026-05-10` flags this as
  a follow-up DoS vector on the same code. Bounded state machine or
  size/window-limited scan. Lane: `[security-detection]`.
- **`[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]`** —
  M9. W12-5 architecture gate
  `tests/architecture/test_network_body_preview_redaction.py` covers
  `*_body_preview` only;
  `executor/flows/playwright/runtime_capture/extension_host_strace_parse.py`
  assigns `arguments_preview` without `redact_secrets()`. Extend the
  W12-5 gate scope to include `arguments_preview` and route assignments
  through `redact_secrets()`. Lane: `[security-detection]`.

### Backlog (post-W13 candidates)

- **`[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]`** —
  M4 + M7. `read_output_channel_logs()` and
  `parse_output_signal_events()` parse extension-controlled `ts` field
  and pass to `datetime.fromtimestamp()` without finite/range guard;
  `monitor_lifecycle` invokes outside try/except. Malicious VSIX with
  `ts: 1e999` → `OverflowError` aborts final report. Add finite +
  range check before `fromtimestamp`. Lane: `[security-detection]`
  `[executor-runtime]`.
- **`[FOLLOWUP codex-2026-05-10-M5-epoch-docker-exec-propagation]`** —
  M5. `EXTRACE_EPOCH_RUN_ID` set in `start.sh` but `executor/host.py`
  `docker exec` only injects `PYTHONUNBUFFERED` — epoch not propagated
  → `expected_epoch_run_id` empty → stale-marker check disabled. Empty
  epoch markers always accepted. Add env propagation in `host.py`
  docker exec invocation. Lane: `[executor-runtime]`.
- **`[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]`** —
  M10. Async `run_analysis_job` catches `(TypeError, AttributeError)`
  but sync `/api/marketplace/analyze` endpoint does not; malformed
  `contributes.customEditors` raises uncaught from planner. Add same
  catch wrapper at sync endpoint. Lane: `[platform-storage]`.
- **`[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]`** —
  M11. `analysis_reports.py::_build_report_messages()` calls
  `int(automation_health.get("target_activation_count"))` without
  type-guard; malicious extension writes `"not-an-int"` → ValueError
  fails the job. Pydantic schema for `automation_health` or
  defensive try/except. Lane: `[platform-storage]`.
- **`[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]`** —
  M12. `executor/flows/playwright/workspace/__init__.py::clean_workspace()`
  checks `is_dir()` before `is_symlink()` — directory symlink fails
  `shutil.rmtree`. `reset_state.py::_clear_directory()` (canonical
  reset path) has correct symlink-first order, but the orphan
  `clean_workspace()` is still vulnerable in isolation. Either delete
  `clean_workspace()` if unused or fix the order. Lane:
  `[executor-runtime]`.
- **`[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]`** —
  M13. `runtime_capture/network.py` `path` and `summary` fields
  assigned directly from `http.request.uri` and `_ws.col.Info` without
  `redact_secrets()` — bearer tokens / API keys in query strings leak
  to reports + unauthenticated API. W12-5 gate scope is `*_body_preview`
  only. Extend redaction + gate to URI/summary fields (pair with M9
  fix). Lane: `[security-detection]`.
- **`[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]`** —
  M14b. VS Code `--remote-debugging-port=9222` enabled by default in
  `executor/container/launch_vscode.sh` and `start.sh`; CDP has no
  built-in auth, reachable from same container by analyzed extensions.
  Disable by default; opt-in via `EXECUTOR_CDP_PORT=...` env when
  debugging. Lane: `[executor-runtime]` `[security-detection]`.
- **`[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]`** —
  U1+U2+U3. `EventDensityStrip` allocates `Array.from({length:
  bucketCount})` from unbounded `rel_time_s`; `EventTimeline` uses
  `Math.max(...allEvents.map(e=>e.t))` (RangeError ~130k entries);
  `ActivityBars` same spread risk. Iterative min/max + event-count cap
  - contracts.py `rel_time_s: float = Field(le=86400)`. Lane: `[ui]`
  `[contracts]`.
- **`[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]`** — U6.
  `InspectorSections.tsx` Relations tab passes full `inspector.related`
  array into ECharts force-directed graph with no cap (the existing
  `slice(0,8)` only caps direct-links display, not the graph). Add
  cap (max N nodes / edges) and confidence clamp. Lane: `[ui]`.
- **`[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]`** —
  U4 (MEDIUM) + U12 (LOW). `make sim-target` and `sim-run` recipes
  use `$(TARGET)` / `$(SCENARIO)` unquoted; metacharacters in operator
  input → host shell injection. Quote with `printf %q` or pre-validate
  variable contents. Lane: `[engineering-quality]`.
- **`[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]`** — U8.
  `appcore/contracts/schema_defs/catalog.py::ExtensionActivationEventsSchema`
  `event_type: str` has no `Field(max_length=...)`; list count
  unbounded; DB `event_type` indexed as unbounded String → btree
  failure for very long values + memory/CPU exhaustion at ingestion.
  Add `Field(max_length=128)` + list cap + alembic migration to
  `String(128)`. Lane: `[contracts]` `[platform-storage]`.

### Quick fixes (XS scope, can land alongside any W13-N)

- **`[FOLLOWUP codex-2026-05-10-I1-env-example-truthy-drift]`** — I1.
  `.env.example` says `EXTRACE_SKIP_JOB_RECOVERY=on` is truthy but
  `main.py` only recognizes `1`/`true`/`yes`. Doc fix in
  `.env.example`. Lane: `[engineering-quality]` `[docs]`.
- **`[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]`** — I2.
  `ui/src/lib/api/client.ts::getHealth()` calls `/health`; nginx
  proxies `/api/*` only → falls through to index.html → UI parses
  HTML as JSON. Change path to `/api/health` (or extend nginx config).
  Lane: `[ui]`.
- **`[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]`** — I4.
  `runtime_capture/extension_host_log_parse.py` regex
  `.*?(?P<id>[\w.\-]+)` non-greedy captures `id="for"` instead of the
  actual extension id in `"activate entered for sample.publisher"`
  format. Add `for\s+` literal token requirement; pin with regression
  test using both formats. Lane: `[security-detection]`.

### Posture decisions (ADR rather than code fix)

- **`[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]`** —
  U10 + U11. `/getExtensionsBaseInfo`, `/getExtensionsAllInfo`,
  `/searchExtension`, `/createExtension` registered without
  authentication. AGENTS.md threat model already accepts LAN-reachable
  unauthenticated API as PoC posture (`make dev-lan` flow), but Codex
  flags this. Decide: codify in ADR (PoC-stage acceptance, with
  `EXTRACE_ALLOW_LAN` gate as the explicit operator opt-in) or
  introduce auth before W14. Lane: `[security-detection]`
  `[platform-storage]`.

### Verified-closed by W8-W12 work (audit trail; no action)

For audit completeness — these are no-action items, recorded so
future Codex re-runs can confirm closure persists:

- **H1** — Workspace can shadow trusted contract imports → closed by
  W9 ADR 0008 package-mode pivot (PR #9 `d67944d`); `sys.path.insert`
  debt removed across executor tree.
- **H7** — Executor-writable report symlinks → closed by W8-5 regex
  gate `ACTIVATION_REPORT_NAME_RE` + `resolve()` deduplication in
  `workflows/activation_reports/router.py`. Symlink-specific test
  case still missing — could be added under
  `tests/workflows/activation_reports/test_router_path_traversal.py`.
- **M2** — VSIX rejection logging DoS → cross-ref existing
  `[FOLLOWUP w8-1-vsix-rejection-log-sanitization]` (P2; below);
  Codex evidence confirms still open.
- **M3** — Workspace Python path hijack of signal policy → closed
  by W9 (PYTHONPATH=/home + signal_policy moved to packages/).
- **M6** — Harness diagnostics misattribution → closed by W8-0
  deterministic harness readiness + W11-4 target-log lifecycle
  instrumentation.
- **M8** — Target logs globally misattributed → closed by W11-4.
- **U5** — Typosquat CPU DoS → closed by `_MAX_TYPOSQUAT_DISTANCE = 2`
  early-cutoff in `a3_typosquat.py`. (Length cap on
  `target_extension_expected` would be additional defense-in-depth
  but not strictly necessary.)
- **U7** — Reserved manifest fields crash → closed by defensive
  `isinstance(untrusted, dict)` typing in
  `workflows/extension_catalog/manifest_parser.py`.
- **U9** — Malformed `capabilities` field crash → closed by same
  defensive typing as U7.
- **I3** — Recovery retry deletes valid late marker → closed by W11-1
  lifecycle split refactor (conditional unlink based on reason).

### Partial closures (need follow-up listed above)

- **H2** — Executor entrypoints hijack via `/workspace` cwd. Pattern
  closed by W9 (no more `sys.path.insert` debt) but `executor/host.py`
  `docker exec` does not pin `--workdir /home`. Low residual risk
  given W9 import hygiene, but the defense-in-depth fix is one line.
  Tracked as `[FOLLOWUP codex-2026-05-10-H2-docker-exec-workdir-pin]`
  (not pulled — defense-in-depth, low priority unless an exploitable
  path resurfaces).

### WONT-FIX

- **M14a** — `executor/flows/playwright/workspace/__init__.py`
  ownership `executor:executor`. By-design per W12-1 package layout —
  the executor user owns its automation flows tree; this is not the
  same as H5 (which is a launcher script that should be root-owned).
  Codex conflates the two surfaces; rejected with reason recorded
  here.

## W12 Pull-Forward

- ~~**`[FOLLOWUP w8-6-output-signals-file-backed-redaction]`**~~ —
  **W12-0 landed `2026-05-07` on `week12` in commit `22eb836`.**
  `redact_secrets(_truncate(line))` applied at
  `executor/flows/playwright/signals/output.py:209` (path post-W12-1;
  was `output_signals.py:205` at W12-0 landing); W10-7 source
  comment updated to name both harness-marker and file-backed paths;
  four file-backed regression tests + three harness-marker
  end-to-end regressions added under
  `tests/platform/security/test_output_signals_redaction.py`. W12-1
  unblocked.
- ~~**`[FOLLOWUP w12-promoted-attempt-coverage-erasure]`**~~ —
  **landed `2026-05-07` on `week12` in commit `422a647`.**
  `_derive_runtime_attempted_capabilities` in
  `executor/flows/playwright/monitor/runtime.py` filtered status to
  `{verified, attempted_only, failed}`. After
  `reconcile_event_attempts` (`health/reconciliation.py:187,219`)
  promoted an attempt to `activation_seen` or `target_log_seen` (target
  reacted but full verification did not close), `report_assembler.py:128`
  overwrote `attempted_capabilities` from the runtime view, erasing the
  promoted capability and surfacing `not_attempted` in
  `coverage_summary` despite the target reacting. Routed the filter
  through `RUNTIME_EVIDENCE_STATES` (single source of truth in
  `packages/analysis_contracts/report_invariants.py`) so promoted
  states count as runtime evidence here, matching the contract
  invariant `_attempt_has_runtime_evidence` and the W10-6 docstring.
  Two regression cases under
  `tests/executor/test_playwright_monitor_attribution.py`
  (`test_runtime_attempted_includes_{activation_seen,target_log_seen}_promotion`).
- ~~**`[FOLLOWUP w12-legacy-strategy-outcomes-migration]`**~~ —
  **landed `2026-05-07` on `week12` in commit `ba1accb`.**
  W12-2 P3 (`0981e92`) renamed
  `activation_discovery_strategies: list[str]` →
  `activation_discovery_strategy_outcomes: dict[str, str]` under the
  same `schema_version: "2.1"`. `StrictContractModel(extra="forbid")`
  rejected every 2.1 report persisted in the W11-3 .. W12-2 P3 window
  with `extra_forbidden`, breaking the activation-report API
  (`workflows/activation_reports/router.py:122`) and the marketplace
  ingest path (`workflows/marketplace/analysis_reports.py:52,121`).
  Added `_migrate_legacy_strategy_outcomes` before-validator on
  `ActivationReport`: drops the legacy field and synthesizes the new
  dict, mapping each id → `"succeeded_with_new_activations"` (the
  legacy list semantics). 3 regression cases under
  `tests/platform/contracts/test_activation_discovery_strategies.py`;
  on-disk pre-rename report `c20ac6f91d4a.json` re-ingests cleanly.
- ~~**`[FOLLOWUP w8-6-output-signal-channel-summary-redaction]`**~~ —
  **W12-0 dolgusu landed `2026-05-07` on `week12` in commit `b642af7`.**
  `OutputSignalEvent.channel` ve `OutputSignalEvent.summary` hem
  harness-marker (`signals/output.py:~116`) hem de file-backed
  (`signals/output.py:~180`) source'larda
  `redact_secrets(_truncate(...))` pipeline'ından geçiyor; `summary`
  alan değeri `f"OutputChannel({channel}) appendLine"` olduğu için
  redact'lı channel'ı otomatik miras alır. Adversarial extension
  `vscode.window.createOutputChannel("AKIA...")` çağırarak persisted
  ActivationReport'a secret sızdıramıyor. 7 yeni regression case'i
  (4 harness-marker + 2 file-backed + 1 benign-channel guard)
  `tests/platform/security/test_output_signals_redaction.py`'ye
  eklendi. W12-3 unblocked.
- ~~**`[FOLLOWUP w12-0-output-signal-multiline-secret-redaction]`**~~ —
  **CLOSED `2026-05-08`** on `week12`. Fix:
  `packages/analysis_contracts/evidence.py`'ye `redact_multiline_secrets`
  helper'ı eklendi (sadece `_CROSS_LINE_CLASSES = {"private_key"}`
  pattern'lerini uygular); `signals/output.py` her iki yolda
  (`read_output_channel_logs` + `parse_output_signal_events`)
  `splitlines()` öncesi pre-pass olarak çağırıyor. Single-line pattern'lar
  per-marker `redact_secrets`'ta kaldı çünkü whole-input uygulamak JSON
  marker yapısını bozar (api_key opsiyonel trailing-quote tüketimi
  kapatan `"`'yu yutar). 4 yeni regression
  `tests/platform/security/test_output_signals_redaction.py`'ye eklendi
  (file-backed multi-line PEM block, file-backed PEM with surrounding
  diagnostic lines, harness-marker cross-marker PEM, harness-marker
  single-marker embedded-newline PEM). Existing 20 case'in tamamı
  regression'sız.
- ~~**`[FOLLOWUP api-docker-base-image-digest-pin]`**~~ —
  **CLOSED `2026-05-09` on `week12`.** `docker/api/Dockerfile:2`
  artık `FROM python:3.11-slim-bookworm@sha256:cd67330292a51e2963156f74ff340455d66b2172e9190e99f40dff9357471177`
  formunda.
  `executor/container/Dockerfile:8` ise
  `FROM ubuntu:22.04@sha256:962f6cadeae0ea6284001009daa4cc9a8c37e75d1f5191cf0eb83fe565b63dd7`
  ile pinned. ADR 0002 §4 trust table (`documents/adrs/0002-threat-model.md:97`)
  her base image için `FROM image@sha256:...` zorunluyor. Fix landed:
  `docker buildx imagetools inspect python:3.11-slim-bookworm` ile
  manifest-list digest doğrulandı; yeni
  `tests/architecture/test_dockerfile_digest_pin.py` gate'i `docker/`
  ve `executor/container/` altındaki her `Dockerfile` `FROM` satırını
  `@sha256:` için tarıyor (`scratch` hariç). Focused validation:
  `pytest tests/architecture/test_dockerfile_digest_pin.py` yeşil.
  Yeni dependency yok. Lane: `[platform-storage]`.
- ~~**`[FOLLOWUP ui-docker-base-image-digest-pin]`**~~ — **CLOSED
  `2026-05-10`** on `week12` in commit `a27eb84`. `ui/Dockerfile` stages
  `node:20-alpine` and `nginx:1.27-alpine` now pinned by manifest-list
  digest (`@sha256:fb4cd1...` / `@sha256:65645c...`);
  `tests/architecture/test_dockerfile_digest_pin.py::DOCKERFILE_ROOTS`
  extended with `ROOT / "ui"`. ADR 0002 §4 trust table now 100% closed
  (3/3 runtime images). Lane: `[ui]` `[docs-maintenance]`.
- ~~**`[FOLLOWUP marketplace-installer-tail-multiline-redaction]`**~~ —
  **CLOSED `2026-05-09` on `week12`.** Surfaced `2026-05-09` audit pass
  (Codex review). `workflows/marketplace/analysis_execution.py:80`
  installer failure helper sırası **slice → redact** idi:
  `tail = redact_secrets(output[-500:].strip())`. Single-line token'larda
  çalışıyordu ama multi-line `private_key` PEM bloku 500 karakterlik
  pencereyi bölünce (veya pencere içinde BEGIN/END eşleşmesini parçalarsa)
  `redact_secrets` pattern'i tüm bloku göremiyordu — W12-0 öncesi
  `signals/output.py`'da kapatılan **tam paralel** bypass. W12-0 fix
  (`[FOLLOWUP w12-0-output-signal-multiline-secret-redaction]`,
  `2026-05-08`) `redact_multiline_secrets` pre-pass desenini kurdu;
  bu callsite artık aynı desene migrate edildi: önce
  `redact_multiline_secrets(output)` whole-content pre-pass, sonra
  tail (`output[-500:]`), sonra existing `redact_secrets(...)`
  per-tail. Mantık `executor/flows/playwright/report_builder.py`'daki
  W11-6 "trim → expand → redact" desenine paralel olur. Tests:
  `tests/platform/security/test_output_signals_redaction.py`
  `::test_install_failure_message_redacts_multiline_pem_split_by_tail`
  cross-boundary 500-char split case'i pinliyor; existing DB URL ve
  benign tail regressions yeşil kaldı. Yeni bağımlılık yok. Severity:
  Medium (closed). Lane:
  `[marketplace-analysis]` `[security-detection]`.

## W12 Acceptance Items

- ~~**`[FOLLOWUP w12-attribution-naming-overlap]`**~~ — closed
  `2026-05-07` in commit `0cef876` (W12-2 Commit 2). Rename:
  `background_activation_count` → `target_background_activation_count`;
  `competing_candidate_count` → `competing_extension_event_count`. UI
  contract + adapter + view-model + fixtures updated.
- ~~**`[FOLLOWUP w12-precursor-tests-attribution-links]`**~~ — closed
  `2026-05-07` in commit `5ae0d32`; 26 link-helper cases landed.
- ~~**`[FOLLOWUP w12-precursor-tests-attribution-events]`**~~ — closed
  `2026-05-07` in commit `5ae0d32`; 34 event-helper cases landed.
- ~~**`[FOLLOWUP w12-extension-host-split-scoping]`**~~ — closed
  `2026-05-10` in commit `377f0d5` (W12-5 ahtapot split).
  `runtime_capture/extension_host.py` 679 LoC → 87 LoC thin
  facade + 3 focused modules (`extension_host_log_parse.py`,
  `extension_host_strace_parse.py`, `extension_host_capture.py`).
  Two new architecture gates pin the facade invariant
  (AST shape + re-export identity).
- ~~**`[FOLLOWUP coverage-summary-attempted-drift]`**~~ — closed
  `2026-05-07` in commit `9ebc5b5` (W12-2 Commit 3). The assembler
  collapses planner-seeded `attempted_capabilities` and
  `heuristic_attempted_capabilities` to the runtime-derived
  `event_attempts` view before coverage reconcile, so top-level report
  fields and `coverage_summary["attempted_capabilities"]` resolve to
  one value.
- ~~**`[FOLLOWUP activation-discovery-strategy-outcome-detail]`**~~ —
  closed `2026-05-07` in commit `0981e92` (W12-2 Commit 4, P3). Field
  upgraded from `activation_discovery_strategies: list[str]` to
  `activation_discovery_strategy_outcomes: dict[str, str]` with outcome
  literals `succeeded_with_new_activations` /
  `succeeded_no_new_activations` / `failed:<ExcClassName>`.

## Open Items By Area

### Workflow / Platform

- **`[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread`**
  — move sandbox reset out of the daemon heartbeat thread.
- **`[FOLLOWUP simulation-progress-cancel] dedupe-step-progress-schemas`**
  — reconcile `AnalysisJobStepProgress` vs `AnalyzeJobStepProgress`.
- **`[FOLLOWUP simulation-progress-cancel] is-job-cancelled-session-churn`**
  — revisit fresh DB session polling if profiling shows pressure.
- **`[FOLLOWUP simulation-progress-cancel] heartbeat-refactor`** — extract
  heartbeat polling/JSON/cancel logic into a testable helper.
- **`analysis_service._open_job_session`** — move `SessionLocal` import
  back to module top once the startup-cycle constraint is gone.
- **`run_analysis_job` exception narrowing** — replace broad handling with
  enumerated error paths where possible.
- **`[FOLLOWUP analysis-thread-supervisor]`** — keep daemon-job rows from
  sticking in `running` on unenumerated `BaseException`.
- **`[FOLLOWUP sqlalchemy-error-subtype-logging]`** — distinguish
  `IntegrityError`, `OperationalError`, and `ProgrammingError` for triage.
- **`search_marketplace` return typing** — tighten public return shape.
- **Domain service pattern expansion** — pull remaining router surfaces into
  the established domain-service shape.
- **Migration hardening** — `make migrate` destructive-op precheck plus
  Alembic reversibility audit.
- **`[FOLLOWUP job-service-typevar-audit]`** — keep or remove the generic
  `_run_in_session()` typevar based on mypy/readability value.
- **`[FOLLOWUP w11-8-companion-workflow-orm-bleed]`** — decide DTO
  migration vs documented boundary exception for workflow return types that
  expose storage ORM models.
- ~~**`[FOLLOWUP security-settings-commit-ownership]`**~~ —
  **CLOSED `2026-05-09` on `week12`.** Surfaced `2026-05-09` audit pass
  (Codex review).
  `workflows/security_settings/service.py:84-85` `save_vsix_thresholds()`
  CRUD facade üzerinden `upsert_operator_settings_bulk(db, ...)` çağırıp
  ardından kendisi `db.commit()` yapıyor; AGENTS.md rule 2'nin "write
  logic CRUD'da" zorunluluğu **ihlal edilmiyor** (write logic
  `appcore/storage/crud_ops/operator_settings.py:65-77`'de kalmaya
  devam ediyor) ama transaction boundary workflow tarafında. Mevcut
  storage deseninde commit ownership genelde CRUD/job lifecycle
  tarafında (`crud_ops/analysis_jobs/lifecycle.py` örüntüsü).
  Bugün küçük yüzey; settings alanı büyürse workflow service
  transaction ownership almaya başlar ve "DB write/commit nerede
  yapılır?" sınırı bulanıklaşırdı. Fix landed: yeni
  `appcore.storage.crud_ops.operator_settings.upsert_operator_settings_bulk_and_commit`
  helper'ı transaction boundary'yi CRUD tarafına aldı; workflow service
  artık commit çağırmıyor. SQLAlchemy hata yolunda rollback helper içinde.
  Generic framework / unit-of-work / repository abstraction eklenmedi.
  Existing `tests/workflows/security_settings/test_router.py` 6/6 yeşil.
  Severity: Medium-Low (closed). Lane: `[platform-storage]`.
- **`[FOLLOWUP w8-1-vsix-rejection-log-sanitization]`** — P2; sanitize
  attacker-controlled VSIX entry names before rejection logging.
  Co-tenant of `[FOLLOWUP w8-1-extract-rejection-logging]` (same call
  sites in `workflows/marketplace/client.py`); land jointly in one PR
  to avoid double-touch.

### Executor / Capture

- **T2/T3 live-security plumbing** — harden `make test-security-live`
  around real T2/T3 engagements.
- ~~**`[FOLLOWUP w11-precursor-tests]`**~~ — landed `2026-05-04`.
- ~~**`[BUG silent-scenario-dropout-regression]`**~~ — closed
  `2026-05-07`; last-mile conservation guard reports
  `unaccounted_dropout`.
- **`[BUG scenario-dropout-upstream-root-cause]`** — trace the planner /
  `stimulus_passes` / harness dispatch gap that still drops requested
  scenarios before they reach `ScenarioAccountant`.
- **`[FOLLOWUP monitor-types-property-recomputation]`** — P3; defer until
  profiling shows repeated expensive property access.
- **`[FOLLOWUP scenario-accountant-conservation-split]`** — W13-X.
  `executor/flows/playwright/monitor/scenario_accountant.py` 648 LoC
  (W11 close baseline ~426; +222 LoC drift since W11). Tek collaborator
  scenario lifecycle, event-attempt mutation, scenario conservation,
  activation-log derivation, ve intermediate-state emission'ı taşıyor.
  Hard-rule ihlali değil ama activation debug'ı sırasında en zor
  okunan dosyalardan biri olmaya aday — W12-4 runner split'inden sonra
  executor runtime'daki bir sonraki readability hotspot. W11-1 lifecycle
  split pattern'ini örnek al: önce precursor tests ekle, sonra
  conservation/verification helper'ları ile timeline/intermediate-emission
  helper'larını ayrı modüllere taşı; ana sınıf scenario mutation
  orchestration'ını tutmaya devam etsin. Davranış değişikliği olmamalı,
  generic framework / event bus / plugin abstraction eklenmeyecek.
  W12-4 ve W12-5 ile karıştırma. Severity: Medium. Lane:
  `[executor-runtime]`.
- **`[FOLLOWUP execute-attempt-rebloat-watch]`** — **W13-X watching
  item, refactor önerisi YOK.** Surfaced `2026-05-10` Codex audit pass.
  `executor/flows/playwright/stimulus/attempts.py::execute_attempt`
  bugün branch zinciri sayısı kabul edilebilir; yeni action family
  eklenecekse explicit helper extraction yap (W11-1 lifecycle split
  pattern: precursor tests → küçük helper'lar). Bugün split önerisi
  YOK; sadece her yeni action family commit'inde LoC + cyclomatic
  ratchet kontrolü. Generic framework, action registry, plugin
  abstraction eklenmeyecek. Severity: Low. Lane: `[executor-runtime]`.
- **`[FOLLOWUP dispatch-execution-rebloat-watch]`** — **W13-X watching
  item, refactor önerisi YOK.** Surfaced `2026-05-10` Codex audit pass.
  W12-4 sonrası `executor/flows/playwright/entrypoint/dispatch.py`
  402 LoC; `dispatch_execution()` 6-way mode dispatch'i tek yerde
  topluyor. `runner.py::main` 99 LoC budget altına çekildiği için
  yeni execution mode eklenmesi muhtemelen burayı şişirir. Bugün
  hard-rule ihlali değil; `tests/architecture/
  test_runner_main_loc_budget.py` paterninde benzer bir
  `test_dispatch_execution_under_loc_budget` ratchet **eklemekten
  önce** somut bir şişme görmeyi bekle. Yeni mode/branch eklenirse
  helper extraction (`_dispatch_demo`, `_dispatch_layered_passes`
  vs.) yap. Generic framework / strategy registry eklenmeyecek.
  Severity: Low. Lane: `[executor-runtime]`.
- **`[FOLLOWUP attribution-links-build-evidence-bundle-density]`** —
  **W13-X watching item, refactor önerisi YOK.** Surfaced `2026-05-09`
  audit pass (Codex review). `executor/flows/playwright/attribution/links.py`
  601 LoC; `build_evidence_bundle()` (girişi `links.py:32` civarı)
  birden çok `EvidenceEvent.kind` / `raw_context.event_class` varyantı
  ve link üretim mantığını tek yerde topluyor. W12-3 ile `RawContext`
  union 7 varyanta genişledi; yeni event kind eklendiğinde bu
  fonksiyonun değiştirilmesi kırılganlığı artırır. Bugün güvenlik
  açığı veya hard-rule ihlali değil — okunabilirlik watching'i.
  W12-4 / W12-5 bittikten sonra (en erken W13), küçük explicit helper
  fonksiyonlarına bölünebilir: network/file/process/output/scenario
  event builder'ları gibi. Generic framework, registry pattern,
  abstract factory, plugin abstraction eklenmeyecek; precursor tests
  (`tests/executor/test_playwright_attribution_links.py` 26 cases)
  zaten safety net olarak yerinde, bunlar split sonrası
  bitwise-equal görsel için kullanılabilir.
  `[FOLLOWUP evidence-event-kind-raw-context-invariant]` (W13-X)
  ile kardeş — kind↔event_class invariant'ı landlandığında bu
  fonksiyon zaten daha sıkı tip almış olur, split kararı ona göre
  yeniden değerlendirilir. Severity: Medium-Low. Lane:
  `[executor-runtime]`.

### Detection / Contracts

- ~~**`[FOLLOWUP report-invariants-runtime-evidence-drift]`**~~ — closed
  by W10-6.
- ~~**`[FOLLOWUP planner-executor-action-enum]`**~~ — closed by W10-5.
- ~~**`[FOLLOWUP w8-6-output-signals-redaction]`**~~ — parent closed by
  W10-7 for the harness-marker path; file-backed sibling closed by
  W12-0 (`22eb836`, `2026-05-07`).
- **`[FOLLOWUP signal-summary-needs-review-categories]`** — refine
  category labels for review-oriented verdicts.
- ~~**`[FOLLOWUP target-log-lifecycle-instrumentation]`**~~ — landed with
  W11-4.
- ~~**`[FOLLOWUP w8-6-extension-host-output-redaction]`**~~ — landed with
  the W11 companion.
- **`[FOLLOWUP event-attempt-verification-status-validator]`** — prevent
  drift in runtime-evidence state vocabulary.
- **`[FOLLOWUP compute-verdict-table-driven-test]`** — add table-driven
  coverage for verdict computation.
- **A5/A7 adversary fixtures and allow-list artifacts** — keep deferred
  until the relevant security window.
- **`[FOLLOWUP evidence-event-kind-raw-context-invariant]`** — W13-X.
  `EvidenceEvent.kind: str` ile `raw_context.event_class` literal'i
  arasında pairing validator yok (`packages/analysis_contracts/contracts.py:242,266`);
  Pydantic `kind="network"` + `event_class="file"` kombinasyonunu
  reddetmez. `packages/analysis_engine/rules/_common.py:37-50` accessor'ları
  (`event_type`, `event_method`, `event_message`) `getattr(event.raw_context,
  "...", "")` defensive fallback'larıyla bu boşluğu kapatıyor — yani
  invariant olmadığı için detection helper'ları savunmacı kalmak zorunda.
  Eski rapor migrasyonları, UI adapter fallback'leri veya elle üretilen
  fixture'lar yanlış kombinasyonları sessizce taşıyabilir. Fix: Pydantic
  v2 `model_validator(mode="after")` ekle, kabul edilen mapping'i açıkça
  pinle (`network`→`NetworkRawContext`, `file`→`FileRawContext`,
  `process`→`ProcessRawContext`, `scenario`→`ScenarioRawContext`,
  `activation`→`ActivationRawContext`, `ui_blocker`→`UiBlockerRawContext`,
  `output_channel_appendline`→`OutputChannelRawContext`); legacy summary
  kind'lar intentional olarak farklı context kullanıyorsa explicit
  allow-list. Test:
  `tests/platform/contracts/test_raw_context_discriminated.py::test_evidence_event_rejects_kind_event_class_mismatch`.
  Mevcut canonical reports bozulmamalı. Severity: Medium. Lane:
  `[security-detection]`.
- **`[FOLLOWUP planner-selection-readability-audit]`** — W13-X
  watching item (refactor önerisi YOK).
  `packages/analysis_planner/selection.py` 497 LoC; üç nested closure-based
  dispatch fazı (`_apply_activation_event`, `_apply_contributes_metadata`,
  `_apply_default_fallback`) + mutation-heavy captured callback'lar
  (`mark_scenario`, `register_attempt`). Bugün tek-pas planner fazı
  olarak okunuyor — strategy registry / plugin abstraction değil.
  Sadece yeni activation family eklendiğinde veya planner bug'ı
  çıktığında ele al; küçük helper fonksiyonlar veya veri tabloları
  kullanılabilir. Generic framework, event bus, abstract factory, DI
  container, plugin registry eklenmeyecek. Planner behavior
  değişmemeli; selection output fixture/testleri korunmalı; yeni mimari
  katman yaratılmamalı. Severity: Low. Lane: `[security-detection]`.

### UI

- ~~**`[CLEANUP ui-v3-9]`**~~ and ~~**`[CLEANUP ui-v3-14]`**~~ — closed.
- **`[FOLLOWUP ui-supplemental-types-retire]`** — retire supplemental UI
  type shims once generated contracts fully cover them.
- **`[FOLLOWUP ui-raw-context-discriminator-parity]`** — W13-X.
  Backend `RawContext`'i strict discriminated union
  (`packages/analysis_contracts/evidence.py:183-191`,
  `Field(discriminator="event_class")` + variant başına `Literal[...]`).
  Generated TS contracts (`ui/src/lib/types/contracts.ts:293-350`)
  ise 7 varyantın hepsinde `event_class?: string;` (optional + wide
  string) — generator literal'ı düz string'e indiriyor, discriminator
  parity yok. Ek olarak `ui/src/lib/adapters/report.ts:247,278,318,344,366`
  legacy fallback fonksiyonları (`fromActivation`, `fromNetwork`,
  `fromFile`, `fromProcess`, `fromScenario`) `raw_context` literal'ı
  kuruyor ama hiçbiri `event_class` set etmiyor — bu objeler backend'in
  strict validator'ından geçemezdi, sadece UI-only oldukları için
  hayatta kalıyorlar. Backend W12-3 ile strict olmuşken frontend
  contract bu disiplini yansıtmıyor; ileride typed UI rendering veya
  filtering eklenirse yanlış event sınıfları sessizce kabul edilir.
  Fix: (a) `scripts/generate_ui_contracts.py`'yi her variant için
  `event_class: "network"` (vb.) literal üretecek şekilde güncelle;
  (b) 5 fallback fonksiyonuna kind ↔ event_class eşleştirmesini ekle.
  Tests: `ui/src/lib/adapters/report.test.ts::preserves_raw_context_event_class_for_legacy_fallback_events`
  - generated contract output'unda discriminator literal golden/text
  assertion. Severity: Medium. Lane: `[ui]`.
- ~~**`[FOLLOWUP vsix-threshold-dto-generator-coverage]`**~~ —
  **CLOSED `2026-05-09` on `week12`.** Surfaced `2026-05-09` audit pass
  (Codex review).
  `ui/src/lib/types/contracts.ts:1-2` "Generated by
  scripts/generate_ui_contracts.py. Do not edit this file manually."
  diyor; ama satır 560-593 arasında `VsixThresholdBoundsDto`,
  `VsixThresholdsResponseDto`, `VsixThresholdsUpdateRequestDto`,
  `VsixThresholdBreachDetail` blokları **manuel** eklenmiş — yorumda
  "Mirrors `workflows.security_settings.router.ThresholdsResponse`"
  notu var. `scripts/generate_ui_contracts.py:24-59` `TARGET_SCHEMAS`
  listesinde bu 4 isim **yok**, yani backend Pydantic kaynağından
  render edilmiyor; bir sonraki `python scripts/generate_ui_contracts.py`
  çalışması bu blokları silebilir veya backend↔UI drift sessizce
  biriktirebilirdi. Fix landed: security threshold request/response
  schemas `appcore/contracts/schema_defs/security_settings.py` altına
  taşındı; structured breach detail `VsixThresholdBreachDetail`
  backend-owned Pydantic model oldu; `scripts/generate_ui_contracts.py`
  `TARGET_SCHEMAS` + `NAME_OVERRIDES` bu tipleri üretiyor; manual block
  `contracts.ts`'den kalktı. `observed_value` integer'a daraltılmadı;
  compression-ratio breach path'i float değerini structured 422 olarak
  koruyor. Regression:
  `tests/scripts/test_generate_ui_contracts.py` target-list ve rendered
  threshold/breach typing'i, `tests/workflows/marketplace/test_router.py`
  ise float `observed_value` path'ini pinliyor; `python scripts/generate_ui_contracts.py --check`
  yeşil. `[FOLLOWUP ui-supplemental-types-retire]` hâlâ açık çünkü diğer
  supplemental UI-only tipler duruyor. Severity: Medium (closed). Lane:
  `[ui]` `[contracts]`.
- ~~**`[FOLLOWUP settings-page-stale-localstorage-copy]`**~~ —
  **CLOSED `2026-05-09` on `week12`.** Surfaced `2026-05-09` audit pass
  (Codex review).
  `ui/src/features/settings/SettingsPage.tsx:150` ve `:454`
  hâlâ "changes are persisted to this browser's localStorage until
  settings API lands" benzeri stale copy taşıyor; aynı sayfada artık
  `2026-05-09` operator-tunable VSIX iterasyonuyla API-backed Security
  threshold formu var (`/api/settings/security/thresholds`). Operatöre
  yanlış mental model veriyor — özellikle threshold ayarlarının kalıcı
  olduğu durumda copy "geçici localStorage" izlenimi bırakıyor.
  Fix landed: Settings header copy artık "General console options stay
  in this browser; security thresholds are persisted by the local API"
  diyor; `SettingsPage.test.tsx` bu copy'yi pinliyor. `[BACKLOG ui-v3-5]`
  partial-close notuyla uyumlu. Severity: Low (closed). Lane: `[ui]`.

### Engineering Quality

- **`[FOLLOWUP ci-reintroduction]`** — restore CI/docs-check after the
  runner-image drift is understood.
- **`[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]`** — W13-X.
  Surfaced `2026-05-10` Codex audit pass. The `tests/architecture/
  test_absolute_binary_paths.py` gate enforces absolute-path discipline
  for direct `subprocess.Popen([...])` calls inside the executor tree,
  but variable-indirect command heads — `["tshark", ...]`,
  `["strace", ...]`, `["inotifywait", ...]` in
  `executor/flows/playwright/runtime_capture/{network.py,
  extension_host_capture.py,filesystem.py}` — bypass it because the
  list literal lives next to the `Popen` call rather than inside it.
  Extend the existing AST gate (do **not** write a new generic scanner)
  so it walks list-literal command heads bound to a `_CMD = [...]`
  local immediately before a `subprocess.Popen` call, or pin the head
  string to an explicit allowlist (`tshark`, `strace`, `inotifywait`,
  `nsenter`) sourced from `executor/binary_paths.py`. Severity: Medium.
  Lane: `[security-detection]`.
- ~~**`[FOLLOWUP arch-gate-network-body-preview-redaction]`**~~ —
  closed `2026-05-10` in commit `9433ee3` (W12-5 companion gate).
  New `tests/architecture/test_network_body_preview_redaction.py`
  walks the AST of every module under `executor/`, `packages/`,
  `workflows/` and fails if any `*_body_preview` assignment is not
  routed through `redact_secrets()` — directly, via
  `_bounded_body_metadata()` output, or as a passthrough from an
  already-redacted source. Teeth verified via mutation test.

### Repo Hygiene

- ~~**`[CLEANUP repo-tracked-scratch-files]`**~~ — landed `2026-05-03`.
- ~~**`[CLEANUP tests-scanner-rename]`**~~ — landed `2026-05-03`.
- **`[CLEANUP report-builder-naming]`** — clarify similarly named report
  builder modules.
- **`[CLEANUP env-example-extrace-vars]`** — align example env names with
  runtime configuration.
- ~~**`[CLEANUP agent-context-phase-snapshot-stale]`**~~ — landed.
- **`[CLEANUP postgres-version-fact-drift]`** — keep documented Postgres
  version aligned with Compose/runtime.
- **`[CLEANUP adr-0007-runbook-wording-drift]`** — keep LAN runbook wording
  synchronized with ADR 0007.
- **`[CLEANUP session-docstring-except-exception]`** — update stale
  docstring language around exception handling.
- **`[CLEANUP uri-validation-stale-sys-path-comment]`** — remove stale
  package-mode comments after W9.
- **`[CLEANUP monitor-runtime-naming-overlap]`** — reduce naming ambiguity
  around monitor runtime modules.
- **`[CLEANUP appcore-config-stale-docstring]`** — replace legacy config
  module wording.
- **`[CLEANUP pre-commit-python-version-alignment]`** — align pre-commit
  Python version with the project/runtime target.
- ~~**`[CLEANUP httpx-runtime-dependency-metadata]`**~~ — verified closed
  `2026-05-06`.
- ~~**`[FOLLOWUP scripts-seed-test-rewrite]`**~~ — closed by file removal.
- ~~**`[FOLLOWUP triggers-private-helper-import]`**~~ — verified resolved.

### Test + Observability

- **`[FOLLOWUP w8-9-network-body-boundary-split-secret-test]`** — P2;
  cover secret patterns split by body-preview truncation.
- **`[FOLLOWUP codex-automation-5]`** — executor runtime fingerprint in
  automation output.
- **`[FOLLOWUP codex-automation-6]`** — UI failure taxonomy.
- **`[FOLLOWUP capability-verification-gap]`** — close remaining debug /
  verification capability gaps.
- **`[FOLLOWUP w8-0-capture-pipeline]`** — preserve capture-pipeline smoke
  coverage beyond the partial W8-0 close.
- ~~**`[FOLLOWUP make-test-security-lane-composition]`**~~ — full close
  recorded after W8 lane composition landed.
- **`[FOLLOWUP w8-4-broader-executor]`** — retire remaining bare-binary
  pragmas when executor helpers move to absolute paths.
- **`[FOLLOWUP w8-1-extract-rejection-logging]`**,
  **`[FOLLOWUP w8-1-archive-count-bypass]`**, and
  **`[FOLLOWUP w8-1-vsix-compressed-size-limit]`** — remaining W8-1 hardening
  and observability follow-ups.
- ~~**`[FOLLOWUP w8-1-vsix-entry-count-limit-realistic]`**~~ —
  closed `2026-05-08` on `week12`. W8-1 baseline `MAX_FILE_COUNT = 2_000`
  was tripped on real users by Microsoft's `2026-05-08` ms-python.python
  release (version `2026.5.2026050801`) — modern Python/Pylance/Jupyter
  bundles ship more entries than the original threshold anticipated.
  Raised to `50_000` in `workflows/marketplace/client.py:37` with inline
  rationale linking the size + ratio guards as the load-bearing
  zip-bomb defense; entry-count remains a complementary DoS guard for
  the extract loop. Existing 7 test_vsix_hardening cases stay
  regression-free (they monkeypatch `MAX_FILE_COUNT` locally, so they
  are decoupled from the constant). Sibling drift surfaced during the
  audit: ADR 0002 references a `§7.2.6` for VSIX extraction guards but
  the section was never authored in the ADR body — captured below.
- **`[FOLLOWUP adr-0002-vsix-extraction-section-missing]`** —
  W8-1 commit `bd9d1f1` referenced ADR 0002 §7.2.6 for adversarial
  VSIX extraction limits, but ADR 0002 only contains §1-6 plus the
  template tail; §7 was never written. Author the missing section
  (zip-bomb defense rationale, file-count complementary guard, current
  thresholds) so the cross-ref in `workflows/marketplace/client.py`
  resolves to actual prose. Lane: `[docs]` `[security-detection]`.
- ~~**`[BACKLOG ui-v3-5]` Settings persistence API**~~ —
  **PARTIALLY CLOSED `2026-05-09`** on `week12`. Backend persistence
  layer landed for the Security/VSIX-hardening section (new
  `operator_settings` table + GET/PUT
  `/api/settings/security/thresholds` + `SecuritySection` form in
  `SettingsPage.tsx`). Other localStorage-backed sections (general,
  executor, telemetry) remain client-only — they retire incrementally
  as their values find a backend consumer. The pre-existing
  `localStorage["extrace-v3-settings"]` legend on the Settings header
  was removed since it no longer accurately describes the whole page.
- **`[FOLLOWUP vsix-integrity-in-activation-report]`** — Stage 9 of
  the 2026-05-09 operator-tunable VSIX hardening iteration was
  deferred to keep that iteration shippable. Carry-over scope: persist
  per-extension VSIX extraction metrics (file_count, uncompressed_size,
  compression_ratio, rejected_entry_count) on the `Extension` entity
  (new alembic migration + 4 nullable columns), wire
  `create_extension_from_directory` to write them, add
  `ActivationReport.vsix_integrity` (additive optional Pydantic model;
  no schema_version bump needed), populate it from Extension at report
  build time (`packages/analysis_engine/runner.py` or
  `executor/.../report_builder.py`), and render a "VSIX Integrity"
  subsection on the Reports overview tab (`ui/src/features/reports/`,
  `ui/src/lib/adapters/report.ts`). Acceptance: Reports page shows
  metrics with green/amber/red coloring keyed off the live thresholds
  (use `apiClient.getSecurityThresholds`); pre-existing fixtures with
  no metrics render as "Metrics unavailable" rather than throwing.
  Stage-9 risk-score visualization flows naturally from this since the
  panel is the report-side mirror of the marketplace post-download
  banner that landed today. Lane: `[ui-v3]` `[security-detection]`
  `[contracts]`.
- **`[FOLLOWUP vsix-thresholds-extra-keys]`** — the
  `operator_settings` table is generic key/value but the W12-* PUT
  endpoint only accepts the three VSIX threshold keys. Future
  operator-tunable values (jobTimeout, retention windows, telemetry
  buffers) should land on the same table; pull in their existing
  localStorage defaults from `SettingsPage.DEFAULT_SETTINGS` when the
  first one needs cross-device sync. Lane: `[settings]`.
- **`[FOLLOWUP w8-3-harness-js-scheme]`** — extend URI trigger hardening.
- ~~**`[FOLLOWUP w8-5-list-endpoint-name-filter]`**~~ — closed
  `2026-04-30`.
- **`[FOLLOWUP w8-6-content-sample-structural-test]`** — broader
  structural enforcement for content-sample redaction.
- **`[FOLLOWUP w8-8-manifest-emit-when-needed]`** — deferred until the
  first manifest-field log emit site or proactive security gate.
- ~~**`[FOLLOWUP arch-gate-no-bare-except]`**~~ — landed.
- **`[FOLLOWUP w8-8-trigger-sweep-as-test]`** — convert W8-8 trigger sweep
  into test coverage when W8-8 lands.
- **`[FOLLOWUP arch-gate-executor-control-outbound]`** — gate outbound
  executor-control boundaries.
- **`[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]`** — ratchet bare
  binary path pragmas as W8-4 follow-ups land.

## How To Pull An Item Back

1. Search by stable ID in this file and the latest full archive snapshot.
2. Confirm code/tests still match the recorded premise.
3. Add or update tests first when the item describes a regression risk.
4. Close by preserving the stable ID and adding the landing date/commit.
