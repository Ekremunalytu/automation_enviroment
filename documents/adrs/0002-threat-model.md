# ADR 0002: Threat Model

- Status: Accepted
- Date: 2026-04-17
- Related: ADR 0001 (Single-Host Appliance), ADR 0003 (Detection Taxonomy), ADR 0004 (Malicious Fixture Policy)

## Context

ExTrace is transitioning from a platform-maturity phase into a detection
capability phase. Until now every planning document has treated security as
an implicit outcome of structural cleanup. That is no longer sufficient: the
next weeks will introduce detection rules, and any rule written without an
explicit threat model is a rule that cannot be validated, reviewed, or
retired rationally.

This ADR makes the threat model explicit before any detection work begins.
It is intentionally narrow — scoping decisions are preferred over
aspirational coverage.

## Decision

### 1. In-Scope Adversary Classes

The following classes are **explicitly in scope**. The detection program is
measured against them.

**PoC priority note (2026-04-17):** The 7-week window targets a
proof-of-concept acceptance bar. Classes marked `PoC` below are the
acceptance minimum; classes marked `Stretch` remain in scope but are not
required for PoC sign-off. No class is removed from scope — a PoC that
surfaces `Stretch` findings is better than one that does not, but is not
blocked by their absence.

| Class | Priority | Description | Example behavior |
|---|---|---|---|
| A1. Opportunistic credential stealer | **PoC** | Obfuscated JS payload that reads SSH keys, dotfiles, cloud credential files, and exfiltrates over HTTPS on activation | `~/.ssh/id_rsa` read on first activation + POST to attacker-controlled host |
| A2. Post-install cryptominer | **PoC** | Spawns a mining process or loads WASM miner after activation | `child_process.spawn("xmrig", ...)` or inline CPU-bound worker |
| A3. Typosquat / impersonation | Stretch | Package name similar to a popular extension; identical UI to mask identity | `"ms-pyhton.python"` vs `"ms-python.python"` |
| A4. Remote-loader dropper | **PoC** | Extension downloads the real payload at runtime, bypassing static analysis of the marketplace artifact | `eval(await fetch(c2).then(r=>r.text()))` |
| A5. Malicious update | Stretch | Benign initial version passes review, later version introduces the payload | v1.0 clean, v1.1 adds stealer logic |
| A6. Package.json script abuse | **PoC** | Uses `scripts.postinstall` / lifecycle hooks to execute code outside the VS Code API sandbox | Arbitrary shell command during install |
| A7. VS Code API abuse | Stretch | Legitimate API usage combined in a malicious pattern — e.g. `workspace.fs` to read source code + `net` to exfiltrate | Parsing all `.env` files in the workspace then POSTing them |

**PoC acceptance bar:** at least one T1 fixture per PoC class (A1, A2,
A4, A6) fires its corresponding rule with `confidence ≥ medium` and
severity ≥ `high` (ADR 0003). Stretch classes remain buildable; a rule
authored for a Stretch class is accepted into production if it meets
the same bar as a PoC rule.

### 2. Assumed Adversary Capabilities

The detection program **must be robust against** the following capabilities:

- **Basic obfuscation:** minification, identifier mangling, string splitting,
  Base64-encoded constants.
- **Dynamic code loading:** `eval`, `new Function`, `vm.runInContext`,
  `require` of remote URIs or non-standard paths, WASM loading from remote.
- **Activation-gated behavior:** payload only fires on specific activation
  events (e.g. `onCommand:X`, `onLanguage:python`, chat participant trigger).
- **Trivial timing evasion:** simple "sleep before payload" patterns below
  the analysis timeout.
- **Environment sniffing (basic):** `process.env` checks for common CI markers
  (`CI`, `GITHUB_ACTIONS`).

### 3. Explicitly Out-of-Scope Capabilities

The detection program **is not expected to defeat** the following during
this phase. If encountered, the correct response is `inconclusive`, not a
false-negative-claiming `clean`.

- **Advanced sandbox evasion:** Playwright CDP fingerprinting, detection of
  harness extension presence, detection of the analyzer via `navigator.webdriver`
  or equivalent.
- **Nation-state / APT-grade multi-stage tradecraft:** long-dormant payloads,
  C2 over steganographic channels, kernel-level persistence.
- **Zero-day VS Code or Electron RCE:** exploitation of unpatched platform
  vulnerabilities to escape the sandbox or to subvert analysis integrity.
- **Post-compromise supply chain attacks on ExTrace itself:** attacker has
  already compromised our build pipeline, signing keys, or dependencies.
- **Denial-of-service of the analyzer:** resource exhaustion, crash loops,
  runtime hijack of the monitor. These are operational concerns tracked
  separately.

Out-of-scope classes can be moved in-scope via a follow-up ADR; they do not
become in-scope implicitly.

### 4. Trust Boundaries

The analyzer makes the following trust decisions. Each boundary is stated
with its validation mechanism.

| Entity | Trust level | Validation |
|---|---|---|
| VS Code binary | Trusted if pinned | Pinned version + SHA in `Dockerfile`; unpinned `stable` channel is **not acceptable** under this ADR |
| Playwright runtime | Trusted if pinned | Pinned via `pyproject.toml` lock; CI verifies integrity |
| Harness extension | Trusted if checksummed | SHA256 computed at build, verified in `start.sh` before load (7.2.6) |
| Docker base image | Trusted if SHA-pinned | `FROM image@sha256:...` required |
| Marketplace response (`.vsix`) | Untrusted | Only the declared metadata is trusted; archive contents are subject to analysis |
| Extension code at runtime | **Untrusted** | This is the subject of analysis; never elevated to trusted by any heuristic |
| Analysis output (`activation_report_*.json`) | **Semi-trusted** | May contain captured data originating from an untrusted extension; rendering in UI requires encoding/escaping; retention policy applies |
| Executor container filesystem at rest | Untrusted after first analysis run | Must be reset (not reused) between analyses of different extensions |

### 5. Analyst Operating Environment

The threat model assumes a single-operator environment where the operator
is the security analyst, not the extension publisher. The operator:

- runs the platform on an isolated workstation or dedicated server
- does not expect confidentiality guarantees against themselves
- is responsible for not propagating malicious fixtures outside the
  analyzer (enforced by ADR 0004)

Multi-tenant operation is out of scope (ADR 0001).

### 6. Analysis Output as a Secondary Exfiltration Surface

Because the analyzer captures network payloads, file reads, and process
output, the resulting report may contain data originally stolen by the
extension (e.g. fragments of SSH keys present in an exfiltration POST body).
Output handling therefore inherits a tainted status:

- No automatic forwarding to external log aggregation without scrubbing.
- UI rendering must treat string fields as untrusted (no `dangerouslySetInnerHTML`).
- Retention is bounded and operator-configurable; default is purge after
  verdict is recorded.

## Consequences

### Positive

- Detection rules can be reviewed against "does this class address A1-A7?"
- `inconclusive` becomes a legitimate, first-class verdict rather than a
  failure mode.
- Dependency on VS Code version pinning and harness checksums acquires an
  explicit security justification (not just "reproducibility").

### Negative

- Scope is narrower than an ambitious marketing claim would allow. The tool
  is not a universal malicious-extension detector; it targets a specific
  class of threats.
- Advanced evasion becomes a known gap. Operators must be aware of it.

### Follow-On

- ADR 0003 defines the detection taxonomy aligned with classes A1-A7.
- ADR 0004 defines the malicious fixture policy validating coverage of
  classes A1-A7.
- Re-evaluate this ADR after the first production detection release. If
  advanced evasion becomes a recurring blocker, promote it via a new ADR
  rather than silently expanding scope.
