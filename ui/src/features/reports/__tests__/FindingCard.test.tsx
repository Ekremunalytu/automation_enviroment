import { fireEvent, render, screen } from "@testing-library/react";
import { FindingCard } from "../FindingCard";
import type { DetectionFindingView } from "../../../lib/types/view-models";

const finding: DetectionFindingView = {
  id: "finding-1",
  ruleId: "extrace.a4.workspace_exfil",
  ruleVersion: "1.0.0",
  ruleLifecycle: "production",
  title: "Workspace file read followed by outbound transfer",
  description: "Synthetic finding for evidence deep-link coverage.",
  categories: ["attack.T1041"],
  severity: "high",
  severityLabel: "High",
  confidence: "medium",
  confidenceLabel: "Medium",
  adversaryClass: "A4",
  evidence: [
    { eventId: "file-123", type: "filesystem_read", summary: "Read /workspace/.env" },
  ],
  mitigationHint: "Block the extension.",
};

describe("FindingCard", () => {
  it("emits the first evidence event id when the evidence button is clicked", () => {
    const onShowEvidence = vi.fn();

    render(<FindingCard finding={finding} onShowEvidence={onShowEvidence} />);
    fireEvent.click(screen.getByRole("button", { name: "1 evidence" }));

    expect(onShowEvidence).toHaveBeenCalledWith("file-123");
  });
});
