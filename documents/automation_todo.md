# ExTrace Dynamic Analysis Roadmap & TODO

This document outlines the phased approach for building VS Code extension dynamic analysis automation.

---

## Overview

| Phase | Approach | Coverage | Status |
|-------|----------|----------|--------|
| **Phase 0** | Metadata parsing from `package.json` | Metadata only | Done |
| **Phase 1** | Docker + Xvfb full GUI analysis | Current automation: 12/25 events (~48%) | Active |
| **Phase 2** | Automated GUI interaction + persona simulation | Behavioral analysis | Future |

**Key approach:** VS Code extensions require a running Extension Host process to activate, which needs a full GUI instance. Xvfb provides this with low overhead compared to a real display and enables broad activation-event testing in a single stack.

---

## Activation Event Support Matrix

Current Playwright baseline covers the most common activation events. For the detailed gap analysis and next candidates, see `documents/EXECUTOR_PLAYWRIGHT.md`.

| Activation Event | Automated | Trigger Method | Implementing Module |
|------------------|-----------|----------------|---------------------|
| `*` | Yes | VS Code startup | — (automatic) |
| `onStartupFinished` | Yes | VS Code startup | — (automatic) |
| `onLanguage:*` | Yes | Open file with matching language | `workspace.py` + `editor.py` + `automation.py` |
| `onCommand:*` | Yes | Command Palette via Playwright CDP | `commands.py` |
| `workspaceContains:*` | Yes | Honeypot workspace at container start | `workspace.py` (via `start.sh`) |
| `onView:*` | Yes | Sidebar keyboard shortcuts via CDP | `sidebar.py` + `automation.py` |
| `onDebug:*` | Yes | Debug lifecycle shortcuts/actions | `debug.py` + `automation.py` |
| `onDebugResolve:*` | Yes | Launch config + debug start | `debug.py` |
| `onDebugInitialConfigurations` | Yes | Initial debug configuration flow | `debug.py` |
| `onConfiguration:*` | Yes | Settings JSON/UI interactions | `settings.py` + `automation.py` |
| `onTerminalShellIntegration:*` | Yes | Integrated terminal usage | `terminal.py` + `automation.py` |
| `onAuthenticationRequest:*` | Yes | Built-in auth flow | — (automatic) |

---

# Phase 1: Docker + Xvfb Dynamic Analysis (Active)

> **Goal:** Full VS Code GUI running in Docker with virtual display, monitored by network/filesystem/process tools.

## 1.1 Docker Environment Setup

### Done: Base Docker Image
- [x] Create `executor/Dockerfile` (Ubuntu 22.04)
- [x] Install VS Code (auto-detects arm64/x64 architecture)
- [x] Install Xvfb, openbox, x11vnc, noVNC, xdotool
- [x] Install monitoring tools: tcpdump, tshark, inotify-tools, strace, procps, net-tools
- [x] Install Node.js 20
- [x] Non-root `executor` user with capture capabilities
- [x] Create `executor/start.sh` entrypoint (Xvfb :99, openbox, VNC, noVNC)
- [x] Add to `docker-compose.yml` as `executor` service
- [x] Port 6080 exposed for noVNC browser access
- [x] Volume mounts: `./extensions:/extensions-input:ro`, `./output:/results`
- [x] Resource limits: 4GB RAM, 2 CPUs
- [x] `cap_add: NET_RAW, SYS_PTRACE` for monitoring tools
- [x] `setcap` on tcpdump/dumpcap for non-root capture
- [x] Makefile targets: `executor-build`, `executor-up`, `executor-down`, `executor-shell`, `executor-test`

### Current container stack:
```
Xvfb :99 (1920x1080x24)  ->  Virtual display
openbox                    ->  Window manager
x11vnc                     ->  VNC server (port 5900)
workspace.py               ->  Honeypot dev environment setup
VS Code settings.json      ->  Trust/telemetry disabled
VS Code /workspace         ->  Full GUI instance (CDP port 9222)
noVNC                      ->  Browser access (port 6080)
```

### Access:
- **noVNC:** `http://localhost:6080/vnc.html` (browser-based VNC)
- **Shell:** `make executor-shell`
- **Playwright:** `make executor-playwright`

### Done: VS Code Auto-Configuration
- [x] Workspace Trust dialog auto-disabled (`security.workspace.trust.enabled: false`)
- [x] Welcome tab suppressed (`workbench.startupEditor: none`)
- [x] Telemetry and auto-update disabled
- [x] VS Code opens `/workspace` folder automatically on startup
- [x] Settings written by `start.sh` before VS Code launch

## 1.2 Playwright UI Automation (NEW)

> **Full documentation:** [`documents/EXECUTOR_PLAYWRIGHT.md`](EXECUTOR_PLAYWRIGHT.md)

### Done: Playwright Helper Modules
- [x] Create `executor/playwright/keyboard.py` — all VS Code shortcuts as constants
- [x] Create `executor/playwright/vscode.py` — CDP connect, ready wait, disconnect
- [x] Create `executor/playwright/commands.py` — Command Palette open/run/quick-open (with close-wait)
- [x] Create `executor/playwright/editor.py` — new file, save (xdotool for native dialog), close, type, open
- [x] Create `executor/playwright/sidebar.py` — Explorer, Search, SCM, Debug, Extensions, custom views
- [x] Create `executor/playwright/terminal.py` — toggle, new, type (with auto-Enter)
- [x] Create `executor/playwright/panel.py` — Problems, Output, Debug Console
- [x] Create `executor/playwright/workspace.py` — filesystem helpers + honeypot environment
- [x] Create `executor/playwright/entrypoint.py` — demo using all modules
- [x] Makefile target: `make executor-playwright`

### Done: Extended Modules (2026-02-16)
- [x] `keyboard.py` — Added activation trigger shortcuts: debug (F5/Shift+F5/F10/F11), settings (Ctrl+,), output/problems focus, format/definition/suggest/rename, fullscreen, new terminal
- [x] `editor.py` — Added: `format_document()`, `go_to_definition()`, `trigger_suggest()`, `rename_symbol()`, `select_all()`
- [x] `panel.py` — Added: `focus_problems()`, `focus_output()` (direct keyboard shortcuts)
- [x] `terminal.py` — `new_terminal()` now uses keyboard shortcut, old version as `new_terminal_via_command()`
- [x] Create `executor/playwright/debug.py` — Debug lifecycle: start/stop/step_over/step_into/breakpoint/launch.json
- [x] Create `executor/playwright/settings.py` — Settings UI, settings.json, theme change, fullscreen
- [x] Create `executor/playwright/automation.py` — 10 user behavior simulation scenarios
- [x] Create `executor/playwright/monitor.py` — Extension Host activation monitoring (3 strategies)
- [x] `entrypoint.py` — CLI: `--monitor`, `--scenario`, `--list`, `--shuffle`, `--report-path`, `--demo`
- [x] `start.sh` — Added `--log trace` to VS Code launch, log dir symlink

### Done: Extension Host Monitoring (2026-02-16)
- [x] VS Code started with `--log trace` for verbose Extension Host logging
- [x] Log file discovery and parsing (regex patterns for multiple VS Code versions)
- [x] Running Extensions UI scraping via Playwright (`aria-label` for extension IDs)
- [x] Extension Host log file reading for full post-hoc analysis
- [x] Real-time log watching via `inotifywait` (with polling fallback)
- [x] `ExtensionMonitor` context manager wrapping scenarios
- [x] JSON report generation with `ActivationReport.save(path)`
- [x] Human-readable summary via `ActivationReport.print_summary()`

### Resolved Bugs (2026-02-16)
- [x] BUG-1: `settings_modification` scenario — quick-input timeout on theme picker (Fixed: JSON edits first, theme change with timeout fallback)
- [x] BUG-2: VS Code crashes (Target crashed) under full 10-scenario run (Fixed: increased to 4GB + inter-scenario cleanup)
- [x] BUG-3: `monitor.stop()` Strategy 2 not fully crash-resilient when VS Code is dead (Fixed: broadened exception catch)

### Done: Honeypot Developer Environment
- [x] Fake `.env`, `.env.production`, `.env.local` with realistic API keys
- [x] Fake SSH keys with correct permissions (600/700) in `~/.ssh/`
- [x] Fake AWS credentials (`~/.aws/credentials`, `~/.aws/config`)
- [x] Fake Kubernetes config (`~/.kube/config`)
- [x] Fake Docker registry auth (`~/.docker/config.json`)
- [x] Fake GCP/Firebase service accounts in `credentials/`
- [x] Fake `.npmrc`, `.gitconfig`, `.git-credentials`
- [x] Realistic `.bash_history` and `.python_history`
- [x] Python source code with hardcoded secrets (`src/`)
- [x] Deploy/backup scripts with embedded credentials
- [x] Terraform vars, docker-compose, Dockerfile with passwords
- [x] Crypto wallet keystore (`.wallet/`)
- [x] Environment auto-setup via `start.sh` (before VS Code starts)

### TODO: Extension Installer Module
- [ ] Create `executor/extension_manager.py`
- [ ] Implement `install_extension(path: Path) -> bool` using `code --install-extension`
- [ ] Implement `uninstall_extension(extension_id: str) -> bool`
- [ ] Handle installation errors and timeouts

### TODO: Activation Trigger Engine
- [ ] Create `executor/triggers.py`
- [ ] Implement trigger selection based on `activationEvents` from DB
- [ ] Use Playwright helpers for each trigger type:
  - `onCommand:*` → `commands.run_command()`
  - `onLanguage:*` → `workspace.create_language_file()` + `editor.open_file_by_name()`
  - `onView:*` → `sidebar.open_view_by_command()`
  - `workspaceContains:*` → `workspace.create_workspace_file()` (auto at startup)
- [ ] Add timeout handling (max 60s per trigger)

## 1.3 Monitoring & Telemetry

### Process Monitoring
- [ ] Create `executor/monitors/process_monitor.py`
- [ ] Capture spawned child processes
- [ ] Monitor CPU/memory usage
- [ ] Detect unusual process behavior (crypto mining, etc.)

### Network Monitoring
- [ ] Create `executor/monitors/network_monitor.py`
- [ ] Implement tcpdump/tshark wrapper
- [ ] Capture DNS queries, HTTP(S) requests
- [ ] Detect data exfiltration patterns
- [ ] Log external domain connections

### Filesystem Monitoring
- [ ] Create `executor/monitors/fs_monitor.py`
- [ ] Use `inotifywait` for file events
- [ ] Track file creation/modification/deletion
- [ ] Detect suspicious paths (credentials, SSH keys, etc.)

### Environment Variable Access
- [ ] Monitor `process.env` access patterns
- [ ] Detect credential harvesting attempts
- [ ] Log accessed environment variables

## 1.4 Results Storage

### Analysis Results Schema
- [ ] Create migration: `analysis_runs` table
  ```sql
  id, extension_id, started_at, completed_at, status
  ```
- [ ] Create migration: `analysis_network_events` table
  ```sql
  id, run_id, timestamp, event_type, source, destination, payload_hash
  ```
- [ ] Create migration: `analysis_process_events` table
- [ ] Create migration: `analysis_fs_events` table
- [ ] Create migration: `analysis_risk_signals` table

### Risk Scoring Engine
- [ ] Create `analyzer/risk_scorer.py`
- [ ] Define risk indicators and weights:
  - Network to unknown domains: +20
  - Credential file access: +50
  - Obfuscated code detected: +30
  - Spawns shell processes: +40
- [ ] Calculate aggregate risk score
- [ ] Generate risk summary

## 1.5 API Endpoints

### Analysis Endpoints
- [ ] `POST /api/v1/analyze/{extension_id}` - Start analysis
- [ ] `GET /api/v1/analyze/{run_id}/status` - Get status
- [ ] `GET /api/v1/analyze/{run_id}/results` - Get results
- [ ] `GET /api/v1/extensions/{id}/risk-score` - Get risk score

---

# Phase 2: Automated GUI Interaction & Persona Simulation (Future)

> **Goal:** Automated interaction with VS Code GUI for behavioral analysis.
> **Prerequisite:** Phase 1 completed.

## 2.1 GUI Automation

### VS Code Window Control (Partially done via Playwright)
- [x] CDP connection to VS Code via Playwright (`vscode.py`)
- [x] Startup wait for VS Code ready state (`wait_until_ready`)
- [ ] Window focus/maximize with `xdotool` (for edge cases)

### UI Interaction Engine (Partially done via Playwright)
- [x] Keyboard actions via Playwright CDP: `type_text`, `press_key`, `hotkey` (`keyboard.py` + all modules)
- [x] Command Palette navigation (`commands.py`)
- [x] Sidebar navigation (`sidebar.py`)
- [x] Editor interaction (`editor.py`)
- [x] Terminal interaction (`terminal.py`)
- [x] Native dialog interaction via `xdotool` (`editor.save_file_as`)
- [ ] Mouse actions: `click(x, y)`, `double_click(x, y)`, `right_click(x, y)`

### WebView Interaction
- [ ] Detect WebView panels
- [ ] Capture WebView content
- [ ] Interact with WebView elements (if possible)

## 2.2 Persona-Based Simulation

### Define User Personas
- [ ] **Curious User** - Explores multiple features, opens settings, long session
- [ ] **Cautious User** - Checks permissions first, minimal interaction
- [ ] **Impatient User** - Fast clicks, skips dialogs, short session
- [ ] **Normal User** - Balanced behavior, typical workflow

### Randomized Execution
- [ ] Generate seed per run for reproducibility
- [ ] Randomize: click timing, scroll depth, navigation order
- [ ] Log seed for replay capability

## 2.3 Anti-Detection Measures

### Fingerprinting Resistance
- [ ] Rotate browser fingerprints
- [ ] Randomize window size
- [ ] Vary user agent strings
- [ ] Disable automation indicators

### Behavioral Realism
- [ ] Add human-like mouse movements (Bezier curves)
- [ ] Implement realistic typing speed
- [ ] Add natural pauses between actions

## 2.4 Evidence Collection

### Screenshot Capture
- [ ] Capture before/after each action
- [ ] Store in organized directory structure
- [ ] Compress and hash for integrity

### Screen Recording
- [ ] Record entire session (ffmpeg + x11grab)
- [ ] Compress with reasonable quality
- [ ] Link recordings to analysis runs

### Interaction Timeline
- [ ] Log every action with timestamp
- [ ] Map actions to consequences (Action -> Network request, DOM change, Process spawn)

---

# Cross-Phase Components

## Output & Reporting

### Structured Output Schema
```json
{
  "run_id": "uuid",
  "extension_id": 123,
  "duration_ms": 45000,
  "actions": [...],
  "network_events": [...],
  "process_events": [...],
  "fs_events": [...],
  "risk_signals": [...],
  "risk_score": 75,
  "summary": "..."
}
```

### Explainability Layer
- [ ] Generate "Why suspicious" summary
- [ ] Evidence-backed reasoning
- [ ] Highlight interaction-gated findings

### Visualization (Future)
- [ ] Timeline view of events
- [ ] Domain relationship graph
- [ ] Action -> consequence graph

---

## Design Principles

1. **Single Stack**: Xvfb + full GUI covers all extension types
2. **Full Activation**: Every activation event can be triggered
3. **Audit Everything**: Every action produces evidence
4. **Fail Safe**: Sandbox isolation, resource limits, timeouts
5. **Determinism for Speed**: Fast baseline analysis
6. **Randomness for Evasion**: AI mode for sophisticated malware

---

## Success Criteria

### Phase 1 Complete When:
- [ ] Can install/uninstall extensions via CLI inside Xvfb container
- [x] Can trigger activation events via Playwright UI helpers (commands, editor, sidebar, terminal, panel)
- [ ] Can trigger ALL activation event types (current baseline: 12/25 via 10 automation scenarios)
- [x] Extension Host activation monitoring working (log parsing + UI scraping + log reading)
- [x] Honeypot developer environment auto-deployed at container start
- [x] VS Code auto-configured (trust disabled, workspace opened, --log trace)
- [x] noVNC access verified for debugging
- [ ] Network/process/filesystem monitoring works
- [ ] Results stored in database
- [ ] Basic risk scoring functional
- [ ] API endpoints working

### Phase 2 Complete When:
- [x] Automated Playwright CDP interaction working (replaces xdotool/Puppeteer for most cases)
- [ ] Persona-based simulation working
- [ ] Screenshot/recording capture working
- [ ] Anti-detection measures in place
- [ ] Full coverage of extension behaviors
