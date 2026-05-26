# W19-X Handoff — HMAC Nonce Reactivation Race + Pending Live Verification

> **STATUS: SUPERSEDED — frozen `2026-05-26` at W19-6 close-out.**
> W19-X primary landed at `8b7b7f6` and self-stamp at `a3e634f`. This
> handoff doc was authored mid-session before commits landed; the
> "IN-FLIGHT, NOT COMMITTED" framing below is stale. The "Next steps"
> instructions (Step 1 / Step 2 / Step 3) have been executed and live
> verification passed (live anchor
> `output/activation_report_ms-python.python-2026.5.2026052501-8247e05ec9ef.json`
> shows 2/2 onDebug* attempts stamped with `confirmation_source="harness_nonce"`
> and suppressed `failure_reason_code`).
>
> **Why this doc is kept frozen rather than deleted**: the "Problem
> genealogy (the three bug classes uncovered during W19-4 live
> verification)" section below is irrecoverable narrative context for
> future ADR work on HMAC secret distribution (W13-1 design + VS Code
> reload cycle interaction). The "Risk register" entry on the W13-1
> design assumption migrated to POST_POC_BACKLOG.md as `[FOLLOWUP
> harness-secret-distribution-redesign]` at W19-6 close-out; the
> "extra reactivation source" follow-up migrated to W18-W22-roadmap.md
> W20-0 forward-ref block as `[FOLLOWUP harness-secret-extra-reactivation-source]`.
> Refer to those backlog entries for the actionable next steps; this
> doc is bug-genealogy archaeology only.

---

**Original status (frozen)**: IN-FLIGHT, NOT COMMITTED. Source surface and tests changed; W19-4 primary
landed at `7d44b0e`. The W19-X follow-up sub-iter (3 pre-existing bug classes
surfaced during W19-4 live verification) has partial fixes applied to working tree
but **no W19-X commit yet** and **live verification has not been re-run with the
latest defensive polling fix**.

**Branch**: `week19` (no new branch — user direction `2026-05-21`, W11-W18 paterni).

**Why this handoff doc exists**: Context from the prior session is bloated.
Everything a new session needs to pick up cold is captured here. Do not re-do
investigation that this doc settles; do verify the assertions are still true by
reading the cited files at the cited line numbers.

---

## TL;DR for the next session

1. **W19-4 (Half A + Half B + 15 tests) is landed at `7d44b0e`** — source on
   disk reflects this. Don't touch `reconciliation.py` lines 85-94 (Half B
   consumer guard) or 347-348 (Half A producer stamp) unless you have a new
   reason; W19-4 acceptance is met for the source surface.
2. **W19-X (3 follow-up bug classes) source fixes are in working tree but
   uncommitted.** The next action is *not* "design" — it is "rebuild executor
   container with current working tree, run a fresh `ms-python.python`
   analyze via the UI, verify HMAC nonce stamps on at least one onDebug*
   attempt." If verification passes → primary + self-stamp commits. If it
   still fails → continue debugging on the polling fix or move secret
   distribution to a longer-lived strategy.
3. **The fix being verified is `extension.js` defensive polling** (30 attempts
   × 100 ms = 3 s ceiling) for the HMAC secret file. Earlier fixes (channel
   routing, parser glob, `--secret-only` mode, `_rewrite_harness_secret`) are
   already in working tree and were validated separately, but the previous live
   run still saw 2 of 3 reactivations read ENOENT for `/run/extrace/harness-secret`.
   The polling layer is the latest defense and **has not been tested in live
   yet** (container has not been rebuilt since the change).

---

## Working-tree changes (uncommitted)

`git diff HEAD --stat` summary (20 files, +247 / -63):

| File | What changed | Lane |
|---|---|---|
| [executor/flows/harness_extension/extension.js](../../executor/flows/harness_extension/extension.js) | (a) `consumeHarnessNonceSecret` is now async with 30×100ms polling loop. (b) `HARNESS_OUTPUT_CHANNEL_NAME` constant; hook skips it. (c) `setHarnessChannel(harnessChannel)` after createOutputChannel. (d) `_diag("activate_enter", _secretConsumeDiag)` records `poll_attempts` + `has_secret`. | W19-X-1 marker pipeline + reactivation race |
| [executor/flows/harness_extension/markers.js](../../executor/flows/harness_extension/markers.js) | `_harnessChannel` module var + `setHarnessChannel(channel)` + `_emitMarkerLine` helper; `emitHarnessMarker` + `emitHarnessEvent` route through channel instead of `console.log`. Console.log fallback preserved for dev mode. | W19-X-1 |
| [executor/container/launch_vscode.sh](../../executor/container/launch_vscode.sh) | `--secret-only` mode: writes both secret paths then exits without launching VS Code. Called by `reload_vscode.py` before CDP reload. | W19-X-1 |
| [executor/flows/playwright/reload_vscode.py](../../executor/flows/playwright/reload_vscode.py) | `_rewrite_harness_secret()` calls `bash launch_vscode.sh --secret-only` before `reload_window()`. New `# arch-allow: bare-binary-path` pragma → ratchet baseline 6→7. | W19-X-1 |
| [executor/flows/playwright/monitor/sources.py](../../executor/flows/playwright/monitor/sources.py) | `read_extension_host_output` reads from `output_logging_*/*ExTrace Harness.log` (channel log files) in addition to `exthost.log`. Markers land in channel log; the prior parser missed them. | W19-X-1 |
| [executor/flows/playwright/runtime_capture/extension_host_log_parse.py](../../executor/flows/playwright/runtime_capture/extension_host_log_parse.py) | Mirror fix to the second `read_extension_host_output` function in the runtime_capture module. **Note: the LIVE path uses `monitor/sources.py`**, this file is captured for completeness / future test runs. | W19-X-1 |
| [packages/analysis_planner/attempts.py](../../packages/analysis_planner/attempts.py) | `_resolve_executor_action` onDebug family: `"extra:debug_lifecycle"` → `"harness:run_current_stimulus"`. Routes through `runCurrentStimulus` so the signed completion marker is emitted. | W19-X-2 |
| [tests/architecture/test_bare_binary_pragma_ratchet.py](../../tests/architecture/test_bare_binary_pragma_ratchet.py) | `_BASELINE_PRAGMA_COUNT: 6 → 7`; added `reload_vscode.py: 1` to distribution. | W19-X-1 ratchet bump |
| [tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json](../../tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json) | Planner replay output: onDebug attempts now have `"executor_action": "harness:run_current_stimulus"`. | W19-X-2 fixture regen |
| [tests/workflows/marketplace/test_triggers.py](../../tests/workflows/marketplace/test_triggers.py) | `test_on_debug_selects_debug_session` assertion updated to `"harness:run_current_stimulus"`. | W19-X-2 |
| `documents/POST_POC_BACKLOG.md`, `documents/REFACTOR_OPTIMIZATION.md`, `documents/active-work/W18-W22-roadmap.md`, `documents/active-work/W19-live-run-root-cause.md`, `documents/REFACTOR_STATUS.md`, `documents/AGENT_CONTEXT.md`, `documents/active-work/README.md`, `AGENTS.md`, `CLAUDE.md`, `README.md` | 8-doc canonical preamble + tracker placeholder text. **NOT YET LIVE-VERIFIED**, so the preamble copy still has `LIVE-PENDING` markers. Should be finalized in the W19-X self-stamp commit after live passes. | doc trail |

`main` directory exists at repo root as an untracked entry (pre-existing
oddity, not introduced by this work — leave alone).

---

## Problem genealogy (the three bug classes uncovered during W19-4 live verification)

W19-4 source surface landed at `7d44b0e`. First live UI analyze run on
`ms-python.python` (2026-05-25) showed `confirmation_source` still `"none"` on
all 21 event_attempts. Three independent bug classes were isolated:

### Bug A — Planner routing (W19-X-2, source fix applied, tests green)

**Symptom**: onDebug* attempts had `executor_action == "extra:debug_lifecycle"`
in the planner output; that branch never invokes
`runCurrentStimulus`, so no signed `start`/`complete` marker is ever emitted.

**Root cause**: [packages/analysis_planner/attempts.py:224-231](../../packages/analysis_planner/attempts.py)
mapped the onDebug family to a legacy direct-action branch instead of the
harness command. Pre-W19, no consumer cared because no one was looking at
harness markers for onDebug; W19-4 changed that — and exposed the gap.

**Fix**: switched the executor_action to `"harness:run_current_stimulus"`,
regenerated `tests/workflows/marketplace/fixtures/trigger_payloads/ms_python_python.json`
via planner replay, updated [tests/workflows/marketplace/test_triggers.py:66](../../tests/workflows/marketplace/test_triggers.py).

**Status**: GREEN in synthetic. Will be live-verified together with B + C.

### Bug B — Marker pipeline log destination (W19-X-1, layers a + b + c applied)

**Symptom**: Even after Bug A fix, parser still saw no `[extrace-harness]`
lines. Investigation: harness markers were going to `console.log`, which VS
Code's Extension Host writes only to stdout/stderr, which
[executor/container/launch_vscode.sh:91](../../executor/container/launch_vscode.sh) discards
with `</dev/null >/dev/null 2>&1 &`.

**Layered fix**:

- **Layer a (markers.js)**: introduce `setHarnessChannel` + `_emitMarkerLine`;
  route emitters through an OutputChannel (whose backing log file the
  parser already reads).
- **Layer b (extension.js)**: register the channel under
  `HARNESS_OUTPUT_CHANNEL_NAME = "ExTrace Harness"`; install the
  OutputChannel hook *before* createOutputChannel, but make the hook skip
  the harness channel itself (otherwise every marker would recursively
  emit an `output_channel_appendline` marker, blowing up the parser).
- **Layer c (monitor/sources.py)**: extend `read_extension_host_output`
  to read `output_logging_*/*ExTrace Harness.log` files — the per-channel
  log files VS Code writes. Note: there are two functions named
  `read_extension_host_output` in this repo
  ([monitor/sources.py:177](../../executor/flows/playwright/monitor/sources.py) is
  the LIVE path,
  [runtime_capture/extension_host_log_parse.py:311](../../executor/flows/playwright/runtime_capture/extension_host_log_parse.py)
  is the test/replay path); both were updated.

**Status**: layers GREEN in container manual test (markers reach channel
log; parser reads channel log). Live test on its own — partial: markers do
reach the parser, but most attempts still showed unsigned markers because
of Bug C below.

### Bug C — HMAC secret ENOENT on reload reactivations (W19-X-1 reactivation race)

**Symptom**: After A + B, live diagnostic showed `_diag("activate_enter", ...)`
records with `pre_existed: false, has_secret: false, read_error: "ENOENT"`
for **2 of 3 reactivations** in the lifetime of a single analyze run. Only
the first activate (boot launch via `start.sh → launch_vscode.sh`) saw the
secret; reload-driven reactivations read empty → fell back to unsigned →
verifier (correctly) rejects as unverified.

**Root cause is W13-1 (Codex H6) design assumption**: the per-launch secret
file lives only between `launch_vscode.sh` write and `activate()` read +
unlink. The design assumed ONE `activate()` per VS Code lifetime, but CDP
`Page.reload()` (called by [reload_vscode.py](../../executor/flows/playwright/reload_vscode.py))
restarts the Extension Host, which runs `activate()` again — and the secret
file is already unlinked from the first activate.

**Fix-in-progress (two layers)**:

1. **Pre-reload secret rewrite (CONFIRMED in tree, validated in isolation)**:
   - [executor/container/launch_vscode.sh:61-67](../../executor/container/launch_vscode.sh)
     added a `--secret-only` mode that writes both
     `/run/extrace/harness-secret` and `/results/_extrace_harness_python_secret`,
     then exits without launching VS Code.
   - [executor/flows/playwright/reload_vscode.py:32-54](../../executor/flows/playwright/reload_vscode.py)
     calls `bash launch_vscode.sh --secret-only` immediately before
     `reload_workbench_window()` so the reactivating Extension Host finds
     a fresh secret on disk.

2. **Defensive polling in the extension (LATEST, NOT LIVE-TESTED)**:
   - [executor/flows/harness_extension/extension.js:32-71](../../executor/flows/harness_extension/extension.js)
     turned `consumeHarnessNonceSecret` async, with a 30 × 100 ms polling
     loop. If the file isn't there yet, retry up to 3 s. Returns
     `poll_attempts` + `has_secret` so the next live run will show in
     `1-ExTrace Harness.log` whether the race got resolved by polling or
     never resolved at all.

**Why polling is defense-in-depth, not the primary fix**: the primary fix
is the pre-reload rewrite. Polling is for the case where there is *another*
reactivation path that the orchestration doesn't know about — most
plausibly an `install_extension` action whose internal reload isn't gated
by `reload_window()._rewrite_harness_secret`. If polling resolves it
(`poll_attempts: 5-25, has_secret: true`), then we should hunt down that
extra reactivation source for a clean fix. If polling exhausts
(`poll_attempts: 30, has_secret: false`), then we need a different
distribution strategy (probably "stop unlinking the secret file; keep it
0400; rely on container-restart for temporal isolation").

---

## What to do next (in order)

### Step 1 — Rebuild executor + run live analyze

```bash
docker compose up -d --build api executor
# Wait for both services to be healthy.

# Then, via the UI at http://localhost:8000/ (or whichever port the api
# service maps to), trigger an analyze run on the marketplace fixture
# `ms-python.python` (publisher `ms-python`, name `python`).
# This goes through the W17-2 lifecycle harness path that the prior live
# run used; do NOT use sim-target — per W19-0 baseline finding,
# sim-target does not reproduce the live shape.
```

### Step 2 — Inspect the resulting activation report

```bash
ls -lat output/activation_report_ms-python.python-*.json | head -1

REPORT=$(ls -t output/activation_report_ms-python.python-*.json | head -1)

# Acceptance check 1: at least one onDebug* attempt stamped.
jq '[.event_attempts[]
     | select(.event_family | startswith("onDebug"))
     | select(.confirmation_source == "harness_nonce")] | length' "$REPORT"
# Expect: >= 1

# Acceptance check 2: those stamped attempts no longer carry the
# unconfirmed failure_reason_code.
jq '[.event_attempts[]
     | select(.event_family | startswith("onDebug"))
     | select(.confirmation_source == "harness_nonce")
     | select(.failure_reason_code != "harness_verification_unconfirmed")]
     | length' "$REPORT"
# Expect: same number as above.

# Diagnostic check (does polling fix the reactivation race?):
# Look at the activate_enter records the harness emits.
docker compose exec executor bash -c '
  ls -lat /home/executor/.vscode/logs/*/exthost*/output_logging_*/*"ExTrace Harness".log 2>/dev/null | head -5
'
# Then read each one; each should have one activate_enter line with the
# diagnostic struct.
```

### Step 3 — Branch on the verification result

**If acceptance checks 1 + 2 PASS** (>= 1 stamped onDebug + suppressed reason):

- Verify the diagnostic shows `has_secret: true` on every activate_enter.
  - If `poll_attempts: 1` everywhere → pre-reload rewrite alone resolved it,
    polling is unused defense.
  - If `poll_attempts > 1` on some activate_enter records → polling
    rescued reactivations the rewrite missed. Open a follow-up
    `[FOLLOWUP harness-secret-extra-reactivation-source]` to find which
    code path (probably `install_extension`) triggers reload without
    going through `_rewrite_harness_secret`. Keep polling as defense.
- Finalize the W19-X self-stamp:
  - Replace `LIVE-PENDING` placeholders in [W19-live-run-root-cause.md](W19-live-run-root-cause.md)
    with the live evidence (JSON path, jq counts, commit SHA).
  - 8-doc canonical preamble refresh (mirrors `9b56e94` shape).
  - Flip W19 plan tracker `[FOLLOWUP harness-verification-debug-events]`
    to `closed at <SHA>`.
- Commit cadence (W11-W18 paterni):
  - **Primary**: `feat(W19-X): close onDebug* marker pipeline + planner
    routing + reactivation race (Bug A + B + C)`. Bundle the source
    changes + ratchet bump + fixture regen + test assertion update.
  - **Self-stamp followup**: `docs(W19-X-followup): self-stamp W19-X live
    smoke recorded — confirmation_source=harness_nonce now stamps`.

**If acceptance check 1 FAILS** (still no stamped onDebug):

- First, read the `ExTrace Harness.log` files and check the
  `activate_enter` diagnostic for the reactivation activations.
- If `has_secret: false, poll_attempts: 30, read_error: "ENOENT"`:
  polling exhausted — there is a reactivation path completely separate
  from `reload_window()`. Hunt for it. Candidates:
  - `code --install-extension` triggers an automatic reload that bypasses
    `reload_window()`. Check `executor/flows/playwright/install_extension.py`
    (if exists) or wherever the install-then-reload sequence lives.
  - The lifecycle harness `reload=True` path may do its own CDP reload
    without calling `_rewrite_harness_secret`.
- If `has_secret: true` on some but not all → check which attempts those
  correspond to; could be that the polling fixed the race but the marker
  pipeline (Bug B) still misses some channel log paths.
- If markers reach the parser but verifier rejects (look at
  `_verify_harness_marker_signature` debug output): HMAC contract drift.
  Don't touch `security.py` / `handshake.py` / `markers.js` HMAC code —
  that path is W13-1 frozen.

**If acceptance check 1 PASSES but check 2 FAILS** (stamped but
failure_reason_code still set): the consumer wire at
[executor/flows/playwright/health/reconciliation.py:85-94](../../executor/flows/playwright/health/reconciliation.py)
isn't suppressing as designed. Re-read the Half B implementation and check
that the W19-X live attempt actually has `confirmation_source ==
"harness_nonce"` in `_mark_unverified_harness_attempt`'s view (could be
that the per-attempt loop runs Half A *after* the unverified mark, putting
the order wrong).

---

## Source-of-truth file locations (don't re-derive)

- **W19-4 Half A producer stamp**: [executor/flows/playwright/health/reconciliation.py:347-348](../../executor/flows/playwright/health/reconciliation.py)
- **W19-4 Half B consumer guard**: [executor/flows/playwright/health/reconciliation.py:85-94](../../executor/flows/playwright/health/reconciliation.py)
- **W19-4 tests**: [tests/executor/test_playwright_health_reconciliation.py:813-1090](../../tests/executor/test_playwright_health_reconciliation.py)
  (15 test items: 7 functions + 8 parametrize cases)
- **W19-4 helpers (W13-1 reused)**: same file, lines 345-363 (`_w13_1_sign`,
  `_w13_1_canonical_payload`)
- **HMAC verifier (do not touch)**: [executor/flows/playwright/health/security.py:88-125](../../executor/flows/playwright/health/security.py)
- **Per-attempt harness completion check (do not touch)**: [executor/flows/playwright/health/handshake.py:59-104](../../executor/flows/playwright/health/handshake.py)
- **Run-level reason emit (don't touch yet — W19-X delivery makes this
  correctly gated by Half B upstream)**: [executor/flows/playwright/health/summary.py:327-332](../../executor/flows/playwright/health/summary.py)
- **JS-side onDebug branch (already covers all 5 variants)**: [executor/flows/harness_extension/stimulus_dispatch.js:115](../../executor/flows/harness_extension/stimulus_dispatch.js)
- **OFFICIAL_EVENT_REGISTRY onDebug variants**: [packages/analysis_planner/event_scenario_index.py:69-114](../../packages/analysis_planner/event_scenario_index.py)
- **W13-1 secret distribution (the design Bug C ran into)**: [executor/container/launch_vscode.sh:32-67](../../executor/container/launch_vscode.sh)
- **CDP reload entry point**: [executor/flows/playwright/reload_vscode.py:57-91](../../executor/flows/playwright/reload_vscode.py)
- **Channel log parser glob (Bug B layer c)**: [executor/flows/playwright/monitor/sources.py:177-235](../../executor/flows/playwright/monitor/sources.py)
- **Active tracker**: [documents/active-work/W19-live-run-root-cause.md](W19-live-run-root-cause.md)
- **Multi-iter roadmap**: [documents/active-work/W18-W22-roadmap.md](W18-W22-roadmap.md)
- **W19 plan source**: `documents/REFACTOR_OPTIMIZATION.md` §17
- **Stable ID registry**: `documents/POST_POC_BACKLOG.md` W19 Pull-Forward
  Acceptance Bar

---

## Synthetic test bar (W19-X expected at primary commit)

| Lane | Before W19-X | After W19-X (expected) | Δ |
|---|---|---|---|
| `tests/architecture/` | 202 | 202 | 0 — ratchet bump from 6→7 stays inside the gate (the gate is exact match; bumping baseline + adding the file to the map keeps the assertion green) |
| `make test-security` | 220 | 220 | 0 — no HMAC verifier or security module change |
| Full suite (`.venv/bin/pytest -q`) | 1949 (W19-4 baseline) | 1949 or 1950 | 0 or +1 — depends on whether you add a `test_on_debug_routes_via_harness_command` test or rely on the existing planner fixture round-trip + the assertion update in `test_triggers.py:66` |
| Skip count | 9 | 9 | 0 |

**No new test files necessary.** The W19-X-2 planner change is covered by
the fixture round-trip pin in `tests/platform/contracts/test_analysis_fixture_baselines.py`
(which the fixture regen brings into line) + the assertion update in
`test_triggers.py:66`. The W19-X-1 marker pipeline change is harder to
unit-test (it's a VS Code OutputChannel side-effect chain); the live smoke
gate is the acceptance bar.

**Optional**: a synthetic test that drives `consumeHarnessNonceSecret`
with a delayed-write scenario, asserting `poll_attempts > 1, has_secret:
true`. This would require a Node-side test harness; if the project doesn't
have one, skip and rely on the live smoke.

---

## Commit messages (drafted)

**Primary** (when live verification passes):

```text
feat(W19-X): close onDebug* harness marker pipeline + planner routing + reactivation race

Three independent bug classes surfaced by W19-4 live verification on
ms-python.python (Codex 2026-05-25). All three are pre-existing and were
masked by the W19-3 schema-only landing. W19-4's producer + consumer wire
in reconciliation.py at 347-348 + 85-94 (landed at 7d44b0e) had no live
signal to consume until these closed.

W19-X-1 — marker pipeline log destination (layers a + b + c):
- markers.js: setHarnessChannel + _emitMarkerLine route emitters through
  the OutputChannel instead of console.log (which launch_vscode.sh
  discards via </dev/null >/dev/null 2>&1).
- extension.js: register the dedicated "ExTrace Harness" channel name as
  HARNESS_OUTPUT_CHANNEL_NAME; OutputChannel hook skips this name so the
  marker channel is not wrapped by the target-extension appendLine
  listener.
- monitor/sources.py: read_extension_host_output globs
  output_logging_*/*ExTrace Harness.log files in addition to exthost.log.

W19-X-1 — HMAC secret reactivation race (two layers):
- launch_vscode.sh: --secret-only mode writes both secret paths and
  exits without launching VS Code.
- reload_vscode.py: _rewrite_harness_secret() runs the --secret-only
  before reload_workbench_window() so the reactivating Extension Host
  finds a fresh secret on disk.
- extension.js: consumeHarnessNonceSecret polls (30 × 100 ms) for the
  secret file as defense-in-depth against any reactivation path the
  orchestration doesn't gate (e.g. install_extension's internal reload).

W19-X-2 — planner onDebug executor_action routing:
- attempts.py: _resolve_executor_action onDebug family now returns
  "harness:run_current_stimulus" (was "extra:debug_lifecycle"). The
  legacy direct-action branch never invoked runCurrentStimulus, so no
  signed completion marker was ever emitted. W19-4 Half A producer wire
  depends on _attempt_has_harness_completion_trace returning True, which
  requires the harness command to fire.

Ratchet: tests/architecture/test_bare_binary_pragma_ratchet.py baseline
6 → 7 + reload_vscode.py: 1 added to expected distribution map. The new
pragma covers the bash subprocess invocation; migration to an absolute
path is W19-X-followup territory.

Test bar at primary landing:
- tests/architecture/: 202 passed (unchanged, ratchet stays green via
  baseline + map bump in same commit).
- make test-security: 220 passed (HMAC verifier untouched).
- full suite: <COUNT> passed, 9 skipped, <DESELECTED> deselected.

Live smoke evidence:
- output/activation_report_ms-python.python-<SHA>.json
- jq count of onDebug* attempts with confirmation_source==harness_nonce:
  <N>
- jq count with failure_reason_code != harness_verification_unconfirmed:
  <N>
- activate_enter diagnostic poll_attempts distribution:
  <list per reactivation>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**Self-stamp followup**: `docs(W19-X-followup): self-stamp W19-X live smoke
recorded — onDebug* confirmation_source=harness_nonce stamps on live runs`
plus the 8-doc canonical preamble refresh.

---

## Risk register (next session should be aware of)

| Risk | Why it matters | Mitigation |
|---|---|---|
| **Defensive polling alone isn't enough** (2 of 3 reactivations still ENOENT after 30 polls) | Means there's an Extension Host activation path neither `start.sh` nor `reload_window()._rewrite_harness_secret` gates | Hunt for the third reactivation source — most likely `code --install-extension`'s internal reload — and gate it the same way. Or migrate to "don't unlink the secret" + rely on container restart for temporal isolation. Don't paper over with longer polling. |
| **Pre-reload rewrite race** (rewrite happens, but reactivate fires *before* rewrite finishes) | Can mask test results; the secret is on disk but a stale unlink wins | The `--secret-only` mode does `rm -f` + atomic write + `chmod 0400`. The `subprocess.run` in `reload_vscode.py` is synchronous (`check=False, timeout=5`) and runs *before* `reload_workbench_window`. Order is correct; just verify it under load via the diagnostic. |
| **Marker channel log file naming drift** | If VS Code changes the per-channel log file name format, `monitor/sources.py:198` glob breaks silently | The glob is `**/output_logging_*/*ExTrace Harness.log`. If a future VS Code version changes this, the parser will return no markers and the verifier will see unsigned. Pin a sentinel test: smoke that finds at least one harness channel log file after a baseline activate. |
| **W19-X-2 fixture regen drift** | The trigger payload JSON is regenerated; if planner has any non-determinism it'll churn this fixture on every replay | The fixture regen was deterministic in the prior session. Round-trip pin in `tests/platform/contracts/test_analysis_fixture_baselines.py` catches any future drift. |
| **Architecture concern (out of W19-X scope)** | W13-1 design didn't account for VS Code's normal reload cycle. The "secret is temporal on disk" guarantee only holds for the initial boot, not for reload reactivations. | Open a W20 (or W19-followup) item to either (a) migrate to a non-file secret distribution (env var read at activate, never written to disk) or (b) keep the file at 0400 + accept that target processes running same-UID could read it, with the threat model documented. This is a real but accepted gap for now. |

---

## Commands the next session will need

```bash
# View the current diff over W19-4 primary:
git diff 7d44b0e -- executor/ packages/ tests/

# Run the synthetic tests that should pass on the working tree:
.venv/bin/pytest tests/architecture/test_bare_binary_pragma_ratchet.py -v
.venv/bin/pytest tests/workflows/marketplace/test_triggers.py::TestSelectScenarios::test_on_debug_selects_debug_session -v
.venv/bin/pytest tests/executor/test_playwright_health_reconciliation.py -v  # W19-4 tests at 813-1090

# Full bar:
.venv/bin/pytest tests/architecture/ -q
make test-security
.venv/bin/pytest -q

# Container rebuild + live analyze (the actual verification):
docker compose up -d --build api executor
# Then UI-driven analyze on ms-python.python.

# Inspect resulting activation report (REPORT path from `ls -lat output/`):
jq '.event_attempts[] | select(.event_family | startswith("onDebug")) | {family: .event_family, source: .confirmation_source, code: .failure_reason_code}' "$REPORT"

# Read the harness channel diagnostics:
docker compose exec executor bash -c 'find /home/executor/.vscode/logs -name "*ExTrace Harness*.log" -printf "%T@ %p\n" | sort -n | tail -10 | cut -d" " -f2- | while read f; do echo "=== $f ==="; cat "$f"; done'
```

---

## Memory-style notes (project facts the next session may not derive)

- **The bind mount that lets the host read live activation JSON**: docker
  compose mounts `./output → /results` (executor) and `./output → /app/output`
  (api). The api writes `activation_report_*.json` into `/app/output`,
  which appears on the host at `./output/`.
- **Why `sim-target` doesn't reproduce this**: per W19-0 baseline, the
  sim-target fixture doesn't drive the full Extension Host reload cycle,
  so the reactivation race never fires there. Live UI analyze on a real
  marketplace `.vsix` (here `ms-python.python @ 992ad028f3df`) is required.
- **W11-W18 paterni for sub-iter commit cadence**: primary commit lands the
  source surface + new tests; self-stamp follow-up commit lands the
  evidence + doc preamble refresh + tracker state flip. Both go on the
  same branch (`week19`), no new branch.
- **The `main` directory at repo root is pre-existing**, not introduced by
  this work; leave alone.
- **The HMAC secret has two paths because of UID isolation**:
  `/run/extrace/harness-secret` is consumed by the harness extension
  (Extension Host, same UID); `/results/_extrace_harness_python_secret`
  is read from the host by the Python orchestration for HMAC verification.
  The temporal protection is "delete the executor-side file as soon as
  consumed so the target extension (also same UID) can't read it." The
  Python-side file lives the whole run since the analyzer container
  controls who reads `/results`.

---

## Open questions the next session should not need to answer

These were settled in the prior session; do not re-litigate:

1. **Should W19-X be one commit or three?** One, per W11-W18 paterni —
   ships as a bug-class follow-up (primary + self-stamp). The three bug
   classes are causally chained (A unblocks B, B unblocks C), so a
   bisect-friendly split would not actually help.
2. **Is there an ADR needed?** No. Emit-site stamping + bug-class fix is
   below the ADR threshold (W16-1, W19-2 paterni). The reactivation race
   migration question (memo above) might be ADR-worthy, but defer to W20.
3. **Should we add a Node-side test for `consumeHarnessNonceSecret`'s
   polling?** Optional. Live smoke is the acceptance bar. If the project
   gets a JS test harness later, add then.
4. **Why not just keep the secret file (don't unlink)?** That'd weaken
   W13-1's temporal protection vs same-UID target extensions. Open W20
   item for proper redesign; don't fix in W19-X.
