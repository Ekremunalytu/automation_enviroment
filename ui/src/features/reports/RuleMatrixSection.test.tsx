import { fireEvent, render, screen } from "@testing-library/react";

import type {
  ActivationReportView,
  DetectionReportView,
  StaticReportView,
} from "../../lib/types/view-models";
import { RuleMatrixSection } from "./RuleMatrixSection";

function makeReport(partial: {
  detection?: DetectionReportView | null;
  staticReport?: StaticReportView | null;
}): ActivationReportView {
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
  ],
  findings: [
    {
      id: "f1",
      ruleId: "extrace.a1.credential_read_then_network",
      ruleVersion: "1.0.0",
      ruleLifecycle: "production",
      title: "Credential read then network",
      description: "Secret read followed by an outbound request.",
      categories: ["attack.T1555", "attack.T1041"],
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
  toolStatuses: [{ tool: "inhouse", status: "ok", errorCount: 0 }],
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
  ],
};

describe("RuleMatrixSection", () => {
  it("renders both bands and opens a detail dialog for a fired cell", () => {
    render(<RuleMatrixSection report={makeReport({ detection: DETECTION, staticReport: STATIC_REPORT })} />);

    // Both bands present.
    expect(screen.getByText(/Dynamic · behavioral/i)).toBeTruthy();
    expect(screen.getByText(/Static · pre-check/i)).toBeTruthy();

    // Dynamic fired + silent cells, and a fired static cell, render as buttons.
    expect(screen.getByRole("button", { name: /Credential read.*Fired/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Startup network beacon.*Silent/i })).toBeTruthy();
    const staticCell = screen.getByRole("button", { name: /Embedded native binary.*Fired/i });
    expect(staticCell).toBeTruthy();

    // Clicking the cell opens the detail dialog with the rule id + finding text.
    fireEvent.click(staticCell);
    const dialog = screen.getByRole("dialog");
    expect(dialog.textContent).toContain("extrace.s3.embedded_native_binary");
    expect(dialog.textContent).toContain("T1105");
  });

  it("shows the empty state when the report has no static pre-check", () => {
    render(<RuleMatrixSection report={makeReport({ detection: DETECTION })} />);
    expect(screen.getByText(/No static pre-check for this run/i)).toBeTruthy();
    // Dynamic band still renders.
    expect(screen.getByRole("button", { name: /Credential read.*Fired/i })).toBeTruthy();
  });
});
