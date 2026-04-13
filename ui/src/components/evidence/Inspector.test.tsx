import { render, screen } from "@testing-library/react";
import { Inspector } from "./Inspector";
import type { EvidenceInspectorView, RuleDraftView } from "../../lib/types/view-models";

vi.mock("../../lib/charts/core", () => ({
  ReactECharts: () => <div data-testid="chart" />,
}));

const inspector: EvidenceInspectorView = {
  event: {
    eventId: "file-1",
    kind: "file",
    kindLabel: "File",
    timestamp: "2026-04-13T10:00:05Z",
    relTimeS: 5,
    collector: "strace",
    collectorLabel: "Strace",
    actor: "extension",
    actorLabel: "Extension",
    scenarioName: "credential probe",
    scenarioLabel: "credential probe",
    extensionId: "publisher.tool",
    activationEvent: "onStartupFinished",
    operation: "read",
    protocol: "",
    host: "",
    path: "/workspace/.env",
    destinationIp: "",
    destinationPort: null,
    sensitive: true,
    summary: "Sensitive file read",
    summaryDisplay: "Sensitive file read",
    artifact: "/workspace/.env",
    artifactShort: "/workspace/.env",
    detail: "read",
    rawContext: {},
    timestampDisplay: "10:00:05.000",
  },
  outgoing: [],
  incoming: [],
  related: [
    {
      fromEventId: "file-1",
      toEventId: "activation-1",
      linkType: "candidate_owner",
      linkLabel: "Candidate Owner",
      confidence: 0.61,
      confidencePct: 61,
      confidenceLabel: "Medium",
      reason: "Temporal proximity to extension activation.",
      direction: "outgoing",
      peerEvent: {
        eventId: "activation-1",
        kind: "activation",
        kindLabel: "Activation",
        timestamp: "2026-04-13T10:00:03Z",
        relTimeS: 3,
        collector: "log",
        collectorLabel: "Log",
        actor: "extension",
        actorLabel: "Extension",
        scenarioName: "credential probe",
        scenarioLabel: "credential probe",
        extensionId: "publisher.tool",
        activationEvent: "onStartupFinished",
        operation: "",
        protocol: "",
        host: "",
        path: "",
        destinationIp: "",
        destinationPort: null,
        sensitive: false,
        summary: "Extension activated",
        summaryDisplay: "Extension activated",
        artifact: "publisher.tool",
        artifactShort: "publisher.tool",
        detail: "onStartupFinished",
        rawContext: {},
        timestampDisplay: "10:00:03.000",
      },
    },
  ],
};

const ruleDraft: RuleDraftView = {
  title: "File Watch: /workspace/.env",
  severity: "high",
  confidence: 0.61,
  scope: { kind: "file" },
  conditions: [{ field: "path", operator: "contains", value: "/workspace/.env" }],
  rationale: "Sensitive file read",
  labels: ["file", "strace"],
};

describe("Inspector", () => {
  it("renders provenance metadata without the repeated reason chain", () => {
    render(
      <Inspector
        activeTab="provenance"
        inspector={inspector}
        onTabChange={() => undefined}
        ruleDraft={ruleDraft}
      />,
    );

    expect(screen.getByRole("heading", { name: "Provenance" })).toBeInTheDocument();
    expect(screen.getByText("Sensitive file read")).toBeInTheDocument();
    expect(screen.getByText("Link Status")).toBeInTheDocument();
    expect(screen.getByText(/Relations tab/u)).toBeInTheDocument();
  });

  it("renders the relations graph tab", () => {
    render(
      <Inspector
        activeTab="relations"
        inspector={inspector}
        onTabChange={() => undefined}
        ruleDraft={ruleDraft}
      />,
    );

    expect(screen.getByRole("heading", { name: "Relations" })).toBeInTheDocument();
    expect(screen.getByText("Connection Summary")).toBeInTheDocument();
    expect(screen.getByTestId("chart")).toBeInTheDocument();
  });
});
