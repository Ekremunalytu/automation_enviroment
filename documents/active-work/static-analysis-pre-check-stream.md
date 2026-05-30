# Static Analysis Pre-Check Stream (Active Work Tracker)

`Last Updated: 2026-05-30 — ES-2 hardened automation_static_analyzer container scaffold + runtime stub on branch static.`

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
| ES-3a | 6 in-house Python rules (s1/s2/s3) + static runner | PENDING |
| ES-3b | Decision gate + orchestrator wiring; 7-step order + `empty_job_steps` extension (the ES-1 regression mitigation) land here | PENDING |
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
