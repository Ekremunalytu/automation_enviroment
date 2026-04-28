import { useMemo } from "react";

import { RISK_COLOR, V3, type Risk } from "../../../components/v3";

type RiskEvent = {
  id: string;
  relTimeS?: number | null;
  risk?: Risk | null;
};

type RiskStripProps = {
  events: ReadonlyArray<RiskEvent>;
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  height?: number;
};

export function RiskStrip({ events, selectedId = null, onSelect, height = 76 }: RiskStripProps) {
  const points = useMemo(() => {
    const valid = events.filter(
      (event): event is RiskEvent & { relTimeS: number } =>
        typeof event.relTimeS === "number" && Number.isFinite(event.relTimeS),
    );
    if (!valid.length) return null;
    const min = Math.min(...valid.map((event) => event.relTimeS), 0);
    const max = Math.max(...valid.map((event) => event.relTimeS), min + 1);
    const span = max - min || 1;
    return {
      min,
      max,
      span,
      data: valid.map((event) => ({
        id: event.id,
        risk: (event.risk ?? "low") as Risk,
        x: ((event.relTimeS - min) / span) * 100,
      })),
    };
  }, [events]);

  const width = 600;

  if (!points) {
    return (
      <div
        style={{
          height,
          border: `1px dashed ${V3.rule2}`,
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

  return (
    <svg
      role="img"
      aria-label="Risk timeline"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      style={{ width: "100%", height, display: "block" }}
    >
      <line
        x1={0}
        x2={width}
        y1={height / 2}
        y2={height / 2}
        stroke={V3.rule2}
        strokeWidth={1}
      />
      {ticks.map((ratio, index) => {
        const x = ratio * width;
        const seconds = points.min + ratio * points.span;
        return (
          <g key={`tick-${index}`}>
            <line
              x1={x}
              x2={x}
              y1={height / 2 - 6}
              y2={height / 2 + 6}
              stroke={V3.rule2}
              strokeWidth={1}
            />
            <text
              x={x}
              y={height - 6}
              textAnchor="middle"
              fontFamily="'JetBrains Mono', monospace"
              fontSize={9}
              fill={V3.ink4}
              letterSpacing="0.12em"
            >
              {seconds.toFixed(1)}s
            </text>
          </g>
        );
      })}
      {points.data.map((entry) => {
        const cx = (entry.x / 100) * width;
        const cy = height / 2;
        const isSelected = entry.id === selectedId;
        return (
          <g key={entry.id}>
            <line
              x1={cx}
              x2={cx}
              y1={cy - 14}
              y2={cy + 14}
              stroke={RISK_COLOR[entry.risk]}
              strokeWidth={isSelected ? 2 : 1}
              opacity={isSelected ? 1 : 0.6}
            />
            <circle
              cx={cx}
              cy={cy}
              r={isSelected ? 5 : 3.5}
              fill={RISK_COLOR[entry.risk]}
              stroke={isSelected ? V3.ink : "none"}
              strokeWidth={isSelected ? 1.5 : 0}
              style={{ cursor: onSelect ? "pointer" : undefined }}
              onClick={() => onSelect?.(entry.id)}
            />
          </g>
        );
      })}
    </svg>
  );
}
