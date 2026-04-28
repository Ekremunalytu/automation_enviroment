import { EvidenceLedger } from "../../components/evidence/EvidenceLedger";
import { Inspector } from "../../components/evidence/Inspector";
import { LogStreamsPanel } from "../../components/evidence/LogStreamsPanel";
import { RiskOverviewPanel } from "../../components/evidence/RiskOverviewPanel";
import { RunActivityRail } from "../../components/simulation/RunActivityRail";
import { EmptyState } from "../../components/ui/EmptyState";
import { Panel, PanelHeader } from "../../components/ui/Panel";
import { Eyebrow, Panel as V3Panel, SectionTitle, V3 } from "../../components/v3";
import type { AnalyzeJobStatusDto } from "../../lib/types/contracts";
import type {
  ActivationReportView,
  EvidenceInspectorView,
  SimulationViewModel,
  RuleDraftView,
} from "../../lib/types/view-models";
import type { InspectorTab } from "../evidence";
import { getExpectedTelemetry } from "./telemetry";

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

export function LiveEvidenceWorkspace({
  filteredEvents,
  eventId,
  inspector,
  inspectorTab,
  ruleDraft,
  model,
  status,
  detection,
  onInspectorTabChange,
  onSelectEvent,
}: {
  filteredEvents: ActivationReportView["evidence"];
  eventId?: string;
  inspector: EvidenceInspectorView | null;
  inspectorTab: InspectorTab;
  ruleDraft: RuleDraftView | null;
  detection: ActivationReportView["detection"];
  model: SimulationViewModel | null;
  status?: string;
  onInspectorTabChange: (next: InspectorTab) => void;
  onSelectEvent: (eventId: string) => void;
}) {
  if (!filteredEvents.length) {
    return <WarmupPanel body={getExpectedTelemetry(status, false)} model={model} />;
  }

  return (
    <section style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div>
        <Eyebrow>Live</Eyebrow>
        <SectionTitle style={{ marginTop: 10, fontSize: 22 }}>Live event ledger</SectionTitle>
        <p style={{ marginTop: 10, maxWidth: 720, color: V3.ink3, fontSize: 13.5, lineHeight: 1.6 }}>
          Inspect the raw stream and selected-event provenance in the same surface.
        </p>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1fr) minmax(280px, 320px)",
          gap: 18,
          alignItems: "start",
        }}
      >
        <V3Panel label="Event stream" bodyStyle={{ padding: 0 }}>
          <EvidenceLedger
            events={filteredEvents}
            onSelect={onSelectEvent}
            selectedEventId={eventId}
            expandSelected={false}
          />
        </V3Panel>
        <div style={{ position: "sticky", top: 80 }}>
          <Inspector
            activeTab={inspectorTab}
            detection={detection}
            inspector={inspector}
            onTabChange={onInspectorTabChange}
            ruleDraft={ruleDraft}
          />
        </div>
      </div>
    </section>
  );
}

export function SimulationLogsPanel({ report }: { report: ActivationReportView | null }) {
  if (!report) {
    return (
      <EmptyState
        eyebrow="Logs"
        body="Coverage and log streams are available after a report is attached to this job."
        title="No report logs yet"
      />
    );
  }

  return (
    <LogStreamsPanel
      eventAttempts={report.eventAttempts}
      coverageTracks={report.coverageTracks}
      heuristicWorkflowCoverage={report.heuristicWorkflowCoverage}
      logStreams={report.logStreams}
      officialEventCoverage={report.officialEventCoverage}
      stimulusPasses={report.stimulusPasses}
    />
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
