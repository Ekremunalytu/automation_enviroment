import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";

import { FilterRail, type EvidenceFilterState } from "../../components/evidence/FilterRail";
import { LogStreamsPanel } from "../../components/evidence/LogStreamsPanel";
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
  V3,
  type V3Tone,
} from "../../components/v3";
import {
  applyEvidenceFilters,
  buildEvidenceFilterOptions,
  countEvidenceFilters,
  filterEvidenceEvents,
  normalizeInspectorTab,
  parseEvidenceFilters,
} from "../evidence";
import { apiClient } from "../../lib/api/client";
import {
  adaptBundle,
  adaptReport,
  buildInteractionGraph,
  buildRiskRadar,
  getInspectorView,
} from "../../lib/adapters/report";
import { buildRuleDraft } from "../../lib/rules/draft";
import { CategoryWorkspace, type ReportWorkspaceTab } from "./sections";
import { DetectionPanel } from "./DetectionPanel";
import { EventTimeline } from "./charts/EventTimeline";
import { InteractionGraph } from "./charts/InteractionGraph";
import { RADAR_AXES, RiskRadar } from "./charts/RiskRadar";

type ReportTab = "detection" | "activation" | "file" | "network" | "scenario" | "evidence" | "logs";

const REPORT_TABS: Array<{ value: ReportTab; label: string }> = [
  { value: "detection", label: "Detection" },
  { value: "activation", label: "Activation" },
  { value: "file", label: "File I/O" },
  { value: "network", label: "Network" },
  { value: "scenario", label: "Scenario" },
  { value: "evidence", label: "All Events" },
  { value: "logs", label: "Logs" },
];

const TAB_META: Record<Exclude<ReportTab, "detection">, { title: string; description: string; emptyTitle: string }> = {
  activation: {
    title: "Activation stream",
    description: "Extension activation entries only. Use this view to isolate startup triggers and activation ownership.",
    emptyTitle: "No activation evidence in this slice",
  },
  file: {
    title: "File I/O",
    description: "File system reads and writes only. This tab isolates path-level evidence and sensitive file access.",
    emptyTitle: "No file I/O evidence in this slice",
  },
  network: {
    title: "Network activity",
    description: "Outbound hosts, paths, and destinations only. This tab keeps network evidence separate from file and activation noise.",
    emptyTitle: "No network evidence in this slice",
  },
  scenario: {
    title: "Scenario traces",
    description: "Automation and scenario events only. Use this view to understand which scenario produced which evidence clusters.",
    emptyTitle: "No scenario traces in this slice",
  },
  evidence: {
    title: "All evidence",
    description: "Full evidence view across all event kinds, with the timeline and the table kept as the dominant working surface.",
    emptyTitle: "No evidence matches this slice",
  },
  logs: {
    title: "Split-stream logs",
    description: "Target extension triggers, other extensions, and automation trace are kept in separate streams.",
    emptyTitle: "No logs are available for this report",
  },
};

function normalizeTab(raw: string | null): ReportTab {
  if (!raw || raw === "overview" || raw === "dashboard") return "detection";
  if (raw === "evidence") return "evidence";
  return REPORT_TABS.some((tab) => tab.value === raw) ? (raw as ReportTab) : "detection";
}

function normalizeWorkspaceTab(raw: string | null): ReportWorkspaceTab {
  return raw === "analysis" ? "analysis" : "evidence";
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

function scopeEventsForTab(
  tab: ReportTab,
  events: NonNullable<ReturnType<typeof adaptReport>>["evidence"],
) {
  if (tab === "detection" || tab === "evidence") return events;
  if (tab === "file") return events.filter((event) => event.kind === "file");
  return events.filter((event) => event.kind === tab);
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
  const inspectorTab = normalizeInspectorTab(searchParams.get("inspector"));
  const workspaceTab = normalizeWorkspaceTab(searchParams.get("workspace"));
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
  const filteredEvents = report
    ? filterEvidenceEvents(report.evidence, filters, deferredSearch)
    : [];

  const scopedEvents = scopeEventsForTab(selectedTab, filteredEvents);

  useEffect(() => {
    if (selectedTab === "detection" || selectedTab === "logs") return;
    if (!scopedEvents.length) return;

    const candidate = scopedEvents[0]?.eventId;
    if (!candidate) return;

    if (!eventId || !scopedEvents.some((event) => event.eventId === eventId)) {
      const next = new URLSearchParams(searchParams);
      next.set("event", candidate);
      setSearchParams(next, { replace: true });
    }
  }, [eventId, scopedEvents, searchParams, selectedTab, setSearchParams]);

  const inspector = report ? getInspectorView(report, eventId) : null;
  const ruleDraft = buildRuleDraft(inspector);
  const options = buildEvidenceFilterOptions(report?.evidence || []);
  const activeFilterCount = countEvidenceFilters(filters);
  const activeReport =
    reportParam === "latest"
      ? reportsQuery.data?.[0]
      : reportsQuery.data?.find((item) => item.filename === reportParam) || reportsQuery.data?.[0];

  const interactionGraph = useMemo(() => (report ? buildInteractionGraph(report) : null), [report]);
  const radarScores = useMemo(() => (report ? buildRiskRadar(report) : null), [report]);
  const timelineEvents = useMemo(() => {
    if (!report) return [];
    return report.evidence.map((event) => ({
      id: event.eventId,
      relTimeS: event.relTimeS,
      kind: event.kind,
      label: event.summaryDisplay || event.summary,
      risk: (event.sensitive ? "high" : event.kind === "network" ? "medium" : "low") as
        | "low"
        | "medium"
        | "high",
    }));
  }, [report]);

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

  const showFindingEvidence = (nextEventId: string) => {
    startTransition(() => {
      const next = new URLSearchParams(searchParams);
      next.set("tab", "evidence");
      next.set("workspace", "evidence");
      next.set("event", nextEventId);
      setSearchParams(next, { replace: true });
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
            <Badge tone={verdictTone} data-feature-stub="verdict-badge">
              Verdict · {verdict.toUpperCase()}
            </Badge>
          ) : null}
          <Badge tone="neutral" data-feature-stub="reports-list-metadata">
            Severity TBD · backend pending
          </Badge>
        </div>
        <PageTitle style={{ marginTop: 14 }}>Security report</PageTitle>
        <p style={{ fontSize: 14, color: V3.ink3, marginTop: 14, maxWidth: 640, lineHeight: 1.6 }}>
          Keep the dashboard clean, then drill into one evidence class at a time instead of
          stacking every signal into a single screen.
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

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "1fr auto",
          gap: 24,
          alignItems: "stretch",
        }}
      >
        <Panel padded={false}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              borderBottom: `1px solid ${V3.rule}`,
            }}
          >
            <Cell label="Total events" value={formatNumber(report?.summary.totalEvents ?? 0)} />
            <Cell label="Sensitive" value={formatNumber(report?.summary.sensitiveEvents ?? 0)} tone="danger" />
            <Cell label="Network" value={formatNumber(report?.summary.networkEvents ?? 0)} tone="warn" />
            <Cell label="Score" value={`${report?.summary.signalSummaryScore ?? 0}`} tone={verdictTone} />
          </div>
          <div style={{ padding: "16px 22px" }}>
            <KVRow k="Active report" v={report?.metadataFilename || "Preparing selected report"} />
            <KVRow k="Last updated" v={formatModified(activeReport?.modified)} />
            <KVRow k="Run quality" v={report?.summary.runQuality ?? "—"} mono={false} />
          </div>
        </Panel>

        <Panel label="Selector" padded>
          <div style={{ display: "flex", flexDirection: "column", gap: 12, minWidth: 280 }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
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
                  padding: "10px 12px",
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 12.5,
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
        </Panel>
      </section>

      <section
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 0,
          borderBottom: `1px solid ${V3.rule2}`,
        }}
      >
        {REPORT_TABS.map((tab) => {
          const active = tab.value === selectedTab;
          return (
            <button
              key={tab.value}
              type="button"
              onClick={() => {
                const params = new URLSearchParams(searchParams);
                params.set("tab", tab.value);
                setSearchParams(params, { replace: true });
              }}
              style={{
                background: "none",
                border: "none",
                padding: "12px 18px 13px",
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 11,
                fontWeight: active ? 700 : 500,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                color: active ? V3.ink : V3.ink3,
                cursor: "pointer",
                position: "relative",
                transition: "color 140ms",
              }}
            >
              {tab.label}
              {active ? (
                <span
                  aria-hidden
                  style={{
                    position: "absolute",
                    left: 0,
                    right: 0,
                    bottom: -1,
                    height: 3,
                    background: V3.coral,
                  }}
                />
              ) : null}
            </button>
          );
        })}
      </section>

      {reportQuery.isLoading ? (
        <EmptyState
          eyebrow="Loading"
          body="Fetching the selected report and normalizing evidence."
          title="Preparing report workspace"
        />
      ) : reportQuery.isError ? (
        <EmptyState eyebrow="Error" body={String(reportQuery.error)} title="Report could not be loaded" />
      ) : !report ? null : selectedTab === "detection" ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <DetectionPanel detection={report.detection} onShowEvidence={showFindingEvidence} />
          {radarScores ? (
            <Panel label="Risk radar (synthetic)">
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr auto",
                  gap: 24,
                  alignItems: "center",
                }}
              >
                <RiskRadar scores={radarScores} />
                <div style={{ minWidth: 240 }}>
                  {RADAR_AXES.map((axis) => (
                    <KVRow
                      key={axis}
                      k={axis}
                      v={`${radarScores[axis]} / 100`}
                    />
                  ))}
                  <p
                    style={{
                      marginTop: 12,
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 10,
                      color: V3.ink4,
                      letterSpacing: "0.06em",
                      lineHeight: 1.6,
                    }}
                  >
                    Approximate scores derived from kind frequency. Backend axis
                    scoring lands with [BACKLOG ui-v3-4].
                  </p>
                </div>
              </div>
            </Panel>
          ) : null}
          {interactionGraph && interactionGraph.groups.length ? (
            <Panel label="Interaction graph (synthetic)">
              <InteractionGraph data={interactionGraph} />
            </Panel>
          ) : null}
          <Panel label="Event timeline">
            <EventTimeline
              events={timelineEvents}
              selectedId={eventId || undefined}
              onSelect={(id) => setSelectedEvent(id)}
            />
          </Panel>
        </div>
      ) : selectedTab === "logs" ? (
        <LogStreamsPanel
          eventAttempts={report.eventAttempts}
          coverageTracks={report.coverageTracks}
          heuristicWorkflowCoverage={report.heuristicWorkflowCoverage}
          logStreams={report.logStreams}
          officialEventCoverage={report.officialEventCoverage}
          stimulusPasses={report.stimulusPasses}
        />
      ) : (
        <CategoryWorkspace
          emptyTitle={TAB_META[selectedTab].emptyTitle}
          events={scopedEvents}
          inspector={inspector}
          inspectorTab={inspectorTab}
          onInspectorTabChange={(next) => {
            const params = new URLSearchParams(searchParams);
            params.set("inspector", next);
            setSearchParams(params, { replace: true });
          }}
          onWorkspaceTabChange={(next) => {
            const params = new URLSearchParams(searchParams);
            params.set("workspace", next);
            setSearchParams(params, { replace: true });
          }}
          onSelectEvent={setSelectedEvent}
          selectedEventId={eventId || undefined}
          ruleDraft={ruleDraft}
          title={TAB_META[selectedTab].title}
          description={TAB_META[selectedTab].description}
          workspaceTab={workspaceTab}
        />
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
        value={<span style={{ fontSize: 28, letterSpacing: "-0.03em" }}>{value}</span>}
        tone={tone}
      />
    </div>
  );
}
