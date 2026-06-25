# Post-PoC Backlog

`Last Updated: 2026-06-23`

`Last merged weekly: W22 — closed synthetically on the week22 branch, merged to main via PR #31 week22 -> main 2026-05-28 via 1399f82.`

`Active stream: verdict-provenance-reproducibility (Stream 3 — B5 verdict-bound-to-bytes + B6 verdict-reproducibility; the spine; week label W26) — opened on week26 (off main 27dc7f1, 2026-06-25). Closes B5+B6; ADR 0017 (Proposed) records the design, ADR 0016 gets an additive --vsix-sha256 flag. Prior stream operator-console-honesty (UI-only console-honesty) merged to main via PR #36 (week24 -> main, 1e3fba6) on 2026-06-23. Tracker: documents/active-work/W26-verdict-provenance-reproducibility.md.`

`Sources of truth: documents/REFACTOR_STATUS.md (state) · documents/POST_POC_BACKLOG.md (deferred) · documents/REFACTOR_OPTIMIZATION.md §20 (last weekly plan) · documents/phase.json (weekly pointer + active stream).`

Open deferred work after the W0-W7 PoC acceptance bar. **Slim canonical** —
verbose closure rationales, evidence paragraphs, and per-iter Note columns
are frozen in dated snapshots. Each closed item below is one line with
stable ID + landing commit; full context in the snapshot.

- latest full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-06-15.md`](archive/backlog/POST_POC_BACKLOG_full_2026-06-15.md)
- previous full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-14.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-14.md)

W8-W18 are closed; W13 close-out PR #20 `week13 -> main` **MERGED**
`2026-05-13` via `772deb3`; W14 close-out PR #21 `week14 -> main`
**MERGED** `2026-05-14` via `4e03c8d`; W15 close-out PR #22
`week15 -> main` **MERGED** `2026-05-18` via `6161472`; W16 close-out
PR #23 `week16 -> main` **MERGED** `2026-05-18` via `1b6d43f`;
W17 close-out PR #25 `week17 -> main` **MERGED** `2026-05-18` via
`bff565d`; **W18 close-out PR #26 `week18 -> main` MERGED `2026-05-21`
via `9874e79`**.
W17-0..W17-7 sub-iter slate landed (pull-forward table below);
W18-0..W18-4 sub-iter slate + W18-4-followup post-merge audit
landed (pull-forward table below). W14 tracker:
[`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md);
W15 tracker (frozen):
[`active-work/W15-codex-uclass-bounds-posture.md`](active-work/W15-codex-uclass-bounds-posture.md);
W16 tracker (frozen):
[`active-work/W16-regression-and-audit-closeout.md`](active-work/W16-regression-and-audit-closeout.md);
W17 tracker (frozen):
[`active-work/W17-carryover-and-lifecycle-harness.md`](active-work/W17-carryover-and-lifecycle-harness.md);
W18 tracker (frozen):
[`active-work/W18-heartbeat-refactor.md`](active-work/W18-heartbeat-refactor.md).

## Stable IDs Are A Contract

Do not rename existing IDs. Current code/tests reference at least:

- `[FOLLOWUP analysis-jobs-race]`
- `[FOLLOWUP simulation-progress-cancel]`
- `[FOLLOWUP simulation-progress-cancel] cancel-after-finish race test`
- this filename from `packages/analysis_contracts/contracts.py`

Use stable IDs in new references; do not cite canonical doc line numbers.

## W13 Pull-Forward Acceptance Bar

All W13 items closed; full Note column lives in archive snapshot.

| Stable ID | Closed via |
|---|---|
| `[FOLLOWUP codex-2026-05-10-H3-dev-lan-makefile-drift]` | W13-5 |
| `[FOLLOWUP codex-2026-05-10-H4-cancel-concurrent-race]` | W13-3 |
| `[FOLLOWUP codex-2026-05-10-H5-writable-vscode-launcher]` | W13-2 |
| `[FOLLOWUP codex-2026-05-10-H6-spoofable-harness-markers]` | W13-1 |
| `[FOLLOWUP codex-2026-05-10-M1-pem-regex-dos]` | W13-7 |
| `[FOLLOWUP codex-2026-05-10-M9-arguments-preview-redaction-extension]` | W13-6 |
| `[FOLLOWUP w13-3-close-pass-cancellation-test-hardening]` | W13-4 |
| `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` | deferred (fresh-DB-per-test fixture needed) |
| `[CLOSE-GATE codex-second-opinion-F1-hmac-python-secret-target-install-race]` | W13-11 (2026-05-12) |
| `[CLOSE-GATE codex-second-opinion-F2-fail-closed-harness-handshake]` | W13-12 (2026-05-12) |
| `[CLOSE-GATE codex-second-opinion-F3-worker-start-cancel-race-CAS]` | W13-13 (2026-05-13) |

## W14 Pull-Forward Acceptance Bar

All W14 sub-iters closed (slate + post-slate hotfixes); per-iter Per-Item
Detail evidence in the W14 tracker + archive snapshot.

| Iter | Stable ID(s) | Landing commit |
|---|---|---|
| W14-1 | `[BUG scenario-dropout-upstream-root-cause]` (BLOCKER → HIGH) | `0c8bd02` |
| W14-2 | `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` + `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` | `bde17be` |
| W14-3 | `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` + `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` + `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` | `941250d` |
| W14-4 | `[FOLLOWUP analysis-jobs-race]` + `[FOLLOWUP evidence-event-kind-raw-context-invariant]` | `03b32bc` |
| W14-5 | `[GOAL w14-logger-consolidation]` + `[GOAL w14-run-id-stamping]` + `[FOLLOWUP codex-automation-5]` + `[FOLLOWUP codex-2026-05-10-M5-epoch-docker-exec-propagation]` (byproduct) | `dc79f61` + `9c095d2` + `db25d5f` |
| W14-6 | `[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]` + `[FOLLOWUP arch-gate-executor-control-outbound]` + `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]` | `2adad43` + `b031803` + `e42a448` |
| W14-7 | `[FOLLOWUP w14-container-shipping-regression]` (post-slate hotfix) | `df925f8` + `c11ebd8` |
| W14-8 | `[FOLLOWUP w14-container-python-compat-gate]` (post-slate preventive) | `5638f82` |

## W15 Pull-Forward Acceptance Bar

All W15 sub-iters closed and merged via PR #22 on `2026-05-18` (`6161472`);
per-iter Per-Item Detail evidence in the W15 tracker + archive snapshot.

| Iter | Stable ID(s) | Landing commit |
|---|---|---|
| W15-1 | `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]` + post-slate typing hotfix | `c58c365` + `976dc96` |
| W15-2 | `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]` | `765cde7` |
| W15-3 | `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]` | `3512a7c` |
| W15-4 | `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]` + `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]` | `89e13e3` |
| W15-5 | `[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]` + `[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]` | `43d6438` |
| W15-6 | `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]` (ADR 0011 Accepted + implemented, Option A) | `be52520` (Proposed at `e41722e`) |
| W15-7 | `[FOLLOWUP compose-image-mutable-ref-pin]` + `[FOLLOWUP gh-action-trivy-version-pin]` + close-out hygiene | `54e7a93` + `7ebbbfb` + `452f1a1` + `7ff31d9` (early pulls `a7a876e` + `2573e35`) |

## W16 Pull-Forward Acceptance Bar

W16 closed `2026-05-18` and merged via PR #23 `week16 -> main`
(`1b6d43f`). All rows below are closed audit trail; full Per-Item
Detail evidence in the frozen tracker
[`active-work/W16-regression-and-audit-closeout.md`](active-work/W16-regression-and-audit-closeout.md).

| Iter | Stable ID(s) (planned) | Landing commit |
|---|---|---|
| W16-1 | `[FOLLOWUP scenario-accountant-conservation-split]` (W14-1 root-cause split; HIGH prod regression — dispatch-layer outcome=None emit-site closed) | `01f910a` |
| W16-2 | `[FOLLOWUP analysis-job-worker-entry-crud-ownership]` (W15 audit finding; row-lock-aware lifecycle CRUD primitive — closed at facade boundary) | `9d6d110` |
| W16-3 | `[FOLLOWUP report-finalize-top-level-field-sync-drift]` (W14 production scan-driven investigation — null-leakage half closed at contract seam; attribution-count parity split to follow-up) | `fa430f2` |
| W16-4 | `[FOLLOWUP health-reconciliation-responsibility-split]` (W15 audit finding; behavior-preserving extraction; W13-1 HMAC + W13-12 fail-closed gates preserved) | `304b99f` |
| W16-5 | `[FOLLOWUP simulation-progress-cancel]` umbrella (3 sub-items) — scope reduced: `dedupe-step-progress-schemas` **rejected** (distinct surface roles), `heartbeat-sandbox-reset-off-thread` + `heartbeat-refactor` **deferred to W17+** (lifecycle harness prerequisite). | documented in tracker (no code commit) |
| W16-6 | `[CLEANUP marketplace-router-test-suite-split]` (2374 LoC → 5 endpoint-grouped files) + `[CLEANUP test-import-graph-policy-dump-split]` (767 LoC → 4 thematic files) + `[FOLLOWUP w13-4-alembic-roundtrip-programmatic]` (skip removed; `fresh_alembic_engine` per-test throwaway Postgres DB) | `d40bb01` |
| W16-7 | close-out hygiene + canonical preamble refresh + W16 tracker freeze + `week16 -> main` close-out PR + post-PR `unaccounted_dropout` surface pin (security lane 217 → 220) | `8bf3c6b` + `78f080e` (post-PR top-up); PR #23 MERGED `2026-05-18` via `1b6d43f` |

## W17 Pull-Forward Acceptance Bar

W17 phase work complete `2026-05-18` on the `week17` branch (per user
direction 2026-05-18; W11-W16 paterni preserved); W17 closed via
PR #25 `week17 -> main` MERGED `2026-05-18` via `bff565d`. All rows
below are closed audit trail; full Per-Item Detail evidence in the
frozen tracker
[`active-work/W17-carryover-and-lifecycle-harness.md`](active-work/W17-carryover-and-lifecycle-harness.md).

| Iter | Stable ID(s) (planned) | Landing commit |
|---|---|---|
| W17-0 | doc-direction reconcile — `week17` branch + `week17 -> main` close-out PR wording across canonical docs; W11-W16 paterni preserved | `4508c2e` |
| W17-1 | `[FOLLOWUP attribution-count-parity]` (W16-3 carry-over; producer-side fix at `build_evidence_bundle` activation emit-site — `is_target_extension_event` stamp; 4 invariant tests including parity contract pin) | `8c26d02` |
| W17-2 | lifecycle harness scaffold (W17-3/4 enabler) — `LifecycleHarness` + `lifecycle_harness` fixture at `tests/workflows/marketplace/test_lifecycle_harness.py` composing `test_engine` + per-test UUID `AnalysisJob` row + mocked `ExecutorControl` (reset_sandbox call recorder w/ thread identity) + spawnable `_run_monitoring_heartbeat` thread; smoke test pins cancel-via-heartbeat path (thread = `harness-monitoring-heartbeat`, kwargs = `reload_window=True`, CAS = `WorkerEntryOutcome.CLAIMED`). Scope cut: harness does NOT drive `run_analysis_job` end-to-end, does NOT use `fresh_alembic_engine` (UUID-keyed rows + cleanup-delete suffice). W17-3 extension points listed in module docstring. | `ff98235` |
| W17-3 | `[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread` — **scope-reduced 2026-05-18 (doc-only)**: harness prerequisite (W17-2) met, but the refactor shape is **DESIGN-NEEDED** (worker-thread step-1 reset is a HARD SYNC POINT for W13-11 HMAC secret; heartbeat thread starts only at step 4; multiple plausible refactor shapes have different invariant cost). Deferred to W18 dedicated sub-iter that opens with a design ADR / §16 plan entry. | _deferred to W18 (doc-only this iter)_ |
| W17-4 | `[FOLLOWUP simulation-progress-cancel] heartbeat-refactor` — **scope-reduced 2026-05-18 (doc-only)**: bundled with W17-3 thread-relocation design decision; refactoring heartbeat shape in isolation before deciding the thread destination would land throw-away work. W18 pulls both together. | _deferred to W18 (doc-only this iter)_ |
| W17-5 | hygiene cleanup batch — `[CLEANUP postgres-version-fact-drift]` closed (`seed_project_2.py` synthetic-fixture `postgres:15 -> postgres:16-alpine` stack alignment); other four candidates (`env-example-extrace-vars`, `adr-0007-runbook-wording-drift`, `pre-commit-python-version-alignment`, `report-builder-naming` / alt: `monitor-runtime-naming-overlap`) deferred to W18+ opportunistic pull-as-found (lack inline scope descriptions, need per-item owner discovery) | `394d40d` |
| W17-6 | **closed `2026-05-18`** via `21f7c68` (close-out hygiene: canonical preamble refresh across 7 docs + §15 self-stamp + final W17 bar recorded + backlog item statuses updated; close-out PR `week17 -> main` not yet opened; branch is pushed) | `21f7c68` |
| W17-7 | **closed `2026-05-18`** post-slate hotfix batch (W14-7/W14-8 paterni): W17-7a `bf983eb` Makefile `test-security` target enrolls `test_unaccounted_dropout_surface.py` (217 → 220 — recovers the W16-7-followup audit-trail count); W17-7b `fc88678` `.env.example` adds `EXTRACE_EPOCH_RUN_ID` (W14-5 log run-id stamping env var, was missing); W17-7c `326dac8` ADR 0007 runbook references aligned with current `lan-exposure.md` (drops "short" qualifier, lists all 5 pre-flight items, declares runbook canonical); W17-7d `51dba29` `.pre-commit-config.yaml` header comment block documenting the intentional Python version gap (3 versions in play: 3.10 executor / 3.11 API+pyproject / 3.12 dev+pre-commit) | `bf983eb` + `fc88678` + `326dac8` + `51dba29` |

## W18 Pull-Forward Acceptance Bar

W18 closed for phase work `2026-05-21` on the `week18` branch (per
user direction; W11-W17 paterni preserved); close-out PR #26
`week18 -> main` MERGED `2026-05-21` via `9874e79`. All rows below
are closed audit trail; full Per-Item Detail evidence in the frozen
tracker
[`active-work/W18-heartbeat-refactor.md`](active-work/W18-heartbeat-refactor.md).

| Iter | Stable ID(s) | Landing commit |
|---|---|---|
| W18-0 | doc-reconcile — `week18` branch + `week18 -> main` close-out PR wording across canonical docs; new W18 active-work tracker + README phase-pointer arch gate transition W17→W18 + new W17 close-out fact gate | `89d0c9b` |
| W18-1 | `[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread` (W17-3 carry-over; ADR 0012 `documents/adrs/0012-heartbeat-thread-relocation.md` Option A1 Accepted — dedicated sandbox-reset coordinator with cancel-path teardown reset staying on the heartbeat thread; invariant cost trade-offs against W13-1 HMAC / W13-3 two-phase cancel / W13-13 CAS / W16-2 facade lock all preserved byte-identical) + followup doc-truth alignment | `acf6cc9` + `73d8a5c` |
| W18-2 | `[FOLLOWUP simulation-progress-cancel] heartbeat-refactor` (W17-4 carry-over; ADR 0012 Option A1 implementation — step-1 reset moved off the worker thread via dedicated `_run_reset_off_thread` coordinator; function-extension shape, ~42 LOC; W17-2 harness smoke passes byte-identical; three AST/behavioral gates pinning the bare `_reset_sandbox(...)` Name call at `analysis_service.py:155` preserved) + ADR self-stamp + ruff-format followup + full-repo lint sweep + pre-commit install | `a9bffb1` + `78ed7cc` + `b5b64b6` + `306d744` |
| W18-3 | `[FOLLOWUP w17-2-harness-extension-tests]` — lifecycle harness extension tests landed in `tests/workflows/marketplace/test_lifecycle_harness.py` per ADR 0012 §Follow-On: `test_lifecycle_harness_parallel_reset_does_not_deadlock` + `test_lifecycle_harness_reset_idempotency` + `test_lifecycle_harness_reset_during_finalize` (W17-2 module docstring L27-35 forward contract); test-only commit + self-stamp | `92b310d` + `32d9905` |
| W18-4 | close-out hygiene + canonical preamble refresh + §16 W18 self-stamp + W18 tracker freeze (W17-6 paterni `21f7c68`) | `3f4f95a` |
| W18-4-followup | 4 W18-2 invariant pins at `tests/workflows/marketplace/test_coordinator_invariants.py` + 2 pre-existing doc drift fixes (signature default / poll-interval bound / cancel-propagation behavior / reporter thread-isolation) | `e1043e5` |
| W18-post-merge | PR #26 merge `9874e79` doc-truth alignment: 8-doc canonical preamble refresh + §16 close-out audit-trail entry + W18 tracker `Phase:` freeze stamp (W17-post-merge `bf6ec3e` paterni — direct commit on `main`, no PR) | this commit |

Final W18 bar: `tests/architecture/` **201 passed** (W17 final 200,
+1 from W18-0 README phase-pointer arch gate W17→W18 transition);
`make test-security` **220 passed** (unchanged from W17); full suite
**1907 passed, 9 skipped, 8 deselected** (W17 final 1899, +8: W18-0
README arch gate + 3 W18-3 lifecycle harness extension tests + 4
W18-4-followup W18-2 invariant tests via `e1043e5`).

## W19 Pull-Forward Acceptance Bar

W19 closed synthetically `2026-05-26` on the `week19` branch (per
user direction 2026-05-21; W11-W18 paterni preserved); merged to main
via PR #28 `c879603` on `2026-05-26`. W19-0..W19-6 + W19-X all
closed. Stable IDs W19-1..W19-5 promoted from W19-W22 Roadmap
Acceptance Bar (planning, now W20-W22) to this Pull-Forward table at
W19-0 open. Frozen tracker:
[`active-work/W19-live-run-root-cause.md`](active-work/W19-live-run-root-cause.md).

| Iter | Stable ID(s) | Status |
|---|---|---|
| W19-0 | doc-reconcile — `week19` branch + 8-doc canonical preamble refresh + new W19 active-work tracker + §17 W19 plan header doc-open + §17-§20 combined header split into §17 W19 active + §18-§20 W20-W22 planning + README phase-pointer arch gate transition W18→W19 + new W18 close-out fact gate `test_readme_phase_pointer_mentions_w18_closeout_merge` + baseline live-run smoke artefakt | **closed `2026-05-21`** via this commit |
| W19-1 | `[BUG scenario-unaccounted-dropout-regression-fixture]` — Live-run dropout regression fixture; new file `tests/executor/test_scenario_accountant_dropout_regression.py`; parametrize on `debug_session` + `refactor_workflow` + aggregate gate; landed RED with `@pytest.mark.xfail(strict=True)` at W19-1 primary; xfail markers removed + whitelist narrowed to `frozenset({"covered_via_layered_attempts"})` at W19-2 primary | **closed `2026-05-25`** via primary `6a21cf3` + self-stamp `fd02ca4` |
| W19-2 | `[BUG scenario-unaccounted-dropout-debug-refactor]` — Dropout emit-site fix (Hat-1; W16-1 paterni); ONE-PATH verdict (no mini-ADR); upstream emit-site landed in `executor/flows/playwright/stimulus/passes.py` covered-only branch — new `covered_via_layered_attempts` reason_code; accountant fallback `scenario_accountant.py:392-438` preserved as son-mil koruyucu; +2 W16-1-mirror synthetic unit tests at `tests/security/test_scenario_dropout_repro.py`; W19-1 fixture initially regenerated SYNTHESIZED then re-anchored to live-lifted at W19-2-followup-2 (`c2bf28ca9506` / sha256 `e9e60b2e42...`); +1 `_meta.source_sha256` canonical-hex format gate; **live Hat-1 GREEN gate SATISFIED `2026-05-25 22:23`** (`unaccounted_dropout` count = 0 in live JSON, both scenarios classified `covered_via_layered_attempts`, 16 of 16 key fields byte-identical with pre-fix anchor save the W19-2 reason_code) | **closed `2026-05-25`** via primary `89b64da` + self-stamp `d9c6262` + live re-anchor `d5de9ca` |
| W19-3 | `[GOAL harness-verification-contract-event-level]` (new) — HARD GATE for W19-4/W19-5 SATISFIED; new field `confirmation_source: str = "none"` (typing decision: `str + field_validator` not `Literal[...]` per §17 plan — codebase parity with `status` field pattern, JSON wire shape identical) on `EventAttemptRecord` (Pydantic + executor dataclass mirror + UI `EventAttemptDto`/`EventAttemptView`/`fromEventAttempt`) with default `"none"` for back-compat; `_VALID_CONFIRMATION_SOURCES` shared frozenset + `_validate_confirmation_source` validator; new test `tests/executor/test_automation_health_reasons.py` (12 tests pinning dataclass ↔ Pydantic parity + trigger-payload deserialization default/parametrize + validator rejects unknown + orthogonality with existing `harness_verification_unconfirmed_present` reason emission rule); +6 contract round-trip tests at `test_analysis_fixture_baselines.py`; +4 UI adapter tests at `report.test.ts`; frozen trigger fixture `ms_python_python.json` regenerated via planner replay so each of 21 event_attempts gains `"confirmation_source": "none"` | **closed `2026-05-25`** via primary `d2e83e7` + self-stamp this commit |
| W19-4 | `[FOLLOWUP harness-verification-debug-events]` — **producer side**: `onDebug*` family nonce confirmation generation in `executor/flows/harness_extension/*`; reconciliation Python side stamps `attempt.confirmation_source = "harness_nonce"` at `health/reconciliation.py:347-348` when `execution_closed and family.startswith("onDebug")`. **consumer wire**: `_mark_unverified_harness_attempt` at `reconciliation.py:85-90` gates `failure_reason_code="harness_verification_unconfirmed"` on `confirmation_source == "none"` so stamped attempts skip the unverified marker → unlocks W19 must-pass #2 reason drop. 7 new behavioral tests at `tests/executor/test_playwright_health_reconciliation.py:813-1090` (producer happy-path / fail-closed forged HMAC / missing marker / scope discipline non-onDebug / consumer skip+set). | **closed `2026-05-26`** via `7d44b0e` |
| W19-5 | `[FOLLOWUP harness-verification-terminal-and-lm-tool]` — `onTerminalShellIntegration` + `onLanguageModelTool:*` local-only confirmation marker `confirmation_source="log_record"`; producer arm extension at `reconciliation.py:347-365` sibling elif to W19-4 onDebug arm; live-anchor evidence (`8247e05ec9ef.json`) confirmed all 6 unstamped attempts already carried `harness_trace:<attempt_id>` evidence via existing runCurrentStimulus + `harness_fallback="run_current_stimulus"` paths → no JS / no new predicate / no planner mapping needed; +7 new behavioral tests at `test_playwright_health_reconciliation.py:1175-1369` (terminal happy-path / LM parametrize 5 / forged HMAC / missing marker / scope discipline / consumer skip+set); W19-4 scope-discipline parametrize narrowed to onCommand only; pre-W19-5 chat-tool attribution pin at `test_playwright_monitor_attribution.py:658` updated to assert `confirmation_source=="log_record"` + suppressed `failure_reason_code` | **closed `2026-05-26`** via primary `e537ebd` + self-stamp this commit |
| W19-6 | close-out hygiene + 9-doc canonical preamble refresh + §17 W19 self-stamp post-final-bar + W19 tracker freeze + PR #28 `week19 -> main` MERGED `2026-05-26` via `c879603`; W18-4 paterni `3f4f95a`; **+ 3 hygiene items from W19-3-followup-2 audit `2026-05-25`**: (a) **field-set parity gate** widened at `test_executor_dataclass_and_pydantic_contract_share_confirmation_source_field`; (b) **hotspot LOC ratchet** at `tests/architecture/test_executor_hotspot_loc_ratchet.py` pinning 8 modules >500 LOC under `executor/flows/playwright/` at LOC × 1.05 ceiling; (c) **acceptance-bar column** added to W19 sub-iter table at §17.3; **+ W19-6-followup-2 pre-merge hygiene** closing 6 test gaps (+20 parametrized tests) + 9-doc preamble drift fix + W19 tracker freeze | **closed `2026-05-26`** via primary `f17b4b1` + self-stamp `cd82153` + W19-6-followup-2 `800c69f` |

W19 acceptance (live-run-driven; see §17.4 in
[`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md) for full
checklist): `unaccounted_dropout == 0` (must-pass) ✓;
`harness_verification_unconfirmed_present` reason drops
(must-pass) ✓ synthetic / live-pending-next-run;
`run_quality: low → medium` (expected); `verification_gap_present`
drops (stretch); `automation_health.status: degraded` OK (W20
closes `official_unresolved_present`). Final W19 bar:
`tests/architecture/` **204 passed**; `make test-security` **220
passed**; full suite **1995 passed, 9 skipped, 8 deselected**.

## Newly Captured (audit `2026-05-26`)

W19-3-followup-2 post-merge audit (Codex `Roadmap Addendum Request`)
flagged one out-of-roadmap security/hygiene finding. Schedule at
W19-6 close-out hygiene if it fits, otherwise W20-0 doc-reconcile
pull list.

| Stable ID | Description | Status |
|---|---|---|
| `[FOLLOWUP vsix-entry-log-sanitization]` (new) | VSIX/ZIP archive entry names are attacker-controlled. Rejected entries are logged raw at `workflows/marketplace/client.py:268-271` (`vsix_entry_rejected reason=path_traversal entry=%s`) and `client.py:318-321` (`reason=symlink_escape`). Entry filename can contain newlines / control chars / terminal escape sequences → log forging / log confusion risk during forensic triage. **Not W8-8** (W8-8 is manifest field logging deferral — no trigger observed). **Scope**: apply control-char escaping / safe representation to `info.filename` before the warning emit; consider reusing redaction helpers in `packages/analysis_contracts/evidence.py`; truncate display length. **Test**: small regression in marketplace/security lane — malicious ZIP entry name with newline/control chars rejects + log output shows sanitized representation (no raw newline). **Severity/Confidence**: Medium / High, evidence type direct, chronology verified against `week19` `7d44b0e` HEAD. Lane: `[marketplace-analysis]` or `[security-detection]`. | pending — W19-6 or W20-0 schedule TBD |
| `[FOLLOWUP harness-secret-distribution-redesign]` (new; migrated from W19-X-handoff.md risk register at W19-6 close-out) | **Architecture gap surfaced during W19-X live close-out (2026-05-26).** W13-1 secret distribution design assumed ONE `activate()` per VS Code lifetime — the per-launch HMAC secret file lives only between `launch_vscode.sh` write and `activate()` read+unlink. The W19-X investigation proved CDP `Page.reload()` (called by `executor/flows/playwright/reload_vscode.py`) restarts the Extension Host and runs `activate()` again, hitting ENOENT on the already-unlinked secret. W19-X closed the immediate failure via pre-reload secret rewrite in `vscode.reload_workbench_window` + defensive 30×100ms polling in `consumeHarnessNonceSecret`, but those are layered patches over a design assumption that no longer holds. **Two clean redesigns to weigh**: (a) migrate to a non-file secret distribution (env var read at `activate()`, never written to disk — closes the temporal-isolation gap but loses container-restart cleanup); (b) keep the file at `0400` for VS Code lifetime + accept that target processes running same-UID could theoretically read it, with the threat model documented (current temporal-protection vs same-UID target extensions weakens by approximately the duration of the run, not by an order of magnitude — likely an acceptable trade vs. patch-on-patch complexity). **Scope**: ADR comparing (a) and (b), with explicit threat model documentation; whichever wins gets a coordinated landing across `launch_vscode.sh` + `extension.js` + `reload_vscode.py` + the polling layer. **Test**: existing W19-X behavioral tests at `tests/executor/test_playwright_health_reconciliation.py:1175+` plus the harness completion verifier under `test_harness_handshake_required.py` — both must stay green across the redesign. **Severity/Confidence**: Medium / High (no current breakage; this is design hygiene). | pending — W20-W22 ADR candidate |
| `[FOLLOWUP harness-secret-extra-reactivation-source]` (new; migrated from W19-X-handoff.md risk register at W19-6 close-out) | **Un-gated reload path surfaced during W19-X live close-out (2026-05-26).** Live diagnostic from `activate_enter` records shows that even after W19-X's pre-reload `_rewrite_harness_secret` wiring (which gates the 3 reload sites in `vscode.reload_workbench_window`), at least one reactivation still hits ENOENT on `/run/extrace/harness-secret`. The defensive 30×100ms polling layer in `consumeHarnessNonceSecret` rescues the marker emission (`poll_attempts > 1, has_secret: true`), but the existence of a fourth reload path means there's another orchestration step that calls `Page.reload()` (or equivalent) without going through the gated entry point. Most plausible candidate: `code --install-extension`'s internal reload (the install/reload sequence likely lives in `executor/flows/playwright/install_extension.py` or wherever the install-then-reload step is invoked). **Scope**: trace the un-gated reload source via the `activate_enter` diagnostic (1 ENOENT remaining → 1 reload path not yet routed through `_rewrite_harness_secret`), then gate it through the same `launch_vscode.sh --secret-only` pre-write. **Test**: live smoke on `ms-python.python` — `activate_enter` records show `poll_attempts: 1` for every reactivation (i.e., polling layer goes unused defensively). **Severity/Confidence**: Low / High (defensive polling already masks the failure mode; this is forensic hygiene). | pending — W20-0 forward reference per W19-6 close-out |
| `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` (new; surfaced during W20-5 fresh live-run on `2026-05-27`) | **`reset_sandbox` step deterministically flakes on the second analyze in the same executor container.** Repro observed during W20-5 close-out fresh live-run: container had been Up ~31 min after a successful prior analyze (`71ce478660bb` at 23:48); next analyze (`99af09b6d8a9`) failed at `reset_sandbox` with `Command failed (rc=1): /usr/bin/docker exec ... /usr/bin/python3 -m executor.flows.playwright.reload_vscode` — WebSocket `ws://localhost:9222/devtools/browser/...` connected, but the reload script exited non-zero. noVNC inspection during the failure showed VS Code's Developer Tools panel still open from the prior analyze (Elements inspector visible alongside the workbench DOM). After `docker compose restart executor` (single container restart, ~30s downtime), the retry (`4e92de149802`) ran clean in ~5.3 min. **Hypothesis**: VS Code state accumulated across analyses (open auxiliary windows like DevTools, lingering CDP attachments, perhaps unclosed terminal panes — pid output showed 2 bash terminal subprocesses still alive 2 hours later) interferes with the CDP `Page.reload()` issued by `reload_vscode.py`. The reload sends the message and connects, but VS Code's response to the reload returns an error path that surfaces as rc=1 in the wrapper. **Scope**: trace the rc=1 exit path inside `executor/flows/playwright/reload_vscode.py` to identify whether the reload itself errors or a post-reload assertion fails; then add a pre-reload cleanup pass that closes DevTools windows + auxiliary tool panels + ensures terminal panes don't accumulate. May overlap with W18-2 heartbeat refactor coordinator scope (step-1 reset coordinator at `executor/flows/playwright/health/...` — W18-1 ADR 0012 Option A1) — investigate if the heartbeat-relocated reset path is the one that races vs the worker-thread invocation. **Test**: extend `tests/workflows/marketplace/test_lifecycle_harness.py` (W17-2 lifecycle harness scaffold) with a back-to-back-analyze pattern: spin lifecycle harness, run first analyze synchronously, immediately run second analyze on the same container, assert second analyze reaches `install_extension` step (i.e., `reset_sandbox` passed). Pre-condition: container does NOT restart between the two analyses. **Severity/Confidence**: Medium / High (deterministic repro on lokal interactive flow; production impact LOW because CI typically spawns per-analyze fresh containers, so the bug doesn't surface there — but if any user runs back-to-back analyses on the same container, the second fails with no helpful error message). Lane: `[executor]` + `[lifecycle-harness]`. | **RESOLVED 2026-06-24** (`4437d1e`): real root cause was a malformed `pgrep` (no `--` separator) making `terminate_vscode()` no-op in every config — the stale instance + orphaned terminal shells accumulated; fix = pgrep `--` + CDP-independent needle + `/proc` descendant reap. See [`active-work/reliability-analyze-resilience.md`](active-work/reliability-analyze-resilience.md) §B2. |

## W20 Pull-Forward Acceptance Bar (closed; merged via PR #29 `64a3c3d` 2026-05-26)

**W20 closed synthetically `2026-05-27` on the `week20` branch**
(per user direction `2026-05-26`; W11-W19 paterni preserved);
close-out PR #29 `week20 -> main` **MERGED `2026-05-26 23:10:21Z`
via `64a3c3d`**. Stable IDs W20-1..W20-5 promoted from W20-W22
Roadmap Acceptance Bar (planning, now W22 Roadmap Acceptance Bar
planning after the W21-0 split) to this Pull-Forward table at W20-0
open and all closed in the W20-0..W20-5 window. Frozen tracker:
[`active-work/W20-coverage-promotion-easy-wins.md`](active-work/W20-coverage-promotion-easy-wins.md)
(frozen at W20-5 + followups per W17/W18/W19 paterni).

| Iter | Stable ID(s) | Status |
|---|---|---|
| W20-0 | doc-reconcile — `week20` branch + 9-doc canonical preamble refresh + new active-work tracker for W20 + §18 W20 plan header doc-open + §18-§20 combined header split into §18 W20 active + §19-§20 W21-W22 planning + W20 Pull-Forward Acceptance Bar promotion (this section) + README phase-pointer arch gate transition W19→W20 + new W19 close-out fact gate `test_readme_phase_pointer_mentions_w19_closeout_merge` pinning PR #28 / `week19 -> main` / `c879603` + baseline live-run captured (`e89a82ca9ba8`, sha256 `4dd788...0256ffe`) | **closed `2026-05-26`** via primary `66a8a0b` + self-stamp `5f13757` |
| W20-1 | `[GOAL taxonomy-scm-official-promotion]` (new) — `_OFFICIAL_CAPABILITY_SUPPORT["scm"]: "missing" → "covered"` at [`capabilities.py:88`](../packages/analysis_planner/capabilities.py); 4 new invariant tests at `tests/platform/contracts/test_capability_support_invariants.py` pinning the flip + heuristic-track state + `git_workflow` scenario advertising `scm` in `api_capabilities`; frozen trigger fixture `ms_python_python.json` regenerated via planner replay (scm `coverage_tracks.official.matrix.support_status` flips `missing → covered`, `status` lands at `partial` since ms-python.python's activation events don't select `git_workflow`) | **closed `2026-05-26`** via primary `82276cb` + self-stamp `a17e595` |
| W20-2 | `[GOAL taxonomy-settings-official-promotion]` (new) — `_OFFICIAL_CAPABILITY_SUPPORT["settings"]: "missing" → "covered"` at [`capabilities.py:90`](../packages/analysis_planner/capabilities.py); 4 new invariant tests at `tests/platform/contracts/test_capability_support_invariants.py` mirroring the W20-1 scm pattern; frozen trigger fixture regenerated (settings official matrix entry: `support_status: missing → covered`, `status: partial` since ms-python.python doesn't select `settings_modification`) | **closed `2026-05-26`** via primary `a4343d2` + self-stamp `7406588` |
| W20-3 | `[GOAL coverage-matrix-contract-tests]` (new) — 5 new contract invariant tests added to `tests/platform/contracts/test_capability_support_invariants.py`: keyset parity (`_OFFICIAL_/_HEURISTIC_/_GLOBAL_CAPABILITY_SUPPORT` ↔ `CAPABILITY_TAXONOMY`) + Official ⊆ Heuristic subset + `_GLOBAL_CAPABILITY_NOTES` keys ↔ taxonomy + exact-tuple ordering pin + W20-1/W20-2 combined post-condition gate | **closed `2026-05-26`** via primary `d4c03b6` + self-stamp `2e39230` |
| W20-4 | `[DESIGN taxonomy-comments-testing-readiness]` (new) — design note landed at `documents/architecture/comments-testing-readiness.md` covering VS Code Comments API + Test Controller API surface envelope, current stub-vs-missing inventory (extension.js has `extrace.harness.comments` bare stub + constants.js has `workbench.view.testing` view id), W21-1 + W21-2 plumbing şablonu, inherited policy constraints, 5 open questions for W21-0 | **closed `2026-05-26`** via primary `05f47f3` + self-stamp `b409894` |
| W20-5 | close-out hygiene + 9-doc canonical preamble Active → Previous flip + §18 W20 self-stamp + W20 tracker freeze + W20 Pull-Forward Acceptance Bar audit-trail close + 3 new arch invariant tests (GAP-A `test_w20_section_18_cross_doc_parity.py` + GAP-B `_OFFICIAL_CAPABILITY_SUPPORT` full dict shape pin extension + GAP-D `test_w20_4_design_doc_presence.py`); final live-run captured 2026-05-27 (`4e92de149802`, sha256 `3804a5b5...4394c`) — W20 acceptance bar live-satisfied on fresh run; followup-2 `d163b02` filed `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` for W21; followup-3 `ae5b7de` finalized 10-doc preamble `26bb080` placeholder backfill; followup-4 `25f33d1` pre-PR body drift sweep; close-out PR #29 `week20 -> main` **MERGED 2026-05-26 23:10:21Z via `64a3c3d`** | **closed `2026-05-27`** via primary `4665d32` + self-stamp `95b0010` + followup-2 `d163b02` + followup-3 `ae5b7de` + followup-4 `25f33d1` |

W20-0 forward-refs (carried as pending pull; promoted from W20-W22
Roadmap Acceptance Bar at W20-0 open):

- `[RESEARCH activation-event-spec-crosswalk]` (new) — Üç kaynaklı
  crosswalk: resmi VS Code Activation Events sayfası ↔ repo
  `OFFICIAL_EVENT_REGISTRY` 29 entry ↔ DB `ExtensionActivationEvents`
  + indirilmiş VSIX `package.json` `activationEvents[]`. Çıktı: matris
  + gerçek gap listesi backlog'a. W22-6 implement if gap çıkarsa.
- `[FOLLOWUP harness-secret-extra-reactivation-source]` (W19-X migrated;
  opportunistic W20-5 if `activate_enter` diagnostic surfaces
  `poll_attempts > 1`).
- `[FOLLOWUP harness-secret-distribution-redesign]` (W19-X migrated;
  W20-W22 ADR candidate; W22-1 öncesi opportunistic kapanış, aksi
  halde W23+).
- `[FOLLOWUP defensive-test-parametrize-helper]` (W19-3-followup-2
  audit) — schema-only field landings için tablo-yolu helper.

W20 acceptance (live-run-driven; see §18.4 in
[`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md) for full
checklist) **LIVE-SATISFIED** on W20-5 fresh live-run anchor
`4e92de149802` (sha256 `3804a5b5...4394c`):
`coverage_summary.missing_capabilities` dropped 6 → **4** (lost
`scm` + `settings`; remaining `[chat, comments, testing,
workspace_trust]`); static suite green (final W20 bar
`tests/architecture/` **240 passed** + `make test-security`
**220 passed** + full suite **2045 passed, 9 skipped, 8
deselected**); `automation_health.status: degraded` OK
(`official_unresolved_present` W22-end'inde kapanır — Hat-3
hard tier); W19 Hat-1 (`unaccounted_dropout == 0`) + Hat-2
(`harness_verification_unconfirmed_present` DROPPED) both
hold post-W20.

## W21 Pull-Forward Acceptance Bar (closed and merged)

**W21 closed `2026-05-28` and merged via PR #30 `week21 -> main`
MERGED `2026-05-28` via `5dc18aa`** (W21-N close-out at `dd24f1e`;
per user direction `2026-05-27`; W11-W20 paterni preserved); sub-iter
commits landed on `week21` and close-out PR `week21 -> main` merged
to `main`. Stable IDs W21-0..W21-4 were promoted from W21-W22
Roadmap Acceptance Bar (planning, now W22 Roadmap Acceptance Bar
active below) to this Pull-Forward table at W21-0 open. Frozen
tracker:
[`active-work/W21-coverage-promotion-mid-tier.md`](active-work/W21-coverage-promotion-mid-tier.md).

Ordering (user-confirmed `2026-05-27` via AskUserQuestion): **W21-3
→ W21-1 → W21-2**. W21-3 (`workspace_trust`) lands first because
trust state is a precondition for many editor APIs in
restricted-mode workspaces; W20-4 DESIGN doc open Q4 resolved with
the "yes" branch.

| Iter | Stable ID(s) | Status |
|---|---|---|
| W21-0 | doc-reconcile — `week21` branch + 10-doc canonical preamble refresh + new active-work tracker for W21 + §19 W21 plan header doc-open + §19-§20 combined header split into §19 W21 active + §20 W22 planning + W21 Pull-Forward Acceptance Bar promotion (this section) + README phase-pointer arch gate transition W20→W21 + new W20 close-out fact gate `test_readme_phase_pointer_mentions_w20_closeout_merge` pinning PR #29 / `week20 -> main` / `64a3c3d` + baseline live-run captured via self-stamp follow-up (anchor `600d9ecba5eb`, sha256 `1db1480551fd...c4477`; W20 close-out invariants live-verified — missing_capabilities = [chat, comments, testing, workspace_trust] byte-identical with W20-5 anchor `4e92de149802`; Hat-1 `unaccounted_dropout_count: null` byte-identical with W20-5; Hat-2 `harness_verification_unconfirmed_present` DROPPED; one new `extra_trigger_failures_present` reason from intermittent flake — not a W20 invariant violation) | **closed `2026-05-27`** via primary `8434323` + self-stamp `19bd9c7` |
| W21-3 | `[GOAL taxonomy-workspace-trust-coverage]` (new) — `_OFFICIAL_CAPABILITY_SUPPORT["workspace_trust"]: "missing" → "covered"` at [`capabilities.py:99`](../packages/analysis_planner/capabilities.py) + mirror in `_GLOBAL_CAPABILITY_SUPPORT:47` (heuristic derives) + harness `vscode.workspace.isTrusted` baseline marker + `onDidGrantWorkspaceTrust` listener via reserved OutputChannel route (W19-X Bug B paterni) + `workspace_trust_transition` scenario advertising `workspace_trust` capability + 4 invariant tests at `tests/platform/contracts/test_capability_support_invariants.py` (W20-1 scm template mirror) + dict shape canonical pin update + `test_split_did_not_lose_data_volume` count bump 13→14 + frozen trigger fixture regen for ms-python.python. Runtime stimulus pass deferred to W22 as `[FOLLOWUP workspace-trust-stimulus-pass]` (workspace trusted-by-default in fixture; granted-transition exercise requires fixture restructuring). Live anchor `6fd7b959bd5a` sha256 `fa83017a4de25e...d6f7477` confirms `missing_capabilities` 4 → 3 items, `covered/partial/missing` 7/7/4 → 8/7/3, workspace_trust matrix entry status `covered` is_active=true. W20 invariants HOLD (Hat-1 `dropout=null`, Hat-2 `harness_verification_unconfirmed_present` DROPPED). | **closed `2026-05-27`** via primary `c744c15` + self-stamp `4b0a1ed` |
| W21-1 | `[GOAL taxonomy-testing-coverage]` (new) — `_OFFICIAL_CAPABILITY_SUPPORT["testing"]: "missing" → "covered"` at [`capabilities.py:97`](../packages/analysis_planner/capabilities.py) + mirror in `_GLOBAL_CAPABILITY_SUPPORT:45` (heuristic derives) + harness Test Controller run/debug profile callbacks emit `test_controller_event` markers via `emitHarnessEvent` through reserved OutputChannel route (W19-X Bug B paterni) with ephemeral TestItem rebuild on every invocation (W19-X HMAC reactivation race lesson) + `local_test_controller` scenario in `scenarios.py` (mirror W21-3 workspace_trust_transition shape) + 4 invariant tests (W21-3 workspace_trust template mirror) + dict shape canonical pin update + `test_split_did_not_lose_data_volume` count bump 14→15 + frozen trigger fixture regen for ms-python.python. Runtime stimulus pass (testing.runAll) deferred to W21-N or W22 (listeners observe synthetic invocations from any subsequent stimulus pass without dedicated pass). Live anchor `0b4998ce31b4` sha256 `b7192bc2ff9c611f00e9dd806af54e0648c92d9201d78fe9ccb886dcf5968be4` confirms `missing_capabilities` 3 → 2 items (testing dropped). W20 invariants HOLD. | **closed `2026-05-27`** via primary `7e87030` + self-stamp `38b8fd8` |
| W21-2 | `[GOAL taxonomy-comments-coverage]` (new) — `_OFFICIAL_CAPABILITY_SUPPORT["comments"]: "missing" → "covered"` at [`capabilities.py:96`](../packages/analysis_planner/capabilities.py) + mirror in `_GLOBAL_CAPABILITY_SUPPORT:44` (heuristic derives) + harness CommentController baseline marker at activate() entry + `ensureCommentThread` extended in `stimulus_dispatch.js` to emit `thread_created` + `thread_disposed` markers via `emitHarnessEvent` (W19-X Bug B paterni) with ephemeral thread default (W19-X HMAC reactivation race lesson) + `local_comments_controller` scenario in `scenarios.py` (mirror W21-3 / W21-1 shape) + 4 invariant tests + dict shape canonical pin update + `test_split_did_not_lose_data_volume` count bump 15→16 + frozen trigger fixture regen for ms-python.python. Runtime stimulus pass implicit (ensureCommentThread invoked from existing extrace.harness.runCurrentStimulus command handler). Live anchor `1ddb3702c0ca` sha256 `2dabd15be329bbf1685fe7fc31469355bdc4a5acac2a364d43a196437339cbff` confirms `missing_capabilities` 2 → 1 items (comments dropped — **W21 mid-tier closure target hit; only chat for W22**). W20 invariants HOLD. | **closed `2026-05-28`** via primary `8948ea6` + self-stamp `3088709` |
| W21-4 | `[GOAL container-hardening-baseline]` (existing W18 candidate) — user-pulled into W21 per AskUserQuestion 2026-05-28 after W21-1 + W21-2 closed cleanly. `docker-compose.yml` `cap_drop: [ALL]` on executor/api/ui + audited `cap_add` per service (executor: NET_RAW + SYS_PTRACE; api: SETUID + SETGID; ui: SETUID + SETGID + CHOWN + DAC_OVERRIDE) + `security_opt: ["no-new-privileges:true"]`. New ADR [`documents/adrs/0013-container-isolation-baseline.md`](adrs/0013-container-isolation-baseline.md) documenting decisions + deferred items (read_only + tmpfs + custom seccomp → W22 ratchet-down lane). 12 invariant tests at `tests/architecture/test_compose_isolation_invariants.py`. Live anchor `eacea0b6690e` sha256 `5d7c8b974f21e3bf4ad679a41551dd3e7b71d37573f5e7f2b28b87d2ad4a6a84` confirms NO coverage regression vs W21-2 (`missing_capabilities = [chat]` byte-identical). Manual kernel smoke `NoNewPrivs:1`. W20 invariants HOLD. | **closed `2026-05-28`** via primary `16e2224` + followup-1 `2f9cba2` + self-stamp `8c42445` |
| W21-N | close-out hygiene + 10-doc canonical preamble Active → Previous flip (`W21 closed synthetically 2026-05-28`) + §19 W21 self-stamp + W21 tracker freeze + W21 Pull-Forward Acceptance Bar audit-trail close + 34 new arch invariant tests at [`test_w21_section_19_cross_doc_parity.py`](../tests/architecture/test_w21_section_19_cross_doc_parity.py) (GAP-A cross-doc parity gate — mirror W20-5 paterni) + per-row "this commit" → explicit SHA backfills + final live-run anchor `eacea0b6690e` sha256 `5d7c8b974f21e3...d4a6a84` (W21-4 anchor doubles as W21-N final since W21-N is docs-only) + UI-triggered confirmation anchor `92cf90d6edb5`. Dict shape canonical pin update for W21 end-state already landed at W21-1/W21-2/W21-3 primaries. W18-4 / W19-6 / W20-5 paterni. [FOLLOWUP sandbox-reset-stale-state-multi-analyze] not pulled at W21-N (opportunity-not-found; remains W22 candidate). Close-out PR #30 `week21 -> main` MERGED `2026-05-28` via `5dc18aa`. | **closed `2026-05-28`** via `dd24f1e` |

W21-0 forward-refs (carried as pending pull):

- `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` (W20-5
  filed; W21 candidate, opportunistic at W21-N close-out window
  per user-confirmed strategy).
- `[RESEARCH activation-event-spec-crosswalk]` (W20-0 forward-ref'd;
  W22-6 implement if W20-0 crosswalk reveals gap).
- `[FOLLOWUP harness-secret-extra-reactivation-source]` (W19-X
  migrated; opportunistic, defensive polling already masks).
- `[FOLLOWUP harness-secret-distribution-redesign]` (W19-X migrated;
  W22-1 öncesi opportunistic ADR candidate or W23+).
- `[FOLLOWUP defensive-test-parametrize-helper]` (W19-3-followup-2
  audit) — schema-only field landings için tablo-yolu helper.
- `[FOLLOWUP workspace-trust-stimulus-pass]` (W21-3 filed
  `c744c15` + this commit) — runtime stimulus pass exercising
  untrusted → granted transition end-to-end. W21-3 landed taxonomy
  promotion + harness observability listener + scenario advertisement;
  runtime exercise of `onDidGrantWorkspaceTrust` requires fixture
  restructuring (untrusted-by-default workspace via either
  `extrace.fixture-restricted-trust` or explicit
  `--disable-workspace-trust=off` boot flag). W22 pull window
  (after W22-1 ADR Accepted, before W22-2 chat coverage if capacity
  permits). No code change required for W21-3 acceptance — the
  listener fires on any future trust transition once the fixture
  supports it.

W21 acceptance (live-run-driven; see §19.4 in
[`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md) for full
checklist):

- **Must-pass**: `coverage_summary.missing_capabilities` drops 4 → 1
  (`chat` only) — assumes W21-3 + W21-1 + W21-2 all land.
- **Acceptable fallback**: drops 4 → 2 (`chat` + `workspace_trust`)
  if W21-3 defers as DESIGN-only per W20-4 paterni.
- W19 Hat-1 (`unaccounted_dropout == 0`) holds post-W21.
- W19 Hat-2 (`harness_verification_unconfirmed_present` DROPPED)
  holds post-W21.
- Static suite green (final W21 bar pinned at W21-N self-stamp).

## W22 Roadmap Acceptance Bar (closed synthetically — merged to main via PR #31 1399f82)

**W22 closed synthetically on the `week22` branch and merged to main via PR #31 `1399f82`** (per user direction
`2026-05-28`; W11-W21 paterninden bu sefer ayrılma — tek branch
week22, sub-iter başına ayrı branch yok); close-out PR `week22 ->
main` MERGED to main via PR #31 `1399f82` on `2026-05-28`. Branch was created from
`main` @ `5dc18aa` (W21 close-out PR #30 merge `2026-05-28
14:18:22+03:00`). Promoted from "planning" to "active" at W22-0
doc-reconcile 26bb080 per W19-0 / W20-0 / W21-0 paterni
mirror — W19-W22 → W20-W22 at W19-0, W20-W22 → W21-W22 at W20-0,
W21-W22 → W22 at W21-0, W22 planning → active here.

Active tracker:
[`active-work/W22-coverage-promotion-hard-tier.md`](active-work/W22-coverage-promotion-hard-tier.md).

Driving signal: Codex live-run validation of `ms-python.python` @
`992ad028f3df` (2026-05-21 10:10). W21-2 live-run confirmed
`missing_capabilities` 1 [chat] post W21-3 + W21-1 + W21-2; W21-4
container hardening baseline did NOT regress (eacea0b6690e
anchor). **W22 closes hard tier** (`chat`) + sandbox evasion ADR +
attribution depth + container hardening ratchet-down (W21-4 ADR
0013 §Deferred).

Plan source-of-truth: [`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md). Full sub-iter scope, acceptance gates, ADR paths, and critical files there. Plan went through 3 review rounds (Codex live-run + GPT × 2).

Stable IDs `W22-0..W22-N` are now active. Sıralama önerisi
(overlap-aware): W22-0 doc-reconcile (in-flight) → düşük-risk
sub-iter'lar önce (W22-6 container hardening + W22-4 sandbox ADR +
W22-5 canary + W22-1 chat ADR — `executor/`, `docker/`, `adrs/`,
`tests/security/` surface'leri statik analiz şeridi ile çakışmaz)
→ orta/yüksek-risk sub-iter'lar sonra (W22-3 attribution +
W22-2 chat coverage — `packages/analysis_planner/` +
`appcore/contracts/schema_defs/` surface'leri statik analiz şeridi
ile potansiyel overlap).

| Iter | Stable ID(s) | Status |
|---|---|---|
| W22-0 | doc-reconcile — `week22` branch + 10-doc canonical preamble refresh (W21 → W22) + new W22 active-work tracker + §19 W21 plan header doc-close ("closed and merged via PR #30 / 5dc18aa") + §20 W22 plan header doc-open + W21 Pull-Forward Acceptance Bar "closed and merged" stamp (this section's predecessor) + W22 Roadmap Acceptance Bar "planning" → "active" promotion (this section) + README phase-pointer arch gate transition W21 → W22 + new W21 close-out fact gate `test_readme_phase_pointer_mentions_w21_closeout_merge` pinning PR #30 / `week21 -> main` / `5dc18aa` + `test_canonical_preamble_parity.py` fingerprint refresh (PR #29 → PR #30, `64a3c3d` → `5dc18aa`, tracker slot W21 → W22) | **closed** `26bb080` + `ff3fbbd` |
| W22-1 | `[GOAL taxonomy-chat-policy-adr]` (new) — Chat policy ADR `documents/adrs/0014-chat-and-language-model-tool-policy.md` Accepted (Option C — tool-only local coverage via `vscode.chat.createChatParticipant` + `vscode.lm.registerTool` + `vscode.lm.invokeTool`, GA since VS Code 1.90, no proposed APIs) + 2 architecture invariants at `tests/architecture/test_chat_policy_adr.py` | **closed** `906fcd5` + `d018fe1` |
| W22-2 | `[GOAL taxonomy-chat-coverage]` (new) — `chat` both tracks "missing" → "covered" (HARD TIER CLOSURE STATIC): `capabilities.py` 2 dict flips + `scenarios.py` 2 new ScenarioDefinition (`local_chat_participant_controller` + `local_language_model_tool_controller`) + `executor/flows/harness_extension/extension.js` GREENFIELD chat participant + LM tool registration per ADR 0014 + `stimulus_dispatch.js` REPLACE incomplete handler with API-level dispatch + 5 invariants + dict shape canonical pin + count pin 16→18 + fixture regen via `select_scenarios()` showing `missing_capabilities=[]` | **closed (static cut)** `ffbb743` + `d9e4558`; **runtime live-run anchor DEFERRED TO USER** per direction 2026-05-28 (Linux required) |
| W22-3 | `[FOLLOWUP attribution-count-parity-process-events]` + `[FOLLOWUP attribution-count-parity-output-channel]` (new) — Producer-side stamps at `executor/flows/playwright/attribution/links.py` for `kind=process` + `kind=output_channel_appendline` mirroring W17-1 activation paterni byte-identical + 2 new count helpers at `health/summary.py` + 8 invariant tests (4 per family) + LOC ceiling bump 537→552 | **closed** `cff10d3` + `70dc43a` |
| W22-4 | `[GOAL sandbox-evasion-defense-mvp]` (existing W18 candidate) — ADR `documents/adrs/0015-sandbox-evasion-defense-policy.md` Accepted (Draft Policy — 5-family taxonomy E1..E5 with per-family stance; W23+ implementation roadmap) + 2 architecture invariants at `tests/architecture/test_sandbox_evasion_adr.py` | **closed** `9a8ad28` + `ea418a6` |
| W22-5 | `[GOAL sandbox-evasion-canary-fixture]` (new) — `tests/security/test_sandbox_evasion_canary.py` (4 functions / 8 cases with parametrize: 1 taxonomy alignment + 5 family probes + 2 rejection safety nets) + new module `packages/analysis_planner/evasion_signals.py` (`EVASION_FAMILY_TAXONOMY` + `EvasionSignal` frozen dataclass) + Makefile `test-security` enrolment; `make test-security` 220 → 228 (+8) | **closed** `a6dd24b` + `1de616b` |
| W22-6 | `[GOAL container-hardening-ratchet-down]` (new, W21-4 §Deferred closure) — ADR 0013 §Deferred → §Closed; `docker-compose.yml` `read_only:true` + tmpfs mounts + `docker/seccomp.json` custom profile + +8-10 invariants + `test_seccomp_profile_sanity.py` + manual smoke (NoNewPrivs/Seccomp/Cap/mount/unshare) | **DEFERRED TO USER** per direction 2026-05-28 — Linux required for live-smoke; user-owned closure |
| W22-7 | `[GOAL activation-event-spec-gap-followup]` (new, conditional) — W20-0 crosswalk's 5 candidate events (`onMemento`, `onTerminalQuickFixRequest`, `onChat`, `onAuthenticationProvider`, `onRendererScript`) flagged by GPT review as NOT in official spec; no real-world fixture exercises a genuine gap | **skipped — `[NO-W22-7]` doc-only stamp** (W22 tracker §W22-7 section records the skip rationale) |
| W22-N | close-out hygiene + tracker freeze + §20 W22 close-out narrative + POST_POC W22 acceptance audit close (this section) + CLAUDE.md preamble W22-N close narrative. Phase-internal close-out had **NO PR** (per direction 2026-05-28). PR #31 `week22 -> main` subsequently **MERGED** `2026-05-28` via `1399f82`; the canonical preamble parity test fingerprint was refreshed to PR #31 / `1399f82` in the post-merge alignment (`6ded4c0`). | **closed** `11595c0` |

W22 acceptance final status (synthetic close; runtime live-run +
container ratchet-down deferred to user on Linux):

- **Must-pass** (live-run-driven from the W22 tracker checklist):
  - #1 ADR 0014 chat policy Accepted + local-only impl ✅
    (static; live-run pending user confirmation).
  - #2 ADR 0015 sandbox-evasion defense Accepted + impl W23+
    scope ✅.
  - #3 W22-3 attribution parity 8/8 green ✅.
  - #4 W22-5 canary fixture green ✅.
  - #5 W22-6 container ratchet-down active + manual smoke pass —
    **DEFERRED TO USER** (Linux required; ADR 0013 §Deferred
    remains open until user closes the lane).
  - #6 `coverage_summary.missing_capabilities == 0` ✅ static
    (fixture regen reflects post-W22-2 expected state); live-run
    anchor confirmation user-owned on Linux.
  - #7 W19 Hat-1 (`unaccounted_dropout == 0`) holds ✅ (no
    regression introduced statically).
  - #8 W19 Hat-2 (`harness_verification_unconfirmed_present`
    DROPPED) holds ✅ (no regression introduced statically).
  - #9 Static suite green — **re-verified on Mac `2026-05-28`** (the
    W22-N counts were transcribed, not run). A close-out `make check-all`
    found 2 pre-stamp gaps and fixed them in-branch: 3 stale
    `test_triggers.py` assertions (W22-2 `chat`-flip fallout) + inherited
    `ui/src/lib/types/contracts.ts` drift. Full gate now green ✅ —
    **2130 passed, 9 skipped, 8 deselected** (`tests/architecture/` 292;
    capability invariants 31; `make test-security` 228). Detail in the W22
    tracker §W22-N Close-Out Re-Verification.
- **Expected**: `tests/architecture/` 287 → 292 (+5; plan estimate
  was ~310 because W22-6 invariants were to add another ~10);
  `make test-security` 220 → 228 (+8; plan estimate was 220 → 222
  because W22-6 seccomp sanity test was to add +1); full suite
  ~2104 → ~2129 (W22-1 +2, W22-4 +2, W22-5 +8, W22-3 +8, W22-2 +5
  = +25); `automation_health.reasons` reduction expected at
  live-run (user-owned).
- **Stretch**: `automation_health.status: degraded → healthy` and
  `run_quality: medium → high` pending live-run confirmation.
  `[FOLLOWUP workspace-trust-stimulus-pass]` and
  `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` NOT pulled
  in this session (capacity used on the hard-tier closure work);
  remain available as opportunistic pulls for W23+.

**Plan motivation reference**:

- Live `ms-python.python` rapor: `output/activation_report_ms-python.python-2026.5.2026052001-992ad028f3df.json`
- `CAPABILITY_TAXONOMY` source: [`packages/analysis_planner/capabilities.py:8-27`](../packages/analysis_planner/capabilities.py)
- `OFFICIAL_EVENT_REGISTRY` count pin (29): [`tests/platform/contracts/test_registry_split_regression.py:101`](../tests/platform/contracts/test_registry_split_regression.py)
- Status enum (`healthy/degraded/inconclusive`): [`executor/flows/playwright/health/summary.py:260,378`](../executor/flows/playwright/health/summary.py)

## W23 Candidate Captures (audit 2026-06-01)

Surfaced by executing `[RESEARCH activation-event-spec-crosswalk]` (W20-0
forward-ref) against the official VS Code Activation Events page
(`https://code.visualstudio.com/api/references/activation-events`) on
2026-06-01. **Recognition layer is complete**: all 29 documented activation
event kinds (incl. `*`) are present in `OFFICIAL_EVENT_REGISTRY`
([`packages/analysis_planner/event_scenario_index.py:30`](../packages/analysis_planner/event_scenario_index.py)),
so the crosswalk found NO missing event _kind_ — this is distinct from the
already-skipped `[NO-W22-7]` `[GOAL activation-event-spec-gap-followup]`
(that one was about adding non-spec kinds). The gaps below are in
_sourcing_ and _stimulus fidelity_, not the kind taxonomy. None is urgent
(no live breakage); all are W23 candidates — the first two parked per user
direction `2026-06-01`, the third (`when`-clause sourcing) per `2026-06-03`.

| Stable ID | Description | Status |
|---|---|---|
| `[FOLLOWUP activation-event-contributes-implicit-synthesis]` (new) | **Blind to VS Code 1.74+ auto-generated activation events.** Per the official page, since 1.74.0/1.76.0 VS Code auto-generates `onCommand` / `onLanguage` / `onView` / `onCustomEditor` / `onAuthenticationRequest` / `onTaskType` from contribution points, so an extension may ship `activationEvents: []` and still activate. ExTrace's parser reads ONLY the declared `activationEvents` array ([`workflows/extension_catalog/manifest_parser.py:83-109`](../workflows/extension_catalog/manifest_parser.py)); `contributes` is fetched separately and used only as metadata / heuristic scenario hints, never to synthesize per-id `onX:<id>` attempts ([`workflows/marketplace/trigger_service.py:102-127`](../workflows/marketplace/trigger_service.py)). Proof: `assert activation_events == []` for a contributes-only fixture at [`tests/platform/contracts/test_analysis_fixture_baselines.py:419`](../tests/platform/contracts/test_analysis_fixture_baselines.py). **Impact**: a minimal-`activationEvents` extension is seen as ~zero events → falls back to the generic `workspace_probe` scenario; the specific activation paths VS Code actually uses (`onCommand:<id>` from `contributes.commands`, etc.) are never exercised, so the run under-represents the real activation surface. **Scope**: add a `contributes`→implicit-event synthesizer (gated to the 6 auto-generated families per the 1.74/1.76 note) feeding the same attempt pipeline; new fixture with empty `activationEvents` + `contributes.commands`; contract/count pins. Touches the parser/planner contract — opens with a design note. **Severity/Confidence**: Medium-High / High (grep-backed; both kinds match the spec, the gap is sourcing). Lane: `[marketplace-analysis]` + `[analysis-planner]`. | **partially addressed** — the `onCommand` sub-portion landed on branch `extension-trigger-matrix`: at the **planner** layer `_apply_contributes_metadata` ([`packages/analysis_planner/selection.py`](../packages/analysis_planner/selection.py)) now synthesizes a per-id `onCommand` attempt from every `contributes.commands` entry (`selected_by="contributes_command"`), independent of the declared `activationEvents`. Live-validated against `ms-python.python` (24/24 synthesized commands `verified` — see [`active-work/extension-trigger-matrix.md`](active-work/extension-trigger-matrix.md) → Activation Coverage Promotion). Still open: the `manifest_parser`/`trigger_service` sourcing layer is unchanged, and the other 5 auto-generated families (`onLanguage` / `onView` / `onCustomEditor` / `onAuthenticationRequest` / `onTaskType`) are not yet synthesized — W23 candidate. |
| `[FOLLOWUP activation-event-stimulus-fidelity-target-specific]` (new) | **Several families fire a GENERIC proxy, not the target's specific contribution → `attempted_only`, not `verified`.** `onWebviewPanel` creates a fresh panel ([`stimulus_dispatch.js:145`](../executor/flows/harness_extension/stimulus_dispatch.js)) but the event fires on webview RESTORE, not creation; `onNotebook`/`onRenderer` use a hardcoded `jupyter-notebook` + `text/plain` ([`:112`](../executor/flows/harness_extension/stimulus_dispatch.js)) so non-jupyter notebook types + arbitrary renderers aren't hit; `onTerminalProfile` opens a generic `/bin/bash` terminal not the contributed profile ([`:132`](../executor/flows/harness_extension/stimulus_dispatch.js)); `onWalkthrough` opens the generic picker not the target walkthrough id ([`:45`](../executor/flows/harness_extension/stimulus_dispatch.js)); `onDebug*` uses a command-palette proxy without starting a real session ([`:159`](../executor/flows/harness_extension/stimulus_dispatch.js)) — matches the live `debug_session` `attempted_only` outcome. **Explicitly EXCLUDES** `onChatParticipant` + `onLanguageModelTool` (harness exercises its OWN participant/tool by ADR 0014 Option C — intentional local-only, not a gap; [`:52`](../executor/flows/harness_extension/stimulus_dispatch.js) / [`:72`](../executor/flows/harness_extension/stimulus_dispatch.js)). **Impact**: these events still fire at the target's `activate()`, so coverage is not zero, but the harness can't re-invoke the target's specific contribution for `verified`-grade confirmation. **Scope**: per-family fidelity passes, each independent — pull opportunistically. **Severity/Confidence**: Low-Medium / High. Lane: `[executor]` + `[harness-extension]`. | pending — W23 candidate |
| `[FOLLOWUP contributes-command-when-clause-unused]` (new; captured 2026-06-03) | **A contributed command's `when` gate is stored but never sourced into the plan or evaluated — the harness force-invokes every command regardless of its condition.** The `when` clause that gates a command's palette visibility/enablement is captured in the DB schema (`extension_contributes_commands.when` at [`appcore/storage/model_defs/contributes.py:96`](../appcore/storage/model_defs/contributes.py); `extension_contributes_menus.when` at [`:137`](../appcore/storage/model_defs/contributes.py)) but is **dropped** when the trigger plan is built: `trigger_service.py` constructs `commands_data` from only `{title, command_id}` ([`workflows/marketplace/trigger_service.py:158-161`](../workflows/marketplace/trigger_service.py)), so `select_scenarios` never receives `when`. The planner then treats every `contributes.commands` entry as unconditionally invocable (`_apply_contributes_metadata` synthesizes an `onCommand` attempt regardless — [`packages/analysis_planner/selection.py:307-341`](../packages/analysis_planner/selection.py)), and the harness `executeCommand` backfill ([`executor/flows/harness_extension/stimulus_dispatch.js:174-176`](../executor/flows/harness_extension/stimulus_dispatch.js)) directly invokes the command, bypassing the `when` gate entirely. The UI Command-Palette primary is the only `when`-aware step; the backfill defeats it **by design** for coverage (session-fatal commands excluded via `_SESSION_FATAL_COMMAND_PATTERNS`, reload-class deferred via `_defer_window_reload_commands` — [`selection.py:35-43`](../packages/analysis_planner/selection.py) / `:46-76`). No `when` expression is parsed or evaluated anywhere (grep of `packages`/`executor`/`appcore`/`static_runtime` returns no `when`-clause evaluator). Sibling to `[FOLLOWUP activation-event-contributes-implicit-synthesis]` above (same sourcing seam; that one closed the `onCommand`-synthesis half on `extension-trigger-matrix`). **Impact**: coverage-positive (even `when`-gated commands are exercised), but the harness never models the activation _condition_ — so a `when`-gated command is indistinguishable from an always-available one, and a future rule keyed on conditional-activation context (e.g. secret-context / restricted-mode / view-focus gated commands) has no `when` signal to consume. **Scope**: (1) record-only first — thread the `when` string through `commands_data` → `select_scenarios` → attempt metadata, no behavior change; (2) optional follow-on rule/heuristic that flags or prioritizes high-risk `when` contexts. Touches the parser/planner contract — opens with a design note. **Severity/Confidence**: Low / High (grep-backed; no live breakage, this is fidelity + future-rule-surface hygiene). Lane: `[marketplace-analysis]` + `[analysis-planner]`. | pending — W23 candidate (post-PoC; user direction 2026-06-03) |

## Linux-Blocked Deferrals (resume when Linux env ready)

Single canonical list of work that cannot be validated on macOS — each item
needs a Linux host for its kernel / Docker-stack behavior. Stable IDs are
unchanged (contract); the detail rows stay in the W22 acceptance table above.
This section exists because the user's Linux environments are not ready yet
(direction `2026-05-28`); pull these once a Linux host is available.

- `[GOAL container-hardening-ratchet-down]` (W22-6) — ADR 0013 §Deferred →
  §Closed: `docker-compose.yml` `read_only: true` + per-service `tmpfs` +
  `docker/seccomp.json` custom profile (`unshare`/`mount`/`personality` deny)
  + +8-10 invariants + `test_seccomp_profile_sanity.py` + manual smoke
  (`NoNewPrivs`/`Seccomp`/`Cap`/`mount`/`unshare`). **Linux-only**: the
  `docker exec` syscall/mount verification does not run on Docker Desktop for
  Mac. Resumption checklist lives in the W22 tracker.
- `[GOAL taxonomy-chat-coverage]` runtime live-run anchor (W22-2) —
  `make sim-target TARGET=ms-python.python` to confirm
  `coverage_summary.missing_capabilities == []` on a live run and that W19
  Hat-1 (`unaccounted_dropout == 0`) + Hat-2
  (`harness_verification_unconfirmed_present` dropped) still hold. The static
  cut shipped (and is re-verified green on Mac); only the live anchor needs the
  executor Docker stack (Linux).
- ADR 0015 **E5 `process_introspection`** containment — depends on W22-6's
  `read_only` + seccomp + `cap_drop:[ALL]`; W23+ implementation. Bounding
  `/proc` visibility needs the Linux kernel surface to verify.

Resumption order: **W22-6 first** (its `read_only`/seccomp/`cap_drop` surface is
the prerequisite that bounds ADR 0015 E5), then re-capture the W22-2 live anchor
on the hardened stack.

## Codex Cloud Audit Backlog

### Post-W13 Candidates

W14- and W15-pulled items are below. Remaining for W15+:

_(W15-4 closed both surviving U-class entries on `2026-05-16`; the open
list is empty until the next Codex audit pass.)_

Closed via W14 (one-line audit trail; full rationale in archive):

- `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` — W14-2.
- `[FOLLOWUP codex-2026-05-10-M5-epoch-docker-exec-propagation]` — W14-5.2 (byproduct).
- `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` — W14-2.
- `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` — W14-3.
- `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` — W14-3 (see ADR 0009).
- `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` — W14-3.

Closed via W15 (one-line audit trail; full rationale in W15 tracker Per-Item Detail):

- `[FOLLOWUP codex-2026-05-10-M10-sync-analyze-typeerror-catch]` — W15-1 (`c58c365`); post-slate typing annotation hotfix follow-up landed `2026-05-16` via `976dc96`.
- `[FOLLOWUP codex-2026-05-10-M12-workspace-symlink-check-order]` — W15-2 (`765cde7`, path b fix).
- `[FOLLOWUP codex-2026-05-10-U8-activationevents-bounds]` — W15-3 (`3512a7c`).
- `[FOLLOWUP codex-2026-05-10-U1-U2-U3-ui-event-spread-cap]` — W15-4 (`89e13e3`).
- `[FOLLOWUP codex-2026-05-10-U6-relations-graph-cap]` — W15-4 (`89e13e3`).

### Quick Fixes

- `[FOLLOWUP codex-2026-05-10-I1-env-example-truthy-drift]` — closed `2026-05-11`.
- `[FOLLOWUP codex-2026-05-10-I2-ui-health-proxy]` — W15-5 (`43d6438`).
- `[FOLLOWUP codex-2026-05-10-I4-lifecycle-for-id-regex]` — W15-5 (`43d6438`).

### Posture Decisions

- `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]` — W15-6 (`be52520`, ADR 0011 Accepted; Option A).

### Verified Closed Audit Trail

H1, H7, M3, M6, M8, U5, U7, U9, U10, U11, I1, I2, I3, I4, M14a, plus
H4/H5/H6 are closed or WONT-FIX as recorded in the full snapshot. W15-5
closed I2 + I4 via `43d6438`; W15-6 closed U10 + U11 via `be52520`
(ADR 0011 Accepted; Option A). Do not re-open without fresh code
evidence.

## Current Open Items By Area

### Workflow / Platform

- `[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread` — **W17-3 scope-reduced; deferred to W18+** (W16-5 paterni; doc-only commit). Harness prerequisite is now MET (W17-2 landed `ff98235`
  with `LifecycleHarness` + `lifecycle_harness` fixture + cancel-via-
  heartbeat smoke), but the W17-3 design intent surfaced as
  **DESIGN-NEEDED**: the deferral note says "move sandbox-reset call
  from worker thread to heartbeat thread", yet the worker-thread
  `_reset_sandbox` call (`workflows/marketplace/analysis_service.py:155`)
  is a HARD SYNC POINT before
  `consume_harness_python_secret` (W13-11 / Codex F1 close-pass for
  W13-1 H6) — the reset restarts VS Code which writes the per-launch
  HMAC python secret to
  `/results/_extrace_harness_python_secret`; the secret MUST be
  consumed before the analyzed VSIX is admitted. The monitoring
  heartbeat thread itself only starts at step 4 (`_run_monitoring`,
  after install + triggers), so it cannot host the step-1 reset
  without a pipeline ordering refactor. Several plausible refactor
  shapes exist (dedicated reset thread started before step 1; merge
  heartbeat's cancel-path reset with step-1 reset via a queue;
  restructure pipeline to start heartbeat earlier) and the choice
  has different invariant cost: W13-1 HMAC marker wiring vs. W13-3
  two-phase cancel vs. W13-13 worker-entry CAS vs. W16-2 facade row
  lock. **W17 scope cap** keeps W17 focused on attribution-parity +
  harness + hygiene; the thread relocation belongs in a dedicated
  W18 sub-iter that opens with a design-decision ADR (or §16 plan
  entry) naming the chosen refactor shape and the invariant
  preservation strategy. The lifecycle harness at
  `tests/workflows/marketplace/test_lifecycle_harness.py` is ready
  for W18 — its module docstring already enumerates the three
  W17-3 extension points (parallel reset / idempotency /
  reset-during-finalize) so W18 inherits the rig with zero
  bootstrap cost. Pre-W17-3 description retained (original W16-5
  deferral context): The sandbox-reset call currently fires on the
  analysis worker thread in `workflows/marketplace/analysis_execution.py`;
  moving it onto the monitoring heartbeat thread (or any sibling
  background thread) is concurrency-sensitive — it interacts with
  the W13-3 two-phase cancel contract, the W13-13 worker-entry CAS,
  and the W16-2 facade's row lock discipline.
- `[FOLLOWUP simulation-progress-cancel] dedupe-step-progress-schemas` — **W16-5 rejected** after investigation. The two schemas
  (`appcore/contracts/schema_defs/analysis_jobs.AnalysisJobStepProgress`
  with `extra="forbid"`; `appcore/contracts/schema_defs/marketplace.AnalyzeJobStepProgress`
  with the default lenient Pydantic config) carry identical field
  shape (`completed: int >= 0`, `total: int >= 0`) but serve distinct
  surface roles: the internal storage layer needs the strict variant
  to catch typos at write time, while the public API surface drives
  TypeScript binding generation via `scripts/generate_ui_contracts.py`
  (line 70's `"AnalyzeJobStepProgress"` allowlist) and downstream
  external consumers may expect leniency for forward-compatibility.
  Aliasing the marketplace symbol to the analysis_jobs class would
  flip the public API to `extra="forbid"` silently (changes
  `__pydantic_config__.extra` on the same `__qualname__`) and the
  emitted TS binding's class name would shift to
  `AnalysisJobStepProgress`. Both are observable changes for callers
  outside the codebase. The dedupe value (35 LoC eliminated) does not
  justify the surface-role coupling or the breaking risk; the audit
  finding stays open as documentation but no schema change lands.
- `[FOLLOWUP simulation-progress-cancel] heartbeat-refactor` — **W17-4
  scope-reduced; deferred to W18+** (bundled with
  `heartbeat-sandbox-reset-off-thread` above; W16-5 paterni). The
  W17-2 harness prerequisite is now MET, but the heartbeat-refactor
  clarity gain is **bundled with the W17-3 thread-relocation
  design decision** — refactoring the heartbeat shape in isolation
  before deciding whether the thread will also host the step-1
  reset would land throw-away work. W18 pulls both together once
  the W17-3 refactor shape is named in an ADR / §16 plan entry.
  Pre-W17-4 description retained (W16-5 deferral context): Current
  heartbeat shape
  (`workflows/marketplace/analysis_execution._run_monitoring_heartbeat`
  L102-128 + thread setup L287-313) is functional and exercises
  every cancel-poll branch; the audit-driven refactor is a clarity
  gain rather than a correctness fix, so deferring without
  behavioral consequence is safe.
- `[FOLLOWUP analysis-thread-supervisor]`
- `[FOLLOWUP job-service-typevar-audit]`
- `[FOLLOWUP sqlalchemy-error-subtype-logging]`
- `[FOLLOWUP w11-8-companion-workflow-orm-bleed]` (W17+; DTO desen kararı ayrı ADR ister).
- `[FOLLOWUP analysis-job-worker-entry-crud-ownership]` — **closed at
  W16-2** via `9d6d110`. New row-lock-aware lifecycle CRUD primitive
  `claim_queued_analysis_job_at_worker_entry` (+ `WorkerEntryOutcome`
  enum + `WorkerEntryClaim` dataclass) extracted to
  `appcore/storage/crud_ops/analysis_jobs/lifecycle.py`;
  `workflows/marketplace/analysis_service.run_analysis_job` body
  refactored to dispatch on the returned outcome instead of issuing
  inline `SELECT ... FOR UPDATE` + branch + `db.commit()`. `AGENTS.md:57`
  hard rule compliance restored. W13-13 CAS pattern preserved
  byte-identically (row-lock-on-entry → branch-on-status → atomic
  finalize-or-promote); the W13-13 lock-asymmetry rationale (direct
  `finalize_cancelled_analysis_job` call vs. wrapper deadlock) moved
  from the caller docstring into the facade docstring. **Architecture
  gate** at `tests/architecture/test_run_analysis_job_entry_snapshot.py`
  re-targeted on the facade boundary per W14-6 "extend, do not
  duplicate" (INV1: claim helper is the first DB action in
  `run_analysis_job`; INV2: claim helper body contains both
  `with_for_update()` and `finalize_cancelled_analysis_job` AST call
  sites). All 6 W13-13 behavioral pins in
  `tests/platform/storage/test_analysis_jobs_cancel_at_worker_entry.py`
  stay green; one monkeypatch target moved from `analysis_service` to
  `lifecycle` because the W16-2 refactor removed the bare-name binding
  from the analysis_service module scope. Lifecycle surface pin
  (`test_module_path_pins_lifecycle_surface`) extended with the three
  new public exports.

Closed (one-line audit trail):

- `[FOLLOWUP simulation-progress-cancel] is-job-cancelled-session-churn` — W13-3.
- `[FOLLOWUP analysis-jobs-race]` — W14-4 (lifecycle.py lock symmetry).

### Contracts / Reports / Detection

- `[FOLLOWUP file-capture-pid-lineage-attribution]` — **landed `2026-05-29`
  on `static` (this commit).** Fixes the `target_file_events: 0` attribution
  gap for child-process file I/O. Verified-then-corrected a standing brief
  whose hypothesis ("strace lacks `-f`") was wrong — `-f` and the `[pid N]`
  prefix parser were already present, so its proposed fix was a no-op. Real
  fix in three parts: (W1) `/proc` PPID/cwd backfill
  (`runtime_capture/_shared.py`) seeding lineage for processes that pre-exist
  the attach; (W2a) `pid` on `FileEvent` dataclass + Pydantic contract +
  `FileRawContext`, `ACTIVATION_REPORT_SCHEMA_VERSION` 2.1→2.2 (additive),
  generated TS DTO; (W2b) pid-lineage attribution (`attribution/lineage.py`) —
  a strace file event whose owning PID descends from a process the target
  spawned during activation is attributed to the target even outside the
  ±1.25s temporal window, shared ext-host root PID deliberately excluded.
  Volume flags `-qq` + `-e signal=none` added (NOT `status=successful` — keeps
  failed/recon syscalls). Gates green (ruff/mypy/bandit/ui-types/ui-boundaries;
  full local suite 2061). Test pins:
  `tests/executor/test_runtime_capture_proc_backfill.py`; pid-lineage cases in
  `test_playwright_attribution_events.py`; pid-threading + cmd-flag cases in
  `test_playwright_extension_host_capture.py`.
- `[FOLLOWUP file-capture-w3-ancestor-attach-do-not-repeat]` — **reverted
  `2026-05-29`.** W3 attached strace to the VS Code **main** process (so `-f`
  would cover ext-host + pty-host from one attach). A live scan disproved it:
  report `output/activation_report_ms-python.python-2026.5.2026052901-2cb1bd9e7aa2.json`
  (18:00, schema 2.2) captured **0** strace file events + 4 thread-clones, vs
  the `df4471b` ext-host-attach baseline of 139 file / 53 process events. Root
  cause: `strace -f` follows only children forked AFTER attach, and the
  ext-host subtree pre-exists the attach (main resolves at attempt 1).
  Reverted `_find_vscode_attach_pid` to attach to the ext host. **Lesson:
  out-of-tree coverage needs a separate ADDITIVE attach, never an ancestor
  attach.**
- `[FOLLOWUP file-capture-out-of-tree-coverage]` — **deferred / pull-next.**
  Cause C: terminal/task processes are spawned by VS Code's pty-host (a
  sibling of the ext host), invisible to an ext-host-only strace. Fix = a
  SECOND strace attached to the pty-host (discover via `--type=utility` +
  `ptyHost`/`ptyHostMain` arg token, parent == VS Code main), merging its
  stderr into the existing single `_consume_stderr` consumer under a lock,
  keeping the ext-host attach primary (regression-free). Cause B (raw capture
  of activation-window I/O before attach) is a documented residual — `/proc`
  backfill mitigates lineage but not pre-attach capture. Both need live
  CPU/volume validation under `cpus: 2.0`.
- `[BUG scenario-dropout-upstream-root-cause]` — **closed via W14-1
  `2026-05-13`** (BLOCKER → HIGH); conservation guard at
  `scenario_accountant.py:392-438` is the fix-of-record.
- `[BUG silent-scenario-dropout-regression]` — **observation `2026-05-14`:**
  vuran versiyonu UI tarama'da gözlendi
  (`output/activation_report_ms-python.python-2026.5.2026051301-d2e24db709bd.json`,
  `15:15`): 5 requested scenario'dan 2'si (`debug_session`,
  `refactor_workflow`) `unaccounted_dropout` ile `skipped_scenarios`
  listesinde raporlandı; 3'ü (`project_exploration`, `coding_session`,
  `terminal_usage`) `status: completed`. Conservation guard
  (`scenario_accountant.py:392-438`) beklendiği gibi yakaladı; upstream
  emit-site fix hâlâ açık (`[FOLLOWUP scenario-accountant-conservation-split]`).
  **Second confirmation `2026-05-15` 09:51** (`e801c8d9c8b1.json`,
  post-rebuild against `week15` HEAD `c0c6066` which carries W15-1 +
  W15-2): identical drop set — same 2 scenarios, same `reason_code`,
  same downstream symptoms. The dropout is **deterministic** across
  runs and **not** a side effect of the W15-1/W15-2 changes; the
  upstream emit-site bug class is reproducible without retry.
- `[FOLLOWUP scenario-accountant-conservation-split]` — **dispatch
  layer closed at W16-1** via `01f910a` (HIGH prod regression,
  severity-leading W16 item). `dispatch._normalize_execution_result`
  outcome=None branch now emits `dispatch_outcome_none` (`reason_code`
  + non-empty `detail`) for each requested scenario instead of leaving
  them to the downstream
  `ScenarioAccountant._validate_scenario_conservation` last-mile
  guard's `unaccounted_dropout` fallback. Adjacent emit-site audit
  (W16-1 closure context): `executor/flows/playwright/stimulus/passes.py`
  already records specific reasons (`prerequisite_blocked`,
  `unsupported_activation_surface`, `unknown_scenario`) at L102-158
  per W11+; `executor/flows/playwright/automation.py` accounts every
  requested scenario by design (no silent drops at L275-365); planner
  (`executor/flows/playwright/entrypoint/triggers.py:22-38`) does not
  drop. Any new `unaccounted_dropout` surface would indicate an
  undiscovered emit-site, not the dispatch outcome=None bug class
  (now closed). **Observed in production `2026-05-14`:** debug_session
  + refactor_workflow drop edildiğinde `run_quality: low`,
  `automation_health.status: degraded`, `verification_gap: 2`
  (debug + terminal_tasks capability'leri verify edilemedi —
  dropout'un türevi). `signal_summary.level: needs_review` (score 28)
  — extension için risk_signals 0 olmasına rağmen attribution
  korelatif kaldığı için manuel review öneriliyor. **Deterministic
  confirmation `2026-05-15` 09:51** — bir saatlik rebuild + ikinci
  scan aynı state'i raporladı; root cause non-intermittent, repro
  fixture senkron çekilebilir. **W16-1 test pins:**
  `test_dispatch_outcome_none_emits_specific_reason_code` +
  `test_dispatch_outcome_none_emits_nothing_when_no_requested_scenarios`
  (`tests/security/test_scenario_dropout_repro.py`).
- `[FOLLOWUP report-finalize-top-level-field-sync-drift]` — **null-leakage
  half closed at W16-3** via `fa430f2` (W14 production scan-driven
  investigation). Root cause: the five analyst-facing scalars existed
  on the in-memory ``ActivationReport`` dataclass but had no slot on
  the strict-forbid contract
  (`packages/analysis_contracts/contracts.py` ``ActivationReport`` —
  ``StrictContractModel`` with ``extra='forbid'``). The save path in
  ``executor/flows/playwright/report_builder.save_report_payload``
  parses ``build_report_data`` output through
  ``_validate_report_against_contract`` and persists
  ``parsed.model_dump(mode='json')``; any field not on the contract
  was silently dropped at validation time. W16-3 adds the five fields
  as additive-optional schema slots (schema version unchanged at 2.1
  — same precedent as W14-5's ``executor_fingerprint`` extension) and
  populates them in ``build_report_data`` with explicit
  ``float()`` / ``list()`` / ``bool()`` coercions so a future writer
  cannot re-introduce the leak. Pin:
  `tests/security/test_report_finalize_field_sync.py` (5 round-trip
  tests; pre-W16-3 the file held an xfail-marked RED stub that
  predicted a heavier lifecycle harness would be needed; W16-3
  discovered the root cause at the contract seam and replaced the
  stub with direct save() round-trip pins). The attribution-count
  parity drift from the same `2026-05-14` observation is in a
  different code path (`build_signal_summary` /
  `attribution_summary` producer side) and lives under
  `[FOLLOWUP attribution-count-parity]` (new entry below).
- `[FOLLOWUP attribution-count-parity]` — **closed at W17-1** via
  `8c26d02` (W14 production scan `2026-05-14` evidence-vs-stream
  divergence half; W16-3 split). Root cause located at
  `executor/flows/playwright/attribution/links.py`
  `build_evidence_bundle`: the activation emit-site walked
  `report.activated[]` and emitted one `EvidenceEvent(kind="activation",
  ...)` per entry but never stamped `is_target_extension_event` —
  the only producer-side hole among the kind branches (network /
  file / process / output_channel_appendline all forward
  `is_target_extension_event` from the upstream typed event at
  links.py:173/218/264/302). Fix captures `target_extension_id =
  report.target_extension_id` at function entry and stamps
  `is_target_extension_event=bool(target_extension_id and
  activation.extension_id == target_extension_id)` on each
  activation `EvidenceEvent`. Mirrors `count_target_activations`'s
  empty-id guard so the two predicates are byte-identical at all
  inputs. 4 new invariant tests in
  `tests/executor/test_playwright_attribution_links.py` including
  the W17-1 contract pin
  (`test_build_evidence_bundle_target_activation_parity_invariant`).
  Pre-W17-1 description (W16-3 split context): W14 production scan
  `2026-05-14`: `attribution_summary.target_activation_count = 1`
  raporlanırken `evidence_events` listesinde
  `kind=activation,is_target_extension_event=True` hiç yok; ancak
  `target_extension_host` log stream'inde 1 entry mevcut. İki
  agregasyon kaynağı aynı aktivasyon için farklı target-flag verdiği
  için top-level sayım stream-türevli, evidence-kind sayımı 0.
  W16-3 (`fa430f2`) closed the contract-seam null-leakage half; W17-1
  closes the evidence-vs-stream divergence half at the producer
  emit-site.
- `[FOLLOWUP event-attempt-verification-status-validator]`
- `[FOLLOWUP report-invariants-runtime-evidence-drift]`
- `[FOLLOWUP compute-verdict-table-driven-test]`
- `[FOLLOWUP signal-summary-needs-review-categories]`
- `[FOLLOWUP monitor-types-property-recomputation]`
- `[FOLLOWUP activation-discovery-strategy-outcome-detail]`
- `[FOLLOWUP planner-executor-action-enum]`
- `[FOLLOWUP planner-selection-readability-audit]`
- `[FOLLOWUP attribution-links-build-evidence-bundle-density]`
- `[FOLLOWUP execute-attempt-rebloat-watch]`
- `[FOLLOWUP dispatch-execution-rebloat-watch]`
- `[CLEANUP rule-registry-side-effect-loader]` — dynamic `registry.py` now
  carries `_REGISTRY` global + `importlib` side-effect loader +
  `_BUILTINS_LOADED` for A1-A8 plus the demo canary; static runtime has the
  same lazy-loader shape for 26 production static rule ids (`s1`-`s20`). A flat
  `RULES` tuple is now more justified than the original six-rule W15 snapshot, but this
  remains W23+ hygiene unless rule loading itself becomes unstable.
- `[GOAL mitre-mapping-adr]` (new) — **W23-0 candidate (after static stream
  ES-5 closes).** ADR 0017 fixing the MITRE ATT&CK technique↔rule mapping
  strategy: technique→tactic source-of-truth shape, canonical ATT&CK Enterprise
  tactic ordering, the criticality signal (severity + `is_blocker`; dynamic
  rules carry no per-rule blocker — the dynamic gate is verdict-driven via
  `Verdict.MALICIOUS`, not per-rule), and the catalog-vs-overlay split.
  Framing doc for `[GOAL mitre-coverage-catalog]` + `[GOAL mitre-coverage-ui]`
  + `[GOAL mitre-static-overlay]`. **Severity/Confidence**: design / High.
  Lane: `[security-detection]` + `[static-analysis-pre-check]`.
- `[GOAL mitre-coverage-catalog]` (new) — **W23 candidate; INDEPENDENT (no ES-3b
  dependency).** Backend MITRE coverage catalog: a fresh
  `packages/analysis_contracts/mitre/` subpackage (technique→tactic→name map +
  `TACTIC_ORDER` + `resolve_technique`) + a hand-authored `RULE_MITRE_TECHNIQUES`
  `rule_id → (technique…)` map keyed by the granular PRODUCTION rule_ids of BOTH
  registries (static `static_runtime/rules/registry.get_production_rules()` +
  dynamic `packages/analysis_engine/rules/registry.get_all_rules()`) + a
  `GATE_BLOCKER_RULE_IDS = frozenset({"extrace.s2.typosquat"})` constant in
  `packages/analysis_contracts/static_detection/gate.py` realizing the ADR 0016
  `_PROMOTED_HIGH_BLOCKERS` token. Surfaced via a new `GET /api/mitre/catalog`
  route (`workflows/coverage/`) returning response-only DTOs
  `CoverageCatalogResponse`/`CoverageRuleEntry`/`CoverageRuleTechnique`/`CoverageTactic`
  (`appcore/contracts/schema_defs/coverage.py`, `schema_version` born at `"1"`),
  enumerating every rule with severity + MITRE technique/tactic + `is_blocker`.
  **Why an authored map**: rule objects expose only
  `rule_id`/`rule_version`/`lifecycle`/`severity`/`adversary_class`/`description`
  — the `attack.T####` categories and `confidence` live on _findings_, not the
  rule, so a report-independent catalog cannot read techniques off the rule
  object and must map them explicitly (a CI drift-guard test keeps the map
  honest). Enumerates the full ruleset including Semgrep once ES-4 lands.
  **Test**: `tests/platform/contracts/test_mitre_catalog.py` (tactic order +
  `resolve_technique` round-trip) + `tests/platform/contracts/test_rule_mitre_techniques_sync.py`
  (DRIFT-GUARD: map keyset == union of both registries' rule_ids) +
  `tests/workflows/coverage/test_coverage_catalog_endpoint.py` + generator-target
  extension at `tests/scripts/test_generate_ui_contracts.py` + `make ui-types`.
  **Risk**: the API process importing `static_runtime` — verify no heavy/optional
  deps + Docker image path; wrap enumeration in `try/except ImportError` to
  degrade to dynamic-only. Optionally pullable earlier as an `ES-4b` item
  (dependency-free) if the data layer is wanted before W23. **Severity/Confidence**:
  feature work / High. Lane: `[security-detection]` + `[static-analysis-pre-check]`.
- `[GOAL mitre-coverage-ui]` (new) — **W23 candidate; depends on
  `[GOAL mitre-coverage-catalog]`.** New `/mitre` UI page (NOT `/coverage` —
  avoids collision with the W20–W22 capability "coverage promotion" taxonomy):
  a MITRE ATT&CK-navigator-style matrix, tactics as columns × technique cells,
  each cell listing the rules mapped to it with severity color (reuse
  `ui/src/components/v3/tokens.ts` `RISK_COLOR`/`BADGE_TONE`, extended with a
  distinct critical + muted info), a static/dynamic marker + a blocker glyph;
  rule click opens the existing `ui/src/components/ui/SlideOverDrawer.tsx` with
  full rule detail (technique+tactic name, adversary class, categories, blocker).
  URL-param filters (severity/source/lifecycle) mirroring
  `ui/src/features/rules/RulesPage.tsx`; adapter + view-models under
  `Matrix*`/`RuleCatalog*` names to avoid colliding with the existing capability
  `Coverage*View` types. Wiring: route in `ui/src/app/App.tsx` + nav in
  `ui/src/app/layout/AppShell.tsx` (`NavId` + `NAV` + `activeIdFromPath`).
  **Severity/Confidence**: feature work / High. Lane: `[security-detection]` (UI surface).
- `[GOAL mitre-static-overlay]` (new) — **W23 candidate.** Per-report overlay
  on the `/mitre` page highlighting which techniques/rules FIRED for a selected
  analysis job. The backend/contract plumbing this used to depend on landed at
  the ES-5 close-out: the static report is already served to the UI via the
  additive optional `static_report: StaticAnalysisReport | None` on both
  `AnalyzeResponse` and `AnalyzeJobStatusResponse`
  (`appcore/contracts/schema_defs/marketplace.py`), loaded by
  `load_static_report_from_name` (`workflows/marketplace/analysis_reports.py`)
  and surfaced through the analyze router (`workflows/marketplace/router.py`),
  with the static DTOs (`StaticAnalysisReportDto` / `StaticDetectionReportDto` /
  `StaticDetectionFindingDto` / `StaticEvidenceRefDto` / `StaticGateOutcomeDto` /
  `StaticSeverityCountsDto` / `StaticToolExecutionRecordDto`) generated into the
  TS contracts; ALLOW/WARN now persists `static_report_path`, so the field is
  populated (no longer always None). Dynamic side works today via
  `detection_report.rules_executed`. Residual W23 scope is just the `/mitre`-page
  per-report overlay rendering + its test
  (`tests/workflows/marketplace/test_static_report_overlay.py`).
  **Severity/Confidence**: feature work / High. Lane: `[security-detection]` +
  `[marketplace-analysis]`.

Closed: `[FOLLOWUP evidence-event-kind-raw-context-invariant]` — W14-4
(9-kind allowlist + `@model_validator(mode='after')`).

### UI / Settings

- `[FOLLOWUP ui-raw-context-discriminator-parity]`
- `[FOLLOWUP ui-supplemental-types-retire]`
- `[FOLLOWUP vsix-integrity-in-activation-report]`
- `[FOLLOWUP vsix-thresholds-extra-keys]`
- `[BACKLOG ui-v3-5]` — Settings persistence API partially closed for
  Security thresholds; other localStorage sections client-only.
- `[CLEANUP ui-v3-9]`
- `[CLEANUP ui-v3-14]`

### Engineering Quality

- `[FOLLOWUP ci-reintroduction]`
- `[CLEANUP report-builder-naming]`
- `[CLEANUP monitor-runtime-naming-overlap]`
- `[GOAL container-hardening-baseline]` — **W18 candidate (intake
  2026-05-19; external security-posture review).** Mevcut Docker
  konteyner izolasyonunu ADR 0002 §1/§2 ("malicious extension
  contained on dev host") hedefini daha sıkı karşılayacak şekilde
  sıkılaştırmak: `cap_drop: ALL` + audit edilmiş minimum re-add
  (bugün `docker-compose.yml:103-105`'de `NET_RAW + SYS_PTRACE`
  yazılı gerekçe olmadan **eklenmiş** — `SYS_PTRACE` için
  necessity araştırması ve `NET_RAW` için executor capture
  contract dokümantasyonu ön-şart); `security_opt:
  [no-new-privileges:true, seccomp:custom-profile]` ve proje sahipli
  `docker/seccomp.json` (host-escape primitif syscall'larını —
  `ptrace`, `unshare`, `bpf`, `mount`, `pivot_root` — VS Code +
  analiz edilen extension surface için gereksiz olanlar — engeller);
  `read_only: true` root FS + açık `tmpfs` mount'lar (`/tmp`, log
  dirs, VS Code cache); `pids_limit` + `mem_limit` + `cpus` resource
  tavanları (fork-bomb / DoS sınırı). Non-root `USER executor`
  direktifi Dockerfile'da zaten doğru, korunur. **Mimari etki:
  sıfır production-kod değişikliği** — pure infra config +
  `tests/architecture/` altında 1 compose-property-invariant pin +
  `tests/platform/security/` altında 1 seccomp-profile-sanity pin +
  manuel konteyner-içi smoke. Threat model genişletmesi GEREKMİYOR;
  mevcut ADR 0002 §1/§2 hedefini daha iyi karşılar. Küçük bir
  **ADR 0002 amendment** veya yeni **`ADR 0008: Container Isolation
  Baseline`** ile posture karar yazılı hale getirilir. **Riskler:**
  (a) read-only root FS bilinmeyen bir yazma yolunu kırabilir
  (tmpfs mount ile düzeltilir); (b) seccomp profili dar/geniş
  dengesi — çok dar = analiz edilen extension çalışmaz; çok geniş =
  koruma yok; (c) `cap_add: SYS_PTRACE`'in gerekçesi bulunamazsa
  kaldırılır (test surface'ı debug-ergonomy düşüşüne karşı
  hassaslaşır). **W18 prerequisite:** yok — `week17 -> main`
  close-out merge'ünden sonra hemen pull-edilebilir; W17-3/W17-4
  deferred refactor'la rekabet etmez (farklı dosya seti).
  `[GOAL sandbox-evasion-defense-mvp]` ile bilinçli olarak ayrı
  tutuldu: bu entry threat-model-içi hardening, oraki entry
  threat-model genişletmesi gerektiriyor.
- `[GOAL sandbox-evasion-defense-mvp]` — **deferred W18+ candidate
  (intake 2026-05-19; pull only if W18 capacity allows after
  `[GOAL container-hardening-baseline]` closes and the W17-3/W17-4
  heartbeat refactor lands; otherwise W19+).** Playwright + xdotool
  katmanında "bu bir sandbox'tır" sinyallerini yumuşatmak —
  birincil hedef analiz edilen extension'ın sandbox tespit edip
  dormant'a düşmesini engellemek (false-negative riskini düşürür,
  birincil mission'a doğrudan hizmet eder). MVP scope: (1) klavye
  gecikmelerine jitter — `executor/flows/playwright/vscode/editor.py:41`
  hardcoded `xdotool --delay 30` rastgele 20-85ms aralığına;
  `page.keyboard.type(delay=10/20)` çağrıları (aynı dosya
  satır 58/114) da rastgeleleştirilir; (2) Playwright Chromium
  başlatma argümanlarına `--disable-blink-features=AutomationControlled`
  (gerçek bağlantı `reload_vscode.py:141` `connect_over_cdp()` —
  ya CDP-tarafı stealth ya da launch arg ekleme route'u; bu adım
  ADR'da netleştirilecek); (3) opsiyonel `playwright-stealth`
  paketi veya equivalent inline JS injection (Canvas/WebGL/UA
  fingerprint maskelemesi). **ADR 0002 §3 ile DOĞRUDAN ÇATIŞIYOR**
  — orada "Advanced sandbox evasion: Playwright CDP fingerprinting,
  detection of harness extension presence, detection of the
  analyzer via `navigator.webdriver` or equivalent" açıkça
  **OUT-OF-SCOPE** yazılı. Bu nedenle **kod yazımından önce yeni
  bir ADR şart**: (a) yeni threat actor sınıfı (sandbox-aware
  malicious extension) tanımı, (b) defense surface scope (hangi
  fingerprint vektörü modelleniyor — sadece `navigator.webdriver`
  + timing mi, yoksa tüm Canvas/WebGL/UA dahil mi?), (c) **ongoing
  maintenance commitment** kabulü (Chromium her sürümde yeni
  fingerprint vektörü ekliyor; stealth kodu _sessiz_ şekilde
  bozulabilir). **Mimari etki: cross-cutting kod değişikliği** —
  `executor/flows/playwright/` altında 8-15 dokunuş noktası
  (her klavye/mouse/timing call), yeni utility modülü
  (`extrace/stealth/jitter.py` veya benzeri), opsiyonel
  `playwright-stealth` dependency. **Kritik prerequisite (landing
  öncesi):** sandbox-detection canary fixture —
  `tests/security/test_sandbox_evasion_canary.py` benzeri bir
  test, `navigator.webdriver`, timing predictability, ve diğer
  probe'ları simüle eden bir kontrollü "extension"; bu fixture
  GREEN kalmadan stealth değişikliği landing yapma, yoksa Chromium
  sürüm yükselişinde sessizce bozulur ve fark edilmez. **MAC
  spoofing (`--mac-address`) + `/.dockerenv` masking deliberate
  olarak dışarıda** — daha agresif, daha kırılgan, eğer
  yapılırsa ayrı bir iteryon. **"Vakit kalırsa"** rasyoneli: W18
  birincil scope hardening + W17-3/W17-4 deferred refactor; bu
  entry üçüncü sırada, kapasite yetmezse W19'a kayar — ADR taslağı
  W18 içinde drafted olabilir, implementation W19'a düşse de
  threat model genişletmesi düşünme süresinden faydalanır.
- `[CLEANUP env-example-extrace-vars]` — **closed at W17-7b** via
  `fc88678`. `EXTRACE_EPOCH_RUN_ID` (W14-5 sub-commit 2 wiring;
  log run-id stamping; propagated across docker exec boundary)
  was the only EXTRACE_-prefixed env var used in source code
  (`appcore/logging.py:36`) but missing from `.env.example`.
  Added a commented `EXTRACE_EPOCH_RUN_ID=` entry to the OPTIONAL
  EXTRACE OVERRIDES block with operator-facing scope notes.
  (`EXTRACE_LOGGER_ROOT` matched the grep but is a Python
  `Final[str]` constant, not an env var — skipped.)
- `[CLEANUP postgres-version-fact-drift]` — **closed at W17-5** via
  `394d40d`. `executor/flows/playwright/workspace/seed_project_2.py:76`
  synthetic-fixture `docker-compose.yml` string bumped from
  `image: postgres:15` to `image: postgres:16-alpine` so the synthetic
  project surface aligns with the rest of the stack (CONTRIBUTING.md /
  README.md / `docker-compose.yml` all on postgres:16-alpine; W15-7
  digest-pinned the production compose at `54e7a93`). No test pins
  the fixture's postgres tag — verified by grep before edit; full
  non-smoke suite 1899 passed unchanged.
- `[CLEANUP adr-0007-runbook-wording-drift]` — **closed at W17-7c**
  via `326dac8`. Two wording-drift points fixed: ADR 0007 §2
  called the runbook "short" (now 192 lines), and the ADR §2
  prose + §Implementation §Follow-On bullet both enumerated the
  runbook's pre-flight items as 4 entries while the current
  runbook §Pre-Flight Checklist has 5 (item 5 "Re-read the threat
  model" added post-W8-7). Fix at both occurrences: drop the
  "short" qualifier, list all 5 items, declare the runbook the
  canonical source of truth so future evolution does not re-drift
  the ADR. ADR Context-section line numbers (pre-W8-7 historical
  state, immutable record) intentionally NOT updated.
- `[CLEANUP pre-commit-python-version-alignment]` — **closed at
  W17-7d** via `51dba29` (documentation-only resolution).
  Investigation surfaced three deliberate Python versions in play
  across the codebase (3.10 executor container shipped via
  `executor/container/Dockerfile` + gated by
  `tests/architecture/test_executor_container_python_compat.py`;
  3.11 API container shipped via `docker/api/Dockerfile` +
  `pyproject.toml` `requires-python = ">=3.11"` + ruff
  `target-version="py311"` + mypy `python_version="3.11"`; 3.12
  dev env + pre-commit interpreter). The lint tools read their
  own `target-version` / `python_version` from `pyproject.toml`,
  so pre-commit's interpreter does not affect lint output —
  only the W14-8 arch gate
  (`test_executor_container_python_compat`) and the per-tool
  pyproject targets gate the language-level surface. Fix: header
  comment block in `.pre-commit-config.yaml` documenting the
  three versions + rationale for pinning python3.12 (every dev
  env has it; pinning 3.11 would require devs to install a
  second interpreter for no behavioural gain). No interpreter
  or hook version change.
- `[CLEANUP test-import-graph-policy-dump-split]` — **pulled to W16-6**
  (hygiene splits bundle). `test_import_graph.py` carries 18 distinct
  architectural test functions in 767 LoC; thematic split
  (`test_import_isolation.py` / `test_facade_locks.py` /
  `test_executor_invocation.py` / `test_monitor_stimulus_boundary.py`)
  improves discoverability.
- `[FOLLOWUP health-reconciliation-responsibility-split]` — **closed at
  W16-4** via `304b99f` (behavior-preserving extraction; W13-1 HMAC
  + W13-12 fail-closed gates preserved). The 682-LoC monolith
  `executor/flows/playwright/health/reconciliation.py` split into three
  responsibility-aligned siblings:
  - `security.py` (~125 LoC, new): `HARNESS_PYTHON_SECRET_PATH`,
    `load_harness_python_secret` (W13-11 env-priority + defense-in-depth
    unlink), `_verify_harness_marker_signature` (W13-1 HMAC-SHA256
    constant-time compare).
  - `handshake.py` (~100 LoC, new): `_HARNESS_MARKER_RE`,
    `_harness_trace_records_by_attempt`,
    `_attempt_has_harness_completion_trace` (W13-12 three-branch dispatch
    — HMAC verify / fail-closed / legacy phase-only).
  - `reconciliation.py` (~440 LoC, slimmed from 682): event-attempt
    verification state machine + coverage track reconciler.
  Architecture gates re-targeted (W14-6 extend-not-duplicate; no new
  gate files): `tests/architecture/test_harness_marker_auth.py` parses
  `handshake.py` for the `_attempt_has_harness_completion_trace ->
  _verify_harness_marker_signature` wiring;
  `tests/architecture/test_harness_secret_eager_consume.py` gate 3
  parses `security.py` for the env-priority ordering. Test-side import
  paths updated: `dispatch.py` + 3 inline test imports moved from
  `..health.reconciliation` to `..health.security`. Risk-class
  separation: a future small edit can now target a single
  responsibility (security primitives, handshake dispatch, or event-
  attempt state machine) without the reviewer needing to reason across
  the cross-concern coupling that the pre-W16-4 monolith carried.
  Pre-W16-4 rationale retained below for the audit trail (W15 mid-iter
  finding context).

  _Pre-W16-4 audit context (preserved verbatim):_
  Risk class: change-safety drift — the same file owned both
  fail-closed security gates (W13-1 / Codex H6 HMAC anchor) and
  report-coverage classification. A future small edit could regress
  security or report fidelity without the reviewer noticing the
  cross-concern coupling. Recommendation: map responsibility
  boundaries first (which functions own which risk
  class), validate test coverage on both sides, then do a behavior-
  preserving extraction. **Do not auto-refactor**; W13-1 HMAC gates
  must not regress. W15+ hygiene; new audit finding `2026-05-16`.
- `[CLEANUP marketplace-router-test-suite-split]` — **pulled to W16-6**
  (hygiene splits bundle). `tests/workflows/marketplace/test_router.py` (2374 LoC). Title
  docstring at :5 implies search/download scope but file spans analyze
  (:744), trigger planning (:778), background job persistence (:1581),
  and async job endpoint (:2080). Test-maintenance burden only — no
  runtime risk. Recommended: classify-then-split by domain
  (search/download + sync analyze + trigger planning + background job
  lifecycle + async job endpoint) with behavior-preserving moves.
  Not a W15 priority; W16+ hygiene candidate. New audit finding
  `2026-05-16`.

Closed (one-line audit trail):

- `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]` — W14-6.6 (`e42a448`).
- `[FOLLOWUP arch-gate-executor-control-outbound]` — W14-6.5 (`b031803`).
- `[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]` — W14-6.4 (`2adad43`).
- `[CLEANUP appcore-config-stale-docstring]` — `2026-05-11`.
- `[CLEANUP session-docstring-except-exception]` — `2026-05-11`.
- `[CLEANUP uri-validation-stale-sys-path-comment]` — `2026-05-11`.
- `[FOLLOWUP compose-image-mutable-ref-pin]` — W15-7 (`54e7a93` compose pin + `7ebbbfb` test extension; postgres:16-alpine + alpine/socat:1.8.0.3 manifest digest pin; `tests/architecture/` 196 → 198).
- `[FOLLOWUP gh-action-trivy-version-pin]` — W15-7 (`452f1a1`; `aquasecurity/trivy-action@v0.36.0` version tag pin matching repo `actions/*@vN` precedent).

### Test + Observability

- `[FOLLOWUP w8-0-capture-pipeline]`
- `[FOLLOWUP w8-1-extract-rejection-logging]`
- `[FOLLOWUP w8-1-archive-count-bypass]`
- `[FOLLOWUP w8-1-vsix-compressed-size-limit]`
- `[FOLLOWUP w8-3-harness-js-scheme]`
- `[FOLLOWUP w8-4-broader-executor]`
- `[FOLLOWUP w8-6-content-sample-structural-test]`
- `[FOLLOWUP w8-8-manifest-emit-when-needed]`
- `[FOLLOWUP w8-8-trigger-sweep-as-test]`
- `[FOLLOWUP w8-9-network-body-boundary-split-secret-test]`
- `[FOLLOWUP codex-automation-6]` — UI failure taxonomy for operator
  clarity; W15+.
- `[FOLLOWUP capability-verification-gap]` — `NEEDS-DESIGN`; W15+.
- `[FOLLOWUP adr-0002-vsix-extraction-section-missing]`

Closed: `[FOLLOWUP codex-automation-5]` — W14-5.3 (`db25d5f`); executor
runtime fingerprint module + automation output emit + ActivationReport
`executor_fingerprint` field.

### Product Vision (Post-Extrace)

- `[GOAL marketplace-user-scan-and-notify]` — Tüketici-yönlü marketplace
  akışı. **Extrace bitiminden sonra** ele alınacak; şu an yalnızca vizyon
  notu — kod / tracker yok. Dört yetenek halkası:
  1. **Kullanıcı taraması (request)**: kullanıcı marketplace içinde bir
     eklenti gördüğünde "tara" isteği atabilir; istek mevcut analiz
     pipeline'ına (W16-2 lifecycle CRUD + `workflows/marketplace/router.py`
     `/api/marketplace/analyze/start`) bağlanır.
  2. **Kurulum kapısı (gate)**: tarama sonucu güvenli ise kurulum
     izni verilir, güvensiz ise engellenir. Karar eşiği + appeal yolu
     ayrıca tasarlanacak.
  3. **Ekip raporu e-postası**: her tarama olayında ekibe e-posta —
     zaman damgası, taramayı isteyen kullanıcı, eklenti kimliği +
     sürümü, çalıştırılan adımlar, üretilen risk bulguları.
  4. **Retroaktif uyarı e-postası**: bir eklenti sonradan zararlı
     olarak işaretlendiğinde, o eklentiyi daha önce kuran kullanıcılara
     ve onların ekiplerine bilgi e-postası gönderilir (kurulum
     envanteri ↔ risk re-değerlendirme bağlantısı gerekir).

  Bu kalem pull edildiğinde tracker doğal yeri:
  `documents/agent-lanes/marketplace-analysis.md` veya yeni bir
  `documents/active-work/<iter>-marketplace-user-flow.md`.
  Sürüklenen prior art: `workflows/marketplace/router.py`,
  `analysis_service.py`, `job_service.py`, `client.py`; UI tarafında
  `/marketplace?q=…` (ui/README). E-posta + retroaktif envanter
  altyapısı şu anda yok — yeni bileşenler.

## Newly Captured (v1.0 roadmap intake 2026-06-08)

Forward roadmap recorded at
[`active-work/v1-roadmap.md`](active-work/v1-roadmap.md) — the v1.0 arc that
turns ExTrace into a real, daily-usable single-operator defensive tool (user
direction `2026-06-08`, after the project report was delivered). Built from a
7-dimension real-tool gap assessment; every file/line claim verified against
`main` @ `441cb72`. Stream 1 (`reliability-self-defense`) **merged to main** via PR #35
(`week23 -> main`, `653d807`) `2026-06-12` (S0 + S1 + S2 + S3 + S4 + S5 + S7) — see
[`active-work/W23-reliability-self-defense.md`](active-work/W23-reliability-self-defense.md).
The active-stream pointer flip (S0) landed `2026-06-12` — `phase.json` +
canonical doc preambles/bodies now name `reliability-self-defense`
(`last_merged_weekly` stays W22 — a named feature stream does not advance the `phase.json` weekly pointer; see REFACTOR_STATUS.md "Post-W22 Feature Streams").

Detailed evidence and dispositions are archived at
[`archive/backlog/v1-roadmap-intake-2026-06-08.md`](archive/backlog/v1-roadmap-intake-2026-06-08.md).
Stable IDs below map to the roadmap streams (see `v1-roadmap.md` §7).

- **Stream 1 — reliability-self-defense (merged to main via PR #35 `653d807`):** `[BUG report-builder-unbounded-pem-redact]` ✅ S1 `729d0d3`, `[BUG wedged-job-no-same-boot-recovery]` ✅ S2 `2026-06-12` (migration `c3f8a1d7e9b2` nullable `last_heartbeat_at`; same-boot heartbeat + stale-running reaper + terminal-write guard; `744b3e1`/`eb79f79`), `[FOLLOWUP offline-vsix-size-bound]` ✅ S3/F-2 `e3a8af6`, `[BUG import-graph-relative-import-gate-gap]` ✅ S3/F-3 `818c6be`, `[BUG verdict-color-inconclusive-renders-clean]` ✅ S4 (canonical v3 verdict palette; INCONCLUSIVE → neutral STOP), `[FOLLOWUP exthost-logparse-redos-bounds-sweep]` ✅ S5 (audit: family line-anchored/linear; one unanchored greedy-prefix pattern bounded `{1,256}` + 16 KiB per-line cap).
- **Stream 2 — reliability-multi-analyze:** `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` (existing; do not duplicate).
- **Stream 3 — verdict-provenance-reproducibility:** `[GOAL vsix-content-sha256-provenance]`, `[GOAL verdict-reproducibility-anchor]`.
- **Stream 4 — operator-report-export:** `[GOAL report-export-artifact]`, `[FOLLOWUP vsix-entry-log-sanitization]` (existing; do not duplicate), offline skip-reason UX.
- **Stream 5 — release-identity-ops:** `[CLEANUP version-identity-coherence]`, `[GOAL api-health-db-probe]`, `[GOAL podman-backup-restore]` (live-on-Fedora acceptance deferred via `[FOLLOWUP fedora-host-live-validation]` below — code still lands on dev/CI).
- **Stream 6 — measured-catch-rate:** `[GOAL measured-catch-rate-corpus]`, `[GOAL benign-false-positive-gate]`, `[GOAL platform-blind-verdict-annotation]`, `[GOAL adr-0015-e1-e2-evasion-detection]`.
- **Stream 7 — sequential-batch-corpus (post-v1.0):** `[GOAL sequential-batch-corpus]`.
- **Stream 8 — linux-host-hardening-evasion (post-v1.0):** `[GOAL container-hardening-ratchet-down]`, `[GOAL adr-0015-e3-e5-evasion-detection]`, `[FOLLOWUP harness-secret-distribution-redesign]` (existing; do not duplicate).
- **Operator-console-honesty (merged to main via PR #36 `1e3fba6`; non-bar):** `[CLEANUP settings-decorative-controls-honesty]` ✅ H1, `[CLEANUP system-mock-status-honesty]` ✅ H2 (+ `/api/health` tone case-bug fix), `[GOAL light-dark-theme]` ✅ H3 (delivered; ECharts canvas charts stay dark — deferred, see tracker). Also wired timeZone + density (H1b). Tracker: `active-work/W24-operator-console-honesty.md`.
- **Stream 9 — operator-settings-ops (post-v1.0):** `[GOAL operator-settings-server-persistence]`, `[GOAL telemetry-retention-purge]`, `[GOAL danger-zone-destructive-actions]`.
- **Stream 10 — operator-disposition (post-v1.0):** `[GOAL benign-domain-disposition]` (raw versus adjusted reporting; annotation only; excluded from the B8 raw gate).
- **Stream 11 — network-egress-enforcement (post-v1.0):** `[GOAL mitmproxy-tls-interception]`, `[GOAL egress-allowlist-enforcement]` (ADR + spike gated; depends on Stream 9).

### Fedora-gated live-validation — deferred (user direction `2026-06-12`)

`[FOLLOWUP fedora-host-live-validation]` (new) — the parts of the roadmap that
need a **physical Fedora host** are explicitly deferred here so they never block
stream code from landing. Resolves `v1-roadmap.md` §10 Open Question 1 by
deferral, not by acquiring the box. Scope:

- **Stream 5 (`release-identity-ops`)** — `extrace-ctl.sh backup`/`restore` and
  `/api/health` real-host proof. The **code lands and is validated on the macOS
  dev host / CI** (endpoint unit + integration tests, backup/restore round-trip
  against the dev DB). Only the **on-real-host live acceptance** (Podman on
  Fedora, upgrade-survives-history smoke) is deferred to this item. Stream 5 is
  **not blocked** — it ships with dev/CI validation and a documented "live-host
  proof pending" note.
- **Stream 8 (`linux-host-hardening-evasion`, post-v1.0)** — kernel/seccomp
  ratchet-down validation (`read_only` + tmpfs + custom seccomp from ADR 0013
  §Deferred / W22-6) needs live kernel smoke on Fedora. Already post-v1.0;
  remains deferred until the box is in hand.

**Pull-back trigger:** Fedora box physically available → run the live smokes,
stamp Stream 5 live-acceptance, schedule Stream 8. **Severity/Confidence:**
N/A (planning-gate) / High. Lane: `[deploy]` + `[executor]`.

## Newly Captured (extrace-audit `2026-06-15`)

Surfaced by `/extrace-audit` (read-only multi-agent defensive-security +
architecture audit) against `main` @ `9471ffe`; code is byte-identical at the
current `d3b20ea` (that commit is docs-only). Overall verdict: **Mostly healthy
with risks** — no Critical/High, no hard-rule violation, all 16 ADRs aligned, and
all 18 `guard_test_drift.sh` flags independently adjudicated benign (refactors
re-pin invariants, never silently weaken). The dominant theme is **redaction-
contract completeness**: redaction is enforced per-field (with per-field AST gates)
rather than at one serialization chokepoint, so three extension-controlled report
sinks fall outside the gated set. None is urgent (narrow exploitability, no live
breakage); recorded here as evidence-cited, none-blocking captures.

| Stable ID | Description | Status |
|---|---|---|
| `[BUG report-field-redaction-completeness]` (new) | **Three extension-controlled strings reach the persisted `ActivationReport` without `redact_secrets`, while sibling fields are redacted.** (F1) activation-log `message`/`activation_event` — captured via `(?P<event>[^']*)` at [`extension_host_log_parse.py:19,28`](../executor/flows/playwright/runtime_capture/extension_host_log_parse.py) (admits space/`:`/`=`/`@`, influenced by extension `package.json` `activationEvents`/command IDs), built at [`monitor/runtime.py:366`](../executor/flows/playwright/monitor/runtime.py), written into `LogStreamEntry` at [`monitor/scenario_accountant.py:574-576`](../executor/flows/playwright/monitor/scenario_accountant.py), serialized via `asdict` at [`report_builder.py:408-411`](../executor/flows/playwright/report_builder.py) (contrast `:413` which redacts `extension_host_output`). (F2) `FileEvent.path/secondary_path/summary/flags` built from strace output at [`runtime_capture/filesystem.py:108-120`](../executor/flows/playwright/runtime_capture/filesystem.py), serialized at [`report_builder.py:384`](../executor/flows/playwright/report_builder.py) + copied into the file `EvidenceEvent` at [`attribution/links.py:226,234,237`](../executor/flows/playwright/attribution/links.py) — the **sibling `NetworkEvent` producer redacts the identical field class** at [`runtime_capture/network.py:109-110`](../executor/flows/playwright/runtime_capture/network.py) (explicit shared-chokepoint comment). (F3) `ProcessEvent.command`/`cwd` at [`extension_host_strace_parse.py:71,88,97`](../executor/flows/playwright/runtime_capture/extension_host_strace_parse.py) unredacted while sibling `arguments_preview` is redacted at `:108`. **No AST gate covers any of these** (only `test_arguments_preview_redaction.py` / `test_network_uri_summary_redaction.py` / `test_network_body_preview_redaction.py` exist). **Impact**: a `db_url` DSN (`scheme://user:pass@host`) or AWS key-id (`AKIA…`) inside an extension-created path or activation-event token persists verbatim in the report. **Exploitability narrow** (path/event tokens carry no spaces, so `Bearer`/`api_key=`/`AWS_…=` patterns in [`evidence.py:28-81`](../packages/analysis_contracts/evidence.py) are unreachable; only `db_url` + `AKIA…` are) → caps at Medium. **Scope**: route the three field clusters through `redact_secrets` at construction (or redact at the `report_builder` serialization chokepoint so future sinks inherit it) + add the three missing AST gates mirroring `test_arguments_preview_redaction.py`; behavioral test (`tests/security/`) proving a DSN-in-path is redacted in the persisted report. No new deps, no contract field additions. **Severity/Confidence**: F1+F2 Medium / Medium, F3 Info / Medium. Lane: `[executor-runtime]` (CRSC-2). Regression surface: CRSC-2 / W12-5 / W13-6 / W14-3 (the field-by-field redaction this completes). | pending — fix small + isolated; can ride any stream close-out |
| `[BUG reset-cdp-needle-stale]` (new) | **Between-scan VS Code terminate logic keys on a CDP flag the default boot no longer sets.** [`reset_state.py:32`](../executor/flows/playwright/reset_state.py) defines `_VSCODE_PROCESS_NEEDLE = "--remote-debugging-port"`, consumed by `pgrep -f` in `_find_vscode_pids()` at `:63`, feeding `terminate_vscode()` from `reset_executor_state()` at `:179`. Since W14-3 made CDP opt-in ([`launch_vscode.sh:27,96-99`](../executor/container/launch_vscode.sh): `EXECUTOR_CDP_PORT` empty default; flag appended only when non-empty), the default-boot VS Code argv carries no such flag, so the needle matches nothing and `terminate_vscode()` no-ops — relaunch proceeds only because `cleanup_singleton_locks()` (`:182`) drops the Chromium `SingletonLock`. `tests/executor/test_reset_state.py` mocks `_find_vscode_pids`, so the real needle-vs-CDP-off path is unexercised. **NOT a security regression** — unauthenticated CDP is correctly closed by default (verified across launch_vscode.sh/start.sh/compose + `test_cdp_port_default.py`); this is a reliability/correctness side-effect of the (correct) CDP hardening. **Scope**: re-derive the needle to match the actual default VS Code/Electron process (or make explicit terminate CDP-flag-independent) + a test exercising the CDP-off path. **Severity/Confidence**: Low / Low. Lane: `[executor-runtime]`. Overlap: closed-regression vs the W14-3 CDP-opt-in stream. **Maps to Stream 2** (`reliability-multi-analyze` / B2 — same-container between-scan reset). | **RESOLVED 2026-06-24** (`4437d1e`): diagnosis corrected — the no-op is actually a malformed `pgrep -f --remote-debugging-port` (missing `--` separator → exit 2), which fails in EVERY config (incl. CDP ON), not only CDP-off; fixed with the multi-analyze reset (pgrep `--` + CDP-independent needle + `/proc` tree reap). See [`active-work/reliability-analyze-resilience.md`](active-work/reliability-analyze-resilience.md) §B2. |
| `[CLEANUP pragma-ratchet-docstring]` (new) | **Doc drift in a guard-test docstring; the gate itself is correct and stricter.** [`tests/architecture/test_bare_binary_pragma_ratchet.py:20-33`](../tests/architecture/test_bare_binary_pragma_ratchet.py) docstring states "Baseline … Total: 6 pragmas" and lists only 3 files (editor.py:3, reset_state.py:2, runtime.py:1), claiming sub-commit 6 lowered 7→6. But the enforced constants are `_BASELINE_PRAGMA_COUNT = 7` (`:51`) and `_EXPECTED_PRAGMA_DISTRIBUTION` (`:53-58`) including `vscode/__init__.py:1`, summing to 7 across 4 files — matching disk (the `vscode/__init__.py:61` pragma carries a `# W19-X` marker, added after the docstring was last edited). The ratchet still fires on any growth; **no security impact, documentation-only**. **Scope**: one-line docstring fix (6/3-files → 7/4-files). **Severity/Confidence**: Info / High. Lane: `[docs-maintenance]`. | pending — trivial |
| `[CLEANUP event-attempt-validate-assignment]` (new) | **`EventAttemptRecord` lacks `validate_assignment`, so `confirmation_source` attribute-set sites skip the field validator.** [`StrictContractModel`](../packages/analysis_contracts/contracts.py) sets `model_config = ConfigDict(extra="forbid")` but not `validate_assignment=True`; [`EventAttemptRecord`](../packages/analysis_contracts/contracts.py) (`:223`) inherits that. The reconciliation path mutates by direct attribute assignment at [`health/reconciliation.py:348,363`](../executor/flows/playwright/health/reconciliation.py), which under Pydantic v2 (no `validate_assignment`) bypasses `_validate_confirmation_source` (`contracts.py:266-274`). **Benign today** — both assigned literals (`"harness_nonce"`/`"log_record"`) are members of `_VALID_CONFIRMATION_SOURCES`, and every untrusted-input path enters via validated model construction ([`monitor/payload.py:101`](../executor/flows/playwright/monitor/payload.py)). Latent only: a FUTURE out-of-set attribute assignment would persist unvalidated. Contrast `ContentSample` which deliberately sets `validate_assignment=True`. **Scope**: either set `validate_assignment=True` on `EventAttemptRecord` (cheap, consistent with `ContentSample`) or stamp the two set-sites through the validator. **Severity/Confidence**: Info / Low. Lane: `[platform-storage]` / `[security-detection]`. | pending — hardening hygiene |

**Also noted, already tracked (not re-captured):** the container-isolation runtime
gates (`test_container_entrypoint.py` + the runtime layer of
`test_compose_isolation_invariants.py`) `pytest.skip` on a non-Docker dev host, so
their runtime cap/flat-mode invariants are verified at compose/AST level only — this
real-environment coverage gap is already covered by
`[FOLLOWUP fedora-host-live-validation]` (above) + Stream 8
`[GOAL container-hardening-ratchet-down]`. The raw-VSIX-entry-name logging
(`client.py:269/319`) remains `[FOLLOWUP vsix-entry-log-sanitization]` (Stream 4).

### Resolved on main — reliability-analyze-resilience (2026-06-25)

Two reliability fixes landed directly on `main` (not a named-stream PR), from an
analyze-timeout incident on the running appliance. Full detail + corrected
root-causes:
[`active-work/reliability-analyze-resilience.md`](active-work/reliability-analyze-resilience.md).

| Stable ID | Description | Status |
|---|---|---|
| `[BUG analyze-timeout-no-incontainer-kill]` (new) | The host-side `_AUTOMATION_TIMEOUT` killed the `docker exec` client but not the in-container entrypoint; its W22 SIGTERM handler cannot unwind a CPU-bound C-stage, and `_cleanup_stale_entrypoint_processes()` sent only one SIGTERM → a timed-out analyze burned ~100% CPU past its deadline and wedged the next run. Fix: cleanup escalates SIGTERM → grace(10s) → SIGKILL (`host.py`, baked in `automation_api`). Lane: `[executor]`. | **RESOLVED 2026-06-25** — `tests/executor/test_host_entrypoint_cleanup.py`; live: copilot re-run completed 160s, no zombie. |
| `[GOAL stimulus-early-giveup-nonresponsive-target]` (new) | A non-responsive target (copilot-chat: ~558 trigger attempts, no auth/network → zero effect) drove the interaction phase past the 1800s budget. Fix: `run_stimulus_plan` gives up after 60 consecutive attempts with no cheap target reaction (in-memory file/network events, NOT the expensive `capture_runtime_snapshot`), marking the remainder skipped (`skipped_after_early_giveup`); any real reaction resets the counter. Lane: `[executor]`. | **RESOLVED 2026-06-25** — `tests/executor/test_stimulus_early_giveup.py` + 153 regression; deployed-executor proof. |

## Newly Captured (extrace-audit 2026-06-25)

A read-only `/extrace-audit` pass against `main` @ `8a0057d` (multi-agent: 3
investigation passes → adversarial critic → 4 verifiers → consolidation).
**No new findings** — every surfaced item is already tracked below, and the
newest code (W23 `reliability-self-defense`, the analyze-resilience fixes, and
the `operator-console-honesty` UI work) introduced **zero new regressions**.
Overall verdict: **Mostly healthy with risks** — 0 Critical / 0 High, no
hard-rule violation, all 16 ADRs aligned. Recorded here only as a
re-confirmation of already-open items at current HEAD (line numbers re-verified;
stable IDs unchanged). The first investigation pass mis-marked CRSC-2 redaction
"verified-clean"; the adversarial verification round overturned it by reading the
_un-enumerated sibling sinks_ — the methodological catch this format exists for.

| Stable ID | Re-confirmation @ `8a0057d` |
|---|---|
| `[BUG report-field-redaction-completeness]` | **Still-open.** F1 `monitor/scenario_accountant.py:576` (`activation_event`), F2 `runtime_capture/filesystem.py:112` (`FileEvent.path/secondary_path/summary/flags`; sibling `runtime_capture/network.py:109-110` redacts the identical field class), F3 `runtime_capture/extension_host_strace_parse.py:61` (`ProcessEvent.command/cwd`; sibling `arguments_preview` redacted at `:108`). The **three AST gates are still absent** (only `test_arguments_preview_redaction.py` / `test_network_uri_summary_redaction.py` / `test_network_body_preview_redaction.py` exist). Severity F1+F2 Medium, F3 Info (narrow: extension must self-plant a `db_url`/`AKIA…` token into a captured path/command/log). Fix can ride any stream close-out as pre-close hygiene; prefer routing the three clusters through `redact_secrets` at the `report_builder` serialization chokepoint so future sinks inherit it, + the 3 missing AST gates. |
| `[CLEANUP pragma-ratchet-docstring]` | **Still-open.** `tests/architecture/test_bare_binary_pragma_ratchet.py:29` docstring says "6 pragmas / 3 files"; enforced constants (`:51` `_BASELINE_PRAGMA_COUNT=7`, `:53-58` 4 files incl. `vscode/__init__.py:1`) are correct/stricter. Info, docstring-only one-line fix. |
| `[CLEANUP event-attempt-validate-assignment]` | **Still-open.** `EventAttemptRecord` (`contracts.py:223`) inherits `StrictContractModel` (`:47`, `extra="forbid"`, no `validate_assignment=True`); attribute-set sites `health/reconciliation.py:348,363` bypass `_validate_confirmation_source` (`contracts.py:266-274`). Benign today (both literals in-set), latent only for a future out-of-set assignment. Info; fix = set `validate_assignment=True` (consistent with `ContentSample`) or stamp the two set-sites through the validator. |

**Verified clean (NOT findings):** the analyze-resilience fixes
(`[BUG analyze-timeout-no-incontainer-kill]`,
`[GOAL stimulus-early-giveup-nonresponsive-target]`, both RESOLVED below —
typed exceptions, argv discipline, observability, taxonomy parity all hold);
W23 same-boot wedged-job reaper + migration `c3f8a1d7e9b2`; the PEM
multiline-redaction linear scanner (`evidence.py:169-219`); the offline-VSIX
pre-read size gate (`offline.py:172-194`); the extension-host log-parse ReDoS
bounds (`{1,256}` + 16 KiB per-line cap); and the Makefile env auto-create
(create-if-missing, no overwrite) + Windows/WSL guards.

**Record-only (benign, no action):** `phase.json` `active_stream` still names the
closed `operator-console-honesty` stream — the documented named-stream close-out
convention (the next stream's H0 repoints it). The compose-isolation cap test's
`NET_RAW`/`SYS_PTRACE` assertion removal was a **tightening** to exact-5-cap
matching (W21 `5dc18aa` → ES-0 `70e4364`), not a weakening.

## Closed/Archived Groups

Full close evidence in the latest archive snapshot for:

- W8/W9/W10/W11/W12 closure work.
- Closed W12 companion items: attribution precursor tests, attribution
  facade cleanups, marketplace installer-tail redaction, generated UI
  contract coverage, Settings copy drift, security-settings ownership,
  API/UI Docker digest pins, W12 close-out gates.
- Repo hygiene items already closed:
  `[CLEANUP repo-tracked-scratch-files]`, `[CLEANUP tests-scanner-rename]`,
  `[CLEANUP agent-context-phase-snapshot-stale]`,
  `[CLEANUP httpx-runtime-dependency-metadata]`,
  `[FOLLOWUP scripts-seed-test-rewrite]`, `[FOLLOWUP triggers-private-helper-import]`.

## How To Pull An Item Back

1. Search by stable ID in this file and the latest full archive snapshot.
2. Confirm code/tests still match the recorded premise.
3. Add or update tests first when the item describes a regression risk.
4. Close by preserving the stable ID and adding the landing date/commit.
