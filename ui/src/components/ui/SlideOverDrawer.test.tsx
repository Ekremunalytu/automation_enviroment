import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { SlideOverDrawer } from "./SlideOverDrawer";

function Harness() {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button onClick={() => setOpen(true)} type="button">
        Open filters
      </button>
      <SlideOverDrawer
        description="Filter the active evidence stream."
        onClose={() => setOpen(false)}
        open={open}
        title="Evidence filters"
      >
        <div>Drawer body</div>
      </SlideOverDrawer>
    </div>
  );
}

describe("SlideOverDrawer", () => {
  it("moves focus into the dialog, exposes the dismiss label, and restores focus on close", async () => {
    render(<Harness />);

    const trigger = screen.getByRole("button", { name: "Open filters" });
    trigger.focus();
    fireEvent.click(trigger);

    expect(screen.getByRole("dialog", { name: "Evidence filters" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close filters" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close" })).toHaveFocus();

    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "Evidence filters" })).not.toBeInTheDocument();
      expect(trigger).toHaveFocus();
    });
  });
});
