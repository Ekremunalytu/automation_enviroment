import { adaptReport, getInspectorView } from "./report";
import type { ActivationReportDto } from "../types/contracts";

describe("adaptReport", () => {
  it("prefers canonical evidence events and links", () => {
    const dto: ActivationReportDto = {
      report_version: 2,
      _metadata: { filename: "activation_report_demo.json" },
      summary: {
        total_activated: 1,
        scenarios_run: ["sandbox analysis"],
        monitoring_duration_s: 12,
        network_events: 1,
        file_events: 0,
      },
      evidence_events: [
        {
          event_id: "network-1",
          kind: "network",
          timestamp: "2026-04-13T10:00:00Z",
          rel_time_s: 2.3,
          collector: "tshark",
          actor: "extension",
          scenario_name: "sandbox analysis",
          extension_id: "ms.test",
          protocol: "https",
          host: "api.example.com",
          path: "/collect",
          destination_ip: "1.2.3.4",
          destination_port: 443,
          summary: "Outbound request to api.example.com",
        },
      ],
      evidence_links: [
        {
          from_event_id: "network-1",
          to_event_id: "scenario-1",
          link_type: "occurred_in_scenario",
          confidence: 1,
          reason: "Observed during sandbox analysis.",
        },
      ],
    };

    const report = adaptReport(dto, "latest");

    expect(report.reportVersion).toBe(2);
    expect(report.metadataFilename).toBe("activation_report_demo.json");
    expect(report.evidence).toHaveLength(1);
    expect(report.evidence[0]?.artifact).toBe("/collect");
    expect(report.evidenceLinks[0]?.linkType).toBe("occurred_in_scenario");
  });

  it("falls back to legacy activation/file/scenario arrays", () => {
    const dto: ActivationReportDto = {
      summary: {
        total_activated: 1,
        monitoring_duration_s: 9,
      },
      activated: [
        {
          extension_id: "publisher.tool",
          activation_event: "onStartupFinished",
          timestamp: "2026-04-13T10:00:00Z",
          source: "log",
        },
      ],
      file_events: [
        {
          timestamp: "2026-04-13T10:00:02Z",
          rel_time_s: 2,
          operation: "read",
          path: "/workspace/secrets/.env",
          observer: "inotify",
          source: "extension",
          scenario_name: "credential probe",
          related_extension_id: "publisher.tool",
          sensitive: true,
          summary: "Sensitive file read",
        },
      ],
      scenario_traces: [
        {
          name: "credential probe",
          started_at: 1713002400,
          ended_at: 1713002403,
          status: "completed",
        },
      ],
    };

    const report = adaptReport(dto, "legacy");
    const inspector = getInspectorView(report, "file-0001");

    expect(report.reportVersion).toBe(1);
    expect(report.evidence.map((event) => event.eventId)).toEqual([
      "file-0001",
      "activation-0001",
      "scenario-0001",
    ]);
    expect(report.evidenceLinks.map((link) => link.linkType)).toEqual(
      expect.arrayContaining(["occurred_in_scenario", "candidate_owner"]),
    );
    expect(inspector?.related).toHaveLength(2);
  });
});
