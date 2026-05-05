# REFACTOR_OPTIMIZATION

`Last Updated: 2026-05-05`

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
| **W9** | Executor↔Detection boundary | container-packaging ADR (TBD; ADR 0008 if next), dual-import fallback sweep, `signal_policy.py` relocation, `sys.path.insert` audit, container import-mode CI test | Claude §6/§10; Codex §9/§4 |
| **W10** | Contract hygiene + Planner split | `schema_version` + DeprecationWarning, `_TriggerPayloadDraft` elimination, `registry.py` 4-way split, `automation_health`/`coverage_*` typing | Codex §1.2/§1.4/§2; Claude §4 |
| **W11** | Monitor lifecycle split | `monitor_lifecycle.py` 834 LoC → `MonitorRuntime` + `ReportAssembler` + `ScenarioAccountant` + `ExtensionMonitor` facade | Codex §3.1; Claude §3 |
| **W12** | Executor subpackaging + attribution cleanup | `executor/flows/playwright/` 54 → 5 subpackage; `entrypoint_runner.main` 487→≤200 LoC; attribution facade cleanup | Codex §3.1/§3.2/§4; Claude §2/§3/§5 |
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
pattern'lerinin elimine edilmesi; container-packaging ADR (number TBD;
ADR 0008 if next available) — paket-mode vs top-level import kararı;
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

**Goal:** `executor/flows/playwright/` 54 flat dosya → 5 subpackage
({monitor, stimulus, workspace, health, entrypoint}/); `entrypoint_runner.main`
487 LoC → ≤200 LoC dispatch extraction; attribution facade underscore
cleanup; `raw_context` per-event-type typing.

Detail: archive §11.9.

### §11.10 — W13 Test Expansion + Observability

**Goal:** Benign silence fixture 3→5; stale singleton-lock + `.env`
gitignore regression tests; `extrace.executor.*` logger consolidation;
run-ID stamping; W8-W12 regression lock-in.

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
