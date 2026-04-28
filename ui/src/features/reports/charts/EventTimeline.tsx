import { useEffect, useMemo, useRef, useState } from "react";

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
  const [playing, setPlaying] = useState(false);
  const [cursor, setCursor] = useState(0);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const frameRef = useRef<number | null>(null);
  const startedRef = useRef<number | null>(null);

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

  useEffect(() => {
    if (!playing) {
      if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
      startedRef.current = null;
      return;
    }

    const duration = 6000;
    const step = (timestamp: number) => {
      if (startedRef.current === null) startedRef.current = timestamp - cursor * duration;
      const next = Math.min(1, (timestamp - startedRef.current) / duration);
      setCursor(next);
      if (next >= 1) {
        setPlaying(false);
        return;
      }
      frameRef.current = window.requestAnimationFrame(step);
    };

    frameRef.current = window.requestAnimationFrame(step);
    return () => {
      if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
    };
  }, [cursor, playing]);

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

  const lanes = [
    { kind: "activation", label: "Activation", color: V3.coral },
    { kind: "file", label: "File", color: V3.warn },
    { kind: "network", label: "Network", color: V3.ok },
  ] as const;
  const ticks = [0, 0.25, 0.5, 0.75, 1];
  const left = 112;
  const right = 20;
  const top = 26;
  const bottom = 34;
  const innerWidth = width - left - right;
  const laneStep = (height - top - bottom) / lanes.length;
  const selectedEvent = events.find((event) => event.id === selectedId);
  const selectedX =
    selectedEvent && typeof selectedEvent.relTimeS === "number"
      ? left + ((selectedEvent.relTimeS - span.min) / span.total) * innerWidth
      : null;
  const cursorX = left + cursor * innerWidth;
  const playheadX = selectedX ?? cursorX;

  return (
    <div style={{ border: `1px solid ${V3.rule}`, background: V3.paper }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 14,
          padding: "10px 14px",
          borderBottom: `1px solid ${V3.rule}`,
          background: V3.paper2,
        }}
      >
        <button
          type="button"
          onClick={() => {
            if (cursor >= 0.999) setCursor(0);
            setPlaying((value) => !value);
          }}
          style={{
            border: `1px solid ${V3.ink}`,
            background: playing ? V3.ink : V3.paper,
            color: playing ? V3.paper : V3.ink,
            padding: "5px 10px",
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11,
            letterSpacing: "0.08em",
            textTransform: "lowercase",
            minWidth: 78,
            cursor: "pointer",
          }}
        >
          {playing ? "pause" : "scan"}
        </button>
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10.5,
            color: V3.ink3,
            letterSpacing: "0.06em",
          }}
        >
          t = {(cursor * span.total + span.min).toFixed(1)}s / {span.max.toFixed(1)}s · {events.length} events
        </span>
      </div>
      <svg
        role="img"
        aria-label="Event timeline"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        style={{ width: "100%", height, display: "block" }}
      >
      <rect x={0} y={0} width={width} height={height} fill={V3.paper2} />
      {lanes.map((lane, index) => {
        const y = top + index * laneStep + laneStep / 2;
        return (
          <g key={lane.kind}>
            <text
              x={12}
              y={y + 4}
              fontFamily="'JetBrains Mono', monospace"
              fontSize={10}
              fill={V3.ink3}
              letterSpacing="0.1em"
            >
              {lane.label}
            </text>
            <line
              x1={left}
              x2={width - right}
              y1={y}
              y2={y}
              stroke={V3.rule}
              strokeWidth={1}
            />
            <rect x={left} y={y - 10} width={2} height={20} fill={lane.color} opacity={0.8} />
          </g>
        );
      })}
      {ticks.map((ratio, index) => {
        const x = left + ratio * innerWidth;
        const seconds = span.min + ratio * span.total;
        return (
          <g key={`tick-${index}`}>
            <line
              x1={x}
              x2={x}
              y1={top - 6}
              y2={height - bottom + 10}
              stroke={V3.rule2}
              strokeWidth={1}
              opacity={0.45}
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
      {playheadX !== null ? (
        <g>
          <line x1={playheadX} x2={playheadX} y1={top - 10} y2={height - bottom + 14} stroke={V3.coral} strokeWidth={1.5} strokeDasharray={selectedX === null ? "4 3" : undefined} />
          <text
            x={Math.min(width - 80, Math.max(left + 42, playheadX))}
            y={16}
            textAnchor="middle"
            fontFamily="'JetBrains Mono', monospace"
            fontSize={10}
            fill={V3.coral}
            letterSpacing="0.1em"
          >
            PLAYHEAD
          </text>
        </g>
      ) : null}
      {(() => {
        const ordered = [...events]
          .filter((event) => typeof event.relTimeS === "number" && lanes.some((lane) => lane.kind === event.kind))
          .sort((a, b) => (a.relTimeS! - b.relTimeS!));
        return ordered.slice(0, -1).map((event, i) => {
          const next = ordered[i + 1];
          const laneA = lanes.findIndex((lane) => lane.kind === event.kind);
          const laneB = lanes.findIndex((lane) => lane.kind === next.kind);
          if (laneA < 0 || laneB < 0) return null;
          const x0 = left + ((event.relTimeS! - span.min) / span.total) * innerWidth;
          const x1 = left + ((next.relTimeS! - span.min) / span.total) * innerWidth;
          const y0 = top + laneA * laneStep + laneStep / 2;
          const y1 = top + laneB * laneStep + laneStep / 2;
          const dx = (x1 - x0) * 0.4;
          const visible = playheadX === null || x0 <= playheadX;
          return (
            <path
              key={`conn-${event.id}-${next.id}`}
              d={`M ${x0} ${y0} C ${x0 + dx} ${y0} ${x1 - dx} ${y1} ${x1} ${y1}`}
              stroke={V3.ink3}
              strokeWidth={1}
              fill="none"
              strokeDasharray="3 3"
              opacity={visible ? 0.4 : 0.12}
            />
          );
        });
      })()}
      {events.map((event) => {
        const time = event.relTimeS ?? span.min;
        const cx = left + ((time - span.min) / span.total) * innerWidth;
        const risk = event.risk ?? "low";
        const fill = RISK_COLOR[risk];
        const isSelected = event.id === selectedId;
        const isHover = event.id === hoverId;
        const laneIndex = lanes.findIndex((lane) => lane.kind === event.kind);
        const cy = top + (laneIndex >= 0 ? laneIndex : 0) * laneStep + laneStep / 2;
        const showCallout = (isSelected || isHover) && Boolean(event.label);
        const calloutX = Math.min(cx + 10, width - 222);
        const calloutY = Math.max(cy - 38, 4);
        return (
          <g
            key={event.id}
            onClick={() => onSelect?.(event.id)}
            onMouseEnter={() => setHoverId(event.id)}
            onMouseLeave={() => setHoverId((current) => (current === event.id ? null : current))}
            style={{ cursor: onSelect ? "pointer" : undefined }}
          >
            <rect
              x={cx - (isSelected ? 6 : isHover ? 5 : 4)}
              y={cy - (isSelected ? 6 : isHover ? 5 : 4)}
              width={isSelected ? 12 : isHover ? 10 : 8}
              height={isSelected ? 12 : isHover ? 10 : 8}
              fill={fill}
              stroke={isSelected ? V3.ink : V3.paper2}
              strokeWidth={isSelected ? 1.5 : 1}
              opacity={isSelected || isHover ? 1 : 0.85}
            />
            {showCallout ? (
              <g transform={`translate(${calloutX}, ${calloutY})`}>
                <rect width={210} height={32} fill={V3.paper3} stroke={V3.rule} />
                <rect width={3} height={32} fill={fill} />
                <text
                  x={10}
                  y={13}
                  fontFamily="'JetBrains Mono', monospace"
                  fontSize={10}
                  fill={V3.ink}
                  letterSpacing="0.06em"
                >
                  {`+${(event.relTimeS ?? 0).toFixed(1)}s · ${(event.kind ?? "").toUpperCase()}`}
                </text>
                <text
                  x={10}
                  y={26}
                  fontFamily="'JetBrains Mono', monospace"
                  fontSize={10}
                  fill={V3.ink2}
                >
                  {event.label && event.label.length > 32 ? `${event.label.slice(0, 30)}…` : event.label}
                </text>
              </g>
            ) : null}
          </g>
        );
      })}
      </svg>
    </div>
  );
}
