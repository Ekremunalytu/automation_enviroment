export const DISPLAY_CAPS = {
  TIMELINE_EVENTS: 800,
  EVENT_DENSITY_EVENTS: 800,
  RELATIONS_GROUPS: 5,
  RELATIONS_LEAVES_PER_GROUP: 6,
} as const;

export type CappedList<T> = {
  visible: ReadonlyArray<T>;
  truncated: boolean;
  overflowCount: number;
  totalCount: number;
};

export function applyDisplayCap<T>(items: ReadonlyArray<T>, cap: number): CappedList<T> {
  const totalCount = items.length;
  if (cap <= 0) {
    return {
      visible: [],
      truncated: totalCount > 0,
      overflowCount: totalCount,
      totalCount,
    };
  }
  if (totalCount <= cap) {
    return {
      visible: items,
      truncated: false,
      overflowCount: 0,
      totalCount,
    };
  }
  return {
    visible: items.slice(0, cap),
    truncated: true,
    overflowCount: totalCount - cap,
    totalCount,
  };
}

export function formatTruncationLabel(c: CappedList<unknown>, noun = "items"): string {
  if (!c.truncated) return "";
  return `+${c.overflowCount.toLocaleString()} more · showing first ${c.visible.length.toLocaleString()} of ${c.totalCount.toLocaleString()} ${noun} · filter to narrow`;
}
