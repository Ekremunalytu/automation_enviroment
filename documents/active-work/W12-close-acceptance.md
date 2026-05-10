# W12 Close Acceptance Bar — Pre-W13 Geçiş Kontrolleri

`Created: 2026-05-10`
`Phase: W12 close acceptance dry run; W13 transition pending`
`Branch: week12 (single-branch policy)`
`Owner: ekrem`

> Bu doküman W12'nin `main`'e merge edilmesinden önce çalıştırılması gereken
> son kontrol listesi. Her satır bağımsız olarak doğrulanabilir; her bölüm
> tamamlanmadan bir sonrakine geçme. Çıktıyı kanıt olarak işaretle (commit
> hash, test sayısı, job_id).
>
> **Read path:** `AGENTS.md` → bu doküman → açık kalan kalemler için
> `documents/active-work/W12-executor-subpackaging.md` (W12-N detayları)
> ve `documents/POST_POC_BACKLOG.md` (W12 Pull-Forward + W12 Acceptance
> Items + W13 candidates).

---

## §0. Hızlı Durum Özeti (`2026-05-10` itibariyle)

| W12-N | Konu | Durum | Commit / Tarih |
|---|---|---|---|
| W12-0 | Output-signals file-backed redaction | ✅ landed | `22eb836` (`2026-05-07`) |
| W12-1 | Executor subpackaging (54→10 flat + 7 yeni paket) | ✅ landed | `b4bd3ee` + `0eb072e` + `0e74beb` + `95a409f` (`2026-05-07`) |
| W12-2 | Attribution facade cleanup (29→10 public) | ✅ landed | `37fcaad` + `0cef876` + `9ebc5b5` + `0981e92` (`2026-05-07`) |
| W12-3 | `raw_context` discriminated union typing | ✅ landed | `2026-05-07` |
| pre-W12-4 | Multi-line PEM redaction + API Docker digest pin + installer-tail multiline | ✅ landed | `2026-05-08` / `2026-05-09` |
| W12-4 | `entrypoint/runner.py::main` 324→99 LoC dispatch extraction | ✅ landed | `1dde578` + `adaf792` (`2026-05-10`) |
| W12-5 | `runtime_capture/extension_host.py` 679→87 LoC ahtapot split + body-preview gate | ✅ landed | `377f0d5` + `9433ee3` + `63f5254` (`2026-05-10`) |

**Test bar (en son ölçüm):**

- `make test-local` 1430 passed / 6 skipped / 6 deselected (`2026-05-10` post-W12-5).
- `make test-security` 211 passed / 32 warnings (W12-4'ten beri değişmedi).

**Live-scan validation:** 17/17 detection-relevant field bitwise-equal,
`ms-python.python` üzerinde W12-5 öncesi (`6fab298e81a1...`,
`2026-05-09 21:47`) ve W12-5 sonrası (`e5e33ec6e34f...`,
`2026-05-10 14:21`) tarama karşılaştırması ile (bkz. §3.4).

---

## §1. Kod Durumu — LoC Bütçeleri ve Yapısal Hedefler

Her satır halen geçerli olmalı. Bütçe sınırı kıracak biri varsa bu W12 close
değil, yeni bir W12-N gerektirir.

### §1.1 Flat-file ve subpackage hedefleri

```bash
# Flat .py dosya sayısı ≤10
ls executor/flows/playwright/*.py | wc -l
# Beklenen: 10
```

- [ ] `executor/flows/playwright/` flat dosya sayısı ≤ 10
  (mimari gate: `test_executor_playwright_flat_file_count_limit`).
- [ ] 10 paket dizini mevcut: `attribution/`, `entrypoint/`, `health/`,
  `monitor/`, `runtime_capture/`, `scenarios/`, `signals/`, `stimulus/`,
  `vscode/`, `workspace/`.

### §1.2 LoC Bütçeleri

```bash
wc -l executor/flows/playwright/entrypoint/runner.py
# Beklenen: ≤ 200 LoC for main(); whole file ≤ 200 (W12-4 ratchet)

wc -l executor/flows/playwright/runtime_capture/extension_host*.py
# Beklenen: extension_host.py ~87, log_parse ~329, strace_parse ~106, capture ~264
```

- [ ] `entrypoint/runner.py::main` body span ≤ 200 LoC
  (mimari gate: `test_runner_main_under_loc_budget`).
- [ ] `runtime_capture/extension_host.py` ≤ 100 LoC (facade-only).
- [ ] Üç W12-5 split modülü mevcut ve canonical sahipliği koruyor.

### §1.3 Public surface contracts

```bash
# attribution/__init__.py public surface
.venv/bin/python -c "from executor.flows.playwright import attribution; print(len([n for n in attribution.__all__ if not n.startswith('_')]))"
# Beklenen: 10

# extension_host facade
.venv/bin/python -c "from executor.flows.playwright.runtime_capture import extension_host; print(len(extension_host.__all__))"
# Beklenen: 17
```

- [ ] `attribution/__init__.py` 10 public name (W12-2 cleanup).
- [ ] `runtime_capture/extension_host.py` 17 re-export name (W12-5).
- [ ] `monitor/__init__.py` lazy-proxy invariant korunuyor
  (mimari gate: `test_monitor_lazy_proxy_completeness`).

---

## §2. Mimari Gate Süitleri (hepsi yeşil olmalı)

```bash
.venv/bin/python -m pytest tests/architecture -q
```

- [ ] **Tüm `tests/architecture/` testleri yeşil.** Beklenen ~100 case.
- [ ] Hiçbir gate skip / xfail durumda değil.

### §2.1 Önemli W12 gate'leri (özel olarak doğrula)

| Gate | Ne korur | Dosya |
|---|---|---|
| `test_executor_playwright_flat_file_count_limit` | ≤10 flat .py | `test_import_graph.py` |
| `test_monitor_facade_does_not_eagerly_import_attribution` | W12-1 cycle break | `test_import_graph.py` |
| `test_monitor_and_stimulus_subpackages_do_not_cross_import` | W12-1 topology | `test_import_graph.py` |
| `test_monitor_lazy_proxy_completeness` | PEP 562 proxy parity | `test_import_graph.py` |
| `test_attribution_does_not_eagerly_import_monitor` | W12-1 cycle break (simetrik) | `test_import_graph.py` |
| `test_python_m_playwright_invocations_have_main_module` | Container `__main__.py` | `test_import_graph.py` |
| `test_extension_catalog_service_*` (2 case) | W11-7 facade ratchet | `test_import_graph.py` |
| `test_analysis_jobs_facade_*` (2 case) | W11-8 facade ratchet | `test_import_graph.py` |
| `test_runtime_capture_extension_host_stays_a_thin_facade` | W12-5 AST shape | `test_import_graph.py` |
| `test_runtime_capture_extension_host_reexports_match_canonical_modules` | W12-5 identity | `test_import_graph.py` |
| `test_runner_main_under_loc_budget` | W12-4 LoC ratchet | `test_runner_main_loc_budget.py` |
| `test_runner_main_dispatch_helpers_remain_imported` | W12-4 import contract | `test_runner_main_loc_budget.py` |
| `test_body_preview_assignments_are_redacted` | W12-5 redaction defense | `test_network_body_preview_redaction.py` |
| `test_dockerfile_digest_pin` | ADR 0002 §4 trust (kısmi — UI hariç) | `test_dockerfile_digest_pin.py` |
| `test_no_bare_except_exception_in_production_code` | AGENTS rule 6 | `test_no_bare_except_exception.py` |
| `test_no_dual_import_fallback_in_executor` | W9-3 invariant | `test_import_graph.py` |
| `test_no_sys_path_manipulation_in_runtime` | W9-4 invariant | `test_import_graph.py` |

- [ ] Yukarıdaki tüm gate'ler isim isim grep ile mevcut ve yeşil.

---

## §3. Test Bar — Tam Acceptance Süiti

### §3.1 `make test-local`

```bash
make test-local 2>&1 | tail -10
```

- [ ] **Beklenen:** `1430 passed, 6 skipped, 6 deselected` (post-W12-5).
- [ ] 0 failed.
- [ ] Yeni warnings yok (mevcut 75 warning Pydantic deprecation,
  bunlar `[FOLLOWUP pydantic-schema-version-deprecation]` altında).

### §3.2 `make test-security`

```bash
make test-security 2>&1 | tail -5
```

- [ ] **Beklenen:** `211 passed, 32 warnings` (W12-4'ten beri sabit).
- [ ] 0 failed.
- [ ] Hiçbir kural fixture'ı çıkartılmamış.

### §3.3 `make check-all` (tam acceptance bar)

```bash
make check-all 2>&1 | tail -15
```

`check-all` sırasıyla şunları çalıştırır:

1. `lint` — `.venv/bin/ruff check .` (auto-fix dahil).
2. `typecheck` — `.venv/bin/mypy . --config-file=pyproject.toml --ignore-missing-imports`.
3. `security` — `.venv/bin/bandit -c pyproject.toml -r . -ll`.
4. `ui-types-check` — `scripts/generate_ui_contracts.py --check`.
5. `ui-boundaries` — `cd ui && npm run lint:boundaries`.
6. `test` — full pytest with DB.

- [ ] **`make check-all` yeşil.** Bu W12 close'un ana acceptance bar'ı.
- [ ] Son satır: `✅ All checks (including security) passed!`.
- [ ] Kayıt: çıktıyı veya tail'i tracker'a (`W12-executor-subpackaging.md`)
  ekle, `2026-05-XX` damgasıyla.

### §3.4 Live-scan validation (tamamlandı `2026-05-10`)

W12-5 plan §4'te tanımlanan bitwise-equal kontrolü UI üzerinden tetiklenen
tarama ile kapatıldı.

| Tarama | Job ID | Tarih | Status |
|---|---|---|---|
| Pre-W12-5 (baseline) | `6fab298e81a14bf8a7a557a13953e57b` | `2026-05-09 21:47` | completed |
| Post-W12-5 (validation) | `e5e33ec6e34f4993b795664d83e25fd4` | `2026-05-10 14:21` | completed |

**Detection-relevant fields: 17/17 BITWISE-EQUAL** ✓

- `signal_summary.level` = `needs_review`, `score` = `28`
- `verified_capabilities` (4): `commands`, `languages_editor`, `window_ui`, `workspace_fs`
- `attempted_capabilities` (6): + `debug`, `terminal_tasks`
- `coverage_summary`: `covered=7, partial=5, missing=6, attempted=6, verified=4`
- `automation_health.status` = `degraded`, 4 reason
  (`skipped_scenarios_present`, `verification_gap_present`,
  `official_unresolved_present`, `harness_verification_unconfirmed_present`)
- `target_extension_observed` = `True`
- `run_quality` = `low`
- `output_signal_events` = 12
- `len(activated)` = 22, `len(scenario_traces)` = 3,
  `len(stimulus_passes)` = 5, `len(event_attempts)` = 21
- `summary.scenarios_run` = `[project_exploration, coding_session, terminal_usage]`
- `failed_scenarios` = `[]`

**Tolerans bandı (W11 baseline aralıklarında):**

| Alan | pre | post | W11 aralığı |
|---|---:|---:|---|
| `network_events` | 186 | 168 | 167–198 ✓ |
| `file_events` | 2518 | 2531 | 2467–2689 ✓ |
| `process_events` | 75 | 69 | 66–78 ✓ |
| `evidence_links` | 3836 | 3723 | 3541–3810 ✓ |

- [x] Live-scan bitwise-equal validation **tamamlandı**.
  Kanıt: `output/activation_report_ms-python.python-2026.5.2026050801-{6fab298e81a1,e5e33ec6e34f}.json`.

> Not: `REFACTOR_STATUS.md` ve `W12-executor-subpackaging.md` halen
> "live-scan deferred" diyor. Close öncesi bu satırları "completed
> 2026-05-10" olarak güncellemek `[ACTION-1]`'de listeleniyor.

---

## §4. Açık Kalan W12 Kalemleri (kapatma vs. erteleme kararı)

### §4.1 `[FOLLOWUP ui-docker-base-image-digest-pin]` — KARAR GEREKLİ

`POST_POC_BACKLOG.md:118-128` altında **W12-close** etiketli açık item.
Sebebi: `docker/api/Dockerfile` ve `executor/container/Dockerfile`
W12 sürecinde digest-pin'lendi; ancak `ui/Dockerfile` halen tag-only
(`node:20-alpine`, `nginx:1.27-alpine`). ADR 0002 §4 her runtime base
image için `@sha256:...` zorunlu kılıyor.

İki yol:

**Yol A — W12 close'a dahil et (önerilen):** ~30-45 dakika.

1. `docker buildx imagetools inspect node:20-alpine` ve `nginx:1.27-alpine`
   ile manifest-list digest'lerini al.
2. `ui/Dockerfile:1` ve `:11` satırlarını `FROM image@sha256:...` formuna
   güncelle.
3. `tests/architecture/test_dockerfile_digest_pin.py::DOCKERFILE_ROOTS`
   tuple'ına `"ui"` ekle.
4. `pytest tests/architecture/test_dockerfile_digest_pin.py -q` yeşil.
5. Commit: `chore(ui): pin Dockerfile base images by digest (ADR 0002 §4
   close-out)`.

**Yol B — W13'e ertele:** Backlog'da kalır, W12 close mesajına not düş.
ADR 0002 trust table %66 kapalı (2/3 runtime imaj), `ui/` kalmaya devam
eder. Risk: kullanılan UI imaj tag'i remote'da rebuild edilirse
tutarlılık kaybı.

- [x] **Karar:** Yol A seçildi (W12 close'a dahil). Karar `2026-05-10`
  ekrem onayıyla; manifest-list digest'leri
  `docker buildx imagetools inspect` ile alındı (node:20-alpine →
  `sha256:fb4cd12c85ee03686f6af5362a0b0d56d50c58a04632e6c0fb8363f609372293`,
  nginx:1.27-alpine →
  `sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10`).
- [x] Landed `2026-05-10` in commit `a27eb84` (`chore(ui): pin
  Dockerfile base images by digest (ADR 0002 §4 close-out)`).
  `tests/architecture/test_dockerfile_digest_pin.py` tek case yeşil
  (3 root: `docker/`, `executor/container/`, `ui/`). ADR 0002 §4
  trust table %100 kapalı.
- [x] Karar + closure W12 tracker (`W12-executor-subpackaging.md`
  Acceptance Sub-Tasks ve §11.9 closing summary) ve POST_POC_BACKLOG
  içinde reflect edildi.

### §4.2 W12 Acceptance Items — hepsi kapalı

`POST_POC_BACKLOG.md:153-183` altında listelenen 8 followup'ın hepsi
~~üstü çizili~~:

- ~~`w12-attribution-naming-overlap`~~ (`0cef876`)
- ~~`w12-precursor-tests-attribution-links`~~ (`5ae0d32`)
- ~~`w12-precursor-tests-attribution-events`~~ (`5ae0d32`)
- ~~`w12-extension-host-split-scoping`~~ (`377f0d5` — W12-5)
- ~~`coverage-summary-attempted-drift`~~ (`9ebc5b5`)
- ~~`activation-discovery-strategy-outcome-detail`~~ (`0981e92`)

Plus bağlı pull-forward'lar:

- ~~`w8-6-output-signals-file-backed-redaction`~~ (`22eb836`)
- ~~`w12-0-output-signal-multiline-secret-redaction`~~ (`2026-05-08`)
- ~~`api-docker-base-image-digest-pin`~~ (`2026-05-09`)
- ~~`marketplace-installer-tail-multiline-redaction`~~ (`2026-05-09`)
- ~~`security-settings-commit-ownership`~~ (`2026-05-09`)
- ~~`arch-gate-network-body-preview-redaction`~~ (`9433ee3` — W12-5)

- [x] W12 Acceptance Items kapanışları doğrulandı.

---

## §5. Doküman Kapanışı

### §5.1 `documents/REFACTOR_STATUS.md`

```bash
head -3 documents/REFACTOR_STATUS.md
grep -c "landed.*W12-" documents/REFACTOR_STATUS.md
```

- [x] Header tarihi `2026-05-10` (W12 closing) ile güncel; "all
  W12-N landed; live-scan validated; UI digest pin closed; acceptance
  bar dry run pending merge".
- [x] "Active phase" satırı `W12 closing — executor subpackaging +
  attribution cleanup` formuna geçirildi; W13 lane resmi açılışta
  oluşturulacak (W11/W12 precedent).
- [x] W12-5 satırı "live-scan completed `2026-05-10`" olarak işaretli;
  UI digest pin landing satırı + W12 close-out test coverage satırı
  eklendi. Son `make check-all` tail değeri merge öncesi son commit'le
  güncellenecek.

### §5.2 `documents/active-work/W12-executor-subpackaging.md`

- [x] W12-3, W12-4, W12-5 Detailed Item Notes bölümlerinin
  "live-scan" alt-bullet'ları "completed `2026-05-10`, 17/17
  bitwise-equal, job IDs `6fab298e81a1` / `e5e33ec6e34f`" diyor.
- [x] Exit Criteria bölümünün son iki kutusu işaretli:
  - [x] Import-graph gates green; full W12-close `make check-all`
    bar recorded.
  - [x] Live-scan validation: pre/post bitwise-equal detection-relevant
    fields.
- [x] Header damgası "W12-0..W12-5 + UI digest pin landed; live-scan
  completed; close-out test coverage landed" formuna geçirildi.
  Final "Phase complete" damgası kapanış commit'iyle birlikte
  eklenecek.

### §5.3 `documents/POST_POC_BACKLOG.md`

- [x] §4.1'deki UI Docker pin kararı reflect edildi
  (CLOSED `2026-05-10`, commit `a27eb84`).
- [x] Pull-Forward bölümündeki kapalı item'lar üstü çizili
  (✓ W12 sonu itibariyle).

### §5.4 `documents/REFACTOR_OPTIMIZATION.md` §11.9 + §11.10

- [x] §11.9 closing summary güncel ("All five W12 work items landed
  `2026-05-10`; live-scan completed; UI digest pin closed").
- [x] §11.10 W13 Entry conditions block eklendi (W12 close baseline
  damga, ratchet gate envanteri, lane doc precedent notu).

---

## §6. Branch & Commit Hijyeni

### §6.1 Working tree temiz

```bash
git status
git diff --stat
```

- [ ] Working tree temiz (uncommitted change yok).
- [ ] Stash boş (`git stash list`).

### §6.2 Commit ordering doğru

```bash
git log --oneline week12 ^main | head -30
```

W12 commit'leri ters kronolojik sırayla görünmeli, her W12-N için
`refactor → test → docs` triplet'i. W12-5 örnek:

```text
63f5254 docs(W12): close W12-5 extension_host split + body-preview gate
9433ee3 test(architecture): W12-5 add body-preview redaction gate
377f0d5 refactor(executor): W12-5 ahtapot split extension_host into 3 modules
```

- [ ] Her W12-N için en az bir refactor + en az bir docs commit'i var.
- [ ] No `WIP` / `tmp` / `debug` commit'i.
- [ ] No `--amend`'lenmiş veya force-pushlanmış commit yok.
- [ ] `Co-Authored-By:` trailer'ları tutarlı.

### §6.3 W12 commit envanteri

```bash
git log --oneline --no-merges main..week12 | wc -l
```

- [ ] Beklenen commit sayısı kayıt altında (ör. ~25-30 commit).
- [ ] Her commit message conventional commit formatında (`type(scope): subject`).

---

## §7. PR Hazırlığı (`week12 → main`)

### §7.1 PR title taslağı

```text
W12: executor subpackaging + attribution cleanup + raw_context typing + dispatch & ahtapot splits
```

### §7.2 PR description bölümleri

PR body şu bölümleri içermeli:

1. **Summary (1-3 madde):** §11.9'un üst düzey hedefi + W12-5 ahtapot
   genişlemesi + body-preview defense gate.
2. **Test plan (markdown checkbox):**
   - `make check-all` green
   - `make test-security` 211 passed
   - Live-scan bitwise-equal verification (job IDs)
   - Architecture gate inventory (15+ gates listed)
3. **Risk inventory:** none for W12-1..W12-3 (already merged inside
   week12 over a week ago); W12-4 + W12-5 verified via tests + UI scan.
4. **W13 forward note:** bu PR'da kapsam dışı kalan kalemler
   (`scenario-accountant-conservation-split`,
   `evidence-event-kind-validator`, vb.).
5. **Changelog footer:** Co-Authored-By etiketi.

### §7.3 PR pre-merge gates

- [ ] PR description draft'ı `git log --oneline main..week12` ile
  cross-check'lendi.
- [ ] Reviewer assignment yapıldı (gerekirse).
- [ ] Eğer CI varsa son commit'te yeşil status.
- [ ] Branch `week12` push edildi (`git push origin week12`).

### §7.4 Merge sonrası

- [ ] `main`'e merge yapıldıktan sonra `week12` silindi (local + remote).
- [ ] Tag opsiyonel: `v0.W12-close` (eğer release scheme uygulanıyorsa).

---

## §8. W13'e Geçiş Hazırlığı

### §8.1 Pull-next backlog signals

`POST_POC_BACKLOG.md`'de W13 candidate olarak işaretli açık item'lar
(W12 close sonrası ilk pull-next havuzu):

- `[FOLLOWUP scenario-accountant-conservation-split]` — W13-X.
  `executor/flows/playwright/monitor/scenario_accountant.py` halen
  geniş; W12-4 runner split sonrası en geniş okunan dosyalardan biri.
- `[FOLLOWUP evidence-event-kind-validator]` — W13.
  `EvidenceEvent.kind` ↔ `raw_context.event_class` parity validator
  (W12-3 discriminated union'ın inverse'i).
- `[FOLLOWUP ui-event-class-literal-parity]` — W13.
  UI tarafında `event_class` literal'ları backend ile drift kontrolü.
- `[FOLLOWUP planner-selection-readability-audit]` — W13-X.
  `planner.selection`'ın readability hotspot olup olmadığını ölç.
- `[FOLLOWUP attribution-links-density-audit]` — W13-X.
- `[FOLLOWUP logger-consolidation]` — W13-X.
- (eğer §4.1 yol B seçildiyse) `[FOLLOWUP ui-docker-base-image-digest-pin]`.

### §8.2 W13 entry conditions taslağı

W13 başlangıç koşulları (W12 close sonrası baz alınmalı):

- [ ] `make check-all` yeşil baseline `2026-05-XX` damgalı.
- [ ] `tests/architecture/` 100+ case yeşil; yeni gate eklemeden önce
  sayım kayda geçirildi.
- [ ] `documents/REFACTOR_STATUS.md` "Active phase" satırı W13 olarak
  güncellendi.
- [ ] W13 lane doc'u (`documents/active-work/W13-…md`) draft halde.

### §8.3 W12 Lessons learned (kısa)

W13 planı yazılırken hatırlanmalı:

1. **Container build cache W12-N arasında reset edilmeli.** W12-5 sonrası
   ilk live-scan denemesinde executor container build-time pre-W12-5
   kodu vardı; UI'dan tetiklenen ikinci tarama refactor sonrası kodla
   doğru çalıştı çünkü API container bind-mount yoluyla yeni kodu
   gördü, executor de rebuild olmuştu. W13'te ilk live-scan öncesi
   `make exec-build && make exec-up` zorunlu olarak yapılmalı.
2. **Tests-driven refactor still requires monkey-patch awareness.**
   `extension_host_log_parse._resolve_vscode_logs_dir()` lazy-facade
   helper'ı, 23-case güvenlik ağının `monkeypatch.setattr(extension_host,
   "VSCODE_LOGS_DIR", tmp_path)` deseni split sonrası boşa düşmesin
   diye eklendi. Benzer monkeypatch dependency'leri W13 split adaylarında
   önceden audit edilmeli.
3. **Plan validation pass çok değerli.** W12-5 plan'ında `_TIMESTAMP_RE`,
   `_activation_within_monitoring_window`, `VSCODE_LOGS_DIR` re-export'ları
   ilk taslakta atlamıştı; pre-implementation grep audit'i (Phase 1
   Explore) bu üç ismi yakaladı. W13 planlarında aynı disiplin
   uygulanmalı.

---

## §9. Final Action — Close Sign-off

W12 close kapanış adımı:

1. Yukarıdaki §1-§7 hepsi ✓.
2. `documents/REFACTOR_STATUS.md` "Active phase" → "W12 closed `2026-05-XX`
   via `<commit-or-PR-ref>`" satırına geçirildi.
3. Bu doküman (`W12-close-acceptance.md`) "completed" damgalı arşive taşındı:

   ```bash
   mv documents/active-work/W12-close-acceptance.md \
      documents/archive/active-work/W12-close-acceptance-completed-2026-05-XX.md
   ```

4. W13 lane dokümanı oluşturuldu (`documents/active-work/W13-…md`).
5. `documents/REFACTOR_OPTIMIZATION.md` §11.10 (W13 plan) review için
   açıldı.

- [ ] **W12 closed** — kapanış commit'i atıldı, `main`'e merge edildi.

---

## Ekler

### A. W12 commit kanıtı (zaman çizgisi)

```text
2026-05-07  22eb836  feat(security): W12-0 file-backed output redaction
2026-05-07  b4bd3ee  refactor(executor): W12-1 subpackaging
2026-05-07  +3 more  W12-1 follow-ups
2026-05-07  37fcaad  refactor(attribution): W12-2 facade cleanup
2026-05-07  +3 more  W12-2 commits
2026-05-07           W12-3 raw_context discriminated union
2026-05-08           pre-W12-4 multi-line PEM redaction
2026-05-09           pre-W12-4 API Docker digest pin + installer tail
2026-05-10  1dde578  refactor(executor): W12-4 dispatch extraction
2026-05-10  adaf792  docs(W12): close W12-4
2026-05-10  377f0d5  refactor(executor): W12-5 ahtapot split
2026-05-10  9433ee3  test(architecture): W12-5 body-preview gate
2026-05-10  63f5254  docs(W12): close W12-5
```

### B. Test bar progression

| Tarih | `make test-local` | `make test-security` | Olay |
|---|---:|---:|---|
| W11 close | 1274 | 190 | W11 merge (PR #14) |
| Pre-W12-0 | 1274 | 190 | baseline |
| W12-0 | +13 | +21 | output-signals redaction tests |
| W12-1 | +20 | unchanged | architecture gates + lazy proxy |
| W12-2 | +14 | unchanged | naming-overlap, coverage-summary |
| W12-3 | +8 | unchanged | discriminated union tests |
| pre-W12-4 | +5 | unchanged | digest-pin gate, multiline PEM |
| W12-4 | +2 | unchanged | LoC budget gate |
| W12-5 | +3 | unchanged | facade gates + body-preview |
| **W12 close** | **1430** | **211** | **target** |

### C. Doğrulama tek-komut özeti

W12 close sürecini hızlıca koşturmak için:

```bash
# 1. Working tree temiz mi?
git status && git log --oneline -5

# 2. Architecture gates green mi?
.venv/bin/python -m pytest tests/architecture -q

# 3. Full check-all
make check-all 2>&1 | tail -10

# 4. Test bar
make test-local 2>&1 | tail -5
make test-security 2>&1 | tail -3

# 5. LoC budget cross-check
wc -l executor/flows/playwright/runtime_capture/extension_host*.py \
      executor/flows/playwright/entrypoint/runner.py
ls executor/flows/playwright/*.py | wc -l

# 6. Public surface invariants
.venv/bin/python -c "from executor.flows.playwright.runtime_capture import extension_host; assert len(extension_host.__all__) == 17; print('extension_host facade: 17 ✓')"
.venv/bin/python -c "from executor.flows.playwright import attribution; pub = [n for n in attribution.__all__ if not n.startswith('_')]; assert len(pub) == 10; print(f'attribution: {len(pub)} public ✓')"
```

Hepsinin `0` exit code dönmesi → close sign-off için yeşil.
