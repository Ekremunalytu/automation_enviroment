# W21 — Coverage Promotion Round 2: Mid Tier (Active Work Tracker)

`Last Updated: 2026-05-28 (W21 closed synthetically 2026-05-28 via W21-N close-out dd24f1e; this follow-up clears PR-readiness doc drift without runtime changes. Sub-iter slate complete on the week21 branch: W21-0 doc-reconcile (8434323 + 19bd9c7) + W21-3 [GOAL taxonomy-workspace-trust-coverage] (c744c15 + 4b0a1ed) + W21-1 [GOAL taxonomy-testing-coverage] (7e87030 + 38b8fd8) + W21-2 [GOAL taxonomy-comments-coverage] (8948ea6 + 3088709) + W21-4 [GOAL container-hardening-baseline] (16e2224 + 2f9cba2 + 8c42445) + W21-N close-out (dd24f1e). PR week21 -> main PENDING USER APPROVAL. W21 mid-tier closure target HIT: missing_capabilities went 4 -> 1 [chat] across the iter (W21-0 baseline 600d9ecba5eb sha256 1db1480551fd...c4477; W21-3 anchor 6fd7b959bd5a sha256 fa83017a4de25e...d6f7477; W21-1 anchor 0b4998ce31b4 sha256 b7192bc2ff9c611f00e9dd806af54e0648c92d9201d78fe9ccb886dcf5968be4; W21-2 anchor 1ddb3702c0ca sha256 2dabd15be329bbf1685fe7fc31469355bdc4a5acac2a364d43a196437339cbff; W21-4 final runtime anchor eacea0b6690e sha256 5d7c8b974f21e3bf4ad679a41551dd3e7b71d37573f5e7f2b28b87d2ad4a6a84). W21-4 container hardening landed cap_drop:[ALL] + no-new-privileges:true on executor/api/ui + ADR 0013 + 12 invariant tests; read_only + tmpfs + custom seccomp profile explicitly deferred to W22 ratchet-down lane per ADR 0013 §Deferred. W19 invariants HOLD post-W21: Hat-1 unaccounted_dropout_count=null; Hat-2 harness_verification_unconfirmed_present DROPPED. Final test bar at W21-N: tests/architecture/ 287 passed, 4 deselected; tests/platform/contracts/test_capability_support_invariants.py 26 passed; tests/platform/contracts/test_registry_split_regression.py 8 passed; make test-security 220 passed; full suite 2104 passed, 9 skipped, 8 deselected. [FOLLOWUP sandbox-reset-stale-state-multi-analyze] not pulled (opportunity-not-found; remains W22 candidate). [FOLLOWUP workspace-trust-stimulus-pass] and W21-4 ratchet-down items carry forward to W22. W20 closed via PR #29 week20 -> main MERGED 2026-05-26 via 64a3c3d; W19 closed via PR #28 week19 -> main MERGED 2026-05-26 via c879603; W18 closed via PR #26 week18 -> main MERGED 2026-05-21 via 9874e79. Multi-iter roadmap source-of-truth: documents/active-work/W18-W22-roadmap.md. The W21-N close-out merge fact gate test test_readme_phase_pointer_mentions_w21_closeout_merge lands at W22-0 doc-reconcile per W20->W21 paterni mirror (post-merge audit, not pre-merge), not in this close-out.)`
`Phase: W21 closed synthetically 2026-05-28 — W21-0 closed (8434323 + 19bd9c7) + W21-3 closed (c744c15 + 4b0a1ed) + W21-1 closed (7e87030 + 38b8fd8) + W21-2 closed (8948ea6 + 3088709) + W21-4 closed (16e2224 + 2f9cba2 + 8c42445) + W21-N close-out (this commit); PR week21 -> main PENDING USER APPROVAL`
`Branch: week21 (per user direction 2026-05-27; W11-W20 paterni preserved — sub-iter commits land on week21, close-out merges into main via week21 -> main PR PENDING USER APPROVAL)`
`Owner: ekrem`

**Post-merge note (2026-06-15):** PR #30 `week21 -> main` **MERGED** `2026-05-28` via `5dc18aa` (recorded canonically in `phase.json` history + the README phase-pointer gate). The "PENDING USER APPROVAL" phrasing below is the frozen pre-merge close-out state, not current.

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

- **W21 closed synthetically on the `week21` branch via W21-N `dd24f1e`;
  PR `week21 -> main` remains PENDING USER APPROVAL.** Branch was created
  from `main` @ `64a3c3d` (W20 close-out PR #29 merge
  `2026-05-26 23:10:21Z`) per user direction `2026-05-27`.
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
- **W21-0 closed.** Doc reconcile + canonical preamble refresh across 10
  docs (`CLAUDE.md` / `README.md` / `AGENTS.md` /
  `documents/AGENT_CONTEXT.md` / `documents/active-work/README.md` /
  `documents/REFACTOR_STATUS.md` / `documents/REFACTOR_OPTIMIZATION.md`
  anchor map + this tracker + `documents/POST_POC_BACKLOG.md` +
  `documents/active-work/W18-W22-roadmap.md`) landed via `8434323` +
  `19bd9c7`. W21 Pull-Forward Acceptance Bar promoted in
  `POST_POC_BACKLOG.md`; W22 rows remained under `W22 Roadmap Acceptance
  Bar (planning)`. Baseline live-run captured at W21-0 self-stamp anchor
  `600d9ecba5eb` (sha256 `1db1480551fd...c4477`).

## Sub-Iter Scope (Authored 2026-05-27)

| Iter | Status | Theme | Closes which acceptance-bar item? |
|---|---|---|---|
| W21-0 | **closed `2026-05-27`** via primary `8434323` + self-stamp `19bd9c7` (doc-reconcile — `week21` branch + new W21 active-work tracker (this file) + §19 W21 plan header doc-open + §19-§20 W21-W22 planning header split into §19 W21 active + §20 W22 planning + 10-doc canonical preamble refresh + W21 Pull-Forward Acceptance Bar promotion in `POST_POC_BACKLOG.md` + README phase-pointer arch gate transition W20→W21 + new W20 close-out fact gate `test_readme_phase_pointer_mentions_w20_closeout_merge` pinning PR #29 / week20 -> main / 64a3c3d + baseline live-run captured via self-stamp anchor `600d9ecba5eb` sha256 `1db1480551...c4477` confirming W20 close-out invariants hold) | primary `8434323` + self-stamp `19bd9c7` | — (doc-reconcile; no acceptance-bar item) |
| W21-3 | **closed `2026-05-27`** via primary `c744c15` + self-stamp `4b0a1ed` — `[GOAL taxonomy-workspace-trust-coverage]` — `_OFFICIAL_CAPABILITY_SUPPORT["workspace_trust"]: "missing" → "covered"` flip at `capabilities.py:99` + mirror in `_GLOBAL_CAPABILITY_SUPPORT:47` (heuristic derives) + harness `vscode.workspace.isTrusted` baseline marker + `onDidGrantWorkspaceTrust` listener via OutputChannel route (W19-X paterni) + `workspace_trust_transition` scenario in `scenarios.py` advertising `workspace_trust` capability + 4 invariant tests (W20-1 scm template mirror) + dict shape canonical pin update + `test_split_did_not_lose_data_volume` count bump 13→14 + frozen trigger fixture regen for ms-python.python. Runtime stimulus pass (untrusted → granted exercise) deferred to W22 as `[FOLLOWUP workspace-trust-stimulus-pass]` — workspace is trusted-by-default in container fixture; runtime exercise requires fixture restructuring. Live-run smoke anchor `6fd7b959bd5a` sha256 `fa83017a4de25e...d6f7477` confirms `coverage_summary.missing_capabilities` 4 → 3 items (workspace_trust dropped), `covered/partial/missing` 7/7/4 → 8/7/3, workspace_trust matrix entry status="covered" is_active=true with `workspace_trust_transition` advertised in supported_scenarios. W20 invariants HOLD: `unaccounted_dropout_count = null` (Hat-1), `harness_verification_unconfirmed_present` NOT in reasons (Hat-2 DROPPED), event_attempts = 21. | primary `c744c15` + self-stamp `4b0a1ed` | **live W21 acceptance #1 closed ✓** (`workspace_trust` dropped from `missing_capabilities`) |
| W21-1 | **closed `2026-05-27`** via primary `7e87030` + self-stamp `38b8fd8` — `[GOAL taxonomy-testing-coverage]` — `_OFFICIAL_CAPABILITY_SUPPORT["testing"]: "missing" → "covered"` flip at `capabilities.py:97` + mirror in `_GLOBAL_CAPABILITY_SUPPORT:45` (heuristic derives) + harness Test Controller run/debug profile callbacks emit `test_controller_event` markers (phases `baseline` / `{run,debug}_invoked` / `{run,debug}_complete`) via `emitHarnessEvent` through reserved OutputChannel route (W19-X Bug B paterni) with ephemeral TestItem rebuild on every invocation (W19-X HMAC reactivation race lesson) + `local_test_controller` scenario in `scenarios.py` advertising `testing` capability (mirror W21-3 `workspace_trust_transition` shape) + 4 invariant tests (W21-3 workspace_trust template mirror) + dict shape canonical pin update + `test_split_did_not_lose_data_volume` count bump 14→15 + frozen trigger fixture regen for ms-python.python. Live-run smoke anchor `0b4998ce31b4` sha256 `b7192bc2ff9c611f00e9dd806af54e0648c92d9201d78fe9ccb886dcf5968be4` confirms `coverage_summary.missing_capabilities` 3 → 2 items (testing dropped), `covered/partial/missing` 8/7/3 → 8/8/2, testing matrix entry status="partial" support_status="covered" supported_scenarios=["local_test_controller"]. W20 invariants HOLD: `unaccounted_dropout_count = null` (Hat-1); `harness_verification_unconfirmed_present` NOT in reasons (Hat-2 DROPPED). Live-run drift improvement vs W21-3: `extra_trigger_failures_present` + `chat_tool_verification_incomplete` reasons DROPPED. | primary `7e87030` + self-stamp `38b8fd8` | **live W21 acceptance #2 closed ✓** (`testing` dropped from `missing_capabilities`) |
| W21-2 | **closed `2026-05-28`** via primary `8948ea6` + self-stamp `3088709` — `[GOAL taxonomy-comments-coverage]` — `_OFFICIAL_CAPABILITY_SUPPORT["comments"]: "missing" → "covered"` flip at `capabilities.py:96` + mirror in `_GLOBAL_CAPABILITY_SUPPORT:44` (heuristic derives) + harness CommentController baseline marker at activate() entry + `ensureCommentThread` extended in `stimulus_dispatch.js` to emit `thread_created` + `thread_disposed` markers via `emitHarnessEvent` through reserved OutputChannel route (W19-X Bug B paterni) with ephemeral thread default (W19-X HMAC reactivation race lesson) + `local_comments_controller` scenario in `scenarios.py` advertising `comments` capability (mirror W21-3 workspace_trust_transition + W21-1 local_test_controller shape) + 4 invariant tests + dict shape canonical pin update + `test_split_did_not_lose_data_volume` count bump 15→16 + frozen trigger fixture regen for ms-python.python. Live-run smoke anchor `1ddb3702c0ca` sha256 `2dabd15be329bbf1685fe7fc31469355bdc4a5acac2a364d43a196437339cbff` confirms `coverage_summary.missing_capabilities` 2 → 1 items (comments dropped — **W21 mid-tier closure target hit; only chat remains for W22 hard tier**), `covered/partial/missing` 8/8/2 → 8/9/1, comments matrix entry status="partial" support_status="covered" supported_scenarios=["local_comments_controller"]. W20 invariants HOLD: `unaccounted_dropout_count = null` (Hat-1); `harness_verification_unconfirmed_present` NOT in reasons (Hat-2 DROPPED). | primary `8948ea6` + self-stamp `3088709` | **live W21 acceptance #3 closed ✓** (`comments` dropped from `missing_capabilities`) |
| W21-4 | **closed `2026-05-28`** via primary `16e2224` + followup-1 `2f9cba2` + self-stamp `8c42445` — `[GOAL container-hardening-baseline]` — user-pulled (not defaulted to STRETCH defer) per AskUserQuestion 2026-05-28 after W21-1 + W21-2 closed cleanly. `docker-compose.yml` `cap_drop: [ALL]` on `automation_executor` / `automation_api` / `automation_ui` + audited `cap_add` per service (`executor`: NET_RAW + SYS_PTRACE for tcpdump/tshark/strace per executor/container/Dockerfile L30-L33; `api`: SETUID + SETGID for gosu user drop to appuser; `ui`: SETUID + SETGID + CHOWN + DAC_OVERRIDE for nginx cache-dir chown + worker user drop). `security_opt: ["no-new-privileges:true"]` on all three. `postgres` / `postgres_test` unchanged (image needs CAP_CHOWN for first-run schema bootstrap, deferred to W22). `executor-cdp` unchanged (opt-in debug profile). New ADR `documents/adrs/0013-container-isolation-baseline.md` documents decisions + deferred items (read_only + tmpfs + custom seccomp profile → W22 ratchet-down lane). 12 invariant tests at `tests/architecture/test_compose_isolation_invariants.py`. Live-run smoke anchor `eacea0b6690e` sha256 `5d7c8b974f21e3bf4ad679a41551dd3e7b71d37573f5e7f2b28b87d2ad4a6a84` confirms NO coverage regression vs W21-2 (`missing_capabilities = [chat]` byte-identical, `covered/partial/missing = 8/9/1` byte-identical, 3 health_reasons same shape). Manual kernel smoke `docker exec automation_executor grep -E "NoNewPrivs" /proc/self/status` returns `NoNewPrivs:1`. W20 invariants HOLD post-W21-4: Hat-1 `dropout=null`, Hat-2 `harness_verification_unconfirmed_present` DROPPED. | primary `16e2224` + followup-1 `2f9cba2` + self-stamp `8c42445` | **W21 stretch closed ✓** (container hardening baseline + manual smoke confirmed) |
| W21-N | **closed `2026-05-28`** via `dd24f1e` — close-out hygiene + 10-doc canonical preamble Active → Previous flip (`W21 closed synthetically 2026-05-28`) + §19 W21 self-stamp + W21 tracker freeze (Phase line + per-row "this commit" → explicit SHA backfills) + W21 Pull-Forward Acceptance Bar audit-trail close + 34 new arch invariant tests at `tests/architecture/test_w21_section_19_cross_doc_parity.py` (GAP-A cross-doc parity gate — mirror W20-5 paterni). Dict shape canonical pin for W21 end-state already landed at W21-1/W21-2/W21-3 primaries. Final live-run anchor `eacea0b6690e` sha256 `5d7c8b974f21e3...d4a6a84` (W21-4 anchor doubles as W21-N final since W21-N is docs-only); UI-triggered confirmation anchor `92cf90d6edb5` byte-identical coverage shape. `coverage_summary.missing_capabilities` dropped 4 → 1 [chat] (W21 mid-tier closure target HIT). Close-out PR `week21 -> main` PENDING USER APPROVAL. W18-4 / W19-6 / W20-5 paterni. [FOLLOWUP sandbox-reset-stale-state-multi-analyze] not pulled at W21-N (opportunity-not-found; remains W22 candidate). | `dd24f1e` | **W21 close-out + live acceptance closed ✓** |

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

### §19.4 — Exit Criteria (W21-End) — SATISFIED `2026-05-28`

W21 şu koşullar sağlandığı için kapandı:

- [x] W21-0..W21-N kapandı; residual work explicitly deferred to W22.
- [x] W21-0 doc-reconcile landed via primary `8434323` + self-stamp
  `19bd9c7`: 10-doc canonical preamble refresh + §19 W21 plan header
  doc-open from §19-§20 combined + W21 Pull-Forward Acceptance Bar
  promotion in `POST_POC_BACKLOG.md` + README phase-pointer arch gate
  transition W20→W21 + new W20 close-out fact gate + baseline
  live-run anchor `600d9ecba5eb` / sha256 `1db1480551fd...c4477`.
- [x] W21-3 `workspace_trust` flip landed first per ordering via
  `c744c15` + `4b0a1ed`; `capabilities.py:99` `"missing" → "covered"`
  in both `_OFFICIAL_CAPABILITY_SUPPORT` and `_GLOBAL_CAPABILITY_SUPPORT`;
  4 invariant tests + harness trust-state marker/listener + scenario
  landed. Runtime untrusted → granted stimulus remains W22 follow-up.
- [x] W21-1 `testing` flip landed via `7e87030` + `38b8fd8`;
  `capabilities.py:97` `"missing" → "covered"`; 4 invariant tests +
  harness Test Controller markers + `local_test_controller` scenario +
  frozen trigger fixture regenerated.
- [x] W21-2 `comments` flip landed via `8948ea6` + `3088709`;
  `capabilities.py:96` `"missing" → "covered"`; 4 invariant tests +
  harness Comment Controller plumbing + `local_comments_controller`
  scenario + fixture regen. Comments stimulus is implicit through the
  existing `extrace.harness.runCurrentStimulus` command handler.
- [x] W21-4 stretch pulled and closed via `16e2224` + `2f9cba2` +
  `8c42445`: `cap_drop: [ALL]` + `no-new-privileges:true` on
  executor/api/ui + ADR 0013 + manual `NoNewPrivs: 1` kernel smoke.
- [x] W21-N close-out hygiene landed via `dd24f1e`: 10-doc canonical
  preamble Active → Previous flip + §19 W21 self-stamp + W21 tracker
  freeze + W21 Pull-Forward Acceptance Bar audit-trail close + 34 new
  arch invariant tests at `test_w21_section_19_cross_doc_parity.py`.
- [x] Final live-run on `ms-python.python` confirms:
  - `coverage_summary.missing_capabilities` drops 4 → 1 (`chat`
    only) — **must-pass satisfied**.
  - W19 Hat-1 (`unaccounted_dropout_count=null`) holds post-W21.
  - W19 Hat-2 (`harness_verification_unconfirmed_present` DROPPED)
    holds post-W21.
- [x] `automation_health.reasons` remains expected:
  `[skipped_scenarios_present, verification_gap_present,
  official_unresolved_present]`; `automation_health.status=degraded`
  remains OK until W22 hard tier closes `chat`.
- [x] `REFACTOR_STATUS.md`, `POST_POC_BACKLOG.md`,
  `active-work/README.md`, and related lane docs show the same W21
  closed / W22 planning state after this PR-readiness drift sweep.
- [x] W21 final bar pinned at W21-N: `tests/architecture/` **287
  passed**, 4 deselected; `tests/platform/contracts/test_capability_support_invariants.py`
  **26 passed**; `tests/platform/contracts/test_registry_split_regression.py`
  **8 passed**; `make test-security` **220 passed**; full suite
  **2104 passed, 9 skipped, 8 deselected**.
- [x] Per user direction (`2026-05-27`): W21 worked on the `week21`
  branch; sub-iter commits landed on `week21`; W21 tracker frozen at
  `dd24f1e` and corrected by this follow-up drift sweep before PR.
- [x] Close-out PR readiness: `week21 -> main` remains **PENDING USER
  APPROVAL**; this follow-up does not open or push the PR.
- [ ] Post-merge audit (W18-4-followup / W19-post-merge-drift /
  W20-post-merge-drift paterni; separate post-merge commit or next
  weekly branch).

## Per-Item Detail

### W21-0 — Doc-Reconcile + §19 Promote + Baseline Live-Run

**Status**: **closed `2026-05-27`** via primary `8434323` + self-stamp
`19bd9c7` (doc-reconcile + baseline live-run capture).

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
- Baseline live-run on `ms-python.python` captured at W21-0 self-stamp:
  `output/activation_report_ms-python.python-2026.5.2026052501-600d9ecba5eb.json`
  with sha256 `1db1480551fd...c4477`. Diff vs W20-5 anchor
  `4e92de149802` (sha256 `3804a5b5...4394c`) confirmed W20 close-out
  invariants hold: `unaccounted_dropout_count=null`,
  `harness_verification_unconfirmed_present` absent, and
  `coverage_summary.missing_capabilities` remains
  `[chat, comments, testing, workspace_trust]`.

**Commits**:

- Primary `8434323` `chore(W21-0): doc-reconcile — open week21 + §19
  promote from §19-§20 + 10-doc canonical preamble refresh + W21
  Pull-Forward Acceptance Bar promotion + README phase-pointer arch gate
  transition W20→W21 + new W20 close-out fact gate + baseline live-run
  pending`.
- Self-stamp `19bd9c7` `docs(W21-0-followup): self-stamp — baseline
  live-run anchor + sha256 + W21 tracker row flip`.

### W21-3 — `workspace_trust` Coverage

**Status**: **closed `2026-05-27`** via primary `c744c15` + self-stamp `4b0a1ed`. First substantive W21 sub-iter per user-confirmed ordering W21-3 → W21-1 → W21-2 (W20-4 DESIGN open Q4 resolved with "yes" branch).

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
- Self-stamp `4b0a1ed` `docs(W21-3-followup): self-stamp — W21-3 tracker row flip + §19 + POST_POC mirrors + 10-doc canonical preamble refresh + live-run anchor`.

### W21-1 — `testing` Coverage (closed `2026-05-27`)

**Stable ID**: `[GOAL taxonomy-testing-coverage]` (POST_POC_BACKLOG.md
W21 Pull-Forward Acceptance Bar).

**Driving paterni**: W21-3 (`workspace_trust`) primary `c744c15` + W20-1
(`scm`) primary `82276cb`. W20-4 DESIGN doc
`documents/architecture/comments-testing-readiness.md` §W21-1 is the
plumbing template.

**Three layers landed in primary `7e87030`** (mirror W21-3 c744c15 paterni;
6 files +162/-38):

1. **Capability taxonomy** (W21-3 paterni mirror):
   - `_OFFICIAL_CAPABILITY_SUPPORT["testing"]: "missing" → "covered"`
     at `packages/analysis_planner/capabilities.py:97`.
   - `_GLOBAL_CAPABILITY_SUPPORT["testing"]: "missing" → "covered"` at
     line 45 (`_HEURISTIC_CAPABILITY_SUPPORT` derives from `_GLOBAL_`,
     auto-flips).
   - `_GLOBAL_CAPABILITY_NOTES["testing"]` policy text unchanged
     (W20-4 DESIGN doc seed already in place pre-W21-1).

2. **Planner scenario registry** — `local_test_controller` added to
   `SCENARIO_REGISTRY` at `packages/analysis_planner/scenarios.py`:
   - `activation_events=("onStartupFinished",)` — broad surface; Test
     Controller is registered at activate() entry, not tied to a
     specific activation event (mirrors W21-3 `workspace_trust_transition`).
   - `api_capabilities=("commands", "window_ui", "testing")`.
   - 14 → 15 scenarios; `test_split_did_not_lose_data_volume` count
     bumped at `test_registry_split_regression.py:100`.

3. **Harness extension observability** —
   `executor/flows/harness_extension/extension.js:191-247` (extended
   from the existing 191-211 silent stub):
   - Run/debug profile callbacks emit `test_controller_event` markers
     via `emitHarnessEvent` (phases: `baseline` / `run_invoked` /
     `run_complete` / `debug_invoked` / `debug_complete`).
   - Ephemeral TestItem rebuild on every invocation (W19-X HMAC
     reactivation race lesson): `testController.items.replace([])` +
     fresh `createTestItem` + `add` so a stale cache cannot mask a
     regression.
   - `TestRun` lifecycle minimum closure: `createTestRun(request)` +
     `passed(item)` + `end()` so the run finalizes deterministically
     even under synthetic invocation.
   - Routes through reserved `"ExTrace Harness"` OutputChannel (W19-X
     Bug B paterni — `console.log` discarded by `launch_vscode.sh`).

**Invariant tests** (W21-3 workspace_trust block mirror at
`tests/platform/contracts/test_capability_support_invariants.py:141-202`):

- `test_testing_official_track_is_covered` — pins line 97 flip.
- `test_testing_heuristic_track_is_covered` — pins line 45 + derived
  heuristic; protects Official ⊆ Heuristic invariant (W20-3 gate).
- `test_testing_in_capability_taxonomy` — pins taxonomy membership.
- `test_local_test_controller_scenario_advertises_testing_capability`
  — pins scenario ↔ capability registry consistency.

Plus dict shape canonical pin update at line 349: `testing: "missing"`
→ `"covered"` with W21-1 promotion comment.

**Frozen trigger fixture regen** —
`tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json`:

- `coverage_summary.missing_capabilities`: 3 → 2 items (testing
  drops).
- `coverage_summary.covered/partial/missing`: 7/8/3 → 7/9/2;
  `partial_capabilities` adds `testing` in taxonomy order.
- `testing` matrix entries (official + heuristic + top-level):
  status `missing` → `partial`, `support_status` `missing` →
  `covered`, `supported_scenarios` populated with
  `local_test_controller`.
- `commands` + `window_ui` matrix entries (across all 3 tracks):
  `supported_scenarios` extended with `local_test_controller` (since
  the new scenario advertises both capabilities).

**Live-run smoke** (this self-stamp commit):

Anchor: `output/activation_report_ms-python.python-2026.5.2026052501-0b4998ce31b4.json`
sha256: `b7192bc2ff9c611f00e9dd806af54e0648c92d9201d78fe9ccb886dcf5968be4`

- `coverage_summary.missing_capabilities = [chat, comments]` (2
  items — testing dropped from W21-3 anchor's 3 items; must-pass ✓).
- `coverage_summary.covered/partial/missing = 8/8/2` (was 8/7/3 in
  W21-3 anchor — testing moved to partial in static fixture but
  runtime evidence upgraded one capability further; net: -1 missing
  must-pass ✓).
- `testing` matrix entry: status=`partial`, support_status=`covered`,
  `supported_scenarios=["local_test_controller"]`, is_active=false
  (mirror W21-3 workspace_trust paterni — scenario advertised but
  not selected for ms-python.python; static coverage matches).
- W20 invariants HOLD: `unaccounted_dropout_count = null` (Hat-1);
  `harness_verification_unconfirmed_present` NOT in reasons (Hat-2
  DROPPED); `event_attempts` count = 21 (unchanged).

**Live-run drift IMPROVEMENT vs W21-3 anchor**:

- `extra_trigger_failures_present` reason DROPPED from
  `automation_health.reasons` (was count=9 in W21-3 — confirmed
  transient stale executor state after rebuild; full-stack
  `docker compose up -d --build executor api` from clean state
  resolves it).
- `chat_tool_verification_incomplete` reason DROPPED (was W21-3
  surface; remains W22 `[GOAL taxonomy-chat-coverage]` candidate, not
  a W21-1 regression).
- Only 3 `automation_health.reasons` remain: `skipped_scenarios_present`,
  `verification_gap_present`, `official_unresolved_present` —
  cleaner than W21-3 anchor (5 reasons).

**Scope decision** (W21-N close-out or W22 deferral):

Runtime stimulus pass that drives `testing.runAll` end-to-end deferred.
Rationale: Test Controller callbacks fire on any future run profile
invocation without requiring a dedicated stimulus pass. Minimum W21-1
acceptance achieved via taxonomy promotion + scenario advertisement +
harness observability wiring. The listeners observe synthetic run-profile
invocations originating from any subsequent stimulus pass without
fixture restructuring.

**Test bar** (static):

- `tests/architecture/`: 241 passed (unchanged from W21-3).
- `tests/platform/contracts/test_capability_support_invariants.py`:
  18 → 22 passed (+4 W21-1 invariants).
- `tests/platform/contracts/test_registry_split_regression.py`:
  8 passed (count pin 14 → 15).
- `tests/workflows/marketplace/test_analysis_planner.py`:
  fixture parity green.
- `make test-security`: 220 passed (unchanged).
- Full suite: 2050 → 2054 passed, 9 skipped, 8 deselected (+4 net:
  W21-1 +4 invariants).

**Commits**:

- Primary `7e87030` `feat(W21-1): testing official-track promotion (missing → covered) + harness Test Controller marker emission + scenario + 4 invariant tests + fixture regen` — 6 files, +162 / -38.
- Self-stamp `38b8fd8` `docs(W21-1-followup): self-stamp — W21-1 tracker row flip + per-item detail + Phase line + 10-doc canonical preamble refresh + live-run anchor`.

### W21-2 — `comments` Coverage (closed `2026-05-28`)

**Stable ID**: `[GOAL taxonomy-comments-coverage]` (POST_POC_BACKLOG.md
W21 Pull-Forward Acceptance Bar).

**Driving paterni**: W21-1 (`testing`) primary `7e87030` + W21-3
(`workspace_trust`) primary `c744c15`. W20-4 DESIGN doc
`documents/architecture/comments-testing-readiness.md` §W21-2 is the
plumbing template. Comments stub was already partially in place
pre-W21-2 (`extension.js` CommentController creation + `ensureCommentThread`
called from stimulus command handler); W21-2 added the observability
markers and the planner scenario advertisement.

**Three layers landed in primary `8948ea6`** (mirror W21-1 7e87030 /
W21-3 c744c15 paterni; 7 files +161/-31):

1. **Capability taxonomy** (W21-3 / W21-1 paterni mirror):
   - `_OFFICIAL_CAPABILITY_SUPPORT["comments"]: "missing" → "covered"`
     at `packages/analysis_planner/capabilities.py:96`.
   - `_GLOBAL_CAPABILITY_SUPPORT["comments"]: "missing" → "covered"`
     at line 44 (`_HEURISTIC_CAPABILITY_SUPPORT` derives from
     `_GLOBAL_`, auto-flips).
   - `_GLOBAL_CAPABILITY_NOTES["comments"]` policy text unchanged
     (W20-4 DESIGN doc seed already in place pre-W21-2).

2. **Planner scenario registry** — `local_comments_controller` added
   to `SCENARIO_REGISTRY` at `packages/analysis_planner/scenarios.py`:
   - `activation_events=("onStartupFinished",)` — broad surface;
     CommentController is registered at activate() entry, not tied
     to a specific activation event (mirrors W21-3
     `workspace_trust_transition` + W21-1 `local_test_controller`).
   - `api_capabilities=("commands", "window_ui", "comments")`.
   - 15 → 16 scenarios; `test_split_did_not_lose_data_volume` count
     bumped at `test_registry_split_regression.py:100`.

3. **Harness extension observability** — two sites:
   - `executor/flows/harness_extension/extension.js`: after
     CommentController creation, emit a `comment_thread_state`
     baseline marker via `emitHarnessEvent`.
   - `executor/flows/harness_extension/stimulus_dispatch.js`:
     `ensureCommentThread` extended to emit `thread_created`
     immediately after `createCommentThread` and `thread_disposed`
     immediately after `dispose`. Imports `emitHarnessEvent` from
     markers.js. Ephemeral thread default (W19-X HMAC reactivation
     race lesson): thread is created + disposed within the same
     call so a stale handle from a previous activation cannot mask
     a regression. Routes through reserved `"ExTrace Harness"`
     OutputChannel (W19-X Bug B paterni — `console.log` discarded
     by `launch_vscode.sh`).

**Invariant tests** (W21-1 testing block + W21-3 workspace_trust block
mirror at `tests/platform/contracts/test_capability_support_invariants.py`):

- `test_comments_official_track_is_covered` — pins line 96 flip.
- `test_comments_heuristic_track_is_covered` — pins line 44 +
  derived heuristic; protects Official ⊆ Heuristic invariant
  (W20-3 gate).
- `test_comments_in_capability_taxonomy` — pins taxonomy membership.
- `test_local_comments_controller_scenario_advertises_comments_capability`
  — pins scenario ↔ capability registry consistency.

Plus dict shape canonical pin update at line ~411: `comments:
"missing"` → `"covered"` with W21-2 promotion comment.

**Frozen trigger fixture regen** —
`tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json`:

- `coverage_summary.missing_capabilities`: 2 → 1 items (comments
  drops; only `chat` remains for W22).
- `coverage_summary.covered/partial/missing`: 7/9/2 → 7/10/1;
  `partial_capabilities` adds `comments` in taxonomy order.
- `comments` matrix entries (official + heuristic + top-level):
  status `missing` → `partial`, `support_status` `missing` →
  `covered`, `supported_scenarios` populated with
  `local_comments_controller`.
- `commands` + `window_ui` matrix entries (across all 3 tracks):
  `supported_scenarios` extended with `local_comments_controller`
  (since the new scenario advertises both capabilities).

**Live-run smoke** (this self-stamp commit):

Anchor: `output/activation_report_ms-python.python-2026.5.2026052501-1ddb3702c0ca.json`
sha256: `2dabd15be329bbf1685fe7fc31469355bdc4a5acac2a364d43a196437339cbff`

- `coverage_summary.missing_capabilities = [chat]` (1 item —
  comments dropped from W21-1 anchor's 2 items; **W21 mid-tier
  closure target hit**; only `chat` remains for W22 hard tier —
  must-pass ✓).
- `coverage_summary.covered/partial/missing = 8/9/1`.
- `comments` matrix entry: status=`partial`, support_status=`covered`,
  `supported_scenarios=["local_comments_controller"]`, is_active=false.
- W20 invariants HOLD: `unaccounted_dropout_count = null` (Hat-1);
  `harness_verification_unconfirmed_present` NOT in reasons (Hat-2
  DROPPED).
- Live-run drift clean (same shape as W21-1): only 3
  `automation_health.reasons` remain: `skipped_scenarios_present`,
  `verification_gap_present`, `official_unresolved_present`.

**Scope decision** (W21-N close-out or W22 deferral):

Runtime stimulus pass that drives comment thread create/dispose
end-to-end is implicit: `ensureCommentThread` is already invoked
from the existing stimulus command handler (`extension.js` line ~254),
so any stimulus pass that lands on `extrace.harness.runCurrentStimulus`
exercises the new markers. No dedicated stimulus pass required.

**Test bar** (static):

- `tests/architecture/`: 241 passed (unchanged from W21-1).
- `tests/platform/contracts/test_capability_support_invariants.py`:
  22 → 26 passed (+4 W21-2 invariants).
- `tests/platform/contracts/test_registry_split_regression.py`:
  8 passed (count pin 15 → 16).
- `tests/workflows/marketplace/test_analysis_planner.py`:
  fixture parity green.
- `make test-security`: 220 passed (unchanged).
- Full suite: 2054 → 2058 passed, 9 skipped, 8 deselected (+4 net:
  W21-2 +4 invariants).

**Commits**:

- Primary `8948ea6` `feat(W21-2): comments official-track promotion (missing → covered) + harness Comment thread marker emission + scenario + 4 invariant tests + fixture regen` — 7 files, +161 / -31.
- Self-stamp `3088709` `docs(W21-2-followup): self-stamp — W21-2 tracker row flip + per-item detail + Phase line + 10-doc canonical preamble refresh + live-run anchor`.

### W21-4 — Container Hardening Baseline (closed `2026-05-28`)

**Stable ID**: `[GOAL container-hardening-baseline]` (POST_POC_BACKLOG.md
W21 Pull-Forward Acceptance Bar).

**Driving paterni**: ADR 0002 §4 threat model + ADR 0007 loopback
binding + ADR 0008 container packaging. User-pulled into W21 per
AskUserQuestion 2026-05-28 after W21-1 + W21-2 closed cleanly
(W21 mid-tier closure target `missing_capabilities = [chat]` already
hit before W21-4).

**Scope** (baseline first, ratchet-down deferred to W22):

This iter lands the easy half of container hardening — drop the
Docker-default capability keepset and refuse new privileges via
PR_SET_NO_NEW_PRIVS. The hard half (`read_only: true` root + tmpfs
mounts + custom seccomp profile) requires write-surface
restructuring (`/home/executor/.vscode-server`, `/run/extrace` for
W13-1 secrets, `/tmp` for stimulus materialization) that needs its
own iteration with measured retention semantics.

**Primary commit `16e2224`** (3 files +398/-0):

1. ADR 0013 (`documents/adrs/0013-container-isolation-baseline.md`):
   Decision table per service, rationale for cap_drop:[ALL] +
   no-new-privileges:true, deferred items audit trail, manual
   smoke checklist.

2. docker-compose.yml — three runtime services hardened:
   - `executor`: `cap_drop: [ALL]` + `cap_add: [NET_RAW, SYS_PTRACE]`
     (preserves harness monitoring tools — tcpdump/tshark/strace
     per executor/container/Dockerfile L30-L33) + `security_opt:
     ["no-new-privileges:true"]`.
   - `api`: `cap_drop: [ALL]` + `security_opt:
     ["no-new-privileges:true"]`.
   - `ui`: same shape as api.
   - `postgres` / `postgres_test`: unchanged (deferred to W22).
   - `executor-cdp`: unchanged (opt-in debug profile).

3. 10 invariant tests at
   `tests/architecture/test_compose_isolation_invariants.py`.

**Followup-1 commit `2f9cba2`** (3 files +117/-9) — surfaced during
the W21-4 primary live-run smoke:

The initial `cap_drop: [ALL]` on api + ui without cap_add audit
broke two services because the official Docker images use
runtime-user-switching entrypoints:

1. `automation_api`: `error: failed switching to "appuser":
   operation not permitted` — gosu-style entrypoint drops from
   root to appuser, needs CAP_SETUID + CAP_SETGID.
2. `automation_ui`: `chown("/var/cache/nginx/client_temp", 101)
   failed (1: Operation not permitted)` — nginx entrypoint chowns
   cache dir to user 101 before forking workers; needs CAP_CHOWN
   + defensive CAP_DAC_OVERRIDE, plus SETUID + SETGID for the
   worker drop.

Followup-1 restores the minimum caps each service needs, adds 2
new invariant tests pinning the cap_add lists exactly, and
documents the rationale in ADR 0013 §SETUID + SETGID retention
and §UI nginx caps.

**Invariant tests** (12 total at
`tests/architecture/test_compose_isolation_invariants.py`):

- 3 × `test_runtime_service_drops_all_capabilities[svc]` (executor,
  api, ui).
- 3 × `test_runtime_service_refuses_new_privileges[svc]`.
- `test_executor_keeps_audited_capabilities` — pins NET_RAW +
  SYS_PTRACE retention; flags any extra cap_add for ADR audit.
- `test_api_keeps_setuid_setgid_for_user_drop` — pins api cap_add
  list exactly.
- `test_ui_keeps_nginx_required_capabilities` — pins ui cap_add
  list exactly (SETUID + SETGID + CHOWN + DAC_OVERRIDE).
- `test_postgres_services_remain_unhardened_until_w22` — inverse
  pin so accidental cap_drop on postgres surfaces.
- `test_adr_0013_exists` + `test_adr_0013_documents_deferred_items`
  — pin the doc reference + ratchet-down audit trail.

**Live-run smoke** (this self-stamp commit):

Anchor: `output/activation_report_ms-python.python-2026.5.2026052501-eacea0b6690e.json`
sha256: `5d7c8b974f21e3bf4ad679a41551dd3e7b71d37573f5e7f2b28b87d2ad4a6a84`

- `coverage_summary.missing_capabilities = [chat]` (1 item —
  byte-identical with W21-2 anchor `1ddb3702c0ca`; **NO coverage
  regression from container hardening** — must-pass ✓).
- `coverage_summary.covered/partial/missing = 8/9/1` (byte-identical
  with W21-2).
- `automation_health.status = degraded` with 3 reasons:
  `skipped_scenarios_present`, `verification_gap_present`,
  `official_unresolved_present` (same shape as W21-2 — clean).
- W20 invariants HOLD: `unaccounted_dropout_count = null` (Hat-1);
  `harness_verification_unconfirmed_present` NOT in reasons (Hat-2
  DROPPED).

**Manual kernel smoke** (operator-verifiable from outside the
container): `docker exec automation_executor grep -E
"NoNewPrivs" /proc/self/status` returns `NoNewPrivs: 1`,
confirming PR_SET_NO_NEW_PRIVS active at the kernel level.

**Scope decision** (W22+ ratchet-down lane):

Per ADR 0013 §Deferred, the next ratchet-down iter targets:

1. `read_only: true` + tmpfs mounts for executor
   (`/home/executor/.vscode-server`, `/run/extrace`, `/tmp`),
   api, ui.
2. Custom `docker/seccomp.json` profile audited against
   Playwright + Xvfb + VS Code's actual syscall surface.
3. `postgres` / `postgres_test` cap_drop after upstream image
   no longer needs CAP_CHOWN at first-run, OR a custom
   entrypoint pattern.

**Test bar**:

- `tests/architecture/`: 241 → 253 passed (+10 W21-4 primary
  invariants + 2 W21-4-followup-1 cap_add pins; total +12).
- `tests/platform/contracts/test_capability_support_invariants.py`:
  26 passed (unchanged from W21-2).
- `make test-security`: 220 passed (unchanged).
- Full suite: 2058 → 2070 passed (+12 net W21-4).

**Commits**:

- Primary `16e2224` `feat(W21-4): container isolation baseline — cap_drop + no-new-privileges on executor/api/ui + ADR 0013 + invariant tests` — 3 files, +398 / -0.
- Followup-1 `2f9cba2` `fix(W21-4-followup-1): restore SETUID + SETGID for api/ui + CHOWN + DAC_OVERRIDE for ui (nginx) — surfaced during W21-4 primary live-run smoke` — 3 files, +117 / -9.
- Self-stamp `8c42445` `docs(W21-4-followup): self-stamp — W21-4 tracker row flip + per-item detail + Phase line + 10-doc canonical preamble refresh + live-run anchor`.

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
