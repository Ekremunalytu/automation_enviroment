# GlassWorm Detection Spec - VS Code / OpenVSX Native-Loader Worm

> Fourth in the custom-rule series after apollyon, securezeron, and kagema.
> This spec maps the local GlassWorm / `icon-theme-materiall` handoff into
> ExTrace's actual rule layers. No real VSIX, native implant, or stage-2 payload
> is downloaded, stored, or executed in this repository.

## 0. Safety And Scope

This design is driven by a local rule-development handoff, not by vendoring a
live malicious sample. The source-verified shape is a readable JS loader stub:

- `context.globalState` activation state and throttle.
- `os.platform()` / `process.platform` dispatch.
- Windows `os.node` and macOS `darwin.node` native addon loading.
- Host context (`process.execPath`, `__dirname`) passed into native code.
- No Linux branch, which creates a Linux-sandbox blind spot.

Campaign context says the family also used invisible Unicode source hiding,
native Rust implants, Solana / calendar dead-drop C2, stage-2 retrieval, credential
theft, wallet theft, proxy/RAT behavior, and worm propagation. Those capabilities
belong to campaign context unless the scanned VSIX itself exposes evidence.

## 1. Detection Invariants

| Signal | Rule layer | Rule id | Status |
|---|---|---|---|
| UC2 invisible Unicode / PUA run in original source bytes | in-house static | `extrace.s12.invisible_unicode_run` | shipped - CRITICAL when run >= 16; shorter runs INFO |
| NL bundled `.node` native load with platform dispatch and host context | in-house static | `extrace.s13.native_node_loader` | shipped - CRITICAL for GlassWorm-strength conjunction |
| AA globalState timestamp dormancy / throttle | in-house static | `extrace.s14.globalstate_dormancy` | shipped - MEDIUM telemetry/warn |
| Raw public-IP / cleartext C2 endpoint | in-house static | `extrace.s5.suspicious_network_endpoint` | pre-existing - MEDIUM |
| Curated known-bad C2 host/IP in source | in-house static | `extrace.s4.blacklisted_domain` | pre-existing - HIGH |
| Observed outbound C2 host/IP | dynamic | `extrace.a7.blacklisted_domain` | pre-existing - HIGH |
| Embedded native binary in package tree | in-house static | `extrace.s3.embedded_native_binary` | pre-existing - INFO inventory; S13 owns conviction |

The durable detection is behavior-first: source steganography, native-loader
shape, platform gate, host-context invoke, and stateful dormancy. IOCs enrich the
report and pin regressions, but they are secondary because hosts, wallets, and
calendar dead-drops rotate.

## 2. False Positive Strategy

Legitimate native addons exist in language servers, debuggers, compiler tooling,
and performance-heavy parsers. `extrace.s13.native_node_loader` therefore starts
at MEDIUM for a plain `.node` load and escalates only on context:

- platform dispatch (`win32`, `darwin`, `linux`);
- host context passed to the native module (`process.execPath`, `__dirname`,
  `process.env`, extension storage paths);
- theme/icon/snippet/formatter-like package identity;
- platform-generic native filenames such as `os.node` or `darwin.node`;
- win32/darwin-only payload with no Linux branch.

A theme or icon extension with `os.node` / `darwin.node`, no Linux branch, and
`process.execPath` / `__dirname` passed into native code is not treated like a
normal native parser. It is a static block candidate before the Linux sandbox can
miss the payload branch.

## 3. IOC Appendix - Defanged Reference Text

These values are inert reference indicators only. Do not fetch, resolve, open,
ping, or convert them into clickable report output.

Sample-specific SHA-256 references:

```text
os.node:
6ebeb188f3cc3b647c4460c0b8e41b75d057747c662f4cd7912d77deaccfd2f2

darwin.node:
fb07743d139f72fca4616b01308f1f705f02fda72988027bc68e9316655eadda

extension.js:
9212a99a7730b9ee306e804af358955c3104e5afce23f7d5a207374482ab2f8f

decrypted stage JavaScript:
c32379e4567a926aa0d35d8123718e2ebeb15544a83a5b1da0269db5829d5ece
```

Curated denylist additions in
[`blacklist_domains.txt`](../../packages/analysis_contracts/data/blacklist_domains.txt):

```text
217[.]69[.]11[.]60
217[.]69[.]3[.]218
140[.]82[.]52[.]31
```

Known URL forms from the handoff remain defanged in documentation:

```text
hxxp://217[.]69[.]11[.]60/uVK7ZJefmiIoJkIP6lxWXw==
hxxp://217[.]69[.]11[.]60/get_arhive_npm/karMkkT87qcssRoaHL1zYQ==
hxxp://217[.]69[.]11[.]60/get_zombi_payload/uVK7ZJefmiIoJkIP6lxWXw%3D%3D
hxxps://calendar[.]google[.]com/calendar/share?slt=...
hxxps://calendar[.]app[.]google/M2ZCvM8ULL56PD1d6
uhjdclolkdn[at]gmail[.]com
```

The Google Calendar / Gmail hosts are deliberately not added to the shipped
denylist because they are shared infrastructure and would create broad false
positives. The direct IP C2/stager hosts are listed because the matcher treats
them as exact host indicators and both `s4` and `a7` can use them safely.
