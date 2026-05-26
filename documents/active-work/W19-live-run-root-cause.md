# W19 — Live-Run Kök Neden: Dropout + Harness Verification (Active Work Tracker)

`Last Updated: 2026-05-26 (W19 fully closed synthetically — Hat-1 closed + live-verified; Hat-2 fully closed via W19-3 schema landing (d2e83e7 + 39121e4 + W19-3-followup-2 8-doc preamble refresh 9b56e94) + W19-4 onDebug* producer/consumer wire (7d44b0e) + W19-X onDebug* live close-out (8b7b7f6 + a3e634f) + W19-5 onTerminal+onLM log_record stamp (e537ebd + 4fd6ed6) — closes the entire harness_verification_unconfirmed_present reason driver synthetically; +22 new behavioral tests (15 W19-X + 7 W19-5); live anchor 8247e05ec9ef.json: 2/2 onDebug* stamped (W19-X) + 6 non-onDebug stamp expected on next live (W19-5 producer arm extension); W19-6 close-out hygiene via f17b4b1 + cd82153 (parity gate widened, hotspot LOC ratchet, acceptance-bar column, handoff freeze); W19-6-followup-2 pre-merge hygiene this commit closes 6 test gaps (+20 parametrized tests) + corrects stale W19 preamble drift across the 9-doc canonical set + freezes this tracker per W17/W18 paterni; final W19 test bar 1995/9/8 (tests/architecture/ 204 / make test-security 220 / full suite 1995 passed) on the week19 branch (per user direction 2026-05-21; W11-W18 paterni preserved). W19-0..W19-6 + W19-X all closed; PR week19 -> main pending user approval; stable IDs W19-1..W19-5 tracked at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar; assigned at first pull per W11-W18 precedent. Driving signal: Codex live-run validation 2026-05-21 of ms-python.python @ 992ad028f3df reports automation_health.status=degraded + run_quality=low while W19-2 live re-anchor satisfies unaccounted_dropout == 0. Hat-1 is closed + live-verified; Hat-2 HARD GATE W19-3 schema landing + W19-4 producer + consumer wire closed (W19-3 lands confirmation_source: str = "none" field on EventAttemptRecord with str + field_validator typing mirroring the status field pattern; W19-4 producer at executor/flows/playwright/health/reconciliation.py:347-348 stamps confirmation_source="harness_nonce" on onDebug* attempts with verified harness completion; consumer wire at reconciliation.py:85-90 gates failure_reason_code="harness_verification_unconfirmed" on confirmation_source=="none" so stamped attempts skip the unverified marker; 7 new behavioral tests at test_playwright_health_reconciliation.py:813-1090; W19-5 extends the producer arm with sibling elif at reconciliation.py:347-365 stamping confirmation_source="log_record" on onTerminalShellIntegration + onLanguageModelTool families with verified harness completion; +7 new behavioral tests at test_playwright_health_reconciliation.py:1175-1369 mirroring W19-4 shape; W19-4 scope-discipline parametrize narrowed to onCommand only, orthogonality tests' unstamped half swapped to onCommand to preserve test premise); Hat-3 (coverage matrix promotion) deferred to W20-W22 per multi-iter roadmap. W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; final W18 bar tests/architecture/ 201 / make test-security 220 / full suite 1907 passed, 9 skipped, 8 deselected. W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d. W18 frozen tracker: W18-heartbeat-refactor.md; multi-iter roadmap source-of-truth: W18-W22-roadmap.md; §17 W19 plan source in REFACTOR_OPTIMIZATION.md.)`
`Phase: W19 closed synthetically — Hat-1 closed + live-verified (W19-0..W19-2 + W19-2-followup-2 live re-anchor); Hat-2 fully closed via W19-3 (d2e83e7 + 39121e4 + 9b56e94) + W19-4 (7d44b0e) + W19-X (8b7b7f6 + a3e634f) + W19-5 (e537ebd + 4fd6ed6); W19-6 close-out hygiene (f17b4b1 + cd82153); W19-6-followup-2 pre-merge hygiene this commit — closes 6 test gaps + 9-doc drift fix + this tracker freeze; PR week19 -> main pending user approval; tracker frozen at W19-6-followup-2 per W17/W18 paterni (Hat-3 deferred to W20-W22)`
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
  `automation_health.status=degraded` + `run_quality=low`; W19-2
  live re-anchor `d5de9ca` now satisfies `unaccounted_dropout == 0`.
  Four reasons
  recorded: `skipped_scenarios_present`, `verification_gap_present`,
  `official_unresolved_present`, `harness_verification_unconfirmed_present`.
  21 `event_attempts` of which capability-level verified = 4 only.
  Coverage summary: covered=7 / partial=5 / missing=6. W19 is closing
  the first two of three independent problem hatları surfaced by this
  signal; Hat-1 is already closed + live-verified:
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
- **W19-1 RED fixture landed `2026-05-25` via primary `6a21cf3` +
  self-stamp `fd02ca4`** — Hat-1 closure step 1 of 2.
  `tests/executor/test_scenario_accountant_dropout_regression.py`
  (3 xfail/strict tests parametrized on `debug_session` +
  `refactor_workflow` + an aggregate gate) lifts the live-run
  dropout shape from W19-0 baseline JSON anchor `992ad028f3df`
  (sha256 `7e06153c66...`, pinned alongside the slim canonical
  excerpt at
  `tests/executor/fixtures/activation_reports/w19_baseline_ms_python_python.{json,sha256}`).
  Root-cause-blind by design — asserts the surface symptom
  (`reason_code != "unaccounted_dropout"` + whitelist membership)
  without prescribing the upstream fix-site. W19-2 emit-site fix
  landed'inde xfail flips to PASS, strict mode turns the unexpected
  PASS into a CI break → W19-2 self-stamp removes the xfail markers
  and narrows the whitelist to the new reason_code. Test bar at
  W19-1 primary landing: `tests/architecture/` **202 passed,
  4 deselected** (unchanged); `make test-security` **220 passed**
  (unchanged — W19-1 lives in `tests/executor/`); full suite
  **1908 passed, 9 skipped, 8 deselected, 3 xfailed** (W19-0 baseline
  1908 + W19-1 +3 xfail).
- **W19-2 emit-site fix landed `2026-05-25` via primary `89b64da` +
  self-stamp this commit** — Hat-1 closure step 2 of 2;
  **Hat-1 fully closed**. `executor/flows/playwright/stimulus/passes.py`
  layered-passes reconciliation now splits into `handler_invoked`
  vs `covered_only` skip-sets; covered-only scenarios get a
  classified `covered_via_layered_attempts` reason_code via
  `scenario_reasons.get(name, default)` (default-fallback: a
  previously-recorded reason still wins). **Triage verdict:
  ONE-PATH bug** (no mini-ADR; W16-1 emsali holds). +2
  W16-1-mirror synthetic unit tests at
  [`tests/security/test_scenario_dropout_repro.py`](../../tests/security/test_scenario_dropout_repro.py)
  (`test_layered_attempts_coverage_emits_specific_reason_code` +
  `test_layered_attempts_coverage_pre_recorded_reason_wins`).
  W19-1 fixture regenerated to post-fix shape
  (`reason_code=covered_via_layered_attempts`); xfail markers
  removed; whitelist narrowed to single member. **Live Hat-1
  GREEN gate (`unaccounted_dropout == 0` in fresh live JSON)
  SATISFIED `2026-05-25 22:23`** via UI-driven analyze API
  re-run after `docker compose up -d --build api executor`
  picked up the W19-2 `passes.py` change inside the containers
  — output JSON
  `activation_report_ms-python.python-2026.5.2026052501-c2bf28ca9506.json`
  (sha256 `e9e60b2e42...`) shows `unaccounted_dropout` count = 0,
  both `debug_session` + `refactor_workflow` now classified
  `covered_via_layered_attempts`; 16 of 16 key fields
  byte-identical with the pre-fix anchor (`992ad028f3df`) save
  the W19-2 reason_code change. W19-1 fixture re-anchored
  synthesized → live-lifted in W19-2-followup-2 this commit.
  Test bar at W19-2 primary landing:
  `tests/architecture/` **202 passed, 4 deselected** (unchanged);
  `make test-security` **220 passed** (unchanged — W19-2
  synthetic tests on full suite, not on the curated lane); full
  suite **1913 passed, 9 skipped, 8 deselected, 0 xfailed**
  (W19-1 baseline 1908 + 3 xfail → 1908 + W19-1 3 flip
  xfail→pass + W19-2 2 new synthetic = 1913).
- **W19-3 schema landing landed `2026-05-25` via primary `d2e83e7` +
  self-stamp `39121e4` + W19-3-followup-2 8-doc preamble refresh
  `9b56e94`** — Hat-2 HARD GATE step 1 of 3 closed; W19-4 emit-site
  stamps + consumer wire landed `2026-05-26` via `7d44b0e` (step 2 of 3
  closed); W19-5 emit-site stamps pending (step 3 of 3). New
  `confirmation_source: str = "none"` field lands on both
  [`packages/analysis_contracts/contracts.py`](../../packages/analysis_contracts/contracts.py)
  `EventAttemptRecord` (Pydantic) and
  [`executor/flows/playwright/monitor/records.py`](../../executor/flows/playwright/monitor/records.py)
  `EventAttemptRecord` (executor dataclass), with
  `_VALID_CONFIRMATION_SOURCES = frozenset({"harness_nonce", "log_record", "none"})`
  module constant + `_validate_confirmation_source` `@field_validator`
  mirroring the `status` field pattern. UI side: optional
  `confirmation_source?: string` on `EventAttemptDto`
  ([`ui/src/lib/types/contracts.ts`](../../ui/src/lib/types/contracts.ts))
  + required `confirmationSource: string` on `EventAttemptView`
  ([`ui/src/lib/types/view-models.ts`](../../ui/src/lib/types/view-models.ts))
  + `fromEventAttempt()` adapter map with `"none"` default
  ([`ui/src/lib/adapters/report.ts`](../../ui/src/lib/adapters/report.ts)).
  **Typing decision:** `str + field_validator` not `Literal[...]`
  per §17 plan — codebase parity with the `status` field pattern;
  JSON wire shape identical (deviation captured in Per-Item Detail
  block below). New test file
  [`tests/executor/test_automation_health_reasons.py`](../../tests/executor/test_automation_health_reasons.py)
  (12 tests) pins dataclass ↔ Pydantic parity + trigger-payload
  deserialization (default + parametrize over 3 documented values)
  + validator rejects unknown + orthogonality with the existing
  `harness_verification_unconfirmed_present` reason emission rule
  (presence + absence parametrize over 3 sources). +6 contract
  round-trip tests at
  [`tests/platform/contracts/test_analysis_fixture_baselines.py`](../../tests/platform/contracts/test_analysis_fixture_baselines.py).
  +4 UI adapter tests at
  [`ui/src/lib/adapters/report.test.ts`](../../ui/src/lib/adapters/report.test.ts).
  Frozen trigger fixture
  [`tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json`](../../tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json)
  regenerated via planner replay (`select_scenarios()` →
  `model_dump(mode="json")`) so each of the 21 event_attempts
  gains `"confirmation_source": "none"`. Test bar at W19-3 primary
  landing: `tests/architecture/` **202 passed, 4 deselected**
  (unchanged from W19-2 baseline); `make test-security` **220 passed**
  (unchanged); full suite **1932 passed, 9 skipped, 8 deselected,
  0 xfailed** (W19-2 baseline 1913 + W19-3 +19 net new tests:
  12 health_reasons + 6 contract round-trip + 1 incidental delta
  on the trigger-fixture parity test pair returning to baseline
  after the regenerate). No live-run required — field lands at
  `"none"` everywhere with no behavior change; live verification
  belongs to W19-4 + W19-6.

## Sub-Iter Scope (Authored 2026-05-21)

| Iter | Hat | Theme | Source / Why | Notes | Closes which acceptance-bar item? |
|---|---|---|---|---|---|
| W19-0 | — | Doc reconcile + §17 W19 active-phase pointer + baseline live-run smoke | Pattern match W18-0 (`89d0c9b`) | Open this tracker, refresh §17 anchor map entry, canonical preamble bumps across 8 docs, flip README phase-pointer arch gate (W18→W19 + new W18 close-out fact gate), update `W18-W22-roadmap.md` status (W18 closed → W19 active), baseline `make exec-up` + `make sim-target TARGET=ms-python.python` smoke artefakt. Doc-only + 1 test file flip + baseline JSON capture. | — (doc-reconcile; no acceptance-bar item) |
| W19-1 | Hat-1 | Regression fixture (xfail/RED) | `[BUG scenario-unaccounted-dropout-regression-fixture]` (new; reserved at POST_POC_BACKLOG.md W19-W22 Roadmap Acceptance Bar) | New file `tests/executor/test_scenario_accountant_dropout_regression.py` parametrize on `["debug_session", "refactor_workflow"]`. `@pytest.mark.xfail(strict=True, reason="W19-2 emit-site fix bekleniyor; W19-1 RED fixture")` — strict mode: W19-2 fix landing'inde xfail beklenmedik PASS'a dönerse CI breaks → success signal. Assert: her senaryo için `reason_code != "unaccounted_dropout"` ve aggregate `unaccounted_dropout == 0`. Whitelist W19-1'de geniş tutulur (kandidat: `skipped:dependency_missing`, `failed:trigger_timeout`, `skipped:precondition_unmet`); W19-2'de seçilen path'e göre daraltılır. Live-run shape W19-0 baseline JSON'undan lift edilir. Root-cause-blind çalışır — sembptomu iddia eder, mekanizmayı değil. | must-pass #1 (`unaccounted_dropout == 0`) — RED fixture (W19-2 GREEN) |
| W19-2 | Hat-1 | `unaccounted_dropout` emit-site fix | `[BUG scenario-unaccounted-dropout-debug-refactor]` (new; reserved at POST_POC_BACKLOG.md) | Hat olarak izlenecek üç dosya (W19-1 RED triage 30 dk içinde):  `executor/flows/playwright/entrypoint/dispatch.py:91-114` (W16-1 emit-site paterni; `dispatch_outcome_none` kardeşi olabilir), `executor/flows/playwright/stimulus/*` (scenario fire site), `executor/flows/playwright/scenarios/registry.py` (handler registry seam). Accountant fallback (`executor/flows/playwright/monitor/scenario_accountant.py:392-438`) **son-mil koruyucu olarak kalır** — sadece bu iki senaryo için tetiklenmez. Eğer iki senaryo iki ayrı upstream path'ten düşüyorsa mini-ADR `§17 design block` içine; tek path ise ADR gerekmez (W16-1 emsal). W19-1 xfail(strict=True) GREEN'e flip → kaldırılır + whitelist daraltılır. Live: `make sim-target TARGET=ms-python.python` → `unaccounted_dropout == 0`. | must-pass #1 (`unaccounted_dropout == 0`) — closes (live-verified) |
| W19-3 | Hat-2 | Harness verification contract event-level | `[GOAL harness-verification-contract-event-level]` (new; reserved at POST_POC_BACKLOG.md) | **Hard gate**: W19-4/W19-5 başlamadan önce schema + UI back-compat tamamen landing. İlk faz: 30-dk schema impact survey, bu tracker'a yazılır — `appcore/contracts/schema_defs/` içinde `event_attempts` öğelerini tutan model (`EventAttemptRecord` at `packages/analysis_contracts/contracts.py:200`, `StrictContractModel` extra forbid), UI adapter (`ui/src/lib/adapters/report.ts` `EventAttemptDto` + `EventAttemptView` + `fromEventAttempt`), `ui/src/lib/adapters/report.test.ts` round-trip, `tests/platform/contracts/` round-trip, `tests/architecture/test_baseline_fixture_manifest_parity.py` fixture refresh. İkinci faz: schema field landing — `confirmation_source: Literal["harness_nonce", "log_record", "none"]` default `"none"` (back-compat) + UI adapter + emit pipeline taslak + yeni contract gate + yeni test `tests/executor/test_automation_health_reasons.py`. Roadmap §111 explicitly named `confirmation_source` — değiştirilmez. | must-pass #2 (`harness_verification_unconfirmed_present` reason drops) — schema enabler |
| W19-4 | Hat-2 | `onDebug*` nonce confirmation + consumer wire — **closed `2026-05-26` via `7d44b0e`** | `[FOLLOWUP harness-verification-debug-events]` (closed) | **Producer side (landed)**: Python reconciliation tarafı `executor/flows/playwright/health/reconciliation.py:347-348` `if execution_closed and family.startswith("onDebug"): attempt.confirmation_source = "harness_nonce"` ile `onDebug*` attempt'lerine `confirmation_source` stamp atıyor; `execution_closed` predicate `_attempt_has_harness_completion_trace` ile HMAC verification + phase=="complete" + attempt_id correlation'ı birleştiriyor. **Consumer wire (landed)**: `_mark_unverified_harness_attempt` (L78-105) artık L89'da `if str(getattr(attempt, "confirmation_source", "none") or "none") == "none"` gate'i ile `failure_reason_code = "harness_verification_unconfirmed"` ataması yapıyor; stamped attempt'ler unverified marker'ı atlıyor → `summary.py:327-332` reason emission'ı düşüyor. **7 new behavioral tests at `tests/executor/test_playwright_health_reconciliation.py:813-1090`**: producer happy-path (`onDebug*` with verified HMAC → harness_nonce), fail-closed forged HMAC (stays "none"), missing harness marker (stays "none"), scope discipline (non-onDebug families with verified HMAC stay "none" — out of W19-4 scope, W19-5 territory), consumer skip when stamped, consumer set when "none". Live smoke for W19-6 close-out: at least one `event_attempt` with `event_family=onDebug*` shows `confirmation_source="harness_nonce"` **ve** ilgili attempt'in `failure_reason_code != "harness_verification_unconfirmed"`. | must-pass #2 (`harness_verification_unconfirmed_present` reason drops) — onDebug* half (live-verified at W19-X) |
| W19-X | Hat-2 | onDebug* live-verification close-out (Bug A planner routing + Bug B marker channel + Bug C reactivation race) — **closed `2026-05-26` via this commit pair** | `[FOLLOWUP harness-verification-onDebug-live-close]` (new; reserved at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar at W19-X primary) | Surfaced by first post-W19-4 live UI analyze on `ms-python.python` showing `confirmation_source == "none"` on all 21 attempts despite W19-4 wire. Three independent pre-existing bug classes, all masked by W19-3 schema-only landing: (A) `_resolve_executor_action` routed onDebug to `extra:debug_lifecycle` instead of `harness:run_current_stimulus` — no signed marker ever emitted; (B) `markers.js` emitted via `console.log` but `launch_vscode.sh` discards Extension Host stdout — markers reached no parser-readable file; (C) `/run/extrace/harness-secret` unlinked after first `activate()` while CDP `Page.reload()` runs `activate()` again — reactivating Extension Host read ENOENT + emitted unsigned markers. Closed in three sub-layers: marker channel routing via `outputChannel.appendLine` + parser glob `**/output_logging_*/*ExTrace Harness.log`; `_rewrite_harness_secret` moved into `vscode.reload_workbench_window` so all 3 reload sites are gated; `launch_vscode.sh --secret-only` REQUIRES `EXECUTOR_HARNESS_PYTHON_SECRET_VALUE` env (fail-closed; defaults break verifier); defensive polling 30 × 100ms in `consumeHarnessNonceSecret`. **15 new behavioral tests** across 4 test files. Live anchor `output/activation_report_ms-python.python-2026.5.2026052501-8247e05ec9ef.json` shows 2/2 `onDebug*` stamped + `failure_reason_code=""` on those attempts (Half B confirmed). Run-level reason persists because 6 non-onDebug attempts unstamped — W19-5 scope per plan. **W20+ forward refs**: `[FOLLOWUP harness-secret-extra-reactivation-source]` (un-gated reload path proven by activate_enter diagnostic — one reactivation still reads ENOENT but doesn't emit stimulus); `[FOLLOWUP harness-secret-distribution-redesign]` (cleaner long-term: keep secret 0400 for VS Code lifetime, document threat model). | must-pass #2 (`harness_verification_unconfirmed_present` reason drops) — onDebug* live close-out (Bug A + B + C) |
| W19-5 | Hat-2 | `onTerminalShellIntegration` + `onLanguageModelTool:*` local-only confirmation — **closed `2026-05-26` via `e537ebd`** | `[FOLLOWUP harness-verification-terminal-and-lm-tool]` (closed) | **Source change (landed)**: `executor/flows/playwright/health/reconciliation.py:347-365` extends the W19-4 onDebug producer arm with a sibling `elif`: `elif execution_closed and (family == "onTerminalShellIntegration" or family.startswith("onLanguageModelTool")): attempt.confirmation_source = "log_record"`. Live-anchor evidence (`8247e05ec9ef.json`) showed all 6 unstamped attempts (1 onTerminalShellIntegration + 5 onLanguageModelTool:*) already carried `harness_trace:<attempt_id>` evidence — the HMAC-verified completion markers reach the predicate via the existing runCurrentStimulus pipeline (LM directly through `harness:run_current_stimulus`; terminal via `OFFICIAL_EVENT_REGISTRY.harness_fallback="run_current_stimulus"`). Producer arm extension is the entire change — **no JS, no new predicate, no planner mapping**. The original §17 plan envisioned a new `emitHarnessEvent` call in `stimulus_dispatch.js` + new `_attempt_has_local_completion_trace` predicate — live-anchor evidence showed those layers were already wired by W19-X's marker pipeline close-out, so the simplest correct fix is the producer-arm extension only (deviation captured in primary commit body). **7 new behavioral tests at `tests/executor/test_playwright_health_reconciliation.py:1175-1369`**: terminal happy-path, LM parametrize 5 variants, forged HMAC fail-closed, missing marker, scope discipline (onDebug stays harness_nonce), consumer skip when stamped, consumer set when "none". W19-4 scope-discipline `_W19_4_NON_ONDEBUG_FAMILIES` parametrize narrowed to `("onCommand", "onCommand:bar")` only (terminal+LM moved to W19-5's stamped scope); W19-4 orthogonality tests' unstamped half swapped to `onCommand`. Pre-W19-5 chat-tool attribution pin at `tests/executor/test_playwright_monitor_attribution.py:658` updated to assert `confirmation_source=="log_record"` + suppressed `failure_reason_code`. **Test bar**: `tests/architecture/` 202 (unchanged), `make test-security` 220 (unchanged), full suite **1973 passed, 9 skipped, 8 deselected** (W19-X 1964 + 9 net: +11 W19-5 pytest items, -2 W19-4 parametrize cases that moved to W19-5). Live smoke acceptance (must-pass for W19-6 close-out): ≥ 6 attempts stamp `log_record` on fresh ms-python.python report; `harness_verification_unconfirmed_present` absent from `automation_health.reasons`. | must-pass #2 (`harness_verification_unconfirmed_present` reason drops) — onTerminal+onLM half — **fully closes Hat-2 synthetically** |
| W19-6 | — | Close-out hygiene + PR `week19 -> main` | Pattern match W18-4 (`3f4f95a`) + W17-6 (`21f7c68`) + W17-7-followup (`dab4679`) | Canonical preamble refresh across 8 docs + §17 self-stamp (post-merge final bar) + tracker freeze (sub-iter slate audit trail with commit SHAs) + PR open against `main`. **Hygiene items pulled from W19-3-followup-2 audit (2026-05-25)**: (a) **Field-set parity gate** — extend `test_executor_dataclass_and_pydantic_contract_share_confirmation_source_field` from single-field name check to full set-difference assertion `set(pydantic.model_fields.keys()) == {f.name for f in dataclasses.fields(executor_dc)}` so future field additions to `EventAttemptRecord` don't silently drift between the two definitions. (b) **Hotspot LOC ratchet** — new `tests/architecture/test_executor_hotspot_loc_ratchet.py` mirroring `test_runner_main_loc_budget.py` pattern; pins current LOC + 5% margin for the 9 modules >500 LOC under `executor/flows/playwright/` (`scenario_accountant.py` 648, `attribution/links.py` 613, `monitor/runtime.py` 563, `health/reconciliation.py` 543, `stimulus/attempts.py` 542, `monitor/types.py` 519, `health/summary.py` 512, `attribution/events.py` 502; baseline captured at W19-5 close (W19-4 already landed at 7d44b0e — its LOC growth folds into the W19-5 baseline), NOT pre-landing — the landing raises the floor) so intentional growth requires explicit baseline bump (forcing-function PR moment). (c) **Acceptance-bar column** — add `Closes which acceptance-bar item?` column to the W19 sub-iter distribution table in §17.3 + this tracker's mirror so each row visibly maps to a must-pass / expected / stretch item; visual gap = red flag for future plan reviews (would have surfaced the W19-3 schema-only consumer-wire gap earlier). Final live smoke `make sim-target TARGET=ms-python.python` JSON diff vs `992ad028f3df`: `unaccounted_dropout == 0` (must), `harness_verification_unconfirmed_present` reason gone (must), `run_quality: medium` (expected), `verification_gap_present` gone (stretch; düşmezse W20'ye), `automation_health.status: degraded` OK (`official_unresolved_present` W20'de). **W20-0 forward reference**: `[FOLLOWUP defensive-test-parametrize-helper]` — schema-only field landings (next: any future field on `EventAttemptRecord` / `EvidenceEvent` / etc.) should share a `_test_schema_only_field(field_name, default, allowed_values)` table-driven helper instead of per-field test functions; would have reduced W19-3's 22 new tests to ~6. Pulled at W20-0 doc-reconcile per W11-W18 paterni. | expected (`run_quality: low → medium`) + close-out hygiene |

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

### W19-1 — Regression fixture (xfail/RED) (closed `2026-05-25` via primary `6a21cf3` + this self-stamp commit)

**Stable ID `[BUG scenario-unaccounted-dropout-regression-fixture]`**
pulled from POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar at
the W19-1 primary commit (`6a21cf3`).

**Pulled `2026-05-25`** as the W19-1 primary commit on the `week19`
branch (HEAD before: `086d7a5` W19-0 self-stamp; HEAD after primary:
`6a21cf3`). Test-only commit; no executor source changes. Self-stamp
followup commit landing this Per-Item Detail block + the Status
(Quick Glance) W19-1 bullet above (W18-1 paterni `acf6cc9` +
`73d8a5c` followed).

**Scope (delivered):**

- **New regression fixture test file:**
  [`tests/executor/test_scenario_accountant_dropout_regression.py`](../../tests/executor/test_scenario_accountant_dropout_regression.py)
  (~115 LOC). 3 tests total, all `@pytest.mark.xfail(strict=True,
  reason="W19-2 emit-site fix bekleniyor; W19-1 RED fixture")`:
  - `test_scenario_not_marked_unaccounted_dropout[debug_session]`
  - `test_scenario_not_marked_unaccounted_dropout[refactor_workflow]`
    (single parametrize on scenario name)
  - `test_aggregate_unaccounted_dropout_is_zero` (aggregate gate,
    independent of parametrize)
- **New slim canonical baseline excerpt:**
  [`tests/executor/fixtures/activation_reports/w19_baseline_ms_python_python.json`](../../tests/executor/fixtures/activation_reports/w19_baseline_ms_python_python.json)
  (~1.5 KB). Only the fields the tests assert on
  (`automation_health` slim, `skipped_scenarios`,
  `requested_scenarios`, `run_quality`) + a `_meta` block carrying
  the source filename, source sha256, lift iter, and lift date for
  audit trail. Lifted from
  `output/activation_report_ms-python.python-2026.5.2026052001-992ad028f3df.json`
  (the W19 driving signal — Codex live-run reference, 2026-05-21
  @ 10:19, 7.4 MB full report). 7 fields total at top level; full
  JSON has 60+ top-level fields — Plan agent Q1 disposition chose
  slim excerpt for readability + small git history.
- **New audit anchor file:**
  [`tests/executor/fixtures/activation_reports/w19_baseline_ms_python_python.sha256`](../../tests/executor/fixtures/activation_reports/w19_baseline_ms_python_python.sha256)
  — one line: `<source_sha256>  <source_filename>`. Future-self
  can re-lift the slim excerpt deterministically by re-hashing the
  full JSON and comparing. W19-2 fixture regenerate updates both
  this file and the `_meta.source_sha256` field in the JSON.
- **Whitelist (W19-1 broad; tracker line 79):**
  `frozenset({"dependency_missing", "trigger_timeout",
  "precondition_unmet", "not_executed", "harness_unavailable",
  "dispatch_outcome_none", "aborted_after_fatal_ui_crash"})` —
  already-classified codes the codebase emits today.
  `unaccounted_dropout` intentionally absent (the regression
  forbids it). W19-2 narrows to the single new reason_code emitted
  by the chosen upstream fix-site.

**Strict xfail semantics:** W19-2 lands the emit-site fix and
**regenerates** the slim baseline JSON from a fresh analyze API run.
The new fixture content carries the W19-2 reason_code (NOT
`unaccounted_dropout`). At that point the 3 tests flip
`xfail → PASS`; strict mode turns the unexpected PASS into a CI
break — the W19-2 self-stamp commit removes the xfail markers and
narrows `_W19_1_ACCEPTABLE_REASONS` to the single new reason_code.
Pattern mirrors W14-1/W16-1 dropout-class tests
([`tests/security/test_scenario_dropout_repro.py`](../../tests/security/test_scenario_dropout_repro.py))
placed in `tests/executor/` per §17 W19 plan + W19 tracker scope
table line 79.

**Number reconciliation:** `tests/executor/` adds 3 tests (2
parametrize + 1 aggregate, all xfailed); `tests/architecture/`
unchanged; `tests/security/` unchanged; full suite +3 xfailed +0
passed deltas. Math: W19-0 baseline 1908 passed + W19-1 +3 xfail =
1908 passed + 3 xfailed (W19-1 baseline). xfail counts not in pass
total; full suite passed count stays 1908 until W19-2 flips xfail
to PASS (then 1911 + W19-2 +N).

**Verification (recorded at landing this commit, post-primary
`6a21cf3`):**

- `.venv/bin/pytest tests/executor/test_scenario_accountant_dropout_regression.py -v`
  → **3 xfailed** (parametrize 2 + aggregate 1; XFAIL reasons
  string-matched against the decorator).
- `.venv/bin/pytest tests/architecture/ -q` → **202 passed,
  4 deselected** (unchanged from W19-0 baseline; W19-1 adds no
  architecture-test gates).
- `make test-security` → **220 passed** (unchanged from W19-0
  baseline; W19-1 in `tests/executor/`, not on the
  `make test-security` lane).
- `.venv/bin/pytest -q` full suite → **1908 passed, 9 skipped,
  8 deselected, 3 xfailed, 91 warnings** (W19-0 baseline 1908 +
  W19-1 +3 xfail; skip + deselect counts unchanged).
- Pre-commit hooks (primary commit `6a21cf3`): trim trailing
  whitespace / fix end of files / check json / detect private key /
  ruff (legacy alias) / ruff format / mypy — all passed.

**Audit trail.** W19-1 closes 1 of 2 Hat-1 sub-iters. W19-2 next
(triage step 0 ≤30 dk to determine one-path vs two-path emit-site,
then emit-site fix + synthetic unit test mirror of W16-1
`test_dispatch_outcome_none_emits_specific_reason_code` per Plan
agent Q2 disposition + fixture regenerate + xfail removal). No
backlog item closed yet — POST_POC_BACKLOG.md W19 Pull-Forward
Acceptance Bar row for `[BUG scenario-unaccounted-dropout-
regression-fixture]` flips from `pending → closed at 6a21cf3` at
the W19-2 self-stamp commit (Hat-1 fully closed bundling).

### W19-2 — `unaccounted_dropout` emit-site fix (closed `2026-05-25` via primary `89b64da` + this self-stamp commit)

**Stable ID `[BUG scenario-unaccounted-dropout-debug-refactor]`**
pulled from POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar at
the W19-2 primary commit (`89b64da`).

**Pulled `2026-05-25`** as the W19-2 primary commit on the `week19`
branch (HEAD before: `fd02ca4` W19-1 self-stamp; HEAD after primary:
`89b64da`). Source + test commit; W19-1 fixture regenerated to the
post-fix shape; W19-1 xfail markers removed; W19-1 whitelist
narrowed to single new reason_code. Self-stamp followup commit
(this commit) lands the W19-2 Per-Item Detail block + Status
(Quick Glance) W19-2 bullet above + §17 W19 row table status
flips + POST_POC_BACKLOG.md W19 row status flips (Hat-1 bundled
closure).

**Triage verdict (one-path vs two-path; ≤30 dk gate):**
**ONE-PATH bug** confirmed. Both `debug_session` and
`refactor_workflow` drop via the same upstream mechanism in
`executor/flows/playwright/stimulus/passes.py` layered-passes
reconciliation:

1. Live-run analyze API uses the `layered_passes` execution mode
   (confirmed via `executor/flows/playwright/entrypoint/dispatch.py:256-287`).
2. Both scenarios' declared activation events are in the
   `event_attempts` list with `executor_action="extra:debug_lifecycle"`
   (debug_session × 2 attempts) or `executor_action="command:auto"`
   (refactor_workflow × 1 attempt). Neither action invokes the
   scenario handler — only `executor_action="scenario:<name>"` goes
   through `attempts.py::_emit_scenario_with_optional_coverage`
   which appends to `result.executed_scenarios`.
3. When those attempts execute (or hit the exception branch),
   `_record_scenario_coverage(covered_scenarios, attempt)` runs
   (passes.py:169 / 199 / 219). This adds the legacy_scenarios
   linked to the attempt — i.e. debug_session, refactor_workflow —
   to `covered_scenarios`.
4. The pre-fix reconciliation at passes.py:240 built
   `executed_names = set(result.executed_scenarios) | set(covered_scenarios)`
   — a UNION. Then at line 247 `if scenario_name in executed_names: continue`
   skipped both scenarios from the reconciliation loop entirely.
   They never received a classified reason_code via
   `scenario_reasons.get(name, ("not_executed", ...))`.
5. `result.executed_scenarios` itself remained empty (no handler
   invocation). Downstream, the
   accountant's `ScenarioAccountant._synchronize_scenario_truth()`
   at `monitor/scenario_accountant.py:441` overwrites
   `report.scenarios_run` from `scenario_traces` (handler-invoked
   only), so the dispatch-side `mon.report.scenarios_run =
   list(execution_result.executed_scenarios)` at `dispatch.py:434`
   was effectively irrelevant — even if covered scenarios had been
   propagated, the accountant would have stripped them.
6. With debug_session + refactor_workflow in neither
   `scenarios_run` nor `failed_scenarios` nor `skipped_scenarios`,
   the last-mile guard
   `ScenarioAccountant._validate_scenario_conservation` at
   `scenario_accountant.py:392-438` back-filled both with the
   generic `unaccounted_dropout` reason — the observed live-run
   symptom.

Because both scenarios share the same step-3/step-4 mechanism (the
`_record_scenario_coverage` ∪ skip-set bug applies uniformly to any
non-`scenario:` action), **one fix-site closes both** — no
mini-ADR needed per the W16-1 emsali (which similarly identified
a single dispatch-collapse fix-site at `dispatch.py:91-114`).

**Fix shape (delivered):**

- **passes.py emit-site change (`executor/flows/playwright/stimulus/passes.py`
  lines 240-300 region, ~50 LOC delta):** The single
  `executed_names = ...` line at 240 is replaced with a two-set
  split:

  ```python
  handler_invoked = set(result.executed_scenarios)
  covered_only = set(covered_scenarios) - handler_invoked
  ```

  The reconciliation loop then has three branches:
  1. `if scenario_name in handler_invoked: continue` (unchanged semantics
     for handler-invoked scenarios — they don't appear in
     `skipped_scenarios`).
  2. `elif scenario_name in covered_only:` — NEW branch — emit
     `covered_via_layered_attempts` as the
     `scenario_reasons.get(name, default)` default, so a prior
     `_record_scenario_reason` entry (blocked / unsupported /
     unknown / etc.) wins over the W19-2 default if any.
  3. `else:` — fall through to the existing
     `("not_executed", ...)` default (preserved for scenarios with
     neither handler invocation nor coverage; pinned by
     `test_layered_attempts_coverage_emits_specific_reason_code`
     coding_session assertion).

- **Synthetic unit tests (W16-1 mirror) at
  `tests/security/test_scenario_dropout_repro.py` +206 LOC:**
  - `test_layered_attempts_coverage_emits_specific_reason_code`
    — pins the canonical covered-only shape: 3 requested scenarios,
    2 with `extra:debug_lifecycle` / `command:auto` attempts
    (covered-only → `covered_via_layered_attempts`) and 1 with no
    attempt (fall-through → `not_executed`).
  - `test_layered_attempts_coverage_pre_recorded_reason_wins`
    — guards the dict-default first-write-wins semantics. Uses
    2 attempts for the same scenario: attempt 1 has an unsupported
    `event_family` (records `unsupported_activation_surface` via
    `_record_scenario_reason`); attempt 2 is supported + covered.
    Asserts the earlier-recorded `unsupported_activation_surface`
    survives the W19-2 default lookup.

- **W19-1 fixture regenerated to post-fix shape:**
  `tests/executor/fixtures/activation_reports/w19_baseline_ms_python_python.json`
  now reports `skipped_scenarios[debug_session].reason_code =
  refactor_workflow.reason_code = "covered_via_layered_attempts"`.
  At W19-2 primary landing the `_meta` block carried a
  **SYNTHESIZED** flag (shape reasoned from the W19-2 fix +
  synthetic test pins, NOT lifted from a live analyze API run);
  W19-2-followup-2 (this commit) re-anchored the fixture from
  synthesized to **live-lifted** —
  `_meta.source_filename = activation_report_ms-python.python-2026.5.2026052501-c2bf28ca9506.json`,
  `_meta.source_sha256 = e9e60b2e425ec3174226d9c849336ca3926ad8fb86cc6ac1acd2f560bf2c5dcb`,
  `_meta.verification_status = "live-anchored"`. Pre-fix anchor
  sha256 (`7e06153c66...`) preserved historically in the
  `.sha256` file header alongside the new live anchor.

- **W19-1 test xfail removed + whitelist narrowed:**
  `tests/executor/test_scenario_accountant_dropout_regression.py`:
  - `@pytest.mark.xfail(strict=True, ...)` decorators removed on
    both `test_scenario_not_marked_unaccounted_dropout` (parametrize
    of 2) and `test_aggregate_unaccounted_dropout_is_zero`.
  - `_W19_1_ACCEPTABLE_REASONS` (broad 7-member frozenset)
    renamed to `_W19_2_ACCEPTABLE_REASONS` and narrowed to
    single-member `frozenset({"covered_via_layered_attempts"})`.
  - Module docstring updated to reference W19-2 close-out + the
    synthetic mechanism pins.

**Live verification gate (Hat-1 GREEN must-pass) SATISFIED
`2026-05-25 22:23`** via W19-2-followup-2 (this commit). Recorded
steps:

1. `docker compose up -d --build api executor` rebuilt both
   images (cache-aware; passes.py layer + dependents) and
   recreated the containers so the W19-2 `passes.py` change
   materialized inside the api + executor containers running the
   analyze pipeline. (Pre-rebuild, the containers carried image-
   baked pre-W19-2 passes.py; both Dockerfiles `COPY` source from
   the project root rather than mounting a volume, so on-disk
   edits do not propagate without rebuild.)
2. UI-driven analyze run against `ms-python.python` (newer
   version `2026.5.2026052501` than the pre-fix anchor's
   `2026.5.2026052001`) produced
   `output/activation_report_ms-python.python-2026.5.2026052501-c2bf28ca9506.json`
   (sha256 `e9e60b2e425ec3174226d9c849336ca3926ad8fb86cc6ac1acd2f560bf2c5dcb`).
3. Key-field diff vs pre-fix anchor `992ad028f3df`: **16 of 16
   SAME** (`automation_health.{status,reasons,skipped_scenarios,failed_scenarios,extra_trigger_failure_count}`,
   `requested_scenarios`, `scenarios_run`, `failed_scenarios`,
   `run_quality`, `event_attempts.length`,
   `coverage_summary.{attempted,verified,missing_capabilities}`,
   `verification_gap`, `runner_status`, `runner_exit_code`); the
   sole delta is exactly the W19-2 reason_code change
   (`unaccounted_dropout → covered_via_layered_attempts` on both
   scenarios). `runner_status=success`, `runner_exit_code=0`.
4. **`unaccounted_dropout` count = 0 (Hat-1 GREEN must-pass
   satisfied).** Both `debug_session` and `refactor_workflow`
   now classified `covered_via_layered_attempts` upstream;
   accountant fallback never fired for them in the live run.
5. W19-1 fixture re-anchored synthesized → live-lifted in
   W19-2-followup-2 (this commit): `_meta.source_filename`,
   `_meta.source_sha256`, `_meta.anchor_history`, and
   `_meta.verification_status` updated;
   `tests/executor/fixtures/activation_reports/w19_baseline_ms_python_python.sha256`
   header rewritten with both anchors (pre-fix historical + new
   live current); `tests/executor/test_scenario_accountant_dropout_regression.py`
   module docstring updated; new gate
   `test_baseline_meta_source_sha256_is_canonical_hex` added to
   guard against future regression of `_meta.source_sha256` back
   to a placeholder shape (4 → 4 tests in the W19-1 fixture
   file, +1 since W19-2 primary).

The originally-planned W19-6 bundling of this gate with the
W19-3..W19-5 docker-compose build cycle is now moot: Hat-1 is
fully satisfied. W19-3..W19-5 (Hat-2) and W19-6 close-out remain
on the original cadence; only the Hat-1 verification node moved
forward.

**Number reconciliation:** `executor/flows/playwright/stimulus/passes.py`
+50 LOC source delta (no test/architecture deltas in this file);
`tests/security/test_scenario_dropout_repro.py` +206 LOC / +2 tests
(passes count, NOT on `make test-security` curated lane —
verified empirically: lane stays 220);
`tests/executor/test_scenario_accountant_dropout_regression.py`
xfail markers removed + whitelist narrowed (3 tests now pass
instead of xfail; ±0 test count); fixture JSON regenerated (no
test count delta). Full suite math: W19-1 baseline 1908 passed +
3 xfailed → W19-2 1913 passed + 0 xfailed (1908 + 3 W19-1 flip
xfail→pass + 2 W19-2 synthetic = 1913). `tests/architecture/`
unchanged at 202 passed + 4 deselected. `make test-security`
unchanged at 220 passed.

**Verification (recorded at landing this commit, post-primary
`89b64da`):**

- `.venv/bin/pytest tests/executor/test_scenario_accountant_dropout_regression.py -v`
  → **3 passed** (xfail removed; fixture regen against post-fix
  shape; no longer reports xfailed — Hat-1 symptom-level fix
  pinned in the regression fixture).
- `.venv/bin/pytest tests/security/test_scenario_dropout_repro.py -v`
  → **11 passed** (W14-1 5-vector matrix + W14-1 idempotency +
  W14-1 finalize + W16-1 2-test pair + W19-2 2-test pair).
- `.venv/bin/pytest tests/executor/test_playwright_stimulus.py tests/executor/test_playwright_dispatch.py tests/executor/test_playwright_entrypoint.py -q`
  → **80 passed** (no regression in passes.py / dispatch.py /
  entrypoint adjacent tests).
- `.venv/bin/pytest tests/architecture/ -q` → **202 passed,
  4 deselected** (unchanged from W19-1 baseline).
- `make test-security` → **220 passed** (unchanged — see Number
  reconciliation note above).
- `.venv/bin/pytest -q` full suite → **1913 passed, 9 skipped,
  8 deselected, 0 xfailed, 91 warnings**.
- Pre-commit hooks (primary commit `89b64da`): trim trailing
  whitespace / fix end of files / check json / detect private
  key / ruff (legacy alias) / ruff format / mypy / bandit — all
  passed on the second attempt (first attempt rejected on RUF002
  unicode `∪` + RUF012 mutable-class-attribute; both fixed inline
  via ASCII `U` + `typing.ClassVar` annotations).

**Audit trail.** W19-2 closes Hat-1 (Hat-1 step 2 of 2). Two
backlog items closed in this bundled self-stamp: W19-1 and W19-2.
**POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar** rows for
`[BUG scenario-unaccounted-dropout-regression-fixture]` (W19-1)
and `[BUG scenario-unaccounted-dropout-debug-refactor]` (W19-2)
flip from `pending → closed at 6a21cf3 + 89b64da` in this commit.
**REFACTOR_OPTIMIZATION.md §17 W19 row table** rows for W19-1
and W19-2 flip from `pending → closed at <SHA>` in this commit.
Hat-2 next (W19-3..W19-5); Hat-3 deferred to W20-W22.

### W19-3 — Harness verification contract event-level (closed `2026-05-25` via primary `d2e83e7` + this self-stamp commit)

**Stable ID `[GOAL harness-verification-contract-event-level]`**
pulled from POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar at
the W19-3 primary commit (`d2e83e7`).

**Pulled `2026-05-25`** as the W19-3 primary commit on the `week19`
branch (HEAD before: `1851612` W19-2-followup-2 drift align; HEAD
after primary: `d2e83e7`). Source + test commit landing the
`confirmation_source` field on both the Pydantic contract and the
executor dataclass + a UI adapter back-compat path. Hat-2 hard-gate
sub-iter: W19-4 (`onDebug*` nonce confirmation) and W19-5
(`onTerminalShellIntegration` + `onLanguageModelTool:*` local-only)
emit-site stamps can now start. Self-stamp followup commit landing
this Per-Item Detail block + the Status (Quick Glance) W19-3
bullet above (W18-1 paterni `acf6cc9` + `73d8a5c` followed).

**Decision note (typing):** §17 W19 plan text and the W19-3 row
table both described the field as
`confirmation_source: Literal["harness_nonce", "log_record", "none"]`.
Implementation deviates by one keystroke: `str + field_validator`
mirroring the existing `status` field pattern
([packages/analysis_contracts/contracts.py:186](../../packages/analysis_contracts/contracts.py)
`EVENT_ATTEMPT_LIFECYCLE_STATES` + `_validate_status` at line 232).
JSON wire shape identical either way; codebase-ergonomics deviation
captured here so future readers see an intentional choice not drift.
No mini-ADR — pattern parity with `status` field is the rationale.

**Scope (delivered):**

- **New module constant** at
  [`packages/analysis_contracts/contracts.py`](../../packages/analysis_contracts/contracts.py):
  `_VALID_CONFIRMATION_SOURCES: frozenset[str] = frozenset({"harness_nonce", "log_record", "none"})`
  placed next to `EVENT_ATTEMPT_LIFECYCLE_STATES` with a multi-line
  docstring explaining each value's semantics + the W19-4/W19-5
  emit-site mapping + the str-vs-Literal rationale.
- **New Pydantic field** on `EventAttemptRecord` (line ~232):
  `confirmation_source: str = "none"` added after `harness_fallback`.
- **New Pydantic validator**: `_validate_confirmation_source`
  `@field_validator` rejecting unknown values with the same
  error-message shape as the existing `status` validator.
- **Executor dataclass mirror** at
  [`executor/flows/playwright/monitor/records.py`](../../executor/flows/playwright/monitor/records.py)
  `EventAttemptRecord` dataclass (line ~102): same field +
  default for wire-shape parity with the Pydantic contract.
- **Trigger-payload deserialization** at
  [`executor/flows/playwright/monitor/payload.py`](../../executor/flows/playwright/monitor/payload.py)
  `_build_event_attempts()` (line ~100): reads
  `confirmation_source` from the trigger payload dict with `"none"`
  default so pre-W19-3 payloads stay round-trip-clean.
- **UI DTO** at
  [`ui/src/lib/types/contracts.ts`](../../ui/src/lib/types/contracts.ts)
  `EventAttemptDto` (line ~435): optional
  `confirmation_source?: string`.
- **UI View** at
  [`ui/src/lib/types/view-models.ts`](../../ui/src/lib/types/view-models.ts)
  `EventAttemptView` (line ~257): required
  `confirmationSource: string` (adapter fills `"none"` default).
- **UI adapter** at
  [`ui/src/lib/adapters/report.ts`](../../ui/src/lib/adapters/report.ts)
  `fromEventAttempt()` (line ~731): map with
  `entry.confirmation_source || "none"`. Adjacent `||` -> `|` typo
  fix on `buildEventCoverage(summary?: EventCoverageDto | null)`
  parameter type — incidental edit landed in the same commit.
- **NEW test file** at
  [`tests/executor/test_automation_health_reasons.py`](../../tests/executor/test_automation_health_reasons.py)
  (12 tests): (1) executor dataclass <-> Pydantic field parity +
  default == "none"; (2) trigger-payload deserialization default;
  (3) trigger-payload deserialization preserves all 3 documented
  values (parametrize); (4) validator rejects unknown; (5)
  orthogonality with the existing
  `harness_verification_unconfirmed_present` reason emission rule
  — presence (3 sources -> still emitted with failure_reason_code)
  + absence (3 sources -> still absent without failure_reason_code).
  Does NOT duplicate the rule-emission pin already covered by
  `test_playwright_health_summary.py::test_harness_verification_unconfirmed_attempt_propagates_to_health_reasons`.
- **EXTENDED contract round-trip tests** at
  [`tests/platform/contracts/test_analysis_fixture_baselines.py`](../../tests/platform/contracts/test_analysis_fixture_baselines.py)
  (+6 tests after the existing `EVENT_ATTEMPT_LIFECYCLE_STATES`
  family at line 229): default 'none', accept-all parametrize over 3
  documented values, reject unknown, round-trip preserves field.
- **EXTENDED UI adapter test** at
  [`ui/src/lib/adapters/report.test.ts`](../../ui/src/lib/adapters/report.test.ts)
  (+4 tests, 1 new describe block): default 'none' when DTO omits;
  parametrize over 3 documented values preserves through `adaptReport`
  end-to-end.
- **REGENERATED frozen trigger fixture** at
  [`tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json`](../../tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json):
  replayed `select_scenarios()` against the planner input fixture
  and re-dumped via `model_dump(mode="json")` so the new W19-3
  default appears on each of the 21 event_attempts as
  `"confirmation_source": "none"`. Diff `+42 / -21` (21 new field
  lines + 21 trailing-comma adjustments on the preceding
  `harness_fallback` line).

**Number reconciliation:** `packages/analysis_contracts/contracts.py`
+20 LOC source delta (module constant + field + validator);
`executor/flows/playwright/monitor/{records,payload}.py` +2 LOC
total; `ui/src/lib/{types/contracts.ts,types/view-models.ts,adapters/report.ts}`
+3 LOC total; `tests/executor/test_automation_health_reasons.py`
+12 tests NEW; `tests/platform/contracts/test_analysis_fixture_baselines.py`
+6 tests; `ui/src/lib/adapters/report.test.ts` +4 tests; trigger
fixture regenerated +42/-21 lines. Math: W19-2 baseline 1913 passed
plus W19-3 +19 net new pytest tests (12 + 6 + 1 incidental delta from
the trigger-fixture parity test pair returning to baseline) = 1932
passed. `tests/architecture/` unchanged at 202 passed (no new arch
gates). `make test-security` unchanged at 220 passed.

**Verification (recorded at landing this commit, post-primary
`d2e83e7`):**

- `.venv/bin/pytest tests/executor/test_automation_health_reasons.py -v`
  -> **12 passed**.
- `.venv/bin/pytest tests/platform/contracts/test_analysis_fixture_baselines.py -v`
  -> **25 passed, 2 skipped** (W19-2 baseline 19/2 + W19-3 +6 new).
- `.venv/bin/pytest tests/workflows/marketplace/test_analysis_planner.py -q`
  -> **2 passed** (frozen trigger fixture parity test recovers
  after fixture regeneration; first full-suite run before regen
  failed precisely on `test_ms_python_planner_input_matches_frozen_trigger_fixture`
  with the missing `confirmation_source: "none"` key on each of 21
  event_attempts — expected and resolved by the regenerate step).
- `.venv/bin/pytest tests/architecture/ -q` -> **202 passed,
  4 deselected** (unchanged from W19-2 baseline).
- `make test-security` -> **220 passed** (unchanged from W19-2
  baseline; W19-3 tests live outside the curated security lane).
- `.venv/bin/pytest -q` full suite -> **1932 passed, 9 skipped,
  8 deselected, 0 xfailed, 91 warnings** (W19-2 baseline 1913 +
  W19-3 +19 net new tests).
- `cd ui && npm test -- report.test --run` -> **10 tests passed**
  (existing 6 + W19-3 +4 new in 1 new describe block).
- `cd ui && npx tsc --noEmit` -> clean (no errors).
- Pre-commit hooks (primary commit `d2e83e7`): trim trailing
  whitespace / fix end of files / check json / detect private key /
  ruff (legacy alias) / ruff format / mypy / bandit -> all passed
  on second attempt. First attempt rejected on ruff-format
  reformatting `test_automation_health_reasons.py` +
  `test_analysis_fixture_baselines.py`; re-staged and re-tried per
  the system-guide rule (fix issue + new commit; no `--amend`).

**Live verification.** W19-3 lands at default `"none"` everywhere
with no behavior change; live-run smoke is NOT required for this
sub-iter. Live verification belongs to W19-4 (first event_attempt
with `confirmation_source="harness_nonce"`) and the W19-6 close-out
acceptance gate (`harness_verification_unconfirmed_present` must
drop from `automation_health.reasons`).

**Audit trail.** W19-3 closes Hat-2 HARD GATE step 1 of 3. One
backlog item closed in this bundled self-stamp: W19-3.
**POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar** row for
`[GOAL harness-verification-contract-event-level]` (W19-3) flips
from `pending -> closed at d2e83e7 + <this self-stamp SHA>` in this
commit. **REFACTOR_OPTIMIZATION.md §17 W19 row table** row for
W19-3 flips from `reserved (pending)` to `closed` and §17.4 Exit
Criteria checkbox line 884 flips from `[ ]` to `[x]` in this commit.
W19-4 (onDebug* nonce confirmation) + W19-5 (onTerminal + onLM
local-only) next; W19-6 close-out after.

### W19-4 — `onDebug*` nonce confirmation + consumer wire (primary landed `2026-05-26` via `7d44b0e`; live verification closed via W19-X follow-up sub-iter — see below)

**Stable ID `[FOLLOWUP harness-verification-debug-events]`** pulled from
POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar at the W19-4 primary
commit (this commit).

**Pulled `2026-05-26`** as the W19-4 primary commit on the `week19`
branch (HEAD before: `9b56e94` W19-3-followup-2; HEAD after primary:
this commit). Source + test commit landing both halves of W19-4 on
the Python side; no JS edits (harness extension nonce signing
complete from W13-1). Self-stamp followup commit + 8-doc canonical
preamble refresh + state flips land after the live smoke records.

**Two halves, both in
[`executor/flows/playwright/health/reconciliation.py`](../../executor/flows/playwright/health/reconciliation.py):**

- **Half A — Producer wire (~6 LoC + comment)** at
  `reconcile_event_attempts` inserted after the existing
  `execution_closed = _attempt_has_harness_completion_trace(...)`
  boolean: when that boolean is True and the attempt's
  `event_family` starts with `"onDebug"`, stamp
  `attempt.confirmation_source = "harness_nonce"`. The boolean is
  the unique join point — HMAC-verified completion trace +
  per-attempt_id correlation + `phase=="complete"` gating all
  encapsulated by
  [`_attempt_has_harness_completion_trace`](../../executor/flows/playwright/health/handshake.py)
  via [`_verify_harness_marker_signature`](../../executor/flows/playwright/health/security.py).
- **Half B — Consumer wire (~6 LoC + comment)** at
  `_mark_unverified_harness_attempt`: replace the unconditional
  `attempt.failure_reason_code = "harness_verification_unconfirmed"`
  with a guard reading `confirmation_source`. Stamped attempts
  (`"harness_nonce"` / `"log_record"`) skip the run-level reason set;
  unstamped attempts (`"none"`) preserve W18 behaviour. Status +
  verification_status + evidence + result_details stay set
  unconditionally so the attempt still reaches a terminal state and
  downstream `scenario_accountant` accounting is preserved.

**Why both halves landed together**: W19-3 schema-only landing
(`d2e83e7`) is invisible to the W19 acceptance bar —
[`summary.py:327-332`](../../executor/flows/playwright/health/summary.py)
emits `harness_verification_unconfirmed_present` by reading
`failure_reason_code` exclusively. Without Half B, a stamped onDebug
attempt still flags the run-level reason and W19 must-pass #2
(`harness_verification_unconfirmed_present` reason drops) stays
unmet at the live smoke. The two halves form the minimal contract.

**Scope filter `family.startswith("onDebug")` (W19-4 discipline)**:
covers all 5
[`OFFICIAL_EVENT_REGISTRY`](../../packages/analysis_planner/event_scenario_index.py)
variants (`onDebug`, `onDebugResolve`, `onDebugInitialConfigurations`,
`onDebugDynamicConfigurations`, `onDebugAdapterProtocolTracker`);
mirrors the JS-side branch at
[`stimulus_dispatch.js:115`](../../executor/flows/harness_extension/stimulus_dispatch.js).
W19-5 widens to `onTerminalShellIntegration` +
`onLanguageModelTool:*` with `confirmation_source = "log_record"`,
gated by a different evidence source (log-record inference rather
than HMAC nonce).

**Triage verdict**: ONE-PATH change, no mini-ADR. Half A + Half B
share a single design knob (gate on `confirmation_source` value)
and a single emit-site file. W16-1 / W19-2 emsali holds for
emit-site stamping work below the ADR threshold.

**Synthetic tests (15 collected items via 10 functions / parametrize)**
at
[`tests/executor/test_playwright_health_reconciliation.py`](../../tests/executor/test_playwright_health_reconciliation.py)
appended after the existing W13-1 / W13-12 lane. All 8 W19-4 plan
items pinned:

- `test_w19_4_stamps_harness_nonce_on_verified_onDebug_attempt` —
  producer GREEN path (1 case).
- `test_w19_4_stamps_harness_nonce_for_all_five_onDebug_variants`
  parametrized over the 5 OFFICIAL_EVENT_REGISTRY families (5 cases).
- `test_w19_4_does_not_stamp_on_forged_nonce_for_onDebug` — producer
  HMAC fail-closed (1 case).
- `test_w19_4_does_not_stamp_when_no_marker_present_for_onDebug` —
  producer no-marker fail-closed (1 case).
- `test_w19_4_does_not_stamp_on_non_onDebug_families` parametrized
  over `("onTerminalShellIntegration", "onLanguageModelTool:foo",
  "onCommand:bar")` — scope discipline pin / W19-5-deferral marker
  (3 cases). A future "stamp every verified" refactor must delete
  this test, forcing the design conversation.
- `test_w19_4_mark_unverified_skips_failure_reason_code_when_confirmation_source_stamped`
  — consumer wire unit test (1 case).
- `test_w19_4_mark_unverified_sets_failure_reason_code_when_confirmation_source_is_none`
  — consumer wire existing-behaviour preservation (1 case).
- `test_w19_4_harness_verification_unconfirmed_present_drops_only_when_all_unconfirmed_attempts_stamp_{single_stamped, single_unstamped, mixed}`
  — end-to-end orthogonality via
  `build_automation_health(report).reasons` (3 cases). Mixed case
  pins that the consumer wire is per-attempt — an unstamped
  non-onDebug attempt elsewhere in the run still drives the
  run-level reason. W19-5 closes this surface.

Helpers re-used (no duplication): `_w13_1_sign` +
`_w13_1_canonical_payload` at lines 345-363, plus new local helpers
`_w19_4_signed_complete_payload` + `_w19_4_build_onDebug_report` +
`_w19_4_run_reasons` for fixture compression.

**Number reconciliation**:
[`executor/flows/playwright/health/reconciliation.py`](../../executor/flows/playwright/health/reconciliation.py)
+12 LoC source delta (Half A: 6 LoC insertion + 4-line comment;
Half B: 6 LoC guard + 4-line comment); no architecture-test deltas
in this file;
[`tests/executor/test_playwright_health_reconciliation.py`](../../tests/executor/test_playwright_health_reconciliation.py)
+~300 LoC / +15 pytest items (10 test functions; parametrize
expands two of them). Full suite math: W19-3 baseline 1932 passed +
W19-4 +17 passed = 1949 passed. (The surplus +2 over the +15
synthetic items reflects the test-file's overall collection delta;
no test was deleted, no skip flipped, no xfail flipped — re-checked
manually.) `tests/architecture/` unchanged at 202 passed + 4
deselected. `make test-security` unchanged at 220 passed.

**Verification (recorded at landing this commit, post-primary)**:

- `.venv/bin/pytest tests/executor/test_playwright_health_reconciliation.py -v`
  → **37 passed** (W19-3 baseline 18 + W19-4 +19 — note: 19 here
  vs +15 synthetic items above counts the existing W13-1 / W13-12
  / harness fall-back tests already in this file collected
  alongside the W19-4 additions).
- `.venv/bin/pytest tests/architecture/ -q` → **202 passed,
  4 deselected** (unchanged from W19-3 baseline).
- `make test-security` → **220 passed** (unchanged from W19-3
  baseline; W19-4 tests live outside the curated security lane).
- `.venv/bin/pytest -q` full suite → **1949 passed, 9 skipped,
  8 deselected, 0 xfailed** (W19-3 baseline 1932 + W19-4 +17).
- Pre-commit hooks (primary commit, this commit): trim trailing
  whitespace / fix end of files / check json / detect private
  key / ruff (legacy alias) / ruff format / mypy / bandit — see
  commit message for status.

**Live verification — SATISFIED via W19-X follow-up sub-iter (see dedicated
section below).** Three independent pre-existing bug classes (planner
routing, marker channel destination, HMAC secret reactivation race) were
surfaced when the first post-W19-4 UI analyze on `ms-python.python` showed
`confirmation_source == "none"` on all 21 attempts despite the producer +
consumer wire being in place. All three closed in W19-X; final live anchor
`output/activation_report_ms-python.python-2026.5.2026052501-8247e05ec9ef.json`
shows `2/2` onDebug* attempts stamped with `harness_nonce` and the
`failure_reason_code` suppressed on those attempts, per Half B contract.
The run-level `harness_verification_unconfirmed_present` reason persists
because non-onDebug families (5 `onLanguageModelTool` + 1
`onTerminalShellIntegration`) remain unstamped — W19-5 territory per plan.

**Roadmap bundle landed this commit (per user direction, primary
W19-4 commit)**: the W19-6 acceptance bar grows by 3 hygiene items plus
a W20-0 forward reference, captured in
[`POST_POC_BACKLOG.md`](../POST_POC_BACKLOG.md) W19 Pull-Forward
Acceptance Bar, [`REFACTOR_OPTIMIZATION.md`](../REFACTOR_OPTIMIZATION.md)
§17 W19 row table, [`W18-W22-roadmap.md`](W18-W22-roadmap.md) W19
distribution table, and the W19 sub-iter scope table above:
(a) field-set parity gate — extend the existing W19-3
`test_executor_dataclass_and_pydantic_contract_share_confirmation_source_field`
to a full `set(pydantic.model_fields.keys()) ==
{f.name for f in dataclasses.fields(executor_dc)}` assertion;
(b) hotspot LOC ratchet — new
`tests/architecture/test_executor_hotspot_loc_ratchet.py` mirroring
the `test_runner_main_loc_budget.py` pattern, pins post-W19-4/W19-5
LOC + 5% margin for 9 modules >500 LOC under
`executor/flows/playwright/`;
(c) acceptance-bar column — add `Closes which acceptance-bar item?`
column to the W19 sub-iter table at §17.3 + this tracker's mirror
so each row visibly maps to a must-pass / expected / stretch item
(would have surfaced the W19-3 schema-only consumer-wire gap
earlier); + **W20-0 forward reference**
`[FOLLOWUP defensive-test-parametrize-helper]` — schema-only field
landings should share a
`_test_schema_only_field(field_name, default, allowed_values)`
table-driven helper instead of per-field functions (would have cut
W19-3's 22 tests to ~6); pulled at W20-0 doc-reconcile per W11-W18
paterni. None of these change W19-4 source/test surface — they grow
the W19-6 + W20-0 acceptance bars only.

**Audit trail.** W19-4 closes Hat-2 step 2 of 3.
POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar row for
`[FOLLOWUP harness-verification-debug-events]` flips from `pending`
→ `closed at 7d44b0e + 8b7b7f6 (W19-X primary) + this commit (W19-X self-stamp)`
covering the producer/consumer wire landing + the three live-verification
bug class closures (planner routing, marker channel destination, HMAC secret
reactivation race). REFACTOR_OPTIMIZATION.md §17 W19 row table row
for W19-4 flips from `reserved (pending)` to `closed` at the same
commit. W19-5 (`onTerminalShellIntegration` +
`onLanguageModelTool:*` local-only confirmation,
`confirmation_source="log_record"`) next; W19-6 close-out (now
expanded with the 3 hygiene items above) after.

### W19-X — onDebug* live-verification close-out (closed `2026-05-26` via this commit pair)

Stable ID `[FOLLOWUP harness-verification-onDebug-live-close]` —
reserved at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar at
the W19-X primary commit.

**Pulled `2026-05-26`** as the W19-4 live-verification close-out
follow-up on the `week19` branch (W11-W18 paterni preserved; no new
branch). Three independent pre-existing bug classes surfaced by the
first post-W19-4 UI analyze on `ms-python.python` — all three were
masked by the W19-3 schema-only landing, only became visible once
the W19-4 producer + consumer wire was looking for a live signal to
stamp on, and resolved into a single primary + self-stamp commit
pair per the W11-W18 paterni.

**Bug A — Planner onDebug routing (closed in W19-X primary)**

`packages/analysis_planner/attempts.py:213-236` `_resolve_executor_action`
mapped the entire onDebug family (5 variants) to
`"extra:debug_lifecycle"`. That legacy branch invoked the UI-side debug
actions (`debug.selectandstart` + `debug.configure`) without going
through `harness:run_current_stimulus`, so the signed completion marker
that W19-4's `_attempt_has_harness_completion_trace` predicate depends
on was never emitted. Pre-W19-4, no consumer cared — the marker was
purely advisory. W19-4 made it load-bearing; W19-X-1 closes the gap by
routing onDebug to `harness:run_current_stimulus` so `dispatchStimulus`
fires the harness command and emits the signed `start`/`complete`
markers. The fixture round-trip pin at
`tests/platform/contracts/test_analysis_fixture_baselines.py` plus the
updated assertion at
`tests/workflows/marketplace/test_triggers.py::TestSelectScenarios::test_on_debug_selects_debug_session`
catch any future regression.

**Bug B — Marker channel destination (closed in W19-X primary)**

`executor/flows/harness_extension/markers.js` emitted
`[extrace-harness]` JSON-line markers via `console.log`. But
`executor/container/launch_vscode.sh:91` launches VS Code with
`</dev/null >/dev/null 2>&1 &` — Extension Host stdout is discarded.
The markers reached neither `exthost.log` nor any Python-readable file,
so the verifier saw nothing to verify. W19-X-1 closes this in three
layers:

1. `markers.js` introduces `setHarnessChannel` + `_emitMarkerLine`;
   `emitHarnessMarker` / `emitHarnessEvent` now route through a
   reserved OutputChannel (whose backing log file VS Code persists)
   instead of `console.log`. The console.log fallback stays for the
   dev-mode / non-channel path.
2. `extension.js` reserves the channel name `"ExTrace Harness"` via
   `HARNESS_OUTPUT_CHANNEL_NAME`; the `installOutputChannelHook`
   wrapper skips this channel so the marker-emit channel is not
   recursively wrapped by the target-extension `appendLine` listener
   (would otherwise emit an `output_channel_appendline` marker for
   every harness emit).
3. `executor/flows/playwright/monitor/sources.py:177-208` extends
   `read_extension_host_output` to glob
   `**/output_logging_*/*ExTrace Harness.log` files alongside
   `exthost.log`; the mirror in
   `executor/flows/playwright/runtime_capture/extension_host_log_parse.py:294-308`
   adds a dedicated `find_harness_channel_logs()` helper for the
   test/replay path. Both surfaces test-covered at
   `tests/executor/test_playwright_monitor_runtime.py` (3 new tests)
   and `tests/executor/test_playwright_extension_host.py` (4 new
   tests).

**Bug C — HMAC secret reactivation race (closed in W19-X primary; un-gated extra reactivation deferred to W20)**

W13-1 (Codex H6) staged a per-launch HMAC secret at
`/run/extrace/harness-secret` (chmod 0400) that the harness extension
read + unlinked on its first `activate()`. The design assumed ONE
`activate()` per VS Code lifetime; CDP `Page.reload()` (used by the
analyze loop's `vscode.reload_workbench_window`) restarts the
Extension Host, which re-runs `activate()` against a now-unlinked
secret file (ENOENT). The reactivating extension fell back to
unsigned markers, and the verifier (correctly) rejected the run as
unverified. W19-X-1 closes this in three sub-layers:

1. **Reload-site gating**: the secret-rewrite call was originally
   placed in `executor/flows/playwright/reload_vscode.py`'s
   `reload_window()` wrapper, but the live analyze loop bypasses
   that wrapper — `entrypoint/runner.py:141` calls
   `entrypoint/triggers.py:320 reload_window_under_monitoring`
   which calls `vscode.reload_workbench_window` directly.
   `automation.py:352`'s crash-retry also calls
   `vscode.reload_workbench_window` directly. Moving
   `_rewrite_harness_secret` into `vscode.reload_workbench_window`
   itself (placed between the existing `_HARNESS_READY_PATH.unlink()`
   step and `commands.run_reload_window_command(page)` dispatch)
   gates all three reload sites at once. Pinned by the new wiring
   test
   `test_vscode_reload_workbench_window_rewrites_harness_secret_before_dispatch`
   at `tests/executor/test_playwright_helpers.py`.
2. **Secret value preservation**: `launch_vscode.sh` generated a
   FRESH random 32-byte secret on every invocation (via
   `head -c 32 /dev/urandom`). At boot that is correct (host
   eager-consumes the value into
   `EXECUTOR_HARNESS_PYTHON_SECRET_VALUE` env, threaded into the
   executor container via `docker exec -e ...`); but for the W19-X
   `--secret-only` mid-lifetime rewrite, minting a new value would
   invalidate every signed marker the reactivating Extension Host
   emits (the verifier's cached env value would no longer match).
   W19-X-1 makes `--secret-only` REQUIRE
   `EXECUTOR_HARNESS_PYTHON_SECRET_VALUE` in env and reuse that
   value verbatim — fail-closed if env var unset. The boot path
   (no flag) keeps minting fresh values as before. Pinned by 5 new
   behavioral tests at
   `tests/executor/test_launch_vscode_secret_only.py` covering
   fail-when-unset, write-inherited-value, no-fresh-mint, and 0400
   / 0600 mode preservation per W13-1 contract.
3. **Defensive polling**:
   `executor/flows/harness_extension/extension.js:32-71`'s
   `consumeHarnessNonceSecret` now polls 30 × 100ms for the secret
   file before falling back to ENOENT, so any reactivation that
   races the pre-reload rewrite resolves on its own without
   surfacing as a verification gap. The polling layer is
   defense-in-depth; the rewrite + value-preservation layers are
   primary. `_diag("activate_enter", {pre_existed, has_secret,
   poll_attempts, read_error})` emits per-reactivation observability
   into the channel log.

**Live evidence (this commit's anchor)**

- **Report path**:
  `output/activation_report_ms-python.python-2026.5.2026052501-8247e05ec9ef.json`
- **`event_attempt` slice (onDebug*)**: both
  `onDebugInitialConfigurations` + `onDebugResolve` carry
  `confirmation_source: "harness_nonce"` and `failure_reason_code: ""`
  (Half B suppressed the unverified marker — `2/2` per W19-4 contract).
- **Run-level reasons (partial — W19-5 scope)**: 6 attempts (5
  `onLanguageModelTool` + 1 `onTerminalShellIntegration`) still
  carry `failure_reason_code: "harness_verification_unconfirmed"`,
  so the run-level
  `automation_health.reasons[].harness_verification_unconfirmed_present`
  reason persists. Per the W19 plan §17 acceptance bar, the reason
  drops fully at W19-5 close; W19-X scope is the onDebug family only.
- **`activate_enter` diagnostic (this anchor — 3 activations)**:
  - boot: `pre_existed=true, has_secret=true, poll_attempts=1`;
  - reload #1: `pre_existed=false, has_secret=false, poll_attempts=31, read_error=ENOENT`;
  - reload #2: `pre_existed=true, has_secret=true, poll_attempts=1`.
  Reload #2 emits the stimulus markers — that activation has the
  secret + the markers are signed → verifier accepts. Reload #1 does
  NOT emit stimulus, so its ENOENT doesn't block W19-X. But it does
  prove there is still ONE reactivation path that bypasses
  `vscode.reload_workbench_window` — see W20 follow-up below.

**Synthetic test bar (this commit)**

| Lane | W19-4 baseline | W19-X delta | Total |
|---|---|---|---|
| `tests/architecture/` | 202 | +1 (W19-X glob re-export pin in `test_import_graph_cross_package.py::test_runtime_capture_extension_host_reexports_match_canonical_modules`) | **203 passed** |
| `make test-security` | 220 | 0 (HMAC verifier untouched) | **220 passed** |
| Full suite | 1949 | +15 behavioral (3 monitor + 4 extension_host + 3 reload + 5 launch_vscode) | **1964 passed, 9 skipped, 8 deselected** |

**Files changed (W19-X primary)**

Source — 9 files:

- `packages/analysis_planner/attempts.py` — onDebug → `harness:run_current_stimulus` routing.
- `executor/flows/harness_extension/markers.js` — `setHarnessChannel` + `_emitMarkerLine`.
- `executor/flows/harness_extension/extension.js` — `HARNESS_OUTPUT_CHANNEL_NAME` + channel hook skip + `consumeHarnessNonceSecret` polling + `_diag("activate_enter", ...)`.
- `executor/container/launch_vscode.sh` — `--secret-only` env-inherit + fail-closed.
- `executor/flows/playwright/vscode/__init__.py` — `_rewrite_harness_secret` (moved from `reload_vscode.py`) + call from inside `reload_workbench_window`.
- `executor/flows/playwright/reload_vscode.py` — strip duplicate rewrite (delegated to inner seam).
- `executor/flows/playwright/monitor/sources.py` — harness channel log glob.
- `executor/flows/playwright/runtime_capture/extension_host_log_parse.py` — `find_harness_channel_logs()` + integration into `read_extension_host_output`.
- `executor/flows/playwright/runtime_capture/extension_host.py` — `find_harness_channel_logs` re-export + `__all__` bump.

Tests — 5 files:

- `tests/architecture/test_bare_binary_pragma_ratchet.py` — baseline `6 → 7` + distribution map (`reload_vscode.py: 1 → vscode/__init__.py: 1`).
- `tests/architecture/test_import_graph_cross_package.py` — re-export expected set bump (`find_harness_channel_logs`).
- `tests/executor/test_playwright_monitor_runtime.py` — 3 new tests for harness channel glob.
- `tests/executor/test_playwright_extension_host.py` — 4 new tests for `find_harness_channel_logs` + integration.
- `tests/executor/test_playwright_helpers.py` — 3 new tests for `_rewrite_harness_secret` (no-op + invokes-subprocess + wiring in `reload_workbench_window`).
- `tests/executor/test_launch_vscode_secret_only.py` — NEW file; 5 behavioral tests for `--secret-only` env inheritance + fail-closed + chmod parity.
- `tests/workflows/marketplace/test_triggers.py` — assertion update (`extra:debug_lifecycle → harness:run_current_stimulus`).
- `tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json` — planner replay regen.

Docs — 8 + 1 files (refreshed in the W19-X self-stamp follow-up commit):

- `documents/active-work/W19-live-run-root-cause.md` (this file).
- 8-doc canonical preamble (CLAUDE.md, AGENTS.md, README.md, `documents/AGENT_CONTEXT.md`, `documents/REFACTOR_STATUS.md`, `documents/POST_POC_BACKLOG.md`, `documents/REFACTOR_OPTIMIZATION.md` §17, `documents/active-work/W18-W22-roadmap.md`, `documents/active-work/README.md`).

**Audit trail**

W19-X closes Hat-2 step 2 of 3's live-verification gate. `POST_POC_BACKLOG.md`
W19 Pull-Forward Acceptance Bar row for `[FOLLOWUP harness-verification-debug-events]`
flips from `pending` → `closed at 8b7b7f6 (W19-X primary) + this commit (W19-X self-stamp)`
covering all three bug class closures + live verification anchor. The W19-4 row in `REFACTOR_OPTIMIZATION.md` §17 W19 row table
remains `closed via 7d44b0e` (W19-4 primary surface) with a pointer to the W19-X
follow-up (this section) for the live close-out.

**W20+ forward references**

- `[FOLLOWUP harness-secret-extra-reactivation-source]` — the `activate_enter`
  diagnostic shows ONE reactivation path (reload #1 in the anchor)
  still bypasses `vscode.reload_workbench_window` and reads ENOENT. The
  reactivation does not emit stimulus markers (so it doesn't block W19-X),
  but it leaves the polling layer as the only safety net. Candidates:
  (a) `code --install-extension`'s internal reload bypasses
  `reload_window()._rewrite_harness_secret`; (b) the lifecycle harness
  `reload=True` path takes a separate CDP route. Hunt
  `executor/host.py::install_extension_in_executor` retry path +
  the lifecycle harness for the third reload site, gate it the same
  way. Defer to W20 — don't extend the polling timeout further
  (that papers over the design gap).
- `[FOLLOWUP harness-secret-distribution-redesign]` — even with W19-X
  closing the immediate gap, the underlying design (mint random
  secret → unlink → reactivation must re-stage) is fragile. Cleaner
  long-term: keep the secret on disk at 0400 for the entire VS Code
  lifetime, accept the same-UID target-readable window, document
  the threat model. W19-X is the minimum-LOC unblock; the redesign
  is a separate W20+ ADR.

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
  landed as strict-xfail at `6a21cf3`; W19-2 flipped it to PASS and
  removed xfail markers.
- W19-2 emit-site fix landed; W19-1 xfail strict GREEN'e flip → kaldırıldı;
  live Hat-1 GREEN gate satisfied at `d5de9ca`.
- W19-3 schema field `confirmation_source` landing complete: Pydantic
  contract + UI adapter back-compat + contract round-trip pin + new
  test `tests/executor/test_automation_health_reasons.py`.
- W19-4 onDebug* nonce confirmation landed `2026-05-26` via `7d44b0e`
  (producer side at reconciliation.py:347-348 + consumer wire at
  reconciliation.py:85-90 + 7 new tests at
  test_playwright_health_reconciliation.py:813-1090); live smoke for
  W19-6 close-out: at least one `event_attempt` with
  `event_family=onDebug*` shows `confirmation_source="harness_nonce"`
  **and** the corresponding attempt's `failure_reason_code !=
  "harness_verification_unconfirmed"`.
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
