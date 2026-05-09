# REFACTOR_OPTIMIZATION

`Last Updated: 2026-05-07`

W0-W13 plan dokümanı: stabilizasyon + güvenlik + post-PoC external-review
integration. **Slim canonical** — full historical content (review pass'leri,
weekly detail blocks, bulgular tablosu) frozen under
[`archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md).
Tarihsel detayı yalnız spesifik bir referans bunu açıkça istediğinde aç.

## Anchor Map (For Inbound Cross-Refs)

Diğer dokümanlardan gelen başlıca anchor referansları aşağıdadır. Heading
isimleri ve bölüm numaralandırması korunur; içerik özet düzeyindedir.

- §10 / §10.3 / §10.7 → W0-W7 PoC window (kapalı). Bkz. §10 aşağıda.
- §11 / §11.0 - §11.4 → W8-W13 entry/scope (özet aşağıda).
- §11.5 → **moved to**
  [`active-work/W8-security.md`](active-work/W8-security.md).
- §11.6 - §11.10 → W9-W13 weekly briefs (özet aşağıda; detay archive).
- §11.11 - §11.14 → cross-ref + rejected + lane + exit criteria (özet
  aşağıda; detay archive).

---

## §10 — W0-W7 PoC Stabilization Window (closed 2026-04-23)

PoC penceresi 7 hafta süren stabilizasyon → güvenlik akışıyla planlandı.
Pencere 2026-04-23 tarihinde §10.7 acceptance bar 11/11 green ile kapandı.
Hafta dağılımı, prensipler, paralel ajan lane'leri ve W1/W5 entry checklist
tarihsel referans olduğu için archive altında. Aktif inbound atıf yok.

### §10.7 — PoC acceptance checklist (W7 sonu, closed 2026-04-23)

W7 sonunda aşağıdakilerin hepsi yeşil olduğunda PoC kabul sayıldı.

**Stabilizasyon tarafı (closed):**

- [x] Legacy klasörler silinmiş (`routers/`, `scanner/`, `core/`,
      `database/`, `crud/`, `models/`, `schemas/`).
- [x] `packages/` import-graph testi CI'da çalışıyor.
- [x] VS Code versiyonu Dockerfile'da pinli; harness extension checksum
      doğrulamalı.
- [x] `monitor.py` capture/ alt paketine ayrılmış.
- [x] `ExecutorControl` sarmalayıcı mevcut; API süreci `docker` modülünü
      doğrudan import etmiyor.

**Detection tarafı (closed):**

- [x] A1/A2/A4/A6 her biri için en az bir T1 canary `confidence ≥ medium`
      ve severity ≥ `high` ile ateşliyor.
- [x] Benign baseline'da production rule false-positive yok
      (`correlative_suspicious_activity` benign baseline'da sessiz).
- [x] Scenario-dropout honesty: `requested_scenarios` ↔ `scenarios_run`
      farkı `failed_scenarios` veya `skipped_scenarios` üzerinden
      raporlanıyor.
- [x] `make test-security` CI'da yeşil.
- [x] Verdict rollup `inconclusive` vakalarını doğru işaretliyor.
- [x] UI'da `DetectionReport` görüntüleniyor; finding evidence deep-link'i
      aktivasyon raporuna geçiyor.
- [x] Demo senaryosu yazılmış (`scripts/demo_acceptance.py` → `DEMO GREEN`).

Tam tarihsel test sonuçları + W7 closure log:
`archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md` §10.7 ve
`REFACTOR_STATUS.md` (slim canonical).

---

## §11 — W8-W13 External Review Integration Window (2026-04-24+)

PoC penceresi (W0-W7) §10.7 acceptance bar (11/11 green, 2026-04-23) ile
kapandığında iki bağımsız external review dokümanı teslim edildi
(Claude Opus 4.7 ve Codex GPT-5.4, her biri 18 bölüm). §11 bu iki review'ı
**§10 penceresini değiştirmeden** altı haftalık post-PoC hardening +
modülerleştirme window'una entegre eder.

Review dokümanları snapshot olarak `archive/reviews/` altında dondurulmuş:

- [`archive/reviews/claude_code_review.md`](archive/reviews/claude_code_review.md)
- [`archive/reviews/codex_project_review.md`](archive/reviews/codex_project_review.md)

### §11.0 — Neden §11, §10'a ek satır değil

§10 PoC acceptance bar'ı altında yazıldı; §10.7 ile sabitlendi. Aynı
tabloya W8-W13 eklemek "PoC acceptance bar'ı kaymış" sinyali verir.
İki review **stabilizasyon değil**, post-PoC hardening + modülerleştirme
turudur; kapsamı ayrı tutmak audit trail için gerekli.

### §11.1 — Entry Gate (W8 başlama koşulu)

W8 entry gate **MET as of 2026-04-27** (tarihsel kayıt):

- [x] PR345 tüm PR'ları (1-5) landed.
- [x] ADR 0006 `target-output-channel-capture` Accepted.
- [x] `make test-security` → 45 passing (entry-gate baseline; current
      lane is 170+ cases — `REFACTOR_STATUS.md`).
- [x] `scripts/demo_acceptance.py` → `DEMO GREEN`.
- [x] `REFACTOR_STATUS.md` "PR345 Complete" closure block.
- [x] W8-0 deterministic harness readiness gate landed.

W8 açıldı `2026-04-27` ve **kapandı `2026-04-29`** (W8-1..W8-7 + W8-9
landed, W8-8 deferred). Closure detayları `REFACTOR_STATUS.md` ve
`active-work/W8-security.md`'da. W9 kapandı `2026-05-04` (PR #9), W10
kapandı `2026-05-04` (PR #11), **W11 kapandı `2026-05-05`** (W11-1..W11-8
landed on the `week11` working branch). Past W11 tracker:
`active-work/W11-monitor-lifecycle.md`. Aktif faz: W12 executor
subpackaging + attribution cleanup (§11.9).

### §11.2 — Haftalık dağılım (W8-W13)

| Hafta | Etiket | Kapsam (özet) | Kaynak |
|---|---|---|---|
| **W8** | Güvenlik sıkılaştırma | VSIX zip-bomb guard, marketplace identity helper, URI trigger argv-form, absolute paths, router regex consolidation, content-sample redaction, ADR 0007 local network binding, manifest log-sanitization | Claude §1/§18; Codex §1; supplementary 2026-04-25 |
| **W9** | Executor↔Detection boundary | ADR 0008 container package-mode invocation, dual-import fallback sweep, `signal_policy.py` relocation, `sys.path.insert` audit, container import-mode CI test | Claude §6/§10; Codex §9/§4 |
| **W10** | Contract hygiene + Planner split | `schema_version` + DeprecationWarning, `_TriggerPayloadDraft` elimination, `registry.py` 4-way split, `automation_health`/`coverage_*` typing | Codex §1.2/§1.4/§2; Claude §4 |
| **W11** | Monitor lifecycle split | `monitor_lifecycle.py` 834 LoC → `MonitorRuntime` + `ReportAssembler` + `ScenarioAccountant` + `ExtensionMonitor` facade | Codex §3.1; Claude §3 |
| **W12** | Executor subpackaging + attribution cleanup | W12-1 landed 2026-05-07 (`b4bd3ee` + follow-ups): `executor/flows/playwright/` 54 → 7 new subpackages + 10 flat (10 package dirs total with existing attribution/scenarios/runtime_capture); W12-2 attribution facade cleanup landed; W12-3 `raw_context` discriminated union typing landed (3 named + 4 extra variants under `event_class` discriminator); W12-4 landed 2026-05-10: `entrypoint/runner.py::main` 324 → 99 LoC (≤200 LoC budget) via dispatch extraction to new `entrypoint/dispatch.py` (`PageRef` + 6 helper functions). All four W12 work items landed; W12 close acceptance bar pending | Codex §3.1/§3.2/§4; Claude §2/§3/§5 |
| **W13** | Test expansion + observability | Benign silence 3→5 fixture, regression locks, `extrace.executor.*` logger consolidation, run-ID stamping | Claude §9/§12; Codex §10/§12 |

### §11.3 — Haftalar arası bağımlılıklar

- W8 ve W9 paralel — file çakışması yok.
- W10 ← W9 (container-packaging ADR + dual-import kill typed contract
  import path'ini kararlaştırır).
- W11 ← W10 (typed contract update'leri monitor split assembler
  imzasında oturmalı).
- W12 ← W11 (subpackaging deterministik olabilmek için lifecycle önce
  split edilmeli).
- W13 ← W8-W12 (her hafta regression test bırakır; W13 merkezi lock-in).

### §11.4 — Non-goals (W8-W13 kapsamında olmayan)

`POST_POC_BACKLOG.md`'de kalan ve W13 sonunda yeniden değerlendirilecek
maddeler: UI surface stabilizasyonu (POST_POC § "UI"), A5/A7 T1/T2 canary,
test-security-live T2/T3 lane, T3 handling, doc consolidation, mypy strict,
monorepo tooling, OpenAPI client gen, allow-list versioned artifacts,
domain service pattern genişletmesi (2.8).

### §11.5 — W8 Güvenlik Sıkılaştırma

**Moved to [`active-work/W8-security.md`](active-work/W8-security.md).**

Aktif tracker; 8 stable-ID item (W8-1..W8-8). Code comments and tests
reference items by ID. Slim canonical artık §11.5 detayını taşımaz; eski
`§11.5 item N` referansları `active-work/W8-security.md item W8-N`
formuna eşdeğerdir.

Status quick glance:

- W8-1 — landed `2026-04-27`
- W8-2 — landed `2026-04-27`
- W8-3 — landed `2026-04-28`
- W8-4 — landed `2026-04-29`
- W8-5 — landed `2026-04-29`
- W8-6 — landed `2026-04-29`
- W8-7 — landed `2026-04-29`
- W8-8 — deferred `2026-04-29` (named triggers; see
  `active-work/W8-security.md`)
- W8-9 — landed `2026-05-02` (external-review follow-up on
  `feat/w9-executor-detection-boundary`)

### §11.6 — W9 Executor↔Detection Boundary

**Goal:** Paket import topolojisinde `except ImportError` dual-fallback
pattern'lerinin elimine edilmesi; ADR 0008 container package-mode
kararı; paket-mode vs top-level import kararı;
`signal_policy.py` lokasyonu; `sys.path.insert` audit; container
import-mode CI test.

Detail: `archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md` §11.6.

### §11.7 — W10 Contract Hygiene + Planner Cleanup

**Goal:** `schema_version` + DeprecationWarning rollout; `_TriggerPayloadDraft`
elimination; `registry.py` 4-way split (planner/runner/registry/types);
`automation_health` ve `coverage_*` typing.

Detail: archive §11.7.

### §11.8 — W11 Monitor Lifecycle Split

**Goal:** `monitor_lifecycle.py` (834 LoC) →
`MonitorRuntime` + `ReportAssembler` + `ScenarioAccountant` +
`ExtensionMonitor` facade; `activation_discovery_strategies` report field;
per-strategy `_stop_*` helpers.

Detail: archive §11.8.

### §11.9 — W12 Executor Subpackaging + Attribution Cleanup

**Goal:** `executor/flows/playwright/` 54 flat dosya → ≤10 flat files
via the planned 5 subpackages plus any needed helper packages;
`entrypoint/runner.py::main` 324 LoC → ≤200 LoC dispatch extraction
(W11-3 sonrası post-extraction baseline; pre-W11 pencerede 487 LoC idi);
attribution facade underscore cleanup; `raw_context` per-event-type typing.

Detail: archive §11.9. Active tracker:
[`active-work/W12-executor-subpackaging.md`](active-work/W12-executor-subpackaging.md)
(W12-1..W12-4 stable IDs, entry/exit criteria, pre-W12 precursor gate).

**W12-1 landed 2026-05-07** (commit `b4bd3ee` plus follow-ups): the
planned 5-subpackage target expanded to 7 new packages (`monitor/`,
`stimulus/`, `workspace/`, `health/`, `entrypoint/`) plus `vscode/`
and `signals/` to satisfy the ≤10 flat-file exit criterion, alongside
the existing `attribution/`, `scenarios/`, and `runtime_capture/`
packages. Cycle break via PEP 562 `__getattr__` lazy proxy in
`monitor/__init__.py` plus a lazy `RiskSignal` import inside
`attribution._build_risk_signals`. Two
mimari kapı landed in
[`tests/architecture/test_import_graph.py`](../tests/architecture/test_import_graph.py)
in the same commit
(`test_monitor_facade_does_not_eagerly_import_attribution`,
`test_monitor_and_stimulus_subpackages_do_not_cross_import`); follow-up
gates landed post-commit
(`test_monitor_lazy_proxy_completeness`,
`test_executor_playwright_flat_file_count_limit`,
`test_attribution_does_not_eagerly_import_monitor`,
`test_python_m_playwright_invocations_have_main_module`). Live-scan
deferred to W12 close.

**W12-2 landed 2026-05-07** (commits `37fcaad` + `0cef876` +
`9ebc5b5` + `0981e92`): attribution facade trimmed from 29
underscore re-exports to 10 public names; naming-overlap,
coverage-summary, and activation-discovery strategy-outcome follow-ups
closed. W12-3 `raw_context` typing was unblocked here.

**W12-3 landed 2026-05-07**: `EvidenceEvent.raw_context: dict[str, Any]`
flipped to `RawContext = Annotated[..., Field(discriminator="event_class")]`
in `packages/analysis_contracts/evidence.py`. Scope-extension note: the
literal §11.9 plan named only `NetworkRawContext` / `FileRawContext` /
`ProcessRawContext`, written for the pre-W7 world where each event class
carried its own `raw_context`. After the W7+W11 `EvidenceEvent`
consolidation the live producer (`attribution/links.py`) emits seven
distinct `kind`s, so the union covers all seven (3 named + 4 extra:
scenario, activation, ui_blocker, output_channel_appendline) — closing
exit-criteria bullet 4 with `dict[str, Any]` residue 0. Incidental fix:
`packages/analysis_engine/rules/_common.py::event_method` migrated from
the never-emitted `method` key to the producer's actual `http_method`
(latent bug surfaced once typed variants pinned the field set; a4
workspace-exfil canary fires correctly on HTTP fallback now). UI TS
contracts regenerated.

**W12-4 landed 2026-05-10**: `executor/flows/playwright/entrypoint/runner.py::main`
324 → 99 LoC (limit ≤200) via dispatch extraction to new
`executor/flows/playwright/entrypoint/dispatch.py` (402 LoC). The new
module owns the 6-way execution mode dispatch (`demo` /
`skip_automation` / `layered_passes` / `selected_scenarios` /
`single_scenario` / default-all `run_all_scenarios`), monitor setup,
page-callback factory, extra-trigger application, skipped-scenario
summary, and monitor finalize sequence. `PageRef` mutable wrapper
crosses the page-rebind invariant (callbacks-after-reload) across
the module boundary without `nonlocal`. Pattern follows W11-1
(`monitor_lifecycle.py` 834→split): pure relocation, no behavior
change, no generic framework / strategy registry / event bus
introduced. Two new architecture gates pin the readability ratchet:
`tests/architecture/test_runner_main_loc_budget.py::test_runner_main_under_loc_budget`
(AST gate, ≤200 LoC) and `::test_runner_main_dispatch_helpers_remain_imported`
(import-contract pin). Direct unit coverage for the dispatch module
lives in `tests/executor/test_playwright_dispatch.py`. All four W12
work items landed; W12 close acceptance bar (full `make check-all`
plus `make test-security` plus live-scan validation) is the remaining
exit-criteria gate.

**Pre-W12-4 hardening pull-forward (added `2026-05-07` audit pass):**
W12-3 close sırasında yapılan denetim iki pre-W12-4 sertleştirme öğesini
açığa çıkardı; ikisi de `POST_POC_BACKLOG.md` "W12 Pull-Forward"
bölümünde OPEN olarak takip ediliyor ve W12-4 dispatch extraction'ından
**önce** landlanacak:

- ~~`[FOLLOWUP w12-0-output-signal-multiline-secret-redaction]`~~ —
  closed `2026-05-08` on `week12`. Cross-line `private_key` pattern'i
  yeni `redact_multiline_secrets` helper'ı ile her iki yolda
  (`read_output_channel_logs` + `parse_output_signal_events`) `splitlines()`
  öncesi pre-pass olarak uygulanıyor. Single-line pattern'lar per-marker /
  per-line `redact_secrets`'ta kaldı (whole-input uygulamak JSON marker
  yapısını bozardı). 4 yeni regression case'i, existing 20 case
  regression'sız.
- ~~`[FOLLOWUP api-docker-base-image-digest-pin]`~~ — closed
  `2026-05-09` on `week12`. `docker/api/Dockerfile:2` now pins
  `python:3.11-slim-bookworm@sha256:cd67330292a51e2963156f74ff340455d66b2172e9190e99f40dff9357471177`
  formunda;
  new AST gate `tests/architecture/test_dockerfile_digest_pin.py`
  covers `docker/` + `executor/container/` Dockerfiles. W12-4 is no
  longer blocked by this ADR 0002 item.

#### §11.9.1 — `runtime_capture/extension_host.py` Split Scoping

`runtime_capture/extension_host.py` (679 LoC; executor flow tree'deki
en büyük tek dosya) üç bağımsız capture source'unu sahipleniyor:
exthost.log parser, strace text-mode line parser, ve harness output
capture + `ExtensionHostFileCapture` class. Slim canonical §11.9'un
5-subpackage hedefi (`{monitor, stimulus, workspace, health, entrypoint}/`)
bu dosyaya dokunmaz — archive §11.9 line 2341 `runtime_capture/`'ı
non-goal olarak işaretler. Ancak dosya boyutu pratikte W12 radar
içinde; `runtime_capture/` tree'sinin split target'ı W12 giriş
bandında belirsiz kalmıştı. Bu alt-bölüm o boşluğu doldurur:

- **`extension_host_log_parse.py`** (~200 LoC) — `exthost.log` parser
- **`extension_host_strace_parse.py`** (~200 LoC) — strace text-mode
  line parser
- **`extension_host_capture.py`** (~250 LoC) — harness output capture +
  `ExtensionHostFileCapture` class
- Plus a re-export facade (`runtime_capture/extension_host.py` thin
  `__all__`-only wrapper; W11-7/W11-8 ahtapot pattern, mypy `--strict`
  re-export form)

Safety floor: `[FOLLOWUP w11-precursor-tests]` (LANDED `2026-05-04`,
23-case net at `tests/executor/test_playwright_extension_host.py`)
imported the module at its real path so the split cannot silently
regress. Backlog item: `[FOLLOWUP w12-extension-host-split-scoping]`.
Stable ID assignment deferred to
W12 entry; landing pattern follows W11-7/W11-8 ahtapot closure
(facade + per-source split + mypy `--strict` re-export, callers
unchanged).

### §11.10 — W13 Test Expansion + Observability

**Goal:** Benign silence fixture 3→5; stale singleton-lock + `.env`
gitignore regression tests; `extrace.executor.*` logger consolidation;
run-ID stamping; W8-W12 regression lock-in.

**W13 candidates added `2026-05-07` audit pass** (full detail in
`POST_POC_BACKLOG.md`):

- `[FOLLOWUP scenario-accountant-conservation-split]` —
  `monitor/scenario_accountant.py` 648 LoC (W11-close 426; +222 LoC
  drift). W11-1 lifecycle split pattern: precursor tests → conservation
  - intermediate-emission helper extraction. Lane: `[executor-runtime]`.
- `[FOLLOWUP evidence-event-kind-raw-context-invariant]` —
  `EvidenceEvent.kind` ↔ `raw_context.event_class` pairing validator
  yok; `_common.py` accessor'ları getattr fallback'larla bu açığı
  defensive olarak kapatıyor. Pydantic v2 `model_validator` + explicit
  mapping. Lane: `[security-detection]`.
- `[FOLLOWUP ui-raw-context-discriminator-parity]` — Generated TS
  contracts'ta `event_class?: string` (literal değil); 5 legacy adapter
  fallback'ı `event_class` set etmiyor. Generator + adapter fix. Lane:
  `[ui]`.
- `[FOLLOWUP planner-selection-readability-audit]` — Watching item;
  `analysis_planner/selection.py` 497 LoC, mutation-heavy closure'lar.
  Refactor önerisi YOK; sadece yeni activation family veya planner
  bug'ı tetiklediğinde ele al. Lane: `[security-detection]`.

**W13 candidates added `2026-05-09` audit pass (Codex review):**

- ~~`[FOLLOWUP vsix-threshold-dto-generator-coverage]`~~ — closed
  `2026-05-09` on `week12`. VSIX threshold
  DTO blokları (`ui/src/lib/types/contracts.ts:560-593`) manuel
  eklenmişti; artık backend-owned Pydantic schemas +
  `scripts/generate_ui_contracts.py` `TARGET_SCHEMAS` üretiyor. Manual
  tail kalktı; generator coverage testi ve `--check` gate'i bu drift'i
  kilitliyor. `[FOLLOWUP ui-supplemental-types-retire]` açık kalır
  çünkü diğer supplemental UI-only tipler hâlâ var. Lane: `[ui]`
  `[contracts]`.
- ~~`[FOLLOWUP settings-page-stale-localstorage-copy]`~~ — closed
  `2026-05-09` on `week12`. Settings header copy artık general
  localStorage tercihleri ile API-persisted Security thresholds'ı ayırıyor;
  `SettingsPage.test.tsx` regression'ı pinliyor. Lane: `[ui]`.
- ~~`[FOLLOWUP security-settings-commit-ownership]`~~ — closed
  `2026-05-09` on `week12`. Operator-settings write transaction boundary
  workflow service'ten CRUD facade helper'a taşındı; yeni abstraction yok.
  Lane: `[platform-storage]`.
- `[FOLLOWUP attribution-links-build-evidence-bundle-density]` —
  Watching item; `attribution/links.py` 601 LoC, `build_evidence_bundle()`
  birden çok event-class varyantını tek yerde topluyor. W12-3 union
  genişledikten sonra fragility arttı; refactor önerisi YOK,
  `[FOLLOWUP evidence-event-kind-raw-context-invariant]` landlandığında
  yeniden değerlendir. Lane: `[executor-runtime]`.

**Pre-W12-4 / W13 sürüklenen item:**

- ~~`[FOLLOWUP marketplace-installer-tail-multiline-redaction]`~~ —
  closed `2026-05-09` on `week12`. `workflows/marketplace/analysis_execution.py`
  now applies `redact_multiline_secrets(output)` before the 500-char
  installer stderr/stdout tail, then the existing single-line
  `redact_secrets` pass. Regression:
  `test_install_failure_message_redacts_multiline_pem_split_by_tail`.
  Lane: `[marketplace-analysis]` `[security-detection]`.

Detail: archive §11.10.

### §11.11 — Kaynak Cross-Reference Tablosu

W8-W13 bulgularının iki review'ın hangi bölümlerinden türediğini gösteren
tam tablo archive §11.11 altındadır. Pratikte ihtiyaç olduğu nadirdir
(çoğunlukla audit trail için). Aktif iş için W8 tracker'ı yeterlidir.

### §11.12 — Rejected Items (iki review, promote edilmedi)

Review'larda yer alan ancak §11.2 weekly split'e dâhil edilmeyen
findings'in red gerekçeleri archive §11.12 altındadır. Re-evaluation W13
sonu dokuman consolidation pass'inde yapılır.

### §11.13 — Paralel lane assignments (§10.4 + W8-W13)

W0-W7 lane assignment'larının W8-W13'e devamı archive §11.13. Aktif lane
docs `documents/agent-lanes/` altında.

### §11.14 — W13-end Overall Exit Criteria

W13 sonunda overall exit criteria (rule lane breadth, contract drift
guard, monitor split health, executor topology) archive §11.14. Bu pencere
açıldığında current-state `REFACTOR_STATUS.md` slim canonical'da takip
edilir.

---

## Archive Pointer

Frozen full content (review passes 1-2-3, full §10 weekly breakdowns,
detailed §11.5-§11.14 specs, kod kalitesi değerlendirmeleri):
[`archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md).

Re-archive when this slim canonical exceeds the 2,500-token budget. Drop a
new dated snapshot under `archive/plans/`, then trim — see
`agent-lanes/docs-maintenance.md` invariants.
