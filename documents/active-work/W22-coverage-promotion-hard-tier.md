# W22 — Coverage Promotion Round 3: Hard Tier + Sandbox ADR + Container Hardening Ratchet-Down (Active Work Tracker)

`Last Updated: 2026-05-28 (W22-0 doc-reconcile in-flight 26bb080 opening week22 branch — new W22 active-work tracker per W18-W21 paterni + 10-doc canonical preamble refresh transitioning W21 closed/merged → W22 active + §19 W21 plan header "Previous phase" stamp + §20 W22 plan header doc-open in REFACTOR_OPTIMIZATION.md (W19-0/W20-0/W21-0 paterni mirror) + W21 Pull-Forward Acceptance Bar in POST_POC_BACKLOG.md closed/merged stamp + W22 Roadmap Acceptance Bar "planning" → "active" promotion listing W22-0..W22-N + W21-deferred [FOLLOWUP workspace-trust-stimulus-pass] + [FOLLOWUP sandbox-reset-stale-state-multi-analyze] + W21-4 ADR 0013 §Deferred ratchet-down lane (read_only + tmpfs + custom seccomp) pulled into W22-6 + README phase-pointer arch gate transition W21 → W22 (test_readme_phase_pointer.py tracks_active_w22_status + new W21 close-out merge gate test pinning PR #30 / week21 -> main / 5dc18aa) + test_canonical_preamble_parity.py fingerprint refresh (PR #29 → PR #30, 64a3c3d → 5dc18aa, tracker slot W21 → W22). W21 closed and merged via PR #30 week21 -> main MERGED 2026-05-28 via 5dc18aa; final W21 bar tests/architecture/ 287 passed / make test-security 220 passed / full suite 2104 passed, 9 skipped, 8 deselected. W22 entry signal: coverage_summary.missing_capabilities = [chat] (1 item) at W21-4 anchor eacea0b6690e sha256 5d7c8b974f21e3bf4ad679a41551dd3e7b71d37573f5e7f2b28b87d2ad4a6a84; W22-2 closes [chat] hard tier (1 → 0 missing). Parallel statik analiz şeridi ayrı worktree'de extrace-static branch çalışıyor (kendi W21 referans temizliği yapıyor; bu W22 oturumu ile çakışma yok). Main'e onaysız push/merge yok (user direction 2026-05-28; memory feedback_pr_push_approval standing).)`
`Phase: W22-0 doc-reconcile in-flight 26bb080 — opening week22 branch; W22-0..W22-N sub-iter slate planned (W22-1 chat ADR + W22-2 chat coverage + W22-3 attribution depth + W22-4 sandbox-evasion ADR + W22-5 sandbox canary + W22-6 container hardening ratchet-down + W22-7 activation event spec gap conditional + W22-N close-out)`
`Branch: week22 (per user direction 2026-05-28; W11-W21 paterninden bu sefer ayrılma — sub-iter commits land directly on week22 without per-sub-iter branches; close-out merges via week22 -> main PR PENDING USER APPROVAL)`
`Owner: ekrem`

> **Authored 2026-05-28** as the W22 scope skeleton against `main` HEAD
> `5dc18aa` (W21 close-out PR #30 merge `2026-05-28 14:18:22+03:00`).
> Stable IDs `W22-1..W22-7` are reserved by the iteration plan at
> `POST_POC_BACKLOG.md` W22 Roadmap Acceptance Bar (active after W22-0) +
> the planning roadmap at `documents/active-work/W18-W22-roadmap.md`
> §W22 (lines 267-287) and **assigned at first pull** per the
> W11-W21 precedent
> (`REFACTOR_OPTIMIZATION.md` §15.0 / §16.0 / §17.0 / §18.0 / §19.0).

This is the canonical active work tracker for the W22 Coverage Promotion
Round 3 (hard tier) + Sandbox ADR Draft + Container Hardening
Ratchet-Down window. Items receive stable IDs (`W22-1`, `W22-2`, …)
**at first pull**, not preemptively, per the W11-W21 precedent.

Slim canonical [`REFACTOR_OPTIMIZATION.md §20`](../REFACTOR_OPTIMIZATION.md)
carries the entry-conditions block, goal statement, and the W22
closing-iter context for the W18-W22 multi-iter roadmap. The multi-iter
source-of-truth roadmap is at
[`W18-W22-roadmap.md`](W18-W22-roadmap.md); this tracker is the W22
slice. The W21 frozen tracker
([`W21-coverage-promotion-mid-tier.md`](W21-coverage-promotion-mid-tier.md))
is the template structurally followed here.

## Status (Quick Glance)

- **W22 active on the `week22` branch.** Branch was created from `main`
  @ `5dc18aa` (W21 close-out PR #30 merge `2026-05-28 14:18:22+03:00`)
  per user direction `2026-05-28`. **Single-branch model**: tüm
  sub-iter commits doğrudan `week22` üzerine; sub-iter başına ayrı
  branch açılmaz (W11-W21 paterninden bu sefer ayrılma per user
  direction).
- **Entry gate (met).** W21 close-out PR #30 `week21 -> main` MERGED
  `2026-05-28` via `5dc18aa`; W21 final bar (recorded at W21-N
  `dd24f1e`): `tests/architecture/` **287 passed, 4 deselected**;
  `make test-security` **220 passed**; full suite **2104 passed, 9
  skipped, 8 deselected**.
- **Driving signal (live run, 2026-05-21 + W21-4 re-anchor
  2026-05-28).** Codex live-run validation of `ms-python.python` @
  `992ad028f3df` reports `coverage_summary.missing_capabilities`
  started at `[scm, settings, chat, comments, testing, workspace_trust]`
  (6 items). W20-1/W20-2 promoted `scm` + `settings` (6 → 4). W21-3
  promoted `workspace_trust` (4 → 3). W21-1 promoted `testing` (3 →
  2). W21-2 promoted `comments` (2 → 1). W21-4 container hardening
  baseline did NOT regress (anchor `eacea0b6690e` sha256
  `5d7c8b974f21e3bf4ad679a41551dd3e7b71d37573f5e7f2b28b87d2ad4a6a84` —
  covered/partial/missing 8/9/1 byte-identical with W21-2).
  **W22-2 closes the hard tier** (`chat`); expected post-W22 drop
  1 → 0.
- **Branch model (user direction 2026-05-28).** **Tek branch
  `week22`** — sub-iter commits doğrudan üzerinde; close-out PR
  `week22 -> main` PENDING USER APPROVAL. Paralel statik analiz
  şeridi başka worktree'de `extrace-static` branch'inde çalışıyor
  (kendi W21 referans temizliği yapıyor; bu session ile çakışma yok).
- **Main onayı zorunlu (user direction 2026-05-28).** Main'e push,
  PR oluşturma, merge, branch silme: hepsi user onayı zorunlu.
  Memory entry `feedback_pr_push_approval.md` standing.
- **Acceptance bar carry-forwards from W21.**
  - `[FOLLOWUP workspace-trust-stimulus-pass]` (filed W21-3 `c744c15`
    + `4b0a1ed`) — runtime untrusted → granted transition exercise;
    needs fixture restructuring. Opportunistic W22 pull window (after
    W22-1 ADR Accepted, before W22-2 chat coverage if capacity
    permits).
  - `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` (filed W20-5
    `d163b02`) — multi-analyze second-pass flake. Opportunistic
    close-out window pull; not a sub-iter, not a blocker. Production
    impact LOW (CI uses fresh-per-analyze containers).
  - W21-4 ADR 0013 §Deferred ratchet-down (`read_only` + tmpfs +
    custom seccomp) — pulled into W22 as `W22-6 [GOAL
    container-hardening-ratchet-down]` (closing W21-4 deferred slate
    is part of W22 must-pass per ADR 0013 §Deferred plan).
- **W22-0 in-flight 26bb080.** Doc reconcile + canonical
  preamble refresh across 10 docs (`CLAUDE.md` / `README.md` /
  `AGENTS.md` / `documents/AGENT_CONTEXT.md` /
  `documents/active-work/README.md` / `documents/REFACTOR_STATUS.md`
  / `documents/REFACTOR_OPTIMIZATION.md` anchor map + this tracker +
  `documents/POST_POC_BACKLOG.md` +
  `documents/active-work/W18-W22-roadmap.md`) +
  test_canonical_preamble_parity.py fingerprint refresh + new
  test_readme_phase_pointer_mentions_w21_closeout_merge gate
  pinning PR #30 / week21 -> main / 5dc18aa +
  tracks_active_w21_status → tracks_active_w22_status rename.

## Sub-Iter Scope (Authored 2026-05-28)

| Iter | Status / Theme | Commit ref | Closes which acceptance-bar item? |
|---|---|---|---|
| W22-0 | **in-flight 26bb080** doc-reconcile — `week22` branch open + new W22 active-work tracker (this file) + §19 W21 plan header doc-close ("Previous phase" stamp) + §20 W22 plan header doc-open in `REFACTOR_OPTIMIZATION.md` (W19-0/W20-0/W21-0 paterni mirror) + 10-doc canonical preamble refresh W21 closed/merged → W22 active + W21 Pull-Forward Acceptance Bar in `POST_POC_BACKLOG.md` closed/merged stamp + W22 Roadmap Acceptance Bar "planning" → "active" promotion + README phase-pointer arch gate transition W21→W22 + new W21 close-out fact gate `test_readme_phase_pointer_mentions_w21_closeout_merge` pinning PR #30 / `week21 -> main` / `5dc18aa` + canonical preamble parity test fingerprint refresh (PR #29 → PR #30, `64a3c3d` → `5dc18aa`, tracker slot W21 → W22). | this commit | — (doc-reconcile; no acceptance-bar item) |
| W22-1 | **planned** — `[GOAL taxonomy-chat-policy-adr]` (new) — ADR `documents/adrs/0014-chat-and-language-model-tool-policy.md`. `onChatParticipant` + `onLanguageModelTool:*` local verification strategy. Decision: harness-side stub LM provider vs mock LM endpoint. NO CODE. | — | — |
| W22-2 | **planned** — `[GOAL taxonomy-chat-coverage]` (new) — `_OFFICIAL_CAPABILITY_SUPPORT["chat"]: "missing" → "covered"` at `capabilities.py:95` + mirror in `_GLOBAL_CAPABILITY_SUPPORT:43` (heuristic derives) + `local_chat_participant_controller` + `local_language_model_tool_controller` scenarios in `scenarios.py` + harness `extension.js` + `stimulus_dispatch.js` `ensureChatParticipant`/`ensureLanguageModelTool` markers via reserved OutputChannel route (W19-X Bug B paterni; W21-2 paterni byte-identical) with ephemeral participant default (W19-X HMAC reactivation race lesson) + 4-5 invariant tests at `tests/platform/contracts/test_capability_support_invariants.py` (W21-2 comments template mirror) + dict shape canonical pin update + `test_split_did_not_lose_data_volume` count pin bump 16→17/18 + frozen trigger fixture regen for ms-python.python. Local LM stub provider: harness-side, no external network (depends on W22-1 ADR decision). | depends on W22-1 ADR Accepted | **W22 acceptance #1** (`chat` dropped from `missing_capabilities`) |
| W22-3 | **planned** — `[FOLLOWUP attribution-count-parity-process-events]` + `[FOLLOWUP attribution-count-parity-output-channel]` (new) — Attribution depth ProcessEvent + OutputChannelAppendLine (W17-1 paterni — `build_evidence_bundle` producer-side stamp at `executor/flows/playwright/attribution/links.py` + 4+4=8 invariant test). | — | — |
| W22-4 | **planned** — `[GOAL sandbox-evasion-defense-mvp]` (existing W18 candidate) — ADR draft only `documents/adrs/0015-sandbox-evasion-defense-policy.md`. Anti-analysis pattern taxonomy: webdriver presence checks, timing probes, `navigator.platform` interrogation, mouse trail detection. Implementation deferred to W23+. NO CODE. | — | — |
| W22-5 | **planned** — `[GOAL sandbox-evasion-canary-fixture]` (new) — `tests/security/test_sandbox_evasion_canary.py` — webdriver presence probe + timing probe simulation. `make test-security` 220 → 221. | depends on W22-4 ADR shape | — |
| W22-6 | **planned** — `[GOAL container-hardening-ratchet-down]` (new, W21-4 §Deferred closure) — ADR 0013 §Deferred → §Closed. `docker-compose.yml` `read_only: true` on each service (executor/api/ui) + tmpfs mounts `/tmp` + `/run/extrace` + `/home/executor/.vscode` + `/var/cache/nginx` + `/var/run` + `docker/seccomp.json` custom profile (Docker default + `unshare`/`mount`/`personality` deny; Playwright + Xvfb + VS Code Extension Host compat audit in ADR addendum). `tests/architecture/test_compose_isolation_invariants.py` +8-10 new invariants + new `tests/platform/security/test_seccomp_profile_sanity.py`. Manual smoke (W19+ live-run gate per roadmap): `cat /proc/self/status \| grep -E "^(Cap\|NoNewPrivs\|Seccomp)"`, `mount \| grep "rw,"`, `unshare --net 2>&1 \| grep "Operation not permitted"`. | — | — |
| W22-7 | **planned (conditional)** — `[GOAL activation-event-spec-gap-followup]` (new) — W20-0 crosswalk residual gap implement. Skip case: `[NO-W22-7]` doc-only stamp. | depends on W20-0 crosswalk re-verify at W22-0 or W22-N | — |
| W22-N | **planned** — close-out hygiene + 10-doc canonical preamble W22 active → closed flip + §20 W22 self-stamp + W22 tracker freeze + W22 Roadmap Acceptance Bar audit-trail close + final live-run anchor + PR `week22 -> main` (PENDING USER APPROVAL — user direction 2026-05-28; main approval required). | — | — |

## W22 Acceptance Bar (live-run-driven)

### Must-pass

1. ADR 0014 (chat policy) Accepted + local-only implementation veya
   deferred-with-blocker documented (W22-1, W22-2)
2. ADR 0015 (sandbox-evasion defense) Accepted, implementation W23+
   scope (W22-4)
3. W22-3 attribution parity tests yeşil (8/8)
4. W22-5 sandbox canary fixture green
5. W22-6 container ratchet-down: docker-compose `read_only:true` +
   tmpfs + seccomp her servis aktif; manual smoke pass (mount/Cap
   grep)
6. `coverage_summary.missing_capabilities == 0` live run anchor'da
   (hard tier closure)
7. W19 Hat-1 (`unaccounted_dropout == 0`) holds post-W22
8. W19 Hat-2 (`harness_verification_unconfirmed_present` DROPPED)
   holds post-W22
9. Static suite green (final W22 bar pinned at W22-N self-stamp)

### Expected

1. `tests/architecture/` ~287 → ~310 (W22-0 +1 README phase-pointer
   gate + W22-1 +1 ADR existence + W22-2 +5 chat invariants + W22-3
   +8 attribution parity + W22-4 +1 ADR existence + W22-6 +8-10
   compose ratchet-down)
2. `make test-security` 220 → 222 (W22-5 +1 canary + W22-6 +1
   seccomp sanity)
3. Full suite ~2104 → ~2125+
4. `automation_health.reasons` from 3 down to 1-2 (if
   `skipped_scenarios_present` and `verification_gap_present` are
   closed)

### Stretch

1. `automation_health.status: degraded → healthy`
2. `run_quality: medium → high`
3. `[FOLLOWUP workspace-trust-stimulus-pass]` pulled at W22-N
   opportunistic window
4. `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` pulled at
   W22-N opportunistic window

## Parallel-Branch Coordination

W22 ile eş zamanlı başka worktree'de `extrace-static` branch
çalışıyor (statik analiz şeridi; user info 2026-05-28). O session
kendi worktree'sinde eski W21 referans temizliğini yapıyor — bu W22
oturumu ile çakışma yok. Main'e merge sırası ne olursa olsun, week22
üzerinde planlanan değişiklikler bağımsız hat üzerinden ilerliyor.

### Surface overlap risk matrisi

- **Yüksek risk** — `packages/analysis_planner/` (capabilities.py,
  scenarios.py, event_scenario_index.py, selection.py). W22-2 chat
  coverage burayı edit ediyor. Eğer extrace-static main'e merge
  edilirse ve aynı dosyaları farklı satırlardan edit ettiyse
  3-way merge.
- **Orta risk** — `appcore/contracts/schema_defs/` ve
  `tests/platform/contracts/`. W22-3 attribution depth schema
  field ekliyor.
- **Düşük risk** — `executor/`, `docker/`, `docker-compose.yml`,
  `documents/adrs/`, `tests/security/`, `tests/architecture/test_compose_isolation_invariants.py`.
  W22-4/W22-5/W22-6 hep buralarda.

### Sıralama önerisi (overlap-aware)

Düşük-risk sub-iter'ları önce, yüksek-risk sub-iter'ları sona bırak.
Eğer extrace-static main'e merge edilirse, W22-3/W22-2 öncesi
rebase yap. (Stable ID sırası ≠ execution order; bkz. sub-iter
tablosundaki status sütunu.)

## Plan Source & Related Docs

- Slim canonical:
  [`REFACTOR_OPTIMIZATION.md §20`](../REFACTOR_OPTIMIZATION.md)
- Multi-iter source-of-truth:
  [`W18-W22-roadmap.md`](W18-W22-roadmap.md)
- POST-PoC Backlog W22 Roadmap Acceptance Bar:
  [`../POST_POC_BACKLOG.md`](../POST_POC_BACKLOG.md)
- W21 frozen tracker (template):
  [`W21-coverage-promotion-mid-tier.md`](W21-coverage-promotion-mid-tier.md)
- W21-4 ADR 0013 (W22-6 §Deferred kaynak):
  [`../adrs/0013-container-isolation-baseline.md`](../adrs/0013-container-isolation-baseline.md)
- W17-1 attribution-count-parity (W22-3 paterni):
  commits `8c26d02` + `0a8f59e`

## Sub-Iter Sections

(Each sub-iter section will be added as it is opened — W18/W19/W20/W21
paterni. W22-0 section below as the in-flight commit.)

### W22-0 — Doc reconcile + W22 open

**Status**: in-flight 26bb080.

**Goal**: Open the W22 phase doc-side — flip the 10-doc canonical
preamble from W21 closed/merged to W22 active, transition
REFACTOR_OPTIMIZATION.md §19 W21 plan header to "Previous phase"
and open §20 W22 plan header, create the W22 active-work tracker
(this file), promote the W22 Roadmap Acceptance Bar in
POST_POC_BACKLOG.md from "planning" to "active", update the README
phase-pointer arch gate to track W22 status + add the W21 close-out
merge fact gate, and refresh the canonical preamble parity test
fingerprint to the new most-recent-merge (PR #30 / `5dc18aa`).

**Changes**:

1. **New W22 active-work tracker** — this file at
   `documents/active-work/W22-coverage-promotion-hard-tier.md`. W18-W21
   paterni mirror.

2. **10-doc canonical preamble refresh** — `CLAUDE.md`, `AGENTS.md`,
   `README.md`, `documents/AGENT_CONTEXT.md`,
   `documents/REFACTOR_STATUS.md`,
   `documents/REFACTOR_OPTIMIZATION.md`,
   `documents/POST_POC_BACKLOG.md`,
   `documents/active-work/README.md`,
   `documents/active-work/W18-W22-roadmap.md`, and this tracker.
   "W21 closed synthetically" → "W21 closed and merged via PR #30
   week21 -> main MERGED 2026-05-28 via 5dc18aa" and W22-0
   in-flight stamp.

3. **`documents/REFACTOR_OPTIMIZATION.md` §19** — W21 plan header
   doc-close (W19-0/W20-0/W21-0 paterni mirror — "Previous phase"
   stamp with W21 closed-and-merged narrative + final test bar).

4. **`documents/REFACTOR_OPTIMIZATION.md` §20** — W22 plan header
   doc-open ("Active phase" stamp with W22 sub-iter slate +
   acceptance bar).

5. **`documents/POST_POC_BACKLOG.md`** — W21 Pull-Forward Acceptance
   Bar "closed and merged" stamp + W22 Roadmap Acceptance Bar
   promotion from "planning" → "active" (move out of the
   placeholder section into a Pull-Forward shape with `W22-0..W22-N`
   stable IDs reserved).

6. **`documents/REFACTOR_STATUS.md` Current State** — add W21
   closed-and-merged bullet (PR #30 / `5dc18aa`); mark W22 as the
   Active phase.

7. **`README.md` phase pointer block** — transition from W21 active
   to W22 active narrative + W21 close-out merge fact (PR #30 /
   `week21 -> main` / `5dc18aa`).

8. **`documents/AGENT_CONTEXT.md` Source of Truth** — W21 closed-
   and-merged + W22 active narrative.

9. **`documents/active-work/README.md`** — W21 frozen note + W22
   active pointer.

10. **`documents/active-work/W18-W22-roadmap.md`** — Status block:
    W21 → closed-and-merged via PR #30; W22 → active.

11. **`tests/architecture/test_canonical_preamble_parity.py`** —
    `_EXPECTED_MERGE_FINGERPRINT` `"PR #29"` → `"PR #30"`;
    `_EXPECTED_MERGE_SHA` `"64a3c3d"` → `"5dc18aa"`;
    `_CANONICAL_PREAMBLE_DOCS[9]`
    `"documents/active-work/W21-coverage-promotion-mid-tier.md"` →
    `"documents/active-work/W22-coverage-promotion-hard-tier.md"`.

12. **`tests/architecture/test_readme_phase_pointer.py`** — rename
    `test_readme_phase_pointer_tracks_active_w21_status` →
    `_active_w22_status` + update markers + update tokens (`W22`,
    `active-work/W22-coverage-promotion-hard-tier.md`, `week22`) +
    add new `test_readme_phase_pointer_mentions_w21_closeout_merge`
    pinning `PR #30` / `week21 -> main` / `5dc18aa`.

**Acceptance**: 10 canonical docs carry `PR #30` + `5dc18aa`;
`test_canonical_preamble_parity.py` 3 tests green; new
`test_readme_phase_pointer_mentions_w21_closeout_merge` green;
`test_readme_phase_pointer_tracks_active_w22_status` green; W22 tracker
file exists.

**Test bar delta**: `tests/architecture/` ~287 → ~288 (+1 W21
close-out merge gate).

**Live-run anchor**: deferred to W22-0 self-stamp (or first sub-iter
that warrants a fresh smoke); W22-0 is doc-only so no behavior
regression expected.

(Self-stamp follow-up will replace this commit's `26bb080`
placeholders with the actual SHA after the W22-0 primary commit
lands — W21-0 paterni: primary `8434323` + self-stamp `19bd9c7`.)
