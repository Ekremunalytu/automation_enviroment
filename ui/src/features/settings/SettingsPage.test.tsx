import { fireEvent, render, screen } from "@testing-library/react";

import { SettingsPage } from "./SettingsPage";

describe("SettingsPage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("renders the v3 header with the backend-pending stub badge and the four sections", () => {
    render(<SettingsPage />);

    expect(screen.getByText(/Configure/u)).toBeInTheDocument();
    expect(screen.getByText(/the appliance/u)).toBeInTheDocument();
    expect(screen.getByText(/Backend pending/u)).toBeInTheDocument();
    for (const label of ["General", "Executor", "Telemetry", "Danger"]) {
      expect(screen.getByRole("button", { name: new RegExp(`^${label}`, "i") })).toBeInTheDocument();
    }
  });

  it("toggles the auto-analyze switch and persists settings to localStorage on save", () => {
    render(<SettingsPage />);

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
    render(<SettingsPage />);

    fireEvent.click(screen.getByRole("button", { name: /^Executor/u }));
    const toggle = screen.getByRole("button", { name: "Auto-analyze on download" });
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(screen.getByRole("button", { name: "Discard" }));
    expect(toggle).toHaveAttribute("aria-pressed", "true");
  });
});
