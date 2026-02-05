# ExTrace Dynamic Analysis Roadmap & TODO

This document outlines the phased approach for building VS Code extension dynamic analysis automation.

---

## 🎯 Overview

| Phase | Approach | Xvfb Required | Coverage | Complexity |
|-------|----------|---------------|----------|------------|
| **Phase 1** | CLI-Based (Headless) | ❌ No | ~60-70% | Low |
| **Phase 2** | GUI-Based (Xvfb) | ✅ Yes | 100% | High |

---

## 📋 Activation Event Support Matrix

| Activation Event | Phase 1 (CLI) | Phase 2 (GUI) | Trigger Method |
|------------------|---------------|---------------|----------------|
| `*` | ✅ | ✅ | Auto-activate |
| `onStartupFinished` | ✅ | ✅ | VSCode start |
| `onLanguage:*` | ✅ | ✅ | `code file.py` |
| `onCommand:*` | ✅ | ✅ | `--command` flag |
| `workspaceContains:*` | ✅ | ✅ | Open folder |
| `onFileSystem:*` | ⚠️ Partial | ✅ | FileSystem provider |
| `onView:*` | ❌ | ✅ | Sidebar click |
| `onWebviewPanel:*` | ❌ | ✅ | WebView open |
| `onCustomEditor:*` | ❌ | ✅ | Custom editor |
| `onUri` | ⚠️ Partial | ✅ | URI handler |

---

# Phase 1: CLI-Based Dynamic Analysis (No GUI)

> **Goal:** Maximum coverage without graphical interface dependencies.
> **Target:** Extensions with CLI-compatible activation events.

## 1.1 Docker Environment Setup

### ⬜ Base Docker Image
- [ ] Create `Dockerfile.cli-executor`
  - Base: `node:20-slim` or `ubuntu:22.04`
  - Install: VSCode CLI (`code`), monitoring tools
  - No X11/Xvfb dependencies
- [ ] Add to `docker-compose.yml` as `cli-executor` service
- [ ] Configure volume mounts for extensions and results

### ⬜ VSCode CLI Installation
- [ ] Download official VSCode `.deb` package
- [ ] Install with `--no-sandbox` flag for container
- [ ] Verify `code --version` works in container
- [ ] Configure user data directory for isolation

## 1.2 Extension Loading & Activation

### ⬜ Extension Installer Module
- [ ] Create `executor/cli_executor.py`
- [ ] Implement `install_extension(vsix_path: Path) -> bool`
  ```bash
  code --install-extension ./extension.vsix --force
  ```
- [ ] Implement `uninstall_extension(extension_id: str) -> bool`
- [ ] Handle installation errors and timeouts

### ⬜ Activation Trigger Engine
- [ ] Create `executor/triggers.py`
- [ ] Implement trigger strategies based on activation events:
  ```python
  class TriggerStrategy(Protocol):
      def trigger(self, extension: Extension) -> TriggerResult: ...

  class OnLanguageTrigger(TriggerStrategy):
      # code --wait test.{language}

  class OnCommandTrigger(TriggerStrategy):
      # code --command {command_id}

  class OnStartupTrigger(TriggerStrategy):
      # code --wait .
  ```
- [ ] Implement trigger selection based on `activationEvents` from DB
- [ ] Add timeout handling (max 60s per trigger)

### ⬜ Smart Trigger Selection
- [ ] Query `extension_activation_events` table
- [ ] Implement `needs_gui(events: list[str]) -> bool` helper
- [ ] Route to appropriate executor (CLI vs GUI placeholder)
- [ ] Log trigger decisions for audit

## 1.3 Monitoring & Telemetry

### ⬜ Process Monitoring
- [ ] Create `executor/monitors/process_monitor.py`
- [ ] Capture spawned child processes
- [ ] Monitor CPU/memory usage
- [ ] Detect unusual process behavior (crypto mining, etc.)

### ⬜ Network Monitoring
- [ ] Create `executor/monitors/network_monitor.py`
- [ ] Implement tcpdump/tshark wrapper
- [ ] Capture DNS queries, HTTP(S) requests
- [ ] Detect data exfiltration patterns
- [ ] Log external domain connections

### ⬜ Filesystem Monitoring
- [ ] Create `executor/monitors/fs_monitor.py`
- [ ] Use `inotifywait` for file events
- [ ] Track file creation/modification/deletion
- [ ] Detect suspicious paths (credentials, SSH keys, etc.)

### ⬜ Environment Variable Access
- [ ] Monitor `process.env` access patterns
- [ ] Detect credential harvesting attempts
- [ ] Log accessed environment variables

## 1.4 Results Storage

### ⬜ Analysis Results Schema
- [ ] Create migration: `analysis_runs` table
  ```sql
  id, extension_id, run_type (cli/gui), started_at, completed_at, status
  ```
- [ ] Create migration: `analysis_network_events` table
  ```sql
  id, run_id, timestamp, event_type, source, destination, payload_hash
  ```
- [ ] Create migration: `analysis_process_events` table
- [ ] Create migration: `analysis_fs_events` table
- [ ] Create migration: `analysis_risk_signals` table

### ⬜ Risk Scoring Engine
- [ ] Create `analyzer/risk_scorer.py`
- [ ] Define risk indicators and weights:
  - Network to unknown domains: +20
  - Credential file access: +50
  - Obfuscated code detected: +30
  - Spawns shell processes: +40
- [ ] Calculate aggregate risk score
- [ ] Generate risk summary

## 1.5 API Endpoints

### ⬜ Analysis Endpoints
- [ ] `POST /api/v1/analyze/{extension_id}` - Start analysis
- [ ] `GET /api/v1/analyze/{run_id}/status` - Get status
- [ ] `GET /api/v1/analyze/{run_id}/results` - Get results
- [ ] `GET /api/v1/extensions/{id}/risk-score` - Get risk score

---

# Phase 2: GUI-Based Dynamic Analysis (Xvfb)

> **Goal:** Full coverage including UI-dependent extensions.
> **Target:** Extensions with `onView`, `onWebviewPanel`, `onCustomEditor`.
> **Prerequisite:** Phase 1 completed.

## 2.1 Xvfb Docker Environment

### ⬜ Extended Docker Image
- [ ] Create `Dockerfile.gui-executor`
  - Base: Phase 1 image
  - Add: `xvfb`, `xdotool`, `xte`, `scrot`
  - Optional: `pulseaudio` for audio testing
- [ ] Configure virtual display (`:99`)
- [ ] Add VNC server for debugging (optional)

### ⬜ Display Management
- [ ] Create `executor/display_manager.py`
- [ ] Implement `start_xvfb(display: str, resolution: str) -> Process`
- [ ] Implement `stop_xvfb(process: Process) -> None`
- [ ] Add screenshot capture utility

## 2.2 GUI Automation

### ⬜ VSCode Window Control
- [ ] Create `executor/gui_executor.py`
- [ ] Launch VSCode with `DISPLAY=:99 code --wait`
- [ ] Implement window focus/maximize with `xdotool`
- [ ] Add startup wait for VSCode ready state

### ⬜ UI Interaction Engine
- [ ] Create `executor/interactions/`
- [ ] Implement mouse actions:
  - `click(x, y)`
  - `double_click(x, y)`
  - `right_click(x, y)`
- [ ] Implement keyboard actions:
  - `type_text(text)`
  - `press_key(key)`
  - `hotkey(keys)`
- [ ] Implement navigation:
  - `open_command_palette()` → Ctrl+Shift+P
  - `open_sidebar(name)` → View shortcuts
  - `open_extension_view()`

### ⬜ View Trigger Implementation
- [ ] Implement `OnViewTrigger` strategy
- [ ] Map view IDs to UI navigation paths
- [ ] Handle dynamic view loading

### ⬜ WebView Interaction
- [ ] Detect WebView panels
- [ ] Capture WebView content
- [ ] Interact with WebView elements (if possible)

## 2.3 Persona-Based Simulation

### ⬜ Define User Personas
- [ ] **Curious User**
  - Explores multiple features
  - Opens settings, documentation
  - Long session duration
- [ ] **Cautious User**
  - Checks permissions first
  - Reads privacy policy
  - Minimal interaction
- [ ] **Impatient User**
  - Fast clicks
  - Skips dialogs
  - Short session
- [ ] **Normal User**
  - Balanced behavior
  - Typical workflow

### ⬜ Randomized Execution
- [ ] Generate seed per run for reproducibility
- [ ] Randomize:
  - Click timing (human-like delays)
  - Scroll depth
  - Navigation order
- [ ] Log seed for replay capability

## 2.4 Anti-Detection Measures

### ⬜ Fingerprinting Resistance
- [ ] Rotate browser fingerprints
- [ ] Randomize window size
- [ ] Vary user agent strings
- [ ] Disable automation indicators

### ⬜ Behavioral Realism
- [ ] Add human-like mouse movements (Bezier curves)
- [ ] Implement realistic typing speed
- [ ] Add natural pauses between actions

## 2.5 Evidence Collection

### ⬜ Screenshot Capture
- [ ] Capture before/after each action
- [ ] Store in organized directory structure
- [ ] Compress and hash for integrity

### ⬜ Screen Recording
- [ ] Record entire session (ffmpeg + x11grab)
- [ ] Compress with reasonable quality
- [ ] Link recordings to analysis runs

### ⬜ Interaction Timeline
- [ ] Log every action with timestamp
- [ ] Map actions to consequences:
  - Action → Network request
  - Action → DOM change
  - Action → Process spawn

---

# Cross-Phase Components

## Output & Reporting

### ⬜ Structured Output Schema
```json
{
  "run_id": "uuid",
  "extension_id": 123,
  "phase": "cli|gui",
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

### ⬜ Explainability Layer
- [ ] Generate "Why suspicious" summary
- [ ] Evidence-backed reasoning
- [ ] Highlight interaction-gated findings
- [ ] Diff between baseline and AI mode

### ⬜ Visualization (Future)
- [ ] Timeline view of events
- [ ] Domain relationship graph
- [ ] Action → consequence graph

---

## Design Principles

1. **Phase 1 First**: CLI covers most malicious extensions (they want early activation)
2. **GUI When Needed**: Only for UI-dependent extensions
3. **Determinism for Speed**: Fast baseline analysis
4. **Randomness for Evasion**: AI mode for sophisticated malware
5. **Audit Everything**: Every action produces evidence
6. **Fail Safe**: Sandbox isolation, resource limits, timeouts

---

## Success Criteria

### Phase 1 Complete When:
- [ ] Can install/uninstall extensions via CLI
- [ ] Can trigger CLI-compatible activation events
- [ ] Network/process/filesystem monitoring works
- [ ] Results stored in database
- [ ] Basic risk scoring functional
- [ ] API endpoints working

### Phase 2 Complete When:
- [ ] Xvfb environment stable
- [ ] Can trigger all activation events including UI-based
- [ ] Persona-based simulation working
- [ ] Screenshot/recording capture working
- [ ] Full coverage of extension behaviors
