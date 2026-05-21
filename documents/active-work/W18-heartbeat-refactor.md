# W18 — Heartbeat Refactor (Active Work Tracker)

`Last Updated: 2026-05-21 (W18-0 in progress against main HEAD 05b6b9b — W17 closed via PR #25 week17 -> main MERGED 2026-05-18 via bff565d; W18-W22 multi-iter roadmap landed in planning state on main HEAD 05b6b9b (2026-05-21); W18 entered on the week18 branch per user direction 2026-05-21 (W11-W17 paterni preserved). §16 W18 plan source — sub-iter slate W18-0..W18-4 reserved; stable IDs assigned at first pull per W11-W17 precedent. Entry gate met: W17 final bar tests/architecture/ 200 passed + make test-security 220 passed + full suite 1899 passed, 9 skipped, 4 deselected.)`
`Phase: W18 active — authoring (W18-0 in progress)`
`Branch: week18 (per user direction 2026-05-21; W11-W17 paterni preserved — sub-iter commits land on week18, close-out merges into main via week18 -> main PR)`
`Owner: ekrem`

> **Authored 2026-05-21** as the W18 scope skeleton against `main` HEAD
> `05b6b9b` (W18-W22 multi-iter roadmap landed in planning state) +
> `1584c4d` (W18 candidate intake — `[GOAL container-hardening-baseline]` +
> `[GOAL sandbox-evasion-defense-mvp]`) + `bf6ec3e` (W17 post-merge audit
> trail). Stable IDs `W18-1..W18-4` are reserved by the iteration plan
> and **assigned at first pull** per the W11/W12/W13/W14/W15/W16/W17
> precedent (`REFACTOR_OPTIMIZATION.md` §16.0).

This is the canonical active work tracker for the W18 Heartbeat Refactor
window. Items receive stable IDs (`W18-1`, `W18-2`, …) **at first pull**,
not preemptively, per the W11/W12/W13/W14/W15/W16/W17 precedent.

Slim canonical [`REFACTOR_OPTIMIZATION.md §16`](../REFACTOR_OPTIMIZATION.md)
carries the entry-conditions block, goal statement, and the W18-W22
multi-iter roadmap context. The multi-iter source-of-truth roadmap is at
[`W18-W22-roadmap.md`](W18-W22-roadmap.md); this tracker is the W18
slice. The W17 frozen tracker
([`W17-carryover-and-lifecycle-harness.md`](W17-carryover-and-lifecycle-harness.md))
is the template structurally followed here.

## Status (Quick Glance)

- **W18 active — on `week18` branch per user direction (2026-05-21;
  W11-W17 paterni preserved).** Sub-iter commits land on `week18`;
  close-out merges into `main` via a `week18 -> main` PR.
- **Entry gate (met).** W17 close-out PR #25 `week17 -> main` MERGED
  `2026-05-18` via `bff565d`; W17 final bar (recorded at W17-6/W17-7
  close-out): `tests/architecture/` **200 passed**; `make test-security`
  **220 passed** (W17-7a `bf983eb` enrolled
  `test_unaccounted_dropout_surface.py` — 217 → 220); full suite
  **1899 passed, 9 skipped, 4 deselected**.
- **Driving signal (live run, 2026-05-21).** Codex live-run validation of
  `ms-python.python` @ `992ad028f3df` reports
  `automation_health.status=degraded` + `run_quality=low` while the
  static W17 final bar (1899/200/220) remains 🟢. W18 closes the
  W17-3/W17-4 `DESIGN-NEEDED` deferral as the **first** of five iters
  (W18-W22) responding to the live-run signal. W18 scope is **narrow**:
  heartbeat thread relocation only. The dropout fix (Hat-1) ships in
  W19; coverage promotion (Hat-3) in W20-W22.
- **W18-0 in progress** — this commit reconciles the doc truth-state
  from "W17 closed / W18-W22 planning state / W18 not yet entered" to
  "W18 active on week18 branch" across the canonical doc set, authors
  this tracker, and flips the README phase-pointer architecture gate
  (W16→W17 paterni applied to W17→W18).

## Sub-Iter Scope (Authored 2026-05-21)

| Iter | Theme | Source / Why | Notes |
|---|---|---|---|
| W18-0 | Doc reconcile + §16 W18 active-phase pointer | Pattern match W17-0 (`4508c2e`) | Open this tracker, refresh §16 anchor map entry, canonical preamble bumps across 7 docs, flip README phase-pointer arch gate (W17→W18 + new W17 close-out fact gate), update W18-W22-roadmap.md status (pre-W18 → W18 active, branch main → week18). Doc-only + 1 test file flip. |
| W18-1 | Heartbeat thread relocation ADR (NO CODE) | `[FOLLOWUP simulation-progress-cancel] heartbeat-sandbox-reset-off-thread` (W17-3 DESIGN-NEEDED carry-over via `c4c0646`) | `documents/adrs/0012-heartbeat-thread-relocation.md`. Three plausible refactor shapes enumerated with invariant-cost trade-offs against W13-1 HMAC eager-consume / W13-3 two-phase cancel / W13-13 worker-entry CAS / W16-2 facade row lock. Single shape picked with `Status: Accepted (pending W18-2 implementation)`. KOD YOK. |
| W18-2 | Heartbeat refactor implementation | `[FOLLOWUP simulation-progress-cancel] heartbeat-refactor` (W17-4 DESIGN-NEEDED carry-over via `c4c0646`) | Chosen ADR shape implemented at `workflows/marketplace/analysis_service.py` (HMAC consume window L155-L165) + `workflows/marketplace/analysis_execution.py` (`_run_monitoring_heartbeat` L292 + L299-L313 thread spawn). W17-2 harness smoke (`test_lifecycle_harness_smoke_cancel_triggers_heartbeat_reset`) MUST still pass with same invariants pinned. W13-11 HMAC consume invariant tests PASS (no regression on `consume_harness_python_secret` callers). |
| W18-3 | Lifecycle harness extension tests | `[FOLLOWUP w17-2-harness-extension-tests]` (new) | Three new tests in `tests/workflows/marketplace/test_lifecycle_harness.py` (parallel reset / reset idempotency / reset-during-finalize per W17-2 module docstring lines 27-35). Tests written **after** W18-2 implementation lands so assertions reflect actual behavior of the chosen shape. |
| W18-4 | Close-out hygiene + PR `week18 -> main` | Pattern match W17-6 (`8bf3c6b`) + W17-7-followup (`dab4679`) | Canonical preamble refresh across 7 docs + §16 self-stamp (post-merge final bar) + tracker freeze (sub-iter slate audit trail with commit SHAs) + PR open against `main`. |

## Per-Item Detail

Stable IDs W18-1..W18-4 get Per-Item Detail entries here as each is
pulled. Currently scope skeleton only (W18-0 authoring).

## Exit Criteria (W18-End)

W18 kapanır şu koşullar sağlandığında:

- W18-0..W18-4 kapanır ya da deferral rasyoneli ile W19'a taşınır.
- W18-1 ADR `documents/adrs/0012-heartbeat-thread-relocation.md` Accepted
  (pending implementation) — 3 refactor shapes enumerated, 1 picked,
  invariant-cost trade-offs against W13-1 / W13-3 / W13-13 / W16-2
  documented.
- W18-2 heartbeat refactor lands: W17-2 harness smoke
  (`test_lifecycle_harness_smoke_cancel_triggers_heartbeat_reset`) PASS
  with thread identity (`harness-monitoring-heartbeat`) and
  `reload_window=True` kwargs unchanged. W13-11 HMAC eager-consume
  invariant'ı regression etmez (existing `consume_harness_python_secret`
  tests + handshake-side gates green).
- W18-3 üç yeni harness extension testi PASS: parallel reset (lock ordering
  + no deadlock), reset idempotency (no executor surface corruption),
  reset-during-finalize (DB row `cancelled` not `completed`, reset runs
  at most once).
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `active-work/README.md`, ve ilgili lane docs aynı active/closed
  state'i gösterir.
- W18 final bar: `make test-security` ≥220 passed; `tests/architecture/`
  ≥201 passed (W17 final 200 + 1 W17 close-out fact gate from W18-0);
  full suite skip count W17 baseline 9'dan **artmamalı**; full suite
  pass count W17 final 1899 + W18-0 phase pointer + W18-3 harness
  extensions = 1903 hedef.
- `make sim-target TARGET=ms-python.python` smoke (W18-2 close):
  heartbeat refactor regression yok — `automation_health.reasons`
  listesi YENİ reason eklemez (`degraded` kalabilir, W19 düşürür).
- Close-out hygiene pass: Ruff lint, UI contract sync, markdown
  formatting, doc truth-state alignment.
- Per user direction (2026-05-21): W18 `week18` branch'inde çalışır;
  sub-iter commits `week18` branch'inde land eder; close-out
  `week18 -> main` PR ile merge edilir; W18 tracker scope kapanışında
  frozen olur (W11-W17 paterni).

## Risk Notes

- **W18-1 ADR derin teknik karar** — heartbeat thread relocation üç
  refactor shape arasından seçim yapılacak (dedicated reset thread /
  unified reset queue / pipeline restructure). Her birinin farklı
  invariant maliyeti var: W13-1 HMAC eager-consume L155-L165 hard sync
  point'i ile sıkı bağlı. Yanlış shape seçimi W18-2 implementation'da
  W17-2 harness smoke'un kıracağı bir regression yaratabilir. Mitigation:
  ADR Accepted edilmeden önce W17-2 harness smoke assertion'larına
  (thread identity, reload_window kwargs, CAS outcome) karşı her shape
  için tablo hazırla; en düşük invariant cost'lu shape'i seç.
- **W18-2 ↔ W17-2 harness smoke coupling** — eğer ADR Option C
  (pipeline restructure / heartbeat owns reset from step 1) seçilirse,
  harness fixture'ın kendisi paralel revision gerektirebilir
  (`harness-monitoring-heartbeat` thread'in artık step-1'i yönettiği
  varsayımı kırılır). W18-2 entry'de bu paralel rev'i scope flag olarak
  değerlendir; gerekirse W18-2a + W18-2b'ye böl.
- **Live-run health düşüş — W18 scope dışı** — Codex live-run rapor
  `automation_health.status=degraded` durumunu W18 düşürmez (Hat-1
  unaccounted_dropout fix W19'a, Hat-2 harness verification W19'a,
  Hat-3 coverage promotion W20+'a). W18-2 sim-target smoke'unda
  `degraded` görmek beklenen davranış; "YENİ reason eklenmedi"
  kriteri yeterli.

## Notes

- Branching policy: tek `week18` branch'i; per-iter feature branch
  açılmaz. Sub-iter commits sıralı `W18-0`, `W18-1`, ... olarak
  `week18`'e push edilir. W18-4 sonrası `week18 -> main` close-out PR.
- W17 tracker
  ([`W17-carryover-and-lifecycle-harness.md`](W17-carryover-and-lifecycle-harness.md))
  W17-7 + `dab4679` W17-7-followup sonrası **frozen reference**;
  W18 boyunca sadece okuma için açılır (W17-3 §W17-3 detay bloğu —
  3 plausible refactor shapes ve W13-11 hard sync point context'i
  için L205-249 spesifik referans; W17-2 harness module docstring
  L27-35 W18-3 extension noktaları için spesifik referans).
- W18-W22 multi-iter roadmap source-of-truth:
  [`W18-W22-roadmap.md`](W18-W22-roadmap.md). Bu tracker W18 slice'ı;
  W19+ için yeni active-work tracker'ları W18 kapanışında veya W19-0
  entry'de açılır.
