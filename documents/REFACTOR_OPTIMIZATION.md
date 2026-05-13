# REFACTOR_OPTIMIZATION

`Last Updated: 2026-05-13 (W13 closed; PR #20 week13 -> main merged via 772deb3; §12 W14 active on week14 branch cut 69251f1 — W14-1 BLOCKER → HIGH, W14-2/W14-3/W14-4/W14-5/W14-6 closed; W14 sub-iter slate complete; W14-7 post-slate hotfix closed via df925f8+c11ebd8 — container-shipping regression + Python 3.10 UTC compat; close-out PR week14 -> main next)`

W0-W14 plan document: stabilization + security + post-PoC external-review
integration + W14 acceptance + observability continuation. **Slim canonical**
— full historical content is frozen under dated snapshots:

- latest full snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-13.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-13.md)
- previous full snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-11.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-11.md)
- older snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-04-29.md)

## Anchor Map

- §10 / §10.7 → W0-W7 PoC window and acceptance bar.
- §11 / §11.0 - §11.4 → W8-W13 external-review integration frame.
- §11.5 → W8 tracker:
  [`active-work/W8-security.md`](active-work/W8-security.md).
- §11.6 - §11.10 → W9-W13 weekly briefs.
- §11.11 - §11.14 → cross-ref, rejected, lane, and exit criteria summaries.
- §12 → W14 Codex M-class Acceptance + Observability (active on the
  `week14` branch cut from `main` at `69251f1` on `2026-05-13`).
  W14-1 BLOCKER → HIGH downgrade landed same day; W14-2 (M4-M7 +
  M11) closed via `bde17be`; W14-3 (M13 + M14b + U4-U12) closed via
  `941250d`; W14-4 (analysis-jobs-race + EvidenceEvent kind
  invariant) closed via `03b32bc`; W14-5 (logger consolidation +
  run-ID stamping + executor runtime fingerprint + ADR 0010 + M5
  byproduct) closed via `dc79f61` + `9c095d2` + `db25d5f`; W14-6
  (regression lock-in umbrella: bare-binary pragma ratchet +
  executor.control outbound surface gate + variable-indirect
  subprocess coverage with binary_paths migration) closed via
  `2adad43` + `b031803` + `e42a448`. W14 sub-iter slate complete.
  **W14-7 post-slate hotfix** closed `2026-05-13` via `df925f8` (fix:
  Dockerfile COPY for `executor/binary_paths.py` +
  `executor/runtime_fingerprint.py` + Python 3.10 `datetime.UTC`
  compat shim aligned with `packages/analysis_engine/runner.py:26`)
  and `c11ebd8` (regression gate
  `tests/architecture/test_executor_container_shipping.py`, +2 arch
  cases). Close-out PR `week14 -> main` is the next milestone. Tracker:
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

## §11 — W8-W13 External Review Integration Window (2026-04-24+)

§11 integrates the post-PoC external reviews without moving the W0-W7 PoC
acceptance bar. Review snapshots live under `archive/reviews/`.

### §11.0 — Neden §11, §10'a ek satır değil

W8-W13 work is post-PoC hardening and modularization. Keeping it under §11
preserves the audit trail that §10.7 already closed.

### §11.1 — Entry Gate

W8 entry gate was met `2026-04-27`: PR345 PRs 1-5 landed, ADR 0006 accepted,
`make test-security` entry baseline was green, demo acceptance was green, and
W8-0 deterministic harness readiness landed.

Current closure chain: W8 closed `2026-04-29`; W9 closed `2026-05-04` via
PR #9; W10 closed `2026-05-04` via PR #11; W11 closed `2026-05-05` via
PR #14; W12 closed `2026-05-10` via PR #18; W13 closed `2026-05-13` via
PR #20.

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
closed for active work; retained for W8-1..W8-9 stable-ID references.

### §11.6 — W9 Executor/Detection Boundary

W9 closed `2026-05-04` via PR #9. ADR 0008 container package-mode invocation
is accepted; dual-import fallback and runtime `sys.path.insert` debt were
removed.

### §11.7 — W10 Contract Hygiene + Planner Cleanup

W10 closed `2026-05-04` via PR #11. `schema_version`, planner registry
cleanup, typed health/coverage models, executor action enum, and W10
contract gates landed.

### §11.8 — W11 Monitor Lifecycle Split

W11 closed `2026-05-05` via PR #14. W11-1..W11-8 split monitor runtime,
report assembly, scenario accounting, monitor facade, workflow service, and
storage CRUD modules. Tracker:
[`active-work/W11-monitor-lifecycle.md`](active-work/W11-monitor-lifecycle.md).

### §11.9 — W12 Executor Subpackaging + Attribution Cleanup

W12 closed `2026-05-10` and merged via PR #18 (`33a0852`). Tracker is frozen:
[`active-work/W12-executor-subpackaging.md`](active-work/W12-executor-subpackaging.md).

Closed scope:

- W12-0 security pull-forward: file-backed output-signal redaction.
- W12-1 executor subpackaging: ≤10 flat Playwright modules, 10 package dirs,
  `python -m` shims, and import-cycle gates.
- W12-2 attribution facade cleanup: public facade trimmed, companion follow-ups
  closed.
- W12-3 `raw_context` discriminated union typing.
- W12-4 entrypoint dispatch extraction: `runner.py::main` under 200 LoC.
- W12-5 `runtime_capture/extension_host.py` split + body-preview redaction
  architecture gate.
- UI/API Dockerfile digest pins, W12 close-out coverage, and Codex CRITICAL
  subprocess-output redaction fix.

Final close evidence is archived at
[`archive/active-work/W12-close-acceptance-completed-2026-05-10.md`](archive/active-work/W12-close-acceptance-completed-2026-05-10.md).

#### §11.9.1 — `runtime_capture/extension_host.py` Split Scoping

§11.9.1 is closed by W12-5. Full scoping detail lives in the W12 tracker and
archive snapshot; current code keeps `extension_host.py` as a thin facade over
focused runtime-capture modules.

### §11.10 — W13 Test Expansion + Observability

Entry conditions were met `2026-05-10`; W13 closed `2026-05-13` and merged
via PR #20 (`772deb3`). Tracker:
[`active-work/W13-test-expansion-observability.md`](active-work/W13-test-expansion-observability.md).

Summary:

| Scope | Status |
|---|---|
| Acceptance bar | W13-1..W13-7 closed H3/H4/H5/H6/M1/M9 from the 2026-05-10 Codex Cloud audit. |
| §11.10 GOAL pulls | W13-8 benign silence fixture 3->5, W13-9 `.env` gitignore gate, and W13-10 singleton-lock recovery closed. |
| Close-gate pulls | W13-11 HMAC python secret target-install race, W13-12 fail-closed harness handshake, and W13-13 worker-start cancel-race CAS closed in-window. |
| Final bar | `make test-local` 1551 passed / 10 skipped / 8 deselected; `make test-security` 215 passed; `tests/architecture/` 117 passed. |

Original §11.10 candidates still open are tracked in `POST_POC_BACKLOG.md`
and the W14 tracker. Close-out PR #20 already merged; the remaining
§11.10 GOAL umbrellas iterate into W14.

### §11.11 — Cross-Reference

External review findings are tracked by stable IDs in `POST_POC_BACKLOG.md`;
closed W8-W12/W13 items stay visible there only as audit trail summaries.

### §11.12 — Rejected Or Out-Of-Scope Items

Rejected review findings and WONT-FIX decisions live in the archive snapshots.
Current WONT-FIX audit item: M14a, workspace ownership by design.

### §11.13 — Paralel Lane Assignments

Use `documents/AGENT_CONTEXT.md` and the lane docs for routing. Active W14
work starts from `security-detection`, `executor-runtime`, `platform-storage`,
or `ui` depending on the stable ID.

### §11.14 — W13-End Overall Exit Criteria

W13 closed once:

- H3, M1, and M9 are either closed or explicitly deferred with acceptance
  rationale. (H3 closed via W13-5; M9 closed via W13-6; M1 closed via W13-7.)
- W13 tracker has final close evidence and current test counts.
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, `documents/README.md`, and
  relevant lane docs point to the same active/closed state.
- Slim canonicals remain short; verbose evidence is archived first.
- **Close-gate (added `2026-05-11`, cleared `2026-05-13`): W13-11/12/13
  close-pass items all GREEN.** Codex Cloud second-opinion review
  identified 3 P1 bypass surfaces in the originally W13-claimed H6 +
  H4 closures (W13-11 HMAC python secret target-install race —
  **closed `2026-05-12`**; W13-12 fail-closed harness handshake —
  **closed `2026-05-12`**; W13-13 worker-start cancel-race CAS —
  **closed `2026-05-13`**; F4 README drift sweep + regex pin
  originally bundled in W13-13 scope landed early in W13-11 push
  `2026-05-12`). Close-out PR #20 `week13 -> main` **MERGED**
  `2026-05-13` via `772deb3` — all fixes in-window preserve audit-trail
  integrity (history shows H6/H4 work as a coherent iteration family
  rather than a deferred follow-up).

## §12 — W14 Codex M-class Acceptance + Observability (active 2026-05-13)

§12 opened with the `week14` branch cut from `main` at `69251f1` on
`2026-05-13` (close-out PR #20 already merged the same day via
`772deb3`). The active tracker
[`active-work/W14-codex-acceptance-observability.md`](active-work/W14-codex-acceptance-observability.md)
carries per-iter Per-Item Detail evidence (sub-commits, module
locations, test deltas, production validation). Sub-iter closure
state as of `2026-05-13`:

| Iter | Status | Landing commit |
|---|---|---|
| W14-1 | BLOCKER → HIGH downgrade (stochastic-bound rationale) | `0c8bd02` |
| W14-2 | closed (M4-M7 + M11 input validation) | `bde17be` |
| W14-3 | closed (M13 + M14b + U4-U12 external surface) | `941250d` |
| W14-4 | closed (analysis-jobs-race + EvidenceEvent kind invariant) | `03b32bc` |
| W14-5 | closed (logger consolidation + run-ID stamping + executor runtime fingerprint; ADR 0010; M5 byproduct) | `dc79f61` + `9c095d2` + `db25d5f` |
| W14-6 | closed (regression lock-in umbrella: bare-binary pragma ratchet + executor.control outbound gate + variable-indirect subprocess coverage with binary_paths migration) | `2adad43` + `b031803` + `e42a448` |
| W14-7 | closed post-slate (container-shipping regression + Python 3.10 UTC compat — Dockerfile COPY gap for `executor/binary_paths.py` + `executor/runtime_fingerprint.py` exposed via post-`2cbdca0` production smoke retry; W14-5.3's `from datetime import UTC` swapped to `getattr(_dt, "UTC", _dt.timezone.utc)` shim; +2 arch gate cases pinning import-graph ↔ Dockerfile invariant) | `df925f8` + `c11ebd8` |

### §12.0 — Neden ayrı §12

§11 W8-W13 external-review integration penceresini sınırlar (W12 close
2026-05-10, W13 acceptance bar 2026-05-11). W14 yeni bir tema: Codex
M-class acceptance-bar pull-forward devamı + §11.10 GOAL umbrella'larının
ertelenen kısmı. §12 ayrı tutuluyor ki §11 audit trail'i (`2026-05-10`
Codex Cloud audit, H/M class çekim sırası) donmuş kalsın.

### §12.1 — Entry Gate

W14 entry gate was triggered when the W13 close-out PR merged. The remaining
activation step is an explicit W14 pull / `week14` branch cut from `main`:

- `week13 -> main` close-out PR #20 merged `2026-05-13` via `772deb3`
  (W12 PR #18 cut-off pattern).
- W13 final/post-merge baseline: `make test-local` 1551 passed /
  10 skipped / 8 deselected, `make test-security` 215 passed,
  `tests/architecture/` 117 passed.
- W14 tracker marks close-out prerequisites complete; phase opens on explicit
  pull.

### §12.2 — W14 alt-iterasyon dağılımı

W13'ün 10 sub-iter ritmi yerine, 6 sub-iter kohezyon kümelerine bölünür.
İlk pull anında `W14-N` stable ID atanır (W11/W12/W13 precedent).

| Iter | Tema | Stable ID(s) |
|---|---|---|
| W14-1 | BLOCKER araştırma — scenario-dropout kök neden | `[BUG scenario-dropout-upstream-root-cause]` |
| W14-2 | Codex M-class — input validation | `[FOLLOWUP codex-2026-05-10-M4-M7-output-ts-range-validation]` + `[FOLLOWUP codex-2026-05-10-M11-report-health-malformed-types]` |
| W14-3 | Codex M-class — dış yüzey sertleştirme | `[FOLLOWUP codex-2026-05-10-M13-network-uri-summary-redaction]` + `[FOLLOWUP codex-2026-05-10-M14b-cdp-port-default-disabled]` + `[FOLLOWUP codex-2026-05-10-U4-U12-makefile-shell-quoting]` |
| W14-4 | Doğruluk + concurrency | `[FOLLOWUP analysis-jobs-race]` + `[FOLLOWUP evidence-event-kind-raw-context-invariant]` |
| W14-5 | §11.10 GOAL devamı — Logger consolidation + run-ID stamping + executor runtime fingerprint | `[GOAL w14-logger-consolidation]` + `[GOAL w14-run-id-stamping]` + `[FOLLOWUP codex-automation-5]` |
| W14-6 | §11.10 GOAL devamı — W8-W12 regression lock-in umbrella | `[FOLLOWUP arch-gate-executor-control-outbound]` + `[FOLLOWUP arch-gate-bare-binary-pragma-ratchet]` + `[FOLLOWUP w8-4-variable-indirect-subprocess-coverage]` |

Sıralama gerekçesi: W14-1 önce — CRITICAL BUG W14 scope'unu genişletebilir
veya HIGH'a indirebilir. Sonra düşük-risk M-class (W14-2), W13-6 redaction
zincirinin devamı (W14-3), correctness/concurrency (W14-4), altyapı GOAL
pulls (W14-5, W14-6). W14-5, W14-6'dan önce gelir çünkü logger
consolidation regression lock-in gate'lerinde test enstrümantasyonuna girdi
olur.

### §12.3 — Non-goals (W14)

Aşağıdaki kalemler W14 scope'unda DEĞİL — W15+'a düşer. Stable ID'leri
[`POST_POC_BACKLOG.md`](POST_POC_BACKLOG.md) altında açık kalır:

- Codex M-class: M5 (W14-5 yan ürünü değilse), M10, M12, U1-U3, U6, U8,
  I2, I4
- Posture decision: `[FOLLOWUP codex-2026-05-10-U10-U11-unauth-catalog-endpoints]`
  — W14 öncesi ADR oturumu, plan değil karar
- Watching items: `planner-selection-readability-audit`,
  `attribution-links-build-evidence-bundle-density`,
  `execute-attempt-rebloat-watch`, `dispatch-execution-rebloat-watch` —
  LoC bütçesi aşılana kadar dokunma
- UI follow-up'ları: `ui-raw-context-discriminator-parity`,
  `vsix-integrity-in-activation-report` → W14-4 backend invariant tamamlandıktan
  sonra UI parity ayrı pull
- Refactor: `scenario-accountant-conservation-split` (W14-1 kök neden
  netleştikten sonra ayrı pull adayı; W14-1 PR'ına dahil edilmez)
- Automation/verification: `[FOLLOWUP codex-automation-6]` (UI failure
  taxonomy) + `[FOLLOWUP capability-verification-gap]` — W14 temasıyla
  örtüşmüyor; ikincisi `NEEDS-DESIGN`. `codex-automation-5` ise W14-5'e
  katlandı (run-ID stamping ile sibling)

### §12.4 — Exit Criteria (W14-End)

W14 kapanır şu koşullar sağlandığında:

- W14-1 BLOCKER kalemi ya kapanır ya da HIGH'a indirilip dokümante edilir.
- W14-2..W14-6 ya kapanır ya da slim canonical'da explicit deferral
  rasyoneli ile W15'e taşınır.
- W14 tracker final close evidence + current test counts tutar.
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`, `documents/active-work/README.md`
  ve ilgili lane docs aynı active/closed state'i gösterir.
- Slim canonicals kısa kalır; verbose evidence önce arşivlenir.
- `week14 → main` close-out PR W12 PR #18 / W13 close-out cut-off pattern'ini
  izler.
