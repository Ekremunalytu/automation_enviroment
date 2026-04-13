import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { ReportsPage } from "./ReportsPage";
import { apiClient } from "../../lib/api/client";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    listReports: vi.fn(),
    getLatestReport: vi.fn(),
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
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const latestReport = {
  report_version: 2,
  target_extension_expected: "publisher.tool",
  target_extension_observed: true,
  trigger_plan_applied: true,
  verification_gap: 1,
  run_quality: "medium",
  attribution_summary: {
    target_activation_count: 1,
    strong_target_file_event_count: 1,
    strong_target_network_event_count: 1,
    correlated_only_event_count: 0,
    background_activation_count: 1,
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
    verdict: {
      level: "suspicious",
      score: 72,
      reasons: ["Sensitive file access was followed by outbound traffic."],
      note: "Sensitive file access was followed by outbound traffic.",
    },
  },
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
      selected_scenarios: ["coding_session"],
      supported_scenarios: ["coding_session", "refactor_workflow"],
    },
  ],
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

describe("ReportsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.listReports).mockResolvedValue([
      { filename: "activation_report_demo.json", size_bytes: 2048, modified: 1713002410 },
    ]);
    vi.mocked(apiClient.getLatestReport).mockResolvedValue(latestReport);
  });

  it("renders the dashboard score, category tabs, and supports opening the filter drawer", async () => {
    renderPage("/reports?report=latest&tab=overview");

    expect(await screen.findByText("Security report")).toBeInTheDocument();
    expect(await screen.findByText("General score")).toBeInTheDocument();
    expect(await screen.findByText("Detection signals")).toBeInTheDocument();
    expect(screen.getByText("Run quality")).toBeInTheDocument();
    expect(screen.getByText("The target extension accessed a secret-bearing path.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "File I/O" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Network" }));
    expect(await screen.findByText("Network activity")).toBeInTheDocument();
    expect(await screen.findAllByTestId("chart")).toHaveLength(1);

    fireEvent.click(screen.getByRole("button", { name: "Filters" }));
    expect(screen.getByText("Evidence filters")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    await waitFor(() => {
      expect(screen.queryByText("Evidence filters")).not.toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Logs" }));
    expect(await screen.findByText("Coverage audit")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Target Triggers" })).toBeInTheDocument();
    expect(screen.getByText("Activated publisher.tool via onStartupFinished")).toBeInTheDocument();
  });

  it("keeps tab and inspector state in the URL while updating inspector content from table selection", async () => {
    renderPage("/reports?report=latest&tab=evidence&event=activation-1");

    expect(await screen.findByText("Event Table")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "File I/O" }));

    await waitFor(() => {
      expect(screen.getByTestId("location-search").textContent).toContain("tab=file");
    });

    fireEvent.click(screen.getAllByText("/workspace/.env")[0]);

    expect(screen.getByText("/workspace/.env")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Analysis" }));
    await waitFor(() => {
      expect(screen.getByTestId("location-search").textContent).toContain("workspace=analysis");
    });

    fireEvent.click(screen.getByRole("button", { name: "Rules" }));
    await waitFor(() => {
      expect(screen.getByTestId("location-search").textContent).toContain("inspector=rules");
    });
  });
});
