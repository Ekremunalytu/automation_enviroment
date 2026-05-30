# Static Analysis Pre-Check Stream (Active Work Tracker)

`Last Updated: 2026-05-30 — ES-3a in-house static rules MVP (s1/s2/s3) + static runner on branch static.`

`Status: ACTIVE on branch static (single-branch model per user direction 2026-05-29; sub-iter başına ayrı branch yok). Resumed serially from the frozen extrace-static-stream-handoff.md design intent after the extrace-static branch was abandoned 2026-05-28.`

`Branch: static (cut from main; all ES-0..ES-5 sub-iter commits land directly on it). Close-out PR static -> main PENDING USER APPROVAL.`

`Owner: ekrem`

This is the canonical active-work tracker for the Static Analysis
Pre-Check Stream. It fronts the dynamic sandbox with a pre-execution
static stage (block-and-warn) so known-bad extensions are rejected
before any sandbox spin. The four locked design decisions and the
field-level spec for every sub-iter live in the frozen handoff
[`extrace-static-stream-handoff.md`](extrace-static-stream-handoff.md);
the decision record is [`ADR 0016`](../adrs/0016-static-analysis-pre-check-stage.md).

Stable sub-iter IDs (`ES-0`..`ES-5`) are inherited from the handoff and
must not be renumbered — code comments and tests reference them.

## Status (Quick Glance)

- **Stream active on branch `static`** (cut from `main`). Single-branch,
  single Docker stack — the explicit lesson from the 2026-05-28
  abandonment of the parallel `extrace-static` worktree.
- **Phase framing:** this is a named stream (`ES-0`..`ES-5`), not a
  weekly `W<N>` phase, to avoid colliding with the ADR 0015
  sandbox-evasion `W23+` roadmap. It does not claim the canonical
  weekly active-phase pointer; `W22` remains the last merged phase.
- **Gate (strict, per user direction 2026-05-29):** every sub-iter runs
  `postgres_test` up + `make check-all` (and `make test-smoke` for
  container / pipeline iters) green before the next; one commit per
  sub-iter on green.
- **Main onayı zorunlu.** Push, PR oluşturma, merge, branch silme: hepsi
  user onayı zorunlu (memory `feedback_pr_push_approval`).

## Sub-Iter Slate

| ID | Scope | Status |
|----|-------|--------|
| ES-0 | Doc-reconcile: ADR 0016 (Proposed) + lane doc + this tracker + ADR existence arch test | DONE (`735fdf0`) |
| ES-1a | Schema contracts: static-detection finding/report/gate + combined bundle (producer-free) | DONE (`33cfdfc`) |
| ES-1b | Lifecycle landing: `rejected_static` terminal status + `static_report_path` (snapshot/update + ORM column) + Alembic; folded audit fixes (gate decision-consistency, evidence `relative_path` boundary). No step-Literal change. | DONE |
| ES-2 | Hardened `automation_static_analyzer` container scaffold + runtime stub | DONE |
| ES-3a | 6 in-house Python rules (s1/s2/s3) + static runner | DONE |
| ES-3b | Decision gate + orchestrator wiring; 7-step order + `empty_job_steps` extension (the ES-1 regression mitigation) | DONE |
| ES-4 | Semgrep integration (version-pinned wheel + 4 custom JS rules) | PENDING |
| ES-5 | Close-out: UI surfaces + `AnalyzeResponse` extension + smoke evidence + feature-flag flip; ADR 0016 → Accepted | PENDING |

## Per-Item Detail

### ES-0 — Doc-reconcile (DONE, `735fdf0`)

Re-homes the design artifacts lost when the `extrace-static` branch was
deleted. Additive only — no canonical preamble doc is touched, so the
preamble-parity / phase-pointer gates stay green.

- `documents/adrs/0016-static-analysis-pre-check-stage.md` — Proposed;
  records the four locked decisions + the ES-0..ES-5 roadmap; cites the
  handoff as Source.
- `documents/agent-lanes/static-analysis-pre-check.md` — lane doc.
- `documents/active-work/static-analysis-pre-check-stream.md` — this
  tracker.
- `tests/architecture/test_static_analysis_adr.py` — pins ADR 0016
  existence + the load-bearing tokens (four decisions, `rejected_static`,
  `automation_static_analyzer`, `extrace.s2.typosquat`, ES-0..ES-5, the
  handoff cross-reference).

### ES-1a — Schema contracts (DONE, `33cfdfc`)

Schema-first, producer-free. Additive facade re-export only (not yet in the UI
`TARGET_SCHEMAS` allowlist — UI regen is ES-5).

- `packages/analysis_contracts/static_detection/{__init__,finding,report,gate}.py`
  — `StaticDetectionFinding` (field-set parity with the dynamic
  `DetectionFinding`), `StaticEvidenceRef`, `StaticToolExecutionRecord`,
  `StaticSeverityCounts`, `StaticDetectionReport`, `StaticGateDecision`,
  `StaticGateOutcome`. v2 evidence types + tool slots pre-shipped.
- `appcore/contracts/schema_defs/static_analysis_bundle.py` —
  `StaticAnalysisReport`, `CombinedAnalysisBundle` (`dynamic_bundle` None on BLOCK).
- `tests/platform/contracts/test_static_detection_contracts.py` — schema invariants.

### ES-1b — Lifecycle landing + folded audit fixes (DONE)

The one "critical" sub-iter: mutates shared job-lifecycle state + adds a DB
migration. Adds the terminal `rejected_static` status and the
`static_report_path` column; folds in two audit fixes while the contracts are
still producer-free.

- `appcore/contracts/schema_defs/analysis_jobs.py` — `rejected_static` appended
  to `ANALYSIS_JOB_STATUSES` + `AnalysisJobStatus` Literal (terminal; NOT in
  `ACTIVE_ANALYSIS_JOB_STATUSES`). `static_report_path: str | None = None` on
  `AnalysisJobCreateSnapshot` + `AnalysisJobUpdate`. Step names untouched.
- `appcore/storage/model_defs/analysis_job.py` — nullable `static_report_path`
  column; partial unique index unchanged.
- `alembic/versions/f4b9d2e7a1c3_add_static_report_path_to_analysis_jobs.py` —
  additive add/drop column, `down_revision = e7c0a8f3b9d2` (no index / data motion).
- Audit fixes: `gate.py` decision-consistency validator (BLOCK⟹blocked_by,
  WARN⟹warned_by, ALLOW⟹both empty); `finding.py` `relative_path` boundary
  (reject absolute / `..` / control chars). Snippet redaction deferred to the
  ES-3a producer (reuse `redact_secrets`), not a DTO validator.
- Tests: `test_job_state_invariants.py` six→seven; new
  `test_rejected_static_terminal_status.py` (5 invariants); new
  `test_alembic_static_report_path_migration.py` (`requires_db` round-trip);
  `test_static_detection_contracts.py` negative tests + line-188 fix.
- Deferred to ES-3b: `_TERMINAL_JOB_STATUSES += rejected_static` and the 7-step
  / `empty_job_steps` extension (land with the producer/orchestrator wiring).

### ES-2 — Hardened container scaffold + runtime stub (DONE)

Stands up the `automation_static_analyzer` Docker boundary (ADR 0016 §Decision
2) plus a producer-free runtime stub. Scaffold only — the container writes an
*empty* `StaticDetectionReport`; rules land ES-3a, orchestrator wiring ES-3b.
Feature flag stays OFF.

- `static_runtime/` (NEW top-level package: `__init__` / `entrypoint` /
  `__main__`) — `python -m static_runtime` writes an empty
  `StaticDetectionReport` to `--report-path`. **Placement deviation from the
  handoff** (which said `packages/analysis_engine/static_runtime/`):
  `packages/analysis_engine/__init__.py` eagerly imports `run_detection`, so
  that path would drag the whole dynamic engine into the minimal hardened
  image. The stub needs only `packages.analysis_contracts.static_detection`
  (pydantic-only; verified no back-edge to `analysis_engine`), so it lives at
  top level and the image copies `packages/analysis_contracts/` + `static_runtime/`
  only.
- `docker/static_analyzer/{Dockerfile,requirements.txt}` — reuses the api's
  audited `python:3.11-slim-bookworm@sha256:cd6733…` base digest (one audited
  base, not two; 3.11 suffices for the pydantic-only stub) rather than the
  handoff's unpinned 3.12. Non-root `static` user; pydantic + pyyaml (pyyaml
  pre-staged for ES-4); no semgrep.
- `docker-compose.yml` `static_analyzer` service — `network_mode: none`,
  `cap_drop: [ALL]`, no `cap_add`, `no-new-privileges`, `mem_limit 1g` /
  `cpus 1.0`, ro extensions / rw results mounts (reusing the executor mount env
  vars), no docker.sock, no ports, idled via `command: ["sleep","infinity"]`.
- `executor/static_host.py` + `executor/static_control.py` — lean clones of
  `host.py::_run_docker_exec` / `ExecutorControl` (`StaticAnalyzerError`,
  `StaticAnalyzerControl.run_static_analysis`). Baked into the api image;
  DORMANT until the ES-3b orchestrator calls them.
- `executor/config.py` — `StaticAnalyzerSettings` + `StaticAnalysisSettings`
  (`ENABLED` defaults False). `executor/binary_paths.py` — absolute
  `STATIC_ANALYZER_PYTHON3_PATH` (the slim image's `/usr/local/bin/python3`).
- Makefile `static-build/up/down/shell/run-fixture` + help / `.PHONY`;
  `.env.example` static block.
- Tests: `tests/security/test_static_container_isolation.py` (enrolled into
  `test-security`); `tests/executor/test_static_control.py` (mocked subprocess +
  the argparse contract + **container-free locks on the stub's on-disk
  `StaticDetectionReport` JSON contract** via `run_static_detection` / `main`,
  plus the **feature-flag default-OFF** invariant — these run in the default
  lane, unlike the container-gated smoke test);
  `tests/smoke/test_static_container_smoke.py` (`smoke`+`integration`, live
  container); `static_analyzer` added to `_HARDENED_SERVICES` in
  `test_compose_isolation_invariants.py`; `STATIC_ANALYZER_PYTHON3_PATH` pinned
  in `test_absolute_paths.py`. The hardened image's base digest is auto-covered
  by `test_dockerfile_digest_pin.py` (rglob over `docker/`).
- Deferred: real rules → ES-3a; orchestrator wiring + `static_host` callers +
  `docker compose build api` → ES-3b; semgrep → ES-4; `/results` non-root write
  permission → ES-3b.

### ES-3a — In-house static rules MVP + static runner (DONE)

Swaps the ES-2 empty-report stub for the real in-house rule engine, behind the
unchanged ES-2 flag surface + on-disk `StaticDetectionReport` JSON contract.
Producer-only — the decision gate + orchestrator wiring stay in ES-3b; feature
flag stays OFF. `make check-all` green (2214 passed); container rebuilt +
`make test-smoke` green (rules fire live in the hardened image). Regression-
checked against a live UI scan (ms-python.python, 2026-05-30): job `completed`,
all 5 dynamic steps green, `static_report_path` NULL (gate not wired yet), and
re-running `run_detection` over the scanned report confirmed `extrace.a3.typosquat`
still executes silent with the moved allowlist loading 18 entries — the
shared-leaf refactor did not disturb the dynamic pipeline.

- **Placement deviation from the frozen handoff (Option A, user-approved
  2026-05-30):** the handoff put rules under `packages/analysis_engine/static_rules/`
  and reused `a3_typosquat._nearest_popular_match`. That conflicts with the ES-2
  minimal-image decision — `packages/analysis_engine/__init__.py` eagerly imports
  `run_detection`, so importing any engine submodule drags the whole dynamic
  engine into the hardened image (which copies only `packages/analysis_contracts/`
  + `static_runtime/`). Instead the rules live under `static_runtime/` (already
  in the image), and the typosquat matcher + `popular_extensions.txt` moved to
  `packages/analysis_contracts/typosquat_match.py` (+ `data/`), a stdlib-only
  leaf both the dynamic `a3_typosquat` and the static `s2` rule import. One
  curated allowlist copy; no engine import; `a3_typosquat` behaviour unchanged
  (its existing tests are the regression guard).
- `static_runtime/context.py` — `StaticAnalysisContext.from_vsix_dir`: parses
  `package.json` (root or `extension/`) with **stdlib `json`** (NOT
  `workflows.extension_catalog.manifest_reader`, which imports `appcore` and
  would break the `static_runtime` boundary); `iter_files` skips symlinks.
- `static_runtime/rules/{base,registry,_common,s1_manifest_red_flags,
  s2_typosquat_static,s3_file_tree_heuristics}.py` — mirrors the dynamic
  `packages.analysis_engine.rules` shape (Protocol base + self-registering
  singletons + lazy registry). Six PRODUCTION rules: `extrace.s1.activation_wildcard`
  / `extrace.s1.suspicious_capabilities` / `extrace.s1.generic_publisher` /
  `extrace.s2.typosquat` (HIGH, the promoted gate blocker) /
  `extrace.s3.embedded_native_binary` / `extrace.s3.unusual_file_signature`.
  Evidence snippets routed through `redact_secrets`
  (`packages/analysis_contracts/evidence.py`) — the ES-1b producer-side deferral.
- `static_runtime/static_runner.py` — `run_static_detection_engine` mirrors
  `packages.analysis_engine.runner.run_detection`: loads production rules,
  evaluates each over the context (soft `timeout_budget_s` check between rules;
  rule errors degrade to no-finding), rolls up `StaticSeverityCounts` + an
  `inhouse` `StaticToolExecutionRecord`. `entrypoint.run_static_detection` is the
  thin file-writing wrapper (signature + on-disk shape unchanged from ES-2).
- Tests: `tests/static_runtime/` (per-rule fire/silent + runner rollup/round-trip
  + budget; `conftest.make_context` factory); `tests/architecture/test_static_runtime_import_boundary.py`
  (static_runtime must not import `workflows`/`appcore`/`packages.analysis_engine`);
  updated `tests/executor/test_static_control.py` (stub→runner on-disk lock) +
  `tests/smoke/test_static_container_smoke.py` (clean-tree inhouse record + live
  rules-fire). `a3_typosquat` tests unchanged (shared-leaf regression guard).
- Deferred to ES-3b (now landed — see ES-3b below): decision gate, orchestrator
  wiring, 7-step / `empty_job_steps`, `_TERMINAL_JOB_STATUSES += rejected_static`,
  api rebuild. Semgrep → ES-4.

### ES-3b — Decision gate + orchestrator wiring (DONE)

Wires the ES-3a producer into the live analysis-job orchestrator behind the
unchanged OFF feature flag — the documented ES-1 step-Literal regression
mitigation lands here. `make check-all` green (ruff + mypy clean, full pytest
green, ui-types/ui-boundaries/markdownlint clean). Regression-checked against a
live UI scan (ms-python.python, 2026-05-30): job `completed`, verdict `clean`,
the two new static steps seeded `skipped` (flag OFF), the 5 dynamic steps green —
zero regression. No Alembic migration (`static_report_path` landed ES-1b).

- **Step contract 5 → 7** (`appcore/contracts/schema_defs/analysis_jobs.py`):
  `ANALYSIS_JOB_STEP_NAMES` + the `AnalysisJobStepName` Literal gain
  `static_analysis` + `decision_gate`, leading the order (pre-check before any
  sandbox spin); `_validate_steps` pins the exact 7-step order.
- **`empty_job_steps` flag-aware** (`workflows/marketplace/job_service.py`): 7
  records; the two static steps seed `skipped` when the flag is OFF, `pending`
  when ON — landed together with the step-name extension (the regression seam).
- **`rejected_static` terminal transition**: `_TERMINAL_JOB_STATUSES` gains
  `rejected_static` (`lifecycle.py`); new
  `appcore/storage/crud_ops/analysis_jobs/static_gate.py::reject_analysis_job_static`
  (row-locked, mirrors `finalize_cancelled_analysis_job`), re-exported via
  `crud.py`; `job_service.reject_static_job` wrapper.
- **Orchestrator stage** (`workflows/marketplace/analysis_service.py`):
  `_run_static_gate` inserted between `ensure_vsix_exists` and `_reset_sandbox`,
  gated on `settings.static_analysis.ENABLED`. BLOCK → persist the combined
  bundle + raise `StaticAnalysisBlockedError` → `reject_static_job` (terminal
  `rejected_static`, dynamic steps skipped); ALLOW/WARN → proceed.
  `StaticAnalysisBlockedError` added to `ANALYZE_RECOVERABLE_ERROR_TYPES` and
  mapped to HTTP 422 (sync + async parity).
- **Execution + cancel** (`workflows/marketplace/analysis_execution.py`):
  `run_static_analysis_stage` + `static_analysis_failure_message`;
  `_run_static_off_thread` cancel coordinator (~100ms poll, mirrors the W18-2
  reset coordinator) firing `control.cancel()` → `pkill -f static_runtime`
  (`executor/static_host.py` + `executor/static_control.py`).
- **Settings** (`appcore/api/config.py`): `StaticAnalysisSettings`
  (`ENABLED=False`, `RULES_VERSION`, `TIMEOUT_BUDGET_S`); shares the
  `STATIC_ANALYSIS_ENABLED` env flag with the executor-side mirror.
- **Path seam**: container `report_path` on the `/results` mount; host read-back
  under `settings.project.OUTPUT_DIR` (mirrors `analysis_reports.load_report_payload`).
- Tests: `tests/platform/storage/test_static_blocked_job_state.py` (DB
  state-machine), `tests/workflows/marketplace/test_static_gate_stage.py` (gate
  ALLOW/WARN/BLOCK + path seam + flag-aware `empty_job_steps` + cancel
  coordinator), `test_run_analysis_job_finalize.py` (BLOCK → reject routing),
  `test_static_control.py` (cancel argv + delegation); architecture gates
  updated (terminal-set invariant, facade re-export, ES-1b deferral note).
- Deferred to ES-4: Semgrep. Deferred to ES-5: UI / `AnalyzeResponse` static
  surfacing + flag flip + ADR 0016 → Accepted.

## Acceptance Bar / Notes

- The four locked decisions (block-and-warn · separate hardened container
  · schema-first · in-house + Semgrep MVP) are settled; re-opening any
  requires an amendment to ADR 0016, not a fresh design round.
- ES-1 must NOT touch `ANALYSIS_JOB_STEP_NAMES` / `empty_job_steps`; the
  7-step extension lands with its producer update in ES-3b (the
  documented regression mitigation).
- New security-lane tests enroll into the explicit `test-security`
  Makefile file list (no auto-discovery).
- Feature flag `settings.static_analysis.ENABLED` stays OFF until ES-5
  flips it after smoke evidence passes.
- **Downstream (W23, not in this stream) — forward-pointer only, ES slate
  unchanged.** A MITRE ATT&CK coverage matrix (`/mitre` UI surface +
  `GET /api/mitre/catalog` backend) visualizing which rules are critical
  across both the static (s1/s2/s3) and dynamic (a1–a6) rulesets is tracked
  in `POST_POC_BACKLOG.md` (Contracts / Reports / Detection) as
  `[GOAL mitre-mapping-adr]` / `[GOAL mitre-coverage-catalog]` /
  `[GOAL mitre-coverage-ui]` / `[GOAL mitre-static-overlay]`, W23 candidate
  after this stream's ES-5 close-out. The backend catalog is independent and
  could be pulled as an `ES-4b` item if the data layer is wanted sooner; the
  per-report static overlay depends on ES-3b populating `static_report_path`.

## Pre-Close-Out Review Checklist (static-branch audit + Codex cross-review, 2026-05-30)

Surfaced by a read-only architecture/security audit of the `static` branch plus a
Codex cross-review. **No code action is taken yet (owner direction 2026-05-30):
each row is a gating CHECK to verify or consciously waive before the
`static -> main` close-out PR (ES-5 window).** None is a P0/P1 hard-rule
violation; all are hygiene / observability / test-coverage on the in-flight
surface. The W0-W22 closed-phase regression scan came back clean, so every item
below lives in branch-delta code (no pre-existing-main regression).

Provenance: 11/12 are ES static-analysis-stream work; `static-events-loc-ratchet-headroom`
rides on this branch from `c5879bb` (`feat(executor/file-capture)`), NOT ES work —
resolve it with that change's owner or bump the ceiling. `static-input-bounds`
SEC-STATIC-01/02 share a fix-locus with the dynamic engine (`typosquat_match`
relocated from `a3_typosquat`; shared `redact_secrets`) — regression-guard the
dynamic side when fixing.

Buckets: **GATE** = one-line gate/config, goes green immediately · **CODE** =
additive code+test (ES-3b/ES-4 window) · **ES5** = fold into the ES-5 ADR-Accepted /
settings reconcile · **DEC** = ES-4 design decision · **NON-ES** = not
static-analysis work (handle with the file-capture change or at close).

| ID | Pre-close check (verify or consciously waive) | Evidence (HEAD) | Bucket |
|----|-----------------------------------------------|-----------------|--------|
| `[ES-CLOSE static-execution-observability]` | `StaticDetectionReport` / `StaticToolExecutionRecord` carry no execution telemetry — a swallowed rule error, an early budget break, or an unparseable manifest is indistinguishable from a clean ALLOW (bad failure mode for a security tool). Add `status` / `partial` / `error_count` / `errored_rule_ids` (additive v2 bump). Merges Codex #1 + #7 + audit QEL-2. | `static_runtime/static_runner.py:59-65`; `packages/analysis_contracts/static_detection/report.py:21-30`; `static_runtime/context.py:52-57` | CODE |
| `[ES-CLOSE static-typosquat-confidence-wording]` | ADR 0016 §Decision 1 says "HIGH-**confidence** blocker" but `s2` emits `confidence=MEDIUM` and the gate blocks on severity + rule-id only (confidence unread). Fix wording -> "HIGH-**severity** promoted blocker" (MEDIUM is correct — parity with dynamic `a3`); add a `test_decision_gate.py` policy test pinning the block reason. Codex #2. | `documents/adrs/0016-static-analysis-pre-check-stage.md:57`; `static_runtime/rules/s2_typosquat_static.py:31,58`; `workflows/marketplace/static_analysis.py:79` | ES5 |
| `[ES-CLOSE static-runtime-bare-except-gate]` | the no-bare-except gate's `SCANNED_DIRS` omits the new `static_runtime` adversarial-input prod root. Add `"static_runtime"` (green now — no bare except today). Codex #3 / audit QEL-1. | `tests/architecture/test_no_bare_except_exception.py:35` | GATE |
| `[ES-CLOSE static-control-outbound-surface-gate]` | the semantic outbound gate scans only `executor/control.py`; the workflows-importable `executor.static_control` seam is not checked for docker/subprocess leakage. Extend the gate to scan `static_control.py` too (+ `subprocess.CompletedProcess` to the forbidden tokens). Current public surface is clean (verified). Codex #4. | `tests/architecture/test_executor_control_outbound.py:42`; `executor/static_control.py:25-47` | GATE |
| `[ES-CLOSE static-cancel-path-effectiveness]` | cancel runs `pkill -f static_runtime` but the hardened image installs no `procps`/`pkill`, so cancel is a guaranteed no-op; an in-flight run is bounded only by `exec_timeout`. Latent now (fast in-house rules), real once ES-4 Semgrep makes scans long. Decide: document timeout-authoritative semantics / move to one-shot `docker run --rm` / add `procps` (dependency -> needs approval). Codex #5. | `executor/static_host.py:113-138`; `docker/static_analyzer/Dockerfile` | DEC |
| `[ES-CLOSE static-packaging-coverage-metadata]` | `static_runtime` is prod code (image-COPYed) but absent from the setuptools include AND the coverage source -> coverage reports understate the new package. Add it to coverage source; document the image-only setuptools decision (or include it). Codex #6. | `pyproject.toml:40-45` (include); `pyproject.toml:184-189` (coverage source) | GATE |
| `[ES-CLOSE static-input-bounds]` (SEC-STATIC-01/02/03) | container-bounded but unbounded adversarial reads: Levenshtein with no length band (**shared with dynamic `a3`**), snippet `redact_secrets` runs before the `[:400]` clamp = latent ReDoS (**shared root**), manifest `read_text()` no byte cap + `rglob` no file-count cap. Add stdlib caps; regression-guard the dynamic side for the two shared loci. Audit. | `packages/analysis_contracts/typosquat_match.py:47-86`; `static_runtime/rules/_common.py:23-25` + `packages/analysis_contracts/evidence.py:56-91`; `static_runtime/context.py:53,74` | CODE |
| `[ES-CLOSE static-events-loc-ratchet-headroom]` (NON-ES) | `attribution/events.py` = 526 LoC vs the pinned ratchet ceiling 527 (1 LoC headroom); the next touch breaks the gate. Came from `c5879bb` (`feat(executor/file-capture)`), NOT ES work. Extract the pid-lineage block to the `lineage.py` sibling OR bump the ceiling with a one-line rationale. Audit SH-1. | `executor/flows/playwright/attribution/events.py:526`; `tests/architecture/test_executor_hotspot_loc_ratchet.py:48`; commit `c5879bb` | NON-ES |
| `[ES-CLOSE static-host-nosec-consistency]` | Bandit dir-excludes `executor/`, so the new `static_host.py` subprocess sites carry no `# nosec`, leaving the `pyproject.toml` Bandit rationale comment ("every subprocess call carries `# nosec`") factually stale. Add `# nosec` to the two `subprocess.run` sites OR update the rationale. Audit QEL-3. | `executor/static_host.py` (the two `subprocess.run` sites); `pyproject.toml` Bandit block (verify exact line at close) | GATE |
| `[ES-CLOSE static-run-fixture-quoting-gate]` | the new Makefile `static-run-fixture` target regex-validates + double-quotes operator vars (W14-3 pattern) but is unpinned by the quoting gate. Extend it. Audit TDC-13-1. | Makefile `static-run-fixture` target; `tests/architecture/test_makefile_sim_quoting.py` (verify exact lines at close) | GATE |
| `[ES-CLOSE static-settings-timeout-naming]` | two env keys for one logical timeout — `StaticAnalysisSettings.TIMEOUT_S` vs the app-side `TIMEOUT_BUDGET_S` (env `STATIC_ANALYSIS_TIMEOUT_BUDGET_S`, absent from `.env.example`). Defaults agree (30s) so correct out-of-box; reconcile naming. Audit TDC-13-2. | `executor/config.py` (`StaticAnalysisSettings`); `.env.example` static block | ES5 |
| `[ES-CLOSE static-malformed-report-test]` | empty-report (`test_run_static_analysis_empty_report_allows`), exec-failure, and BLOCK error-taxonomy ARE tested, but a specifically malformed/truncated JSON report body -> typed terminal failure (not a silent ALLOW) is unpinned. Add one test. Audit. | `workflows/marketplace/static_analysis.py:142-143`; `tests/workflows/marketplace/test_static_analysis_pipeline.py` | CODE |

**Disposition at a glance:** GATE (cheap, green now) — `bare-except`, `outbound-surface`,
`packaging-coverage`, `host-nosec`, `run-fixture-quoting`. CODE (additive code+test) —
`execution-observability`, `input-bounds`, `malformed-report-test`. ES5 (fold into
ADR-Accepted / settings reconcile) — `confidence-wording`, `settings-timeout-naming`.
DEC (ES-4) — `cancel-path-effectiveness`. NON-ES — `events-loc-ratchet-headroom`.
None blocks the merge on its own; the owner may waive any with a recorded rationale
at the `static -> main` close-out.

## Audit Findings — Disposition (resolved / deferred in ES-1b, 2026-05-30)

Cross-audit (self + Codex) after ES-1a (`33cfdfc`) + the tshark fix
(`ac79c1e`) landed on `static`. The two real contract findings were folded into
the ES-1b commit while the contracts are still producer-free. Severity is
yüzey-önem, not a live exploit (no static producer exists yet — rules land
ES-3a/ES-4).

Disposition:

- `adr0013-rationale-cap-parity` — already fixed by `3a23cbb` (Rationale now
  lists the 5-cap set); no further action.
- `static-gate-decision-consistency` — **FIXED in ES-1b** (`gate.py`
  `validate_decision_consistency` + negative tests).
- `static-evidence-boundary-validation` — `relative_path` boundary **FIXED in
  ES-1b** (`finding.py`). Snippet redaction is **deferred to the ES-3a
  producer** (reuse `redact_secrets`), NOT a DTO validator — keeps static
  layering consistent with the dynamic side. (Supersedes the table row's
  "route `snippet` through `redact_secrets` [now]" wording.)
- `tracker-and-test-truth-sync` — (a) slate flipped in ES-1b (this edit).
  (b) Enrolling `test_static_detection_contracts.py` into `test-security` is
  **out of scope**: it is a contract-invariant test that already runs under
  `make check-all`; the `test-security` enrollee is the future ES-2
  container-isolation test (`test_static_container_isolation.py`).

The historical finding table (as raised 2026-05-29) is retained below for
provenance.

| ID | Severity | File (evidence) | Problem | Fix |
|----|----------|-----------------|---------|-----|
| `[ES-1 adr0013-rationale-cap-parity]` | P1-doc | `documents/adrs/0013-container-isolation-baseline.md` §Rationale point 1 (~L173) | The decision table (L49) + amendment (§Network capture under no-new-privileges) now list 5 caps `[NET_RAW, SYS_PTRACE, SETUID, SETGID, SETPCAP]`, but Rationale point 1 still says "adding back only monitoring capabilities (`NET_RAW`, `SYS_PTRACE`)". Self-contradiction, already pushed in `ac79c1e`. | Update the Rationale prose to match the 5-cap set + cross-ref the setpriv ambient-drop amendment. |
| `[ES-1 static-gate-decision-consistency]` | P1 | `packages/analysis_contracts/static_detection/gate.py:23-37` | `StaticGateOutcome` only validates `allow_reason`. `BLOCK`/`WARN` are valid with empty `blocked_by`/`warned_by`; `ALLOW` may still carry blocker lists → a terminal `rejected_static` reachable with no machine-readable cause (observability hard rule). | Add a `@model_validator(mode="after")`: `BLOCK ⟹ blocked_by` non-empty; `WARN ⟹ warned_by` non-empty; `ALLOW ⟹ both empty`. + negative tests in `tests/platform/contracts/test_static_detection_contracts.py`. |
| `[ES-1 static-evidence-boundary-validation]` | P1 | `packages/analysis_contracts/static_detection/finding.py:47-55` (`StaticEvidenceRef`) | `relative_path` is only `min_length=1` (no absolute/`..`/control-char reject); `snippet` has a length bound but is NOT run through the redaction contract. Extension-controlled VSIX path/snippet can cross into JSON/UI/log surfaces unredacted (AGENTS rule 11; impact = report/log poisoning, not RCE). | Reject absolute/traversal/control-char `relative_path`; route `snippet` through `redact_secrets` (the dynamic `ContentSample` pattern). + negative tests. |
| `[ES-1 tracker-and-test-truth-sync]` | P2 | this tracker (Sub-Iter Slate) + `Makefile:219-234` | (a) Slate still shows ES-0 IN PROGRESS / ES-1 PENDING, but `33cfdfc` landed ES-1a contracts — split ES-1 into ES-1a (schema contracts, DONE) / ES-1b (PENDING: `rejected_static` status + `static_report_path` ORM column + Alembic). (b) `tests/platform/contracts/test_static_detection_contracts.py` is not in the explicit `test-security` Makefile list (lane doc line 44 requires enrollment; no auto-discovery). | Flip slate rows; add the test to the Makefile `test-security` target. |

Verification note: all four confirmed against HEAD git blobs (the working
tree shifted during the audit and both the Bash content layer and a
second reviewer produced phantom paths — trust `git show HEAD:<path>`,
not recalled line numbers, when fixing).
