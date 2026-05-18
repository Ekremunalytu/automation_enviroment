# W17 — Carry-Over Closeout + Lifecycle Harness Yatırımı + Hygiene Sweep (Active Work Tracker)

`Last Updated: 2026-05-18 (W17 authored — scope skeleton against main HEAD 1b6d43f / W16 close-out merge commit; sub-iter slate W17-0..W17-6 reserved by iteration plan; stable IDs assigned at first pull per W11/W12/W13/W14/W15/W16 precedent)`
`Phase: W17 active — authoring (sub-iter pulls land sequentially on week17)`
`Branch: week17 (per user direction 2026-05-18; W11-W16 paterni preserved — sub-iter commits land on week17, close-out merges into main via week17 -> main PR)`
`Owner: ekrem`

> **Authored 2026-05-18** as the W17 scope skeleton against `main` HEAD
> `1b6d43f` (W16 close-out merge commit) + `92eda39` (post-merge backlog
> top-up `[GOAL marketplace-user-scan-and-notify]`). Stable IDs
> `W17-1..W17-6` are reserved by the iteration plan and **assigned at
> first pull** per the W11/W12/W13/W14/W15/W16 precedent
> (`REFACTOR_OPTIMIZATION.md` §15.0).

This is the canonical active work tracker for the W17 Carry-Over Closeout
+ Lifecycle Harness + Hygiene Sweep window. Items receive stable IDs
(`W17-1`, `W17-2`, …) **at first pull**, not preemptively, per the
W11/W12/W13/W14/W15/W16 precedent.

Slim canonical [`REFACTOR_OPTIMIZATION.md §15`](../REFACTOR_OPTIMIZATION.md)
carries the entry-conditions block, goal statement, and current candidate
list. The W16 frozen tracker
([`W16-regression-and-audit-closeout.md`](W16-regression-and-audit-closeout.md))
is the template structurally followed here.

## Status (Quick Glance)

- **W17 active — on `week17` branch per user direction (2026-05-18;
  W11-W16 paterni preserved).** Sub-iter commits land on `week17`;
  close-out merges into `main` via a `week17 -> main` PR.
- **Entry gate (met).** W16 close-out PR #23 `week16 -> main` MERGED
  `2026-05-18` via `1b6d43f`; W16 final post-merge bar (recorded at
  W16-7 close-out + post-PR top-up `78f080e`):
  `tests/architecture/` **199 passed** (+27 from W15 final 172);
  `make test-security` **220 passed** (+5 from W13 final 215, three
  added post-PR as `unaccounted_dropout` surface pins matching the
  live-scan shape); full suite **1893 passed, 9 skipped**.
- **W17-0 in progress `2026-05-18`** — doc-direction reconcile +
  W17 tracker authored against canonical docs (this commit lands as
  the first commit on `week17`).

## Sub-Iter Scope (Authored 2026-05-18)

| Iter | Theme | Source / Why | Notes |
|---|---|---|---|
| W17-0 | Doc reconcile + W17 tracker open | Pattern match W16-0 | Open this tracker, §15 header, canonical preamble bumps, freeze W16 tracker (already self-frozen at W16-7 + `78f080e`). Doc-only. |
| W17-1 | `attribution-count-parity` closeout | Carry-over from W16-3 (W14 production scan) | Producer-side divergence: `target_activation_count = 1` while evidence-kind count = 0. Single subsystem (report-finalize / attribution_summary). Emit-site fix pattern W16-1 (`01f910a` + `a4a050e`); contract-seam pattern W16-3 (`fa430f2` + `e3d4a0c`). |
| W17-2 | Lifecycle harness scaffold | Enabler for W17-3 + W17-4 | `start → reset → cancel → finalize` harness against real Postgres DB (reuse `fresh_alembic_engine` fixture from W16-6 `d40bb01`) + Playwright mock surface (reuse browser-monitor side mock primitives). Likely lives under `tests/integration/lifecycle_harness/`. W17's heaviest sub-iter. |
| W17-3 | `heartbeat-sandbox-reset-off-thread` | Carry-over from W16-5 deferral (W17+ pending lifecycle harness) | Move sandbox-reset call from analysis worker thread to monitoring heartbeat thread. Concurrency-sensitive: lock ordering + reset idempotency + partial-state recovery. W13-1 HMAC + W13-12 fail-closed gates byte-identical (W16-4 pattern `304b99f` + `384d276`). Verified under W17-2 harness. |
| W17-4 | `heartbeat-refactor` | Carry-over from W16-5 deferral (bundled with W17-3) | Clarity refactor of heartbeat shape — behavior byte-identical, hygiene gain not correctness. Builds on W17-3; harness regression catches behavioral drift. |
| W17-5 | Hygiene cleanup batch | Low-risk pull-next from `POST_POC_BACKLOG.md` | 3-5 `[CLEANUP]` items. Aday set (final pick at W17-5 entry): `env-example-extrace-vars`, `postgres-version-fact-drift`, `adr-0007-runbook-wording-drift`, `pre-commit-python-version-alignment`, `report-builder-naming` (alt: `monitor-runtime-naming-overlap`). Pattern W16-6 hygiene splits (`d40bb01`) — separate small commits. |
| W17-6 | Close-out hygiene + canonical preamble refresh | Pattern match W16-7 | Slim canonical 7 doc preamble truth-state refresh + §15 self-stamp post-merge W17 final bar + backlog item statuses (closed items → DONE/CLOSED audit trail). Pattern W16-7 (`8bf3c6b`) + post-merge top-up paterni (`78f080e`). |

## Per-Item Detail

Stable IDs `W17-1..W17-6` get Per-Item Detail entries here as each is
pulled. Currently scope skeleton only (W17-0 authoring).

## Exit Criteria (W17-End)

W17 kapanır şu koşullar sağlandığında:

- W17-1..W17-6 kapanır ya da deferral rasyoneli ile W18'ye taşınır.
- W17-1 producer-side parity invariant runtime'da yakalanır
  (`tests/architecture/` veya report-invariants test ailesinde +1 gate).
- W17-2 harness happy-path smoke + cancel-mid-flight +
  reset-during-finalize edge case'leri yeşil; harness'ın kendi smoke
  testi (lifecycle açılıp kapanıyor mu) `make test-local` altında.
- W17-3 davranış paritesi: sandbox-reset thread relocation sonrası
  W13-1 HMAC + W13-12 fail-closed davranışı + W13-13 CAS pattern
  regress etmez; harness altında lock ordering + idempotency yeşil.
- W17-4 byte-identical refactor: heartbeat clarity refactor sonrası
  W17-2 harness'ı tüm edge case'leri yeşil bırakır.
- W17-5 hygiene cleanup: seçilen 3-5 `[CLEANUP]` kalem
  `POST_POC_BACKLOG.md`'de DONE/CLOSED işaretli; ruff clean; arch
  gate'lere yeni regression eklemez.
- `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `active-work/README.md`, ve ilgili lane docs aynı active/closed
  state'i gösterir.
- W17 final bar: `make test-security` ≥220 passed; `tests/architecture/`
  ≥199 passed + W17-1 invariant + W17-2 harness smoke; full-suite skip
  count W16 baseline 9'dan **artmamalı**.
- Close-out hygiene pass: Ruff lint, UI contract sync, markdown
  formatting, doc truth-state alignment, (varsa) yeni regression gate'ler.
- Per user direction (2026-05-18): W17 `week17` branch'inde çalışır;
  sub-iter commits `week17` branch'inde land eder; close-out
  `week17 -> main` PR ile merge edilir; W17 tracker scope kapanışında
  frozen olur (W11-W16 paterni).

## Risk Notes

- **W17-2 harness en büyük belirsizlik** — Playwright mock surface'inin
  ne kadar iş istediği keşfedilmeden bilinmiyor. Eğer harness W17 ortasında
  balon olursa, W17-3/4 W18'e iter ve W17 attribution-parity + hygiene
  ile kapatılır. Scope reduction kararı W17-2 ortasında verilir
  (W16-5 paterni: doc-only commit + deferral rasyonelinin
  `POST_POC_BACKLOG.md`'ye audit trail'i).
- **W17-1 küçük görünüyor** ama W16-3 split'inde "evidence vs stream
  divergence" derin bir contract sorun çıkarsa büyüyebilir; W17-2
  başlamadan W17-1 kapanmalı (sequencing constraint).

## Notes

- Branching policy: tek `week17` branch'i; per-iter feature branch
  açılmaz. Sub-iter commits sıralı `W17-0`, `W17-1`, ... olarak
  `week17`'e push edilir. W17-6 sonrası `week17 -> main` close-out PR.
- W16 tracker
  ([`W16-regression-and-audit-closeout.md`](W16-regression-and-audit-closeout.md))
  W16-7 + `78f080e` post-PR top-up sonrası **frozen reference**;
  W17 boyunca sadece okuma için açılır (W17-3 file path context'i
  için L526-543 spesifik referans).
