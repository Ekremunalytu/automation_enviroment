import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppShell } from "./AppShell";

describe("AppShell", () => {
  it("renders the top navigation shell and current section actions", () => {
    render(
      <MemoryRouter initialEntries={["/simulation?job=job-1&tab=live"]}>
        <AppShell>
          <div>Workspace body</div>
        </AppShell>
      </MemoryRouter>,
    );

    expect(screen.getByText("ExTrace")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Simulation" })).toHaveClass("nav-button-active");
    expect(screen.getAllByRole("link", { name: /Latest Report/u }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /New Analysis/u }).length).toBeGreaterThan(0);
    expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  });
});
