# REFACTOR_OPTIMIZATION

`Last Updated: 2026-05-16 (W14 closed via PR #21 week14 -> main MERGED 2026-05-14 via 4e03c8d; W15 active on week15 branch cut from main HEAD 7cc2921 on 2026-05-14; W15-1/W15-2/W15-3/W15-4 closed (M10/M12/U8/U1/U2/U3/U6); W15-5..W15-7 pending; §13 W15 plan source entry triggered by W14 merge; W15 mid-iter hygiene 2026-05-16: doc-preamble consistency arch gate + 3 new audit findings in POST_POC_BACKLOG)`

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
- §12 → W14 Codex M-class Acceptance + Observability — **sub-iter slate
  complete; W14-7/W14-8 post-slate hotfixes closed; close-out PR
  `week14 -> main` next.** Tracker:
  [`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md).

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

## §13 — W15 Codex U-class Close-Out + UI Bounds + Posture (active 2026-05-14)

§13 opened with the `week15` branch cut from `main` HEAD `7cc2921` on
`2026-05-14` (W14 close-out PR #21 merged at `4e03c8d`; W15 base
includes the `7cc2921` scope-skeleton commit). Active tracker:
[`active-work/W15-codex-uclass-bounds-posture.md`](active-work/W15-codex-uclass-bounds-posture.md)
carries per-iter scope locks, candidate items, and Per-Item Detail
evidence (sub-commits, module locations, test deltas). Mid-iter status
`2026-05-16`: W15-1..W15-4 closed (M10/M12/U8/U1/U2/U3/U6); W15-1
post-slate typing hotfix landed; W15-5..W15-7 pending. Mid-iter
hygiene pass `2026-05-16` pulled forward the W15-7 doc-preamble
subset — six canonical doc preambles refreshed and
`tests/architecture/test_doc_preamble_consistency.py` added; three
new audit findings appended to `POST_POC_BACKLOG.md`. Remaining
W15-7 items (compose image pin + GH-action pin) still not started.

| Iter | Status | Landing commit |
|---|---|---|
| W15-1 | **closed `2026-05-14`** (sync analyze error taxonomy alignment — M10) | `c58c365` |
| W15-2 | **closed `2026-05-14`** (workspace symlink check order / orphan removal — M12; path b: fix) | `765cde7` |
| W15-3 | **closed `2026-05-15`** (`activationEvents` bounds + DB field-length Alembic migration — U8) | `3512a7c` |
| W15-4 | **closed `2026-05-16`** (UI bounds bundle: timeline / density strip / relations graph caps with truncation indicators — U1-U3 + U6; new `ui/src/lib/displayCaps.ts` helper; extracted `EventDensityStrip` from `ReportsPage`; 21 vitest cases; `+0` arch gates per UI-side cap policy. **W15-1 post-slate typing hotfix** `976dc96` landed in the same close-out window — `ANALYZE_*_ERROR_TYPES` annotation narrowed from `BaseException` to `Exception` after the W15-4 close-out `make typecheck` surfaced the mismatch at `workflows/marketplace/router.py:341`; W14-7 hotfix precedent.) | `89e13e3` (+ `976dc96`) |
| W15-5 | planned (quick fixes bundle: UI `/health` proxy + lifecycle `for <id>` regex — I2 + I4) | — |
| W15-6 | planned (unauthenticated catalog endpoints posture — ADR 0011 — U10-U11) | — |
| W15-7 | planned (regression lock-in umbrella: compose image pin + GH action pin + doc preamble truth-state refresh) | — |

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
  cut-off pattern'ini izler.
- Close-out hygiene pass (W14 paterni): Ruff lint, UI contract sync,
  markdown formatting, doc truth-state alignment, (varsa) yeni
  regression gate'ler.
