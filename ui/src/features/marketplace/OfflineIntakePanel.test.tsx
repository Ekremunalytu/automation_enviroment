import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { MarketplacePage } from "./MarketplacePage";
import { apiClient } from "../../lib/api/client";
import { ApiError } from "../../lib/api/http";
import type { OfflineExtensionDto } from "../../lib/types/contracts";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    searchMarketplace: vi.fn(),
    downloadMarketplaceExtension: vi.fn(),
    startAnalysisJob: vi.fn(),
    listOfflineExtensions: vi.fn(),
    ingestOfflineExtension: vi.fn(),
  },
}));

function LocationDisplay() {
  const location = useLocation();
  return <div data-testid="location-path">{`${location.pathname}${location.search}`}</div>;
}

function renderPage(entry: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
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

const STAGED: OfflineExtensionDto = {
  publisher: "ms-python",
  name: "python",
  version: "2025.0.0",
  displayName: "Python (offline)",
  description: "Python tooling, staged offline.",
  filename: "ms-python.python-2025.0.0.vsix",
  size_bytes: 2_500_000,
  already_ingested: true,
};

const FRESH: OfflineExtensionDto = {
  publisher: "esbenp",
  name: "prettier-vscode",
  version: "10.1.0",
  displayName: "Prettier (offline)",
  description: "Formatter, staged offline.",
  filename: "esbenp.prettier-vscode-10.1.0.vsix",
  size_bytes: 800_000,
  already_ingested: false,
};

describe("Offline intake tab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.searchMarketplace).mockResolvedValue([]);
    vi.mocked(apiClient.listOfflineExtensions).mockResolvedValue([STAGED, FRESH]);
    vi.mocked(apiClient.ingestOfflineExtension).mockResolvedValue({
      status: "success",
      publisher: "esbenp",
      name: "prettier-vscode",
      version: "10.1.0",
      extension_dir: "/app/extensions/esbenp.prettier-vscode-10.1.0",
      message: "ingested",
    });
    vi.mocked(apiClient.startAnalysisJob).mockResolvedValue({
      job_id: "job-off-1",
      status: "queued",
      publisher: "ms-python",
      name: "python",
      version: "2025.0.0",
      message: "queued",
      steps: [],
      created_at: 1713002400,
      updated_at: 1713002401,
    });
  });

  it("lists staged packages and exposes Ingest vs Analyze per state", async () => {
    renderPage("/marketplace?tab=offline");

    expect(await screen.findByText("Python (offline)")).toBeInTheDocument();
    expect(await screen.findByText("Prettier (offline)")).toBeInTheDocument();
    expect(screen.getByText(/2 packages staged/u)).toBeInTheDocument();

    // The already-ingested package is analyzable; the fresh one needs ingest.
    expect(screen.getByRole("button", { name: "Analyze" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ingest" })).toBeInTheDocument();
  });

  it("ingests a fresh package and flips it to analyzable", async () => {
    renderPage("/marketplace?tab=offline");

    const ingestButton = await screen.findByRole("button", { name: "Ingest" });
    fireEvent.click(ingestButton);

    await waitFor(() => {
      expect(apiClient.ingestOfflineExtension).toHaveBeenCalledWith(
        "esbenp.prettier-vscode-10.1.0.vsix",
      );
    });

    // Both rows are now analyzable (the staged one + the freshly ingested one).
    await waitFor(() => {
      expect(screen.getAllByRole("button", { name: "Analyze" })).toHaveLength(2);
    });
  });

  it("surfaces a threshold-breach 422 as the dedicated popup, not the inline banner", async () => {
    vi.mocked(apiClient.ingestOfflineExtension).mockRejectedValue(
      new ApiError("breach", 422, {
        error: "vsix_threshold_breach",
        breach_kind: "uncompressed_size",
        threshold_name: "vsix_max_uncompressed_size",
        threshold_value: 268435456,
        observed_value: 999999999,
        message: "too big",
        publisher: "esbenp",
        name: "prettier-vscode",
        version: "10.1.0",
      }),
    );

    renderPage("/marketplace?tab=offline");
    fireEvent.click(await screen.findByRole("button", { name: "Ingest" }));

    expect(await screen.findByText(/exceeds uncompressed size/u)).toBeInTheDocument();
  });

  it("navigates to the sandbox when analyzing a staged package", async () => {
    renderPage("/marketplace?tab=offline");

    fireEvent.click(await screen.findByRole("button", { name: "Analyze" }));

    expect(await screen.findByText("Simulation route")).toBeInTheDocument();
    expect(screen.getByTestId("location-path").textContent).toContain(
      "/simulation?job=job-off-1&tab=live",
    );
  });

  it("switches between the Marketplace and Offline tabs", async () => {
    renderPage("/marketplace");

    // Default tab is the online marketplace search.
    expect(await screen.findByText("Search marketplace")).toBeInTheDocument();
    expect(apiClient.listOfflineExtensions).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("tab", { name: "Offline" }));

    expect(await screen.findByText("Python (offline)")).toBeInTheDocument();
    await waitFor(() => {
      expect(apiClient.listOfflineExtensions).toHaveBeenCalled();
    });
  });
});
