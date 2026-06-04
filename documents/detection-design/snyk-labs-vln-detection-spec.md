# snyk-labs VLN Detection Spec — Vulnerable-Legit-Extension class (path traversal)

> Fifth in the custom-rule series after apollyon, securezeron, kagema, and
> GlassWorm — but on a **new, orthogonal axis**. The earlier specs ask "is this
> extension *malicious*?"; this one asks "does this *legitimate* extension ship an
> *exploitable insecure pattern*?". The design driver is the 2021 Snyk-labs
> Instant Markdown class and its recurring descendants. No real VSIX, exploit
> page, or receiver is downloaded, stored, or executed in this repository.

## 0. Safety And Scope

This design is driven by a prior text-only rule-development handoff (the
snyk-labs README's claim + public Snyk/Kirill89/THN reporting), **not** by
vendoring a live sample. Nothing was fetched, opened, or executed; the vulnerable
extension's source was never opened.

The full exploit chain has three parts; ExTrace sees only the first:

| Part | Where | ExTrace scope |
|---|---|---|
| **(1) Vulnerable pattern** — guard-less local file-serving server | extension source | ✅ in-scope (this spec) |
| (2) Malicious content — hidden iframe / XSS payload | attacker web page | ⛔ content-borne, extension-external |
| (3) Exfil infra — receiver endpoint | attacker server | ⛔ infrastructure, extension-external |

The attacker exploit server (the snyk-labs directory's `index.php` landing /
`track.php` receiver) and the malicious markdown content are **out of scope and
are not reproduced** anywhere in this repo. The detection target is the
*upstream extension source pattern* — the only artifact the static layer scans.

Version anchor: Instant Markdown `1.4.6` vulnerable, `1.4.7` fixed (Snyk advisory,
2021). No Instant-Markdown-specific public CVE ID was confirmed — cite the Snyk
advisory, not a CVE.

## 1. How It Works (detection level)

Two root causes, both in the *extension* code:

1. **Path traversal.** The extension stands up a local static HTTP server to live-
   preview markdown and maps the request path onto a filesystem path with no
   guard: `/foo/?/../../../../home/<user>/.ssh/id_rsa` escapes the intended root
   and returns an arbitrary file. Correct defense = a hardened static lib
   (`send` / `serve-static`) **or** `path.resolve` + a `startsWith(root)`
   containment check. The vulnerable version has neither.
2. **Reachable origin.** The local server is cross-origin reachable (permissive
   CORS / no origin check), so a malicious page the developer opens in a browser
   can reach `localhost` and trigger the traversal. The webview variant of the
   same class is a CSP-less scripted webview rendering untrusted markdown→HTML.

The conjunction of (1) and (2) is a finished **arbitrary-local-file-read
primitive** that lives entirely in the extension — the exploit's content half is
not needed to convict the *vulnerability*.

## 2. Signal Catalog — `VLN` family (design vocabulary)

`VLN` is a design-side vocabulary on a separate **vulnerability** axis; it does
**not** extend the A1–A8 malice taxonomy. Mapped onto ExTrace's real layers in §3.

| ID | Signal | Static evidence | FP risk |
|---|---|---|---|
| VLN1 | Local HTTP server | `http.createServer` / `.listen(port)` / `express()` / `connect()` | **very high alone** |
| VLN2 | Request-path → fs read, **no traversal guard** | `req.url`/`req.params` → `fs.readFile`/`sendFile`, no `resolve`+`startsWith` | medium |
| VLN3 | Untrusted render, **no CSP** | `webview.html = …` + no CSP meta / `enableScripts:true` | medium |
| VLN4 | Permissive CORS | `Access-Control-Allow-Origin: "*"` | medium |
| VLN5 | **Conjunction** (the real signal) | VLN1 × VLN2 × (VLN3 ∨ VLN4), guard absent | **low** |
| VLN-D | Dependency smell | custom server, no `send`/`serve-static` dep | weight, not a signal |

**FP semantics (the whole game):** VLN1 alone is a massive false-positive — Live
Preview, dev-server, LSP-over-http, dozens of legitimate extensions stand up a
local server. The signal strength is in **guard absence** (VLN2) and the
**conjunction** (VLN5). A rule must never key on VLN1.

## 3. As-built layer map (real ExTrace rules)

The spec's placeholder `extrace-rules/vln/*.yml` paths do **not** exist; the VLN
signals land on ExTrace's three real layers (architecture-reconciliation.md §1).

| Signal | Layer | Rule id | Status |
|---|---|---|---|
| VLN5 conjunction (folds VLN1∧VLN2∧(VLN3∨VLN4), guard-absent) | in-house static | `extrace.s15.path_traversal_server` | ✅ shipped — **MEDIUM / WARN** |
| VLN4 permissive-CORS surface (cleartext echo) | semgrep | `permissive_cors` → `extrace.sg.permissive_cors` | ✅ shipped — advisory MEDIUM/WARN |
| VLN2 request-path → fs-read **taint** (true dataflow) | semgrep (taint) | *tbd* | ⬜ container-iteration follow-up (§7) |
| VLN3 CSP-absence in a `$HTML` variable (string layer) | in-house static | *tbd* | ⬜ deferred (known `pattern-not-regex` limit) |

`s15` is the heart. It keys on the **conjunction, never the parts**: one source
file where (VLN1) a local HTTP server, (VLN2) a request-derived path flowing into
an `fs` read sink with **no containment guard**, and (reachable origin) permissive
CORS (VLN4) **or** a CSP-less scripted webview (VLN3) all co-occur. Each part
alone stays silent.

**It approximates the spec's taint by file-level co-occurrence + guard-absence,
not true dataflow** — the honest static limit (§7). The guard detection is
deliberately **conservative**: any plausible containment (`path.resolve`/
`normalize` near a `startsWith`, or a hardened static lib) makes the rule go
silent even at the cost of a false negative, because flagging a *correctly-guarded*
server is the one false positive that destroys user trust.

### Severity / axis reconciliation (important)

`s15` is **MEDIUM / WARN, never CRITICAL / BLOCK** — unlike the malice rules `s10`
(reverse shell) and `s11` (download cradle) which BLOCK. A *vulnerable-but-benign*
extension must surface for review, not be rejected before the sandbox; rejecting a
legitimate extension over a bug is a trust-destroying false positive. It stays
`adversary_class=None` (the static-IOC convention — and adversary attribution is
the *wrong axis* for a vulnerability). On the confidentiality axis the impact is
high (arbitrary local file read → SSH-key / credential disclosure), but until the
orthogonal `VULNERABLE` verdict axis exists (§6) the finding rides the existing
**malice-severity** field; MEDIUM/WARN is the deliberate, conservative stopgap so
a vulnerability is never mistaken for a malice conviction and can never silently
become a gate blocker.

## 4. Detection Invariant — VLN5

One part benign; all three together deterministically exploitable:

```text
VLN1 local HTTP server  ─┐
VLN2 request-path → fs read, guard ABSENT  ─┼─►  arbitrary local file read + exfil
reachable origin (VLN4 CORS ∨ VLN3 webview-no-CSP)  ─┘   (HIGH-fidelity / VULNERABLE)

any single part alone  ─►  benign static server / dev-server (no verdict)
```

High-fidelity because a guarded server (VLN2 negative) is already clean; a
guard-absent + reachable-origin server is exploitable without ever observing the
exploit's *content* side — the primitive is in the extension itself.

## 5. False Positive Strategy

The dominant risk is legitimate local-server extensions. Mitigation is the VLN5
conjunction + conservative guard modeling:

- A server using `send` / `serve-static` → guarded → silent.
- A server doing `path.resolve(root, p)` + `resolved.startsWith(root)` → silent.
- A server with no request-path-driven `fs` read → silent.
- A server with no reachable origin (no permissive CORS, no scripted webview) →
  silent.

Verified by synthetic fixtures in `tests/static_runtime/test_s15_path_traversal_server.py`:
two positive shapes (CORS variant, webview-no-CSP variant) fire; the guarded
variant, the hardened-lib variant, server-without-fs-read, unguarded-without-
reachable-origin, and fs-read-without-server all stay silent.

## 6. The `VULNERABLE` verdict axis — DEFERRED, needs owner sign-off

The spec's headline proposal is a **second, orthogonal verdict axis**:

```text
Axis A — MALICIOUSNESS: is the author hostile?
Axis B — VULNERABILITY: does the extension ship an exploitable insecure pattern?
  benign + vulnerable  → Instant Markdown (this class)
  hostile + clean-code → obfuscated/native implant (GlassWorm)
```

Reporting both axes separately (e.g. `MALICIOUSNESS: none` + `VULNERABILITY:
high`) is the correct end state — "not malicious → clean" is the error this axis
prevents. **But adding a verdict axis is a shared-contract change** (report
dataclass + Pydantic contract + `schema_version` bump + generated TS DTO, plus a
new `V`-taxonomy node distinct from `AdversaryClass` A1–A8). Per repo precedent
(the A8 enum addition was signed off before the edit) and the standing rule on
shared-contract / gate-policy changes, **this axis is held for explicit owner
sign-off** and is recorded on the pre-close checklist (§8). The `V`-taxonomy ID
mapping must be verified against the real taxonomy definition before any ID is
assigned — do not invent one. Until then, `s15` rides the malice-severity field at
MEDIUM/WARN (§3 reconciliation).

## 7. Evasion / Limitations (honest bounds)

**Catches:** custom static server with no traversal guard + reachable origin;
CSP-less scripted webview render; permissive CORS on a local server.

**Misses (documented):**

1. **Hardened lib + logic flaw** — code using `send`/`serve-static` but passing
   the wrong root; the pattern looks clean, static cannot see it. (Conservative
   guard modeling makes this a deliberate FN to protect the FP rate.)
2. **Config / runtime-gated server** — a server stood up only under a specific
   setting/command; the AST co-occurrence may not assemble → dynamic layer
   territory (the VLN analogue of kagema/GlassWorm's platform-gate blind spot).
3. **True dataflow** — `s15` approximates taint by file-level co-occurrence; a
   real semgrep **taint** rule (source = request path, sink = fs read, sanitizer =
   containment guard) is the higher-fidelity VLN2 and is a container-iteration
   follow-up (no local semgrep on this machine to verify it).
4. **Content + infra** — the malicious page and the receiver are extension-
   external and out of scope; not a gap, a scope boundary (§0).

**Recurring-class value (the thesis point):** this is not a one-off 2021 bug. The
VLN5 invariant recurs across years — the 2021 Snyk wave (Instant Markdown, Open in
Default Browser) and a 2026 wave (Live Server `CVE-2025-65717` local-file exfil;
Markdown Preview Enhanced `CVE-2025-65716` arbitrary JS + port enum + exfil). The
VLN axis covers a **5-year recurring class**, not a single sample — those other
samples are an ideal out-of-the-box regression set for the `s15` rule.

## 8. IOC / Signal Appendix — structural, no network IOCs

This is a **vulnerability-pattern class**, so it has **no classic network IOCs**
(no C2 domain, no payload hash) — by design (the malicious content + receiver are
extension-external and not reproduced). **No domains were fabricated**; the
durable signals are structural/behavioral:

| Signal | Type | Durability |
|---|---|---|
| `http.createServer` / `.listen($port)` | structural | high |
| request-path → `fs.readFile`/`sendFile` (co-occurrence/taint) | dataflow | high |
| containment-guard **absence** (`resolve`+`startsWith` / hardened lib) | structural-absence | high (the invariant) |
| `webview.html` set + CSP **absence** | structural-absence | medium |
| `Access-Control-Allow-Origin: "*"` | string/header | medium |
| hardened static lib absence (`send`/`serve-static`) | dependency | medium (prior) |
| port literal `8090` (Instant Markdown default) | string | **low** — config/version-bound, not durable |

Defanged related-sample references (reference-only text — do **not** fetch,
resolve, or make clickable):

```text
Snyk advisory: Instant Markdown 1.4.6 vulnerable, 1.4.7 fixed (2021)
CVE-2025-65717  — Live Server (local-file exfil), recurring VLN class
CVE-2025-65716  — Markdown Preview Enhanced (arbitrary JS + port enum + exfil)
```

**Blocklist integration (safe):** the curated `blacklist_domains.txt` carries a
documented, **host-less** section for this class explaining *why* it contributes
no entries (structural class, not C2-driven) — so the integration point is
recorded without fabricating or fetching any host. If a future sample (analyzed
**in the sandbox**, never on the host) yields a concrete receiver host, that
single host can be added there for the s4/a7 matcher.

---

**Notes for the next session:**

- (a) This spec is **not** source-verified — built on public reporting + the prior
  text handoff. The rule was concretized fixture-first (synthetic repros), per the
  iteration loop.
- (b) The VLN axis is open: Live Server / Markdown Preview Enhanced / Open in
  Default Browser exercise `s15` out-of-the-box and are the natural regression set.
- (c) Open sign-off items in §6 (the `VULNERABLE` verdict axis) + §7 (semgrep
  taint VLN2). See the pre-close checklist below.

### Pre-close checklist (gating, none auto-applied)

- [ ] **Owner sign-off** on the `VULNERABLE` verdict axis (§6) — shared-contract +
  new `V`-taxonomy node. Not started; held for approval.
- [ ] **Container-iteration** of the semgrep taint VLN2 rule (§7.3) — needs the
  `automation_static_analyzer` container (no local semgrep).
- [ ] Decide whether `s15` warrants a UI `ruleCatalog.ts` entry (enrichment;
  surfaces the rule in the Rules tab) — non-blocking.
