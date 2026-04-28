import { useMemo } from "react";

import { V3 } from "../../../components/v3";

export const RADAR_AXES = ["Threat", "Exfil", "Persistence", "Privesc", "Defense", "Resource"] as const;
export type RadarAxis = (typeof RADAR_AXES)[number];

export type RadarScore = Record<RadarAxis, number> & { _synthetic?: boolean };

type RiskRadarProps = {
  scores: RadarScore;
  size?: number;
};

export function RiskRadar({ scores, size = 320 }: RiskRadarProps) {
  const points = useMemo(() => {
    return RADAR_AXES.map((axis, index) => {
      const angle = (Math.PI * 2 * index) / RADAR_AXES.length - Math.PI / 2;
      const value = clamp01(scores[axis] / 100);
      return {
        axis,
        angle,
        value,
      };
    });
  }, [scores]);

  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - 32;

  const polygon = points
    .map((point) => {
      const r = radius * point.value;
      const x = cx + Math.cos(point.angle) * r;
      const y = cy + Math.sin(point.angle) * r;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");

  const labels = points.map((point) => {
    const labelDist = radius + 14;
    const x = cx + Math.cos(point.angle) * labelDist;
    const y = cy + Math.sin(point.angle) * labelDist;
    return { ...point, x, y };
  });

  const rings = [0.25, 0.5, 0.75, 1];

  return (
    <svg
      role="img"
      aria-label="Risk radar"
      viewBox={`0 0 ${size} ${size}`}
      style={{ width: "100%", maxWidth: size, height: "auto", display: "block" }}
    >
      {rings.map((ratio) => (
        <circle
          key={ratio}
          cx={cx}
          cy={cy}
          r={radius * ratio}
          stroke={V3.rule}
          strokeWidth={1}
          fill="none"
        />
      ))}
      {points.map((point, index) => {
        const x = cx + Math.cos(point.angle) * radius;
        const y = cy + Math.sin(point.angle) * radius;
        return (
          <line
            key={`axis-${index}`}
            x1={cx}
            y1={cy}
            x2={x}
            y2={y}
            stroke={V3.rule2}
            strokeWidth={1}
          />
        );
      })}
      <polygon
        points={polygon}
        fill={V3.coral}
        fillOpacity={0.18}
        stroke={V3.coral}
        strokeWidth={1.5}
        className="animate-radarBreath"
      />
      <g
        transform={`rotate(0 ${cx} ${cy})`}
        className="animate-radarSweep"
        style={{ transformOrigin: `${cx}px ${cy}px` }}
      >
        <line
          x1={cx}
          y1={cy}
          x2={cx}
          y2={cy - radius}
          stroke={V3.coral}
          strokeWidth={1.2}
          opacity={0.6}
          strokeDasharray="2 4"
        />
      </g>
      {labels.map((label, index) => (
        <text
          key={`label-${index}`}
          x={label.x}
          y={label.y}
          textAnchor="middle"
          dominantBaseline="middle"
          fontFamily="'JetBrains Mono', monospace"
          fontSize={10}
          fill={V3.ink3}
          letterSpacing="0.12em"
        >
          {label.axis.toUpperCase()}
        </text>
      ))}
    </svg>
  );
}

function clamp01(value: number): number {
  if (Number.isNaN(value)) return 0;
  return Math.max(0, Math.min(1, value));
}
