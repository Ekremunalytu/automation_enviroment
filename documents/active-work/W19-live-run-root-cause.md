# W19 — Live-Run Kök Neden: Dropout + Harness Verification (Active Work Tracker)

`Last Updated: 2026-05-21 (W19 active — W19-0 doc-reconcile this commit on the week19 branch (per user direction 2026-05-21; W11-W18 paterni preserved). Sub-iter slate W19-0..W19-6 reserved by §17 plan; stable IDs W19-1..W19-5 reserved at POST_POC_BACKLOG.md W19-W22 Roadmap Acceptance Bar; assigned at first pull per W11-W18 precedent. Driving signal: Codex live-run validation 2026-05-21 of ms-python.python @ 992ad028f3df reports automation_health.status=degraded + run_quality=low while static W18 final bar (1907/201/220) remains green. W19 closes Hat-1 (executor muhasebe bug → unaccounted_dropout) + Hat-2 (harness verification gap → declared ≠ verified) in this iter; Hat-3 (coverage matrix promotion) deferred to W20-W22 per multi-iter roadmap. W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; final W18 bar tests/architecture/ 201 / make test-security 220 / full suite 1907 passed, 9 skipped, 8 deselected. W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d. W18 frozen tracker: W18-heartbeat-refactor.md; multi-iter roadmap source-of-truth: W18-W22-roadmap.md; §17 W19 plan source in REFACTOR_OPTIMIZATION.md.)`
`Phase: W19 active — W19-0 doc-reconcile landed this commit; W19-1..W19-6 next on the week19 branch`
`Branch: week19 (per user direction 2026-05-21; W11-W18 paterni preserved — sub-iter commits land on week19, close-out merges into main via week19 -> main PR)`
`Owner: ekrem`

> **Authored 2026-05-21** as the W19 scope skeleton against `main` HEAD
> `6166f7f` (W18 post-merge audit tracking commit) + `9874e79` (PR #26
> `week18 -> main` merge commit). Stable IDs `W19-1..W19-5` are reserved
> by the iteration plan at `POST_POC_BACKLOG.md` W19-W22 Roadmap
> Acceptance Bar and **assigned at first pull** per the
> W11/W12/W13/W14/W15/W16/W17/W18 precedent
> (`REFACTOR_OPTIMIZATION.md` §15.0 / §16.0).

This is the canonical active work tracker for the W19 Live-Run Kök Neden
window. Items receive stable IDs (`W19-1`, `W19-2`, …) **at first pull**,
not preemptively, per the W11/W12/W13/W14/W15/W16/W17/W18 precedent.

Slim canonical [`REFACTOR_OPTIMIZATION.md §17`](../REFACTOR_OPTIMIZATION.md)
carries the entry-conditions block, goal statement, and the W19-W22
multi-iter roadmap context. The multi-iter source-of-truth roadmap is at
[`W18-W22-roadmap.md`](W18-W22-roadmap.md); this tracker is the W19
slice. The W18 frozen tracker
([`W18-heartbeat-refactor.md`](W18-heartbeat-refactor.md)) is the
template structurally followed here.

## Status (Quick Glance)

- **W19 active — on `week19` branch per user direction (2026-05-21;
  W11-W18 paterni preserved).** Sub-iter commits land on `week19`;
  close-out merges into `main` via a `week19 -> main` PR.
- **Entry gate (met).** W18 close-out PR #26 `week18 -> main` MERGED
  `2026-05-21` via `9874e79`; W18 final bar (recorded at W18-4 +
  W18-4-followup): `tests/architecture/` **201 passed**;
  `make test-security` **220 passed**; full suite **1907 passed,
  9 skipped, 8 deselected**.
- **Driving signal (live run, 2026-05-21).** Codex live-run validation
  of `ms-python.python` @ `992ad028f3df` reports
  `automation_health.status=degraded` + `run_quality=low` while the
  static W18 final bar (1907/201/220) remains 🟢. Four reasons
  recorded: `skipped_scenarios_present`, `verification_gap_present`,
  `official_unresolved_present`, `harness_verification_unconfirmed_present`.
  21 `event_attempts` of which capability-level verified = 4 only.
  Coverage summary: covered=7 / partial=5 / missing=6. W19 closes
  the **first two of three** independent problem hatları surfaced
  by this signal:
  - **Hat-1 — Executor muhasebe bug** (`unaccounted_dropout > 0` —
    two scenarios `debug_session` + `refactor_workflow` drop without
    a classified `reason_code`). W19-1 RED fixture + W19-2
    emit-site fix.
  - **Hat-2 — Harness verification gap** (declared ≠ verified; 21
    attempt → 4 verified at capability level). W19-3 contract
    field landing + W19-4 `onDebug*` nonce + W19-5
    `onTerminalShellIntegration` + `onLanguageModelTool:*`
    local-only confirmation.
  - **Hat-3 — Coverage matrix promotion** (6 missing capabilities)
    is **out of scope for W19** — deferred to W20-W22 per
    multi-iter roadmap.
- **W19-0 closed `2026-05-21` via this commit** — doc reconcile +
  canonical preamble refresh across 8 docs (CLAUDE.md / AGENTS.md /
  README.md / `documents/AGENT_CONTEXT.md` /
  `documents/REFACTOR_STATUS.md` / `documents/POST_POC_BACKLOG.md` /
  `documents/REFACTOR_OPTIMIZATION.md` anchor map + this tracker)
  + `documents/active-work/README.md` Last Updated bump + new W19
  tracker (this file) + §17 W19 header doc-open (planning → active)
  in `REFACTOR_OPTIMIZATION.md` + README phase-pointer arch gate
  transition W18→W19 (`tests/architecture/test_readme_phase_pointer.py`
  flipped active-phase gate from W18 to W19 + new W18 close-out
  fact gate `test_readme_phase_pointer_mentions_w18_closeout_merge`
  pinning PR #26 / `week18 -> main` / `9874e79`, mirroring the
  W18-0 W17→W18 transition paterni from `89d0c9b`).

## Sub-Iter Scope (Authored 2026-05-21)

| Iter | Hat | Theme | Source / Why | Notes |
|---|---|---|---|---|
| W19-0 | — | Doc reconcile + §17 W19 active-phase pointer + baseline live-run smoke | Pattern match W18-0 (`89d0c9b`) | Open this tracker, refresh §17 anchor map entry, canonical preamble bumps across 8 docs, flip README phase-pointer arch gate (W18→W19 + new W18 close-out fact gate), update `W18-W22-roadmap.md` status (W18 closed → W19 active), baseline `make exec-up` + `make sim-target TARGET=ms-python.python` smoke artefakt. Doc-only + 1 test file flip + baseline JSON capture. |
| W19-1 | Hat-1 | Regression fixture (xfail/RED) | `[BUG scenario-unaccounted-dropout-regression-fixture]` (new; reserved at POST_POC_BACKLOG.md W19-W22 Roadmap Acceptance Bar) | New file `tests/executor/test_scenario_accountant_dropout_regression.py` parametrize on `["debug_session", "refactor_workflow"]`. `@pytest.mark.xfail(strict=True, reason="W19-2 emit-site fix bekleniyor; W19-1 RED fixture")` — strict mode: W19-2 fix landing'inde xfail beklenmedik PASS'a dönerse CI breaks → success signal. Assert: her senaryo için `reason_code != "unaccounted_dropout"` ve aggregate `unaccounted_dropout == 0`. Whitelist W19-1'de geniş tutulur (kandidat: `skipped:dependency_missing`, `failed:trigger_timeout`, `skipped:precondition_unmet`); W19-2'de seçilen path'e göre daraltılır. Live-run shape W19-0 baseline JSON'undan lift edilir. Root-cause-blind çalışır — sembptomu iddia eder, mekanizmayı değil. |
| W19-2 | Hat-1 | `unaccounted_dropout` emit-site fix | `[BUG scenario-unaccounted-dropout-debug-refactor]` (new; reserved at POST_POC_BACKLOG.md) | Hat olarak izlenecek üç dosya (W19-1 RED triage 30 dk içinde):  `executor/flows/playwright/entrypoint/dispatch.py:91-114` (W16-1 emit-site paterni; `dispatch_outcome_none` kardeşi olabilir), `executor/flows/playwright/stimulus/*` (scenario fire site), `executor/flows/playwright/scenarios/registry.py` (handler registry seam). Accountant fallback (`executor/flows/playwright/monitor/scenario_accountant.py:392-438`) **son-mil koruyucu olarak kalır** — sadece bu iki senaryo için tetiklenmez. Eğer iki senaryo iki ayrı upstream path'ten düşüyorsa mini-ADR `§17 design block` içine; tek path ise ADR gerekmez (W16-1 emsal). W19-1 xfail(strict=True) GREEN'e flip → kaldırılır + whitelist daraltılır. Live: `make sim-target TARGET=ms-python.python` → `unaccounted_dropout == 0`. |
| W19-3 | Hat-2 | Harness verification contract event-level | `[GOAL harness-verification-contract-event-level]` (new; reserved at POST_POC_BACKLOG.md) | **Hard gate**: W19-4/W19-5 başlamadan önce schema + UI back-compat tamamen landing. İlk faz: 30-dk schema impact survey, bu tracker'a yazılır — `appcore/contracts/schema_defs/` içinde `event_attempts` öğelerini tutan model (`EventAttemptRecord` at `packages/analysis_contracts/contracts.py:200`, `StrictContractModel` extra forbid), UI adapter (`ui/src/lib/adapters/report.ts` `EventAttemptDto` + `EventAttemptView` + `fromEventAttempt`), `ui/src/lib/adapters/report.test.ts` round-trip, `tests/platform/contracts/` round-trip, `tests/architecture/test_baseline_fixture_manifest_parity.py` fixture refresh. İkinci faz: schema field landing — `confirmation_source: Literal["harness_nonce", "log_record", "none"]` default `"none"` (back-compat) + UI adapter + emit pipeline taslak + yeni contract gate + yeni test `tests/executor/test_automation_health_reasons.py`. Roadmap §111 explicitly named `confirmation_source` — değiştirilmez. |
| W19-4 | Hat-2 | `onDebug*` nonce confirmation | `[FOLLOWUP harness-verification-debug-events]` (new; reserved at POST_POC_BACKLOG.md) | `executor/flows/harness_extension/{extension.js, markers.js, providers.js, stimulus_dispatch.js, constants.js, package.json}` — `onDebug` + alt aileleri (`onDebugResolve`, `onDebugInitialConfigurations`, `onDebugDynamicConfigurations`, `onDebugAdapterProtocolTracker`) için nonce generation. `executor/flows/playwright/runtime_capture/` Python tarafı emit yakalar ve `confirmation_source = "harness_nonce"` stamp'ler. `OFFICIAL_EVENT_REGISTRY` (`packages/analysis_planner/event_scenario_index.py`) onDebug* aileyi zaten tanıyor — `verification_contract` alanı `harness_nonce` ile uyumlanır. Live smoke: en az bir `event_attempt` with `event_family=onDebug*` shows `confirmation_source="harness_nonce"`. |
| W19-5 | Hat-2 | `onTerminalShellIntegration` + `onLanguageModelTool:*` local-only confirmation | `[FOLLOWUP harness-verification-terminal-and-lm-tool]` (new; reserved at POST_POC_BACKLOG.md) | W19-4 ile paralel uygulanabilir (disjoint event families); tek branch'te CI yeşil tutmak için W19-4 sonrası landing önerilir. Local-only confirmation marker `confirmation_source = "log_record"`. Confirmation üretilemeyen event'ler için açık `blocked` / `unsupported` reason kaydı (mevcut `verification_status` veya yeni alan ile uyumlu; W19-3 contract'ı buna izin verir: `confirmation_source = "none"` + sebep ayrıca). ADR 0002 (sandbox isolation) policy: external service çağırma yasağı — local stub-only pipeline. Live smoke: terminal + LM event_attempt entry'leri `confirmation_source` doldurulmuş. |
| W19-6 | — | Close-out hygiene + PR `week19 -> main` | Pattern match W18-4 (`3f4f95a`) + W17-6 (`21f7c68`) + W17-7-followup (`dab4679`) | Canonical preamble refresh across 8 docs + §17 self-stamp (post-merge final bar) + tracker freeze (sub-iter slate audit trail with commit SHAs) + PR open against `main`. Final live smoke `make sim-target TARGET=ms-python.python` JSON diff vs `992ad028f3df`: `unaccounted_dropout == 0` (must), `harness_verification_unconfirmed_present` reason gone (must), `run_quality: medium` (expected), `verification_gap_present` gone (stretch; düşmezse W20'ye), `automation_health.status: degraded` OK (`official_unresolved_present` W20'de). |

## Per-Item Detail

### W19-0 — Doc reconcile + §17 W19 plan header + baseline live-run smoke (closed 2026-05-21 via this commit)

**Pulled `2026-05-21`** (first commit on `week19` branch cut from
`main` HEAD `6166f7f` — W18 post-merge audit tracking commit).
Doc-only commit; one test file flip; baseline JSON capture
(W18-0 `89d0c9b` paterni).

**Scope (delivered):**

- **New W19 tracker** (this file) authored as the W19 scope skeleton
  against `main` HEAD `6166f7f`.
- **§17 W19 header doc-open** in
  [`documents/REFACTOR_OPTIMIZATION.md`](../REFACTOR_OPTIMIZATION.md):
  the `## §17-§20 — W19-W22 Capability + Otomasyon Sağlık + Coverage
  Promotion Roadmap (planning)` combined header is split into
  `## §17 — W19 Live-Run Kök Neden: Dropout + Harness Verification
  (active; on the week19 branch since 2026-05-21)` (new W19 active
  block) and `## §18-§20 — W20-W22 Capability + Otomasyon Sağlık +
  Coverage Promotion Roadmap (planning)` (W20-W22 retained,
  renumbered). §16 W18 closed entry remains stable.
- **8-doc canonical preamble refresh** (W18-4 paterni applied):
  - `CLAUDE.md` — preamble line 3 + "Active phase: W18" body
    paragraph (line 96+) flipped from "W18 active" to **"Previous
    phase: W18"** + **"Active phase: W19 — Live-Run Kök Neden"**
    with sub-iter slate W19-0..W19-6 inline (open IDs reserved).
  - `AGENTS.md` — preamble line 3 + body "Active phase" sentence
    (line 31+) flipped to "Active phase: W19 — Live-Run Kök Neden";
    W18 audit trail demoted to "Previous phase: W18 ..." one-line
    summary pointing at the W18 frozen tracker.
  - `README.md` — preamble line 3 + body Current Phase block W19
    bullet added; arch gate `test_readme_phase_pointer_tracks_active_w19_status`
    tokens (`W19`, `active-work/W19-live-run-root-cause.md`, `week19`)
    present; arch gate `test_readme_phase_pointer_mentions_w18_closeout_merge`
    tokens (`PR #26`, `week18 -> main`, `9874e79`) present.
  - `documents/AGENT_CONTEXT.md` — preamble line 3 + body
    "Active phase" bullet flipped to W19; "W8-W18 are closed"
    expanded to "W8-W18/W19 are closed... — note: W19 itself
    active, others closed"; section pointer line updated to
    "section 17 (W19) + sections 18-20 (W20-W22)".
  - `documents/REFACTOR_STATUS.md` — preamble line 3 + Current State
    new W19 bullet inserted above the W19-W22 multi-iter roadmap
    planning bullet (which now becomes W20-W22 only).
  - `documents/POST_POC_BACKLOG.md` — preamble line 3 +
    new `## W19 Pull-Forward Acceptance Bar` subsection inserted
    above the renamed `## W20-W22 Roadmap Acceptance Bar
    (planning)` table (was: `W19-W22 Roadmap Acceptance Bar`);
    W19-1..W19-5 rows moved from planning table to W19
    Pull-Forward (status: in flight).
  - `documents/REFACTOR_OPTIMIZATION.md` — anchor map `§17 → W19`
    bullet added; `§18-§20 → W20-W22` bullet renamed from
    `§17-§20 → W19-W22 ... Roadmap` to `§18-§20 → W20-W22 ...
    Roadmap` (planning state); §17-§20 combined header split as
    described above.
  - `documents/active-work/README.md` — Last Updated bump (W18
    close-out summary → W19 active state).
  - This W19 tracker (added to the canonical preamble refresh as
    the 8th doc — W18 paterni used 7-doc; the 8th here is the
    new W19 tracker file itself, which gets its own preamble).
- **README phase-pointer arch gate transition W18→W19** in
  [`tests/architecture/test_readme_phase_pointer.py`](../../tests/architecture/test_readme_phase_pointer.py):
  - Renamed `test_readme_phase_pointer_tracks_active_w18_status`
    → `test_readme_phase_pointer_tracks_active_w19_status`; banner
    assertion `"W18 active" in status_banner` → `"W19 active" in
    status_banner`; README tokens flipped W18 → W19 and
    `active-work/W18-heartbeat-refactor.md` → `active-work/W19-live-run-root-cause.md`
    and `week18` → `week19`.
  - **New** `test_readme_phase_pointer_mentions_w18_closeout_merge`
    added (W17→W18 paterni mirror from W18-0 `89d0c9b`): tokens
    `"PR #26"`, `"week18 -> main"`, `"9874e79"` pinned in both
    `REFACTOR_STATUS.md` banner and `README.md` so the W18
    close-out fact does not drift while W19 is active. Banner text
    template updated W17→W18 references (`"while W18 is active"`
    → `"while W19 is active"`).
  - All other close-out fact gates (`W13`, `W14`, `W15`, `W16`,
    `W17`) preserved with their PR numbers and merge SHAs.
- **Baseline live-run smoke** (Plan agent R5 mitigation; user
  confirmed at plan time): `make exec-up` + `make sim-target
  TARGET=ms-python.python` baseline run. W18 heartbeat refactor
  sonrası live-run hâlâ 992ad028f3df ile aynı dropout shape
  üretiyor mu kontrol edildi; yeni JSON `output/` altında
  zaman-damgalı dosya olarak landed; özet bu tracker'a aşağıda
  yapıştırıldı (Baseline Live-Run Smoke section). W19-1 fixture
  lifted shape buradan alınır.

**Number reconciliation: tests/architecture/ canonical count is 202
(W19-0 baseline), +1 vs W18 final 201.** Math: W18 final 201 +
W19-0 +1 (README phase-pointer arch gate W18→W19 transition + new
W18 close-out fact gate `test_readme_phase_pointer_mentions_w18_closeout_merge`,
net +1 because the previous-active gate was renamed not added) =
W19-0 baseline 202.

**Verification (recorded at landing this commit):**

- `.venv/bin/pytest tests/architecture/ -q` → **202 passed,
  4 deselected** (W18 final 201 + 1 new W18 close-out fact gate).
- `.venv/bin/pytest tests/architecture/test_doc_preamble_consistency.py
  tests/architecture/test_readme_phase_pointer.py -v` → **8 passed**
  (1 doc preamble consistency gate + 7 README phase-pointer gates
  including the W18 close-out fact gate added this commit + the
  W19 active status gate flipped from W18).
- `make test-security` → **220 passed** (unchanged from W18).
- `.venv/bin/pytest -q` full suite → **1908 passed, 9 skipped,
  8 deselected** (W18 final 1907 + W19-0 +1 from new W18 close-out
  fact gate; skip count unchanged from W18 baseline 9).
- Baseline live-run smoke artefakt landed under `output/` (path
  recorded in the Baseline Live-Run Smoke section below).

**Audit trail.** W19-0 opens the W19-0..W19-6 sub-iter slate. W18
close-out facts cited where W18 paterni transferred (preamble
template, §17 header structure, arch gate transition rule). No new
backlog item closed — W19-1..W19-5 stable IDs are reserved by
POST_POC_BACKLOG.md W19-W22 Roadmap Acceptance Bar and assigned
when pulled.

### W19-1 — Regression fixture (xfail/RED) — to be pulled

Stable ID `[BUG scenario-unaccounted-dropout-regression-fixture]`
reserved at POST_POC_BACKLOG.md W19-W22 Roadmap Acceptance Bar (now
W19 Pull-Forward Acceptance Bar after W19-0 promotion). Per-Item
Detail block populated at first pull (W18-1 paterni).

### W19-2 — `unaccounted_dropout` emit-site fix — to be pulled

Stable ID `[BUG scenario-unaccounted-dropout-debug-refactor]`
reserved at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar.
Per-Item Detail block populated at first pull.

### W19-3 — Harness verification contract event-level — to be pulled

Stable ID `[GOAL harness-verification-contract-event-level]`
reserved at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar.
Per-Item Detail block populated at first pull. Hard-gate
sequencing pin recorded above: W19-4/W19-5 cannot start until
W19-3 schema landing complete.

### W19-4 — `onDebug*` events nonce confirmation — to be pulled

Stable ID `[FOLLOWUP harness-verification-debug-events]` reserved
at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar. Per-Item
Detail block populated at first pull.

### W19-5 — `onTerminalShellIntegration` + `onLanguageModelTool:*` confirmation — to be pulled

Stable ID `[FOLLOWUP harness-verification-terminal-and-lm-tool]`
reserved at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar.
Per-Item Detail block populated at first pull.

### W19-6 — Close-out hygiene — to be pulled

Stable ID gets a Per-Item Detail entry here when pulled (W18-4
paterni `3f4f95a` followed). Close-out PR `week19 -> main` opened
at this point.

## Baseline Live-Run Smoke (W19-0)

Pre-fix baseline live-run captured at W19-0 to establish that the
W18 heartbeat refactor did not change (or accidentally close) the
dropout shape. **Key finding**: the dropout class is alive +
deterministic + reproducible via the **analyze API only** — not via
`make sim-target` (which exercises a narrower scope per W18-2 ADR
0012 §Implementation note). W19-1 fixture lifts shape from the
canonical Codex reference `992ad028f3df`, validated against three
independent W18-2 era confirmations.

### sim-target smoke (ran 2026-05-21 ~19:29)

- **Command**: `make sim-target TARGET=ms-python.python` (W19-0
  scope-locked).
- **Host report path**:
  `output/activation_report_564d91c628544a1ab0cdf2f50a6dbde0.json`
  (2.6 MB; written from container `/results/`).
- **Shape observed**:
  - `automation_health.status = inconclusive` (**not** `degraded`)
  - `run_quality = inconclusive` (**not** `low`)
  - 7 reasons including `target_extension_not_observed`,
    `fatal_ui_crash`, `scenario_failures_present` — disjoint
    from the W19 4-reason set
  - 13 requested scenarios → 6 ran (`coding_session`,
    `debug_session`, `terminal_usage`, `git_workflow`,
    `extension_browsing`, `settings_modification`); 1 failed
    (`settings_modification`); 7 skipped — **all** with
    `reason_code = "aborted_after_fatal_ui_crash"` (a sim-target
    flake; VS Code renderer crashed mid-run)
  - `event_attempts.length = 0` (sim-target doesn't run the full
    event-attempt pipeline)
  - `coverage_summary` all zeros
  - **NO `unaccounted_dropout` reason_code** — dropout class is
    not exercised here
  - **NO `harness_verification_unconfirmed_present`** in reasons —
    harness verification flow not exercised here

**Disposition**: matches the W18-2 ADR 0012 §Implementation note
(`make sim-target` doesn't invoke `_reset_sandbox` or the
analyze pipeline scenario_accountant). The "fatal_ui_crash" is a
sim-target flake unrelated to W19; not pursued under W19 scope.
The sim-target smoke confirms only that the executor entrypoint
itself is alive post-W18 heartbeat refactor.

### Analyze API confirmation (W18-2 era runs)

The full analyze API exercises the dropout class. Three
independent runs landed `2026-05-21` after the W18-2 heartbeat
refactor implementation (`a9bffb1`) — recorded here as the
authoritative baseline:

| Run SHA (filename suffix) | Time (local) | Phase context |
|---|---|---|
| `a938bf05d116` | 12:19 | Post-W18-2 analyze API smoke |
| `18fbd60b6b59` | 14:21 | Post-W18-2 analyze API smoke |
| `1c4966a2616b` | 15:11 | Post-W18-2 analyze API smoke (most recent) |
| `992ad028f3df` | 10:19 | **Original Codex live-run reference** (W19 driving signal) |

All four reports carry **byte-identical** dropout shape:

- `automation_health.status = degraded`
- `automation_health.reasons = [skipped_scenarios_present,
  verification_gap_present, official_unresolved_present,
  harness_verification_unconfirmed_present]` (exact order)
- `run_quality = low`
- `requested_scenarios = [coding_session, project_exploration,
  debug_session, terminal_usage, refactor_workflow]` (5
  scenarios; full analyze API uses a smaller scenario set than
  sim-target's 13)
- `skipped_scenarios = [(debug_session, "unaccounted_dropout"),
  (refactor_workflow, "unaccounted_dropout")]`
- `event_attempts.length = 21`
- `coverage_summary`: covered=7, partial=5, missing=6;
  attempted=6, verified=4
- `verification_gap = 2`
- `target_extension_id = ms-python.python`

### Conclusions (W19-0 baseline pin)

1. **Dropout class is alive post-W18** — three independent
   analyze API confirmations reproduce the byte-identical
   `unaccounted_dropout` shape on `debug_session` +
   `refactor_workflow`. W19 scope premise validated; no
   re-evaluation needed.
2. **Dropout class is deterministic** — four runs spanning ~5
   hours produce byte-identical reason_code shape; W19-1
   fixture can lift from any of them with confidence.
3. **W19-1 fixture canonical anchor**: `992ad028f3df` (original
   Codex reference; the W19 driving signal). Alternative
   anchor `1c4966a2616b` (most recent post-W18-2 confirmation)
   may be used if `992ad028f3df` becomes unavailable; both
   produce identical fixture data.
4. **sim-target is NOT a usable smoke for W19** — confirms
   W18-2 ADR 0012 §Implementation note. W19-2 GREEN
   verification must use a fresh analyze API smoke (full
   pipeline), not sim-target.
5. **No W18-side-effect kapanışı** — W18 heartbeat refactor did
   not accidentally close the dropout bug class. The three
   post-W18 confirmations match the pre-W18 Codex reference
   byte-for-byte.

## Exit Criteria (W19-End)

W19 kapanır şu koşullar sağlandığında:

- W19-0..W19-6 kapanır ya da deferral rasyoneli ile W20'a taşınır.
- W19-1 RED fixture `tests/executor/test_scenario_accountant_dropout_regression.py`
  landed olarak `xfail(strict=True)` reports.
- W19-2 emit-site fix landed; W19-1 xfail strict GREEN'e flip → kaldırılır.
- W19-3 schema field `confirmation_source` landing complete: Pydantic
  contract + UI adapter back-compat + contract round-trip pin + new
  test `tests/executor/test_automation_health_reasons.py`.
- W19-4 onDebug* nonce confirmation landed; live smoke: at least
  one `event_attempt` with `event_family=onDebug*` shows
  `confirmation_source="harness_nonce"`.
- W19-5 onTerminal + onLM local-only confirmation landed; live
  smoke: terminal + LM `event_attempt` entries with
  `confirmation_source` populated (`log_record` or `none` with
  explicit `blocked`/`unsupported` reason).
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `active-work/README.md`, ve ilgili lane docs aynı active/closed
  state'i gösterir.
- W19 final bar: `make test-security` ≥220 passed;
  `tests/architecture/` ≥202 passed (W18 final 201 + 1 W18
  close-out fact gate from W19-0); full suite skip count W18
  baseline 9'dan **artmamalı**; full suite pass count W18 final
  1907 + W19-0 +1 + W19-N additions (estimate ≥1915, non-binding).
- **Live acceptance gate** — final `make sim-target TARGET=ms-python.python`:
  - **Must-pass #1**: `unaccounted_dropout == 0`
  - **Must-pass #2**: `harness_verification_unconfirmed_present`
    NOT in `automation_health.reasons`
  - **Expected**: `run_quality: medium` (low → medium); `low`
    kalırsa W19 stretch failed → tracker'a not, W20 takes over
  - **Stretch**: `verification_gap_present` gone (düşmezse W20'ye)
  - `automation_health.status: degraded` OK (`official_unresolved_present`
    W20'de kapanır — Hat-3 scope)
- Close-out hygiene pass: Ruff lint, UI contract sync, markdown
  formatting, doc truth-state alignment.
- Per user direction (2026-05-21): W19 `week19` branch'inde çalışır;
  sub-iter commits `week19` branch'inde land eder; close-out
  `week19 -> main` PR ile merge edilir; W19 tracker scope kapanışında
  frozen olur (W11-W18 paterni).

## Risk Notes

- **W18 heartbeat refactor live-run davranışını değiştirdi
  hipotezi** — Düşük-Orta olasılık. Mitigation: W19-0 baseline
  smoke (this commit) yeni live JSON üretir. Eğer dropout shape
  değişti ise W19-1 fixture canlı veriden lift edilir (varsayım
  yerine ölçüm). Eğer dropout class tamamen kapandı ise (W18 yan
  etki olarak fixe etti), kullanıcıya escalate edilir.
- **W19-2 emit-site root-cause iki ayrı path** — Orta olasılık.
  Mitigation: W19-1 RED triage 30 dk içinde path sayısı belirler;
  birden fazla ise `§17 design block` içine mini-ADR — yeni ADR
  dosyası açılmaz, W16-1 emsal.
- **W19-3 `confirmation_source` UI adapter back-compat kırılması**
  — Orta olasılık. Mitigation: default `"none"` + `EventAttemptDto`
  optional alan + UI adapter `report.test.ts` round-trip pin.
  Architecture-test count drift (fixture refresh): non-binding
  estimate; small delta.
- **W19-4/5 harness extension JS test infra coverage eksik** —
  Düşük-Orta. Mitigation: mevcut harness extension test paterni
  W18-2 ile aynı; reuse.
- **Live-run `run_quality` low→medium beklenen ama düşmez** —
  Düşük. Mitigation: acceptance bar "expected" olarak işaretli
  (must-pass değil); stretch alanına çekilir, W20'ye not.
- **Scope creep into W20+ (coverage matrix)** — Düşük; Hat-3
  açıkça W19 dışı yazılı. Mitigation: tracker disiplini, code
  review gate.

## Notes

- Branching policy: tek `week19` branch'i; per-iter feature branch
  açılmaz. Sub-iter commits sıralı `W19-0`, `W19-1`, ... olarak
  `week19`'a push edilir. W19-6 sonrası `week19 -> main` close-out
  PR. Sub-iter primary commit + self-stamp followup commit cadence
  (W18-2 `a9bffb1` + `78ed7cc` paterni).
- W18 frozen tracker
  ([`W18-heartbeat-refactor.md`](W18-heartbeat-refactor.md)) W18-4
  + post-merge sonrası **frozen reference**; W19 boyunca sadece
  okuma için açılır.
- W18-W22 multi-iter roadmap source-of-truth:
  [`W18-W22-roadmap.md`](W18-W22-roadmap.md). Bu tracker W19 slice'ı;
  W20+ için yeni active-work tracker'ları W19 kapanışında veya W20-0
  entry'de açılır.
- Driving plan dosyası (full Codex live-run + GPT × 2 review history):
  `/Users/ekrem/.claude/plans/week19-i-in-bir-branch-elegant-piglet.md`
  (local; not in repo). Bu tracker repo-canonical kopyadır.
