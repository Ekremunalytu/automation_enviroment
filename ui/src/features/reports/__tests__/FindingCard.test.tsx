import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
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

function LocationDisplay() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}{location.search}</div>;
}

describe("FindingCard", () => {
  it("links to the rules registry for the finding rule", () => {
    render(
      <MemoryRouter initialEntries={["/reports"]}>
        <Routes>
          <Route
            path="*"
            element={
              <>
                <FindingCard finding={finding} />
                <LocationDisplay />
              </>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: /workspace file read followed/iu }));

    expect(screen.getByTestId("location").textContent).toBe(
      "/rules?rule=extrace.a4.workspace_exfil&from=reports",
    );
  });
});
