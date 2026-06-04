# securezeron Detection Spec — VS Code Reverse-Shell PoC

> Sibling of [`apollyon-detection-spec.md`](apollyon-detection-spec.md). The
> apollyon spec reasons about an infostealer's exfil channel (signals S1–S6); this
> one reasons about a **reverse shell** (signals RS1–RS4). Both map onto ExTrace's
> real rule layers via [`architecture-reconciliation.md`](architecture-reconciliation.md).
>
> ⛔ **Safety:** no real `securezeron` sample is ever downloaded into this repo or
> onto the host. Repo fixtures are synthetic declawed canaries; live-sample
> validation is sandbox-only. The C2 / shell literals below are reference IOCs —
> text in a doc, never a fetch or execute instruction. Full policy: the
> [README](README.md) safety section.

## 0. Provenance (read-only, attribution only)

| Field | Value |
|---|---|
| Upstream | `trailofbits/vsix-zoo` → `samples/securezeron/Files/` |
| Publisher (manifest) | `Zeron-CySec` / `securezeron` |
| Family | Reverse-Shell |
| VSIX-relevant | `extension.js` (logic), `package.json` (manifest) |
| Shape | single file, no obfuscation; `activationEvents: ["*"]`; platform-selected shell → `child_process.exec` → `net.Socket` → bidirectional stdio pipe |

Content hashes are PoC-specific and drift on fork/EOL — **behaviour (RS1–RS4), not
content hash, is the durable signal.**

## 1. How it works (detection-level)

On launch the manifest's `["*"]` activation runs the extension with no user
intent. `activate()` picks a shell by platform (`win32 → cmd.exe`, else `sh`),
spawns it with `child_process.exec`, opens a `net.Socket` to a hardcoded `IP:port`,
and **pipes the shell's stdio to the socket in both directions** (`socket →
shell.stdin`, `shell.stdout/stderr → socket`). The attacker types into the socket,
the bytes run on the victim's shell, output streams back — an interactive reverse
shell at startup.

The critical loop is `socket → shell → socket`. That **bidirectional** wiring is a
different capability class from apollyon's one-way `content → network` exfil.

## 2. Signal catalog (RS1–RS4)

| # | Signal | Evidence | Base sev | FP risk | Note |
|---|---|---|---|---|---|
| **RS1** | shell stdio ↔ socket **bidirectional pipe** | `socket.pipe(proc.stdin)` + `proc.stdout/stderr.pipe(socket)` | CRITICAL | very low | self-sufficient — the reverse-shell signature |
| **RS2** | `child_process` spawn of a **shell** binary | `exec("cmd.exe"/"sh")` | HIGH | medium | + network sink → CRITICAL |
| **RS3** | socket connect to a **hardcoded IPv4** (no DNS) | `connect(port, "<ipv4>")` | MEDIUM‑HIGH | medium | + shell spawn → HIGH |
| **RS4** | `activationEvents: ["*"]` eager auto-activate | manifest | INFO → escalate | high | benign alone; amplifier for the rest |

**Why RS1 is the load-bearing signal:** `exec` alone is benign (extensions shell
out to git / build / language servers); a socket alone is benign (telemetry,
update checks). The malicious thing is the **conjunction** — a shell process's
stdio bridged to a network socket. Build on the conjunction and the false-positive
rate collapses. RS4 is an **escalation multiplier**, not a standalone "bad" rule.

## 3. As-built: signal → layer → rule → status

ExTrace has three rule layers (reconciliation §1). The reverse shell lands across
all three:

| Signal | Layer | Rule id | Status |
|---|---|---|---|
| RS1 (RS2/RS3 as conjuncts) | in-house static | [`extrace.s10.reverse_shell`](../../static_runtime/rules/s10_reverse_shell.py) | ✅ shipped — **CRITICAL → BLOCK** |
| RS1 pipe topology (AST echo) | semgrep | `reverse_shell_pipe` | ✅ shipped (advisory MEDIUM/WARN) |
| RS2 shell-name spawn (echo) | semgrep | `reverse_shell_spawn` | ✅ shipped (advisory) |
| RS3 raw-IP connect (echo) | semgrep | `reverse_shell_ip_connect` | ✅ shipped (advisory) |
| RS4 `*` activation | in-house static | [`extrace.s1.activation_wildcard`](../../static_runtime/rules/s1_manifest_red_flags.py) | ✅ pre-existing (HIGH / WARN) |
| runtime: shell spawn + outbound socket | dynamic | [`extrace.a8.reverse_shell`](../../packages/analysis_engine/rules/a8_reverse_shell.py) | ✅ shipped (HIGH, `AdversaryClass.A8`) |

The in-house **`s10` is the conviction**: it requires shell-spawn ∧ shell-name ∧
socket ∧ stdio↔socket pipe **in one file** (RS1's co-occurrence, which also folds
in RS2/RS3), so the individually benign parts never fire alone. It is the only
severity-CRITICAL in-house static rule, so it **blocks before the sandbox** (ADR
0016: CRITICAL → `rejected_static`). The semgrep rules are AST-precise but
advisory (the runner hard-pins MEDIUM/WARN); they add a second line of evidence.
`a8` is the runtime confirmation: the sandbox sees the shell spawn and the egress
but not the wiring between them, so it is HIGH/MEDIUM-confidence, not CRITICAL.

## 4. Severity / gate (reconciliation §2)

`s10` = **CRITICAL → BLOCK**: a shell piped to a socket has no benign explanation,
so it is rejected at the static gate before any sandbox run — the first in-house
rule to do so (every other static signal warns and lets the sandbox proceed). `a8`
is a post-sandbox dynamic detection (dynamic rules never gate); it reports for
review. RS4 (`s1.activation_wildcard`) stays HIGH/WARN.

## 5. Evasion — what holds, what slips

- **Caught (commodity / this PoC):** plaintext IP (RS3), explicit shell name (RS2),
  flat pipe topology (RS1), `*` activation (RS4).
- **Slips the IOC layer, RS1 still holds:** domain/DGA C2 (RS3 dies), `tls.connect`
  (covered — `s10`/semgrep socket conjunct includes `tls`), shell-name hidden via
  `env.ComSpec` / charcodes (RS2 weakens) — **but the stdio↔socket pipe topology
  (RS1) is structural and still matches.**
- **Slips static entirely:** `eval`/`Function`/computed `child_process[fn]` indirect
  spawn — the structural pattern disappears; the **dynamic plane** (`a8`: observed
  shell spawn + outbound socket) is the backstop.
- **Shifts the signature:** **staging.** A loader variant carries no reverse shell —
  it fetches and executes a stage at runtime. Then the signal is not RS1 but a
  `network fetch → child_process exec of fetched content` dropper pattern (a
  separate rule family, not built here).

APT-grade (encrypted + domain-C2 + staged + indirect-spawn) is not reliably caught
by the static layer; the dynamic plane + outbound-baselining is required.

## 6. IOC / signal appendix (regression anchors — behaviour first)

```text
# PoC-specific strings (drift on fork — DO NOT use as primary IOC)
c2_target        : 192.168.0.149:9098   # RFC1918 lab IP; note: s5 only flags GLOBAL IPs,
                                         # so s10's connect-literal conjunct (not s5) carries this
activation_event : "*"
shell_win/unix   : cmd.exe / sh

# Durable behavioural signals (primary)
RS1  : socket.pipe(proc.stdin) + proc.stdout/stderr.pipe(socket)   # bidirectional
RS2  : exec/spawn/execFile + (cmd.exe|powershell|sh|bash|ComSpec|SHELL)
RS3  : .connect(PORT,"<ipv4>") | net.connect/createConnection({host,port})
RS4  : activationEvents ⊇ {"*"}

# Test literals (synthetic only — RFC 5737 ranges, never the real C2)
unit/canary C2   : 203.0.113.10:4444
```

Synthetic test inputs live in
[`tests/static_runtime/test_s10_reverse_shell.py`](../../tests/static_runtime/test_s10_reverse_shell.py),
[`tests/security/rules/test_a8_reverse_shell.py`](../../tests/security/rules/test_a8_reverse_shell.py),
and the canary
[`t1-a8-reverse-shell-canary`](../../extensions/malicious/t1-a8-reverse-shell-canary/) —
never in rule logic (rules are general-purpose scanners, not securezeron signatures).
