# VS Code API Coverage Audit

`Last Updated: 2026-05-28 — W22 closed synthetically on week22 and merged to main via PR #31 week22 -> main 1399f82; W21 closed and merged via PR #30 5dc18aa.`

This document summarizes how ExTrace currently maps VS Code extension behavior
into trigger planning and verification.

Open this only when changing trigger selection, capability support, coverage
matrix logic, or related report semantics.

> **Authoritative source:** `_GLOBAL_CAPABILITY_SUPPORT`,
> `_OFFICIAL_CAPABILITY_SUPPORT`, and `_HEURISTIC_CAPABILITY_SUPPORT` maps in
> `packages/analysis_planner/capabilities.py`. The scenario registry in
> `packages/analysis_planner/scenarios.py` is the canonical scenario list.
> If this doc disagrees with either module, trust the module and update the
> doc. Last full spot-verification: W22-2 close (2026-05-28); the
> hard-tier `chat` promotion landed at `ffbb743`.

The important distinction in the current implementation is:

- global/scenario support
  - what the trigger system knows how to stimulate at all
  - source: `_GLOBAL_CAPABILITY_SUPPORT` in
    `packages/analysis_planner/registry.py`
- official activation-track verification
  - what the coverage matrix can verify directly from declared activation
    metadata
  - source: `_OFFICIAL_CAPABILITY_SUPPORT` in the same module

These are not the same thing.

## Baseline Benign Fixtures

The current benign reference corpus used by docs and tests is:

- `ms-python.python`
  - broad layered-pass reference fixture
- `extrace.fixture-chat`
  - isolated `onChatParticipant` benign fixture
- `extrace.fixture-theme`
  - scenario-zero benign fixture used to validate non-executable semantics

## Capability Status

`CAPABILITY_TAXONOMY` declares **18 capabilities total** in
`packages/analysis_planner/capabilities.py`. Both
`_OFFICIAL_CAPABILITY_SUPPORT` and `_GLOBAL_CAPABILITY_SUPPORT` mark all 18
`"covered"` as of W22-2 close (2026-05-28).

### Covered End-to-End (all 18)

- `commands`
- `window_ui`
- `workspace_fs`
- `languages_editor`
- `debug`
- `terminal_tasks`
- `scm` (W20-1, `82276cb`)
- `search_views`
- `settings` (W20-2, `a4343d2`)
- `notebooks`
- `custom_editors`
- `uri_walkthrough`
- `authentication`
- `chat` (W22-2, `ffbb743` — per ADR 0014 Option C; static cut, runtime
  live-run anchor deferred to user on Linux)
- `comments` (W21-2, `8948ea6`)
- `testing` (W21-1, `7e87030`)
- `webview`
- `workspace_trust` (W21-3, `c744c15`)

Per-capability `_GLOBAL_CAPABILITY_NOTES` entries in `capabilities.py`
qualify the local-only / harness-assisted policies for `chat`, `comments`,
`testing`, `workspace_trust`, `authentication`, `custom_editors`, and
`uri_walkthrough`.

## Scenario Registry

### `coding_session`

- Intent: exercise editor commands, formatting, suggest, definition, and save.
- Activation focus: `onLanguage`, `onCommand`
- Capability coverage: `commands`, `window_ui`, `workspace_fs`,
  `languages_editor`

### `project_exploration`

- Intent: open multiple files and explorer surfaces to trigger broad language
  activation.
- Activation focus: `workspaceContains`, `onView:explorer`, `onLanguage`
- Capability coverage: `window_ui`, `workspace_fs`, `languages_editor`

### `diagnostics_check`

- Intent: inspect Problems and Output surfaces.
- Activation focus: `onView:output`
- Capability coverage: `window_ui`, `workspace_fs`

### `search_workflow`

- Intent: drive the search sidebar with workspace queries.
- Activation focus: `onView:search`, `onSearch`
- Capability coverage: `window_ui`, `search_views`

### `settings_modification`

- Intent: modify settings and browse configuration UI.
- Activation focus: `onConfiguration`
- Capability coverage: `commands`, `window_ui`, `settings`, `workspace_fs`

### `debug_session`

- Intent: drive debug tooling, breakpoints, and start/stop flows.
- Activation focus: `onDebug`, `onDebugResolve`,
  `onDebugAdapterProtocolTracker`, `onDebugDynamicConfigurations`,
  `onDebugInitialConfigurations`
- Capability coverage: `commands`, `window_ui`, `debug`, `workspace_fs`

### `terminal_usage`

- Intent: open terminals and task-adjacent shell commands.
- Activation focus: `onTaskType`, `onTerminal`, `onTerminalProfile`,
  `onTerminalShellIntegration`
- Capability coverage: `commands`, `terminal_tasks`, `workspace_fs`

### `git_workflow`

- Intent: drive Source Control view and git-oriented workspace activity.
- Activation focus: `onView:scm`
- Capability coverage: `commands`, `window_ui`, `scm`, `workspace_fs`

### `extension_browsing`

- Intent: browse the Extensions view and marketplace search.
- Activation focus: `onView:extensions`
- Capability coverage: `window_ui`

### `refactor_workflow`

- Intent: trigger rename and refactor actions in the editor.
- Activation focus: `onCommand`, `onLanguage`
- Capability coverage: `commands`, `languages_editor`, `workspace_fs`

### `notebook_session`

- Intent: open notebook content and interact with notebook UI.
- Activation focus: `onNotebook`, `onRenderer`
- Capability coverage: `window_ui`, `notebooks`, `workspace_fs`

### `authentication_probe`

- Intent: open account and sign-in surfaces to trigger authentication flows.
- Activation focus: `onAuthenticationRequest`
- Capability coverage: `commands`, `window_ui`, `authentication`

### `webview_probe`

- Intent: open preview and panel flows backed by a VS Code webview.
- Activation focus: `onWebviewPanel`, `onView`
- Capability coverage: `commands`, `window_ui`, `webview`

### W21-W22 Scenario Additions (local-only / harness-assisted)

These scenarios land per ADR 0014 (chat policy) + the W21 mid-tier
promotions. They are local-only — no external services, no proposed APIs.
See `packages/analysis_planner/scenarios.py` for full definitions.

- `local_test_controller` (W21-1, advertises `testing`).
- `local_comments_controller` (W21-2, advertises `comments`).
- `workspace_trust_transition` (W21-3, advertises `workspace_trust`).
- `local_chat_participant_controller` (W22-2, advertises `chat` via
  `vscode.chat.createChatParticipant`).
- `local_language_model_tool_controller` (W22-2, advertises `chat` via
  `vscode.lm.registerTool` + `vscode.lm.invokeTool`).

## Current Gaps

- Coverage promotion is complete in the support matrix (all 18 covered);
  remaining drift risk is **declared ≠ verified** at runtime. Chat coverage
  in particular is static-only on the current Mac development machine; the
  runtime live-run anchor (`make sim-target TARGET=ms-python.python` →
  `coverage_summary.missing_capabilities == []`) is deferred to user on
  Linux per W22-N close-out (memory `feedback_pr_push_approval`).
- Command and UI launch coverage is stronger than result verification; some
  flows still prove stimulation better than they prove extension-specific
  follow-through. Per-capability detection-surface depth (e.g., chat-side
  defense-in-depth via ADR 0015 sandbox-evasion policy) is V2 scope.
- **Activation-event sourcing gap (W23 candidate).** The trigger parser reads
  only the declared `activationEvents` array, so VS Code 1.74+
  auto-generated events (from `contributes.commands` / `languages` / `views`
  / `customEditors` / `authentication` / `taskDefinitions`) are not
  synthesized — a minimal-`activationEvents` extension under-represents its
  real activation surface. **Partially closed on branch
  `extension-trigger-matrix`:** the `onCommand` family is now synthesized at the
  **planner** layer (`_apply_contributes_metadata` in
  `packages/analysis_planner/selection.py`), live-validated on
  `ms-python.python` (24/24 contributed commands `verified`); the other 5
  auto-generated families remain. The recognition taxonomy itself is complete (all
  29 documented kinds in `OFFICIAL_EVENT_REGISTRY`); the gap is sourcing, not
  the kind set. Tracked as
  `[FOLLOWUP activation-event-contributes-implicit-synthesis]` (sourcing) and
  `[FOLLOWUP activation-event-stimulus-fidelity-target-specific]` (generic
  proxy vs. target-specific contribution) in `POST_POC_BACKLOG.md` →
  "W23 Candidate Captures (audit 2026-06-01)".

## Post-PoC Follow-On Candidates

Coverage promotion (`scm` + `settings` + `testing` + `comments` +
`workspace_trust` + `chat`) closed across W20-W22. Remaining follow-on
candidates are detection-surface deepening, not capability matrix fills:

- **Sandbox-evasion defense implementation** (ADR 0015 Draft Policy + W22-5
  observer-side canary). 5-family taxonomy (`webdriver_presence`,
  `cdp_fingerprint`, `timing_probe`, `platform_identity`,
  `process_introspection`); V2 implementation roadmap — W23+ scope per
  ADR 0015 §Implementation Roadmap.
- **Static-analysis pre-check stream** (deferred; design intent in
  `documents/active-work/extrace-static-stream-handoff.md`). Pre-execution
  signal layer (manifest red flags, typosquats, embedded binaries, JS
  literal `eval` / `Function` / `child_process`) with block-and-warn
  semantics, separate `automation_static_analyzer` Docker service,
  schema-first contract landing, in-house Python rules + Semgrep MVP.
- **Container-hardening ratchet-down** (W21-4 ADR 0013 §Deferred → W22-6).
  `read_only` + tmpfs + custom seccomp profile; deferred to user (Linux
  required for live-smoke).
