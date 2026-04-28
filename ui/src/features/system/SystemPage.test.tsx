import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";

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
    vi.mocked(apiClient.getHealth).mockResolvedValue({
      status: "ok",
      service: "extension-catalog-api",
    });
  });

  it("renders the v3 header, stub badge, and lists the four service tiles", async () => {
    renderPage();

    expect(await screen.findByText(/All systems/u)).toBeInTheDocument();
    expect(screen.getByText(/operational/u)).toBeInTheDocument();
    expect(screen.getByText(/Backend pending/u)).toBeInTheDocument();

    expect(screen.getByTestId("service-tile-executor")).toBeInTheDocument();
    expect(screen.getByTestId("service-tile-catalog")).toBeInTheDocument();
    expect(screen.getByTestId("service-tile-sandbox")).toBeInTheDocument();
    expect(screen.getByTestId("service-tile-telemetry")).toBeInTheDocument();

    await waitFor(() => {
      expect(apiClient.getHealth).toHaveBeenCalled();
    });
  });

  it("falls back to mock service detail and marks stub services explicitly", () => {
    renderPage();
    expect(screen.getAllByText("stub").length).toBeGreaterThanOrEqual(3);
  });
});
