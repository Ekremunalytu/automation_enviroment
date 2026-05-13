# W14 — Codex M-class Acceptance + Observability (Active Work Tracker)

`Last Updated: 2026-05-13 (W14 active; W14-1 pulled; W14-2/W14-3/W14-4 closed; week14 branch cut from main at 69251f1; W13 close-out PR #20 week13 -> main merged via 772deb3)`
`Phase: W14 active (W14-4 closed 2026-05-13 — analysis-jobs-race lock symmetry + evidence-event-kind invariant)`
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
| **W14-2** | `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` (extension-controlled `ts` field guard sız `datetime.fromtimestamp()`'a giriyor; OverflowError DoS vector) | `[security-detection]` | **closed** `2026-05-13` |
| **W14-2** | `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` (`_build_report_messages()` `int(automation_health.get(...))` ValueError'a açık) | `[security-detection]` | **closed** `2026-05-13` |
| **W14-3** | `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` (network capture event'lerinin `path` + `summary` alanları secret sızdırıyor; W12-5 gate sadece `*_body_preview`'i kapsıyor; W13-6 factory-internal redaction deseninin tekrarı) | `[security-detection]` `[executor-runtime]` | **closed** `2026-05-13` |
| **W14-3** | `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` (VS Code `--remote-debugging-port=9222` auth'suz default-on, container'dan erişilebilir) | `[executor-runtime]` `[security-detection]` | **closed** `2026-05-13` — posture: default-disabled + opt-in via `EXECUTOR_CDP_PORT` env var |
| **W14-3** | `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` (`Makefile` `sim-target`/`sim-run` `$(TARGET)`/`$(SCENARIO)` tırnaksız; shell injection riski; W13-5 dev-lan recipe-fix deseninin tekrarı) | `[security-detection]` | **closed** `2026-05-13` |
| **W14-4** | `[FOLLOWUP analysis-jobs-race]` (`complete_analysis_job` ve `fail_analysis_job` `with_for_update()` lock'undan yoksundu; `cancel_analysis_job` lock var; W13-4.4'te race window dokümante edildi) | `[platform-storage]` `[executor-runtime]` | **closed** `2026-05-13` |
| **W14-4** | `[FOLLOWUP evidence-event-kind-raw-context-invariant]` (`EvidenceEvent.kind` ↔ `raw_context.event_class` eşleşmesi Pydantic'te validate edilmiyordu; closed 9-kind allowlist + `@model_validator(mode='after')`) | `[security-detection]` `[contracts]` | **closed** `2026-05-13` |
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

**Actual cumulative bar (post-W14-4):**

| Suite | W13 baseline | W14-1 | W14-2 | W14-3 | W14-4 | Current |
|---|---|---|---|---|---|---|
| `make test-security` | 215 | 222 (+7 dropout repro) | 269 (+47 M4-M7 + M11) | 279 (+10 M13) | 279 (lane subset stable; W14-4 surface lands in `tests/platform/storage/` + `tests/platform/contracts/`) | **279** |
| `tests/architecture/` | 117 | 117 (W14-1 updated `test_readme_phase_pointer` in place) | 121 (+4: 2 ts-guard + 2 int-guard) | 131 (+10: 2 uri redaction + 4 cdp default + 4 makefile quoting) | 135 (+4: 2 lock-symmetry + 2 kind-invariant) | **135** |
| Broad regression suite (security + arch + executor + workflows/marketplace) | — | — | — | 1106 | 1110 (+4 arch gates; lock + concurrency cases live under `tests/platform/storage/`) | **1110 passed / 7 skipped / 4 deselected** (sıfır regresyon) |
| `make test-local` (full sweep) | 1551 | — | — | — | — | **1701 passed / 10 skipped / 8 deselected / 1 xfailed** |

W14-5..W14-6 dilimleri hedefi karşılayacak; `make test-security` hedefi
(~225-230) şimdiden geçilmiş durumda, kalan iter'ler
`tests/architecture/` hedefini W14-6 umbrella'sıyla genişletecek.

## Per-Item Detail

Pattern from `W13-test-expansion-observability.md`: each `W14-N` block
records landing date, commit hashes, module locations new/modified, LoC
changes, tests added/modified at real module import paths, live-scan
validation if applicable. Blocks are added at first pull.

### W14-1 — `[BUG scenario-dropout-upstream-root-cause]` (BLOCKER → HIGH downgrade)

**Pulled.** `2026-05-13` on `week14` (cut from `main` at `69251f1`).

**Outcome.** **Downgraded BLOCKER → HIGH** with stochastic-bound rationale.
The last-mile conservation guard
(`executor/flows/playwright/monitor/scenario_accountant.py:392-438`,
`_validate_scenario_conservation`) is the deterministic fix-of-record:
every entry in `requested_scenarios` that is missing from
`scenarios_run | failed_scenarios | skipped_scenarios` is appended to
`skipped_scenarios` with `reason_code='unaccounted_dropout'` so the W7
§10.7 honesty invariant holds end-to-end. Upstream emit-site work
(planner / `stimulus_passes` / `dispatch._normalize_execution_result`
scenario-level trace + reason-code propagation) is intentionally
deferred to `[FOLLOWUP scenario-accountant-conservation-split]` per the
W14-1 scope lock ("kök neden tespiti + refactor karışmamalı"), and
becomes a W15+ candidate.

**Sub-commits (self-stamped post-landing).**

| Sub-commit | Theme | SHA |
|---|---|---|
| 1 | Branch cut + tracker activation (header sweep across `CLAUDE.md`, `REFACTOR_STATUS.md`, this file) | `34aeeb2` |
| 2 | Repro fixture + README phase pointer gate + BUG downgrade + Per-Item Detail close evidence | `0c8bd02` |
| 3 | Self-stamp sub-commits 1 + 2 SHAs in this table | (this commit) |

**Module locations.**

+ Test surface added: [`tests/security/test_scenario_dropout_repro.py`](../../tests/security/test_scenario_dropout_repro.py)
  — 7 cases (5-row parametrize matrix + idempotency pin + finalize-time
  conservation pin). Imports at real module paths
  (`executor.flows.playwright.monitor.scenario_accountant`,
  `executor.flows.playwright.monitor.records`,
  `executor.flows.playwright.monitor.types`).
+ Architecture gate updated: [`tests/architecture/test_readme_phase_pointer.py`](../../tests/architecture/test_readme_phase_pointer.py)
  — `"W14 staging"` token expectation flipped to `"W14 active"` for the
  W14-1 pull; W13 close-out tokens (`PR #20`, `week13 -> main`, `772deb3`)
  preserved in the banner so the close-out fact does not drift while W14
  iterates.
+ Slim canonical sweep: [`documents/REFACTOR_STATUS.md`](../REFACTOR_STATUS.md),
  [`documents/POST_POC_BACKLOG.md`](../POST_POC_BACKLOG.md),
  [`CLAUDE.md`](../../CLAUDE.md), [`README.md`](../../README.md) — phase
  banner + W14-1 status line updated.

**Test deltas.** `make test-security` 215 → 222 (`+7` repro fixture
cases). `tests/architecture/` 117 (gate count unchanged; existing
README-phase gate updated in place rather than replaced).

**Production-code touched.** None — W14-1 is triage-only by scope lock.
The 648-LoC `scenario_accountant.py` refactor and any upstream
trace-instrumentation belong to the deferred follow-up
`[FOLLOWUP scenario-accountant-conservation-split]`.

**Repro matrix coverage** (`tests/security/test_scenario_dropout_repro.py::_DROPOUT_VECTORS`):

| Vector ID | Requested | Ran | Failed | Explicit skip codes | Expected `unaccounted_dropout` |
|---|---|---|---|---|---|
| `vec_ms_python_python` | 5 | 3 | 0 | — | `{debug_session, refactor_workflow}` |
| `vec_stimulus_collapse` | 3 | 0 | 0 | — | `{x1, x2, x3}` |
| `vec_all_accounted` | 2 | 2 | 0 | — | `∅` |
| `vec_all_explicit_skip` | 2 | 0 | 0 | `harness_unavailable` ×2 | `∅` |
| `vec_partial_failed` | 3 | 1 | 1 | `precondition_unmet` ×1 | `∅` |

**Plus** an idempotency case (`second record_execution_result must not
double-append`) and a finalize-time case (`finalize_running_scenarios`
also invokes the conservation guard).

**Future work hand-off.** `[FOLLOWUP scenario-accountant-conservation-split]`
in `POST_POC_BACKLOG.md` Contracts/Reports/Detection section now carries
the upstream emit-site work (planner / stimulus / dispatch scenario-level
trace) as a separate W15+ candidate. The W14-1 stochastic-bound
conclusion (`upstream root cause may vary by extension class, but the
last-mile guard always catches the dropout`) is the rationale for
declining to inline that refactor here.

**Production validation.** UI-launched scan
`activation_report_ms-python.python-2026.5.2026051301-c71107e2ff84.json`
(`2026-05-13` 15:36, post-W14-3 working tree) provides live-scan parity
for the `vec_ms_python_python` repro vector: 5 requested scenarios
(`coding_session`, `project_exploration`, `debug_session`,
`terminal_usage`, `refactor_workflow`) → 3 ran (`scenario_traces` filled
for the first, second, fourth) → 2 `unaccounted_dropout` records for
`debug_session` and `refactor_workflow` with the exact `reason_code` +
`detail` strings the fixture pins. This is the production-ground-truth
match that converted the BLOCKER triage into a downgrade-with-evidence
rather than a downgrade-by-conjecture.

The scan also surfaced a separate pre-existing finalize-time field-sync
drift (`target_extension_id`, `monitoring_start` / `monitoring_end`,
`scenarios_run`, `harness_handshake_required` all serialized as `null`
despite the underlying evidence being present). Hand-off:
`[FOLLOWUP report-finalize-top-level-field-sync-drift]` in
`POST_POC_BACKLOG.md` Contracts/Reports/Detection; W15+ candidate; not
a W14 regression (pre-W14 W13 close-out smoke `9d327b30b60f` exhibits
the same nulls).

### W14-2 — Codex M-class input validation cluster (M4-M7 + M11)

**Pulled.** `2026-05-13` on `week14`.

**Outcome.** **Closed.** Two Codex audit M-class items landed under a
single bundled pull, both following the W13-6 parametrize-regression +
arch-gate pattern:

+ **M4 + M7 (output ts range validation)** — `_coerce_safe_epoch_s()`
  added as the single chokepoint in
  `executor/flows/playwright/signals/output.py`. The helper rejects
  ``inf`` / ``NaN`` and bounds the epoch within
  ``[_MIN_SAFE_EPOCH_S, _MAX_SAFE_EPOCH_S]`` (1970-01-01 .. 3000-01-01,
  inside every platform's ``time_t`` ceiling). ``_format_epoch_ms`` now
  routes every extension-controlled ``ts`` through it before invoking
  ``datetime.fromtimestamp()``. Both consuming sites
  (``parse_output_signal_events`` harness-marker JSON and
  ``read_output_channel_logs`` VS Code 1.105+ file-backed) inherit the
  guard at the single chokepoint.
+ **M11 (report-message malformed types)** — `_safe_int_coerce()`
  defensive helper added to `workflows/marketplace/analysis_reports.py`;
  `build_report_messages` now coerces
  ``automation_health.get("target_activation_count")`` through it,
  defaulting to ``0`` on every coercion failure. The helper has a final
  ``except (TypeError, ValueError, OverflowError)`` net so list / dict /
  custom-class inputs cannot escape with a raised exception.

**Sub-commits (self-stamped post-landing).**

| Sub-commit | Theme | SHA |
|---|---|---|
| 1 | M4-M7 + M11 production patches, behavioral regression cases (51 cases), 2 AST architecture gates, and tracker / backlog close-out | `bde17be` |
| 2 | Self-stamp sub-commit 1 SHA in this table | (this commit) |

**Module locations.**

+ Production diff:
  + [`executor/flows/playwright/signals/output.py`](../../executor/flows/playwright/signals/output.py)
    — added ``math`` import, ``_MIN_SAFE_EPOCH_S`` / ``_MAX_SAFE_EPOCH_S``
    module constants, ``_coerce_safe_epoch_s()`` helper, and routed
    ``_format_epoch_ms`` through the helper. Diff ~25 net LoC.
  + [`workflows/marketplace/analysis_reports.py`](../../workflows/marketplace/analysis_reports.py)
    — added ``typing.Any`` import, ``_safe_int_coerce()`` helper, and
    rewrote the ``target_count`` cast in ``build_report_messages``. Diff
    ~25 net LoC.
+ Behavioral regression coverage:
  + [`tests/security/test_output_signal_ts_range.py`](../../tests/security/test_output_signal_ts_range.py)
    — 18 cases (coercion matrix × 9, ``_format_epoch_ms`` adversarial-ts
    matrix × 6, plus alignment / idempotency / boundary pins).
  + [`tests/security/test_report_messages_malformed_types.py`](../../tests/security/test_report_messages_malformed_types.py)
    — 29 cases (``_safe_int_coerce`` matrix × 20,
    ``build_report_messages`` adversarial-target-count matrix × 6, plus
    non-zero-default and valid-target preservation pins).
+ Architecture gates (AST, modeled on W13-6
  ``test_arguments_preview_redaction.py``):
  + [`tests/architecture/test_output_signal_ts_guard.py`](../../tests/architecture/test_output_signal_ts_guard.py)
    — 2 cases (body invariant on ``_coerce_safe_epoch_s`` + routing gate
    on every ``datetime.fromtimestamp(...)`` call site).
  + [`tests/architecture/test_report_messages_int_guard.py`](../../tests/architecture/test_report_messages_int_guard.py)
    — 2 cases (exception-trio catch on ``_safe_int_coerce`` body + no
    raw ``int(automation_health.get(...))`` patterns inside
    ``build_report_messages``).

**Test deltas.** `make test-security` 222 → 269 (+47 behavioral cases:
+18 M4-M7 + +29 M11). `tests/architecture/` 117 → 121 (+4 AST cases
spread across 2 new gate modules).

**No follow-up deferral.** Both audit items collapse to closed in
`POST_POC_BACKLOG.md` — no W15+ remnant.

### W14-3 — Codex M-class external surface hardening (M13 + M14b + U4-U12)

**Pulled.** `2026-05-13` on `week14`.

**Outcome.** **Closed.** Three Codex audit M-class items landed under
a single bundled pull. All three target adversary-reachable external
surfaces (network capture report fields, the in-container CDP socket,
operator-supplied Makefile variables) and follow the W12-5 / W13-6 /
W13-5 patterns established by earlier audit pulls.

+ **M13 (network URI/summary redaction)** — `NetworkEvent.path` and
  `NetworkEvent.summary` now route through ``redact_secrets()`` at the
  same chokepoint that already covers ``*_body_preview`` (W12-5) and
  ``arguments_preview`` (W13-6). Production diff is a 2-line redaction
  funnel inside ``parse_tshark_event_line`` at
  `executor/flows/playwright/runtime_capture/network.py:99-122`.
+ **M14b (CDP port default-disabled)** — posture decision: **opt-in via
  `EXECUTOR_CDP_PORT` env var**. Formalized in
  [`ADR 0009: CDP Default-Disabled in the Executor Container`](../adrs/0009-cdp-default-disabled.md)
  as the container-internal complement to ADR 0007 §4 (which already
  gated host→container exposure via the `debug` Compose profile).
  ``launch_vscode.sh``, ``start.sh``, and ``docker-compose.yml`` all
  default the env var to empty; the launch wrapper appends
  ``--remote-debugging-port=...`` to the ``code`` invocation only when
  the value is non-empty. The ``make up-debug`` Makefile lane now
  explicitly sets ``EXECUTOR_CDP_PORT=9222`` before invoking compose,
  so the debug profile keeps the previous UX while routine ``make up``
  boots stay CDP-closed.
+ **U4-U12 (Makefile sim-target / sim-run shell quoting)** — both
  recipes now (a) validate operator-supplied variables against strict
  character classes (``[A-Za-z0-9._-]+`` for TARGET,
  ``[A-Za-z0-9_]+`` for SCENARIO, ``[A-Za-z0-9./_-]+`` for TRIGGERS)
  before any expansion reaches the shell, and (b) double-quote every
  Make-variable interpolation inside the ``docker exec`` command line.

**Sub-commits (self-stamped post-landing).**

| Sub-commit | Theme | SHA |
|---|---|---|
| 1 | M13 + M14b + U4-U12 production patches, 10 behavioral regression cases, 10 content/AST architecture gate cases, and tracker / backlog close-out | `941250d` |
| 2 | Self-stamp sub-commit 1 SHA in this table | (this commit) |

**Module locations.**

+ Production diff:
  + [`executor/flows/playwright/runtime_capture/network.py`](../../executor/flows/playwright/runtime_capture/network.py)
    — added `summary_raw` / `redacted_path` local variables sourced
    from ``redact_secrets()`` calls; ``NetworkEvent`` constructor now
    sources both fields from those locals. Diff ~12 net LoC.
  + [`executor/container/launch_vscode.sh`](../../executor/container/launch_vscode.sh)
    — `CDP_PORT` defaults to empty; the ``code`` invocation builds a
    `CDP_FLAG=()` array that is non-empty only when `CDP_PORT` is set.
    Diff ~14 net LoC.
  + [`executor/container/start.sh`](../../executor/container/start.sh)
    — same empty default; CDP banner conditionally reports
    ``disabled (set EXECUTOR_CDP_PORT to opt in)``. Diff ~6 net LoC.
  + [`docker-compose.yml`](../../docker-compose.yml) — executor
    service `EXECUTOR_CDP_PORT` env source defaults to empty (the
    `executor-cdp` debug-profile sidecar keeps its own 9222 fallback
    because the Makefile lane explicitly sets the env var). Diff ~6
    net LoC.
  + [`Makefile`](../../Makefile) — `up-debug` recipe exports
    `EXECUTOR_CDP_PORT=9222`; `sim-target` and `sim-run` recipes carry
    new validation + quoted expansion. Diff ~22 net LoC.
+ Behavioral regression coverage:
  + [`tests/security/test_network_uri_summary_redaction.py`](../../tests/security/test_network_uri_summary_redaction.py)
    — 10 cases (3-row × 2-field × `_SECRET_CLASSES` parametrize matrix
    covering `aws` / `api_key` / `db_url` URLs through both `path` and
    `summary`, plus a bearer-in-info-column case, multi-secret URI,
    and 2 preserve / non-secret pins).
+ Architecture gates:
  + [`tests/architecture/test_network_uri_summary_redaction.py`](../../tests/architecture/test_network_uri_summary_redaction.py)
    — 2 AST cases (module imports `redact_secrets` invariant + every
    `path=` / `summary=` keyword routes through the redactor).
  + [`tests/architecture/test_cdp_port_default.py`](../../tests/architecture/test_cdp_port_default.py)
    — 4 content cases (launch script empty default + conditional CDP
    flag append + start script mirror + docker-compose empty default).
  + [`tests/architecture/test_makefile_sim_quoting.py`](../../tests/architecture/test_makefile_sim_quoting.py)
    — 4 content cases (sim-target validation + sim-target quoting +
    sim-run validation + sim-run quoting).

**Test deltas.** `make test-security` 269 → 279 (+10 M13 behavioral
cases). `tests/architecture/` 121 → 131 (+10 cases across 3 new gate
modules: 2 + 4 + 4).

**No follow-up deferral.** All three audit items collapse to closed in
`POST_POC_BACKLOG.md` — no W15+ remnant.

### W14-4 — analysis-jobs-race lock symmetry + evidence-event-kind invariant

**Pulled.** `2026-05-13` on `week14`.

**Outcome.** **Closed.** Two correctness items landed under a single
bundled pull. Both follow the W13-3 / W13-6 invariant-and-test pattern
established by earlier audit pulls.

+ **`[FOLLOWUP analysis-jobs-race]`** (CRITICAL) — `complete_analysis_job`
  and `fail_analysis_job` now acquire `select(...).with_for_update()`
  before any state check (mirroring the W13-3 lock discipline at
  `lifecycle.py:128` / `:181`) and gate against the full
  `_TERMINAL_JOB_STATUSES` frozenset in addition to the existing
  `cancelling` guard. Pre-W14-4 a concurrent loser could pass its
  cached snapshot status check and silently overwrite the winner's
  terminal write; post-fix the second writer reads the new status
  under the lock and raises `JobNotCancellableError`. The pre-existing
  `test_cancel_vs_complete_concurrent_write_final_state_is_consistent`
  test docstring's "future hardening pass" caveat (lines 183-195) is
  removed and the assertion tightened to require exactly one winner.
+ **`[FOLLOWUP evidence-event-kind-raw-context-invariant]`** (HIGH) —
  `EvidenceEvent` now carries a `@model_validator(mode='after')`
  decorated method that enforces a closed 9-kind allowlist
  (`_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS` in
  [packages/analysis_contracts/contracts.py](../../packages/analysis_contracts/contracts.py)).
  The allowlist contains the 7 strict 1:1 producer kinds plus 2 alias
  kinds (`extension_host` → `activation`, `log` → `scenario`) that
  reuse an existing raw_context variant. Pre-W14-4 a producer drift
  like `kind="network"` + `event_class="file"` was silently accepted
  and downstream rule helpers in
  `packages/analysis_engine/rules/_common.py` masked the mismatch via
  getattr defaults, producing false-negative detections. The closed
  allowlist also surfaces unrecognized kinds so a future producer
  cannot drift past ingest.

**Sub-commits (self-stamped post-landing).**

| Sub-commit | Theme | SHA |
|---|---|---|
| 1 | analysis-jobs-race lock + terminal guard on `complete_analysis_job` / `fail_analysis_job`; `EvidenceEvent` kind↔event_class invariant + `_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS` allowlist; 65 behavioral cases (9 positive + 54 mismatch + 1 unknown-kind + 1 default-rc edge); 3 new concurrency cases (`complete-vs-fail`, `double-complete`, `double-fail`); existing concurrency-test docstring tightening + exactly-one-winner assertion; 2 new AST architecture gates; fixture drift repair (file-kind events with missing raw_context in 3 malicious-canary activation_report.json + inline test_rule_attribution / test_router fixtures); tracker / backlog / status / CLAUDE / AGENTS sweep | `03b32bc` |
| 2 | Self-stamp sub-commit 1 SHA in this table | (this commit) |

**Module locations.**

+ Production diff:
  + [appcore/storage/crud_ops/analysis_jobs/lifecycle.py](../../appcore/storage/crud_ops/analysis_jobs/lifecycle.py)
    — `complete_analysis_job` (`:314`) and `fail_analysis_job`
    (`:255`) both rewritten to acquire `with_for_update()` first and
    raise on `_TERMINAL_JOB_STATUSES`. Diff ~30 net LoC.
  + [packages/analysis_contracts/contracts.py](../../packages/analysis_contracts/contracts.py)
    — added `collections.abc.Mapping` import, the
    `_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS` module-level constant, and
    the `EvidenceEvent._kind_matches_raw_context_event_class`
    `@model_validator(mode='after')`. Diff ~45 net LoC.
+ Behavioral regression coverage:
  + [tests/platform/contracts/test_raw_context_discriminated.py](../../tests/platform/contracts/test_raw_context_discriminated.py)
    — `_evidence_payload` helper extended with a `kind` parameter; all
    existing variant tests updated to pass matching `kind`; 65 new
    cases (9 positive parametrize × full allowlist + 54 mismatch
    matrix + 1 unknown-kind reject + 1 default-rc edge).
  + [tests/platform/storage/test_analysis_jobs_concurrency.py](../../tests/platform/storage/test_analysis_jobs_concurrency.py)
    — `test_cancel_vs_complete_concurrent_write_final_state_is_consistent`
    docstring + assertions tightened to require exactly one winner;
    3 new cases (`test_concurrent_complete_vs_fail_exactly_one_winner`,
    `test_double_complete_rejected_after_completed`,
    `test_double_fail_rejected_after_failed`).
+ Architecture gates:
  + [tests/architecture/test_analysis_jobs_lock_symmetry.py](../../tests/architecture/test_analysis_jobs_lock_symmetry.py)
    — 2 AST cases (lock body invariant on `complete_analysis_job` +
    `fail_analysis_job`; terminal-status guard on the same two
    functions).
  + [tests/architecture/test_evidence_event_kind_invariant.py](../../tests/architecture/test_evidence_event_kind_invariant.py)
    — 2 AST cases (allowlist key pin on
    `_EVIDENCE_EVENT_KIND_TO_EVENT_CLASS` + body invariant on the
    `@model_validator(mode='after')` decorated method inside
    `EvidenceEvent`).
+ Fixture drift repair (silent producer drift that the new invariant
  surfaced — the fixtures already had `kind` set but were missing
  `raw_context` so they defaulted to the scenario variant; the
  invariant correctly rejected the mismatched pair, and the fix is to
  populate the expected `raw_context.event_class`):
  + [extensions/malicious/t1-a1-credential-read-canary/activation_report.json](../../extensions/malicious/t1-a1-credential-read-canary/activation_report.json)
  + [extensions/malicious/t1-a4-workspace-exfil-canary/activation_report.json](../../extensions/malicious/t1-a4-workspace-exfil-canary/activation_report.json)
  + [extensions/malicious/t1-demo-runnable-canary/activation_report.json](../../extensions/malicious/t1-demo-runnable-canary/activation_report.json)
    (2 events)
  + [tests/security/rules/test_rule_attribution.py](../../tests/security/rules/test_rule_attribution.py)
    (inline `_a1_events()` + `_a4_events()` file builders)
  + [tests/workflows/activation_reports/test_router.py](../../tests/workflows/activation_reports/test_router.py)
    (`test_get_latest_activation` evidence event)

**Test deltas.** `tests/architecture/` 131 → 135 (+4: 2 lock-symmetry +
2 kind-invariant). `make test-local` lands at 1701 passed / 10 skipped
/ 8 deselected / 1 xfailed (W13 baseline 1551; W14-4 added the 65
invariant cases + 3 concurrency cases on top of W14-1/2/3 cumulative).
Broad regression suite (security + arch + executor +
workflows/marketplace) lands at 1110 passed (W14-3 baseline 1106;
delta is the 4 new arch gates — the behavioral lock + concurrency
cases live under `tests/platform/storage/` outside this subset).

**No follow-up deferral for the audit items.** Both
`[FOLLOWUP analysis-jobs-race]` and
`[FOLLOWUP evidence-event-kind-raw-context-invariant]` collapse to
closed in `POST_POC_BACKLOG.md`. The W15+ UI follow-up
`[FOLLOWUP ui-raw-context-discriminator-parity]` remains a watching
item — UI invariant parity is a separate pull now that the backend
contract is hard-pinned.

**Production validation.** `make test-security` 215 lane stays green
(the W14-4 surface lives in `tests/platform/storage/` and
`tests/platform/contracts/`, outside the fixed test-security lane).
`make test-local` 1701 green confirms the full sweep — including the
once-drifted canary fixtures that the new invariant correctly
rejected pre-fix and now ingest cleanly post-fix.

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
