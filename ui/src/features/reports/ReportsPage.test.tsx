import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { ReportsPage } from "./ReportsPage";
import { apiClient } from "../../lib/api/client";
import type { ActivationReportDto, AnalysisBundleDto } from "../../lib/types/contracts";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    listReports: vi.fn(),
    getLatestReportBundle: vi.fn(),
    getReportBundleByName: vi.fn(),
    getReportByName: vi.fn(),
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

describe("ReportsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.listReports).mockResolvedValue([
      { filename: "activation_report_demo.json", size_bytes: 2048, modified: 1713002410 },
    ]);
    vi.mocked(apiClient.getLatestReportBundle).mockResolvedValue(latestBundle);
    vi.mocked(apiClient.getReportBundleByName).mockResolvedValue(latestBundle);
  });

  it("renders overview, canonical tabs, and supports opening the filter drawer", async () => {
    renderPage("/reports?report=latest&tab=overview");

    expect(await screen.findByText("Security report")).toBeInTheDocument();
    expect(await screen.findByText("Verdict · MALICIOUS")).toBeInTheDocument();
    expect(screen.getByText("critical finding with high confidence")).toBeInTheDocument();
    expect(screen.getByText("Credential file read followed by outbound request")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /credential file read followed by outbound request/iu })).toBeInTheDocument();
    expect(screen.getByText("Composite score")).toBeInTheDocument();
    expect(screen.getByText("Findings · 1")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Overview" })).toBeInTheDocument();
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

    await screen.findByText("Findings · 1");
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
