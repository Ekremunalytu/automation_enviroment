# Refactor Status

`Last Updated: 2026-05-10 (W12 closed; post-Codex-fix make check-all green; week12 → main PR pending)`

Active status board for current closure state. **Slim canonical** — full
phase history and verbose evidence are frozen under dated snapshots:

- latest full snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-05-07.md`](archive/status/REFACTOR_STATUS_full_2026-05-07.md)
- older W4-W8 snapshot:
  [`archive/status/REFACTOR_STATUS_full_2026-04-29.md`](archive/status/REFACTOR_STATUS_full_2026-04-29.md)

## Current State

- **W0-W7 closed `2026-04-23`** — PoC acceptance bar 11/11 green
  (`REFACTOR_OPTIMIZATION.md` §10.7).
- **PR345 target activation lifecycle closed `2026-04-27`** — PRs 1-5
  plus ADR 0006 landed; W8-0 deterministic harness readiness also landed
  `2026-04-27`.
- **W8 closed for active work `2026-04-29`** — W8-1..W8-7 and W8-9
  landed. W8-8 manifest log sanitization is deferred, not abandoned,
  under `[FOLLOWUP w8-8-manifest-emit-when-needed]`.
- **W9 closed `2026-05-04` via PR #9 (`d67944d`)** — ADR 0008 container
  package-mode invocation is Accepted; dual-import fallback and runtime
  `sys.path.insert` debt removed; `signal_policy.py` moved to
  `packages/analysis_engine/signals/policy.py`.
- **W10 closed `2026-05-04` via PR #11 (`25e4c16`)** — contract hygiene
  and planner cleanup landed (`schema_version`, `_TriggerPayloadDraft`
  removal, registry split, automation health typing, executor action enum,
  runtime-evidence alignment, output signal redaction parent).
- **W11 closed `2026-05-05` and merged via PR #14 (`50ca69e`)** — all
  eight §11.8 scope items landed: monitor split W11-1..W11-6,
  workflow-side ahtapot closure W11-7, storage-side ahtapot closure
  W11-8, plus the bundled W11 acceptance sub-tasks.
- **W12 closed `2026-05-10` — executor subpackaging + attribution cleanup.**
  All five W12-N work items landed (W12-0..W12-5) plus UI Dockerfile
  digest pin, W12 close-out test coverage, and Codex audit CRITICAL
  fix (`executor/host.py` retry/reload subprocess-output redaction).
  Live-scan bitwise-equal validation completed; post-Codex-fix
  `make check-all` green: `make test-local` 1452 passed / 6 skipped /
  6 deselected / 75 warnings; `make test-security` 211 passed / 32
  warnings; `tests/architecture/` 76 passed / 2 deselected.
  `week12 → main` PR pending. Tracker:
  [`active-work/W12-executor-subpackaging.md`](active-work/W12-executor-subpackaging.md)
  (frozen post-close); acceptance bar:
  [`active-work/W12-close-acceptance.md`](active-work/W12-close-acceptance.md)
  (to be moved to archive at merge).
- **Active phase: W13 — Test Expansion + Observability.** Entry
  baseline established `2026-05-10` (`make check-all` green at the
  W12 close commit; W12 architecture ratchet gates inventoried in
  `REFACTOR_OPTIMIZATION.md` §11.10). W13 lane document
  (`active-work/W13-test-expansion-observability.md`) opens with the
  post-merge cleanup PR per W11/W12 precedent (tracker is born at
  phase entry, not preemptively).

## W12 Entry Snapshot

- W11 closed: **met** (`2026-05-05`, PR #14).
- W11 precursor tests: **met** (`2026-05-04`).
- W12 attribution precursor tests: **met** (`2026-05-07`, commit
  `5ae0d32`; 26 link-helper cases + 34 event-helper cases).
- §11.9.1 runtime-capture split scoping: **met** (PR #15, no code
  change).
- W12-0 security pull-forward:
  **landed** `2026-05-07` on `week12` in commit `22eb836`.
  `[FOLLOWUP w8-6-output-signals-file-backed-redaction]` closed; W12-1
  unblocked.
- W12-1 executor subpackaging:
  **landed** `2026-05-07` on `week12` in commits `b4bd3ee` +
  `0eb072e` + `0e74beb` + `95a409f`. 54 flat playwright files →
  ≤10 flat + 7 new subpackages (monitor/, stimulus/, workspace/,
  health/, entrypoint/, vscode/, signals/) plus existing
  attribution/ + scenarios/ + runtime_capture/ (10 package dirs
  total). Architecture gates now cover flat-count, import-cycle, and
  `python -m` package-shim invariants.
- W12-2 attribution facade cleanup:
  **landed** `2026-05-07` on `week12` in commits `37fcaad` +
  `0cef876` + `9ebc5b5` + `0981e92`. 29 underscore re-exports → 10
  public names; three companion follow-ups closed (naming-overlap
  rename, coverage-summary unify, P3 strategy-outcome dict).
- W12-3 raw_context discriminated union typing:
  **landed** `2026-05-07` on `week12`. `EvidenceEvent.raw_context:
  dict[str, Any]` → `RawContext` Pydantic discriminated union under
  `Field(discriminator="event_class")` covering all 7 producer kinds
  (3 named in §11.9 + 4 extra surfaced post-W7+W11 consolidation).
  `_PENDING_MIGRATION` raw_context entry purged; W12 close exit
  criterion bullet 4 cleared. Incidental fix:
  `_common.py::event_method` now reads `http_method` (pre-existing
  latent key mismatch).
- Pre-W12-4 API Docker base image digest pin:
  **landed** `2026-05-09` on `week12`. `docker/api/Dockerfile` now pins
  `python:3.11-slim-bookworm` by manifest-list digest, matching ADR 0002
  and the already-pinned executor container. New architecture gate:
  `tests/architecture/test_dockerfile_digest_pin.py`.
- Marketplace installer-tail multiline redaction:
  **landed** `2026-05-09` on `week12`. `install_failure_message()` now
  applies `redact_multiline_secrets(output)` before the 500-char tail,
  so orphaned PEM body lines cannot survive when the tail boundary splits
  a private-key span. Regression:
  `test_install_failure_message_redacts_multiline_pem_split_by_tail`.
- UI contract drift cleanup:
  **landed** `2026-05-09` on `week12`. VSIX threshold DTOs and structured
  breach detail now come from backend-owned Pydantic schemas through
  `scripts/generate_ui_contracts.py`; Settings header copy now distinguishes
  browser-local general preferences from API-persisted Security thresholds.
  Structured breach detail preserves compression-ratio float
  `observed_value` values instead of narrowing them to integers.
- Security-settings commit ownership cleanup:
  **landed** `2026-05-09` on `week12`. Operator-settings transaction
  commit moved into the CRUD facade helper, leaving
  `workflows/security_settings/service.py` as validation/default merge
  orchestration only.
- Baseline fixture drift cleanup:
  **landed** `2026-05-09` on `week12`. The platform baseline fixture
  contract now points at the locally complete
  `ms-python.python@2026.5.2026050801` artifact instead of the stale
  partial `2026.5.2026032701` directory, restoring the no-network
  local-artifact guarantee in `test_analysis_fixture_baselines.py`.
- W12-4 entrypoint dispatch extraction:
  **landed** `2026-05-10` on `week12`.
  `executor/flows/playwright/entrypoint/runner.py::main` 324 LoC →
  99 LoC (limit ≤200). New `entrypoint/dispatch.py` (402 LoC) owns
  the 6-way execution mode dispatch, monitor setup, page-callback
  factory, extra-trigger application, skipped-scenario summary, and
  monitor finalize sequence. `runner.py` total 494 → 196 LoC. Two new
  architecture gates pin the readability ratchet:
  `tests/architecture/test_runner_main_loc_budget.py::test_runner_main_under_loc_budget`
  (AST gate, ≤200 LoC) and `::test_runner_main_dispatch_helpers_remain_imported`.
  W12 close exit criterion bullet 5 cleared.
- W12-5 extension_host ahtapot split + body-preview redaction gate:
  **landed** `2026-05-10` on `week12`.
  `executor/flows/playwright/runtime_capture/extension_host.py`
  679 LoC → 87 LoC thin facade + 3 focused modules
  (`extension_host_log_parse.py` 329, `extension_host_strace_parse.py` 106,
  `extension_host_capture.py` 264). Pattern follows W11-7 and W11-8
  (verbatim relocation, `from .X import Y as Y` + `__all__`, no
  generic frameworks). Two new architecture gates pin the facade
  invariant:
  `tests/architecture/test_import_graph.py::test_runtime_capture_extension_host_stays_a_thin_facade`
  (AST shape) and
  `::test_runtime_capture_extension_host_reexports_match_canonical_modules`
  (identity check across `__all__`). A third gate
  `tests/architecture/test_network_body_preview_redaction.py::test_body_preview_assignments_are_redacted`
  enforces that every `*_body_preview` assignment under
  `executor/`, `packages/`, or `workflows/` routes through
  `redact_secrets()`; teeth verified via mutation. Closes
  `[FOLLOWUP w12-extension-host-split-scoping]` and
  `[FOLLOWUP arch-gate-network-body-preview-redaction]`.
  **Live-scan bitwise-equal validation completed `2026-05-10`** on
  `ms-python.python@2026.5.2026050801`: 17/17 detection-relevant
  fields identical pre/post W12-5 (job IDs
  `6fab298e81a14bf8a7a557a13953e57b` /
  `e5e33ec6e34f4993b795664d83e25fd4`; full evidence in
  `documents/active-work/W12-close-acceptance.md` §3.4).
- **UI Dockerfile base-image digest pin (W12-close item)**
  landed `2026-05-10`. `ui/Dockerfile` `node:20-alpine` and
  `nginx:1.27-alpine` stages now pinned by manifest-list digest
  (`@sha256:fb4cd1...` / `@sha256:65645c...`);
  `tests/architecture/test_dockerfile_digest_pin.py` extended so
  `DOCKERFILE_ROOTS` covers `ui/` alongside `docker/` and
  `executor/container/`. ADR 0002 §4 trust table now 100% (3/3
  runtime images).
- **W12 close-out test coverage** landed `2026-05-10`. Five
  runtime/integration tests (~14 cases) fill the W12-4/W12-5
  coverage gap left by the AST gates:
  `ExtensionHostFileCapture` start/stop integration (5 cases in a
  new `tests/executor/test_playwright_extension_host_capture.py`),
  strace edge cases + log_parse lazy-resolver invariant (+5 in
  `test_playwright_extension_host.py`), network body-preview
  runtime redaction (5 cases in a new
  `tests/executor/test_network_body_redaction.py`), and the W12-4
  `PageRef` cross-module rebind (+1 in
  `test_playwright_entrypoint.py`).
- Last known broad check bar: `make check-all` ✅ green on
  `2026-05-10` post-Codex-fix re-run (W12 close baseline);
  `make test-local` 1452 passed / 6 skipped / 6 deselected / 75
  warnings (+5 over the W12-close-acceptance dry-run `1447`: 5
  mutation-verified regression cases in
  `tests/security/test_executor_host_error_redaction.py` from the
  Codex audit fix `e42e79c`); `make test-security` 211 passed / 32
  warnings (unchanged); `tests/architecture/` 76 passed / 2
  deselected. Earlier checkpoints: W12 dry-run `1447` (pre-Codex-fix
  re-run), W12-5 close `1430`, W12-4 close `1402`, pre-W12-4
  hardening close `1400`.
- **Codex audit close-out** `2026-05-10` (commit `e42e79c`):
  CRITICAL leak in `executor/host.py` retry-error messages closed
  (`redact_secrets()` wrap; 5 mutation-verified regression cases in
  `tests/security/test_executor_host_error_redaction.py`).
  Post-fix full `make check-all` ✅ green on the W12 close commit
  (postgres_test container active; `1452 passed / 6 skipped / 6
  deselected / 75 warnings`; `211 passed` security; `76 passed / 2
  deselected` architecture).
- Latest focused verification (`2026-05-09`): `make test-security`
  211 passed / 32 warnings; 113 marketplace/security-settings/helper/
  generator/digest tests passed; generated-contract `--check` passed;
  Settings Vitest 4 passed; UI `npm run build` passed with the existing
  large-chunk warning only.

## 2026-05-07 Audit Pass

The audit surfaced six roadmap gaps. The W12-0 pull-forward landed
the same day:

- ~~**P1 / W12-0:** `[FOLLOWUP w8-6-output-signals-file-backed-redaction]`~~
  — closed `2026-05-07` on `week12` (`22eb836`). W10-7 redacted the
  harness-marker output-signal path; W12-0 closes the file-backed
  `read_output_channel_logs` sibling, the primary source on VS Code
  1.105+.
- ~~**P1 / pre-W12-4:** `[FOLLOWUP w12-0-output-signal-multiline-secret-redaction]`~~
  — closed `2026-05-08` on `week12`. New `redact_multiline_secrets`
  helper (cross-line patterns only, currently `private_key`) applied as
  a pre-pass on both `read_output_channel_logs` and
  `parse_output_signal_events` before `splitlines()`. Single-line
  patterns stay per-line/per-marker (whole-input application would
  corrupt JSON marker structure). 4 new regressions; existing 20 case
  regression-free.

The remaining five are tracked in `POST_POC_BACKLOG.md` as P2/P3 work:

- `[FOLLOWUP w8-1-vsix-rejection-log-sanitization]`
- `[FOLLOWUP monitor-types-property-recomputation]`
- `[FOLLOWUP arch-gate-network-body-preview-redaction]`
- `[CLEANUP pre-commit-python-version-alignment]`
- `[FOLLOWUP w8-9-network-body-boundary-split-secret-test]`

## Current Deferrals

- W8-8 manifest field log sanitization reopens on the first real
  manifest-field log emit site or an explicit proactive security gate.
- `[BUG scenario-dropout-upstream-root-cause]` remains W13-oriented unless
  dropout proves stochastic or misses a live threat category.

## Read Order

When updating this file, keep it as a slim closure board. Put verbose
evidence in `documents/archive/status/`, keep pull-next detail in
`POST_POC_BACKLOG.md`, and keep active W12 mechanics in
`active-work/W12-executor-subpackaging.md`.
