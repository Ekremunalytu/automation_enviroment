import { useMemo } from "react";

import { RISK_COLOR, V3, type Risk } from "../../../components/v3";

type TimelineEvent = {
  id: string;
  label?: string;
  relTimeS?: number | null;
  kind?: string;
  risk?: Risk;
};

type EventTimelineProps = {
  events: ReadonlyArray<TimelineEvent>;
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  height?: number;
};

export function EventTimeline({ events, selectedId, onSelect, height = 140 }: EventTimelineProps) {
  const span = useMemo(() => {
    const times = events
      .map((event) => event.relTimeS)
      .filter((value): value is number => typeof value === "number" && Number.isFinite(value));
    if (!times.length) return null;
    const min = Math.min(...times, 0);
    const max = Math.max(...times, min + 1);
    return { min, max, total: max - min || 1 };
  }, [events]);

  const width = 720;

  if (!span) {
    return (
      <div
        style={{
          height,
          border: `1px dashed ${V3.rule2}`,
          background: V3.paper2,
          color: V3.ink4,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 11,
          letterSpacing: "0.12em",
          textTransform: "uppercase",
        }}
      >
        Awaiting timeline data
      </div>
    );
  }

  const ticks = [0, 0.5, 1];
  const baselineY = height - 36;

  return (
    <svg
      role="img"
      aria-label="Event timeline"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      style={{ width: "100%", height, display: "block" }}
    >
      <line
        x1={0}
        x2={width}
        y1={baselineY}
        y2={baselineY}
        stroke={V3.rule2}
        strokeWidth={1}
      />
      {ticks.map((ratio, index) => {
        const x = ratio * width;
        const seconds = span.min + ratio * span.total;
        return (
          <g key={`tick-${index}`}>
            <line
              x1={x}
              x2={x}
              y1={baselineY - 6}
              y2={baselineY + 6}
              stroke={V3.rule2}
              strokeWidth={1}
            />
            <text
              x={x}
              y={height - 8}
              textAnchor="middle"
              fontFamily="'JetBrains Mono', monospace"
              fontSize={10}
              fill={V3.ink4}
              letterSpacing="0.12em"
            >
              {seconds.toFixed(1)}s
            </text>
          </g>
        );
      })}
      {events.map((event) => {
        const time = event.relTimeS ?? span.min;
        const cx = ((time - span.min) / span.total) * width;
        const risk = event.risk ?? "low";
        const fill = RISK_COLOR[risk];
        const isSelected = event.id === selectedId;
        const stemHeight = 24 + (event.kind === "network" ? 18 : event.kind === "file" ? 12 : 6);
        const stemTop = baselineY - stemHeight;
        return (
          <g key={event.id}>
            <line
              x1={cx}
              x2={cx}
              y1={stemTop}
              y2={baselineY}
              stroke={fill}
              strokeWidth={isSelected ? 2 : 1}
              opacity={isSelected ? 1 : 0.65}
            />
            <circle
              cx={cx}
              cy={stemTop}
              r={isSelected ? 5.5 : 4}
              fill={fill}
              stroke={isSelected ? V3.ink : "none"}
              strokeWidth={isSelected ? 1.5 : 0}
              style={{ cursor: onSelect ? "pointer" : undefined }}
              onClick={() => onSelect?.(event.id)}
            />
            {isSelected && event.label ? (
              <text
                x={cx}
                y={Math.max(12, stemTop - 8)}
                textAnchor="middle"
                fontFamily="'JetBrains Mono', monospace"
                fontSize={10}
                fill={V3.ink}
                letterSpacing="0.06em"
              >
                {event.label}
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}
