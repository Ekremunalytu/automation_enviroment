import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { MarketplacePage } from "./MarketplacePage";
import { apiClient } from "../../lib/api/client";
import type { MarketplaceDownloadResponseDto } from "../../lib/types/contracts";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    searchMarketplace: vi.fn(),
    downloadMarketplaceExtension: vi.fn(),
    startAnalysisJob: vi.fn(),
  },
}));

function LocationDisplay() {
  const location = useLocation();
  return <div data-testid="location-path">{`${location.pathname}${location.search}`}</div>;
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
          <Route element={<MarketplacePage />} path="/marketplace" />
          <Route
            element={
              <>
                <div>Simulation route</div>
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

describe("MarketplacePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.searchMarketplace).mockResolvedValue([
      {
        publisher: "ms",
        name: "python",
        version: "1.0.0",
        displayName: "Python",
        description: "Python tooling for VS Code.",
        installs: 123456,
        rating: 4.8,
      },
    ]);
    vi.mocked(apiClient.downloadMarketplaceExtension).mockResolvedValue({
      status: "downloaded",
      publisher: "ms",
      name: "python",
      version: "1.0.0",
      extension_dir: "/tmp/ms.python",
      message: "Downloaded",
    });
    vi.mocked(apiClient.startAnalysisJob).mockResolvedValue({
      job_id: "job-9",
      status: "queued",
      publisher: "ms",
      name: "python",
      version: "1.0.0",
      message: "queued",
      steps: [],
      created_at: 1713002400,
      updated_at: 1713002401,
    });
  });

  it("renders the v3 layout, surfaces backend-pending stubs, and preserves the download/analyze flow", async () => {
    renderPage("/marketplace?q=python");

    expect(await screen.findByText("Extension intake")).toBeInTheDocument();
    expect(screen.getByDisplayValue("python")).toBeInTheDocument();
    expect(await screen.findByText("Python")).toBeInTheDocument();
    expect(await screen.findByText(/Results for/u)).toBeInTheDocument();
    expect(screen.getByText("UNCATEGORIZED")).toBeInTheDocument();
    expect(screen.getByText("RISK TBD")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Download" }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Analyze" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Analyze" }));
    expect(await screen.findByText("Simulation route")).toBeInTheDocument();
    expect(screen.getByTestId("location-path").textContent).toContain("/simulation?job=job-9&tab=live");
  });

  it("ignores a rapid second download click for the same artifact", async () => {
    let resolveDownload: ((value: MarketplaceDownloadResponseDto) => void) | undefined;
    vi.mocked(apiClient.downloadMarketplaceExtension).mockImplementation(
      () =>
        new Promise<MarketplaceDownloadResponseDto>((resolve) => {
          resolveDownload = resolve;
        }),
    );

    renderPage("/marketplace?q=python");

    const downloadButton = await screen.findByRole("button", { name: "Download" });
    fireEvent.click(downloadButton);
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(apiClient.downloadMarketplaceExtension).toHaveBeenCalledTimes(1);
    });

    if (!resolveDownload) {
      throw new Error("Download resolver was not initialized.");
    }

    resolveDownload({
      status: "success",
      publisher: "ms",
      name: "python",
      version: "1.0.0",
      extension_dir: "/tmp/ms.python",
      message: "Downloaded",
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Analyze" })).toBeInTheDocument();
    });
  });
});
