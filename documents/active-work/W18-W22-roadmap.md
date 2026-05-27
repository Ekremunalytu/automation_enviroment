# W18-W22 — Capability + Otomasyon Sağlık + Coverage Promotion Roadmap (Planning Tracker)

`Last Updated: 2026-05-27 (Active phase: W21 — W21-0 doc-reconcile in-flight via this commit. Opens week21 branch (per user direction 2026-05-27; W11-W20 paterni preserved — sub-iter commits land on week21, close-out merges via week21 -> main PR PENDING USER APPROVAL). New W21 active-work tracker documents/active-work/W21-coverage-promotion-mid-tier.md. §19 W21 plan header doc-open in REFACTOR_OPTIMIZATION.md split from §19-§20 W21-W22 planning combined header (W19-0 / W20-0 paterni mirror — §17 split at W19-0, §18 split at W20-0, §19 split here). W21 Pull-Forward Acceptance Bar promoted in POST_POC_BACKLOG.md (from W21-W22 Roadmap Acceptance Bar, now W22 Roadmap Acceptance Bar planning). 10-doc canonical preamble refresh. README phase-pointer arch gate transition W20→W21 (test_readme_phase_pointer.py tracks_active_w21_status + new test_readme_phase_pointer_mentions_w20_closeout_merge pinning PR #29 / week20 -> main / 64a3c3d mirroring W18-0 / W19-0 / W20-0 transition paterni). Baseline live-run captured via this W21-0 self-stamp follow-up (anchor activation_report_ms-python.python-2026.5.2026052501-600d9ecba5eb.json sha256 1db1480551fd90625a5c7c2e474b43c4de3a867d35dab4aacc65e8060bcc4477; W20 close-out invariants live-verified — coverage_summary.missing_capabilities = [chat, comments, testing, workspace_trust] (4 items byte-identical with W20-5 anchor 4e92de149802); W19 Hat-1 unaccounted_dropout_count is null (byte-identical with W20-5 anchor — note: W20-5 banner stated 'unaccounted_dropout count = 0' but the actual field value was already null, so the W20-5 preamble carried a minor banner drift; this self-stamp records the correct value); W19 Hat-2 harness_verification_unconfirmed_present DROPPED from reasons; W21-0 observed one new extra_trigger_failures_present reason (intermittent flake on official-onterminalshellintegration-python:harness:run_current_stimulus — not a W20 invariant violation; W21-N close-out will re-verify on fresh final live-run). W20 closed and merged via PR #29 week20 -> main MERGED 2026-05-26 via 64a3c3d; final W20 bar tests/architecture/ 240 passed / make test-security 220 passed / full suite 2045 passed, 9 skipped, 8 deselected. W21 driving signal (carried over from W19 / W20): same Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities started at [scm, settings, chat, comments, testing, workspace_trust]; W20-5 final live-run 4e92de149802 (sha256 3804a5b5...4394c) confirmed missing dropped 6 → 4 [chat, comments, testing, workspace_trust]; W21 closes mid tier (testing, comments, workspace_trust) — expected drop 4 → 1 [chat] or 4 → 2 [chat, workspace_trust] if W21-3 defers; W22 closes hard tier (chat) + sandbox evasion ADR draft. §19 W21 plan source (active) + §20 W22 planning. W21 sub-iter slate: W21-0 doc-reconcile (this commit) + W21-3 [GOAL taxonomy-workspace-trust-coverage] (lands first per user-confirmed ordering 2026-05-27 — W21-3 → W21-1 → W21-2; W20-4 DESIGN doc open Q4 resolved with "yes" branch) + W21-1 [GOAL taxonomy-testing-coverage] + W21-2 [GOAL taxonomy-comments-coverage] + W21-4 [GOAL container-hardening-baseline] STRETCH (conditional pull only if W21-0..W21-3 closed cleanly; user-confirmed) + W21-N close-out hygiene + PR week21 -> main PENDING USER APPROVAL. [FOLLOWUP sandbox-reset-stale-state-multi-analyze] (filed d163b02 at W20-5-followup-2) opportunistic at W21-N close-out window (user-confirmed); not a sub-iter, not a blocker. W19 closed and merged via PR #28 week19 -> main MERGED 2026-05-26 via c879603 — Hat-1 closed + live-verified; Hat-2 fully closed synthetically (W19-3 schema landing + W19-4 onDebug* producer/consumer + W19-X live close-out + W19-5 onTerminal+onLM log_record stamp); final W19 bar tests/architecture/ 204 / make test-security 220 / full suite 1995. W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; final W18 bar tests/architecture/ 201 / make test-security 220 / full suite 1907. W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f; W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 closed via PR #20 week13 -> main MERGED 2026-05-13 via 772deb3. W20 frozen tracker: documents/active-work/W20-coverage-promotion-easy-wins.md (frozen at W20-5 + followups per W17/W18/W19 paterni); W19 frozen tracker: documents/active-work/W19-live-run-root-cause.md (frozen at W19-6-followup-2); W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md; W21 active tracker: documents/active-work/W21-coverage-promotion-mid-tier.md; multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md.)`
`Phase: W20 closed synthetically 2026-05-27 — W20-0..W20-5 delivered + W20-5-followup-2 d163b02 + this commit (W20-5-followup-3 finalizing preamble backfill) on the week20 branch (W11-W19 paterni preserved); PR week20 -> main PENDING USER APPROVAL. W19 closed synthetically — PR #28 week19 -> main MERGED 2026-05-26 via c879603. W18 closed — PR #26 week18 -> main MERGED 2026-05-21 via 9874e79.`
`Branch: week20 (per user direction 2026-05-26; W11-W19 paterni preserved — sub-iter commits land on week20, close-out merges into main via week20 -> main PR PENDING USER APPROVAL)`
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

- **W18 closed 2026-05-21 via PR #26 `week18 -> main`
  MERGED `2026-05-21` via `9874e79`.** Sub-iter slate W18-0..W18-4
  fully delivered on the `week18` branch (per user direction
  2026-05-21; W11-W17 paterni preserved); W18-4-followup (`e1043e5`)
  added 4 W18-2 invariant pins + 2 pre-existing doc drift fixes
  before merge. W18 active tracker (frozen at W18-4):
  [`W18-heartbeat-refactor.md`](W18-heartbeat-refactor.md).
- **W19 closed synthetically `2026-05-26` — Hat-1 closed + live-verified
  `2026-05-25`; Hat-2 HARD GATE W19-3 + W19-4 + W19-X + W19-5 all
  closed on the `week19` branch; PR #28 `week19 -> main` MERGED
  `2026-05-26` via `c879603`.** Sub-iter delivery: W19-0 doc-reconcile 2026-05-21
  (`72712bd` + `086d7a5`); W19-1 RED dropout regression fixture
  2026-05-25 (`6a21cf3` + `fd02ca4`); W19-2 emit-site fix at
  `executor/flows/playwright/stimulus/passes.py` covered-only
  branch — new `covered_via_layered_attempts` reason_code
  (`89b64da` + `d9c6262`); W19-2-followup-2 live re-anchor + drift
  fix + sha256 format gate (`d5de9ca`); **W19-3 schema landing
  (primary `d2e83e7` + self-stamp `39121e4`)** — `confirmation_source: str = "none"`
  field landed on `EventAttemptRecord` (Pydantic at
  `packages/analysis_contracts/contracts.py` + executor dataclass at
  `executor/flows/playwright/monitor/records.py` + UI `EventAttemptDto`/`EventAttemptView`/`fromEventAttempt`),
  `_VALID_CONFIRMATION_SOURCES` module constant +
  `_validate_confirmation_source` `@field_validator` mirroring the
  `status` field pattern (typing decision: `str + field_validator`
  not `Literal[...]` — codebase parity, JSON wire shape identical),
  22 new tests (12 `test_automation_health_reasons.py` +
  6 contract round-trip + 4 UI adapter) + frozen trigger fixture
  regenerated via planner replay (21 event_attempts each gain
  `"confirmation_source": "none"`). **Live Hat-1 GREEN gate
  SATISFIED `2026-05-25 22:23`** via UI-driven analyze API re-run
  after `docker compose up -d --build api executor`: live JSON
  `activation_report_ms-python.python-2026.5.2026052501-c2bf28ca9506.json`
  (sha256 `e9e60b2e42...`) shows `unaccounted_dropout` count = 0,
  both `debug_session` + `refactor_workflow` now classified
  `covered_via_layered_attempts`; 16 of 16 key fields byte-identical
  with pre-fix anchor `992ad028f3df` save the W19-2 reason_code
  change. **Post-W19-3 live run `2026-05-25 23:27`
  (`86e0f3646ce9`)** confirms `confirmation_source` field landed
  at `"none"` on 21/21 event_attempts with no behavior regression.
  Hat-2 W19-4 `onDebug*` producer + consumer wire closed via `7d44b0e`
  (`health/reconciliation.py:347-348` + `:85-90` + 7 new tests at
  `test_playwright_health_reconciliation.py:813-1090`); W19-X `onDebug*`
  live close-out (`8b7b7f6` + `a3e634f`) closes Bug A/B/C; W19-5
  onTerminal + onLM log_record stamp (`e537ebd` + `4fd6ed6`); W19-6
  close-out hygiene (`f17b4b1` + `cd82153` + `800c69f`). W19 frozen
  tracker: [`W19-live-run-root-cause.md`](W19-live-run-root-cause.md).
- **W20 closed synthetically `2026-05-27` on the `week20` branch**
  (per user direction `2026-05-26`; W11-W19 paterni preserved);
  close-out PR `week20 -> main` **PENDING USER APPROVAL**.
  Sub-iter delivery: W20-0 doc-reconcile (`66a8a0b` + `5f13757`)
  + baseline live-run capture (anchor `e89a82ca9ba8`, sha256
  `4dd78826...0256ffe` — W19 close-out Hat-1 + Hat-2 both
  live-verified); W20-1
  `[GOAL taxonomy-scm-official-promotion]` (`82276cb` + `a17e595`)
  — `_OFFICIAL_CAPABILITY_SUPPORT["scm"]: "missing" → "covered"`
  at [`capabilities.py:88`](../../packages/analysis_planner/capabilities.py)
  + 4 invariant tests + fixture regen; W20-2
  `[GOAL taxonomy-settings-official-promotion]` (`a4343d2` +
  `7406588`) — W20-1 paterni byte-identical at
  [`capabilities.py:90`](../../packages/analysis_planner/capabilities.py);
  W20-3 `[GOAL coverage-matrix-contract-tests]` (`d4c03b6` +
  `2e39230`) — 5 contract invariant tests (keyset parity +
  Official ⊆ Heuristic + notes ↔ taxonomy + ordering +
  W20-1/W20-2 combined post-condition); W20-4
  `[DESIGN taxonomy-comments-testing-readiness]` (`05f47f3` +
  `b409894`) — doc-only readiness şablonu at
  [`comments-testing-readiness.md`](../architecture/comments-testing-readiness.md)
  (W21-1 `testing` + W21-2 `comments` unblocker); W20-5
  close-out hygiene (`4665d32` primary + `95b0010` self-stamp +
  `d163b02` followup-2 filed
  `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` for W21 +
  `ae5b7de` followup-3 10-doc preamble `(this commit)` placeholder
  backfill) — 9-doc canonical preamble Active → Previous flip +
  §18 W20 self-stamp + W20 tracker freeze + 3 new arch invariant
  tests (GAP-A cross-doc parity + GAP-B dict shape pin extension
  + GAP-D DESIGN doc presence) + W20-5 final live-run captured
  `2026-05-27` (anchor `4e92de149802`, sha256
  `3804a5b5...4394c`). **W20 acceptance LIVE-SATISFIED**:
  `coverage_summary.missing_capabilities` dropped 6 → **4**
  (lost `scm` + `settings`); W19 Hat-1
  (`unaccounted_dropout == 0`) + Hat-2
  (`harness_verification_unconfirmed_present` DROPPED) both
  hold post-W20. Hat-3 mid + hard tiers (`testing`, `comments`,
  `workspace_trust`, `chat`) deferred to W21-W22 per multi-iter
  roadmap below. Final W20 bar: `tests/architecture/` **240
  passed**, 4 deselected; `make test-security` **220 passed**;
  full suite **2045 passed, 9 skipped, 8 deselected**. W20
  frozen tracker:
  [`W20-coverage-promotion-easy-wins.md`](W20-coverage-promotion-easy-wins.md).
  W21-W22 remain in planning state.
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
| W19-4 | Hat-2 | `onDebug*` nonce confirmation + consumer wire | `[FOLLOWUP harness-verification-debug-events]` — **closed `2026-05-26` via `7d44b0e`** | Producer at `health/reconciliation.py:347-348` stamps `confirmation_source="harness_nonce"` on onDebug* attempts with verified harness completion; consumer wire at `reconciliation.py:85-90` gates `failure_reason_code="harness_verification_unconfirmed"` on `confirmation_source == "none"`; 7 new tests at `test_playwright_health_reconciliation.py:813-1090` |
| W19-5 | Hat-2 | `onTerminalShellIntegration` + `onLanguageModelTool:*` confirmation | `[FOLLOWUP harness-verification-terminal-and-lm-tool]` (new) | Local-only confirmation marker. Confirmation üretilemeyen event için açık `blocked` / `unsupported` reason. |
| W19-6 | — | Close-out hygiene + audit hygiene items | — | PR `week19 -> main`; **+ 3 hygiene items** from W19-3-followup-2 audit: field-set parity gate (extend tek-field gate'i set-difference'a), hotspot LOC ratchet (9 modül >500 LOC için `bare-binary pragma ratchet` paterni), W19 sub-iter table'ına `Closes which acceptance-bar item?` kolonu; **+ W20-0 forward ref** `[FOLLOWUP defensive-test-parametrize-helper]` schema-only field landings için tablo-yolu helper |

**W19 acceptance (live-run-driven)**:

- **Must-pass**: yeni `make sim-target TARGET=ms-python.python` çıktısında `unaccounted_dropout == 0`
- **Must-pass**: supported harness event'lerde `harness_verification_unconfirmed` reason'ı düşer
- **Expected**: `run_quality` `low` → `medium`
- **Stretch**: `verification_gap_present` de düşer (tam düşmezse W20'ye)
- `automation_health.status` `degraded` kalabilir (`official_unresolved_present` W20'de kapanır) — bu OK

---

### W20 — Coverage Promotion Round 1: Easy Wins (1 iter) — closed synthetically `2026-05-27`

GPT-önerdiği "kolaydan zora" gradient'in ilk dilimi. `scm` +
`settings` official promotion — scenario kodu zaten
heuristic-covered, eksik olan official-track verification.

> **W20 closed synthetically `2026-05-27` on the `week20` branch**
> (per user direction `2026-05-26`; W11-W19 paterni preserved);
> close-out PR `week20 -> main` **PENDING USER APPROVAL**. The
> planning table below is the original 2026-05-21 author intent;
> W20 sub-iter audit trail (closed) lives in the W20 frozen
> tracker [`W20-coverage-promotion-easy-wins.md`](W20-coverage-promotion-easy-wins.md)
> and the W20 closed bullet in Status (Quick Glance) above.

| Iter | Theme | Stable ID | Notes |
|---|---|---|---|
| W20-0 | Doc reconcile + §18 plan + Activation event spec crosswalk + W19-6-migrated forward refs | `[RESEARCH activation-event-spec-crosswalk]` (new) + `[FOLLOWUP harness-secret-extra-reactivation-source]` (migrated from W19-X-handoff.md at W19-6 close-out) + `[FOLLOWUP harness-secret-distribution-redesign]` (migrated from W19-X-handoff.md risk register at W19-6 close-out — W20-W22 ADR candidate) + `[FOLLOWUP defensive-test-parametrize-helper]` (W19-3-followup-2 audit) | **Üç kaynaklı crosswalk**: (1) resmi [VS Code Activation Events](https://code.visualstudio.com/api/references/activation-events) sayfası, (2) repo `OFFICIAL_EVENT_REGISTRY` (29 entry), (3) gerçek manifest source-of-truth (DB'deki `ExtensionActivationEvents` tablosu + indirilen VSIX'lerin `package.json` `activationEvents[]`). Çıktı: matris + gerçek gap listesi backlog'a. **+ W19-6-migrated items** (full descriptions in `documents/POST_POC_BACKLOG.md` Newly Captured table): trace the un-gated 4th reload path via `activate_enter` diagnostic + ADR comparing non-file vs file-kept-0400 secret distribution + table-driven helper for schema-only field landings. |
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

1. **Dropout emit-site lokasyonu**: `debug_session`/`refactor_workflow`'un `unaccounted_dropout` üzerinden düştüğü path. W16-1 fix'ten kalan path mi, yeni emit-site mi? W19-1 fixture pin'lendikten sonra W19-2 çözer.
2. **Harness verification scheme**: Per-event nonce mi, batch confirmation mi? `runtime_capture/` tasarımı W19-3'te.

### W20 başlangıcında

1. **Activation event spec crosswalk (W20-0)**: 5 "missing" event ismi (`onMemento`, `onTerminalQuickFixRequest`, `onChat`, `onAuthenticationProvider`, `onRendererScript`) GPT review'de resmi spec'te görünmedi. Crosswalk gerçek gap çıkarırsa W22-6'da implement.
2. **Container hardening konumlandırması**: W21-4'te ertelenmiş. W18 erken biterse W18-4 olarak çekilebilir mi — karar W18-3 sonrası.

### W22 başlangıcında

1. **Chat policy (W22-1 ADR)**: Mock LM endpoint mi, harness-side stub mı? Dış servis çağırma yasağı net.
2. **Sandbox-evasion (W22-4 ADR)**: Implementation kapasite. Şu an plan: sadece ADR + canary, kod W23+.

---

## Source Plan

Driving plan file (with full Codex + GPT review history):
`/Users/ekrem/.claude/plans/senden-projemdeki-capabilites-ve-mellow-valley.md`
(local; not in repo). Bu tracker repo-canonical kopyadır.
