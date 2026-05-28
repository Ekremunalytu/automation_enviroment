# W22 — Coverage Promotion Round 3: Hard Tier + Sandbox ADR + Container Hardening Ratchet-Down (Active Work Tracker)

`Last Updated: 2026-05-28 (W22-2 [GOAL taxonomy-chat-coverage] closed (static cut) ffbb743 + self-stamp (this commit) — HARD TIER CLOSURE STATIC: capabilities.py 2 dict flips (chat missing→covered both tracks) + scenarios.py 2 new ScenarioDefinition (local_chat_participant_controller + local_language_model_tool_controller) + executor/flows/harness_extension/extension.js GREENFIELD chat participant + LM tool registration per ADR 0014 Option C (vscode.chat.createChatParticipant + vscode.lm.registerTool, GA since VS Code 1.90, no proposed APIs, no engine bump, ephemeral subscriptions on context.subscriptions, baseline markers via emitHarnessEvent → reserved OutputChannel W19-X Bug B paterni) + stimulus_dispatch.js REPLACE pre-W22-2 incomplete UI-nav chat handler with two distinct API-level branches (onChatParticipant emits chat_participant_state phase=stimulated marker + onLanguageModelTool calls vscode.lm.invokeTool against the locally-registered tool + emits lm_tool_state phase=invoked marker with try/catch invoke_failed fallback) + 5 invariants at test_capability_support_invariants.py (W21-2 paterni mirror, +1 extra for second scenario) + dict shape canonical pin update + count pin 16→18 + fixture regen via select_scenarios() programmatic call (no hand-editing; deterministic projection) showing coverage_summary.missing_capabilities = ["chat"] → [] (W22 must-pass #6 satisfied STATICALLY) + counts 8/9/1 → 8/10/0 + chat matrix entries 3 tracks status missing→partial support_status missing→covered; static test bar capability invariants 26 → 31 (+5); registry count pin 16 → 18; broader sweep 631 passed 2 skipped 4 deselected; runtime live-run anchor (make sim-target TARGET=ms-python.python → missing_capabilities==[] on actual run) DEFERRED TO USER per direction 2026-05-28 (Linux required for docker stack; Mac smoke unreliable). W22-3 [FOLLOWUP attribution-count-parity-process-events]+[FOLLOWUP attribution-count-parity-output-channel] closed cff10d3 + 70dc43a — producer-side stamps at executor/flows/playwright/attribution/links.py for kind=process + kind=output_channel_appendline mirroring W17-1 activation paterni byte-identical (W14 production scan divergence shape applied to two additional event families); two new count helpers at health/summary.py (count_target_process_events + count_target_output_events) mirroring count_target_activations guard shape; 8 new invariant tests at tests/executor/test_playwright_attribution_links.py (4 per family: target flag / non-target unflag / no-target-set unflag / parity contract pin); LOC ceiling bump health/summary.py 537 → 552 with W22-3 rationale; closes 2 [FOLLOWUP] tags; test bar delta tests/executor/test_playwright_attribution_links.py 30 → 38 passed; tests/architecture/ 292 unchanged; make test-security 228 unchanged; no live-run anchor (producer-side stamp consistency fix). W22-5 [GOAL sandbox-evasion-canary-fixture] closed a6dd24b + 1de616b — observer-side synthetic-probe canary at tests/security/test_sandbox_evasion_canary.py (4 test functions / 8 cases with parametrize expansion: 1 taxonomy alignment + 5 parametrized family probes + 2 rejection safety nets) + new module packages/analysis_planner/evasion_signals.py (EVASION_FAMILY_TAXONOMY tuple byte-identical with ADR 0015 + EvasionSignal frozen dataclass validating family membership + non-empty detail at construction) + Makefile test-security target enrolment; observer-side ONLY per ADR 0015 §Operational notes (no recorder integration / no detection logic / no suppression — W23+ scope); test bar delta make test-security 220 → 228 (+8 — plan estimate +1 was file-level conservative); tests/architecture/ 292 unchanged; no live-run anchor (pytest-based observer-side fixture). W22-6 [GOAL container-hardening-ratchet-down] DEFERRED TO USER per direction 2026-05-28 — Linux required for live-smoke (NoNewPrivs/Seccomp/Cap/mount/unshare + Playwright/Xvfb/VS Code tmpfs surface audit); ADR 0013 §Deferred remains open; user closure'a alacak Linux ortamında. W22-4 [GOAL sandbox-evasion-defense-mvp] closed 9a8ad28 + ea418a6 — ADR 0015 documents/adrs/0015-sandbox-evasion-defense-policy.md Accepted (Draft Policy — taxonomy stable; W23+ defense implementation roadmap); 5-family taxonomy E1 webdriver_presence / E2 cdp_fingerprint / E3 timing_probe / E4 platform_identity / E5 process_introspection with per-family stance (Suppress+Detect for E1/E2/E4 / Passively observe+Detect for E3 / Defense-in-depth via W22-6 for E5); promotes ADR 0002 §3 OOS bucket via the follow-up ADR mechanism; alternatives A (defer whole lane to V2), B (combine ADR with first runtime cut), C (detect-only uniformly), D (must-suppress uniformly) rejected with gerekçe in ADR §Alternatives Rejected; + 2 architecture invariants at tests/architecture/test_sandbox_evasion_adr.py (existence pin + taxonomy short-name + ADR 0002 promotion link + W23+ deferral + W22-5 canary entry-point reference); unblocks W22-5 [GOAL sandbox-evasion-canary-fixture]; test bar delta tests/architecture/ 290 → 292 (+2); make test-security 220 unchanged; no live-run anchor needed (W22-4 doc-only). W22-1 [GOAL taxonomy-chat-policy-adr] closed 906fcd5 + d018fe1 — ADR 0014 documents/adrs/0014-chat-and-language-model-tool-policy.md Accepted Option C (tool-only coverage via stable vscode.chat.createChatParticipant + vscode.lm.registerTool + vscode.lm.invokeTool APIs, all GA since VS Code 1.90 / no external services / no proposed APIs / no engine bump); markers route via reserved OutputChannel (W19-X Bug B paterni); ephemeral lifecycle on context.subscriptions (W19-X Bug C lesson); alternatives A (proposed-API stub provider via registerChatModelProvider), B (mock invokeTool without registration), D (declare partial with blocker) rejected with gerekçe in ADR §Alternatives Rejected; + 2 architecture invariants at tests/architecture/test_chat_policy_adr.py (existence pin + Option C content marker pin); unblocks W22-2 [GOAL taxonomy-chat-coverage]; test bar delta tests/architecture/ 288 → 290 (+2); make test-security 220 unchanged; no live-run anchor needed (W22-1 doc-only). W22-0 doc-reconcile closed 26bb080 + ff3fbbd opening week22 branch — new W22 active-work tracker per W18-W21 paterni + 10-doc canonical preamble refresh transitioning W21 closed/merged → W22 active + §19 W21 plan header "Previous phase" stamp + §20 W22 plan header doc-open in REFACTOR_OPTIMIZATION.md (W19-0/W20-0/W21-0 paterni mirror) + W21 Pull-Forward Acceptance Bar in POST_POC_BACKLOG.md closed/merged stamp + W22 Roadmap Acceptance Bar "planning" → "active" promotion listing W22-0..W22-N + W21-deferred [FOLLOWUP workspace-trust-stimulus-pass] + [FOLLOWUP sandbox-reset-stale-state-multi-analyze] + W21-4 ADR 0013 §Deferred ratchet-down lane (read_only + tmpfs + custom seccomp) pulled into W22-6 + README phase-pointer arch gate transition W21 → W22 (test_readme_phase_pointer.py tracks_active_w22_status + new W21 close-out merge gate test pinning PR #30 / week21 -> main / 5dc18aa) + test_canonical_preamble_parity.py fingerprint refresh (PR #29 → PR #30, 64a3c3d → 5dc18aa, tracker slot W21 → W22). W21 closed and merged via PR #30 week21 -> main MERGED 2026-05-28 via 5dc18aa; final W21 bar tests/architecture/ 287 passed / make test-security 220 passed / full suite 2104 passed, 9 skipped, 8 deselected. W22 entry signal: coverage_summary.missing_capabilities = [chat] (1 item) at W21-4 anchor eacea0b6690e sha256 5d7c8b974f21e3bf4ad679a41551dd3e7b71d37573f5e7f2b28b87d2ad4a6a84; W22-2 closes [chat] hard tier (1 → 0 missing). Parallel statik analiz şeridi ayrı worktree'de extrace-static branch çalışıyor (kendi W21 referans temizliği yapıyor; bu W22 oturumu ile çakışma yok). Main'e onaysız push/merge yok (user direction 2026-05-28; memory feedback_pr_push_approval standing).)`
`Phase: W22-2 [GOAL taxonomy-chat-coverage] closed (static cut) ffbb743 + self-stamp (this commit) — HARD TIER CLOSURE STATIC: capabilities.py 2 flips + scenarios.py 2 new (local_chat_participant + local_language_model_tool) + harness extension.js + stimulus_dispatch.js per ADR 0014 Option C + 5 invariants + fixture regen showing missing_capabilities=[]; runtime live-run gate user-owned on Linux. W22-3 [FOLLOWUP attribution-count-parity-process-events]+[FOLLOWUP attribution-count-parity-output-channel] closed cff10d3 + 70dc43a; W22-5 [GOAL sandbox-evasion-canary-fixture] closed a6dd24b + 1de616b; W22-6 [GOAL container-hardening-ratchet-down] DEFERRED TO USER per direction 2026-05-28 (Linux required); W22-4 [GOAL sandbox-evasion-defense-mvp] closed 9a8ad28 + ea418a6; W22-1 [GOAL taxonomy-chat-policy-adr] closed 906fcd5 + d018fe1; W22-0 doc-reconcile closed 26bb080 + ff3fbbd opening week22 branch; remaining slate (W22-7 activation event spec gap conditional + W22-N close-out)`
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
- **W22-0 closed `26bb080` + `ff3fbbd`.** Doc reconcile + canonical
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
- **W22-1 closed `906fcd5` + `d018fe1`.** `[GOAL
  taxonomy-chat-policy-adr]` ADR 0014 Accepted (Option C —
  tool-only coverage via stable `vscode.chat.createChatParticipant`
  + `vscode.lm.registerTool` + `vscode.lm.invokeTool` APIs, all
  GA since VS Code 1.90; no external services, no proposed APIs,
  no engine bump). + 2 architecture invariants at
  `tests/architecture/test_chat_policy_adr.py`. Unblocks W22-2.
- **W22-4 closed `9a8ad28` + `ea418a6`.** `[GOAL
  sandbox-evasion-defense-mvp]` ADR 0015 Accepted (Draft Policy
  — 5-family taxonomy `webdriver_presence` / `cdp_fingerprint` /
  `timing_probe` / `platform_identity` / `process_introspection`
  with per-family stance; W23+ defense implementation roadmap;
  ADR 0002 §3 OOS bucket promoted via the follow-up ADR
  mechanism). + 2 architecture invariants at
  `tests/architecture/test_sandbox_evasion_adr.py`. Unblocks
  W22-5 canary fixture.
- **W22-5 closed `a6dd24b` + `1de616b`.** `[GOAL
  sandbox-evasion-canary-fixture]` observer-side synthetic-probe
  coverage of the five families via
  `tests/security/test_sandbox_evasion_canary.py` (8 cases when
  parametrize expands) + new module
  `packages/analysis_planner/evasion_signals.py`
  (`EVASION_FAMILY_TAXONOMY` + `EvasionSignal` frozen dataclass)
  + Makefile `test-security` enrolment. Observer-side ONLY per
  ADR 0015 — no recorder integration, no detection, no
  suppression (W23+ scope). `make test-security` 220 → 228 (+8).
- **W22-6 DEFERRED TO USER per direction 2026-05-28.** `[GOAL
  container-hardening-ratchet-down]` requires Linux for
  live-smoke (NoNewPrivs/Seccomp/Cap/mount/unshare + tmpfs
  surface audit for Playwright+Xvfb+VS Code). This W22 session
  is on Mac; user will close the ratchet-down lane themselves
  in a Linux environment. ADR 0013 §Deferred (read_only + tmpfs
  + custom seccomp) remains open until then.
- **W22-3 closed `cff10d3` + `70dc43a`.**
  `[FOLLOWUP attribution-count-parity-process-events]` +
  `[FOLLOWUP attribution-count-parity-output-channel]` —
  producer-side stamps at `links.py` for `kind="process"` +
  `kind="output_channel_appendline"` mirror W17-1 activation
  paterni byte-identical (W14 production scan divergence shape
  applied to two additional event families). Two new count
  helpers at `summary.py` (`count_target_process_events` +
  `count_target_output_events`) + 8 new invariant tests
  (4 per family: target flag / non-target unflag / no-target-set
  unflag / parity contract pin). LOC ceiling bump
  `health/summary.py` 537 → 552. Closes 2 [FOLLOWUP] tags.
- **W22-2 closed (static cut) `ffbb743` + self-stamp (this commit);
  runtime gate DEFERRED TO USER (Linux required).**
  `[GOAL taxonomy-chat-coverage]` HARD TIER CLOSURE STATIC.
  capabilities.py 2 dict flips (`chat: "missing" → "covered"` both
  tracks) + scenarios.py 2 new ScenarioDefinition entries
  (`local_chat_participant_controller` +
  `local_language_model_tool_controller`) + extension.js
  GREENFIELD chat participant + LM tool registration per ADR 0014
  Option C (`vscode.chat.createChatParticipant` +
  `vscode.lm.registerTool`, GA since VS Code 1.90, no proposed
  APIs, no engine bump) + stimulus_dispatch.js REPLACE pre-W22-2
  incomplete UI-nav chat handler with two distinct API-level
  branches + 5 invariants (W21-2 paterni mirror) + dict shape
  canonical pin update + count pin 16 → 18 + fixture regen via
  `select_scenarios()` programmatic call. Static:
  `coverage_summary.missing_capabilities = ["chat"] → []` —
  **W22 must-pass #6 satisfied STATICALLY.** Runtime live-run
  anchor (`make sim-target TARGET=ms-python.python`) user-owned
  on Linux (docker stack required).

## Sub-Iter Scope (Authored 2026-05-28)

| Iter | Status / Theme | Commit ref | Closes which acceptance-bar item? |
|---|---|---|---|
| W22-0 | **in-flight 26bb080** doc-reconcile — `week22` branch open + new W22 active-work tracker (this file) + §19 W21 plan header doc-close ("Previous phase" stamp) + §20 W22 plan header doc-open in `REFACTOR_OPTIMIZATION.md` (W19-0/W20-0/W21-0 paterni mirror) + 10-doc canonical preamble refresh W21 closed/merged → W22 active + W21 Pull-Forward Acceptance Bar in `POST_POC_BACKLOG.md` closed/merged stamp + W22 Roadmap Acceptance Bar "planning" → "active" promotion + README phase-pointer arch gate transition W21→W22 + new W21 close-out fact gate `test_readme_phase_pointer_mentions_w21_closeout_merge` pinning PR #30 / `week21 -> main` / `5dc18aa` + canonical preamble parity test fingerprint refresh (PR #29 → PR #30, `64a3c3d` → `5dc18aa`, tracker slot W21 → W22). | this commit | — (doc-reconcile; no acceptance-bar item) |
| W22-1 | **closed** `906fcd5` + `d018fe1` — `[GOAL taxonomy-chat-policy-adr]` ADR `documents/adrs/0014-chat-and-language-model-tool-policy.md` Accepted (Option C — tool-only coverage with explicit local boundary). `onChatParticipant:*` covered via `vscode.chat.createChatParticipant`; `onLanguageModelTool:*` covered via `vscode.lm.registerTool` + `vscode.lm.invokeTool`. Stable VS Code 1.90+ APIs, network-free; NO engine bump, NO proposed APIs, NO Insiders build. Alternatives A (proposed-API stub provider), B (mock invoke without registration), D (declare partial with blocker) rejected with gerekçe. Markers route via reserved OutputChannel (W19-X Bug B paterni); ephemeral lifecycle on `context.subscriptions` (W19-X Bug C lesson). + 2 architecture invariants at `tests/architecture/test_chat_policy_adr.py` (existence + content pin). | `906fcd5` (primary) + `d018fe1` (self-stamp) | unblocks W22-2 |
| W22-2 | **closed (static cut)** `ffbb743` + self-stamp (this commit); **runtime gate DEFERRED TO USER** (Linux required) — `[GOAL taxonomy-chat-coverage]` hard tier closure. capabilities.py 2 flips (chat missing→covered both tracks) + scenarios.py 2 new ScenarioDefinition (local_chat_participant_controller + local_language_model_tool_controller) + extension.js GREENFIELD chat participant + LM tool registration (vscode.chat.createChatParticipant + vscode.lm.registerTool, GA 1.90+, no proposed APIs) + stimulus_dispatch.js REPLACE pre-W22-2 incomplete UI-nav chat handler with two distinct API-level branches (chat_participant_state phase=stimulated + lm_tool_state phase=invoked with try/catch invoke_failed fallback) + 5 invariants at test_capability_support_invariants.py (W21-2 paterni mirror, +1 extra for second scenario) + dict shape canonical pin update + count pin 16→18 + fixture regen via select_scenarios() programmatic call. **Static**: coverage_summary.missing_capabilities = `["chat"]` → `[]` (HARD TIER CLOSURE STATIC). Runtime live-run anchor (make sim-target → missing_capabilities == [] on actual ms-python.python run) user-owned on Linux. | `ffbb743` (primary) + (this commit) (self-stamp) | **W22 acceptance #6 (Must-pass) satisfied STATICALLY** |
| W22-3 | **closed** `cff10d3` + self-stamp (this commit) — `[FOLLOWUP attribution-count-parity-process-events]` + `[FOLLOWUP attribution-count-parity-output-channel]` (both) — producer-side stamps at `links.py` for `kind="process"` + `kind="output_channel_appendline"` mirroring W17-1 activation paterni byte-identical (commits `8c26d02` + `0a8f59e`). Two new count helpers at `summary.py` (`count_target_process_events` + `count_target_output_events`) byte-identical with `count_target_activations` guard shape. 8 new invariant tests at `test_playwright_attribution_links.py` (4 per family: target flag / non-target unflag / no-target-set unflag / parity contract pin). `health/summary.py` LOC ceiling 537 → 552 (W22-3 rationale comment). | `cff10d3` (primary) + (this commit) (self-stamp) | closes 2 [FOLLOWUP] tags |
| W22-4 | **closed** `9a8ad28` + self-stamp (this commit) — `[GOAL sandbox-evasion-defense-mvp]` ADR `documents/adrs/0015-sandbox-evasion-defense-policy.md` Accepted (Draft Policy — taxonomy stable; defense implementation deferred to W23+). Five-family taxonomy (E1 `webdriver_presence` / E2 `cdp_fingerprint` / E3 `timing_probe` / E4 `platform_identity` / E5 `process_introspection`) with per-family stance (Suppress+Detect / Passively observe / Defense-in-depth via W22-6). Promotes ADR 0002 §3 OOS bucket via the explicit follow-up ADR mechanism. + 2 architecture invariants at `tests/architecture/test_sandbox_evasion_adr.py` (existence + taxonomy short-name pin). Alternatives A/B/C/D rejected with gerekçe in §Alternatives Rejected. | `9a8ad28` (primary) + (this commit) (self-stamp) | unblocks W22-5 |
| W22-5 | **closed** `a6dd24b` + self-stamp (this commit) — `[GOAL sandbox-evasion-canary-fixture]` observer-side synthetic-probe coverage of ADR 0015 five-family taxonomy via `tests/security/test_sandbox_evasion_canary.py` (4 test functions, 8 cases when parametrize expands: 1 taxonomy alignment + 5 parametrized family probes + 2 rejection safety nets) + `packages/analysis_planner/evasion_signals.py` new module (`EVASION_FAMILY_TAXONOMY` tuple + `EvasionSignal` frozen dataclass with family/detail validation at construction) + Makefile `test-security` target enrolment. Observer-side ONLY per ADR 0015 §Operational notes — no recorder integration / no detection logic / no suppression (W23+ scope). `make test-security` 220 → 228 (+8 — plan estimate +1 was file-level conservative). | `a6dd24b` (primary) + (this commit) (self-stamp) | satisfies ADR 0015 §W22-5 acceptance |
| W22-6 | **deferred to user** per direction 2026-05-28 — `[GOAL container-hardening-ratchet-down]` (W21-4 §Deferred closure) requires Linux host for live-smoke (NoNewPrivs/Seccomp/Cap/mount/unshare doğrulamaları + Playwright+Xvfb+VS Code tmpfs surface audit). Bu W22 session'ı Mac üzerinde, smoke test edilemez; user kendisi Linux ortamında implement edecek. ADR 0013 §Deferred (read_only + tmpfs + custom seccomp) açık kalıyor — user closure'a alacak. | — | (out of session scope) |
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

### W22-1 — Chat + LM tool policy ADR (ADR 0014)

**Status**: **closed** — primary `906fcd5` + self-stamp (this commit).

**Goal**: Author ADR 0014 `documents/adrs/0014-chat-and-language-model-tool-policy.md` to record the local-only verification strategy for `onChatParticipant:*` + `onLanguageModelTool:*` activation events before W22-2 implementation. Resolve the open `_GLOBAL_CAPABILITY_NOTES["chat"]` policy seed (`packages/analysis_planner/capabilities.py:63-66`, W20-4 design pre-stage) with an Accepted ADR.

**Decision**: **Option C — tool-only coverage with explicit local boundary.**

- `onChatParticipant:*` covered via
  `vscode.chat.createChatParticipant("extrace.harness.chat",
  noopChatHandler)` at extension activate(). Handler returns
  synchronously; no chat model interaction.
- `onLanguageModelTool:*` covered via
  `vscode.lm.registerTool("extrace.harness.lm.tool",
  { invoke: noopToolInvoke })` at activate() +
  `vscode.lm.invokeTool(...)` from `stimulus_dispatch.js` under
  the `onLanguageModelTool` family branch. `noopToolInvoke`
  returns a canned `LanguageModelToolResult` constructed
  in-process; no model call.
- Both APIs are GA since VS Code 1.90 (June 2024); existing
  `engines.vscode: "^1.90.0"` in
  `executor/flows/harness_extension/package.json` covers both.
  **NO engine bump, NO `enabledApiProposals` entry, NO Insiders
  build required.**
- Markers route via reserved `"ExTrace Harness"` OutputChannel
  through `emitHarnessEvent` (W19-X Bug B paterni). Subscriptions
  live on `context.subscriptions` and dispose at extension
  deactivate; stimulus dispatch is one-shot (W19-X Bug C HMAC
  reactivation race lesson).

**Alternatives Rejected** (gerekçe in ADR §Alternatives Rejected):

- Option A — proposed-API stub provider via
  `vscode.lm.registerChatModelProvider` (requires
  `enabledApiProposals` + Insiders build; violates stable-only
  stance).
- Option B — mock `invokeTool` without registration (throws
  synchronously; collapses into Option C anyway).
- Option D — declare `chat` permanently `partial` with a
  documented blocker (cedes ground unnecessarily; the activation
  events ARE fully exercisable via stable local API).

**Changes**:

1. **New ADR** —
   `documents/adrs/0014-chat-and-language-model-tool-policy.md`
   mirroring ADR 0013 structure (Status/Date/Authors/Driving
   phase + Context/Decision/API Surface Boundary/Security Posture/
   W19-X Lesson Application/Engine Compatibility/Consequences/
   §Alternatives Rejected/References).

2. **New architecture invariants** —
   `tests/architecture/test_chat_policy_adr.py`:
   - `test_adr_0014_exists` (file path existence pin)
   - `test_adr_0014_documents_option_c_decision` (Option C
     decision marker pin: `vscode.chat.createChatParticipant`,
     `vscode.lm.registerTool`, `vscode.lm.invokeTool`, `Option C`,
     `must not call external services`, `engines.vscode`, `1.90`,
     `W22-2`)

**Acceptance**: ADR file exists at expected path; 2 architecture
invariants green; W22-2 unblocked.

**Test bar delta**: `tests/architecture/` 288 → 290 (+2 — ADR
existence + content pin). `make test-security` 220 unchanged.

**Live-run anchor**: not applicable (W22-1 doc-only; no behavior
change). Next live-run anchor at W22-2 self-stamp must show
`coverage_summary.missing_capabilities == []` (hard tier closure,
W22 must-pass #6).

### W22-4 — Sandbox-evasion defense policy ADR (ADR 0015)

**Status**: **closed** — primary `9a8ad28` + self-stamp (this commit).

**Goal**: Author ADR 0015 `documents/adrs/0015-sandbox-evasion-defense-policy.md` to formalize the anti-analysis pattern taxonomy + per-family defense stance + W23+ implementation roadmap. Promotes ADR 0002 §3 "advanced sandbox evasion" out-of-scope bucket into a scoped W23+ in-scope lane via the follow-up ADR mechanism ADR 0002 §3 explicitly invites. Unblocks W22-5 canary fixture which builds observer-side probes against the stable taxonomy contract.

**Decision**: **Accepted (Draft Policy — taxonomy stable; defense implementation deferred to W23+).**

Five-family taxonomy (stable short-names; load-bearing for W22-5 canary fixture):

- **E1 `webdriver_presence`** — Suppress + Detect (Playwright launcher + page init script overriding `navigator.webdriver`)
- **E2 `cdp_fingerprint`** — Suppress + Detect (page init script deletes well-known CDP-leak globals: `window.cdc_*`, `window.callPhantom`)
- **E3 `timing_probe`** — Passively observe + Detect (full masking too brittle; classify suspicious and route to `inconclusive`)
- **E4 `platform_identity`** — Suppress + Detect (Playwright UA + `navigator.platform` overrides; container `uname` shape matches "real user" Debian + glibc)
- **E5 `process_introspection`** — Defense-in-depth via W22-6 container ratchet-down (`cap_drop:[ALL]` + custom seccomp already constrains `/proc` visibility)

**Alternatives Rejected** (gerekçe in ADR §Alternatives Rejected):

- Option A — defer whole lane to V2 (rejected — W22-5 depends on stable taxonomy contract today)
- Option B — combine ADR with first runtime cut (rejected — launcher hot path touches need dedicated W23+ sub-iter with live-run smoke gate)
- Option C — detect-only uniformly (rejected — E1/E2 suppression has high leverage)
- Option D — must-suppress uniformly (rejected — E3 per-call instrumentation risks breaking legitimate extensions)

**Changes**:

1. **New ADR** — `documents/adrs/0015-sandbox-evasion-defense-policy.md` mirroring ADR 0013/0014 structure (Status/Date/Authors/Driving phase + Context/Decision/Pattern Taxonomy/Policy Stance/Defense Surface Placement/Security Posture/W19-X Marker Channel Conformance/Engine Compatibility/Consequences/Implementation Roadmap (W23+)/§Alternatives Rejected/References).

2. **New architecture invariants** — `tests/architecture/test_sandbox_evasion_adr.py`:
   - `test_adr_0015_exists` (file path existence pin)
   - `test_adr_0015_documents_taxonomy_short_names` (taxonomy short-name pin: `webdriver_presence`, `cdp_fingerprint`, `timing_probe`, `platform_identity`, `process_introspection` + E1..E5 + `ADR 0002` + `W23` + `page.addInitScript` + `test_sandbox_evasion_canary.py`)

**Acceptance**: ADR file exists at expected path; 2 architecture invariants green; W22-5 unblocked.

**Test bar delta**: `tests/architecture/` 290 → 292 (+2 — ADR existence + taxonomy short-name pin). `make test-security` 220 unchanged (W22-5 brings the +1).

**Live-run anchor**: not applicable (W22-4 doc-only; no behavior change). Next runtime gate at W22-5 canary fixture acceptance (synthetic-probe observer-side coverage of all five families).

### W22-5 — Sandbox-evasion canary fixture (synthetic probes, observer-side)

**Status**: **closed** — primary `a6dd24b` + self-stamp (this commit).

**Goal**: Land the observer-side synthetic-probe canary for the ADR 0015 five-family taxonomy at `tests/security/test_sandbox_evasion_canary.py`. The fixture simulates the data flow an analyzer-side observer would see when each family's probe fires inside an untrusted extension, with the load-bearing taxonomy short-names (`webdriver_presence`, `cdp_fingerprint`, `timing_probe`, `platform_identity`, `process_introspection`) pinned as a contract for W23+ runtime detection paths.

**Decision**: Observer-side ONLY (per ADR 0015 §Operational notes). Three artifacts: (a) new minimal module `packages/analysis_planner/evasion_signals.py` with the taxonomy tuple + `EvasionSignal` frozen dataclass that validates family membership + non-empty detail at construction; (b) canary tests with 8 cases (1 taxonomy alignment + 5 parametrized family probes + 2 rejection safety nets); (c) Makefile `test-security` target enrolment. No recorder API, no detection logic, no suppression — those land in W23+ when the actual probe detection code lives alongside Playwright page-init scripts.

**Changes**:

1. **New module** — `packages/analysis_planner/evasion_signals.py`:
   - `EVASION_FAMILY_TAXONOMY: tuple[str, ...]` — five short-names byte-identical with ADR 0015 §Sandbox-Evasion Pattern Taxonomy.
   - `EvasionSignal` (`@dataclass(frozen=True)`) — `family: str` + `detail: str`; `__post_init__` rejects unknown family or empty detail.

2. **New test file** — `tests/security/test_sandbox_evasion_canary.py`:
   - `test_evasion_family_taxonomy_matches_adr_0015` (1 case) — pins five short-names byte-identical with ADR.
   - `test_synthetic_probe_records_the_expected_family` (5 parametrized cases) — observer-side simulation per family.
   - `test_evasion_signal_rejects_unknown_family` (1 case) — taxonomy drift safety net.
   - `test_evasion_signal_rejects_empty_detail` (1 case) — opaque-signal safety net.

3. **`Makefile` `test-security` target** — enrolls `tests/security/test_sandbox_evasion_canary.py`.

**Acceptance**: All 8 cases pass; `make test-security` count delta + 8; registry split regression unaffected (new module is independent of analysis_planner facade contract).

**Test bar delta**: `make test-security` 220 → 228 (+8). `tests/architecture/` 292 (unchanged). Plan estimate `+1` was file-level conservative; actual case-level is `+8`.

**Live-run anchor**: not applicable (pytest-based observer-side fixture; no runtime container behavior). Next runtime gate is W23+ when probe detection lands.

### W22-6 — Container ratchet-down (DEFERRED TO USER per direction 2026-05-28)

**Status**: **deferred to user** — out of session scope.

**Reason**: ADR 0013 §Deferred (read_only + tmpfs + custom seccomp profile) closure requires a Linux host for the W19+ live-smoke gate (`docker exec` into the executor + grep `/proc/self/status` for `NoNewPrivs`/`Seccomp`/`Cap` + `mount | grep "rw,"` + `unshare --net 2>&1 | grep "Operation not permitted"`). This W22 session is running on Mac and cannot perform the smoke; without live-smoke validation the tmpfs surface for Playwright + Xvfb + VS Code Extension Host write paths cannot be audited safely (W21-4 `cap_add` audit paterni surfaced runtime needs only at the smoke stage). User will close the ratchet-down lane themselves in a Linux environment.

**Implications**:

- ADR 0013 §Deferred remains open in the canonical text. User will flip §Deferred → §Closed when implementing.
- W22 acceptance bar Must-pass #5 (`docker-compose read_only:true + tmpfs + seccomp her servis aktif; manual smoke pass`) remains NOT met in this session.
- W22-N close-out will record the W22-6 deferral in the audit trail; the close-out is otherwise unblocked since W22-6 was an independent lane (no downstream sub-iter depends on it).

**Resumption checklist (for the user, when on Linux)**:

1. Write `docker/seccomp.json` (Docker default + `unshare`/`mount`/`personality` explicit deny).
2. Edit `docker-compose.yml`: add `read_only: true` + `tmpfs:` per service + `security_opt: ["seccomp=./docker/seccomp.json", ...]`.
3. Run `make exec-up`; if Playwright/Xvfb/VS Code surface a write-permission error, add the missing path to the service's `tmpfs:` list (W21-4-followup-1 `2f9cba2` paterni).
4. Manual smoke per ADR 0013 §Operational notes checklist (NoNewPrivs/Seccomp/Cap/mount/unshare verifications).
5. Add invariants to `tests/architecture/test_compose_isolation_invariants.py` + new `tests/platform/security/test_seccomp_profile_sanity.py`.
6. Flip ADR 0013 §Deferred → §Closed with the closing iter reference.

### W22-3 — Attribution count parity (process + output channel events)

**Status**: **closed** — primary `cff10d3` + self-stamp (this commit).

**Goal**: Close `[FOLLOWUP attribution-count-parity-process-events]` and `[FOLLOWUP attribution-count-parity-output-channel]` by mirroring the W17-1 `attribution-count-parity` paterni (commits `8c26d02` + `0a8f59e`) byte-identical for two additional `EvidenceEvent` families: `kind="process"` and `kind="output_channel_appendline"`. Closes the silent divergence between evidence-side counters and summary-side counters for these event families (the W14 production scan divergence shape applied to non-activation events).

**Decision**: Apply the W17-1 producer-side stamp paterni — `is_target_<family> = bool(target_extension_id and entry.<extension_id_field> == target_extension_id)` computed once in the `build_evidence_bundle` loop, used both for the actor ternary (process events only — output events have `actor="harness"` unconditionally per ADR 0006) AND for the `EvidenceEvent.is_target_extension_event=` constructor argument. Two new count helpers in `summary.py` mirror `count_target_activations`. 4+4=8 invariant tests pin the parity contract.

**Changes**:

1. **`executor/flows/playwright/attribution/links.py`** — producer-side stamps at two emit sites:
   - Process loop (~L245): `is_target_process = bool(target_extension_id and process_event.related_extension_id == target_extension_id)` — used in actor ternary + EvidenceEvent constructor.
   - Output loop (~L294): `is_target_output = bool(target_extension_id and output_event.extension_id == target_extension_id)` — used in EvidenceEvent constructor.
   - Inline W22-3 audit-trail comment blocks cite W17-1 paterni + W14 production scan paterni.

2. **`executor/flows/playwright/health/summary.py`** — two new count helpers mirroring `count_target_activations`:
   - `count_target_process_events(events, target_extension_id)` — empty `target_extension_id` guard + sums `entry.related_extension_id == target_extension_id`.
   - `count_target_output_events(events, target_extension_id)` — empty `target_extension_id` guard + sums `entry.extension_id == target_extension_id`.

3. **`tests/executor/test_playwright_attribution_links.py`** — 8 new invariant tests appended after W17-1 activation tests (lines 481-601), mirroring the 4-test paterni for each family:
   - Process family: `test_build_evidence_bundle_process_event_flags_target_extension`, `_does_not_flag_non_target`, `_unflagged_when_no_target_set`, `test_build_evidence_bundle_target_process_parity_invariant` (parity contract pin).
   - Output family: `test_build_evidence_bundle_output_event_flags_target_extension`, `_does_not_flag_non_target`, `_unflagged_when_no_target_set`, `test_build_evidence_bundle_target_output_parity_invariant` (parity contract pin).
   - Import added: `OutputSignalEvent` from `executor.flows.playwright.runtime_capture.events`.

4. **`tests/architecture/test_executor_hotspot_loc_ratchet.py`** — `health/summary.py` LOC ceiling 537 → 552 with explicit W22-3 rationale comment (co-location with `count_target_activations` preferred over splitting since all three helpers share the same `build_automation_health` consumer call site at L228).

**Acceptance**: 8 new tests green; broader regression sweep (executor + marketplace + architecture + contracts) 1553 passed, 3 skipped, 4 deselected.

**Test bar delta**: `tests/executor/test_playwright_attribution_links.py` 30 → 38 passed (+8 W22-3). `tests/architecture/` 292 unchanged (LOC bump doesn't affect count). `make test-security` 228 unchanged.

**Live-run anchor**: not applicable (W22-3 is a producer-side stamp consistency fix; the change makes the existing fixture data flow correctly attributed, but doesn't add new runtime behavior that needs a fresh anchor). Next runtime gate is W22-2 chat coverage self-stamp.

### W22-2 — Chat hard-tier coverage promotion (static cut; live-run user-owned on Linux)

**Status**: **closed (static cut)** — primary `ffbb743` + self-stamp (this commit). **Runtime gate DEFERRED TO USER per direction 2026-05-28** (Linux required for docker stack).

**Goal**: Close `[GOAL taxonomy-chat-coverage]` — the last `missing` capability in `coverage_summary.missing_capabilities`. Implements ADR 0014 Option C (tool-only local coverage) at the harness + planner level. Hard tier closure target.

**Decision**: Mirror W21-2 comments promotion (`8948ea6` + `3088709`) byte-identical SHAPE-wise, with two W22-2 differences: (a) chat is a TWO-scenario family (`onChatParticipant:*` and `onLanguageModelTool:*` are distinct activation event families per ADR 0014 §API Surface Boundary); (b) `extension.js` is GREENFIELD for chat surfaces (no prior chat participant or LM tool code; W21-2's CommentController had partial code pre-existing).

**Changes** (7 files):

1. **`packages/analysis_planner/capabilities.py`** — two dict flips: `_GLOBAL_CAPABILITY_SUPPORT["chat"]` + `_OFFICIAL_CAPABILITY_SUPPORT["chat"]` both `"missing" → "covered"`.

2. **`packages/analysis_planner/scenarios.py`** — append two new `ScenarioDefinition` entries after `local_comments_controller`:
   - `local_chat_participant_controller` (covers `onChatParticipant:*`)
   - `local_language_model_tool_controller` (covers `onLanguageModelTool:*`)
   - Both: `activation_events=("onStartupFinished",)`, `api_capabilities=("commands", "window_ui", "chat")`, low risk.
   - Registry count 16 → 18.

3. **`executor/flows/harness_extension/extension.js`** — chat participant + LM tool registration block added in `activate()` after W21-2 CommentController block:
   - `_noopChatHandler` async no-op handler.
   - `_noopToolInvoke` returns `new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart("extrace-harness-noop")])` — synthesized in-process; no model call.
   - `vscode.chat.createChatParticipant("extrace.harness.chat", _noopChatHandler)` + push to `context.subscriptions`.
   - `vscode.lm.registerTool("extrace.harness.lm.tool", { invoke: _noopToolInvoke })` + push to `context.subscriptions`.
   - Baseline markers: `chat_participant_state` phase=`registered`, `lm_tool_state` phase=`registered`. Both route via `emitHarnessEvent` → reserved OutputChannel (W19-X Bug B paterni). Ephemeral lifecycle (W19-X Bug C lesson).
   - Engine compat: GA since VS Code 1.90; existing `engines.vscode: "^1.90.0"` covers; NO proposed APIs.

4. **`executor/flows/harness_extension/stimulus_dispatch.js`** — REPLACE pre-W22-2 incomplete UI-nav chat handler (L52-61 typed `@<participant> harness` into chat input box; did not exercise any chat API surface reliably) with two distinct API-level branches:
   - `onChatParticipant` branch: emits `chat_participant_state` phase=`stimulated` parser-confirmation marker (registration already fired the activation event at activate(); this marker confirms a stimulus pass exercised the family).
   - `onLanguageModelTool` branch: `await vscode.lm.invokeTool("extrace.harness.lm.tool", { input: { stimulus: value || "harness" } })` + emits `lm_tool_state` phase=`invoked` marker. try/catch emits phase=`invoke_failed` marker on error so surface changes don't silently fail.

5. **`tests/platform/contracts/test_capability_support_invariants.py`** — 5 new W22-2 invariants appended after W21-2 comments block:
   - `test_chat_official_track_is_covered`
   - `test_chat_heuristic_track_is_covered`
   - `test_chat_in_capability_taxonomy`
   - `test_local_chat_participant_controller_scenario_advertises_chat_capability`
   - `test_local_language_model_tool_controller_scenario_advertises_chat_capability`
   - Plus dict shape canonical pin at L562: `chat: "missing"` (W22-2 candidate comment) → `"covered"` (W22-2 promotion).
   - Test count: 26 → 31 (+5).

6. **`tests/platform/contracts/test_registry_split_regression.py`** — `test_split_did_not_lose_data_volume` count pin bump 16 → 18 with W22-2 rationale.

7. **`tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json`** — regen via `select_scenarios()` programmatic call (no hand-editing; deterministic projection). Net delta:
   - `coverage_summary.missing_capabilities: ["chat"] → []` (HARD TIER CLOSURE STATIC).
   - `coverage_summary` counts: covered 8 / partial 10 / missing 0 (was 8/9/1).
   - `chat` matrix entries (3 tracks): status `missing` → `partial`; support_status `missing` → `covered`; `supported_scenarios` populated with both new scenarios.
   - `commands` + `window_ui` matrix entries extended with the two new scenarios in registry order.

**Static acceptance (all green)**:

- `pytest tests/platform/contracts/test_capability_support_invariants.py` — 26 → 31 (+5 W22-2).
- `pytest tests/platform/contracts/test_registry_split_regression.py` — 8 passed (count pin 18).
- `pytest tests/workflows/marketplace/test_analysis_planner.py` — fixture parity green (regen reproduces expected output).
- `pytest tests/architecture/` — 292 unchanged.
- `pytest tests/executor/test_playwright_attribution_links.py` — 38 passed (W22-3 invariants unaffected).
- `make test-security` — 228 unchanged.
- Broader sweep — 631 passed, 2 skipped, 4 deselected.

**Runtime acceptance**: DEFERRED TO USER per direction 2026-05-28. Required action (Linux):

1. `make exec-up`
2. `make sim-target TARGET=ms-python.python`
3. Capture anchor `output/activation_report_ms-python.python-2026.5.*.json`
4. Verify must-pass: `coverage_summary.missing_capabilities == []`
5. Verify W19 invariants HOLD (Hat-1 `unaccounted_dropout_count = null`; Hat-2 `harness_verification_unconfirmed_present` NOT in `automation_health.reasons`)
6. If anchor diverges from static fixture, file W22-2-followup with the delta (W17-1-followup paterni).

**Live-run anchor**: PENDING (user-owned). Static side is fully aligned with the expected post-W22-2 state.
