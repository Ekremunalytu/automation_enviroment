# REFACTOR_OPTIMIZATION

`Last Updated: 2026-05-18 (W17 active — authoring on week17 branch per user direction; W16 closed via PR #23 week16 -> main MERGED 2026-05-18 via 1b6d43f. §15 W17 plan source — sub-iter slate W17-0..W17-6 reserved: W17-0 doc-reconcile (in progress); W17-1 attribution-count-parity closeout (W16-3 carry-over); W17-2 lifecycle harness scaffold (enabler); W17-3 heartbeat-sandbox-reset-off-thread (W16-5 carry-over, harness-gated); W17-4 heartbeat-refactor (W16-5 carry-over, byte-identical); W17-5 hygiene cleanup batch; W17-6 close-out hygiene + §15 self-stamp. Entry gate post-merge bar (recorded at W16-7 + post-PR 78f080e): tests/architecture/ 199 passed; make test-security 220 passed; full suite 1893 passed, 9 skipped. §14 W16 plan source — sub-iter slate fully delivered: W16-0 doc-reconcile (0e243ca + d78aa9c); W16-1 scenario-accountant emit-site fix (HIGH prod regression W14-1 carry-over, 01f910a + a4a050e); W16-2 analysis-job worker-entry CRUD ownership (W15 audit, 9d6d110 + c8b7811); W16-3 report-finalize null-leakage half (W14 carry-over, fa430f2 + e3d4a0c; attribution-count-parity split to W17 as [FOLLOWUP attribution-count-parity]); W16-4 health-reconciliation responsibility split (W15 audit, 304b99f + 384d276); W16-5 simulation-progress-cancel scope reduction (1 rejected, 2 deferred to W17 — heartbeat-sandbox-reset-off-thread + heartbeat-refactor, e21a05c); W16-6 hygiene splits + Alembic fresh-DB fixture (d40bb01); W16-7 close-out hygiene + canonical preamble refresh (8bf3c6b) + post-PR unaccounted_dropout surface pin (78f080e). W15 closed via PR #22 week15 -> main MERGED 2026-05-18 via 6161472; W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d)`

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
  Hygiene Sweep — **active `2026-05-18` on the `week17` branch (per
  user direction; W11-W16 paterni preserved).** Active tracker:
  [`active-work/W17-carryover-and-lifecycle-harness.md`](active-work/W17-carryover-and-lifecycle-harness.md).

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

## §15 — W17 Carry-Over Closeout + Lifecycle Harness Yatırımı + Hygiene Sweep (active 2026-05-18 on week17 branch)

§15 opened with the W16 close-out PR #23 `week16 -> main` merge on
`2026-05-18` via `1b6d43f`. **Per user direction (2026-05-18) W17
lives on a `week17` branch (W11-W16 paterni preserved); close-out
merges into `main` via a `week17 -> main` PR.** Active tracker:
[`active-work/W17-carryover-and-lifecycle-harness.md`](active-work/W17-carryover-and-lifecycle-harness.md)
carries per-iter scope locks, candidate items, and Per-Item Detail
evidence (assigned at first pull). Entry gate post-merge bar
(recorded at W16-7 close-out + post-PR `78f080e` top-up):
`tests/architecture/` **199 passed**; `make test-security` **220
passed**; full suite **1893 passed, 9 skipped**.

| Iter | Status | Theme |
|---|---|---|
| W17-0 | **closed `2026-05-18`** via `4508c2e` (doc-direction reconcile — `week17` branch + `week17 -> main` close-out PR wording across canonical docs; W11-W16 paterni preserved; README phase-pointer arch gate transition W14→W15→W16 paterni W16→W17'ye uygulandı) | `4508c2e` |
| W17-1 | **closed `2026-05-18`** via `8c26d02` (`[FOLLOWUP attribution-count-parity]` W16-3 carry-over; `build_evidence_bundle` activation emit-site stamps `is_target_extension_event` byte-identical with `count_target_activations` predicate; 4 invariant tests including W17-1 contract pin) | `8c26d02` |
| W17-2 | reserved | Lifecycle harness scaffold (enabler for W17-3 + W17-4) |
| W17-3 | reserved | `heartbeat-sandbox-reset-off-thread` (carry-over W16-5 deferral; harness-gated) |
| W17-4 | reserved | `heartbeat-refactor` (carry-over W16-5 deferral; W17-3 üzerine) |
| W17-5 | reserved | Hygiene cleanup batch (3-5 `[CLEANUP]` items) |
| W17-6 | reserved | Close-out hygiene + canonical preamble refresh + §15 self-stamp |

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
relocation harness sonrası — concurrency-sensitive, W13-1 HMAC
+ W13-12 fail-closed + W13-13 CAS pattern regress etmemeli
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
