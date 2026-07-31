import type {
  SeverityDto,
  StaticToolExecutionRecordDto,
} from "../../lib/types/contracts";
import { Badge, Eyebrow, FONT_MONO, Panel, V3 } from "../../components/v3";
import {
  STATIC_SEVERITIES,
  type StaticInspectionSummary,
} from "./buildStaticInspection";
import { severityColor } from "./staticInspectionTone";

function titleCase(value: string): string {
  return value
    .split("_")
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(" ");
}

export function FileInspectionField({
  summary,
}: {
  summary: StaticInspectionSummary;
}) {
  const cellCount = Math.min(summary.filesDiscovered, 64);
  const parsedCells = summary.filesDiscovered
    ? Math.round((summary.filesParsed / summary.filesDiscovered) * cellCount)
    : 0;
  const scannedCells = summary.filesDiscovered
    ? Math.max(
        parsedCells,
        Math.round((summary.filesScanned / summary.filesDiscovered) * cellCount),
      )
    : 0;

  return (
    <Panel
      label="Inspection field"
      right={<Badge tone={summary.coveragePct === 100 ? "ok" : "warn"}>{summary.coveragePct}% scanned</Badge>}
    >
      <div
        role="img"
        aria-label={`${summary.filesScanned} of ${summary.filesDiscovered} discovered files scanned; ${summary.filesParsed} parsed`}
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(8, minmax(12px, 1fr))",
          gap: 6,
          minHeight: 112,
          alignContent: "start",
        }}
      >
        {cellCount ? (
          Array.from({ length: cellCount }, (_, index) => {
            const state =
              index < parsedCells
                ? "parsed"
                : index < scannedCells
                  ? "scanned"
                  : "not scanned";
            const background =
              state === "parsed"
                ? V3.ok
                : state === "scanned"
                  ? V3.ink3
                  : V3.warnBg;
            return (
              <span
                key={index}
                aria-hidden
                title={`Coverage unit ${index + 1}: ${state}`}
                style={{
                  minHeight: 10,
                  aspectRatio: "1.75 / 1",
                  border: `1px solid ${state === "not scanned" ? V3.warn : V3.rule2}`,
                  background,
                  opacity: state === "scanned" ? 0.72 : 1,
                }}
              />
            );
          })
        ) : (
          <span style={{ color: V3.ink3, fontSize: 13 }}>
            No discovered-file measurement was recorded.
          </span>
        )}
      </div>
      <div
        aria-label="Inspection field legend"
        style={{ display: "flex", flexWrap: "wrap", gap: 14, marginTop: 16 }}
      >
        <LegendDot color={V3.ok} label="Parsed" />
        <LegendDot color={V3.ink3} label="Scanned, not parsed" />
        <LegendDot color={V3.warnBg} label="Not scanned" border={V3.warn} />
      </div>
    </Panel>
  );
}

function LegendDot({
  color,
  label,
  border = V3.rule2,
}: {
  color: string;
  label: string;
  border?: string;
}) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 7,
        color: V3.ink3,
        fontFamily: FONT_MONO,
        fontSize: 9.5,
        textTransform: "uppercase",
        letterSpacing: "0.08em",
      }}
    >
      <span
        aria-hidden
        style={{ width: 9, height: 9, background: color, border: `1px solid ${border}` }}
      />
      {label}
    </span>
  );
}

export function SeverityProfile({
  activeSeverity,
  onSelect,
  summary,
}: {
  activeSeverity: SeverityDto | "all";
  onSelect: (severity: SeverityDto | "all") => void;
  summary: StaticInspectionSummary;
}) {
  const maxCount = Math.max(1, ...Object.values(summary.severityCounts));

  return (
    <Panel
      label="Severity profile"
      right={<Badge tone={summary.actionableFindings ? "warn" : "ok"}>{summary.actionableFindings} actionable</Badge>}
    >
      <div role="group" aria-label="Filter findings by severity">
        {STATIC_SEVERITIES.map((severity) => {
          const count = summary.severityCounts[severity];
          const active = activeSeverity === severity;
          return (
            <button
              key={severity}
              type="button"
              aria-label={`${titleCase(severity)}: ${count} findings`}
              aria-pressed={active}
              onClick={() => onSelect(active ? "all" : severity)}
              style={{
                display: "grid",
                gridTemplateColumns: "76px minmax(0, 1fr) 34px",
                gap: 12,
                alignItems: "center",
                width: "100%",
                border: 0,
                borderBottom: `1px solid ${V3.rule}`,
                padding: "11px 0",
                background: "transparent",
                color: V3.ink,
                textAlign: "left",
              }}
            >
              <span
                style={{
                  color: active ? severityColor(severity) : V3.ink2,
                  fontFamily: FONT_MONO,
                  fontSize: 10,
                  fontWeight: 600,
                  textTransform: "uppercase",
                }}
              >
                {severity}
              </span>
              <span
                aria-hidden
                style={{ height: 7, background: V3.paper3, overflow: "hidden" }}
              >
                <span
                  style={{
                    display: "block",
                    width: `${(count / maxCount) * 100}%`,
                    minWidth: count ? 5 : 0,
                    height: "100%",
                    background: severityColor(severity),
                  }}
                />
              </span>
              <span
                style={{
                  color: severityColor(severity),
                  fontFamily: FONT_MONO,
                  fontSize: 12,
                  textAlign: "right",
                }}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>
    </Panel>
  );
}

export function ToolExecutionPanel({
  tools,
}: {
  tools: StaticToolExecutionRecordDto[];
}) {
  const maxDuration = Math.max(1, ...tools.map((tool) => tool.duration_ms));
  return (
    <Panel
      label="Static tool execution"
      right={<Badge tone={tools.every((tool) => (tool.status ?? "ok") === "ok") ? "ok" : "warn"}>{tools.length} tools</Badge>}
    >
      {tools.length ? (
        <div role="list" aria-label="Static tool execution statistics">
          {tools.map((tool) => {
            const status = tool.status ?? "ok";
            return (
              <div
                key={`${tool.tool}:${tool.version}`}
                role="listitem"
                className="static-inspection-tool-row"
                style={{
                  display: "grid",
                  gap: 14,
                  alignItems: "center",
                  padding: "14px 0",
                  borderBottom: `1px solid ${V3.rule}`,
                }}
              >
                <div style={{ minWidth: 0 }}>
                  <div style={{ color: V3.ink, fontSize: 13, fontWeight: 700 }}>
                    {titleCase(tool.tool)}
                  </div>
                  <div
                    style={{ color: V3.ink3, fontFamily: FONT_MONO, fontSize: 9.5 }}
                  >
                    v{tool.version}
                  </div>
                </div>
                <div>
                  <div style={{ height: 6, background: V3.paper3 }}>
                    <span
                      aria-hidden
                      style={{
                        display: "block",
                        width: `${(tool.duration_ms / maxDuration) * 100}%`,
                        minWidth: 4,
                        height: "100%",
                        background: status === "ok" ? V3.ok : V3.warn,
                      }}
                    />
                  </div>
                  <div
                    style={{ marginTop: 6, color: V3.ink3, fontFamily: FONT_MONO, fontSize: 9.5 }}
                  >
                    {tool.duration_ms.toLocaleString()} ms
                  </div>
                </div>
                <ToolStat label="Rules" value={tool.rules_loaded} />
                <ToolStat label="Findings" value={tool.findings_emitted} />
                <Badge
                  tone={
                    status === "ok"
                      ? "ok"
                      : status === "error" || status === "timeout"
                        ? "danger"
                        : "warn"
                  }
                >
                  {status}
                </Badge>
              </div>
            );
          })}
        </div>
      ) : (
        <span style={{ color: V3.ink3, fontSize: 13 }}>
          No tool execution record was emitted.
        </span>
      )}
    </Panel>
  );
}

function ToolStat({ label, value }: { label: string; value: number }) {
  return (
    <span style={{ minWidth: 0 }}>
      <Eyebrow>{label}</Eyebrow>
      <span
        style={{ display: "block", marginTop: 4, fontFamily: FONT_MONO, fontSize: 12 }}
      >
        {value}
      </span>
    </span>
  );
}

export function EvidenceFootprint({ summary }: { summary: StaticInspectionSummary }) {
  const visible = summary.evidenceFiles.slice(0, 8);
  const maxCount = Math.max(1, ...visible.map((entry) => entry.count));
  return (
    <Panel
      label="Evidence footprint"
      right={<Badge tone="neutral">{summary.evidenceFiles.length} files</Badge>}
    >
      {visible.length ? (
        <div role="list" aria-label="Evidence locations by file">
          {visible.map((entry) => (
            <div
              key={entry.path}
              role="listitem"
              style={{ padding: "10px 0", borderBottom: `1px solid ${V3.rule}` }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 10,
                  color: V3.ink2,
                  fontFamily: FONT_MONO,
                  fontSize: 10,
                }}
              >
                <span title={entry.path} style={{ overflowWrap: "anywhere" }}>
                  {entry.path}
                </span>
                <span style={{ color: V3.coral, flexShrink: 0 }}>{entry.count}</span>
              </div>
              <div style={{ height: 3, marginTop: 8, background: V3.paper3 }}>
                <span
                  aria-hidden
                  style={{
                    display: "block",
                    width: `${(entry.count / maxCount) * 100}%`,
                    height: "100%",
                    background: V3.coral,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <span style={{ color: V3.ink3, fontSize: 13 }}>
          No evidence locations were emitted.
        </span>
      )}
    </Panel>
  );
}
