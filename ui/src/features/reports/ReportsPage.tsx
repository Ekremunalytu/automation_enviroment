import { startTransition, useDeferredValue, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { EvidenceTable } from "../../components/evidence/EvidenceTable";
import { EvidenceTimelineChart } from "../../components/evidence/EvidenceTimelineChart";
import { FilterRail, type EvidenceFilterState } from "../../components/evidence/FilterRail";
import { Inspector } from "../../components/evidence/Inspector";
import { LogStreamsPanel } from "../../components/evidence/LogStreamsPanel";
import { RiskOverviewPanel } from "../../components/evidence/RiskOverviewPanel";
import { EmptyState } from "../../components/ui/EmptyState";
import { Panel, PanelHeader } from "../../components/ui/Panel";
import { SegmentedTabs } from "../../components/ui/SegmentedTabs";
import { SlideOverDrawer } from "../../components/ui/SlideOverDrawer";
import { apiClient } from "../../lib/api/client";
import { adaptReport, getInspectorView } from "../../lib/adapters/report";
import { buildRuleDraft } from "../../lib/rules/draft";

type ReportTab = "dashboard" | "activation" | "file" | "network" | "scenario" | "evidence" | "logs";
type InspectorTab = "provenance" | "relations" | "rules";
type WorkspaceTab = "evidence" | "analysis";

const REPORT_TABS: Array<{ value: ReportTab; label: string }> = [
  { value: "dashboard", label: "Dashboard" },
  { value: "activation", label: "Activation" },
  { value: "file", label: "File I/O" },
  { value: "network", label: "Network" },
  { value: "scenario", label: "Scenario" },
  { value: "evidence", label: "All Events" },
  { value: "logs", label: "Logs" },
];

const TAB_META: Record<Exclude<ReportTab, "dashboard">, { title: string; description: string; emptyTitle: string }> = {
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
  if (!raw || raw === "overview") return "dashboard";
  if (raw === "evidence") return "evidence";
  return REPORT_TABS.some((tab) => tab.value === raw) ? (raw as ReportTab) : "dashboard";
}

function normalizeInspectorTab(raw: string | null): InspectorTab {
  if (raw === "relations" || raw === "rules") return raw;
  if (raw === "rule") return "rules";
  return "provenance";
}

function normalizeWorkspaceTab(raw: string | null): WorkspaceTab {
  return raw === "analysis" ? "analysis" : "evidence";
}

function parseFilters(searchParams: URLSearchParams): EvidenceFilterState {
  return {
    kinds: searchParams.get("kind") ? [searchParams.get("kind")!] : [],
    actors: searchParams.get("actor") ? [searchParams.get("actor")!] : [],
    collectors: searchParams.get("collector") ? [searchParams.get("collector")!] : [],
    scenarios: searchParams.get("scenario") ? [searchParams.get("scenario")!] : [],
    sensitiveOnly: searchParams.get("sensitive") === "true",
    search: searchParams.get("search") || "",
  };
}

function applyFilters(searchParams: URLSearchParams, filters: EvidenceFilterState) {
  const next = new URLSearchParams(searchParams);
  const assign = (key: string, value?: string) => {
    if (value) next.set(key, value);
    else next.delete(key);
  };
  assign("kind", filters.kinds[0]);
  assign("actor", filters.actors[0]);
  assign("collector", filters.collectors[0]);
  assign("scenario", filters.scenarios[0]);
  assign("search", filters.search || undefined);
  if (filters.sensitiveOnly) next.set("sensitive", "true");
  else next.delete("sensitive");
  return next;
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

function countActiveFilters(filters: EvidenceFilterState) {
  return [
    filters.kinds.length,
    filters.actors.length,
    filters.collectors.length,
    filters.scenarios.length,
    filters.sensitiveOnly ? 1 : 0,
    filters.search ? 1 : 0,
  ].reduce((sum, count) => sum + count, 0);
}

function formatNumber(value: number) {
  return value.toLocaleString();
}

function computeRiskScore(report: NonNullable<ReturnType<typeof adaptReport>>) {
  const score = Math.max(8, Math.min(96, Math.round(report.summary.verdictScore || 0)));
  const labelByLevel = {
    benign: "Benign",
    needs_review: "Needs review",
    suspicious: "Suspicious",
    likely_malicious: "Likely malicious",
  } as const;

  return {
    score,
    label: labelByLevel[report.summary.verdictLevel] || "Needs review",
    note:
      report.summary.verdictNote ||
      "This report did not include a computed verdict note.",
    reasons: report.summary.verdictReasons,
  };
}

function scopeEventsForTab(
  tab: ReportTab,
  events: NonNullable<ReturnType<typeof adaptReport>>["evidence"],
) {
  if (tab === "dashboard" || tab === "evidence") return events;
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
  const filters = parseFilters(searchParams);
  const deferredSearch = useDeferredValue(filters.search);

  const reportsQuery = useQuery({
    queryKey: ["reports"],
    queryFn: () => apiClient.listReports(),
    refetchInterval: 4000,
  });

  const reportQuery = useQuery({
    queryKey: ["report", reportParam],
    queryFn: async () => {
      const dto = reportParam === "latest" ? await apiClient.getLatestReport() : await apiClient.getReportByName(reportParam);
      return adaptReport(dto, reportParam);
    },
  });

  const report = reportQuery.data;
  const filteredEvents =
    report?.evidence.filter((event) => {
      if (filters.kinds.length && !filters.kinds.includes(event.kindLabel)) return false;
      if (filters.actors.length && !filters.actors.includes(event.actorLabel)) return false;
      if (filters.collectors.length && !filters.collectors.includes(event.collectorLabel)) return false;
      if (filters.scenarios.length && !filters.scenarios.includes(event.scenarioName)) return false;
      if (filters.sensitiveOnly && !event.sensitive) return false;
      if (deferredSearch) {
        const haystack = [
          event.artifact,
          event.summaryDisplay,
          event.extensionId,
          event.host,
          event.path,
          event.scenarioName,
        ]
          .join(" ")
          .toLowerCase();
        if (!haystack.includes(deferredSearch.toLowerCase())) return false;
      }
      return true;
    }) || [];

  const scopedEvents = scopeEventsForTab(selectedTab, filteredEvents);

  useEffect(() => {
    if (selectedTab === "dashboard" || selectedTab === "logs") return;
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
  const options = {
    kinds: [...new Set(report?.evidence.map((event) => event.kindLabel) || [])],
    actors: [...new Set(report?.evidence.map((event) => event.actorLabel) || [])],
    collectors: [...new Set(report?.evidence.map((event) => event.collectorLabel) || [])],
    scenarios: [...new Set(report?.evidence.map((event) => event.scenarioName).filter(Boolean) || [])],
  };
  const activeFilterCount = countActiveFilters(filters);
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
      setSearchParams(applyFilters(searchParams, nextFilters), { replace: true });
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
      ) : !report ? null : selectedTab === "dashboard" ? (
        <DashboardScore report={report} onSelectEvent={setSelectedEvent} />
      ) : selectedTab === "logs" ? (
        <LogStreamsPanel
          coverageMatrix={report.coverageMatrix}
          coverageSummary={report.coverageSummary}
          logStreams={report.logStreams}
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

function DashboardScore({
  report,
  onSelectEvent,
}: {
  report: NonNullable<ReturnType<typeof adaptReport>>;
  onSelectEvent: (eventId: string) => void;
}) {
  const risk = computeRiskScore(report);
  const toneClass = risk.score >= 75 ? "text-danger" : risk.score >= 45 ? "text-warning" : "text-accent";

  return (
    <div className="space-y-6">
      <RiskOverviewPanel
        attributionSummary={report.attributionSummary}
        onSelectEvent={onSelectEvent}
        riskSignals={report.riskSignals}
        summary={report.summary}
        title="Automation health"
        description="Target observation and run reliability are shown ahead of risk scoring so degraded or inconclusive runs are visible immediately."
      />

      <section className="score-surface">
        <div className="eyebrow">Dashboard</div>
        <div className="mt-6 grid gap-8 lg:grid-cols-[260px_minmax(0,1fr)] lg:items-center">
          <div className="flex h-[220px] w-[220px] items-center justify-center rounded-full border border-lineStrong bg-panelAlt">
            <div className="text-center">
              <div className={`font-display text-[82px] font-semibold tracking-[-0.06em] ${toneClass}`}>{risk.score}</div>
              <div className="mt-2 text-sm font-medium text-inkSoft">General score</div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <div className="text-[30px] font-semibold tracking-[-0.04em] text-ink">{risk.label}</div>
              <p className="mt-3 max-w-2xl text-base leading-8 text-mute">{risk.note}</p>
              {risk.reasons.length ? (
                <div className="mt-4 space-y-2 text-sm leading-6 text-mute">
                  {risk.reasons.slice(0, 4).map((reason) => (
                    <div key={reason}>{reason}</div>
                  ))}
                </div>
              ) : null}
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-panelAlt">
              <div className="h-full rounded-full bg-accent" style={{ width: `${risk.score}%` }} />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function CategoryWorkspace({
  title,
  description,
  events,
  selectedEventId,
  onSelectEvent,
  inspector,
  inspectorTab,
  onInspectorTabChange,
  onWorkspaceTabChange,
  emptyTitle,
  ruleDraft,
  workspaceTab,
}: {
  title: string;
  description: string;
  events: NonNullable<ReturnType<typeof adaptReport>>["evidence"];
  selectedEventId?: string;
  onSelectEvent: (eventId: string) => void;
  inspector: ReturnType<typeof getInspectorView>;
  inspectorTab: InspectorTab;
  onInspectorTabChange: (next: InspectorTab) => void;
  onWorkspaceTabChange: (next: WorkspaceTab) => void;
  emptyTitle: string;
  ruleDraft: ReturnType<typeof buildRuleDraft>;
  workspaceTab: WorkspaceTab;
}) {
  if (!events.length) {
    return <EmptyState eyebrow="Filtered Out" body="The active filters and report slice produced no matching events." title={emptyTitle} />;
  }

  return (
    <div className="space-y-6">
      <section className="space-y-4">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <div className="eyebrow">Evidence class</div>
            <h2 className="mt-3 text-[32px] font-semibold tracking-[-0.04em] text-ink">{title}</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-mute sm:text-base">{description}</p>
          </div>

          <SegmentedTabs
            onChange={(next) => onWorkspaceTabChange(next as WorkspaceTab)}
            options={[
              { value: "evidence", label: "Evidence" },
              { value: "analysis", label: "Analysis" },
            ]}
            value={workspaceTab}
          />
        </div>
      </section>

      {workspaceTab === "evidence" ? (
        <section className="space-y-4">
        <Panel className="overflow-hidden p-0">
          <div className="border-b border-line px-5 py-5">
            <PanelHeader
              description="Temporal shape for this evidence class only. Use the table below as the primary investigation surface."
              title="Timeline"
            />
          </div>
          <div className="px-5 py-5">
            <EvidenceTimelineChart className="h-[220px] w-full" compact events={events} onSelect={onSelectEvent} />
          </div>
        </Panel>

        <Panel className="overflow-hidden p-0">
          <div className="border-b border-line px-5 py-5">
            <PanelHeader
              description="Only the selected evidence class is shown here, so paths, hosts, and summaries are easier to scan."
              title="Event Table"
            />
          </div>
          <div className="px-5 py-5">
            <EvidenceTable events={events} onSelect={onSelectEvent} selectedEventId={selectedEventId} />
          </div>
        </Panel>
        </section>
      ) : (
        <Inspector activeTab={inspectorTab} inspector={inspector} onTabChange={onInspectorTabChange} ruleDraft={ruleDraft} />
      )}
    </div>
  );
}
