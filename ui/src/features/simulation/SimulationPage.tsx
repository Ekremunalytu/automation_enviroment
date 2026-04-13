import { useDeferredValue, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { EvidenceTable } from "../../components/evidence/EvidenceTable";
import { EvidenceTimelineChart } from "../../components/evidence/EvidenceTimelineChart";
import { FilterRail, type EvidenceFilterState } from "../../components/evidence/FilterRail";
import { Inspector } from "../../components/evidence/Inspector";
import { RunActivityRail } from "../../components/simulation/RunActivityRail";
import { EmptyState } from "../../components/ui/EmptyState";
import { Panel, PanelHeader } from "../../components/ui/Panel";
import { SegmentedTabs } from "../../components/ui/SegmentedTabs";
import { SlideOverDrawer } from "../../components/ui/SlideOverDrawer";
import { apiClient } from "../../lib/api/client";
import { adaptJob } from "../../lib/adapters/job";
import { adaptReport, getInspectorView } from "../../lib/adapters/report";
import { buildRuleDraft } from "../../lib/rules/draft";

const LAST_JOB_KEY = "extrace:lastJobId";

function getStoredJobId() {
  if (typeof window === "undefined") return null;
  const storage = window.localStorage;
  return typeof storage?.getItem === "function" ? storage.getItem(LAST_JOB_KEY) : null;
}

function rememberJobId(jobId: string) {
  if (typeof window === "undefined") return;
  const storage = window.localStorage;
  if (typeof storage?.setItem === "function") {
    storage.setItem(LAST_JOB_KEY, jobId);
  }
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
  const params = new URLSearchParams(searchParams);
  const assign = (key: string, value?: string) => {
    if (value) params.set(key, value);
    else params.delete(key);
  };
  assign("kind", filters.kinds[0]);
  assign("actor", filters.actors[0]);
  assign("collector", filters.collectors[0]);
  assign("scenario", filters.scenarios[0]);
  assign("search", filters.search || undefined);
  if (filters.sensitiveOnly) params.set("sensitive", "true");
  else params.delete("sensitive");
  return params;
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

function getExpectedTelemetry(status?: string, hasEvidence?: boolean) {
  if (hasEvidence) return "Evidence is streaming into the event table and inspector.";
  if (status === "queued") return "Sandbox reset and installation logs should appear next.";
  if (status === "running") return "Activation events should land once the extension host finishes warming up.";
  return "Report output will populate when the executor finalizes the run.";
}

export function SimulationPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const jobId = searchParams.get("job");
  const tab = searchParams.get("tab") || "live";
  const eventId = searchParams.get("event");
  const inspectorTab = (searchParams.get("inspector") as "provenance" | "relations" | "rule" | null) || "provenance";
  const filters = parseFilters(searchParams);
  const deferredSearch = useDeferredValue(filters.search);

  useEffect(() => {
    if (!jobId) {
      const remembered = getStoredJobId();
      if (remembered) {
        const next = new URLSearchParams(searchParams);
        next.set("job", remembered);
        setSearchParams(next, { replace: true });
      }
      return;
    }
    rememberJobId(jobId);
  }, [jobId, searchParams, setSearchParams]);

  const jobQuery = useQuery({
    enabled: Boolean(jobId),
    queryKey: ["job", jobId],
    queryFn: () => apiClient.getAnalysisJob(jobId!),
    refetchInterval: (query) => {
      const data = query.state.data;
      return data && ["queued", "running"].includes(data.status) ? 2000 : false;
    },
  });

  const reportQuery = useQuery({
    enabled: Boolean(jobQuery.data?.report_path),
    queryKey: ["live-report", jobQuery.data?.report_path],
    queryFn: async () => {
      const reportName = jobQuery.data?.report_path!;
      const dto = await apiClient.getReportByName(reportName);
      return adaptReport(dto, reportName);
    },
    refetchInterval: () => {
      const status = jobQuery.data?.status;
      return status && ["queued", "running"].includes(status) ? 2000 : false;
    },
  });

  const job = jobQuery.data;
  const report = reportQuery.data;
  const model = job ? adaptJob(job) : null;

  const filteredEvents =
    report?.evidence.filter((event) => {
      if (filters.kinds.length && !filters.kinds.includes(event.kindLabel)) return false;
      if (filters.actors.length && !filters.actors.includes(event.actorLabel)) return false;
      if (filters.collectors.length && !filters.collectors.includes(event.collectorLabel)) return false;
      if (filters.scenarios.length && !filters.scenarios.includes(event.scenarioName)) return false;
      if (filters.sensitiveOnly && !event.sensitive) return false;
      if (deferredSearch) {
        const haystack = [event.artifact, event.summaryDisplay, event.extensionId, event.host, event.path].join(" ").toLowerCase();
        if (!haystack.includes(deferredSearch.toLowerCase())) return false;
      }
      return true;
    }) || [];

  useEffect(() => {
    if (!report?.evidence.length) return;
    const candidate = filteredEvents[0]?.eventId || report.evidence[0]?.eventId;
    if (!candidate) return;

    if (!eventId) {
      const next = new URLSearchParams(searchParams);
      next.set("event", candidate);
      setSearchParams(next, { replace: true });
      return;
    }

    if (filteredEvents.length && !filteredEvents.some((event) => event.eventId === eventId)) {
      const next = new URLSearchParams(searchParams);
      next.set("event", filteredEvents[0].eventId);
      setSearchParams(next, { replace: true });
    }
  }, [eventId, filteredEvents, report?.evidence, searchParams, setSearchParams]);

  const inspector = report ? getInspectorView(report, eventId) : null;
  const ruleDraft = buildRuleDraft(inspector);
  const options = {
    kinds: [...new Set(report?.evidence.map((event) => event.kindLabel) || [])],
    actors: [...new Set(report?.evidence.map((event) => event.actorLabel) || [])],
    collectors: [...new Set(report?.evidence.map((event) => event.collectorLabel) || [])],
    scenarios: [...new Set(report?.evidence.map((event) => event.scenarioName).filter(Boolean) || [])],
  };
  const activeFilterCount = countActiveFilters(filters);

  const setSelectedEvent = (nextEventId: string) => {
    const next = new URLSearchParams(searchParams);
    next.set("event", nextEventId);
    setSearchParams(next, { replace: true });
  };

  const updateFilters = (nextFilters: EvidenceFilterState) => {
    setSearchParams(applyFilters(searchParams, nextFilters), { replace: true });
  };

  if (!jobId && !getStoredJobId()) {
    return <EmptyState body="Start an analysis from Marketplace to open the live simulation surface." eyebrow="Simulation" title="No active job selected" />;
  }

  return (
    <div className="space-y-6">
      <section className="page-header">
        <div className="space-y-3">
          <div className="eyebrow">Simulation</div>
          <h1 className="page-title">{model?.title || "Live run"}</h1>
          <p className="max-w-3xl text-sm leading-7 text-mute sm:text-base">
            {job?.message || "Track sandbox progress, then inspect live evidence and attribution without leaving the simulation surface."}
          </p>
          <div className="flex flex-wrap gap-2">
            <span className="info-chip">Job {jobId || "pending"}</span>
            <span className="info-chip">{filteredEvents.length} visible events</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button className="ghost-button" onClick={() => setFiltersOpen(true)} type="button">
            Filters {activeFilterCount ? `(${activeFilterCount})` : ""}
          </button>
          <SegmentedTabs
            onChange={(next) => {
              const params = new URLSearchParams(searchParams);
              params.set("tab", next);
              setSearchParams(params, { replace: true });
            }}
            options={[
              { value: "live", label: "Live Evidence" },
              { value: "status", label: "Run Status" },
            ]}
            value={tab === "status" ? "status" : "live"}
          />
        </div>
      </section>

      <section className="toolbar-surface">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <TelemetryField label="Status" value={job?.status || "pending"} />
          <TelemetryField label="Current phase" value={model?.currentStepLabel || "Awaiting job"} />
          <TelemetryField label="Last update" value={model?.lastUpdatedLabel || "--"} />
          <TelemetryField label="Progress" value={model ? `${model.progressPct}%` : "--"} />
        </div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-canvas">
          <div className="h-full rounded-full bg-accent" style={{ width: `${model?.progressPct || 0}%` }} />
        </div>
        <div className="mt-3 text-sm text-mute">
          {filteredEvents.length} visible events {report ? `from ${report.summary.totalEvents} total` : "while the run warms up"}
        </div>
      </section>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_390px]">
        <div className="space-y-5">
          <Panel className="overflow-hidden p-0">
            <div className="border-b border-line px-5 py-5">
              <PanelHeader
                description="Step-by-step executor progress with enough detail to understand where the sandbox run is spending time."
                title="Run Activity"
              />
            </div>
            <div className="px-5 py-5">{job && model ? <RunActivityRail job={job} model={model} /> : <EmptyState body="Job metadata is still loading." eyebrow="Warmup" title="Fetching job snapshot" />}</div>
          </Panel>

          {tab === "status" ? (
            <Panel className="overflow-hidden p-0">
              <div className="border-b border-line px-5 py-5">
                <PanelHeader
                  description="Short operational guidance while the run is queued, warming up, or already streaming evidence."
                  title="Run Status"
                />
              </div>
              <div className="grid gap-4 px-5 py-5 lg:grid-cols-3">
                <StatusCard body={model?.currentStepLabel || "Queued"} title="Current step" />
                <StatusCard body={getExpectedTelemetry(job?.status, Boolean(report?.evidence.length))} title="Next expected telemetry" />
                <StatusCard
                  body={(model?.recentMessages || ["Waiting for job metadata."]).join("\n")}
                  preformatted
                  title="Recent messages"
                />
              </div>
            </Panel>
          ) : report && filteredEvents.length ? (
            <Panel className="overflow-hidden p-0">
              <div className="border-b border-line px-5 py-5">
                <PanelHeader
                  description="Live Event Stream"
                  title="Evidence"
                />
              </div>
              <div className="space-y-5 px-5 py-5">
                <div className="rounded-[22px] border border-line bg-canvas/55 px-4 py-4">
                  <div className="micro-label">Mini Timeline</div>
                  <div className="mt-3">
                    <EvidenceTimelineChart className="h-[210px] w-full" compact events={filteredEvents} onSelect={setSelectedEvent} />
                  </div>
                </div>
                <div>
                  <div className="micro-label">Live Event Stream</div>
                  <div className="mt-3">
                    <EvidenceTable events={filteredEvents} onSelect={setSelectedEvent} selectedEventId={eventId || undefined} />
                  </div>
                </div>
              </div>
            </Panel>
          ) : (
            <Panel className="overflow-hidden p-0">
              <div className="border-b border-line px-5 py-5">
                <PanelHeader
                  description="Compact guidance cards keep the workspace readable until the first event lands."
                  title="Run Is Warming Up"
                />
              </div>
              <div className="grid gap-4 px-5 py-5 lg:grid-cols-3">
                <StatusCard body={model?.currentStepLabel || "Queued"} title="Current step" />
                <StatusCard body={getExpectedTelemetry(job?.status, false)} title="Next expected telemetry" />
                <StatusCard
                  body={(model?.recentMessages || ["Waiting for the sandbox run to emit telemetry."]).join("\n")}
                  preformatted
                  title="Recent messages"
                />
              </div>
            </Panel>
          )}
        </div>

        <Inspector
          activeTab={inspectorTab}
          inspector={inspector}
          onTabChange={(next) => {
            const params = new URLSearchParams(searchParams);
            params.set("inspector", next);
            setSearchParams(params, { replace: true });
          }}
          ruleDraft={ruleDraft}
        />
      </div>

      <SlideOverDrawer
        description="Apply the same URL-backed evidence filters used in reports without sacrificing workspace width."
        onClose={() => setFiltersOpen(false)}
        open={filtersOpen}
        title="Simulation filters"
      >
        <FilterRail
          description="Use filters to tighten the live stream before inspecting provenance."
          filters={filters}
          onChange={updateFilters}
          options={options}
          showSearch
          title="Refine stream"
        />
      </SlideOverDrawer>
    </div>
  );
}

function TelemetryField({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-tile">
      <div className="micro-label">{label}</div>
      <div className="mt-3 text-sm font-medium text-ink">{value}</div>
    </div>
  );
}

function StatusCard({
  title,
  body,
  preformatted = false,
}: {
  title: string;
  body: string;
  preformatted?: boolean;
}) {
  return (
    <div className="metric-tile">
      <div className="micro-label">{title}</div>
      {preformatted ? (
        <pre className="mt-3 whitespace-pre-wrap break-words font-body text-sm leading-6 text-mute">{body}</pre>
      ) : (
        <p className="mt-3 text-sm leading-6 text-mute">{body}</p>
      )}
    </div>
  );
}
