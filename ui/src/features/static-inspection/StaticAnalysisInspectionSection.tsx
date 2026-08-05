import { useDeferredValue, useMemo, useState } from "react";

import {
  Badge,
  Eyebrow,
  Field,
  FONT_MONO,
  Panel,
  V3,
  type V3Tone,
} from "../../components/v3";
import { resolveTimeZone } from "../../lib/settings/presentation";
import type {
  SeverityDto,
  StaticDetectionFindingDto,
  StaticEvidenceRefDto,
  StaticReportArtifactDto,
} from "../../lib/types/contracts";
import {
  buildStaticInspection,
  evidenceLocation,
  filterStaticFindings,
} from "./buildStaticInspection";
import { ArtifactInventoryPanel } from "./ArtifactInventoryPanel";
import { FindingDeduplicationPanel } from "./FindingDeduplicationPanel";
import {
  EvidenceFootprint,
  FileInspectionField,
  SeverityProfile,
  ToolExecutionPanel,
} from "./StaticInspectionVisuals";
import { severityColor, severityTone } from "./staticInspectionTone";

function titleCase(value: string): string {
  return value
    .split("_")
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(" ");
}

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KiB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MiB`;
}

function formatModified(value: number): string {
  const timestamp = value > 1_000_000_000_000 ? value : value * 1000;
  return new Date(timestamp).toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: resolveTimeZone(),
  });
}

function decisionTone(decision: string): V3Tone {
  if (decision === "block") return "danger";
  if (decision === "warn" || decision === "inconclusive") return "warn";
  if (decision === "allow") return "ok";
  return "neutral";
}

function decisionColor(decision: string): string {
  if (decision === "block") return V3.coral;
  if (decision === "warn" || decision === "inconclusive") return V3.warn;
  if (decision === "allow") return V3.ok;
  return V3.ink3;
}

function operatorAction(decision: string): string {
  if (decision === "block") {
    return "Static gate stopped this extension before sandbox execution. Inspect the connected blocking evidence.";
  }
  if (decision === "warn") {
    return "Actionable static findings need analyst review before the extension enters the sandbox.";
  }
  if (decision === "inconclusive") {
    return "Coverage is incomplete. Resolve the reported gaps before interpreting this scan as clean.";
  }
  return "No actionable static finding gated this artifact. INFO inventory remains visible and this is not behavioral clearance.";
}

export function StaticAnalysisInspectionSection({
  artifact,
}: {
  artifact: StaticReportArtifactDto;
}) {
  const [severity, setSeverity] = useState<SeverityDto | "all">("all");
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);

  const summary = useMemo(
    () => buildStaticInspection(artifact.static_report),
    [artifact.static_report],
  );
  const visibleFindings = useMemo(
    () => filterStaticFindings(summary.findings, severity, deferredSearch),
    [deferredSearch, severity, summary],
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      <header
        style={{
          display: "flex",
          alignItems: "end",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 16,
          paddingBottom: 18,
          borderBottom: `1px solid ${V3.rule}`,
        }}
      >
        <div>
          <Eyebrow>Latest static artifact</Eyebrow>
          <h2 style={{ margin: "7px 0 0", color: V3.ink, fontSize: 25, lineHeight: 1.1 }}>
            Static analysis inspection
          </h2>
        </div>
        <div style={{ minWidth: 0, maxWidth: "100%", textAlign: "right" }}>
          <Badge tone="neutral">Independent static result</Badge>
          <div
            title={artifact.filename}
            style={{
              maxWidth: 480,
              marginTop: 8,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              color: V3.ink3,
              fontFamily: FONT_MONO,
              fontSize: 10,
            }}
          >
            {artifact.filename} · {formatModified(artifact.modified)}
          </div>
        </div>
      </header>

      <InspectionWorkspace
        artifact={artifact.static_report}
        summary={summary}
        severity={severity}
        search={search}
        visibleFindings={visibleFindings}
        onSearch={setSearch}
        onSeverity={setSeverity}
      />
    </div>
  );
}

function InspectionWorkspace({
  artifact,
  onSearch,
  onSeverity,
  search,
  severity,
  summary,
  visibleFindings,
}: {
  artifact: StaticReportArtifactDto["static_report"];
  onSearch: (value: string) => void;
  onSeverity: (value: SeverityDto | "all") => void;
  search: string;
  severity: SeverityDto | "all";
  summary: ReturnType<typeof buildStaticInspection>;
  visibleFindings: StaticDetectionFindingDto[];
}) {
  const detection = artifact.detection_report;
  const gate = artifact.gate_outcome;
  const coverage = detection.coverage;
  const gateReasons =
    gate.decision === "block"
      ? gate.blocked_by ?? []
      : gate.decision === "warn"
        ? gate.warned_by ?? []
        : gate.decision === "inconclusive"
          ? gate.inconclusive_reasons ?? []
          : gate.allow_reason
            ? [gate.allow_reason]
            : [];
  const coverageReasons = coverage?.coverage_reasons ?? [];
  const structuralFallbackPaths = coverage?.structural_fallback_paths ?? [];

  return (
    <>
      <section
        aria-label="Static gate inspection"
        className="static-inspection-hero"
        style={{
          display: "grid",
          border: `1px solid ${V3.rule}`,
          background: V3.paper2,
        }}
      >
        <div
          style={{
            padding: "26px 24px",
            borderRight: `1px solid ${V3.rule}`,
            background: V3.paper3,
            minWidth: 0,
            overflow: "hidden",
          }}
        >
          <Eyebrow>Pre-sandbox gate</Eyebrow>
          <div
            style={{
              marginTop: 18,
              color: decisionColor(gate.decision),
              fontSize: "clamp(36px, 3.5vw, 58px)",
              fontWeight: 800,
              letterSpacing: "-0.055em",
              lineHeight: 0.84,
              textTransform: "uppercase",
            }}
          >
            {gate.decision}
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 24 }}>
            <Badge tone={decisionTone(gate.decision)}>
              {summary.actionableFindings} actionable
            </Badge>
            <Badge tone={detection.partial ? "warn" : "ok"}>
              {detection.partial ? "Partial run" : "Complete run"}
            </Badge>
          </div>
        </div>
        <div style={{ padding: "26px 28px", minWidth: 0 }}>
          <Eyebrow>Operator reading</Eyebrow>
          <p
            role="note"
            aria-label="Static inspection action"
            style={{
              maxWidth: 760,
              margin: "12px 0 0",
              color: V3.ink2,
              fontSize: 14,
              lineHeight: 1.65,
            }}
          >
            {operatorAction(gate.decision)}
          </p>
          <div
            aria-label="Static gate reasons"
            style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 22 }}
          >
            {gateReasons.length ? (
              gateReasons.map((reason) => (
                <span
                  key={reason}
                  style={{
                    border: `1px solid ${V3.rule2}`,
                    padding: "7px 9px",
                    color: V3.ink2,
                    fontFamily: FONT_MONO,
                    fontSize: 10,
                    overflowWrap: "anywhere",
                  }}
                >
                  {reason}
                </span>
              ))
            ) : (
              <span style={{ color: V3.ink3, fontFamily: FONT_MONO, fontSize: 10 }}>
                No explicit gate reason was recorded.
              </span>
            )}
          </div>
        </div>
      </section>

      <section
        aria-label="Static inspection metrics"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 128px), 1fr))",
          border: `1px solid ${V3.rule}`,
          background: V3.paper2,
        }}
      >
        <InspectionMetric label="Findings" value={summary.findings.length} />
        <InspectionMetric label="Evidence locations" value={summary.evidenceCount} />
        <InspectionMetric label="Rules fired" value={summary.firedRules} />
        <InspectionMetric label="Files scanned" value={`${summary.filesScanned}/${summary.filesDiscovered}`} />
        <InspectionMetric label="Parse rate" value={`${summary.parsePct}%`} />
        <InspectionMetric label="Tools healthy" value={`${summary.healthyTools}/${summary.totalTools}`} />
      </section>

      <div className="static-inspection-analytics" style={{ display: "grid", gap: 20 }}>
        <FileInspectionField summary={summary} />
        <SeverityProfile
          activeSeverity={severity}
          onSelect={onSeverity}
          summary={summary}
        />
      </div>

      <ToolExecutionPanel tools={detection.tool_executions ?? []} />

      <section
        aria-label="Static coverage detail"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 150px), 1fr))",
          border: `1px solid ${V3.rule}`,
          background: V3.paper2,
        }}
      >
        <InspectionMetric label="Selected" value={summary.filesSelected} compact />
        <InspectionMetric label="Eligible" value={summary.filesEligible} compact />
        <InspectionMetric label="Parsed" value={summary.filesParsed} compact />
        <InspectionMetric label="Bytes considered" value={formatBytes(summary.bytesConsidered)} compact />
        <InspectionMetric label="Bytes read" value={formatBytes(summary.bytesRead)} compact />
        <InspectionMetric
          label="Structural fallback"
          value={coverage?.structural_fallback_files ?? 0}
          compact
        />
        <InspectionMetric label="Manifest" value={titleCase(coverage?.manifest_status ?? "unknown")} compact />
      </section>

      {structuralFallbackPaths.length ? (
        <Panel
          label="Structural fallback"
          right={<Badge tone="neutral">{structuralFallbackPaths.length}</Badge>}
        >
          <div
            role="list"
            aria-label="Static structural fallback paths"
            style={{ display: "grid", gap: 6 }}
          >
            {structuralFallbackPaths.map((path) => (
              <code
                key={path}
                role="listitem"
                className="mono-path"
                style={{ maxWidth: "100%", overflowWrap: "anywhere", whiteSpace: "pre-wrap" }}
              >
                {path}
              </code>
            ))}
          </div>
        </Panel>
      ) : null}

      {coverageReasons.length ? (
        <Panel
          label="Coverage gaps"
          right={<Badge tone="warn">{coverageReasons.length}</Badge>}
        >
          <div role="list" aria-label="Static coverage gaps" style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {coverageReasons.map((reason) => (
              <span
                key={reason}
                role="listitem"
                style={{
                  border: `1px solid ${V3.warn}`,
                  background: V3.warnBg,
                  color: V3.warn,
                  padding: "7px 9px",
                  fontFamily: FONT_MONO,
                  fontSize: 10,
                }}
              >
                {titleCase(reason)}
              </span>
            ))}
          </div>
        </Panel>
      ) : null}

      <ArtifactInventoryPanel
        entries={detection.artifact_inventory ?? []}
        reachability={detection.reachability}
      />

      <FindingDeduplicationPanel
        records={detection.finding_deduplications ?? []}
        retainedFindings={(detection.findings ?? []).length}
      />

      <section aria-labelledby="static-findings-title">
        <div
          style={{
            display: "flex",
            alignItems: "end",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 18,
            paddingBottom: 14,
            borderBottom: `1px solid ${V3.rule}`,
          }}
        >
          <div>
            <Eyebrow>Evidence review</Eyebrow>
            <h2
              id="static-findings-title"
              style={{ margin: "7px 0 0", color: V3.ink, fontSize: 25, lineHeight: 1.1 }}
            >
              Static findings
            </h2>
          </div>
          <Badge tone={visibleFindings.length ? "warn" : "ok"}>
            {visibleFindings.length} visible
          </Badge>
        </div>

        <div
          className="static-inspection-findings"
          style={{ display: "grid", gap: 20, marginTop: 20 }}
        >
          <div style={{ minWidth: 0 }}>
            <div
              className="static-inspection-filterbar"
              style={{
                display: "grid",
                alignItems: "end",
                gap: 12,
                padding: 14,
                border: `1px solid ${V3.rule}`,
                background: V3.paper3,
              }}
            >
              <Field
                label="Search findings"
                placeholder="rule, title, category, path, snippet…"
                value={search}
                onChange={onSearch}
                mono
              />
              <button
                type="button"
                onClick={() => {
                  onSearch("");
                  onSeverity("all");
                }}
                style={{
                  minHeight: 43,
                  border: `1px solid ${V3.rule2}`,
                  background: "transparent",
                  color: V3.ink2,
                  padding: "9px 13px",
                  fontFamily: FONT_MONO,
                  fontSize: 10,
                  textTransform: "uppercase",
                }}
              >
                Clear filters
              </button>
            </div>

            <div
              role="list"
              aria-label="Static analysis findings"
              style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 14 }}
            >
              {visibleFindings.length ? (
                visibleFindings.map((finding) => (
                  <FindingInspection key={finding.id ?? `${finding.rule_id}:${finding.title}`} finding={finding} />
                ))
              ) : (
                <div
                  role="status"
                  style={{
                    border: `1px solid ${V3.rule}`,
                    padding: "24px 20px",
                    color: V3.ink3,
                    fontSize: 13,
                  }}
                >
                  No finding matches the active filters.
                </div>
              )}
            </div>
          </div>
          <aside style={{ minWidth: 0 }}>
            <EvidenceFootprint summary={summary} />
          </aside>
        </div>
      </section>
    </>
  );
}

function InspectionMetric({
  compact = false,
  label,
  value,
}: {
  compact?: boolean;
  label: string;
  value: number | string;
}) {
  return (
    <div
      aria-label={`${label}: ${value}`}
      style={{
        minWidth: 0,
        padding: compact ? "14px 15px" : "18px 17px",
        borderRight: `1px solid ${V3.rule}`,
        borderBottom: `1px solid ${V3.rule}`,
      }}
    >
      <Eyebrow>{label}</Eyebrow>
      <div
        title={String(value)}
        style={{
          marginTop: 8,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          color: V3.ink,
          fontFamily: compact ? FONT_MONO : undefined,
          fontSize: compact ? 13 : 24,
          fontWeight: compact ? 500 : 750,
        }}
      >
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
    </div>
  );
}

function FindingInspection({ finding }: { finding: StaticDetectionFindingDto }) {
  const evidence = finding.evidence ?? [];
  return (
    <article
      role="listitem"
      style={{
        border: `1px solid ${V3.rule}`,
        borderLeft: `4px solid ${severityColor(finding.severity)}`,
        background: V3.paper2,
      }}
    >
      <div style={{ padding: "17px 18px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "start",
            gap: 14,
          }}
        >
          <div style={{ minWidth: 0 }}>
            <div
              style={{
                color: V3.ink,
                fontSize: 15,
                fontWeight: 700,
                lineHeight: 1.35,
              }}
            >
              {finding.title}
            </div>
            <div
              style={{
                marginTop: 6,
                color: V3.ink3,
                fontFamily: FONT_MONO,
                fontSize: 9.5,
                overflowWrap: "anywhere",
              }}
            >
              {finding.rule_id} · v{finding.rule_version}
            </div>
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "flex-end" }}>
            <Badge tone={severityTone(finding.severity)}>{finding.severity}</Badge>
            <Badge tone="neutral">{finding.confidence} confidence</Badge>
          </div>
        </div>
        <p
          style={{
            margin: "13px 0 0",
            color: V3.ink2,
            fontSize: 12.5,
            lineHeight: 1.6,
          }}
        >
          {finding.description}
        </p>
        <div style={{ display: "flex", gap: 7, flexWrap: "wrap", marginTop: 13 }}>
          {finding.categories.map((category) => (
            <span
              key={category}
              style={{
                border: `1px solid ${V3.rule2}`,
                padding: "4px 6px",
                color: V3.ink3,
                fontFamily: FONT_MONO,
                fontSize: 9,
              }}
            >
              {category}
            </span>
          ))}
        </div>
      </div>

      <details style={{ borderTop: `1px solid ${V3.rule}`, background: V3.paper3 }}>
        <summary
          style={{
            padding: "12px 18px",
            color: V3.ink2,
            fontFamily: FONT_MONO,
            fontSize: 10,
            cursor: "pointer",
          }}
        >
          Inspect {evidence.length} evidence location{evidence.length === 1 ? "" : "s"}
        </summary>
        <div
          role="list"
          aria-label={`Evidence for ${finding.title}`}
          style={{ borderTop: `1px solid ${V3.rule}` }}
        >
          {evidence.length ? (
            evidence.map((item, index) => (
              <EvidenceRow key={`${item.relative_path}:${item.line_number ?? 0}:${index}`} evidence={item} />
            ))
          ) : (
            <div style={{ padding: "14px 18px", color: V3.ink3, fontSize: 12 }}>
              No evidence location was recorded for this finding.
            </div>
          )}
        </div>
      </details>
    </article>
  );
}

function EvidenceRow({ evidence }: { evidence: StaticEvidenceRefDto }) {
  return (
    <div
      role="listitem"
      style={{ padding: "13px 18px", borderBottom: `1px solid ${V3.rule}` }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <code
          style={{
            color: V3.ink2,
            fontFamily: FONT_MONO,
            fontSize: 10,
            overflowWrap: "anywhere",
          }}
        >
          {evidenceLocation(evidence)}
        </code>
        <Badge tone="neutral">{evidence.tool}</Badge>
      </div>
      {evidence.snippet ? (
        <pre
          style={{
            margin: "10px 0 0",
            maxWidth: "100%",
            overflowX: "auto",
            whiteSpace: "pre-wrap",
            overflowWrap: "anywhere",
            color: V3.ink3,
            fontFamily: FONT_MONO,
            fontSize: 10,
            lineHeight: 1.55,
          }}
        >
          {evidence.snippet}
        </pre>
      ) : null}
    </div>
  );
}
