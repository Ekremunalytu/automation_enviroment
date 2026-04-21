import { startTransition, useDeferredValue, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { FilterRail, type EvidenceFilterState } from "../../components/evidence/FilterRail";
import { EmptyState } from "../../components/ui/EmptyState";
import { SegmentedTabs } from "../../components/ui/SegmentedTabs";
import { SlideOverDrawer } from "../../components/ui/SlideOverDrawer";
import {
  applyEvidenceFilters,
  buildEvidenceFilterOptions,
  countEvidenceFilters,
  filterEvidenceEvents,
  normalizeInspectorTab,
  parseEvidenceFilters,
} from "../evidence";
import { getStoredJobId, rememberJobId } from "./jobStorage";
import { apiClient } from "../../lib/api/client";
import { adaptJob } from "../../lib/adapters/job";
import { adaptReport, getInspectorView } from "../../lib/adapters/report";
import { buildRuleDraft } from "../../lib/rules/draft";
import {
  LiveRiskStrip,
  RunActivityPanel,
  SimulationStatusPanel,
  SimulationWorkspace,
  TelemetryField,
  type WorkspaceTab,
} from "./sections";

function normalizeWorkspaceTab(raw: string | null): WorkspaceTab {
  if (raw === "analysis" || raw === "logs") return raw;
  return "evidence";
}

export function SimulationPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const jobId = searchParams.get("job");
  const tab = searchParams.get("tab") || "live";
  const workspaceTab = normalizeWorkspaceTab(searchParams.get("workspace"));
  const eventId = searchParams.get("event");
  const inspectorTab = normalizeInspectorTab(searchParams.get("inspector"));
  const filters = parseEvidenceFilters(searchParams);
  const deferredSearch = useDeferredValue(filters.search);

  useEffect(() => {
    if (!jobId) {
      const remembered = getStoredJobId();
      if (remembered) {
        startTransition(() => {
          const next = new URLSearchParams(searchParams);
          next.set("job", remembered);
          setSearchParams(next, { replace: true });
        });
      }
      return;
    }
    rememberJobId(jobId);
  }, [jobId, searchParams, setSearchParams]);

  const jobQuery = useQuery({
    enabled: Boolean(jobId),
    queryKey: ["job", jobId],
    queryFn: ({ signal }) => apiClient.getAnalysisJob(jobId!, signal),
    refetchInterval: (query) => {
      const data = query.state.data;
      return data && ["queued", "running"].includes(data.status) ? 2000 : false;
    },
  });

  const reportQuery = useQuery({
    enabled: Boolean(jobQuery.data?.report_path),
    queryKey: ["live-report", jobQuery.data?.report_path],
    queryFn: async ({ signal }) => {
      const reportName = jobQuery.data?.report_path;
      if (!reportName) {
        throw new Error("report_path is unavailable");
      }
      const dto = await apiClient.getReportByName(reportName, signal);
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

  const filteredEvents = report
    ? filterEvidenceEvents(report.evidence, filters, deferredSearch)
    : [];

  useEffect(() => {
    if (!report?.evidence.length) return;
    const candidate = filteredEvents[0]?.eventId || report.evidence[0]?.eventId;
    if (!candidate) return;

    if (!eventId) {
      startTransition(() => {
        const next = new URLSearchParams(searchParams);
        next.set("event", candidate);
        setSearchParams(next, { replace: true });
      });
      return;
    }

    if (filteredEvents.length && !filteredEvents.some((event) => event.eventId === eventId)) {
      startTransition(() => {
        const next = new URLSearchParams(searchParams);
        next.set("event", filteredEvents[0].eventId);
        setSearchParams(next, { replace: true });
      });
    }
  }, [eventId, filteredEvents, report?.evidence, searchParams, setSearchParams]);

  const inspector = report ? getInspectorView(report, eventId) : null;
  const ruleDraft = buildRuleDraft(inspector);
  const options = buildEvidenceFilterOptions(report?.evidence || []);
  const activeFilterCount = countEvidenceFilters(filters);

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
              startTransition(() => {
                const params = new URLSearchParams(searchParams);
                params.set("tab", next);
                setSearchParams(params, { replace: true });
              });
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

      {model?.reportError ? (
        <section
          className="rounded-[18px] border border-danger/40 bg-danger/10 px-5 py-4 text-sm text-danger"
          role="alert"
        >
          <div className="font-semibold">Activation report failed validation</div>
          <p className="mt-1 text-mute">
            The sandbox finished but the generated report did not match the
            contract, so detection results are unavailable. The run can be
            retried; re-running the analysis usually resolves transient
            executor issues.
          </p>
          <pre className="mt-3 whitespace-pre-wrap break-words font-body text-xs leading-5 text-mute">
            {model.reportError}
          </pre>
        </section>
      ) : null}

      <div className="space-y-5">
        <RunActivityPanel job={job || null} model={model} />
        <LiveRiskStrip onSelectEvent={setSelectedEvent} report={report || null} />

        {tab === "status" ? (
          <SimulationStatusPanel hasEvidence={Boolean(report?.evidence.length)} model={model} status={job?.status} />
        ) : (
          <SimulationWorkspace
            eventId={eventId || undefined}
            filteredEvents={filteredEvents}
            inspector={inspector}
            inspectorTab={inspectorTab}
            model={model}
            onInspectorTabChange={(next) => {
              startTransition(() => {
                const params = new URLSearchParams(searchParams);
                params.set("inspector", next);
                setSearchParams(params, { replace: true });
              });
            }}
            onSelectEvent={setSelectedEvent}
            onWorkspaceTabChange={(next) => {
              startTransition(() => {
                const params = new URLSearchParams(searchParams);
                params.set("workspace", next);
                setSearchParams(params, { replace: true });
              });
            }}
            report={report || null}
            ruleDraft={ruleDraft}
            status={job?.status}
            workspaceTab={workspaceTab}
          />
        )}
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
