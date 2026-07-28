import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { SystemPage } from "./SystemPage";
import { apiClient } from "../../lib/api/client";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    getSystemHealth: vi.fn(),
  },
}));

const measuredHealth = {
  observed_at: "2026-07-28T11:00:00Z",
  services: [
    {
      id: "api",
      name: "API",
      health: "ok" as const,
      status: "OK",
      detail: "ExTrace API · v1.0.0",
      source: "/api/system/health · current process",
      metrics: [
        { label: "status", value: "OK" },
        { label: "uptime", value: "4m 12s" },
      ],
      observations: ["Aggregate health request served by the API process"],
    },
    {
      id: "catalog",
      name: "Catalog",
      health: "ok" as const,
      status: "online",
      detail: "12 persisted extension records",
      source: "PostgreSQL · extensions table",
      metrics: [
        { label: "extensions", value: "12" },
        { label: "database", value: "postgresql" },
      ],
      observations: ["Database query completed"],
    },
    {
      id: "sandbox",
      name: "Sandbox",
      health: "degraded" as const,
      status: "starting",
      detail: "Isolated dynamic-analysis executor",
      source: "Docker Engine · container state",
      metrics: [{ label: "state", value: "running" }],
      observations: ["Health check: starting"],
    },
    {
      id: "static",
      name: "Static",
      health: "ok" as const,
      status: "running",
      detail: "Network-isolated static pre-check",
      source: "Docker Engine · container state",
      metrics: [{ label: "state", value: "running" }],
      observations: ["Container state: running"],
    },
  ],
  inventory: [
    { label: "hostname", value: "api-container" },
    { label: "platform", value: "linux/x86_64" },
  ],
};

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <SystemPage />
    </QueryClientProvider>,
  );
}

describe("SystemPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.getSystemHealth).mockResolvedValue(measuredHealth);
  });

  it("renders the live runtime header without the removed helper copy", async () => {
    renderPage();

    expect(screen.getByText("Runtime pulse.")).toBeInTheDocument();
    expect(
      await screen.findByLabelText("Measured services"),
    ).toBeInTheDocument();
    expect(screen.queryByText("System status")).not.toBeInTheDocument();
    expect(screen.queryByText("Appliance status.")).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Only the API card reflects a real measurement/u),
    ).not.toBeInTheDocument();
  });

  it("renders only measured services and no mock markers", async () => {
    renderPage();

    expect(await screen.findByTestId("service-tile-api")).toBeInTheDocument();
    expect(screen.getByTestId("service-tile-catalog")).toBeInTheDocument();
    expect(screen.getByTestId("service-tile-sandbox")).toBeInTheDocument();
    expect(screen.getByTestId("service-tile-static")).toBeInTheDocument();
    expect(screen.queryByText("MOCK")).not.toBeInTheDocument();
    expect(screen.queryByTestId("service-tile-telemetry")).not.toBeInTheDocument();
    expect(screen.queryByText("Measured service")).not.toBeInTheDocument();
    expect(screen.queryByText("ExTrace API · v1.0.0")).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Source · \/api\/system\/health/u),
    ).not.toBeInTheDocument();

    await waitFor(() => {
      expect(apiClient.getSystemHealth).toHaveBeenCalled();
    });
  });

  it("switches service detail to real catalog measurements", async () => {
    renderPage();

    fireEvent.click(await screen.findByTestId("service-tile-catalog"));

    expect(screen.queryByText("12 persisted extension records")).not.toBeInTheDocument();
    expect(screen.queryByText(/PostgreSQL · extensions table/u)).not.toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("postgresql")).toBeInTheDocument();
    expect(screen.getByText("Database query completed")).toBeInTheDocument();
    expect(screen.getByText("api-container")).toBeInTheDocument();
  });
});
