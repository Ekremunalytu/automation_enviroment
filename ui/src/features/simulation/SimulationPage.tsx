import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";

import { FilterRail, type EvidenceFilterState } from "../../components/evidence/FilterRail";
import { SlideOverDrawer } from "../../components/ui/SlideOverDrawer";
import {
  EmptyState,
  Eyebrow,
  GhostButton,
  MetricCell,
  Panel,
  PageTitle,
  ProgressBar,
  V3,
} from "../../components/v3";
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
import { LiveEvidenceWorkspace } from "./sections";
import { ActivityBars } from "./charts/ActivityBars";

function renderRunTitle(title: string) {
  const parts = title.split(".").filter(Boolean);
  if (parts.length <= 1) return title;
  return parts.map((part, index) => (
    <span key={`${part}-${index}`} style={{ display: "inline-block" }}>
      {index === 0 ? part : `.${part}`}
    </span>
  ));
}

export function SimulationPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const queryClient = useQueryClient();
  const jobId = searchParams.get("job");
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

  useEffect(() => {
    if (searchParams.get("tab") === "status") {
      const next = new URLSearchParams(searchParams);
      next.set("tab", "live");
      setSearchParams(next, { replace: true });
    }
  }, [searchParams, setSearchParams]);

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

  const cancelMutation = useMutation({
    mutationFn: () => {
      if (!jobId) throw new Error("Cannot cancel without an active job id.");
      return apiClient.cancelAnalysisJob(jobId);
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["job", jobId], data);
      queryClient.invalidateQueries({ queryKey: ["job", jobId] });
    },
  });

  const isJobActive = job?.status === "queued" || job?.status === "running";

  const handleStopRun = () => {
    if (!jobId || cancelMutation.isPending) return;
    const ok = window.confirm(
      "Stop the simulation? The sandbox will be reset and a partial report will be saved.",
    );
    if (ok) cancelMutation.mutate();
  };

  const filteredEvents = useMemo(
    () => (report ? filterEvidenceEvents(report.evidence, filters, deferredSearch) : []),
    [report, filters, deferredSearch],
  );

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
  const [runTitle, runVersion] = (model?.title || "").split("@", 2);

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
    return (
      <EmptyState
        eyebrow="Simulation"
        title="No active job selected"
        body="Start an analysis from Marketplace to open the live simulation surface."
      />
    );
  }

  const selectedEventRelTime = (() => {
    if (!report) return null;
    const event = report.evidence.find((entry) => entry.eventId === eventId);
    return event?.relTimeS ?? null;
  })();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      <header style={{ paddingBottom: 24, borderBottom: `1px solid ${V3.rule}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <Eyebrow>Simulation</Eyebrow>
        </div>
        <PageTitle style={{ marginTop: 14, fontSize: 26, lineHeight: 1.08, overflowWrap: "anywhere" }}>
          {runTitle ? renderRunTitle(runTitle) : "Live run"}
        </PageTitle>
        <p style={{ fontSize: 14, color: V3.ink3, marginTop: 14, maxWidth: 640, lineHeight: 1.6 }}>
          {job?.message ||
            "Track sandbox progress, then inspect live evidence and attribution without leaving the simulation surface."}
        </p>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            flexWrap: "wrap",
            marginTop: 18,
          }}
        >
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: V3.ink3,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
            }}
          >
            Job · {jobId || "pending"}
          </span>
          {runVersion ? (
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 11,
                color: V3.ink3,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
              }}
            >
              Version · {runVersion}
            </span>
          ) : null}
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: V3.ink3,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
            }}
          >
            Status · {job?.status || "pending"}
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
            Visible · {filteredEvents.length} events
          </span>
          <div style={{ flex: 1 }} />
          {isJobActive ? (
            <GhostButton
              ariaLabel="Stop simulation"
              disabled={cancelMutation.isPending}
              onClick={handleStopRun}
              style={{ borderColor: V3.coral, color: V3.coral }}
            >
              {cancelMutation.isPending ? "Stopping…" : "Stop simulation"}
            </GhostButton>
          ) : null}
          <GhostButton ariaLabel="Filters" onClick={() => setFiltersOpen(true)}>
            Filters {activeFilterCount ? `(${activeFilterCount})` : ""}
          </GhostButton>
        </div>

        {cancelMutation.isError ? (
          <div
            role="alert"
            style={{
              marginTop: 14,
              border: `1px solid ${V3.coral}`,
              background: V3.dangerBg,
              color: V3.coral,
              padding: "10px 14px",
              fontSize: 12,
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            {cancelMutation.error instanceof Error
              ? cancelMutation.error.message
              : "Failed to cancel run."}
          </div>
        ) : null}
      </header>

      <Panel padded={false} bodyStyle={{ display: "flex", flexDirection: "column", gap: 0 }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 180px), 1fr))",
            borderBottom: `1px solid ${V3.rule}`,
          }}
        >
          {[
            { label: "Status", value: job?.status || "pending" },
            { label: "Current phase", value: model?.currentStepLabel || "Awaiting job" },
            { label: "Last update", value: model?.lastUpdatedLabel || "—" },
            { label: "Progress", value: model ? `${model.progressPct}%` : "—" },
          ].map((cell, index) => (
            <div
              key={cell.label}
              style={{
                padding: "20px 22px",
                borderRight: index < 3 ? `1px solid ${V3.rule}` : "none",
                borderBottom: index < 3 ? `1px solid ${V3.rule}` : "none",
              }}
            >
              <MetricCell
                label={cell.label}
                value={
                  <span style={{ fontSize: 22, letterSpacing: 0 }}>{cell.value}</span>
                }
              />
            </div>
          ))}
        </div>
        <div style={{ padding: "16px 22px" }}>
          <ProgressBar pct={model?.progressPct ?? 0} />
          <div
            style={{
              marginTop: 10,
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: V3.ink3,
              letterSpacing: "0.04em",
            }}
          >
            {filteredEvents.length} visible events
            {report ? ` from ${report.summary.totalEvents} total` : " while the run warms up"}
          </div>
        </div>
        {report?.evidence.length ? (
          <div
            style={{
              padding: "14px 22px 18px",
              borderTop: `1px solid ${V3.rule}`,
              background: V3.paper3,
            }}
          >
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 8 }}>
              <Eyebrow>Activity histogram</Eyebrow>
              <span
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 10,
                  letterSpacing: "0.12em",
                  textTransform: "uppercase",
                  color: V3.ink4,
                }}
              >
                20 bins · relative time
              </span>
            </div>
            <ActivityBars
              events={report.evidence.map((event) => ({ relTimeS: event.relTimeS }))}
              selectedRelTimeS={selectedEventRelTime}
            />
          </div>
        ) : null}
      </Panel>

      {model?.reportError ? (
        <section
          role="alert"
          style={{
            border: `1px solid ${V3.coral}`,
            background: V3.dangerBg,
            color: V3.coral,
            padding: "16px 18px",
            fontSize: 13,
            lineHeight: 1.5,
          }}
        >
          <div style={{ fontWeight: 700 }}>Activation report failed validation</div>
          <p style={{ marginTop: 6, color: V3.ink3 }}>
            The sandbox finished but the generated report did not match the contract, so detection
            results are unavailable. Re-running the analysis usually resolves transient executor
            issues.
          </p>
          <pre
            style={{
              marginTop: 12,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              lineHeight: 1.5,
              color: V3.ink3,
            }}
          >
            {model.reportError}
          </pre>
        </section>
      ) : null}

      <LiveEvidenceWorkspace
        eventId={eventId || undefined}
        filteredEvents={filteredEvents}
        detection={report?.detection || null}
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
        ruleDraft={ruleDraft}
        status={job?.status}
      />

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
