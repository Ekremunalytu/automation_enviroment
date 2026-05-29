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

## Audit Findings — Open (2026-05-29)

Cross-audit (self + Codex) after ES-1a (`33cfdfc`) + the tshark fix
(`ac79c1e`) landed on `static`. All four are ES-1 scope, cheap, and
schema-first (close while the contracts are still producer-free). Owner
fixes these; no agent edits. Severity is yüzey-önem, not a live exploit
(no static producer exists yet — rules land ES-3a/ES-4).

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
