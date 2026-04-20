import { render } from "@testing-library/react";
import { DetectionPanel } from "../DetectionPanel";
import type { DetectionReportView } from "../../../lib/types/view-models";

function buildDetection(verdict: DetectionReportView["verdict"]): DetectionReportView {
  return {
    verdict,
    verdictLabel: verdict.replaceAll("_", " "),
    verdictRationale: `Rationale for ${verdict}`,
    findings: verdict === "clean"
      ? []
      : [
          {
            id: `finding-${verdict}`,
            ruleId: "extrace.a1.credential_read_then_network",
            ruleVersion: "1.0.0",
            ruleLifecycle: "production",
            title: "Synthetic detection finding",
            description: "Synthetic description",
            categories: ["attack.T1555"],
            severity: verdict === "malicious" ? "critical" : "medium",
            severityLabel: verdict === "malicious" ? "Critical" : "Medium",
            confidence: verdict === "malicious" ? "high" : "medium",
            confidenceLabel: verdict === "malicious" ? "High" : "Medium",
            adversaryClass: "A1",
            evidence: [{ eventId: "event-1", type: "filesystem_read", summary: "Read file" }],
            mitigationHint: "Review extension behavior.",
          },
        ],
  };
}

describe("DetectionPanel", () => {
  it.each([
    "malicious",
    "suspicious",
    "clean_with_notes",
    "clean",
    "inconclusive",
  ] as const)("renders %s verdict state", (verdict) => {
    const { container } = render(
      <DetectionPanel detection={buildDetection(verdict)} onShowEvidence={vi.fn()} />,
    );

    expect(container).toMatchSnapshot();
  });
});
