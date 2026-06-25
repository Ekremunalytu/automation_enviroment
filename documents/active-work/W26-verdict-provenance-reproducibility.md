# W26 — verdict-provenance-reproducibility (Stream 3, the spine)

`Last Updated: 2026-06-25`

`Status: OPEN on week26 (off main 27dc7f1, 2026-06-25). Closes v1.0 bars B5 (verdict bound to the bytes) + B6 (verdict reproducible). Named-stream convention: this branch's H0 (S0) flips documents/phase.json active_stream from operator-console-honesty -> verdict-provenance-reproducibility and refreshes the canonical preambles. ADR 0017 (Proposed) records the provenance/reproducibility design; ADR 0016 gets an additive 5th-flag amendment for the static container's --vsix-sha256.`

Stream 3 of the v1.0 roadmap (`documents/active-work/v1-roadmap.md` §4). The
**spine**: four downstream streams (B7/B8 measurement, export, release-identity,
batch) depend on a verdict that is **build-attributable** and **reproducible**.
Getting this order wrong is the one mistake that lets the project measure and
scale on sand (roadmap §4 "Spine decision").

Stable IDs (roadmap §7): `[GOAL vsix-content-sha256-provenance]` (B5),
`[GOAL verdict-reproducibility-anchor]` (B6).

## Bar acceptance (roadmap §3)

- **B5** — `vsix_sha256` computed at intake, persisted on `AnalysisJob`, stamped
  into the report; two byte-different same-version VSIX are not conflated.
- **B6** — same VSIX run twice → same malicious/clean/inconclusive verdict;
  `run_quality_reasons` partitioned into behavioral vs harness-health; residual
  variance is a labeled band, not silent flicker; N-run determinism test on the
  reference target.

## Design summary (full detail in ADR 0017)

**B5 — one hash, threaded to three consumers.** `vsix_sha256 =
sha256(<staged .vsix bytes>).hexdigest()` is computed **once at analyze-start**
(`start_analysis_job`, from the `ensure_vsix_exists` path — the exact archive
this run scans; streamed to bound memory). Computing here rather than at the
ingest chokepoint is deliberate: the analyze flow reads an already-staged
`.vsix` and never re-enters ingest, so hashing the bytes the run consumes binds
the verdict to *those* bytes (catches post-ingest replacement; no
Extension-catalog schema change). It is threaded to the worker and fanned out
to:

1. **`AnalysisJob`** (DB) — new nullable `vsix_sha256` column, written through
   the CRUD snapshot (S4).
2. **Dynamic report** (`ActivationReport`) — contract field + emit-boundary
   stamp, mirroring the existing `executor_fingerprint` precedent. The value
   reaches the in-container producer via a new `--vsix-sha256` arg on
   `run_playwright_automation` → `host.py` docker-exec argv → entrypoint (S2).
3. **Static report** (`StaticDetectionReport`) — contract field + stamp; the
   value reaches the hardened static container via an additive 5th flag
   `--vsix-sha256` on the `executor/static_host.py` invocation contract (ADR
   0016 amendment) (S3).

The orchestrator then **asserts agreement** (intake == dynamic-report-stamp ==
static-report-stamp); a mismatch is a wiring defect, surfaced not swallowed.
Chosen over (a) orchestrator post-hoc stamping and (b) in-container archive
re-hash — see ADR 0017 "Alternatives". (b), the gold-standard "hash exactly the
bytes scanned" variant, is deliberately deferred (the container scans the
extracted tree, not the archive; mounting the `.vsix` in is future hardening).

**B6 — reproducible by construction + deterministic finalization.**
`compute_verdict` is already a pure function of `(findings,
automation_health.status)` and does **not** read `run_quality` (rollup.py), so
the verdict is reproducible by construction. The flicker the operator sees is in
the `run_quality` **anchor** and its attribution inputs, not the verdict:

- **S5** — partition `run_quality_reasons` into **behavioral** (what the
  extension did) vs **harness-health** (how cleanly the sandbox ran), and add a
  labeled `residual_variance` band so non-deterministic harness timing reads as a
  named state, not a silent `degraded`/`inconclusive` flip
  (`executor/flows/playwright/health/summary.py`).
- **S6** — kill the true finalization-time non-determinism: the
  competitor-tie-break in `_classify_event_attribution` /
  `_nearest_activation_matches` (wall-clock delta thresholds with a
  non-deterministic tie-break) gets a **deterministic stable tie-break**; the
  fixed 2.0s startup grace in `runtime_state.py` becomes a **bounded
  wait-on-condition** so log/activation flush timing stops perturbing the
  partition (`attribution/events.py`, `monitor/runtime_state.py`).

  > Corrected root cause (adversarial-verified): the flicker is **not**
  > `_cheap_target_reaction_count` (that field reads `is_target_extension_event`,
  > default `False`, set `True` only at finalization → always-zero mid-loop →
  > the W25 early-give-up is deterministic). Do **not** "fix" it as the flicker
  > source. The real source is finalization-time attribution + activation/log
  > flush timing.

## Sub-items

| Sub-item | Files | Acceptance |
|---|---|---|
| **S0** doc-reconcile + H0 | this tracker; ADR `0017` (Proposed); `documents/phase.json` (active-stream flip); 6 canonical preambles (`CLAUDE.md`, `AGENTS.md`, `documents/AGENT_CONTEXT.md`, `documents/POST_POC_BACKLOG.md`, `documents/REFACTOR_OPTIMIZATION.md`, `documents/README.md`) + `REFACTOR_STATUS.md` banner tail + `v1-roadmap.md` preamble | stream registered as the named successor to operator-console-honesty; the 4 doc-governance gates stay green; B2 close-out + 3 ride-alongs recorded as the pre-close checklist below |
| **S1** analyze-start hash + thread + agreement | `workflows/marketplace/client.py` (`compute_vsix_sha256` streamed helper); `workflows/marketplace/router.py` (`start_analysis_job`: compute from the `ensure_vsix_exists` path, pass as a worker thread-arg); `workflows/marketplace/analysis_service.py` (`run_analysis_job` -> `execute_analysis_request(vsix_sha256=...)`; thread to `_run_static_gate` + `_run_monitoring`; `_check_vsix_provenance_agreement` log-checks dynamic-stamp == static-stamp == computed) | the streamed `sha256` helper bounds memory; the same canonical 64-char lowercase hash reaches both producers; the orchestrator **logs an ERROR** on a non-empty stamp mismatch (non-raising — a raise would escape the worker's closed taxonomy and wedge the queue); the **hard agreement assertion is the S7 test** |
| **S2** B5 dynamic contract + producer | `packages/analysis_contracts/contracts.py` (`ActivationReport.vsix_sha256: str = ""`; `ACTIVATION_REPORT_SCHEMA_VERSION` 2.2 -> 2.3 + comment block); `executor/host.py` (`run_playwright_automation(vsix_sha256=...)` -> `--vsix-sha256`); entrypoint arg parse; `executor/flows/playwright/report_builder.py` emit-boundary stamp (sibling to `executor_fingerprint`); generated TS DTO (`make ui-types-check`) | contract field is additive-optional (legacy fixtures still validate); a new dynamic write stamps the intake hash; `make ui-types-check` regenerates the DTO. **4-atomic-touch** (dataclass step skipped — emit-boundary injection, same as `executor_fingerprint`). host.py is baked into `automation_api` → `docker compose build api && up -d api` |
| **S3** B5 static contract + producer + agreement | `packages/analysis_contracts/static_detection/report.py` (`StaticDetectionReport.vsix_sha256: str = ""`); `executor/static_host.py` (additive `--vsix-sha256` flag); `static_runtime/entrypoint.py` (parser + thread); `static_runtime/static_runner.py` (`run_static_detection_engine(vsix_sha256=...)` stamp); ADR `0016` additive-flag amendment; generated TS DTO; orchestrator agreement-assertion in `analysis_execution.py` | static report carries the same hash; static container invocation contract gains one additive optional flag (boundary change → ADR 0016); orchestrator asserts dynamic == static == intake; `make ui-types-check` |
| **S4** B5 DB persistence | `appcore/storage/model_defs/analysis_job.py` (nullable `vsix_sha256` after `last_heartbeat_at`); `appcore/contracts/schema_defs/analysis_jobs.py` (create-snapshot field); `appcore/storage/crud_ops/analysis_jobs/lifecycle.py` (`create_analysis_job` CRUD facade, `**snapshot.model_dump()`); `workflows/marketplace/job_service.py` (`reserve_job` threads the S1 hash into the snapshot) + `router.py` (`start_analysis_job` passes it); new alembic revision (additive-nullable, head off the current head) | **GATED — migration shown before run.** the row carries the analyzed-bytes hash at creation; two byte-different VSIX → two distinct `vsix_sha256` rows; `alembic-upgrade extrace` (5432) then `make check-all` (dev-DB gotcha) |
| **S5** B6 run_quality partition | `executor/flows/playwright/health/summary.py` (`_REASON_LABELS`, `build_run_quality`, discriminator) | `run_quality_reasons` partitioned behavioral vs harness-health; `residual_variance` is a labeled band; the partition is a pure function of stable inputs |
| **S6** B6 finalization determinism | `executor/flows/playwright/attribution/events.py` (deterministic stable tie-break); `executor/flows/playwright/monitor/runtime_state.py` (bounded wait-on-condition replaces the fixed 2.0s grace) | identical-input N-run determinism; no competitor tie-break or grace-timing flip perturbs the partition |
| **S7** tests + verification | `tests/executor/`, `tests/contracts/`, `tests/storage/`, lifecycle harness | N-run determinism test on the reference target; byte-different-VSIX-not-conflated provenance test; static/dynamic agreement test; B2 lifecycle-harness test (ride-along RA2); `make test-security` includes any new security test |

## Pre-close checklist (resolve/waive before close-out)

Per the audit-findings → pre-close-checklist practice (bucketed, evidence-cited,
none blocking). Ride-along scope was operator-approved at maximum (2026-06-25).

### B2 formal close-out (carry-over from the direct-to-main reliability work)

B2 (`survives back-to-back use`) is **functionally closed** —
`reliability-analyze-resilience.md` records the `4437d1e` fix (reset_state.py
pgrep `--` separator + CDP-independent needle + `/proc` tree reap),
live-verified. The roadmap B2 acceptance also asks for a **lifecycle-harness
test** asserting analyze #2/#3 reach `install_extension` with no container
restart. That harness test is **RA2** below; landing it formally closes B2's
acceptance language. (B2's code already shipped direct-to-main; this stream only
adds the missing harness assertion.)

### Ride-alongs (operator-approved, in-scope this stream)

| ID | Item | Files | Disposition |
|---|---|---|---|
| **RA1** | `[BUG report-field-redaction-completeness]` — 3 ungated extension-controlled report sinks | `monitor/scenario_accountant.py:~576` (`activation_event`), `runtime_capture/filesystem.py:108-120` (`FileEvent.path/summary`), `runtime_capture/extension_host_strace_parse.py:71,88,97` (`ProcessEvent.command/cwd`); redact at the chokepoint like sibling `network.py:109-110`; add 3 AST gates | fix + gate this stream |
| **RA2** | B2 lifecycle-harness test (the missing test for the landed B2 fix) | lifecycle harness under `tests/executor/` | land this stream → formally closes B2 |
| **RA3a** | `[CLEANUP pragma-ratchet-docstring]` — docstring says 6/3-files, enforced 7/4-files | `tests/architecture/test_bare_binary_pragma_ratchet.py:20-33` | trivial doc fix |
| **RA3b** | `[CLEANUP event-attempt-validate-assignment]` — `EventAttemptRecord` lacks `validate_assignment` | `packages/analysis_contracts/contracts.py:~223` | hardening hygiene |

## Regression surface

- **Report contracts** are `extra=forbid`; the dynamic add is the 4-atomic-touch
  (contract + schema bump + emit-boundary stamp + generated TS DTO) — a partial
  change fails `ReportContractError` / `make ui-types-check`.
- **Static invocation contract** (ADR 0016) — the 5th flag is additive-optional;
  the container's 4-flag stable surface stays backward-compatible.
- **Alembic** — additive-nullable only; after the change `alembic-upgrade
  extrace` (5432) or `make check-all` fails `UndefinedColumn` until the dev DB is
  upgraded (dev-DB gotcha).
- **B6 attribution** — the tie-break/grace changes must not regress
  `attribution_summary` or the W25 early-give-up (which is already deterministic).
- **Doc governance** — the S0 active-stream flip must keep the 4 doc-preamble
  gates green (canonical-preamble parity keeps `PR #31`/`1399f82`; consistency
  keeps each preamble naming the active stream without a `W<N> active` N≠22).
