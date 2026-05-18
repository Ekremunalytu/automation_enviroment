import { DISPLAY_CAPS, applyDisplayCap, formatTruncationLabel } from "./displayCaps";

describe("applyDisplayCap", () => {
  it("returns the input array reference when below the cap", () => {
    const items = [1, 2, 3];
    const result = applyDisplayCap(items, 10);
    expect(result.truncated).toBe(false);
    expect(result.overflowCount).toBe(0);
    expect(result.totalCount).toBe(3);
    expect(result.visible).toBe(items);
  });

  it("returns truncated:false when count equals the cap exactly (boundary)", () => {
    const items = [1, 2, 3];
    const result = applyDisplayCap(items, 3);
    expect(result.truncated).toBe(false);
    expect(result.overflowCount).toBe(0);
    expect(result.totalCount).toBe(3);
    expect(result.visible.length).toBe(3);
  });

  it("slices to the cap and marks truncated when count exceeds the cap", () => {
    const items = Array.from({ length: 1234 }, (_, index) => index);
    const result = applyDisplayCap(items, 800);
    expect(result.truncated).toBe(true);
    expect(result.overflowCount).toBe(434);
    expect(result.totalCount).toBe(1234);
    expect(result.visible.length).toBe(800);
    expect(result.visible[0]).toBe(0);
    expect(result.visible[799]).toBe(799);
  });

  it("handles an empty input without marking truncated", () => {
    const result = applyDisplayCap<number>([], 800);
    expect(result.truncated).toBe(false);
    expect(result.overflowCount).toBe(0);
    expect(result.totalCount).toBe(0);
    expect(result.visible).toEqual([]);
  });

  it("treats cap=0 defensively (truncated when items present, visible empty)", () => {
    const items = [1, 2, 3];
    const result = applyDisplayCap(items, 0);
    expect(result.truncated).toBe(true);
    expect(result.overflowCount).toBe(3);
    expect(result.totalCount).toBe(3);
    expect(result.visible).toEqual([]);
  });
});

describe("formatTruncationLabel", () => {
  it("returns empty string when not truncated", () => {
    const label = formatTruncationLabel({
      visible: [1, 2],
      truncated: false,
      overflowCount: 0,
      totalCount: 2,
    });
    expect(label).toBe("");
  });

  it("includes overflow count, locale-formatted totals, and default noun when truncated", () => {
    const visible = Array.from({ length: 800 }, (_, index) => index);
    const label = formatTruncationLabel({
      visible,
      truncated: true,
      overflowCount: 434,
      totalCount: 1234,
    });
    expect(label).toContain("+434 more");
    expect(label).toMatch(/first 800 of 1\D?234/u);
    expect(label).toContain("items");
    expect(label).toContain("filter to narrow");
  });
});

describe("DISPLAY_CAPS constants", () => {
  it("preserves InteractionGraph leaf/group caps (value-preserving)", () => {
    expect(DISPLAY_CAPS.RELATIONS_GROUPS).toBe(5);
    expect(DISPLAY_CAPS.RELATIONS_LEAVES_PER_GROUP).toBe(6);
  });
});
