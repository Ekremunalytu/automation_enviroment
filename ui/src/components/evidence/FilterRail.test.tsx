import { fireEvent, render, screen } from "@testing-library/react";
import { FilterRail, type EvidenceFilterState } from "./FilterRail";

describe("FilterRail", () => {
  it("keeps the search input in sync with the latest filter state", () => {
    let filters: EvidenceFilterState = {
      kinds: [],
      actors: [],
      collectors: [],
      scenarios: [],
      sensitiveOnly: false,
      search: "",
    };

    const { rerender } = render(
      <FilterRail
        filters={filters}
        onChange={(next) => {
          filters = next;
          rerender(
            <FilterRail
              filters={filters}
              onChange={() => undefined}
              options={{ kinds: [], actors: [], collectors: [], scenarios: [] }}
            />,
          );
        }}
        options={{ kinds: [], actors: [], collectors: [], scenarios: [] }}
      />,
    );

    const searchInput = screen.getByRole("textbox", { name: "Search" });
    fireEvent.change(searchInput, { target: { value: "secret.env" } });

    expect(screen.getByRole("textbox", { name: "Search" })).toHaveValue(
      "secret.env",
    );
  });
});
