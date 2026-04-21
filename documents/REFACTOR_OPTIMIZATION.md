# Refactor Optimization — Plan Kritiği ve Düzeltme Önerileri

`Last Updated: 2026-04-21`

> **Değerlendirici (yazarlar):**
>
> - **Pass 1 (2026-04-16) — Claude Opus 4.6**, paralel-ajan (Explore subagents)
>   tabanlı kod tabanı incelemesi. Bölüm 1-8 bu geçişin çıktısıdır.
> - **Pass 2 (2026-04-17) — Claude Opus 4.7**, plan + kod revalidation. Bölüm 9
>   ("Güncel Durum Doğrulaması") ve Bölüm 10 ("7 Haftalık Stabilizasyon →
>   Güvenlik Penceresi") bu geçişte eklenmiştir; ayrıca Bölüm 7-8 içindeki
>   stale bulgular üzerine satır-içi `⚠ STALE (YYYY-MM-DD)` notları düşülmüştür.
>
> **Uygulama ajanı:** **GPT-5.4** kod değişikliğini uygular. Bu doküman GPT-5.4
> için spec'tir; her madde için verilen `file_path:line_number` referansları ve
> kabul kriterleri bağlayıcıdır.
>
> **Multi-ajan sağlığı:** Bu doküman iki Claude sürümü ve bir GPT sürümü
> tarafından okunur. Okuma/yazma disiplini:
>
> - Stale bulgular **silinmez**, `⚠ STALE` etiketiyle işaretlenir (geçmiş kanıt
>   kaybolmasın). Bkz. Bölüm 9.
> - Yeni geçiş yapan ajan, Bölüm 9'a o tarihli kısa bir doğrulama bloğu ekler.
> - GPT-5.4 uygulama sırasında stale olmayan maddeleri takip eder; stale
>   maddeleri atlar, commit mesajında `skip(stale: <madde>)` formatında
>   referans verir.
> - Herhangi bir ajan bir maddeyi tamamen reddediyorsa, silmek yerine madde
>   altına `> Reddedildi (ajan, tarih, gerekçe)` bloğu ekler.

Bu doküman, `REFACTOR_EXECUTION_PLAN.md` (Week 1-4B) üzerine yapılan bağımsız bir
değerlendirmenin çıktısıdır. Amacı plana rakip olmak değil, **"modüler ve
kaliteli repo"** hedefine ulaşmak için mevcut planın hangi kararlarının doğru,
hangilerinin yetersiz veya erken ertelenmiş olduğunu kanıta dayalı biçimde
göstermektir.

> **Kapanis notu (2026-04-20):** Week 4 kapanis durumu artik
> `documents/REFACTOR_STATUS.md` dosyasinda tutuluyor. Bu belgeyi okurken,
> burada onerilen maddelerin hangilerinin coktan land ettigini veya stale
> oldugunu o durum panosuyla birlikte degerlendir.

Okuma sırası:

1. Planın doğru kararları (korunmalı)
2. Planın eksik / mantıksız yönleri (borç olarak birikiyor)
3. Week 4C olarak önerilen somut paket
4. Orta vadeli notlar (UI, test piramidi, plan-status ayrımı)
5. Kabul kriterleri ve uygulama sırası
6. Özet (plan kritiğinin kapanışı)
7. Kod Kalitesi Değerlendirmesi (Opus 4.6, paralel-ajan taraması)
8. Kod Kalitesi Önceliklendirmesi (GPT-5.4'ün uygulayacağı madde sırası)

---

## 1. Planın Doğru Kararları — Değiştirme

Aşağıdaki kararlar Week 1-4B iskeletinin sağlam durmasını sağlıyor. Herhangi
birini geri almak planın değerini düşürür.

### 1.1 Sıralama: contracts → planner → correctness → persistence

`REFACTOR_EXECUTION_PLAN.md:73-267` sırasını takip ediyor. **Mantıklı çünkü:**

- Sözleşmeyi (Pydantic v2 backend-owned contracts, Week 2) sabitlemeden
  planner'ı (Week 3) bölmek, iki katmanın aynı anda titremesine yol açardı.
- Persistence'i (Week 4B) correctness'ten (Week 4A) önce yapmak, kayıt edilen
  durumun yanlış semantiği kemikleştirmesine yol açardı; plan bunu tersine
  almış.
- Her adım "no endpoint path change" kuralıyla sınırlandığı için dışarıdan
  gözlemlenen davranış stabil kalıyor.

**Koruma önerisi:** Week 4C ve sonrası için de "önce sınır, sonra state, sonra
güvenlik" sırasına sadık kal.

### 1.2 Exit criteria bazlı haftalar

Her hafta "Goal / Scope / Non-Goals / Entry / Exit / Implementation Snapshot"
bloklarıyla tanımlanmış. **Mantıklı çünkü:**

- "Bittiği nereden belli" sorusu her hafta için somut bir cevaba sahip.
- Non-Goals listesi scope creep'i önceden bloke ediyor (`Week 1 Non-Goals`
  `REFACTOR_EXECUTION_PLAN.md:50-57`).
- Implementation Snapshot bölümleri, hafta kapandıktan sonra "ne yapıldı"
  kanıtını toparlıyor.

**Koruma önerisi:** Aynı template'i Week 4C için de kullan.

### 1.3 Hard rules (AGENTS.md)

`AGENTS.md:17-25` listesi: `(publisher, name, version)` unique, tüm write
`appcore/storage/crud.py` facade'ı üzerinden, Pydantic v2 + SQLAlchemy 2.0,
Alembic zorunlu, sandbox Docker'da. **Mantıklı çünkü:**

- Bu kurallar refactor sırasında ajanların "kestirme" yapmasını engelliyor.
- Week 4B'de `analysis_jobs` tablosu eklenirken bile `crud.py` facade kuralı
  ihlal edilmedi (`appcore/storage/crud.py:3-12`); kural fiilen işliyor.

**Koruma önerisi:** Liste kısa kalmalı. Yeni kural eklerken rastgele eklemek
yerine bir ADR ile gerekçelendir.

### 1.4 Expansion notes'un plandan ayrılması

`REFACTOR_EXPANSION_NOTES.md` Week 5+ fikirlerini plandan ayırıyor.
**Mantıklı çünkü:**

- Bir fikir "görünür" olurken "taahhüt" olmuyor.
- Plan dokümanı status dashboard'a dönüşmüyor, niyet dokümanı olarak kalıyor
  (Week 4A/4B status blokları bu disiplini bozmaya başladı — bkz. 4.3).

**Koruma önerisi:** Week 4C eklenirken expansion notes'tan promote edilenleri
açıkça işaretle (`REFACTOR_EXPANSION_NOTES.md:28-42` pattern'ini kullan).

### 1.5 Week 3 banned-import boundary testi

Planner paketi için web/DB/workflow/executor import'ları test seviyesinde
yasaklanmış (`REFACTOR_EXECUTION_PLAN.md:155-156`). **Mantıklı çünkü:**

- Modülerliği "niyet" seviyesinden "CI kırılır" seviyesine taşıyor.
- Planner'ın gelecekte web frame'i import etmesini imkânsız kılıyor.

**Eksik olan:** Aynı disiplin diğer katmanlara uygulanmamış. Bkz. 2.2.

### 1.6 Baseline fixture + round-trip testleri

`ms-python.python` için donmuş activation report ve trigger payload, Week 2/3'ün
semantik değişmediğini doğrulayan temel kanıt (`REFACTOR_EXECUTION_PLAN.md:116-120`).
**Mantıklı çünkü:**

- Aynı girdi için aynı çıktı üreten "contract tape" oluşturuyor.
- Refactor sırasında davranış kaymasını yakalamanın en ucuz yolu.

**Eksik olan:** Tek fixture istatistiksel olarak zayıf. Bkz. 2.3.

---

## 2. Planın Eksik / Mantıksız Yönleri

Aşağıdaki noktalar tek başına plan yıkıcı değil; ama "kaliteli ve modüler
repo" hedefi açısından **borç olarak birikiyor** ve paralel ajanlarla çalışma
niyetinle doğrudan çelişiyor.

### 2.1 `packages/` charter'ı yok — en büyük mantıksal boşluk

**Sorun:** `REFACTOR_EXECUTION_PLAN.md:27-28` Week 1'de "visible `apps/` ve
`packages/` skeletons" diyor, ama paket nedir net değil:

- `packages/analysis_contracts` ve `packages/analysis_planner` bugün mevcut.
- Ama **paket olmanın anlamı nedir** tanımsız:
  - Import izinleri? (`packages/` → `workflows/` yasak mı?)
  - Bağımlılıkları? (her paketin kendi `pyproject.toml`'ı var mı, yoksa
    root'u mu paylaşıyor?)
  - Versiyonlama? (paketler birbirinden bağımsız versiyonlanacak mı?)
  - Kimin sahibi? ("AI-safe ownership map" Week 5'e ertelenmiş —
    `REFACTOR_EXPANSION_NOTES.md:62-67`)

**Neden mantıksız:** Sen paralel AI ajanlarıyla çalışmak istiyorsun. Paralel
ajanların güvenle çalışması için **dokunabilecekleri / dokunamayacakları
katmanın yazılı olması** ön koşul. Ownership map'i Week 5'e ertelemek, Week
4B'den sonra paralelleşmek istediğinde "her ajan kendi yorumunu getiriyor"
duvarına çarpar.

**Öneri — Week 4C'ye al:**

- `documents/adrs/ADR_PACKAGES_CHARTER.md` yaz:
  - Paket tanımı (tek sorumluluk, stateless, framework-agnostic, test edilebilir
    izole)
  - İzin verilen import grafı (bkz. 2.2)
  - Paket iç yapı standardı (örn. `__init__.py` yalnızca public API export
    eder, alt modüller private)
  - Bağımlılık politikası (paket-içi yalnızca stdlib + Pydantic; workflows
    bağımlılığı eklemek ADR ile)
- `apps/` skeleton'ı bugünkü tree'de nerede, ne işe yarayacak? Eğer
  kullanılmayacaksa sil; kullanılacaksa charter'a ekle. Yarı-dolu
  klasör bırakma.

### 2.2 Dependency graph tek yönlü korunmuyor

**Sorun:** Banned-import testi sadece `packages.analysis_planner` için var.
Oysa modüler bir repo'da tüm katmanlar arası graph tek yönlü korunmalı:

```text
ui  ─►  workflows  ─►  appcore
                ├─►  packages
                └─►  executor

executor  ─►  packages
```

Bugün `workflows/marketplace/` `executor.host`'u direkt import edebiliyor;
bunun gerçekten istenen mi yoksa kaza mı olduğunu hiçbir test sormaz.

**Neden mantıksız:** Modülerliği "iyi niyet" seviyesinde bırakmak, ajanlı
çalışmada ilk ihlalde bozulur. Kural yazılı değilse kural yok demektir.

**Öneri — Week 4C'ye al:**

- `tests/architecture/test_import_graph.py` ekle. `import-linter` veya
  `grimp` kullan (zaten Python ekosisteminde olgun araçlar; yeni
  bağımlılık eklemek AGENTS.md kuralına göre onay ister — bu testi
  ADR ile onayla).
- Test şu kuralları doğrulasın:
  - `appcore/` hiçbir şeyi `workflows/`, `executor/`, `ui/`, `packages/`
    içinden import etmez.
  - `packages/` hiçbir şeyi `workflows/`, `executor/`, `ui/`, `appcore/`
    içinden import etmez; framework-agnostic yardımcı katman olarak kalır.
  - `workflows/` `executor/` içinden **yalnızca** `executor.host` public
    API'sini import edebilir (ya da hiç — boundary'yi burada çek).
  - `workflows/` `packages/` ve `appcore/` kullanabilir; bu iki bağımlılığın
    rolü charter'da açıkça ayrılmalıdır.
  - `executor/` `workflows/`, `ui/`, `appcore/` import etmez; yalnızca
    `packages/` (contracts) kullanır.
- Mevcut ihlalleri kısa bir `whitelist.yml` ile kabul et, yeni ihlalleri
  bloke et. Zamanla whitelist'i sıfıra indir.

### 2.3 Tek fixture (ms-python.python) semantik corpus olarak zayıf

**Sorun:** `REFACTOR_EXECUTION_PLAN.md:157-160` ikinci contrast-heavy
fixture'ı Week 4A ve 4B stabil olduktan sonra yapmayı planlıyor. Ama
Week 4A zaten "runtime correctness" — bir fixture üzerinde validate
edilmiş "runtime correctness" istatistiksel olarak yetersizdir.

Özellikle şu davranışlar tek fixture ile test edilemez:

- `summary.scenarios_run = 0` (sıfır-aktivasyon extension'ı, örn. pure
  color-theme)
- `verification_gap` farklı şekilleri (chat/tool path kapalı vs hiç
  tetiklenmemiş)
- `onLanguageModelTool` varken `onChatParticipant` yokken nasıl
  davranılır

**Neden mantıksız:** Week 4B validation'ı tek fixture ile imzalamak,
gerçek regression ihtimalini görmeden hafta kapatmaktır.

**Öneri — Week 4C'ye al:**

- İkinci fixture olarak minimum iki aday:
  1. **Color-theme extension** (örn. `github.github-vscode-theme`):
     `activationEvents` boş veya yalnızca `onStartupFinished`, runtime
     verification path kapalı. `summary.scenarios_run=0` test eder.
  2. **Pure chat-participant extension**: `onChatParticipant` evet,
     `onLanguageModelTool` hayır. Week 4A'nın kapatmayı iddia ettiği
     "verification closure" path'ini izole test eder.
- `tests/platform/contracts/test_analysis_fixture_baselines.py` bu
  fixture'ları da round-trip test etmeli.
- Smoke corpus'u da genişlet: `tests/smoke/test_marketplace_analysis_smoke.py`
  en az iki fixture'ı paralel koşsun.

### 2.4 Executor control boundary güvenlik borcu olarak ertelenmiş

**Sorun:** `REFACTOR_EXPANSION_NOTES.md:48-51` "API-side Docker host
control'u daralt" maddesi Week 5'e atılmış. Ama bu mesele **mimari
temizlik değil, sandbox güvenlik sınırıdır.**

Bugün `main.py` üzerinden FastAPI süreci Docker daemon'a geniş yetkiyle
erişiyor; analiz edilen extension'ın sandbox'ın dışına sızma yolu tek
bir sınır ihlaline bakıyor.

**Neden mantıksız:** "Sandbox analiz platformu" olan bir projede sandbox
boundary'sinin "nice-to-have" kutusunda durması plan seviyesinde ciddi
bir karardır. Expansion notes'un içinde sessizce durması bu kararı
görünür bile kılmıyor.

**Öneri:** Executor Control Boundary'yi **Week 4C veya Week 5'in ilk
maddesi olarak plana promote et**. Minimum:

- `executor/host.py`'nin Docker CLI/daemon'a yaptığı her çağrıyı tek bir
  `ExecutorControl` arayüzünün arkasına al.
- API süreci yalnızca bu arayüzü görür; doğrudan `docker` import etmez.
- ADR yaz: hangi sandbox primitive'leri kullanıldı, hangileri
  yasaklandı (örn. `--privileged`, host network, host volume mount
  yasak).

### 2.5 Plan ve status karışmış — plan dokümanı dashboard'a dönüyor

**Sorun:** `REFACTOR_EXECUTION_PLAN.md:203-224` Week 4A'nın "Status"
bloğu tarih etiketli kanıtlarla dolu (`2026-04-15`, `422 passed`).
Week 4B için de `254-259` benzer şekilde "implemented, validation
pending" diyor.

Bu bilgiler **değerli**, ama plan dokümanının içinde olmamalı. Plan =
niyet + exit criteria. Status = tarihli doğrulama.

**Neden mantıksız:** İki dokümanın amaçları farklı. Karıştığında:

- Plan okuması uzuyor (Week 5 planlarken eski status bloklarını atlaman
  gerekiyor).
- Tarih etiketleri planı "stale" gibi gösteriyor.
- Status güncellemek için plan dokümanına dokunmak, plan niyeti
  değiştirmeye çok benziyor.

**Öneri:**

- `documents/REFACTOR_STATUS.md` oluştur (tarihli, hafta-başlı).
- Plan dokümanındaki "Implementation Snapshot" ve "Status" bloklarını
  oraya taşı; plan dokümanında sadece "durum: status dosyasında" satırı
  kalsın.
- ADR formatında tutmak da kabul edilebilir (`documents/adrs/` altında
  hafta bazlı birer ADR).

### 2.6 UI refactor iskeleti yok

**Sorun:** Plan sonuna kadar `ui/` sadece "contract tüketicisi". Oysa:

- `ui/src/lib/api/` tipleri **manuel** mi yazılıyor? Eğer öyleyse
  backend contract değişince UI sessizce drift eder.
- `ui/src/features/` altında modül sınırları tutarlı mı? Bir feature
  başka bir feature'ı import edebilir mi?
- Job polling, restart recovery, optimistic update gibi state
  pattern'leri tek yerde mi?

Week 4B UI değişikliği (`ui/src/features/marketplace/MarketplacePage.tsx`)
yalnızca happy path'i güncellemiş; UI tarafında regresyon riski
görünmüyor ama **ölçülmüyor** da.

**Neden mantıksız:** "Modüler ve kaliteli repo" hedefi backend'e indirgenemez.
UI drift eden bir repo modüler sayılmaz.

**Öneri — Week 4D veya 5'in ilk maddesi olarak plana al:**

- **Contract-driven type generation**: `appcore/contracts/` → TypeScript
  tiplerine otomatik türetim (örn. `datamodel-code-generator` + OpenAPI
  schema, ya da `pydantic2ts`). Her `make check-all` bunu çalıştırır; UI
  tipi elle değiştirildiyse CI kırılır.
- UI için import-boundary testi (`eslint-plugin-boundaries` veya
  `dependency-cruiser`):
  - `ui/src/features/A` → `ui/src/features/B` yasak.
  - Her feature kendi `lib/api` dilimini import eder, başka feature'ın
    lib'ini değil.
- UI state pattern ADR'ı: polling vs streaming, restart recovery stratejisi
  (localStorage vs backend query), optimistic update politikası.

### 2.7 Test piramidi ve DB-erişim politikası yazılı değil

**Sorun:** Plan "fast test lanes green" diyor ama:

- Unit/integration/smoke oranı nedir?
- Hangi katman gerçek Postgres'le konuşur (`@pytest.mark.requires_db`),
  hangisi mock kullanır?
- Coverage hedefi var mı, yok mu?

Örnek: Week 4B'de `tests/platform/storage/test_analysis_jobs.py` gerçek
Postgres kullanıyor; `tests/workflows/marketplace/test_router.py` ise
job_service'i mock'luyor. Bu bilinçli bir ayrım mı, yoksa yazan kişinin
tercihi mi — plan söylemiyor.

**Neden mantıksız:** Yazılı olmayan bir test politikası, her PR'da tekrar
tartışılır. Ajanlar tutarsız seçimler yapar.

**Öneri — Week 4C'ye al:**

- `documents/TESTING.md` güncelle (zaten var, boş veya eksikse
  doldur):
  - Unit: pure function, mock'lu, saniyeler mertebesinde.
  - Integration: gerçek DB, `@pytest.mark.requires_db`, dakikalar.
  - Smoke: gerçek executor container, `@pytest.mark.smoke`, dakikalar-on
    dakikalar.
- Her katman için "nerede hangi test tipi" yazılı olsun:
  - `appcore/storage/crud_ops/` → integration zorunlu.
  - `workflows/*/service.py` → unit (mock'lu crud) + integration (gerçek
    crud) karışık.
  - `workflows/*/router.py` → unit (mock'lu service) — gerçek DB
    sadece smoke'ta.
- `make test-unit`, `make test-integration`, `make test-smoke`
  hedefleri Makefile'da ayrık olsun.

### 2.8 Domain service pattern tutarlı değil

**Sorun:** Week 4B `workflows/marketplace/job_service.py` ekledi. Bu iyi
bir soyutlama. Ama diğer domain'lerde (catalog, activation_reports)
karşılık gelen bir `*_service.py` yok.

**Neden mantıksız:** Bir desen ya zorunlu ya yasak olmalı. "Bazen
servis katmanı" en kötüsü — gelecekteki ajanlar hangi domain'de ne
koyacağını bilemeyecek.

**Öneri:**

- ADR yaz: "Her domain için `router → service → crud` üç katmanlı".
  Tek bir domain'de bile write varsa service katmanı zorunlu.
- Mevcut domain'leri (extension_catalog, activation_reports) bu pattern'e
  hizalamak için bir migration planı çıkar (Week 4C değil, Week 5
  adayı).

### 2.9 2026-04-16 kod inceleme bulguları dokümana bağlanmalı

Week 4B çalışma ağacı için yapılan hedefli inceleme, plandaki soyut risklerin
yanında doğrudan takip edilmesi gereken dört somut bulgu üretti. Bunlar
"daha sonra bakarız" notu olarak kalmamalı; ilgili status/follow-up
dokümanlarında açıkça yer almalı.

#### A. VSIX yeniden indirme yolu bozuk arşivi değiştirmiyor

- Konum: `workflows/marketplace/client.py:130-132`
- Sorun: Bozuk extracted directory yeniden oluşturulsa bile diskte duran
  bozuk final `.vsix` dosyası yerinde kalabiliyor.
- Etki: Sonraki sandbox install akışları hâlâ eski bozuk VSIX'i kullanabilir.
- Takip: Week 4B sonrası marketplace download hardening alt işi olarak ele al.

#### B. Startup recovery DB arızasını sessizce yutuyor

- Konum: `workflows/marketplace/job_store.py:51-55`
- Sorun: `recover_interrupted_jobs()` içindeki `OperationalError` yutuluyor.
- Etki: Eksik migration veya erişilemeyen DB ile API ayağa kalkıp durable-job
  garantisini sessizce kaybedebilir.
- Takip: Week 4B validation checklist'ine "migration yoksa fast-fail" maddesi
  eklenmeli.

#### C. Package charter tartışması açıkken execution plan'a promote edilmemeli

- Konum: bu dokümanın önceki `2.2` bölümü
- Sorun: Import graph ancak net bir charter ile uygulanabilir; aksi halde ajan
  lane'leri farklı yorumlar üretir.
- Etki: Multi-worktree/çok-ajans çalışma hedefi için ownership ve boundary
  kuralları yarım kalır.
- Takip: Week 4C önerisinden önce ADR ile boundary yönü bağlanmalı.

#### D. 4B sonrası repo haritası dokümanlarında job persistence drift'i var

- Konumlar:
  - `documents/ARCHITECTURE.md`
  - `documents/EXECUTOR_PLAYWRIGHT.md`
  - `documents/PIPELINE_ROADMAP.md`
- Sorun: Bazı dokümanlar hâlâ `output/analysis_jobs/` ve `_ANALYSIS_JOBS`
  anlatısını kaynak gerçeklik gibi sunuyor.
- Etki: Paralel ajanlar yanlış lane varsayımlarıyla hareket eder; gereksiz
  merge çatışması ve hatalı task routing oluşur.
- Takip: Week 4B doküman hizalama işi, kod stabil kabul edilir edilmez aynı
  commit zincirinde yapılmalı.

---

## 3. Önerilen Week 4C Paketi

Yukarıdaki 2.1, 2.2, 2.3, 2.5, 2.7 "hızlı kazanç" kategorisinde —
çoğu tek oturumda yazılabilir, runtime davranışı değiştirmez, paralel
ajan kullanımını **bugün** iyileştirir.

Bu beşini tek haftalık bir paket olarak plana eklemeni öneriyorum:

### Week 4C — Modülerlik Enforcement + Status Disiplini

**Goal:** Week 4B sonrasında oluşan modüler iddiayı CI ile zorlamak ve
plan dokümanını status yükünden kurtarmak.

**Scope:**

- `documents/adrs/ADR_PACKAGES_CHARTER.md` yaz (2.1).
- `tests/architecture/test_import_graph.py` ekle ve mevcut ihlaller için
  whitelist.yml çıkar (2.2).
- İkinci ve üçüncü fixture'ı ekle (`color-theme` + `chat-only`),
  baseline round-trip ve smoke testlerine dahil et (2.3).
- `documents/REFACTOR_STATUS.md` oluştur; mevcut Week 4A/4B status
  bloklarını taşı, plan dokümanını küçült (2.5).
- `documents/TESTING.md`'ı test piramidi + DB politikasıyla güncelle;
  Makefile'a `test-unit / test-integration / test-smoke` ayrımını
  getir (2.7).

**Non-Goals:**

- Executor control boundary (Week 5 veya 4D'ye bırak — ayrı güvenlik
  ADR'ı gerekiyor).
- UI type generation ve UI boundary testi (Week 4D).
- Diğer domain'lere service pattern genişletmek (Week 5).

**Entry Criteria:**

- Week 4B "validation passed" durumunda (smoke + migration upgrade/
  downgrade + router DB contention testi geçiyor).
- `make test` yeşil.

**Exit Criteria:**

- Yeni bir paket oluştururken charter'a başvurmadan karar
  verilemiyor.
- `test_import_graph.py` whitelist dışı ihlaller için kırılıyor.
- En az üç fixture baseline corpus'ta var.
- Plan dokümanı sadece niyet + exit criteria içeriyor; status ayrı
  dosyada.
- Her test dosyasının hangi piramit katmanına ait olduğu yazılı.

### Week 4D (önerilen) — Sandbox Boundary + UI Sertleştirme

**Scope:**

- Executor control boundary (2.4) — `ExecutorControl` arayüzü, ADR,
  Docker daemon erişimini daraltma.
- UI contract-driven type generation + UI import boundary testi (2.6).

**Not:** 4D, 4C'nin çıktılarına bağımlı (ADR formatı, test
piramidi). Önce 4C, sonra 4D.

### Week 5 — Tutarlılık Genişletmesi

- Domain service pattern'ini extension_catalog ve activation_reports'a
  yay (2.8).
- Deterministic executor runtime (expansion notes).
- Expanded smoke matrix (ms-python + color-theme + chat-only üzerine
  ekleme).

---

## 4. Uygulama Sırası — Somut Adımlar

Her öneriyi şu sıra ile bitirmeni öneriyorum. Sıra önemli çünkü sonraki
adımlar öncekilerin çıktısını kullanır.

1. **Status ayrımı (2.5)** — ilk çünkü plan okuması zaten artıyor.
   - `documents/REFACTOR_STATUS.md` oluştur.
   - `REFACTOR_EXECUTION_PLAN.md:203-224` ve `254-259`'u oraya taşı.
   - Plan dokümanında her hafta için `Status: bkz. REFACTOR_STATUS.md`
     satırı bırak.

2. **Packages charter (2.1)** — ikinci çünkü sonraki testler buna
   referans verecek.
   - `documents/adrs/ADR_PACKAGES_CHARTER.md` yaz.
   - `apps/` klasörünün kaderine karar ver (sil veya charter'a ekle).

3. **Import graph testi (2.2)** — üçüncü çünkü charter'ı CI'ya bağlar.
   - `import-linter` veya `grimp` için ADR onayı al.
   - `tests/architecture/test_import_graph.py` yaz.
   - İhlaller için `tests/architecture/whitelist.yml` ve bunu zamanla
     sıfıra indirme planı yaz.

4. **Fixture genişletme (2.3)** — dördüncü çünkü Week 4B validation'ın
   sağlam ayağı bu.
   - `extensions/` altına iki yeni fixture (color-theme, chat-only).
   - Baseline round-trip testleri (`test_analysis_fixture_baselines.py`)
     ve smoke testleri bunları içersin.

5. **Test piramidi (2.7)** — beşinci çünkü charter ve status ayrımı
   sonrası belgelemek daha kolay.
   - `documents/TESTING.md` güncellemesi.
   - Makefile ayrımı.

6. **Executor control boundary (2.4)** — ayrı hafta (4D).
7. **UI refactor (2.6)** — ayrı hafta (4D).
8. **Domain service tutarlılığı (2.8)** — Week 5.

---

## 5. Kabul Kriterleri Özet Tablosu

| Öneri | Dosya | Kabul kriteri |
|-------|-------|---------------|
| 2.1 Packages charter | `documents/adrs/ADR_PACKAGES_CHARTER.md` | Yeni paket PR'ı charter referansı vermeden geçmez |
| 2.2 Import graph testi | `tests/architecture/test_import_graph.py` | Whitelist dışı yeni ihlal CI'ı kırar |
| 2.3 İkinci+üçüncü fixture | `extensions/<new>/`, `test_analysis_fixture_baselines.py`, `test_marketplace_analysis_smoke.py` | Üç fixture baseline'da round-trip geçer, smoke corpus'u çoklu |
| 2.4 Executor boundary | `executor/control.py` (yeni), `documents/adrs/ADR_EXECUTOR_CONTROL.md` | API süreci `docker` module'ünü doğrudan import etmez |
| 2.5 Status ayrımı | `documents/REFACTOR_STATUS.md` | Plan dokümanı tarih etiketi içermez |
| 2.6 UI type generation | `make ui-types` veya benzeri, UI boundary testi | Backend contract değişikliği UI tip dosyasını otomatik günceller; manuel değişiklik CI'ı kırar |
| 2.7 Test piramidi | `documents/TESTING.md`, `Makefile` | `make test-unit / test-integration / test-smoke` ayrı çalışır |
| 2.8 Domain service | ADR + genişletme planı | Her domain'de `router → service → crud` üçlüsü var |

---

## 6. Özet

Mevcut plan **doğru ama dar**. Disiplinli teslim, contract-first yaklaşım,
expansion notes ayrımı — hepsi sağlam. Ama plan şu an **"backend temizlik"**
formunda; "modüler ve kaliteli repo" vaadinin tamamını karşılamıyor çünkü:

- Modülerliği CI ile zorlamıyor (2.1, 2.2, 2.8).
- Test corpus'unu genişletmiyor (2.3).
- Sandbox boundary kararını görünmezde bırakıyor (2.4).
- UI drift'ini hiç adreslemiyor (2.6).
- Plan/status ayrımını kaybetmeye başladı (2.5).
- Test politikasını yazıya dökmedi (2.7).

Week 4C paketi (bu dokümanın 3. bölümü) bu eksiklerin hızlı kazanç kısmını
kapatır. 4D ve 5 kalan büyük parçaları taşır. Bu eklemeler yapıldığında
"paralel AI ajanlarıyla çalışıyorum" ifadesi **iyi niyet** değil,
**CI-korumalı bir gerçek** olur.

---

## 7. Kod Kalitesi Değerlendirmesi (Opus 4.6)

> Bu bölüm, `appcore/`, `workflows/`, `packages/`, `executor/`, `ui/` ve
> kesişen alanlarda (CI, docs, deps) dört paralel Explore subagent ile
> yapılan kod okumasının sentezidir. Kod değişikliği yapılmamıştır.
> GPT-5.4 bu bulguları spec olarak kullanmalıdır.

### 7.0 Katman Bazında Not

| Katman | Not | Özet |
|---|---|---|
| Backend (appcore + workflows) | **7.5 / 10** | Layering temiz, Pydantic v2 + SQLAlchemy 2.0 disiplini tam. Üç kırılgan nokta var. |
| Executor (sandbox runtime) | **5.5 / 10** | En zayıf halka. 3995 satırlık `monitor.py`, determinism delikleri, güvenlik açık noktaları. |
| Frontend (React/TS) | **7 / 10** | Tip güvenliği çok iyi (hiç `any` yok). İki büyük component ve sınır zorlaması eksik. |
| Cross-cutting (CI, docs, deps) | **6 / 10** | CI ölü path referansı, `.env` commit, legacy klasörler bakımsız. |
| **Genel** | **6.5 / 10** | Temel sağlam; büyüyen iki karmaşıklık cebi + hijyen borcu var. |

### 7.1 Backend — Sağlam, Üç Kırılgan Nokta

**İyi olanlar (korunmalı):**

- `router → service → crud` sınırı marketplace ve extension_catalog'da tutarlı.
- Pydantic v2 disiplini **tam**: hiçbir yerde `class Config`, `.dict()`,
  `.parse_obj()` yok.
- SQLAlchemy 2.0 tam: `session.query()` yok, `select()` + `Mapped[]` her
  yerde; `future=True` + `DeclarativeBase`.
- Özel exception hierarchy var: `TriggerPlanError`, `ActiveAnalysisJobError`,
  `PackageJsonReadError` — generic `Exception` değil.

**Düzeltilecekler:**

#### 7.1.1 `analysis_service.execute_analysis_request` şişmiş

`workflows/marketplace/analysis_service.py:195-329` — **135 satır, 5 nesting
level**, içinde 7 kez tekrarlanan `report()` closure. Test edilmesi zor, okuma
maliyeti yüksek.

**Fix (GPT-5.4 için):** Progress handler'ı bir sınıfa (örn. `_StepReporter`)
taşı; adımları fonksiyonlara böl:
`_reset_sandbox()`, `_install_extension()`, `_build_triggers()`,
`_run_monitoring()`, `_finalize_report()`. Her biri < 40 satır olmalı.
Ana fonksiyon yalnızca dispatch/error-propagation içersin.

**Kabul kriteri:** Her adım ayrı bir test ile mock'lanabiliyor; mevcut
`test_router.py`, `test_marketplace_analysis_smoke.py` yeşil kalıyor.

#### 7.1.2 `SessionLocal` modül seviyesinde import

`workflows/marketplace/analysis_service.py:17` — import zamanında DB engine
oluşturma riski; unit testte mock'lanamıyor. Sadece `run_analysis_job()` (worker
thread) ihtiyacı var.

**Fix:** `from appcore.db.session import SessionLocal` satırını
`run_analysis_job()` (line 342) içine taşı.

**Kabul kriteri:** `python -c "import workflows.marketplace.analysis_service"`
DB engine açmıyor; `tests/workflows/marketplace/` yeşil kalıyor.

#### 7.1.3 `job_store.py` layering sidecar

> ⚠ STALE (2026-04-17, Opus 4.7): `workflows/marketplace/job_store.py` artık
> **silinmiş**; `recover_interrupted_jobs()` `job_service.py`'ye taşınmış ve
> `main.py` yalnızca `job_service` üzerinden çağırıyor. Week 4B status bloğu
> (`REFACTOR_EXECUTION_PLAN.md:256-260`) bunu zaten teyit ediyor. GPT-5.4 bu
> maddeyi uygulamaya almayacak. Bulgu tarihi kanıt olarak bırakıldı.

`workflows/marketplace/job_store.py` — Week 4B sonrası `job_service`
abstraksiyonunu bypass ediyor. `main.py:54` doğrudan
`job_store.recover_interrupted_jobs()` çağırıyor. `get_job_file()` ve
`clear_job_cache()` ölü kod.

**Fix:** `recover_interrupted_jobs()` çağrısını `job_service.py`'ye taşı
(public API olarak). `main.py` yalnızca `job_service.recover_interrupted_jobs()`
çağırsın. `job_store.py`'yi sil veya `_job_recovery_bootstrap.py` olarak
yeniden adlandır ve internal işaretle.

**Kabul kriteri:** `job_store` modülü kod tabanında aranınca import eden
sadece `main.py` ya da test yardımcıları kalmıyor.

#### 7.1.4 Çok-geniş exception yakalama

`workflows/marketplace/analysis_service.py:258` — `except (SQLAlchemyError,
OSError, ValueError, TypeError, AttributeError)`. `AttributeError` ve
`TypeError` fail-fast olmalı; yakalandığında silent bug olasılığı artıyor.
AGENTS.md "no generic try/except Exception" kuralının ruhu ihlal ediliyor.

**Fix:** `AttributeError` ve `TypeError`'u kaldır. Sadece gerçekten runtime
koşullarından kaynaklanan hataları yakala: `SQLAlchemyError`, `OSError`,
`ValueError`.

**Kabul kriteri:** Mevcut testler yeşil; CI'da hiçbir bilinen regression yok.

#### 7.1.5 Return type uyumsuzluğu

`workflows/marketplace/router.py:60` — `search_marketplace` signature `list[dict]`
diyor ama `response_model=list[MarketplaceExtension]`. IDE tip yardımı çalışmıyor.

**Fix:** Signature'ı `list[MarketplaceExtension]` yap; client tarafı (`client.py`
ve `router.py` arasındaki adapter) bu tipi üretecek şekilde uyarlansın.

**Kabul kriteri:** mypy (strict açıldığında) hata vermiyor;
`test_client.py` yeşil.

### 7.2 Executor — En Ciddi Borç Cebi

Plan executor'a dokunmadı, ama kod tabanının **en kırılgan** yeri burası.
Plan Week 4D veya 5'e "Executor Modularization" maddesini eklemeli.

#### 7.2.1 `monitor.py` 3995 satır god-module — KRİTİK

`executor/flows/playwright/monitor.py` — tek dosya, `ExtensionMonitor` (line
1644) üç paralel capture thread'i + page + report + mutable dict'leri tutuyor.
Invariant kontrolü yok, class-level lock yok, state mutations dosyanın her
yerinde.

**Fix:** Minimum dört modüle böl:

- `executor/flows/playwright/capture/network.py` (`NetworkCapture`)
- `executor/flows/playwright/capture/filesystem.py` (`FileSystemCapture`)
- `executor/flows/playwright/capture/extension_host.py` (`ExtensionHostFileCapture`)
- `executor/flows/playwright/monitor.py` (sadece `ExtensionMonitor` facade'ı,
  hedef < 800 satır)

Her capture sınıfı kendi lifecycle'ını yönetir (`start/stop/flush`). Monitor
facade'ı yalnızca orchestration yapar; state mutation'ı yoktur, event'leri
her capture'dan pull eder.

**Kabul kriteri:** `tests/executor/test_playwright_monitor.py` yeşil; fixture
round-trip değişmiyor; `monitor.py` dosya boyutu < 1000 satır.

#### 7.2.2 VS Code "stable" channel pinlenmiş değil — KRİTİK

`executor/container/Dockerfile:12,63` — her build farklı VS Code versiyonu
çekiyor. **Aynı commit, farklı sonuç** sorunu bugün yaşayan gerçek. Expansion
notes'taki "Deterministic Executor Runtime" aslında acil bir problem.

**Fix:** `EXECUTOR_VSCODE_VERSION=<YYYY.MM.DD>` (ya da commit sha) env var'ı
ekle; `update.code.visualstudio.com/v<VERSION>/linux-deb-x64/stable` URL'sinden
pinli versiyon çek. `start.sh` parametreleşsin. `.env.example`'da default
version pinle.

**Kabul kriteri:** Aynı commit iki farklı zamanda build edilince container
imajının VS Code versiyonu aynı.

#### 7.2.3 `time.time()` wall-clock kullanımı

`executor/flows/playwright/monitor.py:1826,1923` — `monitoring_start` ve
`monitoring_end` wall-clock. Sistem saati kayarsa süre bozulur.

**Fix:** Duration için `time.monotonic()`; wall-clock yalnızca display amacıyla
saklansın, süre hesaplamasına girmesin.

**Kabul kriteri:** `test_playwright_monitor.py`'ya "clock drift mock" testi
ekle: saat geri gitse bile duration pozitif.

#### 7.2.4 Report path collision riski

`executor/flows/playwright/entrypoint.py:366-368` — iki eşzamanlı çalışma aynı
`/results/activation_report.json`'a yazıyor; ikinci `replace()` birinciyi
sessizce üstüne yazıyor.

**Fix:** `--report-path` verilmediyse `/results/activation_report_<job_id>.json`
veya UUID'li path üret. Final rename yalnızca successful save sonrası.

**Kabul kriteri:** İki job aynı anda başlatıldığında iki farklı dosya oluşuyor;
test ile doğrulanıyor.

#### 7.2.5 Docker exec retry/backoff yok

`executor/host.py:19-72` — geçici network hıçkırığı → anında job fail.

**Fix:** `_docker_exec` ve `_docker_exec_allow_partial` etrafına exponential
backoff wrapper (max 3 retry, 2^attempt saniye). Yalnızca network/connection
hatalarında retry; non-zero exit code'da retry yok.

**Kabul kriteri:** Kurumsal "container unreachable" senaryosu yeni bir
`test_host_retry.py` ile kapatılıyor.

#### 7.2.6 Harness extension imza doğrulaması yok

`executor/container/start.sh:95-100` —
`/home/executor/flows/harness_extension` checksum'suz yükleniyor.

**Fix:** Dockerfile build aşamasında harness extension'ın hash'ini hesapla
(SHA256), imaja yaz. `start.sh` extension'ı yüklemeden önce hash doğrulasın;
uymazsa hata vererek çıksın.

**Kabul kriteri:** Harness extension dosyası değiştirildiğinde container
start fail oluyor.

#### 7.2.7 Trigger file cleanup host-side fallback yok

`executor/flows/playwright/triggers.py:54-55` — container crash olursa trigger
file kalıyor.

**Fix:** `executor/host.py` içinde `run_playwright_automation` sonrası
`/results/triggers.json` silinmemişse host-side cleanup yap.

**Kabul kriteri:** Container crash simüle edilen testte bir sonraki run temiz
başlıyor.

### 7.3 Frontend — Tip Disiplini Çok İyi, İki Büyük Component

**İyi olanlar (korunmalı):**

- **Sıfır `any`, sıfır `@ts-ignore`, sıfır `as unknown as`** — dikkat çekici.
- `tsconfig.app.json` strict + `noUnusedLocals` + `noUnusedParameters`.
- DTO → ViewModel adapter pattern temiz: `ui/src/lib/adapters/report.ts:91-149`.
- React Query + URL state deep-linking doğru kullanılmış.
- `useDeferredValue` + `startTransition` gibi advanced pattern'ler doğru.

**Düzeltilecekler:**

#### 7.3.1 `Inspector.tsx` 562 LOC

`ui/src/components/evidence/Inspector.tsx` — içinde 5 inline sub-component
(`ProvenanceTab`, `RelationsTab`, `RulesTab`, `SelectedEventHero`,
`InspectorShell`).

**Fix:** Her sub-component ayrı dosyaya taşı:

- `ui/src/components/evidence/inspector/ProvenanceTab.tsx`
- `ui/src/components/evidence/inspector/RelationsTab.tsx`
- `ui/src/components/evidence/inspector/RulesTab.tsx`
- `ui/src/components/evidence/inspector/SelectedEventHero.tsx`
- `ui/src/components/evidence/inspector/InspectorShell.tsx`
- `ui/src/components/evidence/Inspector.tsx` < 150 satır olmalı (sadece tab
  orchestration).

**Kabul kriteri:** Mevcut `Inspector` testleri yeşil; her sub-component en az
bir unit test'e sahip.

#### 7.3.2 `ReportsPage.tsx` 478 LOC

`ui/src/features/reports/ReportsPage.tsx` — filter handling, URL sync, data
loading, render hepsi tek dosyada.

**Fix:** Üçe böl:

- `ui/src/features/reports/hooks/useReportFilters.ts` (URL state + filter logic)
- `ui/src/features/reports/components/ReportsHeader.tsx`
- `ui/src/features/reports/components/ReportsList.tsx`
- `ui/src/features/reports/ReportsPage.tsx` yalnızca compose eder (< 150 satır).

Aynı refactor `ui/src/features/simulation/SimulationPage.tsx` için de
uygulansın (similar structure).

**Kabul kriteri:** Mevcut `ReportsPage.test.tsx` yeşil; filter hook'u ayrı
bir testle kapsansın.

#### 7.3.3 `window.__EXTRACE_CONFIG__` runtime API URL — FRAGILE

`ui/src/lib/api/runtime.ts:2` — runtime window injection, undocumented.

**Fix:** `import.meta.env.VITE_API_BASE_URL` kullan. `.env.development` ve
`.env.production` dosyalarıyla build-time config. `window.__EXTRACE_CONFIG__`
fallback olarak kalabilir ama deprecated olarak işaretlenmeli.

**Kabul kriteri:** `ui/` içinde `window.__EXTRACE_CONFIG__` referansı yalnızca
legacy fallback yolunda.

#### 7.3.4 Fetch'lerde `AbortController` yok

`ui/src/lib/api/http.ts:17` — component unmount olurken in-flight request
iptal edilmiyor.

**Fix:** `requestJson<T>` imzasına `signal?: AbortSignal` parametresi ekle;
React Query entegrasyonunda `queryFn`'in aldığı `signal`'i pas geç.

**Kabul kriteri:** Polling yapan sayfalar (SimulationPage) unmount olunca
pending request'ler iptal ediliyor (test ile doğrulandı).

#### 7.3.5 ESLint feature-boundary rule yok

`ui/eslint.config.js` — `features/A` → `features/B/internal` import engellenmiyor.

**Fix:** `no-restricted-imports` kuralı ekle:

```js
"no-restricted-imports": ["error", {
  patterns: [{
    group: ["features/*/internal/*", "features/*/components/*"],
    message: "Features cannot import another feature's internals"
  }]
}]
```

Her feature `index.ts` üzerinden public API export etmeli.

**Kabul kriteri:** Yeni bir cross-feature internal import CI'ı kırar.

#### 7.3.6 Accessibility zayıf

Sadece `EvidenceTable` keyboard nav'a sahip.

**Fix:** Minimum:

- `Inspector` modal → `role="dialog"`, `aria-modal="true"`, focus trap.
- Tüm butonlarda `aria-label` (ikon-only olanlar).
- Chart wrapper'larına `role="img"` + `aria-label` ile özet.

**Kabul kriteri:** `axe-core` temel audit (en azından 0 critical) geçiyor.

### 7.4 Cross-Cutting — Hijyen Borcu

#### 7.4.1 CI ölü path referansı

`.github/workflows/ci.yml:17,29,90,132,195` — `routers/requirements.txt`
hiç yok (`routers/` boş, sadece `__pycache__`).

**Fix:** Bu satırları `docker/api/requirements.txt` veya `pyproject.toml`'a
işaret edecek şekilde güncelle. `routers/` referanslarını kaldır.

**Kabul kriteri:** `grep -r "routers/requirements" .github/` boş dönüyor.

#### 7.4.2 `.env` commit edilmiş

> ⚠ STALE (2026-04-17, Opus 4.7): `git ls-files | grep -E "^\.env$"` **boş
> dönüyor** — `.env` artık tracked değil, kabul kriteri zaten karşılanmış
> durumda. `.gitignore` pattern'i netleştirme (`*.env` → `/.env`) isteğe bağlı
> ufak iyileştirme olarak kalıyor; güvenlik borcu olarak görülmüyor. GPT-5.4
> bu maddeyi uygulamaya almayacak.

`.gitignore:8` `*.env` diyor ama `.env` tracked. Dev credentials
(`POSTGRES_PASSWORD=postgres`) repo'da.

**Fix:** `git rm --cached .env`; `.env.example` zaten var. `.gitignore`
pattern'ini `/.env` olarak netleştir (root-only match).

**Kabul kriteri:** `git ls-files | grep -E "^\.env$"` boş dönüyor.

#### 7.4.3 Legacy klasörler `__pycache__` ile dolu

`routers/`, `scanner/`, `core/`, `database/`, `crud/`, `models/`, `schemas/` —
hepsi boş, sadece cache. AGENTS.md "not primary" diyor ama silinmemiş.

**Fix:** Hepsini tamamen sil. AGENTS.md'den bu klasörlere atıfı kaldır (artık
"not primary" değil, "yok"). CI `grep` ile bu path'leri yasaklayabilir.

**Kabul kriteri:** `find . -type d -name routers -o -name scanner -o -name core
-o -name database -o -name crud -o -name models -o -name schemas | grep -v
node_modules | grep -v .venv` boş.

#### 7.4.4 mypy strict=false + CI'da blocking değil

`pyproject.toml:112` `strict = false`. `.github/workflows/ci.yml:94` mypy
çalışıyor ama fail merge'i bloklamıyor.

**Fix:** İki adım:

1. Yeni modüller için `strict = true` (per-module override).
2. CI'da mypy job'unun `continue-on-error: false` (veya eşdeğeri).

**Kabul kriteri:** Yeni bir `def foo(x):` (annotasyonsuz) CI'ı kırıyor.

#### 7.4.5 Dokümantasyon fragmantasyonu

12+ markdown (`documents/`) + kökte `ARCHITECTURE.md`. Çift `ARCHITECTURE.md`
(hem kök hem `documents/`). `automation_todo.md`, `DEVELOPMENT_PRIORITIES.md`,
`PIPELINE_ROADMAP.md` stale.

**Fix:**

- Kökteki `ARCHITECTURE.md`'yi sil, `documents/ARCHITECTURE.md`'ye redirect
  eden tek satırlık README ekle veya hiç bırakma.
- `documents/archive/` oluştur; stale dosyaları oraya taşı.
- `documents/README.md`'ye "Authoritative Docs" listesi yaz.

**Kabul kriteri:** `documents/README.md` her aktif dokümanı tek cümleyle
tanımlıyor; archive dışında stale doküman yok.

#### 7.4.6 `make migrate` DB connection check yok

`Makefile:263-266` — Postgres down ise sessizce fail.

**Fix:** Target'ın başına `pg_isready -h $(POSTGRES_HOST)` check.

**Kabul kriteri:** DB down iken `make migrate` anlamlı hata veriyor.

#### 7.4.7 Alembic migration reversibility denenmemiş

12 migration var, hiçbiri `downgrade → upgrade` döngüsüyle test edilmemiş.

**Fix:** `tests/platform/storage/test_migrations.py` ekle:
`alembic upgrade head → downgrade -1 → upgrade head` her migration için
çalışsın.

**Kabul kriteri:** Yeni migration reversible değilse CI kırılıyor.

### 7.5 Üç Yapısal Gözlem

1. **Executor, refactor planında hiç yok.** Plan tamamen "control plane"
   odaklı. Ama kod tabanının en kırılgan yeri executor (7.2). Plan Week 4D/5'e
   "Executor Modularization" maddesini almalı. 7.2.1 tek başına bir haftalık
   iş.

2. **Tip disiplini frontend'de backend'den güçlü.** UI'da sıfır `any`; backend'de
   `**updates: Any`, `list[dict]` gibi loose yerler var. Backend de bu disipline
   çekilmeli (7.4.4 mypy strict ile).

3. **Legacy + `.env` + dead CI path = "bitmemiş taşınma".** Plan Week 1'de
   skeleton'lar kurdu ama eski evi yıkmadı. 7.4.1 / 7.4.2 / 7.4.3 tek bir
   "legacy cleanup" commit'inde tek seferde yapılabilir.

---

## 8. Kod Kalitesi Önceliklendirmesi (GPT-5.4 İçin Uygulama Sırası)

Aşağıdaki sıra, **etki × risk** dengesine göre önerilmiştir. GPT-5.4 bu
sırayı takip etmeli; her madde için verilen `file_path:line_number` ve
kabul kriterleri bağlayıcıdır.

### Acil (Week 4C içinde, risk düşük + etki yüksek)

1. **7.4.3 — Legacy klasörleri sil** (`routers/`, `scanner/`, `core/`,
   `database/`, `crud/`, `models/`, `schemas/`). Tek commit, zero diff risk.
   (2026-04-17 doğrulandı: hâlâ `__pycache__`-only, silinmeyi bekliyor.)
2. **7.4.1 — CI'daki `routers/requirements.txt` referanslarını temizle.**
   `.github/workflows/ci.yml` tek dosya değişikliği.
3. ~~**7.4.2 — `.env` untrack**~~ — ⚠ STALE, zaten yapılmış (bkz. 7.4.2).
4. **7.1.2 — `SessionLocal` modül-seviyesi import'u fonksiyona taşı.** 3
   satırlık değişiklik, testleri rahatlatır.
5. **7.1.5 — `search_marketplace` return type uyumsuzluğunu düzelt.**
6. **7.1.4 — `AttributeError` ve `TypeError`'u geniş `except`'ten çıkar.**

### Kritik ama daha büyük iş (Week 4D-5)

1. **7.2.2 — VS Code version pinleme (determinism).** Bugün yaşayan sorun.
2. **7.2.1 — `monitor.py` modülerleşmesi.** Tek başına bir haftalık iş;
   Week 4D veya Week 5. (2026-04-17 doğrulandı: 3993 satır, hiç bölünmemiş.)
3. ~~**7.1.3 — `job_store.py` layering temizliği.**~~ — ⚠ STALE, Week 4B
   kapanışında tamamlandı; dosya silindi (bkz. 7.1.3).
4. **7.1.1 — `analysis_service.execute_analysis_request` parçalanması.**

### Frontend pass (paralel olabilir)

1. **7.3.1 — `Inspector.tsx` bölünmesi.**
2. **7.3.2 — `ReportsPage.tsx` + `SimulationPage.tsx` bölünmesi.**
3. **7.3.5 — ESLint feature-boundary rule.** Tek config değişikliği.
4. **7.3.3 — `window.__EXTRACE_CONFIG__` → `import.meta.env`.**
5. **7.3.4 — `AbortController` wiring.**

### Güvenlik + dayanıklılık (Week 5 içinde)

1. **7.2.4 — Report path collision fix.**
2. **7.2.6 — Harness extension imza doğrulaması.**
3. **7.2.5 — Docker exec retry/backoff.**
4. **7.2.3 — `time.monotonic()` geçişi.**
5. **7.2.7 — Trigger file cleanup host-side fallback.**

### Hijyen (sürekli)

1. **7.4.4 — mypy strict + CI blocking.**
2. **7.4.5 — Dokümantasyon konsolidasyonu.**
3. **7.4.6 — `make migrate` pre-check.**
4. **7.4.7 — Alembic reversibility testi.**
5. **7.3.6 — Accessibility (axe-core baseline).**

---

## Uygulama Notu (GPT-5.4 İçin)

- Her maddeden önce ilgili test lane'ini çalıştır; yeşil baseline görmeden
  değişikliğe başlama.
- Her madde bittiğinde kabul kriteri yazılı olarak doğrulansın; commit
  mesajında madde numarası referans verilsin (örn. `fix(executor): 7.2.3 —
  use monotonic clock for duration`).
- Bir madde başka bir maddenin altyapısına ihtiyaç duyuyorsa sıra korunmalı
  (örn. 7.2.1'den önce 7.4.7 migration testi kurulmuş olmamalı — bunlar
  bağımsız, ama 7.2.2 sonrası 7.2.1 daha anlamlı).
- AGENTS.md hard rules'ı ihlal edecek bir çözüm önerisi çıkarsa
  (yeni dependency, bare `except Exception`, crud bypass) **durdur ve
  kullanıcıya sor** — dokümanda belirtilen fix'lerden farklılaşma gerekirse
  ADR eşliğinde yapılmalı.
- `⚠ STALE` etiketli maddeler **uygulanmaz**. Commit mesajında bu maddeler
  geçerse `skip(stale: 7.x.y)` formatında atlama açıklaması ver.

---

## 9. Güncel Durum Doğrulaması (2026-04-17, Opus 4.7)

Pass 1 (Opus 4.6, 2026-04-16) yazıldıktan sonra Week 4B kapanışı ve paralel
temizlikler bazı bulguları stale yaptı. Bu bölüm repo'nun 2026-04-17
itibarıyla doğrulanmış durumunu özetler; madde bazlı stale notları
ilgili bölümlerde (`⚠ STALE` etiketi) satır-içi yer alır.

### 9.1 Pass 1'e göre değişenler

| Madde | 2026-04-16 iddiası | 2026-04-17 gerçeği | Durum |
|---|---|---|---|
| 7.1.3 `job_store.py` | `job_service`'i bypass ediyor | Dosya silinmiş, `job_service` tek yol | ⚠ STALE |
| 7.4.2 `.env` tracked | `git ls-files` `.env` döndürüyor | Tracked değil, `.env.example` tek sürüm | ⚠ STALE |

### 9.2 Pass 1 bulgularından hâlâ geçerli olanlar (spot-check)

- `routers/ scanner/ core/ database/ crud/ models/ schemas/` — **hâlâ mevcut**,
  içlerinde yalnızca `__pycache__`. 7.4.3 açık.
- `apps/api`, `apps/ui` — yalnızca `README.md` içeriyor. 2.1'deki "yarım
  skeleton" uyarısı geçerliliğini koruyor; `apps/` charter kararı hâlâ eksik.
- `packages/` altında `analysis_contracts`, `analysis_planner`,
  `analysis_engine` var; charter (2.1) ve import-graph testi (2.2) hâlâ yok.
- `executor/flows/playwright/monitor.py` — **3993 satır**, 7.2.1 hâlâ en
  büyük tekil borç.
- `tests/architecture/` klasörü yok; 2.2 yazılmamış durumda.
- Fixture corpus'u hâlâ tek (`extensions/ms-python.python`); 2.3 açık
  (extensions/ altında 36 fixture var ama baseline/smoke yalnızca
  `ms-python.python`'a dayanıyor).

### 9.3 Pass 2 ek bulgular — güvenlik duruşu

Pass 2 (Opus 4.7, 2026-04-17) siber güvenlikçi bakış açısıyla yapılan
değerlendirmede Pass 1'in kapsamadığı yedi yapısal boşluk tespit etti:

1. Sandbox boundary operasyonel borç olarak sınıflandırılmış; oysa
   analizörün **ana güvenlik yüzeyi** burası. → W4 (Sandbox Boundary) bu
   yüzden promote edildi.
2. Anti-evasion düşüncesi yok. → ADR 0002'de scope dışı ilan edildi; `inconclusive`
   verdict'i bu eksiği açıkça karşılıyor (ADR 0003 §5).
3. Fixture corpus benign-only. → ADR 0004 T1/T2/T3 tier'ları bu boşluğu
   spec seviyesinde kapatır; W5 implementasyonu bekliyor.
4. Threat model yazılı değildi. → ADR 0002 yazıldı.
5. Detection taxonomy yoktu. → ADR 0003 yazıldı.
6. Platform supply chain attestation eksik (VS Code unpinned, harness
   checksum yok). → W2 + W4 bu maddeleri karşılıyor.
7. Output secondary-exfiltration yüzeyi sessizdi. → ADR 0002 §6 ve ADR 0004
   §7'de açıkça tanımlandı.

### 9.4 Bir sonraki pass için protokol

Bir sonraki Claude veya GPT pass'i, doğrulama sırasında şunları yapsın:

1. Bu bölümün altına `### 9.N (tarih, ajan)` başlığıyla yeni bir blok ekle.
2. Değişen maddeleri `⚠ STALE` ile işaretle; bulguyu silme.
3. Yeni bir bulgu varsa Bölüm 2 veya Bölüm 7 formatında ekle, numarayı
   sıralı devam ettir (örn. 7.1.6, 7.2.8).
4. Öncelik sırası değişirse Bölüm 8'i güncelle ama stale maddeleri listeden

### 9.5 Güncel Durum Doğrulaması (2026-04-20, GPT-5.4)

- Pre-W6 cleanup tamamlandı: tracked `apps/` ve `legacy_ui/` kaldırıldı,
  `workflows.marketplace.analysis_service` içindeki legacy trigger-plan tuple
  shim'i silindi ve `executor/flows/playwright/monitor.py` facade haline
  getirildi.
- 9.2 içindeki `apps/api`, `apps/ui` bulgusu artık **⚠ STALE (2026-04-20)**;
  bu placeholder tree repo yüzeyinden kaldırıldı.
- 9.2 içindeki `monitor.py` "hiç bölünmemiş" bulgusu artık
  **⚠ STALE (2026-04-20)**; facade korunurken lifecycle/source/runtime/
  attribution split'i landed.
- W6 kapsamı yapısal temizlik değil; açık kalan maddeler automation
  reliability + capture hardening backlog'unda kalıyor.
   tamamen silme — üstlerine çizgi çek (`~~...~~`).

---

## 10. 7 Haftalık Stabilizasyon → Güvenlik Penceresi (PoC-öncelikli)

**Bağlam (2026-04-17):** Kullanıcının 7 haftası kaldı. Hedef: otomasyon
akışını stabilize etmek, ardından güvenlik (dynamic-analysis detection)
adımlarına geçmek. Bu bölüm Pass 1'in Week 4C/4D/5 önerilerini bu pencereye
sığacak şekilde sıralar; Pass 1 önerileri **iptal değil**, tarihsel olarak
sıralanmıştır.

**PoC framing (2026-04-17):** bu 7 haftanın **acceptance bar'ı PoC
seviyesi**. "Temel zararlıları yakalayabilen demonstrable bir araç"
hedefiyle ölçülür; full production security product hedefiyle değil.
Kapsam **daraltılmadı**: tüm maddeler planda kalıyor. Ama **öncelik**
PoC'dir — iki madde çatışırsa PoC bar'ını karşılayan kazanır.

PoC öncelik sıralaması:

- **Must (PoC acceptance bar):** W1-W4 stabilizasyon, ADR 0002 PoC
  sınıfları (A1/A2/A4/A6), her sınıf için en az bir T1 canary, en az
  bir production rule per PoC class, minimum UI detection rendering.
- **Should (PoC'yi güçlendirir, bar'ı bloklamaz):** Stretch sınıfları
  (A3/A5/A7), ikinci benign fixture'lar, executor'ın minimum-invaziv
  split'i yerine tam split, `analysis_service` dekompozisyonu.
- **Nice-to-have (PoC sonrası):** T2 declawed samples, T3 handling,
  axe-core accessibility, mypy strict promotion, dokümantasyon
  konsolidasyonu, domain service pattern genişletmesi.

PoC acceptance değerlendirmesi W7 sonunda yapılır; Must maddelerinin
hepsi yeşil ise PoC "kabul" kabul edilir, kalan Should/Nice-to-have
maddeleri post-PoC backlog'una taşınır.

**Kullanıcı kararı (2026-04-17):** Otomasyon stabilizasyonu öncelikli;
güvenlik sıkılaştırmaları şimdiye kadar geride kalmış durumda. Bu karar W0
(güvenlik ön-yatırımı) haftasını getirdi — güvenlik fazı başlamadan **spec
seviyesinde** üç ADR yazıldı:

- [ADR 0002 — Threat Model](adrs/0002-threat-model.md): in-scope adversary
  sınıfları (A1-A7), kabul edilen yetenekler, scope dışı, trust boundaries.
- [ADR 0003 — Detection Taxonomy](adrs/0003-detection-taxonomy.md):
  MITRE ATT&CK hizalaması, severity/confidence, `DetectionReport` contract'ı,
  verdict rollup, kural lifecycle.
- [ADR 0004 — Malicious Fixture Policy](adrs/0004-malicious-fixture-policy.md):
  T1/T2/T3 izolasyon tier'ları, `LABEL.yaml` manifest, `make test-security`
  ve `make test-security-live` ayrımı, CI guardrail'leri.

Bu üç ADR W5-W7 detection çalışmasının **contract'ıdır**; kod uygulaması
W5'te başlar.

### 10.1 Ana prensip — güvenliğe geçiş ön koşulu

Güvenlik fazına girmeden önce **sandbox kenarı sessiz olmamalı**. Pass 1'in
en büyük kör noktası: plan dokümanı executor'a hiç dokunmuyor, ama kod
tabanının en kırılgan halkası orası (bkz. 7.2 ve 7.5 #1). Güvenlik
bulguları "extension'dan mı executor'dan mı?" belirsizliğiyle gelirse faz
gürültülü olur. Bu yüzden W2-W4 executor'a ayrılmalıdır.

**İkinci ön koşul (Pass 2 ekledi):** güvenlik fazı "ne yakalıyoruz?"
sorusunun yazılı cevabı olmadan başlayamaz. ADR 0002/0003/0004 bu cevabı
spec seviyesinde veriyor; W0'da yazıldı, W5 implementasyonun zeminidir.

### 10.2 Haftalık dağılım (öneri)

| Hafta | Etiket | Kapsam | Kaynak maddeler |
|---|---|---|---|
| **W0** | Security foundations (spec) ✅ | Üç ADR yazımı: threat model, detection taxonomy, malicious fixture policy | ADR 0002, 0003, 0004 (2026-04-17'de tamamlandı) |
| **W1** | Week 4C (Pass 1 önerisi) | Legacy cleanup, import-graph testi, 2. fixture, plan/status ayrımı, test piramidi | 2.1, 2.2, 2.3, 2.5, 2.7, 7.4.1, 7.4.3 |
| **W2** | Week 4D-a (Executor determinism) | VS Code pinleme, `time.monotonic`, report path collision, Docker exec retry/backoff | 7.2.2, 7.2.3, 7.2.4, 7.2.5 |
| **W3** | Week 4D-b (Executor modularization) | `monitor.py` capture/ alt paketine bölünmesi; `analysis_service.execute_analysis_request` parçalanması | 7.2.1, 7.1.1 |
| **W4** | Week 4E (Sandbox boundary) | `ExecutorControl` arayüzü + ADR, harness checksum, trigger-file host-side cleanup | 2.4, 7.2.6, 7.2.7 |
| **W5** | Security foundations (implemented) | ADR 0002/0003/0004 **kod karşılıkları** landed: `DetectionReport` contract'ı, initial rule engine, A1/A2/A4/A6 production PoC rules, T1 canary'leri, `make test-security`, `/api/activations/{name}/bundle`, minimum analyst UI rendering | ADR 0002, 0003, 0004 |
| **W6** | Automation reliability + capture hardening | **PoC must:** activation confirmation gate, extension-aware workspace/materializer completeness, deferred-activation coverage (idle observation window), HTTP body capture / child-process tracking, CI security lane egress hardening, scenario-dropout honesty (skipped scenarios surface in `failed_scenarios` with reason code; `automation_health` demoted), correlative-signal FP floor (min evidence count + tight time window; benign baselines must not raise `correlative_suspicious_activity`). **Stretch:** ek rule'lar, stretch sınıf rule'ları | ADR 0002, ADR 0003 |
| **W7** | Acceptance + hardening buffer | **PoC must:** demo senaryosu, PoC acceptance checklist doğrulaması, kalan hardening maddelerinin kapanışı. **Stretch/post-PoC:** axe-core, mypy strict, doc konsolidasyon, `test-security-live`, T3 handling | 7.3.6, 7.4.4, 7.4.5, ADR 0004 T3 handling |

2026-04-20 doğrulaması: pre-W6 cleanup landed. W6 bu tablodaki kapsamla
başlar; structural cleanup maddeleri ayrı bir giriş kriteri değildir.

### 10.3 Ertelenenler (7 hafta içine girmeyen)

Bu maddeler iyi fikir ama güvenliğe geçiş için kritik değil; W7 sonrasına
bırakılmaları önerilir:

- **7.1.2** `SessionLocal` import taşıma — küçük iyileştirme, test kolaylığı.
- **7.1.4** Geniş `except` daraltma — cosmetic, AGENTS.md ruhuyla uyumlu
  ama production'ı bloklamıyor.
- **7.1.5** `search_marketplace` return type — IDE deneyimi, güvenlik değil.
- **7.3.1 / 7.3.2** UI component bölünmesi — UI drift ölçülmeden büyük
  iş; güvenlik detection UI'ı ayrı maddeyi hak ediyor.
- **7.3.3 / 7.3.4** `window.__EXTRACE_CONFIG__`, `AbortController` — UI
  polish.
- **7.3.5** ESLint feature boundary — faydalı ama 7.3.1 öncesinde
  prematüre.
- **2.8** Domain service pattern yayılımı — Week 5 adayıydı, halen öyle.
- **7.4.6 / 7.4.7** `make migrate` pre-check, Alembic reversibility testi
  — operasyonel konfor; güvenliği bloklamıyor.

### 10.4 Paralel ajan lane'leri (7 hafta için)

Kullanıcı Claude + GPT paralel çalıştırdığı için lane çakışmasını önlemek
gerekir. Önerilen lane haritası:

| Lane | Sorumlu ajan tipi | Tipik çıktı |
|---|---|---|
| **Backend refactor** (`workflows/`, `appcore/`) | GPT-5.4 (uygulama) | Kod değişikliği + test |
| **Executor modularization** (`executor/`) | GPT-5.4 (uygulama), Claude (review) | W2-W4 ana iş |
| **Plan/ADR/status dokümanları** (`documents/`) | Claude (yazı), GPT (okuyucu) | ADR'lar, status blokları |
| **Mimari review + pass'ler** | Claude Opus 4.x paralel Explore | Bu dokümana Bölüm 9.N ekleyişleri |
| **Güvenlik plan + threat model** | Claude (tasarım), GPT (test fixture üretimi) | W5+ çıktısı |

**Çakışma kuralları:**

- Aynı dosyayı **aynı gün** birden fazla ajan değiştirmemeli. Lane
  sahibi olmayan ajan dokunacaksa lane sahibine PR/branch üzerinden
  iletmeli.
- Doküman yazımı Claude'a, kod yazımı GPT'ye ait; Claude'un Edit yetkisi
  kullanıldığında yalnızca `documents/` altına yazılmalı.
- Import-graph testi (2.2) W1'de kurulduğunda her iki ajan için CI
  seviyesinde korkuluk olur; lane ihlalleri otomatik kırılır.

### 10.5 W1 girişi için hazırlık checklist

GPT-5.4 W1'e başlamadan önce Claude'un (veya kullanıcının) şunları
onaylaması gerekir:

- [x] `apps/` klasörünün kaderi karara bağlandı: repo yüzeyinden silindi
      (pre-W6 cleanup, 2026-04-20).
- [ ] `documents/adrs/0005-packages-charter.md` taslağı yazıldı
      (charter ADR'ı; numara 0005 ayrıldı).
- [ ] `import-linter` veya `grimp` bağımlılık eklemesi için ADR onayı var
      (AGENTS.md "no new dependency without approval" kuralı).
- [ ] İkinci/üçüncü fixture seçimi yapıldı (color-theme + chat-only) —
      bunlar ADR 0004 kapsamı **dışında** benign fixture olarak
      `extensions/` altında kalır.
- [ ] `REFACTOR_STATUS.md` iskeleti hazır; Week 4A/4B status blokları
      taşınacak pattern'e uygun.

### 10.6 W5 girişi için hazırlık checklist

W4 bittikten sonra güvenlik implementasyonuna geçmeden önce.
2026-04-20 itibariyle doğrulanmış durum:

- [ ] ADR 0002/0003/0004 operatör tarafından son bir kere gözden geçirildi
      (W0'dan bu yana executor çalışmalarından ötürü trust boundaries
      kayma durumunda — özellikle W4 `ExecutorControl` arayüzünün güven
      modelini etkilediği kontrol edilmeli).
- [x] `extensions/malicious/` klasörü oluşturuldu, `README.md` uyarı
      metni yazıldı.
- [x] **PoC must:** A1/A2/A4/A6 (PoC sınıfları) her biri için en az bir
      T1 synthetic canary yazıldı.
- [ ] **Stretch:** A3/A5/A7 için T1 canary (zaman kalırsa).
- [x] `make test-security` hedefi Makefile'a eklendi; CI'da dedicated
      `security-fixtures` job'u olarak çalışıyor.
- [ ] `security-fixtures` job'u için explicit network egress hardening
      uygulanmış.
- [x] `tests/security/test_fixture_hygiene.py` ve
      `tests/security/test_rule_coverage.py` kuruldu (ADR 0004 §4, §6).
- [x] **Harness-extension checksum verification** (7.2.6, W4'ten devralındı
      2026-04-20): `executor/flows/harness_extension/*.js` için sha256
      attestation; executor bundle'ı yüklemeden önce doğrulama adımı
      eklendi. Bu madde W4 stabilizasyon kapsamından supply-chain güvenlik
      kapsamına taşınmıştı; Week 5 implementasyonunda kapatıldı.

### 10.7 PoC acceptance checklist (W7 sonu)

W7 sonunda aşağıdakilerin hepsi yeşil ise PoC kabul sayılır. Kalan
Should/Nice-to-have maddeleri post-PoC backlog'una yazılır, W7 kapanışını
bloklamaz.

**Stabilizasyon tarafı:**

- [ ] Legacy klasörler silinmiş (`routers/`, `scanner/`, `core/`,
      `database/`, `crud/`, `models/`, `schemas/`).
- [ ] `packages/` import-graph testi CI'da çalışıyor.
- [ ] VS Code versiyonu Dockerfile'da pinli; harness extension checksum
      doğrulamalı.
- [ ] `monitor.py` minimum olarak capture/ alt paketine ayrılmış (tam split
      zorunlu değil; capture concerns ayrıştırılmış olması yeter).
- [ ] `ExecutorControl` sarmalayıcı mevcut; API süreci `docker`
      modülünü doğrudan import etmiyor.

**Detection tarafı:**

- [ ] A1/A2/A4/A6 her biri için en az bir T1 canary fires its rule
      with `confidence ≥ medium` and severity ≥ `high`.
- [ ] Hiçbir benign fixture (extensions/, malicious/ dışı) bir
      production rule'u tetiklemiyor; `correlative_suspicious_activity`
      benign baseline'da (ms-python, chat, theme) ateşlenmemeli
      (2026-04-21 itibariyle ateşleniyor — W6'da `signal_policy` eşik
      sıkılaştırması gerekli).
- [ ] Scenario-dropout honesty: `requested_scenarios` ↔ `scenarios_run`
      farkı her zaman `failed_scenarios` veya `skipped_scenarios`
      üzerinden raporlanıyor; sessiz drop yok.
- [ ] `make test-security` CI'da yeşil.
- [ ] Verdict rollup `inconclusive` vakalarını doğru işaretliyor
      (verification gap açıkken `clean` dönmüyor).
- [ ] UI'da `DetectionReport` görüntüleniyor; en az bir finding'in
      evidence deep-link'i aktivasyon raporuna geçiyor.
- [ ] Demo senaryosu yazılmış: PoC sınıflarından en az birinin
      canary'sini analiz et, UI'da finding'i göster, verdict'i kanıtla.

Bu checklist yeşilken W1 tek oturumda kapanabilir; eksiklerinden biri
sarkarsa W1 haftasına taşma riski yaratır ve güvenlik faz başlangıcını
geriye iter.
