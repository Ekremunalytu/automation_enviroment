import { adaptReport, getInspectorView } from "./report";
import type { ActivationReportDto } from "../types/contracts";

describe("adaptReport", () => {
  it("prefers canonical evidence events and links", () => {
    const dto: ActivationReportDto = {
      report_version: 2,
      target_extension_expected: "ms.test",
      verdict: {},
      scenario_traces: [],
      network_events: [],
      file_events: [],
      target_extension_observed: true,
      trigger_plan_applied: true,
      verification_gap: 1,
      run_quality: "medium",
      automation_health: {
        status: "degraded",
        reasons: ["verification_gap_present"],
        trigger_requested: true,
        trigger_loaded: true,
        trigger_applied: true,
        extension_host_log_present: true,
        extension_host_output_present: true,
        target_stream_present: true,
        target_activation_count: 1,
        failed_scenarios: [],
      },
      log_health: {
        extension_host_log_found: true,
        extension_host_output_present: true,
        target_extension_log_entries: 1,
        total_activation_entries: 1,
      },
      attribution_summary: {
        target_activation_count: 1,
        strong_target_file_event_count: 0,
        strong_target_network_event_count: 1,
        correlated_only_event_count: 0,
      },
      risk_signals: [
        {
          signal_id: "background_outbound_network",
          category: "background_outbound_network",
          severity: "high",
          confidence: 0.84,
          evidence_event_ids: ["network-1"],
          summary: "Network activity followed a startup activation.",
        },
      ],
      risk_summary: {
        total_signals: 1,
        high: 1,
        medium: 0,
        low: 0,
        critical: 0,
        categories: ["background_outbound_network"],
      },
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
      coverage_summary: {
        covered: 4,
        partial: 2,
        missing: 1,
        missing_capabilities: ["chat"],
      },
      coverage_matrix: [
        {
          capability: "commands",
          status: "covered",
          track: "official",
          source: "official_activation_track",
          selected_scenarios: ["coding_session"],
          supported_scenarios: ["coding_session", "refactor_workflow"],
        },
      ],
      coverage_tracks: {
        official: {
          source: "official_activation_track",
          selected_scenarios: ["coding_session"],
          summary: {
            covered: 4,
            partial: 2,
            missing: 1,
            attempted: 2,
            verified: 1,
            missing_capabilities: ["chat"],
            attempted_capabilities: ["commands", "workspace_fs"],
            verified_capabilities: ["workspace_fs"],
          },
          matrix: [
            {
              capability: "commands",
              status: "covered",
              track: "official",
              source: "official_activation_track",
              selected_scenarios: ["coding_session"],
              supported_scenarios: ["coding_session", "refactor_workflow"],
            },
          ],
        },
        heuristic: {
          source: "heuristic_workflow_track",
          selected_scenarios: ["search_workflow"],
          summary: {
            covered: 1,
            partial: 0,
            missing: 0,
            attempted: 1,
            verified: 0,
            missing_capabilities: [],
            attempted_capabilities: ["search_views"],
            verified_capabilities: [],
          },
          matrix: [
            {
              capability: "search_views",
              status: "covered",
              track: "heuristic",
              source: "heuristic_workflow_track",
              selected_scenarios: ["search_workflow"],
              supported_scenarios: ["search_workflow"],
            },
          ],
        },
      },
      log_streams: {
        target_extension_host: [
          {
            timestamp: "2026-04-13T10:00:01Z",
            rel_time_s: 1,
            stream: "target_extension_host",
            kind: "activation",
            message: "Activated ms.test via onCommand:test",
            extension_id: "ms.test",
            activation_event: "onCommand:test",
            scenario_name: "sandbox analysis",
            status: "completed",
            is_target_extension: true,
          },
        ],
        automation: [
          {
            timestamp: "2026-04-13T10:00:00Z",
            rel_time_s: 0.1,
            stream: "automation",
            kind: "scenario",
            message: "Started scenario coding session",
            scenario_name: "coding_session",
            status: "running",
          },
        ],
      },
    };

    const report = adaptReport(dto, "latest");

    expect(report.reportVersion).toBe(2);
    expect(report.metadataFilename).toBe("activation_report_demo.json");
    expect(report.evidence).toHaveLength(1);
    expect(report.evidence[0]?.artifact).toBe("/collect");
    expect(report.evidenceLinks[0]?.linkType).toBe("occurred_in_scenario");
    expect(report.coverageSummary.missingCapabilities).toEqual(["chat"]);
    expect(report.coverageMatrix[0]?.capability).toBe("commands");
    expect(report.coverageTracks.official.summary.attempted).toBe(2);
    expect(report.coverageTracks.heuristic.summary.attemptedCapabilities).toEqual([
      "search_views",
    ]);
    expect(report.logStreams.targetExtensionHost[0]?.extensionId).toBe("ms.test");
    expect(report.logStreams.automation[0]?.kind).toBe("scenario");
    expect(report.summary.targetExtensionObserved).toBe(true);
    expect(report.summary.runQuality).toBe("medium");
    expect(report.summary.automationHealthStatus).toBe("degraded");
    expect(report.summary.triggerLoaded).toBe(true);
    expect(report.riskSignals[0]?.category).toBe("background_outbound_network");
    expect(report.riskSummary.totalSignals).toBe(1);
  });

  it("falls back to legacy activation/file/scenario arrays", () => {
    const dto = {
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
    } as unknown as ActivationReportDto;

    const report = adaptReport(dto, "legacy");
    const inspector = getInspectorView(report, "file-0001");

    expect(report.reportVersion).toBe(1);
    expect(report.evidence.map((event) => event.eventId)).toEqual([
      "file-0001",
      "activation-0001",
      "scenario-0001",
    ]);
    expect(report.summary.automationHealthStatus).toBe("inconclusive");
    expect(report.summary.automationHealthReasons).toEqual([
      "legacy_report_missing_health_block",
    ]);
    expect(report.evidenceLinks.map((link) => link.linkType)).toEqual(
      expect.arrayContaining(["occurred_in_scenario", "candidate_owner"]),
    );
    expect(inspector?.related).toHaveLength(2);
  });

  it("surfaces skipped scenario details and process events", () => {
    const dto: ActivationReportDto = {
      report_version: 2,
      target_extension_expected: "ms.test",
      verdict: {},
      summary: {
        skipped_scenarios: ["debug_session"],
      },
      scenario_traces: [
        {
          name: "coding_session",
          started_at: 1713002400,
          ended_at: 1713002404,
          status: "completed",
        },
      ],
      skipped_scenarios: [
        {
          name: "debug_session",
          reason_code: "unsupported_activation_surface",
          detail: "family not supported by runtime",
        },
      ],
      evidence_events: [],
      network_events: [],
      file_events: [],
      process_events: [
        {
          timestamp: "2026-04-13T10:00:03Z",
          rel_time_s: 3,
          pid: 4123,
          ppid: 4010,
          operation: "execve",
          command: "/usr/bin/python3",
          arguments_preview: "--child --flag",
          cwd: "/workspace",
          related_extension_id: "ms.test",
          related_activation_event: "onCommand:test",
          attribution_status: "target_attributed",
          attribution_basis: "child process observed in target extension host tree",
          attribution_confidence: 0.92,
          is_target_extension_event: true,
          summary: "Spawned python helper",
        },
      ],
      automation_health: {
        status: "degraded",
        reasons: ["skipped_scenarios_present"],
        trigger_requested: true,
        trigger_loaded: true,
        trigger_applied: true,
        extension_host_log_present: true,
        extension_host_output_present: true,
        target_stream_present: true,
        target_activation_count: 1,
        failed_scenarios: [],
        skipped_scenarios: ["debug_session"],
      },
      log_streams: {
        automation: [],
      },
      target_extension_observed: true,
      trigger_plan_applied: true,
      verification_gap: 0,
      run_quality: "low",
    };

    const report = adaptReport(dto, "latest");
    const process = report.evidence.find((event) => event.kind === "process");

    expect(report.summary.skippedScenarios).toEqual(["debug_session"]);
    expect(report.summary.skippedScenarioDetails).toEqual([
      {
        name: "debug_session",
        reasonCode: "unsupported_activation_surface",
        detail: "family not supported by runtime",
      },
    ]);
    expect(process?.artifact).toBe("ms.test");
    expect(process?.rawContext).toMatchObject({
      pid: 4123,
      ppid: 4010,
      command: "/usr/bin/python3",
      arguments_preview: "--child --flag",
      cwd: "/workspace",
    });
  });
});
