# Comments + Testing Capability Readiness (W21 Plumbing Şablonu)

`Authored: 2026-05-26 by W20-4 sub-iter (`[DESIGN taxonomy-comments-testing-readiness]`).`
`Status: DESIGN (doc-only). No code lands here; this is the unblocker template for W21-1 (`testing`) + W21-2 (`comments`).`
`Owner: W21 pull.`

> **Purpose**. After W20-1 + W20-2 closed the `scm` + `settings`
> easy-wins tier, `comments` and `testing` remain `missing` in both
> tracks (and `workspace_trust` does too — but that lands at W21-3).
> This doc surveys the existing harness plumbing, identifies what's
> stubbed vs missing, and proposes a surface layout for the W21
> implementation. **W21-0 doc-reconcile should pin a stable ID per
> capability and lift the plumbing items into a sub-iter slate**.

## Context

`_GLOBAL_CAPABILITY_SUPPORT` at
[`packages/analysis_planner/capabilities.py:29`](../../packages/analysis_planner/capabilities.py)
lists both capabilities as `missing` (heuristic track) and they're
mirrored at `_OFFICIAL_CAPABILITY_SUPPORT` lines 95–97 as `missing`
too. Policy text at `_GLOBAL_CAPABILITY_NOTES`
([`capabilities.py:66-74`](../../packages/analysis_planner/capabilities.py))
already establishes the constraint shape:

- **`comments`**: "Comment thread coverage is provided through local
  harness surfaces so discussion flows stay inside the sandbox."
- **`testing`**: "Testing coverage uses local controllers and
  run/debug flows without calling external test services."

The notes block is the W22-end policy north star — any W21
implementation must respect them.

## Surface Survey

### Comments — VS Code API

Public API entry: `vscode.comments.createCommentController(id, label)`
returning a `CommentController` with:

- `commentingRangeProvider`: line-range hook the editor calls to ask
  "where can the user comment?"
- `inputBox`: text input for active comment threads.
- `createCommentThread(uri, range, comments)`: programmatic thread
  creation.
- `options`: control comment thread visibility (collapsible /
  reaction support).

### Comments — Current Codebase State

- **Stub present**: [`executor/flows/harness_extension/extension.js`](../../executor/flows/harness_extension/extension.js)
  registers `extrace.harness.comments` controller (search for
  `vscode.comments.createCommentController`). This is a **bare
  stub** — it exists for activation purposes but does not drive a
  comment scenario nor verify thread creation.
- **Missing**: a planner-side scenario whose `api_capabilities`
  includes `comments`. The closest match would be a new
  `discussion_thread` or `comment_review` scenario in
  `packages/analysis_planner/scenarios.py`.
- **Missing**: a Playwright stimulus pass that exercises the
  comment thread UI flow (open comment widget → submit → assert
  visible thread).
- **Missing**: a harness completion marker emission for the
  comment-thread interaction.

### Testing — VS Code API

Public API entry: `vscode.tests.createTestController(id, label)`
returning a `TestController` with:

- `items: TestItemCollection`: tree of test items (programmatic add).
- `createTestItem(id, label, uri?)`: factory for individual items.
- `createRunProfile(label, kind, runHandler, isDefault?)`: bind a
  run/debug handler.
- `resolveHandler`: lazy expansion hook for test discovery.
- `refreshHandler`: pull-to-refresh hook.

### Testing — Current Codebase State

- **Stub present**: [`executor/flows/harness_extension/constants.js`](../../executor/flows/harness_extension/constants.js)
  has `test: ["workbench.view.testing"]` in the view-id map. This
  gives the Playwright driver a way to *open* the Test Explorer
  view, but no test items or run handlers exist behind it.
- **Missing**: a planner-side scenario whose `api_capabilities`
  includes `testing`. Candidates: `unit_test_run`,
  `test_discovery`, or a more generic `local_test_controller`.
- **Missing**: a harness test controller registration alongside the
  comment controller (`createTestController` + at least one
  `createTestItem` + a `createRunProfile`).
- **Missing**: a Playwright stimulus pass exercising the test
  controller flow (run → assert outcome via the
  `vscode.tests.runTest()` proxy or the Test Explorer view state).

## Proposed W21 Plumbing Layout

> The W21 sub-iter slate at
> [`active-work/W18-W22-roadmap.md`](../active-work/W18-W22-roadmap.md)
> earmarks W21-1 (`testing`) and W21-2 (`comments`) as the
> implementation iters. The proposed surface below is **suggestion
> shape** — W21-0 doc-reconcile finalizes.

### W21-1 — `testing` Coverage Path

1. **Harness side** ([`executor/flows/harness_extension/extension.js`](../../executor/flows/harness_extension/extension.js)):
   - Register a `vscode.tests.createTestController("extrace.harness.testing", "ExTrace Harness Tests")`.
   - Add ≥1 `TestItem` via `controller.items.add(...)` so the Test
     Explorer view shows non-empty content.
   - Add a `createRunProfile("Run", TestRunProfileKind.Run, runHandler, true)`
     whose `runHandler` calls `controller.createTestRun(request)`,
     immediately marks the items `passed`/`failed`, and ends the run.
   - Emit a harness completion marker through the existing
     `markers.js` channel so the Python side detects the run
     completion (W19-X paterni: route through OutputChannel, not
     `console.log`).
2. **Planner side** ([`packages/analysis_planner/scenarios.py`](../../packages/analysis_planner/scenarios.py)):
   - Add a `local_test_controller` scenario (or
     `unit_test_run`) with `api_capabilities=("testing", "commands",
     "window_ui")`, `activation_events=("onView:workbench.view.testing",)`.
   - Wire it into `SCENARIO_REGISTRY` and verify the planner
     selects it for an extension that contributes Test Explorer
     views.
3. **Stimulus pass** ([`executor/flows/playwright/stimulus/`](../../executor/flows/playwright/stimulus/)):
   - New pass: open Test Explorer → click "Run all" → wait for run
     completion marker.
4. **Capability flip**:
   - `_OFFICIAL_CAPABILITY_SUPPORT["testing"]: "missing" → "covered"`
   - `_HEURISTIC_CAPABILITY_SUPPORT["testing"]: "missing" → "covered"`
   - Fixture regen for any frozen trigger payloads.

### W21-2 — `comments` Coverage Path

Mirrors W21-1 paterni:

1. **Harness side**: extend the existing `extrace.harness.comments`
   stub. Add a `commentingRangeProvider` returning a fixed range
   for the harness fixture file. Add a `createCommentThread()` call
   on activation to populate a thread.
2. **Planner side**: add `discussion_thread` scenario with
   `api_capabilities=("comments", "window_ui", "languages_editor")`,
   `activation_events=("onLanguage:plaintext",)` or similar.
3. **Stimulus pass**: open the harness file → trigger the comment
   widget → submit a reply → wait for harness completion marker
   emitting the thread state.
4. **Capability flip** for both tracks; fixture regen.

## Policy Constraints (Inherited From `_GLOBAL_CAPABILITY_NOTES`)

The W21 implementation **must not**:

- Call any external service for testing (no test discovery via
  cloud APIs, no remote test runners).
- Surface comment thread content outside the sandbox (no external
  webhook posts, no telemetry of thread state).
- Add network-bound dependencies (the W8 hardening + W14 network
  redaction posture stays in force).

The W21 implementation **must**:

- Live inside the harness extension (`executor/flows/harness_extension/`)
  and the local planner / executor surfaces.
- Use the existing W19-X marker pipeline (OutputChannel route +
  HMAC-signed completion markers via the harness JS) so the
  reconciliation reads the events through the same parser glob.
- Respect the W17-2 lifecycle harness invariants (cancel-via-heartbeat
  must still pass after the new controllers register).

## Open Questions for W21-0

These should be pinned at W21-0 doc-reconcile before W21-1 starts:

1. **Test items: persistent vs ephemeral?** Should the harness Test
   Controller keep its `TestItem` list across `activate()` calls,
   or rebuild on each activation? The W13-1 HMAC secret reactivation
   race (W19-X Bug C) suggests ephemeral is safer — but live-run
   state needs to be visible to the Python parser regardless.
2. **Comment thread persistence?** Same question for comment
   threads — the harness fixture file path needs to be stable so
   the stimulus pass can find the widget.
3. **Stimulus pass placement.** New file under
   `stimulus/` or extend an existing pass? The W19-2 paterni for
   `passes.py` covered-only branch suggests a dedicated pass per
   capability is cleaner for accountability.
4. **Workspace trust ordering**. W21-3 (`workspace_trust`) is the
   third capability in the mid tier. Does it need to land BEFORE
   W21-1/W21-2 because the test/comments scenarios may require a
   trusted workspace? Likely yes — but a `workspace_trust` flip is
   itself non-trivial; this might force the slate order
   `W21-3 → W21-1 → W21-2`.
5. **Container hardening (W21-4) interaction**. If W21-4 stretch
   lands seccomp / cap_drop / read_only, do the new test
   controller and comment controller call any syscalls the
   hardened profile blocks? Worth a sanity check before W21-4
   pull, especially around any FS write the comment thread
   persistence (Q2 above) would require.

## References

- [`packages/analysis_planner/capabilities.py`](../../packages/analysis_planner/capabilities.py)
- [`packages/analysis_planner/scenarios.py`](../../packages/analysis_planner/scenarios.py)
- [`executor/flows/harness_extension/extension.js`](../../executor/flows/harness_extension/extension.js)
- [`executor/flows/harness_extension/constants.js`](../../executor/flows/harness_extension/constants.js)
- [`active-work/W18-W22-roadmap.md`](../active-work/W18-W22-roadmap.md) — W21 sub-iter slate
- [`active-work/W20-coverage-promotion-easy-wins.md`](../active-work/W20-coverage-promotion-easy-wins.md) — W20-4 close-out
- VS Code Comments API:
  <https://code.visualstudio.com/api/references/vscode-api#comments>
- VS Code Test API:
  <https://code.visualstudio.com/api/references/vscode-api#tests>
