import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { ReportsPage } from "./ReportsPage";
import { apiClient } from "../../lib/api/client";
import type {
  ActivationReportDto,
  AnalysisBundleDto,
  StaticReportArtifactDto,
} from "../../lib/types/contracts";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    listReports: vi.fn(),
    getLatestReportBundle: vi.fn(),
    getReportBundleByName: vi.fn(),
    getReportByName: vi.fn(),
    getExecutorPreferences: vi.fn(),
    getLatestStaticReport: vi.fn(),
  },
}));

vi.mock("../../lib/charts/core", () => ({
  ReactECharts: () => <div data-testid="chart" />,
}));

function LocationDisplay() {
  const location = useLocation();
  return <div data-testid="location-search">{location.search}</div>;
}

function renderPage(entry: string) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[entry]}>
        <Routes>
          <Route
            element={
              <>
                <ReportsPage />
                <LocationDisplay />
              </>
            }
            path="/reports"
          />
          <Route element={<LocationDisplay />} path="/rules" />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const latestReport: ActivationReportDto = {
  report_version: 2,
  target_extension_expected: "publisher.tool",
  signal_summary: {},
  target_extension_observed: true,
  trigger_plan_applied: true,
  verification_gap: 1,
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
    target_background_activation_count: 1,
    ui_blocker_count: 0,
  },
  risk_signals: [
    {
      signal_id: "credential_or_secret_access",
      category: "credential_or_secret_access",
      severity: "high",
      confidence: 0.88,
      evidence_event_ids: ["file-1"],
      summary: "The target extension accessed a secret-bearing path.",
    },
  ],
  risk_summary: {
    total_signals: 1,
    high: 1,
    medium: 0,
    low: 0,
    critical: 0,
    categories: ["credential_or_secret_access"],
  },
  _metadata: { filename: "activation_report_demo.json" },
  summary: {
    total_activated: 1,
    scenarios_run: ["credential probe"],
    monitoring_duration_s: 14,
    network_events: 1,
    file_events: 1,
    sensitive_file_events: 1,
    signal_summary: {
      level: "suspicious",
      score: 72,
      reasons: ["Sensitive file access was followed by outbound traffic."],
      note: "Sensitive file access was followed by outbound traffic.",
    },
  },
  scenario_traces: [],
  evidence_events: [
    {
      event_id: "activation-1",
      kind: "activation",
      timestamp: "2026-04-13T10:00:00Z",
      rel_time_s: 1,
      collector: "log",
      actor: "extension",
      scenario_name: "credential probe",
      extension_id: "publisher.tool",
      activation_event: "onStartupFinished",
      summary: "Extension activated",
    },
    {
      event_id: "network-1",
      kind: "network",
      timestamp: "2026-04-13T10:00:05Z",
      rel_time_s: 5,
      collector: "tshark",
      actor: "extension",
      scenario_name: "credential probe",
      extension_id: "publisher.tool",
      host: "api.example.com",
      path: "/collect",
      destination_ip: "1.2.3.4",
      destination_port: 443,
      summary: "Outbound request",
    },
    {
      event_id: "file-1",
      kind: "file",
      timestamp: "2026-04-13T10:00:06Z",
      rel_time_s: 6,
      collector: "strace",
      actor: "extension",
      scenario_name: "credential probe",
      extension_id: "publisher.tool",
      path: "/workspace/.env",
      operation: "read",
      sensitive: true,
      summary: "Sensitive file read",
    },
  ],
  evidence_links: [
    {
      from_event_id: "file-1",
      to_event_id: "activation-1",
      link_type: "candidate_owner",
      confidence: 0.61,
      reason: "Temporal proximity to extension activation.",
    },
  ],
  coverage_summary: {
    covered: 6,
    partial: 2,
    missing: 3,
    missing_capabilities: ["chat", "comments", "webview"],
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
        covered: 6,
        partial: 2,
        missing: 3,
        attempted: 2,
        verified: 1,
        missing_capabilities: ["chat", "comments", "webview"],
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
  network_events: [],
  file_events: [],
  log_streams: {
    target_extension_host: [
      {
        timestamp: "2026-04-13T10:00:00Z",
        rel_time_s: 1,
        stream: "target_extension_host",
        kind: "activation",
        message: "Activated publisher.tool via onStartupFinished",
        extension_id: "publisher.tool",
        activation_event: "onStartupFinished",
        scenario_name: "credential probe",
        status: "completed",
        is_target_extension: true,
      },
    ],
    automation: [
      {
        timestamp: "2026-04-13T09:59:59Z",
        rel_time_s: 0.2,
        stream: "automation",
        kind: "scenario",
        message: "Started scenario credential probe",
        scenario_name: "credential probe",
        status: "running",
      },
    ],
  },
};

const latestBundle: AnalysisBundleDto = {
  activation_report: latestReport,
  detection_report: {
    schema_version: "1",
    activation_report_ref: "activation_report_demo.json",
    analyzed_extension: {
      publisher: "publisher",
      name: "tool",
      version: "1.0.0",
    },
    findings: [
      {
        id: "01HXYZABCDE1234567890ABCDE",
        rule_id: "extrace.a1.credential_read_then_network",
        rule_version: "1.0.0",
        rule_lifecycle: "production",
        categories: ["attack.T1555", "attack.T1041"],
        severity: "critical",
        confidence: "high",
        title: "Credential file read followed by outbound request",
        description: "The extension read a credential-bearing path and contacted an unknown host.",
        evidence: [
          {
            type: "filesystem_read",
            event_id: "file-1",
            summary: "Sensitive file read",
          },
        ],
        adversary_class: "A1",
        mitigation_hint: "Rotate credentials and remove the extension.",
      },
    ],
    verdict: "malicious",
    verdict_rationale: "critical finding with high confidence",
    rules_executed: [
      {
        rule_id: "extrace.a1.credential_read_then_network",
        rule_version: "1.0.0",
        lifecycle: "production",
        status: "fired",
        finding_ids: ["01HXYZABCDE1234567890ABCDE"],
      },
    ],
    generated_at: "2026-04-20T09:00:00Z",
  },
};

const latestStaticArtifact: StaticReportArtifactDto = {
  filename: "static_report_22222222222222222222222222222222.json",
  modified: 1713002510,
  static_report: {
    detection_report: {
      coverage: {
        files_discovered: 3,
        files_selected: 3,
        files_eligible: 2,
        files_scanned: 3,
        files_parsed: 2,
        bytes_considered: 512,
        bytes_read: 512,
        manifest_status: "parsed",
        coverage_reasons: [],
      },
      findings: [
        {
          rule_id: "extrace.s3.embedded_native_binary",
          rule_version: "1.0.0",
          rule_lifecycle: "production",
          categories: ["attack.T1105"],
          severity: "medium",
          confidence: "high",
          title: "Embedded native binary",
          description: "Ships native binaries.",
        },
      ],
      tool_executions: [
        {
          tool: "inhouse",
          version: "1.0.0",
          rules_loaded: 26,
          findings_emitted: 1,
          duration_ms: 10,
          status: "ok",
        },
      ],
    },
    gate_outcome: {
      decision: "warn",
      warned_by: ["extrace.s3.embedded_native_binary"],
    },
  },
};

describe("ReportsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.listReports).mockResolvedValue([
      { filename: "activation_report_demo.json", size_bytes: 2048, modified: 1713002410 },
    ]);
    vi.mocked(apiClient.getLatestReportBundle).mockResolvedValue(latestBundle);
    vi.mocked(apiClient.getReportBundleByName).mockResolvedValue(latestBundle);
    vi.mocked(apiClient.getExecutorPreferences).mockResolvedValue({
      dynamic_analysis_enabled: true,
    });
  });

  it("shows the disabled dynamic state and the latest static-only artifact", async () => {
    vi.mocked(apiClient.getExecutorPreferences).mockResolvedValue({
      dynamic_analysis_enabled: false,
    });
    vi.mocked(apiClient.getLatestStaticReport).mockResolvedValue(latestStaticArtifact);

    renderPage("/reports?report=latest&tab=matrix");

    expect(await screen.findByText("Dynamic analysis is disabled")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Credential read.*Fired/i })).not.toBeInTheDocument();
    expect(await screen.findByText("Latest static artifact")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Embedded native binary.*Fired/i }),
    ).toBeInTheDocument();
    expect(apiClient.getLatestStaticReport).toHaveBeenCalled();
  });

  it("renders static analysis inspection as the tab beside Rule matrix", async () => {
    vi.mocked(apiClient.getLatestStaticReport).mockResolvedValue(latestStaticArtifact);

    renderPage("/reports?report=latest&tab=inspection");

    expect(
      await screen.findByRole("heading", { name: "Static analysis inspection" }),
    ).toBeInTheDocument();
    const reportTabs = screen.getAllByRole("tab").map((tab) => tab.textContent);
    expect(reportTabs.slice(0, 3)).toEqual([
      "Overview",
      "Rule matrix",
      "Static analysis inspection",
    ]);
    expect(
      screen.getByRole("tab", { name: "Static analysis inspection" }),
    ).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("combobox", { name: "Report source" })).toBeDisabled();
    expect(screen.getByRole("textbox", { name: "Search evidence" })).toBeDisabled();
    expect(screen.getByLabelText("Static gate inspection")).toBeInTheDocument();
    expect(apiClient.getLatestStaticReport).toHaveBeenCalled();
    expect(apiClient.getLatestReportBundle).not.toHaveBeenCalled();
  });

  it("keeps a static inspection loading failure explicit inside Reports", async () => {
    vi.mocked(apiClient.getLatestStaticReport).mockRejectedValue(
      new Error("static artifact unavailable"),
    );

    renderPage("/reports?report=latest&tab=inspection");

    expect(
      await screen.findByText("Static inspection could not be loaded"),
    ).toBeInTheDocument();
    expect(screen.getByText("Error: static artifact unavailable")).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: "Static analysis inspection" }),
    ).toHaveAttribute("aria-selected", "true");
    expect(apiClient.getLatestReportBundle).not.toHaveBeenCalled();
  });

  it("uses the latest static artifact for overview and disables dynamic-only controls", async () => {
    vi.mocked(apiClient.getExecutorPreferences).mockResolvedValue({
      dynamic_analysis_enabled: false,
    });
    vi.mocked(apiClient.getLatestStaticReport).mockResolvedValue(latestStaticArtifact);

    renderPage("/reports?report=latest&tab=overview");

    expect(await screen.findByText("Static scan")).toBeInTheDocument();
    const workspace = screen.getByLabelText("Report workspace");
    expect(
      within(workspace).getByRole("option", { name: "Latest static artifact" }),
    ).toBeInTheDocument();
    expect(
      await within(workspace).findByLabelText("Findings: 1"),
    ).toBeInTheDocument();
    expect(within(workspace).getByLabelText("Decision: Warn")).toBeInTheDocument();
    expect(within(workspace).getByLabelText("Coverage: 3/3")).toBeInTheDocument();
    expect(within(workspace).getByRole("textbox", { name: "Search evidence" }))
      .toBeDisabled();
    expect(within(workspace).getByRole("button", { name: "Filters" })).toBeDisabled();

    expect(await screen.findByText("Dynamic analysis is disabled")).toBeInTheDocument();
    expect(screen.getByLabelText("Static decision overview")).toHaveTextContent(
      "Decision · WARN",
    );
    expect(screen.getByText("Embedded native binary")).toBeInTheDocument();
    expect(screen.queryByText("Composite score")).not.toBeInTheDocument();

    expect(screen.getByRole("tab", { name: "Overview" })).toBeEnabled();
    expect(screen.getByRole("tab", { name: "Rule matrix" })).toBeEnabled();
    expect(
      screen.getByRole("tab", { name: "Static analysis inspection" }),
    ).toBeEnabled();
    expect(screen.getByRole("tab", { name: "Interactions" })).toBeDisabled();
    expect(screen.getByRole("tab", { name: "Timeline" })).toBeDisabled();
    expect(screen.getByRole("tab", { name: "Event ledger" })).toBeDisabled();
    expect(screen.getByRole("tab", { name: "Audit" })).toBeDisabled();

    expect(apiClient.getLatestStaticReport).toHaveBeenCalled();
    expect(apiClient.getLatestReportBundle).not.toHaveBeenCalled();
  });

  it("redirects a latest static-only dynamic deep link to overview", async () => {
    vi.mocked(apiClient.getExecutorPreferences).mockResolvedValue({
      dynamic_analysis_enabled: false,
    });
    vi.mocked(apiClient.getLatestStaticReport).mockResolvedValue(latestStaticArtifact);

    renderPage("/reports?report=latest&tab=ledger&event=file-1");

    expect(await screen.findByLabelText("Static decision overview")).toBeInTheDocument();
    await waitFor(() => {
      const search = screen.getByTestId("location-search").textContent || "";
      expect(search).toContain("tab=overview");
      expect(search).not.toContain("event=");
    });
    expect(screen.getByRole("tab", { name: "Event ledger" })).toBeDisabled();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows a static-only error without falling back to an unrelated activation report", async () => {
    vi.mocked(apiClient.getExecutorPreferences).mockResolvedValue({
      dynamic_analysis_enabled: false,
    });
    vi.mocked(apiClient.getLatestStaticReport).mockRejectedValue(
      new Error("static artifact unavailable"),
    );

    renderPage("/reports?report=latest&tab=overview");

    expect(
      await screen.findByText("Latest static pre-check unavailable"),
    ).toBeInTheDocument();
    expect(screen.getByText("Error: static artifact unavailable")).toBeInTheDocument();
    expect(apiClient.getLatestReportBundle).not.toHaveBeenCalled();
  });

  it("keeps an explicitly selected historical activation report inspectable", async () => {
    vi.mocked(apiClient.getExecutorPreferences).mockResolvedValue({
      dynamic_analysis_enabled: false,
    });

    renderPage("/reports?report=activation_report_demo.json&tab=overview");

    expect(await screen.findByText("Run control")).toBeInTheDocument();
    expect(await screen.findByLabelText("Verdict overview")).toHaveTextContent(
      "Verdict · MALICIOUS",
    );
    expect(screen.getByRole("tab", { name: "Interactions" })).toBeEnabled();
    expect(apiClient.getReportBundleByName).toHaveBeenCalledWith(
      "activation_report_demo.json",
      expect.any(AbortSignal),
    );
    expect(apiClient.getLatestStaticReport).not.toHaveBeenCalled();
  });

  it("renders overview, canonical tabs, and supports opening the filter drawer", async () => {
    renderPage("/reports?report=latest&tab=overview");

    expect(await screen.findByText("Security report")).toBeInTheDocument();
    expect(screen.getByLabelText("Report workspace")).toBeInTheDocument();
    expect(screen.getByText("Run control")).toBeInTheDocument();
    const verdictOverview = await screen.findByLabelText("Verdict overview");
    expect(within(verdictOverview).getByText("Verdict · MALICIOUS")).toBeInTheDocument();
    expect(within(verdictOverview).getByLabelText("Verdict scale")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Security report" }).closest("header"),
    ).not.toHaveTextContent("Verdict");
    expect(screen.getByText("critical finding with high confidence")).toBeInTheDocument();
    expect(screen.getByText("Credential file read followed by outbound request")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /credential file read followed by outbound request/iu })).toBeInTheDocument();
    expect(screen.getByText("Composite score")).toBeInTheDocument();
    expect(screen.queryByText("Findings · 1")).not.toBeInTheDocument();
    expect(screen.queryByText(/File ·/u)).not.toBeInTheDocument();
    expect(screen.queryByText(/Visible ·/u)).not.toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Overview" })).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: "Static analysis inspection" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Interactions" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Timeline" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Event ledger" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Audit" })).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "File I/O" })).not.toBeInTheDocument();
    expect(screen.queryByText("Automation health")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Interactions" }));
    expect(await screen.findByText("Interaction graph")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Interaction flow graph" })).toBeInTheDocument();
    expect(screen.queryByText("Attribution context")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Timeline" }));
    expect(
      await screen.findByText(
        "Canonical report timeline. Category mini timelines were removed so temporal analysis has one source of truth.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Event timeline" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Filters" }));
    expect(
      screen.getByRole("dialog", { name: "Evidence filters" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    await waitFor(() => {
      expect(screen.queryByText("Evidence filters")).not.toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("tab", { name: "Event ledger" }));
    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "All" })).toBeInTheDocument();
    });
    expect(screen.getByRole("tab", { name: "Network" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "File" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Activation" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Scenario" })).toBeInTheDocument();
    expect(screen.queryByText("Coverage audit")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Audit" }));
    expect(await screen.findByText("Coverage audit")).toBeInTheDocument();
    expect(screen.getByText("Official coverage")).toBeInTheDocument();
    expect(screen.getByText("Heuristic workflow coverage")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Target Triggers" })).toBeInTheDocument();
    expect(screen.getByText("Activated publisher.tool via onStartupFinished")).toBeInTheDocument();
  });

  it("renders an INCONCLUSIVE verdict as a non-green stop with a recommended action", async () => {
    // B4: an analysis that could not complete must not read like a clean pass.
    const inconclusiveBundle: AnalysisBundleDto = {
      ...latestBundle,
      detection_report: {
        ...latestBundle.detection_report!,
        findings: [],
        rules_executed: [],
        verdict: "inconclusive",
        verdict_rationale: "incomplete analysis: extension_host_log_missing",
      },
    };
    vi.mocked(apiClient.getLatestReportBundle).mockResolvedValue(inconclusiveBundle);
    vi.mocked(apiClient.getReportBundleByName).mockResolvedValue(inconclusiveBundle);

    renderPage("/reports?report=latest&tab=overview");

    expect(await screen.findByText("Verdict · INCONCLUSIVE")).toBeInTheDocument();
    expect(
      screen.getByRole("list", { name: "Verdict signals" }),
    ).toBeInTheDocument();
    expect(screen.getByText("1 verdict signal")).toBeInTheDocument();
    expect(screen.getByText("extension host log missing")).toBeInTheDocument();

    // The recommended-action note must tell the operator this is NOT clean.
    const note = await screen.findByRole("note", { name: "Recommended action" });
    expect(note.textContent?.toLowerCase()).toContain("not a clean");

    // The compact verdict scale legend renders all five states; "Clean with
    // notes" is unique to the legend, so its presence proves the legend mounted.
    expect(screen.getByText("Clean with notes")).toBeInTheDocument();
  });

  it("maps legacy tabs to the ledger and keeps canonical tab state in the URL", async () => {
    renderPage("/reports?report=latest&tab=evidence&event=activation-1");

    expect(await screen.findByRole("tab", { name: "Event ledger" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Event ledger" })).toHaveAttribute("aria-selected", "true");

    fireEvent.click(screen.getByRole("tab", { name: "Timeline" }));
    await waitFor(() => {
      expect(screen.getByTestId("location-search").textContent).toContain("tab=timeline");
    });

    fireEvent.click(screen.getByRole("tab", { name: "Event ledger" }));
    await waitFor(() => {
      expect(screen.getByTestId("location-search").textContent).toContain("tab=ledger");
    });

    fireEvent.click(screen.getByRole("tab", { name: "Audit" }));
    await waitFor(() => {
      expect(screen.getByTestId("location-search").textContent).toContain("tab=audit");
    });
  });

  it("opens the Inspector drawer on deep-link and routes 'Draft rule from event' to /rules", async () => {
    renderPage("/reports?report=latest&tab=ledger&event=file-1");

    await screen.findByText("Security report");
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    const draftButton = await screen.findByRole(
      "button",
      { name: /draft rule from event/i },
      { timeout: 4000 },
    );
    fireEvent.click(draftButton);

    await waitFor(() => {
      const search = screen.getByTestId("location-search").textContent || "";
      expect(search).toContain("tab=draft");
      expect(search).toContain("from=file-1");
    });
  });
});
