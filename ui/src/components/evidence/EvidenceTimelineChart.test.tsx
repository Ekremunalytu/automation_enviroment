import { render, screen } from "@testing-library/react";
import { EvidenceTimelineChart } from "./EvidenceTimelineChart";
import type { EvidenceEventView } from "../../lib/types/view-models";

vi.mock("../../lib/charts/core", () => ({
  ReactECharts: () => <div data-testid="chart" />,
}));

const events: EvidenceEventView[] = [
  {
    eventId: "activation-1",
    kind: "activation",
    kindLabel: "Activation",
    timestamp: "2026-04-13T10:00:00Z",
    relTimeS: 1,
    collector: "log",
    collectorLabel: "Log",
    actor: "extension",
    actorLabel: "Extension",
    scenarioName: "bootstrap",
    scenarioLabel: "bootstrap",
    extensionId: "publisher.tool",
    activationEvent: "onStartupFinished",
    operation: "",
    protocol: "",
    host: "",
    path: "",
    destinationIp: "",
    destinationPort: null,
    attributionStatus: "target_attributed",
    attributionStatusLabel: "Target Attributed",
    attributionBasis: "",
    attributionConfidence: 1,
    attributionConfidencePct: 100,
    isTargetExtensionEvent: true,
    noiseReason: "",
    artifactClass: "",
    sensitive: false,
    summary: "Extension activated",
    summaryDisplay: "Extension activated",
    artifact: "publisher.tool",
    artifactShort: "publisher.tool",
    detail: "onStartupFinished",
    rawContext: {},
    timestampDisplay: "10:00:00.000",
  },
  {
    eventId: "file-1",
    kind: "file",
    kindLabel: "File",
    timestamp: "2026-04-13T10:00:05Z",
    relTimeS: 5,
    collector: "strace",
    collectorLabel: "Strace",
    actor: "extension",
    actorLabel: "Extension",
    scenarioName: "bootstrap",
    scenarioLabel: "bootstrap",
    extensionId: "publisher.tool",
    activationEvent: "",
    operation: "read",
    protocol: "",
    host: "",
    path: "/workspace/.env",
    destinationIp: "",
    destinationPort: null,
    attributionStatus: "near_target_activation",
    attributionStatusLabel: "Correlated Only",
    attributionBasis: "",
    attributionConfidence: 0.62,
    attributionConfidencePct: 62,
    isTargetExtensionEvent: false,
    noiseReason: "",
    artifactClass: "workspace_runtime",
    sensitive: true,
    summary: "Sensitive file read",
    summaryDisplay: "Sensitive file read",
    artifact: "/workspace/.env",
    artifactShort: "/workspace/.env",
    detail: "read",
    rawContext: {},
    timestampDisplay: "10:00:05.000",
  },
];

describe("EvidenceTimelineChart", () => {
  it("exposes an aria summary for screen readers", () => {
    render(<EvidenceTimelineChart events={events} onSelect={() => undefined} />);

    expect(
      screen.getByRole("img", {
        name: "Evidence timeline with 2 total events: 1 activation event, 1 file event.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("chart")).toBeInTheDocument();
  });
});
