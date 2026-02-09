# Executor: Playwright UI Automation & Honeypot Environment

`Last Updated: 2026-02-09` | `Status: Active Development`

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
    ├── editor.py              # Editor: open/save/close/type files
    ├── sidebar.py             # Activity Bar and sidebar views
    ├── terminal.py            # Integrated terminal
    ├── panel.py               # Bottom panel: problems, output, debug console
    ├── workspace.py           # Filesystem: honeypot environment + file operations
    ├── language_samples.py    # Multi-language sample files for activation coverage
    └── entrypoint.py          # Demo script using all helpers
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
6. VS Code /workspace            -> GUI starts (CDP port 9222)
7. noVNC (port 6080)            -> Browser access
```

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

**Full list:** Command Palette, Quick Open, Editor (new/save/close), Sidebar (explorer/search/scm/debug/extensions), Panel, Terminal, Navigation.

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
| `new_terminal(page)` | Create new terminal (Command Palette) |
| `type_in_terminal(page, text, press_enter=True)` | Type in terminal, presses Enter by default |

`press_enter=True` is the default — commands are automatically executed after typing.

---

### panel.py — Bottom Panel

| Function | Description |
|----------|-------------|
| `toggle_panel(page)` | Show/hide bottom panel (Ctrl+J) |
| `open_problems(page)` | Problems tab (Command Palette) |
| `open_output(page)` | Output tab |
| `open_debug_console(page)` | Debug Console tab |

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
| `onLanguage:*` | `workspace.py` + `editor.py` | Create language-appropriate file + open |
| `onCommand:*` | `commands.py` | Run command via Command Palette |
| `workspaceContains:*` | `workspace.py` | Create file when container starts |
| `onView:*` | `sidebar.py` | Keyboard shortcut or Command Palette |
| `onCustomEditor:*` | `editor.py` | Open matching file type |
| `onWebviewPanel:*` | `commands.py` | Run related command |

---

## Usage

### Starting the Container
```bash
make executor-build     # Build image
make executor-up        # Start container (honeypot + VS Code automatic)
```

### Running Playwright Demo
```bash
make executor-playwright   # Runs entrypoint.py
```

### Observing via noVNC
```
http://localhost:6080/vnc.html
```

### Container Shell
```bash
make executor-shell
```

---

## Known Limitations

| Limitation | Description | Workaround |
|------------|-------------|------------|
| Native dialogs | GTK file picker not in Playwright DOM | Interact via `xdotool` |
| Package name conflict | `playwright/` directory conflicts with pip package | `sys.path` bootstrap + direct imports |
| Quick Input widget | VS Code doesn't remove from DOM, sets `display:none` | Custom CSS selector |

---

## Next Steps

- [ ] Extension install/uninstall automation (`code --install-extension`)
- [ ] Monitoring integration (tcpdump, inotifywait, strace)
- [ ] Automatic trigger selection based on activation events
- [ ] Save analysis results to database
- [ ] Persona-based simulation (Phase 2)
