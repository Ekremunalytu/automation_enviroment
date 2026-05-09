# Post-PoC Backlog

`Last Updated: 2026-05-09 (5 new FOLLOWUPs added from Codex review pass; full detail archived)`

Open deferred work after the W0-W7 PoC acceptance bar. **Slim canonical** —
verbose descriptions, evidence, and older triage notes are frozen in dated
snapshots:

- latest full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-07.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-07.md)
- previous full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-04.md)

W8, W9, W10, and W11 are closed. Active phase: **W12 executor
subpackaging + attribution cleanup**, tracked in
[`active-work/W12-executor-subpackaging.md`](active-work/W12-executor-subpackaging.md).

## Stable IDs Are A Contract

Do not rename existing IDs. Code/tests currently reference:

- `[FOLLOWUP analysis-jobs-race]`
- `[FOLLOWUP simulation-progress-cancel]`
- `[FOLLOWUP simulation-progress-cancel] cancel-after-finish race test`
- this filename from `packages/analysis_contracts/contracts.py`

Use stable IDs in new references; do not cite canonical doc line numbers.

## W12 Pull-Forward

- ~~**`[FOLLOWUP w8-6-output-signals-file-backed-redaction]`**~~ —
  **W12-0 landed `2026-05-07` on `week12` in commit `22eb836`.**
  `redact_secrets(_truncate(line))` applied at
  `executor/flows/playwright/signals/output.py:209` (path post-W12-1;
  was `output_signals.py:205` at W12-0 landing); W10-7 source
  comment updated to name both harness-marker and file-backed paths;
  four file-backed regression tests + three harness-marker
  end-to-end regressions added under
  `tests/platform/security/test_output_signals_redaction.py`. W12-1
  unblocked.
- ~~**`[FOLLOWUP w12-promoted-attempt-coverage-erasure]`**~~ —
  **landed `2026-05-07` on `week12` in commit `422a647`.**
  `_derive_runtime_attempted_capabilities` in
  `executor/flows/playwright/monitor/runtime.py` filtered status to
  `{verified, attempted_only, failed}`. After
  `reconcile_event_attempts` (`health/reconciliation.py:187,219`)
  promoted an attempt to `activation_seen` or `target_log_seen` (target
  reacted but full verification did not close), `report_assembler.py:128`
  overwrote `attempted_capabilities` from the runtime view, erasing the
  promoted capability and surfacing `not_attempted` in
  `coverage_summary` despite the target reacting. Routed the filter
  through `RUNTIME_EVIDENCE_STATES` (single source of truth in
  `packages/analysis_contracts/report_invariants.py`) so promoted
  states count as runtime evidence here, matching the contract
  invariant `_attempt_has_runtime_evidence` and the W10-6 docstring.
  Two regression cases under
  `tests/executor/test_playwright_monitor_attribution.py`
  (`test_runtime_attempted_includes_{activation_seen,target_log_seen}_promotion`).
- ~~**`[FOLLOWUP w12-legacy-strategy-outcomes-migration]`**~~ —
  **landed `2026-05-07` on `week12` in commit `ba1accb`.**
  W12-2 P3 (`0981e92`) renamed
  `activation_discovery_strategies: list[str]` →
  `activation_discovery_strategy_outcomes: dict[str, str]` under the
  same `schema_version: "2.1"`. `StrictContractModel(extra="forbid")`
  rejected every 2.1 report persisted in the W11-3 .. W12-2 P3 window
  with `extra_forbidden`, breaking the activation-report API
  (`workflows/activation_reports/router.py:122`) and the marketplace
  ingest path (`workflows/marketplace/analysis_reports.py:52,121`).
  Added `_migrate_legacy_strategy_outcomes` before-validator on
  `ActivationReport`: drops the legacy field and synthesizes the new
  dict, mapping each id → `"succeeded_with_new_activations"` (the
  legacy list semantics). 3 regression cases under
  `tests/platform/contracts/test_activation_discovery_strategies.py`;
  on-disk pre-rename report `c20ac6f91d4a.json` re-ingests cleanly.
- ~~**`[FOLLOWUP w8-6-output-signal-channel-summary-redaction]`**~~ —
  **W12-0 dolgusu landed `2026-05-07` on `week12` in commit `b642af7`.**
  `OutputSignalEvent.channel` ve `OutputSignalEvent.summary` hem
  harness-marker (`signals/output.py:~116`) hem de file-backed
  (`signals/output.py:~180`) source'larda
  `redact_secrets(_truncate(...))` pipeline'ından geçiyor; `summary`
  alan değeri `f"OutputChannel({channel}) appendLine"` olduğu için
  redact'lı channel'ı otomatik miras alır. Adversarial extension
  `vscode.window.createOutputChannel("AKIA...")` çağırarak persisted
  ActivationReport'a secret sızdıramıyor. 7 yeni regression case'i
  (4 harness-marker + 2 file-backed + 1 benign-channel guard)
  `tests/platform/security/test_output_signals_redaction.py`'ye
  eklendi. W12-3 unblocked.
- ~~**`[FOLLOWUP w12-0-output-signal-multiline-secret-redaction]`**~~ —
  **CLOSED `2026-05-08`** on `week12`. Fix:
  `packages/analysis_contracts/evidence.py`'ye `redact_multiline_secrets`
  helper'ı eklendi (sadece `_CROSS_LINE_CLASSES = {"private_key"}`
  pattern'lerini uygular); `signals/output.py` her iki yolda
  (`read_output_channel_logs` + `parse_output_signal_events`)
  `splitlines()` öncesi pre-pass olarak çağırıyor. Single-line pattern'lar
  per-marker `redact_secrets`'ta kaldı çünkü whole-input uygulamak JSON
  marker yapısını bozar (api_key opsiyonel trailing-quote tüketimi
  kapatan `"`'yu yutar). 4 yeni regression
  `tests/platform/security/test_output_signals_redaction.py`'ye eklendi
  (file-backed multi-line PEM block, file-backed PEM with surrounding
  diagnostic lines, harness-marker cross-marker PEM, harness-marker
  single-marker embedded-newline PEM). Existing 20 case'in tamamı
  regression'sız.
- **`[FOLLOWUP api-docker-base-image-digest-pin]`** —
  **OPEN, P1, pre-W12-4.** `docker/api/Dockerfile:2`
  `FROM python:3.11-slim-bookworm` (sadece tag, digest yok).
  `executor/container/Dockerfile:8` ise
  `FROM ubuntu:22.04@sha256:962f6cadeae0ea6284001009daa4cc9a8c37e75d1f5191cf0eb83fe565b63dd7`
  ile pinned. ADR 0002 §4 trust table (`documents/adrs/0002-threat-model.md:97`)
  her base image için `FROM image@sha256:...` zorunluyor — bu net bir
  ADR ihlali. API container FastAPI yüzeyi + Docker socket bridge
  olduğu için kritik boundary; mutable tag aynı Dockerfile'ın zamanla
  farklı base image üretmesine yol açabilir. Fix: (a)
  `docker/api/Dockerfile:2`'yi `FROM python:3.11-slim-bookworm@sha256:...`
  formuna geçir (mevcut imajın digest'ini `docker pull` ile çekip pinle);
  (b) yeni AST gate `tests/architecture/test_dockerfile_digest_pin.py`
  ekle — `docker/` ve `executor/container/` altındaki her `Dockerfile`'ın
  `FROM` satırı `@sha256:` içermeli. Yeni dependency yok. Lane:
  `[platform-storage]`.
- **`[FOLLOWUP marketplace-installer-tail-multiline-redaction]`** —
  **OPEN, P2, pre-W12-4 / W13-X.** Surfaced `2026-05-09` audit pass
  (Codex review). `workflows/marketplace/analysis_execution.py:80`
  installer failure helper sırası **slice → redact**:
  `tail = redact_secrets(output[-500:].strip())`. Single-line token'larda
  doğru çalışır ama multi-line `private_key` PEM bloku 500 karakterlik
  pencereyi bölünce (veya pencere içinde BEGIN/END eşleşmesini parçalarsa)
  `redact_secrets` pattern'i tüm bloku göremez — W12-0 öncesi
  `signals/output.py`'da kapatılan **tam paralel** bypass. W12-0 fix
  (`[FOLLOWUP w12-0-output-signal-multiline-secret-redaction]`,
  `2026-05-08`) `redact_multiline_secrets` pre-pass desenini kurdu;
  bu callsite o desene migrate edilmedi. Gerçek sızıntı operatöre
  `code --install-extension` stderr'inin attacker-controlled içerik
  taşıdığı durumlarda; severity Medium çünkü sızıntı yüzeyi installer
  hata akışı. Fix: önce
  `redact_multiline_secrets(output)` whole-content pre-pass, sonra
  tail (`output[-500:]`), sonra existing `redact_secrets(_truncate(...))`
  per-tail; mantık `executor/flows/playwright/report_builder.py`'daki
  W11-6 "trim → expand → redact" desenine paralel olur. Tests:
  `tests/workflows/marketplace/test_analysis_execution.py::test_install_failure_message_redacts_multiline_pem`
  - cross-boundary 500-char split case. W11-6 / W12-0 ile
  yapılan iş bu callsite'a yansıtıldığı için yeni bağımlılık veya
  helper gerekmiyor. Severity: Medium. Lane:
  `[marketplace-analysis]` `[security-detection]`.

## W12 Acceptance Items

- ~~**`[FOLLOWUP w12-attribution-naming-overlap]`**~~ — closed
  `2026-05-07` in commit `0cef876` (W12-2 Commit 2). Rename:
  `background_activation_count` → `target_background_activation_count`;
  `competing_candidate_count` → `competing_extension_event_count`. UI
  contract + adapter + view-model + fixtures updated.
- ~~**`[FOLLOWUP w12-precursor-tests-attribution-links]`**~~ — closed
  `2026-05-07` in commit `5ae0d32`; 26 link-helper cases landed.
- ~~**`[FOLLOWUP w12-precursor-tests-attribution-events]`**~~ — closed
  `2026-05-07` in commit `5ae0d32`; 34 event-helper cases landed.
- **`[FOLLOWUP w12-extension-host-split-scoping]`** — plan addendum
  closed by PR #15; implementation lands during W12 as the
  `runtime_capture/extension_host.py` ahtapot split.
- ~~**`[FOLLOWUP coverage-summary-attempted-drift]`**~~ — closed
  `2026-05-07` in commit `9ebc5b5` (W12-2 Commit 3). The assembler
  collapses planner-seeded `attempted_capabilities` and
  `heuristic_attempted_capabilities` to the runtime-derived
  `event_attempts` view before coverage reconcile, so top-level report
  fields and `coverage_summary["attempted_capabilities"]` resolve to
  one value.
- ~~**`[FOLLOWUP activation-discovery-strategy-outcome-detail]`**~~ —
  closed `2026-05-07` in commit `0981e92` (W12-2 Commit 4, P3). Field
  upgraded from `activation_discovery_strategies: list[str]` to
  `activation_discovery_strategy_outcomes: dict[str, str]` with outcome
  literals `succeeded_with_new_activations` /
  `succeeded_no_new_activations` / `failed:<ExcClassName>`.

## Open Items By Area

### Workflow / Platform

- **`[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread`**
  — move sandbox reset out of the daemon heartbeat thread.
- **`[FOLLOWUP simulation-progress-cancel] dedupe-step-progress-schemas`**
  — reconcile `AnalysisJobStepProgress` vs `AnalyzeJobStepProgress`.
- **`[FOLLOWUP simulation-progress-cancel] is-job-cancelled-session-churn`**
  — revisit fresh DB session polling if profiling shows pressure.
- **`[FOLLOWUP simulation-progress-cancel] heartbeat-refactor`** — extract
  heartbeat polling/JSON/cancel logic into a testable helper.
- **`analysis_service._open_job_session`** — move `SessionLocal` import
  back to module top once the startup-cycle constraint is gone.
- **`run_analysis_job` exception narrowing** — replace broad handling with
  enumerated error paths where possible.
- **`[FOLLOWUP analysis-thread-supervisor]`** — keep daemon-job rows from
  sticking in `running` on unenumerated `BaseException`.
- **`[FOLLOWUP sqlalchemy-error-subtype-logging]`** — distinguish
  `IntegrityError`, `OperationalError`, and `ProgrammingError` for triage.
- **`search_marketplace` return typing** — tighten public return shape.
- **Domain service pattern expansion** — pull remaining router surfaces into
  the established domain-service shape.
- **Migration hardening** — `make migrate` destructive-op precheck plus
  Alembic reversibility audit.
- **`[FOLLOWUP job-service-typevar-audit]`** — keep or remove the generic
  `_run_in_session()` typevar based on mypy/readability value.
- **`[FOLLOWUP w11-8-companion-workflow-orm-bleed]`** — decide DTO
  migration vs documented boundary exception for workflow return types that
  expose storage ORM models.
- **`[FOLLOWUP security-settings-commit-ownership]`** —
  **OPEN, P3, W13-X.** Surfaced `2026-05-09` audit pass (Codex review).
  `workflows/security_settings/service.py:84-85` `save_vsix_thresholds()`
  CRUD facade üzerinden `upsert_operator_settings_bulk(db, ...)` çağırıp
  ardından kendisi `db.commit()` yapıyor; AGENTS.md rule 2'nin "write
  logic CRUD'da" zorunluluğu **ihlal edilmiyor** (write logic
  `appcore/storage/crud_ops/operator_settings.py:65-77`'de kalmaya
  devam ediyor) ama transaction boundary workflow tarafında. Mevcut
  storage deseninde commit ownership genelde CRUD/job lifecycle
  tarafında (`crud_ops/analysis_jobs/lifecycle.py` örüntüsü).
  Bugün küçük yüzey; settings alanı büyürse workflow service
  transaction ownership almaya başlar ve "DB write/commit nerede
  yapılır?" sınırı bulanıklaşır. Fix seçenekleri: (a) yeni helper
  `save_operator_settings_bulk_and_commit(db, items, updated_by)`
  CRUD tarafına; (b) mevcut `upsert_operator_settings_bulk`'a opsiyonel
  `commit: bool = False` parametresi (varsayılan invariant'ı korur);
  (c) `[FOLLOWUP w11-8-companion-workflow-orm-bleed]` kapsamına
  ekleyip DTO/transaction sözleşmesini birlikte revize et. Generic
  framework / unit-of-work / repository abstraction eklenmeyecek.
  Severity: Medium-Low. Lane: `[platform-storage]`.
- **`[FOLLOWUP w8-1-vsix-rejection-log-sanitization]`** — P2; sanitize
  attacker-controlled VSIX entry names before rejection logging.
  Co-tenant of `[FOLLOWUP w8-1-extract-rejection-logging]` (same call
  sites in `workflows/marketplace/client.py`); land jointly in one PR
  to avoid double-touch.

### Executor / Capture

- **T2/T3 live-security plumbing** — harden `make test-security-live`
  around real T2/T3 engagements.
- ~~**`[FOLLOWUP w11-precursor-tests]`**~~ — landed `2026-05-04`.
- ~~**`[BUG silent-scenario-dropout-regression]`**~~ — closed
  `2026-05-07`; last-mile conservation guard reports
  `unaccounted_dropout`.
- **`[BUG scenario-dropout-upstream-root-cause]`** — trace the planner /
  `stimulus_passes` / harness dispatch gap that still drops requested
  scenarios before they reach `ScenarioAccountant`.
- **`[FOLLOWUP monitor-types-property-recomputation]`** — P3; defer until
  profiling shows repeated expensive property access.
- **`[FOLLOWUP scenario-accountant-conservation-split]`** — W13-X.
  `executor/flows/playwright/monitor/scenario_accountant.py` 648 LoC
  (W11 close baseline ~426; +222 LoC drift since W11). Tek collaborator
  scenario lifecycle, event-attempt mutation, scenario conservation,
  activation-log derivation, ve intermediate-state emission'ı taşıyor.
  Hard-rule ihlali değil ama activation debug'ı sırasında en zor
  okunan dosyalardan biri olmaya aday — W12-4 runner split'inden sonra
  executor runtime'daki bir sonraki readability hotspot. W11-1 lifecycle
  split pattern'ini örnek al: önce precursor tests ekle, sonra
  conservation/verification helper'ları ile timeline/intermediate-emission
  helper'larını ayrı modüllere taşı; ana sınıf scenario mutation
  orchestration'ını tutmaya devam etsin. Davranış değişikliği olmamalı,
  generic framework / event bus / plugin abstraction eklenmeyecek.
  W12-4 ve W12-5 ile karıştırma. Severity: Medium. Lane:
  `[executor-runtime]`.
- **`[FOLLOWUP attribution-links-build-evidence-bundle-density]`** —
  **W13-X watching item, refactor önerisi YOK.** Surfaced `2026-05-09`
  audit pass (Codex review). `executor/flows/playwright/attribution/links.py`
  601 LoC; `build_evidence_bundle()` (girişi `links.py:32` civarı)
  birden çok `EvidenceEvent.kind` / `raw_context.event_class` varyantı
  ve link üretim mantığını tek yerde topluyor. W12-3 ile `RawContext`
  union 7 varyanta genişledi; yeni event kind eklendiğinde bu
  fonksiyonun değiştirilmesi kırılganlığı artırır. Bugün güvenlik
  açığı veya hard-rule ihlali değil — okunabilirlik watching'i.
  W12-4 / W12-5 bittikten sonra (en erken W13), küçük explicit helper
  fonksiyonlarına bölünebilir: network/file/process/output/scenario
  event builder'ları gibi. Generic framework, registry pattern,
  abstract factory, plugin abstraction eklenmeyecek; precursor tests
  (`tests/executor/test_playwright_attribution_links.py` 26 cases)
  zaten safety net olarak yerinde, bunlar split sonrası
  bitwise-equal görsel için kullanılabilir.
  `[FOLLOWUP evidence-event-kind-raw-context-invariant]` (W13-X)
  ile kardeş — kind↔event_class invariant'ı landlandığında bu
  fonksiyon zaten daha sıkı tip almış olur, split kararı ona göre
  yeniden değerlendirilir. Severity: Medium-Low. Lane:
  `[executor-runtime]`.

### Detection / Contracts

- ~~**`[FOLLOWUP report-invariants-runtime-evidence-drift]`**~~ — closed
  by W10-6.
- ~~**`[FOLLOWUP planner-executor-action-enum]`**~~ — closed by W10-5.
- ~~**`[FOLLOWUP w8-6-output-signals-redaction]`**~~ — parent closed by
  W10-7 for the harness-marker path; file-backed sibling closed by
  W12-0 (`22eb836`, `2026-05-07`).
- **`[FOLLOWUP signal-summary-needs-review-categories]`** — refine
  category labels for review-oriented verdicts.
- ~~**`[FOLLOWUP target-log-lifecycle-instrumentation]`**~~ — landed with
  W11-4.
- ~~**`[FOLLOWUP w8-6-extension-host-output-redaction]`**~~ — landed with
  the W11 companion.
- **`[FOLLOWUP event-attempt-verification-status-validator]`** — prevent
  drift in runtime-evidence state vocabulary.
- **`[FOLLOWUP compute-verdict-table-driven-test]`** — add table-driven
  coverage for verdict computation.
- **A5/A7 adversary fixtures and allow-list artifacts** — keep deferred
  until the relevant security window.
- **`[FOLLOWUP evidence-event-kind-raw-context-invariant]`** — W13-X.
  `EvidenceEvent.kind: str` ile `raw_context.event_class` literal'i
  arasında pairing validator yok (`packages/analysis_contracts/contracts.py:242,266`);
  Pydantic `kind="network"` + `event_class="file"` kombinasyonunu
  reddetmez. `packages/analysis_engine/rules/_common.py:37-50` accessor'ları
  (`event_type`, `event_method`, `event_message`) `getattr(event.raw_context,
  "...", "")` defensive fallback'larıyla bu boşluğu kapatıyor — yani
  invariant olmadığı için detection helper'ları savunmacı kalmak zorunda.
  Eski rapor migrasyonları, UI adapter fallback'leri veya elle üretilen
  fixture'lar yanlış kombinasyonları sessizce taşıyabilir. Fix: Pydantic
  v2 `model_validator(mode="after")` ekle, kabul edilen mapping'i açıkça
  pinle (`network`→`NetworkRawContext`, `file`→`FileRawContext`,
  `process`→`ProcessRawContext`, `scenario`→`ScenarioRawContext`,
  `activation`→`ActivationRawContext`, `ui_blocker`→`UiBlockerRawContext`,
  `output_channel_appendline`→`OutputChannelRawContext`); legacy summary
  kind'lar intentional olarak farklı context kullanıyorsa explicit
  allow-list. Test:
  `tests/platform/contracts/test_raw_context_discriminated.py::test_evidence_event_rejects_kind_event_class_mismatch`.
  Mevcut canonical reports bozulmamalı. Severity: Medium. Lane:
  `[security-detection]`.
- **`[FOLLOWUP planner-selection-readability-audit]`** — W13-X
  watching item (refactor önerisi YOK).
  `packages/analysis_planner/selection.py` 497 LoC; üç nested closure-based
  dispatch fazı (`_apply_activation_event`, `_apply_contributes_metadata`,
  `_apply_default_fallback`) + mutation-heavy captured callback'lar
  (`mark_scenario`, `register_attempt`). Bugün tek-pas planner fazı
  olarak okunuyor — strategy registry / plugin abstraction değil.
  Sadece yeni activation family eklendiğinde veya planner bug'ı
  çıktığında ele al; küçük helper fonksiyonlar veya veri tabloları
  kullanılabilir. Generic framework, event bus, abstract factory, DI
  container, plugin registry eklenmeyecek. Planner behavior
  değişmemeli; selection output fixture/testleri korunmalı; yeni mimari
  katman yaratılmamalı. Severity: Low. Lane: `[security-detection]`.

### UI

- ~~**`[CLEANUP ui-v3-9]`**~~ and ~~**`[CLEANUP ui-v3-14]`**~~ — closed.
- **`[FOLLOWUP ui-supplemental-types-retire]`** — retire supplemental UI
  type shims once generated contracts fully cover them.
- **`[FOLLOWUP ui-raw-context-discriminator-parity]`** — W13-X.
  Backend `RawContext`'i strict discriminated union
  (`packages/analysis_contracts/evidence.py:183-191`,
  `Field(discriminator="event_class")` + variant başına `Literal[...]`).
  Generated TS contracts (`ui/src/lib/types/contracts.ts:293-350`)
  ise 7 varyantın hepsinde `event_class?: string;` (optional + wide
  string) — generator literal'ı düz string'e indiriyor, discriminator
  parity yok. Ek olarak `ui/src/lib/adapters/report.ts:247,278,318,344,366`
  legacy fallback fonksiyonları (`fromActivation`, `fromNetwork`,
  `fromFile`, `fromProcess`, `fromScenario`) `raw_context` literal'ı
  kuruyor ama hiçbiri `event_class` set etmiyor — bu objeler backend'in
  strict validator'ından geçemezdi, sadece UI-only oldukları için
  hayatta kalıyorlar. Backend W12-3 ile strict olmuşken frontend
  contract bu disiplini yansıtmıyor; ileride typed UI rendering veya
  filtering eklenirse yanlış event sınıfları sessizce kabul edilir.
  Fix: (a) `scripts/generate_ui_contracts.py`'yi her variant için
  `event_class: "network"` (vb.) literal üretecek şekilde güncelle;
  (b) 5 fallback fonksiyonuna kind ↔ event_class eşleştirmesini ekle.
  Tests: `ui/src/lib/adapters/report.test.ts::preserves_raw_context_event_class_for_legacy_fallback_events`
  - generated contract output'unda discriminator literal golden/text
  assertion. Severity: Medium. Lane: `[ui]`.
- **`[FOLLOWUP vsix-threshold-dto-generator-coverage]`** —
  **W13-X.** Surfaced `2026-05-09` audit pass (Codex review).
  `ui/src/lib/types/contracts.ts:1-2` "Generated by
  scripts/generate_ui_contracts.py. Do not edit this file manually."
  diyor; ama satır 560-593 arasında `VsixThresholdBoundsDto`,
  `VsixThresholdsResponseDto`, `VsixThresholdsUpdateRequestDto`,
  `VsixThresholdBreachDetail` blokları **manuel** eklenmiş — yorumda
  "Mirrors `workflows.security_settings.router.ThresholdsResponse`"
  notu var. `scripts/generate_ui_contracts.py:24-59` `TARGET_SCHEMAS`
  listesinde bu 4 isim **yok**, yani backend Pydantic kaynağından
  render edilmiyor; bir sonraki `python scripts/generate_ui_contracts.py`
  çalışması bu blokları silebilir veya backend↔UI drift sessizce
  birikir. Operator-tunable VSIX hardening
  iterasyonunda (`bea3bfe` + `733c3bc` + `f15b6c0` + `65f741a`,
  `2026-05-09`) hızlı landetmek için seçildi; generated-source-of-truth
  disiplini bozulmuş halde. Fix: (a) backend tarafında
  `workflows/security_settings/router.py` response/request tiplerini
  Pydantic modellere çevir (eğer dataclass/TypedDict ise);
  (b) `TARGET_SCHEMAS`'a 4 ismi ekle; (c) manuel blok'ları `contracts.ts`'den
  kaldır; (d) generator'ı çalıştırıp diff'in net regen olduğunu
  doğrula. Alternatif (daha az tercih edilen): generator'a explicit
  bir "supplemental" bloğu kaynağı ekle. `[FOLLOWUP ui-supplemental-types-retire]`
  ile yarı-overlap — birlikte landetmek mantıklı. Tests: golden
  contract output snapshot + UI vitest setup'ında halen tüm tipler
  resolve ediyor. Severity: Medium. Lane: `[ui]` `[contracts]`.
- **`[FOLLOWUP settings-page-stale-localstorage-copy]`** —
  **OPEN, P3, W13-X.** Surfaced `2026-05-09` audit pass (Codex review).
  `ui/src/features/settings/SettingsPage.tsx:150` ve `:454`
  hâlâ "changes are persisted to this browser's localStorage until
  settings API lands" benzeri stale copy taşıyor; aynı sayfada artık
  `2026-05-09` operator-tunable VSIX iterasyonuyla API-backed Security
  threshold formu var (`/api/settings/security/thresholds`). Operatöre
  yanlış mental model veriyor — özellikle threshold ayarlarının kalıcı
  olduğu durumda copy "geçici localStorage" izlenimi bırakıyor.
  Fix: copy'i "general preferences may remain local; security
  thresholds are persisted by the local API" gibi gerçeğe uygun
  metinle değiştir; `[BACKLOG ui-v3-5]` partial-close notuyla uyumlu.
  Bir sonraki Settings dokunuşunda inline halledilebilir; ayrı PR
  şart değil. Severity: Low. Lane: `[ui]`.

### Engineering Quality

- **`[FOLLOWUP ci-reintroduction]`** — restore CI/docs-check after the
  runner-image drift is understood.
- **`[FOLLOWUP arch-gate-network-body-preview-redaction]`** — P2; AST gate
  ensuring body-preview assignments stay behind `redact_secrets`.

### Repo Hygiene

- ~~**`[CLEANUP repo-tracked-scratch-files]`**~~ — landed `2026-05-03`.
- ~~**`[CLEANUP tests-scanner-rename]`**~~ — landed `2026-05-03`.
- **`[CLEANUP report-builder-naming]`** — clarify similarly named report
  builder modules.
- **`[CLEANUP env-example-extrace-vars]`** — align example env names with
  runtime configuration.
- ~~**`[CLEANUP agent-context-phase-snapshot-stale]`**~~ — landed.
- **`[CLEANUP postgres-version-fact-drift]`** — keep documented Postgres
  version aligned with Compose/runtime.
- **`[CLEANUP adr-0007-runbook-wording-drift]`** — keep LAN runbook wording
  synchronized with ADR 0007.
- **`[CLEANUP session-docstring-except-exception]`** — update stale
  docstring language around exception handling.
- **`[CLEANUP uri-validation-stale-sys-path-comment]`** — remove stale
  package-mode comments after W9.
- **`[CLEANUP monitor-runtime-naming-overlap]`** — reduce naming ambiguity
  around monitor runtime modules.
- **`[CLEANUP appcore-config-stale-docstring]`** — replace legacy config
  module wording.
- **`[CLEANUP pre-commit-python-version-alignment]`** — align pre-commit
  Python version with the project/runtime target.
- ~~**`[CLEANUP httpx-runtime-dependency-metadata]`**~~ — verified closed
  `2026-05-06`.
- ~~**`[FOLLOWUP scripts-seed-test-rewrite]`**~~ — closed by file removal.
- ~~**`[FOLLOWUP triggers-private-helper-import]`**~~ — verified resolved.

### Test + Observability

- **`[FOLLOWUP w8-9-network-body-boundary-split-secret-test]`** — P2;
  cover secret patterns split by body-preview truncation.
- **`[FOLLOWUP codex-automation-5]`** — executor runtime fingerprint in
  automation output.
- **`[FOLLOWUP codex-automation-6]`** — UI failure taxonomy.
- **`[FOLLOWUP capability-verification-gap]`** — close remaining debug /
  verification capability gaps.
- **`[FOLLOWUP w8-0-capture-pipeline]`** — preserve capture-pipeline smoke
  coverage beyond the partial W8-0 close.
- ~~**`[FOLLOWUP make-test-security-lane-composition]`**~~ — full close
  recorded after W8 lane composition landed.
- **`[FOLLOWUP w8-4-broader-executor]`** — retire remaining bare-binary
  pragmas when executor helpers move to absolute paths.
- **`[FOLLOWUP w8-1-extract-rejection-logging]`**,
  **`[FOLLOWUP w8-1-archive-count-bypass]`**, and
  **`[FOLLOWUP w8-1-vsix-compressed-size-limit]`** — remaining W8-1 hardening
  and observability follow-ups.
- ~~**`[FOLLOWUP w8-1-vsix-entry-count-limit-realistic]`**~~ —
  closed `2026-05-08` on `week12`. W8-1 baseline `MAX_FILE_COUNT = 2_000`
  was tripped on real users by Microsoft's `2026-05-08` ms-python.python
  release (version `2026.5.2026050801`) — modern Python/Pylance/Jupyter
  bundles ship more entries than the original threshold anticipated.
  Raised to `50_000` in `workflows/marketplace/client.py:37` with inline
  rationale linking the size + ratio guards as the load-bearing
  zip-bomb defense; entry-count remains a complementary DoS guard for
  the extract loop. Existing 7 test_vsix_hardening cases stay
  regression-free (they monkeypatch `MAX_FILE_COUNT` locally, so they
  are decoupled from the constant). Sibling drift surfaced during the
  audit: ADR 0002 references a `§7.2.6` for VSIX extraction guards but
  the section was never authored in the ADR body — captured below.
- **`[FOLLOWUP adr-0002-vsix-extraction-section-missing]`** —
  W8-1 commit `bd9d1f1` referenced ADR 0002 §7.2.6 for adversarial
  VSIX extraction limits, but ADR 0002 only contains §1-6 plus the
  template tail; §7 was never written. Author the missing section
  (zip-bomb defense rationale, file-count complementary guard, current
  thresholds) so the cross-ref in `workflows/marketplace/client.py`
  resolves to actual prose. Lane: `[docs]` `[security-detection]`.
- ~~**`[BACKLOG ui-v3-5]` Settings persistence API**~~ —
  **PARTIALLY CLOSED `2026-05-09`** on `week12`. Backend persistence
  layer landed for the Security/VSIX-hardening section (new
  `operator_settings` table + GET/PUT
  `/api/settings/security/thresholds` + `SecuritySection` form in
  `SettingsPage.tsx`). Other localStorage-backed sections (general,
  executor, telemetry) remain client-only — they retire incrementally
  as their values find a backend consumer. The pre-existing
  `localStorage["extrace-v3-settings"]` legend on the Settings header
  was removed since it no longer accurately describes the whole page.
- **`[FOLLOWUP vsix-integrity-in-activation-report]`** — Stage 9 of
  the 2026-05-09 operator-tunable VSIX hardening iteration was
  deferred to keep that iteration shippable. Carry-over scope: persist
  per-extension VSIX extraction metrics (file_count, uncompressed_size,
  compression_ratio, rejected_entry_count) on the `Extension` entity
  (new alembic migration + 4 nullable columns), wire
  `create_extension_from_directory` to write them, add
  `ActivationReport.vsix_integrity` (additive optional Pydantic model;
  no schema_version bump needed), populate it from Extension at report
  build time (`packages/analysis_engine/runner.py` or
  `executor/.../report_builder.py`), and render a "VSIX Integrity"
  subsection on the Reports overview tab (`ui/src/features/reports/`,
  `ui/src/lib/adapters/report.ts`). Acceptance: Reports page shows
  metrics with green/amber/red coloring keyed off the live thresholds
  (use `apiClient.getSecurityThresholds`); pre-existing fixtures with
  no metrics render as "Metrics unavailable" rather than throwing.
  Stage-9 risk-score visualization flows naturally from this since the
  panel is the report-side mirror of the marketplace post-download
  banner that landed today. Lane: `[ui-v3]` `[security-detection]`
  `[contracts]`.
- **`[FOLLOWUP vsix-thresholds-extra-keys]`** — the
  `operator_settings` table is generic key/value but the W12-* PUT
  endpoint only accepts the three VSIX threshold keys. Future
  operator-tunable values (jobTimeout, retention windows, telemetry
  buffers) should land on the same table; pull in their existing
  localStorage defaults from `SettingsPage.DEFAULT_SETTINGS` when the
  first one needs cross-device sync. Lane: `[settings]`.
- **`[FOLLOWUP w8-3-harness-js-scheme]`** — extend URI trigger hardening.
- ~~**`[FOLLOWUP w8-5-list-endpoint-name-filter]`**~~ — closed
  `2026-04-30`.
- **`[FOLLOWUP w8-6-content-sample-structural-test]`** — broader
  structural enforcement for content-sample redaction.
- **`[FOLLOWUP w8-8-manifest-emit-when-needed]`** — deferred until the
  first manifest-field log emit site or proactive security gate.
- ~~**`[FOLLOWUP arch-gate-no-bare-except]`**~~ — landed.
- **`[FOLLOWUP w8-8-trigger-sweep-as-test]`** — convert W8-8 trigger sweep
  into test coverage when W8-8 lands.
- **`[FOLLOWUP arch-gate-executor-control-outbound]`** — gate outbound
  executor-control boundaries.
- **`[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]`** — ratchet bare
  binary path pragmas as W8-4 follow-ups land.

## How To Pull An Item Back

1. Search by stable ID in this file and the latest full archive snapshot.
2. Confirm code/tests still match the recorded premise.
3. Add or update tests first when the item describes a regression risk.
4. Close by preserving the stable ID and adding the landing date/commit.
