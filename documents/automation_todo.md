# ExTrace Dynamic Analysis Roadmap & TODO

This document outlines the phased approach for building VS Code extension dynamic analysis automation.

---

## Overview

| Phase | Approach | Coverage | Status |
|-------|----------|----------|--------|
| **Phase 0** | Static analysis of `package.json` | Metadata only | Done |
| **Phase 1** | Docker + Xvfb full GUI analysis | 100% activation events | Active |
| **Phase 2** | Automated GUI interaction + persona simulation | Behavioral analysis | Future |

**Key decision:** CLI-only analysis was dropped because VS Code extensions require a running Extension Host process to activate, which needs a full VS Code GUI instance. Xvfb provides this with zero overhead compared to a real display.

---

## Activation Event Support Matrix

All activation events are supported via Xvfb + full VS Code GUI:

| Activation Event | Supported | Trigger Method |
|------------------|-----------|----------------|
| `*` | Yes | VS Code startup |
| `onStartupFinished` | Yes | VS Code startup |
| `onLanguage:*` | Yes | Open file with matching language |
| `onCommand:*` | Yes | Command palette or xdotool |
| `workspaceContains:*` | Yes | Open folder with matching files |
| `onFileSystem:*` | Yes | FileSystem provider |
| `onView:*` | Yes | Sidebar navigation via xdotool |
| `onWebviewPanel:*` | Yes | WebView panel open |
| `onCustomEditor:*` | Yes | Custom editor open |
| `onUri` | Yes | URI handler |

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
- [x] Resource limits: 2GB RAM, 2 CPUs
- [x] `cap_add: NET_RAW, SYS_PTRACE` for monitoring tools
- [x] `setcap` on tcpdump/dumpcap for non-root capture
- [x] Makefile targets: `executor-build`, `executor-up`, `executor-down`, `executor-shell`, `executor-test`

### Current container stack:
```
Xvfb :99 (1920x1080x24)  ->  Virtual display
openbox                    ->  Window manager
x11vnc                     ->  VNC server (port 5900)
noVNC                      ->  Browser access (port 6080)
VS Code                    ->  Full GUI instance
```

### Access:
- **noVNC:** `http://localhost:6080/vnc.html` (browser-based VNC)
- **Shell:** `make executor-shell`
- **VS Code launch:** `docker exec -d automation_executor bash -c "code --no-sandbox --disable-gpu /workspace"`

## 1.2 Extension Loading & Activation

### Extension Installer Module
- [ ] Create `executor/extension_manager.py`
- [ ] Implement `install_extension(path: Path) -> bool` using `code --install-extension`
- [ ] Implement `uninstall_extension(extension_id: str) -> bool`
- [ ] Handle installation errors and timeouts

### Activation Trigger Engine
- [ ] Create `executor/triggers.py`
- [ ] Implement trigger strategies based on activation events:
  ```python
  class TriggerStrategy(Protocol):
      def trigger(self, extension: Extension) -> TriggerResult: ...

  class OnLanguageTrigger(TriggerStrategy):
      # Open a file with matching language via xdotool

  class OnCommandTrigger(TriggerStrategy):
      # Execute command via command palette (Ctrl+Shift+P)

  class OnStartupTrigger(TriggerStrategy):
      # VS Code startup automatically triggers

  class OnViewTrigger(TriggerStrategy):
      # Navigate to sidebar view via xdotool
  ```
- [ ] Implement trigger selection based on `activationEvents` from DB
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

### VS Code Window Control
- [ ] Create `executor/gui_executor.py`
- [ ] Implement window focus/maximize with `xdotool`
- [ ] Add startup wait for VS Code ready state

### UI Interaction Engine
- [ ] Create `executor/interactions/`
- [ ] Implement mouse actions: `click(x, y)`, `double_click(x, y)`, `right_click(x, y)`
- [ ] Implement keyboard actions: `type_text(text)`, `press_key(key)`, `hotkey(keys)`
- [ ] Implement navigation:
  - `open_command_palette()` (Ctrl+Shift+P)
  - `open_sidebar(name)` (View shortcuts)
  - `open_extension_view()`

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

1. **Single Stack**: Xvfb covers all extension types (no CLI/GUI split)
2. **Full Activation**: Every activation event can be triggered
3. **Audit Everything**: Every action produces evidence
4. **Fail Safe**: Sandbox isolation, resource limits, timeouts
5. **Determinism for Speed**: Fast baseline analysis
6. **Randomness for Evasion**: AI mode for sophisticated malware

---

## Success Criteria

### Phase 1 Complete When:
- [ ] Can install/uninstall extensions via CLI inside Xvfb container
- [ ] Can trigger all activation events (VS Code GUI running on Xvfb)
- [ ] Network/process/filesystem monitoring works
- [ ] Results stored in database
- [ ] Basic risk scoring functional
- [ ] API endpoints working
- [ ] noVNC access verified for debugging

### Phase 2 Complete When:
- [ ] Automated xdotool/Puppeteer interaction working
- [ ] Persona-based simulation working
- [ ] Screenshot/recording capture working
- [ ] Anti-detection measures in place
- [ ] Full coverage of extension behaviors
