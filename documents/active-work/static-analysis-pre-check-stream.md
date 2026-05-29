# Static Analysis Pre-Check Stream (Active Work Tracker)

`Last Updated: 2026-05-29 — ES-0 doc-reconcile landing on branch static.`

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
| ES-0 | Doc-reconcile: ADR 0016 (Proposed) + lane doc + this tracker + ADR existence arch test | IN PROGRESS |
| ES-1 | Schema landing: static-detection contracts + combined bundle + `rejected_static` terminal status + `static_report_path` ORM column + Alembic. No step-Literal change. | PENDING |
| ES-2 | Hardened `automation_static_analyzer` container scaffold + runtime stub | PENDING |
| ES-3a | 6 in-house Python rules (s1/s2/s3) + static runner | PENDING |
| ES-3b | Decision gate + orchestrator wiring; 7-step order + `empty_job_steps` extension (the ES-1 regression mitigation) land here | PENDING |
| ES-4 | Semgrep integration (version-pinned wheel + 4 custom JS rules) | PENDING |
| ES-5 | Close-out: UI surfaces + `AnalyzeResponse` extension + smoke evidence + feature-flag flip; ADR 0016 → Accepted | PENDING |

## Per-Item Detail

### ES-0 — Doc-reconcile (IN PROGRESS)

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
