import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { AppShell } from "./AppShell";

describe("AppShell", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("marks the rail item matching the current path as active", () => {
    render(
      <MemoryRouter initialEntries={["/simulation?job=job-1&tab=live"]}>
        <AppShell>
          <div>Workspace body</div>
        </AppShell>
      </MemoryRouter>,
    );

    expect(screen.getByText("ExTrace")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Simulation/i })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("button", { name: /^Reports/i })).not.toHaveAttribute("aria-current");
  });

  it("exposes all five v3 nav targets including Settings and System", () => {
    render(
      <MemoryRouter initialEntries={["/reports"]}>
        <AppShell>
          <div>Workspace body</div>
        </AppShell>
      </MemoryRouter>,
    );

    for (const label of ["Reports", "Simulation", "Marketplace", "Settings", "System"]) {
      const pattern = new RegExp(`^${label}`, "i");
      expect(screen.getByRole("button", { name: pattern })).toBeInTheDocument();
    }
  });

  it("toggles collapsed state via the masthead button and persists to localStorage", () => {
    render(
      <MemoryRouter initialEntries={["/reports"]}>
        <AppShell>
          <div>Workspace body</div>
        </AppShell>
      </MemoryRouter>,
    );

    const toggle = screen.getByRole("button", { name: "Collapse sidebar" });
    expect(toggle).toHaveAttribute("aria-expanded", "true");

    fireEvent.click(toggle);

    expect(screen.getByRole("button", { name: "Expand sidebar" })).toHaveAttribute("aria-expanded", "false");
    expect(window.localStorage.getItem("extrace-v3-rail")).toBe("1");
  });
});
