# Detection Design — custom rule development

`Branch: security-development` · `Started: 2026-06-03`

Working area for **custom detection-rule development**: per-malware-class design
specs, the map from those specs to ExTrace's real rule layers, and a living
status board. This is an **iterative** effort — the owner writes tests and feeds
back; rules and these docs grow per cycle. This directory is intentionally
self-contained and does **not** drive the canonical static-lane docs (those
reconcile on the owner's cadence, post-merge).

---

## ⛔ SAFETY — never bring live malware into this repository

> **Real malicious extension samples are NEVER downloaded, committed, or stored
> anywhere in this repository or on the developer host.** Not in `extensions/`,
> not in `documents/`, not in a scratch dir, not "temporarily".
>
> - **Repo fixtures are SYNTHETIC, declawed canaries only** — hand-authored
>   manifests / `activation_report.json` files that *describe* a behaviour shape
>   (see [`extensions/malicious/`](../../extensions/malicious/), all
>   `kind: internal_canary`). They contain no working payload, no live C2
>   endpoint, no real wallet address, no executable malware.
> - **Live samples are analysed ONLY inside the isolated sandbox** — the
>   `automation_executor` / `automation_static_analyzer` containers
>   (`network_mode: none`, `cap_drop: [ALL]`, disposable). A sample enters the
>   sandbox through the analysis pipeline and is destroyed with the container; it
>   never lands on the host filesystem or in git.
> - **IOC strings in these docs are reference-only** (attribution + regression
>   anchors). A webhook URL or address in the appendix is text in a doc, not a
>   fetched artefact, and must never be resolved, executed, or used to pull the
>   real sample down.
>
> Provenance fields (upstream repo URLs, hashes) exist for *attribution and
> citation*, not as a fetch instruction. If a rule needs validating against a
> real sample, that happens in the sandbox — full stop.

---

## Docs

| Doc | Purpose |
|---|---|
| [`architecture-reconciliation.md`](architecture-reconciliation.md) | **Read first.** The three rule layers, the ADR-0016 gate truth table, the A1–A7 taxonomy, and the exact files/tests to add a rule in each layer. |
| [`apollyon-detection-spec.md`](apollyon-detection-spec.md) | Detection design spec for the `apollyon` Discord-webhook infostealer class: behaviour breakdown, signal catalog, escalation matrix, evasion limits, IOC appendix. |
| [`securezeron-detection-spec.md`](securezeron-detection-spec.md) | Detection design spec for the `securezeron` VS Code **reverse-shell** class: signals RS1–RS4, the as-built layer map (s10 / a8 / semgrep echoes), severity/gate, evasion limits, IOC appendix. |
| [`kagema-detection-spec.md`](kagema-detection-spec.md) | Detection design spec for the `kagema` VS Code **download-cradle dropper** class: signals DR/OB/MN, the as-built layer map (s11 / `sg.download_cradle`), the ordered-shape-not-loose-AND FP reconciliation, the win32-gate dynamic blind spot, A4/A3 attribution, evasion limits, IOC appendix. |
| [`glassworm-detection-spec.md`](glassworm-detection-spec.md) | Detection design spec for the GlassWorm / `icon-theme-materiall` native-loader worm class: invisible Unicode, `.node` loader dispatch, host-context invoke, globalState dormancy, Linux blind spot, and safe IOC handling. |
| [`snyk-labs-vln-detection-spec.md`](snyk-labs-vln-detection-spec.md) | Detection design spec for the **VLN** (vulnerable-legit-extension) class, driven by the 2021 Snyk-labs Instant Markdown path-traversal bug: signals VLN1–VLN5, the as-built layer map (`s15` conjunction / `permissive_cors` semgrep echo), the new **orthogonal `VULNERABLE` axis** (deferred for sign-off), and why the class has **no network IOCs**. |
| [`nf3xn-reverse-shell-spec.md`](nf3xn-reverse-shell-spec.md) | Detection design spec for the `nf3xn` VS Code **reverse-shell** PoC (RS class, `securezeron` sibling): the connect-back / shell-spawn / stdio-bridge invariant, the `s10` **manual `stdin.write` bridge** improvement, the new **`s1.reserved_publisher_spoof`** manifest rule (signal MN), and the Linux-detonation insight (`a8` *fires* for this sample, unlike kagema/glassworm). |
| [`ecm3401-malicious-suite-spec.md`](ecm3401-malicious-suite-spec.md) | Detection design spec for the `ecm3401` "Educational Attack Suite" (MAL / **MALICIOUSNESS** axis, the snyk-labs contrast): 9 techniques across all three trust planes, the three high-fidelity invariants (TAMPER1 / CRED-X / DROP1) and their as-built rules (`s16` CRITICAL crown jewel / `s17` / `s18` + three semgrep echoes), the cross-extension trust-boundary class, and the durable-vs-sample-specific IOC split. |
| [`nextsecurity-stylesheet-spec.md`](nextsecurity-stylesheet-spec.md) | Detection design spec for the `nextsecurity` / vsix-zoo **stylesheet-borne TTP** class (STY — the first CSS/LESS detection surface): the two execution contexts (webview Chromium vs extension-host LESS compile), the honest TTP→impact matrix (~7 dead in Electron, ~9 data-plane beacons, 1 CRITICAL RCE), the `.less`/`.scss`/`.sass` **coverage fix**, the as-built `s19` family (`stylesheet_inline_js` CRITICAL / `stylesheet_nonstandard_scheme` / `stylesheet_css_exfil`), the explicit DoS/taint/CSP-grading gaps, and the all-synthetic IOC handling (no host added to the denylist). |

## Design principle: general, not sample-specific

Rules are **engine-wide scanners**, not apollyon signatures. Every rule here runs
over *every* extension's source/runtime in the normal pipeline and asks a generic
question — "why does **any** extension hardcode a Discord webhook?", "why does
**any** extension carry crypto-address regexes?" — never "is this byte-for-byte
apollyon?". Sample-specific IOCs live only in the spec's regression appendix and
in test inputs; **never** in rule logic. apollyon is the *design driver*, not the
*target*. New rules must keep this property: match a behaviour/capability class,
not a known sample.

## The three layers (one-liner)

- **In-house static** (`static_runtime/rules/s*`) — VSIX-tree rules; can carry any
  severity and can **BLOCK** before the sandbox.
- **Semgrep static** (`static_runtime/semgrep_rules/`) — commodity dataflow rules;
  **hard-pinned MEDIUM/WARN**, never blocks.
- **Dynamic** (`packages/analysis_engine/rules/a*`) — behavioural rules over the
  runtime `ActivationReport`; carry `AdversaryClass` attribution.

## Shipped so far (this branch)

**General** detection rules across the static / semgrep / dynamic layers (+ advisory
Semgrep echoes) + the UI to surface them. None hardcodes a sample literal; all scan
every extension.

| Rule | Layer | What it catches | Severity |
|---|---|---|---|
| [`extrace.s8.exfil_webhook`](../../static_runtime/rules/s8_exfil_webhook.py) | static | Hardcoded Discord/Slack/Telegram **webhook** ingestion endpoint (the exfil channel) | HIGH (warn) |
| [`extrace.s9.crypto_address_scan`](../../static_runtime/rules/s9_crypto_address_scan.py) | static | Source recognises **crypto-address** formats (Base58/ETH/bech32) — clipper capability | MEDIUM (warn) |
| [`extrace.s10.reverse_shell`](../../static_runtime/rules/s10_reverse_shell.py) | static | Shell `child_process` stdio **wired to a network socket** (reverse shell) — `.pipe()` **and** manual `stdin.write` bridge | **CRITICAL (block)** |
| [`extrace.s11.download_cradle`](../../static_runtime/rules/s11_download_cradle.py) | static | `child_process` driving a hidden-PowerShell `irm`→`iex` **download cradle** (dropper) | **CRITICAL (block)** |
| [`extrace.s12.invisible_unicode_run`](../../static_runtime/rules/s12_invisible_unicode.py) | static | Invisible Unicode / PUA source-hiding runs in original packaged bytes | **CRITICAL (block)** for runs |
| [`extrace.s13.native_node_loader`](../../static_runtime/rules/s13_native_node_loader.py) | static | Bundled `.node` load with platform dispatch and host-context invoke | **CRITICAL (block)** for GlassWorm-strength conjunction |
| [`extrace.s14.globalstate_dormancy`](../../static_runtime/rules/s14_globalstate_dormancy.py) | static | `context.globalState` timestamp dormancy / throttle | MEDIUM (warn) |
| [`extrace.s15.path_traversal_server`](../../static_runtime/rules/s15_path_traversal_server.py) | static | Local server maps a request path onto an unguarded `fs` read, reachable cross-origin (path traversal) | MEDIUM (warn) |
| [`extrace.s16.cross_extension_tamper`](../../static_runtime/rules/s16_cross_extension_tamper.py) | static | Write/copy into **another extension's install directory** (foreign `extensionPath` / `.vscode/extensions` path) — persistence / execution hijack | **CRITICAL (block)** |
| [`extrace.s17.credential_exfil`](../../static_runtime/rules/s17_credential_exfil.py) | static | Sensitive **credential file read** + outbound network egress sink in one module | HIGH (warn) |
| [`extrace.s18.download_exec_dropper`](../../static_runtime/rules/s18_download_exec_dropper.py) | static | File made **executable (`chmod +x`) and run** via `child_process` — drop-and-run dropper | HIGH (warn) |
| [`extrace.s1.reserved_publisher_spoof`](../../static_runtime/rules/s1_manifest_red_flags.py) | static | Manifest **claims a reserved first-party publisher** (`ms-vscode`/`github`/…) — impersonation (signal MN) | MEDIUM (warn) |
| [`extrace.s19.stylesheet_inline_js`](../../static_runtime/rules/s19_stylesheet_threats.py) | static | **LESS inline-JavaScript eval** (backtick `` ~`...` ``) in a stylesheet → compile-time RCE in the extension-host Node context | **CRITICAL (block)** |
| [`extrace.s19.stylesheet_nonstandard_scheme`](../../static_runtime/rules/s19_stylesheet_threats.py) | static | Stylesheet resource loader (`@import`/`url()`/`src:`) to a **non-standard scheme** (`ftp`/`ws`/`file`/`javascript`/…) | MEDIUM (warn) |
| [`extrace.s19.stylesheet_css_exfil`](../../static_runtime/rules/s19_stylesheet_threats.py) | static | **CSS-native exfiltration** — substring-attribute keylogger or `::after` content beacon firing a remote `url()` | MEDIUM (warn) |
| [`extrace.a5.workspace_file_tamper`](../../packages/analysis_engine/rules/a5_workspace_file_tamper.py) | dynamic | Workspace file **read then rewritten in place** at runtime — clipper/integrity | MEDIUM |
| [`extrace.a8.reverse_shell`](../../packages/analysis_engine/rules/a8_reverse_shell.py) | dynamic | Runtime **shell spawn + outbound socket** co-occurrence (reverse shell) | HIGH |

UI ([`ruleCatalog.ts`](../../ui/src/features/reports/ruleCatalog.ts) +
[`RulesPage.tsx`](../../ui/src/features/rules/RulesPage.tsx)): the **Rules tab now
lists static *and* dynamic rules** (was dynamic-only), each with a **Static /
Dynamic** badge and a stream filter; every catalog rule carries a richer `detail`
description. Detail in the reconciliation doc §6.

Policy tweak: `extrace.s1.activation_wildcard` raised **LOW → HIGH** (an always-on
`*` foothold is too load-bearing for LOW; warns, never blocks).

## Status board — apollyon class

| Signal | Layer | Rule id | Status |
|---|---|---|---|
| S1 chat-webhook IOC | in-house static | `extrace.s8.exfil_webhook` | ✅ shipped + verified |
| S2 crypto-address awareness | in-house static | `extrace.s9.crypto_address_scan` | ✅ shipped + verified |
| S5 content→network (runtime) | dynamic | `extrace.a4.workspace_exfil` | ✅ exists |
| S6 / B3 crypto clipper (integrity) | dynamic | `extrace.a5.workspace_file_tamper` | ✅ shipped + verified |
| S1 webhook (commodity echo) | semgrep | *tbd* | ⬜ next |
| S4 auto-trigger→sink co-occurrence | in-house static | *tbd (next free `sN`; `s10` is now reverse-shell)* | ⬜ planned |
| S5 content→network (taint) | semgrep | *tbd* | ⬜ planned |

## Status board — securezeron / reverse-shell class

See [`securezeron-detection-spec.md`](securezeron-detection-spec.md). General rules
(no securezeron literal in rule logic); the conjunction insight, not any single part.

| Signal | Layer | Rule id | Status |
|---|---|---|---|
| RS1 shell↔socket pipe (folds RS2/RS3) | in-house static | `extrace.s10.reverse_shell` | ✅ shipped — **CRITICAL → BLOCK** |
| RS1/RS2/RS3 AST echoes | semgrep | `reverse_shell_pipe` / `_spawn` / `_ip_connect` | ✅ shipped (advisory MEDIUM/WARN) |
| RS4 `*` activation | in-house static | `extrace.s1.activation_wildcard` | ✅ pre-existing (HIGH / WARN) |
| runtime shell spawn + outbound socket | dynamic | `extrace.a8.reverse_shell` | ✅ shipped (HIGH, `AdversaryClass.A8`) |

## Status board — kagema / download-cradle dropper class

See [`kagema-detection-spec.md`](kagema-detection-spec.md). General rules (no kagema
literal in rule logic); the **DR5 conjunction** (sink × cradle), not any single part.

| Signal | Layer | Rule id | Status |
|---|---|---|---|
| DR5 sink × cradle (DR1∧DR2, one file) | in-house static | `extrace.s11.download_cradle` | ✅ shipped — **CRITICAL → BLOCK** (class-less; A4 conceptual, spec §7) |
| DR2 cradle string (cleartext echo) | semgrep | `download_cradle` (`extrace.sg.download_cradle`) | ✅ shipped (advisory MEDIUM/WARN) |
| runtime PowerShell spawn + outbound socket | dynamic | `extrace.a8.reverse_shell` | ✅ pre-existing — covers the runtime shape (win32-**blind** for this family, spec §6) |
| MN1/MN3/MN4 manifest signals | in-house static | *tbd* | ⬜ deferred (spec §4.2) |
| OB1 obfuscator.io `_0x` string-array signature | in-house static | *tbd* | ⬜ deferred (spec §9) |

C2 domain `niggboo.com` is on the shipped
[`blacklist_domains.txt`](../../packages/analysis_contracts/data/blacklist_domains.txt)
(matched by s4 + a7); the slur hostname is listed verbatim to block the operator's
infrastructure. Stage-2 MSI / URL SHA-256 hashes are reference IOCs in the spec §8
(no in-pipeline hash rule — they block the dropped payload, not the VSIX). The
durable signal is still DR5, not the host.

## Status board — GlassWorm / native-loader worm class

See [`glassworm-detection-spec.md`](glassworm-detection-spec.md). General rules
stay behavior-first; sample IPs are only curated denylist entries for s4/a7.

| Signal | Layer | Rule id | Status |
|---|---|---|---|
| UC2 invisible Unicode / PUA source-hiding run | in-house static | `extrace.s12.invisible_unicode_run` | ✅ shipped — **CRITICAL → BLOCK** for runs |
| NL3 bundled `.node` load + platform dispatch + host-context invoke | in-house static | `extrace.s13.native_node_loader` | ✅ shipped — **CRITICAL → BLOCK** for GlassWorm-strength conjunction |
| AA1 `context.globalState` dormancy / throttle | in-house static | `extrace.s14.globalstate_dormancy` | ✅ shipped — MEDIUM / dynamic fresh-profile telemetry |
| Embedded native binary | in-house static | `extrace.s3.embedded_native_binary` | ✅ pre-existing |
| Direct-IP C2/stager references | in-house static + dynamic | `extrace.s4.blacklisted_domain` / `extrace.a7.blacklisted_domain` | ✅ shipped via curated blacklist IP hosts |

## Status board — snyk-labs / VLN (vulnerable-legit-extension) class

See [`snyk-labs-vln-detection-spec.md`](snyk-labs-vln-detection-spec.md). This is a
**new, orthogonal axis** — "is the extension *vulnerable*?", not "is it
*malicious*?". General rules (no Instant-Markdown literal in rule logic); the
**VLN5 conjunction**, not any single part.

| Signal | Layer | Rule id | Status |
|---|---|---|---|
| VLN5 conjunction (server ∧ unguarded request→fs-read ∧ reachable-origin) | in-house static | `extrace.s15.path_traversal_server` | ✅ shipped — **MEDIUM / WARN** (vulnerability surface, never BLOCK) |
| VLN4 permissive-CORS surface (cleartext echo) | semgrep | `permissive_cors` (`extrace.sg.permissive_cors`) | ✅ shipped (advisory MEDIUM/WARN) |
| VLN2 request-path → fs-read **taint** (true dataflow) | semgrep (taint) | *tbd* | ⬜ container-iteration follow-up |
| **`VULNERABLE` verdict axis** (orthogonal to malice) | report contract + UI | — | ⛔ **deferred — needs owner sign-off** (shared-contract change, spec §6) |

This class has **no network IOCs by design** (the malicious page + receiver are
extension-external and not reproduced); the durable signals are structural. No
domains were fabricated. `blacklist_domains.txt` carries a documented **host-less**
section for the class so the integration point is recorded without inventing a
host (spec §8).

## Status board — nf3xn / reverse-shell (RS) class

See [`nf3xn-reverse-shell-spec.md`](nf3xn-reverse-shell-spec.md). A `securezeron`
sibling: already convicted by the RS rules; the two additions below are the
genuinely-new work it motivated. No nf3xn literal in rule logic.

| Signal | Layer | Rule id | Status |
|---|---|---|---|
| RS1 shell↔socket bridge — `.pipe()` **and** manual `stdin.write` form | in-house static | `extrace.s10.reverse_shell` | ✅ **improved** (CRITICAL → BLOCK) — manual-bridge variant now caught |
| MN reserved-publisher impersonation (`ms-vscode`) | in-house static | `extrace.s1.reserved_publisher_spoof` | ✅ **NEW** — MEDIUM / WARN (provenance-review signal, never a blocker) |
| RS4 `*` activation | in-house static | `extrace.s1.activation_wildcard` | ✅ pre-existing — **silent for nf3xn** (`onCommand`, correctly lower severity) |
| runtime shell spawn + outbound socket | dynamic | `extrace.a8.reverse_shell` | ✅ pre-existing — **fires** for nf3xn (Linux `/bin/sh` detonates, unlike kagema/glassworm) |

The L5 syscall expectation (socket-fd `dup2` + shell `execve`, `strace -f`
follow-fork) is documented in spec §5 and carried at runtime by `a8` — **no Falco
rule artifact** exists in this repo.

## Status board — ecm3401 / malicious-suite (MAL) class

See [`ecm3401-malicious-suite-spec.md`](ecm3401-malicious-suite-spec.md). The
**MALICIOUSNESS**-axis contrast to snyk-labs. General rules (no ecm3401 literal);
each of the three invariants alone is sufficient for a MALICIOUS verdict.

| Signal | Layer | Rule id | Status |
|---|---|---|---|
| TAMPER1 foreign-extension write (crown jewel, INV3) | in-house static | `extrace.s16.cross_extension_tamper` | ✅ **NEW — CRITICAL → BLOCK** (≈0 FP; own-dir allowlisted) |
| CRED-X credential read + network egress (INV1) | in-house static | `extrace.s17.credential_exfil` | ✅ **NEW — HIGH / WARN** (co-occurrence, not proven taint) |
| DROP1 make-executable + run (INV2) | in-house static | `extrace.s18.download_exec_dropper` | ✅ **NEW — HIGH / WARN** (HIGH confidence with remote fetch / shared symbol) |
| TAMPER1b install-root write (echo) | semgrep | `cross_extension_write` | ✅ **NEW** advisory MEDIUM/WARN |
| RECON1 home-dir enumeration | semgrep | `home_dir_enumeration` | ✅ **NEW** advisory MEDIUM/WARN |
| FINGERPRINT1 device fingerprint | semgrep | `device_fingerprint` | ✅ **NEW** advisory MEDIUM/WARN |
| CRED1 sensitive-path read (echo) / EXEC1 / NET1 | semgrep | `sensitive_file_read` / `child_process` / `outbound_net_module` | ✅ pre-existing |
| runtime cred read → egress | dynamic | `extrace.a1.credential_read_then_network` / `extrace.a4.workspace_exfil` | ✅ pre-existing (the runtime CRED-X half) |

No taxonomy / contract / gate-policy change: `s16` is CRITICAL (auto-BLOCKs like
`s10`/`s11`); `s17`/`s18` are HIGH/WARN; all three class-less per the static-IOC
convention. ECM3401 is a **first-class dynamic sample** (every command produces
syscalls) — `strace -f` follow-fork is required for the dropper's detached child
(spec §5).

## Status board — nextsecurity / stylesheet-TTP (STY) class

See [`nextsecurity-stylesheet-spec.md`](nextsecurity-stylesheet-spec.md). The
**first stylesheet (CSS/LESS) detection surface** — every prior rule reasons about
JS/manifest. General rules (no `nextsecurity` literal); the corpus is an
all-synthetic detection-test set, so **no host was added to the denylist**.

| Signal | Layer | Rule id | Status |
|---|---|---|---|
| Coverage gap — `.less`/`.scss`/`.sass` were never scanned | content scanners | `_common.TEXT_SUFFIXES` | ✅ **fix** — extends s4/s5/s7/s8/s9/s12 + s19 to stylesheets |
| TTP #8-less LESS inline-JS eval (RCE) | in-house static | `extrace.s19.stylesheet_inline_js` | ✅ shipped — **CRITICAL → BLOCK** (stylesheet-suffix-scoped; the one true RCE) |
| TTP #1/#3/#6 non-standard-scheme load | in-house static | `extrace.s19.stylesheet_nonstandard_scheme` | ✅ shipped — MEDIUM / WARN (signature/intent + `file://` local-read) |
| TTP #11/#16 CSS keylogger + content exfil | in-house static | `extrace.s19.stylesheet_css_exfil` | ✅ shipped — MEDIUM / WARN (href/src excluded; CSP-gated egress) |
| TTP #15 zero-width / RTL unicode in stylesheet | in-house static | `extrace.s12.invisible_unicode_run` | ✅ pre-existing — scans raw bytes of every file (`.less` included) |
| DoS structures / taint indirection / CSP-grading | AST / taint / dynamic | *tbd* | ⬜ **deferred** (spec §6) — regex cannot model graph cycles or variable→sink flow |

## Roadmap — deferred / next (security-development stream)

Forward items captured here so they are not lost; **none is auto-applied**. The
two below were explicitly held by the owner ("roadmap'e ekle, şimdilik dokunma").

| Item | Why deferred | Gate to start |
|---|---|---|
| **`VULNERABLE` verdict axis** (orthogonal to malice) — report both a MALICIOUSNESS and a VULNERABILITY verdict (snyk-labs spec §6) | **Shared-contract change**: report dataclass + Pydantic contract + `schema_version` bump + generated TS DTO + a new `V`-taxonomy node distinct from `AdversaryClass` A1–A8. Precedent: the A8 enum addition was signed off before the edit. | **Explicit owner sign-off.** Then verify the `V`-taxonomy ID against the real taxonomy before assigning one. |
| **Semgrep taint VLN2** — true dataflow (source = request path, sink = `fs` read, sanitizer = containment guard), higher-fidelity than `s15`'s co-occurrence approximation | Needs the `automation_static_analyzer` container; **no local semgrep** on the dev machine to verify a `mode: taint` rule. | Container-iteration cycle (owner runs the live-fire check). |
| `s15` UI `ruleCatalog.ts` entry | Enrichment only — surfaces the rule in the Rules tab. Non-blocking. | Opportunistic, next UI pass. |

Until the axis lands, `extrace.s15.path_traversal_server` ships at **MEDIUM / WARN**
on the existing malice-severity field — the documented stopgap (spec §3, §6).

## Iteration loop

1. Owner writes / runs a test against a fixture (or a live sample **in the
   sandbox** — never on the host).
2. Owner feeds back the result (fired / silent / FP / miss).
3. Rule(s) are added or tuned in the right layer (see reconciliation §5).
4. This board + the relevant spec are enriched; tests stay green.

## Verify locally (what runs without the container)

```bash
.venv/bin/python -m pytest tests/static_runtime/ tests/security/ -q  # static + dynamic rules
.venv/bin/ruff check static_runtime/rules/ packages/analysis_engine/rules/
npx --prefix ui tsc -b && npx --prefix ui vitest run                 # UI types + tests
```

Semgrep and the full VSIX pipeline run only in the `automation_static_analyzer`
container (`make static-up` / CI) — there is no local semgrep on the dev machine.
