import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { SystemPage } from "./SystemPage";
import { apiClient } from "../../lib/api/client";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    getHealth: vi.fn(),
  },
}));

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
    // The real backend emits HEALTH_STATUS = "OK" (uppercase). Mock the real
    // shape so the case-insensitive tone path is exercised end-to-end.
    vi.mocked(apiClient.getHealth).mockResolvedValue({
      status: "OK",
      service: "extension-catalog-api",
    });
  });

  it("renders the honest header and lists the API + three mock tiles", async () => {
    renderPage();

    expect(await screen.findByText(/Appliance/u)).toBeInTheDocument();
    expect(screen.getByText(/status\./u)).toBeInTheDocument();
    expect(screen.queryByText(/Backend pending/u)).not.toBeInTheDocument();

    // The mislabelled "executor" card is now honestly "API" (it polls
    // /api/health, not the executor sandbox).
    expect(screen.getByTestId("service-tile-api")).toBeInTheDocument();
    expect(screen.queryByTestId("service-tile-executor")).not.toBeInTheDocument();
    expect(screen.getByTestId("service-tile-catalog")).toBeInTheDocument();
    expect(screen.getByTestId("service-tile-sandbox")).toBeInTheDocument();
    expect(screen.getByTestId("service-tile-telemetry")).toBeInTheDocument();

    await waitFor(() => {
      expect(apiClient.getHealth).toHaveBeenCalled();
    });
  });

  it("marks the mock services as MOCK and leaves the real API card unmarked", () => {
    renderPage();

    // The fabricated catalog/sandbox/telemetry cards now carry a MOCK marker;
    // the real API card does not.
    expect(screen.getByTestId("service-mock-catalog")).toBeInTheDocument();
    expect(screen.getByTestId("service-mock-sandbox")).toBeInTheDocument();
    expect(screen.getByTestId("service-mock-telemetry")).toBeInTheDocument();
    expect(screen.queryByTestId("service-mock-api")).not.toBeInTheDocument();

    expect(
      screen.getByText(/catalog, sandbox, and telemetry render mock values/iu),
    ).toBeInTheDocument();
  });

  it("shows a mock-data note only when a stub service is selected", () => {
    renderPage();

    // Default selection is the real API card — no mock note.
    expect(screen.queryByText(/Mock data — not measured/u)).not.toBeInTheDocument();

    // Selecting a stub card surfaces the explicit not-measured note.
    fireEvent.click(screen.getByTestId("service-tile-catalog"));
    expect(screen.getByText(/Mock data — not measured/u)).toBeInTheDocument();
  });

  it("surfaces the real /api/health service on the default-selected API card", async () => {
    renderPage();
    expect(
      await screen.findByText(/Live · extension-catalog-api · \/api\/health/u),
    ).toBeInTheDocument();
  });
});
