# REFACTOR_OPTIMIZATION

`Last Updated: 2026-06-15`

`Last merged weekly: W22 — closed synthetically on the week22 branch, merged to main via PR #31 week22 -> main 2026-05-28 via 1399f82.`

`Active stream: operator-console-honesty (UI-only console-honesty stream, sequenced ahead of Stream 2 per 2026-06-15 direction) — opened on week24 (off main 8250db0); makes decorative/dead Settings + System controls honest (no backend/DB/detection/executor). Prior stream reliability-self-defense merged to main via PR #35 (week23 -> main, 653d807). Tracker: documents/active-work/W24-operator-console-honesty.md.`

`Sources of truth: documents/REFACTOR_STATUS.md (state) · documents/POST_POC_BACKLOG.md (deferred) · documents/REFACTOR_OPTIMIZATION.md §20 (last weekly plan) · documents/phase.json (weekly pointer + active stream).`

W0-W14 plan document: stabilization + security + post-PoC external-review
integration + W14 acceptance + observability continuation. **Slim canonical**
— full historical content (per-iter rationale, sub-commit narratives, entry/
exit prose) is frozen under dated snapshots. Each closed iter below is one
row with stable ID + landing commit; full context in the snapshot.

- latest full snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-06-15.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-06-15.md)
- previous full snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-14.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-14.md)
- older snapshot:
  [`archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-13.md`](archive/plans/REFACTOR_OPTIMIZATION_full_2026-05-13.md)

Legacy references to retired subsection IDs such as §2.6, §10.7, §11.5,
§11.8-§11.10, and §12.0-§19.4 refer to the
[`2026-06-15` full snapshot](archive/plans/REFACTOR_OPTIMIZATION_full_2026-06-15.md).
This slim file retains only the major section anchors and current pointers.

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
- §18 → W20 Coverage Promotion Round 1: Easy Wins — **closed
  synthetically `2026-05-27` and merged via PR #29 `week20 -> main`
  `64a3c3d`** on the `week20` branch (per user
  direction `2026-05-26`; W11-W19 paterni preserved);
  W20-0..W20-5 sub-iter slate fully delivered (W20-0
  doc-reconcile `66a8a0b` + `5f13757`; W20-1 scm flip `82276cb`
  + `a17e595`; W20-2 settings flip `a4343d2` + `7406588`; W20-3
  coverage matrix contract invariants `d4c03b6` + `2e39230`;
  W20-4 comments+testing readiness DESIGN `05f47f3` + `b409894`;
  W20-5 close-out hygiene `4665d32` primary + `95b0010`
  self-stamp + `d163b02` followup-2 filed
  `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` for W21
  + `ae5b7de` followup-3 10-doc preamble `26bb080`
  placeholder backfill). W20 acceptance LIVE-SATISFIED on fresh
  run `4e92de149802`:
  `coverage_summary.missing_capabilities` 6 → 4 (lost `scm` +
  `settings`); W19 Hat-1 + Hat-2 hold post-W20. Final W20 bar:
  `tests/architecture/` **240 passed**, 4 deselected;
  `make test-security` **220 passed**; full suite **2045 passed,
  9 skipped, 8 deselected**. Frozen tracker:
  [`active-work/W20-coverage-promotion-easy-wins.md`](active-work/W20-coverage-promotion-easy-wins.md).
- §19-§20 → W21-W22 Multi-iter Capability + Coverage Promotion +
  Sandbox Evasion + Chat Policy Roadmap (planning state, authored
  `2026-05-21`; split from the original §18-§20 combined header at
  W20-0 open when W20 promoted to its own §18 active block — same
  paterni as the W19-0 split of §17-§20 into §17 + §18-§20).
  Multi-iter roadmap source-of-truth:
  [`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md).

## §10 — W0-W7 PoC Stabilization Window (closed 2026-04-23)

Closed `2026-04-23`; acceptance bar §10.7 (11/11 green). Full per-iter plan history in the dated archive snapshot.

## §11 — W8-W13 External Review Integration Window (closed 2026-05-13)

Closed W8-W13. Trackers: `active-work/{W8-security,W11-monitor-lifecycle,W12-executor-subpackaging,W13-test-expansion-observability}.md`. Close facts in the Anchor Map above; full plan in the archive snapshot.

## §12 — W14 Codex M-class Acceptance + Observability (closed 2026-05-14, PR #21 `4e03c8d`)

Closed. Tracker: `active-work/W14-codex-acceptance-observability.md`. Full plan in the archive snapshot.

## §13 — W15 Codex U-class Close-Out + UI Bounds + Posture (closed 2026-05-17, merged 2026-05-18 via PR #22 `6161472`)

Closed. Tracker: `active-work/W15-codex-uclass-bounds-posture.md`. Full plan in the archive snapshot.

## §14 — W16 Carry-Over Closeout + Audit Findings + Production Regression (closed 2026-05-18, merged via PR #23 `1b6d43f`)

Closed. Tracker: `active-work/W16-regression-and-audit-closeout.md`. Full plan in the archive snapshot.

## §15 — W17 Carry-Over Closeout + Lifecycle Harness Yatırımı + Hygiene Sweep (closed 2026-05-18, merged via PR #25 `bff565d`)

Closed. Tracker: `active-work/W17-carryover-and-lifecycle-harness.md`. Full plan in the archive snapshot.

## §16 — W18 Heartbeat Refactor (closed 2026-05-21; PR #26 `week18 -> main` `9874e79`)

Closed. Tracker: `active-work/W18-heartbeat-refactor.md`; ADR `adrs/0012-heartbeat-thread-relocation.md`. Full plan in the archive snapshot.

## §17 — W19 Live-Run Kök Neden: Dropout + Harness Verification (closed synthetically 2026-05-26; PR #28 `week19 -> main` `c879603`)

Closed. Tracker: `active-work/W19-live-run-root-cause.md`. Full plan in the archive snapshot.

## §18 — W20 Coverage Promotion Round 1: Easy Wins (closed; merged via PR #29 `week20 -> main` `64a3c3d` 2026-05-26)

Closed. Tracker: `active-work/W20-coverage-promotion-easy-wins.md`. Full plan in the archive snapshot.

## §19 — W21 Coverage Promotion Round 2: Mid Tier (closed and merged 2026-05-28 via PR #30 `week21 -> main` `5dc18aa`; W21-N close-out `dd24f1e`)

Closed. Tracker: `active-work/W21-coverage-promotion-mid-tier.md`. Full plan in the archive snapshot. Sub-iter primaries: W21-0 `8434323`, W21-3 `c744c15`, W21-1 `7e87030`, W21-2 `8948ea6`, W21-4 `16e2224` (+ followup-1 `2f9cba2`).

## §20 — W22 Coverage Promotion Round 3: Hard Tier + Sandbox Evasion ADR + Chat Policy + Container Hardening Ratchet-Down (closed synthetically; merged via PR #31 `week22 -> main` `1399f82` `2026-05-28`)

§20 W22 plan header doc-open at W22-0 26bb080. §19 W21 closed
and merged via PR #30 `week21 -> main` MERGED `2026-05-28` via
`5dc18aa` (W21-N close-out at `dd24f1e`); W22 inherits 1 missing
capability (`chat`) per W21-4 anchor `eacea0b6690e`. **W22 closes
the hard tier** (`chat` policy ADR + implementation) **+ sandbox
evasion ADR draft** (canary fixture + defense ADR) **+ container
hardening ratchet-down** (W21-4 ADR 0013 §Deferred — `read_only` +
tmpfs + custom seccomp profile) **+ attribution depth** for
ProcessEvent + OutputChannelAppendLine (W17-1 paterni).

**Branch model (user direction `2026-05-28`)**: tek branch
`week22` — sub-iter commits doğrudan üzerinde, sub-iter başına
ayrı branch yok (W11-W21 paterninden bu sefer ayrılma). Close-out
PR #31 `week22 -> main` **MERGED** `2026-05-28` via `1399f82`
(memory `feedback_pr_push_approval` standing — onay alındıktan sonra merge edildi).

Active tracker:
[`active-work/W22-coverage-promotion-hard-tier.md`](active-work/W22-coverage-promotion-hard-tier.md)
carries per-iter scope locks, Per-Item Detail evidence, the
baseline + final live-run smoke artefakts, and the W22 Closure
section. Roadmap kaynak gerçek dosyası (W22 sub-iter slate'i +
acceptance gate'leri + critical files + ADR yolları + açık karar
noktaları):

[`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md)

| Iter | Status | Theme | Notes |
|---|---|---|---|
| W22-0 | **closed** (`26bb080` + `ff3fbbd`) doc-reconcile — `week22` branch + new W22 active-work tracker + §19 W21 plan header doc-close ("closed and merged") + §20 W22 plan header doc-open (this section) + 10-doc canonical preamble refresh transitioning W21 → W22 + W21 Pull-Forward Acceptance Bar "closed and merged" stamp + W22 Roadmap Acceptance Bar "planning" → "active" promotion + README phase-pointer arch gate transition W21 → W22 + new W21 close-out fact gate `test_readme_phase_pointer_mentions_w21_closeout_merge` pinning PR #30 / `week21 -> main` / `5dc18aa` + `test_canonical_preamble_parity.py` fingerprint refresh (PR #29 → PR #30, `64a3c3d` → `5dc18aa`, tracker slot W21 → W22) | this commit | — (doc-reconcile; no acceptance-bar item) |
| W22-1 | **closed** `906fcd5` + `d018fe1` | `[GOAL taxonomy-chat-policy-adr]` ADR `documents/adrs/0014-chat-and-language-model-tool-policy.md` (kod-free) | — |
| W22-2 | **closed (static cut)** `ffbb743` + `d9e4558` | `[GOAL taxonomy-chat-coverage]` `chat` her iki track → covered (W21-2 paterni); depends on W22-1 ADR Accepted | — |
| W22-3 | **closed** `cff10d3` + `70dc43a` | `[FOLLOWUP attribution-count-parity-process-events]` + `[FOLLOWUP attribution-count-parity-output-channel]` (W17-1 paterni; 4+4=8 invariant) | — |
| W22-4 | **closed** `9a8ad28` + `ea418a6` | `[GOAL sandbox-evasion-defense-mvp]` ADR `documents/adrs/0015-sandbox-evasion-defense-policy.md` (kod-free; implementation W23+) | — |
| W22-5 | **closed** `a6dd24b` + `1de616b` | `[GOAL sandbox-evasion-canary-fixture]` `tests/security/test_sandbox_evasion_canary.py` | — |
| W22-6 | **DEFERRED TO USER** (Linux) | `[GOAL container-hardening-ratchet-down]` W21-4 ADR 0013 §Deferred → §Closed (read_only + tmpfs + custom seccomp) | — |
| W22-7 | **skipped — `[NO-W22-7]`** | `[GOAL activation-event-spec-gap-followup]` (W20-0 crosswalk residual gap if any; else `[NO-W22-7]` stamp) | — |
| W22-N | **closed** `11595c0` | close-out hygiene + tracker freeze; PR #31 `week22 -> main` MERGED `1399f82` | — |

### §20.0 — Neden ayrı §20 (closed)

§19 W21 coverage promotion round 2 mid-tier kapanış penceresini
kapadı (closed and merged via PR #30 / `5dc18aa` on `2026-05-28`).
§20 hard tier + sandbox + container ratchet-down devamı:

- **§20 — W22**: Coverage promotion round 3 (hard tier:
  `chat` policy ADR + implementation) + attribution depth +
  sandbox-evasion ADR draft + container hardening ratchet-down

§20 W22-0 close-out'ta §20 active block'a promote edildi (this
commit). W19-0/W20-0/W21-0 paterni mirror — §17 split at W19-0,
§18 split at W20-0, §19 split at W21-0, §20 split here.

### §20.1 — Driving Signal (live run, 2026-05-21)

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
([summary.py:401-418](../executor/flows/playwright/health/summary.py)).

W20-5 final live-run anchor `4e92de149802` (sha256
`3804a5b5...4394c`) confirmed `missing_capabilities` 6 → 4 post
W20-1/W20-2 promotion. **W21 closes mid tier** (`testing`,
`comments`, `workspace_trust`); **W22 closes hard tier** (`chat`).

### §20.2 — Üç katmanlı capability modeli

Plan üç ayrı "capability" katmanını tespit etti — sırasıyla aksiyon
gerektiriyor (A ve B) ya da spec uyumlu (C):

- **Katman A — Activation events**: `OFFICIAL_EVENT_REGISTRY` 29
  entry
  ([test_registry_split_regression.py:103](../tests/platform/contracts/test_registry_split_regression.py)).
  4 shallow trigger (`onView`, `onWebviewPanel` restore semantics,
  `onAuthenticationRequest`, `onChatParticipant`). W20-0 spec
  crosswalk araştırması ile gerçek gap doğrulanır.
- **Katman B — Capability taxonomy**: 18 bucket
  ([capabilities.py:8-27](../packages/analysis_planner/capabilities.py)).
  W20-5 final state: Heuristic 14/4 covered/missing, official 14/4
  covered/missing (scm + settings promoted; chat/comments/testing/
  workspace_trust still missing both tracks). W21 + W22 close
  remaining.
- **Katman C — Manifest capability**: `ExtensionCapabilitiesSchema`
  ([catalog.py:12](../appcore/contracts/schema_defs/catalog.py))
  `untrusted_*` + `virtual_*` — VSCode-spec uyumlu, **gap yok**.

### §20.3 — Driving Plan dosyası

Tüm sub-iter slate'i, acceptance kriterleri (must-pass / expected /
stretch), live-run gate'leri, critical file paths, ADR yolları, ve
açık karar noktaları tracker dosyasında:

[`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md)

Plan dosyası 3 review turundan geçti:

1. Initial Codex live-run validation (live rapor doğrulaması + capability taxonomy gap teyidi)
2. GPT round-1 (üç hat ayrımı, W19-1 xfail/RED pattern, harness verification ayrı boyut)
3. GPT round-2/3 (W20'nin 13 sub-iter'a patlaması, W20→W22 ayırma, `healthy/degraded/inconclusive` enum doğrulaması, ADR yolu `documents/adrs/` doğrulaması, `OFFICIAL_EVENT_REGISTRY` 29 sayısı, `onWebviewPanel` restore semantics, manifest source-of-truth, `confirmation_source` schema impact, `workspace_trust` defer fallback, chat-conditional W22 acceptance)

W19-0 doc-reconcile sub-iter'inde §17 W19 active block §17-§20'den
ayrıldı (`72712bd` + `086d7a5`). W20-0 doc-reconcile sub-iter'inde
§18 W20 active block §18-§20 combined'dan ayrıldı (`66a8a0b` +
`5f13757`). W21-0 doc-reconcile sub-iter'inde 26bb080 §19 W21
active block §19-§20 combined'dan ayrıldı. §20 W22 entry'si W22
açıldığında self-stamped olur (W14/W15/W16/W17/W18/W19/W20/W21
paterni).

### §20.4 — Exit Criteria summary

W19 exit kriteri §17.4'te + W20 exit kriteri §18.4'te + W21 exit
kriteri §19.4'te (yukarıda). W22 için tam exit criteria
[`active-work/W18-W22-roadmap.md`](active-work/W18-W22-roadmap.md)
"Sub-Iter Scope" bölümlerinde + "Live-Run Acceptance Gate"
bölümünde. Özet:

- **W22 exit**: chat ADR Accepted + path implemented **or**
  deferred-with-blocker; sandbox ADR + canary GREEN; her iki
  track missing == 0 (chat implemented path seçildiyse).
