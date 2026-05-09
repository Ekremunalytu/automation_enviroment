import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";

import { SettingsPage } from "./SettingsPage";

function renderPage(initialEntries: string[] = ["/settings"]): void {
  // SettingsPage now uses useSearchParams (Stage 7 deep-link target for
  // the Marketplace popup) and useQuery (security thresholds). The
  // MemoryRouter satisfies the routing context; the QueryClientProvider
  // makes the Security tab's network calls inert when the test focuses on
  // the localStorage-backed sections.
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
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
  });

  it("renders the v3 header and the five sections without placeholder badges", () => {
    renderPage();

    expect(screen.getByText(/Configure/u)).toBeInTheDocument();
    expect(screen.getByText(/the appliance/u)).toBeInTheDocument();
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
});
