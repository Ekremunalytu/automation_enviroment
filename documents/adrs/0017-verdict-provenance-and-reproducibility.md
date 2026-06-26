# ADR 0017 — Verdict Provenance & Reproducibility

- Status: **Proposed** (2026-06-25). Authored at Stream 3 (`verdict-provenance-
  reproducibility`) H0. Stays `Proposed` until the stream's S2–S6 implementation
  + N-run determinism evidence land; flips to `Accepted + Implemented` at
  close-out.
- Date: 2026-06-25 (Proposed)
- Authors: ekrem + Claude
- Driving stream: `verdict-provenance-reproducibility` (v1.0 Stream 3, the
  spine) — closes bars B5 + B6.
- Related: ADR 0010 (executor/logger observability — `run_id`/`attempt_id`
  adjacency), ADR 0013 (container isolation baseline), ADR 0016 (static
  pre-check stage — amended here with an additive `--vsix-sha256` flag), ADR
  0004 (synthetic-corpus safety), report contract (`packages/analysis_contracts`).
- Source: `documents/active-work/v1-roadmap.md` §3 (B5/B6 acceptance), §4 (spine
  decision), §5 corrected design decisions; `documents/active-work/
  W26-verdict-provenance-reproducibility.md`.

## Context

ExTrace produces a single verdict on a single extension. Two trust defects in
that verdict block everything downstream (measurement, export, batch):

1. **Not bound to the bytes (B5).** No `vsix_sha256` ties a report to the exact
   archive scanned. A re-published malicious update at the same version string is
   conflated with an earlier clean scan — the operator cannot prove *which bytes*
   a verdict describes. The report already carries `executor_fingerprint`
   (producer build provenance); it carries **no input provenance**.
2. **Not reproducible (B6).** The verdict itself is already a pure function of
   `(findings, automation_health.status)` (`packages/analysis_contracts/
   detection/rollup.py::compute_verdict` does not read `run_quality`), so the
   verdict is reproducible *by construction*. But the `run_quality` anchor the
   operator reads alongside it flickers `degraded`/`inconclusive` on identical
   inputs, because finalization-time event attribution and a fixed startup grace
   make the reason set timing-dependent. A flickering anchor reads as an
   unstable verdict even when the verdict is stable.

## Decision

### B5 — one hash, computed once at analyze-start, threaded to three consumers, agreement-asserted

`vsix_sha256 = hashlib.sha256(<staged .vsix bytes>).hexdigest()` (canonical
64-char lowercase) is computed **once at analyze-start** — in
`start_analysis_job`, from the `ensure_vsix_exists(request)` path, i.e. the exact
archive *this run is about to scan* — streamed in chunks to bound memory (the
archive is already size-gated at ingest). Computing at analyze-start rather than
at the ingest chokepoint (`persist_and_extract_vsix_bytes`) is deliberate: the
analyze flow does not re-enter the ingest path (it reads an already-staged
`.vsix`), and hashing the bytes the run actually consumes binds the verdict to
*those* bytes — catching any post-ingest replacement and avoiding an
Extension-catalog schema change. It is threaded to the worker, persisted on
`AnalysisJob`, and fanned out to three consumers, each of which **stamps its own
output**:

1. **`AnalysisJob`** — a new nullable `vsix_sha256` column, written through the
   CRUD snapshot. Persistence so the row, the history, and any later export carry
   the input identity.
2. **Dynamic report (`ActivationReport`)** — an additive-optional contract field,
   stamped at the report-builder **emit boundary**, exactly mirroring the
   `executor_fingerprint` precedent. The value crosses the container boundary as
   a new `--vsix-sha256` arg on `run_playwright_automation` → the `host.py`
   docker-exec argv → the entrypoint. Schema version `2.2 → 2.3`.
3. **Static report (`StaticDetectionReport`)** — an additive-optional contract
   field, stamped by the static runner. The value crosses the hardened static
   container boundary as an additive **5th flag** `--vsix-sha256` on the
   `executor/static_host.py` invocation contract (ADR 0016 frozen it at four
   flags; this ADR amends it to five — additive, optional, backward-compatible).

The orchestrator then **checks agreement**: `analyze-start ==
dynamic-report-stamp == static-report-stamp`. Agreement is not assumed by
construction — it is verified, so a mis-wired thread surfaces rather than
producing a silently wrong provenance claim. The runtime check is **non-raising**
(it logs an ERROR on a non-empty disagreeing stamp): a raise inside the analyze
worker would escape its closed error taxonomy (`ANALYZE_ERROR_TYPES`) and wedge
the single-active queue, so the runtime path logs and the **hard agreement
assertion lives in the S7 provenance test**. This satisfies the roadmap's
"dynamic / static / bundle outputs agree for the same analyzed bytes".

Contract tests accept legacy blank/default values (`""`) but require new producer
paths to emit a canonical hash — same backward-compatibility posture as
`executor_fingerprint`.

### B6 — reproducible by construction + deterministic finalization

The verdict stays a pure function of `(findings, automation_health.status)`. To
stop the **anchor** flicker:

- **Partition `run_quality_reasons`** into *behavioral* (what the extension did)
  vs *harness-health* (how cleanly the sandbox ran), and add a labeled
  `residual_variance` band so bounded non-deterministic harness timing reads as a
  *named* state instead of silently tipping the discriminator to
  `degraded`/`inconclusive`.
- **Remove the finalization non-determinism sources.** A multi-agent
  adversarial verification pass (2026-06-26) confirmed the real run_quality
  flicker drivers and corrected the initial design:
  - **(primary) live-FS read in the anchor** — `ActivationReport._log_capture_health`
    was a plain property that re-`stat()`ed the exthost log on *every* access, so
    `extension_host_log_missing` flickered run-to-run AND the ~6 property reads
    across `print_summary` + `save` could derive `run_quality` /
    `run_quality_reasons` / `run_quality_reason_partition` from *different* FS
    snapshots in one report. Fix: freeze the capture-health view once at the end
    of `stop()` (after the grace + discovery merge + refresh) onto an in-memory
    `log_capture_health_snapshot`; the property returns the snapshot when frozen,
    else a live read (fallback mandatory for `log_health` + fixture paths).
  - **startup grace** — the fixed `sleep(2.0)` raced the async exthost.log flush
    that decides `target_extension_observed`; replaced by a bounded poll that
    re-parses the logs read-only and early-exits the instant the target's
    activation appears, keeping a 2.0s deadline as the (strict-superset) upper
    bound.
  - **band correction** — `harness_ready_marker_stale` / `harness_activation_timeout`
    are never appended to `automation_health.reasons` (they surface as a
    behavioral `skipped_scenarios_present`), so `_RESIDUAL_VARIANCE_REASON_CODES`
    is narrowed to the four reachable codes, guarded by a reachability test.
  - **deferred (NOT B6)** — the `_nearest_activation_matches` equal-delta
    tie-break is real non-determinism but was confirmed *not* to affect
    run_quality (status is delta-driven; only `related_activation_event` flips,
    whose consumer is the B5 signal/correlation path). A stable sort there would
    change `correlated_groups` grouping and can shift a B5 verdict, so it is
    recorded as `[FOLLOWUP attribution-tiebreak-determinism]` for the signal
    owner, not bundled into B6.

> **Corrected root cause (adversarial-verified, 2026-06).** The flicker is **not**
> `_cheap_target_reaction_count`. That field reads `is_target_extension_event`,
> which defaults `False` and is set `True` only at finalization, so it is
> always-zero mid-loop and the W25 early-give-up keyed on it is deterministic.
> The real source is finalization-time attribution + activation/log flush timing.
> A future change must not "fix" `_cheap_target_reaction_count` as the flicker
> source (it is a separable dead-signal observation).

## Alternatives considered

- **(a) Orchestrator post-hoc stamping** — let the orchestrator write
  `vsix_sha256` onto both reports after they return, avoiding the two container
  boundary changes. **Rejected**: the report written to `/results` inside the
  container would not be provenance-complete until a later pass; it diverges from
  the `executor_fingerprint` precedent (which stamps in-container); and it cannot
  *cross-check* agreement (it would just write its own value with nothing to
  verify against). The chosen design keeps each producer self-describing and lets
  the orchestrator verify, not assume.
- **(b) In-container archive re-hash (gold standard)** — mount the `.vsix` into
  the executor and re-hash exactly the bytes scanned. **Deferred**: the container
  scans the *extracted* tree, not the archive, so it cannot today re-derive the
  archive hash without extra plumbing. The intake hash threaded + agreement-
  asserted is the pragmatic v1 choice that meets B5 acceptance; the re-hash is
  recorded as future hardening.
- **(c) Hash the extracted tree instead of the archive** — **Rejected**:
  extraction is not bit-reproducible across zip implementations; the archive byte
  hash is the stable, operator-meaningful identity ("these exact downloaded
  bytes").

## Consequences

- **Positive**: a verdict is now provably bound to a specific archive; a
  re-published same-version sample is no longer conflated; the `run_quality`
  anchor stops flickering on identical inputs; downstream measurement (B7/B8) and
  export (B9) build on a stable, attributable anchor.
- **Cost**: two report contracts gain a field (each a 4-atomic-touch incl.
  generated TS DTO); two container invocation contracts gain an additive flag
  (ADR 0016 amended); one additive-nullable DB column + migration.
- **Backward compatibility**: every new field defaults to `""`/nullable; legacy
  fixtures and pre-2.3 reports still validate; the static container's 4-flag
  surface stays callable.
- **Bounded risk**: the B6 attribution/grace changes touch executor finalization
  — guarded by an N-run determinism test on the reference target and an
  `attribution_summary` regression check.

## Status flip criteria

Flip to `Accepted + Implemented` at stream close-out when: both report contracts
carry `vsix_sha256`; the orchestrator agreement-assertion is live; the
`AnalysisJob` column + migration land; the `run_quality` partition + finalization
determinism ship; and the N-run determinism + byte-different-not-conflated tests
are green.
