# REFACTOR_OPTIMIZATION

`Last Updated: 2026-05-26 (Active phase: W20 — W20-0 doc-reconcile in-flight via this commit — open week20 branch (per user direction; W11-W19 paterni preserved) + new active-work tracker for W20 documents/active-work/W20-coverage-promotion-easy-wins.md + §18 W20 plan header doc-open in REFACTOR_OPTIMIZATION.md split from the combined §18-§20 header (W19-0 paterni §17 split from §17-§20) + W20 Pull-Forward Acceptance Bar promoted in POST_POC_BACKLOG.md (from W20-W22 Roadmap Acceptance Bar now W21-W22 Roadmap Acceptance Bar planning) + 9-doc canonical preamble refresh + README phase-pointer arch gate transition W19→W20 (test_readme_phase_pointer.py tracks_active_w20_status + new test_readme_phase_pointer_mentions_w19_closeout_merge pinning PR #28 / week19 -> main / c879603 mirroring W18-0 / W19-0 transition paterni); baseline live-run on ms-python.python pending user go (pre-approved baseline + final per AskUserQuestion 2026-05-26). W20 driving signal (same as W19): Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities = [scm, settings, chat, comments, testing, workspace_trust]; W20 easy-wins tier closes scm + settings (heuristic-covered at capabilities.py:36,38; _OFFICIAL_CAPABILITY_SUPPORT missing at :88,90 — single-character flips at W20-1 + W20-2); W21 mid tier; W22 hard tier + sandbox evasion ADR. §18 W20 plan source (active) + §19-§20 W21-W22 planning roadmap (split at W20-0 from W19-0 era §18-§20 combined header). W20-0..W20-5 sub-iter slate: W20-0 doc-reconcile (this commit) + W20-1 [GOAL taxonomy-scm-official-promotion] + W20-2 [GOAL taxonomy-settings-official-promotion] + W20-3 [GOAL coverage-matrix-contract-tests] + W20-4 [DESIGN taxonomy-comments-testing-readiness] + W20-5 close-out hygiene + PR week20 -> main PENDING USER APPROVAL. W19 closed and merged — Hat-1 closed + live-verified via W19-2-followup-2 d5de9ca; Hat-2 HARD GATE W19-3 closed via primary d2e83e7 + self-stamp 39121e4 + W19-3-followup-2 8-doc preamble refresh 9b56e94; W19-4 closed via 7d44b0e + W19-X live-verification close-out via 8b7b7f6 (W19-X primary) + a3e634f (W19-X self-stamp) — closes Bug A planner routing / Bug B marker channel destination / Bug C HMAC secret reactivation race; +15 new behavioral tests; live anchor 8247e05ec9ef.json: 2/2 onDebug* stamped; W19-5 closed via e537ebd + 4fd6ed6; W19-6 close-out hygiene via f17b4b1 + cd82153; W19-6-followup-2 pre-merge hygiene (this commit) closes 6 test gaps (+20 parametrized tests) + corrects stale W19 preamble drift across the 9-doc canonical set + freezes W19 tracker per W17/W18 paterni; final W19 test bar 1995/9/8 (tests/architecture/ 204 / make test-security 220 / full suite 1995 passed) on the week19 branch (per user direction 2026-05-21; W11-W18 paterni preserved); W19-0..W19-6 + W19-X closed on the week19 branch; merged to main via PR #28 2026-05-26 via c879603; live smoke pending; stable IDs W19-1..W19-5 closed at POST_POC_BACKLOG.md W19 Pull-Forward Acceptance Bar, assigned at first pull per W11-W18 precedent. Driving signal: Codex live-run validation 2026-05-21 of ms-python.python @ 992ad028f3df reports automation_health.status=degraded + run_quality=low while W19-2 live re-anchor now satisfies unaccounted_dropout == 0 and static W18 final bar (1907/201/220) remains green. W19 Hat-1 closed + live-verified (executor muhasebe bug → unaccounted_dropout); Hat-2 W19-3 schema landing + W19-4 onDebug* producer + consumer wire closed; W19-5 closed via primary e537ebd + self-stamp 4fd6ed6 (onTerminal+onLM log_record stamp at reconciliation.py:347-365 sibling elif to W19-4 onDebug arm); Hat-3 (coverage matrix promotion) deferred to W20-W22 per multi-iter roadmap. §17 W19 plan source + §18-§20 W20-W22 multi-iter roadmap (split at W19-0 open from the previous §17-§20 combined header). W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79; final W18 bar tests/architecture/ 201 passed; make test-security 220 passed; full suite 1907 passed, 9 skipped, 8 deselected. Sub-iter W18 audit trail (frozen, all closed): W18-0 doc-reconcile (89d0c9b); W18-1 ADR documents/adrs/0012-heartbeat-thread-relocation.md Option A1 (acf6cc9 + 73d8a5c followup); W18-2 heartbeat refactor implementation — step-1 reset off worker thread via dedicated coordinator (a9bffb1 + 78ed7cc + b5b64b6 + 306d744); W18-3 lifecycle harness extension tests — parallel reset / idempotency / reset-during-finalize (92b310d + 32d9905); W18-4 close-out hygiene (3f4f95a); W18-4-followup (e1043e5) — 4 W18-2 invariant pins + 2 pre-existing doc drift fixes. W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. §15 W17 plan source — W17-0..W17-7 sub-iter slate complete (frozen); §14 W16 plan source — W16-0..W16-7 sub-iter slate fully delivered (frozen). W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W13 closed via PR #20 week13 -> main MERGED 2026-05-13 via 772deb3. W18 frozen tracker: active-work/W18-heartbeat-refactor.md; W19 frozen tracker: active-work/W19-live-run-root-cause.md (frozen at W19-6-followup-2 per W17/W18 paterni); multi-iter roadmap source-of-truth: active-work/W18-W22-roadmap.md)`

W0-W14 plan document: stabilization + security + post-PoC external-review
integration + W14 acceptance + observability continuation. **Slim canonical**
— full historical content (per-iter rationale, sub-commit narratives, entry/
exit prose) is frozen under dated snapshots. Each closed iter below is one
row with stable ID + landing commit; full context in the snapshot.

- latest full snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-14.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-14.md)
- previous full snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-13.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-13.md)
- older snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-11.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-11.md)

## Anchor Map

- §10 / §10.7 → W0-W7 PoC window and acceptance bar (closed).
- §11 → W8-W13 external-review integration window (closed).
- §11.5 → W8 tracker pointer.
- §11.6 - §11.10 → W9-W13 weekly closure summaries.
- §11.11 - §11.14 → cross-ref, rejected, lane, and exit summaries.
- §12 → W14 Codex M-class Acceptance + Observability — **closed
  `2026-05-14`; PR #21 `week14 -> main` merged via `4e03c8d`.**
  Frozen tracker:
  [`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md).
- §13 → W15 Codex U-class Close-Out + UI Bounds + Posture — **closed
  `2026-05-17`; PR #22 `week15 -> main` merged `2026-05-18` via
  `6161472`.** Frozen tracker:
  [`active-work/W15-codex-uclass-bounds-posture.md`](active-work/W15-codex-uclass-bounds-posture.md).
- §14 → W16 Carry-Over Closeout + Audit Findings + Production
  Regression — **closed `2026-05-18`; PR #23 `week16 -> main`
  merged via `1b6d43f` on `2026-05-18`.** Frozen tracker:
  [`active-work/W16-regression-and-audit-closeout.md`](active-work/W16-regression-and-audit-closeout.md).
- §15 → W17 Carry-Over Closeout + Lifecycle Harness Yatırımı +
  Hygiene Sweep — **closed `2026-05-18`; PR #25 `week17 -> main`
  merged via `bff565d` on `2026-05-18`.** Frozen tracker:
  [`active-work/W17-carryover-and-lifecycle-harness.md`](active-work/W17-carryover-and-lifecycle-harness.md).
- §16 → W18 Heartbeat Refactor — **closed `2026-05-21`; PR #26
  `week18 -> main` merged via `9874e79` on `2026-05-21`;
  W18-0..W18-4 sub-iter slate fully delivered + W18-4-followup
  post-merge audit** (W18-0 `89d0c9b` + W18-1 ADR 0012 Option A1
  accepted `acf6cc9` + `73d8a5c` followup doc-truth + W18-2
  implementation `a9bffb1` + `78ed7cc` ADR self-stamp + `b5b64b6`
  ruff-format + `306d744` full-repo lint sweep + `pre-commit install`
  + W18-3 lifecycle harness extension tests `92b310d` + `32d9905`
  self-stamp + W18-4 close-out hygiene `3f4f95a` + W18-4-followup
  `e1043e5` 4 invariant pins + 2 doc drift fixes); on the `week18`
  branch (per user direction `2026-05-21`; W11-W17 paterni
  preserved). Frozen tracker:
  [`active-work/W18-heartbeat-refactor.md`](active-work/W18-heartbeat-refactor.md);
  ADR: [`adrs/0012-heartbeat-thread-relocation.md`](adrs/0012-heartbeat-thread-relocation.md).
- §17 → W19 Live-Run Kök Neden: Dropout + Harness Verification —
  **closed synthetically `2026-05-26`; PR #28 `week19 -> main`
  MERGED `2026-05-26` via `c879603`** on the `week19` branch
  (W11-W18 paterni preserved); W19-0..W19-6 + W19-X sub-iter slate
  fully delivered (Hat-1 closed + live-verified; Hat-2 fully closed
  synthetically). Frozen tracker:
  [`active-work/W19-live-run-root-cause.md`](active-work/W19-live-run-root-cause.md)
  (frozen at W19-6-followup-2 per W17/W18 paterni).
- §18 → W20 Coverage Promotion Round 1: Easy Wins —
  **W20-0 in-flight `2026-05-26`** on the `week20` branch (W11-W19
  paterni preserved). W20-0 doc-reconcile landed this commit; sub-iter
  slate W20-0..W20-5 reserved by §18 plan; stable IDs W20-1..W20-5
  reserved at `POST_POC_BACKLOG.md` W20 Pull-Forward Acceptance Bar
  (promoted from W20-W22 Roadmap Acceptance Bar at W20-0 open). Active
  tracker:
  [`active-work/W20-coverage-promotion-easy-wins.md`](active-work/W20-coverage-promotion-easy-wins.md).
- §19-§20 → W21-W22 Multi-iter Capability + Coverage Promotion +
  Sandbox Evasion + Chat Policy Roadmap (planning state, authored
  `2026-05-21`; split from the original §18-§20 combined header at
  W20-0 open when W20 promoted to its own §18 active block — same
  paterni as the W19-0 split of §17-§20 into §17 + §18-§20).
  Multi-iter roadmap source-of-truth:
  [`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md).

## §10 — W0-W7 PoC Stabilization Window (closed 2026-04-23)

PoC window closed `2026-04-23` with §10.7 acceptance bar 11/11 green.
Detailed W0-W7 plan history lives in the archive.

### §10.7 — PoC acceptance checklist (W7 sonu, closed 2026-04-23)

- [x] Legacy top-level business directories removed.
- [x] `packages/` import-graph enforcement exists.
- [x] VS Code version pinned; harness extension checksum verified.
- [x] Executor control boundary exists.
- [x] A1/A2/A4/A6 canaries and rules landed; A3 landed in the W7 buffer.
- [x] Benign baseline, scenario-dropout honesty, verdict rollup, UI finding
  display, `make test-security`, and demo acceptance were green.

## §11 — W8-W13 External Review Integration Window (closed 2026-05-13)

§11 integrates post-PoC external reviews without moving the W0-W7 PoC
acceptance bar. Review snapshots live under `archive/reviews/`.

### §11.1 — Entry/Exit

W8 entry met `2026-04-27`; W8 closed `2026-04-29`; W9 closed `2026-05-04`
via PR #9; W10 closed `2026-05-04` via PR #11; W11 closed `2026-05-05`
via PR #14; W12 closed `2026-05-10` via PR #18; W13 closed `2026-05-13`
via PR #20 (`772deb3`).

### §11.2 — Haftalık dağılım (W8-W13)

| Hafta | Etiket | Status |
|---|---|---|
| W8 | Security hardening | closed `2026-04-29`; W8-8 deferred |
| W9 | Executor/detection boundary | closed `2026-05-04`; ADR 0008 accepted |
| W10 | Contract hygiene + planner cleanup | closed `2026-05-04`; PR #11 |
| W11 | Monitor lifecycle split | closed `2026-05-05`; PR #14 |
| W12 | Executor subpackaging + attribution cleanup | closed `2026-05-10`; PR #18 |
| W13 | Test expansion + observability | closed `2026-05-13`; PR #20 |

### §11.3 — Haftalar arası bağımlılıklar

- W10 depends on W9 package-mode import discipline.
- W11 depends on W10 typed contracts.
- W12 depends on W11 monitor lifecycle split.
- W13 locks in W8-W12 regression coverage and pulls audit follow-ups.

### §11.4 — Non-goals

Queue-backed distributed workers, multi-tenant accounts, broad run-history
infrastructure, and speculative UI/product expansion remain outside W8-W13
unless pulled from `POST_POC_BACKLOG.md` with a stable ID.

### §11.5 — W8 Güvenlik Sıkılaştırma

Moved to [`active-work/W8-security.md`](active-work/W8-security.md). W8 is
closed; retained for W8-1..W8-9 stable-ID references.

### §11.6-§11.9 — W9..W12 Closures

W9 (`2026-05-04`, PR #9): ADR 0008 container package-mode invocation
accepted; dual-import fallback + runtime `sys.path.insert` debt removed.
W10 (`2026-05-04`, PR #11): `schema_version`, planner registry cleanup,
typed health/coverage models, executor action enum, W10 contract gates.
W11 (`2026-05-05`, PR #14): monitor lifecycle split (W11-1..W11-8).
W12 (`2026-05-10`, PR #18, `33a0852`): executor subpackaging,
attribution facade cleanup, `raw_context` discriminated union typing,
entrypoint dispatch extraction, runtime_capture split + body-preview
redaction gate, API/UI Dockerfile digest pins, Codex CRITICAL
subprocess-output redaction fix. Final close evidence:
[`archive/active-work/W12-close-acceptance-completed-2026-05-10.md`](archive/active-work/W12-close-acceptance-completed-2026-05-10.md).

### §11.10 — W13 Test Expansion + Observability (closed 2026-05-13, PR #20)

Tracker: [`active-work/W13-test-expansion-observability.md`](active-work/W13-test-expansion-observability.md).

| Scope | Status |
|---|---|
| Acceptance bar | W13-1..W13-7 closed H3/H4/H5/H6/M1/M9 from 2026-05-10 Codex Cloud audit |
| §11.10 GOAL pulls | W13-8 benign silence 3→5, W13-9 `.env` gitignore, W13-10 singleton-lock recovery closed |
| Close-gate | W13-11/W13-12/W13-13 (HMAC race, fail-closed handshake, worker-start CAS) closed in-window |
| Final bar | `make test-local` 1551 passed / 10 skipped / 8 deselected; `make test-security` 215 passed; `tests/architecture/` 117 passed |

Remaining §11.10 GOAL umbrellas iterated into W14. Close-gate post-pull
behavioral pins (3a89c09, 9c80f25, 0d3e343, 826f91c, 26a2025) retained
audit-trail integrity.

### §11.11-§11.14 — Cross-Ref / Rejected / Lanes / Exit

Cross-ref by stable ID via `POST_POC_BACKLOG.md`. Current WONT-FIX
audit item: M14a (workspace ownership by design). Lane routing via
`AGENT_CONTEXT.md`. W13 exit criteria met `2026-05-13` (H3/M1/M9
closed + close-gate W13-11/12/13 GREEN + close-out PR #20 merged).

## §12 — W14 Codex M-class Acceptance + Observability (closed 2026-05-14)

§12 opened with the `week14` branch cut from `main` at `69251f1` on
`2026-05-13` (close-out PR #20 merged the same day via `772deb3`) and
closed when PR #21 `week14 -> main` merged on `2026-05-14` via
`4e03c8d`. Frozen tracker:
[`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md)
carries per-iter Per-Item Detail evidence (sub-commits, module
locations, test deltas, production validation).

| Iter | Status | Landing commit |
|---|---|---|
| W14-1 | BLOCKER → HIGH downgrade (stochastic-bound rationale) | `0c8bd02` |
| W14-2 | closed (M4-M7 + M11 input validation) | `bde17be` |
| W14-3 | closed (M13 + M14b + U4-U12 external surface) | `941250d` |
| W14-4 | closed (analysis-jobs-race + EvidenceEvent kind invariant) | `03b32bc` |
| W14-5 | closed (logger consolidation + run-ID stamping + executor runtime fingerprint; ADR 0010; M5 byproduct) | `dc79f61` + `9c095d2` + `db25d5f` |
| W14-6 | closed (regression lock-in umbrella: pragma ratchet + executor.control outbound gate + variable-indirect subprocess coverage + binary_paths migration) | `2adad43` + `b031803` + `e42a448` |
| W14-7 | closed post-slate (container-shipping regression + Python 3.10 UTC compat; +2 arch gate cases) | `df925f8` + `c11ebd8` |
| W14-8 | closed post-slate, preventive (AST gate forbidding Python 3.11+ API imports in container-shipped paths; per-import `# arch-allow: py311-api` pragma; +1 arch case) | `5638f82` |

Close-out hygiene pass (this PR): Ruff lint fixes (7 violations), UI
contract sync (`executor_fingerprint` TS field), markdown formatting,
doc truth-state alignment, slim canonical compression, +2 new
regression gates (`make markdownlint`, ADR code fence arch test).

### §12.0 — Neden ayrı §12

§11 W8-W13 external-review integration penceresini sınırlar (W12 close
`2026-05-10`, W13 acceptance bar `2026-05-11`). W14 yeni bir tema:
Codex M-class acceptance-bar pull-forward devamı + §11.10 GOAL
umbrella'larının ertelenen kısmı. §12 ayrı tutuluyor ki §11 audit
trail'i donmuş kalsın.

### §12.1-§12.2 — Entry + Sub-iter Distribution

W14 entry triggered by W13 close-out PR #20 merge. Sub-iter sequencing
rationale (W14-1 önce — BLOCKER scope etkisi belirsiz; sonra düşük-risk
M-class W14-2, redaction zinciri W14-3, correctness/concurrency W14-4,
altyapı GOAL pulls W14-5 → W14-6 sırasıyla — W14-5 logger consolidation
W14-6 gate'lerinde test enstrümantasyonuna girdi olur) full archive
snapshot'ta. Stable ID → iter eşlemesi `POST_POC_BACKLOG.md`'de W14
Pull-Forward tablosunda.

### §12.3 — Non-goals (W14)

W15+'a düşen kalemler stable ID'leri `POST_POC_BACKLOG.md` altında açık
kalır:

- Codex M-class: M10, M12, U1-U3, U6, U8, I2, I4.
- Posture decision: `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]`.
- Watching items: `planner-selection-readability-audit`,
  `attribution-links-build-evidence-bundle-density`,
  `execute-attempt-rebloat-watch`, `dispatch-execution-rebloat-watch`.
- UI follow-up'ları: `ui-raw-context-discriminator-parity`,
  `vsix-integrity-in-activation-report`.
- Refactor: `scenario-accountant-conservation-split` (W14-1 sonrası ayrı pull).
- Automation/verification: `[FOLLOWUP codex-automation-6]`,
  `[FOLLOWUP capability-verification-gap]`.

### §12.4 — Exit Criteria (W14-End)

W14 kapanır şu koşullar sağlandığında:

- W14-1 BLOCKER ya kapanır ya da HIGH'a indirilip dokümante edilir. **DONE** (`0c8bd02`).
- W14-2..W14-6 kapanır ya da deferral rasyoneli ile W15'e taşınır. **DONE**.
- W14 tracker final close evidence + current test counts tutar. **DONE**.
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, `active-work/README.md`,
  ve ilgili lane docs aynı active/closed state'i gösterir. **DONE** (close-out hygiene PR).
- Slim canonicals kısa kalır; verbose evidence önce arşivlenir. **DONE** (snapshot `2026-05-14`).
- `week14 → main` close-out PR W12 PR #18 / W13 close-out cut-off pattern'ini izler. **DONE** (PR #21 merged `2026-05-14` via `4e03c8d`).

## §13 — W15 Codex U-class Close-Out + UI Bounds + Posture (closed 2026-05-17, merged 2026-05-18 via PR #22)

§13 opened with the `week15` branch cut from `main` HEAD `7cc2921` on
`2026-05-14` (W14 close-out PR #21 merged at `4e03c8d`; W15 base
includes the `7cc2921` scope-skeleton commit) and closed when PR #22
`week15 -> main` merged on `2026-05-18` via `6161472`. Frozen tracker:
[`active-work/W15-codex-uclass-bounds-posture.md`](active-work/W15-codex-uclass-bounds-posture.md)
carries per-iter scope locks, candidate items, and Per-Item Detail
evidence (sub-commits, module locations, test deltas). Final status
`2026-05-17`: W15-1..W15-7 closed
(M10/M12/U8/U1/U2/U3/U6/I2/I4/U10/U11 + W15-7 regression lock-in);
W15-1 post-slate typing hotfix landed. W15-6 closed `2026-05-17` via
`be52520` (ADR 0011 Accepted and implemented — Option A:
unauthenticated catalog endpoints posture pinned under
single-host + loopback default + opt-in-LAN preconditions;
new `tests/architecture/test_catalog_endpoint_posture.py`
gate; `tests/architecture/` 188 → 191 passing). W15-5 closed
`2026-05-17` via `43d6438` (quick fixes bundle: UI `/health`
proxy I2 + lifecycle `for <id>` regex I4; `+0` arch gates per
W14-6 "extend, do not duplicate"). Mid-iter hygiene pass `2026-05-16`
pulled forward the W15-7 doc-preamble subset — seven canonical doc
preambles refreshed and
`tests/architecture/test_doc_preamble_consistency.py` added; three
new audit findings appended to `POST_POC_BACKLOG.md`. **W15-7 finalized
`2026-05-17`** — compose image SHA pin (`54e7a93`) + test extension
(`7ebbbfb`; `tests/architecture/` 196 → 198) + GH action trivy pin
(`452f1a1`; `aquasecurity/trivy-action@v0.36.0`) + final canonical
preamble flip via this docs commit. ADR 0002 NOT amended; no new
architecture gate per W14-6 "extend, do not duplicate" — compose
gate is an extension of the existing Dockerfile FROM-pin invariant.

| Iter | Status | Landing commit |
|---|---|---|
| W15-1 | **closed `2026-05-14`** (sync analyze error taxonomy alignment — M10) | `c58c365` |
| W15-2 | **closed `2026-05-14`** (workspace symlink check order / orphan removal — M12; path b: fix) | `765cde7` |
| W15-3 | **closed `2026-05-15`** (`activationEvents` bounds + DB field-length Alembic migration — U8) | `3512a7c` |
| W15-4 | **closed `2026-05-16`** (UI bounds bundle: timeline / density strip / relations graph caps with truncation indicators — U1-U3 + U6; new `ui/src/lib/displayCaps.ts` helper; extracted `EventDensityStrip` from `ReportsPage`; 21 vitest cases; `+0` arch gates per UI-side cap policy. **W15-1 post-slate typing hotfix** `976dc96` landed in the same close-out window — `ANALYZE_*_ERROR_TYPES` annotation narrowed from `BaseException` to `Exception` after the W15-4 close-out `make typecheck` surfaced the mismatch at `workflows/marketplace/router.py:341`; W14-7 hotfix precedent.) | `89e13e3` (+ `976dc96`) |
| W15-5 | **closed `2026-05-17`** (quick fixes bundle: UI `/health` proxy I2 + lifecycle `for <id>` regex I4; additive `/api/health` route via new `appcore/api/health_router.py` (`prefix="/api"`) + UI `client.ts` `/health` → `/api/health` migration with legacy root `/health` preserved for external-monitoring back-compat; `_LIFECYCLE_MARKER_PATTERNS` two entries narrowed to enforce `<publisher>.<name>` shape with `\s+` anchor; +14 behavioral cases — 3 backend pytest + 2 UI vitest + 9 parser unit parametrize; `+0` arch gates per W14-6 "extend, do not duplicate" — no extendable gate; new gates deferred to W15-7 close-out hygiene) | `43d6438` |
| W15-6 | **closed `2026-05-17`** (ADR 0011 Accepted and implemented — Option A: catalog endpoints remain unauthenticated under three preconditions — single-host appliance scope ADR 0001, loopback bind default ADR 0007 §1, operator-side hardening for LAN exposure per `documents/runbooks/lan-exposure.md`; `workflows/extension_catalog/router.py` module docstring + router construction-site comment cite ADR 0011; new `tests/architecture/test_catalog_endpoint_posture.py` gate locks three AST invariants — docstring cite + no auth dependency + endpoint-count lock at 12; `tests/architecture/` 188 → 191 passing; ADR 0002 NOT amended) | `be52520` (Proposed at `e41722e`) |
| W15-7 | **closed `2026-05-17`** (regression lock-in umbrella: compose image SHA pin `54e7a93` — postgres:16-alpine + alpine/socat:1.8.0.3 manifest digest; test extension `7ebbbfb` — `test_dockerfile_digest_pin.py` compose `image:` scope, `tests/architecture/` 196 → 198; GH action trivy version pin `452f1a1` — `aquasecurity/trivy-action@v0.36.0`; doc preamble truth-state refresh via this docs commit; ADR 0002 NOT amended; no new architecture gate per W14-6 "extend, do not duplicate") | `54e7a93` (+ `7ebbbfb`, `452f1a1`) |

### §13.0 — Neden ayrı §13

§11 W8-W13 external-review integration penceresini sınırlar; §12 W14
Codex M-class acceptance + observability penceresini kapatır. §13 yeni
bir tema: Codex 2026-05-10 audit'inin geri kalan U-class + I-class +
tail M-class kalemlerini kapatır (audit kapanışı), bir architectural
posture decision (ADR 0011) verir, ve W14 close-out audit'inin
immediate hijyen finding'lerini regression lock-in altında bağlar.
§13 ayrı tutuluyor ki §12 audit trail'i (W14 close-out date'leri ve
SHA'leri) donmuş kalsın.

### §13.1-§13.2 — Entry + Sub-iter Distribution

W15 entry triggered by W14 close-out PR #21 merge (`4e03c8d`,
`2026-05-14`). Sub-iter sequencing rationale: W15-1 + W15-2 önce —
düşük blast radius, izole; sonra W15-3 (DB migration sequencing
standalone pull ister); sonra UI bundle W15-4; quick fixes bundle
W15-5; ADR-pending posture W15-6 (ADR önce, kod sonra); regression
lock-in umbrella W15-7 en son (W14-6 paterni). Stable ID → iter
eşlemesi `POST_POC_BACKLOG.md`'de W15 Pull-Forward tablosunda
(W15-1 pull'da açılır).

### §13.3 — Non-goals (W15)

W16+'a düşen kalemler stable ID'leri `POST_POC_BACKLOG.md` altında
açık kalır:

- `[FOLLOWUP scenario-accountant-conservation-split]` (W14-1 root-cause
  downgrade hâlâ geçerli; direct trigger yok, defer).
- `[FOLLOWUP report-finalize-top-level-field-sync-drift]` (production
  scan-driven investigation; izole pull olur, W15 temasıyla uyumsuz).
- `[CLEANUP rule-registry-side-effect-loader]` (ADR 0003 deferred rules
  A5/A7 landed olunca).
- `[CLEANUP test-import-graph-policy-dump-split]` (test dosyası
  okunabilirliği; W15 arc'ına yakışmıyor).
- `[FOLLOWUP codex-automation-6]`, `[FOLLOWUP capability-verification-gap]`
  (`NEEDS-DESIGN`; W16+ design pass'i gerek).
- `[FOLLOWUP simulation-progress-cancel]` alt-kalemleri (heartbeat refactor
  familyası; ayrı umbrella ister).
- Watching items: `planner-selection-readability-audit`,
  `attribution-links-build-evidence-bundle-density`,
  `execute-attempt-rebloat-watch`, `dispatch-execution-rebloat-watch`
  (LoC bütçesi aşılana kadar dokunma).
- `[FOLLOWUP ci-reintroduction]` (geniş GH Actions CI reintroduction;
  W15-7 yalnızca tek action pin'i ele alır).

### §13.4 — Exit Criteria (W15-End)

W15 kapanır şu koşullar sağlandığında:

- W15-1..W15-7 kapanır ya da deferral rasyoneli ile W16'ya taşınır.
- W15 tracker final close evidence + current test counts tutar
  (`tests/architecture/` 171 → hedef 174-175).
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, `active-work/README.md`,
  ve ilgili lane docs aynı active/closed state'i gösterir.
- W15-6 verirse: ADR 0011 (unauthenticated catalog endpoints posture)
  accepted + implemented date'i ile landed.
- W15-7 verirse: compose image refs + GH action ref digest/version
  pinned + 4 canonical preamble truth-state refresh.
- Slim canonicals kısa kalır; verbose evidence önce arşivlenir.
- `week15 → main` close-out PR W12 PR #18 / W13 PR #20 / W14 PR #21
  cut-off pattern'ini izler. **DONE** (PR #22 merged `2026-05-18` via
  `6161472`).
- Close-out hygiene pass (W14 paterni): Ruff lint, UI contract sync,
  markdown formatting, doc truth-state alignment, (varsa) yeni
  regression gate'ler. **DONE** (doc preamble truth-state refresh
  across 7 canonical docs + close-out lint hygiene via `7ff31d9` +
  ADR 0011 catalog endpoint posture gate + compose image SHA pin +
  GH action trivy version pin).

## §14 — W16 Carry-Over Closeout + Audit Findings + Production Regression (closed 2026-05-18, merged 2026-05-18 via PR #23)

§14 opened with the W15 close-out PR #22 `week15 -> main` merge on
`2026-05-18` via `6161472`. **Per user direction (2026-05-18) W16
lives on a `week16` branch (W11-W15 paterni restored via W16-0 doc
reconcile); close-out merges into `main` via a `week16 -> main` PR.**
W16-0..W16-7 sub-iter slate fully delivered on `2026-05-18`. Frozen
tracker:
[`active-work/W16-regression-and-audit-closeout.md`](active-work/W16-regression-and-audit-closeout.md)
carries per-iter scope locks, candidate items, and Per-Item Detail
evidence (sub-commits, module locations, test deltas). Final W16 bar:
`tests/architecture/` **199 passed** (W15 final 172, +27);
`make test-security` **220 passed** (W13 final 215, +5); full suite
**1893 passed, 9 skipped**.

| Iter | Status | Landing commit |
|---|---|---|
| W16-0 | **closed `2026-05-18`** (doc-direction reconcile — `week16` branch + `week16 -> main` close-out PR wording across canonical docs; W11-W15 paterni restored) | `0e243ca` (+ `d78aa9c` followup) |
| W16-1 | **closed `2026-05-18`** (scenario-accountant upstream emit-site fix — HIGH prod regression `2026-05-14`/`2026-05-15`; `dispatch_outcome_none` reason_code surface introduced + W14-1 root-cause closed at the dispatcher layer; +2 security tests green) | `01f910a` (+ `a4a050e`) |
| W16-2 | **closed `2026-05-18`** (analysis-job worker-entry CRUD ownership — W15 audit finding; `claim_queued_analysis_job_at_worker_entry` lifecycle facade extracted in `appcore/storage/crud_ops/analysis_jobs/lifecycle.py`; W13-13 CAS preserved byte-identically; AGENTS.md L57 compliance restored) | `9d6d110` (+ `c8b7811`) |
| W16-3 | **closed `2026-05-18`** (report-finalize null-leakage half — W14 production scan; 5 contract-seam additive fields + `build_report_data` coercions, 5 round-trip pins green. Attribution-count-parity half **SPLIT to W17+** as `[FOLLOWUP attribution-count-parity]`) | `fa430f2` (+ `e3d4a0c`) |
| W16-4 | **closed `2026-05-18`** (health-reconciliation responsibility split — W15 audit finding; `health/reconciliation.py` 682 LoC behavior-preservingly extracted into `health/security.py` + `health/handshake.py` + leaner `health/reconciliation.py`; W13-1 HMAC + W13-12 fail-closed gates green; +1 arch gate) | `304b99f` (+ `384d276`) |
| W16-5 | **scope reduced `2026-05-18`** (doc-only commit — `dedupe-step-progress-schemas` REJECTED on distinct-surface-roles rationale; `heartbeat-sandbox-reset-off-thread` + `heartbeat-refactor` DEFERRED to W17+ pending lifecycle harness; audit trail updated in `POST_POC_BACKLOG.md`) | `e21a05c` (doc-only) |
| W16-6 | **closed `2026-05-18`** (test hygiene + Alembic fixture bundle: `marketplace-router-test-suite-split` 2374 LoC → 5 endpoint-grouped files; `test-import-graph-policy-dump-split` 767 LoC → 4 thematic files; `w13-4-alembic-roundtrip-programmatic` skip removed + `fresh_alembic_engine` per-test throwaway Postgres DB fixture; ruff clean; 67/18 test IDs preserved via collect-only diff) | `d40bb01` |
| W16-7 | **closed `2026-05-18`** (canonical preamble refresh across 7 docs + W16 tracker freeze + final test bar recorded; PR #23 `week16 -> main` MERGED `2026-05-18` via `1b6d43f`; post-PR top-up `78f080e` added 3 `unaccounted_dropout` surface round-trip pins matching the W16 live-scan shape — security lane 217 → 220) | `8bf3c6b` (+ `78f080e` post-PR) |

### §14.0 — Neden ayrı §14

§13 W15 Codex U-class + posture penceresini kapatır (audit kapanışı,
ADR 0011, compose pin + GH action pin); §14 yeni bir tema: production
regression closeout (W14-1 carry-over) + W15 mid-iter audit
findings + W11/W14 carry-over closeouts (heartbeat family, alembic
round-trip, top-level field sync drift). §14 ayrı tutuluyor ki §13
audit trail'i (W15 sub-iter close date'leri ve commit'leri) donmuş
kalsın.

### §14.1-§14.2 — Entry + Sub-iter Distribution

W16 entry triggered by W15 close-out PR #22 merge (`6161472`,
`2026-05-18`). Sub-iter sequencing rationale: W16-1 önce —
production'da deterministik regression (`2026-05-14` + `2026-05-15`
observations), severity-leading. Sonra W16-2 (CRUD ownership;
concurrency-sensitive, W13-13 CAS pattern bağlantısı). W16-3 W16-1
ile coupling (finalize ordering temizliği, scenario dropout fix
sonrası doğal devam). W16-4 behavior-preserving extraction —
W13-1 HMAC gates regress etmemeli. W16-5 üç haftalık umbrella'yı
toplu kapatır. W16-6 hygiene splits + alembic fixture paralel
yapılabilir; runtime risk yok. W16-7 close-out hygiene W14/W15
paterni.

Stable ID → iter eşlemesi `POST_POC_BACKLOG.md`'de W16 Pull-Forward
tablosunda (W16-1 pull'da açılır).

Per user direction (2026-05-18) W16 lives on a `week16` branch
(W11-W15 paterni restored via W16-0 doc reconcile); sub-iter commits
land on `week16` and the W16 close-out is merged into `main` via a
`week16 -> main` PR.

### §14.3 — Non-goals (W16)

W17+'a düşen kalemler stable ID'leri `POST_POC_BACKLOG.md` altında
açık kalır:

- `[FOLLOWUP w11-8-companion-workflow-orm-bleed]` (DTO desen kararı
  önce ayrı bir ADR ister; W17+ design pass).
- `[CLEANUP rule-registry-side-effect-loader]` (ADR 0003 deferred
  rules A5/A7 landed olunca).
- `[FOLLOWUP codex-automation-6]`, `[FOLLOWUP capability-verification-gap]`
  (`NEEDS-DESIGN`; W17+).
- Watching items: `planner-selection-readability-audit`,
  `attribution-links-build-evidence-bundle-density`,
  `execute-attempt-rebloat-watch`, `dispatch-execution-rebloat-watch`
  (LoC bütçesi aşılana kadar dokunma).
- `[FOLLOWUP ci-reintroduction]` (geniş GH Actions CI reintroduction;
  W15-7 yalnızca tek action pin'i ele aldı, W16'da pull etmez).
- W15'te kapanan tüm kalemler (M10/M12/U1/U2/U3/U6/U8/I2/I4/U10/U11 +
  compose pin + trivy pin) — `POST_POC_BACKLOG.md`'de kapanış audit
  trail'i korunmuştur, yeniden pull değil.

### §14.4 — Exit Criteria (W16-End)

W16 kapanır şu koşullar sağlandığında:

- W16-1..W16-7 kapanır ya da deferral rasyoneli ile W17'ye taşınır.
- W16 tracker final close evidence + current test counts tutar
  (`tests/architecture/` hedef 198 → ~205+; W16-2 + W16-4 yeni
  arch gate eklerse).
- W16-1 production replay: `activation_report_*.json` fixture'ında
  `debug_session` + `refactor_workflow` scenario'ları deterministik
  drop etmiyor; `[FOLLOWUP scenario-accountant-conservation-split]`
  POST_POC_BACKLOG'da kapanış audit trail'i ile işaretlenir.
- W16-3 production replay: `target_extension_id`, `monitoring_*`,
  `scenarios_run`, `harness_handshake_required` top-level field'ler
  non-null populate edilir; finalize ordering drift kapanır.
- W16-4 davranış paritesi: `executor/flows/playwright/health/`
  paketinde security_gates + reconciliation responsibility split,
  W13-1 HMAC marker gates + fail-closed handshake davranışı
  regress etmez.
- W16-5 umbrella: `[FOLLOWUP simulation-progress-cancel]` family
  3 alt-kalemi kapanır; umbrella POST_POC_BACKLOG'da CLOSED
  işaretlenir.
- W16-6 hygiene: `tests/workflows/marketplace/test_router.py` →
  domain bazlı splits; `tests/architecture/test_import_graph.py`
  → tematik splits; `test_alembic_cancelling_migration.py`
  `pytest.skip` kalkar (fresh-DB fixture aktif).
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `active-work/README.md`, ve ilgili lane docs aynı active/closed
  state'i gösterir.
- Slim canonicals kısa kalır; verbose evidence önce arşivlenir.
- Close-out hygiene pass (W14/W15 paterni): Ruff lint, UI contract
  sync, markdown formatting, doc truth-state alignment, (varsa)
  yeni regression gate'ler.
- Per user direction (2026-05-18 restored): W16 `week16` branch'inde
  çalışır; sub-iter commits `week16` branch'inde land eder; close-out
  `week16 -> main` PR ile merge edilir; W16 tracker scope kapanışında
  frozen olur (W11-W15 paterni).

## §15 — W17 Carry-Over Closeout + Lifecycle Harness Yatırımı + Hygiene Sweep (closed 2026-05-18, merged 2026-05-18 via PR #25)

§15 opened with the W16 close-out PR #23 `week16 -> main` merge on
`2026-05-18` via `1b6d43f`. **Per user direction (2026-05-18) W17
lives on a `week17` branch (W11-W16 paterni preserved); close-out
merges into `main` via a `week17 -> main` PR — PR #25 MERGED
`2026-05-18` via `bff565d`.** W17-0..W17-7 sub-iter slate fully
delivered on `2026-05-18`. Frozen tracker:
[`active-work/W17-carryover-and-lifecycle-harness.md`](active-work/W17-carryover-and-lifecycle-harness.md)
carries per-iter scope locks, candidate items, and Per-Item Detail
evidence (sub-commits, module locations, test deltas). Final W17
bar (recorded at W17-6 close-out + W17-7 post-slate hotfix batch):
`tests/architecture/` **200 passed** (W16 final 199, +1 from W17-0
README phase-pointer gate transition); `make test-security` **220
passed** (Makefile target list; W17-7a `bf983eb` enrolled
`test_unaccounted_dropout_surface.py` in the hardcoded file list
— 217 → 220 recovers the W16-7-followup audit-trail count);
full suite **1899 passed, 9 skipped, 4 deselected** (W16 final
1893, +6: 4 W17-1 invariant tests + 1 W17-0 README phase-pointer
gate + 1 W17-2 harness smoke).

| Iter | Status | Theme |
|---|---|---|
| W17-0 | **closed `2026-05-18`** via `4508c2e` (doc-direction reconcile — `week17` branch + `week17 -> main` close-out PR wording across canonical docs; W11-W16 paterni preserved; README phase-pointer arch gate transition W14→W15→W16 paterni W16→W17'ye uygulandı) | `4508c2e` |
| W17-1 | **closed `2026-05-18`** via `8c26d02` (`[FOLLOWUP attribution-count-parity]` W16-3 carry-over; `build_evidence_bundle` activation emit-site stamps `is_target_extension_event` byte-identical with `count_target_activations` predicate; 4 invariant tests including W17-1 contract pin) | `8c26d02` |
| W17-2 | **closed `2026-05-18`** via `ff98235` (W17-3 enabler — `LifecycleHarness` + `lifecycle_harness` fixture at `tests/workflows/marketplace/test_lifecycle_harness.py`; smoke pins cancel-via-heartbeat path with thread identity assertion + production-wiring kwargs; scope cuts: no end-to-end `run_analysis_job` drive, no `fresh_alembic_engine` — UUID-keyed rows + cleanup-delete suffice) | `ff98235` |
| W17-3 | **scope-reduced `2026-05-18`** (doc-only commit — DESIGN-NEEDED for thread-relocation refactor shape; W17-2 harness prerequisite met but worker-thread step-1 reset is a HARD SYNC POINT for W13-11 HMAC secret consume, and the heartbeat thread starts only at step 4 — multiple plausible refactor shapes have different invariant cost; deferred to W18 dedicated sub-iter opening with ADR / §16 plan entry) | _deferred to W18 (doc-only)_ |
| W17-4 | **scope-reduced `2026-05-18`** (doc-only commit — bundled with W17-3 thread-relocation design decision; refactoring heartbeat shape in isolation would land throw-away work) | _deferred to W18 (doc-only)_ |
| W17-5 | **closed `2026-05-18`** via `394d40d` (`[CLEANUP postgres-version-fact-drift]` half closed at `seed_project_2.py` synthetic-fixture `postgres:15 -> postgres:16-alpine` stack alignment; other 4 candidate `[CLEANUP]` items deferred to W18+ opportunistic pull-as-found — they lack inline scope descriptions in the backlog and need per-item owner discovery) | `394d40d` |
| W17-6 | **closed `2026-05-18`** via `21f7c68` (close-out hygiene: canonical preamble refresh across 7 docs + §15 self-stamp post-final-bar + W17 tracker freeze; close-out via `week17 -> main` PR not yet opened — branch is pushed) | `21f7c68` |
| W17-7 | **closed `2026-05-18`** post-slate hotfix batch (W14-7/W14-8 paterni): W17-7a `bf983eb` enrolls `test_unaccounted_dropout_surface.py` in `make test-security` Makefile target (217 → 220 — recovers W16-7-followup audit-trail count); W17-7b `fc88678` `.env.example` adds `EXTRACE_EPOCH_RUN_ID` (W14-5 log run-id stamping env var that was missing); W17-7c `326dac8` ADR 0007 runbook references aligned with current `lan-exposure.md` (drops "short", lists all 5 pre-flight items); W17-7d `51dba29` `.pre-commit-config.yaml` header comment documents the intentional Python version gap (3 deliberate versions in play). Closes 3 backlog `[CLEANUP]` items + 1 Makefile-target hygiene gap; no source code change | `bf983eb` + `fc88678` + `326dac8` + `51dba29` |

### §15.0 — Neden ayrı §15

§14 W16 carry-over + audit findings + production regression
penceresini kapatır (W14-1 emit-site fix, W15 audit closeouts,
W14 finalize-drift null half, marketplace router + import graph
hygiene splits, alembic fresh-DB fixture); §15 yeni bir tema:
W16'dan doğrudan devreden üç kalem (attribution-count-parity,
heartbeat-sandbox-reset-off-thread, heartbeat-refactor) + bu
heartbeat trio'yu açan **lifecycle harness yatırımı**. §15 ayrı
tutuluyor ki §14 audit trail'i (W16 sub-iter close date'leri
ve commit'leri) donmuş kalsın.

### §15.1-§15.2 — Entry + Sub-iter Distribution

W17 entry triggered by W16 close-out PR #23 merge (`1b6d43f`,
`2026-05-18`). Sub-iter sequencing rationale: W17-0 doc reconcile
önce — W11-W16 paterni preservation. W17-1 attribution-count-parity
ikinci — küçük bounded subsystem (report-finalize / attribution_summary
producer side), W17-2 başlamadan kapanmalı (sequencing constraint
risk note). W17-2 lifecycle harness scaffold üçüncü — W17-3/4 ön
koşulu, W17'nin en ağır parçası; balon olursa scope reduction
kararı (W16-5 paterni). W17-3 heartbeat-sandbox-reset thread
relocation harness sonrası — concurrency-sensitive, W13-1 HMAC +
W13-12 fail-closed + W13-13 CAS pattern regress etmemeli
(W16-4 davranış-koruma paterni). W17-4 byte-identical clarity
refactor W17-3 üzerine. W17-5 hygiene cleanup batch düşük-risk,
paralel; W17-6 close-out hygiene + §15 self-stamp W14/W15/W16
paterni.

Stable ID → iter eşlemesi `POST_POC_BACKLOG.md`'de W17 Pull-Forward
tablosunda (W17-1 pull'da açılır).

Per user direction (2026-05-18) W17 lives on a `week17` branch
(W11-W16 paterni preserved); sub-iter commits land on `week17`
and the W17 close-out is merged into `main` via a `week17 -> main`
PR.

### §15.3 — Non-goals (W17)

W18+'a düşen kalemler stable ID'leri `POST_POC_BACKLOG.md` altında
açık kalır:

- `[GOAL marketplace-user-scan-and-notify]` (W16 close-out'ta
  eklendi `92eda39`; ayrı bir tracker + ADR-scale design pass
  ister — consumer-facing marketplace flow 4-halka: user scan
  request, installation gate, team report email, retroactive
  alert email; W18+).
- `[FOLLOWUP w11-8-companion-workflow-orm-bleed]` (W16 non-goal
  taşıma; W17+'a düşmüştü, W17 scope dışı tutuluyor).
- `[CLEANUP rule-registry-side-effect-loader]` (ADR 0003 A5/A7
  deferred rules landed olunca).
- `[FOLLOWUP codex-automation-6]`, `[FOLLOWUP capability-verification-gap]`
  (`NEEDS-DESIGN`; W18+).
- Watching items: `planner-selection-readability-audit`,
  `attribution-links-build-evidence-bundle-density`,
  `execute-attempt-rebloat-watch`, `dispatch-execution-rebloat-watch`
  (LoC bütçesi aşılana kadar dokunma).
- `[FOLLOWUP ci-reintroduction]` (geniş GH Actions CI reintroduction;
  W17 scope'a alınmıyor — harness yatırımı W17 ana yükü).
- W16'da kapanan tüm kalemler — `POST_POC_BACKLOG.md`'de kapanış
  audit trail'i korunmuştur, yeniden pull değil.

### §15.4 — Exit Criteria (W17-End)

W17 kapanır şu koşullar sağlandığında:

- W17-1..W17-6 kapanır ya da deferral rasyoneli ile W18'ye taşınır.
- W17 tracker final close evidence + current test counts tutar
  (`tests/architecture/` hedef 199 → ~201+; W17-1 invariant +
  W17-2 harness smoke ekleyince).
- W17-1 producer-side parity: `target_activation_count` ve evidence-
  kind count tek bir doğruluk kaynağından beslenir; runtime invariant
  test'i parity'yi yakalar.
- W17-2 harness: happy-path lifecycle (`start → reset → cancel →
  finalize`) smoke testi yeşil; cancel-mid-flight ve reset-during-
  finalize edge case'leri yeşil; harness `make test-local` altında
  çalışır.
- W17-3 davranış paritesi: sandbox-reset thread relocation sonrası
  W13-1 HMAC marker gates + W13-12 fail-closed dispatch + W13-13
  CAS pattern regress etmez (W17-2 harness altında doğrulanır).
- W17-4 byte-identical: heartbeat clarity refactor sonrası harness
  davranış paritesi yeşil.
- W17-5 hygiene cleanup: 3-5 `[CLEANUP]` kalem `POST_POC_BACKLOG.md`'de
  DONE/CLOSED audit trail ile işaretli.
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `active-work/README.md`, ve ilgili lane docs aynı active/closed
  state'i gösterir.
- Slim canonicals kısa kalır; verbose evidence önce arşivlenir.
- Close-out hygiene pass (W14/W15/W16 paterni): Ruff lint, UI
  contract sync, markdown formatting, doc truth-state alignment,
  (varsa) yeni regression gate'ler.
- Per user direction (2026-05-18): W17 `week17` branch'inde
  çalışır; sub-iter commits `week17` branch'inde land eder; close-out
  `week17 -> main` PR ile merge edilir; W17 tracker scope kapanışında
  frozen olur (W11-W16 paterni).

## §16 — W18 Heartbeat Refactor (closed 2026-05-21; PR #26 week18 -> main MERGED 2026-05-21 via 9874e79)

§16 opened with the W17 close-out PR #25 `week17 -> main` merge on
`2026-05-18` via `bff565d`. **Per user direction (2026-05-21) W18
lives on a `week18` branch (W11-W17 paterni preserved); close-out
PR #26 `week18 -> main` MERGED `2026-05-21` via `9874e79`;
post-merge audit (W18-4-followup `e1043e5`) landed
2026-05-21 directly on `main` (W17-post-merge `bf6ec3e` paterni).**
W18-0..W18-4 sub-iter slate fully delivered on `2026-05-21`. Frozen
tracker:
[`active-work/W18-heartbeat-refactor.md`](active-work/W18-heartbeat-refactor.md)
carries per-iter scope locks, Per-Item Detail evidence (sub-commits,
ADR map, test deltas). Driving signal: Codex live-run validation
`2026-05-21` of `ms-python.python` @ `992ad028f3df` reports
`automation_health.status=degraded` + `run_quality=low` while
static W17 final bar (1899/200/220) remains 🟢; W18 closes the
W17-3/W17-4 DESIGN-NEEDED heartbeat thread relocation deferral via
ADR 0012 Option A1 (dedicated sandbox-reset coordinator for the
step-1 setup reset; cancel-path teardown reset stays on the
heartbeat thread; function-extension shape; ~42 LOC across
`workflows/marketplace/analysis_execution.py` +
`analysis_service.py`). Final W18 bar (recorded at W18-4 close-out
hygiene): `tests/architecture/` **201 passed** (W17 final 200 +
W18-0 README phase-pointer arch gate W17->W18 transition);
`make test-security` **220 passed** (unchanged from W17); full
suite **1907 passed, 9 skipped, 8 deselected** (W17 final 1899 +
W18-0 +1 + W18-3 +3 + W18-4-followup +4 W18-2 invariant tests via
`e1043e5`).

| Iter | Status | Theme |
|---|---|---|
| W18-0 | **closed `2026-05-21`** via `89d0c9b` (doc-reconcile — `week18` branch + `week18 -> main` close-out PR wording across canonical docs; W11-W17 paterni preserved; new W18 active-work tracker + README phase-pointer arch gate transition W17→W18 + new W17 close-out fact gate `test_readme_phase_pointer_mentions_w17_closeout_merge`) | `89d0c9b` |
| W18-1 | **closed `2026-05-21`** via `acf6cc9` + `73d8a5c` followup doc-truth (ADR 0012 [`documents/adrs/0012-heartbeat-thread-relocation.md`](adrs/0012-heartbeat-thread-relocation.md) Option A1 Accepted — dedicated sandbox-reset coordinator for the step-1 setup reset; cancel-path teardown reset stays on the heartbeat thread; invariant cost trade-offs against W13-1 HMAC eager-consume / W13-3 two-phase cancel / W13-13 worker-entry CAS / W16-2 facade row lock all preserved byte-identical; W17-2 harness smoke pin preserved; NO CODE) | `acf6cc9` + `73d8a5c` |
| W18-2 | **closed `2026-05-21`** via `a9bffb1` + `78ed7cc` ADR self-stamp + `b5b64b6` ruff-format followup + `306d744` full-repo lint sweep + `pre-commit install` (heartbeat refactor implementation — step-1 reset moved off the worker thread via a dedicated `_run_reset_off_thread` coordinator; function-extension shape `~42 LOC`; new public `COORDINATOR_THREAD_NAME = "analysis-sandbox-reset-coordinator"` constant; W17-2 harness smoke passes byte-identical: thread identity `harness-monitoring-heartbeat` + `reload_window=True` kwargs + worker-entry CAS `WorkerEntryOutcome.CLAIMED`; three AST/behavioral gates pinning the bare `_reset_sandbox(...)` Name call at `analysis_service.py:155` preserved; ADR 0012 self-stamped via `78ed7cc`) | `a9bffb1` + `78ed7cc` + `b5b64b6` + `306d744` |
| W18-3 | **closed `2026-05-21`** via `92b310d` + `32d9905` self-stamp (3 lifecycle harness extension tests landed in `tests/workflows/marketplace/test_lifecycle_harness.py` per ADR 0012 §"Follow-On (W18-3 test surface)": `test_lifecycle_harness_parallel_reset_does_not_deadlock` (pins ADR §Consequences (Negative) bullet 2 "no deadlock" risk), `test_lifecycle_harness_reset_idempotency` (pins coordinator-thread name + setup-reset no-kwargs contract), `test_lifecycle_harness_reset_during_finalize` (pins post-finalize-barrier invariant); test-only commit; no production code change; ADR 0012 §Implementation self-stamped via `32d9905`) | `92b310d` + `32d9905` |
| W18-4 | **closed `2026-05-21`** via `3f4f95a` (close-out hygiene: 8-doc canonical preamble refresh + §16 W18 self-stamp post-final-bar + §16-§20 combined header split into §16 W18 closed + §17-§20 W19-W22 planning + W18 tracker freeze; W17-6 paterni `21f7c68` applied) | `3f4f95a` |
| W18-4-followup | **closed `2026-05-21`** via `e1043e5` (post-merge audit: 4 W18-2 invariant pins at `tests/workflows/marketplace/test_coordinator_invariants.py` — cancel_check signature default-None, `_COORDINATOR_POLL_INTERVAL_S ≤ 0.1` constant pin, cancel-propagation-within-poll-interval behavioral pin, reporter-emit thread-isolation pin — + 2 pre-existing doc drift fixes at `REFACTOR_OPTIMIZATION.md` line 3 + `W18-W22-roadmap.md`; full suite 1903 → 1907) | `e1043e5` |
| W18-post-merge | **closed `2026-05-21`** via this commit (PR #26 merge `9874e79` doc-truth alignment: 8-doc canonical preamble refresh + §16 close-out audit-trail entry + W18 tracker `Phase:` freeze stamp; W17-post-merge `bf6ec3e` paterni applied — direct commit on `main`, no PR) | this commit |

### §16.0 — Neden ayrı §16

§15 W17 carry-over kapanış penceresini kapatır (attribution parity,
lifecycle harness scaffold, heartbeat trio DESIGN-NEEDED deferral,
hygiene single-item). §16 yeni bir tema: **W17-3/W17-4
DESIGN-NEEDED heartbeat thread relocation deferral'ını kapatma** —
W17-2 harness scaffold üzerine inşa edilen ADR 0012 Option A1
implementation + W18-3 follow-on extension tests. §16 ayrı tutuluyor
ki §15 audit trail (W17 sub-iter close date'leri ve commit'leri)
donmuş kalsın; W18-4 close-out'ta §16 self-stamped olur
(W14/W15/W16/W17 paterni). W18-4 close-out aynı zamanda §16-§20
combined header'ı §16 (W18 closed) + §17-§20 (W19-W22 planning)
olarak böler — §17-§20 multi-iter roadmap bağımsız planlama bloğu
olarak kalır.

### §16.1-§16.2 — Entry + Sub-iter Distribution

W18 entry triggered by W17 close-out PR #25 merge (`bff565d`,
`2026-05-18`) + Codex live-run validation (`2026-05-21`) reporting
`automation_health.status=degraded`. Sub-iter sequencing rationale:
W18-0 doc-reconcile önce — W11-W17 paterni preservation + README
phase-pointer arch gate transition (W17→W18) + new W17 close-out
fact gate. W18-1 ADR ikinci — kod yazılmadan önce 3 refactor shape
arasından seçim yapılır ve invariant cost trade-offs tablosu
dokümante edilir (W13-1 / W13-3 / W13-13 / W16-2 invariant'ları);
NO CODE. W18-2 implementation üçüncü — seçilen shape (Option A1)
function-extension olarak hayata geçirilir (class-tabanlı
coordinator yerine çünkü 3 AST/behavioral gate `_reset_sandbox`
bare Name call'unu pin'liyor); W17-2 harness smoke MUST pass
byte-identically. W18-3 extension tests dördüncü — implementation
landed sonra tests yazılır ki assertion'lar gerçek davranışı
yansıtsın (W17-1 emit-site fix tests paterni). W18-4 close-out
hygiene + §16 self-stamp + §16-§20 split + W18 tracker freeze
beşinci — W14/W15/W16/W17 paterni.

Stable ID → iter eşlemesi `POST_POC_BACKLOG.md`'de W18 Pull-Forward
Acceptance Bar (closed) tablosunda + W19-W22 Roadmap Acceptance Bar
(planning) tablosunda.

Per user direction (`2026-05-21`) W18 lives on a `week18` branch
(W11-W17 paterni preserved); sub-iter commits land on `week18` and
the W18 close-out PR `week18 -> main` open + post-merge audit
scope-deferred per same user direction.

### §16.3 — Non-goals (W18)

W19+'a düşen kalemler stable ID'leri `POST_POC_BACKLOG.md` /
W19-W22 Roadmap Acceptance Bar (planning) tablosunda:

- `[BUG scenario-unaccounted-dropout-regression-fixture]` +
  `[BUG scenario-unaccounted-dropout-debug-refactor]` (W19-1 + W19-2;
  Hat-1 executor muhasebe bug — `unaccounted_dropout` fix).
- `[GOAL harness-verification-contract-event-level]` +
  `[FOLLOWUP harness-verification-debug-events]` +
  `[FOLLOWUP harness-verification-terminal-and-lm-tool]`
  (W19-3..W19-5; Hat-2 harness verification gap — declared ≠
  verified).
- `[RESEARCH activation-event-spec-crosswalk]` +
  `[GOAL taxonomy-scm-official-promotion]` +
  `[GOAL taxonomy-settings-official-promotion]` (W20-0..W20-2;
  Hat-3 coverage promotion easy tier).
- `[GOAL taxonomy-testing-coverage]` + `[GOAL taxonomy-comments-coverage]`
  + `[GOAL taxonomy-workspace-trust-coverage]` (W21-1..W21-3; mid
  tier).
- `[GOAL container-hardening-baseline]` (W21-4 stretch; W18 candidate
  intake reassigned to W21 per multi-iter roadmap).
- `[GOAL taxonomy-chat-policy-adr]` + `[GOAL taxonomy-chat-coverage]`
  + `[FOLLOWUP attribution-count-parity-process-events]` +
  `[FOLLOWUP attribution-count-parity-output-channel]` +
  `[GOAL sandbox-evasion-defense-mvp]` +
  `[GOAL sandbox-evasion-canary-fixture]` +
  `[GOAL activation-event-spec-gap-followup]` (W22-1..W22-6; hard
  tier + attribution depth + sandbox evasion ADR).
- W17'de kapanan tüm kalemler — `POST_POC_BACKLOG.md` W17
  Pull-Forward Acceptance Bar'da kapanış audit trail'i korunmuştur,
  yeniden pull değil.

### §16.4 — Exit Criteria (W18-End)

W18 kapanır şu koşullar sağlandığında (TÜMÜ SAĞLANDI `2026-05-21`
ya da deferral rasyoneli ile W19+'a taşındı):

- [x] W18-0..W18-4 kapanır ya da deferral rasyoneli ile W19'a taşınır.
- [x] W18-1 ADR `documents/adrs/0012-heartbeat-thread-relocation.md`
  Accepted (Option A1 — 3 refactor shape arasından dedicated
  sandbox-reset coordinator seçildi; invariant-cost trade-offs
  against W13-1 / W13-3 / W13-13 / W16-2 dokümante edildi).
- [x] W18-2 heartbeat refactor lands: W17-2 harness smoke
  (`test_lifecycle_harness_smoke_cancel_triggers_heartbeat_reset`)
  PASS — thread identity (`harness-monitoring-heartbeat`) +
  `reload_window=True` kwargs unchanged. W13-11 HMAC eager-consume
  invariant regression yok.
- [x] W18-3 üç yeni harness extension testi PASS: parallel reset +
  reset idempotency + reset-during-finalize.
- [x] `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `active-work/README.md`, ve ilgili lane docs aynı active/closed
  state'i gösterir (W18-4 close-out hygiene this commit).
- [x] W18 final bar: `make test-security` **220 passed**;
  `tests/architecture/` **201 passed** (W17 final 200 + W18-0
  README arch gate transition); full suite **1903 passed, 9
  skipped, 8 deselected** (W17 final 1899 + W18-0 +1 + W18-3 +3).
- [x] Live-run regression check (`ms-python.python` end-to-end
  analyze API + 2× UI scan): `automation_health.status=degraded`
  byte-identical with W17 baseline; **0 NEW reasons** (`degraded`
  kalır — W19 düşürecek).
- [x] Close-out hygiene pass: Ruff lint, UI contract sync, markdown
  formatting, doc truth-state alignment (`pre-commit run --all-files`
  15/15 hook PASS at landing).
- [x] Per user direction (`2026-05-21`): W18 `week18` branch'inde
  çalışır; sub-iter commits `week18` branch'inde land eder; W18
  tracker scope kapanışında frozen olur (W11-W17 paterni).
- [ ] Close-out PR `week18 -> main` open (deferred per user
  direction; opens when user signals).
- [ ] Post-merge audit (deferred per user direction; lands as
  separate commit after PR merges — W17-7-followup `dab4679`
  paterni).

## §17 — W19 Live-Run Kök Neden: Dropout + Harness Verification (closed synthetically 2026-05-26; PR #28 week19 -> main MERGED 2026-05-26 via c879603)

§17 opened with the W18 close-out PR #26 `week18 -> main` merge on
`2026-05-21` via `9874e79`. **Per user direction (`2026-05-21`) W19
lived on a `week19` branch (W11-W18 paterni preserved); sub-iter
commits landed on `week19` and the W19 close-out PR `week19 -> main`
opened at W19-6.** W19-0..W19-6 + W19-X all closed; PR #28
`week19 -> main` MERGED `2026-05-26` via `c879603`. Frozen tracker:
[`active-work/W19-live-run-root-cause.md`](active-work/W19-live-run-root-cause.md)
carries per-iter scope locks, Per-Item Detail evidence, and the
baseline live-run smoke artefakt (frozen at W19-6-followup-2 per
W17/W18 paterni). Driving signal: Codex live-run validation
`2026-05-21` of `ms-python.python` @ `992ad028f3df` reported
`automation_health.status=degraded` + `run_quality=low`; W19-2 live
re-anchor `d5de9ca` satisfies `unaccounted_dropout == 0`. Hat-1
closed + live-verified; Hat-2 fully closed synthetically.
Hat-3 (coverage matrix promotion — 6 missing capabilities)
deferred to W20-W22 per multi-iter roadmap (`§18-§20` planning
block below).

| Iter | Status | Theme | Closes which acceptance-bar item? |
|---|---|---|---|
| W19-0 | **closed `2026-05-21`** via this commit (doc-reconcile — `week19` branch + `week19 -> main` close-out PR wording across canonical docs; W11-W18 paterni preserved; new W19 active-work tracker + §17 W19 plan header doc-open + §17-§20 combined header split into §17 W19 active + §18-§20 W20-W22 planning + README phase-pointer arch gate transition W18→W19 + new W18 close-out fact gate `test_readme_phase_pointer_mentions_w18_closeout_merge` + baseline live-run smoke artefakt) | this commit | — (doc-reconcile; no acceptance-bar item) |
| W19-1 | **closed `2026-05-25`** via primary `6a21cf3` + self-stamp `fd02ca4` (`[BUG scenario-unaccounted-dropout-regression-fixture]`; RED fixture at `tests/executor/test_scenario_accountant_dropout_regression.py` capturing `unaccounted_dropout > 0` shape from live run; xfail(strict=True) parametrized on `debug_session` + `refactor_workflow` + an aggregate gate — W19-2 fix flipped strict-xfail to PASS; xfail markers removed at W19-2 primary commit + whitelist narrowed to `frozenset({"covered_via_layered_attempts"})`) | primary `6a21cf3` + self-stamp `fd02ca4` | must-pass #1 (`unaccounted_dropout == 0`) — RED fixture (W19-2 GREEN) |
| W19-2 | **closed `2026-05-25`** via primary `89b64da` + self-stamp `d9c6262` + live re-anchor `d5de9ca` (`[BUG scenario-unaccounted-dropout-debug-refactor]`; emit-site fix landed in `executor/flows/playwright/stimulus/passes.py` covered-only branch; ONE-PATH triage verdict — no mini-ADR per W16-1 emsali; new `covered_via_layered_attempts` reason_code emitted at the layered-passes reconciliation site; accountant fallback `scenario_accountant.py:392-438` preserved as son-mil koruyucu; +2 W16-1-mirror synthetic unit tests at `tests/security/test_scenario_dropout_repro.py`; W19-1 fixture initially regenerated SYNTHESIZED, then re-anchored to **live-lifted** at W19-2-followup-2 — `_meta.source_filename=activation_report_ms-python.python-2026.5.2026052501-c2bf28ca9506.json` / `_meta.source_sha256=e9e60b2e42...`; **live Hat-1 GREEN gate SATISFIED `2026-05-25 22:23`**: `unaccounted_dropout` count = 0 in live JSON `c2bf28ca9506`, both scenarios classified `covered_via_layered_attempts`, 16 of 16 key fields byte-identical with pre-fix anchor save the W19-2 reason_code change; +1 `_meta.source_sha256` canonical-hex format gate at the W19-1 regression file) | primary `89b64da` + self-stamp `d9c6262` + live re-anchor `d5de9ca` | must-pass #1 (`unaccounted_dropout == 0`) — closes (live-verified) |
| W19-3 | **closed `2026-05-25`** via primary `d2e83e7` + self-stamp this commit (`[GOAL harness-verification-contract-event-level]`; **HARD GATE for W19-4/W19-5 SATISFIED** — `confirmation_source: str = "none"` field landed on `EventAttemptRecord` (Pydantic at `packages/analysis_contracts/contracts.py` + executor dataclass at `executor/flows/playwright/monitor/records.py` + UI `EventAttemptDto`/`EventAttemptView`/`fromEventAttempt`); `_VALID_CONFIRMATION_SOURCES = frozenset({"harness_nonce", "log_record", "none"})` module constant + `_validate_confirmation_source` `@field_validator` mirroring the `status` field pattern (typing decision: `str + field_validator` not `Literal[...]` per §17 plan — codebase parity, JSON wire shape identical; deviation captured in active tracker Per-Item Detail block); new test file `tests/executor/test_automation_health_reasons.py` (12 tests: dataclass ↔ Pydantic parity + trigger-payload deserialization default + parametrize over 3 documented values + validator rejects unknown + orthogonality with existing `harness_verification_unconfirmed_present` reason emission rule, presence + absence parametrized); +6 contract round-trip tests at `test_analysis_fixture_baselines.py`; +4 UI adapter tests at `report.test.ts`; frozen trigger fixture `tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json` regenerated via planner replay so each of 21 event_attempts gains `"confirmation_source": "none"`; no live-run required at W19-3 — field lands at "none" everywhere with no behavior change) | primary `d2e83e7` + self-stamp this commit | must-pass #2 (`harness_verification_unconfirmed_present` reason drops) — schema enabler |
| W19-4 | **closed `2026-05-26`** via `7d44b0e` (`[FOLLOWUP harness-verification-debug-events]`; **producer side** — `onDebug*` family nonce confirmation generation in `executor/flows/harness_extension/*`; reconciliation Python side stamps `attempt.confirmation_source = "harness_nonce"` at `executor/flows/playwright/health/reconciliation.py:347-348` (`if execution_closed and family.startswith("onDebug")`); **consumer wire** — `_mark_unverified_harness_attempt` at `reconciliation.py:85-90` now gates `failure_reason_code="harness_verification_unconfirmed"` on `confirmation_source == "none"` so stamped attempts skip the unverified marker → W19 must-pass #2 `harness_verification_unconfirmed_present` reason drops becomes reachable; **7 new behavioral tests at `tests/executor/test_playwright_health_reconciliation.py:813-1090`** pinning producer happy-path (onDebug* with verified HMAC → harness_nonce stamp), fail-closed forged HMAC (stays "none"), missing harness marker (stays "none"), scope discipline (non-onDebug families with verified HMAC stay "none" — out of W19-4 scope), consumer skip when stamped, consumer set when "none") | `7d44b0e` | must-pass #2 (`harness_verification_unconfirmed_present` reason drops) — onDebug* half (live-verified at W19-X) |
| W19-5 | **closed `2026-05-26`** via primary `e537ebd` + self-stamp this commit (`[FOLLOWUP harness-verification-terminal-and-lm-tool]`; producer arm extension at `executor/flows/playwright/health/reconciliation.py:347-365` sibling elif to W19-4 onDebug arm — `elif execution_closed and (family == "onTerminalShellIntegration" or family.startswith("onLanguageModelTool")): attempt.confirmation_source = "log_record"`. **Plan deviation captured in primary commit body**: the original §17 plan envisioned a new `emitHarnessEvent` call in `stimulus_dispatch.js` + new `_attempt_has_local_completion_trace` predicate + `blocked_reason_code` fallback; live-anchor evidence on `8247e05ec9ef.json` showed all 6 unstamped attempts (1 onTerminalShellIntegration + 5 onLanguageModelTool:*) already carried `harness_trace:<attempt_id>` evidence — the HMAC-verified completion markers were already reaching the predicate via the existing runCurrentStimulus pipeline (LM directly through `harness:run_current_stimulus`; terminal via `OFFICIAL_EVENT_REGISTRY.harness_fallback="run_current_stimulus"`). So the simplest correct fix is the producer-arm extension only; the JS + predicate + fallback layers are unnecessary. **+7 new behavioral tests at `tests/executor/test_playwright_health_reconciliation.py:1175-1369`**: terminal happy-path, LM parametrize 5 variants (bare + configurePythonEnvironment + createVirtualEnvironment + getPythonEnvironmentDetails + installPythonPackages), forged HMAC fail-closed, missing marker, scope discipline (onDebug stays harness_nonce), consumer skip when stamped, consumer set when "none". W19-4 scope-discipline `_W19_4_NON_ONDEBUG_FAMILIES` narrowed to onCommand only; W19-4 orthogonality tests' unstamped half swapped to onCommand. Pre-W19-5 chat-tool attribution pin at `test_playwright_monitor_attribution.py:658` updated to assert `confirmation_source=="log_record"` + suppressed `failure_reason_code`. Synthetic test bar: `tests/architecture/` 202 (unchanged), `make test-security` 220 (unchanged), full suite 1973 passed (W19-X 1964 + 9 net: +11 new W19-5 pytest items, -2 W19-4 parametrize cases that moved to W19-5)) | primary `e537ebd` + self-stamp this commit | must-pass #2 (`harness_verification_unconfirmed_present` reason drops) — onTerminal+onLM half — **fully closes Hat-2 synthetically** |
| W19-6 | **closed `2026-05-26`** via primary `f17b4b1` + self-stamp `cd82153` + W19-6-followup-2 pre-merge hygiene this commit (close-out hygiene + 9-doc canonical preamble refresh + §17 W19 self-stamp post-final-bar + W19 tracker freeze; W18-4 paterni `3f4f95a`; **+ 3 hygiene items from W19-3-followup-2 audit `2026-05-25`**: (a) field-set parity gate widened at `test_executor_dataclass_and_pydantic_contract_share_confirmation_source_field`; (b) hotspot LOC ratchet at `tests/architecture/test_executor_hotspot_loc_ratchet.py` pinning **8 modules** >500 LOC under `executor/flows/playwright/` at LOC × 1.05 ceiling; (c) acceptance-bar `Closes which acceptance-bar item?` column added to §17.3 + active tracker mirror; **+ W19-X-handoff.md freeze** — SUPERSEDED banner; `[FOLLOWUP harness-secret-distribution-redesign]` migrated to POST_POC_BACKLOG.md, `[FOLLOWUP harness-secret-extra-reactivation-source]` forwarded to W18-W22-roadmap.md W20-0; **+ W19-6-followup-2 pre-merge hygiene** (this commit) — `cd82153` only fully refreshed CLAUDE.md; this commit corrects the remaining 8 docs + closes 6 test gaps (+20 parametrized tests across cross-Hat live-anchor smoke, planner routing onDebug variants, malformed log_record reject, parser glob, producer↔schema round-trip, concurrent reactivation stress) + freezes W19 tracker per W17/W18 paterni) | primary `f17b4b1` + self-stamp `cd82153` + W19-6-followup-2 this commit | expected (`run_quality: low → medium`) + close-out hygiene |

### §17.0 — Neden ayrı §17

§16 W18 heartbeat refactor kapanış penceresini kapatır (ADR 0012
Option A1 implementation + W18-3 harness extension tests). §17
yeni bir tema: **Codex live-run validation (`ms-python.python`
`2026-05-21`) raporladığı `automation_health.status=degraded` +
`run_quality=low` durumunu W18'in çözmediği üç hat'tan ilk ikisini
kapatma** — W18 sadece W17-3/W17-4 deferral'ını çözdü; live-run
health düşüklüğünün üç bağımsız nedeninden (Hat-1 executor
muhasebe bug / Hat-2 harness verification gap / Hat-3 coverage
matrix promotion) W19 ilk ikisini hedef alır. Hat-3 §18-§20
(W20-W22) planning bloğunda. §17 ayrı tutuluyor ki §16 audit
trail (W18 sub-iter close date'leri ve commit'leri) donmuş
kalsın; W19-6 close-out'ta §17 self-stamped olur
(W14/W15/W16/W17/W18 paterni).

§17 ile §18-§20'nin başlangıçta tek combined `§17-§20` başlığı
altında planning state'inde tutulmasının nedeni: W19-W22 dört
iter'lı multi-iter window olarak W18-4 close-out'ta §16'dan
ayrıldı. W19-0 (this commit) §17'yi active block'a promote eder
ve geri kalan §18-§20'yi W20-W22 planning bloğu olarak yeniden
adlandırır.

### §17.1-§17.2 — Entry + Sub-iter Distribution

W19 entry triggered by W18 close-out PR #26 merge (`9874e79`,
`2026-05-21`) + Codex live-run validation (`2026-05-21`)
reporting `automation_health.status=degraded` + `run_quality=low`.
Sub-iter sequencing rationale:

- **W19-0 önce** — W11-W18 paterni preservation + README
  phase-pointer arch gate transition (W18→W19) + new W18
  close-out fact gate + §17 W19 plan header doc-open + baseline
  live-run smoke (W18 heartbeat refactor sonrası dropout shape
  pinleme).
- **W19-1 ikinci (Hat-1 RED)** — root-cause-blind regression
  fixture with `xfail(strict=True)` paterni; canlı veriden lift
  edilir; CI yeşil kalır (xfail beklendiği gibi fails).
- **W19-2 üçüncü (Hat-1 GREEN)** — emit-site fix landed; W19-1
  xfail-strict GREEN'e flip → kaldırılır + whitelist daraltılır.
  Eğer iki senaryo iki ayrı upstream path'ten düşüyorsa
  `§17 design block` içine mini-ADR (W16-1 emsal; yeni ADR
  dosyası açılmaz).
- **W19-3 dördüncü (Hat-2 HARD GATE)** — schema field landing +
  UI adapter back-compat + contract round-trip; **W19-4/W19-5
  başlamaz** bu landing tamamlanana kadar (default `"none"` +
  optional alan back-compat).
- **W19-4 + W19-5 paralel uygulanabilir (Hat-2 emit-side)** —
  disjoint event families; CI yeşil tutmak için W19-4 → W19-5
  sıralaması önerilir.
- **W19-6 close-out** — W18-4 paterni: 8-doc canonical preamble
  refresh + §17 self-stamp + W19 tracker freeze + PR
  `week19 -> main`.

Stable ID → iter eşlemesi `POST_POC_BACKLOG.md`'de W19
Pull-Forward Acceptance Bar (W19-0 promoted from W19-W22 planning
to W19 in-flight) + W20-W22 Roadmap Acceptance Bar (W20-W22
planning) tablolarında.

Per user direction (`2026-05-21`) W19 lives on a `week19` branch
(W11-W18 paterni preserved); sub-iter commits land on `week19`
and the W19 close-out PR `week19 -> main` opens at W19-6.

### §17.3 — Non-goals (W19)

W20+'a düşen kalemler stable ID'leri `POST_POC_BACKLOG.md` /
W20-W22 Roadmap Acceptance Bar (planning) tablosunda:

- `[RESEARCH activation-event-spec-crosswalk]` +
  `[GOAL taxonomy-scm-official-promotion]` +
  `[GOAL taxonomy-settings-official-promotion]` +
  `[GOAL coverage-matrix-contract-tests]` +
  `[DESIGN taxonomy-comments-testing-readiness]` (W20-0..W20-4;
  Hat-3 coverage promotion easy tier).
- `[GOAL taxonomy-testing-coverage]` +
  `[GOAL taxonomy-comments-coverage]` +
  `[GOAL taxonomy-workspace-trust-coverage]` (W21-1..W21-3;
  mid tier).
- `[GOAL container-hardening-baseline]` (W21-4 stretch; W18
  candidate intake reassigned to W21 per multi-iter roadmap).
- `[GOAL taxonomy-chat-policy-adr]` +
  `[GOAL taxonomy-chat-coverage]` +
  `[FOLLOWUP attribution-count-parity-process-events]` +
  `[FOLLOWUP attribution-count-parity-output-channel]` +
  `[GOAL sandbox-evasion-defense-mvp]` +
  `[GOAL sandbox-evasion-canary-fixture]` +
  `[GOAL activation-event-spec-gap-followup]` (W22-1..W22-6;
  hard tier + attribution depth + sandbox evasion ADR draft).
- W18'de kapanan tüm kalemler — `POST_POC_BACKLOG.md` W18
  Pull-Forward Acceptance Bar'da kapanış audit trail'i
  korunmuştur, yeniden pull değil.

### §17.4 — Exit Criteria (W19-End)

W19 kapanır şu koşullar sağlandığında:

- [ ] W19-0..W19-6 kapanır ya da deferral rasyoneli ile W20'a
  taşınır.
- [x] W19-0 doc-reconcile landed via this commit (8-doc canonical
  preamble refresh + §17 W19 plan header doc-open + README
  phase-pointer arch gate transition W18→W19 + new W18 close-out
  fact gate + baseline live-run smoke).
- [x] W19-1 RED fixture
  `tests/executor/test_scenario_accountant_dropout_regression.py`
  landed as strict-xfail at `6a21cf3`; W19-2 later flipped it to
  PASS and removed xfail markers.
- [x] W19-2 emit-site fix landed; W19-1 xfail strict GREEN'e flip
  → kaldırıldı. Live Hat-1 GREEN gate satisfied at `d5de9ca`
  via UI-driven analyze API re-run:
  `unaccounted_dropout == 0` (**must-pass**).
- [x] W19-3 schema field `confirmation_source` landing complete
  (closed `2026-05-25` via primary `d2e83e7` + self-stamp this
  commit): Pydantic contract `EventAttemptRecord` + executor
  dataclass mirror + UI adapter back-compat (default `"none"`,
  `str + field_validator` typing for codebase parity with
  `status`) + contract round-trip pin + new test
  `tests/executor/test_automation_health_reasons.py` (12 tests).
- [x] W19-4 onDebug* nonce confirmation landed (`7d44b0e` — producer
  + consumer wire); reconciliation.py:347-348 stamps
  `confirmation_source="harness_nonce"` on verified onDebug* harness
  completion; reconciliation.py:85-90 gates failure_reason_code on
  confirmation_source=="none" so stamped attempts skip the unverified
  marker; 7 new behavioral tests at
  test_playwright_health_reconciliation.py:813-1090. Live smoke for
  W19-6 close-out: at least one `event_attempt` with
  `event_family=onDebug*` shows `confirmation_source="harness_nonce"`
  **and** `failure_reason_code != "harness_verification_unconfirmed"`.
- [ ] W19-5 onTerminal + onLM local-only confirmation landed;
  live smoke: terminal + LM `event_attempt` entries with
  `confirmation_source` populated.
- [ ] `automation_health.reasons` listesinden
  `harness_verification_unconfirmed_present` düşer
  (**must-pass**).
- [ ] `run_quality`: `low → medium` (**expected**; `low` kalırsa
  stretch failed → tracker'a not, W20'ye).
- [ ] `verification_gap_present`: gone (**stretch**; düşmezse
  W20'ye).
- [ ] `automation_health.status: degraded` OK
  (`official_unresolved_present` W20'de — Hat-3 scope).
- [ ] `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `active-work/README.md`, ve ilgili lane docs aynı active/closed
  state'i gösterir.
- [ ] W19 final bar: `make test-security` ≥220 passed;
  `tests/architecture/` ≥202 passed (W18 final 201 + 1 W18
  close-out fact gate from W19-0); full suite skip count W18
  baseline 9'dan **artmamalı**; full suite pass count W18 final
  1907 + W19-0 +1 + W19-N additions (estimate ≥1915, non-binding).
- [ ] Close-out hygiene pass: Ruff lint, UI contract sync,
  markdown formatting, doc truth-state alignment.
- [ ] Per user direction (`2026-05-21`): W19 `week19` branch'inde
  çalışır; sub-iter commits `week19` branch'inde land eder; W19
  tracker scope kapanışında frozen olur (W11-W18 paterni).
- [ ] Close-out PR `week19 -> main` open (W19-6).
- [ ] Post-merge audit (W18-4-followup `e1043e5` + post-merge
  `bf6ec3e` paterni; ayrı commit/direct on main veya weekly
  branch).

## §18 — W20 Coverage Promotion Round 1: Easy Wins (W20-0 in-flight 2026-05-26 on the week20 branch)

§18 opened with the W19 close-out PR #28 `week19 -> main` merge on
`2026-05-26` via `c879603`. **Per user direction (`2026-05-26`) W20
lives on a `week20` branch (W11-W19 paterni preserved); sub-iter
commits land on `week20` and the W20 close-out PR `week20 -> main`
opens at W20-5 PENDING USER APPROVAL.** Active tracker:
[`active-work/W20-coverage-promotion-easy-wins.md`](active-work/W20-coverage-promotion-easy-wins.md)
carries per-iter scope locks, Per-Item Detail evidence, and the
baseline live-run smoke artefakt. Driving signal: same Codex live-run
validation `2026-05-21` of `ms-python.python` @ `992ad028f3df`
reporting `coverage_summary.missing_capabilities = [scm, settings,
chat, comments, testing, workspace_trust]`. W19 closed Hat-1 + Hat-2;
W20 opens Hat-3 (coverage matrix promotion) easy-wins tier. W21-W22
follow with mid + hard tiers per multi-iter roadmap (§19-§20 planning
below).

| Iter | Status | Theme | Closes which acceptance-bar item? |
|---|---|---|---|
| W20-0 | **in-flight `2026-05-26`** via this commit (doc-reconcile — `week20` branch + new active-work tracker for W20 + §18 W20 plan header doc-open + §18-§20 combined header split into §18 W20 active + §19-§20 W21-W22 planning + 9-doc canonical preamble refresh + W20 Pull-Forward Acceptance Bar promotion in `POST_POC_BACKLOG.md` + README phase-pointer arch gate transition W19→W20 + new W19 close-out fact gate `test_readme_phase_pointer_mentions_w19_closeout_merge` pinning PR #28 / `week19 -> main` / `c879603`; baseline live-run pending user "go") | this commit | — (doc-reconcile; no acceptance-bar item) |
| W20-1 | **planned** — `[GOAL taxonomy-scm-official-promotion]` — `_OFFICIAL_CAPABILITY_SUPPORT["scm"]: "missing" → "covered"` at [`capabilities.py:88`](../packages/analysis_planner/capabilities.py); schema impact survey (W19-3 paterni; UI adapter / report builder / contract test deps; fixture regen if planner output depends) + invariant tests at `tests/platform/contracts/test_coverage_model.py` extend | TBD | live W20 acceptance #1 (`scm` drops from `missing_capabilities`) |
| W20-2 | **planned** — `[GOAL taxonomy-settings-official-promotion]` — `_OFFICIAL_CAPABILITY_SUPPORT["settings"]: "missing" → "covered"` at [`capabilities.py:90`](../packages/analysis_planner/capabilities.py); W20-1 paterni byte-identical | TBD | live W20 acceptance #2 (`settings` drops from `missing_capabilities`) |
| W20-3 | **planned** — `[GOAL coverage-matrix-contract-tests]` — keyset parity (official ↔ heuristic ↔ taxonomy) + official ⊆ heuristic subset + `_GLOBAL_CAPABILITY_NOTES` keyset ↔ taxonomy alignment + `CAPABILITY_TAXONOMY` ordering pin + W20-1/W20-2 post-condition regression. Extend `test_coverage_model.py` or new `test_coverage_track_invariants.py` | TBD | structural pin against future promotion regressions |
| W20-4 | **planned** — `[DESIGN taxonomy-comments-testing-readiness]` — VS Code Comments API surface inventory + Test Controller API surface inventory + W21 plumbing şablonu (`testing` W21-1 + `comments` W21-2); doc-only | TBD | W21-1 + W21-2 unblocker (template) |
| W20-5 | **planned** — close-out hygiene + 9-doc canonical preamble refresh (Active → Previous flip + final test bar) + §18 W20 self-stamp + W20 tracker freeze + W20 Pull-Forward Acceptance Bar audit-trail close + final live-run on `ms-python.python` + cross-doc parity gate for §18 self-stamp marker (W19-6 paterni) + opportunistic pull of `[FOLLOWUP harness-secret-extra-reactivation-source]` if W20-5 diagnostics show `poll_attempts > 1` + close-out PR `week20 -> main` open PENDING USER APPROVAL | TBD | close-out + live acceptance |

### §18.0 — Neden ayrı §18

§17 W19 live-run kök neden (Hat-1 + Hat-2) kapanış penceresini
kapatır (PR #28 `c879603` 2026-05-26'da merge'lendi; W19-0..W19-6 +
W19-X sub-iter slate fully delivered). §18 yeni bir tema: **Hat-3
coverage matrix promotion — easy wins tier** (`scm` + `settings`
official-track promotion). §18 ayrı tutuluyor ki §17 audit trail
(W19 sub-iter close date'leri ve commit'leri) donmuş kalsın;
W20-5 close-out'ta §18 self-stamped olur (W14/W15/W16/W17/W18/W19 paterni).

§18 ile §19-§20'nin başlangıçta tek combined `§18-§20` başlığı
altında planning state'inde tutulmasının nedeni: W19-W22 multi-iter
window olarak W19-0 close-out'ta §17 split'inden sonra geriye kalan
W20-W22 üç iter'lı planning bloğu. W20-0 (this commit) §18'i active
block'a promote eder ve geri kalan §19-§20'yi W21-W22 planning bloğu
olarak yeniden adlandırır (W19-0 paterni §17 split'ini mirror).

### §18.1-§18.2 — Entry + Sub-iter Distribution

W20 entry triggered by W19 close-out PR #28 merge (`c879603`,
`2026-05-26`) + same Codex live-run validation (`2026-05-21`)
reporting `coverage_summary.missing = [scm, settings, chat, comments,
testing, workspace_trust]`. Sub-iter sequencing rationale:

- **W20-0 önce** — W11-W19 paterni preservation + README
  phase-pointer arch gate transition (W19→W20) + new W19 close-out
  fact gate + §18 W20 plan header doc-open + 9-doc canonical preamble
  refresh + W20 Pull-Forward Acceptance Bar promotion + baseline
  live-run smoke (W19 close-out sonrası post-merge state pin).
- **W20-1 + W20-2 (taxonomy flips)** — Single-character flip at
  `capabilities.py:88` (scm) ve `:90` (settings) + invariant tests;
  schema impact survey W19-3 paterni mirror; fixture regen if needed.
- **W20-3 (contract test pin)** — yeni invariant set (parity + subset
  + ordering + post-condition); W20-1 + W20-2 flip'leri için
  regression koruması.
- **W20-4 (W21 readiness, doc-only)** — VS Code Comments API + Test
  Controller API surface envelope + W21-1 + W21-2 plumbing şablonu.
  NO CODE.
- **W20-5 close-out** — W19-6 paterni: 9-doc canonical preamble
  refresh + §18 self-stamp + W20 tracker freeze + final live-run +
  PR `week20 -> main` PENDING USER APPROVAL.

Stable ID → iter eşlemesi `POST_POC_BACKLOG.md`'de W20 Pull-Forward
Acceptance Bar (W20-0..W20-5 promoted from W20-W22 Roadmap Acceptance
Bar planning at W20-0 open) + W21-W22 Roadmap Acceptance Bar
(W21-W22 planning) tablolarında.

Per user direction (`2026-05-26`) W20 lives on a `week20` branch
(W11-W19 paterni preserved); sub-iter commits land on `week20` and
the W20 close-out PR `week20 -> main` opens at W20-5 PENDING USER
APPROVAL.

### §18.3 — Non-goals (W20)

W21+'ye düşen kalemler stable ID'leri `POST_POC_BACKLOG.md` /
W21-W22 Roadmap Acceptance Bar (planning) tablosunda:

- `[GOAL taxonomy-testing-coverage]` +
  `[GOAL taxonomy-comments-coverage]` +
  `[GOAL taxonomy-workspace-trust-coverage]` (W21-1..W21-3; mid tier).
- `[GOAL container-hardening-baseline]` (W21-4 stretch; W18 candidate
  intake reassigned to W21 per multi-iter roadmap).
- `[GOAL taxonomy-chat-policy-adr]` +
  `[GOAL taxonomy-chat-coverage]` +
  `[FOLLOWUP attribution-count-parity-process-events]` +
  `[FOLLOWUP attribution-count-parity-output-channel]` +
  `[GOAL sandbox-evasion-defense-mvp]` +
  `[GOAL sandbox-evasion-canary-fixture]` +
  `[GOAL activation-event-spec-gap-followup]` (W22-1..W22-6; hard
  tier + attribution depth + sandbox evasion ADR draft).
- `[FOLLOWUP harness-secret-distribution-redesign]` (W20-W22 ADR
  candidate; W19-X close-out migrated).
- `[FOLLOWUP harness-secret-extra-reactivation-source]` — opportunistic
  W20-5 if live-run diagnostic surfaces `poll_attempts > 1`.
- `[RESEARCH activation-event-spec-crosswalk]` (W22-6 implement if
  W20-0 crosswalk reveals gap; W20-0 forward-ref'd).
- W19'da kapanan tüm kalemler — `POST_POC_BACKLOG.md` W19
  Pull-Forward Acceptance Bar'da kapanış audit trail'i korunmuştur,
  yeniden pull değil.

### §18.4 — Exit Criteria (W20-End)

W20 kapanır şu koşullar sağlandığında (tam liste W20 tracker §18.4'te
[`active-work/W20-coverage-promotion-easy-wins.md`](active-work/W20-coverage-promotion-easy-wins.md)):

- [x] W20-0 doc-reconcile landed via this commit (9-doc canonical
  preamble refresh + §18 W20 plan header doc-open from §18-§20
  combined + W20 Pull-Forward Acceptance Bar promotion in
  POST_POC_BACKLOG.md + README phase-pointer arch gate transition
  W19→W20 + new W19 close-out fact gate + baseline live-run pending
  user "go").
- [ ] W20-1 + W20-2 official-track flips landed (`scm` + `settings`).
- [ ] W20-3 invariant set landed.
- [ ] W20-4 readiness design landed (doc-only).
- [ ] W20-5 close-out hygiene + final live-run + cross-doc parity
  gate + PR `week20 -> main` (PENDING USER APPROVAL).
- [ ] Live: `coverage_summary.missing_capabilities` drops `scm` +
  `settings` (6 → 4) — **must-pass**.
- [ ] `automation_health.status: degraded` OK
  (`official_unresolved_present` W22-end'inde kapanır — Hat-3 hard
  tier).
- [ ] W20 final bar: `make test-security` ≥220 passed;
  `tests/architecture/` ≥205 passed (W19 final 204 + 1 W19 close-out
  fact gate from W20-0); full suite skip count W19 baseline 9'dan
  **artmamalı**.

## §19-§20 — W21-W22 Capability + Coverage Promotion + Sandbox Evasion + Chat Policy Roadmap (planning)

İki iter'lı multi-iter roadmap planning state'inde dokümante edildi
(orijinal §18-§20 combined header'dan W20-0 close-out'ta
ayrıldı — W20 §18'e promote edildi, W21-W22 §19-§20 olarak yeniden
adlandırıldı; W19-0 paterni §17 split'ini mirror). Roadmap kaynak
gerçek dosyası (W21-W22 sub-iter slate'i + acceptance gate'leri +
critical files + ADR yolları + açık karar noktaları) burada:

[`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md)

### §19-§20.0 — Neden ayrı §19-§20 (multi-iter window)

§18 W20 coverage promotion round 1 easy-wins kapanış penceresini açar
(active `2026-05-26`). §19-§20 mid + hard tier devamı:

- **§19 — W21**: Coverage promotion round 2 (mid tier:
  `testing`, `comments`, `workspace_trust`); container
  hardening **stretch**
- **§20 — W22**: Coverage promotion round 3 (hard tier:
  `chat` policy ADR + implementation) + attribution depth +
  sandbox-evasion ADR draft

§19-§20 birlikte tutuluyor (multi-iter planning window) çünkü
W21-W22 Hat-3'ün mid + hard tier'larının ilerleyişi; her iter
kapandığında §N self-stamped olur (W14/W15/W16/W17/W18/W19 paterni);
§19 / §20 iter kapanışlarında ayrı ayrı self-stamped olur ve sırasıyla
combined header'dan ayrılır (W19-0'ın §17'yi + W20-0'ın §18'i
promote ettiği gibi).

### §19-§20.1 — Driving Signal (live run, 2026-05-21)

`ms-python.python` @ `992ad028f3df`
([output/activation_report_ms-python.python-2026.5.2026052001-992ad028f3df.json](../output/activation_report_ms-python.python-2026.5.2026052001-992ad028f3df.json),
7.4M):

- `automation_health.status = degraded`
- `run_quality = low`
- `automation_health.reasons = [skipped_scenarios_present, verification_gap_present, official_unresolved_present, harness_verification_unconfirmed_present]`
- `coverage_summary` (official track) `covered=7 / partial=5 / missing=6`; missing = `[scm, settings, chat, comments, testing, workspace_trust]`
- `event_attempts = 21`; capability-level `verified = 4`
- `skipped_scenarios = [debug_session, refactor_workflow]` (her ikisi `unaccounted_dropout` reason)
- `harness_handshake_required = True`

Status enum kontratı: `{healthy, degraded, inconclusive}`
([summary.py:260,378](../executor/flows/playwright/health/summary.py)).

W18 analyze API + UI scan smoke (close-out gate, recorded at
W18-2/W18-3 landings): `automation_health.status=degraded`
byte-identical with W17 baseline + **0 NEW reasons** ✓
(W18 doesn't drop the live-run state; that's W19'un Hat-1 + Hat-2
işi).

### §19-§20.2 — Üç katmanlı capability modeli

Plan üç ayrı "capability" katmanını tespit etti — sırasıyla aksiyon
gerektiriyor (A ve B) ya da spec uyumlu (C):

- **Katman A — Activation events**: `OFFICIAL_EVENT_REGISTRY` 29 entry
  ([test_registry_split_regression.py:101](../tests/platform/contracts/test_registry_split_regression.py)).
  4 shallow trigger (`onView`, `onWebviewPanel` restore semantics,
  `onAuthenticationRequest`, `onChatParticipant`). W20-0 spec
  crosswalk araştırması ile gerçek gap doğrulanır.
- **Katman B — Capability taxonomy**: 18 bucket
  ([capabilities.py:8-27](../packages/analysis_planner/capabilities.py)).
  Heuristic 14/4 covered/missing, official 12/6 covered/missing.
- **Katman C — Manifest capability**: `ExtensionCapabilitiesSchema`
  ([catalog.py:12](../appcore/contracts/schema_defs/catalog.py))
  `untrusted_*` + `virtual_*` — VSCode-spec uyumlu, **gap yok**.

### §19-§20.3 — Driving Plan dosyası

Tüm sub-iter slate'i, acceptance kriterleri (must-pass / expected /
stretch), live-run gate'leri, critical file paths, ADR yolları, ve
W19 başlangıcında cevaplanacak açık sorular tracker dosyasında:

[`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md)

Plan dosyası 3 review turundan geçti:

1. Initial Codex live-run validation (live rapor doğrulaması + capability taxonomy gap teyidi)
2. GPT round-1 (üç hat ayrımı, W19-1 xfail/RED pattern, harness verification ayrı boyut)
3. GPT round-2/3 (W20'nin 13 sub-iter'a patlaması, W20→W22 ayırma, `healthy/degraded/inconclusive` enum doğrulaması, ADR yolu `documents/adrs/` doğrulaması, `OFFICIAL_EVENT_REGISTRY` 29 sayısı, `onWebviewPanel` restore semantics, manifest source-of-truth, `confirmation_source` schema impact, `workspace_trust` defer fallback, chat-conditional W22 acceptance)

W19-0 doc-reconcile sub-iter'inde §17 W19 active block §18-§20'den
ayrıldı (`72712bd` + `086d7a5`). W20-0 doc-reconcile sub-iter'inde
§18 W20 active block §18-§20 combined'dan ayrıldı (this commit).
§19-§20 plan entry'si W21-W22 her iter açıldığında ayrı
self-stamped section'lar ekler (W14/W15/W16/W17/W18/W19 paterni).

### §19-§20.4 — Exit Criteria summary

W19 exit kriteri §17.4'te + W20 exit kriteri §18.4'te (yukarıda).
W21-W22 için tam exit criteria
[`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md)
"Sub-Iter Scope" bölümlerinde + "Live-Run Acceptance Gate"
bölümünde. Özet:

- **W21 exit**: her iki track missing `chat` dışında 0
  (`workspace_trust` defer edilirse + `workspace_trust`).
- **W22 exit**: chat ADR Accepted + path implemented **or**
  deferred-with-blocker; sandbox ADR + canary GREEN; her iki
  track missing == 0 (chat implemented path seçildiyse).
