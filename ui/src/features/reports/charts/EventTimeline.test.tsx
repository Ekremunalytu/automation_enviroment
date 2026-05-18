import { render, screen } from "@testing-library/react";
import { EventTimeline } from "./EventTimeline";
import { DISPLAY_CAPS } from "../../../lib/displayCaps";

type ChartEvent = {
  id: string;
  label?: string;
  relTimeS?: number | null;
  kind?: string;
  risk?: "low" | "medium" | "high";
};

const KINDS: Array<"activation" | "file" | "network"> = ["activation", "file", "network"];

function makeEvent(
  index: number,
  t: number | null | undefined,
  overrides: Partial<ChartEvent> = {},
): ChartEvent {
  return {
    id: `evt-${index}`,
    label: `Event ${index}`,
    relTimeS: t,
    kind: KINDS[index % KINDS.length],
    risk: "low",
    ...overrides,
  };
}

function makeAscending(count: number): ChartEvent[] {
  return Array.from({ length: count }, (_, index) => makeEvent(index, index * 0.01));
}

describe("EventTimeline", () => {
  it("renders the empty-state branch without indicator when events are absent", () => {
    render(<EventTimeline events={[]} />);
    expect(screen.getByText(/awaiting timeline data/iu)).toBeInTheDocument();
    expect(screen.queryByTestId("timeline-truncation-indicator")).not.toBeInTheDocument();
    expect(screen.queryAllByTestId("timeline-event-marker")).toHaveLength(0);
  });

  it("renders every event when count is below the cap (no indicator)", () => {
    render(<EventTimeline events={makeAscending(50)} />);
    expect(screen.queryByTestId("timeline-truncation-indicator")).not.toBeInTheDocument();
    expect(screen.getAllByTestId("timeline-event-marker")).toHaveLength(50);
  });

  it("renders exactly the cap when events exceed the cap", () => {
    const total = DISPLAY_CAPS.TIMELINE_EVENTS + 17;
    render(<EventTimeline events={makeAscending(total)} />);
    expect(screen.getAllByTestId("timeline-event-marker")).toHaveLength(DISPLAY_CAPS.TIMELINE_EVENTS);
  });

  it("surfaces the truncation indicator with overflow count and locale-formatted totals", () => {
    const total = DISPLAY_CAPS.TIMELINE_EVENTS + 434;
    render(<EventTimeline events={makeAscending(total)} />);
    const indicator = screen.getByTestId("timeline-truncation-indicator");
    expect(indicator.textContent).toMatch(/\+434 more/u);
    expect(indicator.textContent).toMatch(/first 800 of/u);
    expect(indicator.textContent).toMatch(/1[,.  ]?234/u);
    expect(indicator.textContent).toMatch(/events/u);
  });

  it("omits the indicator when event count equals the cap exactly (boundary)", () => {
    render(<EventTimeline events={makeAscending(DISPLAY_CAPS.TIMELINE_EVENTS)} />);
    expect(screen.queryByTestId("timeline-truncation-indicator")).not.toBeInTheDocument();
    expect(screen.getAllByTestId("timeline-event-marker")).toHaveLength(DISPLAY_CAPS.TIMELINE_EVENTS);
  });

  it("applies the cap after the chronological sort so visible events are first-N by time", () => {
    const total = DISPLAY_CAPS.TIMELINE_EVENTS + 4;
    // index N has t = (total-1-N) * 0.01: low index = HIGH t, high index = LOW t.
    // After chronological sort + cap, the four highest-t events (index 0..3) get dropped;
    // the lowest-t event (index total-1, t=0) is kept.
    const reverseSorted = Array.from({ length: total }, (_, index) =>
      makeEvent(index, (total - 1 - index) * 0.01),
    );
    const lowestT = `evt-${total - 1}`;
    const { rerender } = render(<EventTimeline events={reverseSorted} selectedId={lowestT} />);
    expect(screen.getByTestId("timeline-truncation-indicator")).toBeInTheDocument();
    expect(screen.getAllByTestId("timeline-event-marker")).toHaveLength(DISPLAY_CAPS.TIMELINE_EVENTS);
    expect(screen.queryByText(`Event ${total - 1}`)).toBeInTheDocument();

    rerender(<EventTimeline events={reverseSorted} selectedId="evt-0" />);
    expect(screen.queryByText(/^Event 0$/u)).not.toBeInTheDocument();
  });

  it("filters non-finite relTimeS events out before the cap is applied", () => {
    const valid = makeAscending(DISPLAY_CAPS.TIMELINE_EVENTS);
    const noise: ChartEvent[] = [
      makeEvent(9001, Number.NaN),
      makeEvent(9002, null),
      makeEvent(9003, Number.POSITIVE_INFINITY),
      makeEvent(9004, undefined as unknown as number),
      makeEvent(9005, 12, { kind: "unknown" }),
    ];
    render(<EventTimeline events={[...noise, ...valid]} />);
    expect(screen.queryByTestId("timeline-truncation-indicator")).not.toBeInTheDocument();
    expect(screen.getAllByTestId("timeline-event-marker")).toHaveLength(DISPLAY_CAPS.TIMELINE_EVENTS);
  });
});
