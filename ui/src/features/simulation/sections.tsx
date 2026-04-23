import { EvidenceTable } from "../../components/evidence/EvidenceTable";
import { EvidenceTimelineChart } from "../../components/evidence/EvidenceTimelineChart";
import { Inspector } from "../../components/evidence/Inspector";
import { LogStreamsPanel } from "../../components/evidence/LogStreamsPanel";
import { RiskOverviewPanel } from "../../components/evidence/RiskOverviewPanel";
import { RunActivityRail } from "../../components/simulation/RunActivityRail";
import { EmptyState } from "../../components/ui/EmptyState";
import { Panel, PanelHeader } from "../../components/ui/Panel";
import { SegmentedTabs } from "../../components/ui/SegmentedTabs";
import type { AnalyzeJobStatusDto } from "../../lib/types/contracts";
import type {
  ActivationReportView,
  EvidenceInspectorView,
  SimulationViewModel,
  RuleDraftView,
} from "../../lib/types/view-models";
import type { InspectorTab } from "../evidence";
import { getExpectedTelemetry } from "./telemetry";

export type WorkspaceTab = "evidence" | "analysis" | "logs";

export function RunActivityPanel({
  job,
  model,
}: {
  job: AnalyzeJobStatusDto | null;
  model: SimulationViewModel | null;
}) {
  return (
    <Panel className="overflow-hidden p-0">
      <div className="border-b border-line px-5 py-5">
        <PanelHeader
          description="Step-by-step executor progress with enough detail to understand where the sandbox run is spending time."
          title="Run Activity"
        />
      </div>
      <div className="px-5 py-5">
        {job && model ? (
          <RunActivityRail job={job} model={model} />
        ) : (
          <EmptyState body="Job metadata is still loading." eyebrow="Warmup" title="Fetching job snapshot" />
        )}
      </div>
    </Panel>
  );
}

export function LiveRiskStrip({
  report,
  onSelectEvent,
}: {
  report: ActivationReportView | null;
  onSelectEvent: (eventId: string) => void;
}) {
  if (!report) return null;
  return (
    <RiskOverviewPanel
      attributionSummary={report.attributionSummary}
      onSelectEvent={onSelectEvent}
      riskSignals={report.riskSignals}
      summary={report.summary}
      title="Live detection posture"
      description="Use this strip to see whether the target was observed and whether the current run is conclusive before drilling into raw evidence."
    />
  );
}

export function SimulationStatusPanel({
  model,
  status,
  hasEvidence,
  report,
}: {
  model: SimulationViewModel | null;
  status?: string;
  hasEvidence: boolean;
  report: ActivationReportView | null;
}) {
  const skippedDetail =
    report?.summary.skippedScenarioDetails.length
      ? report.summary.skippedScenarioDetails
          .map((entry) => `${entry.name}: ${entry.reasonCode}${entry.detail ? ` (${entry.detail})` : ""}`)
          .join("\n")
      : "No skipped scenario reasons were recorded.";
  return (
    <Panel className="overflow-hidden p-0">
      <div className="border-b border-line px-5 py-5">
        <PanelHeader
          description="Short operational guidance while the run is queued, warming up, or already streaming evidence."
          title="Run Status"
        />
      </div>
      <div className="grid gap-4 px-5 py-5 lg:grid-cols-3">
        <StatusCard body={model?.currentStepLabel || "Queued"} title="Current step" />
        <StatusCard body={getExpectedTelemetry(status, hasEvidence)} title="Next expected telemetry" />
        <StatusCard
          body={
            report?.summary.skippedScenarioDetails.length
              ? skippedDetail
              : (model?.recentMessages || ["Waiting for job metadata."]).join("\n")
          }
          preformatted
          title={report?.summary.skippedScenarioDetails.length ? "Skipped scenarios" : "Recent messages"}
        />
      </div>
    </Panel>
  );
}

export function SimulationWorkspace({
  workspaceTab,
  report,
  filteredEvents,
  eventId,
  inspector,
  inspectorTab,
  ruleDraft,
  model,
  status,
  onWorkspaceTabChange,
  onInspectorTabChange,
  onSelectEvent,
}: {
  workspaceTab: WorkspaceTab;
  report: ActivationReportView | null;
  filteredEvents: ActivationReportView["evidence"];
  eventId?: string;
  inspector: EvidenceInspectorView | null;
  inspectorTab: InspectorTab;
  ruleDraft: RuleDraftView | null;
  model: SimulationViewModel | null;
  status?: string;
  onWorkspaceTabChange: (next: WorkspaceTab) => void;
  onInspectorTabChange: (next: InspectorTab) => void;
  onSelectEvent: (eventId: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="eyebrow">Workspace</div>
          <h2 className="mt-3 text-[32px] font-semibold tracking-[-0.04em] text-ink">Simulation evidence</h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-mute sm:text-base">
            Switch between the raw live stream and the analysis surface without compressing the inspector into a narrow right rail.
          </p>
        </div>

        <SegmentedTabs
          onChange={(next) => onWorkspaceTabChange(next as WorkspaceTab)}
          options={[
            { value: "evidence", label: "Evidence" },
            { value: "analysis", label: "Analysis" },
            { value: "logs", label: "Logs" },
          ]}
          value={workspaceTab}
        />
      </div>

      {workspaceTab === "analysis" ? (
        <Inspector activeTab={inspectorTab} inspector={inspector} onTabChange={onInspectorTabChange} ruleDraft={ruleDraft} />
      ) : workspaceTab === "logs" ? (
        <LogStreamsPanel
          eventAttempts={report?.eventAttempts || []}
          coverageTracks={report?.coverageTracks || emptyCoverageTracks()}
          heuristicWorkflowCoverage={report?.heuristicWorkflowCoverage || emptyEventCoverage("heuristic")}
          logStreams={report?.logStreams || emptyLogStreams()}
          officialEventCoverage={report?.officialEventCoverage || emptyEventCoverage("official")}
          stimulusPasses={report?.stimulusPasses || []}
        />
      ) : report && filteredEvents.length ? (
        <Panel className="overflow-hidden p-0">
          <div className="border-b border-line px-5 py-5">
            <PanelHeader description="Live Event Stream" title="Evidence" />
          </div>
          <div className="space-y-5 px-5 py-5">
            <div className="rounded-[22px] border border-line bg-canvas/55 px-4 py-4">
              <div className="micro-label">Mini Timeline</div>
              <div className="mt-3">
                <EvidenceTimelineChart className="h-[210px] w-full" compact events={filteredEvents} onSelect={onSelectEvent} />
              </div>
            </div>
            <div>
              <div className="micro-label">Live Event Stream</div>
              <div className="mt-3">
                <EvidenceTable events={filteredEvents} onSelect={onSelectEvent} selectedEventId={eventId} />
              </div>
            </div>
          </div>
        </Panel>
      ) : (
        <WarmupPanel body={getExpectedTelemetry(status, false)} model={model} />
      )}
    </div>
  );
}

export function TelemetryField({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-tile">
      <div className="micro-label">{label}</div>
      <div className="mt-3 text-sm font-medium text-ink">{value}</div>
    </div>
  );
}

export function StatusCard({
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

function WarmupPanel({
  model,
  body,
}: {
  model: SimulationViewModel | null;
  body: string;
}) {
  return (
    <Panel className="overflow-hidden p-0">
      <div className="border-b border-line px-5 py-5">
        <PanelHeader
          description="Compact guidance cards keep the workspace readable until the first event lands."
          title="Run Is Warming Up"
        />
      </div>
      <div className="grid gap-4 px-5 py-5 lg:grid-cols-3">
        <StatusCard body={model?.currentStepLabel || "Queued"} title="Current step" />
        <StatusCard body={body} title="Next expected telemetry" />
        <StatusCard
          body={(model?.recentMessages || ["Waiting for the sandbox run to emit telemetry."]).join("\n")}
          preformatted
          title="Recent messages"
        />
      </div>
    </Panel>
  );
}

function emptyCoverageTracks() {
  return {
    official: {
      source: "",
      selectedScenarios: [],
      summary: {
        covered: 0,
        partial: 0,
        missing: 0,
        attempted: 0,
        verified: 0,
        missingCapabilities: [],
        attemptedCapabilities: [],
        verifiedCapabilities: [],
      },
      matrix: [],
    },
    heuristic: {
      source: "",
      selectedScenarios: [],
      summary: {
        covered: 0,
        partial: 0,
        missing: 0,
        attempted: 0,
        verified: 0,
        missingCapabilities: [],
        attemptedCapabilities: [],
        verifiedCapabilities: [],
      },
      matrix: [],
    },
  };
}

function emptyEventCoverage(track: string) {
  return {
    track,
    declared: 0,
    verified: 0,
    attemptedOnly: 0,
    failed: 0,
    blocked: 0,
    unresolved: 0,
    declaredEvents: [],
  };
}

function emptyLogStreams() {
  return {
    targetExtensionHost: [],
    otherExtensionHost: [],
    automation: [],
    uiBlockers: [],
  };
}
