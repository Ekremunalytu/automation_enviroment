# VS Code API Coverage Audit

`Last Updated: 2026-04-15`

This document summarizes how ExTrace currently maps VS Code extension behavior
into trigger planning and verification.

Open this only when changing trigger selection, capability support, coverage
matrix logic, or related report semantics.

The important distinction in the current implementation is:

- global/scenario support
  - what the trigger system knows how to stimulate at all
- official activation-track verification
  - what the coverage matrix can verify directly from declared activation
    metadata

These are not the same thing.

## Capability Status

### Covered End-to-End

The trigger system and coverage model both treat these capabilities as covered:

- `commands`
- `window_ui`
- `workspace_fs`
- `languages_editor`
- `debug`
- `terminal_tasks`
- `search_views`
- `notebooks`
- `custom_editors`
- `uri_walkthrough`
- `authentication`
- `webview`

### Supported, But With Verification Gaps

These capabilities have scenario-level or heuristic support, but the official
coverage track still marks them incomplete:

- `scm`
  - `git_workflow` exists, but official capability support is still marked
    missing in `workflows/marketplace/triggers.py`.
- `settings`
  - `settings_modification` exists, but the official track still treats this as
    missing for coverage accounting.

### Still Marked Missing In The Support Matrix

These capabilities are still marked `missing` in the current support matrix,
even though some of them now have partial scaffolding elsewhere in the repo:

- `chat`
  - trigger event strategies exist for `onChatParticipant` and
    `onLanguageModelTool`, and monitor-side verification can recognize chat
    activations, but the support matrix still marks chat as missing.
- `comments`
  - the harness extension exposes a local comment-controller surface, but
    trigger planning and coverage accounting do not yet treat comments as
    covered.
- `testing`
  - the harness extension exposes a local test controller, but trigger planning
    and coverage accounting do not yet treat testing as covered.
- `workspace_trust`
  - capability metadata is ingested from manifests and can influence attempted
    capability selection, but the support matrix still marks workspace trust as
    missing.

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
- Current note: scenario exists, but official-track verification is still
  incomplete

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
- Current note: scenario exists, but official-track verification is still
  incomplete

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

## Current Gaps

- Official activation coverage and heuristic workflow coverage are both present,
  but they can still drift if they are summarized as one flat capability list.
- `chat`, `comments`, `testing`, and `workspace_trust` remain missing in the
  support matrix even though the repo now contains partial scaffolding for some
  of them.
- Command and UI launch coverage is stronger than result verification; some
  flows still prove stimulation better than they prove extension-specific
  follow-through.

## Next Candidate Expansions

- `chat`
  - close the gap between existing chat event scaffolding and support-matrix
    coverage
- `comments`
  - promote harness comment-thread support into trigger planning and report
    accounting
- `testing`
  - promote harness test-controller support into trigger planning and report
    accounting
- `workspace_trust`
  - promote manifest capability metadata into a real trust-state execution and
    verification path
- official-track closure for `scm` and `settings`
