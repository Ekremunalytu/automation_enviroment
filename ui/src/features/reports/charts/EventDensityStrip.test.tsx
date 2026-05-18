import { fireEvent, render, screen } from "@testing-library/react";
import { EventDensityStrip, type DensityEvent } from "./EventDensityStrip";
import { DISPLAY_CAPS } from "../../../lib/displayCaps";

function makeEvent(index: number, t: number, overrides: Partial<DensityEvent> = {}): DensityEvent {
  return {
    id: `evt-${index}`,
    label: `Event ${index}`,
    relTimeS: t,
    kind: "network",
    risk: "low",
    ...overrides,
  };
}

describe("EventDensityStrip", () => {
  it("renders bucket placeholders with no truncation indicator when events are absent", () => {
    render(<EventDensityStrip events={[]} onSelect={() => {}} />);
    expect(screen.queryByTestId("density-truncation-indicator")).not.toBeInTheDocument();
    const buckets = screen.getAllByTestId("density-bucket");
    expect(buckets.length).toBeGreaterThanOrEqual(1);
    buckets.forEach((bucket) => {
      expect(bucket).toBeDisabled();
    });
  });

  it("bucket count reflects the maxT of the post-cap event set", () => {
    const compressed = Array.from({ length: DISPLAY_CAPS.EVENT_DENSITY_EVENTS }, (_, index) =>
      makeEvent(index, (index * 0.001) % 0.8),
    );
    const outlier = makeEvent(9999, 100);
    render(<EventDensityStrip events={[...compressed, outlier]} onSelect={() => {}} />);
    const buckets = screen.getAllByTestId("density-bucket");
    expect(buckets.length).toBeLessThanOrEqual(5);
    expect(screen.getByTestId("density-truncation-indicator")).toBeInTheDocument();
  });

  it("does not render the truncation row when event count is below the cap", () => {
    const events = Array.from({ length: 32 }, (_, index) => makeEvent(index, index * 0.1));
    render(<EventDensityStrip events={events} onSelect={() => {}} />);
    expect(screen.queryByTestId("density-truncation-indicator")).not.toBeInTheDocument();
  });

  it("renders the truncation row with overflow count and density-reflects copy when events exceed the cap", () => {
    const overflow = 123;
    const total = DISPLAY_CAPS.EVENT_DENSITY_EVENTS + overflow;
    const events = Array.from({ length: total }, (_, index) => makeEvent(index, (index % 5) * 0.5));
    render(<EventDensityStrip events={events} onSelect={() => {}} />);
    const indicator = screen.getByTestId("density-truncation-indicator");
    expect(indicator.textContent).toMatch(/\+123 events truncated/u);
    expect(indicator.textContent).toMatch(/density reflects first 800/u);
  });

  it("omits the truncation row when event count equals the cap exactly", () => {
    const events = Array.from({ length: DISPLAY_CAPS.EVENT_DENSITY_EVENTS }, (_, index) =>
      makeEvent(index, (index % 5) * 0.5),
    );
    render(<EventDensityStrip events={events} onSelect={() => {}} />);
    expect(screen.queryByTestId("density-truncation-indicator")).not.toBeInTheDocument();
  });

  it("invokes onSelect with the first event id of a clicked bucket", () => {
    const events: DensityEvent[] = [
      makeEvent(0, 0.1, { id: "first-in-bucket-0" }),
      makeEvent(1, 0.4, { id: "second-in-bucket-0" }),
      makeEvent(2, 2.5, { id: "first-in-bucket-2" }),
    ];
    const onSelect = vi.fn();
    render(<EventDensityStrip events={events} onSelect={onSelect} />);
    const buckets = screen.getAllByTestId("density-bucket");
    const clickable = buckets.filter((bucket) => !(bucket as HTMLButtonElement).disabled);
    expect(clickable.length).toBeGreaterThanOrEqual(2);
    fireEvent.click(clickable[0]);
    expect(onSelect).toHaveBeenCalledWith("first-in-bucket-0");
  });
});
