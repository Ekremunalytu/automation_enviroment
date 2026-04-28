import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";

import { FilterRail, type EvidenceFilterState } from "../../components/evidence/FilterRail";
import { EvidenceLedger } from "../../components/evidence/EvidenceLedger";
import { LogStreamsPanel } from "../../components/evidence/LogStreamsPanel";
import { RiskRadarPanel } from "../../components/evidence/RiskRadarPanel";
import { SlideOverDrawer } from "../../components/ui/SlideOverDrawer";
import {
  Badge,
  EmptyState,
  Eyebrow,
  Field,
  GhostButton,
  KVRow,
  MetricCell,
  PageTitle,
  Panel,
  Tabs,
  V3,
  type TabSpec,
  type V3Tone,
} from "../../components/v3";
import {
  applyEvidenceFilters,
  buildEvidenceFilterOptions,
  countEvidenceFilters,
  filterEvidenceEvents,
  parseEvidenceFilters,
} from "../evidence";
import { apiClient } from "../../lib/api/client";
import {
  adaptBundle,
  adaptReport,
  buildInteractionGraph,
  buildRiskRadar,
} from "../../lib/adapters/report";
import { FindingCard } from "./FindingCard";
import { EventTimeline } from "./charts/EventTimeline";
import { InteractionGraph } from "./charts/InteractionGraph";

type ReportModel = NonNullable<ReturnType<typeof adaptReport>>;
type ReportTab = "overview" | "interactions" | "timeline" | "ledger" | "audit";

const REPORT_TABS: TabSpec<ReportTab>[] = [
  { value: "overview", label: "Overview" },
  { value: "interactions", label: "Interactions" },
  { value: "timeline", label: "Timeline" },
  { value: "ledger", label: "Event ledger" },
  { value: "audit", label: "Audit" },
];

function normalizeTab(raw: string | null): ReportTab {
  if (raw === "interactions" || raw === "timeline" || raw === "ledger" || raw === "audit") return raw;
  if (raw === "activation" || raw === "file" || raw === "network" || raw === "scenario" || raw === "evidence" || raw === "logs") {
    return "ledger";
  }
  return "overview";
}

function formatModified(value?: number | null) {
  if (!value) return "Unknown";
  const timestamp = value > 1_000_000_000_000 ? value : value * 1000;
  return new Date(timestamp).toLocaleString([], {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatNumber(value: number) {
  return value.toLocaleString();
}

function severityToTone(severity?: string): V3Tone {
  if (!severity) return "neutral";
  if (severity === "critical" || severity === "high") return "danger";
  if (severity === "medium") return "warn";
  if (severity === "low") return "ok";
  return "neutral";
}

export function ReportsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const reportParam = searchParams.get("report") || "latest";
  const selectedTab = normalizeTab(searchParams.get("tab"));
  const eventId = searchParams.get("event");
  const filters = parseEvidenceFilters(searchParams);
  const deferredSearch = useDeferredValue(filters.search);

  const reportsQuery = useQuery({
    queryKey: ["reports"],
    queryFn: ({ signal }) => apiClient.listReports(signal),
    refetchInterval: 4000,
  });

  const reportQuery = useQuery({
    queryKey: ["report", reportParam],
    queryFn: async ({ signal }) => {
      const dto =
        reportParam === "latest"
          ? await apiClient.getLatestReportBundle(signal)
          : await apiClient.getReportBundleByName(reportParam, signal);
      return adaptBundle(dto, reportParam);
    },
  });

  const report = reportQuery.data;
  const filteredEvents = useMemo(
    () => (report ? filterEvidenceEvents(report.evidence, filters, deferredSearch) : []),
    [report, filters, deferredSearch],
  );

  useEffect(() => {
    if (selectedTab !== "interactions" && selectedTab !== "ledger") return;
    if (!filteredEvents.length) return;

    const candidate = filteredEvents[0]?.eventId;
    if (!candidate) return;

    if (!eventId || !filteredEvents.some((event) => event.eventId === eventId)) {
      const next = new URLSearchParams(searchParams);
      next.set("event", candidate);
      setSearchParams(next, { replace: true });
    }
  }, [eventId, filteredEvents, searchParams, selectedTab, setSearchParams]);

  const options = buildEvidenceFilterOptions(report?.evidence || []);
  const activeFilterCount = countEvidenceFilters(filters);
  const activeReport =
    reportParam === "latest"
      ? reportsQuery.data?.[0]
      : reportsQuery.data?.find((item) => item.filename === reportParam) || reportsQuery.data?.[0];

  const interactionGraph = useMemo(() => (report ? buildInteractionGraph(report) : null), [report]);
  const timelineEvents = useMemo(() => {
    if (!report) return [];
    return filteredEvents.map((event) => ({
      id: event.eventId,
      relTimeS: event.relTimeS,
      kind: event.kind,
      label: event.summaryDisplay || event.summary,
      risk: (event.sensitive ? "high" : event.kind === "network" ? "medium" : "low") as
        | "low"
        | "medium"
        | "high",
    }));
  }, [report, filteredEvents]);
  const timelineKey = timelineEvents.map((event) => `${event.id}:${event.relTimeS ?? "na"}:${event.kind}:${event.risk}`).join("|");

  const setSelectedEvent = (nextEventId: string) => {
    startTransition(() => {
      const next = new URLSearchParams(searchParams);
      next.set("event", nextEventId);
      setSearchParams(next, { replace: true });
    });
  };

  const updateFilters = (nextFilters: EvidenceFilterState) => {
    startTransition(() => {
      setSearchParams(applyEvidenceFilters(searchParams, nextFilters), { replace: true });
    });
  };

  const verdict = report?.detection?.verdict;
  const verdictTone = severityToTone(
    verdict === "malicious" ? "critical" : verdict === "suspicious" ? "medium" : "low",
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      <header style={{ paddingBottom: 24, borderBottom: `1px solid ${V3.rule}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <Eyebrow>Reports</Eyebrow>
          {verdict ? (
            <Badge tone={verdictTone}>
              Verdict · {verdict.toUpperCase()}
            </Badge>
          ) : null}
        </div>
        <PageTitle style={{ marginTop: 14, fontSize: 44, lineHeight: 1, wordBreak: "break-word" }}>Security report</PageTitle>
        <p style={{ fontSize: 13.5, color: V3.ink3, marginTop: 14, maxWidth: 720, lineHeight: 1.6 }}>
          {report?.detection?.verdictRationale
            || "Keep the dashboard clean, then drill into one evidence class at a time instead of stacking every signal into a single screen."}
        </p>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 18 }}>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: V3.ink3,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
            }}
          >
            Findings · {report?.detection?.findings.length ?? 0}
          </span>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: V3.ink3,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
            }}
          >
            File · {report?.metadataFilename || "loading"}
          </span>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: V3.ink3,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
            }}
          >
            Visible · {formatNumber(filteredEvents.length)} events
          </span>
        </div>
      </header>

      {report ? (
        <RiskRadarPanel
          scores={buildRiskRadar(report)}
          compositeScore={report.summary.signalSummaryScore ?? 0}
        />
      ) : null}

      <Panel padded={false}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 240px), 1fr))",
            gap: 14,
            alignItems: "end",
            padding: "16px 18px",
            borderBottom: `1px solid ${V3.rule}`,
            background: V3.paper3,
          }}
        >
          <label style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 0 }}>
            <Eyebrow>Report</Eyebrow>
            <select
              value={reportParam}
              onChange={(event) => {
                const next = new URLSearchParams(searchParams);
                next.set("report", event.target.value);
                setSearchParams(next, { replace: true });
              }}
              style={{
                background: V3.paper2,
                color: V3.ink,
                border: `1px solid ${V3.rule}`,
                borderRadius: 0,
                padding: "11px 12px",
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                minWidth: 0,
              }}
            >
              <option value="latest">Latest report</option>
              {(reportsQuery.data || []).map((item) => (
                <option key={item.filename} value={item.filename}>
                  {item.filename}
                </option>
              ))}
            </select>
          </label>

          <Field
            label="Search"
            placeholder="host, path, extension, summary…"
            value={filters.search}
            onChange={(value) => updateFilters({ ...filters, search: value })}
            mono
          />

          <GhostButton ariaLabel="Filters" onClick={() => setFiltersOpen(true)}>
            Filters {activeFilterCount ? `(${activeFilterCount})` : ""}
          </GhostButton>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 150px), 1fr))",
            borderBottom: `1px solid ${V3.rule}`,
          }}
        >
          <Cell label="Total events" value={formatNumber(report?.summary.totalEvents ?? 0)} />
          <Cell label="Sensitive" value={formatNumber(report?.summary.sensitiveEvents ?? 0)} tone="danger" />
          <Cell label="Network" value={formatNumber(report?.summary.networkEvents ?? 0)} tone="warn" />
          <Cell label="Score" value={`${report?.summary.signalSummaryScore ?? 0}`} tone={verdictTone} />
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 220px), 1fr))",
            gap: 22,
            padding: "14px 18px",
          }}
        >
          <KVRow k="Active report" v={report?.metadataFilename || "Preparing selected report"} />
          <KVRow k="Last updated" v={formatModified(activeReport?.modified)} />
          <KVRow k="Run quality" v={report?.summary.runQuality ?? "—"} mono={false} />
        </div>
      </Panel>

      <Tabs<ReportTab>
        ariaLabel="Report sections"
        tabs={REPORT_TABS}
        value={selectedTab}
        onChange={(nextTab) => {
          const params = new URLSearchParams(searchParams);
          params.set("tab", nextTab);
          setSearchParams(params, { replace: true });
        }}
      />

      {reportQuery.isLoading ? (
        <EmptyState
          eyebrow="Loading"
          body="Fetching the selected report and normalizing evidence."
          title="Preparing report workspace"
        />
      ) : reportQuery.isError ? (
        <EmptyState eyebrow="Error" body={String(reportQuery.error)} title="Report could not be loaded" />
      ) : !report ? null : selectedTab === "overview" ? (
        <OverviewSection report={report} />
      ) : selectedTab === "interactions" ? (
        <InteractionsSection graph={interactionGraph} report={report} onSelectEvent={setSelectedEvent} />
      ) : selectedTab === "timeline" ? (
        <TimelineSection
          events={timelineEvents}
          timelineKey={timelineKey}
          selectedId={eventId || undefined}
          onSelect={setSelectedEvent}
          visibleCount={filteredEvents.length}
          report={report}
        />
      ) : selectedTab === "ledger" ? (
        <LedgerSection
          events={filteredEvents}
          eventId={eventId || undefined}
          onSelectEvent={setSelectedEvent}
          kindFilter={
            filters.kinds[0] === "Network" || filters.kinds[0] === "File" || filters.kinds[0] === "Activation"
              ? filters.kinds[0]
              : "all"
          }
          onKindFilterChange={(next) => {
            const nextKinds = next === "all" ? [] : [next];
            updateFilters({ ...filters, kinds: nextKinds });
          }}
        />
      ) : (
        <AuditSection report={report} />
      )}

      <SlideOverDrawer
        description="Narrow the evidence set without crowding the main workspace."
        onClose={() => setFiltersOpen(false)}
        open={filtersOpen}
        title="Evidence filters"
      >
        <FilterRail
          description="Filters update the URL in place and combine with the active evidence-class tab."
          filters={filters}
          onChange={updateFilters}
          options={options}
          showSearch={false}
          title="Refine evidence"
        />
      </SlideOverDrawer>
    </div>
  );
}

type CellProps = {
  label: string;
  value: string;
  tone?: V3Tone;
};

function Cell({ label, value, tone = "neutral" }: CellProps) {
  return (
    <div
      style={{
        padding: "20px 22px",
        borderRight: `1px solid ${V3.rule}`,
      }}
    >
      <MetricCell
        label={label}
        value={<span style={{ fontSize: 28, letterSpacing: 0 }}>{value}</span>}
        tone={tone}
      />
    </div>
  );
}

function OverviewSection({
  report,
}: {
  report: ReportModel;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <VerdictSummaryPanel detection={report.detection} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))", gap: 20 }}>
        <BreakdownPanel label="By kind" rows={buildKindRows(report)} />
        <BreakdownPanel label="Risk mix" rows={buildRiskRows(report)} />
      </div>
    </div>
  );
}

function VerdictSummaryPanel({
  detection,
}: {
  detection: ReportModel["detection"];
}) {
  if (!detection?.findings.length) return null;
  const visible = detection.findings.slice(0, 3);
  const overflow = detection.findings.length - visible.length;
  return (
    <Panel label="Findings">
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {visible.map((finding) => (
          <FindingCard key={finding.id} finding={finding} />
        ))}
        {overflow > 0 ? (
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: V3.ink3,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
            }}
          >
            +{overflow} more · open Event ledger to drill in
          </span>
        ) : null}
      </div>
    </Panel>
  );
}

function InteractionsSection({
  graph,
  report,
  onSelectEvent,
}: {
  graph: ReturnType<typeof buildInteractionGraph> | null;
  report: ReportModel;
  onSelectEvent: (eventId: string) => void;
}) {
  const relationGroupRows = buildRelationGroupRows(graph);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {graph && graph.groups.length ? (
        <Panel label="Interaction graph">
          <InteractionGraph data={graph} />
        </Panel>
      ) : (
        <EmptyState
          eyebrow="Interactions"
          title="No interaction graph"
          body="This report did not include enough linked evidence to draw an interaction graph."
        />
      )}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))", gap: 20 }}>
        {relationGroupRows.length ? (
          <BreakdownPanel label="Relation groups" rows={relationGroupRows} />
        ) : (
          <Panel label="Relation groups">
            <p style={{ margin: 0, color: V3.ink3, fontSize: 13, lineHeight: 1.6 }}>
              No relation groups were derived from the linked evidence.
            </p>
          </Panel>
        )}
        <ConnectionSummaryPanel report={report} onSelectEvent={onSelectEvent} />
      </div>
    </div>
  );
}

function ConnectionSummaryPanel({
  report,
  onSelectEvent,
}: {
  report: ReportModel;
  onSelectEvent: (eventId: string) => void;
}) {
  const signals = report.riskSignals;
  if (!signals.length) {
    return (
      <Panel label="Connection summary">
        <p style={{ margin: 0, color: V3.ink3, fontSize: 13, lineHeight: 1.6 }}>
          No risk signals were associated with this run.
        </p>
      </Panel>
    );
  }
  return (
    <Panel label="Connection summary" padded={false}>
      <div style={{ display: "flex", flexDirection: "column" }}>
        {signals.map((signal, index) => {
          const tone = severityToTone(signal.severity);
          const firstEvidence = signal.evidenceEventIds[0];
          return (
            <button
              key={signal.signalId}
              type="button"
              onClick={() => firstEvidence && onSelectEvent(firstEvidence)}
              style={{
                textAlign: "left",
                background: "transparent",
                border: "none",
                cursor: firstEvidence ? "pointer" : "default",
                display: "grid",
                gridTemplateColumns: "1fr auto",
                gap: 12,
                alignItems: "start",
                padding: "14px 16px",
                borderBottom: index < signals.length - 1 ? `1px solid ${V3.rule}` : "none",
                color: "inherit",
              }}
            >
              <div style={{ minWidth: 0 }}>
                <Eyebrow>{signal.categoryLabel}</Eyebrow>
                <p style={{ margin: "6px 0 0", color: V3.ink3, fontSize: 13, lineHeight: 1.6 }}>
                  {signal.summary}
                </p>
              </div>
              <Badge tone={tone}>{signal.confidencePct}%</Badge>
            </button>
          );
        })}
      </div>
    </Panel>
  );
}

type TimelineEvent = {
  id: string;
  label?: string;
  relTimeS?: number | null;
  kind?: string;
  risk?: "low" | "medium" | "high";
};

function TimelineSection({
  events,
  timelineKey,
  selectedId,
  onSelect,
  visibleCount,
  report,
}: {
  events: ReadonlyArray<TimelineEvent>;
  timelineKey: string;
  selectedId?: string;
  onSelect: (eventId: string) => void;
  visibleCount: number;
  report: ReportModel;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <Panel
        label="Timeline"
        right={<Eyebrow>{formatNumber(visibleCount)} visible events</Eyebrow>}
        bodyStyle={{ padding: 0 }}
      >
        <div style={{ padding: "18px 20px", borderBottom: `1px solid ${V3.rule}` }}>
          <p style={{ margin: 0, maxWidth: 720, color: V3.ink3, fontSize: 13.5, lineHeight: 1.6 }}>
            Canonical report timeline. Category mini timelines were removed so temporal analysis has one source of truth.
          </p>
        </div>
        <div style={{ padding: "18px 20px" }}>
          <EventTimeline key={timelineKey} events={events} selectedId={selectedId} onSelect={onSelect} height={280} />
        </div>
      </Panel>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))", gap: 20 }}>
        <BreakdownPanel label="By kind" rows={buildKindRows(report)} />
        <Panel label="Density · 1s buckets" bodyStyle={{ padding: 0 }}>
          <EventDensityStrip events={events} selectedId={selectedId} onSelect={onSelect} />
        </Panel>
      </div>
    </div>
  );
}

function EventDensityStrip({
  events,
  selectedId,
  onSelect,
}: {
  events: ReadonlyArray<TimelineEvent>;
  selectedId?: string;
  onSelect: (eventId: string) => void;
}) {
  const maxT = events.reduce((acc, event) => Math.max(acc, event.relTimeS ?? 0), 0) + 1;
  const bucketCount = Math.max(1, Math.ceil(maxT) + 1);
  const buckets: TimelineEvent[][] = Array.from({ length: bucketCount }, () => []);
  events.forEach((event) => {
    if (typeof event.relTimeS === "number") {
      const idx = Math.min(Math.floor(event.relTimeS), bucketCount - 1);
      if (idx >= 0) buckets[idx].push(event);
    }
  });
  const maxCount = Math.max(1, ...buckets.map((bucket) => bucket.length));
  return (
    <div style={{ padding: "14px 16px" }}>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height: 84 }}>
        {buckets.map((bucket, index) => {
          const hasSelected = bucket.some((event) => event.id === selectedId);
          const topRisk = bucket.reduce<{ rank: number; color: string }>(
            (acc, event) => {
              const risk = event.risk ?? "low";
              const rank = risk === "high" ? 3 : risk === "medium" ? 2 : 1;
              if (rank <= acc.rank) return acc;
              return {
                rank,
                color: risk === "high" ? V3.coral : risk === "medium" ? V3.warn : V3.ok,
              };
            },
            { rank: 0, color: V3.rule2 },
          );
          const heightPx = bucket.length === 0 ? 2 : (bucket.length / maxCount) * 64 + 6;
          const target = bucket[0];
          return (
            <button
              key={index}
              type="button"
              disabled={!target}
              onClick={() => target && onSelect(target.id)}
              aria-label={`Bucket ${index}s · ${bucket.length} events`}
              title={`${index}s · ${bucket.length} events`}
              style={{
                flex: 1,
                height: heightPx,
                background: bucket.length ? topRisk.color : V3.rule,
                opacity: bucket.length ? (hasSelected ? 1 : 0.85) : 0.4,
                borderTop: hasSelected ? `2px solid ${V3.ink}` : "none",
                border: 0,
                padding: 0,
                cursor: bucket.length ? "pointer" : "default",
                transition: "all 180ms",
              }}
            />
          );
        })}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: V3.ink4, letterSpacing: "0.08em" }}>
          0s
        </span>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: V3.ink4, letterSpacing: "0.08em" }}>
          {Math.ceil(maxT)}s
        </span>
      </div>
    </div>
  );
}

type LedgerKindFilter = "all" | "Network" | "File" | "Activation";

const LEDGER_KIND_TABS: TabSpec<LedgerKindFilter>[] = [
  { value: "all", label: "All" },
  { value: "Network", label: "Network" },
  { value: "File", label: "File" },
  { value: "Activation", label: "Activation" },
];

function LedgerSection({
  events,
  eventId,
  onSelectEvent,
  kindFilter,
  onKindFilterChange,
}: {
  events: ReportModel["evidence"];
  eventId?: string;
  onSelectEvent: (eventId: string) => void;
  kindFilter: LedgerKindFilter;
  onKindFilterChange: (next: LedgerKindFilter) => void;
}) {
  if (!events.length) {
    return (
      <EmptyState
        eyebrow="Event ledger"
        title="No evidence matches this slice"
        body="The active report and filters produced no matching events."
      />
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <Tabs<LedgerKindFilter>
        ariaLabel="Kind filter"
        tabs={LEDGER_KIND_TABS}
        value={kindFilter}
        onChange={onKindFilterChange}
      />
      <Panel label="Event ledger" bodyStyle={{ padding: 0 }}>
        <EvidenceLedger events={events} onSelect={onSelectEvent} selectedEventId={eventId} />
      </Panel>
    </div>
  );
}

function AuditSection({ report }: { report: ReportModel }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <LogStreamsPanel
        eventAttempts={report.eventAttempts}
        coverageTracks={report.coverageTracks}
        heuristicWorkflowCoverage={report.heuristicWorkflowCoverage}
        logStreams={report.logStreams}
        officialEventCoverage={report.officialEventCoverage}
        stimulusPasses={report.stimulusPasses}
      />
    </div>
  );
}

function BreakdownPanel({
  label,
  rows,
}: {
  label: string;
  rows: Array<{ label: string; value: string; tone?: V3Tone }>;
}) {
  return (
    <Panel label={label} padded={false}>
      <div style={{ display: "flex", flexDirection: "column" }}>
        {rows.map((row, index) => (
          <div
            key={row.label}
            style={{
              display: "grid",
              gridTemplateColumns: "1fr auto",
              gap: 16,
              alignItems: "center",
              padding: "14px 16px",
              borderBottom: index < rows.length - 1 ? `1px solid ${V3.rule}` : "none",
            }}
          >
            <Eyebrow>{row.label}</Eyebrow>
            <span
              style={{
                fontFamily: "'Manrope', sans-serif",
                fontSize: 24,
                fontWeight: 800,
                letterSpacing: 0,
                color: row.tone === "danger" ? V3.coral : row.tone === "warn" ? V3.warn : row.tone === "ok" ? V3.ok : V3.ink,
                lineHeight: 1,
              }}
            >
              {row.value}
            </span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function buildKindRows(report: ReportModel) {
  const counts = report.evidence.reduce<Record<string, number>>((acc, event) => {
    acc[event.kindLabel] = (acc[event.kindLabel] ?? 0) + 1;
    return acc;
  }, {});

  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .map(([label, value]) => ({ label, value: formatNumber(value) }));
}

function buildRiskRows(report: ReportModel) {
  const totalSignals = report.riskSignals.length;
  const highSignals = report.riskSignals.filter((signal) => signal.severity === "critical" || signal.severity === "high").length;
  const mediumSignals = report.riskSignals.filter((signal) => signal.severity === "medium").length;
  const sensitiveEvents = report.evidence.filter((event) => event.sensitive).length;

  return [
    { label: "Signals", value: formatNumber(totalSignals), tone: totalSignals ? "danger" : "ok" },
    { label: "High severity", value: formatNumber(highSignals), tone: highSignals ? "danger" : "neutral" },
    { label: "Medium severity", value: formatNumber(mediumSignals), tone: mediumSignals ? "warn" : "neutral" },
    { label: "Sensitive events", value: formatNumber(sensitiveEvents), tone: sensitiveEvents ? "warn" : "ok" },
  ] satisfies Array<{ label: string; value: string; tone?: V3Tone }>;
}

function buildRelationGroupRows(
  graph: ReturnType<typeof buildInteractionGraph> | null,
): Array<{ label: string; value: string; tone?: V3Tone }> {
  if (!graph) return [];
  return graph.groups.slice(0, 5).map((group) => {
    const tone: V3Tone =
      group.axis === "secret"
        ? "danger"
        : group.axis === "network"
          ? "warn"
          : group.axis === "fs"
            ? "warn"
            : group.axis === "process"
              ? "accent"
              : "neutral";
    return {
      label: group.label,
      value: formatNumber(group.count),
      tone,
    };
  });
}
