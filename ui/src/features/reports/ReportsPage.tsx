import { startTransition, useDeferredValue, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { FilterRail, type EvidenceFilterState } from "../../components/evidence/FilterRail";
import { LogStreamsPanel } from "../../components/evidence/LogStreamsPanel";
import { EmptyState } from "../../components/ui/EmptyState";
import { SlideOverDrawer } from "../../components/ui/SlideOverDrawer";
import {
  applyEvidenceFilters,
  buildEvidenceFilterOptions,
  countEvidenceFilters,
  filterEvidenceEvents,
  normalizeInspectorTab,
  parseEvidenceFilters,
} from "../evidence";
import { apiClient } from "../../lib/api/client";
import { adaptBundle, adaptReport, getInspectorView } from "../../lib/adapters/report";
import { buildRuleDraft } from "../../lib/rules/draft";
import { CategoryWorkspace, type ReportWorkspaceTab } from "./sections";
import { DetectionPanel } from "./DetectionPanel";

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

  return (
    <div className="space-y-6">
      <section className="page-header">
        <div className="space-y-3">
          <div className="eyebrow">Reports</div>
          <h1 className="page-title">Security report</h1>
          <p className="max-w-3xl text-sm leading-7 text-mute sm:text-base">
            Keep the dashboard clean, then drill into one evidence class at a time instead of stacking every signal into a single screen.
          </p>
          <div className="flex flex-wrap gap-2">
            <span className="info-chip">{report?.metadataFilename || "Loading report workspace"}</span>
            <span className="info-chip">{formatNumber(filteredEvents.length)} visible events</span>
          </div>
        </div>

        <div className="section-tabs">
          {REPORT_TABS.map((tab) => {
            const active = tab.value === selectedTab;
            return (
              <button
                className={`section-tab ${active ? "section-tab-active" : ""}`}
                key={tab.value}
                onClick={() => {
                  const params = new URLSearchParams(searchParams);
                  params.set("tab", tab.value);
                  setSearchParams(params, { replace: true });
                }}
                type="button"
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </section>

      <section className="toolbar-surface">
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(420px,0.9fr)]">
          <div className="min-w-0 rounded-[16px] border border-lineSoft bg-panelAlt px-4 py-4">
            <div className="micro-label">Active report</div>
            <div className="mt-3 text-xl font-semibold tracking-tight text-ink">
              {report?.metadataFilename || "Preparing selected report"}
            </div>
            <div className="mt-2 text-sm leading-6 text-mute">
              Last updated {formatModified(activeReport?.modified)}. Filters and inspector state remain shareable through the URL.
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <label className="space-y-2">
              <span className="micro-label">Report</span>
              <select
                className="field-control"
                onChange={(event) => {
                  const next = new URLSearchParams(searchParams);
                  next.set("report", event.target.value);
                  setSearchParams(next, { replace: true });
                }}
                value={reportParam}
              >
                <option value="latest">Latest report</option>
                {(reportsQuery.data || []).map((item) => (
                  <option key={item.filename} value={item.filename}>
                    {item.filename}
                  </option>
                ))}
              </select>
            </label>

            <label className="space-y-2">
              <span className="micro-label">Search</span>
              <input
                className="field-control"
                onChange={(event) => updateFilters({ ...filters, search: event.target.value })}
                placeholder="host, path, extension, summary…"
                value={filters.search}
              />
            </label>

            <div className="md:col-span-2">
              <button className="ghost-button" onClick={() => setFiltersOpen(true)} type="button">
                Filters {activeFilterCount ? `(${activeFilterCount})` : ""}
              </button>
            </div>
          </div>
        </div>
      </section>

      {reportQuery.isLoading ? (
        <EmptyState eyebrow="Loading" body="Fetching the selected report and normalizing evidence." title="Preparing report workspace" />
      ) : reportQuery.isError ? (
        <EmptyState eyebrow="Error" body={String(reportQuery.error)} title="Report could not be loaded" />
      ) : !report ? null : selectedTab === "detection" ? (
        <DetectionPanel detection={report.detection} onShowEvidence={showFindingEvidence} />
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
