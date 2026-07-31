import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";

import { FilterRail, type EvidenceFilterState } from "../../components/evidence/FilterRail";
import { EvidenceLedger } from "../../components/evidence/EvidenceLedger";
import { resolveTimeZone } from "../../lib/settings/presentation";
import { Inspector } from "../../components/evidence/Inspector";
import { LogStreamsPanel } from "../../components/evidence/LogStreamsPanel";
import { RiskRadarPanel } from "../../components/evidence/RiskRadarPanel";
import { SlideOverDrawer } from "../../components/ui/SlideOverDrawer";
import {
  Badge,
  Dialog,
  EmptyState,
  Eyebrow,
  Field,
  FONT_MONO,
  GhostButton,
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
  normalizeInspectorTab,
  parseEvidenceFilters,
} from "../evidence";
import { apiClient } from "../../lib/api/client";
import type { StaticReportView } from "../../lib/types/view-models";
import {
  adaptBundle,
  adaptReport,
  buildInteractionGraph,
  buildRiskRadarAxes,
  getInspectorView,
} from "../../lib/adapters/report";
import { adaptStaticReport } from "../../lib/adapters/job";
import { FindingCard } from "./FindingCard";
import { verdictTone, verdictAction, VERDICT_LEGEND } from "./verdictColors";
import { RuleMatrixSection } from "./RuleMatrixSection";
import { EventTimeline } from "./charts/EventTimeline";
import { EventDensityStrip } from "./charts/EventDensityStrip";
import { InteractionGraph } from "./charts/InteractionGraph";
import { DISPLAY_CAPS } from "../../lib/displayCaps";

type ReportModel = NonNullable<ReturnType<typeof adaptReport>>;
type ReportTab = "overview" | "matrix" | "interactions" | "timeline" | "ledger" | "audit";

const REPORT_TABS: TabSpec<ReportTab>[] = [
  { value: "overview", label: "Overview" },
  { value: "matrix", label: "Rule matrix" },
  { value: "interactions", label: "Interactions" },
  { value: "timeline", label: "Timeline" },
  { value: "ledger", label: "Event ledger" },
  { value: "audit", label: "Audit" },
];
const DYNAMIC_ONLY_REPORT_TABS = new Set<ReportTab>([
  "interactions",
  "timeline",
  "ledger",
  "audit",
]);

function normalizeTab(raw: string | null): ReportTab {
  if (raw === "matrix" || raw === "interactions" || raw === "timeline" || raw === "ledger" || raw === "audit") return raw;
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
    timeZone: resolveTimeZone(),
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

function staticDecisionTone(decision?: StaticReportView["decision"]): V3Tone {
  if (decision === "block") return "danger";
  if (decision === "warn" || decision === "inconclusive") return "warn";
  if (decision === "allow") return "ok";
  return "neutral";
}

function staticDecisionAction(decision: StaticReportView["decision"]): string {
  if (decision === "block") {
    return "Blocked before sandbox execution. Review the blocking static findings before enabling or running dynamic analysis.";
  }
  if (decision === "inconclusive") {
    return "Static coverage is incomplete. Resolve the coverage reasons and re-run before treating the extension as clean.";
  }
  if (decision === "warn") {
    return "Review the warned static findings before deciding whether this extension should enter the sandbox.";
  }
  return "No blocking static finding was produced. This is a static-only result, not behavioral clearance.";
}

export function ReportsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const navigate = useNavigate();
  const reportParam = searchParams.get("report") || "latest";
  const selectedTab = normalizeTab(searchParams.get("tab"));
  const eventId = searchParams.get("event");
  const inspectorParam = searchParams.get("inspector");
  // Default the inspector to the Relations tab (interaction graph) on first open;
  // an explicit ?inspector= value still wins so manual tab switches persist in the URL.
  const inspectorTab = inspectorParam ? normalizeInspectorTab(inspectorParam) : "relations";
  const filters = parseEvidenceFilters(searchParams);
  const deferredSearch = useDeferredValue(filters.search);
  const [inspectorOpen, setInspectorOpen] = useState(
    () =>
      Boolean(eventId) &&
      (selectedTab === "ledger" || selectedTab === "timeline" || selectedTab === "interactions"),
  );

  const reportsQuery = useQuery({
    queryKey: ["reports"],
    queryFn: ({ signal }) => apiClient.listReports(signal),
    refetchInterval: 4000,
  });

  const executorPreferencesQuery = useQuery({
    queryKey: ["settings", "executor-preferences"],
    queryFn: ({ signal }) => apiClient.getExecutorPreferences(signal),
    refetchInterval: 4000,
  });
  const preferencesResolved =
    executorPreferencesQuery.isSuccess || executorPreferencesQuery.isError;
  const dynamicAnalysisEnabled =
    executorPreferencesQuery.data?.dynamic_analysis_enabled ?? true;
  const staticOnlyLatest =
    reportParam === "latest" &&
    executorPreferencesQuery.isSuccess &&
    !dynamicAnalysisEnabled;
  const activeTab =
    staticOnlyLatest && DYNAMIC_ONLY_REPORT_TABS.has(selectedTab)
      ? "overview"
      : selectedTab;
  const reportTabs = useMemo(
    () =>
      REPORT_TABS.map((tab) =>
        staticOnlyLatest && DYNAMIC_ONLY_REPORT_TABS.has(tab.value)
          ? {
              ...tab,
              disabled: true,
              disabledReason:
                "Dynamic analysis is disabled; this section requires sandbox evidence.",
            }
          : tab,
      ),
    [staticOnlyLatest],
  );

  const reportQuery = useQuery({
    queryKey: ["report", reportParam],
    queryFn: async ({ signal }) => {
      const dto =
        reportParam === "latest"
          ? await apiClient.getLatestReportBundle(signal)
          : await apiClient.getReportBundleByName(reportParam, signal);
      return adaptBundle(dto, reportParam);
    },
    enabled: preferencesResolved && !staticOnlyLatest,
  });

  const latestStaticQuery = useQuery({
    queryKey: ["reports", "static", "latest"],
    queryFn: ({ signal }) => apiClient.getLatestStaticReport(signal),
    enabled: staticOnlyLatest,
    refetchInterval: 4000,
  });
  const latestStaticReport = useMemo(
    () =>
      latestStaticQuery.data
        ? adaptStaticReport(latestStaticQuery.data.static_report)
        : undefined,
    [latestStaticQuery.data],
  );

  const report = reportQuery.data;
  const filteredEvents = useMemo(
    () => (report ? filterEvidenceEvents(report.evidence, filters, deferredSearch) : []),
    [report, filters, deferredSearch],
  );
  const inspector = useMemo(
    () => (report ? getInspectorView(report, eventId) : null),
    [report, eventId],
  );

  useEffect(() => {
    if (!staticOnlyLatest || activeTab === selectedTab) return;
    const next = new URLSearchParams(searchParams);
    next.set("tab", activeTab);
    next.delete("event");
    setSearchParams(next, { replace: true });
  }, [
    activeTab,
    searchParams,
    selectedTab,
    setSearchParams,
    staticOnlyLatest,
  ]);

  useEffect(() => {
    if (activeTab !== "interactions" && activeTab !== "ledger") return;
    if (!filteredEvents.length) return;

    const candidate = filteredEvents[0]?.eventId;
    if (!candidate) return;

    if (!eventId || !filteredEvents.some((event) => event.eventId === eventId)) {
      const next = new URLSearchParams(searchParams);
      next.set("event", candidate);
      setSearchParams(next, { replace: true });
    }
  }, [activeTab, eventId, filteredEvents, searchParams, setSearchParams]);

  const options = buildEvidenceFilterOptions(report?.evidence || []);
  const activeFilterCount = countEvidenceFilters(filters);
  const activeReport =
    reportParam === "latest"
      ? reportsQuery.data?.[0]
      : reportsQuery.data?.find((item) => item.filename === reportParam) || reportsQuery.data?.[0];
  const activeArtifactFilename = staticOnlyLatest
    ? latestStaticQuery.data?.filename
    : activeReport?.filename;
  const activeArtifactModified = staticOnlyLatest
    ? latestStaticQuery.data?.modified
    : activeReport?.modified;

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
    setInspectorOpen(true);
  };

  const updateFilters = (nextFilters: EvidenceFilterState) => {
    startTransition(() => {
      setSearchParams(applyEvidenceFilters(searchParams, nextFilters), { replace: true });
    });
  };

  const verdict = report?.detection?.verdict;
  // S4 / B4: tone the verdict through the canonical 5-state map, never a
  // severity fallback. inconclusive/clean_with_notes must not read as the
  // clean (green) tone.
  const headerTone = verdictTone(verdict);
  const inspectorTone: "accent" | "warn" | "danger" = inspector
    ? inspector.event.sensitive
      ? "danger"
      : inspector.event.kind === "network"
        ? "warn"
        : "accent"
    : "accent";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      <header style={{ paddingBottom: 24, borderBottom: `1px solid ${V3.rule}` }}>
        <PageTitle style={{ fontSize: 44, lineHeight: 1, wordBreak: "break-word" }}>Security report</PageTitle>
      </header>

      <section aria-label="Report workspace">
        <Panel padded={false}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 18,
              padding: "12px 16px",
              borderBottom: `1px solid ${V3.rule}`,
              background: V3.paper3,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
              <span aria-hidden style={{ width: 18, height: 2, background: V3.coral }} />
              <Eyebrow>{staticOnlyLatest ? "Static scan" : "Run control"}</Eyebrow>
            </div>
            <span
              title={activeArtifactFilename || "Latest report"}
              style={{
                minWidth: 0,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                color: V3.ink3,
                fontFamily: FONT_MONO,
                fontSize: 10,
                letterSpacing: "0.04em",
              }}
            >
              {activeArtifactFilename || "Latest report"}
            </span>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 220px), 1fr))",
              gap: 12,
              alignItems: "end",
              padding: 16,
            }}
          >
            <label style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 0 }}>
              <Eyebrow>Report source</Eyebrow>
              <select
                value={reportParam}
                onChange={(event) => {
                  const next = new URLSearchParams(searchParams);
                  next.set("report", event.target.value);
                  setSearchParams(next, { replace: true });
                }}
                style={{
                  width: "100%",
                  minWidth: 0,
                  background: V3.paper,
                  color: V3.ink,
                  border: `1px solid ${V3.rule2}`,
                  borderRadius: 0,
                  padding: "11px 12px",
                  fontFamily: FONT_MONO,
                  fontSize: 12,
                }}
              >
                <option value="latest">
                  {staticOnlyLatest ? "Latest static artifact" : "Latest report"}
                </option>
                {(reportsQuery.data || []).map((item) => (
                  <option key={item.filename} value={item.filename}>
                    {item.filename}
                  </option>
                ))}
              </select>
            </label>

            <Field
              label="Search evidence"
              placeholder="host, path, extension, summary…"
              value={filters.search}
              onChange={(value) => updateFilters({ ...filters, search: value })}
              inputProps={{
                disabled: staticOnlyLatest,
                title: staticOnlyLatest
                  ? "Dynamic evidence search is unavailable while dynamic analysis is disabled."
                  : undefined,
              }}
              mono
              style={{ minWidth: 0 }}
            />

            <GhostButton
              ariaLabel="Filters"
              disabled={staticOnlyLatest}
              title={
                staticOnlyLatest
                  ? "Dynamic evidence filters are unavailable while dynamic analysis is disabled."
                  : undefined
              }
              onClick={() => setFiltersOpen(true)}
              style={{ justifySelf: "start" }}
            >
              Filters {activeFilterCount ? `(${activeFilterCount})` : ""}
            </GhostButton>
          </div>

          <div
            aria-label={staticOnlyLatest ? "Static report summary" : "Report summary"}
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 120px), 1fr))",
              borderTop: `1px solid ${V3.rule}`,
              background: V3.paper3,
            }}
          >
            {staticOnlyLatest ? (
              <>
                <ReportReadout
                  label="Findings"
                  value={formatNumber(latestStaticReport?.findings.length ?? 0)}
                  tone={
                    latestStaticReport?.findings.length
                      ? staticDecisionTone(latestStaticReport.decision)
                      : "neutral"
                  }
                />
                <ReportReadout
                  label="Blocked by"
                  value={formatNumber(latestStaticReport?.blockedBy.length ?? 0)}
                  tone="danger"
                />
                <ReportReadout
                  label="Warned by"
                  value={formatNumber(latestStaticReport?.warnedBy.length ?? 0)}
                  tone="warn"
                />
                <ReportReadout
                  label="Decision"
                  value={latestStaticReport?.decisionLabel ?? "—"}
                  tone={staticDecisionTone(latestStaticReport?.decision)}
                />
                <ReportReadout
                  label="Coverage"
                  value={
                    latestStaticReport
                      ? `${latestStaticReport.coverage.filesScanned}/${latestStaticReport.coverage.filesDiscovered}`
                      : "—"
                  }
                />
                <ReportReadout
                  label="Updated"
                  value={formatModified(activeArtifactModified)}
                  compact
                />
              </>
            ) : (
              <>
                <ReportReadout
                  label="Events"
                  value={formatNumber(report?.summary.totalEvents ?? 0)}
                />
                <ReportReadout
                  label="Sensitive"
                  value={formatNumber(report?.summary.sensitiveEvents ?? 0)}
                  tone="danger"
                />
                <ReportReadout
                  label="Network"
                  value={formatNumber(report?.summary.networkEvents ?? 0)}
                  tone="warn"
                />
                <ReportReadout
                  label="Score"
                  value={`${report?.summary.signalSummaryScore ?? 0}`}
                  tone={headerTone}
                />
                <ReportReadout label="Quality" value={report?.summary.runQuality ?? "—"} />
                <ReportReadout
                  label="Updated"
                  value={formatModified(activeArtifactModified)}
                  compact
                />
              </>
            )}
          </div>
        </Panel>
      </section>

      {staticOnlyLatest ? (
        <DynamicAnalysisDisabledPanel />
      ) : report ? (
        <RiskRadarPanel
          axes={buildRiskRadarAxes(report)}
          compositeScore={report.summary.signalSummaryScore ?? 0}
        />
      ) : null}

      <Tabs<ReportTab>
        ariaLabel="Report sections"
        tabs={reportTabs}
        value={activeTab}
        onChange={(nextTab) => {
          const params = new URLSearchParams(searchParams);
          params.set("tab", nextTab);
          setSearchParams(params, { replace: true });
        }}
      />

      {!preferencesResolved ? (
        <EmptyState
          eyebrow="Loading"
          body="Resolving the current analysis mode before selecting report data."
          title="Preparing report workspace"
        />
      ) : staticOnlyLatest ? (
        latestStaticQuery.isLoading ? (
          <EmptyState
            eyebrow="Static"
            body="Reading the newest completed static analysis artifact."
            title="Loading latest static pre-check"
          />
        ) : latestStaticQuery.isError ? (
          <EmptyState
            eyebrow="Static"
            body={String(latestStaticQuery.error)}
            title="Latest static pre-check unavailable"
          />
        ) : !latestStaticReport ? null : activeTab === "overview" ? (
          <StaticOnlyOverviewSection
            artifactFilename={latestStaticQuery.data?.filename ?? "Latest static artifact"}
            report={latestStaticReport}
          />
        ) : (
          <RuleMatrixSection
            report={null}
            dynamicAnalysisEnabled={false}
            staticReportOverride={latestStaticReport}
            latestStaticArtifact
          />
        )
      ) : reportQuery.isLoading ? (
        <EmptyState
          eyebrow="Loading"
          body="Fetching the selected report and normalizing evidence."
          title="Preparing report workspace"
        />
      ) : reportQuery.isError ? (
        <EmptyState
          eyebrow="Error"
          body={String(reportQuery.error)}
          title="Report could not be loaded"
        />
      ) : !report ? null : activeTab === "overview" ? (
        <OverviewSection report={report} />
      ) : activeTab === "matrix" ? (
        <RuleMatrixSection
          report={report}
          dynamicAnalysisEnabled={dynamicAnalysisEnabled}
        />
      ) : activeTab === "interactions" ? (
        <InteractionsSection graph={interactionGraph} report={report} onSelectEvent={setSelectedEvent} />
      ) : activeTab === "timeline" ? (
        <TimelineSection
          events={timelineEvents}
          timelineKey={timelineKey}
          selectedId={eventId || undefined}
          onSelect={setSelectedEvent}
          visibleCount={filteredEvents.length}
          report={report}
        />
      ) : activeTab === "ledger" ? (
        <LedgerSection
          events={filteredEvents}
          eventId={eventId || undefined}
          onSelectEvent={setSelectedEvent}
          kindFilter={
            filters.kinds[0] === "Network" ||
            filters.kinds[0] === "File" ||
            filters.kinds[0] === "Activation" ||
            filters.kinds[0] === "Scenario"
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
        open={filtersOpen && !staticOnlyLatest}
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

      <Dialog
        open={inspectorOpen && !staticOnlyLatest}
        onClose={() => setInspectorOpen(false)}
        eyebrow="Inspector"
        title={inspector?.event.summaryDisplay || "Event inspector"}
        tone={inspectorTone}
        width={1200}
        actions={
          inspector ? (
            <>
              <GhostButton
                ariaLabel="Draft rule from event"
                onClick={() =>
                  navigate(`/rules?tab=draft&from=${encodeURIComponent(inspector.event.eventId)}`)
                }
              >
                Draft rule from event
              </GhostButton>
              <GhostButton ariaLabel="Close inspector" onClick={() => setInspectorOpen(false)}>
                Close
              </GhostButton>
            </>
          ) : undefined
        }
      >
        <Inspector
          activeTab={inspectorTab}
          onTabChange={(next) => {
            const params = new URLSearchParams(searchParams);
            params.set("inspector", next);
            setSearchParams(params, { replace: true });
          }}
          inspector={inspector}
          detection={report?.detection || null}
        />
      </Dialog>
    </div>
  );
}

type ReportReadoutProps = {
  label: string;
  value: string;
  tone?: V3Tone;
  compact?: boolean;
};

function ReportReadout({
  label,
  value,
  tone = "neutral",
  compact = false,
}: ReportReadoutProps) {
  const toneColor =
    tone === "danger"
      ? V3.coral
      : tone === "warn"
        ? V3.warn
        : tone === "ok"
          ? V3.ok
          : tone === "accent"
            ? V3.coral
            : V3.ink;
  return (
    <div
      aria-label={`${label}: ${value}`}
      style={{
        minWidth: 0,
        padding: "12px 14px",
        borderRight: `1px solid ${V3.rule}`,
        borderBottom: `1px solid ${V3.rule}`,
      }}
    >
      <Eyebrow>{label}</Eyebrow>
      <div
        title={value}
        style={{
          marginTop: 7,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          color: toneColor,
          fontFamily: compact ? FONT_MONO : undefined,
          fontSize: compact ? 10.5 : 19,
          fontWeight: compact ? 500 : 650,
          lineHeight: 1.2,
          letterSpacing: compact ? "-0.01em" : 0,
        }}
      >
        {value}
      </div>
    </div>
  );
}

function DynamicAnalysisDisabledPanel() {
  return (
    <Panel
      label="Dynamic analysis"
      right={<Badge tone="neutral">Disabled</Badge>}
      style={{ opacity: 0.78 }}
    >
      <div
        aria-disabled="true"
        role="status"
        style={{
          display: "grid",
          gridTemplateColumns: "36px minmax(0, 1fr)",
          gap: 14,
          alignItems: "center",
        }}
      >
        <span
          aria-hidden
          style={{
            display: "grid",
            placeItems: "center",
            width: 34,
            height: 34,
            border: `1px solid ${V3.rule2}`,
            color: V3.ink3,
            fontFamily: FONT_MONO,
            fontSize: 18,
          }}
        >
          —
        </span>
        <div>
          <div
            style={{
              color: V3.ink,
              fontSize: 15,
              fontWeight: 650,
            }}
          >
            Dynamic analysis is disabled
          </div>
          <p
            style={{
              margin: "5px 0 0",
              color: V3.ink3,
              fontSize: 12.5,
              lineHeight: 1.55,
            }}
          >
            Sandbox evidence, risk radar, interactions, timeline, event ledger,
            and audit views are unavailable. The latest static artifact remains
            fully visible below.
          </p>
        </div>
      </div>
    </Panel>
  );
}

function StaticOnlyOverviewSection({
  artifactFilename,
  report,
}: {
  artifactFilename: string;
  report: StaticReportView;
}) {
  const visibleFindings = report.findings.slice(0, 6);
  const overflow = report.findings.length - visibleFindings.length;
  const coverageIncomplete =
    report.partial || report.coverage.reasons.length > 0;
  const gateRuleIds =
    report.decision === "block"
      ? report.blockedBy
      : report.decision === "warn"
        ? report.warnedBy
        : report.inconclusiveReasons;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <section
        aria-label="Static decision overview"
        style={{
          border: `1px solid ${V3.rule}`,
          background: V3.paper2,
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(min(100%, 260px), 1fr))",
          }}
        >
          <div
            style={{
              padding: "18px 20px",
              borderRight: `1px solid ${V3.rule}`,
              borderBottom: `1px solid ${V3.rule}`,
            }}
          >
            <Eyebrow>Current static decision</Eyebrow>
            <div
              style={{
                marginTop: 12,
                display: "flex",
                gap: 8,
                flexWrap: "wrap",
              }}
            >
              <Badge
                tone={staticDecisionTone(report.decision)}
                style={{ padding: "6px 10px", fontSize: 11 }}
              >
                Decision · {report.decision.toUpperCase()}
              </Badge>
              <Badge tone="neutral">Static only</Badge>
            </div>
          </div>
          <div
            style={{
              padding: "18px 20px",
              borderBottom: `1px solid ${V3.rule}`,
            }}
          >
            <Eyebrow>Operator action</Eyebrow>
            <p
              role="note"
              aria-label="Static recommended action"
              style={{
                margin: "10px 0 0",
                maxWidth: 680,
                fontSize: 13.5,
                lineHeight: 1.55,
                color: V3.ink2,
              }}
            >
              {staticDecisionAction(report.decision)}
            </p>
          </div>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            flexWrap: "wrap",
            padding: "13px 20px",
            background: V3.paper3,
          }}
        >
          <span
            title={artifactFilename}
            style={{
              minWidth: 0,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              color: V3.ink3,
              fontFamily: FONT_MONO,
              fontSize: 10,
            }}
          >
            {artifactFilename}
          </span>
          <Badge tone={coverageIncomplete ? "warn" : "ok"}>
            {coverageIncomplete ? "Coverage incomplete" : "Coverage complete"}
          </Badge>
        </div>
      </section>

      {gateRuleIds.length ? (
        <Panel
          label={
            report.decision === "block"
              ? "Blocking rules"
              : report.decision === "warn"
                ? "Warning rules"
                : "Coverage reasons"
          }
          right={<Badge tone={staticDecisionTone(report.decision)}>{gateRuleIds.length}</Badge>}
        >
          <div
            role="list"
            aria-label="Static gate reasons"
            style={{ display: "flex", gap: 8, flexWrap: "wrap" }}
          >
            {gateRuleIds.map((ruleId) => (
              <span
                key={ruleId}
                role="listitem"
                style={{
                  border: `1px solid ${V3.rule2}`,
                  padding: "6px 8px",
                  color: V3.ink2,
                  fontFamily: FONT_MONO,
                  fontSize: 10.5,
                }}
              >
                {ruleId}
              </span>
            ))}
          </div>
        </Panel>
      ) : null}

      <Panel
        label="Static findings"
        right={
          <Badge tone={report.findings.length ? "warn" : "ok"}>
            {report.findings.length} finding{report.findings.length === 1 ? "" : "s"}
          </Badge>
        }
      >
        {visibleFindings.length ? (
          <div
            role="list"
            aria-label="Static findings"
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(min(100%, 280px), 1fr))",
              gap: 12,
            }}
          >
            {visibleFindings.map((finding) => (
              <article
                key={finding.id}
                role="listitem"
                style={{
                  border: `1px solid ${V3.rule}`,
                  borderLeft: `3px solid ${
                    severityToTone(finding.severity) === "danger"
                      ? V3.coral
                      : severityToTone(finding.severity) === "warn"
                        ? V3.warn
                        : V3.rule2
                  }`,
                  padding: "14px 16px",
                  background: V3.paper3,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 10,
                  }}
                >
                  <span
                    style={{
                      color: V3.ink,
                      fontSize: 13.5,
                      fontWeight: 650,
                    }}
                  >
                    {finding.title}
                  </span>
                  <Badge tone={severityToTone(finding.severity)}>
                    {finding.severityLabel}
                  </Badge>
                </div>
                <p
                  style={{
                    margin: "9px 0 0",
                    color: V3.ink2,
                    fontSize: 12.5,
                    lineHeight: 1.55,
                  }}
                >
                  {finding.description}
                </p>
                <div
                  style={{
                    marginTop: 10,
                    color: V3.ink3,
                    fontFamily: FONT_MONO,
                    fontSize: 10,
                  }}
                >
                  {finding.ruleId} · {finding.evidenceCount} evidence
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p style={{ margin: 0, color: V3.ink3, fontSize: 13 }}>
            No static finding was emitted.
          </p>
        )}
        {overflow > 0 ? (
          <p
            style={{
              margin: "14px 0 0",
              color: V3.ink3,
              fontFamily: FONT_MONO,
              fontSize: 10.5,
            }}
          >
            +{overflow} more finding{overflow === 1 ? "" : "s"} in Rule matrix
          </p>
        ) : null}
      </Panel>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(min(100%, 280px), 1fr))",
          gap: 20,
        }}
      >
        <Panel label="Static coverage">
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
              gap: 12,
            }}
          >
            <StaticMetric label="Discovered" value={report.coverage.filesDiscovered} />
            <StaticMetric label="Scanned" value={report.coverage.filesScanned} />
            <StaticMetric label="Parsed" value={report.coverage.filesParsed} />
          </div>
          {report.coverage.reasons.length ? (
            <p
              style={{
                margin: "14px 0 0",
                color: V3.warn,
                fontFamily: FONT_MONO,
                fontSize: 10.5,
              }}
            >
              {report.coverage.reasons.join(", ")}
            </p>
          ) : null}
        </Panel>

        <Panel label="Static tools">
          <div
            aria-label="Static tool executions"
            style={{ display: "flex", gap: 8, flexWrap: "wrap" }}
          >
            {report.toolStatuses.map((tool) => (
              <Badge
                key={tool.tool}
                tone={
                  tool.status === "ok"
                    ? "ok"
                    : tool.status === "error" || tool.status === "timeout"
                      ? "danger"
                      : "warn"
                }
              >
                {tool.tool} · {tool.status}
                {tool.errorCount ? ` · ${tool.errorCount} err` : ""}
              </Badge>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function StaticMetric({ label, value }: { label: string; value: number }) {
  return (
    <div
      aria-label={`${label}: ${value}`}
      style={{
        border: `1px solid ${V3.rule}`,
        padding: "12px",
        background: V3.paper3,
      }}
    >
      <Eyebrow>{label}</Eyebrow>
      <div
        style={{
          marginTop: 8,
          color: V3.ink,
          fontSize: 20,
          fontWeight: 650,
        }}
      >
        {formatNumber(value)}
      </div>
    </div>
  );
}

// Compact verdict key: every state is shown with its distinct tone so an
// operator can read the header badge against the full scale and never mistake
// an inconclusive/clean-with-notes run for a clean pass (B4).
function VerdictLegend() {
  return (
    <div
      aria-label="Verdict scale"
      style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}
    >
      <Eyebrow>Scale</Eyebrow>
      {VERDICT_LEGEND.map((entry) => (
        <span key={entry.verdict} style={{ display: "inline-flex" }}>
          <Badge tone={entry.tone}>{entry.label}</Badge>
        </span>
      ))}
    </div>
  );
}

function OverviewSection({
  report,
}: {
  report: ReportModel;
}) {
  const rationale = report.detection?.verdictRationale;
  const verdict = report.detection?.verdict;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {verdict ? <VerdictOverviewBand verdict={verdict} /> : null}
      {rationale ? (
        <RationalePanel rationale={rationale} verdict={verdict} />
      ) : null}
      <VerdictSummaryPanel detection={report.detection} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))", gap: 20 }}>
        <BreakdownPanel label="By kind" rows={buildKindRows(report)} />
        <BreakdownPanel label="Risk mix" rows={buildRiskRows(report)} />
      </div>
    </div>
  );
}

function VerdictOverviewBand({ verdict }: { verdict: string }) {
  const action = verdictAction(verdict);
  return (
    <section
      aria-label="Verdict overview"
      style={{
        border: `1px solid ${V3.rule}`,
        background: V3.paper2,
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 260px), 1fr))",
        }}
      >
        <div
          style={{
            padding: "18px 20px",
            borderRight: `1px solid ${V3.rule}`,
            borderBottom: `1px solid ${V3.rule}`,
          }}
        >
          <Eyebrow>Current verdict</Eyebrow>
          <div style={{ marginTop: 12 }}>
            <Badge tone={verdictTone(verdict)} style={{ padding: "6px 10px", fontSize: 11 }}>
              Verdict · {verdict.toUpperCase()}
            </Badge>
          </div>
        </div>
        <div style={{ padding: "18px 20px", borderBottom: `1px solid ${V3.rule}` }}>
          <Eyebrow>Operator action</Eyebrow>
          <p
            role="note"
            aria-label="Recommended action"
            style={{
              margin: "10px 0 0",
              maxWidth: 680,
              fontSize: 13.5,
              lineHeight: 1.55,
              color: V3.ink2,
            }}
          >
            {action}
          </p>
        </div>
      </div>
      <div style={{ padding: "13px 20px", background: V3.paper3 }}>
        <VerdictLegend />
      </div>
    </section>
  );
}

// The backend ships the rationale as a single string, typically
// "<lead>: code_a, code_b, …". Split it into a lead sentence plus one chip per
// reason code so a long incomplete-analysis list reads as scannable signals
// instead of a wall of comma-joined text. Falls back to the raw string when the
// shape doesn't match.
function RationalePanel({ rationale, verdict }: { rationale: string; verdict?: string }) {
  const splitAt = rationale.indexOf(":");
  const lead = splitAt >= 0 ? rationale.slice(0, splitAt).trim() : "";
  const codes =
    splitAt >= 0
      ? rationale
          .slice(splitAt + 1)
          .split(",")
          .map((part) => part.trim())
          .filter(Boolean)
      : [];
  const chipTone: V3Tone = verdictTone(verdict);

  if (!codes.length) {
    return (
      <Panel label="Verdict rationale">
        <p style={{ fontSize: 13.5, color: V3.ink2, lineHeight: 1.6, margin: 0, maxWidth: 820 }}>
          {rationale}
        </p>
      </Panel>
    );
  }

  return (
    <Panel
      label="Verdict rationale"
      right={
        <Badge tone={chipTone}>
          {codes.length} verdict signal{codes.length === 1 ? "" : "s"}
        </Badge>
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
        {lead ? (
          <p style={{ fontSize: 13.5, color: V3.ink2, lineHeight: 1.6, margin: 0, maxWidth: 820 }}>
            {lead.charAt(0).toUpperCase() + lead.slice(1)}
          </p>
        ) : null}
        <div
          role="list"
          aria-label="Verdict signals"
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(min(100%, 260px), 1fr))",
            borderTop: `1px solid ${V3.rule}`,
            borderLeft: `1px solid ${V3.rule}`,
          }}
        >
          {codes.map((code, index) => (
            <div
              key={code}
              role="listitem"
              title={code}
              style={{
                display: "grid",
                gridTemplateColumns: "34px minmax(0, 1fr)",
                minHeight: 64,
                borderRight: `1px solid ${V3.rule}`,
                borderBottom: `1px solid ${V3.rule}`,
                background: V3.paper,
              }}
            >
              <span
                aria-hidden
                style={{
                  display: "grid",
                  placeItems: "center",
                  borderRight: `1px solid ${V3.rule}`,
                  color: V3.coral,
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 10,
                  fontWeight: 700,
                }}
              >
                {String(index + 1).padStart(2, "0")}
              </span>
              <span
                style={{
                  alignSelf: "center",
                  padding: "12px 14px",
                  color: V3.ink2,
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 11,
                  lineHeight: 1.45,
                  letterSpacing: "0.04em",
                  textTransform: "uppercase",
                }}
              >
                {code.replaceAll("_", " ")}
              </span>
            </div>
          ))}
        </div>
      </div>
    </Panel>
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
  const groupOverflow = graph
    ? Math.max(0, graph.groups.length - DISPLAY_CAPS.RELATIONS_GROUPS)
    : 0;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {graph && graph.groups.length ? (
        <Panel
          label="Interaction graph"
          right={
            groupOverflow > 0 ? (
              <span data-testid="interaction-groups-truncation-indicator">
                <Eyebrow>+{groupOverflow.toLocaleString()} groups not shown</Eyebrow>
              </span>
            ) : undefined
          }
        >
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

type LedgerKindFilter = "all" | "Network" | "File" | "Activation" | "Scenario";

const LEDGER_KIND_TABS: TabSpec<LedgerKindFilter>[] = [
  { value: "all", label: "All" },
  { value: "Network", label: "Network" },
  { value: "File", label: "File" },
  { value: "Activation", label: "Activation" },
  { value: "Scenario", label: "Scenario" },
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
