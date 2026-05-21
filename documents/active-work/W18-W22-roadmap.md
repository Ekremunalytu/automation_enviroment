# W18-W22 — Capability + Otomasyon Sağlık + Coverage Promotion Roadmap (Planning Tracker)

`Last Updated: 2026-05-21 (planning state; W18 not yet entered. Source plan authored 2026-05-21 with Codex live-run validation + GPT review (3 rounds) — plan file at /Users/ekrem/.claude/plans/senden-projemdeki-capabilites-ve-mellow-valley.md. W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d. W18 entry gate: this roadmap doc opens, §16 W18 plan entry stub lands in REFACTOR_OPTIMIZATION.md, POST_POC_BACKLOG.md W18-W22 Roadmap section listed with new stable IDs reserved. Sub-iter commits land on weekN branches per W11-W17 paterni; close-out merges via weekN -> main PR.)`
`Phase: pre-W18 (planning; W18 not yet started)`
`Branch: main (no week18 branch yet — branch opens with W18-0 doc-reconcile commit per W11-W17 paterni)`
`Owner: ekrem`

> **Authored 2026-05-21** as a multi-iter (W18-W22) roadmap against
> `main` HEAD `1584c4d` (W18 candidate goals intake). Plan went through
> three review rounds: initial Codex live-run validation (live
> `ms-python.python` report `992ad028f3df` confirmed
> `automation_health.status=degraded` + `run_quality=low`) followed
> by two GPT review passes refining sub-iter boundaries, ADR paths
> (`documents/adrs/0012-...`), status enum (`healthy/degraded/inconclusive`),
> `OFFICIAL_EVENT_REGISTRY` count (29 not 24), and live-run acceptance
> gates.
>
> Stable IDs `W18-1..W22-7` are reserved by the iteration plan and
> **assigned at first pull** per the W11/W12/W13/W14/W15/W16/W17
> precedent (`REFACTOR_OPTIMIZATION.md` §15.0).

This is the canonical planning tracker for the five-iter window
W18-W22. The driving plan file under `/Users/ekrem/.claude/plans/`
carries the full review history; this tracker mirrors the **roadmap
that lands in repo dokümantasyonu** (slim canonical pattern matching
W17 tracker structure).

---

## Status (Quick Glance)

- **W18 not yet entered.** Entry gate: this roadmap doc + §16 stub +
  POST_POC_BACKLOG W18-W22 section landed.
- **Driving signal (live run, 2026-05-21)**: `ms-python.python`
  @ `992ad028f3df` reports `automation_health.status=degraded`,
  `run_quality=low`, 4 reasons (`skipped_scenarios_present`,
  `verification_gap_present`, `official_unresolved_present`,
  `harness_verification_unconfirmed_present`); coverage_summary
  `covered=7 / partial=5 / missing=6`; 21 event_attempts of which
  capability-level verified = 4.
- **Three independent problem hatları** identified (GPT review
  confirmed as separate classes):
  - **Hat-1 — Executor muhasebe bug**: `unaccounted_dropout` →
    emit-site issue, not coverage. `debug_session` +
    `refactor_workflow` drop with this reason. W16-1
    scenario-accountant emit-site fix (`01f910a`) pattern; a new or
    remaining path in the same class.
  - **Hat-2 — Harness verification gap**: declared ≠ verified.
    21 attempts → 4 capability-level verified. Independent of
    coverage matrix.
  - **Hat-3 — Coverage matrix promotion**: 6 capabilities missing
    in official track (`scm`, `settings`, `chat`, `comments`,
    `testing`, `workspace_trust`); 4 missing in heuristic track.
    Hat-1 + Hat-2 must close first; otherwise coverage promotion
    only paints over symptoms.

---

## Three-Layer Capability Model

The "capability" word maps to three distinct artefacts in the
codebase. Plan addresses Layers A and B; Layer C has no gap.

| Layer | Object | Where | Gap |
|---|---|---|---|
| **A — Activation events** | VSCode manifest `activationEvents[]` entry types | [packages/analysis_planner/event_scenario_index.py](../../packages/analysis_planner/event_scenario_index.py), parser, `executor/flows/playwright/scenarios/` | `OFFICIAL_EVENT_REGISTRY` 29 entry ([test_registry_split_regression.py:101](../../tests/platform/contracts/test_registry_split_regression.py)); 4 shallow trigger + spec doğrulama araştırması |
| **B — Capability taxonomy** | Project's 18 capability bucket | [packages/analysis_planner/capabilities.py:8-27](../../packages/analysis_planner/capabilities.py) | Heuristic 14/4 covered/missing; official 12/6 covered/missing |
| **C — Manifest capability** | VSCode `package.json` `capabilities` field (untrusted/virtual) | [appcore/contracts/schema_defs/catalog.py:12-19](../../appcore/contracts/schema_defs/catalog.py) | **Gap YOK** — spec-compliant |

---

## Sub-Iter Scope (Authored 2026-05-21)

### W18 — Heartbeat Refactor (1 iter)

W17 carry-over DESIGN-NEEDED'i kapatır. **Container hardening
W18'den çıkarıldı** — heartbeat refactor ile aynı iter'da iki
büyük değişiklik taşımak risk; W21+'a ayrı pull.

| Iter | Theme | Source / Why | Notes |
|---|---|---|---|
| W18-0 | Doc reconcile + §16 W18 plan açılışı | Pattern match W17-0 | Open this tracker section / §16 header / canonical preamble bumps. Doc-only. |
| W18-1 | Heartbeat thread relocation ADR | `[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread` (W17-3 DESIGN-NEEDED) | `documents/adrs/0012-heartbeat-thread-relocation.md`. 3 plausible refactor shapes — invariant cost trade-offs (W13-1 HMAC / W13-3 two-phase cancel / W13-13 CAS / W16-2 facade lock). KOD YOK. |
| W18-2 | Heartbeat refactor implementation | yukarıdakinin devamı | W17-2 harness'ın 3 extension point'i (parallel reset / idempotency / reset-during-finalize) yeni invariant testleriyle dolduruluyor. |
| W18-3 | Lifecycle harness extension tests | `[FOLLOWUP w17-2-harness-extension-tests]` (new) | W17-2 docstring'te enumerate edilen 3 ek test (W18-2 ile birlikte landing) |
| W18-4 | Close-out hygiene | Pattern W17-6 | Canonical preamble refresh + §16 self-stamp + tracker section freeze + PR `week18 -> main` |

**W18 acceptance**:
- Static suite tamamı yeşil (test sayıları non-binding estimate)
- Manual: `make exec-up` + `make sim-target TARGET=ms-python.python` smoke — heartbeat refactor regression yok
- W13-11 HMAC secret consume invariant'ı bozulmaz (existing test'ler PASS)

---

### W19 — Live Run Kök Neden: Dropout + Harness Verification (1 iter)

`automation_health.status` reason listesini sırayla düşürür.
**Coverage matrisine DOKUNMA.**

| Iter | Hat | Theme | Stable ID | Notes |
|---|---|---|---|---|
| W19-0 | — | Doc reconcile + §17 plan | — | Tracker section + §17 header |
| W19-1 | Hat-1 | Regression fixture (xfail/RED) | `[BUG scenario-unaccounted-dropout-regression-fixture]` (new) | `tests/executor/test_scenario_accountant_dropout_regression.py`. ms-python.python live run paterninde `unaccounted_dropout > 0` durumunu reproducer olarak yakalar (xfail/RED). W19-2 sonrası invariant: `unaccounted_dropout == 0`, xfail kalkar → PASS. |
| W19-2 | Hat-1 | `unaccounted_dropout` emit-site fix | `[BUG scenario-unaccounted-dropout-debug-refactor]` (new) | Hat: `executor/flows/playwright/stimulus/*`, `workflows/marketplace/analysis_execution.py` scenario_accountant, dispatch/result normalization. `debug_session` ve `refactor_workflow` açık `reason_code` (`skipped:dependency_missing`, `failed:trigger_timeout`, vb.) ile bitsin. |
| W19-3 | Hat-2 | Harness verification contract event-level | `[GOAL harness-verification-contract-event-level]` (new) | `executor/flows/playwright/runtime_capture/` + harness extension iletişimi. Her `event_attempt` için `confirmation_source` (`harness_nonce` / `log_record` / `none`) field'ı. **Schema impact check**: `event_attempts` öğesi Pydantic'ten geçiyor mu? UI adapter ([ui/src/lib/adapters/report.ts](../../ui/src/lib/adapters/report.ts) + [report.test.ts](../../ui/src/lib/adapters/report.test.ts)) + fixture baseline + `tests/platform/contracts/` etkilenir mi? 30 dakikalık impact-survey + gerekirse contract migration. |
| W19-4 | Hat-2 | `onDebug*` event'leri nonce confirmation | `[FOLLOWUP harness-verification-debug-events]` (new) | onDebug + alt aileleri için confirmation üretimi |
| W19-5 | Hat-2 | `onTerminalShellIntegration` + `onLanguageModelTool:*` confirmation | `[FOLLOWUP harness-verification-terminal-and-lm-tool]` (new) | Local-only confirmation marker. Confirmation üretilemeyen event için açık `blocked` / `unsupported` reason. |
| W19-6 | — | Close-out hygiene | — | PR `week19 -> main` |

**W19 acceptance (live-run-driven)**:
- **Must-pass**: yeni `make sim-target TARGET=ms-python.python` çıktısında `unaccounted_dropout == 0`
- **Must-pass**: supported harness event'lerde `harness_verification_unconfirmed` reason'ı düşer
- **Expected**: `run_quality` `low` → `medium`
- **Stretch**: `verification_gap_present` de düşer (tam düşmezse W20'ye)
- `automation_health.status` `degraded` kalabilir (`official_unresolved_present` W20'de kapanır) — bu OK

---

### W20 — Coverage Promotion Round 1: Easy Wins (1 iter)

GPT-önerdiği "kolaydan zora" gradient'in ilk dilimi. `scm` +
`settings` official promotion — scenario kodu zaten
heuristic-covered, eksik olan official-track verification.

| Iter | Theme | Stable ID | Notes |
|---|---|---|---|
| W20-0 | Doc reconcile + §18 plan + Activation event spec crosswalk | `[RESEARCH activation-event-spec-crosswalk]` (new) | **Üç kaynaklı crosswalk**: (1) resmi [VS Code Activation Events](https://code.visualstudio.com/api/references/activation-events) sayfası, (2) repo `OFFICIAL_EVENT_REGISTRY` (29 entry), (3) gerçek manifest source-of-truth (DB'deki `ExtensionActivationEvents` tablosu + indirilen VSIX'lerin `package.json` `activationEvents[]`). Çıktı: matris + gerçek gap listesi backlog'a. |
| W20-1 | `scm` official promotion | `[GOAL taxonomy-scm-official-promotion]` (new) | `capabilities.py:88` `scm: missing → covered` (official track). `git_workflow` scenario'su zaten heuristic-covered. |
| W20-2 | `settings` official promotion | `[GOAL taxonomy-settings-official-promotion]` (new) | Aynı patern. `settings_modification` scenario'su official-verifiable. |
| W20-3 | Coverage matrix contract tests | `[GOAL coverage-matrix-contract-tests]` (new) | `tests/platform/contracts/`: official vs heuristic track senkronizasyon invariant'ı, `_GLOBAL_CAPABILITY_NOTES` policy ↔ implementation eşleşmesi. |
| W20-4 | `comments` / `testing` tasarım hazırlığı (kod yok) | `[DESIGN taxonomy-comments-testing-readiness]` (new) | Doc/spec: harness surface envanteri, eksik plumbing, W21 şablonu. |
| W20-5 | Close-out hygiene | — | PR `week20 -> main` |

**W20 acceptance**:
- Static suite yeşil (sayısal estimate non-binding)
- Live: official-track `coverage_summary.missing_capabilities` listesinden `scm` + `settings` düşer (6 → 4)
- Activation event spec crosswalk raporu backlog'a yazılı

---

### W21 — Coverage Promotion Round 2: Mid Tier (1 iter)

`comments`, `testing`, `workspace_trust` her iki track'te
`covered`. Container hardening **stretch / fallback**.

| Iter | Theme | Stable ID | Notes |
|---|---|---|---|
| W21-0 | Doc reconcile + §19 plan | — | — |
| W21-1 | `testing` her iki track → covered | `[GOAL taxonomy-testing-coverage]` (new) | Local test controller + run/debug flow stub. `_GLOBAL_CAPABILITY_NOTES` policy: external test services yasak. |
| W21-2 | `comments` her iki track → covered | `[GOAL taxonomy-comments-coverage]` (new) | Local comment thread harness surface. W20-4 design uygulanır. |
| W21-3 | `workspace_trust` her iki track → covered | `[GOAL taxonomy-workspace-trust-coverage]` (new) | Gerçek trust-state transition + harness-assisted vs UI-only ayrımı. Scope explode ederse W22'ye defer. |
| W21-4 | **STRETCH** — Container hardening baseline | `[GOAL container-hardening-baseline]` | `docker-compose.yml` (`cap_drop:ALL` + audit edilmiş re-add), `docker/seccomp.json`, `read_only`, resource limits. ADR `documents/adrs/0013-container-isolation-baseline.md`. Manual smoke gerekiyor. Kapasite yoksa W22-pre veya W23+. |
| W21-5 | Close-out hygiene | — | PR `week21 -> main` |

**W21 acceptance**:
- Her iki track missing `chat` dışında 0 — **must-pass**
- Workspace_trust defer edilirse missing `chat` + `workspace_trust` dışında 0 (defer audit'lenir)
- Container manual smoke ✅ — **stretch (yalnız W21-4 pull edildiyse)**

---

### W22 — Coverage Promotion Round 3: Hard Tier + Sandbox ADR (1 iter)

`chat` policy ADR + implementation + sandbox-evasion ADR draft.

| Iter | Theme | Stable ID | Notes |
|---|---|---|---|
| W22-0 | Doc reconcile + §20 plan | — | — |
| W22-1 | `chat` policy ADR | `[GOAL taxonomy-chat-policy-adr]` (new) | `documents/adrs/0014-chat-and-language-model-tool-policy.md`. `onChatParticipant` + `onLanguageModelTool:*` yerel verification stratejisi. KOD YOK. |
| W22-2 | `chat` her iki track → covered (ADR Accepted sonra) | `[GOAL taxonomy-chat-coverage]` (new) | Local LM stub provider + 2 chat scenario. |
| W22-3 | Attribution depth: ProcessEvent + OutputChannelAppendLine | `[FOLLOWUP attribution-count-parity-process-events]` + `[FOLLOWUP attribution-count-parity-output-channel]` (new) | W17-1 producer-side stamp paterni. 4+4=8 invariant test. |
| W22-4 | Sandbox-evasion defense ADR draft (kod yok) | `[GOAL sandbox-evasion-defense-mvp]` (existing backlog candidate) | `documents/adrs/0015-sandbox-evasion-defense-policy.md`. ADR 0002 §3 ile ilişki. |
| W22-5 | Sandbox-detection canary fixture | `[GOAL sandbox-evasion-canary-fixture]` (new) | `tests/security/test_sandbox_evasion_canary.py` — webdriver + timing probe simülasyonu. |
| W22-6 | Activation event Tier-1 (W20-0 crosswalk sonuçları) | `[GOAL activation-event-spec-gap-followup]` (new) | W20-0 gerçek gap çıkardıysa implement; çıkarmadıysa skip. |
| W22-7 | Close-out hygiene | — | PR `week22 -> main` |

**W22 acceptance**:
- **Must-pass**: chat ADR Accepted + local-only path implemented **or** deferred-with-blocker; W22-3 + W22-4/5 yeşil
- **Expected** (chat implemented + W21 workspace_trust kapatıldıysa): her iki track missing == 0
- **Stretch**: `automation_health.status == 'healthy'` + `run_quality == 'high'`

---

## Live-Run Acceptance Gate (W19+ close-out'lar)

Codex bulgusu (2026-05-21): static yeşil ≠ runtime sağlık. Bu
nedenle W19, W20, W21, W22 close-out'larında ek olarak:

1. `make exec-up` ile stack ayağa kalkar
2. `make sim-target TARGET=ms-python.python` referans run
3. Yeni rapor JSON'u önceki rapor (`992ad028f3df`) ile diff'lenir; tablo:
   - `automation_health.status` (`degraded` / `healthy` / `inconclusive`)
   - `automation_health.reasons` (delta)
   - `run_quality` (`low` / `medium` / `high`)
   - **Official track**: `coverage_summary` (= `coverage_tracks.official.summary`)
   - **Heuristic track**: `coverage_tracks.heuristic.summary` (top-level karşılığı yok)

## Manual Smoke (W21-4 zorunlu)

- `cat /proc/self/status | grep Cap` → audit edilmiş minimum cap set
- `mount | grep "rw,"` → sadece tmpfs yolları RW
- `tests/platform/security/test_seccomp_profile_sanity.py` PASS

---

## Critical Files (yol haritası)

### Hat-1: Dropout fix (W19-1, W19-2)

- `executor/flows/playwright/stimulus/`
- `workflows/marketplace/analysis_execution.py` (scenario_accountant — W16-1 paterni)
- `executor/flows/playwright/scenarios/registry.py`
- `tests/executor/test_scenario_accountant_dropout_regression.py` (yeni)

### Hat-2: Harness verification (W19-3..W19-5)

- `executor/flows/playwright/runtime_capture/`
- [executor/flows/harness_extension/](../../executor/flows/harness_extension/) — `extension.js`, `markers.js`, `providers.js`, `stimulus_dispatch.js`, `constants.js`, `package.json`
- `tests/executor/test_automation_health_reasons.py` (yeni)
- Schema impact survey: `appcore/contracts/schema_defs/` + [ui/src/lib/adapters/report.ts](../../ui/src/lib/adapters/report.ts) + [report.test.ts](../../ui/src/lib/adapters/report.test.ts) + `tests/platform/contracts/`

### Hat-3: Coverage matrix + Activation events

- [packages/analysis_planner/capabilities.py](../../packages/analysis_planner/capabilities.py)
- `packages/analysis_planner/scenarios.py` + `selection.py`
- `packages/analysis_planner/event_scenario_index.py`
- [appcore/contracts/schema_defs/catalog.py](../../appcore/contracts/schema_defs/catalog.py)
- [appcore/storage/model_defs/extension.py](../../appcore/storage/model_defs/extension.py)
- `executor/flows/playwright/attribution/links.py` (W22-3)

### Heartbeat refactor (W18)

- `workflows/marketplace/analysis_service.py` (L155-L164)
- `workflows/marketplace/analysis_execution.py` (`_run_monitoring_heartbeat`)
- [tests/workflows/marketplace/test_lifecycle_harness.py](../../tests/workflows/marketplace/test_lifecycle_harness.py) — W17-2 extension points

### Container hardening (W21-4)

- `docker-compose.yml`
- `docker/seccomp.json` (yeni)
- `tests/architecture/test_compose_isolation_invariants.py` + `tests/platform/security/test_seccomp_profile_sanity.py` (yeni)

### ADR + tracker dosyaları

- `documents/adrs/0012-heartbeat-thread-relocation.md` (W18-1)
- `documents/adrs/0013-container-isolation-baseline.md` (W21-4)
- `documents/adrs/0014-chat-and-language-model-tool-policy.md` (W22-1)
- `documents/adrs/0015-sandbox-evasion-defense-policy.md` (W22-4)

---

## Açık Sorular / Karar Noktaları

### W18 başlangıcında

1. **Heartbeat refactor opsiyonu (W18-1 ADR)**: (a) Dedicated reset thread, (b) Queue-based merge, (c) Pipeline restructure. W13-1/W13-3/W13-13/W16-2 invariant cost'ları ADR'da kaydedilmeli.

### W19 başlangıcında (live-run-driven)

2. **Dropout emit-site lokasyonu**: `debug_session`/`refactor_workflow`'un `unaccounted_dropout` üzerinden düştüğü path. W16-1 fix'ten kalan path mi, yeni emit-site mi? W19-1 fixture pin'lendikten sonra W19-2 çözer.
3. **Harness verification scheme**: Per-event nonce mi, batch confirmation mi? `runtime_capture/` tasarımı W19-3'te.

### W20 başlangıcında

4. **Activation event spec crosswalk (W20-0)**: 5 "missing" event ismi (`onMemento`, `onTerminalQuickFixRequest`, `onChat`, `onAuthenticationProvider`, `onRendererScript`) GPT review'de resmi spec'te görünmedi. Crosswalk gerçek gap çıkarırsa W22-6'da implement.
5. **Container hardening konumlandırması**: W21-4'te ertelenmiş. W18 erken biterse W18-4 olarak çekilebilir mi — karar W18-3 sonrası.

### W22 başlangıcında

6. **Chat policy (W22-1 ADR)**: Mock LM endpoint mi, harness-side stub mı? Dış servis çağırma yasağı net.
7. **Sandbox-evasion (W22-4 ADR)**: Implementation kapasite. Şu an plan: sadece ADR + canary, kod W23+.

---

## Source Plan

Driving plan file (with full Codex + GPT review history):
`/Users/ekrem/.claude/plans/senden-projemdeki-capabilites-ve-mellow-valley.md`
(local; not in repo). Bu tracker repo-canonical kopyadır.
