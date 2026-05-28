# Static Analysis Pre-Check — Stream Handoff (Post-Abandonment)

`Status: FROZEN — ABANDONED 2026-05-28 on the week22 branch, just before deletion of the extrace-static branch + removal of the parallel worktree at /Users/ekrem/Desktop/Automation-Enviroment-extrace-static. Preserved for design-intent recovery if the static-analysis pre-check stage is resumed later, serially, from main. Companion to W19-X-handoff / W20-handoff / W21-handoff; same convention.`

> **Status**: branch `extrace-static` was abandoned 2026-05-28 after
> ES-0 + ES-1 landed locally (8 commits, also pushed to
> `origin/extrace-static`; remote branch deleted 2026-05-28
> alongside the local branch and the secondary worktree).
> Reason: parallel-worktree development on a shared-Docker project
> turned out to cost more operationally (container_name collisions,
> port juggling, mental overhead of two stacks) than it saved.
> Decision: delete the branch, resume the work serially on a single
> branch off main when the time is right.
>
> **This doc exists to preserve the design intent so a future session
> can resume without re-debating the settled decisions.** None of the
> in-repo artifacts on `extrace-static` (ADR 0014, lane doc, stream
> tracker, ES-1 handoff doc) survive the branch deletion — but the
> design is captured here.

`Authored: 2026-05-28 by Claude Opus 4.7 on the extrace-static worktree
at /Users/ekrem/Desktop/Automation-Enviroment-extrace-static, just
before branch deletion. Landed on the week22 branch (primary worktree)
verbatim with one factual correction on the "never pushed to origin"
line (origin/extrace-static did exist; deleted alongside the local
branch).`

---

## Driving signal (why this work is worth doing)

The current pipeline runs dynamic-only through a Docker sandbox
(`automation_executor`, VS Code + Playwright). Every analyze job pays
1–5 minutes of sandbox spin even when the extension is obviously
malicious. **Pre-flight signals — manifest red flags, typosquats,
embedded native binaries, JS literal `eval` / `Function` /
`child_process` patterns — are observable WITHOUT executing the
extension.** A pre-execution stage adds:

1. **Cheap reject path** for known-bad extensions (no sandbox spin)
2. **Defense-in-depth**: catches adversarial markers that don't depend
   on activation (which a malicious extension can suppress / delay /
   environment-fingerprint)
3. **Detection-surface expansion** orthogonal to ADR 0002's
   dynamic-stage threat model

---

## Four locked design decisions

These were vetted in operator review and should NOT be re-debated when
resuming.

### 1. Block-and-warn semantics

- **CRITICAL findings → new terminal status `rejected_static`**
  (dynamic stage skipped; downstream steps marked `skipped`)
- **LOW / MEDIUM findings → warn**; dynamic stage proceeds and the
  warnings ride along in the bundle
- Truth table lives in ADR 0014 §Sub-decisions; effectively:
  CRITICAL → BLOCK; HIGH × HIGH-conf typosquat (curated allowlist) →
  BLOCK via `_PROMOTED_HIGH_BLOCKERS = frozenset({"extrace.s2.typosquat"})`;
  everything else → WARN or ALLOW

### 2. Separate Docker container

- New `automation_static_analyzer` service, NOT inline in
  `install_extension` and NOT inside the existing executor
- Security envelope: `network_mode: "none"`, non-root user, no
  `cap_add`, no `docker.sock` mount, `cap_drop: [ALL]`,
  `no-new-privileges: true`
- Resource caps: `mem_limit: 1g`, `cpus: 1.0`
- IPC: read-only mount of `${EXECUTOR_EXTENSIONS_HOST_PATH}` →
  `/extensions-input:ro`; read-write mount of
  `${EXECUTOR_OUTPUT_HOST_PATH}` → `/results:rw`. NO host network, NO
  Docker socket.

### 3. Schema-first contract landing

- Pydantic contracts land BEFORE any tool runner
- **Operator quote**: *"Schema = contract. Tool entegrasyonları
  schema'ya map'lenir, schema tool'a değil."* Tools map INTO the
  schema, not the reverse. Prevents the failure mode of "schema
  evolves to fit Semgrep's quirks → forced refactor when YARA / Trivy
  enroll in v2".

### 4. MVP tool stack: in-house Python rules + Semgrep

- **MVP shipped**: in-house Python rules (6 production rules across
  s1/s2/s3 namespaces) + Semgrep with 4 custom YAML rules
- **Deferred to v2** (each via separate ADR 0014 amendment + iter):
  YARA (embedded artifact + base64-decoder co-occurrence), Trivy fs
  CVE scanning (needs DB-freshness audit-trail design + `not_applicable`
  posture for lockfile-less extensions), TLSH fuzzy-hash identity
  (needs fuzzy-hash schema extension), CodeQL interprocedural taint
  (needs a concrete dataflow miss case Semgrep can't cover + LOC /
  image-size justification)

---

## Sub-iter slate (ES-0 → ES-5)

### ES-0 — Doc reconcile (lost on branch delete)

**Artifacts**: ADR 0014 (Proposed) + agent-lane doc + stream tracker +
handoff doc + arch test pinning ADR existence + Status marker.

**Pattern reference**: mirrored W20-handoff.md / W19-X-handoff.md
structural shape.

### ES-1 — Schema landing (lost on branch delete; carries a known regression)

**Pydantic contracts** under
`packages/analysis_contracts/static_detection/`:

- `finding.py`:
  - `StaticEvidenceRef` — `type` (Literal pre-shipped to
    `manifest | source_file | binary_file | lockfile | dependency`),
    `relative_path: str`, `line_number: int | None`, `snippet: str | None`,
    `tool: str`, `rule_match_id: str | None`
  - `StaticDetectionFinding` — mirrors the dynamic `DetectionFinding`
    field set (id ULID 26, rule_id, rule_version, rule_lifecycle,
    categories with `attack.T*` / `extrace.ext.*` / `extrace.host.*`
    namespace validation, severity, confidence, title, description,
    evidence, adversary_class, mitigation_hint). Reuses
    `Severity` / `Confidence` / `RuleLifecycle` / `AdversaryClass`
    from `packages.analysis_contracts` BY IDENTITY (not parallel
    clones).
- `report.py`:
  - `StaticToolExecutionRecord` — `tool` (Literal pre-shipped to
    `inhouse | semgrep | yara | trivy`), `version`, `rules_loaded`,
    `findings_emitted`, `duration_ms`, `db_freshness_days: int | None`
    (for v2 Trivy)
  - `StaticSeverityCounts` — one int per `Severity` tier
  - `StaticDetectionReport` — findings + tool_executions +
    severity_counts + generated_at + schema_version
- `gate.py`:
  - `StaticGateDecision` ContractStrEnum — ALLOW / WARN / BLOCK
  - `StaticGateOutcome` — decision, blocked_by (finding IDs),
    warned_by (finding IDs), allow_reason (None on WARN/BLOCK),
    decided_at

**Bundle wrapper** at
`appcore/contracts/schema_defs/static_analysis_bundle.py`:

- `StaticAnalysisReport` — detection_report + gate_outcome
- `CombinedAnalysisBundle` — static_report + dynamic_bundle:
  `AnalysisBundle | None` (None when the gate BLOCKED)

**Public facade**: re-export `StaticAnalysisReport` +
`CombinedAnalysisBundle` from `appcore/contracts/schemas.py`.

**Status / step contract extension** at
`appcore/contracts/schema_defs/analysis_jobs.py`:

- Append `"rejected_static"` to `ANALYSIS_JOB_STATUSES` tuple +
  `AnalysisJobStatus` Literal (terminal — NOT added to
  `ACTIVE_ANALYSIS_JOB_STATUSES`)
- Insert `"static_analysis"` + `"decision_gate"` into
  `ANALYSIS_JOB_STEP_NAMES` tuple + `AnalysisJobStepName` Literal
  between `"install_extension"` and `"build_triggers"` →
  **canonical 7-step order**
- Mirror `static_report_path: str | None` field on
  `AnalysisJobCreateSnapshot` + `AnalysisJobUpdate` so the new ORM
  column surfaces through the snapshot read-view

**⚠️ KNOWN REGRESSION on the branch**: the step Literal extension
broke `workflows/marketplace/job_service.py:64::empty_job_steps`,
which still emits 5 steps. `_validate_steps` (via
`AnalysisJobCreateSnapshot.validate_steps`) now requires the 7-step
canonical order → every `create_job_snapshot()` raises ValidationError.
The bug was masked because all tests that exercise this path are
`requires_db` and `postgres_test` was not running during ES-1
validation. **Mitigation when resuming**: do NOT extend
`ANALYSIS_JOB_STEP_NAMES` in the schema-landing commit. Defer the
step Literal change to the orchestrator-wiring iter (ES-3b
equivalent), where `empty_job_steps` is updated in the same commit
to return 7 records with the new steps defaulting to `"skipped"`
when the static feature flag is off.

**ORM column** at `appcore/storage/model_defs/analysis_job.py`:
`static_report_path: Mapped[str | None]` nullable `String`. **Do NOT**
widen the partial unique index `uq_analysis_jobs_single_active` WHERE
clause — `rejected_static` is terminal and stays out of the active
set.

**Alembic migration**: simple add_column / drop_column round-trip.
Down-revision pin: whatever the current head is at resume time
(`alembic heads`).

**Tests** (3 arch files + 1 Postgres-only round-trip):

- `test_static_detection_contracts.py` (10 invariants: field-set
  parity, enum identity reuse, evidence ref shape, v2 tool Literal
  pre-ship, report wrapper, severity counts ↔ Severity parity, gate
  decision three-way, gate outcome shape, tool execution record shape,
  combined bundle composition)
- `test_analysis_step_order_includes_static.py` (4 invariants:
  7-step canonical order, Literal mirror, `_validate_steps` rejects
  out-of-order + accepts canonical) — **AUTHOR IN ES-3b**, not ES-1,
  per the regression mitigation above
- `test_rejected_static_terminal_status.py` (5 invariants: status
  membership, terminal-not-active, Literal mirror, partial unique
  index WHERE unchanged, ORM column present)
- `tests/platform/storage/test_alembic_static_report_path_migration.py`
  (`requires_db`; mirrors `test_alembic_cancelling_migration.py` shape
  using the `fresh_alembic_engine` fixture)

**W13-3 ripple** at `test_job_state_invariants.py`: rename
`canonical_six` → `canonical_seven`, add `rejected_static` to the
expected status set, bump count from 6 to 7. W13-3 cancelling
invariants stay untouched.

**Pre-ship rationale**: v2 evidence types and v2 tool slots land on
the Literals at ES-1 even though MVP only emits 2 evidence types and
2 tools. The defensive posture costs zero runtime but prevents a
forced schema migration when v2 tooling enrolls.

### ES-2 — Container scaffold (designed only)

**Surface**:

- `docker/static_analyzer/Dockerfile` — Python 3.12-slim, non-root
  `static` user, NO Semgrep yet (lands at ES-4)
- `docker/static_analyzer/requirements.txt` — pydantic, pyyaml only
- `docker-compose.yml` `static_analyzer` service — full security
  envelope per Decision #2
- `executor/static_host.py` — clone of `_run_docker_exec` for the
  new container
- `executor/static_control.py` — clone of `ExecutorControl`
- `packages/analysis_engine/static_runtime/__init__.py` +
  `entrypoint.py` — argparse stub (`--vsix-dir`, `--report-path`,
  `--rules-version`, `--timeout-budget-s`); writes an empty
  `StaticDetectionReport` for now (ES-3a wires the real runner)
- `executor/config.py` extensions:
  `settings.static_analyzer.{CONTAINER_NAME, DOCKER_EXEC_TIMEOUT,
  ENTRYPOINT_MODULE}` + `settings.static_analysis.{ENABLED, TIMEOUT_S}`
- Makefile: `static-up`, `static-shell`, `static-run-fixture`
- Tests: `tests/smoke/test_static_container_smoke.py`,
  `tests/security/test_static_container_isolation.py`
  (enrolled into `make test-security`),
  `tests/executor/test_static_control.py`

### ES-3a — In-house rules MVP (designed only)

**Rule modules** under `packages/analysis_engine/static_rules/`:

- `__init__.py`, `base.py`, `registry.py`
- `s1_manifest_red_flags.py` — 3 rules:
  - `activationEvents = ["*"]` wildcard
  - Suspicious permission combinations
  - Missing or generic publisher
- `s2_typosquat_static.py` — 1 rule; REUSES
  `packages/analysis_engine/rules/a3_typosquat.py::_nearest_popular_match`
  + `popular_extensions.txt`
- `s3_file_tree_heuristics.py` — 2 rules:
  - Embedded native binaries (.node / .so / .dylib / non-UTF text
    over a threshold)
  - Unusual file size or encoding signatures

**Runner** at `packages/analysis_engine/static_runner.py`:
`run_static_detection_engine(vsix_dir, ...)` mirrors
`packages/analysis_engine/runner.py::run_detection`.

**Reuse hooks**:
`workflows/extension_catalog/manifest_reader.py::get_package_json`
and `workflows/extension_catalog/manifest_parser.py` for manifest
parsing.

**Arch boundary test**:
`tests/architecture/test_static_runner_does_not_import_workflows.py`
pins the `packages/` boundary (static rules cannot import
`workflows.*`).

**Per-rule unit tests**: fire / silent cases for each of the 6 rules.

### ES-3b — Decision gate + orchestrator wiring (designed only)

**`workflows/marketplace/static_analysis.py`** (new):

- `run_static_analysis(vsix_dir, settings) -> StaticAnalysisReport`
- `evaluate_static_gate(report) -> StaticGateOutcome` — applies the
  block-and-warn truth table
- `_PROMOTED_HIGH_BLOCKERS = frozenset({"extrace.s2.typosquat"})`
  (FROZENSET, not config — changes require an ADR amendment +
  commit audit trail)
- `StaticAnalysisBlockedError(RuntimeError)` — raised when the gate
  blocks
- `build_combined_bundle(static_report, dynamic_bundle | None)`

**`workflows/marketplace/analysis_execution.py`** extension: step
helpers + failure-message helpers mirroring `install_failure_message`.

**`workflows/marketplace/analysis_service.py`** modification:

- Insert `_run_static_analysis` + `_evaluate_static_gate` between
  `ensure_vsix` and `_reset_sandbox`
- Gate on `settings.static_analysis.ENABLED` (feature flag OFF by
  default at ES-3b; flipped at ES-5 close-out)
- On `StaticAnalysisBlockedError`: route to `reject_static_job`, mark
  remaining dynamic steps `skipped`, persist `combined_bundle_path`
- Add to `ANALYZE_RECOVERABLE_ERROR_TYPES`; map to HTTP 422

**`workflows/marketplace/job_service.py`**:

- **Update `empty_job_steps`** to return 7 step records, with the 2
  new steps defaulting to `"skipped"` (off-by-default flag) or
  `"pending"` (flag-on); this is where the ES-1 regression on
  extrace-static gets correctly resolved
- `reject_static_job` — public wrapper

**`appcore/storage/crud_ops/analysis_jobs/static_gate.py`** (new):

- `reject_analysis_job_static` — mirror of
  `finalize_cancelled_analysis_job` (same row-locked transition
  pattern). Re-exported via `appcore/storage/crud.py`.

**Cancellation** via `_run_static_off_thread` coordinator (mirror of
W18-2's `_run_reset_off_thread` from `analysis_execution.py:166`):

- ~100ms cancel-poll
- Cancel → `pkill -f static_runtime.entrypoint` inside the
  `automation_static_analyzer` container
- Coordinator thread cleanup mirrors heartbeat-thread shape

**Tests**:

- `test_static_analysis_pipeline.py` — allow / warn / block paths
- `test_decision_gate.py` — severity × confidence parametrize
- `test_static_blocked_job_state.py` — DB state machine for
  `rejected_static`
- `test_combined_bundle.py`

### ES-4 — Semgrep integration (designed only)

**Dockerfile**: Semgrep CLI added (pinned wheel + version). Image
rebuilds at ES-4 (not ES-2) so ES-2 scaffold lands lean.

**Ruleset**: `packages/analysis_engine/static_rules/semgrep/extrace-vsix-js.yml`
— 4 custom rules:

- `extrace.s4.semgrep.eval_with_external_input` — HIGH severity,
  MEDIUM confidence
- `extrace.s4.semgrep.process_spawn` — HIGH / MEDIUM
- `extrace.s4.semgrep.vm_run_in_context` — HIGH / HIGH
- `extrace.s4.semgrep.dynamic_require_nonliteral` — MEDIUM / MEDIUM

**Runner**:
`packages/analysis_engine/static_runtime/tools/semgrep_runner.py`:

- subprocess invocation:
  `semgrep --config /opt/semgrep-rules --json --metrics=off
  --disable-version-check --error-on-findings false <vsix_dir>`
- ENV `SEMGREP_SEND_METRICS=off`
- Maps Semgrep JSON output to `List[StaticDetectionFinding]` with
  `tool="semgrep"`
- Emits `StaticToolExecutionRecord(tool="semgrep", version=...,
  rules_loaded=..., findings_emitted=..., duration_ms=...)`

**Tests**:

- `test_semgrep_runner.py` — golden-file against canary fixture
- `test_static_runtime_no_subprocess_escape.py` — argv injection
  refused from manifest-injected payloads

**Version drift mitigation**: wheel pin is the only thing keeping
rule semantics stable. CI must rebuild the image when the pin
changes; a pre-commit hook or arch test should pin the version
comparison.

### ES-5 — Close-out (designed only)

- ADR 0014 status flip: Proposed → **Accepted and implemented**
- UI surfaces:
  - `ui/src/.../StaticFindingsPanel.tsx` (new)
  - `ui/src/.../AnalysisReportPanel.tsx` (modify — render combined
    bundle when present)
  - `ui/src/.../JobStatusBadge.tsx` (new `rejected_static` variant)
- `make ui-types` regen against the extended schemas
- `appcore/api/marketplace.py` `AnalyzeResponse` extension:
  `combined_bundle_path: str | None`, `static_summary: dict | None`
- `.env.example` `EXTRACE_STATIC_ANALYSIS_ENABLED=true` flip (only
  after the smoke evidence below passes)
- Smoke `tests/smoke/test_full_static_to_dynamic_pipeline.py`:
  - `extensions/malicious/t1-a3-typosquat-canary/` → expect job
    transitions to `rejected_static`
  - `extensions/extrace.fixture-cmd-0.0.1/` → expect allow + dynamic
    flow + `CombinedAnalysisBundle` with zero static findings + a
    non-empty dynamic bundle
- PR open: pending user approval per turn

---

## Lessons learned (apply when resuming)

1. **Single-worktree, serial development on shared-Docker projects.**
   Parallel-worktree streams add operational overhead (Docker stack
   collisions, `container_name` overrides, port shifts,
   `COMPOSE_PROJECT_NAME` juggling, two `.venv`s, two trackers) that
   exceeds the time saved by parallel progress on a small team. When
   resuming, open ONE branch off main and work serially with the main
   Docker stack.

2. **`empty_job_steps` is the canonical step producer; treat
   `ANALYSIS_JOB_STEP_NAMES` as a public contract.** Any change to
   the step tuple MUST update the producer in the SAME commit, or the
   validator must be relaxed. Default status for new steps when the
   feature flag is off is `"skipped"` (matches state-machine
   semantics). Default `"pending"` is fine when the flag is on. ES-1
   on extrace-static missed this; mitigation: put the step Literal
   change in the orchestrator-wiring commit (ES-3b equivalent), not
   the schema commit.

3. **v2 Literal pre-shipping is the right discipline.** The 5
   evidence types (manifest / source_file / binary_file / lockfile /
   dependency) and 4 tool slots (inhouse / semgrep / yara / trivy)
   land on the Literals at ES-1 even though MVP only emits 2 of each.
   Defensive posture: zero runtime cost, no forced schema migration
   when v2 enrolls.

4. **Schema-first is the right disciplining principle.** Don't let
   Semgrep's JSON quirks shape `StaticDetectionFinding`. If a tool
   field doesn't fit, write a mapper; don't bend the contract.

5. **The four design decisions don't need re-debating.**
   block-and-warn / separate container / schema-first / in-house +
   Semgrep MVP were vetted in operator review. Re-opening any of
   these requires an ADR 0014 amendment, not a fresh design round.

6. **Tests against a live DB matter even at ES-1.** The ES-1
   regression was masked because all DB-touching tests were
   `requires_db`-skipped (postgres_test was not running). Before
   declaring a schema iter green, bring up postgres_test (or its
   isolated equivalent) and run the full suite. Don't trust the
   skipped-test count.

---

## Resume plan (when picking this up later from main)

1. **Branch off main**: `git checkout -b <single-branch-name>` (no
   parallel worktrees; no `extrace-static`-style operator-reserved
   namespace).
2. **Re-author ES-0 ADR + lane doc + stream tracker.** Shorter than
   the original because the four decisions are settled per this doc.
   Cross-reference this handoff in the new ADR's "Source" section so
   the trail isn't lost.
3. **ES-1 schema landing — REVISED**: author the Pydantic contracts
   (`packages/analysis_contracts/static_detection/`), the bundle
   wrapper, the `rejected_static` terminal status, the
   `static_report_path` ORM column, the Alembic migration, the
   contract / status / terminal arch tests, and the Alembic
   round-trip. **DO NOT extend `ANALYSIS_JOB_STEP_NAMES` in this
   iter.** Defer the step Literal change + `empty_job_steps` update
   to ES-3b.
4. **ES-2 container scaffold, ES-3a in-house rules, ES-3b
   orchestrator wiring (incl. step Literal extension +
   `empty_job_steps` update + W13-3 `canonical_six` →
   `canonical_seven` ripple), ES-4 Semgrep integration, ES-5
   close-out** — per the sub-iter sections above.
5. **Single worktree, single Docker stack** throughout. Don't open a
   parallel stream.

---

## Recovery references (now dead post-deletion)

These were the SHAs on the `extrace-static` branch before deletion:

- `f150c38` — ES-0 doc-reconcile (original W21-0 framing; ADR named
  0013 here)
- `cff6e67` — ES-1 handoff doc (covers ES-1 only at high fidelity)
- `870ec4f` — post-merge rename (ADR 0013 → 0014, W21-0 → ES-0,
  tracker / handoff path renames, arch test rename)
- `a7425b5` — merge from main (W21 closure sync)
- `564dcb8` — ES-1 primary commit (schema landing — **carries the
  step Literal regression**; if a future operator wants to consult the
  pre-deletion `origin/extrace-static` for raw diff context, they must
  recover from a developer's local reflog before git's GC window
  expires; otherwise the only authoritative record is this doc)
- `00d6c66` — ES-1 self-stamp (tracker row flip + Per-Item Detail
  backfill)
- `79917d8` — compose override + Makefile `es-*` lane (stream
  tooling; not relevant when working from main serially)
- `c1710e6` — `make help` wiring for the `es-*` targets

All eight SHAs are intentionally unrecoverable from the canonical
repo after 2026-05-28. The design is captured here; the code
artifacts are intentionally not preserved.

---

## Cross-links (in-repo, dead post-deletion)

These were the canonical surfaces on the abandoned branch. They are
listed for forensic completeness; they do NOT exist after the
2026-05-28 deletion.

- ADR 0014: `documents/adrs/0014-static-analysis-stage.md`
- Lane doc: `documents/agent-lanes/static-analysis-pre-check.md`
- Stream tracker: `documents/active-work/extrace-static-stream.md`
- ES-1 handoff: `documents/active-work/extrace-static-handoff.md`
- Arch test (ADR presence): `tests/architecture/test_adr_0014_present.py`

(Note: when this doc was originally drafted on the extrace-static
worktree, the highest ADR number on main was 0013. By the time this
doc was landed on `week22`, the highest ADR on main was 0015
(W22-4 sandbox-evasion defense policy). A future re-author should
pick the next free ADR number at resume time — not 0014.)

When resuming from main, recreate equivalents at fresh paths
following whatever doc convention is current at that time.
