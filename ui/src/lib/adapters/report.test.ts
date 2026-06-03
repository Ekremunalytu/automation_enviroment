import {
  adaptBundle,
  adaptReport,
  buildInteractionGraph,
  buildRiskRadar,
  buildRiskRadarAxes,
  getInspectorView,
} from "./report";
import type { ActivationReportDto, ReportBundleDto } from "../types/contracts";

describe("adaptReport", () => {
  it("prefers canonical evidence events and links", () => {
    const dto: ActivationReportDto = {
      report_version: 2,
      target_extension_expected: "ms.test",
      signal_summary: {},
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
      signal_summary: {},
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

describe("buildInteractionGraph", () => {
  it("groups evidence into network / fs / activation buckets and marks the result synthetic", () => {
    const dto: ActivationReportDto = {
      report_version: 2,
      target_extension_expected: "ms.test",
      signal_summary: {},
      scenario_traces: [],
      network_events: [],
      file_events: [],
      target_extension_observed: true,
      trigger_plan_applied: true,
      verification_gap: 0,
      run_quality: "low",
      automation_health: {
        status: "healthy",
        reasons: [],
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
        strong_target_file_event_count: 1,
        strong_target_network_event_count: 1,
        correlated_only_event_count: 0,
      },
      risk_signals: [],
      risk_summary: {
        total_signals: 0,
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        categories: [],
      },
      _metadata: { filename: "graph_demo.json" },
      summary: { network_events: 1, file_events: 1 },
      evidence_events: [
        {
          event_id: "network-1",
          kind: "network",
          timestamp: "2026-04-13T10:00:00Z",
          rel_time_s: 1,
          collector: "tshark",
          actor: "extension",
          extension_id: "ms.test",
          host: "api.example.com",
          path: "/collect",
          summary: "Outbound",
        },
        {
          event_id: "file-1",
          kind: "file",
          timestamp: "2026-04-13T10:00:01Z",
          rel_time_s: 2,
          collector: "strace",
          actor: "extension",
          extension_id: "ms.test",
          path: "/workspace/.env",
          operation: "read",
          sensitive: true,
          summary: "Sensitive read",
        },
        {
          event_id: "activation-1",
          kind: "activation",
          timestamp: "2026-04-13T10:00:02Z",
          rel_time_s: 0,
          collector: "log",
          actor: "extension",
          extension_id: "ms.test",
          activation_event: "onStartupFinished",
          summary: "Activated",
        },
      ],
      evidence_links: [],
      coverage_summary: { covered: 0, partial: 0, missing: 0, missing_capabilities: [] },
      coverage_matrix: [],
      coverage_tracks: {
        official: {
          source: "official_activation_track",
          selected_scenarios: [],
          summary: {
            covered: 0,
            partial: 0,
            missing: 0,
            attempted: 0,
            verified: 0,
            missing_capabilities: [],
            attempted_capabilities: [],
            verified_capabilities: [],
          },
          matrix: [],
        },
        heuristic: {
          source: "heuristic_workflow_track",
          selected_scenarios: [],
          summary: {
            covered: 0,
            partial: 0,
            missing: 0,
            attempted: 0,
            verified: 0,
            missing_capabilities: [],
            attempted_capabilities: [],
            verified_capabilities: [],
          },
          matrix: [],
        },
      },
      log_streams: { automation: [] },
    };

    const report = adaptReport(dto, "graph_demo.json");
    const graph = buildInteractionGraph(report);

    expect(graph._synthetic).toBe(true);
    const ids = graph.groups.map((group) => group.id);
    expect(ids).toEqual(expect.arrayContaining(["network", "fs", "activation"]));
    const network = graph.groups.find((group) => group.id === "network");
    expect(network?.children[0]?.label).toBe("api.example.com");
    const fs = graph.groups.find((group) => group.id === "fs");
    expect(fs?.children[0]?.risk).toBe("high");
  });

  it("returns no groups when the report has no evidence", () => {
    const dto: ActivationReportDto = {
      report_version: 2,
      target_extension_expected: "ms.test",
      signal_summary: {},
      scenario_traces: [],
      network_events: [],
      file_events: [],
      target_extension_observed: false,
      trigger_plan_applied: false,
      verification_gap: 0,
      run_quality: "low",
      automation_health: {
        status: "inconclusive",
        reasons: [],
        trigger_requested: false,
        trigger_loaded: false,
        trigger_applied: false,
        extension_host_log_present: false,
        extension_host_output_present: false,
        target_stream_present: false,
        target_activation_count: 0,
        failed_scenarios: [],
      },
      log_health: {
        extension_host_log_found: false,
        extension_host_output_present: false,
        target_extension_log_entries: 0,
        total_activation_entries: 0,
      },
      attribution_summary: {
        target_activation_count: 0,
        strong_target_file_event_count: 0,
        strong_target_network_event_count: 0,
        correlated_only_event_count: 0,
      },
      risk_signals: [],
      risk_summary: { total_signals: 0, critical: 0, high: 0, medium: 0, low: 0, categories: [] },
      _metadata: { filename: "empty.json" },
      summary: {},
      evidence_events: [],
      evidence_links: [],
      coverage_summary: { covered: 0, partial: 0, missing: 0, missing_capabilities: [] },
      coverage_matrix: [],
      coverage_tracks: {
        official: {
          source: "official_activation_track",
          selected_scenarios: [],
          summary: {
            covered: 0,
            partial: 0,
            missing: 0,
            attempted: 0,
            verified: 0,
            missing_capabilities: [],
            attempted_capabilities: [],
            verified_capabilities: [],
          },
          matrix: [],
        },
        heuristic: {
          source: "heuristic_workflow_track",
          selected_scenarios: [],
          summary: {
            covered: 0,
            partial: 0,
            missing: 0,
            attempted: 0,
            verified: 0,
            missing_capabilities: [],
            attempted_capabilities: [],
            verified_capabilities: [],
          },
          matrix: [],
        },
      },
      log_streams: { automation: [] },
    };

    const report = adaptReport(dto, "empty.json");
    expect(buildInteractionGraph(report).groups).toHaveLength(0);
  });
});

describe("buildRiskRadar", () => {
  it("emits 0-100 axis scores tagged synthetic", () => {
    const dto: ActivationReportDto = {
      report_version: 2,
      target_extension_expected: "ms.test",
      signal_summary: {},
      scenario_traces: [],
      network_events: [],
      file_events: [],
      target_extension_observed: true,
      trigger_plan_applied: true,
      verification_gap: 0,
      run_quality: "medium",
      automation_health: {
        status: "healthy",
        reasons: [],
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
        strong_target_file_event_count: 1,
        strong_target_network_event_count: 1,
        correlated_only_event_count: 0,
      },
      risk_signals: [
        {
          signal_id: "s1",
          category: "credential_or_secret_access",
          severity: "high",
          confidence: 0.9,
          evidence_event_ids: ["file-1"],
          summary: "Credential access",
        },
        {
          signal_id: "s2",
          category: "background_outbound_network",
          severity: "high",
          confidence: 0.8,
          evidence_event_ids: ["network-1"],
          summary: "Outbound network",
        },
      ],
      risk_summary: {
        total_signals: 2,
        critical: 0,
        high: 2,
        medium: 0,
        low: 0,
        categories: ["credential_or_secret_access", "background_outbound_network"],
      },
      _metadata: { filename: "radar_demo.json" },
      summary: {},
      evidence_events: [
        {
          event_id: "network-1",
          kind: "network",
          timestamp: "2026-04-13T10:00:00Z",
          rel_time_s: 1,
          collector: "tshark",
          actor: "extension",
          extension_id: "ms.test",
          host: "api.example.com",
          summary: "Outbound",
        },
        {
          event_id: "file-1",
          kind: "file",
          timestamp: "2026-04-13T10:00:01Z",
          rel_time_s: 2,
          collector: "strace",
          actor: "extension",
          extension_id: "ms.test",
          path: "/workspace/.env",
          operation: "read",
          sensitive: true,
          summary: "Sensitive read",
        },
      ],
      evidence_links: [],
      coverage_summary: { covered: 4, partial: 0, missing: 0, missing_capabilities: [] },
      coverage_matrix: [],
      coverage_tracks: {
        official: {
          source: "official_activation_track",
          selected_scenarios: [],
          summary: {
            covered: 4,
            partial: 2,
            missing: 0,
            attempted: 0,
            verified: 0,
            missing_capabilities: [],
            attempted_capabilities: [],
            verified_capabilities: [],
          },
          matrix: [],
        },
        heuristic: {
          source: "heuristic_workflow_track",
          selected_scenarios: [],
          summary: {
            covered: 0,
            partial: 0,
            missing: 0,
            attempted: 0,
            verified: 0,
            missing_capabilities: [],
            attempted_capabilities: [],
            verified_capabilities: [],
          },
          matrix: [],
        },
      },
      log_streams: { automation: [] },
    };

    const report = adaptReport(dto, "radar_demo.json");
    const radar = buildRiskRadar(report);

    expect(radar._synthetic).toBe(true);
    for (const axis of ["Threat", "Exfil", "Persistence", "Privesc", "Defense", "Resource"] as const) {
      expect(radar[axis]).toBeGreaterThanOrEqual(0);
      expect(radar[axis]).toBeLessThanOrEqual(100);
    }
    // Axes light up only from the real detection signals mapped to them.
    expect(radar.Threat).toBeGreaterThan(0); // credential_or_secret_access → threat
    expect(radar.Exfil).toBeGreaterThan(0); // background_outbound_network → exfil
    // No signal maps to these here, so they are honestly zero (not inflated).
    expect(radar.Persistence).toBe(0);
    expect(radar.Privesc).toBe(0);
    expect(radar.Resource).toBe(0);
    // Defense reflects real coverage shortfall (2 partial of 6 tracked).
    expect(radar.Defense).toBeGreaterThan(0);
  });
});

describe("buildRiskRadarAxes", () => {
  function radarDto(): ActivationReportDto {
    return {
      report_version: 2,
      target_extension_expected: "ms.test",
      signal_summary: {},
      scenario_traces: [],
      network_events: [],
      file_events: [],
      target_extension_observed: true,
      trigger_plan_applied: true,
      verification_gap: 0,
      run_quality: "medium",
      automation_health: {
        status: "healthy",
        reasons: [],
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
        strong_target_file_event_count: 1,
        strong_target_network_event_count: 1,
        correlated_only_event_count: 0,
      },
      risk_signals: [
        { signal_id: "n1", category: "background_outbound_network", severity: "high", confidence: 0.8, evidence_event_ids: ["network-1"], summary: "Outbound" },
        { signal_id: "c1", category: "credential_or_secret_access", severity: "high", confidence: 0.9, evidence_event_ids: ["file-1"], summary: "Credential" },
        { signal_id: "x1", category: "correlative_suspicious_activity", severity: "medium", confidence: 0.5, evidence_event_ids: ["process-1"], summary: "Correlated" },
      ],
      risk_summary: {
        total_signals: 3,
        critical: 0,
        high: 2,
        medium: 1,
        low: 0,
        categories: ["background_outbound_network", "credential_or_secret_access", "correlative_suspicious_activity"],
      },
      _metadata: { filename: "radar_axes_demo.json" },
      summary: {},
      evidence_events: [
        { event_id: "activation-1", kind: "activation", timestamp: "2026-04-13T10:00:00Z", rel_time_s: 0, collector: "host", actor: "extension", extension_id: "ms.test", summary: "Activated" },
        { event_id: "network-1", kind: "network", timestamp: "2026-04-13T10:00:01Z", rel_time_s: 1, collector: "tshark", actor: "extension", extension_id: "ms.test", host: "api.example.com", summary: "Outbound" },
        { event_id: "file-1", kind: "file", timestamp: "2026-04-13T10:00:02Z", rel_time_s: 2, collector: "strace", actor: "extension", extension_id: "ms.test", path: "/workspace/.env", operation: "read", sensitive: true, summary: "Sensitive read" },
        { event_id: "process-1", kind: "process", timestamp: "2026-04-13T10:00:03Z", rel_time_s: 3, collector: "strace", actor: "extension", extension_id: "ms.test", summary: "Spawned shell" },
      ],
      evidence_links: [],
      coverage_summary: { covered: 2, partial: 0, missing: 0, missing_capabilities: [] },
      coverage_matrix: [],
      coverage_tracks: {
        official: {
          source: "official_activation_track",
          selected_scenarios: [],
          summary: { covered: 2, partial: 2, missing: 0, attempted: 0, verified: 0, missing_capabilities: [], attempted_capabilities: [], verified_capabilities: [] },
          matrix: [],
        },
        heuristic: {
          source: "heuristic_workflow_track",
          selected_scenarios: [],
          summary: { covered: 0, partial: 0, missing: 0, attempted: 0, verified: 0, missing_capabilities: [], attempted_capabilities: [], verified_capabilities: [] },
          matrix: [],
        },
      },
      log_streams: { automation: [] },
    };
  }

  it("derives every axis from real detection signals (no fabricated data)", () => {
    const report = adaptReport(radarDto(), "radar_axes_demo.json");
    const axes = buildRiskRadarAxes(report);
    const flat = buildRiskRadar(report);
    const byKey = Object.fromEntries(axes.map((axis) => [axis.key, axis]));

    expect(axes).toHaveLength(6);

    for (const axis of axes) {
      // Trend is a real, fixed-length cumulative replay of detections.
      expect(axis.trend).toHaveLength(6);
      for (const point of axis.trend) {
        expect(point).toBeGreaterThanOrEqual(0);
        expect(point).toBeLessThanOrEqual(100);
      }
      // Headline guarantee: the sparkline ends exactly at the displayed
      // score, and that score matches the flat radar builder.
      expect(axis.trend[axis.trend.length - 1]).toBe(axis.score);
      expect(axis.score).toBe(flat[axis.key]);
      expect(axis.signalCount).toBeGreaterThanOrEqual(0);
    }

    // Axes are non-zero only where the engine actually fired a mapped signal.
    expect(byKey.exfil.score).toBeGreaterThan(0); // background_outbound_network
    expect(byKey.threat.score).toBeGreaterThan(0); // credential_or_secret_access
    expect(byKey.privesc.score).toBeGreaterThan(0); // correlative_suspicious_activity
    expect(byKey.persistence.score).toBe(0); // no mapped signal → honest zero
    expect(byKey.resource.score).toBe(0);
    expect(byKey.defense.score).toBeGreaterThan(0); // real coverage shortfall

    // signalCount reflects the real detection tally per axis.
    expect(byKey.exfil.signalCount).toBe(1);
    expect(byKey.threat.signalCount).toBe(1);
    expect(byKey.privesc.signalCount).toBe(1);
    expect(byKey.persistence.signalCount).toBe(0);
    expect(byKey.defense.signalCount).toBe(0); // coverage-driven, not a signal

    // Detections appear in the trend only once their evidence has emerged:
    // the exfil signal (earliest evidence at t=1) is absent from the first
    // bucket and present by the last.
    expect(byKey.exfil.trend[0]).toBe(0);
    expect(byKey.exfil.trend[byKey.exfil.trend.length - 1]).toBeGreaterThan(0);

    // Benchmark is the real run mean, identical across rows.
    const mean = Math.round(axes.reduce((sum, axis) => sum + axis.score, 0) / axes.length);
    for (const axis of axes) {
      expect(axis.benchmark).toBe(mean);
    }
  });

  it("shows zero threat axes when the engine fired no detections", () => {
    const dto = radarDto();
    dto.risk_signals = [];
    dto.risk_summary = { total_signals: 0, critical: 0, high: 0, medium: 0, low: 0, categories: [] };

    const axes = buildRiskRadarAxes(adaptReport(dto, "clean.json"));
    const byKey = Object.fromEntries(axes.map((axis) => [axis.key, axis]));

    // No signal → the threat axes are honestly zero (the bug this fixes:
    // they previously inflated to 100 from raw event counts).
    for (const key of ["exfil", "threat", "persistence", "privesc", "resource"] as const) {
      expect(byKey[key].score).toBe(0);
      expect(byKey[key].signalCount).toBe(0);
      expect(byKey[key].trend.every((point) => point === 0)).toBe(true);
    }
    // Only the coverage-driven axis can be non-zero without a signal.
    expect(byKey.defense.score).toBeGreaterThan(0);
  });

  it("drops signals whose category maps to no axis", () => {
    const dto = radarDto();
    dto.risk_signals = [
      { signal_id: "u1", category: "totally_unknown_category", severity: "critical", confidence: 1, evidence_event_ids: ["network-1"], summary: "x" },
    ];
    dto.coverage_tracks!.official!.summary = {
      covered: 4,
      partial: 0,
      missing: 0,
      attempted: 0,
      verified: 0,
      missing_capabilities: [],
      attempted_capabilities: [],
      verified_capabilities: [],
    };

    const axes = buildRiskRadarAxes(adaptReport(dto, "unknown.json"));

    // An unmapped category contributes to no axis score or signal count.
    for (const axis of axes) {
      expect(axis.score).toBe(0);
      expect(axis.signalCount).toBe(0);
    }
  });
});

// W19-3 [GOAL harness-verification-contract-event-level]: optional
// ``confirmation_source`` on EventAttemptDto maps to ``confirmationSource``
// on EventAttemptView with default ``"none"`` for back-compat. Documented
// values (`"harness_nonce"`, `"log_record"`, `"none"`) flow through
// unchanged. Emit-site stamps wait for W19-4/W19-5; this pin guards the
// UI adapter back-compat contract.
describe("adaptReport eventAttempts confirmationSource (W19-3)", () => {
  function minimalReportWithAttempt(
    attempt: Partial<{
      confirmation_source: string;
    }> & { attempt_id: string },
  ): ActivationReportDto {
    return {
      report_version: 2,
      target_extension_expected: "ms.test",
      signal_summary: {},
      scenario_traces: [],
      network_events: [],
      file_events: [],
      target_extension_observed: true,
      trigger_plan_applied: true,
      verification_gap: 0,
      run_quality: "medium",
      automation_health: {
        status: "healthy",
        reasons: [],
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
        strong_target_network_event_count: 0,
        correlated_only_event_count: 0,
      },
      risk_signals: [],
      risk_summary: {
        total_signals: 0,
        high: 0,
        medium: 0,
        low: 0,
        critical: 0,
        categories: [],
      },
      summary: {},
      evidence_events: [],
      evidence_links: [],
      event_attempts: [
        {
          attempt_id: attempt.attempt_id,
          declared_event: "onCommand:test",
          activation_event: "onCommand:test",
          event_family: "onCommand",
          ...(attempt.confirmation_source !== undefined
            ? { confirmation_source: attempt.confirmation_source }
            : {}),
        },
      ],
      log_streams: { automation: [] },
    };
  }

  it("defaults confirmationSource to 'none' when DTO omits the field", () => {
    const dto = minimalReportWithAttempt({ attempt_id: "probe-1" });
    const report = adaptReport(dto, "w19_3_default.json");
    expect(report.eventAttempts).toHaveLength(1);
    expect(report.eventAttempts[0].confirmationSource).toBe("none");
  });

  it.each(["harness_nonce", "log_record", "none"] as const)(
    "preserves confirmationSource='%s' when populated on the DTO",
    (source) => {
      const dto = minimalReportWithAttempt({
        attempt_id: "probe-1",
        confirmation_source: source,
      });
      const report = adaptReport(dto, "w19_3_populated.json");
      expect(report.eventAttempts[0].confirmationSource).toBe(source);
    },
  );
});

describe("adaptBundle static fold", () => {
  const activationReport = {
    summary: { total_activated: 1 },
    scenario_traces: [],
  } as unknown as ActivationReportDto;

  const baseBundle: ReportBundleDto = {
    activation_report: activationReport,
    detection_report: {
      activation_report_ref: "activation_report_x.json",
      analyzed_extension: { publisher: "pub", name: "ext", version: "1.0.0" },
      verdict: "clean",
      verdict_rationale: "no behavioral signals",
      findings: [],
      rules_executed: [],
    },
  };

  it("folds the sibling static report onto staticReport", () => {
    const dto: ReportBundleDto = {
      ...baseBundle,
      static_report: {
        detection_report: {
          findings: [
            {
              rule_id: "extrace.s2.typosquat",
              rule_version: "1.0.0",
              rule_lifecycle: "production",
              categories: ["attack.T1036"],
              severity: "high",
              confidence: "high",
              title: "Typosquat",
              description: "Impersonates a popular extension.",
            },
          ],
          tool_executions: [
            {
              tool: "inhouse",
              version: "0.0.0",
              rules_loaded: 6,
              findings_emitted: 1,
              duration_ms: 5,
              status: "ok",
            },
          ],
        },
        gate_outcome: { decision: "warn", warned_by: ["extrace.s2.typosquat"] },
      },
    };

    const report = adaptBundle(dto, "activation_report_x.json");
    expect(report.staticReport?.decision).toBe("warn");
    expect(report.staticReport?.findings[0]?.ruleId).toBe("extrace.s2.typosquat");
    expect(report.staticReport?.toolStatuses[0]?.tool).toBe("inhouse");
    expect(report.detection?.verdict).toBe("clean");
  });

  it("leaves staticReport null when the bundle carries no static_report", () => {
    const report = adaptBundle(baseBundle, "activation_report_x.json");
    expect(report.staticReport).toBeNull();
  });
});
