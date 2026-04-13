# VS Code API Coverage Audit

`Last Updated: 2026-04-13`

This document summarizes how ExTrace automation currently maps to the VS Code
extension surface. The executor still selects scenarios from activation events
and `contributes` metadata, but the coverage view below translates that
behavior into a stable capability matrix.

## Capability Status

### Covered

- `commands`
- `window_ui`
- `workspace_fs`
- `languages_editor`
- `debug`
- `terminal_tasks`
- `scm`
- `search_views`
- `settings`
- `notebooks`

### Partial

- `custom_editors`
  - Covered through bait-file opening only.
  - Does not validate target-specific editor semantics deeply.
- `uri_walkthrough`
  - Covered through generic URI and walkthrough launch flows.
  - Does not validate follow-up UI state beyond launch success.

### Missing

- `authentication`
- `chat`
- `comments`
- `testing`
- `webview`
- `workspace_trust`

## Scenario Registry

### `coding_session`

- Intent: exercise editor commands, formatting, suggest, definition, and save.
- Activation focus: `onLanguage`, `onCommand`
- Capability coverage: `commands`, `window_ui`, `workspace_fs`, `languages_editor`

### `debug_session`

- Intent: drive debug sidebar, breakpoints, debug console, and stop/start flow.
- Activation focus: `onDebug`, `onDebugResolve`, `onDebugAdapterProtocolTracker`
- Capability coverage: `commands`, `window_ui`, `debug`, `workspace_fs`

### `terminal_usage`

- Intent: open integrated terminals and run task-adjacent shell commands.
- Activation focus: `onTaskType`, `onTerminalProfile`
- Capability coverage: `commands`, `terminal_tasks`, `workspace_fs`

### `git_workflow`

- Intent: drive Source Control view and git-oriented workspace activity.
- Activation focus: `onView:scm`
- Capability coverage: `commands`, `window_ui`, `scm`, `workspace_fs`

### `extension_browsing`

- Intent: browse the Extensions view and marketplace search.
- Activation focus: `onView:extensions`
- Capability coverage: `window_ui`

### `settings_modification`

- Intent: modify settings and browse configuration UI.
- Activation focus: `onConfiguration`
- Capability coverage: `commands`, `window_ui`, `settings`, `workspace_fs`

### `project_exploration`

- Intent: open multiple file types and explorer surfaces.
- Activation focus: `workspaceContains`, `onView:explorer`, `onLanguage`
- Capability coverage: `window_ui`, `workspace_fs`, `languages_editor`

### `search_workflow`

- Intent: drive the search sidebar with workspace queries.
- Activation focus: `onView:search`
- Capability coverage: `window_ui`, `search_views`

### `diagnostics_check`

- Intent: inspect Problems and Output surfaces.
- Activation focus: `onView:output`
- Capability coverage: `window_ui`, `workspace_fs`

### `refactor_workflow`

- Intent: trigger rename/refactor actions in the editor.
- Activation focus: `onCommand`, `onLanguage`
- Capability coverage: `commands`, `languages_editor`, `workspace_fs`

### `notebook_session`

- Intent: open notebook content and interact with notebook UI.
- Activation focus: `onNotebook`
- Capability coverage: `window_ui`, `notebooks`, `workspace_fs`

## Current Gaps

- Extension-host logs previously mixed target extension activations with
  automation noise; this now has a split-stream model in report payloads and UI.
- Coverage is still activation-event driven; unsupported capabilities remain
  explicitly marked missing instead of being inferred.
- `contributes.commands` and extra triggers are now logged structurally, but
  command result validation is still shallow and best-effort.

## Next Candidate Expansions

- `webview`: target-specific webview open/load/assertion flows
- `testing`: test explorer and run/debug test commands
- `comments`: comment controller and thread interactions
- `authentication`: provider session prompts and consent flows
- `workspace_trust`: trust prompt detection and trust-state transition handling
