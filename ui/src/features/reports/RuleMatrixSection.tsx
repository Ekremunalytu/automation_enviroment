import { useMemo, useState, type ReactNode } from "react";

import {
  Badge,
  Dialog,
  EmptyState,
  Eyebrow,
  FONT_MONO,
  Panel,
  V3,
  type V3Tone,
} from "../../components/v3";
import type {
  ActivationReportView,
  StaticReportView,
} from "../../lib/types/view-models";
import {
  buildRuleMatrix,
  type FamilyGroup,
  type MatrixCell,
  type RuleStatus,
  type ToolCell,
} from "./buildRuleMatrix";
import type { RuleSeverity } from "../../lib/rules/ruleCatalog";

// MITRE ATT&CK-Navigator-style matrix of detection rules. Two bands (dynamic
// behavioral + static pre-check); each band groups rules into threat-family
// columns and colors every cell by whether it fired / stayed silent / errored.
// Clicking a cell opens a detail dialog.

function statusColor(status: RuleStatus): string {
  switch (status) {
    case "fired":
      return V3.coral;
    case "error":
      return V3.warn;
    case "silent":
      return V3.rule2;
    default:
      return V3.ink4;
  }
}

function statusTone(status: RuleStatus): V3Tone {
  switch (status) {
    case "fired":
      return "danger";
    case "error":
      return "warn";
    default:
      return "neutral";
  }
}

function severityColor(severity: RuleSeverity): string {
  if (severity === "critical" || severity === "high") return V3.coral;
  if (severity === "medium") return V3.warn;
  if (severity === "low") return V3.ok;
  return V3.ink3;
}

function severityTone(severity: RuleSeverity): V3Tone {
  if (severity === "critical" || severity === "high") return "danger";
  if (severity === "medium") return "warn";
  if (severity === "low") return "ok";
  return "neutral";
}

function cellBackground(status: RuleStatus): string {
  if (status === "fired") return V3.dangerBg;
  if (status === "error") return V3.warnBg;
  return V3.paper3;
}

function MatrixCellButton({
  cell,
  onSelect,
}: {
  cell: MatrixCell;
  onSelect: (cell: MatrixCell) => void;
}) {
  const muted = cell.status === "silent" || cell.status === "unknown";
  return (
    <button
      type="button"
      onClick={() => onSelect(cell)}
      aria-label={`${cell.label} — ${cell.statusLabel}`}
      style={{
        textAlign: "left",
        width: "100%",
        cursor: "pointer",
        color: "inherit",
        background: cellBackground(cell.status),
        border: `1px solid ${V3.rule}`,
        borderLeft: `3px solid ${statusColor(cell.status)}`,
        padding: "10px 12px",
        display: "flex",
        flexDirection: "column",
        gap: 8,
        opacity: muted ? 0.78 : 1,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
        <span style={{ fontFamily: FONT_MONO, fontSize: 11.5, color: V3.ink, lineHeight: 1.35 }}>
          {cell.label}
        </span>
        <span
          aria-hidden
          style={{
            width: 8,
            height: 8,
            borderRadius: 999,
            background: statusColor(cell.status),
            flexShrink: 0,
          }}
        />
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
        <span
          style={{
            fontFamily: FONT_MONO,
            fontSize: 9,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: V3.ink2,
            border: `1px solid ${V3.rule2}`,
            padding: "1px 4px",
          }}
        >
          {cell.stream}
        </span>
        <span
          style={{
            fontFamily: FONT_MONO,
            fontSize: 9.5,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: statusColor(cell.status),
          }}
        >
          {cell.statusLabel}
        </span>
        <span aria-hidden style={{ width: 1, height: 10, background: V3.rule2 }} />
        <span
          style={{
            fontFamily: FONT_MONO,
            fontSize: 9.5,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: severityColor(cell.severity),
          }}
        >
          {cell.severity}
        </span>
        {cell.techniques.slice(0, 2).map((technique) => (
          <span
            key={technique}
            style={{
              fontFamily: FONT_MONO,
              fontSize: 9,
              color: V3.ink3,
              border: `1px solid ${V3.rule2}`,
              padding: "1px 4px",
            }}
          >
            {technique}
          </span>
        ))}
      </div>
    </button>
  );
}

function MatrixBand({
  title,
  right,
  groups,
  emptyTitle,
  onSelect,
}: {
  title: string;
  right?: ReactNode;
  groups: FamilyGroup[];
  emptyTitle: string;
  onSelect: (cell: MatrixCell) => void;
}) {
  return (
    <Panel label={title} right={right}>
      {groups.length ? (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 210px), 1fr))",
            gap: 14,
            alignItems: "start",
          }}
        >
          {groups.map((group) => {
            const fired = group.cells.filter((cell) => cell.status === "fired").length;
            return (
              <div key={group.family} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 8,
                    paddingBottom: 6,
                    borderBottom: `1px solid ${V3.rule}`,
                  }}
                >
                  <Eyebrow>{group.family}</Eyebrow>
                  <span style={{ fontFamily: FONT_MONO, fontSize: 9.5, color: fired ? V3.coral : V3.ink4 }}>
                    {fired}/{group.cells.length}
                  </span>
                </div>
                {group.cells.map((cell) => (
                  <MatrixCellButton key={cell.ruleId} cell={cell} onSelect={onSelect} />
                ))}
              </div>
            );
          })}
        </div>
      ) : (
        <p style={{ margin: 0, color: V3.ink3, fontSize: 13, lineHeight: 1.6 }}>{emptyTitle}.</p>
      )}
    </Panel>
  );
}

function Legend() {
  const items: Array<[string, string]> = [
    ["Fired", V3.coral],
    ["Silent", V3.rule2],
    ["Error", V3.warn],
    ["Not run", V3.ink4],
  ];
  return (
    <Panel>
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: "center" }}>
        <Eyebrow>Legend</Eyebrow>
        {items.map(([label, color]) => (
          <span key={label} style={{ display: "inline-flex", alignItems: "center", gap: 7 }}>
            <span aria-hidden style={{ width: 11, height: 11, background: color, borderRadius: 2 }} />
            <span
              style={{
                fontFamily: FONT_MONO,
                fontSize: 10.5,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                color: V3.ink3,
              }}
            >
              {label}
            </span>
          </span>
        ))}
      </div>
    </Panel>
  );
}

function ToolStatuses({ cells }: { cells: ToolCell[] }) {
  if (!cells.length) return null;
  return (
    <div
      aria-label="Static analysis tools"
      style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "flex-end" }}
    >
      {cells.map((tool) => {
        const tone: V3Tone =
          tool.status === "ok"
            ? "ok"
            : tool.status === "error" || tool.status === "timeout"
              ? "danger"
              : "warn";
        return (
          <Badge key={tool.tool} tone={tone} style={{ padding: "4px 7px" }}>
            {tool.tool} · {tool.status}
            {tool.errorCount ? ` · ${tool.errorCount} err` : ""}
          </Badge>
        );
      })}
    </div>
  );
}

function KV({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <Eyebrow>{label}</Eyebrow>
      <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: V3.ink2, wordBreak: "break-word" }}>
        {value}
      </span>
    </div>
  );
}

function RuleDetailDialog({ cell, onClose }: { cell: MatrixCell | null; onClose: () => void }) {
  const tone = cell?.status === "fired" ? "danger" : cell?.status === "error" ? "warn" : "accent";
  return (
    <Dialog
      open={cell != null}
      onClose={onClose}
      eyebrow={cell ? `${cell.stream === "static" ? "Static" : "Dynamic"} rule · ${cell.family}` : undefined}
      title={cell?.label ?? ""}
      tone={tone}
      width={560}
    >
      {cell ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <Badge tone={statusTone(cell.status)}>{cell.statusLabel}</Badge>
            <Badge tone={severityTone(cell.severity)}>{cell.severity}</Badge>
            {cell.lifecycle ? <Badge tone="neutral">{cell.lifecycle}</Badge> : null}
            {cell.findingCount > 0 ? (
              <Badge tone="neutral">
                {cell.findingCount} finding{cell.findingCount === 1 ? "" : "s"}
              </Badge>
            ) : null}
          </div>

          <KV
            label="Rule ID"
            value={cell.ruleId + (cell.ruleVersion ? ` · v${cell.ruleVersion}` : "")}
          />
          {cell.techniques.length ? (
            <KV label="MITRE ATT&CK" value={cell.techniques.join(", ")} />
          ) : null}

          {cell.detail ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <Eyebrow>{cell.status === "fired" ? "Finding" : "About this rule"}</Eyebrow>
              {cell.status === "fired" &&
              cell.detail.title &&
              cell.detail.title !== cell.label ? (
                <span style={{ fontSize: 14, fontWeight: 600, color: V3.ink }}>
                  {cell.detail.title}
                </span>
              ) : null}
              <p style={{ margin: 0, fontSize: 13.5, color: V3.ink2, lineHeight: 1.6 }}>
                {cell.detail.description}
              </p>
            </div>
          ) : null}

          {cell.detail?.mitigation ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <Eyebrow>Mitigation</Eyebrow>
              <p style={{ margin: 0, fontSize: 13, color: V3.ink2, lineHeight: 1.6 }}>
                {cell.detail.mitigation}
              </p>
            </div>
          ) : null}

          {cell.detail && cell.detail.evidence.length ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <Eyebrow>Evidence</Eyebrow>
              <ul style={{ margin: 0, paddingLeft: 18, color: V3.ink2, fontSize: 12.5, lineHeight: 1.6 }}>
                {cell.detail.evidence.slice(0, 6).map((entry, index) => (
                  <li key={index}>{entry}</li>
                ))}
              </ul>
              {cell.detail.evidence.length > 6 ? (
                <span style={{ fontFamily: FONT_MONO, fontSize: 10.5, color: V3.ink3 }}>
                  +{cell.detail.evidence.length - 6} more
                </span>
              ) : null}
            </div>
          ) : cell.detail && cell.detail.evidenceCount > 0 ? (
            <KV
              label="Evidence"
              value={`${cell.detail.evidenceCount} location${cell.detail.evidenceCount === 1 ? "" : "s"}`}
            />
          ) : null}

          {!cell.inCatalog ? (
            <p style={{ margin: 0, fontSize: 12, color: V3.ink3, lineHeight: 1.6 }}>
              External tool rule — surfaced because it fired in this scan. Its silent
              counterparts aren't enumerated.
            </p>
          ) : null}
        </div>
      ) : null}
    </Dialog>
  );
}

export function RuleMatrixSection({
  report,
  dynamicAnalysisEnabled = true,
  staticReportOverride,
  staticReportLoading = false,
  staticReportError = false,
  latestStaticArtifact = false,
}: {
  report: ActivationReportView;
  dynamicAnalysisEnabled?: boolean;
  staticReportOverride?: StaticReportView | null;
  staticReportLoading?: boolean;
  staticReportError?: boolean;
  latestStaticArtifact?: boolean;
}) {
  const effectiveReport = useMemo(
    () =>
      staticReportOverride === undefined
        ? report
        : { ...report, staticReport: staticReportOverride },
    [report, staticReportOverride],
  );
  const matrix = useMemo(() => buildRuleMatrix(effectiveReport), [effectiveReport]);
  const [selected, setSelected] = useState<MatrixCell | null>(null);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <Legend />

      {dynamicAnalysisEnabled ? (
        <MatrixBand
          title="Dynamic · behavioral"
          right={
            <Eyebrow>
              {matrix.counts.dynamicFired}/{matrix.counts.dynamicTotal} fired
            </Eyebrow>
          }
          groups={matrix.dynamic}
          emptyTitle="No dynamic rules were executed for this report"
          onSelect={setSelected}
        />
      ) : (
        <Panel label="Dynamic · behavioral">
          <EmptyState
            eyebrow="Dynamic"
            title="Dynamic analysis is disabled"
            body="Sandbox execution is turned off in Settings. Dynamic rule results are intentionally hidden; enable dynamic analysis to produce behavioral findings."
          />
        </Panel>
      )}

      {staticReportLoading ? (
        <Panel label="Static · pre-check">
          <EmptyState
            eyebrow="Static"
            title="Loading latest static pre-check"
            body="Reading the newest completed static analysis artifact."
          />
        </Panel>
      ) : staticReportError ? (
        <Panel label="Static · pre-check">
          <EmptyState
            eyebrow="Static"
            title="Latest static pre-check unavailable"
            body="Static analysis ran, but no readable latest artifact could be loaded."
          />
        </Panel>
      ) : matrix.hasStatic ? (
        <MatrixBand
          title="Static · pre-check"
          right={
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", justifyContent: "flex-end" }}>
              {latestStaticArtifact ? (
                <Badge tone="neutral">Latest static artifact</Badge>
              ) : null}
              <Eyebrow>
                {matrix.counts.staticFired}/{matrix.counts.staticTotal} fired
              </Eyebrow>
              <ToolStatuses cells={matrix.toolCells} />
            </div>
          }
          groups={matrix.static}
          emptyTitle="No static rules"
          onSelect={setSelected}
        />
      ) : (
        <Panel label="Static · pre-check">
          <EmptyState
            eyebrow="Static"
            title="No static pre-check for this run"
            body="This report was produced without the static analysis gate, so static rule activation isn't available. Static results appear for extensions analyzed through the marketplace flow."
          />
        </Panel>
      )}

      <RuleDetailDialog cell={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
