import { useMemo } from "react";

import { V3 } from "../../../components/v3";

type ActivityBarsProps = {
  events: ReadonlyArray<{ relTimeS?: number | null }>;
  height?: number;
  bins?: number;
  selectedRelTimeS?: number | null;
};

export function ActivityBars({
  events,
  height = 80,
  bins = 20,
  selectedRelTimeS = null,
}: ActivityBarsProps) {
  const { binCounts, maxCount, span } = useMemo(() => {
    const times = events
      .map((event) => event.relTimeS)
      .filter((value): value is number => typeof value === "number" && Number.isFinite(value));
    if (!times.length) {
      return { binCounts: new Array<number>(bins).fill(0), maxCount: 0, span: 0 };
    }
    const min = Math.min(...times, 0);
    const max = Math.max(...times, min + 1);
    const total = max - min || 1;
    const counts = new Array<number>(bins).fill(0);
    for (const value of times) {
      const index = Math.min(bins - 1, Math.max(0, Math.floor(((value - min) / total) * bins)));
      counts[index] += 1;
    }
    const maxBin = Math.max(...counts, 1);
    return { binCounts: counts, maxCount: maxBin, span: total };
  }, [events, bins]);

  const width = 600;
  const barWidth = width / bins;
  const playheadX = (() => {
    if (selectedRelTimeS == null || !span) return null;
    const min = events.reduce<number | null>((acc, event) => {
      const value = event.relTimeS;
      if (typeof value !== "number") return acc;
      return acc == null ? value : Math.min(acc, value);
    }, null);
    if (min == null) return null;
    return Math.min(width, Math.max(0, ((selectedRelTimeS - min) / span) * width));
  })();

  return (
    <svg
      role="img"
      aria-label="Activity histogram"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      style={{ width: "100%", height, display: "block" }}
    >
      <line x1={0} x2={width} y1={height - 1} y2={height - 1} stroke={V3.rule2} strokeWidth={1} />
      {binCounts.map((count, index) => {
        const h = maxCount === 0 ? 0 : (count / maxCount) * (height - 8);
        const x = index * barWidth + 1;
        const y = height - h - 1;
        const isSelected =
          playheadX != null && x <= playheadX && playheadX < x + barWidth - 1;
        return (
          <rect
            key={index}
            x={x}
            y={y}
            width={Math.max(0, barWidth - 2)}
            height={h}
            fill={isSelected ? V3.coral : V3.ink3}
            opacity={count === 0 ? 0.18 : 1}
          />
        );
      })}
      {playheadX != null ? (
        <line
          x1={playheadX}
          x2={playheadX}
          y1={0}
          y2={height}
          stroke={V3.coral}
          strokeWidth={1.5}
          strokeDasharray="4 4"
        />
      ) : null}
    </svg>
  );
}
