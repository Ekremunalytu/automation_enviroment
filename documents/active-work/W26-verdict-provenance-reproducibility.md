# W26 — verdict-provenance-reproducibility (Stream 3, the spine)

`Last Updated: 2026-07-27`

`Status: MERGED to main via PR #38 (week26 -> main, bfb2d2d) on 2026-07-27. Implementation COMPLETE + branch-review-remediated. S0-S7 + all ride-alongs landed (5a2227d..8fa52ce); a 2026-06-26 adversarial multi-agent branch review then surfaced 8 verified findings, all resolved (e3a1054, 8dd6da3, e9e5ef1 — see "Branch-review remediation" below). B5 (S1-S4: vsix_sha256 spine + DB; sync /marketplace/analyze surface bound too per review B5-2) + B6 (S5-S6: partition + finalization determinism) closed. The one BLOCKING review finding (B6-1) was the freeze landing one step too late — signal_summary (the persisted verdict) baked from the pre-freeze live-FS read; fixed by freezing log_capture_health_snapshot BEFORE _refresh_derived_state() with a stop()-level regression guard. RA1 (redaction completeness, +2 sibling sinks RA1-3/RA1-4) + RA2 (B2 lifecycle test) + RA3a/RA3b done; B2 acceptance formally closed via RA2. ADR 0017 is Accepted + Implemented; ADR 0016 carries the accepted additive --vsix-sha256 amendment. Final gates passed 2026-07-27: make check-all (2726 passed, 11 skipped, 13 deselected) and make test-security (326 passed).`

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
- **S6** — kill the true finalization-time non-determinism. The **primary**
  driver (found by the 2026-06-26 verification workflow) is the live-FS re-read:
  `ActivationReport._log_capture_health` re-`stat()`-ed the exthost log on every
  property access, so `extension_host_log_missing` flickered run-to-run and the
  multiple reads in `print_summary` + `save` could disagree within one report.
  Fix: **freeze** `log_capture_health_snapshot` once in `stop()` and have the
  property return it (live read only on the unfrozen fixture path). The fixed
  2.0s startup grace in `runtime_state.py` becomes a **bounded wait-on-condition**
  (read-only poll on the activation-flush predicate) so flush timing stops
  perturbing the partition, and `_RESIDUAL_VARIANCE_REASON_CODES` is narrowed to
  the four reachable codes with a reachability guard
  (`monitor/types.py`, `monitor/runtime_state.py`, `health/summary.py`,
  `health/run_quality_partition.py`).

  > **Freeze ordering (branch-review B6-1, 2026-06-26):** the freeze must run
  > **before** `_refresh_derived_state()`, not after. Refresh computes
  > `signal_summary` — the persisted, operator-facing verdict — from
  > `automation_health` + `run_quality`, both of which funnel through
  > `_log_capture_health`. Freezing after refresh left the verdict baked from the
  > pre-freeze live read (flickering) while the top-level `run_quality` read the
  > frozen snapshot — non-reproducible verdict + intra-report contradiction.
  > Pinned by `test_stop_binds_signal_summary_verdict_to_frozen_snapshot`.

  > Corrected root cause (adversarial-verified): the flicker is **not**
  > `_cheap_target_reaction_count` (that field reads `is_target_extension_event`,
  > default `False`, set `True` only at finalization → always-zero mid-loop →
  > the W25 early-give-up is deterministic). Do **not** "fix" it as the flicker
  > source. The attribution equal-delta tie-break is real non-determinism but is
  > **deferred** (does not affect run_quality; can shift a B5 verdict) — see the
  > Deferred section.

## Sub-items

| Sub-item | Files | Acceptance |
|---|---|---|
| **S0** doc-reconcile + H0 | this tracker; ADR `0017` (Proposed); `documents/phase.json` (active-stream flip); 6 canonical preambles (`CLAUDE.md`, `AGENTS.md`, `documents/AGENT_CONTEXT.md`, `documents/POST_POC_BACKLOG.md`, `documents/REFACTOR_OPTIMIZATION.md`, `documents/README.md`) + `REFACTOR_STATUS.md` banner tail + `v1-roadmap.md` preamble | stream registered as the named successor to operator-console-honesty; the 4 doc-governance gates stay green; B2 close-out + 3 ride-alongs recorded as the pre-close checklist below |
| **S1** analyze-start hash + thread + agreement | `workflows/marketplace/client.py` (`compute_vsix_sha256` streamed helper); `workflows/marketplace/router.py` (`start_analysis_job`: compute from the `ensure_vsix_exists` path, pass as a worker thread-arg); `workflows/marketplace/analysis_service.py` (`run_analysis_job` -> `execute_analysis_request(vsix_sha256=...)`; thread to `_run_static_gate` + `_run_monitoring`; `_check_vsix_provenance_agreement` log-checks dynamic-stamp == static-stamp == computed) | the streamed `sha256` helper bounds memory; the same canonical 64-char lowercase hash reaches both producers; the orchestrator **logs an ERROR** on a non-empty stamp mismatch (non-raising — a raise would escape the worker's closed taxonomy and wedge the queue); the **hard agreement assertion is the S7 test** |
| **S2** B5 dynamic contract + producer | `packages/analysis_contracts/contracts.py` (`ActivationReport.vsix_sha256: str = ""`; `ACTIVATION_REPORT_SCHEMA_VERSION` 2.2 -> 2.3 + comment block); `executor/host.py` (`run_playwright_automation(vsix_sha256=...)` -> `--vsix-sha256`); entrypoint arg parse; `executor/flows/playwright/report_builder.py` emit-boundary stamp (sibling to `executor_fingerprint`); generated TS DTO (`make ui-types-check`) | contract field is additive-optional (legacy fixtures still validate); a new dynamic write stamps the intake hash; `make ui-types-check` regenerates the DTO. **4-atomic-touch** (dataclass step skipped — emit-boundary injection, same as `executor_fingerprint`). host.py is baked into `automation_api` → `docker compose build api && up -d api` |
| **S3** B5 static contract + producer + agreement | `packages/analysis_contracts/static_detection/report.py` (`StaticDetectionReport.vsix_sha256: str = ""`); `executor/static_host.py` (additive `--vsix-sha256` flag); `static_runtime/entrypoint.py` (parser + thread); `static_runtime/static_runner.py` (`run_static_detection_engine(vsix_sha256=...)` stamp); ADR `0016` additive-flag amendment; generated TS DTO; orchestrator agreement-assertion in `analysis_execution.py` | static report carries the same hash; static container invocation contract gains one additive optional flag (boundary change → ADR 0016); orchestrator asserts dynamic == static == intake; `make ui-types-check` |
| **S4** B5 DB persistence | `appcore/storage/model_defs/analysis_job.py` (nullable `vsix_sha256` after `last_heartbeat_at`); `appcore/contracts/schema_defs/analysis_jobs.py` (create-snapshot field); `appcore/storage/crud_ops/analysis_jobs/lifecycle.py` (`create_analysis_job` CRUD facade, `**snapshot.model_dump()`); `workflows/marketplace/job_service.py` (`reserve_job` threads the S1 hash into the snapshot) + `router.py` (`start_analysis_job` passes it); new alembic revision (additive-nullable, head off the current head) | **GATED — migration shown before run.** the row carries the analyzed-bytes hash at creation; two byte-different VSIX → two distinct `vsix_sha256` rows; `alembic-upgrade extrace` (5432) then `make check-all` (dev-DB gotcha) |
| **S5** B6 run_quality partition | `executor/flows/playwright/health/summary.py` (`_REASON_LABELS`, `build_run_quality`, discriminator) | `run_quality_reasons` partitioned behavioral vs harness-health; `residual_variance` is a labeled band; the partition is a pure function of stable inputs |
| **S6** B6 finalization determinism (refined by the 2026-06-26 verification workflow; freeze ordering corrected by the branch review, B6-1) | `monitor/types.py` + `monitor/runtime_state.py` (freeze `log_capture_health_snapshot` in `stop()` **before** `_refresh_derived_state()` so the persisted verdict `signal_summary` reads the frozen snapshot too, not a pre-freeze live read; property falls back to live read only on the unfrozen fixture path) — the **primary** anchor-flicker + intra-finalize inconsistency fix; `monitor/runtime_state.py` (bounded poll on the target-activation-flushed predicate replaces the fixed 2.0s grace); `health/summary.py` + `health/run_quality_partition.py` (narrow `_RESIDUAL_VARIANCE_REASON_CODES` to the 4 reachable codes + reachability guard) | identical-input N-run determinism; the frozen snapshot makes all run_quality **and the verdict** reads agree; the grace early-exits on a real signal; the band matches reachability. Pinned by `test_stop_binds_signal_summary_verdict_to_frozen_snapshot`. **Attribution tie-break deferred** (see followup below) |
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
| **RA1** | `[BUG report-field-redaction-completeness]` — 3 ungated extension-controlled report sinks | `monitor/scenario_accountant.py` (`message`/`activation_event`), `runtime_capture/filesystem.py` (`FileEvent.path/secondary_path/summary`), `runtime_capture/extension_host_strace_parse.py` (`ProcessEvent.command/cwd/summary`); routed through `redact_secrets` like sibling `network.py`; AST gate `test_runtime_capture_field_redaction.py` | **DONE** (f04b8ce) |
| **RA2** | B2 lifecycle test (the missing test for the landed B2 fix) | `tests/workflows/marketplace/test_b2_multi_analyze_install.py` | **DONE** (8fa52ce) → formally closes B2 |
| **RA3a** | `[CLEANUP pragma-ratchet-docstring]` — docstring said 6/3-files, enforced 7/4-files | `tests/architecture/test_bare_binary_pragma_ratchet.py` | **DONE** (92626df) |
| **RA3b** | `[CLEANUP event-attempt-validate-assignment]` — `EventAttemptRecord` lacked `validate_assignment` | `packages/analysis_contracts/contracts.py` | **DONE** (92626df) |

### Branch-review remediation (2026-06-26 adversarial multi-agent review)

After implementation, a 6-dimension multi-agent branch review (review → adversarial
refute → synthesize) over `main...HEAD` surfaced **9 raw findings; 8 survived
independent refutation** (1 high/blocking, 4 medium, 3 low). All resolved before
close-out — the user approved comprehensive (fix-all) scope (2026-06-26).

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| **B6-1** | high (blocking) | `signal_summary` (the persisted verdict) was baked from the **pre-freeze live-FS read**: the snapshot froze AFTER `_refresh_derived_state()`, which computes `signal_summary` from `automation_health`+`run_quality` (both via `_log_capture_health`). Verdict flickered run-to-run + could contradict top-level `run_quality`. | **FIXED** `e3a1054` — freeze moved before `_refresh_derived_state()`; `test_stop_binds_signal_summary_verdict_to_frozen_snapshot` (teeth-verified: fails on the pre-fix order) |
| **B5-2** | medium | Sync `POST /marketplace/analyze` called `execute_analysis_request` with no hash → both producers stamped `vsix_sha256=""` (unbound verdict) on a documented live surface. | **FIXED** `8dd6da3` — hash computed in `analyze_extension` inside the taxonomy try (missing .vsix still 404); `test_sync_analyze_binds_vsix_sha256_to_bytes` |
| **RA1-3** | medium | Extension-controlled `activation_event`/`message` reached persisted `log_entries` un-redacted via `lifecycle.py` `record_automation_event` — a sibling sink the RA1 AST gate did not cover. | **FIXED** `e9e5ef1` — both routed through `redact_secrets`; `lifecycle.py` added to the gate `_TARGETS`; behavioral test |
| **RA1-4** | medium | `FileEvent.flags = args` stored the raw strace arg blob (a superset of the redacted `path`), re-exposing a secret-shaped path substring on the same row. | **FIXED** `e9e5ef1` — `flags` routed through `redact_secrets`; `flags` added to the gate `FileEvent` field set; behavioral test |
| **Tests-3** | medium | No test pinned the dynamic `vsix_sha256` write path end to end (arg → report → on-disk key); a key/attribute rename would silently skip the dynamic agreement branch. | **FIXED** `e3a1054` — `test_dynamic_report_save_stamps_vsix_sha256_top_level_key` exercises the real emit boundary + extra=forbid round-trip |
| **Docs-S6** | low | The S6 design-summary prose claimed a deterministic attribution tie-break that was deferred (contradicted the sub-items table + ADR 0017). | **FIXED** (this commit) — prose rewritten to the implemented design (freeze-before-refresh primary fix; tie-break deferred) |
| **Docs** | low | `[FOLLOWUP attribution-tiebreak-determinism]` said "Logged for POST_POC_BACKLOG.md" but was absent there. | **FIXED** (this commit) — past-tense claim corrected to a close-out action; the backlog's per-stream entry is commit-stamped, so it lands post-merge with this stream's pull-forward table (named-stream convention), recorded here meanwhile |
| **Tests** | low | `test_run_quality_and_partition_are_reproducible` was tautological (pre-froze a snapshot, read a pure property twice; passed on `main`). | **FIXED** `e3a1054` — removed; reproducibility now pinned at the `stop()` level + `test_log_capture_health_snapshot` + `test_run_quality_partition` |

### Deferred (recorded, not done this stream)

- **`[FOLLOWUP attribution-tiebreak-determinism]`** — `_nearest_activation_matches`
  (`attribution/events.py:88-93`) breaks equal-delta ties by iteration order
  (strict `<`). The 2026-06-26 verification workflow confirmed this is real
  non-determinism but **does not affect run_quality** (status is delta-driven;
  the tied candidates share a delta, so `target_attributed` / `competing_candidate`
  is invariant — only `related_activation_event` / `related_extension_id` flip).
  Their sole consumer is `packages/analysis_engine/signals/policy.py`
  `correlated_groups` keying — the **B5 signal/verdict** path. A stable total-order
  sort there WILL change correlated grouping on previously-flickering
  overlapping-activation fixtures and **can shift a verdict**, so it must land as a
  B5 fix coordinated with the signal owner (re-run the signal-engine golden /
  verdict fixtures), NOT bundled into B6. Recorded here; its
  `POST_POC_BACKLOG.md` pull-forward entry lands in this close-out commit so the
  risk remains visible after the tracker freezes.

## Close-out evidence (2026-07-27)

- `make check-all` — PASS: Ruff, mypy (519 source files), Bandit, UI contract
  and boundary checks, markdownlint, and pytest (`2726 passed, 11 skipped,
  13 deselected`).
- `make test-security` — PASS: `326 passed`.
- Fixture corpus — retained. The tracked benign fixtures, T1 malicious canaries,
  runnable demo, and safety README are consumed by security, activation,
  end-to-end canary, and fixture-hygiene tests; no fixture deletion belongs in
  the close-out PR.
- Merge state — PR #38 merged to main as `bfb2d2d`; ADR 0017 is Accepted +
  Implemented.

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
