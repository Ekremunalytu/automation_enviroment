# Static Analysis Pre-Check — ES-1b Resume Handoff

`Authored: 2026-05-29. Purpose: carry full state into a fresh session so
the Static Analysis Pre-Check Stream can resume at ES-1b with zero prior
chat context. Companion to the frozen design-intent doc
extrace-static-stream-handoff.md (field-level spec for ES-2..ES-5).`

## TL;DR — where we are

- Working on branch **`static`** (cut from `main`). Strict per-sub-iter
  gate; one commit per sub-iter on green.
- **ES-0 ✅ committed `735fdf0`** · **ES-1a ✅ committed `33cfdfc`** — both
  passed full `make check-all` (2142 passed, `postgres_test` up).
- **ES-1b ⏸️ NOT STARTED — awaiting user approval** (it mutates a shared
  lifecycle contract + adds a DB migration = "critical", needs an explicit
  go-ahead first).
- ES-2 → ES-5 PENDING.
- ⚠️ Branch is **7 commits over main**, only **2 are static** (`735fdf0`,
  `33cfdfc`); the other 5 are unrelated owner work — see §Open decisions.

## How to resume (first actions for the new session)

1. Read this doc, then `documents/adrs/0016-static-analysis-pre-check-stage.md`
   (the decision record) and `documents/active-work/extrace-static-stream-handoff.md`
   (the frozen field-level spec for ES-2..ES-5). The full 3-day plan is at
   `~/.claude/plans/senden-statik-analiz-i-in-mellow-floyd.md`.
2. **Get explicit user approval before starting ES-1b** (memory
   `feedback_approve_critical_changes`). Push/PR also need a separate
   go-ahead (memory `feedback_pr_push_approval`).
3. Bring `postgres_test` up and keep the strict gate: `docker-compose up -d
   postgres_test && make check-all` green before each commit (the chosen
   discipline; `requires_db` tests must actually run — the ES-1 regression
   below was once masked by skipped DB tests).

## Locked design (do NOT re-debate — ADR 0016)

Four decisions, settled in operator review; changing any needs an ADR 0016
amendment, not a fresh design round:

1. **Block-and-warn**: CRITICAL → terminal status `rejected_static` (skip
   dynamic, downstream steps `skipped`); LOW/MED → warn + proceed; sole
   promoted blocker `_PROMOTED_HIGH_BLOCKERS = frozenset({"extrace.s2.typosquat"})`.
2. **Separate hardened container** `automation_static_analyzer`:
   `network_mode: none`, `cap_drop: [ALL]`, `no-new-privileges`, non-root,
   `mem_limit: 1g`, `cpus: 1.0`, RO `/extensions-input`, RW `/results`, no
   docker.sock.
3. **Schema-first**: contracts before tool runners; tools map INTO the
   schema. Enums reused BY IDENTITY from
   `packages/analysis_contracts/detection/enums.py`.
4. **MVP tools**: in-house Python rules (6) + Semgrep (4 YAML rules); YARA
   / Trivy / TLSH / CodeQL are v2 (Literal slots pre-shipped at ES-1).

Framing: this is a named stream (`ES-0`..`ES-5`), **not** a weekly `W<N>`
phase — avoids colliding with the ADR 0015 sandbox-evasion `W23+` roadmap.
`W22` remains the last merged phase; do not touch the canonical preamble
docs for this stream.

## DONE

### ES-0 — `735fdf0`

- `documents/adrs/0016-static-analysis-pre-check-stage.md` (Proposed)
- `documents/agent-lanes/static-analysis-pre-check.md`
- `documents/active-work/static-analysis-pre-check-stream.md` (tracker)
- `tests/architecture/test_static_analysis_adr.py`

### ES-1a — `33cfdfc` (additive, schema-first)

- `packages/analysis_contracts/static_detection/{__init__,finding,report,gate}.py`
  — `StaticEvidenceRef`, `StaticDetectionFinding` (field-set parity with
  the dynamic `DetectionFinding`), `StaticToolExecutionRecord`,
  `StaticSeverityCounts`, `StaticDetectionReport`, `StaticGateDecision`,
  `StaticGateOutcome`. v2 evidence types + tool slots pre-shipped.
- `appcore/contracts/schema_defs/static_analysis_bundle.py` —
  `StaticAnalysisReport`, `CombinedAnalysisBundle` (`dynamic_bundle` None on BLOCK).
- `appcore/contracts/schemas.py` — additive facade re-export (NOT yet in
  the UI `TARGET_SCHEMAS` allowlist; UI regen is ES-5).
- `tests/platform/contracts/test_static_detection_contracts.py` — 10 invariants.

## NEXT — ES-1b (awaiting approval; "critical")

Schema-first finished; this is the DB / shared-contract mutation. **Two
audit findings are folded in** (verified real this session — see §Audit).

**Base ES-1b set:**

- `appcore/contracts/schema_defs/analysis_jobs.py`: append `"rejected_static"`
  to `ANALYSIS_JOB_STATUSES` + `AnalysisJobStatus` Literal — **terminal,
  NOT added to `ACTIVE_ANALYSIS_JOB_STATUSES`**. Add `static_report_path:
  str | None = None` to `AnalysisJobCreateSnapshot` + `AnalysisJobUpdate`.
  **⚠️ DO NOT touch `ANALYSIS_JOB_STEP_NAMES` / `AnalysisJobStepName`** —
  the 7-step extension + `empty_job_steps` update land together in **ES-3b**
  (the regression mitigation; see §Gotcha).
- `appcore/storage/model_defs/analysis_job.py`: add `static_report_path:
  Mapped[str | None] = mapped_column(String, nullable=True)`. **Do NOT
  widen** the partial unique index `uq_analysis_jobs_single_active`.
- New Alembic migration `alembic/versions/<rev>_add_static_report_path_to_analysis_jobs.py`:
  `down_revision = "e7c0a8f3b9d2"` (current head). upgrade `op.add_column`,
  downgrade `op.drop_column`. Mirror the shape of
  `alembic/versions/c8a2d4e91f5b_add_cancelling_status_to_analysis_jobs.py`.
- `tests/architecture/test_job_state_invariants.py`: bump
  `test_analysis_job_statuses_tuple_matches_canonical_six` → seven (add
  `rejected_static`, `len` 6→7). The terminal-set / active-set /
  partial-index invariants stay UNTOUCHED.
- New `tests/architecture/test_rejected_static_terminal_status.py` (5
  invariants: status membership, terminal-not-active, Literal mirror,
  partial-index WHERE unchanged, ORM column present).
- New `tests/platform/storage/test_alembic_static_report_path_migration.py`
  (`requires_db`; mirror `test_alembic_cancelling_migration.py` using the
  `fresh_alembic_engine` fixture in `tests/platform/storage/conftest.py`).

**Folded-in audit fixes (cheap now — contracts are still producer-free):**

- `packages/analysis_contracts/static_detection/gate.py`: extend
  `StaticGateOutcome` with a `@model_validator(mode="after")` —
  `BLOCK ⟹ blocked_by` non-empty, `WARN ⟹ warned_by` non-empty,
  `ALLOW ⟹ both empty` (plus the existing allow_reason rule). + negative
  tests in `test_static_detection_contracts.py`.
- `packages/analysis_contracts/static_detection/finding.py`:
  `StaticEvidenceRef.relative_path` — reject absolute / `..` traversal /
  control chars (+ negative tests). **Snippet redaction is deferred to the
  ES-3a producer** (reuse `redact_secrets` from
  `packages.analysis_contracts.evidence`), NOT a DTO validator — keeps
  static consistent with the dynamic layering.
- `documents/active-work/static-analysis-pre-check-stream.md`: stamp the
  slate — flip ES-0 → DONE, split ES-1 into ES-1a (DONE) / ES-1b (PENDING).

**Then:** `postgres_test` up + `make check-all` + the new `requires_db`
migration test green → commit ES-1b.

## Remaining slate (field-level spec in extrace-static-stream-handoff.md)

- **ES-2** — `automation_static_analyzer` container scaffold + runtime
  stub; `executor/static_{host,control}.py`; config; Makefile
  `static-up`/`static-shell`/`static-run-fixture`; enroll
  `tests/security/test_static_container_isolation.py` into the **explicit**
  `test-security` Makefile list (no auto-discovery).
- **ES-3a** — 6 in-house rules (`s1` manifest, `s2` typosquat reusing
  `a3_typosquat._nearest_popular_match`, `s3` file-tree) + `static_runner.py`
  mirroring `packages/analysis_engine/runner.py::run_detection`. Snippet
  redaction lands here.
- **ES-3b** — gate + orchestrator wiring; **the 7-step order +
  `empty_job_steps` update + W13-3 ripple land here in one commit**; mirror
  `finalize_cancelled_analysis_job` for `reject_analysis_job_static`; mirror
  `_run_reset_off_thread` for `_run_static_off_thread`. Resolve the
  step-position question (recommend static runs BEFORE `reset_sandbox`).
- **ES-4** — Semgrep (version-pinned wheel + 4 JS rules).
- **ES-5** — UI surfaces, `AnalyzeResponse` extension, `make ui-types`
  regen (add to `TARGET_SCHEMAS`), smoke, feature-flag flip, ADR 0016 →
  Accepted.

## Gotcha — the ES-1 → ES-3b step-Literal regression

`appcore/contracts/schema_defs/analysis_jobs.py` defines exactly 5 step
names; `_validate_steps` requires an exact match; `empty_job_steps()`
(`workflows/marketplace/job_service.py`) emits those same 5. Extending the
step tuple WITHOUT updating the producer in the same commit makes every
`create_job_snapshot()` raise `ValidationError`. **So ES-1b does not touch
step names at all** — the 7-step change + `empty_job_steps` update + the
`test_job_state_invariants` step ripple all land together in ES-3b.

## Audit verdicts (this session — do not re-litigate)

A cross-audit (self + Codex) ran after ES-1a. Verified against HEAD blobs:

- ✅ **REAL, mine, fix in ES-1b**: gate decision-consistency
  (`gate.py`); evidence-boundary `relative_path` validation (`finding.py`).
- ❌ **STALE / already fixed**: "ADR 0013 Rationale 2-cap under-claim" —
  `3a23cbb` already updated the Rationale to the 5-cap set
  (`NET_RAW, SYS_PTRACE, SETUID, SETGID, SETPCAP`) at ~L173.
- ❌ **DISPUTED — do NOT do**: "enroll
  `test_static_detection_contracts.py` into `test-security`". It is a
  contract-invariant test that already runs under `make check-all`; the
  `test-security` enrollee is the future ES-2 container-isolation test.
- 🟡 **REAL but out-of-stream** (owner's doc/bug-fix domain, NOT static):
  W22 tracker body still says "W22 active" + uppercase `PENDING USER
  APPROVAL` (escapes the case-sensitive parity gate);
  `documents/README.md` still describes W19 (in neither preamble tuple);
  `tests/architecture/test_compose_isolation_invariants.py` docstring
  (~L15) still claims only `[NET_RAW, SYS_PTRACE]`; `documents/phase.json`
  gate has blind spots (tracker body + `documents/README.md`).

## Open decisions (need the user)

1. **Approve ES-1b** (revised set above) to begin — it is "critical".
2. **Branch contamination.** `static` = 7 commits over `main`; only 2 are
   static (`735fdf0`, `33cfdfc`). The other 5 are unrelated owner work —
   `ac79c1e` (tshark fix), `c5879bb` (file-capture runtime feat),
   `a12688e` (W22 banner truth-up), `3a23cbb` (ADR-0013 cap test),
   `4fdb5bf` (phase.json refactor). `origin/static` is at `ac79c1e`.
   A `static -> main` PR would bundle 5 unrelated concerns. Decide:
   keep one working branch (split into multiple PRs later via history
   surgery) vs. move the 5 non-static commits off `static` now (cherry-pick
   to `main` / a fix branch, then drop from `static`).

## Operating rules (carry forward)

- **Approval before critical changes** (DB migrations, shared-contract
  mutations, infra, flag flips) — even mid-task. ES-1b qualifies.
- **Push / PR / merge / branch-delete need an explicit same-turn go-ahead.**
- **Strict gate**: `postgres_test` up + `make check-all` (+ `make
  test-smoke` for container/pipeline iters) green per sub-iter; commit on green.
- `ruff-format` reformats files on commit (pre-commit hook) → re-`git add`
  and re-commit; this is expected, not an error.
- One commit per sub-iter; conventional message + AGENTS.md self-review
  trailer (files / DB-schema Y-N / tests Y-N / risks) + the
  `Co-Authored-By: Claude Opus 4.8 (1M context)` trailer.

## Key anchors

- Alembic head: `e7c0a8f3b9d2`. Mirror migration:
  `c8a2d4e91f5b_add_cancelling_status_to_analysis_jobs.py`.
- `StrictContractModel` = `BaseModel(extra="forbid")` in
  `packages/analysis_contracts/contracts.py`.
- UI contract generator uses an explicit `TARGET_SCHEMAS` list
  (`scripts/generate_ui_contracts.py`) — adding to `schemas.py` does NOT
  drift UI types until a name is added to that list (ES-5).
- Frozen design source for ES-2..ES-5:
  `documents/active-work/extrace-static-stream-handoff.md`.
