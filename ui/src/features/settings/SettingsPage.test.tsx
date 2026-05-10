import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";

import { apiClient } from "../../lib/api/client";
import { ApiError } from "../../lib/api/http";
import { SettingsPage } from "./SettingsPage";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    getSecurityThresholds: vi.fn(),
    updateSecurityThresholds: vi.fn(),
  },
}));

function renderPage(initialEntries: string[] = ["/settings"]): void {
  // SettingsPage now uses useSearchParams (Stage 7 deep-link target for
  // the Marketplace popup) and useQuery (security thresholds). The
  // MemoryRouter satisfies the routing context; the QueryClientProvider
  // makes the Security tab's network calls inert when the test focuses on
  // the localStorage-backed sections.
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
    // Default: hang the threshold fetch so the Security tab stays in its
    // loading state. Tests that need a different terminal state override
    // this via `mockRejectedValueOnce` / `mockResolvedValueOnce`.
    vi.mocked(apiClient.getSecurityThresholds).mockReturnValue(
      new Promise<never>(() => undefined),
    );
  });

  it("renders the v3 header and the five sections without placeholder badges", () => {
    renderPage();

    expect(screen.getByText(/Configure/u)).toBeInTheDocument();
    expect(screen.getByText(/the appliance/u)).toBeInTheDocument();
    expect(screen.getByText(/General console options stay in this browser/u)).toBeInTheDocument();
    expect(screen.getByText(/security thresholds are persisted by the local API/u)).toBeInTheDocument();
    expect(screen.queryByText(/Backend pending/u)).not.toBeInTheDocument();
    for (const label of ["General", "Executor", "Security", "Telemetry", "Danger"]) {
      expect(screen.getByRole("button", { name: new RegExp(`^${label}`, "i") })).toBeInTheDocument();
    }
  });

  it("toggles the auto-analyze switch and persists settings to localStorage on save", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: /^Executor/u }));
    const toggle = screen.getByRole("button", { name: "Auto-analyze on download" });
    expect(toggle).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    const stored = window.localStorage.getItem("extrace-v3-settings");
    expect(stored).not.toBeNull();
    const parsed = JSON.parse(stored ?? "{}") as { autoAnalyze: boolean };
    expect(parsed.autoAnalyze).toBe(false);
  });

  it("discards in-flight changes back to the persisted snapshot", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: /^Executor/u }));
    const toggle = screen.getByRole("button", { name: "Auto-analyze on download" });
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(screen.getByRole("button", { name: "Discard" }));
    expect(toggle).toHaveAttribute("aria-pressed", "true");
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
