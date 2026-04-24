import { EvidenceTable } from "../../components/evidence/EvidenceTable";
import { EvidenceTimelineChart } from "../../components/evidence/EvidenceTimelineChart";
import { Inspector } from "../../components/evidence/Inspector";
import { RiskOverviewPanel } from "../../components/evidence/RiskOverviewPanel";
import { EmptyState } from "../../components/ui/EmptyState";
import { Panel, PanelHeader } from "../../components/ui/Panel";
import { SegmentedTabs } from "../../components/ui/SegmentedTabs";
import type { InspectorTab } from "../evidence";
import type {
  ActivationReportView,
  EvidenceInspectorView,
  RuleDraftView,
} from "../../lib/types/view-models";

export type ReportWorkspaceTab = "evidence" | "analysis";

type ReportModel = ActivationReportView;

function computeRiskScore(report: ReportModel) {
  const score = Math.max(8, Math.min(96, Math.round(report.summary.signalSummaryScore || 0)));
  const labelByLevel = {
    benign: "Benign",
    needs_review: "Needs review",
    suspicious: "Suspicious",
    likely_malicious: "Likely malicious",
  } as const;

  return {
    score,
    label: labelByLevel[report.summary.signalSummaryLevel] || "Needs review",
    note:
      report.summary.signalSummaryNote ||
      "This report did not include a computed activation-layer signal summary note.",
    reasons: report.summary.signalSummaryReasons,
  };
}

export function DashboardScore({
  report,
  onSelectEvent,
}: {
  report: ReportModel;
  onSelectEvent: (eventId: string) => void;
}) {
  const risk = computeRiskScore(report);
  const toneClass =
    risk.score >= 75 ? "text-danger" : risk.score >= 45 ? "text-warning" : "text-accent";

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

export function CategoryWorkspace({
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
  events: ReportModel["evidence"];
  selectedEventId?: string;
  onSelectEvent: (eventId: string) => void;
  inspector: EvidenceInspectorView | null;
  inspectorTab: InspectorTab;
  onInspectorTabChange: (next: InspectorTab) => void;
  onWorkspaceTabChange: (next: ReportWorkspaceTab) => void;
  emptyTitle: string;
  ruleDraft: RuleDraftView | null;
  workspaceTab: ReportWorkspaceTab;
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
            onChange={(next) => onWorkspaceTabChange(next as ReportWorkspaceTab)}
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
