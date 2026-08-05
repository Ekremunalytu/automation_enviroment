// Presentation metadata for the detection-rule trigger matrix.
//
// This catalog is *display* metadata only — labels, MITRE technique tags, threat
// family (column grouping), severity, a one-line `blurb`, and a richer `detail`
// paragraph for each known rule. It is NOT a source of activation truth: whether
// a rule fired/stayed silent always comes from the live report payload
// (`detection.rulesExecuted` for dynamic rules, `staticReport.findings` for
// static rules). The catalog only lets a *silent* cell render a meaningful
// label + description, since the payload carries titles for fired rules only.
//
// Values mirror the rule definitions in `packages/analysis_engine/rules/*` (dynamic)
// and `static_runtime/rules/*` (static). A drift-guard test asserts every rule_id seen
// in a representative bundle fixture is covered here. Rules that fire but are absent
// here (e.g. external Semgrep `extrace.sg.*`) still surface — they render from their
// live finding instead of the catalog.

export type RuleStream = "static" | "dynamic";

export type RuleSeverity = "critical" | "high" | "medium" | "low" | "info";

export interface RuleCatalogEntry {
  ruleId: string;
  label: string;
  stream: RuleStream;
  /** Threat family — used as the column grouping in the matrix (MITRE-tactic-like). */
  family: string;
  /** MITRE ATT&CK technique IDs, e.g. ["T1555", "T1041"]. */
  techniques: string[];
  severity: RuleSeverity;
  /** One-line summary (compact surfaces). */
  blurb: string;
  /** Richer 2-3 sentence description: what it detects, why it matters, and the
   *  false-positive / escalation nuance. Rendered in the rule detail dialog. */
  detail: string;
}

const ENTRIES: RuleCatalogEntry[] = [
  // ── Dynamic behavioral rules (packages/analysis_engine/rules) ──────────────
  {
    ruleId: "extrace.a1.credential_read_then_network",
    label: "Credential read → network",
    stream: "dynamic",
    family: "Credential Access",
    techniques: ["T1555", "T1041"],
    severity: "critical",
    blurb: "A credential / secret file is read and is followed by an outbound request.",
    detail:
      "At runtime the extension reads a file under a credential store (~/.ssh, ~/.aws, ~/.config/gh, .netrc) and then contacts a non-benign external host within the same activation window. The read-then-exfil pairing is the classic credential-theft signature; the timing correlation is what separates it from benign config reads.",
  },
  {
    ruleId: "extrace.a2.startup_network_beacon",
    label: "Startup network beacon",
    stream: "dynamic",
    family: "Command & Control",
    techniques: ["T1496"],
    severity: "high",
    blurb: "A burst of outbound connections fires at activation/startup time.",
    detail:
      "A burst of outbound connections fires within seconds of activation, before any user action. This is the check-in pattern of a freshly-installed implant beaconing to its command-and-control server — legitimate extensions rarely open multiple connections at startup with no user trigger.",
  },
  {
    ruleId: "extrace.a3.typosquat",
    label: "Typosquat identifier",
    stream: "dynamic",
    family: "Masquerading",
    techniques: ["T1036"],
    severity: "high",
    blurb: "The extension identifier impersonates a popular, trusted extension.",
    detail:
      "The extension identifier closely imitates a popular, trusted extension via character swaps, insertions, or look-alikes. This masquerading trick gets the extension installed by users who mistype or misread the real one's name.",
  },
  {
    ruleId: "extrace.a4.workspace_exfil",
    label: "Workspace exfiltration",
    stream: "dynamic",
    family: "Exfiltration",
    techniques: ["T1041"],
    severity: "high",
    blurb: "A workspace file is read and then followed by an outbound transfer.",
    detail:
      "A workspace file is read and an outbound transfer to a non-benign host follows soon after — source-code or secret exfiltration. This is the confidentiality counterpart to A5 (file tampering); here the data leaves the machine rather than being rewritten in place.",
  },
  {
    ruleId: "extrace.a5.workspace_file_tamper",
    label: "Workspace file tamper",
    stream: "dynamic",
    family: "Integrity / Tampering",
    techniques: ["T1565"],
    severity: "medium",
    blurb: "A workspace file the extension read is rewritten in place.",
    detail:
      "The extension reads a workspace file and then writes back to the same path — the read-modify-save signature of a crypto-clipper or content-rewriter (the dynamic counterpart of the static crypto-awareness rule). MEDIUM, not HIGH: legitimate formatters and auto-fixers also rewrite files in place, so the runtime file layer can flag the integrity action but not prove intent — escalate when the extension is otherwise flagged.",
  },
  {
    ruleId: "extrace.a6.startup_ui_prompt",
    label: "Startup UI prompt",
    stream: "dynamic",
    family: "UI Deception",
    techniques: [],
    severity: "medium",
    blurb: "A UI prompt is shown at startup, before normal activation — possible spoofing.",
    detail:
      "A UI prompt (notification or input box) is shown at startup, before normal activation. This is consistent with credential-phishing or consent-spoofing — getting the user to approve or type something under the guise of a routine editor prompt.",
  },
  {
    ruleId: "extrace.a7.blacklisted_domain",
    label: "Blacklisted domain (observed)",
    stream: "dynamic",
    family: "Command & Control",
    techniques: ["T1071"],
    severity: "high",
    blurb: "An outbound connection was observed to a domain on the operator blacklist.",
    detail:
      "An outbound connection was observed at runtime to a domain on the operator-maintained blacklist — a known command-and-control or exfiltration destination. The denylist is editable from the Blacklist tab; seed entries are fixed and operator entries can be added or removed.",
  },
  {
    ruleId: "extrace.a8.reverse_shell",
    label: "Reverse shell (observed)",
    stream: "dynamic",
    family: "Execution / C2",
    techniques: ["T1059"],
    severity: "high",
    blurb: "A shell was spawned and an outbound socket opened together at runtime.",
    detail:
      "At runtime the extension spawned an OS shell (sh / bash / cmd.exe / powershell) and opened an outbound socket to a non-benign endpoint within the correlation window — the runtime signature of an interactive reverse shell (the dynamic counterpart of the static s10 rule). HIGH, not the static rule's CRITICAL: the sandbox observes the shell spawn and the egress but not the stdio wiring between them, so it surfaces a strong correlation for review. The shell-binary filter keeps benign language-server / git / build spawns out of the match.",
  },
  {
    ruleId: "extrace.demo.runnable_canary",
    label: "Runnable canary (demo)",
    stream: "dynamic",
    family: "Validation",
    techniques: [],
    severity: "info",
    blurb: "Pipeline validation canary — proves the detection engine ran end-to-end.",
    detail:
      "A pipeline-validation canary that fires on a known input to prove the detection engine ran end-to-end. It is not a real threat signal — its presence confirms the rule runner executed and produced findings.",
  },

  // ── Static pre-check rules (static_runtime/rules) ──────────────────────────
  {
    ruleId: "extrace.s1.activation_wildcard",
    label: "Wildcard activation",
    stream: "static",
    family: "Persistence",
    techniques: ["T1546"],
    severity: "high",
    blurb: "The extension activates on the '*' wildcard event (always-on).",
    detail:
      "The manifest activates on the '*' wildcard — every workspace, always-on — rather than a scoped activation event. That gives the extension a persistent foothold that runs without any user trigger, broadening whatever else it does.",
  },
  {
    ruleId: "extrace.s1.suspicious_capabilities",
    label: "Untrusted workspace support",
    stream: "static",
    family: "Execution",
    techniques: ["T1059"],
    severity: "info",
    blurb: "The manifest declares support for untrusted workspaces.",
    detail:
      "The manifest declares that the extension can run in untrusted workspaces. This is exposure metadata for reviewing Workspace Trust guards, not evidence of malicious behaviour; npm lifecycle scripts in a packaged VSIX are build metadata and do not fire this rule.",
  },
  {
    ruleId: "extrace.s1.generic_publisher",
    label: "Generic publisher",
    stream: "static",
    family: "Masquerading",
    techniques: ["T1036"],
    severity: "low",
    blurb: "Missing or placeholder publisher identity.",
    detail:
      "The publisher identity is missing or a placeholder, so there is no accountable author. A throwaway / generic publisher is a common trait of low-effort malicious uploads and weakens any trust signal from the marketplace listing.",
  },
  {
    ruleId: "extrace.s1.reserved_publisher_spoof",
    label: "Reserved publisher claim",
    stream: "static",
    family: "Masquerading",
    techniques: ["T1036"],
    severity: "info",
    blurb: "The manifest claims a reserved first-party publisher namespace (ms-vscode / github / ...).",
    detail:
      "The manifest publisher is a reserved first-party brand namespace (microsoft / ms-vscode / vscode / github / ...). Name-only matching cannot separate a spoof from a genuine first-party extension, so this remains INFO until marketplace provenance is verified; an independently proven malicious capability owns any WARN/BLOCK.",
  },
  {
    ruleId: "extrace.s2.typosquat",
    label: "Typosquat identifier (static)",
    stream: "static",
    family: "Masquerading",
    techniques: ["T1036"],
    severity: "high",
    blurb: "The extension identifier impersonates a popular, trusted extension.",
    detail:
      "A static identifier check finds the extension id imitating a popular, trusted extension. This is a promoted blocker: a typosquat match rejects the extension at the static gate, before any sandbox run, because the masquerade intent is unambiguous.",
  },
  {
    ruleId: "extrace.s3.embedded_native_binary",
    label: "Embedded native binary",
    stream: "static",
    family: "Ingress / Native Code",
    techniques: ["T1105"],
    severity: "info",
    blurb: "Ships embedded native / binary files that execute outside the JS sandbox.",
    detail:
      "The package ships embedded native or binary files (a .node addon, or an ELF / Mach-O / PE executable). Presence is INFO inventory because legitimate extensions ship native helpers; the separate S13 loader conjunction owns malicious native-loader escalation.",
  },
  {
    ruleId: "extrace.s3.unusual_file_signature",
    label: "Unusual file signature",
    stream: "static",
    family: "Defense Evasion",
    techniques: ["T1027"],
    severity: "info",
    blurb: "Contains unusually large or obfuscated text/source files.",
    detail:
      "The tree contains unusually large or high-entropy text / source files — a shape consistent with bundled or obfuscated payloads. On its own it is weak signal, but it often accompanies packing used to hide executed logic.",
  },
  {
    ruleId: "extrace.s4.blacklisted_domain",
    label: "Blacklisted domain (source)",
    stream: "static",
    family: "Command & Control",
    techniques: ["T1071"],
    severity: "high",
    blurb: "Source or manifest references a domain on the operator blacklist.",
    detail:
      "The source or manifest hardcodes a domain on the operator blacklist — a known-bad endpoint baked into the code, found statically before the extension ever runs. The denylist is shared with the dynamic A7 rule and editable from the Blacklist tab.",
  },
  {
    ruleId: "extrace.s5.suspicious_network_endpoint",
    label: "Suspicious network endpoint",
    stream: "static",
    family: "Command & Control",
    techniques: ["T1071"],
    severity: "info",
    blurb: "Hardcodes a routable public-IP literal and/or a cleartext http:// host.",
    detail:
      "The source hardcodes a routable public-IP literal and/or a cleartext http:// external host. A real extension talks to named services over TLS, so a raw public-IP target or an unencrypted endpoint is a classic command-and-control / staging shape. Loopback, private, and documentation ranges are excluded to keep it high-signal.",
  },
  {
    ruleId: "extrace.s6.obfuscation_indicators",
    label: "Obfuscation indicators",
    stream: "static",
    family: "Defense Evasion",
    techniques: ["T1027"],
    severity: "medium",
    blurb: "Decode-then-execute, char-code chains, base64 blobs, or hex-escape runs.",
    detail:
      "The source shows packing tricks — decode-then-execute, fromCharCode chains, large base64 blobs, or long hex-escape runs — that hide the executed logic from static review. Legitimate code rarely needs to assemble and run a decoded payload, so this is a defense-evasion indicator.",
  },
  {
    ruleId: "extrace.s7.hardcoded_secret",
    label: "Hardcoded secret",
    stream: "static",
    family: "Credential Access",
    techniques: ["T1552"],
    severity: "medium",
    blurb: "Ships a credential (AWS key, GitHub / Slack token, private key) in source.",
    detail:
      "The package ships a credential in source — an AWS key, a GitHub / Slack token, or a private key. That is either an accidental leak (still a supply-chain risk) or an attacker's baked-in credential used to authenticate exfiltration or further access.",
  },
  {
    ruleId: "extrace.s8.exfil_webhook",
    label: "Exfiltration webhook",
    stream: "static",
    family: "Exfiltration",
    techniques: ["T1567"],
    severity: "high",
    blurb: "Hardcodes a Discord / Slack / Telegram webhook ingestion endpoint.",
    detail:
      "The source hardcodes a Discord, Slack, or Telegram webhook ingestion endpoint — the canonical drop point for commodity infostealers. It is matched by the exact ingestion-path shape (e.g. /api/webhooks/<id>/<token>), not a bare host mention, so a community / docs link to the service does not fire. HIGH severity, but warns rather than blocks: presence alone is a strong exfil-channel signal that escalates when paired with content-read and a network sink.",
  },
  {
    ruleId: "extrace.s9.crypto_address_scan",
    label: "Crypto address awareness",
    stream: "static",
    family: "Integrity / Tampering",
    techniques: ["T1565"],
    severity: "info",
    blurb: "Source recognises wallet-address formats (Base58 / Ethereum / bech32).",
    detail:
      "The source contains quantified cryptocurrency address regexes — Base58 (BTC), 0x + 40-hex (Ethereum), or bech32 / SegWit. Recognition alone is INFO inventory; a clipboard or file-write mutation correlation must own escalation. Quantifiers exclude AES lookup arrays and MIPS bc1[ft] instruction patterns.",
  },
  {
    ruleId: "extrace.s10.reverse_shell",
    label: "Reverse shell",
    stream: "static",
    family: "Execution / C2",
    techniques: ["T1059"],
    severity: "critical",
    blurb: "Wires a child_process shell's stdio to a network socket.",
    detail:
      "The source spawns an OS shell and connects the same process/socket variables on both stdio bridge directions inside a bounded region. That variable-connected topology defines an interactive reverse shell. Unrelated child_process, proxy-socket, and stream libraries elsewhere in a bundle cannot combine into this CRITICAL blocker.",
  },
  {
    ruleId: "extrace.s11.download_cradle",
    label: "Download cradle (dropper)",
    stream: "static",
    family: "Execution / C2",
    techniques: ["T1059", "T1105"],
    severity: "critical",
    blurb: "child_process drives a hidden-PowerShell irm → iex download cradle.",
    detail:
      "The source drives a child_process sink with a hidden-PowerShell download cradle — powershell → Invoke-RestMethod / Invoke-WebRequest → Invoke-Expression — that fetches a remote script and runs it in memory, downloading and executing an arbitrary second stage with no user interaction and nothing written to disk (the kagema / ShowSnowcrypto.SnowShoNo dropper shape). CRITICAL and BLOCKs before the sandbox: the cradle is matched as one ordered powershell→download→execute span wired to a child_process sink, so a bare child_process call or a lone powershell mention does not fire. Blocking statically is load-bearing here because the payload is gated on process.platform === 'win32', so a Linux dynamic sandbox never observes it. The cradle string survives string-array obfuscation (literals stay cleartext); an APT variant that splits the command across lines is the documented evasion gap.",
  },
  {
    ruleId: "extrace.s12.invisible_unicode_run",
    label: "Invisible Unicode run",
    stream: "static",
    family: "Defense Evasion",
    techniques: ["T1027"],
    severity: "critical",
    blurb: "Original source bytes contain invisible Unicode / PUA codepoint runs.",
    detail:
      "The source contains invisible Unicode, variation-selector, or Private Use Area codepoints. Runs shorter than 16 remain INFO because localization and generated Unicode tables legitimately contain them; 16+ contiguous codepoints are CRITICAL source-hiding evidence. The scanner works over original packaged bytes.",
  },
  {
    ruleId: "extrace.s13.native_node_loader",
    label: "Native .node loader",
    stream: "static",
    family: "Native Code / C2",
    techniques: ["T1059"],
    severity: "high",
    blurb: "Loads a bundled .node module, escalating on platform dispatch and host context.",
    detail:
      "The source loads a bundled native .node addon. A plain native addon is MEDIUM, but the rule escalates when the loader dispatches on win32/darwin, passes host context such as process.execPath or __dirname into the native module, or appears in a theme/icon/snippet-style package; the GlassWorm-strength conjunction can block before dynamic analysis. A win32/darwin-only branch is also surfaced as a Linux sandbox blind spot, not a reason to lower confidence.",
  },
  {
    ruleId: "extrace.s14.globalstate_dormancy",
    label: "globalState dormancy",
    stream: "static",
    family: "Sandbox Evasion",
    techniques: ["T1497"],
    severity: "medium",
    blurb: "Uses context.globalState with timestamp gating to throttle payload execution.",
    detail:
      "The extension stores activation state in VS Code globalState and gates an init/payload call on a timestamp or cooldown. This is MEDIUM by itself because stateful extensions can be legitimate, but it is important dynamic-analysis telemetry: repeated runs must use a fresh VS Code profile/globalState or the payload may skip execution.",
  },
  {
    ruleId: "extrace.s15.path_traversal_server",
    label: "Path-traversal file server",
    stream: "static",
    family: "Vulnerability",
    techniques: ["T1083", "T1005"],
    severity: "medium",
    blurb: "Local server maps a request path onto an unguarded fs read, reachable cross-origin.",
    detail:
      "The extension runs a local HTTP server whose handler maps a request path onto a filesystem read with no containment guard and is reachable from another origin — the path-traversal exposure that lets a malicious web page read arbitrary local files (the 2021 snyk-labs Instant Markdown class). MEDIUM and never blocks: this is a vulnerability surface, not proven malice. The rule keys on the server ∧ unguarded request→fs-read ∧ reachable-origin conjunction, so a server that sanitizes the path or binds loopback-only does not fire; it belongs to the orthogonal 'is it vulnerable?' axis rather than 'is it malicious?'.",
  },
  {
    ruleId: "extrace.s16.cross_extension_tamper",
    label: "Cross-extension tamper",
    stream: "static",
    family: "Integrity / Tampering",
    techniques: ["T1554", "T1574"],
    severity: "critical",
    blurb: "Writes or copies into another extension's install directory.",
    detail:
      "The source writes or copies into a *different* extension's install directory — a foreign extensionPath or a .vscode/extensions sibling path — overwriting a neighbouring extension's code to hijack its execution or persist (the ecm3401 TAMPER1 crown jewel). CRITICAL and BLOCKs before the sandbox: tampering with another extension's files has no legitimate use, and the rule allowlists the extension's own directory, so writing to itself does not fire.",
  },
  {
    ruleId: "extrace.s17.credential_exfil",
    label: "Credential read → exfil",
    stream: "static",
    family: "Credential Access",
    techniques: ["T1552.004", "T1041"],
    severity: "high",
    blurb: "One module reads a sensitive credential file and holds an outbound egress sink.",
    detail:
      "A single module both reads a sensitive credential file (SSH / AWS / keychain / wallet / private-key paths) and holds an outbound network egress sink — the read-then-exfil shape of a credential stealer (ecm3401 CRED-X). HIGH and warns rather than blocks: it is a co-occurrence, not a proven taint from the read to the network call, so a module that legitimately reads a config near unrelated networking is surfaced for review rather than convicted.",
  },
  {
    ruleId: "extrace.s18.download_exec_dropper",
    label: "Drop-and-run dropper",
    stream: "static",
    family: "Execution / C2",
    techniques: ["T1105", "T1059"],
    severity: "high",
    blurb: "Makes a file executable (chmod +x) and runs it via child_process.",
    detail:
      "The source gives a file the executable bit (chmod +x, or an fs.chmod with an exec mode) and then runs it via child_process — the drop-and-run primitive of a dropper/loader (ecm3401 DROP1). HIGH/WARN because a legitimate cousin exists (a toolchain/LSP extension that fetches and runs a helper binary), so it surfaces rather than blocks; confidence rises to HIGH when a remote fetch completes the download→chmod→execute chain or the chmod target and the exec target are the same symbol.",
  },
  {
    ruleId: "extrace.s19.stylesheet_inline_js",
    label: "Stylesheet inline-JS (LESS eval)",
    stream: "static",
    family: "Execution / C2",
    techniques: ["T1059"],
    severity: "critical",
    blurb: "Backtick eval in a CSS/LESS stylesheet → compile-time RCE in the extension host.",
    detail:
      "A stylesheet (.css/.less/.scss/.sass) contains LESS inline JavaScript — a backtick-delimited expression (~`...`) that the LESS compiler evaluates in the extension-host Node.js process, with full fs/child_process/net access (the nextsecurity stylesheet corpus' one true RCE vector). CRITICAL and BLOCKs: the rule is stylesheet-suffix-scoped because a backtick is anomalous only in CSS (applying it to .js would false-positive on every template literal), and shipping inline JS in a stylesheet has no benign explanation even though less.js ≥ 3.0 defaults javascriptEnabled off.",
  },
  {
    ruleId: "extrace.s19.stylesheet_nonstandard_scheme",
    label: "Stylesheet non-standard scheme",
    stream: "static",
    family: "Command & Control",
    techniques: ["T1071"],
    severity: "medium",
    blurb: "@import / url() / src: targets ftp / ws / file / javascript and similar schemes.",
    detail:
      "A stylesheet resource loader (@import / url() / src:) targets a non-standard URL scheme — ftp, ws/wss, gopher, file, javascript or vbscript. MEDIUM and never blocks: most are inert in a modern Chromium webview, so the value is signature/author-intent plus the live file:// local-read attempt; remote http(s) hosts are deliberately excluded because that scrutiny is the s4/s5 layer's job, gradable by CSP.",
  },
  {
    ruleId: "extrace.s19.stylesheet_css_exfil",
    label: "CSS-native exfiltration",
    stream: "static",
    family: "Exfiltration",
    techniques: ["T1041", "T1056"],
    severity: "medium",
    blurb: "Substring-attribute keylogger or ::after content beacon firing a remote url().",
    detail:
      "A stylesheet uses a CSS-native exfiltration shape — a substring/prefix/suffix attribute selector on a value-bearing attribute (the CSS-keylogger primitive, leaking input character-by-character) or a ::before/::after content pseudo-element — to fire a remote url() GET. MEDIUM/WARN: URL/structural attribute selectors (href/src/class/id/...) are excluded because prefix-matching them with a remote icon is the legitimate external-link-icon pattern, and the remote egress is gated by the webview CSP, so the shape is surfaced for review rather than convicted.",
  },
  {
    ruleId: "extrace.s20.rmm_remote_access",
    label: "RMM-as-RAT (BYOSC)",
    stream: "static",
    family: "Command & Control",
    techniques: ["T1219"],
    severity: "high",
    blurb: "ScreenConnect/ConnectWise client reference ∧ unattended-access relay config.",
    detail:
      "The extension references a remote-access (RMM) client — ScreenConnect / ConnectWise Control — together with an unattended-access relay configuration (the e=Access&y=Guest launch params or a &h=/&p=/&s=/&k= relay connection string): the bring-your-own-ScreenConnect (BYOSC) deployment that turns a legitimately-signed RMM into a RAT (the snowshono Stage-3 payload). HIGH/WARN like s18 because an official remote-support extension is a conceivable legit cousin; confidence rises to HIGH when the relay is a bare IP rather than a named *.screenconnect.com host. The client reference and the unattended-relay config are both required, so a benign product mention alone does not fire.",
  },
];

const BY_ID: Record<string, RuleCatalogEntry> = Object.fromEntries(
  ENTRIES.map((entry) => [entry.ruleId, entry]),
);

export function ruleCatalogEntry(ruleId: string): RuleCatalogEntry | undefined {
  return BY_ID[ruleId];
}

/** All known rule_ids for a stream — the "universe" used to render silent static cells. */
export function catalogRuleIds(stream: RuleStream): string[] {
  return ENTRIES.filter((entry) => entry.stream === stream).map((entry) => entry.ruleId);
}

export function catalogEntries(stream: RuleStream): RuleCatalogEntry[] {
  return ENTRIES.filter((entry) => entry.stream === stream);
}
