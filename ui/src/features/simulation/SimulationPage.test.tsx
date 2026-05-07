import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { SimulationPage } from "./SimulationPage";
import { apiClient } from "../../lib/api/client";
import type { AnalyzeJobStatusDto } from "../../lib/types/contracts";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    getAnalysisJob: vi.fn(),
    getReportByName: vi.fn(),
    getReportBundleByName: vi.fn(),
    cancelAnalysisJob: vi.fn(),
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

  it("shows the warmup empty state before evidence arrives", async () => {
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

    expect(await screen.findByRole("heading", { name: /ms\s*\.lint/u })).toBeInTheDocument();
    expect(screen.getByText("Version · 1.0.0")).toBeInTheDocument();
    expect(await screen.findByText("Run is warming up")).toBeInTheDocument();
    expect(screen.queryByText("Automation health")).not.toBeInTheDocument();
    expect(screen.queryByText("Covered")).not.toBeInTheDocument();
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
    vi.mocked(apiClient.getReportBundleByName).mockResolvedValueOnce({
      activation_report: {
        report_version: 2,
        target_extension_expected: "ms.lint",
        signal_summary: {},
        scenario_traces: [],
        network_events: [],
        file_events: [],
        target_extension_observed: false,
        trigger_plan_applied: false,
        verification_gap: 2,
        run_quality: "inconclusive",
        automation_health: {
          status: "degraded",
          reasons: ["skipped_scenarios_present"],
          trigger_requested: true,
          trigger_loaded: true,
          trigger_applied: false,
          extension_host_log_present: true,
          extension_host_output_present: true,
          target_stream_present: true,
          target_activation_count: 1,
          failed_scenarios: [],
          skipped_scenarios: ["debug_session"],
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
          correlated_only_event_count: 1,
          target_background_activation_count: 1,
          ui_blocker_count: 0,
        },
        risk_signals: [
          {
            signal_id: "correlative_suspicious_activity",
            category: "correlative_suspicious_activity",
            severity: "medium",
            confidence: 0.45,
            evidence_event_ids: ["network-1"],
            summary: "Suspicious telemetry was only correlative in this run.",
          },
        ],
        risk_summary: {
          total_signals: 1,
          critical: 0,
          high: 0,
          medium: 1,
          low: 0,
          categories: ["correlative_suspicious_activity"],
        },
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
        skipped_scenarios: [
          {
            name: "debug_session",
            reason_code: "unsupported_activation_surface",
            detail: "family not supported by runtime",
          },
        ],
        coverage_summary: {
          covered: 5,
          partial: 2,
          missing: 2,
          missing_capabilities: ["chat", "webview"],
        },
        coverage_tracks: {
          official: {
            source: "official_activation_track",
            selected_scenarios: ["coding_session"],
            summary: {
              covered: 5,
              partial: 2,
              missing: 2,
              attempted: 2,
              verified: 0,
              missing_capabilities: ["chat", "webview"],
              attempted_capabilities: ["commands", "workspace_fs"],
              verified_capabilities: [],
            },
            matrix: [
              {
                capability: "commands",
                status: "covered",
                track: "official",
                source: "official_activation_track",
                selected_scenarios: ["coding_session"],
                supported_scenarios: ["coding_session"],
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
          skipped_scenarios: ["debug_session"],
          signal_summary: {
            level: "needs_review",
            score: 34,
            reasons: ["The target extension was not observed with enough confidence."],
            note: "The target extension was not observed with enough confidence.",
          },
        },
      },
      detection_report: {
        activation_report_ref: "activation_report_demo.json",
        analyzed_extension: { publisher: "ms", name: "lint", version: "1.0.0" },
        findings: [],
        verdict: "clean",
        verdict_rationale: "No findings.",
        rules_executed: [],
      },
    });

    renderPage("/simulation?job=job-2&tab=live&event=activation-1");

    await waitFor(() => {
      expect(screen.getAllByText("Event stream").length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Progress")).toBeInTheDocument();
    expect(screen.getByText("Live event ledger")).toBeInTheDocument();
    expect(screen.queryByText("Live detection posture")).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Status" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Live" })).not.toBeInTheDocument();
    expect(screen.queryByText("Mini Timeline")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Filters" }));
    expect(
      screen.getByRole("dialog", { name: "Simulation filters" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    expect(screen.queryByRole("tab", { name: "Rule Draft" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Relations" }));
    await waitFor(() => {
      expect(screen.getByTestId("location-search").textContent).toContain("inspector=relations");
    });

    expect(screen.getByText("Automation health")).toBeInTheDocument();
    expect(screen.getByText("degraded")).toBeInTheDocument();
    expect(screen.getByText("Covered")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /open coverage detail/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "View skipped scenarios" }));
    expect(
      await screen.findByRole("dialog", { name: "Skipped scenarios" }),
    ).toBeInTheDocument();
    expect(screen.getByText("debug_session")).toBeInTheDocument();
    expect(screen.getByText("unsupported_activation_surface")).toBeInTheDocument();
  });

  it("redirects ?tab=status to ?tab=live", async () => {
    vi.mocked(apiClient.getAnalysisJob).mockResolvedValueOnce({
      job_id: "job-redirect",
      status: "completed",
      publisher: "ms",
      name: "lint",
      version: "1.0.0",
      message: "done",
      steps: [],
      created_at: 1713002400,
      updated_at: 1713002410,
      report_path: null,
    });

    renderPage("/simulation?job=job-redirect&tab=status");

    await waitFor(() => {
      expect(screen.getByTestId("location-search").textContent).toContain("tab=live");
    });
    expect(screen.getByTestId("location-search").textContent).not.toContain("tab=status");
  });

  it("renders the Stop button only while the job is active and calls the API after confirm", async () => {
    vi.mocked(apiClient.getAnalysisJob).mockResolvedValueOnce({
      job_id: "job-stop-1",
      status: "running",
      publisher: "ms",
      name: "lint",
      version: "1.0.0",
      message: "running",
      steps: [
        { name: "reset_sandbox", status: "completed", message: "ok" },
        {
          name: "run_monitoring",
          status: "running",
          message: "Scenario 2/5",
          progress: { completed: 2, total: 5 },
        },
      ],
      created_at: 1713002400,
      updated_at: 1713002410,
      report_path: null,
    });
    vi.mocked(apiClient.cancelAnalysisJob).mockResolvedValueOnce({
      job_id: "job-stop-1",
      status: "cancelled",
      publisher: "ms",
      name: "lint",
      version: "1.0.0",
      message: "Cancelled by user.",
      steps: [],
      created_at: 1713002400,
      updated_at: 1713002420,
    });

    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);

    renderPage("/simulation?job=job-stop-1&tab=live");

    const stopButton = await screen.findByRole("button", { name: "Stop simulation" });
    fireEvent.click(stopButton);

    await waitFor(() => {
      expect(apiClient.cancelAnalysisJob).toHaveBeenCalledWith("job-stop-1");
    });
    expect(confirmSpy).toHaveBeenCalled();

    confirmSpy.mockRestore();
  });

  it("hides the Stop button when the job is not active", async () => {
    vi.mocked(apiClient.getAnalysisJob).mockResolvedValueOnce({
      job_id: "job-done-1",
      status: "completed",
      publisher: "ms",
      name: "lint",
      version: "1.0.0",
      message: "done",
      steps: [
        { name: "reset_sandbox", status: "completed", message: "ok" },
        { name: "run_monitoring", status: "completed", message: "ok" },
      ],
      created_at: 1713002400,
      updated_at: 1713002410,
      report_path: null,
    });

    renderPage("/simulation?job=job-done-1&tab=live");

    await screen.findByRole("heading", { name: /ms\s*\.lint/u });
    expect(screen.getByText("Version · 1.0.0")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Stop simulation" })).toBeNull();
  });

  it("does not call the cancel API when the user dismisses the confirm dialog", async () => {
    vi.mocked(apiClient.getAnalysisJob).mockResolvedValueOnce({
      job_id: "job-stop-2",
      status: "running",
      publisher: "ms",
      name: "lint",
      version: "1.0.0",
      message: "running",
      steps: [
        { name: "reset_sandbox", status: "completed", message: "ok" },
        { name: "run_monitoring", status: "running", message: "running" },
      ],
      created_at: 1713002400,
      updated_at: 1713002410,
      report_path: null,
    });

    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);

    renderPage("/simulation?job=job-stop-2&tab=live");

    const stopButton = await screen.findByRole("button", { name: "Stop simulation" });
    fireEvent.click(stopButton);

    expect(confirmSpy).toHaveBeenCalled();
    expect(apiClient.cancelAnalysisJob).not.toHaveBeenCalled();

    confirmSpy.mockRestore();
  });

  it("shows 'Stopping…' and disables the button while the cancel request is in-flight", async () => {
    vi.mocked(apiClient.getAnalysisJob).mockResolvedValue({
      job_id: "job-stop-3",
      status: "running",
      publisher: "ms",
      name: "lint",
      version: "1.0.0",
      message: "running",
      steps: [
        { name: "reset_sandbox", status: "completed", message: "ok" },
        { name: "run_monitoring", status: "running", message: "running" },
      ],
      created_at: 1713002400,
      updated_at: 1713002410,
      report_path: null,
    });

    // Stall the cancel response so we can observe the pending state.
    let resolveCancel: (
      value: AnalyzeJobStatusDto | PromiseLike<AnalyzeJobStatusDto>,
    ) => void = () => {};
    vi.mocked(apiClient.cancelAnalysisJob).mockImplementationOnce(
      () =>
        new Promise<AnalyzeJobStatusDto>((resolve) => {
          resolveCancel = resolve;
        }),
    );

    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    renderPage("/simulation?job=job-stop-3&tab=live");

    const stopButton = await screen.findByRole("button", { name: "Stop simulation" });
    fireEvent.click(stopButton);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Stop simulation" }).textContent,
      ).toContain("Stopping");
    });
    expect(screen.getByRole("button", { name: "Stop simulation" })).toBeDisabled();

    // Clicking again while pending must not fire a second cancel request.
    fireEvent.click(screen.getByRole("button", { name: "Stop simulation" }));
    expect(apiClient.cancelAnalysisJob).toHaveBeenCalledTimes(1);

    resolveCancel({
      job_id: "job-stop-3",
      status: "cancelled",
      publisher: "ms",
      name: "lint",
      version: "1.0.0",
      message: "Cancelled by user.",
      steps: [],
      created_at: 1713002400,
      updated_at: 1713002420,
    });

    confirmSpy.mockRestore();
  });

  it("surfaces a cancel error inline when the API rejects", async () => {
    vi.mocked(apiClient.getAnalysisJob).mockResolvedValue({
      job_id: "job-stop-4",
      status: "running",
      publisher: "ms",
      name: "lint",
      version: "1.0.0",
      message: "running",
      steps: [
        { name: "reset_sandbox", status: "completed", message: "ok" },
        { name: "run_monitoring", status: "running", message: "running" },
      ],
      created_at: 1713002400,
      updated_at: 1713002410,
      report_path: null,
    });
    vi.mocked(apiClient.cancelAnalysisJob).mockRejectedValueOnce(
      new Error("Job already completed"),
    );

    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    renderPage("/simulation?job=job-stop-4&tab=live");

    const stopButton = await screen.findByRole("button", { name: "Stop simulation" });
    fireEvent.click(stopButton);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Job already completed");

    confirmSpy.mockRestore();
  });
});
