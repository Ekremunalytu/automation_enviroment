# Executor: Playwright UI Automation & Honeypot Environment

`Last Updated: 2026-02-16` | `Status: Active Development`

---

## Overview

A modular system inside the executor container that controls VS Code GUI via Playwright CDP (Chrome DevTools Protocol). Each module has a single responsibility, is function-based (no classes), stateless, and composable.

Additionally, a realistic **honeypot developer environment** is automatically set up when the container starts, designed to attract malicious extensions scanning for secrets.

---

## File Structure

```
executor/
├── Dockerfile                # Ubuntu 22.04 + VS Code + monitoring tools
├── start.sh                  # Container entrypoint (Xvfb, VNC, VS Code, honeypot)
├── requirements.txt          # Python dependencies (playwright)
├── __init__.py
└── playwright/
    ├── __init__.py            # Package docstring
    ├── keyboard.py            # VS Code shortcut constants (single source of truth)
    ├── vscode.py              # CDP connection, ready wait
    ├── commands.py            # Command Palette operations
    ├── editor.py              # Editor: open/save/close/type + language server actions
    ├── sidebar.py             # Activity Bar and sidebar views
    ├── terminal.py            # Integrated terminal
    ├── panel.py               # Bottom panel: problems, output, debug console
    ├── debug.py               # Debug lifecycle (start/stop/step)          [NEW]
    ├── settings.py            # Settings & theme changes                   [NEW]
    ├── monitor.py             # Extension Host activation monitoring       [NEW]
    ├── automation.py          # User behavior simulation scenarios (10x)   [NEW]
    ├── workspace.py           # Filesystem: honeypot environment + file operations
    ├── language_samples.py    # Multi-language sample files for activation coverage
    └── entrypoint.py          # CLI with --monitor, --scenario, --list, --shuffle
```

---

## Container Startup Flow

When `start.sh` runs, the following sequence executes:

```
1. Xvfb :99 (1920x1080x24)     -> Virtual display
2. Openbox                       -> Window manager
3. x11vnc (port 5900)           -> VNC server
4. workspace.py                  -> Honeypot environment setup
5. VS Code settings.json         -> Trust/telemetry disabled
6. VS Code /workspace            -> GUI starts (CDP port 9222, --log trace)
7. noVNC (port 6080)            -> Browser access
8. Symlink latest log dir        -> /home/executor/.vscode/logs/latest
```

VS Code is now started with `--log trace` to enable verbose Extension Host logging
for activation monitoring. Log level is configurable via `EXECUTOR_VSCODE_LOG_LEVEL` env var.

### VS Code Auto-Configuration

`start.sh` writes these settings before VS Code starts:

```json
{
  "security.workspace.trust.enabled": false,
  "workbench.startupEditor": "none",
  "telemetry.telemetryLevel": "off",
  "update.mode": "none"
}
```

This ensures:
- **Workspace Trust dialog** does not appear
- **Welcome tab** does not open
- **Telemetry** is disabled
- **Auto-update** is disabled

VS Code opens `/workspace` directly — no manual selection required.

---

## Module Details

### keyboard.py — Shortcut Constants

All VS Code keyboard shortcuts are defined in one place. Other modules import these constants. If VS Code changes a shortcut, only this file needs updating.

```python
# Examples
COMMAND_PALETTE = "Control+Shift+KeyP"
QUICK_OPEN      = "Control+KeyP"
NEW_FILE        = "Control+KeyN"
SAVE_FILE       = "Control+KeyS"
TOGGLE_TERMINAL = "Control+Backquote"
FOCUS_EXPLORER  = "Control+Shift+KeyE"
```

**Full list:** Command Palette, Quick Open, Editor (new/save/close), Sidebar (explorer/search/scm/debug/extensions), Panel, Terminal, Navigation, Debug lifecycle (F5/Shift+F5/F10/F11), Settings (Ctrl+,), Language server actions (format/definition/suggest/rename), Output/Problems focus, Fullscreen toggle.

---

### vscode.py — CDP Connection

Connects to VS Code via Chrome DevTools Protocol.

| Function | Description |
|----------|-------------|
| `connect(playwright)` | Connects via CDP, returns `(browser, page)` |
| `wait_until_ready(page, timeout_ms)` | Waits until `.monaco-workbench` is visible |
| `disconnect(browser)` | Closes the CDP connection |

```python
from playwright.sync_api import sync_playwright
import vscode

with sync_playwright() as pw:
    browser, page = vscode.connect(pw)
    vscode.wait_until_ready(page)
    # ... operations ...
    vscode.disconnect(browser)
```

**CDP URL:** `http://localhost:9222` (env: `EXECUTOR_CDP_PORT`)

---

### commands.py — Command Palette

Command Palette and Quick Open operations. **Each function presses Enter and waits for the widget to close.**

| Function | Description |
|----------|-------------|
| `open_command_palette(page)` | Opens palette, waits for visibility |
| `run_command(page, command_text)` | Opens palette, types command, presses Enter, **waits for close** |
| `quick_open(page, query)` | Opens Ctrl+P, types query, presses Enter, **waits for close** |

**Important detail:** VS Code doesn't remove `.quick-input-widget` from DOM, it sets `display: none`. A custom CSS selector checks for widget closure:

```python
_QUICK_INPUT_VISIBLE = ".quick-input-widget:not([style*='display: none'])"
```

**Covers:** `onCommand:*` activation events.

---

### editor.py — Editor Operations

Opening, writing, saving, and closing files.

| Function | Description |
|----------|-------------|
| `new_untitled_file(page)` | Opens new empty tab (Ctrl+N) |
| `save_file(page)` | Saves current file (Ctrl+S) |
| `save_file_as(page, filename)` | Saves via Save-As dialog (**xdotool**) |
| `close_active_editor(page)` | Closes active tab (Ctrl+W) |
| `type_in_editor(page, text)` | Types text into editor |
| `open_file_by_name(page, filename)` | Opens file via Quick Open |
| `close_all_editors(page)` | Closes all tabs (Command Palette) |
| `format_document(page)` | Format document (Ctrl+Shift+I) — triggers formatters |
| `go_to_definition(page)` | Go to definition (F12) — triggers language servers |
| `trigger_suggest(page)` | IntelliSense suggestions (Ctrl+Space) — triggers completion |
| `rename_symbol(page, new_name)` | Rename symbol (F2) — triggers rename providers |
| `select_all(page)` | Select all text (Ctrl+A) |

**Native Dialog Issue:** The `save_file_as` function opens a GTK native file dialog via `Ctrl+Shift+S`. This dialog is outside Playwright's DOM — it's not in the Chromium web page. Therefore `xdotool` is used:

```python
subprocess.run(["xdotool", "key", "ctrl+a"], check=True)      # Select current name
subprocess.run(["xdotool", "type", "--delay", "30", filename]) # Type new name
subprocess.run(["xdotool", "key", "Return"], check=True)       # Save
```

**Covers:** `onLanguage:*`, `onCustomEditor:*` activation events.

---

### sidebar.py — Sidebar & Activity Bar

Opening/closing left sidebar views.

| Function | Description |
|----------|-------------|
| `toggle_sidebar(page)` | Show/hide sidebar (Ctrl+B) |
| `open_explorer(page)` | Explorer view (Ctrl+Shift+E) |
| `open_search(page)` | Search view (Ctrl+Shift+F) |
| `open_source_control(page)` | Source Control (Ctrl+Shift+G) |
| `open_debug(page)` | Run & Debug (Ctrl+Shift+D) |
| `open_extensions_view(page)` | Extensions (Ctrl+Shift+X) |
| `open_view_by_command(page, view_name)` | Any view via Command Palette |

**Covers:** `onView:*` activation events. `open_view_by_command` is used for custom `viewContainers`.

---

### terminal.py — Integrated Terminal

| Function | Description |
|----------|-------------|
| `toggle_terminal(page)` | Show/hide terminal panel |
| `new_terminal(page)` | Create new terminal (keyboard shortcut Ctrl+Shift+`) |
| `new_terminal_via_command(page)` | Create terminal via Command Palette (fallback) |
| `type_in_terminal(page, text, press_enter=True)` | Type in terminal, presses Enter by default |

`press_enter=True` is the default — commands are automatically executed after typing.

---

### panel.py — Bottom Panel

| Function | Description |
|----------|-------------|
| `toggle_panel(page)` | Show/hide bottom panel (Ctrl+J) |
| `focus_problems(page)` | Focus Problems tab (Ctrl+Shift+M keyboard shortcut) |
| `focus_output(page)` | Focus Output tab (Ctrl+Shift+U keyboard shortcut) |
| `open_problems(page)` | Problems tab (Command Palette) |
| `open_output(page)` | Output tab (Command Palette) |
| `open_debug_console(page)` | Debug Console tab |

---

### debug.py — Debug Lifecycle [NEW]

| Function | Description |
|----------|-------------|
| `start_debug(page)` | Start debugging (F5) |
| `stop_debug(page)` | Stop debug session (Shift+F5) |
| `step_over(page)` | Step over current line (F10) |
| `step_into(page)` | Step into function call (F11) |
| `add_breakpoint_via_command(page)` | Toggle breakpoint via Command Palette |
| `create_launch_json(page, debug_type)` | Create launch.json configuration |
| `run_debug_session(page, wait_ms)` | Full debug lifecycle: start → wait → stop |

**Covers:** `onDebug:*`, `onDebugResolve:*`, `onDebugAdapterProtocol:*`

---

### settings.py — Settings & Configuration [NEW]

| Function | Description |
|----------|-------------|
| `open_settings(page)` | Open Settings UI (Ctrl+,) |
| `open_settings_json(page)` | Open settings.json via Command Palette |
| `search_setting(page, query)` | Search in Settings UI |
| `change_theme(page, theme_name)` | Change color theme (opens picker, selects, dismisses) |
| `toggle_setting_via_json(page, key, value)` | Insert key-value into settings.json and save |
| `toggle_fullscreen(page)` | Toggle fullscreen/zen mode (F11) |

**Covers:** `onConfiguration:*`, layout change events

---

### monitor.py — Extension Host Activation Monitoring [NEW]

Three strategies to verify extension activations:

**Strategy 1: VS Code log file parsing** (most reliable)
- Finds Extension Host log files under `/home/executor/.vscode/logs/`
- Parses activation events using regex patterns compatible with multiple VS Code versions
- Extracts: extension ID, activation event, timestamp, duration

**Strategy 2: Running Extensions UI snapshot** (via Playwright)
- Opens `Developer: Show Running Extensions` command
- Scrapes the list of active extensions from DOM (`aria-label` for ID, inner text for timing)
- Returns extension ID, display name, and activation time in ms

**Strategy 3: Extension Host log file reading**
- Reads the raw Extension Host log file content
- Provides the full log for detailed post-hoc analysis

| Function / Class | Description |
|----------|-------------|
| `find_exthost_logs()` | Find Extension Host log files (newest first) |
| `parse_activations_from_log(path)` | Parse activation events from a log file |
| `parse_all_exthost_logs()` | Find and parse all log files |
| `get_running_extensions(page)` | Scrape Running Extensions UI via Playwright |
| `read_extension_host_output()` | Read Extension Host log file content |
| `watch_exthost_log(callback, timeout_s)` | Real-time log watching (inotifywait or polling) |
| `check_extension_activated(ext_id, page)` | Quick check if a specific extension is active |
| `ExtensionMonitor(page)` | Context manager: wraps scenarios with monitoring |
| `ActivationReport` | Data class with `.save(path)`, `.print_summary()` |

Usage:
```python
import monitor, automation

mon = monitor.ExtensionMonitor(page)
mon.start()
automation.run_all_scenarios(page)
report = mon.stop()
report.print_summary()
report.save("/results/activation_report.json")
```

---

### automation.py — User Behavior Simulation Scenarios [NEW]

10 scenarios that simulate realistic developer workflows to trigger extension activation events:

| Scenario | Triggers | Status |
|----------|----------|--------|
| `coding_session` | onLanguage, completionProvider, formatterProvider, definitionProvider | Tested OK |
| `debug_session` | onDebug, onDebugResolve, onDebugAdapterProtocol | Tested OK |
| `terminal_usage` | onTerminalCreate, shell integration | Tested OK |
| `git_workflow` | onView:scm, git provider | Tested OK |
| `extension_browsing` | onView:extensions | Tested OK |
| `settings_modification` | onConfiguration, layout events | **Has bugs** (see Known Bugs) |
| `project_exploration` | onLanguage (15 file types) | Tested OK (with memory fix) |
| `search_workflow` | onView:search, search providers | Tested OK (single scenario) |
| `diagnostics_check` | diagnostics, linters | Tested OK (single scenario) |
| `refactor_workflow` | renameProvider, codeActionProvider | Tested OK (single scenario) |

| Function | Description |
|----------|-------------|
| `run_all_scenarios(page, shuffle)` | Run all 10 scenarios sequentially |
| `run_scenario(page, name, **kwargs)` | Run single scenario by name |
| `list_scenarios()` | Return available scenario names |

After a scenario failure, `_recover_ui_state(page)` dismisses stuck dialogs with multiple Escape presses.

---

### workspace.py — Filesystem & Honeypot Environment

Has two responsibilities:

1. **General file operations** — `create_workspace_file`, `create_workspace_dir`, `create_language_file`, `create_workspace_structure`, `clean_workspace`
2. **Honeypot developer environment** — `setup_dev_environment()`

**Not dependent on Playwright** — uses pure `pathlib` and `shutil`.

**Automatically run by `start.sh` when container starts.**

```bash
# Inside start.sh, BEFORE VS Code:
python3 /home/executor/playwright/workspace.py
```

---

## Honeypot Developer Environment

The `setup_dev_environment()` function creates files in two locations:

### /workspace/ (Project Directory)

VS Code opens this folder automatically. Project files that extensions would scan:

| File/Folder | Contents |
|-------------|----------|
| `.env` | DATABASE_URL, JWT_SECRET, OPENAI_API_KEY, STRIPE_SECRET_KEY, AWS keys, SENTRY_DSN |
| `.env.production` | Production DB URL, API key |
| `.env.local` | Local dev credentials |
| `.git/config` | GitHub remote URL (SSH) |
| `src/app.py` | Flask application |
| `src/config.py` | Credential reading via `os.environ.get()` |
| `src/database.py` | Hardcoded DB connection string |
| `src/auth.py` | JWT secret, token operations |
| `src/payments.py` | Stripe API key |
| `src/storage.py` | AWS S3 boto3 client |
| `frontend/.env` | React app env (Stripe publishable key, Sentry DSN) |
| `frontend/package.json` | Node.js dependencies |
| `docker-compose.yml` | DB/Redis passwords in plaintext |
| `credentials/gcp-service-account.json` | GCP service account (fake private key) |
| `credentials/firebase-admin-sdk.json` | Firebase admin SDK |
| `infra/terraform.tfvars` | DB password, Redis password, API secret |
| `infra/main.tf` | AWS RDS definition |
| `scripts/deploy.sh` | Docker login token, SSH commands |
| `scripts/seed.py` | Hardcoded DB password |
| `scripts/backup.sh` | pg_dump connection string |
| `.wallet/keystore.json` | Ethereum wallet (fake) |
| `alembic/env.py` | SQLAlchemy URL |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Production container |
| `README.md` | Project description |

### /home/executor/ (User Profile)

Files accessible by extensions scanning `$HOME` directory:

| File | Contents |
|------|----------|
| `.ssh/id_rsa` | OpenSSH private key (chmod 600) |
| `.ssh/id_rsa.pub` | Public key |
| `.ssh/config` | GitHub + production server |
| `.ssh/known_hosts` | GitHub fingerprint |
| `.aws/credentials` | AWS access key + secret (default & production profiles) |
| `.aws/config` | Region settings |
| `.kube/config` | Kubernetes cluster token |
| `.docker/config.json` | Docker registry auth (ghcr.io, private registry) |
| `.config/gcloud/application_default_credentials.json` | GCP OAuth refresh token |
| `.npmrc` | NPM and GitHub Packages auth tokens |
| `.gitconfig` | Git user info |
| `.git-credentials` | GitHub PAT (plaintext) |
| `.bash_history` | SSH, docker login, kubectl, aws, curl + API key commands |
| `.python_history` | boto3, os.environ accesses |

### Multi-Language Sample Files

For full `onLanguage:*` activation coverage, sample files are created for all supported languages:

| Language | Sample Files |
|----------|--------------|
| TypeScript | `frontend/src/index.ts` |
| Go | `services/api/main.go`, `go.mod` |
| Rust | `services/worker/src/main.rs`, `Cargo.toml` |
| Java | `services/legacy/.../App.java`, `pom.xml` |
| C | `native/parser.c` |
| C++ | `native/engine.cpp` |
| C# | `services/dotnet/Program.cs`, `extrace.sln` |
| Ruby | `scripts/migrate.rb`, `Gemfile` |
| PHP | `legacy/api.php` |
| Swift | `mobile/ios/ExTrace/App.swift` |
| Kotlin | `mobile/android/.../MainActivity.kt` |
| HTML | `frontend/public/index.html` |
| CSS | `frontend/public/styles.css` |
| XML | `config/settings.xml` |

### Design Principles

- All credentials are **fake but correctly formatted** — matches real regex patterns
- AWS keys start with `AKIA...` prefix (real format)
- SSH keys have correct permissions (600/700)
- `.bash_history` contains realistic commands
- File structure reflects a typical startup backend project

---

## Import Strategy

The `executor/playwright/` directory creates a naming conflict with the pip `playwright` package. Solution:

1. **Helper modules** (`commands.py`, `editor.py`, etc.) import each other **directly**: `import keyboard`, `from commands import run_command`
2. **pip `playwright`** package continues to work: `from playwright.sync_api import Page`
3. **`entrypoint.py`** bootstraps by adding its directory to `sys.path`:

```python
_pkg_dir = str(Path(__file__).resolve().parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)
```

4. **`workspace.py`** has no Playwright dependency — run directly by `start.sh` as `python3 /path/to/workspace.py`.

---

## Activation Event Coverage Table

| Activation Event | Triggering Module | Method |
|-----------------|-------------------|--------|
| `*` | — | VS Code startup |
| `onStartupFinished` | — | VS Code startup |
| `onLanguage:*` | `workspace.py` + `editor.py` + `automation.py` | Create language file + open (15 languages) |
| `onCommand:*` | `commands.py` | Run command via Command Palette |
| `workspaceContains:*` | `workspace.py` | Create file when container starts |
| `onView:*` | `sidebar.py` + `automation.py` | Keyboard shortcut or Command Palette |
| `onCustomEditor:*` | `editor.py` | Open matching file type |
| `onWebviewPanel:*` | `commands.py` | Run related command |
| `onDebug:*` | `debug.py` + `automation.py` | Start/stop debug session (F5/Shift+F5) |
| `onDebugResolve:*` | `debug.py` | Create launch.json, start debug |
| `onConfiguration:*` | `settings.py` + `automation.py` | Change theme, edit settings.json |
| `onAuthenticationRequest:*` | — | Automatic (VS Code built-in GitHub auth) |

---

## Usage

### Starting the Container
```bash
make executor-build     # Build image
make executor-up        # Start container (honeypot + VS Code automatic)
```

### Running Automation

```bash
# Inside the container (docker exec or make executor-shell):

# Run all 10 scenarios
python3 /home/executor/playwright/entrypoint.py

# Run all scenarios + activation monitoring (generates JSON report)
python3 /home/executor/playwright/entrypoint.py --monitor

# Run single scenario
python3 /home/executor/playwright/entrypoint.py --scenario coding_session

# Single scenario + monitoring
python3 /home/executor/playwright/entrypoint.py --monitor --scenario debug_session

# List available scenarios
python3 /home/executor/playwright/entrypoint.py --list

# Randomize scenario order
python3 /home/executor/playwright/entrypoint.py --shuffle

# Custom report output path
python3 /home/executor/playwright/entrypoint.py --monitor --report-path /results/my_report.json

# Legacy quick demo
python3 /home/executor/playwright/entrypoint.py --demo
```

**Important:** Use `PYTHONUNBUFFERED=1` when running via `docker exec` for real-time output:
```bash
docker exec -e PYTHONUNBUFFERED=1 automation_executor python3 /home/executor/playwright/entrypoint.py --monitor
```

### Observing via noVNC
```
http://localhost:6080/vnc.html
```

### Container Shell
```bash
make executor-shell
```

### Monitoring Report Output

When `--monitor` is used, a JSON report is saved to `/results/activation_report.json`:

```json
{
  "summary": {
    "total_activated": 15,
    "unique_extensions": 15,
    "running_extensions": 12,
    "monitoring_duration_s": 48.0,
    "extension_ids": ["vscode.css-language-features", "vscode.git", ...]
  },
  "activated": [
    {
      "extension_id": "vscode.typescript-language-features",
      "activation_event": "onLanguage:javascript",
      "duration_ms": null,
      "timestamp": "2026-02-16 12:08:44.501",
      "source": "log"
    }
  ],
  "running_extensions": [
    {
      "extension_id": "vscode.typescript-language-features",
      "name": "TypeScript and JavaScript Language Features",
      "activation_time_ms": 153,
      "status": "active"
    }
  ]
}
```

---

## Known Limitations

| Limitation | Description | Workaround |
|------------|-------------|------------|
| Native dialogs | GTK file picker not in Playwright DOM | Interact via `xdotool` |
| Package name conflict | `playwright/` directory conflicts with pip package | `sys.path` bootstrap + direct imports |
| Quick Input widget | VS Code doesn't remove from DOM, sets `display:none` | Custom CSS selector |
| Container memory | 2GB limit can cause VS Code crash under heavy load | Close editors periodically, reduce open tabs |
| CDP single connection | Only one Playwright connection at a time; orphaned processes block new ones | Kill orphaned processes before reconnecting |

---

## Known Bugs (as of 2026-02-16)

These were discovered during live testing and need to be fixed in the next session:

### BUG-1: `settings_modification` scenario — quick-input timeout

**Symptom:** `Page.wait_for_selector: Timeout 5000ms exceeded` when `change_theme()` runs.

**Root cause:** `commands.run_command()` expects the quick-input widget to close after Enter. But the Color Theme picker in VS Code stays open for live preview even after pressing Enter. The `_wait_quick_input_close()` times out.

**Current state:** Partially fixed — `change_theme()` was rewritten to use `open_command_palette()` directly instead of `run_command()`, with an Escape at the end. However the settings scenario still calls `search_setting()` which opens the Settings UI, and the `open_settings` calls inside also seem to leave state that conflicts with the theme picker.

**Fix needed:** The `settings_modification` scenario needs restructuring. The `search_setting()` function repeatedly opens Settings UI, and between that and `change_theme()`, the quick-input state gets confused. Consider: (1) closing Settings editor tab before calling `change_theme()`, (2) using a dedicated settings scenario that doesn't mix UI Settings with Command Palette theme picker.

**Impact:** `_recover_ui_state()` catches the error and subsequent scenarios continue.

### BUG-2: VS Code crash (Target crashed) under full automation

**Symptom:** `Keyboard.press: Target crashed` — VS Code renderer process crashes, all subsequent Playwright operations fail.

**Root cause:** Container has `mem_limit: 2g`. Running all 10 scenarios sequentially (especially `project_exploration` which opens many files + language servers) causes VS Code to exceed memory.

**Current state:** Partially fixed — `project_exploration` was changed to close editors every 5 files. However when preceded by 6 other scenarios that each open files/terminals, cumulative memory can still exceed the limit.

**Fix needed:** Options: (1) increase `mem_limit` in docker-compose.yml to 4g, (2) add `editor.close_all_editors()` cleanup between ALL scenarios in `run_all_scenarios()`, (3) reduce scenario scope, (4) add memory monitoring to abort before crash.

**Impact:** When VS Code crashes, Playwright loses the CDP connection. The `monitor.stop()` Strategy 2 (UI scraping) also fails since it needs a live page. Strategy 1 (log parsing) still works since it reads files.

### BUG-3: `monitor.stop()` not crash-resilient enough

**Symptom:** When VS Code has crashed (Target crashed), `monitor.stop()` → Strategy 2 (`get_running_extensions`) tries to open Command Palette and throws an unhandled exception, causing the entire entrypoint to fail with a traceback.

**Root cause:** The try-except in `stop()` catches the exception for Strategy 2, but the `Keyboard.press: Target crashed` exception propagates past the inner `commands.run_command()` call before hitting the outer try-except. The issue is the exception happens during `page.keyboard.press()` inside `commands.open_command_palette()`.

**Fix needed:** The try-except in `stop()` for Strategy 2 should already catch this. Verify the exception is actually being caught — the traceback in the test output suggests it isn't. May need to make `get_running_extensions()` itself internally catch all exceptions and return an empty list on failure.

---

## Test Results (2026-02-16)

### Single scenario test: `project_exploration` with `--monitor`

**Result: PASS**

```
Monitoring duration : 48.0s
Activations found   : 15
Unique extensions   : 15
Running extensions  : 12
```

All three monitoring strategies worked:
- Strategy 1 (log parsing): 15 activations parsed from exthost.log
- Strategy 2 (UI scraping): 12 running extensions found with correct IDs and timing
- Strategy 3 (log reading): 1,339,836 chars read from Extension Host log

Detected activation events:
- `onAuthenticationRequest:github` → vscode.github-authentication
- `onLanguage` → vscode.emmet
- `*` → vscode.git-base, vscode.git, vscode.github
- `workspaceContains:package.json` → vscode.npm
- `onStartupFinished` → vscode.debug-auto-launch, vscode.merge-conflict
- `onLanguage:json` → vscode.configuration-editing, vscode.extension-editing, vscode.json-language-features
- `onLanguage:javascript` → vscode.typescript-language-features
- `onLanguage:php` → vscode.php-language-features
- `onLanguage:html` → vscode.html-language-features
- `onLanguage:css` → vscode.css-language-features

### Full automation test: all 10 scenarios with `--monitor`

**Result: PARTIAL — 5/10 scenarios passed before VS Code crashed**

| Scenario | Result |
|----------|--------|
| coding_session | PASS |
| debug_session | PASS |
| terminal_usage | PASS |
| git_workflow | PASS |
| extension_browsing | PASS |
| settings_modification | FAIL (quick-input timeout, BUG-1) |
| project_exploration | FAIL (Target crashed, BUG-2) |
| search_workflow | FAIL (Target crashed, BUG-2) |
| diagnostics_check | FAIL (Target crashed, BUG-2) |
| refactor_workflow | FAIL (Target crashed, BUG-2) |

The VS Code crash at `project_exploration` was caused by cumulative memory pressure from the 6 preceding scenarios. After the crash, all subsequent scenarios and monitoring Strategy 2 also failed (BUG-3).

Strategy 1 (log parsing) still succeeded: parsed 14 activations from log files.

---

## Next Steps

- [ ] Fix BUG-1: Restructure `settings_modification` scenario
- [ ] Fix BUG-2: Add inter-scenario cleanup + increase memory limit
- [ ] Fix BUG-3: Make `monitor.stop()` fully crash-resilient
- [ ] Extension install/uninstall automation (`code --install-extension`)
- [ ] Network/filesystem/process monitoring integration (tcpdump, inotifywait, strace)
- [ ] Automatic trigger selection based on `activationEvents` from DB
- [ ] Save analysis results to database
- [ ] Persona-based simulation (Phase 2)
