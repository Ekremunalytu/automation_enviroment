# W14 — Codex M-class Acceptance + Observability (Active Work Tracker)

`Last Updated: 2026-05-13 (W14 active; W14-1 pulled; week14 branch cut from main at 69251f1)`
`Phase: W14 active (W14-1 pulled 2026-05-13 — scenario-dropout-upstream-root-cause BLOCKER triage)`
`Branch: week14 (cut from main 2026-05-13 at HEAD 69251f1; close-out PR opens after W14-6 GREEN)`
`Owner: ekrem`

> **Authored 2026-05-11** as the W14 scope skeleton. Stable IDs `W14-1..W14-6`
> are reserved by the iteration plan and **assigned at first pull** per the
> W11/W12/W13 precedent (`REFACTOR_OPTIMIZATION.md` §12.0). W14-1 pulled
> `2026-05-13` on the `week14` branch cut from `main` at `69251f1`. Remaining
> sub-iter IDs (`W14-2`..`W14-6`) fill in as each is pulled.

This is the canonical active work tracker for the W14 Codex M-class Acceptance + Observability window. Items receive stable IDs (`W14-1`, `W14-2`, ...)
**at first pull**, not preemptively, per the W11/W12/W13 precedent.

This file mirrors the structure of
[`W13-test-expansion-observability.md`](W13-test-expansion-observability.md).
Slim canonical [`REFACTOR_OPTIMIZATION.md §12`](../REFACTOR_OPTIMIZATION.md)
carries the entry-conditions block, goal statement, and current candidate
list.

## Status (Quick Glance)

+ **W14 active — W14-1 pulled.** Six sub-iterations scoped; W14-1 in progress
  on the `week14` branch (cut from `main` at `69251f1` on `2026-05-13`).
  Close-out PR #20 (`week13 -> main`) **MERGED** `2026-05-13` via `772deb3`.
+ **Entry gate (met).** Opens W14-1:
  + W13 close-gate cleared ✓ (`2026-05-13`): W13-11 (HMAC python secret
    eager-consume) ✓ closed `2026-05-12`; W13-12 (fail-closed harness
    handshake) ✓ closed `2026-05-12`; W13-13 (worker-start cancel-race
    CAS — Path B worker-entry `with_for_update()` snapshot lock;
    README sweep + regex pin already landed in W13-11 push
    `2026-05-12`) ✓ closed `2026-05-13`.
  + `week13 -> main` close-out PR #20 **MERGED** `2026-05-13` via
    `772deb3` ✓ (close-out PR included W13-11/12/13 close-pass fixes
    + W13-1..W13-10 sub-iter ratchet'leri + §11.10 GOAL pulls).
  + W13 final/post-merge baseline recorded: `make test-local` 1551 passed /
    10 skipped / 8 deselected; `make test-security` 215 passed;
    `tests/architecture/` 117 passed.
  + Close-out prerequisites are recorded; the W14-open checklist completes
    at the explicit branch cut / first pull.
+ **Sub-iteration scope (locked, IDs assigned at pull).**

| Iter | Tema | Stable ID(s) | Tahminî efor |
|---|---|---|---|
| **W14-1** | Senaryo dropout kök neden araştırması | `[BUG scenario-dropout-upstream-root-cause]` | 2-3 oturum (repro fixture odaklı, BLOCKER triage) |
| **W14-2** | Codex M-class — input validation kümesi | `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` + `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` | 1-2 oturum |
| **W14-3** | Codex M-class — dış yüzey sertleştirme | `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` + `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` + `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` | 2-3 oturum |
| **W14-4** | Doğruluk + concurrency | `[FOLLOWUP analysis-jobs-race]` + `[FOLLOWUP evidence-event-kind-raw-context-invariant]` | 2 oturum |
| **W14-5** | §11.10 GOAL devamı — Logger consolidation + run-ID stamping + executor runtime fingerprint | `[GOAL w14-logger-consolidation]` + `[GOAL w14-run-id-stamping]` (yeni stable ID'ler) + `[FOLLOWUP codex-automation-5]` (executor runtime fingerprint in automation output — run-ID stamping ile sibling) | 2-3 oturum |
| **W14-6** | §11.10 GOAL devamı — W8-W12 regression lock-in umbrella | `[FOLLOWUP arch-gate-executor-control-outbound]` + `[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]` + `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]` | 1-2 oturum |

+ **Pull sequence rationale.** W14-1 önce — bir CRITICAL kalem (`[BUG
  scenario-dropout-upstream-root-cause]`) W14 scope'unu genişletebilir veya
  HIGH'a indirebilir. Sonra düşük-risk M-class güvenlik yamaları (W14-2);
  sonra W13-6 redaction zincirinin doğal devamı (W14-3); sonra
  correctness/concurrency (W14-4); en son altyapı GOAL pulls (W14-5, W14-6).
  W14-5, W14-6'dan önce gelir çünkü logger consolidation regression lock-in
  gate'lerinde test enstrümantasyonuna girdi olur.

## Entry Conditions (target — to be ticked at W14 open)

+ [x] W13 close-gate cleared `2026-05-13`: W13-11 (HMAC python secret
  eager-consume) ✓ closed `2026-05-12`; W13-12 (fail-closed harness
  handshake) ✓ closed `2026-05-12`; W13-13 (worker-start cancel-race
  CAS — Path B worker-entry `with_for_update()` snapshot lock; README
  sweep + regex pin already landed in W13-11 push `2026-05-12`) ✓
  closed `2026-05-13`.
+ [x] W13 closed and merged to `main` via close-out PR #20
  (`772deb3`, `2026-05-13`); close-out PR included W13-1..W13-13
  ratchet bundle.
+ [x] W13 final/post-merge baseline recorded: `make test-local` 1551
  passed / 10 skipped / 8 deselected; `make test-security` 215 passed;
  `tests/architecture/` 117 passed.
+ [x] W13 ratchet gates pinned: W13-1..W13-7 acceptance-bar gates,
  W13-8/9/10 §11.10 GOAL gates, plus the W13-11/12/13 close-gate
  gates added during the close-pass.
+ [x] W14 lane document (this file) header updated to `Phase: W14 active`
  per W11/W12/W13 precedent (`2026-05-13`; `week14` branch cut from `main`
  at `69251f1`).

## Goal (per `REFACTOR_OPTIMIZATION.md` §12)

Two complementary thrusts:

1. **Codex M-class acceptance-bar pull-forward.** W13 closed the H-class
   (H3/H4/H5/H6) plus M1 + M9. W14 pulls the next eligible M-class items
   (M4-M7, M11, M13, M14b) plus the security/hygiene U4-U12 Makefile
   shell-quoting item. M5/M10/M12/U-other items remain Post-W14 (see
   `POST_POC_BACKLOG.md`).
2. **§11.10 GOAL devamı.** W13 deferred three §11.10 GOAL umbrellas to W14
   per the W12 PR #18 cut-off pattern: logger consolidation, run-ID
   stamping, and W8-W12 regression lock-in. W14-5 + W14-6 close these
   umbrellas (or split them further if scope grows).

Plus two correctness pull-forwards: `analysis-jobs-race` (CRITICAL, lock
asymmetry documented in W13-4.4) and `evidence-event-kind-raw-context-invariant`
(HIGH, Pydantic model_validator target; RED stub still needs to be authored).

## Candidate Items (stable IDs assigned at first pull)

`Status` reflects current backlog state; `W14-N` IDs fill in as items move
from "not started" to "in progress". Items prefixed `[§11.10 GOAL]` are
sourced from `REFACTOR_OPTIMIZATION.md` §11.10's W14-deferred candidates;
`[FOLLOWUP codex-2026-05-10-…]` rows are from the `2026-05-10` Codex Cloud
audit; `[BUG …]` rows are from `POST_POC_BACKLOG.md` Contracts/Reports/Detection.

| ID | Item | Lane | Status |
|---|---|---|---|
| **W14-1** | `[BUG scenario-dropout-upstream-root-cause]` (senaryolar `ScenarioAccountant`'a ulaşmadan planner / stimulus_passes / harness dispatch dizisinde düşüyor; son-metre conservation guard `unaccounted_dropout` raporluyor ama kök neden açık) | `[executor-runtime]` `[security-detection]` | **in progress** — BLOCKER triage; pulled `2026-05-13` on `week14` branch |
| TBD (W14-2) | `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` (extension-controlled `ts` field guard sız `datetime.fromtimestamp()`'a giriyor; OverflowError DoS vector) | `[security-detection]` | not started |
| TBD (W14-2) | `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` (`_build_report_messages()` `int(automation_health.get(...))` ValueError'a açık) | `[security-detection]` | not started |
| TBD (W14-3) | `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` (network capture event'lerinin `path` + `summary` alanları secret sızdırıyor; W12-5 gate sadece `*_body_preview`'i kapsıyor; W13-6 factory-internal redaction deseninin tekrarı) | `[security-detection]` `[executor-runtime]` | not started |
| TBD (W14-3) | `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` (VS Code `--remote-debugging-port=9222` auth'suz default-on, container'dan erişilebilir) | `[executor-runtime]` `[security-detection]` | not started — posture decision: default-disabled vs explicit opt-in env var |
| TBD (W14-3) | `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` (`Makefile` `sim-target`/`sim-run` `$(TARGET)`/`$(SCENARIO)` tırnaksız; shell injection riski; W13-5 dev-lan recipe-fix deseninin tekrarı) | `[security-detection]` | not started |
| TBD (W14-4) | `[FOLLOWUP analysis-jobs-race]` (`complete_analysis_job` `with_for_update()` lock'undan yoksun; `cancel_analysis_job` lock var; W13-4.4'te race window dokümante edildi) | `[platform-storage]` `[executor-runtime]` | not started — CRITICAL race window |
| TBD (W14-4) | `[FOLLOWUP evidence-event-kind-raw-context-invariant]` (`EvidenceEvent.kind` ↔ `raw_context.event_class` eşleşmesi Pydantic'te validate edilmiyor; RED stub adı planlandı: `test_evidence_event_rejects_kind_event_class_mismatch`) | `[security-detection]` `[contracts]` | not started — RED stub henüz yazılmadı |
| TBD (W14-5) | `[§11.10 GOAL]` `extrace.executor.*` logger consolidation (W13'ten devreden; executor logger init + emit pattern'leri worker thread'lerde tutarsız) | `[platform-storage]` | not started — W13'ten W14'e devredildi |
| TBD (W14-5) | `[§11.10 GOAL]` Run-ID stamping (W13'ten devreden; stable `EXTRACE_EPOCH_RUN_ID` executor çıktıları boyunca propagate + emit; logger consolidation'a bağımlı) | `[platform-storage]` `[executor-runtime]` `[security-detection]` | not started — logger consolidation'a bağımlı |
| TBD (W14-5) | `[FOLLOWUP codex-automation-5]` (executor runtime fingerprint in automation output for observability — version/build/commit emit at automation run boundary; run-ID stamping ile sibling tema, aynı PR ailesinde yan ürün olarak çekilir) | `[platform-storage]` `[executor-runtime]` | not started — W14-5 PR ailesinin tematik üyesi |
| TBD (W14-6) | `[§11.10 GOAL]` W8-W12 regression lock-in umbrella (W13'ten devreden; W14-6 alt-üyeleri: `arch-gate-executor-control-outbound` + `arch-gate-bare-binary-pragma-ratchet` + `w8-4-variable-indirect-subprocess-coverage`) | (multi) | not started — W13'ten W14'e devredildi |
| TBD watch | `[FOLLOWUP scenario-accountant-conservation-split]` (W14-1 kök neden tespitinden sonra ayrı pull olarak değerlendirilir; W14-1 PR'ına dahil edilmez) | `[executor-runtime]` | watching — W14-1 sonrası ayrı pull adayı |

## Sub-iteration Scope Locks

Aşağıdaki bloklar her iterasyonun **scope kilit dokümantasyonudur**. İlk
pull'da sub-iterasyonun başlığı `W14-N — …` olarak finalize edilir ve
"Per-Item Detail" bölümüne taşınır.

### W14-1 scope — Senaryo dropout kök neden (BLOCKER araştırma)

**Pull source.** [POST_POC_BACKLOG.md](../POST_POC_BACKLOG.md) "Contracts /
Reports / Detection" → `[BUG scenario-dropout-upstream-root-cause]`.

**Hedef.** Senaryolar `ScenarioAccountant`'a ulaşmadan önce planner /
stimulus_passes / harness dispatch dizisinde nerede düştüğünü tespit etmek.

**Etkilenen yollar.**

+ [scenario_accountant.py](../../executor/flows/playwright/monitor/scenario_accountant.py)
  (648 LoC, 26 mevcut test case; **dokunulmaz** — bu iterasyon kök neden
  ortaya koyana kadar)
+ [packages/analysis_planner/selection.py](../../packages/analysis_planner/selection.py)
  (497 LoC, watching item — bu iterasyon scope'unda dokunmaz)
+ Stimulus pass dispatch path: `executor/flows/playwright/stimulus/`
+ Harness dispatch: `executor/flows/playwright/entrypoint/dispatch.py` (402 LoC)

**Adımlar.**

1. Mevcut `unaccounted_dropout` log/evidence'larından kapsayıcı analiz:
   hangi extension sınıflarında, hangi senaryo tiplerinde dropout görülüyor.
2. Deterministik repro fixture'ı: en az bir benign extension için
   known-dropout senaryo seti (`tests/security/fixtures/` örüntüsü).
3. Trace enstrümantasyonu: planner → stimulus passes → harness boundary'lerinde
   senaryo ID emit.
4. Kök neden tespit; fix ya bu iterasyonda ya da `[FOLLOWUP
   scenario-accountant-conservation-split]` ile birleştirilerek W14 sonu
   ayrı pull olarak çekilir.

**Exit kriterleri.**

+ Repro fixture green/red gate olarak `tests/security/`'da yer alır.
+ Kök neden ya kapatılır (`[BUG scenario-dropout-upstream-root-cause]` kapanır)
  ya da BUG HIGH'a indirilip stochastic-bound dokümantasyonu eklenir.

**Bilinçli hariç.** `[FOLLOWUP scenario-accountant-conservation-split]`
(648 LoC refactor) bu PR'a DAHİL EDİLMEZ — kök neden tespiti + refactor
karışmamalı; refactor ayrı sub-iter veya W15+'a düşer.

### W14-2 scope — Codex M-class input validation kümesi

**Pull source.**

+ `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]`
+ `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]`

**Hedef.** İki kalem aynı patern: extension-kontrollü skalar değerler
tip-cast veya range-cast öncesi guard'sız tüketiliyor. Bundle olarak çekilir
çünkü test deseni (W13-6 parametrize regression örüntüsü) ortak.

**Etkilenen yollar.**

+ M4-M7 ts cast lokasyonu: arşiv evidence ile teyit edilecek
  ([archive/backlog/POST_POC_BACKLOG_full_2026-05-11.md](../archive/backlog/POST_POC_BACKLOG_full_2026-05-11.md))
+ M11: `_build_report_messages()` lokasyonu

**Test paterni (W13-6 mirror).**

+ Adversarial input (negative epoch, INT_MAX+1, NaN, malformed string) →
  guard yakalar, log emit, default fallback
+ Architecture gate: factory body invariant (cast öncesi
  `_validate_ts_range()` veya `_safe_int_coerce()` çağrısı zorunlu)
+ Parametrize regression: 3 case per item × 2 item = ~6 case

**Exit kriterleri.**

+ 2 yeni architecture gate
+ ~6 parametrize regression case
+ Production diff <50 net LoC; tek dosya per item

### W14-3 scope — Codex M-class dış yüzey sertleştirme

**Pull source.**

+ `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]`
+ `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]`
+ `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]`

**Hedef.** Dış yüzey üç farklı vektörde sertleştirilir: network capture
event redaction (M13), in-container CDP port (M14b), Makefile shell quoting
(U4-U12). Üç kalem ortak iterasyona alınır çünkü hepsi "external surface
hardening" kategorisinde ve test paterni paralel (W13-5 + W13-6 deseninin
karışımı).

**Etkilenen yollar.**

+ M13: [network.py](../../executor/flows/playwright/runtime_capture/network.py)
  + W13-6 deseninin tekrarı
+ M14b: VS Code launch wrapper veya
  [executor/host.py](../../executor/host.py) argv builder; default
  `--remote-debugging-port=0` veya explicit opt-in env var
+ U4-U12: [Makefile](../../Makefile) `sim-target`/`sim-run` recipe'leri;
  W13-5 H3 dev-lan recipe-fix deseni (`$${VAR:-default}` quoting)

**Test paterni.**

+ M13: yeni architecture gate `tests/architecture/test_network_uri_summary_redaction.py`
  (W13-6 mirror), parametrize regression 5 secret tipi × 2 alan (path, summary)
+ M14b: arch gate `tests/architecture/test_cdp_port_default.py`
+ U4-U12: arch gate `tests/architecture/test_makefile_sim_quoting.py`
  (W13-5'in `test_makefile_dev_recipes.py` deseni)

**Exit kriterleri.**

+ 3 yeni architecture gate (`tests/architecture/` 105 → 108)
+ M13 production diff küçük (factory-internal redaction zincirinin doğal
  uzantısı)
+ M14b posture decision iterasyon başında verilir (default-disabled vs
  explicit opt-in)
+ Makefile diff tek dosya, recipe-level

### W14-4 scope — Doğruluk + concurrency

**Pull source.**

+ `[FOLLOWUP analysis-jobs-race]` (CRITICAL)
+ `[FOLLOWUP evidence-event-kind-raw-context-invariant]` (HIGH)

**Hedef.**

`analysis-jobs-race`: `complete_analysis_job` `with_for_update()` lock'undan
yoksun; `cancel_analysis_job` lock kullanıyor. Race window W13-4.4'te
belgelendi (concurrent cancel + complete son state'i belirsiz bırakıyor).
W14-4'ün ilk yarısı bu lock asimetrisini W13-3 örüntüsünde (cancellation
two-phase finalize) kapatır.

`evidence-event-kind-raw-context-invariant`: `EvidenceEvent.kind` ↔
`raw_context.event_class` eşleşmesi Pydantic'te validate edilmiyor;
`kind="network"` + `event_class="file"` sessizce kabul ediliyor. W14-4'ün
ikinci yarısı Pydantic v2 `model_validator` ekler.

**Etkilenen yollar.**

+ [crud_ops/analysis_jobs/lifecycle.py](../../appcore/storage/crud_ops/analysis_jobs/lifecycle.py)
  — `complete_analysis_job` lock symmetry
+ [packages/analysis_contracts/contracts.py](../../packages/analysis_contracts/contracts.py)
  (lines 242, 266) — EvidenceEvent model validator
+ [packages/analysis_engine/rules/_common.py](../../packages/analysis_engine/rules/_common.py)
  (lines 37-50) — raw_context accessor invariant assumption

**Test paterni.**

+ analysis-jobs-race: `tests/platform/storage/test_analysis_jobs_concurrency.py`'ye
  complete+cancel paralel oturum case'i (W13-3'ün cancel race deseni)
+ evidence-event-kind: RED stub adı planlandı
  (`test_evidence_event_rejects_kind_event_class_mismatch`); stub henüz
  yazılmadı. Pydantic
  model_validator + 4 kind variant × bozuk eşleşme = 16 reject case

**Exit kriterleri.**

+ 2 yeni behavioral test dosyası (+ ~18 case)
+ `[FOLLOWUP analysis-jobs-race]` slim canonical'da kapalı işaretlenir;
  W13-4.4 dokümantasyonu güncellenir
+ `[FOLLOWUP evidence-event-kind-raw-context-invariant]` kapalı;
  raw_context discriminator parity için UI follow-up
  (`[FOLLOWUP ui-raw-context-discriminator-parity]`) W15'e bırakılır

### W14-5 scope — Logger consolidation + run-ID stamping (§11.10 GOAL devamı)

**Pull source.**

+ `[§11.10 GOAL]` `extrace.executor.*` logger consolidation
+ `[§11.10 GOAL]` Run-ID stamping
+ `[FOLLOWUP codex-automation-5]` — executor runtime fingerprint in
  automation output (run-ID stamping ile sibling tema; aynı PR ailesinde
  çekilir, version/build/commit emit ve correlation kimliği aynı kapakta
  toplanır)

Stable ID önerisi: `[GOAL w14-logger-consolidation]` ve `[GOAL w14-run-id-stamping]`
— ilk pull'da konfirme. `codex-automation-5` mevcut stable ID'sini korur.

**Hedef.** Executor logger initialization + emit pattern'leri worker
thread'lerde tutarsız; aynı çalışma için emit edilen log satırları farklı
formatlarda. Stable `EXTRACE_EPOCH_RUN_ID` executor çıktıları boyunca
propagate olmuyor. Otomasyon çıktısı, üzerine geldiği executor build'in
parmak izini (version/build/commit) taşımıyor — operatör bir scan raporuna
baktığında hangi executor revizyonunun ürettiğini bilemiyor. Üç sorun
ortak çatı altında çözülür: logger consolidation altyapıyı kurar, run-ID
stamping işaretleri propagate eder, runtime fingerprint emit ise statik
build metadata'yı aynı emit pipeline'ı üzerinden çıktıya bağlar. (Bu durum
aynı zamanda `[FOLLOWUP codex-2026-05-10-M5-epoch-docker-exec-propagation]`'in
kök sebebi — W14-5 yan ürünü olarak M5 doğal şekilde çekilebilir; aksi halde
M5 W15'e düşer.)

**Etkilenen yollar.**

+ `appcore/logging.py` (varsa) veya logger init lokasyonları
+ [executor/host.py](../../executor/host.py), executor entry points
+ [workflows/marketplace/analysis_service.py](../../workflows/marketplace/analysis_service.py)
  daemon thread
+ ADR: yeni `documents/decision-records/ADR-00XX-logger-consolidation.md`

**Adımlar.**

1. ADR taslağı: logger ownership, named logger taxonomy, structured field
   sözleşmesi (run_id, epoch, thread, executor_fingerprint)
2. Logger consolidation implementation
3. Run-ID stamping: `EXTRACE_EPOCH_RUN_ID` her log record'a structured
   field olarak
4. Executor runtime fingerprint emit (`codex-automation-5`): otomasyon
   çıktısının üst düzey emit boundary'sinde version/build/commit
   parmak izi structured field olarak basılır; aynı emit pipeline
5. Yeni architecture gate `tests/architecture/test_logger_consolidation.py`:
   her executor entry point'i merkezi factory'den logger almalı; runtime
   fingerprint emit boundary'si structured field içeriği üzerinde gate

**Bağımlılık.** Run-ID stamping logger consolidation'a bağımlı; sıra:
consolidation → stamping → fingerprint. Üç sub-iteration tek W14-5 PR
ailesinde gelir (W13-7'nin sub-commit deseni).

**Exit kriterleri.**

+ ADR landed
+ Architecture gate green
+ `codex-automation-5` POST_POC_BACKLOG'da kapalı işaretlenir
+ M5 (`epoch-docker-exec-propagation`) doğal yan ürün olarak çekilir;
  çekilmezse W15 backlog'a düşer (slim canonical'da işaretlenir)

### W14-6 scope — W8-W12 regression lock-in umbrella (§11.10 GOAL devamı)

**Pull source.**

+ `[FOLLOWUP arch-gate-executor-control-outbound]`
+ `[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]`
+ `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]`

**Hedef.** W8-W12 boyunca eklenen güvenlik invariant'ları (absolute binary
paths, executor control boundary, redaction patterns) için architecture
gate matrisi tamamlanmamış. W13-9'un `.env` gitignore gate'i bu boşluğun
küçük bir dilimini doldurdu. W14-6 umbrella'sı kalan gate'leri toplar.

**Etkilenen yollar.**

+ [tests/architecture/test_absolute_binary_paths.py](../../tests/architecture/test_absolute_binary_paths.py)
  — variable-indirect command head coverage extension
+ Yeni: `tests/architecture/test_executor_control_outbound.py`
+ Yeni: `tests/architecture/test_bare_binary_pragma_ratchet.py`
+ [executor/binary_paths.py](../../executor/binary_paths.py) — allowlist
  genişletme veya pragma temizleme

**Test paterni.** Tüm gate'ler AST-tabanlı arch gate; W8-1/W8-3/W8-6 gate
desenleri (parse, traverse, assert).

**Exit kriterleri.**

+ 3 yeni arch gate (toplam `tests/architecture/` 108 → 111+)
+ Pragma sayımı strict azalır; ratchet test mevcut sayıdan büyük pragma
  kabul etmez
+ W8-W12 boyunca eklenen security invariant'ların hepsi en az bir gate
  ile korunur

## Excluded From W14 (W15+'a düşer)

+ **Codex M-class W15'e:** M5 (W14-5 yan ürünü değilse), M10, M12, U1-U3,
  U6, U8, I2, I4
+ **Posture decision:** `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]`
  — W14 öncesi ADR oturumu, plan değil karar
+ **Watching items:** `[FOLLOWUP planner-selection-readability-audit]`,
  `[FOLLOWUP attribution-links-build-evidence-bundle-density]`,
  `[FOLLOWUP execute-attempt-rebloat-watch]`,
  `[FOLLOWUP dispatch-execution-rebloat-watch]` —
  LoC bütçesi aşılana kadar dokunma
+ **UI follow-up'ları:** `[FOLLOWUP ui-raw-context-discriminator-parity]`,
  `[FOLLOWUP vsix-integrity-in-activation-report]` → W14-4'te backend
  invariant landed olunca UI parity ayrı pull
+ **Hijyen quick wins (opportunistic pull-as-found):**
  `[CLEANUP env-example-extrace-vars]`, `[CLEANUP postgres-version-fact-drift]`,
  `[CLEANUP adr-0007-runbook-wording-drift]`,
  `[CLEANUP pre-commit-python-version-alignment]`,
  `[FOLLOWUP adr-0002-vsix-extraction-section-missing]`,
  `[CLEANUP report-builder-naming]`,
  `[CLEANUP monitor-runtime-naming-overlap]`
+ **Automation/verification follow-up'ları (bilinçli W15+ deferral):**
  + `[FOLLOWUP codex-automation-6]` (UI failure taxonomy for operator
    clarity) → bağımsız UI/ops tema; W14'ün Codex M-class + §11.10 GOAL
    temalarıyla örtüşmüyor.
  + `[FOLLOWUP capability-verification-gap]` (close remaining debug /
    verification capability gaps) → triyajda `NEEDS-DESIGN` etiketlendi;
    W14-6'nın AST-tabanlı arch gate ritmine girmiyor, design pass'i
    önce gerekiyor.
  + (`[FOLLOWUP codex-automation-5]` ise W14-5'e katlandı — yukarıdaki
    sub-iter scope bloğuna bakın.)
+ **Triyajda kapalı bulunan slim-canonical drift** (W13 close-out PR'ında
  veya küçük bir hijyen commit'inde sweep edilir): `ui-v3-9`, `ui-v3-14`,
  `report-invariants-runtime-evidence-drift`, `planner-executor-action-enum`,
  `activation-discovery-strategy-outcome-detail`,
  `silent-scenario-dropout-regression`

## Test Baseline (target deltas)

W13 final/post-merge bar (giriş referansı): `make test-local` 1551 passed /
10 skipped / 8 deselected; `make test-security` 215 passed;
`tests/architecture/` 117 passed.

W14 hedefi (tahminî, iterasyon sonu kümülatif):

+ `make test-local`: 1551 → ~1575-1585 (+24-34 yeni case)
+ `make test-security`: 215 → ~225-230 (M-class regression + dropout fixture)
+ `tests/architecture/`: 117 → ~125-127 (yeni 8-10 arch gate)

## Per-Item Detail

Pattern from `W13-test-expansion-observability.md`: each `W14-N` block
records landing date, commit hashes, module locations new/modified, LoC
changes, tests added/modified at real module import paths, live-scan
validation if applicable. **Blocks added at first pull** — currently empty.

## W13 Lessons Learned (carry-forward)

Three operational lessons to keep in mind when planning W14 splits:

1. **`§11.10 GOAL` umbrella'ları discovery-first çekilmeli.** W13-8 (benign
   silence fixture 3→5) ilk grep'te zero match döndüğünde scope-out
   düşünüldü; sonraki Explore W13-8'in pull edilebilir olduğunu kanıtladı.
   W14-5'in logger consolidation'ı için aynı discipline: önce mevcut
   `getLogger("extrace*")` / `logging.getLogger` çağrılarını grep'le,
   sonra ADR taslağı.
2. **Acceptance-bar test surface birikiyor — W14 close-out planı erken
   yazılmalı.** W13 close-out PR'ı 10 sub-iter biriktirip W12 PR #18
   cut-off pattern'ini izledi. W14'ün 6 sub-iter'i için cut-off kriterleri
   önceden netleşmeli (her sub-iter GREEN olunca close-out adayı olarak
   işaretle, scope drift erken yakala).
3. **CRITICAL kalemler scope'u genişletebilir.** W14-1 (`[BUG
   scenario-dropout-upstream-root-cause]`) BLOCKER araştırma; eğer kök
   neden non-lokal çıkarsa W14-2..W14-6 ertelenebilir. W14-1 sonunda
   scope revize/onay kapısı var.

## References

+ Plan source: [REFACTOR_OPTIMIZATION.md §12](../REFACTOR_OPTIMIZATION.md).
+ Backlog: [POST_POC_BACKLOG.md](../POST_POC_BACKLOG.md) — `[FOLLOWUP …]`
  items + `W14 Pull-Forward Acceptance Bar` tablosu.
+ Predecessor lane (closed; stable-ID evidence only):
  [W13-test-expansion-observability.md](W13-test-expansion-observability.md)
  (stable IDs `W13-1`..`W13-13`).
+ Older predecessor lanes (frozen, stable-ID-only):
  [W12-executor-subpackaging.md](W12-executor-subpackaging.md)
  (`W12-0`..`W12-5`),
  [W11-monitor-lifecycle.md](W11-monitor-lifecycle.md)
  (`W11-1`..`W11-8`),
  [W8-security.md](W8-security.md) (`W8-1`..`W8-9`).
+ Architecture rules entrypoint: `AGENTS.md` (root).
+ Task routing: `documents/AGENT_CONTEXT.md`.
+ W14 planning artifact (out-of-tree, oturum referansı):
  `~/.claude/plans/week-13-ve-backlog-smooth-crab.md`.
