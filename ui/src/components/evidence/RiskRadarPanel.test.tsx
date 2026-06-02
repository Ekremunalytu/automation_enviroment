import { render, screen } from "@testing-library/react";
import { RiskRadarPanel } from "./RiskRadarPanel";
import type { RiskRadarAxisView } from "../../lib/adapters/report";

function axis(overrides: Partial<RiskRadarAxisView> & { key: RiskRadarAxisView["key"]; label: string }): RiskRadarAxisView {
  return {
    id: overrides.key,
    note: "note",
    score: 0,
    benchmark: 30,
    signalCount: 0,
    trend: [0, 0, 0, 0, 0, 0],
    ...overrides,
  };
}

const axes: RiskRadarAxisView[] = [
  axis({ key: "exfil", label: "Exfiltration", score: 80, signalCount: 2, trend: [0, 0, 20, 40, 60, 80] }),
  axis({ key: "threat", label: "Threat surface", score: 0, signalCount: 0 }),
  axis({ key: "defense", label: "Defense gap", score: 25, signalCount: 0, trend: [4, 8, 12, 16, 20, 25] }),
];

describe("RiskRadarPanel", () => {
  it("renders real axis scores and detection counts", () => {
    render(<RiskRadarPanel axes={axes} compositeScore={42} />);

    expect(screen.getByText("Exfiltration")).toBeInTheDocument();
    expect(screen.getByText("Threat surface")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument(); // composite gauge value

    // Detection counts are surfaced (with a descriptive tooltip when > 0).
    expect(screen.getByTitle(/2 detection signals fired/i)).toHaveTextContent("2");
    // An axis with no detections reads zero, not a fabricated value.
    expect(screen.getAllByTitle(/No detection signals fired/i).length).toBeGreaterThan(0);
  });

  it("does not render the old fabricated framing", () => {
    render(<RiskRadarPanel axes={axes} compositeScore={42} />);

    // The hardcoded "+N vs baseline" line and "population benchmark" label
    // were removed; the reference is the real run average.
    expect(screen.queryByText(/vs baseline/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/population benchmark/i)).not.toBeInTheDocument();
    expect(screen.getByText(/run average/i)).toBeInTheDocument();
    expect(screen.getByText(/vs run avg/i)).toBeInTheDocument();
  });
});
