// Presentation metadata for the detection-rule trigger matrix.
//
// This catalog is *display* metadata only — labels, MITRE technique tags, threat
// family (column grouping), and a one-line description for each known rule. It is
// NOT a source of activation truth: whether a rule fired/stayed silent always comes
// from the live report payload (`detection.rulesExecuted` for dynamic rules,
// `staticReport.findings` for static rules). The catalog only lets a *silent* cell
// render a meaningful label, since the payload carries titles for fired rules only.
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
  blurb: string;
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
  },
  {
    ruleId: "extrace.a2.startup_network_beacon",
    label: "Startup network beacon",
    stream: "dynamic",
    family: "Command & Control",
    techniques: ["T1496"],
    severity: "high",
    blurb: "A burst of outbound connections fires at activation/startup time.",
  },
  {
    ruleId: "extrace.a3.typosquat",
    label: "Typosquat identifier",
    stream: "dynamic",
    family: "Masquerading",
    techniques: ["T1036"],
    severity: "high",
    blurb: "The extension identifier impersonates a popular, trusted extension.",
  },
  {
    ruleId: "extrace.a4.workspace_exfil",
    label: "Workspace exfiltration",
    stream: "dynamic",
    family: "Exfiltration",
    techniques: ["T1041"],
    severity: "high",
    blurb: "A workspace file is read and then followed by an outbound transfer.",
  },
  {
    ruleId: "extrace.a6.startup_ui_prompt",
    label: "Startup UI prompt",
    stream: "dynamic",
    family: "UI Deception",
    techniques: [],
    severity: "medium",
    blurb: "A UI prompt is shown at startup, before normal activation — possible spoofing.",
  },
  {
    ruleId: "extrace.demo.runnable_canary",
    label: "Runnable canary (demo)",
    stream: "dynamic",
    family: "Validation",
    techniques: [],
    severity: "info",
    blurb: "Pipeline validation canary — proves the detection engine ran end-to-end.",
  },

  // ── Static pre-check rules (static_runtime/rules) ──────────────────────────
  {
    ruleId: "extrace.s1.activation_wildcard",
    label: "Wildcard activation",
    stream: "static",
    family: "Persistence",
    techniques: ["T1546"],
    severity: "low",
    blurb: "The extension activates on the '*' wildcard event (always-on).",
  },
  {
    ruleId: "extrace.s1.suspicious_capabilities",
    label: "Elevated capabilities",
    stream: "static",
    family: "Execution",
    techniques: ["T1059"],
    severity: "medium",
    blurb: "The manifest requests elevated / sensitive capabilities.",
  },
  {
    ruleId: "extrace.s1.generic_publisher",
    label: "Generic publisher",
    stream: "static",
    family: "Masquerading",
    techniques: ["T1036"],
    severity: "low",
    blurb: "Missing or placeholder publisher identity.",
  },
  {
    ruleId: "extrace.s2.typosquat",
    label: "Typosquat identifier (static)",
    stream: "static",
    family: "Masquerading",
    techniques: ["T1036"],
    severity: "high",
    blurb: "The extension identifier impersonates a popular, trusted extension.",
  },
  {
    ruleId: "extrace.s3.embedded_native_binary",
    label: "Embedded native binary",
    stream: "static",
    family: "Ingress / Native Code",
    techniques: ["T1105"],
    severity: "medium",
    blurb: "Ships embedded native / binary files that execute outside the JS sandbox.",
  },
  {
    ruleId: "extrace.s3.unusual_file_signature",
    label: "Unusual file signature",
    stream: "static",
    family: "Defense Evasion",
    techniques: ["T1027"],
    severity: "low",
    blurb: "Contains unusually large or obfuscated text/source files.",
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
