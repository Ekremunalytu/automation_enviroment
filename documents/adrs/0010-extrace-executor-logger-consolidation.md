# ADR 0010: `extrace.*` Logger Consolidation

- Status: Accepted and implemented (`2026-05-13`)
- Date: 2026-05-13
- Accepted + Implemented: 2026-05-13 via W14-5 on the `week14` branch.
  See the Implementation section below and
  `documents/active-work/W14-codex-acceptance-observability.md`.
- Related: AGENTS.md §"Non-Negotiable Rules" line 52
  ("Keep critical operations observable through logs, report fields,
  traces, or metrics"); ADR 0007 (Local Network Binding Discipline)
  shares the same opt-in-defaults pattern across observability /
  network surfaces.

## Context

`extrace`'in observability altyapısı W14 öncesinde iki farklı boşluk
taşıyordu:

1. **Logger init dağınıklığı.** `workflows/marketplace/*` ve
   `workflows/security_settings/router.py` altındaki altı modül
   her biri `logger = logging.getLogger(__name__)` kalıbını
   kullanıyordu. Modül adları (`workflows.marketplace.client`,
   `workflows.marketplace.router`, ...) bir taxonomy oluşturmuyordu;
   namespace prefix'i yoktu, bu yüzden runtime'da `extrace`'e ait
   bütün log satırlarını tek bir `getLogger("extrace").setLevel(...)`
   ile yönlendirmek mümkün değildi. Daha kötüsü, `executor/` subtree'sinde
   **zero** `logging.getLogger(...)` çağrısı vardı — executor
   modülleri kendi logger'larını init etmiyordu; emit'ler ya ana
   process'in default `root` logger'ını kullanıyor ya da hiç
   görünmüyordu. Aynı scan run'ı worker thread'den, daemon
   thread'den, ve docker exec subprocess'inden farklı formatlarda
   log satırı üretiyordu.

2. **Structured field sözleşmesi yok.** `EXTRACE_EPOCH_RUN_ID` env
   var'ı W8-0 staleness check'i için
   `executor/flows/playwright/stimulus/attempts.py:452`'da
   tüketiliyor ama log emit pipeline'ına bağlı değil. Tek bir scan
   içinde üretilen log satırları arasında run-ID korelasyonu yok;
   operatör hangi log satırının hangi scan'e ait olduğunu manuel
   olarak (timestamp / pid / thread) çıkartmak zorunda. Executor
   build parmak izi (`commit_sha`, `version`, `build_date`)
   activation_report.json'a veya log'lara basılmıyor — bir scan
   raporuna bakıldığında hangi executor revizyonunun ürettiği
   tespit edilemiyor.

§11.10 GOAL (`REFACTOR_OPTIMIZATION.md`) bu iki boşluğu W13'ten W14'e
defer etti. W14-5 her ikisini de kapatır: logger consolidation altyapıyı
kurar, run-ID stamping ve executor runtime fingerprint emit ise structured
field sözleşmesini doldurur.

## Decision

**Tek bir central factory + bir context filter + kapalı bir namespace
taxonomy.**

### 1. Namespace taxonomy

Tüm production logger'ları `extrace.<area>.*` prefix'i altında yaşar:

| Prefix | Sahibi |
|---|---|
| `extrace.executor.*` | `executor/` subtree |
| `extrace.workflows.*` | `workflows/marketplace/*`, `workflows/security_settings/*`, vb. |
| `extrace.appcore.*` | `appcore/api/*`, `appcore/storage/*` (bugün boş; ileri kullanımlar için açık) |
| `extrace.packages.*` | `packages/analysis_engine/rules/*` ve diğer paket-içi emit'ler (bugün boş; ileri kullanımlar için açık) |

Namespace prefix'i factory'de zorlanır; başka bir prefix kullanmak
istemek `LoggerNamespaceError` raise eder. Bu liste **kapalı**:
yeni bir prefix eklemek `appcore/logging.py:_APPROVED_PREFIXES` +
`tests/architecture/test_logger_consolidation.py:APPROVED_PREFIXES`
güncellemesi + bu ADR'a satır eklemeyi gerektirir.

### 2. Tek factory + tek LogRecord stamping mekanizması

`appcore/logging.py` aşağıdaki public sembolleri export eder:

- `get_extrace_logger(name) -> logging.Logger`
- `LogContextFilter` (logging.Filter alt sınıfı; standalone kullanım için)
- `install_extrace_log_context_filter() -> None`
- `set_executor_fingerprint_provider(provider)` (W14-5 sub-commit 3)

`get_extrace_logger("extrace.workflows.marketplace.client")` çağrısı,
`logging.getLogger(...)`'in doğrudan eşdeğeridir; tek farkı namespace
validation yapmasıdır.

**Structured-field contract.** Her `LogRecord` üç alan stamp alır:

- `record.run_id` — `EXTRACE_EPOCH_RUN_ID` env var'ının emit anındaki
  değeri (yoksa boş string).
- `record.executor_fingerprint` — registered fingerprint provider'ın
  döndürdüğü kısa parmak izi (W14-5 sub-commit 3
  `executor.runtime_fingerprint.executor_fingerprint`'i wire eder;
  provider yoksa boş string).
- `record.thread_name` — `threading.current_thread().name` (eğer
  caller `extra={"thread_name": ...}` ile explicit override
  etmemişse).

**Stamping mekanizması: global LogRecord factory.**
`install_extrace_log_context_filter()` Python `logging` framework'ünün
`setLogRecordFactory(...)` hook'unu kullanarak her `LogRecord`'u
yaratıldığı anda stamp'ler. Idempotent: wrapper factory üzerinde
`_is_extrace_factory=True` sentinel taşıdığı için tekrar çağrı
no-op. Mevcut bir third-party factory varsa (örn. başka bir
gözlemlenebilirlik kütüphanesi) onu da chain'ler — base factory'nin
ürettiği attribute'lar korunur, W14-5 alanları üstüne stamp edilir.

**Neden parent-logger filter değil.** Python `logging` framework'ü
`Logger.callHandlers()` sırasında parent logger'lara propagate
ederken parent'in `filters` listesini çalıştırmaz — sadece
`handlers`'ı çalıştırır. Bu, `extrace` parent'ina bir filter
eklemenin child logger'ların emit'lerinde **etkili olmadığı**
anlamına gelir (filter sadece kayıt o logger'da originate olduğunda
çalışır). W14-5 sub-commit 1 ilk olarak parent-logger filter
yaklaşımını denedi; sub-commit 2 W14-5'in entegrasyon testleri
yazılırken bu Python davranışı keşfedildi ve install hook'u
`setLogRecordFactory(...)` chokepoint'ine retarget edildi. Tek
emit-time chokepoint olduğu için LogRecord factory her child
logger'ı, her thread'i, her propagation path'ini kapsar.

**`LogContextFilter` class'ı neden hala var.** Stamping logic'i
factory ve filter form'larında ortak bir helper (`_stamp_record`)
üzerinden gider. Filter form'u, factory'nin global override'ından
bağımsız olarak belirli bir handler'a iliştirmek isteyen veya
tek bir test'in factory'yi izole etmek isteyen caller'lar için
korunur.

### 3. Migration scope

W14-5 sub-commit 1 altında migrate edilen siteler (6 site):

- `workflows/marketplace/client.py`
- `workflows/marketplace/router.py`
- `workflows/marketplace/trigger_service.py`
- `workflows/marketplace/analysis_execution.py`
- `workflows/marketplace/analysis_service.py`
- `workflows/security_settings/router.py`

Her site `import logging` + `logger = logging.getLogger(__name__)`
örüntüsünden `from appcore.logging import get_extrace_logger` +
`logger = get_extrace_logger("extrace.workflows.<module-path>")`
örüntüsüne geçer. Logger ismi modül yolunu birebir takip eder
(kısaltma yapılmaz) — grep'lemeyi kolaylaştırmak için.

`executor/` subtree'sinde bugün zero logger init var; consolidation
gate (`test_logger_consolidation.py`) forward-looking olarak
executor altına eklenmek istenecek `logging.getLogger(...)`
çağrılarını reddeder.

### 4. Architecture gate

`tests/architecture/test_logger_consolidation.py` iki invariant pin'ler:

- **No-raw-getLogger gate.** `executor/`, `workflows/marketplace/`,
  `workflows/security_settings/` subtree'lerindeki hiçbir modülde
  `logging.getLogger(...)` veya `getLogger(...)` çağrısı bulunmamalı.
  Tek exempt path: `appcore/logging.py` (factory'nin kendisi).
- **Approved-prefix gate.** Aynı subtree'lerde `get_extrace_logger(...)`
  çağrıları string literal ile çağrılmalı ve literal `_APPROVED_PREFIXES`
  listesindeki bir prefix ile başlamalı.

İki invariant birlikte: yeni bir modülün ya `get_extrace_logger`
ile factory'den geçmesini ya da hiç logger almamasını zorlar.

### 5. FastAPI startup hook

Filter'ı erkenden bağlamak için, FastAPI uygulamasının startup
hook'unda `install_extrace_log_context_filter()` bir kez
çağrılır (W14-5 sub-commit 2 wires this when the run-ID stamping
arrives). Tek seferlik install idempotent olduğu için reentry
güvenli; testler kendi `monkeypatch`'leri ile filter'ı sıfırlayıp
geri ekleyebilir.

## Consequences

### Positive

- Observability hard rule (AGENTS.md:52) gerçek bir contract'a
  bağlanır: her log satırı `run_id` + `executor_fingerprint`
  taşıyacak. Operatör bir scan raporunu bir log dump'ı ile
  korelasyon kurabilir.
- Worker thread / daemon thread / docker exec subprocess'inden
  çıkan emit'ler aynı format'a sahip olur; emit kaynakları tek
  central factory'den geçtiği için future filter eklemeleri
  (örn. PII redaction layer) tek noktadan eklenebilir.
- Namespace taxonomy log level tuning'i mümkün kılar:
  `logging.getLogger("extrace.executor").setLevel(logging.DEBUG)`
  tek bir alan için verbose mode'a alır; üretici namespace adlarını
  bu hierarchy üzerinden bilinçli tasarlayabilir.
- Forward-looking gate executor subtree'de yeni eklenmek istenecek
  any raw `getLogger(__name__)` örüntüsünü PR review öncesi
  reddeder — silent regression imkansız.

### Negative

- Migration sırasında namespace string'lerini elle yazmak gerekiyor
  (`__name__` interpolation'a değil — gate string literal
  bekliyor). Tek seferlik bir maliyet ve grep'lemeyi kolaylaştırma
  faydası karşılığı kabul edildi.
- `appcore/logging.py` Python stdlib `logging` modülünü gölgelemiyor
  (çakışma yok; explicit `from appcore.logging import ...` zorunlu).
  Çakışma yaratacak bir kullanım çıkarsa rename gerekebilir, ama
  factory + filter dışında public symbol yok.

### Follow-On

- W14-5 sub-commit 2 (`[GOAL w14-run-id-stamping]`):
  `EXTRACE_EPOCH_RUN_ID`'ın `_run_docker_exec` boundary'sinden
  geçişi (`[FOLLOWUP codex-2026-05-10-M5-epoch-docker-exec-propagation]`
  doğal yan ürünü) + filter'ın gerçek env-source'la doğrulama
  testleri.
- W14-5 sub-commit 3 (`[FOLLOWUP codex-automation-5]`):
  `executor/runtime_fingerprint.py` modülü ve
  `set_executor_fingerprint_provider(...)` çağrısının startup
  hook'tan yapılması; automation output boundary'sinde fingerprint
  emit'i.
- W14-6 (`[FOLLOWUP arch-gate-executor-control-outbound]` + sibling'ler)
  bu ADR'a doğrudan bağlı değil; aynı W14 close-out PR ailesinde
  birlikte iniş yapar.

## Implementation

Landed `2026-05-13` on `week14` (W14-5 sub-commit 1).

- `appcore/logging.py` — yeni modül; factory, filter, install hook,
  fingerprint provider setter.
- `workflows/marketplace/{client,router,trigger_service,analysis_execution,analysis_service}.py`
  + `workflows/security_settings/router.py` — 6 site migrate.
- `tests/platform/test_extrace_logging.py` — factory + filter
  behavior coverage (namespace reject, run-ID stamping, idempotent
  install).
- `tests/architecture/test_logger_consolidation.py` — AST gate;
  no-raw-getLogger + approved-prefix invariants.
- `documents/active-work/W14-codex-acceptance-observability.md`
  §"W14-5 — Logger consolidation + run-ID stamping + runtime
  fingerprint" — full landing evidence (sub-commit table, module
  locations, test deltas) sub-commit 3 sonunda yazılır.
