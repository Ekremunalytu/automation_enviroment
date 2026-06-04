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
    label: "Elevated capabilities",
    stream: "static",
    family: "Execution",
    techniques: ["T1059"],
    severity: "medium",
    blurb: "The manifest requests elevated / sensitive capabilities.",
    detail:
      "The manifest requests elevated or sensitive capabilities (for example untrusted-workspace execution) beyond what its stated function appears to need. Over-broad capability requests widen the blast radius if the extension is malicious or compromised.",
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
    severity: "medium",
    blurb: "Ships embedded native / binary files that execute outside the JS sandbox.",
    detail:
      "The package ships embedded native or binary files (a .node addon, or an ELF / Mach-O / PE executable) that run outside the JavaScript sandbox. Native code is opaque to source review, so a bundled binary is a way to smuggle in logic the static scan cannot read.",
  },
  {
    ruleId: "extrace.s3.unusual_file_signature",
    label: "Unusual file signature",
    stream: "static",
    family: "Defense Evasion",
    techniques: ["T1027"],
    severity: "low",
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
    severity: "medium",
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
    severity: "medium",
    blurb: "Source recognises wallet-address formats (Base58 / Ethereum / bech32).",
    detail:
      "The source contains cryptocurrency address patterns — Base58 (BTC), 0x + 40-hex (Ethereum), or bech32 / SegWit — the address-recognition capability a crypto-clipper needs before it can hijack a wallet address. MEDIUM, not a verdict: a genuine blockchain / wallet tool legitimately has these, so it surfaces the capability for review and escalates when it co-occurs with clipboard, file-write, or network access (the dynamic A5 file-tamper rule is its runtime counterpart).",
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
      "The source spawns an OS shell via child_process and pipes that shell's stdio to a raw network socket — the bidirectional wiring that defines an interactive reverse shell, handing a remote endpoint a live command channel on the victim with no user interaction. CRITICAL and the only static rule that BLOCKS before the sandbox runs: the match requires all three elements (shell spawn, socket, and a stdio-to-socket pipe) in one file, so the individually benign uses of child_process or a socket do not fire, and a shell piped to a socket has no legitimate explanation.",
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
