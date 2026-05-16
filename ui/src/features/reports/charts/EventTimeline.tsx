import { useEffect, useMemo, useRef, useState, type MouseEvent } from "react";

import { RISK_COLOR, V3, type Risk } from "../../../components/v3";
import { DISPLAY_CAPS, applyDisplayCap, formatTruncationLabel } from "../../../lib/displayCaps";

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

const W = 960;
const H = 240;
const PAD_L = 110;
const PAD_R = 28;
const PAD_T = 16;
const PAD_B = 40;
const INNER_W = W - PAD_L - PAD_R;
const SCAN_DURATION_MS = 6000;

const R_LANES = [
  { id: "activation", label: "Activation", color: V3.coral, y: 56 },
  { id: "file", label: "File I/O", color: V3.ink2, y: 116 },
  { id: "network", label: "Network", color: V3.warn, y: 176 },
] as const;

type LaneId = (typeof R_LANES)[number]["id"];

type NormalizedTimelineEvent = {
  id: string;
  summary: string;
  t: number;
  kind: LaneId;
  risk: Risk;
};

function normalizeKind(kind?: string): LaneId | null {
  if (kind === "activation" || kind === "file" || kind === "network") return kind;
  return null;
}

function truncate(value: string, max = 32) {
  return value.length > max ? `${value.slice(0, max - 2)}…` : value;
}

export function EventTimeline({ events, selectedId, onSelect, height = 240 }: EventTimelineProps) {
  const [playing, setPlaying] = useState(true);
  const [cursor, setCursor] = useState(0);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [selectionAnchorEnabled, setSelectionAnchorEnabled] = useState(true);
  const frameRef = useRef<number | null>(null);
  const startedRef = useRef<number | null>(null);
  const cursorRef = useRef(0);
  const hasEventsRef = useRef(false);

  const normalizedEvents = useMemo(
    () =>
      events
        .flatMap<NormalizedTimelineEvent>((event) => {
          const kind = normalizeKind(event.kind);
          if (!kind || typeof event.relTimeS !== "number" || !Number.isFinite(event.relTimeS)) return [];
          return [
            {
              id: event.id,
              summary: event.label || event.id,
              t: Math.max(0, event.relTimeS),
              kind,
              risk: event.risk ?? "low",
            },
          ];
        })
        .sort((left, right) => left.t - right.t),
    [events],
  );

  const cappedEvents = useMemo(
    () => applyDisplayCap(normalizedEvents, DISPLAY_CAPS.TIMELINE_EVENTS),
    [normalizedEvents],
  );
  const allEvents = cappedEvents.visible;
  const truncationLabel = cappedEvents.truncated
    ? formatTruncationLabel(cappedEvents, "events")
    : "";

  const maxT = useMemo(() => Math.max(1, ...allEvents.map((event) => event.t)) + 2, [allEvents]);
  const selectedEvent = allEvents.find((event) => event.id === selectedId);
  const anchoredEvent = selectionAnchorEnabled ? selectedEvent : undefined;
  const activeCursor = anchoredEvent ? anchoredEvent.t / maxT : cursor;
  const playX = PAD_L + activeCursor * INNER_W;
  const highRiskCount = allEvents.filter((event) => event.risk === "high").length;

  useEffect(() => {
    cursorRef.current = cursor;
  }, [cursor]);

  useEffect(() => {
    hasEventsRef.current = allEvents.length > 0;
  }, [allEvents.length]);

  useEffect(() => {
    if (!playing) {
      if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
      startedRef.current = null;
      return;
    }

    const step = (timestamp: number) => {
      if (!hasEventsRef.current) {
        startedRef.current = null;
        frameRef.current = window.requestAnimationFrame(step);
        return;
      }
      if (startedRef.current === null) {
        startedRef.current = timestamp - cursorRef.current * SCAN_DURATION_MS;
      }
      const next = Math.min(1, (timestamp - startedRef.current) / SCAN_DURATION_MS);
      cursorRef.current = next;
      setCursor(next);
      if (next >= 1) {
        startedRef.current = null;
        setPlaying(false);
        return;
      }
      frameRef.current = window.requestAnimationFrame(step);
    };

    frameRef.current = window.requestAnimationFrame(step);
    return () => {
      if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
    };
  }, [playing]);

  const xOf = (t: number) => PAD_L + (t / maxT) * INNER_W;
  const laneFor = (kind: LaneId) => R_LANES.find((lane) => lane.id === kind)!;

  const onPlayToggle = () => {
    if (cursorRef.current >= 0.999) {
      cursorRef.current = 0;
      setCursor(0);
    }
    startedRef.current = null;
    setPlaying((value) => !value);
  };

  const onSeek = (event: MouseEvent<SVGSVGElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const scale = Math.min(rect.width / W, rect.height / H);
    const renderedWidth = W * scale;
    const offsetX = (rect.width - renderedWidth) / 2;
    const viewX = (event.clientX - rect.left - offsetX) / scale;
    const next = Math.max(0, Math.min(1, (viewX - PAD_L) / INNER_W));
    cursorRef.current = next;
    setCursor(next);
    setSelectionAnchorEnabled(false);
    startedRef.current = null;
    setPlaying(false);
  };

  if (!allEvents.length) {
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

  return (
    <div style={{ position: "relative", background: V3.paper, border: `1px solid ${V3.rule}` }}>
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
          onClick={onPlayToggle}
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11,
            padding: "5px 10px",
            background: playing ? V3.ink : V3.paper,
            color: playing ? V3.paper : V3.ink,
            border: `1px solid ${V3.ink}`,
            cursor: "pointer",
            letterSpacing: "0.08em",
            textTransform: "lowercase",
            minWidth: 78,
          }}
        >
          {playing ? "❚❚ pause" : "▶ scan"}
        </button>
        <div
          style={{
            marginLeft: "auto",
            display: "flex",
            alignItems: "center",
            gap: 14,
            flexWrap: "wrap",
            justifyContent: "flex-end",
          }}
        >
          {truncationLabel ? (
            <span
              data-testid="timeline-truncation-indicator"
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 10.5,
                color: V3.ink3,
                letterSpacing: "0.06em",
                textTransform: "lowercase",
              }}
            >
              {truncationLabel}
            </span>
          ) : null}
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10.5,
              color: V3.ink3,
              letterSpacing: "0.06em",
            }}
          >
            t = {(activeCursor * maxT).toFixed(1)}s / {maxT.toFixed(1)}s · {allEvents.length} events · {highRiskCount} high-risk
          </span>
        </div>
      </div>

      <svg
        role="img"
        aria-label="Event timeline"
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="xMidYMid meet"
        onClick={onSeek}
        style={{ width: "100%", height, display: "block", cursor: "crosshair" }}
      >
        <defs>
          <linearGradient id="tl-wash" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor={V3.coral} stopOpacity="0" />
            <stop offset="1" stopColor={V3.coral} stopOpacity="0.08" />
          </linearGradient>
        </defs>

        <rect x={0} y={0} width={W} height={H} fill={V3.paper} />
        <rect x={PAD_L} y={PAD_T} width={Math.max(0, playX - PAD_L)} height={H - PAD_T - PAD_B} fill="url(#tl-wash)" />

        {R_LANES.map((lane) => {
          const laneCount = allEvents.filter((event) => event.kind === lane.id).length;
          return (
            <g key={lane.id}>
              <rect x={4} y={lane.y - 18} width={PAD_L - 14} height={36} fill={V3.paper2} stroke={V3.rule} />
              <text
                x={14}
                y={lane.y - 4}
                fontSize="10.5"
                fill={V3.ink}
                fontFamily="JetBrains Mono"
                fontWeight="600"
                letterSpacing="0.06em"
              >
                {lane.label.toUpperCase()}
              </text>
              <text x={14} y={lane.y + 10} fontSize="9.5" fill={V3.ink3} fontFamily="JetBrains Mono">
                n={laneCount}
              </text>
              <line x1={PAD_L} y1={lane.y} x2={W - PAD_R} y2={lane.y} stroke={V3.rule2} strokeWidth="1" />
              <rect
                x={PAD_L}
                y={lane.y - 14}
                width={INNER_W}
                height={28}
                fill="none"
                stroke={V3.rule}
                strokeDasharray="2 4"
                opacity="0.5"
              />
            </g>
          );
        })}

        {Array.from({ length: 7 }).map((_, index) => {
          const p = index / 6;
          const x = PAD_L + p * INNER_W;
          return (
            <g key={`tick-${index}`}>
              <line x1={x} y1={PAD_T} x2={x} y2={H - PAD_B} stroke={V3.rule} strokeWidth="0.5" opacity="0.6" />
              <line x1={x} y1={H - PAD_B} x2={x} y2={H - PAD_B + 5} stroke={V3.ink3} strokeWidth="1" />
              <text
                x={x}
                y={H - PAD_B + 18}
                textAnchor="middle"
                fontSize="9.5"
                fill={V3.ink3}
                fontFamily="JetBrains Mono"
                letterSpacing="0.06em"
              >
                {(p * maxT).toFixed(0)}s
              </text>
            </g>
          );
        })}

        {allEvents.slice(0, -1).map((event, index) => {
          const next = allEvents[index + 1];
          const laneA = laneFor(event.kind);
          const laneB = laneFor(next.kind);
          const x0 = xOf(event.t);
          const y0 = laneA.y;
          const x1 = xOf(next.t);
          const y1 = laneB.y;
          const dx = (x1 - x0) * 0.4;
          const visible = x0 <= playX;
          return (
            <path
              key={`conn-${event.id}-${next.id}`}
              d={`M ${x0} ${y0} C ${x0 + dx} ${y0} ${x1 - dx} ${y1} ${x1} ${y1}`}
              stroke={V3.ink2}
              strokeWidth="1.5"
              fill="none"
              strokeDasharray="4 3"
              opacity={visible ? 0.6 : 0.2}
              style={{ transition: "opacity 240ms" }}
            />
          );
        })}

        {allEvents.map((event) => {
          const lane = laneFor(event.kind);
          const x = xOf(event.t);
          const y = lane.y;
          const col = RISK_COLOR[event.risk];
          const selected = selectedId === event.id;
          const hovered = hoverId === event.id;
          const scanned = x <= playX + 0.5;
          const dimmed = playing && !scanned;
          const strong = selected || hovered;
          const calloutX = Math.min(x, W - PAD_R - 230);
          const calloutY = y - PAD_T < 60 ? y + 24 : 8;

          return (
            <g
              key={event.id}
              data-testid="timeline-event-marker"
              style={{ cursor: onSelect ? "pointer" : "default" }}
              onMouseEnter={() => setHoverId(event.id)}
              onMouseLeave={() => setHoverId((current) => (current === event.id ? null : current))}
              onClick={(clickEvent) => {
                clickEvent.stopPropagation();
                setSelectionAnchorEnabled(true);
                onSelect?.(event.id);
              }}
            >
              <line
                x1={x}
                y1={y}
                x2={x}
                y2={H - PAD_B}
                stroke={strong ? col : V3.rule2}
                strokeWidth={selected ? 1.25 : 1}
                strokeDasharray={selected ? undefined : "2 3"}
                opacity={dimmed ? 0.25 : strong ? 0.8 : 0.5}
                style={{ transition: "opacity 180ms" }}
              />

              {event.risk !== "low" && scanned ? (
                <circle
                  cx={x}
                  cy={y}
                  r="6"
                  fill="none"
                  stroke={col}
                  strokeWidth="1"
                  className="tl-pulse"
                  style={{ animationDelay: `${event.t * 0.1}s` }}
                />
              ) : null}

              {event.kind === "activation" ? (
                <rect
                  x={x - 4.5}
                  y={y - 4.5}
                  width="9"
                  height="9"
                  fill={V3.paper}
                  stroke={col}
                  strokeWidth={strong ? 2 : 1.5}
                  transform={`rotate(45 ${x} ${y})`}
                  opacity={dimmed ? 0.4 : 1}
                  style={{ transition: "opacity 200ms" }}
                />
              ) : event.kind === "file" ? (
                <rect
                  x={x - 4.5}
                  y={y - 4.5}
                  width="9"
                  height="9"
                  fill={V3.paper}
                  stroke={col}
                  strokeWidth={strong ? 2 : 1.5}
                  opacity={dimmed ? 0.4 : 1}
                  style={{ transition: "opacity 200ms" }}
                />
              ) : (
                <circle
                  cx={x}
                  cy={y}
                  r={strong ? 5.5 : 4.5}
                  fill={V3.paper}
                  stroke={col}
                  strokeWidth={strong ? 2 : 1.5}
                  opacity={dimmed ? 0.4 : 1}
                  style={{ transition: "all 200ms" }}
                />
              )}
              <circle cx={x} cy={y} r={strong ? 2 : 1.5} fill={col} opacity={dimmed ? 0.4 : 1} />

              {strong ? (
                <g>
                  <line x1={x} y1={y - 8} x2={x} y2={y - 22} stroke={col} strokeWidth="1" />
                  <rect x={x - 3} y={y - 25} width="6" height="6" fill={col} />
                  <g transform={`translate(${calloutX}, ${calloutY})`}>
                    <rect x="0" y="0" width="230" height="36" fill={V3.ink} stroke={V3.ink} />
                    <rect x="0" y="0" width="3" height="36" fill={lane.color} />
                    <text
                      x="10"
                      y="15"
                      fontSize="10.5"
                      fill={V3.paper}
                      fontFamily="JetBrains Mono"
                      fontWeight="600"
                      letterSpacing="0.04em"
                    >
                      t={event.t.toFixed(1)}s · +{event.t.toFixed(1)}s · {event.kind.toUpperCase()}
                    </text>
                    <text x="10" y="29" fontSize="10" fill={V3.paper} fontFamily="JetBrains Mono" opacity="0.8">
                      {truncate(event.summary)}
                    </text>
                  </g>
                </g>
              ) : null}
            </g>
          );
        })}

        <g style={{ pointerEvents: "none" }}>
          <line
            x1={playX}
            y1={PAD_T - 4}
            x2={playX}
            y2={H - PAD_B + 4}
            stroke={V3.coral}
            strokeWidth="1.25"
            strokeDasharray={playing ? undefined : "4 3"}
          />
          <polygon points={`${playX - 5},${PAD_T - 4} ${playX + 5},${PAD_T - 4} ${playX},${PAD_T + 3}`} fill={V3.coral} />
          <rect x={playX - 28} y={H - PAD_B + 4} width="56" height="16" fill={V3.coral} />
          <text
            x={playX}
            y={H - PAD_B + 16}
            textAnchor="middle"
            fontSize="10"
            fontFamily="JetBrains Mono"
            fontWeight="600"
            fill={V3.paper}
            letterSpacing="0.04em"
          >
            {(activeCursor * maxT).toFixed(1)}s
          </text>
        </g>
      </svg>
    </div>
  );
}
