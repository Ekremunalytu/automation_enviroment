# TODO: Ideas & Recommendations for AI-Driven User Interaction Automation

This document lists actionable ideas, architectural tasks, and research-oriented
recommendations for building a **hybrid user interaction system** that combines
deterministic automation with AI-driven non-deterministic human simulation.

The goal is to:
- Reduce determinism
- Improve realism
- Trigger interaction-gated malicious behaviors
- Collect higher-quality behavioral evidence

---

## 1. Core Architecture Tasks

### ⬜ Define Dual Execution Modes
- [ ] Implement **Deterministic Baseline Mode**
  - Stable, selector-based Playwright scripts
  - Fast execution
  - Used for initial data extraction
- [ ] Implement **AI-Driven Human Simulation Mode**
  - Triggered only when baseline is insufficient or suspicious signals appear
  - Uses goal-oriented interaction instead of fixed steps

### ⬜ Decision Engine (Mode Switch)
- [ ] Define risk thresholds to activate AI mode
  - Obfuscated JS detected
  - No network activity until user interaction
  - Suspicious permissions / APIs
  - New or low-reputation publisher
- [ ] Log why AI mode was triggered (important for explainability)

---

## 2. AI Human Simulation Design

### ⬜ Interaction Policy (Hard Constraints)
- [ ] Allowed actions:
  - Click
  - Scroll
  - Type (dummy input only)
  - Hover
  - Wait
  - Open / close tab
  - Back / forward navigation
- [ ] Forbidden actions:
  - Real credential input
  - Payments / subscriptions
  - File downloads / execution
  - External OS interaction
- [ ] Enforce max limits:
  - Max actions per run
  - Max duration
  - Max opened tabs

### ⬜ Domain Safety Rules
- [ ] Domain allowlist (marketplace, official links)
- [ ] Unknown domains:
  - Flag + observe
  - Optional HEAD request only
- [ ] Track cross-domain navigation chains

---

## 3. Persona-Based Non-Determinism

### ⬜ Define User Personas
- [ ] **Curious User**
  - Explores multiple links
  - Scrolls deeply
  - Opens About / Docs / Privacy pages
- [ ] **Cautious User**
  - Looks for permissions
  - Reads privacy policy
  - Closes popups quickly
- [ ] **Impatient User**
  - Fast scrolling
  - Clicks first visible CTA
  - Leaves quickly
- [ ] **Normal User**
  - Balanced navigation
  - Minimal but realistic interaction

### ⬜ Randomized Execution
- [ ] Generate a seed per run
- [ ] Randomize:
  - Scroll depth
  - Wait times
  - Navigation order
- [ ] Ensure reproducibility by logging the seed

---

## 4. Anti-Analysis & Malware Evasion Detection

### ⬜ Interaction-Gated Behavior Checks
- [ ] Compare network activity:
  - Before interaction
  - After first scroll
  - After first click
- [ ] Detect delayed execution patterns

### ⬜ Time-Based Triggers
- [ ] Idle waiting (30–120s)
- [ ] Observe late network or DOM changes

### ⬜ Focus & Visibility Signals
- [ ] Switch tabs
- [ ] Minimize browser
- [ ] Return after inactivity
- [ ] Detect behavior changes

### ⬜ Fingerprinting Detection
- [ ] Canvas / WebGL access
- [ ] AudioContext probing
- [ ] navigator.*, timezone, language checks
- [ ] Headless / automation detection attempts

---

## 5. Evidence Collection & Telemetry

### ⬜ Interaction Timeline
- [ ] Log every action with timestamp
- [ ] Map actions → consequences
  - Action → Network request
  - Action → DOM mutation
  - Action → Script execution

### ⬜ Network Intelligence
- [ ] Capture:
  - Request type (XHR, fetch, WS, script, image)
  - Initiator
  - Timing
- [ ] Build domain relationship graphs

### ⬜ Behavior Graphs
- [ ] Interaction Graph:
  - Node: user action
  - Edge: resulting behavior
- [ ] Domain Graph:
  - Node: domain
  - Edge: request type / frequency

---

## 6. Output & Reporting

### ⬜ Structured Output Schema (JSON)
- [ ] actions[]
- [ ] observations[]
- [ ] network_events[]
- [ ] risk_signals[]
- [ ] graph_edges[]

### ⬜ Explainability Layer
- [ ] “Why this extension is suspicious” summary
- [ ] Evidence-backed reasoning
- [ ] Highlight interaction-gated findings

---

## 7. UI & Visualization Ideas

### ⬜ Timeline View
- [ ] Scrollable time-based interaction view
- [ ] Hover to see evidence (requests, scripts)

### ⬜ Graph View
- [ ] Domain graph (network behavior)
- [ ] Action → consequence graph

### ⬜ Mode Comparison
- [ ] Baseline vs AI mode differences
- [ ] Highlight behaviors that only appear with human simulation

---

## 8. Advanced / Future Ideas

### ⬜ Multi-Run Behavioral Variance
- [ ] Run AI mode multiple times with different personas
- [ ] Compare behavior deltas
- [ ] Score variance (low variance = likely benign)

### ⬜ Deception Detection
- [ ] Detect behavior that only triggers after:
  - Specific navigation paths
  - Specific delays
- [ ] Flag “conditional malicious logic”

### ⬜ Research-Grade Sandbox Mode
- [ ] Disable screenshots (reduce fingerprinting)
- [ ] Rotate browser fingerprints
- [ ] Warm vs cold browser profiles

---

## 9. Design Philosophy (Guiding Principles)

- Determinism is good for speed, bad for realism
- Non-determinism is expensive, but high-value
- AI is not a replacement for scripts — it is a **recovery & exploration layer**
- Every AI action must produce **auditable evidence**
- Human simulation is a detection technique, not just UX automation

---

## 10. Final Recommendation

Use AI-driven user interaction **selectively**:
- Not for every target
- Only where realism uncovers hidden behavior

This turns automation into **behavioral probing**, not just navigation.
