import { describe, expect, it } from "vitest";

import type {
  ActivationReportView,
  DetectionReportView,
  StaticReportView,
} from "../../lib/types/view-models";
import { buildRuleMatrix } from "./buildRuleMatrix";
import { catalogRuleIds, ruleCatalogEntry } from "./ruleCatalog";

function makeReport(partial: {
  detection?: DetectionReportView | null;
  staticReport?: StaticReportView | null;
}): ActivationReportView {
  // buildRuleMatrix only reads `detection` and `staticReport`; the rest of the
  // (large) view-model is irrelevant for this unit.
  return {
    detection: partial.detection ?? null,
    staticReport: partial.staticReport ?? null,
  } as unknown as ActivationReportView;
}

const DETECTION: DetectionReportView = {
  verdict: "suspicious",
  verdictLabel: "Suspicious",
  verdictRationale: "",
  rulesExecuted: [
    {
      ruleId: "extrace.a1.credential_read_then_network",
      ruleVersion: "1.0.0",
      lifecycle: "production",
      status: "fired",
      statusLabel: "Fired",
      findingIds: ["f1"],
      errorDetail: "",
    },
    {
      ruleId: "extrace.a2.startup_network_beacon",
      ruleVersion: "1.0.0",
      lifecycle: "production",
      status: "silent",
      statusLabel: "Silent",
      findingIds: [],
      errorDetail: "",
    },
    {
      ruleId: "extrace.a3.typosquat",
      ruleVersion: "1.0.0",
      lifecycle: "production",
      status: "error",
      statusLabel: "Error",
      findingIds: [],
      errorDetail: "rule blew up",
    },
  ],
  findings: [
    {
      id: "f1",
      ruleId: "extrace.a1.credential_read_then_network",
      ruleVersion: "1.0.0",
      ruleLifecycle: "production",
      title: "Credential read then network",
      description: "Secret read followed by an outbound request.",
      categories: ["attack.T1555", "attack.T1041", "extrace.host.cred"],
      severity: "critical",
      severityLabel: "Critical",
      confidence: "high",
      confidenceLabel: "High",
      adversaryClass: "A1",
      evidence: [{ eventId: "e1", type: "network", summary: "POST evil.example" }],
      mitigationHint: "Block the egress.",
    },
  ],
};

const STATIC_REPORT: StaticReportView = {
  decision: "warn",
  decisionLabel: "Warn",
  blockedBy: [],
  warnedBy: ["extrace.s3.embedded_native_binary"],
  allowReason: null,
  partial: false,
  toolStatuses: [
    { tool: "inhouse", status: "ok", errorCount: 0 },
    { tool: "semgrep", status: "ok", errorCount: 0 },
  ],
  findings: [
    {
      id: "s1",
      ruleId: "extrace.s3.embedded_native_binary",
      title: "Embedded native binary",
      description: "Ships native binaries.",
      severity: "medium",
      severityLabel: "Medium",
      confidence: "high",
      confidenceLabel: "High",
      evidenceCount: 11,
    },
    {
      id: "sg1",
      ruleId: "extrace.sg.child_process",
      title: "child_process spawn",
      description: "Spawns a child process.",
      severity: "high",
      severityLabel: "High",
      confidence: "high",
      confidenceLabel: "High",
      evidenceCount: 1,
    },
  ],
};

describe("buildRuleMatrix — dynamic", () => {
  const matrix = buildRuleMatrix(makeReport({ detection: DETECTION }));
  const cells = matrix.dynamic.flatMap((group) => group.cells);

  it("emits one cell per executed rule with its live status", () => {
    expect(cells).toHaveLength(3);
    expect(matrix.counts.dynamicFired).toBe(1);
    expect(matrix.counts.dynamicTotal).toBe(3);
  });

  it("enriches a fired rule from its finding (severity + MITRE techniques + evidence)", () => {
    const a1 = cells.find((cell) => cell.ruleId.endsWith("a1.credential_read_then_network"));
    expect(a1?.status).toBe("fired");
    expect(a1?.severity).toBe("critical");
    expect(a1?.techniques).toEqual(["T1555", "T1041"]);
    expect(a1?.detail?.evidence).toContain("POST evil.example");
    expect(a1?.detail?.mitigation).toBe("Block the egress.");
  });

  it("labels a silent rule from the catalog and surfaces error detail", () => {
    const a2 = cells.find((cell) => cell.status === "silent");
    expect(a2?.techniques).toEqual(["T1496"]);
    const a3 = cells.find((cell) => cell.status === "error");
    expect(a3?.detail?.description).toContain("rule blew up");
  });
});

describe("buildRuleMatrix — static", () => {
  const matrix = buildRuleMatrix(makeReport({ staticReport: STATIC_REPORT }));
  const cells = matrix.static.flatMap((group) => group.cells);

  it("renders the in-house catalog universe plus fired external tool rules", () => {
    expect(matrix.hasStatic).toBe(true);
    expect(cells).toHaveLength(catalogRuleIds("static").length + 1);
    expect(matrix.counts.staticFired).toBe(2);
    expect(matrix.toolCells).toHaveLength(2);
  });

  it("marks a catalog rule fired by finding membership", () => {
    const native = cells.find((cell) => cell.ruleId === "extrace.s3.embedded_native_binary");
    expect(native?.status).toBe("fired");
    expect(native?.inCatalog).toBe(true);
    expect(native?.detail?.evidenceCount).toBe(11);
  });

  it("marks a catalog rule silent by exclusion", () => {
    const wildcard = cells.find((cell) => cell.ruleId === "extrace.s1.activation_wildcard");
    expect(wildcard?.status).toBe("silent");
  });

  it("surfaces a fired non-catalog (Semgrep) rule", () => {
    const sg = cells.find((cell) => cell.ruleId === "extrace.sg.child_process");
    expect(sg?.status).toBe("fired");
    expect(sg?.inCatalog).toBe(false);
  });
});

describe("buildRuleMatrix — empty", () => {
  it("reports no static when the report has none", () => {
    const matrix = buildRuleMatrix(makeReport({}));
    expect(matrix.hasStatic).toBe(false);
    expect(matrix.static).toHaveLength(0);
    expect(matrix.toolCells).toHaveLength(0);
    expect(matrix.dynamic).toHaveLength(0);
  });
});

describe("ruleCatalog drift guard", () => {
  // Every rule the engines can emit must have catalog metadata so a *silent*
  // cell still renders a meaningful label. Mirrors packages/analysis_engine/rules
  // and static_runtime/rules; update the catalog when a rule is added/renamed.
  it("covers all known engine rule ids", () => {
    const dynamic = new Set(catalogRuleIds("dynamic"));
    for (const id of [
      "extrace.a1.credential_read_then_network",
      "extrace.a2.startup_network_beacon",
      "extrace.a3.typosquat",
      "extrace.a4.workspace_exfil",
      "extrace.a5.workspace_file_tamper",
      "extrace.a6.startup_ui_prompt",
      "extrace.a7.blacklisted_domain",
    ]) {
      expect(dynamic.has(id)).toBe(true);
    }

    const staticIds = new Set(catalogRuleIds("static"));
    for (const id of [
      "extrace.s1.activation_wildcard",
      "extrace.s1.suspicious_capabilities",
      "extrace.s1.generic_publisher",
      "extrace.s2.typosquat",
      "extrace.s3.embedded_native_binary",
      "extrace.s3.unusual_file_signature",
      "extrace.s4.blacklisted_domain",
      "extrace.s5.suspicious_network_endpoint",
      "extrace.s6.obfuscation_indicators",
      "extrace.s7.hardcoded_secret",
      "extrace.s8.exfil_webhook",
      "extrace.s9.crypto_address_scan",
      "extrace.s10.reverse_shell",
      "extrace.s11.download_cradle",
      "extrace.s12.invisible_unicode_run",
      "extrace.s13.native_node_loader",
      "extrace.s14.globalstate_dormancy",
      "extrace.s15.path_traversal_server",
      "extrace.s16.cross_extension_tamper",
      "extrace.s17.credential_exfil",
      "extrace.s18.download_exec_dropper",
      "extrace.s19.stylesheet_inline_js",
      "extrace.s19.stylesheet_nonstandard_scheme",
      "extrace.s19.stylesheet_css_exfil",
      "extrace.s20.rmm_remote_access",
    ]) {
      expect(staticIds.has(id)).toBe(true);
    }
  });

  it("gives the rules added this branch a stream + a rich detail paragraph", () => {
    const cases: Array<[string, "static" | "dynamic"]> = [
      ["extrace.s8.exfil_webhook", "static"],
      ["extrace.s9.crypto_address_scan", "static"],
      ["extrace.s12.invisible_unicode_run", "static"],
      ["extrace.s13.native_node_loader", "static"],
      ["extrace.s14.globalstate_dormancy", "static"],
      ["extrace.s15.path_traversal_server", "static"],
      ["extrace.s16.cross_extension_tamper", "static"],
      ["extrace.s17.credential_exfil", "static"],
      ["extrace.s18.download_exec_dropper", "static"],
      ["extrace.s19.stylesheet_inline_js", "static"],
      ["extrace.s19.stylesheet_nonstandard_scheme", "static"],
      ["extrace.s19.stylesheet_css_exfil", "static"],
      ["extrace.s20.rmm_remote_access", "static"],
      ["extrace.a5.workspace_file_tamper", "dynamic"],
    ];
    for (const [id, stream] of cases) {
      const entry = ruleCatalogEntry(id);
      expect(entry, id).toBeDefined();
      expect(entry?.stream).toBe(stream);
      // detail is the richer description rendered in the rule dialog / expanded row.
      expect((entry?.detail ?? "").length).toBeGreaterThan(40);
    }
  });

  it("pins extrace.s1.activation_wildcard at HIGH (raised from LOW this branch)", () => {
    expect(ruleCatalogEntry("extrace.s1.activation_wildcard")?.severity).toBe("high");
  });
});
