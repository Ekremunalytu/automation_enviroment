# W21 Handoff — W21-3 Closed → W21-1 Başlangıcı (Yeni Session İçin)

`Status: HANDOFF — W21-0 closed (primary 8434323 + self-stamp 19bd9c7); W21-3 closed (primary c744c15 + self-stamp 4b0a1ed); W21-1 (testing coverage) sıradaki sub-iter per user-confirmed ordering W21-3 → W21-1 → W21-2.`
`Branch: week21 (cut from main @ 64a3c3d — W20 close-out PR #29 merge commit, 2026-05-26 23:10:21Z). 5 commits ahead, working tree clean, NOT pushed.`
`Authored: 2026-05-27 by previous session before context handoff to a W21-1 implementation session.`
`Owner: ekrem.`

> **Purpose.** Yeni Claude Code session'ı W21'i cold pick up edip **W21-1 (testing coverage)** implementation'a başlayabilsin diye self-contained briefing. Burada ne yazıyorsa, ona güven — doğruluğu eğer şüpheliysen cited file path + line number'lardan re-verify et. Bu doc'un yapamadığı şey: previous session'ın conversation context'ini geri vermek. O context kaybedildi ve bu doc o context'ten kritik olanı her şeyi yazıya döküyor.

---

## TL;DR — One Paragraph

W21 (Coverage Promotion Round 2: Mid Tier) `2/3` substantive sub-iter done. `week21` branch açık, **W21-0 closed** (`8434323` + `19bd9c7` + handoff `b4bf53f`) ve **W21-3 closed** (`c744c15` + `4b0a1ed`). 5 commit lokal (NOT pushed). Test bar yeşil (`tests/architecture/` **241 passed**, contracts `test_capability_support_invariants.py` 14 → 18, make test-security 220, full suite **2050 passed** / 9 skipped / 8 deselected). W21-3 live-run anchor `6fd7b959bd5a` (sha256 `fa83017a4de25e...d6f7477`) confirmed `coverage_summary.missing_capabilities = [chat, comments, testing]` (4 → 3 items, workspace_trust dropped). W20 invariants HOLD: Hat-1 `dropout=null`, Hat-2 `harness_verification_unconfirmed_present` DROPPED. **Sıradaki: W21-1 `[GOAL taxonomy-testing-coverage]`** — `_OFFICIAL_CAPABILITY_SUPPORT["testing"]: "missing" → "covered"` flip at `capabilities.py:97` + `_GLOBAL_CAPABILITY_SUPPORT` mirror at line 45 + `vscode.tests.createTestController` registration extension in harness (TestItem + createRunProfile zaten var, genişlet — W19-X HMAC reactivation race lesson: ephemeral TestItem default) + OutputChannel marker (W19-X paterni) + `local_test_controller` scenario in `scenarios.py` advertising `testing` + stimulus pass + 4 invariant tests (W20-1/W21-3 paterni mirror) + frozen trigger fixture regen via planner replay. W20-4 DESIGN doc `documents/architecture/comments-testing-readiness.md` §W21-1 plumbing template. **Push, PR, merge hepsi STRICT pause point — user "go" gerekli per turn, memory entry `feedback_pr_push_approval.md` standing authorization değil.**

---

## State On Disk

### Branch & Commit Audit Trail

`week21` branch on `main` @ `64a3c3d`. **5 commits ahead** (oldest first):

| # | SHA | Sub-Iter | Theme |
|---|---|---|---|
| 1 | `8434323` | W21-0 primary | doc-reconcile — open week21 + §19 promote from §19-§20 + 10-doc canonical preamble refresh + W21 Pull-Forward Acceptance Bar promotion + README phase-pointer arch gate transition W20→W21 + new W20 close-out fact gate `test_readme_phase_pointer_mentions_w20_closeout_merge` pinning PR #29 / week20 -> main / 64a3c3d |
| 2 | `19bd9c7` | W21-0 self-stamp | baseline live-run captured + W20 close-out invariants live-verified (anchor `600d9ecba5eb`, sha256 `1db1480551fd...c4477`) |
| 3 | `b4bf53f` | W21 handoff (previous) | self-contained briefing doc for the W21-3 session (THIS FILE; was created at this commit, now overwritten with the W21-1 handoff for the next session) |
| 4 | `c744c15` | **W21-3 primary** | feat — `_OFFICIAL_CAPABILITY_SUPPORT["workspace_trust"]: "missing" → "covered"` at `capabilities.py:99` + `_GLOBAL_CAPABILITY_SUPPORT:47` mirror + harness `vscode.workspace.isTrusted` baseline marker + `onDidGrantWorkspaceTrust` listener via reserved OutputChannel route + `workspace_trust_transition` scenario + 4 invariant tests + dict shape canonical pin update + `test_split_did_not_lose_data_volume` count bump 13→14 + frozen trigger fixture regen for ms-python.python |
| 5 | `4b0a1ed` | **W21-3 self-stamp** | W21-3 tracker row flip + §19 + POST_POC mirrors + 10-doc canonical preamble refresh + live-run anchor `6fd7b959bd5a` sha256 `fa83017a4de25e...d6f7477` |

Repro: `git log --oneline main..week21 | awk '{a[NR]=$0} END {for (i=NR; i>=1; i--) print a[i]}'`.

### Working Tree

`git status` → clean. No uncommitted changes. No untracked files (`output/activation_report_*.json` files are bind-mount artefacts — gitignored).

### Test Bar (latest, at W21-3 self-stamp `4b0a1ed`)

- `tests/architecture/`: **241 passed**, 4 deselected (unchanged from W21-0 self-stamp; W21-3 invariants live in contracts tier).
- `tests/platform/contracts/test_capability_support_invariants.py`: **18 passed** (14 pre-W21-3 + 4 new W21-3 invariants: `test_workspace_trust_official_track_is_covered`, `_heuristic_track_is_covered`, `_in_capability_taxonomy`, `_transition_scenario_advertises_workspace_trust_capability`).
- `make test-security`: **220 passed** (unchanged).
- Full suite (`.venv/bin/pytest -q`): **2050 passed, 9 skipped, 8 deselected** (+5 net from W20 baseline 2045: W21-0 +1 README phase-pointer gate + W21-3 +4 invariants).

### Live-Run Anchors

**Two anchors landed in W21 so far**:

**W21-0 baseline** (`output/activation_report_ms-python.python-2026.5.2026052501-600d9ecba5eb.json`):

- sha256: `1db1480551fd90625a5c7c2e474b43c4de3a867d35dab4aacc65e8060bcc4477`
- `coverage_summary.missing_capabilities = [chat, comments, testing, workspace_trust]` (4 items, byte-identical with W20-5)
- Hat-1 + Hat-2 hold

**W21-3 acceptance** (`output/activation_report_ms-python.python-2026.5.2026052501-6fd7b959bd5a.json`):

- sha256: `fa83017a4de25ea56c078da2bd7f65e2f54f10af5aa5c10e8ed000c92d6f7477`
- `coverage_summary.missing_capabilities = [chat, comments, testing]` (3 items — `workspace_trust` dropped)
- `covered / partial / missing = 8 / 7 / 3` (was 7/7/4)
- workspace_trust matrix: status `covered`, is_active=true, `supported_scenarios=["workspace_trust_transition"]`
- Hat-1 `unaccounted_dropout_count = null` (HOLDS)
- Hat-2 `harness_verification_unconfirmed_present` NOT in reasons (HOLDS)
- `event_attempts` count = 21 (unchanged)

**W21-3 live-run drift (non-invariant, W21-N close-out re-verify)**:

- `extra_trigger_failures_present` reason count = 9 (W21-0 baseline = 1; W20-5 = 0). Likely transient from previous failed analyze attempt left stale executor state mid-rebuild.
- New `chat_tool_verification_incomplete` reason — W22 surface (chat scenario verification), not in W20-5 / W21-0 baselines.

**W21-1 acceptance smoke** will produce a third anchor with `missing_capabilities` 3 → 2 items (`testing` dropped).

### Docker Stack (currently up — yeni session bunu kullanabilir)

`docker compose ps` at W21-3 self-stamp landing:

- `automation_db` postgres:16-alpine — Up healthy @ 127.0.0.1:5432
- `automation_db_test` postgres:16-alpine — Up healthy @ 127.0.0.1:5434
- `automation_api` — Up @ 127.0.0.1:8000 (rebuilt at W21-3 to pick up `packages/analysis_planner` changes)
- `automation_executor` — Up healthy @ 127.0.0.1:6080 (noVNC; rebuilt at W21-3 to pick up `executor/flows/harness_extension/extension.js` changes)
- `automation_ui` — Up @ 127.0.0.1:3000

**W21-1 stack rebuild requirements**:

- `executor` rebuild gerekiyor — harness extension JS değişecek (`vscode.tests.createTestController` extension).
- `api` rebuild gerekiyor — `packages/analysis_planner/capabilities.py` + `scenarios.py` değişecek.

---

## Plan Source & Related Docs

### Driving plan (kullanıcı-onaylı)

`/Users/ekrem/.claude/plans/week21-de-geli-tirmelere-ba-lad-m-rippling-finch.md` — W21-3 implementation planı; W21-1 için aynı paterni mirror edilebilir.

### Trackers + roadmap

- **W21 active tracker**: [`documents/active-work/W21-coverage-promotion-mid-tier.md`](W21-coverage-promotion-mid-tier.md) — Sub-Iter Scope table (W21-0 closed, W21-3 closed, W21-1 next), Per-Item Detail (W21-0 + W21-3 filled, W21-1/W21-2/W21-4/W21-N placeholders), Baseline Live-Run Smoke (W21-0 anchor), Risk Notes.
- **Multi-iter roadmap**: [`documents/active-work/W18-W22-roadmap.md`](W18-W22-roadmap.md) §W21 — sub-iter table.
- **§19 W21 plan source**: [`documents/REFACTOR_OPTIMIZATION.md`](../REFACTOR_OPTIMIZATION.md) §19 (W21 active, sub-iter slate + acceptance + ordering rationale).
- **W22 planning §20**: same file §20 (singular planning).
- **POST_POC W21 Pull-Forward**: [`documents/POST_POC_BACKLOG.md`](../POST_POC_BACKLOG.md) — W21-0 closed, W21-3 closed, W21-1/W21-2/W21-4/W21-N active acceptance bar.
- **W20-4 DESIGN doc (W21-1 + W21-2 PRIMARY UNBLOCKER)**: [`documents/architecture/comments-testing-readiness.md`](../architecture/comments-testing-readiness.md) — VS Code Test Controller API + Comments API surface envelope, plumbing şablonu (§W21-1 testing primary), 5 open questions (Q4 about workspace_trust ordering already resolved with "yes" → W21-3 landed first).

### Frozen prior phase trackers

- W20 frozen: [`W20-coverage-promotion-easy-wins.md`](W20-coverage-promotion-easy-wins.md) (closed PR #29 / 64a3c3d).
- W19 frozen: [`W19-live-run-root-cause.md`](W19-live-run-root-cause.md).
- W18 frozen: [`W18-heartbeat-refactor.md`](W18-heartbeat-refactor.md).

---

## W21 Sub-Iter Slate (this handoff's anchor state)

| Iter | Status | Stable ID | Theme |
|---|---|---|---|
| W21-0 | **closed `2026-05-27`** via primary `8434323` + self-stamp `19bd9c7` | — | doc-reconcile + baseline live-run |
| W21-3 | **closed `2026-05-27`** via primary `c744c15` + self-stamp `4b0a1ed` | `[GOAL taxonomy-workspace-trust-coverage]` | `workspace_trust` taxonomy + harness observability + scenario + invariants |
| **W21-1** | **planned (NEXT — bu handoff sırada)** | `[GOAL taxonomy-testing-coverage]` | `testing` both tracks → covered |
| W21-2 | planned (after W21-1) | `[GOAL taxonomy-comments-coverage]` | `comments` both tracks → covered |
| W21-4 | **STRETCH (conditional pull)** | `[GOAL container-hardening-baseline]` | docker-compose + seccomp + read_only + ADR 0013 — W21-3 closed cleanly so W21-4 candidate stays in conditional-pull window |
| W21-N | placeholder (after substantive sub-iters) | — | close-out hygiene + final live-run + PR week21 -> main PENDING USER APPROVAL |

---

## What's Next: W21-1 Testing Coverage

### Goal

`_OFFICIAL_CAPABILITY_SUPPORT["testing"]: "missing" → "covered"` flip at [`packages/analysis_planner/capabilities.py:97`](../../packages/analysis_planner/capabilities.py) + mirror in `_GLOBAL_CAPABILITY_SUPPORT` (line 45) + end-to-end harness plumbing exercising `vscode.tests` Test Controller API.

### Acceptance criteria (must-pass at W21-1 closure)

1. `_OFFICIAL_CAPABILITY_SUPPORT["testing"]` = `"covered"`.
2. `_GLOBAL_CAPABILITY_SUPPORT["testing"]` = `"covered"` (heuristic auto-derives).
3. W20-3 invariant `test_official_track_is_subset_of_heuristic` (Official ⊆ Heuristic) — automatic since both flip together.
4. Yeni `local_test_controller` scenario advertises `testing` capability in `api_capabilities` tuple.
5. Harness side: extend existing `extrace.harness.tests` TestController stub with full TestItem hierarchy + createRunProfile (Run + Debug) + OutputChannel markers.
6. 4 yeni invariant test at `tests/platform/contracts/test_capability_support_invariants.py` (W20-1/W21-3 paterni mirror).
7. Frozen trigger fixture `tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json` re-generated via planner replay.
8. Static suite green; dict shape canonical pin update (line ~284 area) — `"testing": "missing"` → `"testing": "covered"`.
9. `test_split_did_not_lose_data_volume` count bump 14 → 15 (yeni scenario).
10. Live-run smoke `missing_capabilities` 3 → 2 items (`testing` dropped); W20 invariants HOLD.

### Current state of `testing` capability infrastructure

**Already in place** (pre-W21-1):

- `extension.js:191-211` — basic TestController stub at activate(): `vscode.tests.createTestController("extrace.harness.tests", ...)` + 1 TestItem (`Harness Smoke`) + 2 RunProfiles (Run + Debug, no callback bodies, just `() => {}`).
- `_GLOBAL_CAPABILITY_NOTES["testing"]` at `capabilities.py:71-74`: "Testing coverage uses local controllers and run/debug flows without calling external test services." — policy text already in place.
- Test Controller infra: `vscode.tests.createTestController`, `TestItem`, `createRunProfile`, `TestRunProfileKind.Run/Debug` all referenced in harness.

**Missing for W21-1 closure**:

- TestController stub is **silent** — no OutputChannel marker emission when run profile invoked. Need to wire run/debug callback bodies to emit harness markers like the W21-3 trust-state pattern.
- No `local_test_controller` scenario in `scenarios.py` advertising `testing` capability.
- Capability dict still says `"missing"`.
- No invariant tests pinning these.
- Frozen fixture has `testing` marked missing.

### Scope (per [`W18-W22-roadmap.md`](W18-W22-roadmap.md) §W21)

> "Local test controller + run/debug flow stub. `_GLOBAL_CAPABILITY_NOTES` policy: external test services yasak."

### W20-4 DESIGN doc §W21-1 (PRIMARY reference)

Read [`documents/architecture/comments-testing-readiness.md`](../architecture/comments-testing-readiness.md) §W21-1 in full before touching code. Key takeaways:

- **Marker emission pattern**: Use `markers.js` `emitHarnessEvent` via OutputChannel route (W19-X Bug B paterni — NOT `console.log`).
- **Scenario shape**: New scenario with `api_capabilities` tuple + `activation_events` list + planner registry wire-in.
- **4-test pattern**: Official-track flip + heuristic-track pin + taxonomy membership + scenario-capability pairing.
- **Ephemeral TestItem default** (W19-X HMAC reactivation race lesson): TestItems should be created fresh per run, not cached across reactivations.

### Critical files to explore

- [`packages/analysis_planner/capabilities.py`](../../packages/analysis_planner/capabilities.py) — `_OFFICIAL_CAPABILITY_SUPPORT` at line 81-100, `_GLOBAL_CAPABILITY_SUPPORT` at line 29-48. **`testing` is at line 45 (_GLOBAL_) + line 97 (_OFFICIAL_)**.
- [`packages/analysis_planner/scenarios.py`](../../packages/analysis_planner/scenarios.py) — SCENARIO_REGISTRY; new `local_test_controller` scenario mirroring `git_workflow` / `workspace_trust_transition` shape.
- [`executor/flows/harness_extension/extension.js:191-211`](../../executor/flows/harness_extension/extension.js) — existing TestController stub. **Extend** with marker emission in run/debug profile callbacks + ephemeral TestItem rebuild.
- [`executor/flows/harness_extension/markers.js`](../../executor/flows/harness_extension/markers.js) — `emitHarnessEvent` already wired (W19-X Bug B paterni); reuse for `kind: "test_controller_event"` payloads.
- [`tests/platform/contracts/test_capability_support_invariants.py`](../../tests/platform/contracts/test_capability_support_invariants.py) — W20-1 (scm) + W20-2 (settings) + W21-3 (workspace_trust) paterni; 4 new tests for W21-1 + dict shape pin update.
- [`tests/platform/contracts/test_registry_split_regression.py`](../../tests/platform/contracts/test_registry_split_regression.py) — `test_split_did_not_lose_data_volume` SCENARIO_REGISTRY count pin (currently 14, bump to 15).
- [`tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json`](../../tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json) — frozen trigger fixture; planner replay regen.
- [`packages/analysis_planner/coverage.py:309-333`](../../packages/analysis_planner/coverage.py) — coverage matrix builder; not edited, but understand consumption.

### Recommended approach (mirror W21-3 paterni)

1. **Read W20-4 DESIGN doc §W21-1** + commit `c744c15` (W21-3 primary) diff for paterni: `git show c744c15`.
2. **Extend harness TestController** (`extension.js:191-211`): wire run profile callbacks to `emitHarnessEvent({kind: "test_controller_event", phase: "run_invoked", ...})` + debug profile to `phase: "debug_invoked"`. Ephemeral TestItem: clear + rebuild items on each invocation.
3. **Add `local_test_controller` scenario** to `scenarios.py`:

   ```python
   ScenarioDefinition(
       name="local_test_controller",
       intent=(
           "Exercise local Test Controller API (TestItems + run/debug "
           "profiles) for extensions that contribute test discovery."
       ),
       activation_events=("onCommand",),  # or "onStartupFinished" if scenario should trigger broadly; check selection.py logic
       contributes_signals=("commands",),
       api_capabilities=("commands", "window_ui", "testing"),
       prerequisites=("test workspace fixture available",),
       success_signals=("test run invoked", "test debug invoked"),
       risk_of_noise="low",
   ),
   ```

   Update `test_split_did_not_lose_data_volume` count 14 → 15.
4. **Flip capability dicts**: `capabilities.py:45` + `:97` "missing" → "covered".
5. **Add 4 invariant tests** to `test_capability_support_invariants.py` (mirror W21-3 block at lines 141-200):
   - `test_testing_official_track_is_covered`
   - `test_testing_heuristic_track_is_covered`
   - `test_testing_in_capability_taxonomy`
   - `test_local_test_controller_scenario_advertises_testing_capability`
   Plus update dict shape pin (line ~282): `"testing": "missing"` → `"covered"` with W21-1 promotion comment.
6. **Run local pytest**: contracts + registry-split should pass.
7. **Regen frozen fixture**: planner replay via inline Python (see W21-3 paterni in conversation history — `select_scenarios()` → `payload.model_dump(mode="json")` → write).
8. **Stack rebuild + live-run smoke**:
   - `docker compose up -d --build executor api` (~5 min).
   - Trigger analyze for ms-python.python via UI (`http://127.0.0.1:3000`) or API (`POST /api/marketplace/analyze/start` with `{publisher, name, version: "2026.5.2026052501"}`).
   - Capture new anchor JSON + verify `missing_capabilities` 3 → 2 items (`testing` dropped).
9. **Primary commit + self-stamp commit** (W21-3 paterni mirror).
10. **PAUSE** — push/PR için kullanıcı "go" bekle.

### Open research questions (W21-1 başlamadan önce cevaplanmalı)

1. **VS Code Test Controller API surface for ms-python.python**. `ms-python.python` testing capability uses `vscode.tests.createTestController` internally for `pytest`/`unittest` discovery. Manifest declares `onStartupFinished` activation. Will the `local_test_controller` scenario get selected for ms-python.python? Check `selection.py` selection logic for `testing` capability — does anything in the planner trigger it for extensions with Test Controller declarations?
2. **Activation event choice**. `local_test_controller` scenario activation:
   - `("onCommand",)` — broad, but might never trigger explicitly
   - `("onStartupFinished",)` — fires for all extensions with that activation event (likely too broad)
   - Custom event? — check if any planner detection logic adds `testing` to `official_extra_capabilities` (mirror `selection.py:322` `untrusted_supported` logic for trust)
3. **Harness TestController extension shape**. Existing stub creates 1 TestItem + 2 RunProfiles with empty callbacks. Options:
   - **Minimal extension**: just wire run/debug callbacks to emit markers (no extra TestItems)
   - **Richer extension**: build a small TestItem tree (parent + leaf), exercise `TestRun` API with status updates
   - **Programmatic invocation**: also expose `extrace.harness.runHarnessTestRun` command that triggers a synthetic run
   - Lean toward minimal — full closure can come at W21-N follow-up if needed.
4. **Stimulus pass shape**. Trigger run via what mechanism?
   - **UI-driven**: Playwright clicks Test Explorer item run button (requires Test Explorer view registered + visible)
   - **Programmatic**: harness command `vscode.commands.executeCommand("testing.runAll")` from `dispatchStimulus`
   - Decision: programmatic is preferred (W21-3 paterni — harness observes, doesn't drive UI).
5. **Frozen fixture impact**. After scenario add, will `local_test_controller` land in ms-python.python's `selected_scenarios`? Likely **no** in static fixture (planner_input doesn't include `capability_metadata.testing_supported` shape — none defined). Fixture diff will still show:
   - `coverage_summary.missing_capabilities` drops `testing` (taxonomy flip propagates).
   - `covered/partial/missing` counts shift.
   - `testing` matrix entry status: `missing` → `partial` (taxonomy `covered` but scenario not selected for ms-python.python in static fixture).
   - `supported_scenarios` populated with `local_test_controller`.
   - This is **acceptable** per W21-3 scm paterni mirror (taxonomy covered, matrix partial when scenario not selected).
6. **Scope-explode → defer**. Eğer harness TestController extension restructuring gerektirirse (ephemeral TestItem rebuild design hatası gibi), W21-1'i DESIGN-only olarak W22'ye defer et — W20-4 / W21-3 paterni mirror, sadece DESIGN doc land et + tracker'da fallback rationale belgele. Erken al, deeply implemente etmeden.

### Commit cadence (mirror W21-3)

**Primary commit message draft**:

```text
feat(W21-1): testing official-track promotion (missing → covered) + harness Test Controller marker emission + scenario + 4 invariant tests + fixture regen

Closes `[GOAL taxonomy-testing-coverage]` (W21-1) at
`POST_POC_BACKLOG.md` W21 Pull-Forward Acceptance Bar. Second
substantive W21 sub-iter per user-confirmed ordering W21-3 → W21-1
→ W21-2; workspace_trust precondition closed at W21-3.

[Body — 3 layers: taxonomy flip + harness extension + scenario;
invariant tests + fixture regen + scope decisions + test bar delta]

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**Self-stamp follow-up**: tracker row flip + §19 + POST_POC + 10-doc preamble refresh + live-run anchor.

---

## Constraints — User Direction & Memory

### Persistent memory (`feedback_pr_push_approval.md`)

> "never push to remote or open/merge/close PRs without an explicit user 'go ahead' in the same turn; plan-mode allowedPrompts ≠ standing authorization."

**Implication**: `git push origin week21` — STRICT PAUSE. `gh pr create` — STRICT PAUSE. `gh pr merge` — STRICT PAUSE. **Push/PR are not authorized; user must say "go" per turn**.

### User direction (2026-05-27)

- W21-3 → W21-1 → W21-2 sıralama onaylı (W21-3 zaten kapandı, sıra W21-1'de).
- W21-4 stretch conditional pull (only if W21-0..W21-3 closed cleanly — **W21-3 closed cleanly**, so W21-4 stays in conditional-pull window; final decision at W21-N).
- `[FOLLOWUP sandbox-reset-stale-state-multi-analyze]` opportunistic at W21-N close-out window.
- `[FOLLOWUP workspace-trust-stimulus-pass]` W22 candidate (W21-3 filed this; runtime untrusted → granted exercise; needs fixture restructuring).
- All work on `week21` branch, sub-iter commits land there, close-out PR `week21 -> main` opens at W21-N PENDING USER APPROVAL.

### Auto mode

Previous session was in auto mode ("bias toward working without stopping for clarifying questions — but stop when genuinely blocked"). Yeni session başlangıçta user-direction olmalı: kullanıcı W21-1'e başlamak için açık komut versin (örneğin "W21-1 başla" / "devam" / "testing coverage'a başla").

---

## STRICT Pause Points (yeni session muhakkak bilsin)

1. **Push to `origin/week21`** — user-gated per turn. `git push -u origin week21` only with same-turn user "go".
2. **PR create** — user-gated per turn. `gh pr create --base main --head week21` only at W21-N close-out + with user "go".
3. **PR merge** — user-gated per turn. `gh pr merge ...` never automatic.
4. **Container builds** — Live-run requires `docker compose up -d --build executor api` (~5-10 min). Stack zaten ayakta olabilir (yukarıdaki Docker Stack section'a bak), ama W21-1 değişiklikleri için her iki container'ın da rebuild gerekli. Minor pause point, not strict.
5. **W21-1 scope explode** — Eğer harness TestController restructuring çok karmaşık olursa (örn. ephemeral TestItem design hatası), paused state'te user'a sor: "DESIGN-only defer to W22 mu?". Mirroring W17-3/W17-4 → W18 paterni.

---

## Quick Sanity Commands (yeni session'ın ilk yapması gereken)

```bash
# 1. Verify branch state
git rev-parse --abbrev-ref HEAD                     # → week21
git log --oneline main..week21 | wc -l              # → 5 commits
git log --oneline main..week21                      # → 5 commits (4b0a1ed, c744c15, b4bf53f, 19bd9c7, 8434323)
git status                                          # → clean

# 2. Verify test bar
.venv/bin/pytest tests/architecture/ -q             # → 241 passed, 4 deselected
.venv/bin/pytest tests/platform/contracts/test_capability_support_invariants.py -v  # → 18 passed
make test-security                                  # → 220 passed

# 3. Verify W21-3 anchor + sha256
shasum -a 256 output/activation_report_ms-python.python-2026.5.2026052501-6fd7b959bd5a.json
# → fa83017a4de25ea56c078da2bd7f65e2f54f10af5aa5c10e8ed000c92d6f7477  <path>

# 4. Inspect key fields (re-confirm W21-3 acceptance holds)
jq '{automation_health_status: .automation_health.status, reasons: .automation_health.reasons, missing_capabilities: .coverage_summary.missing_capabilities, unaccounted_dropout_count: .automation_health.unaccounted_dropout_count, workspace_trust_official: (.coverage_matrix[] | select(.capability == "workspace_trust" and .track == "official") | {status, is_active, supported_scenarios})}' \
  output/activation_report_ms-python.python-2026.5.2026052501-6fd7b959bd5a.json
# Expected: status=degraded, missing=[chat, comments, testing] (3 items), dropout=null, workspace_trust.status=covered + is_active=true + supported_scenarios=["workspace_trust_transition"]

# 5. Verify stack state (rebuild for W21-1 likely needed; both executor and api)
docker compose ps                                   # → all 5 services up + healthy (or down — restart if needed)
```

Eğer herhangi biri farklılaşırsa: durup investigate et, bu doc'a göre divergence'ı analiz et, user'a state hakkında soru sor.

---

## Plan File Reference

Driving plan (W21-3'ten): `/Users/ekrem/.claude/plans/week21-de-geli-tirmelere-ba-lad-m-rippling-finch.md`. W21-1 yeni session yeni plan dosyası yazabilir (plan mode'a girip). Aynı W20-1 / W21-3 paterni mirror — taxonomy flip + harness extension + scenario + 4 invariant + fixture regen.

### W21-3 reference paterni (commit'lere bak)

- `git show c744c15` — W21-3 primary, 6 files +146/-34. Templates: capabilities.py flips, scenarios.py addition, extension.js trust listener, test_capability_support_invariants.py 4 new tests + dict shape pin, test_registry_split_regression.py count bump, frozen fixture regen.
- `git show 4b0a1ed` — W21-3 self-stamp, 10 files +99/-20. Templates: 10-doc preamble refresh + tracker per-item detail fill.

### W20-1 reference paterni (older — scm flip, originating template)

- `git show 82276cb` — W20-1 primary (scm).
- `git show a17e595` — W20-1 self-stamp.

---

## End of Handoff

W21-3 tüm artifact'leri stabilize, lokalde. Yeni session bu doc + W20-4 DESIGN doc §W21-1 + W21 tracker + W21-3 commits paterni ile W21-1'e başlayabilir. **Push / PR / merge için user-go gerekli; her turn bağımsız onay alınmalı.**

W21-3 live-run anchor `6fd7b959bd5a` yeni session'ın referans anchor'ı: W21-3 acceptance live-verified (workspace_trust dropped from missing_capabilities), W20 invariants hold. W21-1 implementation post-flip'lerini bu anchor'a karşı diff'leyerek doğrulayacak — beklenti: `missing_capabilities` 3 → 2 items (`testing` dropped).
