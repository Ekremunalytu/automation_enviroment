# Refactor Optimization — Plan Kritiği ve Düzeltme Önerileri

`Last Updated: 2026-04-25`

> **2026-04-25 update note (operational):** The §1-§11 body of this
> document was frozen on `2026-04-24` — the §11 W8-W13 external-review
> integration window was authored on that date and the §11.1 entry
> gate still waits on PR345 PRs 3-5 + the PR5 ADR. This refreshed
> stamp only flags that the post-W7 simulation-progress-cancel branch
> landed on `2026-04-25` (weighted simulation progress, full-stack
> analysis cancel flow, VNC harness ready-marker fix,
> `t1-demo-runnable-canary` + rule + `make demo-canary` lanes) and
> sits **outside** the §11 window's scope. The canonical sources for
> that work are the [`REFACTOR_STATUS.md`](REFACTOR_STATUS.md)
> "Simulation Progress + Cancel + VNC Harness Fix (2026-04-25)" block
> and the `[FOLLOWUP simulation-progress-cancel]` tags in
> [`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md). §10 and §11 scope are
> **unchanged**; this update note is timestamp hygiene only.

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

### 9.6 Güncel Durum Doğrulaması (2026-04-23, GPT-5.4 + Claude Opus 4.7)

W6 korelasyon + capture hardening commit'lerinden sonra post-W6 review üç
detection-engine correctness gap'i ve bir CI-görünürlük gap'i tespit etti.
Bu pass'te dördü de kapatıldı; W6 kapanışa alındı.

- **A1/A2/A4 attribution gating.** Kurallar `ActivationReport`'un
  `is_target_extension_event` + `attribution_status` alanlarını yok
  sayıyordu; `target_file_events()` ve
  `target_unknown_outbound_network_events()` helper'ları
  (`packages/analysis_engine/rules/_common.py`) target-only evidence'a
  kilitliyor. ADR 0002 §4 trust boundary ve ADR 0003 §4 finding
  attribution ile hizalı.
- **TLS vocabulary (`tls_client_hello`).** Live tshark çıktısı
  `tls_client_hello` emit ediyor; production kuralları yalnızca legacy
  `tls_sni` kabul ediyordu → live veride A1/A2/A4 dead idi. Shared
  `TLS_EVENT_TYPES` constant'ı ve `is_tls_event()` helper'ı her iki
  spelling'i kapsıyor.
- **Runner error dominance.** Handled rule exception'ları sessizce
  yutuluyor, her kural error etse bile `Verdict.CLEAN` dönebiliyordu.
  `packages/analysis_engine/runner.py` artık `RuleExecutionStatus.ERROR`
  görürse automation-health input'unu `rule_execution_errors`
  blocker'ıyla `inconclusive`'e düşürüyor (ADR 0003 §5 error dominance).
- **Security fixtures CI'a ulaşıyor.** `extensions/` klasörü tümüyle
  gitignored olduğundan T1 canary'leri ve chat/theme benign
  baseline'ları `security-fixtures` job'una hiç inmiyordu — lane yeşildi
  çünkü toplayacak test bulamıyordu. `.gitignore` artık `extensions/*`
  pattern'iyle narrow; fixture path'leri exception list'te.
- **Executor test isolation + layered run_quality label.** `monitor`
  package-import testi `sys.modules`'u restore etmiyordu; layered
  medium `run_quality` boş reason list dönüyordu. İkisi de bu pass'te
  kapatıldı; `official_unresolved_present` artık UI'ya reason olarak
  taşınıyor.

Bu pass Bölüm 10.2 tablosundaki W6 kapsamını **değiştirmiyor**; W6
satırındaki "PoC must" maddelerinin teslim edildiğini doğruluyor.
`REFACTOR_STATUS.md` "W6 Correctness Follow-up (2026-04-23)" bloğu
commit referanslarını ve test listesini tutuyor.

### 9.7 Güncel Durum Doğrulaması (2026-04-24, Claude Opus 4.7)

W7 kapanışının (2026-04-23) ve iki ardışık post-W7 hardening bloğunun
(sim-all crash cascade + scan-between install failure) teslim edildiği
günlük. Bu pass yeni bir §10 faz satırı açmıyor — W0-W7 penceresi
§10.7 kabul testi (11/11) ile kapandı; buradaki maddeler §10.2'nin
dışına düşen operasyonel dayanıklılık fix'leri ve
`POST_POC_BACKLOG.md` `[NEXT]` pull'larıdır.

- **W7 Phase 3a — A3 typosquat rule + canary (landed 2026-04-23).**
  Stretch adversary class A3 için `extrace.a3.typosquat`
  (`packages/analysis_engine/rules/a3_typosquat.py`), canary
  (`extensions/malicious/t1-a3-typosquat-canary/`), ve
  `popular_extensions.txt` allow-list'i landed. A5 ve A7 kalan stretch
  sınıfları olarak `POST_POC_BACKLOG.md`'e taşındı.
- **Fatal UI-crash classification + fail-fast (landed 2026-04-24).**
  `_run_scenario_sequence` (`executor/flows/playwright/automation.py`)
  `PlaywrightError` / `RuntimeError` / `ValueError`'ları
  `is_fatal_ui_error` (substring markers + `page.is_closed()` +
  `context.is_closed()` + ≤1.5 s liveness probe) ile sınıflandırıyor;
  renderer ölümü loop'u kırıyor, `ScenarioTrace.failure_reason_code =
  "fatal_ui_crash"` + `error_detail` set ediliyor;
  `health_summary.py` `fatal_ui_crash`'i dominant reason olarak tanıyor
  ve `automation_health.status`'u ADR 0003 §5 error dominance gereği
  `inconclusive`'e düşürüyor. Opt-in `--retry-on-crash` bayrağı
  `vscode.reload_workbench_window` üzerinden loop'a devam ediyor.
  Contract mirror (`packages/analysis_contracts/contracts.py`) ve UI
  `contracts.ts` regen edildi.
- **Scan-between VS Code restart (landed 2026-04-24).** İkinci
  tarama'nın `code --install-extension <eslint>.vsix`'inin rc=1 ile
  düşmesinin kök nedeni bulundu (bir önceki scan'in bıraktığı stale
  Chromium SingletonLock + IPC socket — ESLint'in
  `onStartupFinished` + `extensionKind: workspace` +
  `untrustedWorkspaces.supported: false` kombinasyonu race'i
  kötüleştiriyor). `reset_executor_state`
  (`executor/flows/playwright/reset_state.py`) artık
  workspace setup → `terminate_vscode` (SIGTERM + 5 s grace +
  SIGKILL fallback) → `extensions/`+`logs/` temizliği →
  `cleanup_singleton_locks` → `launch_vscode` sırasıyla orkestre
  ediyor; `launch_vscode.sh` (`executor/container/launch_vscode.sh`)
  shared script'i hem boot hem reset yolunda aynı CDP komutunu
  çağırıyor (`setsid` ile lifetime decoupling). Defense-in-depth:
  `executor/host.py::install_extension_in_executor` transient IPC
  marker'larında bir kere `reload_vscode_window` retry'ı yapıyor;
  `workflows/marketplace/analysis_execution.py::install_failure_message`
  son 500 char stderr tail'ını footer olarak eklediği için
  "Command failed (rc=1)" blind spot'u kapandı.
- **`attribution/` subpackage split (landed 2026-04-24).**
  `executor/flows/playwright/monitor_attribution.py` (1122 LoC) üç
  dosyaya ayrıldı:
  - `attribution/events.py` — event annotation + classification +
    shared actor/artifact/epoch helpers
  - `attribution/links.py` — evidence-bundle + scenario/temporal/
    noise/duplicate-file link builders
  - `attribution/__init__.py` — flat re-export facade, 29-name
    underscore-prefixed API'yi verbatim koruyor; signal-layer shim'leri
    (`_indexed_target_*`, `_build_risk_signals`, `_build_risk_summary`,
    `_build_signal_summary`) ve dual-import pattern (paket vs top-level
    executor mode) aynı kaldı.
  Üç caller (`monitor.py`, `monitor_types.py`, `monitor_lifecycle.py`)
  yalnızca module path flip'i (`monitor_attribution` → `attribution`)
  ile geçti. Pre-existing ruff UP042 warning
  `packages/analysis_contracts/detection/enums.py:12`
  `# noqa: UP042 - intentional <3.11 fallback` ile susturuldu.
  Doğrulama: `make check-all` → 627 passed / 5 skipped;
  `make test-security` → 41 passed; `scripts/demo_acceptance.py` →
  `DEMO GREEN`. **Docker-based A1 canary structural diff
  (`make exec-up && make exec-run` against
  `t1-a1-credential-read-to-network-canary`) user-side** — deferral
  note'unda flag edilen capture-pipeline regresyon riskini
  yalnızca live executor smoke kapatabilir;
  `POST_POC_BACKLOG.md` "Next (post-PoC value-adds)" altında.
- **`sim-target` Makefile lane (landed 2026-04-24).** Yeni
  [`Makefile`](../Makefile) target: `make sim-target
  TARGET=publisher.name [TRIGGERS=/path/to/payload.json]
  [SCENARIO=<name>]` `entrypoint.py --monitor
  --target-extension-id $(TARGET)` ile target-extension smoke'u
  çalıştırıyor; `TARGET` gerekli, missing ise non-zero + usage hint.
  `sim-all` artık `make help` + echo banner'da
  "UI-stimulus stress: scenarios w/o target ext." olarak
  etiketli — operator'ler artık `sim-all` inconclusive raporunu
  "normal extension path failed" sanmıyor.

Bu pass §10.2 haftalık kapsamını **değiştirmiyor** (W7 zaten kapandı);
post-W7 hardening + Phase 3a buffer + pull-first POST_POC entries'in
landed olduğunu doğruluyor. `REFACTOR_STATUS.md` "W7 Acceptance +
Buffer (2026-04-23)" ve "Post-W7 Hardening (2026-04-24)" bloklarıyla
`POST_POC_BACKLOG.md` "Next iteration (pull first)" altındaki
`[LANDED 2026-04-24]` işaretleri commit referanslarını ve test
listesini tutuyor.

### 9.8 External Review Integration Pass (2026-04-24, Claude Opus 4.7)

Aynı gün (2026-04-24) iki bağımsız external review dokümanı teslim
edildi ve plana entegre edildi:

- [`documents/claude_code_review.md`](claude_code_review.md) — Claude
  Opus 4.7, 18 bölüm, line-number referanslı bulgular. Daha keskin
  güvenlik + framework boundary findings.
- [`documents/codex_project_review.md`](codex_project_review.md) — Codex
  GPT-5.4, 18 bölüm, daha abstract framing. Contract hygiene + executor
  observability findings.

**Doğrulanan kritik bulgular (kod tabanında spot-check):**

- **VSIX extraction zip-bomb risk.** `packages/analysis_engine/static/vsix.py`
  `zipfile.extractall()` kullanıyor; `MAX_UNCOMPRESSED_SIZE` sabiti yok,
  ZipSlip koruması yok. (W8-1)
- **Marketplace identity path-traversal.**
  [`workflows/marketplace/client.py:94-103`](../workflows/marketplace/client.py)
  `get_vsix_path` / `_artifact_name` / `_extension_dir` raw
  publisher/name/version'ı filesystem path'e gömüyor. (W8-2)
- **URI trigger shell injection.**
  [`executor/flows/playwright/entrypoint_triggers.py:142`](../executor/flows/playwright/entrypoint_triggers.py)
  ve
  [`executor/flows/playwright/stimulus_attempts.py:136`](../executor/flows/playwright/stimulus_attempts.py)
  `xdg-open '{uri}'` string interpolation; argv form değil. (W8-3)
- **Framework boundary violation.**
  [`executor/flows/playwright/signal_policy.py:33`](../executor/flows/playwright/signal_policy.py)
  `sys.path.insert(0, _PROJECT_ROOT)`; 485 LoC detection signal policy
  executor altında ama framework-agnostic davranıyor. (W9-2)
- **Dual-import fallback.** 17 dosyada `try: from packages.X / except
  ImportError: from X`; container packaging disiplini muğlak. (W9-3)
- **Monitor lifecycle bloat.**
  [`executor/flows/playwright/monitor_lifecycle.py`](../executor/flows/playwright/monitor_lifecycle.py)
  834 LoC; runtime + report assembly + scenario accounting birleşmiş.
  (W11)
- **Planner registry bloat.**
  [`packages/analysis_planner/registry.py`](../packages/analysis_planner/registry.py)
  669 LoC; capabilities + scenarios + event index + pass order. (W10-3)
- **Executor flat layout.** `executor/flows/playwright/` 54 flat dosya;
  domain subpackage bölümlemesi yok. (W12-1)
- **`ActivationReport` Any-typed fields.** `automation_health` ve
  `coverage_*` field'ları `dict[str, Any]`; typed model gerekli. (W10-4, W10-5)
- **`_TriggerPayloadDraft` redundancy.** `packages/analysis_planner/__init__.py`
  `TriggerPayload` ile neredeyse aynı tipi tutuyor. (W10-2)
- **Content-sample secret disclosure.** `ContentSample.value`
  (W8-6'da yeni eklenecek `packages/analysis_contracts/evidence.py`
  modülüne; şu an `packages/analysis_contracts/contracts.py` içindeki
  `EvidenceEvent.context` / rule-match payload'ları raw text embed
  ediyor) raw text'i geçiriyor; redaction filter'ı yok. (W8-6)

**Promote edilmeyen (rejected) review maddeleri §11.12'de
gerekçelenmiştir** — §0 binding rules gereği silinmezler; POST_POC
backlog altında kalırlar.

**Entegrasyon kararı:** Review bulguları §10 penceresine
(W0-W7) **eklenmez**; yeni bir §11 **W8-W13** penceresine dağıtılır.
Gerekçe: W0-W7 PoC acceptance altında yazıldı ve §10.7'de kapandı;
review'lar post-PoC hardening turudur. W8 girişi PR345 (target
activation lifecycle) tamamlandıktan sonra açılır (§11.1 entry gate).
Review dokümanları repo'da archive olarak kalır — silinmez, gelecek
review'larda baseline olarak kullanılır.

Bu pass §10.2 W0-W7 tablosunu değiştirmedi (W7 kapalı); §11 altında
yeni W8-W13 satırları eklendi; §10.2'ye §11'e pointer cross-reference
düşüldü.

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

**Post-W7 external review window (2026-04-24+):** W0-W7 penceresi
§10.7 kabul testi (11/11 green, 2026-04-23) ile **kapandı**. İki
bağımsız external review (`claude_code_review.md`,
`codex_project_review.md`, 2026-04-24) sonrası altı haftalık post-PoC
hardening + modülerleştirme turu **§11 W8-W13** altında planlanmıştır.
§10.2'deki W0-W7 satırları değişmez; W8-W13 penceresi PR345 (target
activation lifecycle) tamamlandıktan sonra açılır — bkz. §11.1 entry
gate.

| Hafta | Etiket | Kapsam | Kaynak |
|---|---|---|---|
| **W8** | Güvenlik sıkılaştırma | VSIX zip-bomb guard, marketplace identity helper, URI trigger shell-safe, absolute binary paths, activation-report regex, content-sample secret redaction, local network binding discipline (ADR 0007) | §11.5 · Claude §1/§18 · Codex §1 · supplementary review 2026-04-25 |
| **W9** | Executor↔Detection boundary | ADR 0006 (container packaging), dual-import fallback kill, `signal_policy.py` relocation, `sys.path.insert` audit | §11.6 · Claude §6/§10 · Codex §9/§4 |
| **W10** | Contract hygiene + Planner split | `schema_version` + DeprecationWarning, `_TriggerPayloadDraft` elimination, `registry.py` 4-way split, `automation_health`/`coverage_*` typing | §11.7 · Codex §1.2/§1.4/§2 · Claude §4 |
| **W11** | Monitor lifecycle split | `monitor_lifecycle.py` 834→≤200 LoC facade; `MonitorRuntime` + `ReportAssembler` + `ScenarioAccountant`; `activation_discovery_strategies` field | §11.8 · Codex §3.1 · Claude §3 |
| **W12** | Executor subpackaging + attribution cleanup | `playwright/` 54→≤10 flat + 5 subpackage; attribution facade underscore cleanup; `raw_context` typed discriminated union | §11.9 · Codex §3.2/§4 · Claude §2/§5 |
| **W13** | Test expansion + observability | Benign silence 3→5; stale singleton-lock + `.env` gitignore regression; `extrace.executor.*` logger konsolidasyonu; run-ID stamping; W8-W12 lock-in | §11.10 · Claude §9/§12 · Codex §10/§12 |

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
      (W6 `signal_policy` eşik sıkılaştırması 2026-04-21'de landed; W7
      acceptance sırasında baseline regresyon doğrulaması yapılacak).
- [ ] Scenario-dropout honesty: `requested_scenarios` ↔ `scenarios_run`
      farkı her zaman `failed_scenarios` veya `skipped_scenarios`
      üzerinden raporlanıyor; sessiz drop yok.
- [ ] `make test-security` CI'da yeşil.
- [ ] Verdict rollup `inconclusive` vakalarını doğru işaretliyor
      (verification gap açıkken `clean` dönmüyor).
- [ ] UI'da `DetectionReport` görüntüleniyor; en az bir finding'in
      evidence deep-link'i aktivasyon raporuna geçiyor.
      (`detection_report_invariant_issues` post-W6'da landed; her finding
      evidence event_id'sinin paired ActivationReport'ta çözüldüğünü test
      lane'i doğruluyor.)
- [ ] Demo senaryosu yazılmış: PoC sınıflarından en az birinin
      canary'sini analiz et, UI'da finding'i göster, verdict'i kanıtla.

Bu checklist yeşilken W1 tek oturumda kapanabilir; eksiklerinden biri
sarkarsa W1 haftasına taşma riski yaratır ve güvenlik faz başlangıcını
geriye iter.

---

## 11. W8–W13 External Review Integration Window (2026-04-24+)

**Bağlam (2026-04-24):** PoC penceresi (W0-W7) §10.7 kabul testi (11/11
green, 2026-04-23) ile kapandı; post-W7 hardening iki bloğu
(sim-all crash cascade + scan-between install failure) ve pull-first
POST_POC entries (`attribution/` split + `sim-target` lane + sim-all
report-semantics 6 fix) 2026-04-24 tarihinde landed. Aynı gün **iki
bağımsız external review** dokümanı teslim edildi:

- [`documents/claude_code_review.md`](claude_code_review.md) — Claude
  Opus 4.7, 18 bölüm, line-number referanslı (§1-18).
- [`documents/codex_project_review.md`](codex_project_review.md) — Codex
  GPT-5.4, 18 bölüm, daha abstract framing (§1-18).

Bu bölüm iki review'ı **§10 penceresini değiştirmeden** altı haftalık
bir post-PoC window'a (W8-W13) entegre eder. §10.2 haftalık dağılımı
**korunur** — W0-W7 kapalı kalır; yeni W8-W13 satırları §11.2'de
ayrıca listelenir (§10.2 tablosunda atıf cross-reference bırakılır).

### 11.0 Neden §11, §10'a ek satır değil

- §10 (W0-W7) PoC acceptance bar'ı altında yazıldı; kapanış kriteri
  §10.7'de sabitlendi. Aynı tabloya W8-W13 eklemek "PoC acceptance
  bar'ı kaymış" sinyali verir.
- İki review PoC sonrası gelen findings; bunlar **stabilizasyon**
  değil, **post-PoC hardening + modülerleştirme** turudur. Kapsamı
  ayrı tutmak audit trail için önemli.
- Kullanıcı in-flight iş olarak **PR345** (target activation lifecycle)
  üzerinde çalışıyor (2026-04-24; PRs 1-2 landed, PRs 3-5 + PR5 ADR
  pending). W8 girişi bu PR345 tamamlanmadan **açılmaz**.

### 11.1 Entry gate (W8 başlama koşulu)

W8 aşağıdakilerin hepsi yeşil olmadan açılmaz:

- [ ] PR345 tüm PR'ları (1-5) landed; özellikle PR5 için
      `documents/adrs/00NN-target-output-channel-capture.md` ADR'ı
      merged (`POST_POC_BACKLOG.md` "Next iteration" → "Target
      activation lifecycle" item (5) requires short ADR).
- [ ] `make check-all` green on `main`
- [ ] `make test-security` → 41 passing
- [ ] `scripts/demo_acceptance.py` → `DEMO GREEN`
- [ ] `REFACTOR_STATUS.md` altında "PR345 complete" kapanış bloğu

Bu gate yeşil değilken W8 bekleme modunda; external review maddeleri
`POST_POC_BACKLOG.md`'de "scheduled for W8-W13" annotation'ı ile
tutulur.

### 11.2 Haftalık dağılım (W8-W13)

| Hafta | Etiket | Kapsam | Kaynak review bölümleri |
|---|---|---|---|
| **W8** | Güvenlik sıkılaştırma | VSIX zip-bomb guard, marketplace identity helper, URI trigger shell-safe invocation, absolute binary paths, activation-report router path-traversal, content-sample secret redaction, local network binding discipline (loopback default + `EXTRACE_ALLOW_LAN` opt-in + CORS allow-list + CDP behind `debug` profile, ADR 0007) | Claude §1/§18; Codex §1; supplementary review 2026-04-25 (network exposure) |
| **W9** | Executor↔Detection boundary | ADR 0006 (container packaging), dual-import fallback sweep, `signal_policy.py` relocation, `sys.path.insert` audit, container import-mode CI test | Claude §6/§10; Codex §9/§4 |
| **W10** | Contract hygiene + Planner split | `schema_version` + DeprecationWarning, `_TriggerPayloadDraft` elimination, `registry.py` 4-way split, `automation_health`/`coverage_*` typing | Codex §1.2/§1.4/§2; Claude §4 |
| **W11** | Monitor lifecycle split | `monitor_lifecycle.py` 834 LoC → `MonitorRuntime` + `ReportAssembler` + `ScenarioAccountant` + `ExtensionMonitor` facade; `activation_discovery_strategies` report field; per-strategy `_stop_*` helpers | Codex §3.1; Claude §3 |
| **W12** | Executor subpackaging + attribution cleanup | `executor/flows/playwright/` 54 → {monitor,stimulus,workspace,health,entrypoint}/; `entrypoint_runner.main` 487 LoC → ≤200 LoC dispatch extraction; attribution facade underscore cleanup; `raw_context` per-event-type typing | Codex §3.1/§3.2/§4; Claude §2/§3/§5 |
| **W13** | Test expansion + observability | Benign silence 3→5 fixture, stale singleton-lock + `.env` gitignore regression tests, `extrace.executor.*` logger konsolidasyonu, run-ID stamping, W8-W12 regression lock-in | Claude §9/§12; Codex §10/§12 |

### 11.3 Haftalar arası bağımlılıklar

```text
W8 ─┐
    ├─ independent (entry gate outside both)
W9 ─┘
      │
      ▼
     W10 (depends on W9 — dual-import kill + ADR 0006 fixes import topology;
           W10 typed contracts nerede oturacağını bilmek için W9'a bağlı)
      │
      ▼
     W11 (depends on W10 — schema_version + typed coverage/health must
           land before monitor split rewrites the report assembler)
      │
      ▼
     W12 (depends on W11 — subpackaging güvenli bir şekilde yapılabilmesi
           için monitor_lifecycle önce split edilmeli)
      │
      ▼
     W13 (depends on W8-W12 — regression lock-in her hafta için yeni test'ler)
```

Kritik yollar:

- **W8 paralelde yürür** — W9 ile file çakışması yok (W8 `packages/`, `workflows/`, `executor/flows/playwright/entrypoint_triggers.py + stimulus_attempts.py`; W9 `executor/flows/playwright/signal_policy.py` + 17 dosyada import fallback + 5 `sys.path.insert` hit).
- **W10 sıralı** — W9'un ADR 0006 kararı (paket mode vs top-level) typed contract'ların import path'ini belirliyor.
- **W11 sıralı** — W10 contract updates (schema_version, AutomationHealth, CoverageSummary) monitor split'inin report assembler imzasında oturmalı; tersi merge conflict hell yaratır.
- **W12 sıralı** — W11 lifecycle split sonrası 54 flat dosyanın 5 subpackage'a bölünmesi deterministik; önce yapılırsa lifecycle split yeni subpackage path'leriyle yeniden kavga eder.
- **W13 en sonda** — her hafta regression test bırakır, W13 merkezi lock-in turu.

### 11.4 Non-goals (W8-W13 kapsamında OLMAYAN)

Bu maddeler `POST_POC_BACKLOG.md`'de kalır; W13 sonunda yeniden
değerlendirilir:

- `POST_POC_BACKLOG.md` § "UI" (7.3.1, 7.3.2, 7.3.3, 7.3.4, 7.3.5,
  axe-core) — UI surface stabilize değil
- Adversary class **A5 + A7** T1/T2 canary + rule (stretch kalır)
- `test-security-live` T2/T3 lane operasyonel kurulumu (T2 engagement'ı
  yoksa plumbing'i yazmak nedensiz)
- `T3 handling` (live malware repo lane)
- Documentation consolidation (`REFACTOR_STATUS.md` /
  `REFACTOR_EXECUTION_PLAN.md` / `REFACTOR_OPTIMIZATION.md` dedupe) —
  W7 < 4 hafta uzak, living-doc cadence oturmadı
- mypy strict promotion
- Monorepo tooling migration (uv / poetry)
- OpenAPI frontend client generation
- Allow-list (`benign_domains.txt`, `popular_extensions.txt`) versioned
  data artifact'a terfi
- Domain service pattern genişletmesi (2.8 — W7'de ertelendi; kalır)

### 11.5 W8 — Güvenlik Sıkılaştırma

**Goal:** İki review'in kesiştiği **altı güvenlik kritik bulgusu**
kapatılır. Stakeholder demo'su için en azından bu tur gerekli —
current state'te scanner'ın kendisi zip-bomb / path-traversal /
command-injection vektörleri içeriyor.

**Scope:**

1. **VSIX zip-bomb + entry-traversal guard.**
   [`workflows/marketplace/client.py:144`](../workflows/marketplace/client.py)
   `_extract_vsix_to_dir()` her üye için path-traversal kontrolü
   (`..` reject + `resolve().relative_to(destination_dir)`) yapıyor
   ama compression ratio / maksimum uncompressed size / dosya sayısı
   limiti yok. Malicious VSIX `zipfile.ZipFile(io.BytesIO(...))`
   üzerinden diske doyurabilir (zip-bomb) ya da extraction sırasında
   OOM yaratabilir.
   - **Change:** Module-level sabitler
     `MAX_UNCOMPRESSED_SIZE = 256 * 1024 * 1024`,
     `MAX_COMPRESSION_RATIO = 100`, `MAX_FILE_COUNT = 2_000`;
     `_extract_vsix_to_dir` içinde iteration sırasında
     `cumulative_uncompressed` ve `cumulative_compressed` takip
     edilir, ratio ve toplam size aşımında yeni
     `VSIXUnpackError`'a düşer; path-traversal guard korunur.
   - **Test:** `tests/workflows/marketplace/test_vsix_hardening.py`
     — 4 case: normal vsix passes, oversize rejects,
     high-compression-ratio rejects, file-count rejects.
   - **Refs:** `workflows/marketplace/client.py:144-170`
     (`_extract_vsix_to_dir` flow); new exception in same module
     or shared util; new test.
   - **Claude:** §1 "Security findings"; **Codex:** §1
     "Supply-chain hardening".

2. **Safe marketplace identity helper.**
   [`workflows/marketplace/client.py:94-103`](../workflows/marketplace/client.py)
   `get_vsix_path` / `_artifact_name` / `_extension_dir` raw
   publisher/name/version string'lerini filesystem path'e gömüyor;
   adversarial publisher `../../etc` path-injection vector'ü.
   - **Change:** Yeni `workflows/marketplace/identity.py` modülü;
     `safe_marketplace_slug(publisher, name, version) -> str`
     helper'ı regex `^[A-Za-z0-9][-_.A-Za-z0-9]{0,64}$` enforcement
     uygular ve `publisher.name-version` canonical format üretir;
     üç call site helper'a taşınır; architecture test
     `raw concat ≠ helper` ihlali bloke eder.
   - **Test:** `tests/workflows/marketplace/test_identity.py` — happy
     path + 5 adversarial input (path traversal, absolute path, null
     byte, unicode confusable, overlength).
   - **Refs:** `workflows/marketplace/client.py:94-103`; new
     `workflows/marketplace/identity.py`; new test; architecture
     test extension.
   - **Claude:** §1 "Path-traversal in identity concat"; **Codex:**
     §1 "Marketplace identity".

3. **URI trigger shell-safe invocation.**
   [`executor/flows/playwright/entrypoint_triggers.py:142`](../executor/flows/playwright/entrypoint_triggers.py)
   ve
   [`executor/flows/playwright/stimulus_attempts.py:136`](../executor/flows/playwright/stimulus_attempts.py)
   `xdg-open '{uri}'` şeklinde terminal stimulus üzerinden string
   interpolation yapıyor; trigger payload'ı adversarial olursa
   `'; rm -rf /;'` → terminal command injection vektörü.
   - **Execution context:** İki dosya executor container içinde
     (`docker exec python3 /home/executor/flows/playwright/entrypoint.py`
     ile invoke edilir) çalışır; argv-form `subprocess.run` da container
     içinde execute olur — host shell'ine kaçış yoktur, blast radius
     sandbox'la sınırlıdır. Değişikliğin amacı container içi
     `rm -rf /home/executor` tipi yıkıcı payload'ı kesmek.
   - **Change:** Terminal stimulus yerine
     `subprocess.run(["xdg-open", uri], check=False, timeout=5)`
     argv form; URI validation
     `urllib.parse.urlparse(uri).scheme in {"vscode", "vscode-insiders", "http", "https"}`;
     direct shell string uygulaması iki dosyadan kaldırılır.
   - **Test:** `tests/executor/security/test_uri_trigger_injection.py`
     — `;` / `$(...)` / backtick / pipe içeren payload reddedilir.
   - **Refs:** iki stimulus dosyası + new test.
   - **Claude:** §18 "Shell injection in triggers"; **Codex:** §1.

4. **Absolute binary paths (executor shell invocations).** PATH
   hijacking koruması. W7-landed
   [`executor/container/launch_vscode.sh`](../executor/container/launch_vscode.sh)
   zaten explicit path disiplini takip ediyor; aynı disiplin
   `entrypoint_triggers.py`, `stimulus_attempts.py`,
   [`executor/host.py::install_extension_in_executor`](../executor/host.py)
   içinde uygulanır.
   - **Change:** `code` → `/usr/bin/code`, `xdg-open` →
     `/usr/bin/xdg-open` gibi absolute path'ler; fallback resolver
     `shutil.which` test başlangıcında tek seferlik.
   - **Test:** `tests/executor/test_absolute_paths.py` — subprocess
     invocation PATH'siz env ile smoke.
   - **Refs:** iki stimulus dosyası + `executor/host.py`.
   - **Claude:** §18; **Codex:** —.

5. **Activation-report router regex konsolidasyonu
   (defense-in-depth).**
   [`workflows/activation_reports/router.py`](../workflows/activation_reports/router.py)
   bundle endpoint'i mevcut durumda `..`, `/`, `\\` karakter
   rejection'ı yapıyor (Claude review §3 step 12 "clean" olarak
   işaretlemiş; concrete exploit path yok). Bu madde bir gap
   kapatmıyor; W8-2'nin `safe_marketplace_slug` helper'ı ile tek
   regex disiplinine konsolidasyon — iki farklı validation path'i
   (router-level ad-hoc + marketplace identity) tek source-of-truth
   altında birleşir, drift riski kapanır.
   - **Change:** FastAPI
     `Path(..., regex=r"^[A-Za-z0-9][-_.A-Za-z0-9]{0,64}$")` tight
     constraint; validator helper
     `appcore/contracts/validators.py::valid_extension_slug` merkezi
     hale getirilir (yeni W8-2 `safe_marketplace_slug` ile aynı
     regex disiplini paylaşır).
   - **Test:**
     `tests/workflows/activation_reports/test_router_path_traversal.py`
     — 6 adversarial path case.
   - **Refs:** `workflows/activation_reports/router.py`; new
     `appcore/contracts/validators.py` (or consolidation); new test.
   - **Claude:** §1; **Codex:** —.

6. **Content-sample secret redaction.** `ContentSample` evidence
   artifact'ları rule match'lerinde `.value` olarak embedded
   ediliyor; regex hit'inden bazı satırlar (`.env` satırları gibi)
   raw text olarak rapor'a yazılabilir → rapor diske yazıldığında
   secret disclosure.
   - **Change:** W8'de yeni `packages/analysis_contracts/evidence.py`
     modülü oluşturulur (bugün `ContentSample` adında ayrı bir sınıf
     yok; `contracts.py` içindeki `EvidenceEvent` + rule-match
     payload'ları raw string taşıyor). Yeni `ContentSample.value`
     setter'ı redaction filter'ından geçirilir;
     `AWS_SECRET_ACCESS_KEY=...`, `bearer <token>`,
     `Authorization: Bearer`, private-key header pattern'leri
     `[REDACTED:<class>]` ile değiştirilir; redaction policy
     **ADR 0003 §6** ek maddesi olarak yazılır.
   - **Test:** `tests/platform/security/test_content_sample_redaction.py`
     — 5 secret class (aws, bearer, private-key, generic api-key, db-url).
   - **Refs:** new `packages/analysis_contracts/evidence.py`;
     migration hook'larıyla `EvidenceEvent.context` raw string
     tüketicileri W8 sonuna kadar yeni API'ya geçer; ADR 0003
     update; new test.
   - **Claude:** §1; **Codex:** §1.

7. **Local network binding discipline (ADR 0007).** Today
   `.env.example` ships `API_HOST=0.0.0.0`, `API_CORS_ALLOW_ORIGINS=*`,
   and `docker-compose.yml` maps the API, UI, executor noVNC + CDP
   ports, and PostgreSQL on every host interface
   (`docker-compose.yml:11-12,27-28,66-68,101-102,119-120` —
   none of the host port mappings carry a `127.0.0.1:` prefix). The
   single-operator trust model from ADR 0001 §1 / ADR 0002 §5 is left
   as a comment in `.env.example:82-84` ("INTERNAL USE ONLY ... ensure
   it runs in a trusted network") with no enforcement. A LAN-adjacent
   attacker today reaches CDP `9222` unauthenticated and can drive the
   live VS Code instance.
   - **Change:** Per ADR 0007, every host-facing port defaults to
     `127.0.0.1`; compose `ports:` entries gain explicit
     `127.0.0.1:` prefixes; `appcore/api/config.py::APISettings.HOST`
     defaults to `127.0.0.1` and `CORS_ALLOW_ORIGINS` defaults to
     `["http://localhost:3000"]`; LAN exposure is opt-in through a
     single `EXTRACE_ALLOW_LAN=1` env var that the entrypoints inspect;
     the executor CDP port mapping moves behind a Compose `debug`
     profile so it is absent from `docker compose up` by default.
     `.env.example` security notice rewritten to describe the
     loopback default + opt-in path.
   - **Test:** new `tests/architecture/test_default_bindings.py` —
     loads `appcore/api/config.py` settings with empty env, asserts
     `settings.api.HOST == "127.0.0.1"` and
     `settings.api.CORS_ALLOW_ORIGINS != ["*"]`; parses
     `docker-compose.yml` and asserts every default-profile `ports:`
     entry begins with `127.0.0.1:` (or is gated behind a non-default
     profile). Companion runbook
     `documents/runbooks/lan-exposure.md` carries the operator-side
     hardening checklist (firewall rules, reverse-proxy auth, CORS
     allow-list, rotated PostgreSQL password) that must precede the
     `EXTRACE_ALLOW_LAN=1` flip.
   - **Refs:** new
     [`documents/adrs/0007-local-network-binding.md`](adrs/0007-local-network-binding.md);
     `.env.example`; `docker-compose.yml`; `appcore/api/config.py`;
     `Makefile` (dev targets); root `README.md` "Service Endpoints"
     section; new test + new runbook.
   - **Supplementary review:** 2026-04-25 (Codex review surfaced the
     ingress side of the trust boundary; original Claude/Codex W8
     review covered scanner-side parsing/injection only).

**Non-Goals:** container egress allowlist (W13 observability ayağına
bağlı — egress logları run-ID ile stamp'lenmeden allowlist audit'i
anlamlı değil); harness extension sandbox (W4 ExecutorControl bar'ı
kapattı); T2/T3 fixture lane (POST_POC_BACKLOG); rotated production
PostgreSQL credentials (operator responsibility per ADR 0007 §5; the
ADR rewrites the `.env.example` notice but does not auto-rotate).

**Entry:** §11.1 entry gate green.

**Exit:**

- [ ] 7 yeni security test lane green
- [ ] `make test-security` 41 → ≥48 passing
- [ ] ADR 0003 §6 redaction ek maddesi merged
- [ ] ADR 0006 (container packaging; W9 opener) **draft** başlamış
      (merged olması gerekmiyor — W9 girişinde merged olur)
- [ ] ADR 0007 (local network binding) merged; `.env.example` +
      `docker-compose.yml` + `appcore/api/config.py` defaultları
      `127.0.0.1` / allow-list CORS; `EXTRACE_ALLOW_LAN=1` opt-in
      yolu doğrulanmış; `documents/runbooks/lan-exposure.md` live
- [ ] `workflows/marketplace/identity.py` + helper live; raw concat
      architecture test bloke ediyor
- [ ] `tests/architecture/test_default_bindings.py` green
      (varsayılan settings `0.0.0.0` üretmiyor; compose `ports:`
      entries `127.0.0.1:` prefix'li veya `debug` profile altında)

### 11.6 W9 — Executor↔Detection Boundary

**Goal:** Paket import topolojisinde `except ImportError` dual-fallback
ve `sys.path.insert` manipülasyonları kaldırılır; container packaging
tek mode'a indirilir. Framework boundary review finding'i (Claude §6)
kapanır.

**Scope:**

1. **ADR 0006 — Container packaging.** Yeni ADR: "Executor paket olarak
   mı, yoksa top-level script olarak mı çalışır?" sorusuna tek cevap.
   Mevcut durum: 17 dosya dual-import fallback + executor runtime'ında
   5 `sys.path.insert(0, ...)` hit (`signal_policy.py:33`,
   `reload_vscode.py:19`, `triggers.py:27`, `report_builder.py:17`,
   `entrypoint.py:18`) her iki mode'u destekliyor.
   - **Decision:** Paket mode (`python -m executor.flows.playwright.entrypoint`
     container içinde); top-level mode destek bitirilir.
   - **Refs:** `documents/adrs/0006-container-packaging.md` (new);
     W8 girişinde draft başlamış olmalı, W9'un 1. PR'ında merged.

2. **`signal_policy.py` relocation.**
   [`executor/flows/playwright/signal_policy.py`](../executor/flows/playwright/signal_policy.py)
   485 LoC; satır 33'te `sys.path.insert(0, _PROJECT_ROOT)` yapıyor.
   İçerik **detection signal policy** (threshold'lar, correlative
   evaluation rules); `packages/analysis_engine/` altında olmalı —
   `executor/` içinde olması framework-agnostic disiplinini kırıyor.
   - **Change:** Module'ü `packages/analysis_engine/signals/policy.py`
     altına taşı; caller'lar (`monitor.py`, `monitor_lifecycle.py`,
     `health_summary.py`) import path'ini günceller; `sys.path.insert`
     kaldırılır.
   - **Test:**
     [`tests/architecture/test_import_graph.py`](../tests/architecture/test_import_graph.py)
     `executor/*` → `packages/analysis_engine/signals/*` izinli ama
     ters yön yasak.
   - **Refs:** `executor/flows/playwright/signal_policy.py:33`; 3
     caller; new `packages/analysis_engine/signals/policy.py`;
     architecture test extension.
   - **Claude:** §6 "Framework boundary violation"; **Codex:** §4
     "Signal policy location".

3. **Dual-import fallback sweep.** 17 dosyada `try: from packages.X /
   except ImportError: from X` pattern'i. Paket mode seçildiği için
   yalnızca `packages.X` import kalır.
   - **Change:** Her dosyada fallback branch kaldır.
   - **Test:**
     `tests/architecture/test_import_graph.py::test_no_dual_import_fallback_in_executor`
     — ripgrep `except ImportError` hit count'u executor ağacında 0.
   - **Refs:** 17 dosya (post-W7 `rg -l "except ImportError" executor/`
     çıktısı): `monitor_lifecycle.py`, `monitor_types.py`,
     `monitor_sources.py`, `monitor_support.py`, `monitor_runtime.py`,
     `monitor_payload.py`, `monitor.py`, `signal_policy.py`,
     `signals.py`, `health.py`, `health_summary.py`,
     `health_reconciliation.py`, `capture.py`, `commands.py`,
     `attribution/__init__.py`, `attribution/events.py`,
     `attribution/links.py`. W9 girişinde final grep ile
     doğrulanır (rakam değişirse exit criteria güncellenir).

4. **`sys.path.insert` audit + removal.** Executor runtime'ında **5
   bilinen hit**: `signal_policy.py:33`, `reload_vscode.py:19`,
   `triggers.py:27`, `report_builder.py:17`, `entrypoint.py:18`. Her
   biri container path disiplini olmadığı için workaround olarak
   kullanılıyor — paket mode (ADR 0006) sonrası hepsi gereksiz.
   Scripts (`scripts/seed_test.py:55`, `scripts/demo_acceptance.py:24`,
   `scripts/generate_ui_contracts.py:16`), test-harness
   (`tests/executor/*` içinde 12+ hit), ve `alembic/env.py:10`
   bu scope'un dışında — test/migration boot-strap zorunluluğu.
   - **Change:** 5 runtime hit için ya relocation (yukarıdaki (2) gibi
     `signal_policy.py` için) ya da delete (paket mode sonrası gerek
     yok); `executor/`, `packages/`, `workflows/`, `appcore/` ağacında
     sıfır hit hedefi.
   - **Test:**
     `tests/architecture/test_import_graph.py::test_no_sys_path_manipulation_outside_scripts`
     — AST-based check, string literal değil;
     `scripts/`, `tests/`, `alembic/` allow-list.
   - **Verification:** W9 açılışında
     `rg -nE "sys\.path\.(insert|append)" ./executor ./packages ./workflows ./appcore`
     → hit count 0.

5. **Container import-mode CI test.** `tests/ci/test_container_entrypoint.py`
   (new, Docker layer'da): `docker exec executor python -c "import
   executor.flows.playwright.entrypoint"` başarılı; `python
   entrypoint.py` (top-level mode) non-zero dönmeli (explicit reddediş).
   - **Refs:** new test + `make exec-up` pre-hook opsiyonel.

**Non-Goals:** detection rule engine değişikliği; `packages/analysis_engine/`
iç subpackage re-org (W10/W12 kapsamında); harness-extension import
topolojisi (zaten ayrı).

**Entry:** W8 green + ADR 0006 **draft** seviyesinde (merged şartı
W9 1. PR'ı).

**Exit:**

- [ ] ADR 0006 merged
- [ ] 17 dosya → `except ImportError` count 0 executor'da
- [ ] `sys.path.insert` hit count 0 `scripts/` dışında
- [ ] `signal_policy.py` → `packages/analysis_engine/signals/policy.py`;
      import-graph test yeşil
- [ ] Container import-mode CI test green

### 11.7 W10 — Contract Hygiene + Planner Cleanup

**Goal:** `ActivationReport` schema evolution için backward-compat
disiplinli yol kurulur; gereksiz private type'lar temizlenir;
`analysis_planner/registry.py` 669 LoC → SOLID 4 file + facade.

**Scope:**

1. **`ActivationReport.schema_version` + DeprecationWarning.**
   Post-W7 `build_verdict` → `build_signal_summary` rename'i reaktif
   bir legacy validator (2026-04-24) gerektirdi; proaktif yol:
   `schema_version` field'ı her report'ta. Minor bump'ta warning,
   major bump'ta reddediş.
   - **Change:**
     [`packages/analysis_contracts/contracts.py::ActivationReport`](../packages/analysis_contracts/contracts.py)
     `schema_version: str = "1.0"` field'ı; `model_validator(mode="before")`
     legacy ingestion'ında `warnings.warn(DeprecationWarning, ...)`
     emit eder; `strict_schema=True` ingest flag'i reddeder.
   - **Test:** `tests/platform/contracts/test_schema_version.py` —
     legacy ingestion DeprecationWarning fırlatır; `strict_schema=True`
     altında reddeder; current version round-trip temiz.
   - **Refs:** `packages/analysis_contracts/contracts.py`; new test.
   - **Codex:** §1.2 "Report schema"; **Claude:** §4 "Contract
     evolution".

2. **`_TriggerPayloadDraft` elimination.** Codex §2 finding:
   [`packages/analysis_planner/__init__.py`](../packages/analysis_planner/__init__.py)
   `_TriggerPayloadDraft` dataclass'ı `TriggerPayload` ile neredeyse
   aynı alan setine sahip; iki tipi tutmak yazım hatalarını masking
   ediyor.
   - **Change:** `_TriggerPayloadDraft` sil; caller'lar direkt
     `TriggerPayload.model_construct(...)` veya
     `TriggerPayload.model_validate(dict)` kullansın.
   - **Test:** `tests/platform/contracts/test_trigger_payload.py`
     eski alias import'u reddedilir; aynı yerde round-trip regression.
   - **Refs:** `packages/analysis_planner/__init__.py`; caller'lar;
     test.
   - **Codex:** §2 "Planner types"; **Claude:** —.

3. **`registry.py` split.**
   [`packages/analysis_planner/registry.py`](../packages/analysis_planner/registry.py)
   669 LoC'da dört concern birleşmiş: capabilities, scenarios,
   event→scenario index, pass order. SOLID çatı:
   - `capabilities.py` — capability declaration + validation
   - `scenarios.py` — scenario registry + lookup
   - `event_scenario_index.py` — reverse-lookup (event →
     scenarios that consume it)
   - `pass_order.py` — topological pass ordering
   - `__init__.py` — backward-compat re-export facade (29-name'lik
     public surface)
   - **Test:** Mevcut planner test'leri pas geçer; yeni
     `tests/packages/analysis_planner/test_registry_split_regression.py`
     4 file'ın bağımsız import'unu ve combined facade'ın identical
     behavior'unu doğrular.
   - **Refs:** `packages/analysis_planner/registry.py` → 4 file + facade.

4. **`automation_health` typing.** Codex §1.4 finding:
   `automation_health: dict[str, Any]` `ActivationReport`'ta raw
   dict; typed Pydantic model'e taşınır.
   - **Change:** `packages/analysis_contracts/automation.py::AutomationHealth`
     Pydantic modeli (status literal `"ok" | "degraded" | "inconclusive"`,
     `reasons: list[str]`, `metrics: dict[str, int]`);
     `ActivationReport.automation_health: AutomationHealth`.
   - **Test:** `tests/platform/contracts/test_automation_health_model.py`.
   - **Refs:** `packages/analysis_contracts/contracts.py`; new
     `automation.py`.
   - **Codex:** §1.4 "Report Any dict"; **Claude:** —.

5. **`coverage_*` fields typing.** `coverage_target_reached`,
   `coverage_gap_reasons`, sibling fields raw dict/list; typed
   `CoverageSummary` model'e taşınır.
   - **Change:** `packages/analysis_contracts/coverage.py::CoverageSummary`.
   - **Test:** `tests/platform/contracts/test_coverage_model.py`.
   - **Refs:** `packages/analysis_contracts/contracts.py`; new file.
   - **Codex:** §1.4; **Claude:** —.

**Non-Goals:** ADR 0003 verdict rollup semantic değişikliği;
`DetectionReport` contract churn; rule engine imza değişikliği.

**Entry:** W9 green.

**Exit:**

- [ ] `schema_version` field + DeprecationWarning emitter live
- [ ] `_TriggerPayloadDraft` removed; caller'lar direkt
      `TriggerPayload` kullanıyor
- [ ] `registry.py` 669 LoC → 4 file + facade; 29-name public
      surface unchanged
- [ ] `automation_health` + `coverage_*` typed; `dict[str, Any]`
      residue 0
- [ ] `make check-all` green; contract migration test eklendi

### 11.8 W11 — Monitor Lifecycle Split

**Goal:**
[`executor/flows/playwright/monitor_lifecycle.py`](../executor/flows/playwright/monitor_lifecycle.py)
834 LoC'u three-responsibility-split + facade ile parçala. W10
typed contract'ları (AutomationHealth, CoverageSummary) yeni
modüllerin imzalarına oturur.

**Scope:**

1. **`MonitorRuntime` extraction.** Runtime state machine (discovery
   → streaming → stop → serialize) ayrı bir modülde
   (`executor/flows/playwright/monitor_runtime.py`, new).
   - **Refs:** new module; eski `monitor_lifecycle.py`'den runtime
     section'ı cut.

2. **`ReportAssembler` extraction.** Report builder (event aggregation
   → summary → `ActivationReport`) ayrı bir modülde
   (`executor/flows/playwright/monitor_report_assembler.py`, new).
   ADR 0003 verdict rollup burada sit eder.
   - **Refs:** new module.

3. **`ActivationReport.activation_discovery_strategies` field.** Codex
   §1.2: strategy list (`warm-start`, `command-probe`,
   `output-channel`, `log-tail`, …) bugün `_discovery_strategies`
   internal state; rapor'a taşınmaz. Scan-sonrası hangi strategy'nin
   işe yaradığını analyst görmeli.
   - **Change:**
     `packages/analysis_contracts/contracts.py::ActivationReport.activation_discovery_strategies: list[str]`;
     `ReportAssembler` doldurur; `schema_version` minor bump.
   - **Test:** `tests/platform/contracts/test_activation_discovery_strategies.py`.
   - **Refs:** `packages/analysis_contracts/contracts.py`; report
     assembler.

4. **`ScenarioAccountant` extraction.** Scenario lifecycle accounting
   (requested, run, failed, skipped, aborted) ayrı bir modülde
   (`executor/flows/playwright/monitor_scenario_accountant.py`, new).
   Post-W7 landed `aborted_after_fatal_ui_crash` accounting'i bu
   modülün içinde konsolide olur.
   - **Refs:** new module.

5. **`ExtensionMonitor` composition facade.** Eski
   `monitor_lifecycle.py` artık sadece `class ExtensionMonitor`
   facade'ı; bileşenler composition ile inject edilir (DI pattern,
   test'te mock edilebilir).
   - **Target:** `monitor_lifecycle.py` 834 LoC → ≤200 LoC (pure
     facade + thin coordination).

6. **Per-strategy helper extraction in `stop()`.**
   `ExtensionMonitor.stop()` hâlâ strategy-specific cleanup branch'leri
   içeriyor; her strategy için `_stop_<strategy>` helper'ına taşınır
   (warm-start, command-probe, output-channel, log-tail).
   - **Refs:** `monitor_runtime.py` / `monitor_lifecycle.py`.

> **Not (2026-04-24 plan review):** `entrypoint_runner.main` dispatch
> extraction (eski item 6) **W12-4'e taşındı** — W12 subpackaging
> `entrypoint/` subpackage'ı zaten oluşturduğu için dispatch split
> aynı operasyonun parçası olarak yapılması iki dosya
> dokunma turunu bire indiriyor.

**Non-Goals:** monitor event model (`EvidenceEvent` hierarchy)
değişikliği; capture pipeline (`runtime_capture/`) dokunulmaz;
scenario implementation (`scenarios/`) dokunulmaz.

**Entry:** W10 green + W10 typed contracts merged.

**Exit:**

- [ ] `monitor_lifecycle.py` 834 → ≤200 LoC (facade)
- [ ] `MonitorRuntime`, `ReportAssembler`, `ScenarioAccountant`
      modülleri canlı + import-graph temiz
- [ ] `activation_discovery_strategies` rapor'da görünüyor; UI
      `contracts.ts` regen'd
- [ ] Per-strategy `_stop_*` helpers canlı
- [ ] `make check-all` green; demo acceptance → `DEMO GREEN`

### 11.9 W12 — Executor Subpackaging + Attribution Cleanup

**Goal:** `executor/flows/playwright/` 54 dosyalı flat layout → 5
domain subpackage + shared helpers; W7-landed `attribution/` facade
underscore API'ı public/private ayrımına kavuşur; `raw_context` typed
hale getirilir.

**Scope:**

1. **Executor subpackaging.** Mevcut 54 flat dosya → 5 subpackage:
   - `monitor/` — lifecycle, runtime, report_assembler,
     scenario_accountant, types, records (W11 landed dosyaları buraya
     sinter)
   - `stimulus/` — stimulus_attempts, triggers, scenarios/
   - `workspace/` — workspace_setup, workspace_fingerprint,
     reset_state
   - `health/` — health_summary, health_reconciliation,
     health_runtime_facts
   - `entrypoint/` — entrypoint, entrypoint_runner,
     entrypoint_dispatch, entrypoint_triggers
   - `attribution/` — already subpackaged W7 post
   - **Remaining flat:** `automation.py`, shared helpers
     (≤10 dosya hedefi)
   - **Refs:** 54 dosya → 5 subpackage; import-graph test subpackage
     cross-reference kurallarını ekler (`monitor/` ve `stimulus/`
     birbirini import edemez, sadece shared helpers üzerinden).

2. **Attribution facade underscore cleanup.** W7 Phase 3b
   `attribution/__init__.py` **29 underscore-prefixed name** verbatim
   korundu (backward-compat); public vs internal ayrımı muğlak.
   W12 temizliği: gerçekten module-external kullanılan ~6-7 name
   underscore'suz expose edilir; yalnızca module-internal olanlar
   private kalır.
   - **Change:** `attribution/__init__.py::__all__` revizyon; 3
     caller (`monitor.py`, `monitor_types.py`, `monitor_lifecycle.py`
     → W11 sonrası `monitor_runtime.py` + `monitor_report_assembler.py`)
     underscore'suz import'a geçer.
   - **Refs:** `executor/flows/playwright/attribution/__init__.py`
     ve üç caller modülü.
   - **Claude:** §5 "Pseudo-private exports"; **Codex:** §4.

3. **`raw_context` per-event-type typing.** Mevcut
   `raw_context: dict[str, Any]` her event type'ta (network, file,
   process) aynı key set'iyle çalıştığı için Any fencing;
   typed variant'lara bölünür.
   - **Change:** `packages/analysis_contracts/evidence.py` (W8-6'da
     oluşturulmuş olacak; W12 burada sadece yeni tipler ekler)
     `NetworkRawContext`, `FileRawContext`, `ProcessRawContext`
     Pydantic models; `RawContext = Annotated[NetworkRawContext |
     FileRawContext | ProcessRawContext, Field(discriminator="event_class")]`.
   - **Test:** `tests/platform/contracts/test_raw_context_discriminated.py`.
   - **Refs:** `packages/analysis_contracts/evidence.py`;
     `attribution/events.py` consumer'ları.
   - **Codex:** §4; **Claude:** §5.

4. **`entrypoint_runner.main` dispatch extraction.**
   [`executor/flows/playwright/entrypoint_runner.py`](../executor/flows/playwright/entrypoint_runner.py)
   487 LoC; `main()` dispatch logic'i (CLI arg parsing → config →
   monitor invocation → page reload callback wiring → UI blocker
   probe wiring) ayrı bir `entrypoint_dispatch.py`'e taşınır. W11'den
   W12'ye taşındı (2026-04-24 plan review) — W12-1 subpackaging'in
   yarattığı `entrypoint/` subpackage içinde `entrypoint/dispatch.py`
   olarak oturur; iki dokunma turu tek operasyona birleşir.
   - **Target:** `entrypoint_runner.py` 487 LoC → ≤200 LoC; dispatch
     logic'i `entrypoint/dispatch.py` içinde.
   - **Test:** Mevcut `tests/executor/test_playwright_entrypoint.py`
     yeni import path'e geçer; `test_main_wires_ui_blocker_probe_and_page_reload_callbacks`
     (post-W7 landed) yeni dispatch modülüne taşınır.
   - **Refs:** `entrypoint_runner.py`; new `entrypoint/dispatch.py`;
     test import path güncellemesi.
   - **Claude:** §3 "`entrypoint_runner.main` god method";
     **Codex:** §3.1.

**Non-Goals:** `runtime_capture/` subpackage re-org (onun kendi
lifecycle'ı var — monitor capture pipeline'ı dokunulmaz kalır);
monitor event class hierarchy (`EvidenceEvent` tip ağacı) değişikliği.

**Entry:** W11 green.

**Exit:**

- [ ] `executor/flows/playwright/` flat dosya sayısı 54 → ≤10
- [ ] 5 subpackage + `attribution/` (W7'den) import-graph kurallarıyla
      izole
- [ ] `attribution/__init__.py::__all__` public 6-7 name;
      underscore'lular internal scoped
- [ ] `raw_context` typed discriminated union; `dict[str, Any]`
      residue 0 evidence modelinde
- [ ] `entrypoint_runner.py` 487 → ≤200 LoC; dispatch logic
      `entrypoint/dispatch.py` içinde
- [ ] Import-graph test green; `make check-all` green

### 11.10 W13 — Test Expansion + Observability

**Goal:** W8-W12 boyunca biriken yeni module + contract'ların test
piramidinde yerli yerine oturması; executor observability disiplini
(logger hiyerarşisi, run-ID stamping) merkezi hale getirilmesi.

**Scope:**

1. **Benign silence expansion.** Şu anki benign baseline 3 fixture
   (ms-python, chat, theme); W13'te 5'e çıkar (+ vscode-eslint, +
   github-copilot-chat). Her biri T1 canary **değil**; silent-run
   baseline'ı için (hiçbir rule fire etmez).
   - **Change:** `extensions/` allow-list 2 yeni benign fixture;
     `tests/security/test_benign_silence.py` 3 → 5 case; `.gitignore`
     allow-list extend.
   - **Refs:** `extensions/` + `tests/security/test_benign_silence.py`.
   - **Claude:** §9 "Test pyramid".

2. **Stale singleton-lock regression test.** W7 post landed fix
   (`cleanup_singleton_locks`) için regresyon koruması:
   deliberately-left `SingletonLock` + `reset_executor_state` →
   kesinlikle cleanup ediyor + re-install success'i doğrulanır.
   - **Refs:**
     [`tests/executor/test_reset_state.py`](../tests/executor/test_reset_state.py)
     (extend).
   - **Claude:** §12 "W7 regression coverage".

3. **`.env` gitignore regression.** Post-W7'de `.gitignore` re-narrow
   edildi (extensions/*/allow-list); bu disiplinin regresyona
   düşmediğini bir contract test'i doğrular: `.env`,
   `extensions/*/node_modules/`, `output/`, `__pycache__/` pattern'leri
   tracked olamaz.
   - **Refs:** new `tests/platform/test_gitignore_contract.py`.
   - **Claude:** §9.

4. **Logging consolidation → `extrace.executor.*` logger.** Codex §10:
   executor boyunca `logging.getLogger(__name__)` + direct
   `print(...)` karışımı; tek logger hiyerarşisi `extrace.executor.<module>`
   altında birleşir.
   - **Change:** `executor/logging_config.py` (new); her `print`
     call site'ı logger'a geçer; structured logging `logger.info("%s",
     dict(...))` pattern'i değil, `logger.info("event", extra={"run_id": ..., "module": ...})`.
   - **Refs:** executor genelinde ~20 call site; new config module.
   - **Codex:** §10 "Logger disjointedness"; **Claude:** §12
     "Observability".

5. **Run-ID stamping.** Codex §10: bir run'ın tüm log / evidence /
   report çıktıları aynı `run_id` (UUIDv7) ile stamp'lenmeli; şu an
   `analysis_run_id` sadece report'ta, log'larda yok.
   - **Change:** Logger filter `run_id`'i tüm log record'lara enjekte
     eder (context-var ile); evidence event'lerinde zaten var
     (`_event_epoch` + `run_id`); log'larda yok — W13'te eklenir.
   - **Refs:** `executor/logging_config.py` + `appcore/` entrypoint
     hook.
   - **Codex:** §10; **Claude:** §12.

6. **Path-traversal router regression (W8-5 lock-in).** W8 §11.5-(5)
   regex hardening'in regresyon test'i `make test-security`'e taşınır
   (W8'de `tests/workflows/activation_reports/` altında landed; W13'te
   security lane'ine de ayna).
   - **Refs:** `tests/security/test_router_path_traversal_regression.py`.

7. **Schema-version migration emitter test (W10-1 lock-in).** W10
   §11.7-(1) DeprecationWarning emitter'ının yan-yan regression test'i:
   `tests/security/test_schema_version_emitter.py` (emitter silenced
   bırakılırsa fail).
   - **Refs:** new test; `pytest` filterwarnings config güncellenir.

8. **Zip-bomb + identity test lock-in (W8-1 + W8-2 lock-in).** W8
   security fixtures (`test_vsix_hardening.py`, `test_identity.py`)
   `make test-security` lane'ine de ayna; count 41 → 47 (W8) → ≥52
   (W13).
   - **Refs:** `tests/security/test_vsix_hardening_lockin.py`,
     `tests/security/test_identity_lockin.py`.

**Non-Goals:** E2E UI tests; stakeholder-facing observability
dashboard (Grafana vb. — post-PoC product lane); benign silence 5+
fixture ötesine scale-out; OpenTelemetry export (POST_POC_BACKLOG).

**Entry:** W12 green.

**Exit:**

- [ ] Benign silence 3 → 5 fixture; baseline silent-run green
- [ ] Stale singleton-lock regression test green
- [ ] `.env` gitignore contract test green
- [ ] Tüm `print(...)` call site'ları `extrace.executor.*` logger'ına
      taşındı (executor ağacında `rg -n "^\s*print\(" executor/`
      hit count 0)
- [ ] Run-ID tüm log record'larda ve report çıktılarında stamp'li
- [ ] `make test-security` ≥52 passing
- [ ] `make check-all` green; `scripts/demo_acceptance.py` →
      `DEMO GREEN`

### 11.11 Kaynak cross-reference tablosu

Her madde → iki review'daki referans + line evidence:

| W# | Madde | Claude ref | Codex ref | Line evidence |
|---|---|---|---|---|
| W8-1 | VSIX zip-bomb guard | §1 | §1 | `workflows/marketplace/client.py:144` `_extract_vsix_to_dir` |
| W8-2 | Marketplace identity helper | §1 | §1 | `workflows/marketplace/client.py:94-103` |
| W8-3 | URI trigger shell-safe | §18 | §1 | `entrypoint_triggers.py:142`, `stimulus_attempts.py:136` |
| W8-4 | Absolute binary paths | §18 | — | stimulus files + `executor/host.py` |
| W8-5 | Activation-report regex | §1 | — | `workflows/activation_reports/router.py` |
| W8-6 | Content-sample redaction | §1 | §1 | new `packages/analysis_contracts/evidence.py::ContentSample` (today `contracts.py::EvidenceEvent` raw strings) |
| W8-7 | Local network binding (ADR 0007) | — | — | `.env.example:46,59,82-84`; `docker-compose.yml:11-12,27-28,66-68,101-102,119-120`; `appcore/api/config.py::APISettings`; supplementary review 2026-04-25 (network exposure) |
| W9-1 | ADR 0006 | §10 | §9 | — (new ADR) |
| W9-2 | `signal_policy.py` relocation | §6 | §4 | `executor/flows/playwright/signal_policy.py:33` |
| W9-3 | Dual-import fallback sweep | §10 | §9 | 17 dosyada `except ImportError` (post-W7 grep) |
| W9-4 | `sys.path.insert` audit | §10 | §9 | 5 runtime hits: `signal_policy.py:33`, `reload_vscode.py:19`, `triggers.py:27`, `report_builder.py:17`, `entrypoint.py:18` |
| W9-5 | Container import-mode CI | §10 | §9 | new test |
| W10-1 | `schema_version` | §4 | §1.2 | `packages/analysis_contracts/contracts.py::ActivationReport` |
| W10-2 | `_TriggerPayloadDraft` elimination | — | §2 | `packages/analysis_planner/__init__.py` |
| W10-3 | `registry.py` split | §4 | §2 | `packages/analysis_planner/registry.py` (669 LoC) |
| W10-4 | `automation_health` typing | — | §1.4 | `packages/analysis_contracts/contracts.py` |
| W10-5 | `coverage_*` typing | — | §1.4 | `packages/analysis_contracts/contracts.py` |
| W11-1 | `MonitorRuntime` extraction | §3 | §3.1 | `monitor_lifecycle.py` (834 LoC) |
| W11-2 | `ReportAssembler` extraction | §3 | §3.1 | same |
| W11-3 | `activation_discovery_strategies` | — | §1.2 | `packages/analysis_contracts/contracts.py` |
| W11-4 | `ScenarioAccountant` extraction | §3 | §3.1 | `monitor_lifecycle.py` |
| W11-5 | `ExtensionMonitor` facade | §3 | §3.1 | same |
| W11-6 | Per-strategy `_stop_*` helpers | §3 | — | `monitor_lifecycle.py::stop()` |
| W12-1 | Executor subpackaging | §2 | §3.2 | `executor/flows/playwright/` (54 files) |
| W12-2 | Attribution facade cleanup | §5 | §4 | `attribution/__init__.py` (29 underscore names) |
| W12-3 | `raw_context` typing | §5 | §4 | `packages/analysis_contracts/evidence.py` |
| W12-4 | `entrypoint_runner.main` dispatch (moved from W11) | §3 | §3.1 | `entrypoint_runner.py` (487 LoC) |
| W13-1 | Benign silence 3→5 | §9 | §10 | `extensions/` + `tests/security/` |
| W13-2 | Stale singleton-lock regression | §12 | — | `tests/executor/test_reset_state.py` |
| W13-3 | `.env` gitignore contract | §9 | — | new `tests/platform/test_gitignore_contract.py` |
| W13-4 | Logger consolidation | §12 | §10 | executor-wide |
| W13-5 | Run-ID stamping | §12 | §10 | `executor/logging_config.py` (new) |
| W13-6 | Path-traversal router regression lock | §1 | — | W8-5 mirror |
| W13-7 | Schema-version emitter test lock | §4 | §1.2 | W10-1 mirror |
| W13-8 | Zip-bomb + identity lock-in | §1 | §1 | W8-1 + W8-2 mirrors |

### 11.12 Rejected items (iki review, promote edilmedi)

§0 binding rules gereği reddedilen review maddeleri silinmez;
gerekçelenir:

- **UI component split (7.3.1 / 7.3.2, `ReportsWorkspace` /
  `DetectionPanel` decomposition).**
  > Reddedildi (Claude Opus 4.7, 2026-04-24 promotion review):
  > evidence-deep-link behavior still settling; premature split would
  > ossify incorrect component boundaries. POST_POC_BACKLOG § "UI"
  > altında kalır — W13 sonunda re-evaluate.
- **mypy strict promotion.**
  > Reddedildi (Claude Opus 4.7, 2026-04-24): strict promotion
  > requires each `ignore_errors` override (scripts, tests, alembic)
  > to be lifted first — W8-W13 bandwidth doesn't cover that surface.
  > POST_POC_BACKLOG § "Engineering quality" altında kalır.
- **axe-core accessibility lane.**
  > Reddedildi (Claude Opus 4.7, 2026-04-24): UI is not
  > stakeholder-facing yet; accessibility bar without real users is
  > premature. POST_POC_BACKLOG § "UI" altında kalır.
- **Documentation consolidation (REFACTOR_STATUS / EXECUTION /
  OPTIMIZATION dedupe).**
  > Reddedildi (Claude Opus 4.7, 2026-04-24): W7 kapanışından < 4
  > hafta geçmedi; living-doc cadence henüz oturmadı — erken merge
  > audit trail'i kaybeder. POST_POC_BACKLOG § "Engineering
  > quality" altında kalır.
- **Monorepo tooling migration (uv / poetry).**
  > Reddedildi (Codex §11, 2026-04-24 promotion review): "no new
  > dependency without approval" AGENTS.md kuralı bu öneriyi ADR'sız
  > bloke ediyor; ADR yok, bu tur tooling churn gereksiz.
- **Async executor runtime refactor (`asyncio.Event` → `threading.Event`).**
  > Reddedildi (Codex §7, 2026-04-24): executor Playwright sync;
  > async boundary yalnızca `appcore/` tarafında. Değişiklik
  > yarar/maliyet oranı düşük — deadlock vektörü açabilir.
- **Frontend OpenAPI client generation.**
  > Reddedildi (Claude §14, 2026-04-24): UI surface stabilize
  > değilken OpenAPI snapshot her PR'da churn üretir; post-PoC UI
  > stabilize olmadan değer yaratmaz.
- **Executor Bandit exclude kaldırma (`pyproject.toml` scope genişletme).**
  > Reddedildi (Claude Opus 4.7, 2026-04-24 plan review — birincil
  > öncelik Claude): Codex §7 bu maddeyi flag'liyor; ancak Codex'in
  > kendi önerisi "targeted security tests + narrow Bandit excludes,
  > blindly enable etme" şeklinde. W8-3 (URI trigger argv-form), W8-4
  > (absolute binary paths), W8-1 (zip-bomb guard) hit vektörlerinin
  > tam kapsamını zaten **targeted test** ile kesiyor — Bandit'in
  > executor genelinde açılması noise/benefit oranı düşük (subprocess
  > call'ların hepsi list-form + `# nosec` annotated). **Post-W13
  > mekanik temizlik** olarak POST_POC_BACKLOG'da kalır; W8-W13
  > bandwidth'inde dahil değil.

### 11.13 Paralel lane assignments (§10.4 + W8-W13)

| Lane | Sorumlu ajan | W8 | W9 | W10 | W11 | W12 | W13 |
|---|---|---|---|---|---|---|---|
| Backend refactor | GPT-5.4 | §11.5-(2)(5) | — | §11.7 (hepsi) | — | §11.9-(3) | §11.10-(3)(7) |
| Executor modularization | GPT-5.4 + Claude review | §11.5-(3)(4) | §11.6-(2)(3)(4)(5) | — | §11.8 (hepsi) | §11.9-(1)(2)(4) | §11.10-(2)(4)(5) |
| Plan/ADR yazımı | Claude | ADR 0003 §6 update + ADR 0006 draft | ADR 0006 merged | — | — | — | — |
| Güvenlik hardening | Claude (tasarım) + GPT (uygulama) | §11.5-(1)(6) | — | — | — | — | §11.10-(1)(6)(8) |
| Mimari review | Claude Opus 4.x Explore | W8 post-review | W9 post-review | W10 post-review | W11 post-review | W12 post-review | W13 post-review |

**Çakışma kuralları (§10.4'ten devralındı, W9 sonrası güçlendirilir):**

- Aynı dosyayı aynı gün birden fazla ajan değiştirmez (AGENTS.md
  multi-agent discipline).
- Doküman yazımı Claude'a, kod yazımı GPT'ye ait.
- Import-graph testi W9 sonrası daha sıkıdır (dual-import fallback
  yasaklı, `sys.path.insert` yasaklı, subpackage cross-reference
  sınırlı); lane ihlalleri CI'da otomatik bloke olur.
- Her hafta bitişinde Claude Opus post-review yapar; bulgular
  `REFACTOR_STATUS.md` altında haftalık blok olarak landed.

### 11.14 W13-end overall exit criteria

W13 bitiminde aşağıdakilerin hepsi yeşil ise external review
integration window **closed** sayılır;
[`REFACTOR_STATUS.md`](REFACTOR_STATUS.md) altına "External Review
Window (W8-W13) — closed YYYY-MM-DD" bloğu eklenir; iki review'ın
promote edilmeyen maddeleri [`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md)
altında "Evaluated but deferred" etiketiyle kalır.

**Güvenlik (W8):**

- [ ] VSIX zip-bomb + path-traversal guard live; security test lock-in
- [ ] `safe_marketplace_slug` helper live; raw concat architecture
      test bloke ediyor
- [ ] URI trigger argv-form invocation; shell injection vector kapalı
- [ ] Absolute binary path disiplini executor genelinde
- [ ] Activation-report router tight regex + helper konsolide
- [ ] `ContentSample` secret redaction live; ADR 0003 §6 ek merged
- [ ] ADR 0007 merged; loopback default + `EXTRACE_ALLOW_LAN` opt-in
      + CORS allow-list + CDP `debug` profile live;
      `tests/architecture/test_default_bindings.py` green;
      `documents/runbooks/lan-exposure.md` live
- [ ] `make test-security` 41 → ≥48 passing (W8 bitişinde) / ≥52 (W13)

**Framework boundary (W9):**

- [ ] ADR 0006 merged
- [ ] 17 dosya → `except ImportError` count 0 executor'da
- [ ] `sys.path.insert` hit count 0 `scripts/` dışında
- [ ] `signal_policy.py` `packages/analysis_engine/signals/` altında
- [ ] Container import-mode CI test green

**Contract hygiene + planner (W10):**

- [ ] `ActivationReport.schema_version` field + DeprecationWarning
      emitter live
- [ ] `_TriggerPayloadDraft` removed
- [ ] `registry.py` 669 LoC → 4 file + facade; 29-name public
      surface unchanged
- [ ] `automation_health`, `coverage_*` typed Pydantic models; report
      `dict[str, Any]` residue 0

**Monitor lifecycle split (W11):**

- [ ] `monitor_lifecycle.py` 834 → ≤200 LoC (facade)
- [ ] `MonitorRuntime`, `ReportAssembler`, `ScenarioAccountant` canlı
- [ ] `activation_discovery_strategies` report field live + UI
      contracts.ts regen'd
- [ ] Per-strategy `_stop_*` helpers canlı

**Executor subpackaging (W12):**

- [ ] `executor/flows/playwright/` flat dosya sayısı 54 → ≤10
- [ ] 5 subpackage + `attribution/` import-graph kurallarıyla izole
- [ ] `entrypoint_runner.py` 487 → ≤200 LoC; dispatch logic
      `entrypoint/dispatch.py` içinde (W11'den W12-4'e taşındı)
- [ ] `attribution/__init__.py::__all__` public 6-7 name;
      underscore'lular internal
- [ ] `raw_context` typed discriminated union; evidence modelinde
      `dict[str, Any]` residue 0

**Test + observability (W13):**

- [ ] Benign silence 3 → 5 fixture
- [ ] Stale singleton-lock + `.env` gitignore regression test green
- [ ] Tüm `print(...)` → `extrace.executor.*` logger (executor ağacında
      `rg -n "^\s*print\(" executor/` hit count 0)
- [ ] Run-ID tüm log record'larda ve report çıktılarında
- [ ] `make check-all` green; `make test-security` ≥52 passing;
      `scripts/demo_acceptance.py` → `DEMO GREEN`

Bu 14 madde yeşilken external review integration kapanır; POST_POC
backlog "Evaluated but deferred" label'ıyla update edilir; iki
review dokümanı (`claude_code_review.md`, `codex_project_review.md`)
archive olarak kalır — silinmez, gelecek review'larda baseline olarak
kullanılır.
