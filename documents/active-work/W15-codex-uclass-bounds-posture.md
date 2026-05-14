# W15 — Codex U-class Close-Out + UI Bounds + Posture (Active Work Tracker)

`Last Updated: 2026-05-14 (W15 active; week15 cut from main HEAD 7cc2921 on 2026-05-14; W15-1 closed via c58c365 — sync analyze error taxonomy parity, M10; W14 close-out PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 close-out PR #20 week13 -> main MERGED 2026-05-13 via 772deb3)`
`Phase: W15 active (W15-1 closed; W15-2..W15-7 pending)`
`Branch: week15 (cut from main HEAD 7cc2921 on 2026-05-14)`
`Owner: ekrem`

> **Authored 2026-05-14** as the W15 scope skeleton. Stable IDs `W15-1..W15-7`
> are reserved by the iteration plan and **assigned at first pull** per the
> W11/W12/W13/W14 precedent (`REFACTOR_OPTIMIZATION.md` §13.0). Remaining
> sub-iter IDs (`W15-2`..`W15-7`) fill in as each is pulled.

This is the canonical active work tracker for the W15 Codex U-class
Close-Out + UI Bounds + Posture window. Items receive stable IDs (`W15-1`,
`W15-2`, ...) **at first pull**, not preemptively, per the
W11/W12/W13/W14 precedent.

This file mirrors the structure of
[`W14-codex-acceptance-observability.md`](W14-codex-acceptance-observability.md).
Slim canonical [`REFACTOR_OPTIMIZATION.md §13`](../REFACTOR_OPTIMIZATION.md)
carries the entry-conditions block, goal statement, and current candidate
list.

## Status (Quick Glance)

+ **W15 active — `week15` branch cut from `main` HEAD `7cc2921` on
  `2026-05-14`.** W15-1 closed `2026-05-14` via `c58c365` (sync analyze
  error taxonomy parity, M10 close); W15-2..W15-7 pending sequential
  pull. W14 close-out PR #21 (`week14 -> main`) **MERGED** `2026-05-14`
  via `4e03c8d`; all W14-1..W14-8 closed. W15 base differs from the
  scope-skeleton plan note (`4e03c8d`) because the `7cc2921`
  ("docs(W15): scope skeleton + …") commit on `main` carries the W15
  tracker itself and must be in-branch for the lane file to exist;
  cutting from `4e03c8d` would have required re-applying the skeleton
  on the branch.
+ **Entry gate (met + branch open).** W15-1 pulled:
  + W14 close-out PR #21 ✓ **MERGED** `2026-05-14` via `4e03c8d`
    (close-out PR included W14-1..W14-8 sub-iter ratchet'leri +
    close-out hygiene pass — Ruff lint, UI contract sync, markdown
    formatting, doc truth-state alignment, `make markdownlint` gate,
    ADR code fence arch test).
  + W14 final/post-merge baseline (re-recorded `2026-05-14` at W15-1
    pull on `week15`): `tests/architecture/` **172 passed** (W14 final
    171 + close-out hygiene ADR-code-fence gate = 172; the W14 tracker
    listed 171 because the hygiene gate counted as a separate +1 and
    was added at the close-out PR rather than within the W14-8
    landing). `make test-security` **215 passed** (unchanged from W13
    final). `make test-local` not re-run at pull (requires Docker
    postgres_test; behavioral coverage validated via targeted suites
    — see W15-1 Per-Item Detail for verification scope).
  + Close-out prerequisites recorded; W15-open checklist complete at
    `2026-05-14` branch cut.
+ **Sub-iteration scope (locked, IDs assigned at pull).**

| Iter | Tema | Stable ID(s) | Tahminî efor |
|---|---|---|---|
| **W15-1** ✅ | Sync analyze error taxonomy alignment — closed `2026-05-14` via `c58c365` | `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]` | 1 oturum |
| **W15-2** | Workspace symlink check order / orphan removal | `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]` | 1 oturum |
| **W15-3** | `activationEvents` bounds + DB field-length migration | `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]` | 2 oturum (migration sequencing) |
| **W15-4** | UI bounds bundle: event spread / timeline / relations graph cap | `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]` + `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]` | 1-2 oturum |
| **W15-5** | Quick fixes bundle: UI `/health` proxy + lifecycle `for <id>` regex | `[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]` + `[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]` | 1 oturum |
| **W15-6** | Unauthenticated catalog endpoints posture (ADR 0011) | `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]` | 2 oturum (ADR + implementation) |
| **W15-7** | Regression lock-in umbrella: compose image pin + GH action pin + doc preamble refresh | `[FOLLOWUP compose-image-mutable-ref-pin]` + `[FOLLOWUP gh-action-trivy-version-pin]` + (post-W14 audit) doc-preamble truth-state refresh | 1 oturum |

+ **Pull sequence rationale.** W15-1 ve W15-2 önce — düşük blast radius,
  her ikisi de izole tek-dosya/birkaç-dosya fix. Sonra W15-3 (DB migration
  içerdiği için orta-risk; izole bir pull olarak güvenli sequencing
  ister — schema değişiklikleri başka sub-iter'lara karışmamalı). W15-4
  ve W15-5 sonraki adım: UI tarafı odaklı, generated `contracts.ts`'ye
  dokunmaz (UI-side caps + view-model). W15-6 (U10-U11) ADR-pending bir
  posture decision; ADR önce yazılır, sonra kod uygulanır — bu sebeple
  geç çekilir. W15-7 en son: W14-6 pattern'i — regression lock-in
  umbrella ratchet/pin türü kalemler en sonda toplanır.

## Entry Conditions (ticked at W15 open `2026-05-14`)

+ [x] W14 closed and merged to `main` via close-out PR #21 (`4e03c8d`,
  `2026-05-14`); close-out PR included W14-1..W14-8 ratchet bundle +
  close-out hygiene pass.
+ [x] W14 sub-iter slate complete (W14-1..W14-6) + post-slate hotfixes
  (W14-7 container-shipping regression + W14-8 preventive Python 3.11+
  API gate) closed `2026-05-13`.
+ [x] W14 final architecture gate count recorded: `tests/architecture/`
  **172** (W14-8 lifted 170 → 171; close-out hygiene PR ADR code fence
  arch test added the +1 separately counted as 171 → 172 on the
  post-merge baseline; `make markdownlint` is a Make-target gate, not
  a pytest case). Re-recorded at W15-1 pull on `week15`.
+ [x] W14 final/post-merge `make test-security` re-recorded **215
  passed** (unchanged from W13 final). `make test-local` not re-run
  at pull (requires Docker postgres_test); behavioral parity for
  W15-1 validated via targeted suites — full `make test-local`
  baseline re-record deferred to the next sub-iter that exercises
  cross-module behavior (or to the W15 close-out hygiene pass).
+ [x] W15 lane document (this file) header updated to `Phase: W15 active`
  per W11/W12/W13/W14 precedent at the explicit branch cut / first pull
  (`2026-05-14`).

## Goal (per `REFACTOR_OPTIMIZATION.md` §13)

Üç tamamlayıcı thrust:

1. **Codex U-class + I-class acceptance-bar pull-forward (close-out).**
   W14 H-class (W13) + M-class (W14-2 + W14-3) close'larından sonra geriye
   2026-05-10 Codex Cloud audit'inde U-class (U1-U3, U6, U8, U10-U11) +
   I-class (I2, I4) + tail M-class (M10, M12) kaldı. W15 bu kalemleri
   kapatır; sonra Codex 2026-05-10 audit kapanmış olur (verified-closed
   audit trail'e taşınır).

2. **Posture decision.** `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]`
   architectural bir karar (ADR pending) — W15-6 bu ADR'ı 0011 olarak
   yazar ve uygular. Karar tek seferlik bir gate; gelecekteki posture
   shift'leri ADR amendment ile yapılır.

3. **Post-W14 close-out audit findings — regression lock-in umbrella.**
   W14 close-out audit (`2026-05-14`) iki açık hijyen kalemi tespit
   etti: (a) `docker-compose.yml`'da mutable image ref'ler
   (`postgres:16-alpine`, `alpine/socat:latest`), (b) `.github/workflows/
   security.yml`'da mutable GH action ref (`aquasecurity/trivy-action@
   master`). Ayrıca audit'in immediate önerisi olarak 4 canonical
   preamble post-merge truth-state refresh. Hepsi W15-7'de bundle olur.

## Candidate Items (stable IDs assigned at first pull)

`Status` reflects current backlog state; `W15-N` IDs fill in as items move
from "not started" to "in progress". Items prefixed
`[FOLLOWUP codex-2026-05-10-…]` rows are from the `2026-05-10` Codex Cloud
audit; `[FOLLOWUP compose-image-mutable-ref-pin]` and
`[FOLLOWUP gh-action-trivy-version-pin]` are from
[`POST_POC_BACKLOG.md`](../POST_POC_BACKLOG.md) Engineering Quality.

| ID | Item | Lane | Status |
|---|---|---|---|
| **W15-1** | `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]` (sync `/api/marketplace/analyze` entry, async path ile error taxonomy uyumsuz — async tarafı pydantic ValidationError + 4xx döner, sync tarafı generic Exception'a düşüp 500 emit ediyor; aynı request shape iki farklı status alıyor) | `[platform-storage]` `[security-detection]` | **closed `2026-05-14` via `c58c365`** |
| **W15-2** | `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]` (`clean_workspace()` orphan symlink handling — check sırası TOCTOU window'u açıyor; ya kontrol sırası fix edilir ya da dead code olarak silinir; W14 audit'inde dokunulmadı) | `[executor-runtime]` `[security-detection]` | not started |
| **W15-3** | `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]` (`activationEvents` liste/string boyutu unbounded; oversized manifest DoS + DB row inflation; cap + Alembic field-length migration ister) | `[security-detection]` `[platform-storage]` | not started — DB migration sequencing requires standalone pull |
| **W15-4** | `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]` (UI event density / timeline spread / count operations unbounded; large activation report → UI freeze) | `[ui]` | not started |
| **W15-4** | `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]` (relations graph node-edge count unbounded; large extension reports UI graph render'ı yavaşlatıyor) | `[ui]` | not started |
| **W15-5** | `[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]` (UI client `/health` fetch'i nginx `/api/*` proxy'sini bypass ediyor olabilir; reverse-proxy posture'a uyumsuz; verify + fix) | `[ui]` `[platform-storage]` | not started |
| **W15-5** | `[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]` (lifecycle `"for <id>"` regex çok geniş; daraltma — log-noise + false-positive parser drift'i) | `[platform-storage]` | not started |
| **W15-6** | `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]` (auth posture decision; ADR 0011 — single-host appliance scope altında catalog endpoint'leri auth'suz mu, marker-based mı? Karar ADR ile, sonra koda uygulanır) | `[platform-storage]` `[security-detection]` | not started — ADR pending |
| **W15-7** | `[FOLLOWUP compose-image-mutable-ref-pin]` (`docker-compose.yml` `postgres:16-alpine` + `alpine/socat:latest` mutable tag'ler; SHA digest pin'e geç; `test_dockerfile_digest_pin.py`'ı compose `image:` anahtarlarını kapsayacak şekilde **extend**) | `[platform-storage]` | not started |
| **W15-7** | `[FOLLOWUP gh-action-trivy-version-pin]` (`.github/workflows/security.yml` `aquasecurity/trivy-action@master` mutable ref; version pin) | `[platform-storage]` | not started |
| **W15-7** | (post-W14 close-out audit immediate finding) doc preamble truth-state refresh — `CLAUDE.md`, `AGENTS.md`, `documents/REFACTOR_STATUS.md`, `documents/POST_POC_BACKLOG.md` "close-out PR week14 -> main next" cümleleri W14 merge'den sonra refresh edilmedi (refresh PR #21'in close-out hygiene commit'inde kısmen yapıldı; W15 close-out hygiene'da finalize) | `[docs-maintenance]` | not started |
| TBD watch | `[FOLLOWUP install-extension-cold-start-ipc-hang]` (W14-7 doğrulama sırasında ortaya çıkan VS Code IPC ack timeout; W14-7 fix'i bu yola dokunmadı; W15+ aday — direct trigger yok) | `[executor-runtime]` | watching — defer |

## Sub-iteration Scope Locks

Aşağıdaki bloklar her iterasyonun **scope kilit dokümantasyonudur**. İlk
pull'da sub-iterasyonun başlığı `W15-N — …` olarak finalize edilir ve
"Per-Item Detail" bölümüne taşınır.

### W15-1 scope — Sync analyze error taxonomy alignment

**Pull source.** [POST_POC_BACKLOG.md](../POST_POC_BACKLOG.md) "Codex Cloud
Audit Backlog → Post-W13 Candidates" → `[FOLLOWUP codex-2026-05-10-M10-
sync-analyze-typeerror-catch]`.

**Hedef.** Sync `/api/marketplace/analyze` entry'sinin error catch'i async
path ile aynı taxonomy'i kullansın. Async tarafı (job-driven path)
pydantic `ValidationError` → 4xx, `ExtensionNotFoundError` → 4xx,
geri kalan `Exception` → 5xx döner. Sync entry generic `try/except` ile
tüm hataları 500'e çeviriyor (M10'un Codex audit notu); aynı request
şekli iki farklı status code alıyor.

**Etkilenen yollar.**

+ [workflows/marketplace/analysis_service.py](../../workflows/marketplace/analysis_service.py)
  (384 LoC; sync entry + async path)
+ [workflows/marketplace/router.py](../../workflows/marketplace/router.py)
  — sync vs async endpoint'lerin error handler'ları
+ Olası: ortak error-taxonomy helper'ı (yeni veya mevcut — analysis_service
  içinde küçük helper yeterli)

**Adımlar.**

1. Async tarafın error taxonomy'sini çıkar (hangi exception → hangi
   status code → hangi response body).
2. Sync entry'yi aynı taxonomy'ye hizala; generic Exception catch
   yerine specific exception classes + ortak helper.
3. Yeni architecture gate `tests/architecture/test_analyze_error_
   taxonomy_parity.py` — AST'de sync ve async entry'lerin aynı
   exception sınıflarını handle ettiğini ve aynı status code map'ini
   kullandığını assert.
4. Behavioral regression: `tests/workflows/marketplace/test_analyze_
   error_taxonomy.py` (yeni) — her exception sınıfı için sync ve async
   parametrize.

**Test paterni.** Architecture gate (AST parity) + behavioral
parametrize (W14-2'nin `_coerce_safe_epoch_s` deseni gibi: input × beklenen
status × beklenen body).

**Exit kriterleri.**

+ 1 yeni architecture gate (`tests/architecture/` 171 → 172)
+ ~5-8 behavioral regression case
+ AGENTS Rule 9 (`no generic try/except Exception`) ihlali yoksa zaten
  spot kalkar; bu kalem onu doğal olarak temizler

**Bilinçli hariç.** `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-
typeerror-catch]`'in error-message-content tarafı (operator-facing
metin standardı) bu PR'a DAHİL EDİLMEZ — onun yeri
`[FOLLOWUP codex-automation-6]` (UI failure taxonomy, W16+ NEEDS-DESIGN).

### W15-2 scope — Workspace symlink check order / orphan removal

**Pull source.** `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-
order]`.

**Hedef.** `clean_workspace()` helper'ının symlink check sırası TOCTOU
window'u açıyor (Codex audit notu). İki seçenek:

(a) Helper kullanılmıyorsa dead code olarak sil (önce reference scan
    `rg -n "clean_workspace" --type py` ile teyit).
(b) Helper kullanılıyorsa: `lstat` → resolve → `realpath` sırasını
    workspace helper'larındaki W8-9 deseni ile aynı sıralamaya getir
    (resolve önce, çünkü symlink target güvenilmez).

**Etkilenen yollar.**

+ [executor/flows/playwright/workspace/](../../executor/flows/playwright/workspace/)
  (helper modüller; `clean_workspace`'in yaşadığı dosya scan ile teyit)
+ Olası caller'ları: `executor/flows/playwright/reset_state.py`,
  `executor/flows/playwright/automation.py`

**Adımlar.**

1. Reference scan: `clean_workspace`'in çağrıldığı yerleri bul.
2. Eğer 0 caller: dead code; sil. Test: import-graph gate'i tetiklemediğini
   doğrula.
3. Eğer caller var: TOCTOU sırasını W8-9 deseni ile hizala. Yeni
   behavioral test `tests/security/test_workspace_symlink_toctou.py`
   (symlinked path adversarial fixture).

**Test paterni.** Eğer fix path'i: behavioral test (symlink fixture +
race window simülasyonu). Eğer remove path'i: yeni test gerekmez, dead
code removal commit'i.

**Exit kriterleri.**

+ Helper ya silinir ya da TOCTOU-safe re-write edilir.
+ Eğer fix: ~3-5 case'lik behavioral test + (opsiyonel) architecture
  gate (workspace helper'larda `lstat`'tan önce `resolve` zorunlu).

**Bilinçli hariç.** Genel workspace TOCTOU sweep (yalnızca M12 path'i;
`[FOLLOWUP w8-9-network-body-boundary-split-secret-test]` ayrı).

### W15-3 scope — `activationEvents` bounds + DB field-length migration

**Pull source.** `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]`.

**Hedef.** `activationEvents` liste/string boyutu unbounded — saldırgan
manifest gigabyte-scale `activationEvents` push edebilir, DB row inflate
olabilir, oversize string parsing slowdown. Cap + DB field-length
Alembic migration.

**Etkilenen yollar.**

+ [packages/analysis_contracts/contracts.py](../../packages/analysis_contracts/contracts.py)
  — `activationEvents` field'ı (varsa) bound + `max_length`
+ Veya `appcore/contracts/schema_defs/` — DB schema'ya yansıyan
  contract
+ `alembic/versions/` — yeni migration: `activation_events` column
  (varsa) length bound; eğer text column ise constraint check
+ DB model: `appcore/db/models/` veya `appcore/storage/model_defs/`
  — Column max length

**Adımlar.**

1. Reference scan: `activationEvents` neresinde kontrat, neresinde DB
   column? (TEXT mi VARCHAR(N) mi şu an?)
2. Adversarial input scan: production scan örneği var mı (oversized
   activationEvents)?
3. Cap kararı: per-event string length ve list length. `activationEvents`
   resmi spec'te ne dökümante? (VS Code marketplace spec).
4. Pydantic v2 `max_length` + `min_length` + list `max_length`.
5. Alembic migration: `op.alter_column` ile column type değişikliği veya
   constraint check.
6. Migration round-trip: `alembic upgrade head` + `alembic downgrade -1`
   manuel doğrulama (programmatic test
   `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` deferred kalır).
7. Architecture gate: `tests/architecture/test_activationevents_bounds.py`
   (W14-2 paterni — Pydantic field'ında bound zorunlu).

**Test paterni.** Adversarial input regression (oversized list,
oversized string per item, NaN / None / non-list types) + Alembic
migration sanity (manuel doğrulama notu).

**Exit kriterleri.**

+ 1 yeni architecture gate (`tests/architecture/` 172 → 173)
+ ~6-10 behavioral regression case
+ Alembic migration landed, both directions test edildi (manuel)
+ DB field length değiştiyse: production-data scan + migration
  reversibility notu PR description'a eklenir

**Bilinçli hariç.** Genel manifest field bounds sweep — bu PR sadece
`activationEvents`. `displayName`, `description`, `keywords` vb. ayrı
W16+ aday (henüz Codex audit kalemi yok).

**Risk.** **Orta.** Migration; production-data shape kontrol etmeden
PR open etme. Eğer column'un mevcut max value'su yeni cap'ten büyükse
data truncation → veri kaybı; bound'u önce mevcut max value'ya göre
ayarla (cap >= max(current_lengths) + güvenlik tampolu).

### W15-4 scope — UI bounds bundle: event spread / timeline / relations graph cap

**Pull source.**

+ `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]`
+ `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]`

**Hedef.** İki kalem aynı patern: UI client-side büyük activation report
render ederken event density / timeline spread / relations graph
node-edge sayısı unbounded; UI freeze veya yavaş render. Cap + truncation
indicator.

**Etkilenen yollar.**

+ [ui/src/lib/](../../ui/src/lib/) view-model katmanı (özellikle
  `view-models.ts` — hand-maintained, generated değil)
+ UI component'ler: timeline view, relations graph view (lokasyon ui/
  scan ile)
+ Generated [`ui/src/lib/types/contracts.ts`](../../ui/src/lib/types/contracts.ts)
  bu PR'da değişmez (cap UI-side, backend contract aynı kalır)

**Adımlar.**

1. UI scan: timeline render edilen component, relations graph render
   edilen component, event list paginate eden component'ler.
2. Cap kararı: UI ergonomic upper bound (kullanıcı 1000+ event'i
   anlamlı şekilde inspect etmiyor; cap 500-1000 arası + scrollable
   truncation indicator).
3. View-model layer'da slice + "X more, truncated" indicator (UX
   pattern; backend cap değil).
4. Relations graph: node + edge cap; force-graph render edilen
   component'in input boundary'sinde slice.
5. UI vitest: cap enforcement + truncation indicator.

**Test paterni.**

+ UI vitest (existing `ui/src/**/*.test.ts(x)` deseni).
+ Snapshot for truncation indicator.

**Exit kriterleri.**

+ UI cap enforced + truncation UX
+ UI vitest coverage: ~5-8 case per cap (event / timeline / relations)
+ Backend contract unchanged

**Bilinçli hariç.** Backend report-side trim (backend zaten W14-2'de
ts bound + W14-3'te summary redaction yaptı; cap UI-side). Eğer backend
de truncation policy ister, ayrı W16+ pull.

### W15-5 scope — Quick fixes bundle: UI `/health` proxy + lifecycle regex

**Pull source.**

+ `[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]`
+ `[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]`

**Hedef.** İki düşük-blast quick fix:

**I2.** UI client'ı `/health` fetch'ini direkt API portuna gönderiyor
olabilir (nginx `/api/*` proxy'sini bypass ediyor); reverse-proxy
posture ile uyumsuz. Doğrula + fix: UI tüm fetch'leri `/api/*`
prefix'i üzerinden yapsın.

**I4.** Lifecycle log'ları "for <id>" regex'i çok geniş — bazı log
satırlarında false-match. Regex'i daralt (örn. `for [0-9a-f]{8}-` veya
job-id format'ına özel).

**Etkilenen yollar.**

+ I2: [ui/src/](../../ui/src/) — fetch utility, base URL config
+ I4: [appcore/storage/crud_ops/analysis_jobs/lifecycle.py](../../appcore/storage/crud_ops/analysis_jobs/lifecycle.py)
  veya `extrace.*` log filter'ında regex (regex location scan)

**Adımlar.**

1. I2: UI fetch scan; `/health` çağrısının base URL'ini doğrula. nginx
   proxy config (`docker/ui/nginx.conf` veya benzeri) ile uyumla.
2. I2 test: UI vitest — fetch mock'unda `/health` yerine `/api/health`
   beklentisi.
3. I4: regex location scan (`rg -n 'for <id>' --type py`); regex'i
   daralt + unit test (positive + negative case'ler).

**Test paterni.** I2 için UI vitest; I4 için unit test (Python regex).

**Exit kriterleri.**

+ I2 fixed + UI vitest case
+ I4 regex tightened + ~4-6 unit test case (positive match + false
  positive reject)

**Bilinçli hariç.** Genel UI fetch surface sweep (I2 sadece `/health`);
genel log regex sweep (I4 sadece "for <id>").

### W15-6 scope — Unauthenticated catalog endpoints posture (ADR 0011)

**Pull source.** `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-
endpoints]` (ADR pending).

**Hedef.** Catalog endpoint'leri (extension_catalog router) auth'suz —
single-host appliance scope altında bu OK mi, yoksa marker-based auth
ister mi? Karar ADR 0011 ile, sonra koda uygulanır.

**Etkilenen yollar.**

+ Yeni: `documents/decision-records/0011-unauthenticated-catalog-
  endpoints-posture.md`
+ [workflows/extension_catalog/router.py](../../workflows/extension_catalog/router.py)
  (posture'a göre)
+ Olası: `appcore/api/auth.py` veya benzeri (marker-based ise)
+ Yeni: `tests/architecture/test_catalog_endpoint_posture.py`
  (posture'ı gate eden test — posture shift ADR amendment ile)

**Adımlar.**

1. ADR taslağı: ADR 0001 (single-host appliance) + ADR 0007 (loopback
   default) bağlamında posture seçenekleri:
   - **Option A:** auth'suz kalsın (single-host scope; loopback default;
     network reachable ancak `EXTRACE_ALLOW_LAN` opt-in ile).
   - **Option B:** marker-based auth (HMAC harness marker'ı W13-1'de
     landed; aynı pattern'i catalog'a uygula).
   - **Option C:** session-based auth (gereksiz karmaşıklık; tek-kullanıcı
     appliance için overkill — muhtemel ret).
2. Trade-off analizi: threat model (ADR 0002), single-host scope
   (ADR 0001), loopback default (ADR 0007).
3. Karar + ADR landed.
4. Posture'a göre kod uygula:
   - A: hiçbir kod değişikliği gerekmez; ADR cite ederek mevcut durumu
     dökümante et + posture gate'i yaz.
   - B: HMAC marker check'i catalog router'a ekle; W13-1 paterni mirror.
   - C: ret.
5. Yeni architecture gate `tests/architecture/test_catalog_endpoint_
   posture.py` — posture'ı pin'le.

**Test paterni.** Posture'a göre değişir. A path'i: gate basit (route
listed, no auth dependency). B path'i: gate marker check'i zorunlu kılar.

**Exit kriterleri.**

+ ADR 0011 landed (accepted + implemented date)
+ Posture'a göre kod
+ 1 yeni architecture gate (`tests/architecture/` 173 → 174)
+ ADR 0002 threat model'ı amendment'la (eğer Option B veya C seçilirse)

**Bilinçli hariç.** Genel auth surface sweep (sadece catalog
endpoints). Marketplace endpoint'leri (`/api/marketplace/*`) ayrı
posture, bu PR'da dokunulmaz.

**Risk.** **Orta** — ADR karar yükü. Karar gerekçesi sonradan
tornaya alınamaz; iyi düşünülmüş gerekçe + threat-model bağı şart.

### W15-7 scope — Regression lock-in umbrella: compose pin + GH action pin + doc preamble refresh

**Pull source.**

+ `[FOLLOWUP compose-image-mutable-ref-pin]`
+ `[FOLLOWUP gh-action-trivy-version-pin]`
+ (post-W14 close-out audit immediate finding) doc preamble truth-state
  refresh

**Hedef.** Üç düşük-blast hijyen + lock-in kalemi:

**(a) Compose image pin.** `docker/docker-compose.yml` (veya repo root
`docker-compose.yml`):

+ `postgres:16-alpine` → `postgres@sha256:...`
+ `alpine/socat:latest` → `alpine/socat@sha256:...` (debug profile
  içinde; opt-in)

`tests/architecture/test_dockerfile_digest_pin.py` şu an Dockerfile
`FROM` satırlarını kontrol ediyor; bunu compose `image:` anahtarlarını
da kapsayacak şekilde **extend** (yeni gate açma; mevcut gate'in
scope'unu genişlet — bu W14-6 "extend, do not duplicate" disiplini).

**(b) GH action pin.** `.github/workflows/security.yml`:

+ `aquasecurity/trivy-action@master` → `aquasecurity/trivy-action@<SHA>`
  veya `aquasecurity/trivy-action@v0.X.Y` (workflow'un diğer action'larıyla
  aynı pattern).

Yeni gate gerekmez; mevcut workflow YAML lint zaten çoğu hata'yı
yakalar. Eğer ekstra invariant istenirse `tests/architecture/
test_gh_action_pinning.py` (ama önce mevcut workflow auditle
ihtiyacı doğrula).

**(c) Doc preamble truth-state refresh.** W14 close-out PR #21 merge
sonrası 4 canonical preamble'ı refresh:

+ `CLAUDE.md` (line 3)
+ `AGENTS.md` (line 3)
+ `documents/REFACTOR_STATUS.md` (line 3)
+ `documents/POST_POC_BACKLOG.md` (line 3)

"W14 close-out PR week14 -> main next" → "W14 close-out PR #21
`week14 -> main` **MERGED** `2026-05-14` via `4e03c8d`". Tarih bump.

`tests/architecture/test_readme_phase_pointer.py` zaten phase pointer
discipline'ı izliyor mu? Doğrula; eğer izlemiyorsa preamble truth-state
gate'i eklemeyi düşün (ama önce mevcut gate'in scope'unu kontrol).

**Etkilenen yollar.**

+ [docker-compose.yml](../../docker-compose.yml) (line 121 civarı —
  `alpine/socat`; postgres tag konum scan ile)
+ [.github/workflows/security.yml](../../.github/workflows/security.yml)
  (line 71 — trivy action)
+ [tests/architecture/test_dockerfile_digest_pin.py](../../tests/architecture/test_dockerfile_digest_pin.py)
  — scope extension
+ [CLAUDE.md](../../CLAUDE.md), [AGENTS.md](../../AGENTS.md),
  [documents/REFACTOR_STATUS.md](../REFACTOR_STATUS.md),
  [documents/POST_POC_BACKLOG.md](../POST_POC_BACKLOG.md)

**Adımlar.**

1. SHA çek: postgres + socat current digest'lerini docker registry'den
   resolve et (`docker pull` + `docker inspect`).
2. Compose pin + gate extension.
3. Trivy action SHA veya version pin.
4. 4 preamble refresh (text edit).
5. Gate extension'ın yeni image entry'leri yakaladığını doğrula
   (existing gate'i koş).

**Test paterni.** Architecture gate scope extension (yeni gate açma).

**Exit kriterleri.**

+ Compose image'ler digest-pinned
+ GH action version/SHA-pinned
+ `test_dockerfile_digest_pin.py` compose `image:` anahtarlarını da
  kapsar — `tests/architecture/` count 174 (unchanged; extension, not
  new gate)
+ 4 preamble refresh'lendi
+ W14 close-out audit immediate finding kapanır

**Bilinçli hariç.** Genel mutable-ref sweep (sadece compose + trivy);
geniş GH Actions CI reintroduction (`[FOLLOWUP ci-reintroduction]`
ayrı, W16+).

## Excluded From W15 (W15+'a veya W16+'ya düşer)

+ **W14-1 sonrası deferral (W15+):**
  `[FOLLOWUP scenario-accountant-conservation-split]` — kök neden
  downgrade hâlâ geçerli, doğrudan trigger yok; defer.
+ **Codex M-class tail (W15 dışı):** M5 (W14-5 yan ürünü olarak kapandı),
  geri kalan tüm M-class kalemler W15 sub-iter slate'inde.
+ **Watching items (LoC bütçesi aşılana kadar dokunma):**
  `[FOLLOWUP planner-selection-readability-audit]`,
  `[FOLLOWUP attribution-links-build-evidence-bundle-density]`,
  `[FOLLOWUP execute-attempt-rebloat-watch]`,
  `[FOLLOWUP dispatch-execution-rebloat-watch]`.
+ **UI follow-up'ları (W15-4 dışında):**
  `[FOLLOWUP ui-raw-context-discriminator-parity]`,
  `[FOLLOWUP ui-supplemental-types-retire]`,
  `[FOLLOWUP vsix-integrity-in-activation-report]`,
  `[FOLLOWUP vsix-thresholds-extra-keys]`,
  `[BACKLOG ui-v3-5]`, `[CLEANUP ui-v3-9]`, `[CLEANUP ui-v3-14]`.
+ **Workflow / platform deferral'leri:**
  `[FOLLOWUP simulation-progress-cancel]` alt-kalemleri,
  `[FOLLOWUP analysis-thread-supervisor]`,
  `[FOLLOWUP job-service-typevar-audit]`,
  `[FOLLOWUP sqlalchemy-error-subtype-logging]`,
  `[FOLLOWUP w11-8-companion-workflow-orm-bleed]`.
+ **Contracts / detection deferral'leri:**
  `[BUG silent-scenario-dropout-regression]`,
  `[FOLLOWUP report-finalize-top-level-field-sync-drift]`,
  `[FOLLOWUP event-attempt-verification-status-validator]`,
  `[FOLLOWUP report-invariants-runtime-evidence-drift]`,
  `[FOLLOWUP compute-verdict-table-driven-test]`,
  `[FOLLOWUP signal-summary-needs-review-categories]`,
  `[FOLLOWUP monitor-types-property-recomputation]`,
  `[FOLLOWUP activation-discovery-strategy-outcome-detail]`,
  `[FOLLOWUP planner-executor-action-enum]`,
  `[CLEANUP rule-registry-side-effect-loader]` (ADR 0003 deferred
  rules A5/A7 landed olunca).
+ **Engineering quality deferral'leri:**
  `[CLEANUP report-builder-naming]`,
  `[CLEANUP monitor-runtime-naming-overlap]`,
  `[CLEANUP env-example-extrace-vars]`,
  `[CLEANUP postgres-version-fact-drift]`,
  `[CLEANUP adr-0007-runbook-wording-drift]`,
  `[CLEANUP pre-commit-python-version-alignment]`,
  `[CLEANUP test-import-graph-policy-dump-split]`,
  `[FOLLOWUP ci-reintroduction]`.
+ **Test + observability deferral'leri:**
  `[FOLLOWUP w8-0-capture-pipeline]`,
  `[FOLLOWUP w8-1-extract-rejection-logging]`,
  `[FOLLOWUP w8-1-archive-count-bypass]`,
  `[FOLLOWUP w8-1-vsix-compressed-size-limit]`,
  `[FOLLOWUP w8-3-harness-js-scheme]`,
  `[FOLLOWUP w8-4-broader-executor]`,
  `[FOLLOWUP w8-6-content-sample-structural-test]`,
  `[FOLLOWUP w8-8-manifest-emit-when-needed]`,
  `[FOLLOWUP w8-8-trigger-sweep-as-test]`,
  `[FOLLOWUP w8-9-network-body-boundary-split-secret-test]`,
  `[FOLLOWUP adr-0002-vsix-extraction-section-missing]`,
  `[FOLLOWUP codex-automation-6]` (UI failure taxonomy, NEEDS-DESIGN
  → W16+),
  `[FOLLOWUP capability-verification-gap]` (NEEDS-DESIGN → W16+).
+ **Hijyen quick wins (opportunistic pull-as-found):** W15 close-out
  hygiene PR'ında sweep edilebilir (W14 close-out paterni: Ruff lint,
  markdown formatting, UI contract sync — eğer drift varsa).

## Test Baseline (target deltas)

W14 final baseline (re-recorded `2026-05-14` at W15-1 pull on `week15`):

+ `tests/architecture/` **172 passed** (W14-8 lifted 170 → 171;
  close-out hygiene PR ADR-code-fence gate counts as the post-merge
  +1 to 172).
+ `make test-security` **215 passed** (unchanged from W13 final).
+ `make test-local` not re-run at pull (Docker postgres_test required);
  full re-record deferred to next sub-iter that exercises cross-module
  behavior or to W15 close-out hygiene.

W15-1 actual deltas (`2026-05-14` via `c58c365`):

+ `tests/architecture/` 172 → **178** (+6 cases — new file
  `test_analyze_error_taxonomy_parity.py`: tuple decomposition, sync
  single-clause discipline, async references both subset tuples,
  helper class-branch coverage, sync handler-body dispatch through
  helper [vacuous-truth], ExecutorError branch delegates to
  `map_executor_error` [W10-7 redaction contract]).
+ New behavioral file `tests/workflows/marketplace/test_analyze_error_taxonomy.py`
  with **+21 cases** (10 helper status map incl. PermissionError
  subclass-dispatch + 1 unmapped-class guard + 1 vacuous-truth
  coverage check + 9 endpoint round-trip).
+ Existing 66 `tests/workflows/marketplace/test_router.py` cases
  unchanged (no regression in the sync surface contract).

W15 target deltas (per sub-iter):

| Iter | `tests/architecture/` delta | Behavioral test delta | Net |
|---|---|---|---|
| W15-1 ✅ | **+6 (actual)** sync-async parity (6 invariants — 4 initial + 2 post-W15-1 strengthening: handler-body dispatch + ExecutorError delegation) | +21 case (helper + endpoint parametrize + PermissionError subclass) | **closed +6 gates** |
| W15-2 | +0 or +1 (workspace TOCTOU gate, fix path'inde) | +1 dosya (~3-5 case, fix path'inde) | +0/+1 gate |
| W15-3 | +1 (activationEvents bounds gate) | +1 dosya (~6-10 case) | +1 gate |
| W15-4 | +0 (UI-side, architecture gate yok) | +3 dosya UI vitest (~15-24 case) | +0 arch |
| W15-5 | +0 (UI vitest + Python unit test) | +1 UI + +1 unit (~6-10 case) | +0 arch |
| W15-6 | +1 (catalog endpoint posture gate) | (posture'a göre) | +1 gate |
| W15-7 | +0 (mevcut gate extension) | (extension, yeni dosya yok) | +0 (extension) |
| **Total** | **+3 ile +4 arası** | **~35-60 behavioral case** | `tests/architecture/` 171 → **174-175** |

`make test-local` ve `make test-security` delta'sı sub-iter close'larından
sonra re-record edilir (W14 paterni: her sub-iter sonu test sayısını
bottom-of-file summary'ye eklenir).

## Per-Item Detail (filled in as sub-iters close)

### W15-1 — Sync analyze error taxonomy parity with async path — closed `2026-05-14` via `c58c365`

**Stable ID(s).** `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]`.

**Landing commit(s).** `c58c365` (single atomic commit — production +
arch gate + behavioral test).

**Module locations.**

+ `workflows/marketplace/analysis_service.py:77-103` — three module-level
  tuples `ANALYZE_RECOVERABLE_ERROR_TYPES`,
  `ANALYZE_PROGRAMMING_ERROR_TYPES`, `ANALYZE_ERROR_TYPES` (union as
  `BinOp(Add)` over the two subset names).
+ `workflows/marketplace/analysis_service.py:218-256` —
  `analyze_error_to_http_response(exc)` helper with isinstance branches
  for ExecutorError (delegates to `map_executor_error`),
  FileNotFoundError, ActivationReportLoadError/TriggerPlanError/OSError/
  SQLAlchemyError, ValueError, TypeError/AttributeError.
+ `workflows/marketplace/analysis_service.py:368-379` — async
  `run_analysis_job` except clauses migrated to
  `ANALYZE_PROGRAMMING_ERROR_TYPES` / `ANALYZE_RECOVERABLE_ERROR_TYPES`
  (replaces the prior open-coded six-class + two-class tuples).
+ `workflows/marketplace/router.py:328-345` — sync `analyze_extension`
  collapses the prior four-clause except into one
  `except ANALYZE_ERROR_TYPES` over the helper.

**Tests added.**

+ `tests/architecture/test_analyze_error_taxonomy_parity.py` × **6** AST
  invariants:
    1. Tuple decomposition (`ANALYZE_ERROR_TYPES = ANALYZE_RECOVERABLE_ERROR_TYPES + ANALYZE_PROGRAMMING_ERROR_TYPES`).
    2. Sync `analyze_extension` single-clause discipline (only
       `except ANALYZE_ERROR_TYPES`).
    3. Async `run_analysis_job` references both subset tuples.
    4. Helper has isinstance branch for every taxonomy class.
    5. **(post-W15-1)** Vacuous-truth — sync handler body dispatches
       through `analyze_error_to_http_response`; no open-coded
       `HTTPException(...)` inside the except body. Prevents a refactor
       from keeping invariant 2 (canonical tuple) while routing the
       caught exception through a hand-rolled status map.
    6. **(post-W15-1)** ExecutorError branch in the helper delegates to
       `map_executor_error` — pins the W10-7 secret-redacted detail +
       structured `error_id` contract so the branch cannot regress into
       a plain inline `HTTPException(502, str(exc))`.
+ `tests/workflows/marketplace/test_analyze_error_taxonomy.py` × **21**
  cases:
  + Parametrized helper status map × **10** (9 taxonomy classes +
    `PermissionError` subclass-dispatch case — verifies `isinstance`
    MRO so `PermissionError` lands on the `OSError` 502 branch
    without an exact-type match).
  + Unmapped-class defensive guard × 1
    (synthetic `RuntimeError` subclass trips the helper's
    `AssertionError`).
  + Vacuous-truth coverage check × 1 (every class in
    `ANALYZE_ERROR_TYPES` appears at least once in `HELPER_CASES`).
  + Endpoint round-trip via TestClient × **9** (HELPER_CASES minus
    ExecutorError — its detail body is asserted by existing
    `test_analyze_install_failure_502` /
    `test_analyze_automation_failure_502`; `PermissionError` included
    and routes to 502 end-to-end).

**Production diff.** +50 net LoC in `analysis_service.py` (tuples +
helper + import + `__all__`); −10 net LoC in `router.py` (four-clause
except collapsed; unused imports dropped). Net +40 LoC production +592
LoC including tests/docs.

**Verification.**

+ `make test-security` **215 passed** (no drift; W13 / W14 baseline).
+ `pytest tests/architecture/` **176 passed** (W14 final 172 + W15-1
  +4).
+ `pytest tests/workflows/marketplace/test_router.py` 66 passed, 1
  skipped (fixture-availability skip, unrelated).
+ `pytest tests/workflows/marketplace/test_analyze_error_taxonomy.py`
  19 passed.
+ `ruff check workflows/marketplace/ tests/architecture/test_analyze_error_taxonomy_parity.py tests/workflows/marketplace/test_analyze_error_taxonomy.py` — clean.
+ `make test-local` not re-run (Docker postgres_test required); full
  baseline re-record deferred to a later sub-iter that needs the
  Docker-backed lane, or to W15 close-out hygiene.

**Status map (mirrors async `fail_job` semantics).**

| Exception | Sync (pre-W15-1) | Sync (post-W15-1) | Async (run_analysis_job) |
|---|---|---|---|
| ExecutorError | 502 (map_executor_error) | 502 (unchanged via helper delegation) | fail_job |
| FileNotFoundError | 404 | 404 | fail_job (recoverable) |
| ActivationReportLoadError | 502 | 502 (helper matches before ValueError branch) | fail_job (recoverable; via ValueError catch) |
| TriggerPlanError | 502 | 502 | fail_job (recoverable) |
| OSError | **500 (bubble)** | **502** | fail_job (recoverable) |
| SQLAlchemyError | **500 (bubble)** | **502** | fail_job (recoverable) |
| ValueError | **500 (bubble — non-ARLE)** | **400** | fail_job (recoverable) |
| TypeError | **500 (bubble)** | **500 (explicit)** | fail_job + re-raise (programming) |
| AttributeError | **500 (bubble)** | **500 (explicit)** | fail_job + re-raise (programming) |

**Consciously excluded (defers to W16+).** Error-message-content
operator-facing standard for the M10 follow-up → tracked under
`[FOLLOWUP codex-automation-6]` (UI failure taxonomy, NEEDS-DESIGN).

## Close-Out (when W15 ends)

W15 kapanır şu koşullar sağlandığında:

+ W15-1..W15-7 kapanır ya da deferral rasyoneli ile W16'ya taşınır.
+ W15 tracker final close evidence + current test counts tutar.
+ `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, `active-work/README.md`,
  ve ilgili lane docs aynı active/closed state'i gösterir.
+ Slim canonicals kısa kalır; verbose evidence önce arşivlenir.
+ `week15 → main` close-out PR W12 PR #18 / W13 PR #20 / W14 PR #21
  cut-off pattern'ini izler.
+ Close-out hygiene pass (W14 paterni): Ruff lint, UI contract sync,
  markdown formatting, doc truth-state alignment, (varsa) yeni
  regression gate'ler. W15-7 doc preamble refresh'i bu pass'in
  parçası olarak finalize.
