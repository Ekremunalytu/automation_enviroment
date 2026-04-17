import { ReactECharts } from "../../lib/charts/core";
import type { EvidenceEventView } from "../../lib/types/view-models";

const KINDS = ["Activation", "Network", "File", "Scenario"];
const COLORS: Record<string, string> = {
  Activation: "#9EC6B3",
  Network: "#7BC47F",
  File: "#D3A35F",
  Scenario: "#A19A8B",
};

function buildTimelineSummary(events: EvidenceEventView[]) {
  if (!events.length) {
    return "Evidence timeline with no events.";
  }

  const counts = new Map<string, number>();
  for (const event of events) {
    counts.set(event.kindLabel, (counts.get(event.kindLabel) || 0) + 1);
  }

  const breakdown = Array.from(counts.entries())
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .map(([kind, count]) => `${count} ${kind.toLowerCase()} ${count === 1 ? "event" : "events"}`)
    .join(", ");

  return `Evidence timeline with ${events.length} total events: ${breakdown}.`;
}

export function EvidenceTimelineChart({
  events,
  onSelect,
  className = "h-[220px] w-full",
  compact = false,
}: {
  events: EvidenceEventView[];
  onSelect: (eventId: string) => void;
  className?: string;
  compact?: boolean;
}) {
  const summary = buildTimelineSummary(events);
  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "#1A2126",
      borderColor: "#2B3640",
      textStyle: { color: "#F4F0E8" },
      formatter: (params: { data: [number, number, string, string, string] }) =>
        `
        <div style="min-width:220px">
          <div style="font-weight:600;margin-bottom:6px">${params.data[2]}</div>
          <div style="color:#a19a8b">${params.data[3]}</div>
          <div style="margin-top:8px;color:#f4f0e8">${params.data[4]}</div>
        </div>
        `,
    },
    grid: {
      left: 36,
      right: 18,
      top: compact ? 18 : 24,
      bottom: compact ? 22 : 34,
    },
    xAxis: {
      type: "value",
      axisLabel: { color: "#A19A8B", fontSize: compact ? 10 : 12 },
      splitLine: { lineStyle: { color: "#2B3640" } },
      name: compact ? "" : "seconds",
      nameTextStyle: { color: "#A19A8B" },
    },
    yAxis: {
      type: "category",
      data: KINDS,
      axisLabel: { color: "#F4F0E8", fontSize: compact ? 10 : 12 },
      axisLine: { lineStyle: { color: "#2B3640" } },
    },
    series: [
      {
        type: "scatter",
        data: events.map((event) => [
          event.relTimeS ?? 0,
          KINDS.indexOf(event.kindLabel),
          event.artifactShort,
          `${event.collectorLabel} / ${event.actorLabel}`,
          event.summaryDisplay,
          event.eventId,
        ]),
        symbolSize: (_value: [number, number, string, string, string, string], params: { dataIndex: number }) =>
          events[params.dataIndex]?.sensitive ? (compact ? 12 : 14) : compact ? 8 : 10,
        itemStyle: {
          color: (params: { dataIndex: number }) => COLORS[events[params.dataIndex]?.kindLabel || "File"] || "#45d6ff",
          opacity: 0.78,
        },
      },
    ],
  };

  return (
    <div aria-label={summary} role="img">
      <ReactECharts
        className={className}
        onEvents={{
          click: (params: { data?: unknown[] }) => {
            const eventId = Array.isArray(params.data) ? String(params.data[5] || "") : "";
            if (eventId) onSelect(eventId);
          },
        }}
        option={option}
      />
    </div>
  );
}
