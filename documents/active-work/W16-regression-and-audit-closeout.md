# W16 — Carry-Over Closeout + Audit Findings + Production Regression (Active Work Tracker)

`Last Updated: 2026-05-18 (W16 active — close-out commit landed 2026-05-18; week16 -> main close-out PR pending. W16-0..W16-7 sub-iter slate complete: W16-0 doc-reconcile (0e243ca + d78aa9c); W16-1 pulled 01f910a (dispatch outcome=None emit-site closed) + a4a050e self-stamp; W16-2 pulled 9d6d110 (analysis-job worker-entry CRUD ownership facade extracted; AGENTS.md:57 compliance restored, W13-13 CAS preserved byte-identically) + c8b7811 self-stamp; W16-3 pulled fa430f2 (report-finalize null-leakage closed at strict-forbid contract seam; attribution-count-parity SPLIT to W17+ as [FOLLOWUP attribution-count-parity]) + e3d4a0c self-stamp; W16-4 pulled 304b99f (health/reconciliation.py 682 LoC split into security/handshake/reconciliation; W13-1 HMAC + W13-12 fail-closed gates preserved) + 384d276 self-stamp; W16-5 doc-only scope reduction e21a05c (1 rejected: dedupe-step-progress-schemas distinct surface roles; 2 deferred to W17+: heartbeat-sandbox-reset-off-thread + heartbeat-refactor pending lifecycle harness); W16-6 pulled d40bb01 (test hygiene splits + Alembic fresh-DB fixture: marketplace router 2374 LoC → 5 endpoint-grouped files, import-graph 767 LoC → 4 thematic files, w13-4-alembic-roundtrip-programmatic skip removed via fresh_alembic_engine per-test throwaway Postgres DB); W16-7 close-out commit (canonical preamble refresh + W16 tracker freeze; this commit). Final W16 bar: tests/architecture/ 199 passed (W15 final 172, +27); make test-security 217 passed (W13 final 215, +2); full suite 1890 passed. W15 closed via PR #22 MERGED 2026-05-18 via 6161472)`
`Phase: W16 close-out commit landed; week16 -> main PR pending (W16-0..W16-7 all closed or scope-resolved)`
`Branch: week16 (per user direction 2026-05-18; W11-W15 paterni restored via W16-0 doc reconcile; close-out merges into main via week16 -> main PR)`
`Owner: ekrem`

> **Authored 2026-05-18** as the W16 scope skeleton against `main` HEAD
> `6161472` (W15 close-out merge commit). Stable IDs `W16-1..W16-7`
> are reserved by the iteration plan and **assigned at first pull** per
> the W11/W12/W13/W14/W15 precedent (`REFACTOR_OPTIMIZATION.md` §14.0).
> Remaining sub-iter IDs (`W16-2..W16-7`) fill in as each is pulled.

This is the canonical active work tracker for the W16 Carry-Over
Closeout + Audit Findings + Production Regression window. Items
receive stable IDs (`W16-1`, `W16-2`, …) **at first pull**, not
preemptively, per the W11/W12/W13/W14/W15 precedent.

Slim canonical [`REFACTOR_OPTIMIZATION.md §14`](../REFACTOR_OPTIMIZATION.md)
carries the entry-conditions block, goal statement, and current candidate
list. The W15 frozen tracker
([`W15-codex-uclass-bounds-posture.md`](W15-codex-uclass-bounds-posture.md))
is the template structurally followed here, though W16 keeps Per-Item
Detail trimmed until each sub-iter is pulled (drift kontrolü).

## Status (Quick Glance)

- **W16 active — on `week16` branch per user direction (2026-05-18;
  W11-W15 paterni restored via W16-0 doc reconcile).** Sub-iter
  commits land on `week16`; close-out merges into `main` via a
  `week16 -> main` PR.
- **Entry gate (met).** W15 close-out PR #22 `week15 -> main` MERGED
  `2026-05-18` via `6161472`; W15 final post-merge bar:
  `tests/architecture/` **198 passed** (+26 from W14 final 172);
  `make test-security` **215 passed** (unchanged from W13 final);
  W15 mid-iter audit findings (`health-reconciliation-responsibility-split`,
  `marketplace-router-test-suite-split`,
  `analysis-job-worker-entry-crud-ownership`) deferred to W16+ per
  §13.3 Non-goals; W15 carry-over items (`scenario-accountant-conservation-split`,
  `report-finalize-top-level-field-sync-drift`,
  `simulation-progress-cancel` family,
  `w13-4-alembic-roundtrip-programmatic`) listed in
  `POST_POC_BACKLOG.md` Current Open Items + W16 Pull-Forward table.
- **W16-1 pulled `2026-05-18` via `01f910a`** (HIGH prod regression,
  severity-leading). Dispatch outcome=None upstream emit-site closed
  at `executor/flows/playwright/entrypoint/dispatch.py`
  (`dispatch_outcome_none` reason_code now emitted per requested
  scenario).
- **W16-2 pulled `2026-05-18` via `9d6d110`** (W15 mid-iter audit
  finding; concurrency-sensitive). Worker-entry CRUD primitive
  extracted to
  `appcore/storage/crud_ops/analysis_jobs/lifecycle.claim_queued_analysis_job_at_worker_entry`;
  `workflows/marketplace/analysis_service.run_analysis_job` now
  dispatches on `WorkerEntryOutcome` instead of issuing inline
  `SELECT ... FOR UPDATE` + commit. `AGENTS.md:57` compliance
  restored; W13-13 CAS preserved byte-identically; arch gate
  re-targeted on the facade boundary per W14-6 extend-not-duplicate.
- **W16-3 pulled `2026-05-18` via `fa430f2`** (W14 production scan
  carry-over; finalize / `report.save()` drift). Null-leakage half
  closed at the strict-forbid contract seam: 5 additive-optional
  fields (`target_extension_id`, `monitoring_start`, `monitoring_end`,
  `scenarios_run`, `harness_handshake_required`) added to
  `packages/analysis_contracts/contracts.ActivationReport`;
  `build_report_data` populates them with explicit type coercions.
  Pre-W16-3 RED stub replaced with 5 round-trip pins (xfail removed).
  The attribution-count-parity half of the W14 observation split to
  `[FOLLOWUP attribution-count-parity]` (W17+ candidate).
- **W16-4 pulled `2026-05-18` via `304b99f`** (W15 mid-iter audit
  finding; behavior-preserving extraction). `executor/flows/playwright/health/reconciliation.py`
  (682 LoC) split into three responsibility-aligned siblings:
  `security.py` (W13-1 HMAC primitives + W13-11 env-priority secret
  load), `handshake.py` (W13-12 fail-closed dispatch), and slimmed
  `reconciliation.py` (event-attempt verification state machine +
  coverage track reconciler). Architecture gates re-targeted per
  W14-6 extend-not-duplicate; W13-1 + W13-12 behavioral pins all stay
  green.
- **W16-5 documented `2026-05-18` (scope reduced, no code commit).**
  The `[FOLLOWUP simulation-progress-cancel]` umbrella's three sub-
  items were investigated and re-classified rather than bundled:
  `dedupe-step-progress-schemas` **rejected** (the two pydantic models
  serve distinct surface roles — internal strict storage vs public API
  + UI TS binding lenient; aliasing would couple them);
  `heartbeat-sandbox-reset-off-thread` + `heartbeat-refactor`
  **deferred to W17+** (concurrency-sensitive thread move + clarity
  refactor; both need a lifecycle harness that does not exist yet).
  `POST_POC_BACKLOG.md` entries updated with the closure rationale.
  W16-6..W16-7 remain `[planned]` until the corresponding pull lands.

## Sub-Iter Scope (planned)

| Iter | Theme | Stable ID(s) (planned) | Why ordered here |
|---|---|---|---|
| W16-1 | scenario-accountant upstream emit-site fix | `[FOLLOWUP scenario-accountant-conservation-split]` (W14-1 root-cause split; HIGH prod regression — deterministic dropout observed `2026-05-14` + `2026-05-15`, `run_quality: low`, `automation_health.status: degraded`) | Highest severity in scope. Production-observed deterministic regression; conservation guard catches but upstream emit-site bug class is non-intermittent. Repro fixture should land first (red), then emit-site fix (green). |
| W16-2 | analysis-job worker-entry CRUD ownership | `[FOLLOWUP analysis-job-worker-entry-crud-ownership]` (W15 audit finding `2026-05-16`; AGENTS.md:57 hard rule violation — direct `SELECT … FOR UPDATE` + `db.commit()` at `workflows/marketplace/analysis_service.py:296-346`) | Correctness/concurrency-sensitive. Couples to W13-13 CAS pattern (`worker-start-cancel-race-CAS`). Right fix: new row-lock-aware lifecycle CRUD primitive in `appcore/storage/crud_ops/analysis_jobs/lifecycle.py`. Land before refactor-class work to flush facade compliance. |
| W16-3 | report-finalize top-level field sync drift | `[FOLLOWUP report-finalize-top-level-field-sync-drift]` (W14 production scan-driven; `target_extension_id`, `monitoring_start`/`monitoring_end`, `scenarios_run`, `harness_handshake_required` null sızıntısı; new manifestation `2026-05-14` — `attribution_summary.target_activation_count` stream-türevli vs evidence-kind sayımı 0 mismatch) | Couples with W16-1: scenario-accountant emit-site fix sonrası finalize ordering temizliği doğal devam. Repro fixtür W16-1'in fixture'ı üzerine inşa edilebilir. |
| W16-4 | health-reconciliation responsibility split | `[FOLLOWUP health-reconciliation-responsibility-split]` (W15 audit finding `2026-05-16`; `executor/flows/playwright/health/reconciliation.py` 682 LoC, HMAC marker verification @:78 + fail-closed handshake @:39 + event reconciliation @:414 + coverage @:581 tek modülde) | Behavior-preserving extraction. W13-1 HMAC gates + W13-12 fail-closed handshake davranışı regress etmemeli. Önce responsibility map (hangi fonksiyon hangi risk class'ı sahipleniyor) + test coverage validation, sonra extract. Do not auto-refactor. |
| W16-5 | simulation-progress-cancel family closeout (3 sub-items) | `[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread` + `dedupe-step-progress-schemas` + `heartbeat-refactor` (W11+ umbrella; W13-3 cancel-after-finish race kapandı, 3 alt-kalem açık) | Üç haftalık umbrella'yı toplu kapatır. Çoklu lane spanning; bir alt-iter'da bundle olmazsa W17/W18'e tekrar düşer. |
| W16-6 | hygiene splits + Alembic round-trip fixture | `[CLEANUP marketplace-router-test-suite-split]` (`tests/workflows/marketplace/test_router.py` 2374 LoC → 5 domain dosyası) + `[CLEANUP test-import-graph-policy-dump-split]` (`test_import_graph.py` 767 LoC → 4 tematik dosya) + `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` (fresh-DB-per-test fixture, `test_alembic_cancelling_migration.py::test_forward_backward_cancelling` `pytest.skip` kalkar) | Test-maintenance + infrastructure hygiene. Runtime risk yok; behavior-preserving moves + new fixture. Paralel yapılabilir. |
| W16-7 | close-out hygiene + canonical preamble refresh | Doc preamble truth-state refresh (CLAUDE.md, AGENTS.md, README.md, AGENT_CONTEXT.md, REFACTOR_STATUS.md, POST_POC_BACKLOG.md, REFACTOR_OPTIMIZATION.md) + Ruff lint + markdown formatting + UI contract sync + (varsa) yeni regression gate'ler + §14 tracker freeze | W14/W15 paterni. Tracker scope kapanışında frozen olur. **Close-out `week16 -> main` PR** (W11-W15 paterni restored 2026-05-18); sub-iter commits `week16` branch'inde land eder. |

## Pre-Lock Entry Conditions

W16 entry met (all conditions satisfied at `2026-05-18`):

- W15 close-out PR #22 `week15 -> main` MERGED `2026-05-18` via `6161472`. ✓
- W15 final post-merge bar recorded: `tests/architecture/` 198 passed,
  `make test-security` 215 passed. ✓
- W15 mid-iter audit findings appended to `POST_POC_BACKLOG.md` and
  marked W16 pull-forward. ✓
- W15 carry-over items (scenario-accountant, report-finalize,
  simulation-progress-cancel family, w13-4-alembic) listed in
  `POST_POC_BACKLOG.md` Current Open Items + W16 Pull-Forward table. ✓
- W16 plan source `REFACTOR_OPTIMIZATION.md §14` authored and committed
  to `main`. ✓
- Canonical doc preambles (CLAUDE.md, AGENTS.md, README.md,
  AGENT_CONTEXT.md, REFACTOR_STATUS.md, POST_POC_BACKLOG.md,
  REFACTOR_OPTIMIZATION.md) refreshed to W15-closed + W16-active
  truth-state. ✓
- W15 tracker frozen (status header updated to "closed and merged via
  PR #22 6161472"). ✓
- This W16 tracker (W16-regression-and-audit-closeout.md) authored. ✓

## Per-Iter Detail (filled at pull)

Each sub-iter section below is added when the iter is pulled. Pattern
follows W14/W15 trackers — Scope, Module Locations, Test Deltas,
Production Validation, Notes. Stable ID line is added on pull commit.

### W16-1 — scenario-accountant upstream emit-site fix

**Pulled `2026-05-18` via `01f910a`** (severity-leading W16 item; HIGH
prod regression). Closes the dispatch-layer half of the W14-1
carry-over emit-site.

**Scope:** `_normalize_execution_result` outcome=None branch
(`executor/flows/playwright/entrypoint/dispatch.py:91-118` post-fix)
now constructs a
`SkippedScenarioRecord(reason_code="dispatch_outcome_none", detail=...)`
for each requested scenario instead of leaving them to the downstream
conservation guard's `unaccounted_dropout` fallback. The W14-1
last-mile guard
(`ScenarioAccountant._validate_scenario_conservation`,
`executor/flows/playwright/monitor/scenario_accountant.py:392-438`)
remains as the catch-all for any non-dispatch silent drop sites; the
W14-1 boundary vectors in
`tests/security/test_scenario_dropout_repro.py` retain their pre-W16-1
semantics on purpose.

**Module locations:**

- `executor/flows/playwright/entrypoint/dispatch.py:91-118` —
  outcome=None branch with the W16-1 instrumentation.
- `executor/flows/playwright/stimulus/types.py:48-51` +
  `executor/flows/playwright/stimulus/__init__.py:85,93` —
  `SkippedScenarioRecord` already exported via stimulus
  `__init__.py`; the dispatch normalizer constructs it via
  `deps.stimulus.SkippedScenarioRecord` (no schema change).
- `executor/flows/playwright/monitor/scenario_accountant.py:124-152`
  (`record_execution_result`) — unchanged; consumes the result's
  `skipped_scenarios` by `getattr` so the new entries flow through
  to the report without modification.

**Adjacent emit-site audit (W16-1 closure context):**

- `executor/flows/playwright/stimulus/passes.py:102-158` — already
  records specific reasons (`prerequisite_blocked`,
  `unsupported_activation_surface`, `unknown_scenario`) per W11+
  wiring.
- `executor/flows/playwright/automation.py:275-365` — accounts every
  requested scenario by design (no silent drops).
- `executor/flows/playwright/entrypoint/triggers.py:22-38` — planner
  selects but does not drop scenarios.

The remaining surface for new `unaccounted_dropout` observations would
indicate an undiscovered emit-site, not the dispatch outcome=None bug
class (now closed).

**Test deltas (`tests/security/test_scenario_dropout_repro.py`, +97 LoC):**

- Module docstring W16-1 closure note appended (W14-1 record-of-state
  retained above it).
- `test_dispatch_outcome_none_emits_specific_reason_code` —
  3 requested scenarios produce 3 `SkippedScenarioRecord`s with
  `reason_code='dispatch_outcome_none'` + non-empty `detail`.
- `test_dispatch_outcome_none_emits_nothing_when_no_requested_scenarios`
  — empty `requested_scenarios` = no-op (no phantom records).
- Existing W14-1 vectors stay green (last-mile fallback semantics
  preserved for non-dispatch sites).

**Pre-merge test counts (W16-1 close):**

- `tests/security/test_scenario_dropout_repro.py`: **9 passed**
  (W14-1 close: 7 passed).
- `tests/executor/test_playwright_monitor_scenario_accountant.py`:
  **48 passed** (unchanged).
- `tests/executor/test_playwright_dispatch.py +
  test_playwright_entrypoint.py`: **53 passed** (unchanged).
- `tests/architecture/` + `make test-security` full sweep recorded
  at W16-7 close-out per W14/W15 paterni.

**Production replay coverage:** Bug class observed `2026-05-14`
(15:15, `ms-python.python` 2026.5.2026051301) + `2026-05-15` 09:51
(deterministic `debug_session` + `refactor_workflow` drop with
`unaccounted_dropout` reason_code) is closed at the dispatch
outcome=None layer; production-only confirmation deferred to the
next live executor run (no new fixture artifact at W16-1 commit).

**Landing commit:** `01f910a` (test + instrumentation co-landed; no
separate red-then-green sub-commits because the new tests pin the
post-W16-1 contract directly).

**Audit trail:** `[FOLLOWUP scenario-accountant-conservation-split]`
in `POST_POC_BACKLOG.md` marked **dispatch layer closed at W16-1**;
surrounding W14-1 production-observation prose retained to preserve
the pre-W16-1 truth-state.

### W16-2 — analysis-job worker-entry CRUD ownership

**Pulled `2026-05-18` via `9d6d110`** (W15 mid-iter audit finding;
AGENTS.md:57 hard-rule violation closed).

**Scope:** Lift the W13-13 worker-entry CAS primitive out of
`workflows/marketplace/analysis_service.run_analysis_job` (where it
was 50+ LoC of inline `SELECT ... FOR UPDATE` + branch + `db.commit()`)
into the lifecycle CRUD facade at
`appcore/storage/crud_ops/analysis_jobs/lifecycle.py`. Behavior is
byte-identical; the change is a pure facade extraction.

**Module locations (post-W16-2):**

- `appcore/storage/crud_ops/analysis_jobs/lifecycle.py` — new primitive
  `claim_queued_analysis_job_at_worker_entry(db, job_id, *, fallback_report_name, cancel_detail)`
  returning a `WorkerEntryClaim(outcome, job, report_path)` dataclass.
  Outcome enum has five members: `CLAIMED`, `ALREADY_TERMINAL`,
  `ROW_MISSING`, `CANCELLING_FINALIZED`, `CANCELLING_RACE`. Lock
  discipline mirrors `cancel_analysis_job` / `fail_analysis_job` /
  `complete_analysis_job` (W14-4 lock symmetry).
- `appcore/storage/crud_ops/analysis_jobs/__init__.py` — re-exports
  `WorkerEntryClaim`, `WorkerEntryOutcome`,
  `claim_queued_analysis_job_at_worker_entry` (W11-8 facade thinness).
- `workflows/marketplace/analysis_service.py` — `run_analysis_job`
  body refactored: dispatch on `claim.outcome`; only `CLAIMED`
  continues to the analysis flow. Direct imports `select`, `AnalysisJob`,
  `_TERMINAL_JOB_STATUSES`, `finalize_cancelled_analysis_job` dropped
  (no longer needed at the caller). Docstring updated to record the
  W16-2 facade move and point at the relocated architecture gate.

**Lock-asymmetry note (preserved):** The `cancelling` branch inside the
facade calls `finalize_cancelled_analysis_job` (the lifecycle helper)
directly under the held lock. The wrapper `job_service.finalize_cancelled_job`
opens its own `SessionLocal()` via `_run_in_session` and would
deadlock against the row lock. The W13-3 exception handler downstream
of the entry block keeps using the wrapper because by then the
entry-block transaction has committed.

**Architecture gate (W14-6 extend-not-duplicate):**
`tests/architecture/test_run_analysis_job_entry_snapshot.py` rewritten
in place (no new gate file). Two AST invariants now target the facade
boundary:

- **INV1** — `run_analysis_job`'s first DB action MUST be a call to
  `claim_queued_analysis_job_at_worker_entry`; no other CRUD helper in
  `_DB_TOUCH_NAMES` may precede it in source order.
- **INV2** — the lifecycle facade
  `claim_queued_analysis_job_at_worker_entry` MUST itself contain
  both a `with_for_update()` call site (row lock) and a
  `finalize_cancelled_analysis_job` call site (cancel-branch finalize
  under the held lock).

**Test deltas:**

- `tests/architecture/test_run_analysis_job_entry_snapshot.py` — 2
  tests rewritten (no count change).
- `tests/platform/storage/test_analysis_jobs_cancel_at_worker_entry.py`
  — 6 W13-13 behavioral pins all stay green; one `monkeypatch.setattr`
  target moved from `analysis_service` to `lifecycle` because the
  W16-2 refactor removed `finalize_cancelled_analysis_job` from the
  analysis_service module scope.
- `tests/platform/storage/test_analysis_jobs_lifecycle.py::test_module_path_pins_lifecycle_surface`
  — `expected` set extended with 3 new public exports
  (`WorkerEntryClaim`, `WorkerEntryOutcome`,
  `claim_queued_analysis_job_at_worker_entry`); docstring notes the
  W16-2 surface extension.

**Pre-merge test counts (W16-2 close):**

- `tests/architecture/`: **198 passed** (unchanged from W15 final;
  W14-6 extend-not-duplicate observed — arch gate file is the same).
- `tests/platform/storage/`: **89 passed, 1 skip** (W13-4 alembic skip
  unchanged; will close at W16-6).
- `tests/workflows/marketplace/test_run_analysis_job_finalize.py +
  test_router.py`: **68 passed, 1 skip** (VSIX fixture infra,
  unchanged).
- `make test-security`: **217 passed** (W15 final 215 + W16-1's 2
  new dispatch-outcome-none tests).

**Landing commit:** `9d6d110`.

**Audit trail:** `[FOLLOWUP analysis-job-worker-entry-crud-ownership]`
in `POST_POC_BACKLOG.md` marked **closed at W16-2** with the closure
details (facade location, lock-asymmetry preservation, arch gate
re-target, test deltas).

### W16-3 — report-finalize top-level field sync drift

**Pulled `2026-05-18` via `fa430f2`** (W14 production scan-driven
investigation; null-leakage half closed).

**Root cause located W16-3.** The W14-3 post-pull review predicted a
finalize / `report.save()` ordering drift and an
`ExtensionMonitor.start()`/`stop()` lifecycle harness as the test
seam. Investigation found a different, simpler root cause: the five
analyst-facing scalars (`target_extension_id`, `monitoring_start`,
`monitoring_end`, `scenarios_run`, `harness_handshake_required`)
existed on the in-memory `ActivationReport` dataclass
(`executor/flows/playwright/monitor/types.py`) but had **no slot on
the strict-forbid contract**
(`packages/analysis_contracts/contracts.ActivationReport` —
`StrictContractModel` with `extra='forbid'`). The save path
(`executor/flows/playwright/report_builder.save_report_payload`)
parses `build_report_data` output through
`_validate_report_against_contract` and persists
`parsed.model_dump(mode='json')`; fields without a contract slot were
silently dropped at validation time, surfacing as missing/`null` keys
in the persisted JSON — independent of finalize ordering.

**Module locations:**

- `packages/analysis_contracts/contracts.py:509-535` — 5
  additive-optional contract slots added inline next to the W14-5
  `executor_fingerprint` extension (same `additive-optional /
  schema-version-unchanged` precedent).
- `executor/flows/playwright/report_builder.py:308-329` —
  `build_report_data` populates the 5 new keys from the live report
  with explicit `float()` / `list()` / `bool()` coercions so a future
  writer that drifts a value to `None` cannot re-introduce the leak.
  Also keeps the pre-existing `target_extension_expected` alias
  populated so downstream readers using either name see the same
  value.

**Test deltas:**

- `tests/security/test_report_finalize_field_sync.py` —
  pre-W16-3 the file held one `xfail`-marked RED stub predicting a
  heavier `ExtensionMonitor.start()`/`stop()` lifecycle harness.
  W16-3 replaces it with 5 direct save-path round-trip pins:
  - `test_save_persists_target_extension_id_top_level` — top-level
    field survives + pre-existing alias stays populated.
  - `test_save_persists_monitoring_start_end_top_level` — non-null
    floats.
  - `test_save_persists_scenarios_run_derived_list` — list (not
    `None`), order preserved.
  - `test_save_persists_harness_handshake_required_flag` — literal
    `True` (not `null`).
  - `test_save_defaults_preserve_legacy_fixture_shape` — empty
    `ActivationReport` round-trips with the 5 W16-3 defaults; legacy
    fixture shape preserved under strict-forbid validation.

**Pre-merge test counts (W16-3 close):**

- `tests/security/test_report_finalize_field_sync.py`: **5 passed**
  (pre-W16-3: 1 xfail stub; replaced).
- `tests/workflows/marketplace/test_run_analysis_job_finalize.py +
  tests/executor/test_playwright_monitor_lifecycle.py +
  tests/executor/test_playwright_monitor_scenario_accountant.py +
  packages/analysis_contracts/`: **66 passed** (no regression).
- `make test-security`: **217 passed** (the new file is outside the
  make rule's narrow allowlist; direct-pytest verification above
  pins the new contract).

**Schema-version stance:** unchanged at `2.1`. The 5 fields are
additive-optional with defaults matching the in-memory dataclass
defaults so legacy fixtures (and any callsite that constructs
`ActivationReport` without stamping the new fields) keep validating.
Precedent: W14-5 `executor_fingerprint` extension.

**Out-of-scope split:** the second W14 production observation
(`attribution_summary.target_activation_count = 1` while
`evidence_events` had no `kind=activation,
is_target_extension_event=True` entry) is in a different code path
(`build_signal_summary` + `attribution_summary` producer side).
Split to `[FOLLOWUP attribution-count-parity]` (new entry in
`POST_POC_BACKLOG.md`; W17+ candidate).

**Landing commit:** `fa430f2`.

**Audit trail:** `[FOLLOWUP report-finalize-top-level-field-sync-drift]`
in `POST_POC_BACKLOG.md` marked **null-leakage half closed at W16-3**
with the closure details (contract additive fields, build_report_data
coercions, RED-stub replacement). Adjacent
`[FOLLOWUP attribution-count-parity]` entry added below it captures
the remaining drift.

### W16-4 — health-reconciliation responsibility split

**Pulled `2026-05-18` via `304b99f`** (W15 mid-iter audit finding;
behavior-preserving extraction). The 682-LoC monolith
`executor/flows/playwright/health/reconciliation.py` is split into
three responsibility-aligned siblings; W13-1 HMAC + W13-12 fail-closed
gates all stay green on byte-identical behavior.

**Submodule layout (post-W16-4, under
`executor/flows/playwright/health/`):**

- `security.py` (~125 LoC, new): `HARNESS_PYTHON_SECRET_PATH`,
  `load_harness_python_secret` (W13-11 env-priority + defense-in-depth
  unlink), `_verify_harness_marker_signature` (W13-1 HMAC-SHA256
  constant-time compare). Owns the secret-handling + signature
  verification responsibility class.
- `handshake.py` (~100 LoC, new): `_HARNESS_MARKER_RE`,
  `_harness_trace_records_by_attempt`,
  `_attempt_has_harness_completion_trace` (W13-12 three-branch dispatch
  — HMAC verify, fail-closed, legacy phase-only). Imports
  `_verify_harness_marker_signature` from `security.py` at module
  scope; the import boundary preserves the W13-1 wiring gate's AST
  walk semantics.
- `reconciliation.py` (~440 LoC, slimmed from 682): the event-attempt
  verification state machine (`reconcile_event_attempts` +
  `_mark_attempt_*` helpers + activation matchers) and the coverage
  track reconciler (`reconcile_coverage_verification`,
  `_reconcile_track`). Imports from `handshake.py` + `security.py` +
  `runtime_facts` + `summary`.
- `__init__.py`: preserves every public re-export
  (`reconcile_event_attempts`, `reconcile_coverage_verification`,
  `derive_verified_capabilities`); `derive_verified_capabilities` now
  sourced direct from `summary` instead of via the
  `reconciliation -> summary` re-export hop.

**Architecture gates re-targeted (W14-6 extend-not-duplicate; no new
gate files):**

- `tests/architecture/test_harness_marker_auth.py`: `HANDSHAKE_PATH`
  constant added; `test_attempt_has_harness_completion_trace_calls_verifier`
  now parses `handshake.py` instead of `reconciliation.py`. The other
  two gates (`reconcile_event_attempts` reads `expected_harness_nonce`;
  `setup_monitor` calls `load_harness_python_secret`) keep their
  `RECONCILIATION_PATH` / `DISPATCH_PATH` targets — those invariants
  did not move.
- `tests/architecture/test_harness_secret_eager_consume.py`:
  `SECURITY_PATH` constant added; gate 3
  (`test_load_harness_python_secret_prefers_env_var_over_file`) parses
  `security.py` instead of `reconciliation.py`. Gates 1 and 2 (call
  ordering in `execute_analysis_request`, env var threading in
  `run_playwright_automation`) are unaffected.

**Test-side import path updates (callers follow the symbol move):**

- `executor/flows/playwright/entrypoint/dispatch.py`:
  `load_harness_python_secret` import moved from
  `..health.reconciliation` to `..health.security`.
- `tests/executor/test_playwright_health_reconciliation.py`: 3 inline
  W13-11 env-priority test imports (lines 725, 758, 785) moved from
  `..health.reconciliation` to `..health.security`. Top-level imports
  (`reconcile_event_attempts`, `reconcile_coverage_verification`) are
  unchanged — those symbols still live in `reconciliation.py`.

**Lock-asymmetry preservation (W13-1 wiring):** the verifier call site
inside `_attempt_has_harness_completion_trace` survives the import
boundary unchanged — the AST walk in `test_harness_marker_auth` still
finds the `Name` node because `handshake.py` imports
`_verify_harness_marker_signature` at module scope. Swapping the
import for the wrapper would not deadlock here (no row lock involved),
but would still trip the structural gate; the responsibility
separation makes the wiring more readable rather than less safe.

**Pre-merge test counts (W16-4 close):**

- `tests/architecture/`: **199 passed** (W15 final 198, +1 — a
  pre-existing AST gate that scans `health/` subpackages picked up
  the new module paths and registered an additional parametrized
  case; no behavioral regression, no test removed).
- `tests/executor/test_playwright_health_reconciliation.py +
  tests/architecture/test_harness_marker_auth.py +
  tests/architecture/test_harness_secret_eager_consume.py +
  tests/security/test_harness_handshake_required.py`: **225 passed**
  (combined sub-slice).
- `make test-security`: **217 passed** (unchanged from W16-3 close).
- `tests/workflows/marketplace/`: **176 passed, 1 skip** (VSIX
  fixture infra, unchanged).

**Landing commit:** `304b99f`.

**Audit trail:** `[FOLLOWUP health-reconciliation-responsibility-split]`
in `POST_POC_BACKLOG.md` marked **closed at W16-4** with the closure
details (submodule layout, gate re-target paths, lock-asymmetry
preservation, test counts). The pre-W16-4 W15 mid-iter audit context
prose is retained verbatim beneath the closure paragraph for the
historical record.

### W16-5 — simulation-progress-cancel family closeout

**Documented `2026-05-18` (scope reduced; no code commit).** The
W11+ umbrella's three sub-items were investigated during the W16-5
pull and re-classified rather than bundled together. The decision
audit trail below records why each sub-item moved off the W16-5
slate.

**dedupe-step-progress-schemas — rejected after investigation.**
Two pydantic models carry identical field shape
(`completed: int >= 0`, `total: int >= 0`):

- `appcore/contracts/schema_defs/analysis_jobs.AnalysisJobStepProgress`
  with `model_config = ConfigDict(extra="forbid")` — the internal
  storage layer's strict variant. Used by
  `appcore/storage/crud_ops/analysis_jobs/lifecycle.py` and the
  `tests/platform/storage/test_analysis_jobs_steps.py` write
  contracts; the strict mode catches typos at write time before they
  reach the database.
- `appcore/contracts/schema_defs/marketplace.AnalyzeJobStepProgress`
  with the default lenient Pydantic config. Used by the public API
  surface (`AnalyzeJobStep.progress` field on the marketplace router
  response models) and explicitly listed in
  `scripts/generate_ui_contracts.py:70`'s allowlist as a source
  symbol for TypeScript binding emission.

Aliasing the marketplace symbol to the analysis_jobs class would
silently flip the public API to `extra="forbid"` (changes the
`__pydantic_config__.extra` semantics on the same `__qualname__`)
and the emitted TS binding's class name would shift from
`AnalyzeJobStepProgress` to `AnalysisJobStepProgress`. Both are
observable changes for callers outside the codebase. The dedupe
value (~35 LoC eliminated) does not justify the surface-role
coupling or the breaking risk. Audit finding stays open as
documentation; no schema change lands.

**heartbeat-sandbox-reset-off-thread — deferred to W17+.** The
sandbox-reset call currently fires on the analysis worker thread in
`workflows/marketplace/analysis_execution.py`; moving it onto the
monitoring heartbeat thread (or any sibling background thread) is
concurrency-sensitive — it interacts with the W13-3 two-phase cancel
contract, the W13-13 worker-entry CAS, and the W16-2 facade's row
lock discipline. A safe move needs a lifecycle harness that drives
start / reset / cancel / finalize against a real DB session and a
real Playwright page mock; that harness does not exist yet (the
same gap surfaced for report-finalize at W14-3 and was sidestepped
at W16-3 by finding the root cause at the contract seam — that
sidestep is not available here because the thread-placement question
is a runtime concurrency property, not a serialization one). The
W16 carry-over closeout window is intentionally narrow; the thread
move belongs in a dedicated sub-iter with the harness as a
prerequisite.

**heartbeat-refactor — deferred to W17+.** Bundled with
`heartbeat-sandbox-reset-off-thread` above; the same lifecycle
harness is the prerequisite. The current heartbeat shape
(`workflows/marketplace/analysis_execution._run_monitoring_heartbeat`
L102-128 + thread setup L287-313) is functional and exercises every
cancel-poll branch; the audit-driven refactor is a clarity gain
rather than a correctness fix, so deferring without behavioral
consequence is safe.

**Module locations (for the deferred items' future pull):**

- `workflows/marketplace/analysis_execution.py:102-128` —
  `_run_monitoring_heartbeat` (heartbeat loop body).
- `workflows/marketplace/analysis_execution.py:287-313` — heartbeat
  thread setup (Event + Thread + `_heartbeat_on_cancel` callback).
- `workflows/marketplace/analysis_service.py` — `_reset_sandbox`
  callsite (currently on the worker thread).
- `executor/control.py` — sandbox reset entry point.

**Landing commit:** the W16-5 doc-only audit trail update lands as
part of the same self-stamp commit that touches
`POST_POC_BACKLOG.md` + `REFACTOR_STATUS.md`; no source code commit
ships under W16-5.

**Audit trail:** all three sub-items in `POST_POC_BACKLOG.md` carry
the closure rationale (rejected / deferred-to-W17+) so a future
pull can pick the deferred work up without re-deriving the analysis.

### W16-6 — hygiene splits + Alembic round-trip fixture

_[Placeholder — filled at pull. Will document: domain classification
for `tests/workflows/marketplace/test_router.py` 2374 LoC → 5 files,
thematic split for `tests/architecture/test_import_graph.py` 767 LoC →
4 files, new fresh-DB-per-test fixture design (Alembic round-trip),
`test_alembic_cancelling_migration.py` skip removal, test deltas,
landing commit(s).]_

### W16-7 — close-out hygiene + canonical preamble refresh

_[Placeholder — filled at pull. Will document: doc preamble
truth-state refresh across 7 canonical docs (W15 paterni), Ruff
lint, markdown formatting, UI contract sync, (varsa) yeni regression
gate'ler, tracker freeze evidence, landing commit. **Close-out via
`week16 -> main` PR** (W11-W15 paterni restored 2026-05-18).]_

## Exit Criteria (W16-End)

Mirror of `REFACTOR_OPTIMIZATION.md §14.4` — W16 kapanır şu koşullar
sağlandığında:

- W16-1..W16-7 kapanır ya da deferral rasyoneli ile W17'ye taşınır.
- Bu tracker final close evidence + current test counts tutar
  (`tests/architecture/` hedef 198 → ~205+; W16-2 + W16-4 yeni
  arch gate eklerse).
- W16-1 production replay: `activation_report_*.json` fixture'ında
  `debug_session` + `refactor_workflow` scenario'ları deterministik
  drop etmiyor; `[FOLLOWUP scenario-accountant-conservation-split]`
  POST_POC_BACKLOG'da kapanış audit trail'i ile işaretlenir.
- W16-3 production replay: `target_extension_id`, `monitoring_*`,
  `scenarios_run`, `harness_handshake_required` top-level field'ler
  non-null populate edilir.
- W16-4 davranış paritesi: W13-1 HMAC marker gates + W13-12
  fail-closed handshake davranışı regress etmez.
- W16-5 umbrella: `[FOLLOWUP simulation-progress-cancel]` family
  3 alt-kalemi kapanır; umbrella POST_POC_BACKLOG'da CLOSED işaretlenir.
- W16-6 hygiene: `tests/workflows/marketplace/test_router.py` →
  domain bazlı splits; `tests/architecture/test_import_graph.py` →
  tematik splits; `test_alembic_cancelling_migration.py` skip kalkar.
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `active-work/README.md`, ve ilgili lane docs aynı active/closed
  state'i gösterir.
- Slim canonicals kısa kalır; verbose evidence önce arşivlenir.
- Close-out hygiene pass (W14/W15 paterni): Ruff lint, UI contract
  sync, markdown formatting, doc truth-state alignment, (varsa)
  yeni regression gate'ler.
- Per user direction (2026-05-18 restored): W16 `week16` branch'inde
  çalışır; close-out `week16 -> main` PR ile merge edilir; W16 tracker
  scope kapanışında frozen olur (W11-W15 paterni).

## Notes

- **Branching policy (user direction, 2026-05-18 restored):** W16
  lives on a `week16` branch; sub-iter commits land on `week16`;
  close-out is merged into `main` via a `week16 -> main` PR
  (W11/W12/W13/W14/W15 paterni restored). The doc-reconcile pass
  landed as W16-0 (first commit on `week16`); earlier preamble text
  that said W16 would stay on `main` is superseded.
- **Stable ID assignment:** Sub-iter IDs (`W16-1`..`W16-7`) are
  assigned at first pull, not preemptively. The Sub-Iter Scope table
  above is a plan, not a commitment — order and contents may shift
  if a higher-severity item surfaces mid-window.
- **Severity-leading order:** W16-1 first because production has
  deterministic regression evidence (`2026-05-14` + `2026-05-15`
  observations). Subsequent ordering balances coupling (W16-3 with
  W16-1), correctness/concurrency risk (W16-2), behavior-preserving
  refactor discipline (W16-4), umbrella closeout (W16-5), and
  parallel-safe hygiene (W16-6).
- **Architecture gate target:** `tests/architecture/` 198 → ~205+
  per W16-2 + W16-4 new gate additions (if applicable). W14-6
  "extend, do not duplicate" rule applies: prefer extending an
  existing gate to adding a new file.
