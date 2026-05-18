# W16 — Carry-Over Closeout + Audit Findings + Production Regression (Active Work Tracker)

`Last Updated: 2026-05-18 (W16 active on main per user direction — no separate week16 branch; W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W16 scope authored 2026-05-18 against main HEAD 6161472; 7 sub-iter (W16-1..W16-7) reserved by §14 plan and assigned at first pull per W11/W12/W13/W14/W15 precedent; first pull pending)`
`Phase: W16 active (W16-1..W16-7 reserved, none yet pulled; no separate branch — commits land directly on main, tracker freezes at scope close)`
`Branch: main (per user direction; no week16 branch is opened)`
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

- **W16 active — on `main` per user direction.** No separate `week16`
  branch is opened; sub-iter commits land directly on `main`, and this
  tracker freezes when scope closes (no `week16 -> main` close-out PR).
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
- **First pull pending.** Severity-leading order (W16-1: HIGH prod
  regression first). All seven sub-iter rows below remain `[planned]`
  until the corresponding pull lands.

## Sub-Iter Scope (planned)

| Iter | Theme | Stable ID(s) (planned) | Why ordered here |
|---|---|---|---|
| W16-1 | scenario-accountant upstream emit-site fix | `[FOLLOWUP scenario-accountant-conservation-split]` (W14-1 root-cause split; HIGH prod regression — deterministic dropout observed `2026-05-14` + `2026-05-15`, `run_quality: low`, `automation_health.status: degraded`) | Highest severity in scope. Production-observed deterministic regression; conservation guard catches but upstream emit-site bug class is non-intermittent. Repro fixture should land first (red), then emit-site fix (green). |
| W16-2 | analysis-job worker-entry CRUD ownership | `[FOLLOWUP analysis-job-worker-entry-crud-ownership]` (W15 audit finding `2026-05-16`; AGENTS.md:57 hard rule violation — direct `SELECT … FOR UPDATE` + `db.commit()` at `workflows/marketplace/analysis_service.py:296-346`) | Correctness/concurrency-sensitive. Couples to W13-13 CAS pattern (`worker-start-cancel-race-CAS`). Right fix: new row-lock-aware lifecycle CRUD primitive in `appcore/storage/crud_ops/analysis_jobs/lifecycle.py`. Land before refactor-class work to flush facade compliance. |
| W16-3 | report-finalize top-level field sync drift | `[FOLLOWUP report-finalize-top-level-field-sync-drift]` (W14 production scan-driven; `target_extension_id`, `monitoring_start`/`monitoring_end`, `scenarios_run`, `harness_handshake_required` null sızıntısı; new manifestation `2026-05-14` — `attribution_summary.target_activation_count` stream-türevli vs evidence-kind sayımı 0 mismatch) | Couples with W16-1: scenario-accountant emit-site fix sonrası finalize ordering temizliği doğal devam. Repro fixtür W16-1'in fixture'ı üzerine inşa edilebilir. |
| W16-4 | health-reconciliation responsibility split | `[FOLLOWUP health-reconciliation-responsibility-split]` (W15 audit finding `2026-05-16`; `executor/flows/playwright/health/reconciliation.py` 682 LoC, HMAC marker verification @:78 + fail-closed handshake @:39 + event reconciliation @:414 + coverage @:581 tek modülde) | Behavior-preserving extraction. W13-1 HMAC gates + W13-12 fail-closed handshake davranışı regress etmemeli. Önce responsibility map (hangi fonksiyon hangi risk class'ı sahipleniyor) + test coverage validation, sonra extract. Do not auto-refactor. |
| W16-5 | simulation-progress-cancel family closeout (3 sub-items) | `[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread` + `dedupe-step-progress-schemas` + `heartbeat-refactor` (W11+ umbrella; W13-3 cancel-after-finish race kapandı, 3 alt-kalem açık) | Üç haftalık umbrella'yı toplu kapatır. Çoklu lane spanning; bir alt-iter'da bundle olmazsa W17/W18'e tekrar düşer. |
| W16-6 | hygiene splits + Alembic round-trip fixture | `[CLEANUP marketplace-router-test-suite-split]` (`tests/workflows/marketplace/test_router.py` 2374 LoC → 5 domain dosyası) + `[CLEANUP test-import-graph-policy-dump-split]` (`test_import_graph.py` 767 LoC → 4 tematik dosya) + `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` (fresh-DB-per-test fixture, `test_alembic_cancelling_migration.py::test_forward_backward_cancelling` `pytest.skip` kalkar) | Test-maintenance + infrastructure hygiene. Runtime risk yok; behavior-preserving moves + new fixture. Paralel yapılabilir. |
| W16-7 | close-out hygiene + canonical preamble refresh | Doc preamble truth-state refresh (CLAUDE.md, AGENTS.md, README.md, AGENT_CONTEXT.md, REFACTOR_STATUS.md, POST_POC_BACKLOG.md, REFACTOR_OPTIMIZATION.md) + Ruff lint + markdown formatting + UI contract sync + (varsa) yeni regression gate'ler + §14 tracker freeze | W14/W15 paterni. Tracker scope kapanışında frozen olur. **No `week16 -> main` PR per main-branch direction**; sub-iter commits doğrudan `main`'e land eder. |

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

_[Placeholder — filled at pull. Will document: deterministic repro
fixture (red), emit-site fix (green), candidate modules
(`workflows/marketplace/dispatch._normalize_execution_result`,
`workflows/.../stimulus_passes/*`, `packages/.../scenario_accountant.py`),
expected production replay outcome, test deltas, landing commit.]_

### W16-2 — analysis-job worker-entry CRUD ownership

_[Placeholder — filled at pull. Will document: new
`appcore/storage/crud_ops/analysis_jobs/lifecycle.py` row-lock-aware
primitive design, worker-entry block migration at
`workflows/marketplace/analysis_service.py:296-346`, W13-13 CAS
preservation evidence, new `tests/architecture/test_crud_facade_ownership.py`
gate (if applicable), test deltas, landing commit.]_

### W16-3 — report-finalize top-level field sync drift

_[Placeholder — filled at pull. Will document: finalize ordering
analysis (`appcore/.../reports/finalize.py` or candidate module),
top-level field population fix, regression gate
(`tests/.../test_report_top_level_fields.py`), production replay
evidence, test deltas, landing commit.]_

### W16-4 — health-reconciliation responsibility split

_[Placeholder — filled at pull. Will document: responsibility map
(security_gates vs reconciliation vs coverage), test-coverage
validation on both sides, behavior-preserving extraction plan,
new submodules under `executor/flows/playwright/health/`,
W13-1 HMAC marker gate regression evidence, new
`tests/architecture/test_health_module_boundaries.py` gate (if
applicable), test deltas, landing commit.]_

### W16-5 — simulation-progress-cancel family closeout

_[Placeholder — filled at pull. Will document each of 3 sub-items:
`heartbeat-sandbox-reset-off-thread`, `dedupe-step-progress-schemas`,
`heartbeat-refactor` — module locations, refactor rationale,
test deltas, umbrella closeout audit trail in `POST_POC_BACKLOG.md`,
landing commit(s).]_

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
gate'ler, tracker freeze evidence, landing commit. **No
`week16 -> main` PR per main-branch direction.**]_

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
- Per user direction: W16 `main` üzerinde kalır — `week16 -> main`
  close-out PR yok; tracker scope kapanışında frozen olur.

## Notes

- **Branching policy (user direction):** W16 stays on `main`. No
  separate `week16` branch is opened; sub-iter commits land directly
  on `main`. This differs from the W11/W12/W13/W14/W15 paterni; the
  per-iter close-out merge step is replaced by tracker freezing at
  scope close.
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
