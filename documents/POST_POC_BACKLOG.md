# Post-PoC Backlog

`Last Updated: 2026-05-21 (W19 active — W19-0 doc-reconcile this commit on the week19 branch (per user direction 2026-05-21; W11-W18 paterni preserved); sub-iter slate W19-0..W19-6 reserved by §17 plan, stable IDs W19-1..W19-5 promoted from W19-W22 Roadmap Acceptance Bar (planning) to new W19 Pull-Forward Acceptance Bar (in flight) at W19-0 open. Driving signal: Codex live-run validation 2026-05-21 of ms-python.python @ 992ad028f3df reports automation_health.status=degraded + run_quality=low while static W18 final bar (1907/201/220) remains green. W19 closes Hat-1 (executor muhasebe bug → unaccounted_dropout) + Hat-2 (harness verification gap → declared ≠ verified); Hat-3 (coverage matrix promotion) deferred to W20-W22. §17 W19 plan source + §18-§20 W20-W22 multi-iter roadmap (split at W19-0 from the original §17-§20 combined header). W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; final W18 bar tests/architecture/ 201 / make test-security 220 / full suite 1907 passed, 9 skipped, 8 deselected. W18 Pull-Forward CLOSED (frozen audit trail): ADR 0012 Option A1 heartbeat thread relocation (W18-1, acf6cc9 + 73d8a5c followup); heartbeat refactor implementation step-1 reset off worker thread (W18-2, a9bffb1 + 78ed7cc + b5b64b6 + 306d744 with pre-commit install — W17-3/W17-4 DESIGN-NEEDED carry-over closed); lifecycle harness extension tests parallel reset / idempotency / reset-during-finalize (W18-3, 92b310d + 32d9905); W18-4 close-out hygiene (3f4f95a); W18-4-followup invariant pins (e1043e5, 4 W18-2 invariant pins + 2 pre-existing doc drift fixes). W18 candidate intake (2026-05-19): [GOAL container-hardening-baseline] (scheduled W21-4 stretch) + [GOAL sandbox-evasion-defense-mvp] (scheduled W22-4 ADR draft + W22-5 canary fixture). W18 frozen tracker: documents/active-work/W18-heartbeat-refactor.md; W19 active tracker: documents/active-work/W19-live-run-root-cause.md; multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md. W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. W17 Pull-Forward CLOSED: attribution-count-parity (W17-1, 8c26d02); lifecycle harness scaffold (W17-2, ff98235); heartbeat-sandbox-reset-off-thread + heartbeat-refactor SCOPE-REDUCED (W17-3 + W17-4 c4c0646 — closed via W18-1 ADR + W18-2 implementation); postgres-version-fact-drift (W17-5, 394d40d); W17-6 close-out hygiene (21f7c68). W16 Pull-Forward CLOSED: scenario-accountant-conservation-split (W16-1, 01f910a); analysis-job-worker-entry-crud-ownership (W16-2, 9d6d110); report-finalize-top-level-field-sync-drift null-leakage half (W16-3, fa430f2); health-reconciliation-responsibility-split (W16-4, 304b99f); simulation-progress-cancel scope reduction (W16-5 doc-only e21a05c); hygiene splits + Alembic fresh-DB fixture (W16-6, d40bb01); close-out hygiene (W16-7, 8bf3c6b) + post-PR unaccounted_dropout surface pin (78f080e). W15 closed via PR #22 MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d)`

Open deferred work after the W0-W7 PoC acceptance bar. **Slim canonical** —
verbose closure rationales, evidence paragraphs, and per-iter Note columns
are frozen in dated snapshots. Each closed item below is one line with
stable ID + landing commit; full context in the snapshot.

- latest full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-14.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-14.md)
- previous full snapshot:
  [`archive/backlog/POST_POC_BACKLOG_full_2026-05-11.md`](archive/backlog/POST_POC_BACKLOG_full_2026-05-11.md)

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
user direction; W11-W17 paterni preserved); close-out PR
`week18 -> main` not yet opened (branch is pushed). All rows below
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

W19 active `2026-05-21` on the `week19` branch (per user direction;
W11-W18 paterni preserved). Sub-iter slate W19-0..W19-6 reserved by
§17 plan; stable IDs W19-1..W19-5 promoted from W19-W22 Roadmap
Acceptance Bar (planning, now W20-W22) to this in-flight Pull-Forward
table at W19-0 open. Active tracker:
[`active-work/W19-live-run-root-cause.md`](active-work/W19-live-run-root-cause.md).

| Iter | Stable ID(s) | Status |
|---|---|---|
| W19-0 | doc-reconcile — `week19` branch + 8-doc canonical preamble refresh + new W19 active-work tracker + §17 W19 plan header doc-open + §17-§20 combined header split into §17 W19 active + §18-§20 W20-W22 planning + README phase-pointer arch gate transition W18→W19 + new W18 close-out fact gate `test_readme_phase_pointer_mentions_w18_closeout_merge` + baseline live-run smoke artefakt | **closed `2026-05-21`** via this commit |
| W19-1 | `[BUG scenario-unaccounted-dropout-regression-fixture]` — Live-run dropout regression fixture; new file `tests/executor/test_scenario_accountant_dropout_regression.py`; parametrize on `debug_session` + `refactor_workflow` + aggregate gate; landed RED with `@pytest.mark.xfail(strict=True)` at W19-1 primary; xfail markers removed + whitelist narrowed to `frozenset({"covered_via_layered_attempts"})` at W19-2 primary | **closed `2026-05-25`** via primary `6a21cf3` + self-stamp `fd02ca4` |
| W19-2 | `[BUG scenario-unaccounted-dropout-debug-refactor]` — Dropout emit-site fix (Hat-1; W16-1 paterni); ONE-PATH verdict (no mini-ADR); upstream emit-site landed in `executor/flows/playwright/stimulus/passes.py` covered-only branch — new `covered_via_layered_attempts` reason_code; accountant fallback `scenario_accountant.py:392-438` preserved as son-mil koruyucu; +2 W16-1-mirror synthetic unit tests at `tests/security/test_scenario_dropout_repro.py`; W19-1 fixture initially regenerated SYNTHESIZED then re-anchored to live-lifted at W19-2-followup-2 (`c2bf28ca9506` / sha256 `e9e60b2e42...`); +1 `_meta.source_sha256` canonical-hex format gate; **live Hat-1 GREEN gate SATISFIED `2026-05-25 22:23`** (`unaccounted_dropout` count = 0 in live JSON, both scenarios classified `covered_via_layered_attempts`, 16 of 16 key fields byte-identical with pre-fix anchor save the W19-2 reason_code) | **closed `2026-05-25`** via primary `89b64da` + self-stamp `d9c6262` + live re-anchor `<W19-2-followup-2-SHA>` |
| W19-3 | `[GOAL harness-verification-contract-event-level]` (new) — HARD GATE for W19-4/W19-5; new field `confirmation_source: Literal["harness_nonce", "log_record", "none"]` on `EventAttemptRecord` with default `"none"` for back-compat; 30-dk schema impact survey + Pydantic contract + UI adapter + contract round-trip + new test `tests/executor/test_automation_health_reasons.py` | pending |
| W19-4 | `[FOLLOWUP harness-verification-debug-events]` (new) — `onDebug*` family nonce confirmation generation in `executor/flows/harness_extension/*`; emit pipeline stamps `confirmation_source="harness_nonce"` | pending |
| W19-5 | `[FOLLOWUP harness-verification-terminal-and-lm-tool]` (new) — `onTerminalShellIntegration` + `onLanguageModelTool:*` local-only confirmation marker `confirmation_source="log_record"`; events where confirmation unattainable → `"none"` + explicit `blocked`/`unsupported` reason | pending |
| W19-6 | close-out hygiene + 8-doc canonical preamble refresh + §17 W19 self-stamp post-final-bar + W19 tracker freeze + PR `week19 -> main`; W18-4 paterni `3f4f95a` | pending |

W19 acceptance (live-run-driven; see §17.4 in
[`REFACTOR_OPTIMIZATION.md`](REFACTOR_OPTIMIZATION.md) for full
checklist): `unaccounted_dropout == 0` (must-pass);
`harness_verification_unconfirmed_present` reason drops
(must-pass); `run_quality: low → medium` (expected);
`verification_gap_present` drops (stretch);
`automation_health.status: degraded` OK (W20 closes
`official_unresolved_present`). Final W19-0 bar:
`tests/architecture/` **202 passed** (W18 final 201 + W19-0 +1 new
W18 close-out fact gate); `make test-security` **220 passed**
(unchanged); full suite **1908 passed, 9 skipped, 8 deselected**
(W18 final 1907 + W19-0 +1).

## W20-W22 Roadmap Acceptance Bar (planning)

Multi-iter roadmap planning landed `2026-05-21` per user direction.
Driving signal: Codex live-run validation of `ms-python.python` @
`992ad028f3df` (2026-05-21 10:10) → `automation_health.status=degraded`,
`run_quality=low`. Static W18 final bar (1907/201/220) remains 🟢;
runtime health is the W19-W22 target (W19 closes Hat-1 + Hat-2 in
flight per W19 Pull-Forward Acceptance Bar above; W20-W22 close
Hat-3 coverage matrix promotion per planning table below).

Plan source-of-truth: [`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md). Full sub-iter scope, acceptance gates, ADR paths, and critical files there. Plan went through 3 review rounds (Codex live-run + GPT × 2).

Stable IDs `W20-0..W22-7` are reserved and assigned at first pull per W11-W18 precedent. Aşağıdaki satırlar **planned**, henüz açılmadı:

| Iter | Planned Stable ID(s) | Theme |
|---|---|---|
| W20-0 | `[RESEARCH activation-event-spec-crosswalk]` (new) | Activation event spec ↔ registry ↔ manifest corpus crosswalk |
| W20-1 | `[GOAL taxonomy-scm-official-promotion]` (new) | `scm` official-track `missing → covered` |
| W20-2 | `[GOAL taxonomy-settings-official-promotion]` (new) | `settings` official-track `missing → covered` |
| W20-3 | `[GOAL coverage-matrix-contract-tests]` (new) | Coverage matrix invariant tests |
| W20-4 | `[DESIGN taxonomy-comments-testing-readiness]` (new) | W21 implementation şablonu (doc-only) |
| W21-1 | `[GOAL taxonomy-testing-coverage]` (new) | `testing` her iki track → covered |
| W21-2 | `[GOAL taxonomy-comments-coverage]` (new) | `comments` her iki track → covered |
| W21-3 | `[GOAL taxonomy-workspace-trust-coverage]` (new) | `workspace_trust` her iki track → covered (scope-explode → W22 defer) |
| W21-4 | `[GOAL container-hardening-baseline]` (existing W18 candidate) — **stretch in W21**, fallback W22+ | Container hardening + ADR `documents/adrs/0013-container-isolation-baseline.md` |
| W22-1 | `[GOAL taxonomy-chat-policy-adr]` (new) | Chat policy ADR `documents/adrs/0014-chat-and-language-model-tool-policy.md` |
| W22-2 | `[GOAL taxonomy-chat-coverage]` (new) | `chat` her iki track → covered (ADR Accepted sonra) |
| W22-3 | `[FOLLOWUP attribution-count-parity-process-events]` + `[FOLLOWUP attribution-count-parity-output-channel]` (new) | Attribution depth ProcessEvent + OutputChannelAppendLine |
| W22-4 | `[GOAL sandbox-evasion-defense-mvp]` (existing W18 candidate) — ADR draft only | Sandbox-evasion defense ADR `documents/adrs/0015-...` |
| W22-5 | `[GOAL sandbox-evasion-canary-fixture]` (new) | `tests/security/test_sandbox_evasion_canary.py` |
| W22-6 | `[GOAL activation-event-spec-gap-followup]` (new) | W20-0 crosswalk gerçek gap çıkardıysa implement |

**Plan motivation reference**:

- Live `ms-python.python` rapor: `output/activation_report_ms-python.python-2026.5.2026052001-992ad028f3df.json`
- `CAPABILITY_TAXONOMY` source: [`packages/analysis_planner/capabilities.py:8-27`](../packages/analysis_planner/capabilities.py)
- `OFFICIAL_EVENT_REGISTRY` count pin (29): [`tests/platform/contracts/test_registry_split_regression.py:101`](../tests/platform/contracts/test_registry_split_regression.py)
- Status enum (`healthy/degraded/inconclusive`): [`executor/flows/playwright/health/summary.py:260,378`](../executor/flows/playwright/health/summary.py)

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
- `[CLEANUP rule-registry-side-effect-loader]` — `registry.py` carries
  `_REGISTRY` global + `importlib` side-effect loader + `_BUILTINS_LOADED`
  flag for six builtin rules; a flat `RULES` tuple would suffice at current
  cardinality. Earns its weight only when ADR 0003 deferred rules
  (A5/A7) land. W15+ hygiene.

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
