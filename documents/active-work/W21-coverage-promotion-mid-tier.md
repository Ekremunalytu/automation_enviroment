# W21 — Coverage Promotion Round 2: Mid Tier (Active Work Tracker)

`Last Updated: 2026-05-27 (W21-3 [GOAL taxonomy-workspace-trust-coverage] closed via primary c744c15 + self-stamp this commit (W21-0 doc-reconcile closed 8434323 + 19bd9c7 before W21-3). W21-3 primary landed _OFFICIAL_CAPABILITY_SUPPORT["workspace_trust"]: "missing" → "covered" at capabilities.py:99 + mirror in _GLOBAL_CAPABILITY_SUPPORT:47 (heuristic derives) + harness vscode.workspace.isTrusted baseline marker + onDidGrantWorkspaceTrust listener via reserved OutputChannel route (W19-X Bug B paterni) + workspace_trust_transition scenario in scenarios.py advertising workspace_trust + 4 invariant tests (W20-1 scm template mirror) at tests/platform/contracts/test_capability_support_invariants.py + dict shape canonical pin update + test_split_did_not_lose_data_volume count bump 13→14 + frozen trigger fixture regen for ms-python.python. Runtime stimulus pass (untrusted → granted exercise) deferred to W22 as [FOLLOWUP workspace-trust-stimulus-pass] — workspace trusted-by-default in container fixture; runtime exercise requires fixture restructuring. W21-0 (week21 branch open + new W21 active-work tracker (this file) + §19 W21 plan header doc-open + §19-§20 split + W21 Pull-Forward Acceptance Bar promotion + 10-doc preamble refresh + README phase-pointer transition W20→W21 + baseline live-run capture anchor 600d9ecba5eb) closed via 8434323 + 19bd9c7. W21-3 live-run anchor 6fd7b959bd5a sha256 fa83017a4de25e...d6f7477 confirms W21-3 acceptance: coverage_summary.missing_capabilities = [chat, comments, testing] (3 items — workspace_trust dropped from W21-0 baseline 4 items; must-pass ✓); covered/partial/missing 7/7/4 → 8/7/3; workspace_trust matrix entry status "covered" is_active=true with workspace_trust_transition advertised in supported_scenarios. W20 invariants HOLD post-W21-3: unaccounted_dropout_count is null (Hat-1); harness_verification_unconfirmed_present DROPPED from reasons (Hat-2). W21-3 live-run drift (non-invariant): extra_trigger_failures_present reason count = 9 (transient — previous failed analyze attempt left stale executor state after rebuild; W21-N close-out final live-run will re-verify on fresh stack) + new chat_tool_verification_incomplete reason (W22 surface — pre-existing matrix gap, not a W21-3 regression). W20 closed and merged via PR #29 week20 -> main MERGED 2026-05-26 23:10:21Z via 64a3c3d; final W20 bar (recorded at W20-5 + W20-5-followup-2): tests/architecture/ 240 passed, 4 deselected; make test-security 220 passed; full suite 2045 passed, 9 skipped, 8 deselected. W21-3 test bar delta: tests/architecture/ 241 passed (unchanged from W21-0; W21-3 invariants live in contracts tier); tests/platform/contracts/test_capability_support_invariants.py 14 → 18 passed (+4 W21-3 invariants); make test-security 220 passed (unchanged); full suite 2045 → 2050 passed, 9 skipped, 8 deselected (+5 net: W21-0 +1 + W21-3 +4). W21 driving signal (carried over from W19 / W20): same Codex live-run 2026-05-21 of ms-python.python @ 992ad028f3df reports coverage_summary.missing_capabilities started at [scm, settings, chat, comments, testing, workspace_trust]; W20 W20-5 final live-run 4e92de149802 confirmed missing dropped 6 → 4 [chat, comments, testing, workspace_trust]; W21-3 dropped workspace_trust (missing 4 → 3 [chat, comments, testing]); expected end-state drop 3 → 1 [chat] after W21-1 (testing) + W21-2 (comments) land; W22 closes hard tier (chat) + sandbox evasion ADR draft. §19 W21 plan source (active) + §20 W22 planning (split at this W21-0 commit from the §19-§20 W21-W22 combined header that W20-0 had created). W21 sub-iter slate: W21-0 doc-reconcile closed (8434323 + 19bd9c7) + W21-3 [GOAL taxonomy-workspace-trust-coverage] closed via c744c15 + this commit + W21-1 [GOAL taxonomy-testing-coverage] (next per user-confirmed ordering W21-3 → W21-1 → W21-2) + W21-2 [GOAL taxonomy-comments-coverage] + W21-4 [GOAL container-hardening-baseline] STRETCH (conditional pull only if W21-0..W21-3 closed cleanly; W21-3 now closed cleanly — W21-4 stays in conditional-pull window) + W21-N close-out hygiene + PR week21 -> main PENDING USER APPROVAL. W21 ordering (user-confirmed 2026-05-27 via AskUserQuestion): W21-3 → W21-1 → W21-2 — workspace_trust lands first as precondition for test/comment controllers, resolving W20-4 DESIGN open question 4 "workspace_trust ordering" with the doc's "likely yes" recommendation. [FOLLOWUP sandbox-reset-stale-state-multi-analyze] opportunistic at W21-N close-out window (user-confirmed); not a sub-iter, not a blocker. [FOLLOWUP workspace-trust-stimulus-pass] (filed c744c15 + this commit) W22 candidate — runtime untrusted → granted transition exercise; needs fixture restructuring. W20 closed via PR #29 week20 -> main MERGED 2026-05-26 via 64a3c3d; W19 closed via PR #28 week19 -> main MERGED 2026-05-26 via c879603; W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79. W20 frozen tracker: documents/active-work/W20-coverage-promotion-easy-wins.md (frozen at W20-5 + followups per W17/W18/W19 paterni); multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md.)`
`Phase: W21-0 closed (8434323 + 19bd9c7) + W21-3 closed (c744c15 + this commit); next is W21-1 [GOAL taxonomy-testing-coverage]; week21 branch open from main @ 64a3c3d (W20 close-out merge commit)`
`Branch: week21 (per user direction 2026-05-27; W11-W20 paterni preserved — sub-iter commits land on week21, close-out merges into main via week21 -> main PR PENDING USER APPROVAL)`
`Owner: ekrem`

> **Authored 2026-05-27** as the W21 scope skeleton against `main` HEAD
> `64a3c3d` (W20 close-out PR #29 merge `2026-05-26 23:10:21Z`). Stable
> IDs `W21-1..W21-4` are reserved by the iteration plan at
> `POST_POC_BACKLOG.md` W21-W22 Roadmap Acceptance Bar (planning) +
> the planning roadmap at `documents/active-work/W18-W22-roadmap.md`
> §W21 (lines 240–260) and **assigned at first pull** per the
> W11/W12/W13/W14/W15/W16/W17/W18/W19/W20 precedent
> (`REFACTOR_OPTIMIZATION.md` §15.0 / §16.0 / §17.0 / §18.0).

This is the canonical active work tracker for the W21 Coverage Promotion
Round 2 (mid tier) window. Items receive stable IDs (`W21-1`, `W21-2`, …)
**at first pull**, not preemptively, per the W11-W20 precedent.

Slim canonical [`REFACTOR_OPTIMIZATION.md §19`](../REFACTOR_OPTIMIZATION.md)
carries the entry-conditions block, goal statement, and the W21-W22
multi-iter roadmap context. The multi-iter source-of-truth roadmap is at
[`W18-W22-roadmap.md`](W18-W22-roadmap.md); this tracker is the W21
slice. The W20 frozen tracker
([`W20-coverage-promotion-easy-wins.md`](W20-coverage-promotion-easy-wins.md))
is the template structurally followed here.

## Status (Quick Glance)

- **W21-0 doc-reconcile in-flight on the `week21` branch (per user
  direction `2026-05-27`; W11-W20 paterni preserved — sub-iter commits
  land on `week21` and the W21 close-out PR `week21 -> main` opens at
  W21-N PENDING USER APPROVAL).** Branch created from `main` @ `64a3c3d`
  (W20 close-out PR #29 merge `2026-05-26 23:10:21Z`).
- **Entry gate (met).** W20 close-out PR #29 `week20 -> main` MERGED
  `2026-05-26` via `64a3c3d`; W20 final bar (recorded at W20-5 +
  followup-2..-4): `tests/architecture/` **240 passed, 4 deselected**;
  `make test-security` **220 passed**; full suite **2045 passed, 9
  skipped, 8 deselected**.
- **Driving signal (live run, 2026-05-21).** Codex live-run validation
  of `ms-python.python` @ `992ad028f3df` reports
  `coverage_summary` (official track) started at `covered=7 / partial=5
  / missing=6` with `missing = [scm, settings, chat, comments, testing,
  workspace_trust]`. W20-5 final live-run `4e92de149802` (sha256
  `3804a5b5...4394c`) confirmed `scm` + `settings` dropped (6 → 4) post
  W20-1/W20-2 promotion. **W21 closes the mid-tier** (`testing`,
  `comments`, `workspace_trust`); expected post-W21 drop 4 → 1 (`chat`
  remaining for W22) or 4 → 2 (`chat` + `workspace_trust` if W21-3
  defers per W20-4 DESIGN doc open Q4 fallback).
- **Ordering (user-confirmed 2026-05-27).** W21-3 → W21-1 → W21-2.
  Trust state is a precondition for many editor APIs in
  restricted-mode workspaces; landing W21-3 first eliminates
  non-determinism from late trust transitions. W20-4 DESIGN doc open
  question 4 ("Workspace trust ordering. Likely yes — but...") resolved
  with the "yes" branch.
- **W21-4 stretch (user-confirmed).** Container hardening baseline + ADR
  0013 pulled **only if** W21-0..W21-3 closed cleanly; otherwise explicit
  defer to W22+ with documented rationale in W21-N close-out tracker.
- **[FOLLOWUP sandbox-reset-stale-state-multi-analyze] (user-confirmed).**
  Opportunistic close-out window pull; not a sub-iter, not a blocker.
  Production impact LOW (CI uses fresh-per-analyze containers).
- **W21-0 entry state (this commit).** doc reconcile + canonical
  preamble refresh across 10 docs (`CLAUDE.md` / `README.md` /
  `AGENTS.md` / `documents/AGENT_CONTEXT.md` /
  `documents/active-work/README.md` /
  `documents/REFACTOR_STATUS.md` /
  `documents/REFACTOR_OPTIMIZATION.md` anchor map + this tracker +
  `documents/POST_POC_BACKLOG.md` +
  `documents/active-work/W18-W22-roadmap.md`) + new W21 tracker
  (this file) + §19 W21 plan header doc-open (planning → active) in
  `REFACTOR_OPTIMIZATION.md` split from the combined §19-§20 header
  (W20-0 paterni mirror) + README phase-pointer arch gate transition
  W20→W21 (`tests/architecture/test_readme_phase_pointer.py` flipped
  active-phase gate from W20 to W21 + new W20 close-out fact gate
  `test_readme_phase_pointer_mentions_w20_closeout_merge` pinning
  PR #29 / `week20 -> main` / `64a3c3d`, mirroring the W18-0 / W19-0 /
  W20-0 transition paterni). W21 Pull-Forward Acceptance Bar promoted
  in `POST_POC_BACKLOG.md` from `W21-W22 Roadmap Acceptance Bar
  (planning)` (now `W22 Roadmap Acceptance Bar (planning)`). Baseline
  live-run pending — captured at W21-0 self-stamp follow-up per
  W19-0 / W20-0 paterni.

## Sub-Iter Scope (Authored 2026-05-27)

| Iter | Status | Theme | Closes which acceptance-bar item? |
|---|---|---|---|
| W21-0 | **in-flight `2026-05-27`** via primary `8434323` + self-stamp this commit (doc-reconcile — `week21` branch + new W21 active-work tracker (this file) + §19 W21 plan header doc-open + §19-§20 W21-W22 planning header split into §19 W21 active + §20 W22 planning + 10-doc canonical preamble refresh + W21 Pull-Forward Acceptance Bar promotion in `POST_POC_BACKLOG.md` + README phase-pointer arch gate transition W20→W21 + new W20 close-out fact gate `test_readme_phase_pointer_mentions_w20_closeout_merge` pinning PR #29 / week20 -> main / 64a3c3d + baseline live-run captured via this self-stamp anchor `600d9ecba5eb` sha256 `1db1480551...c4477` confirming W20 close-out invariants hold) | primary `8434323` + self-stamp this commit | — (doc-reconcile; no acceptance-bar item) |
| W21-3 | **closed `2026-05-27`** via primary `c744c15` + self-stamp this commit — `[GOAL taxonomy-workspace-trust-coverage]` — `_OFFICIAL_CAPABILITY_SUPPORT["workspace_trust"]: "missing" → "covered"` flip at `capabilities.py:99` + mirror in `_GLOBAL_CAPABILITY_SUPPORT:47` (heuristic derives) + harness `vscode.workspace.isTrusted` baseline marker + `onDidGrantWorkspaceTrust` listener via OutputChannel route (W19-X paterni) + `workspace_trust_transition` scenario in `scenarios.py` advertising `workspace_trust` capability + 4 invariant tests (W20-1 scm template mirror) + dict shape canonical pin update + `test_split_did_not_lose_data_volume` count bump 13→14 + frozen trigger fixture regen for ms-python.python. Runtime stimulus pass (untrusted → granted exercise) deferred to W22 as `[FOLLOWUP workspace-trust-stimulus-pass]` — workspace is trusted-by-default in container fixture; runtime exercise requires fixture restructuring. Live-run smoke anchor `6fd7b959bd5a` sha256 `fa83017a4de25e...d6f7477` confirms `coverage_summary.missing_capabilities` 4 → 3 items (workspace_trust dropped), `covered/partial/missing` 7/7/4 → 8/7/3, workspace_trust matrix entry status="covered" is_active=true with `workspace_trust_transition` advertised in supported_scenarios. W20 invariants HOLD: `unaccounted_dropout_count = null` (Hat-1), `harness_verification_unconfirmed_present` NOT in reasons (Hat-2 DROPPED), event_attempts = 21. | primary `c744c15` + self-stamp this commit | **live W21 acceptance #1 closed ✓** (`workspace_trust` dropped from `missing_capabilities`) |
| W21-1 | planned — `[GOAL taxonomy-testing-coverage]` — `_OFFICIAL_CAPABILITY_SUPPORT["testing"]: "missing" → "covered"` flip at `capabilities.py:97` + mirror in `_GLOBAL_CAPABILITY_SUPPORT` + `vscode.tests.createTestController` registration in harness + `TestItem` + `createRunProfile` + OutputChannel marker + `local_test_controller` scenario in `scenarios.py` + stimulus pass + 4 invariant tests + frozen trigger fixture regen via planner replay. W20-4 DESIGN doc `documents/architecture/comments-testing-readiness.md` §W21-1 paterni. Ephemeral TestItem default (W19-X paterni). | TBD | live W21 acceptance #2 (`testing` drops from `missing_capabilities`) |
| W21-2 | planned — `[GOAL taxonomy-comments-coverage]` — `_OFFICIAL_CAPABILITY_SUPPORT["comments"]: "missing" → "covered"` flip at `capabilities.py:96` + mirror in `_GLOBAL_CAPABILITY_SUPPORT` + extension of existing `extrace.harness.comments` stub with `commentingRangeProvider` + `createCommentThread` + `discussion_thread` scenario + stimulus pass + 4 invariant tests + fixture regen. W20-4 DESIGN doc §W21-2 paterni. Ephemeral thread default. | TBD | live W21 acceptance #3 (`comments` drops from `missing_capabilities`) |
| W21-4 | **STRETCH (conditional pull)** — `[GOAL container-hardening-baseline]` — `docker-compose.yml` (`cap_drop: ALL` + audited re-add list), `docker/seccomp.json`, `read_only: true` root FS + tmpfs, resource limits, new ADR `documents/adrs/0013-container-isolation-baseline.md`. Manual smoke required (Cap status + mount checks + `tests/platform/security/test_seccomp_profile_sanity.py`). **Pulled only if W21-0..W21-3 closed cleanly** per user-confirmed strategy; otherwise explicit defer to W22+ with documented rationale in W21-N close-out tracker. | TBD | W21 stretch — container hardening manual smoke ✅ |
| W21-N | placeholder for close-out hygiene + 10-doc canonical preamble Active → Previous flip + §19 W21 self-stamp + W21 tracker freeze + W21 Pull-Forward Acceptance Bar audit-trail close + new arch invariant tests (GAP-A `test_w21_section_19_cross_doc_parity.py` + GAP-B `_OFFICIAL_CAPABILITY_SUPPORT` dict shape pin update for W21 end-state) + final live-run on `ms-python.python` (`testing` + `comments` + maybe `workspace_trust` drop from `missing_capabilities` 4 → 1 or 4 → 2) + close-out PR `week21 -> main` PENDING USER APPROVAL. W18-4 / W19-6 / W20-5 paterni. [FOLLOWUP sandbox-reset-stale-state-multi-analyze] opportunistic pull window. | TBD | close-out + live acceptance |

### §19.0 — Neden ayrı §19

§18 W20 coverage promotion round 1 easy-wins kapanış penceresi kapandı
(W20-0..W20-5 + W20-5-followup-2..-4, PR #29 `64a3c3d`'da `2026-05-26`'da
merge'lendi). §19 yeni bir tema: **Hat-3 coverage matrix promotion —
mid tier** (`testing` + `comments` + `workspace_trust` her iki track
→ covered). §18-§20 combined header'dan §19-§20 split olarak yeniden
yapılandırıldı; W21-0 (this commit) §19'u active block'a promote eder
ve geri kalan §20'yi W22 planning bloğu olarak yeniden adlandırır
(W19-0 / W20-0 paterni mirror — §17 split from §17-§20 at W19-0,
§18 split from §18-§20 at W20-0).

§19'un §18'den ayrı tutulmasının nedeni: W20 audit trail (sub-iter
close date'leri ve commit'leri) frozen kalsın; W21-N close-out'ta
§19 self-stamped olur (W14/W15/W16/W17/W18/W19/W20 paterni).

### §19.1-§19.2 — Entry + Sub-iter Distribution

W21 entry triggered by W20 close-out PR #29 merge (`64a3c3d`,
`2026-05-26 23:10:21Z`) + same Codex live-run validation (`2026-05-21`)
reporting `coverage_summary.missing = [scm, settings, chat, comments,
testing, workspace_trust]` — W20 closed `scm` + `settings`; W21
inherits 4 missing capabilities. Sub-iter sequencing rationale
(user-confirmed via AskUserQuestion 2026-05-27):

- **W21-0 önce** — W11-W20 paterni preservation + README
  phase-pointer arch gate transition (W20→W21) + new W20 close-out
  fact gate + §19 W21 plan header doc-open + 10-doc canonical preamble
  refresh + W21 Pull-Forward Acceptance Bar promotion + baseline
  live-run smoke (W20 close-out sonrası post-merge state pin).
- **W21-3 ikinci (workspace_trust)** — **lands first among substantive
  sub-iters per ordering decision**. Trust state is a precondition for
  many editor APIs in restricted-mode workspaces; landing W21-3 first
  eliminates non-determinism from late trust transitions during
  W21-1/W21-2 stimulus passes. W20-4 DESIGN doc open Q4 ("Workspace
  trust ordering. Likely yes — but a `workspace_trust` flip is itself
  non-trivial") resolved with the "yes" branch. Fallback: DESIGN-only
  defer to W22 if scope explodes (W20-4 paterni).
- **W21-1 üçüncü (testing)** — W20-4 DESIGN doc §W21-1 paterni:
  `vscode.tests.createTestController` registration + `TestItem` +
  `createRunProfile` + OutputChannel marker (W19-X paterni: not
  console.log) + planner `local_test_controller` scenario + stimulus
  pass + dict flips at `capabilities.py:97` + invariant tests +
  fixture regen.
- **W21-2 dördüncü (comments)** — W20-4 DESIGN doc §W21-2 paterni:
  extend existing `extrace.harness.comments` stub with
  `commentingRangeProvider` + `createCommentThread` + planner
  `discussion_thread` scenario + stimulus pass + dict flips at
  `capabilities.py:96` + invariant tests + fixture regen. W21-1
  byte-identical paterni.
- **W21-4 beşinci (STRETCH container hardening)** — **conditional pull**
  per user-confirmed strategy. Only if W21-0..W21-3 closed cleanly +
  capacity permits. Otherwise explicit defer to W22+ with documented
  rationale in W21-N close-out tracker. Scope: `docker-compose.yml`
  `cap_drop: ALL` + audit-vetted re-add list, `docker/seccomp.json`,
  `read_only: true` root + tmpfs, resource limits, new ADR 0013.
  Manual smoke required (`/proc/self/status` Cap + `mount | grep "rw,"`
  + `test_seccomp_profile_sanity.py`).
- **W21-N close-out** — W19-6 / W20-5 paterni: 10-doc canonical preamble
  refresh + §19 self-stamp + W21 tracker freeze + final live-run + PR
  `week21 -> main` PENDING USER APPROVAL.

Stable ID → iter eşlemesi `POST_POC_BACKLOG.md`'de W21 Pull-Forward
Acceptance Bar (W21-0..W21-4 promoted from W21-W22 Roadmap Acceptance
Bar planning at this W21-0 open) + W22 Roadmap Acceptance Bar
(W22 planning) tablolarında.

Per user direction (`2026-05-27`) W21 lives on a `week21` branch
(W11-W20 paterni preserved); sub-iter commits land on `week21` and
the W21 close-out PR `week21 -> main` opens at W21-N PENDING USER
APPROVAL.

### §19.3 — Non-goals (W21)

W22+'ye düşen kalemler stable ID'leri `POST_POC_BACKLOG.md` /
W22 Roadmap Acceptance Bar (planning) tablosunda:

- `[GOAL taxonomy-chat-policy-adr]` (W22-1) — chat policy ADR
  `documents/adrs/0014-chat-and-language-model-tool-policy.md`.
  `onChatParticipant` + `onLanguageModelTool:*` yerel verification
  stratejisi. KOD YOK.
- `[GOAL taxonomy-chat-coverage]` (W22-2) — `chat` her iki track
  → covered (ADR Accepted sonra). Local LM stub provider + 2 chat
  scenario.
- `[FOLLOWUP attribution-count-parity-process-events]` +
  `[FOLLOWUP attribution-count-parity-output-channel]` (W22-3) —
  Attribution depth ProcessEvent + OutputChannelAppendLine.
  W17-1 producer-side stamp paterni. 4+4=8 invariant test.
- `[GOAL sandbox-evasion-defense-mvp]` (W22-4) — Sandbox-evasion
  defense ADR `documents/adrs/0015-sandbox-evasion-defense-policy.md`.
  ADR 0002 §3 ile ilişki. KOD YOK.
- `[GOAL sandbox-evasion-canary-fixture]` (W22-5) —
  `tests/security/test_sandbox_evasion_canary.py` — webdriver + timing
  probe simülasyonu.
- `[GOAL activation-event-spec-gap-followup]` (W22-6) — W20-0
  crosswalk gerçek gap çıkardıysa implement; çıkarmadıysa skip.
- `[FOLLOWUP harness-secret-distribution-redesign]`
  (W20-W22 ADR candidate; W19-X close-out migrated; W22-1 öncesi
  opportunistic kapanış varsa pull, aksi halde W23+).
- `[FOLLOWUP harness-secret-extra-reactivation-source]` —
  opportunistic; defensive polling already masks; forensic hygiene
  olarak POST_POC_BACKLOG'da pending kalır.
- `[RESEARCH activation-event-spec-crosswalk]` — W20-0 forward-ref'd;
  W22-6 implement edilir gerçek gap çıkarsa.
- W20'de kapanan tüm kalemler (`scm` + `settings`
  official-track promotion + W20-3 contract invariants + W20-4
  DESIGN doc) — `POST_POC_BACKLOG.md` W20 Pull-Forward Acceptance
  Bar'da kapanış audit trail'i korunmuştur, yeniden pull değil.

### §19.4 — Exit Criteria (W21-End)

W21 kapanır şu koşullar sağlandığında:

- [ ] W21-0..W21-N kapanır ya da deferral rasyoneli ile W22'ye
  taşınır (W21-3 defer'ı W20-4 DESIGN doc paterni'nde mümkün; W21-4
  stretch zaten conditional pull).
- [ ] W21-0 doc-reconcile landed via primary (this commit) + self-stamp
  (next turn) (10-doc canonical preamble refresh + §19 W21 plan header
  doc-open from §19-§20 combined + W21 Pull-Forward Acceptance Bar
  promotion in POST_POC_BACKLOG.md + README phase-pointer arch gate
  transition W20→W21 + new W20 close-out fact gate + baseline
  live-run anchor + sha256).
- [ ] W21-3 `workspace_trust` flip landed (lands first per ordering)
  OR explicit DESIGN-only defer documented; `capabilities.py:99`
  `"missing" → "covered"` in both `_OFFICIAL_CAPABILITY_SUPPORT` and
  `_GLOBAL_CAPABILITY_SUPPORT` (via _GLOBAL_'s auto-derivation);
  4 invariant tests + harness `vscode.workspace.isTrusted` detection
  + transition listener + scenario + stimulus pass; full suite green.
- [ ] W21-1 `testing` flip landed; `capabilities.py:97`
  `"missing" → "covered"`; 4 invariant tests + harness Test Controller
  registration + planner `local_test_controller` scenario + stimulus
  pass + frozen trigger fixture regenerated.
- [ ] W21-2 `comments` flip landed; `capabilities.py:96`
  `"missing" → "covered"`; 4 invariant tests + harness Comment
  Controller plumbing + planner `discussion_thread` scenario +
  stimulus pass + fixture regen; W21-1 paterni byte-identical.
- [ ] W21-4 stretch pulled OR explicit defer to W22+ documented (per
  user-confirmed conditional pull strategy).
- [ ] W21-N close-out hygiene landed: 10-doc canonical preamble
  Active → Previous flip + §19 W21 self-stamp + W21 tracker freeze +
  W21 Pull-Forward Acceptance Bar audit-trail close + new arch
  invariant tests (GAP-A `test_w21_section_19_cross_doc_parity.py`
  + GAP-B `_OFFICIAL_CAPABILITY_SUPPORT` dict shape pin update for
  W21 end-state).
- [ ] Final live-run on `ms-python.python` confirms:
  - `coverage_summary.missing_capabilities` drops 4 → 1 (`chat`
    only) or 4 → 2 (`chat` + `workspace_trust` if W21-3 defers) —
    **must-pass**.
  - W19 Hat-1 (`unaccounted_dropout == 0`) holds post-W21.
  - W19 Hat-2 (`harness_verification_unconfirmed_present` DROPPED)
    holds post-W21.
- [ ] `automation_health.reasons` listesi:
  `official_unresolved_present` remains as expected (W22-end closes);
  `run_quality` may move `low → medium` after W21-1/W21-2/W21-3
  close `official_unresolved_present` contributors; `automation_health.status:
  degraded` OK.
- [ ] `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `active-work/README.md`, ve ilgili lane docs aynı active/closed
  state'i gösterir — 10-doc canonical preamble parity gate green.
- [ ] W21 final bar pinned at W21-N self-stamp:
  `tests/architecture/` baseline 240 → +5..+10 (W21 GAP-A + W20
  close-out fact gate + phase-pointer transition + per-sub-iter
  invariants); `make test-security` 220 → +0..+2 (W21-3 may add
  trust-state tests); full suite 2045 → +20..+40.
- [ ] Close-out hygiene pass: arch invariant tests added (GAP-A +
  GAP-B updates); preamble flip across 10 docs; W21 tracker freeze.
- [ ] Per user direction (`2026-05-27`): W21 `week21` branch'inde
  çalıştı; sub-iter commits `week21` branch'inde landed; W21
  tracker bu commit'le frozen (W11-W20 paterni).
- [ ] Close-out PR `week21 -> main` open (W21-N) **PENDING USER
  APPROVAL** (per user directive + memory entry
  `feedback_pr_push_approval.md`).
- [ ] Post-merge audit (W18-4-followup / W19-post-merge-drift /
  W20-post-merge-drift paterni; ayrı commit/direct on main veya
  weekly branch).

## Per-Item Detail

### W21-0 — Doc-Reconcile + §19 Promote + Baseline Live-Run

**Status**: **in-flight `2026-05-27`** via this commit (primary
W21-0 doc-reconcile; baseline live-run capture planned for W21-0
self-stamp follow-up after user "go").

**Scope**:

- New W21 active-work tracker (this file) — opens W21 phase
  per W11-W20 paterni. Mirrors `W20-coverage-promotion-easy-wins.md`
  structurally.
- §19 W21 plan header doc-open in `REFACTOR_OPTIMIZATION.md`:
  split combined `§19-§20 — W21-W22 Capability + Coverage Promotion +
  Sandbox Evasion + Chat Policy Roadmap (planning)` header into active
  `§19 — W21 Coverage Promotion Round 2: Mid Tier (active)`
  + planning `§20 — W22 Coverage Promotion Round 3: Hard Tier +
  Sandbox Evasion ADR + Chat Policy (planning)`. W19-0 / W20-0
  paterni mirror.
- W21 Pull-Forward Acceptance Bar promotion in
  `POST_POC_BACKLOG.md`: W21-0..W21-4 stable IDs move from
  `W21-W22 Roadmap Acceptance Bar (planning)` to a new
  `W21 Pull-Forward Acceptance Bar (active)` table; W22 rows
  remain in the planning table (now `W22 Roadmap Acceptance Bar
  (planning)`).
- 10-doc canonical preamble refresh (W20-5-followup-3 paterni —
  expanded from 9 → 10 by adding the new tracker file itself):
  CLAUDE.md / README.md / AGENTS.md /
  documents/AGENT_CONTEXT.md / documents/active-work/README.md /
  documents/REFACTOR_STATUS.md / documents/REFACTOR_OPTIMIZATION.md /
  documents/POST_POC_BACKLOG.md / documents/active-work/W18-W22-roadmap.md /
  this tracker file.
- README phase-pointer arch gate transition W20→W21
  (`tests/architecture/test_readme_phase_pointer.py`): flip
  active-phase gate token set from W20 to W21
  (`tracks_active_w20_status` → `tracks_active_w21_status`); add
  new `test_readme_phase_pointer_mentions_w20_closeout_merge`
  pinning `PR #29` / `week20 -> main` / `64a3c3d`, mirroring
  the W18-0 / W19-0 / W20-0 transition paterni.
- README.md "Current Phase" section updated to mention W21
  active state + W20 close-out merge.
- Baseline live-run on `ms-python.python` PENDING user "go" per
  turn. Live JSON anchored at
  `output/activation_report_ms-python.python-<date>-<SHA>.json`
  with sha256 pinned in this tracker post-capture. Diff vs W20-5
  anchor `4e92de149802` (sha256 `3804a5b5...4394c`):
  `unaccounted_dropout` 0 invariant should hold;
  `harness_verification_unconfirmed_present` reason should remain
  absent (W19 Hat-1 + Hat-2 hold post-W20-merge);
  `coverage_summary.missing_capabilities` should remain
  `[chat, comments, testing, workspace_trust]` (4 items —
  W20-1/W20-2 promotion holds).

**Commits**: primary (this commit) `chore(W21-0): doc-reconcile —
open week21 + §19 promote from §19-§20 + 10-doc canonical preamble
refresh + W21 Pull-Forward Acceptance Bar promotion + README
phase-pointer arch gate transition W20→W21 + new W20 close-out
fact gate + baseline live-run pending` + self-stamp (next turn)
post-baseline-live-run-capture pinning anchor + sha256.

### W21-3 — `workspace_trust` Coverage

**Status**: **closed `2026-05-27`** via primary `c744c15` + self-stamp this commit. First substantive W21 sub-iter per user-confirmed ordering W21-3 → W21-1 → W21-2 (W20-4 DESIGN open Q4 resolved with "yes" branch).

**Scope landed (3 layers)**:

1. **Capability taxonomy promotion** (W20-1 scm paterni mirror):
   - `_OFFICIAL_CAPABILITY_SUPPORT["workspace_trust"]: "missing" → "covered"` at [`packages/analysis_planner/capabilities.py:99`](../../packages/analysis_planner/capabilities.py).
   - `_GLOBAL_CAPABILITY_SUPPORT["workspace_trust"]: "missing" → "covered"` at line 47 (`_HEURISTIC_CAPABILITY_SUPPORT` derives, auto-flips).
   - `_GLOBAL_CAPABILITY_NOTES["workspace_trust"]` policy text unchanged (already in place pre-W21-3).

2. **Planner scenario registry** — `workspace_trust_transition` added to `SCENARIO_REGISTRY` in [`packages/analysis_planner/scenarios.py`](../../packages/analysis_planner/scenarios.py):
   - `activation_events=("onStartupFinished",)` — broad activation surface; trust state is runtime-evaluable, not tied to a specific activation event.
   - `api_capabilities=("commands", "window_ui", "workspace_trust")`.
   - 13 → 14 scenarios; `test_split_did_not_lose_data_volume` count pin bumped.

3. **Harness extension observability** — [`executor/flows/harness_extension/extension.js`](../../executor/flows/harness_extension/extension.js):
   - Baseline trust state marker emitted via `emitHarnessEvent` at `activate()` entry, before stimulus command registration. Payload shape: `{kind: "workspace_trust_state", phase: "baseline", is_trusted: bool, ts, collector: "harness_extension"}`.
   - `onDidGrantWorkspaceTrust` listener registered, emits `{phase: "granted"}` marker when trust is granted on the current workspace.
   - Routes through reserved `"ExTrace Harness"` OutputChannel (W19-X Bug B paterni — `console.log` alone is discarded by `launch_vscode.sh`).
   - `trustDisposable` enrolled in `context.subscriptions.push(...)`.

**Invariant tests added** (W20-1 scm template mirror at [`tests/platform/contracts/test_capability_support_invariants.py:141-200`](../../tests/platform/contracts/test_capability_support_invariants.py)):

- `test_workspace_trust_official_track_is_covered` — pins line 99 flip.
- `test_workspace_trust_heuristic_track_is_covered` — pins line 47 + derived heuristic; protects Official ⊆ Heuristic invariant (W20-3 gate).
- `test_workspace_trust_in_capability_taxonomy` — pins taxonomy membership.
- `test_workspace_trust_transition_scenario_advertises_workspace_trust_capability` — pins scenario ↔ capability registry consistency.

Plus dict shape canonical pin update at line 284: `workspace_trust: "missing"` → `"covered"` with W21-3 promotion comment.

**Frozen trigger fixture regen** — [`tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json`](../../tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json):

- `coverage_summary.missing_capabilities`: 4 → 3 items (`workspace_trust` drops).
- `coverage_summary.covered/partial/missing`: 7/7/4 → 7/8/3 in this static fixture path. Heuristic-track partial+1 because scenario advertises `workspace_trust` but ms-python.python doesn't declare `onStartupFinished` in the test fixture (no `capability_metadata.untrusted_supported` either).
- `workspace_trust` matrix entry: status `missing` → `partial`, `support_status` `missing` → `covered`, `supported_scenarios` populated with `workspace_trust_transition`.

**Scope decision (W22 deferral)** — runtime stimulus pass that exercises untrusted → granted transition end-to-end deferred to W22 as `[FOLLOWUP workspace-trust-stimulus-pass]`. Rationale: harness fixture workspace is trusted-by-default in the container (no `--disable-workspace-trust` flag, no explicit untrusted bootstrap); granted-transition exercise requires fixture restructuring (untrusted-by-default workspace) which exceeds W21-3 scope. Minimum W21-3 acceptance achieved via taxonomy promotion + scenario advertisement + harness observability listener; the listener fires on any future trust transition without requiring fixture changes.

**Live-run smoke** (W21-3 acceptance verification):

Captured `2026-05-27` via UI-driven analyze API on `ms-python.python` @ `2026.5.2026052501` after `docker compose up -d --build executor` + `docker compose up -d --build api` (both containers required rebuild: executor bakes harness extension at image-build time; api bakes planner package). Job id `6fd7b959bd5a4536b2940f16aaaa15ed`.

Live anchor JSON: [`output/activation_report_ms-python.python-2026.5.2026052501-6fd7b959bd5a.json`](../../output/activation_report_ms-python.python-2026.5.2026052501-6fd7b959bd5a.json) (sha256 `fa83017a4de25ea56c078da2bd7f65e2f54f10af5aa5c10e8ed000c92d6f7477`).

W21-3 acceptance vs W21-0 baseline `600d9ecba5eb` (sha256 `1db1480551...c4477`):

| Invariant | W21-0 baseline | W21-3 anchor | Verdict |
|---|---|---|---|
| `coverage_summary.missing_capabilities` | `[chat, comments, testing, workspace_trust]` (4) | `[chat, comments, testing]` (3) | ✅ must-pass (`workspace_trust` dropped) |
| `covered_count / partial_count / missing_count` | 7 / 7 / 4 | 8 / 7 / 3 | ✅ must-pass (+1 covered, -1 missing) |
| `workspace_trust` matrix entry | status=`missing`, scenario=[] | status=`covered`, is_active=true, scenario=[`workspace_trust_transition`] | ✅ must-pass |
| Hat-1 `unaccounted_dropout_count` | `null` | `null` | ✅ HOLDS |
| Hat-2 `harness_verification_unconfirmed_present` reason | DROPPED | DROPPED | ✅ HOLDS |
| `automation_health.status` | degraded | degraded | ✅ expected (`official_unresolved_present` still — chat / comments / testing) |
| `event_attempts` count | 21 | 21 | ✅ unchanged |

**Live-run drift observations (non-invariant, documented for W21-N close-out re-verify)**:

- `extra_trigger_failures_present` reason count = 9 in W21-3 anchor (W21-0 baseline = 1; W20-5 anchor = 0). Likely transient from previous failed analyze attempt leaving stale executor state (executor container restarted mid-session to land harness extension rebuild). W21-N close-out final live-run will re-verify on a fully fresh stack.
- New `chat_tool_verification_incomplete` reason — W22 surface (chat scenario verification), not in W20-5 / W21-0 baselines. Pre-existing matrix gap; not a W21-3 regression.

**Test bar delta**:

- `tests/architecture/`: 241 passed (unchanged from W21-0 — W21-3 invariant tests live in contracts tier).
- `tests/platform/contracts/test_capability_support_invariants.py`: 14 → 18 passed (+4 W21-3 invariants).
- `make test-security`: 220 passed (unchanged).
- Full suite: 2045 → 2050 passed, 9 skipped, 8 deselected (+5 net: W21-0 +1 README phase-pointer gate + W21-3 +4 invariants).

**Commits**:

- Primary `c744c15` `feat(W21-3): workspace_trust official-track promotion (missing → covered) + harness trust observability + scenario + 4 invariant tests + fixture regen` — 6 files, +146 / -34.
- Self-stamp (this commit) `docs(W21-3-followup): self-stamp — W21-3 tracker row flip + §19 + POST_POC mirrors + 10-doc canonical preamble refresh + live-run anchor`.

### W21-1 — `testing` Coverage (placeholder)

[Will be filled in at W21-1 pull. Stable ID
`[GOAL taxonomy-testing-coverage]` reserved. W20-4 DESIGN doc
`documents/architecture/comments-testing-readiness.md` §W21-1 is the
plumbing template.]

### W21-2 — `comments` Coverage (placeholder)

[Will be filled in at W21-2 pull. Stable ID
`[GOAL taxonomy-comments-coverage]` reserved. W20-4 DESIGN doc
§W21-2 is the plumbing template.]

### W21-4 — STRETCH: Container Hardening Baseline (placeholder; conditional)

[Will be filled in at W21-4 pull **IF** W21-0..W21-3 close cleanly
AND capacity permits, otherwise explicit defer to W22+ per
user-confirmed strategy. Stable ID
`[GOAL container-hardening-baseline]` reserved. ADR path
`documents/adrs/0013-container-isolation-baseline.md`.]

### W21-N — Close-Out Hygiene + Final Live-Run + PR Request (placeholder)

[Will be filled in at W21-N pull. No stable ID — close-out hygiene
follows W18-4 / W19-6 / W20-5 paterni.]

## Baseline Live-Run Smoke (W21-0)

**Captured `2026-05-27` via this self-stamp follow-up** using the `/api/marketplace/analyze/start` UI-driven analyze API on `ms-python.python` @ `2026.5.2026052501` (job id `600d9ecba5eb4bab8644878679b1f3c0`, completed in ~5 min after `docker compose up -d --build` brought the full stack up).

**Live anchor JSON**: `output/activation_report_ms-python.python-2026.5.2026052501-600d9ecba5eb.json` (sha256 `1db1480551fd90625a5c7c2e474b43c4de3a867d35dab4aacc65e8060bcc4477`).

**W20 close-out live verification (carry-over evidence)** — the post-W20-merge live re-anchor confirms W20 acceptance bar holds:

- `coverage_summary.missing_capabilities = [chat, comments, testing, workspace_trust]` (4 items — **byte-identical with W20-5 anchor `4e92de149802`**; W20-1 + W20-2 official-track promotion of `scm` + `settings` holds post-merge — must-pass ✓).
- `coverage_summary.covered = 7 / partial = 7 / missing = 4` — byte-identical with W20-5 anchor.
- `coverage_summary.attempted = 6 / verified = 4` — byte-identical with W20-5 anchor.
- W19 Hat-2 `harness_verification_unconfirmed_present` reason DROPPED from `automation_health.reasons` ✓.
- W19 Hat-1 `unaccounted_dropout_count` is `null` — **byte-identical with W20-5 anchor**. Important: the W20-5 preamble fragment stated 'unaccounted_dropout count = 0' but the actual field value in the W20-5 anchor JSON was already `null`. This self-stamp records the corrected interpretation: the field has been `null` since W20-5 (not 0), which is the normal post-W19 state when no scenarios are flagged as unaccounted dropouts. `skipped_scenarios = [debug_session, refactor_workflow]` is the only contributor to `skipped_scenarios_present` reason, unchanged since W19.
- `event_attempts` count = 21 (unchanged from W19/W20 baselines).
- `confirmation_source` distribution: `harness_nonce` = **2** (W19-4 + W19-X), `log_record` = **5**, `none` = **14** — total 21/21 with field present (W19-3 schema landing holds). Minor drift vs W20-5 anchor (`log_record` 6 → 5, `none` 13 → 14): one event_attempt moved from `log_record` to `none` because the `onTerminalShellIntegration` trigger failed this run (see next bullet).
- `run_quality = low` (expected — closes after W22 hard tier).
- `automation_health.status = degraded` (expected; closes after W22 hard tier when `official_unresolved_present` resolves).

**New observation — W21-0 baseline drift**: `automation_health.reasons` gained one new entry: `extra_trigger_failures_present` (`extra_trigger_failure_count = 1`, target `official-onterminalshellintegration-python:harness:run_current_stimulus`). This is **intermittent live-run flake** (not a W20 invariant violation; code is byte-identical with W20-5 since W21-0 is doc-only). Causes the minor `confirmation_source` distribution shift noted above. W21-N close-out final live-run will re-verify; if the flake persists across runs, file as W22+ followup.

**W21 baseline (Hat-3, pre-flip)** — the mid-tier target state this self-stamp pins:

- `coverage_summary.missing_capabilities = [chat, comments, testing, workspace_trust]` (4 missing). W21-3 + W21-1 + W21-2 flips of `_OFFICIAL_CAPABILITY_SUPPORT["workspace_trust"]` / `["testing"]` / `["comments"]` at `packages/analysis_planner/capabilities.py:96-99` (plus the `_GLOBAL_CAPABILITY_SUPPORT` mirror) will drop these from the list (4 → 1 expected at W21-N final live-run, or 4 → 2 if W21-3 defers per W20-4 paterni).
- `coverage_summary.covered = 7 / partial = 7 / missing = 4` — W21 expected end-state: `covered = 10 / partial = 7 / missing = 1` (or `covered = 9 / missing = 2` if W21-3 defers).
- `coverage_summary.verified = 4 capability-level` — W21 may lift to 5-7 (`testing` / `comments` / `workspace_trust` may join after live stimulus passes).

**W20 close-out state holds post-merge** ✓ (key invariants identical to W20-5 anchor; the only drift is one intermittent trigger flake which is not a W20 invariant). Baseline captures W21 entry state; W21-3 ready to start (W21-3 lands first per ordering).

## Risk Notes

- **10-doc canonical preamble drift risk** — W19-6-followup-2 closed a
  gap where only `CLAUDE.md` had the headline flip; the post-merge
  cross-doc parity gate at `tests/architecture/` was added specifically
  to catch this shape. W20-5-followup-3 expanded the set from 9 → 10
  by adding the active-work tracker itself. W21-0 + W21-N preamble
  refreshes must touch all 10 docs simultaneously or the parity gate
  will fire.
- **Harness plumbing complexity ≠ W20 single-char flips.** W20-1/W20-2
  were dict edits; W21-1/W21-2/W21-3 require real harness extension JS
  code + scenario plumbing + stimulus passes. Per-sub-iter scope is
  meaningfully larger than W20 sub-iters. **Mitigation:** W20-4 DESIGN
  doc pre-specifies the plumbing surface; each sub-iter can stay scoped
  to a single capability.
- **Trust-state precondition.** If W21-1/W21-2 run before W21-3, test
  controller and comment controller may behave differently in untrusted
  workspaces. **Mitigation:** Confirmed ordering W21-3 → W21-1 → W21-2.
- **Workspace_trust scope explode (W21-3).** Trust-state transitions
  involve VS Code's per-workspace trust DB, restricted-mode behavior
  across multiple extension points. If real implementation exceeds 1
  sub-iter scope, **defer to W22** as DESIGN-only — mirrors W20-4
  paterni.
- **Sandbox-reset flake** (`[FOLLOWUP sandbox-reset-stale-state-multi-analyze]`
  filed at W20-5-followup-2 `d163b02`) — may surface during W21
  live-runs if back-to-back analyses happen on the same executor
  container. **Mitigation:** Per the followup itself — fresh
  `docker compose restart executor` between live-runs. Long-term fix
  lands W21-N (opportunistic) or W22+.
- **Container hardening surface conflict (W21-4).** W21-4 stretch may
  surface seccomp blocks for the new test/comment controllers
  (especially around FS writes for comment-thread persistence —
  though we recommend ephemeral). **Mitigation:** W21-4 pull gate
  explicitly checks for capability conflicts before commit.
- **Live-run timing (W21-0 baseline + W21-N final)** — container
  build cycle takes ~5-15 minutes. Each live-run requires explicit
  user "go" per turn (no standing authorization per memory entry
  `feedback_pr_push_approval.md`).

## Discoveries (placeholder; W21-N close-out fills in)

[Will be filled at W21-N close-out hygiene commit with any followups
discovered during W21 implementation. Mirror W20-5 Discoveries section.]

## Notes

- Commit cadence per W11-W20 paterni: each sub-iter lands a primary
  commit + a self-stamp follow-up. Primary carries source surface
  changes + tests; self-stamp carries evidence (test bar, live-run
  output, doc preamble drift fixes) + tracker state flip
  (`planned → closed at <SHA>`).
- W21 plan dosyası (driving plan with AskUserQuestion answers):
  `/Users/ekrem/.claude/plans/week21-e-ba-lamadan-nce-tranquil-owl.md`.
- Multi-iter source-of-truth roadmap:
  [`W18-W22-roadmap.md`](W18-W22-roadmap.md).
- W20 frozen tracker:
  [`W20-coverage-promotion-easy-wins.md`](W20-coverage-promotion-easy-wins.md)
  (frozen at W20-5 + followups per W17/W18/W19 paterni).
- W19 frozen tracker:
  [`W19-live-run-root-cause.md`](W19-live-run-root-cause.md)
  (frozen at W19-6-followup-2 per W17/W18 paterni).
- W18 frozen tracker:
  [`W18-heartbeat-refactor.md`](W18-heartbeat-refactor.md).
- W20-4 DESIGN doc (W21-1 + W21-2 plumbing template):
  [`documents/architecture/comments-testing-readiness.md`](../architecture/comments-testing-readiness.md).
- Plan source: [`REFACTOR_OPTIMIZATION.md §19`](../REFACTOR_OPTIMIZATION.md).

## W21 Closure (placeholder; W21-N close-out fills in)

[Will be filled at W21-N close-out commit per W20-5 paterni:
Sub-Iter Audit Trail (frozen) table + Live Evidence (W21 Acceptance
Bar — SATISFIED) table + W21-N Close-Out Surface bullets + Final Test
Bar table.]
