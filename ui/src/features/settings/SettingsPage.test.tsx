import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";

import { apiClient } from "../../lib/api/client";
import { ApiError } from "../../lib/api/http";
import { SettingsPage } from "./SettingsPage";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    getExecutorPreferences: vi.fn(),
    updateExecutorPreferences: vi.fn(),
    getSecurityThresholds: vi.fn(),
    updateSecurityThresholds: vi.fn(),
  },
}));

function renderPage(initialEntries: string[] = ["/settings"]): void {
  // SettingsPage uses useSearchParams (the Marketplace popup deep-links to
  // ?section=security) and useQuery (security thresholds). The MemoryRouter
  // satisfies the routing context; the QueryClientProvider makes the
  // Security tab's network calls inert when a test focuses on the
  // not-yet-enforced console sections.
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
  render(<SettingsPage />, { wrapper });
}

describe("SettingsPage", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.clearAllMocks();
    vi.mocked(apiClient.getExecutorPreferences).mockResolvedValue({
      dynamic_analysis_enabled: false,
    });
    vi.mocked(apiClient.updateExecutorPreferences).mockImplementation(
      async (payload) => ({
        dynamic_analysis_enabled: payload.dynamic_analysis_enabled,
      }),
    );
    // Default: hang the threshold fetch so the Security tab stays in its
    // loading state. Tests that need a different terminal state override
    // this via `mockRejectedValueOnce` / `mockResolvedValueOnce`.
    vi.mocked(apiClient.getSecurityThresholds).mockReturnValue(
      new Promise<never>(() => undefined),
    );
  });

  it("renders the simplified header and the five settings sections", () => {
    renderPage();

    expect(screen.getByText(/Tune the/u)).toBeInTheDocument();
    expect(screen.getByText(/appliance\./u)).toBeInTheDocument();
    expect(screen.queryByText("Settings")).not.toBeInTheDocument();
    expect(screen.queryByText(/Single-operator preferences/u)).not.toBeInTheDocument();
    expect(screen.queryByText(/Backend pending/u)).not.toBeInTheDocument();
    for (const label of ["General", "Executor", "Security", "Telemetry", "Danger"]) {
      expect(screen.getByRole("button", { name: new RegExp(`^${label}`, "i") })).toBeInTheDocument();
    }
  });

  it("enables only the persisted dynamic-scan toggle in executor settings", async () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: /^Executor/u }));

    const dynamicScan = await screen.findByRole("button", {
      name: "Dynamic scan after intake",
    });
    expect(dynamicScan).toBeEnabled();
    expect(dynamicScan).toHaveAttribute("aria-pressed", "false");
    const strictNet = screen.getByRole("button", {
      name: "Strict network mode",
    });
    expect(strictNet).toBeDisabled();

    expect(screen.getAllByText(/Not yet enforced/u).length).toBeGreaterThan(0);
    expect(screen.getByText("Backend-persisted")).toBeInTheDocument();
  });

  it("persists the dynamic-scan toggle immediately", async () => {
    renderPage(["/settings?section=executor"]);

    const dynamicScan = await screen.findByRole("button", {
      name: "Dynamic scan after intake",
    });
    fireEvent.click(dynamicScan);

    await waitFor(() => {
      expect(apiClient.updateExecutorPreferences).toHaveBeenCalledWith({
        dynamic_analysis_enabled: true,
      });
    });
    expect(dynamicScan).toHaveAttribute("aria-pressed", "true");
  });

  it("replaces the fictional pool-size control with the honest single-active queue fact", async () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: /^Executor/u }));

    // The old 2/4/8/16 "Pool size" segmented control contradicted the
    // single-active serial queue (Non-Goal: no parallel sandboxes / B3).
    expect(screen.queryByText("Pool size")).not.toBeInTheDocument();
    expect(
      await screen.findByText("Single active · serial"),
    ).toBeInTheDocument();
  });

  it("has live appearance controls (theme, density, time zone)", () => {
    renderPage();

    // General is the default section. As of H3/H1b these presentation controls
    // are real, apply-on-change, browser-local — not "Not yet enforced".
    expect(screen.getByRole("button", { name: "Shift5" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Comfortable" })).toBeEnabled();
    expect(screen.getByLabelText("Time zone")).toBeEnabled();
  });

  it("drops the general Save/Discard footer (nothing to persist on these sections)", () => {
    renderPage();

    expect(screen.queryByRole("button", { name: "Save changes" })).not.toBeInTheDocument();
  });

  it("opens the Security section directly when the URL deep-links to it", () => {
    renderPage(["/settings?section=security"]);

    // The Security navigation button is selected (aria-current=page).
    // Inside the panel the API-backed threshold form is in its loading
    // state because no fetch resolves in this isolated render — the
    // loading-state copy is unique to the Security section and proves
    // the deep-link landed there.
    expect(
      screen.getByRole("button", { name: /^Security/u }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      screen.getByText(/Loading operator-tunable VSIX hardening thresholds/u),
    ).toBeInTheDocument();
  });

  it("surfaces the error message when the threshold query fails (regression: infinite loading on API error)", async () => {
    // The previous order of guard clauses (`isLoading || !persisted`
    // before `isError`) collapsed every failed first fetch into the
    // loading copy because React Query reports a rejected query as
    // `isLoading=false, isError=true, data=undefined`. An operator
    // arriving here from a VSIX threshold-breach popup with the API
    // down would have been stuck on "Loading…" forever instead of
    // seeing the real cause. Pin the corrected order.
    vi.mocked(apiClient.getSecurityThresholds).mockReset();
    vi.mocked(apiClient.getSecurityThresholds).mockRejectedValueOnce(
      new ApiError("Service Unavailable", 503),
    );

    renderPage(["/settings?section=security"]);

    expect(
      await screen.findByText(/Could not load thresholds/u),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/Loading operator-tunable VSIX hardening thresholds/u),
    ).not.toBeInTheDocument();
  });
});
