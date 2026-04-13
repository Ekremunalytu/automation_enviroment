import { buildRuleDraft, toRuleJson, toRuleYaml } from "./draft";
import type { EvidenceInspectorView } from "../types/view-models";

const inspector: EvidenceInspectorView = {
  event: {
    eventId: "network-1",
    kind: "network",
    kindLabel: "Network",
    timestamp: "2026-04-13T10:00:02Z",
    relTimeS: 2,
    collector: "tshark",
    collectorLabel: "Tshark",
    actor: "extension",
    actorLabel: "Extension",
    scenarioName: "sandbox analysis",
    scenarioLabel: "sandbox analysis",
    extensionId: "publisher.tool",
    activationEvent: "",
    operation: "",
    protocol: "https",
    host: "api.example.com",
    path: "/collect",
    destinationIp: "1.2.3.4",
    destinationPort: 443,
    sensitive: false,
    summary: "Outbound request",
    summaryDisplay: "Outbound request",
    artifact: "/collect",
    artifactShort: "/collect",
    detail: "https",
    rawContext: {},
    timestampDisplay: "10:00:02.000",
  },
  outgoing: [],
  incoming: [],
  related: [
    {
      fromEventId: "network-1",
      toEventId: "scenario-1",
      linkType: "occurred_in_scenario",
      linkLabel: "Occurred In Scenario",
      confidence: 0.92,
      confidencePct: 92,
      confidenceLabel: "High",
      reason: "Observed during sandbox analysis.",
      direction: "outgoing",
    },
  ],
};

describe("buildRuleDraft", () => {
  it("derives scope, conditions, and exports from the focused event", () => {
    const rule = buildRuleDraft(inspector);

    expect(rule).not.toBeNull();
    expect(rule?.conditions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ field: "kind", value: "network" }),
        expect.objectContaining({ field: "host", value: "api.example.com" }),
        expect.objectContaining({ field: "destination_port", value: 443 }),
      ]),
    );
    expect(rule?.scope).toMatchObject({
      kind: "network",
      actor: "extension",
      collector: "tshark",
      extension_id: "publisher.tool",
      scenario_name: "sandbox analysis",
    });
    expect(toRuleJson(rule!)).toContain("\"title\"");
    expect(toRuleYaml(rule!)).toContain("severity:");
  });
});
