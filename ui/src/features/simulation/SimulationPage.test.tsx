import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { SimulationPage } from "./SimulationPage";
import { apiClient } from "../../lib/api/client";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    getAnalysisJob: vi.fn(),
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
                <SimulationPage />
                <LocationDisplay />
              </>
            }
            path="/simulation"
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("SimulationPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows the compact warmup cards before evidence arrives", async () => {
    vi.mocked(apiClient.getAnalysisJob).mockResolvedValueOnce({
      job_id: "job-1",
      status: "running",
      publisher: "ms",
      name: "lint",
      version: "1.0.0",
      message: "running",
      steps: [
        { name: "reset_sandbox", status: "completed", message: "Sandbox reset" },
        { name: "run_monitoring", status: "running", message: "Waiting for telemetry" },
      ],
      created_at: 1713002400,
      updated_at: 1713002410,
      report_path: null,
    });

    renderPage("/simulation?job=job-1&tab=live");

    expect(await screen.findByText("ms.lint@1.0.0")).toBeInTheDocument();
    expect(screen.getByText("Run Is Warming Up")).toBeInTheDocument();
    expect(screen.getByText("Current step")).toBeInTheDocument();
    expect(screen.getByText("Recent messages")).toBeInTheDocument();
    expect(screen.getAllByText("Running Playwright automation").length).toBeGreaterThan(0);
  });

  it("renders the live strip, filter drawer, and keeps tab state in the URL", async () => {
    vi.mocked(apiClient.getAnalysisJob).mockResolvedValueOnce({
      job_id: "job-2",
      status: "completed",
      publisher: "ms",
      name: "lint",
      version: "1.0.0",
      message: "done",
      steps: [
        { name: "reset_sandbox", status: "completed", message: "Sandbox reset" },
        { name: "run_monitoring", status: "completed", message: "Telemetry captured" },
      ],
      created_at: 1713002400,
      updated_at: 1713002410,
      report_path: "activation_report_demo.json",
    });
    vi.mocked(apiClient.getReportByName).mockResolvedValueOnce({
      report_version: 2,
      evidence_events: [
        {
          event_id: "activation-1",
          kind: "activation",
          timestamp: "2026-04-13T10:00:00Z",
          rel_time_s: 1,
          collector: "log",
          actor: "extension",
          extension_id: "ms.lint",
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
          host: "api.example.com",
          path: "/collect",
          summary: "Outbound request",
        },
      ],
      evidence_links: [],
      coverage_summary: {
        covered: 5,
        partial: 2,
        missing: 2,
        missing_capabilities: ["chat", "webview"],
      },
      log_streams: {
        target_extension_host: [
          {
            timestamp: "2026-04-13T10:00:00Z",
            rel_time_s: 1,
            stream: "target_extension_host",
            kind: "activation",
            message: "Activated ms.lint via onStartupFinished",
            extension_id: "ms.lint",
            activation_event: "onStartupFinished",
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
            message: "Started scenario coding session",
            scenario_name: "coding_session",
            status: "running",
          },
        ],
      },
      summary: {
        network_events: 1,
      },
    });

    renderPage("/simulation?job=job-2&tab=live&event=activation-1");

    await waitFor(() => {
      expect(screen.getAllByText("Live Event Stream").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Progress")).toBeInTheDocument();
    expect(screen.getByTestId("chart")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Filters" }));
    expect(screen.getByText("Simulation filters")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    fireEvent.click(screen.getByRole("button", { name: "Run Status" }));
    await waitFor(() => {
      expect(screen.getByTestId("location-search").textContent).toContain("tab=status");
    });

    fireEvent.click(screen.getByRole("button", { name: "Live Evidence" }));
    await waitFor(() => {
      expect(screen.getByText("Simulation evidence")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Analysis" }));
    await waitFor(() => {
      expect(screen.getByTestId("location-search").textContent).toContain("workspace=analysis");
    });

    fireEvent.click(screen.getByRole("button", { name: "Logs" }));
    await waitFor(() => {
      expect(screen.getByText("Coverage audit")).toBeInTheDocument();
    });
    expect(screen.getByText("Activated ms.lint via onStartupFinished")).toBeInTheDocument();

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
