import { Badge } from "../ui/Badge";
import { Panel, PanelHeader } from "../ui/Panel";
import type {
  AttributionSummaryView,
  ReportSummaryView,
  RiskSignalView,
} from "../../lib/types/view-models";

function qualityTone(value: ReportSummaryView["runQuality"]) {
  if (value === "high") return "success";
  if (value === "medium") return "warning";
  if (value === "low") return "danger";
  return "amber";
}

function severityTone(value: string) {
  if (value === "critical" || value === "high") return "danger";
  if (value === "medium") return "warning";
  return "default";
}

export function RiskOverviewPanel({
  summary,
  attributionSummary,
  riskSignals,
  onSelectEvent,
  title = "Risk posture",
  description = "Run quality, attribution strength, and evidence-linked risk signals are summarized here.",
}: {
  summary: ReportSummaryView;
  attributionSummary: AttributionSummaryView;
  riskSignals: RiskSignalView[];
  onSelectEvent?: (eventId: string) => void;
  title?: string;
  description?: string;
}) {
  const inconclusive = summary.runQuality === "inconclusive";

  return (
    <Panel className="overflow-hidden p-0">
      <div className="border-b border-line px-5 py-5">
        <PanelHeader description={description} title={title} />
      </div>
      <div className="space-y-5 px-5 py-5">
        {inconclusive ? (
          <div className="rounded-[16px] border border-warning/25 bg-warning/10 px-4 py-4 text-sm leading-6 text-warning">
            This run is inconclusive because the target extension was not observed with enough confidence.
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <MetricTile title="Target observed" value={summary.targetExtensionObserved ? "Yes" : "No"} />
          <MetricTile title="Run quality" value={summary.runQuality.replaceAll("_", " ")} badgeTone={qualityTone(summary.runQuality)} />
          <MetricTile title="Verification gap" value={String(summary.verificationGap)} />
          <MetricTile title="Strong file attribution" value={String(attributionSummary.strongTargetFileEventCount)} />
          <MetricTile title="Strong network attribution" value={String(attributionSummary.strongTargetNetworkEventCount)} />
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricTile title="Target activations" value={String(attributionSummary.targetActivationCount)} />
          <MetricTile title="Correlative only" value={String(attributionSummary.correlatedOnlyEventCount)} />
          <MetricTile title="Background activations" value={String(attributionSummary.backgroundActivationCount)} />
          <MetricTile title="Trigger plan" value={summary.triggerPlanApplied ? "Applied" : "Not applied"} badgeTone={summary.triggerPlanApplied ? "success" : "warning"} />
        </div>

        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <div className="micro-label">Risk signals</div>
            <Badge tone={riskSignals.length ? "danger" : "success"}>
              {riskSignals.length} signal{riskSignals.length === 1 ? "" : "s"}
            </Badge>
          </div>
          {riskSignals.length ? (
            <div className="space-y-3">
              {riskSignals.map((signal) => (
                <article className="rounded-[16px] border border-line bg-panelAlt/70 px-4 py-4" key={signal.signalId}>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={severityTone(signal.severity)}>{signal.severityLabel}</Badge>
                    <Badge>{signal.categoryLabel}</Badge>
                    <Badge tone="amber">{signal.confidencePct}% confidence</Badge>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-ink">{signal.summary}</p>
                  {signal.evidenceEventIds.length ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {signal.evidenceEventIds.slice(0, 4).map((eventId) => (
                        <button
                          className="ghost-button"
                          key={eventId}
                          onClick={() => onSelectEvent?.(eventId)}
                          type="button"
                        >
                          {eventId}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <div className="rounded-[16px] border border-line bg-panelAlt/50 px-4 py-4 text-sm leading-6 text-mute">
              No explicit risk signals were derived from this run.
            </div>
          )}
        </div>
      </div>
    </Panel>
  );
}

function MetricTile({
  title,
  value,
  badgeTone,
}: {
  title: string;
  value: string;
  badgeTone?: "default" | "success" | "warning" | "danger" | "amber";
}) {
  return (
    <div className="metric-tile">
      <div className="micro-label">{title}</div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {badgeTone ? (
          <Badge tone={badgeTone}>{value}</Badge>
        ) : (
          <div className="text-sm font-medium capitalize text-ink">{value}</div>
        )}
      </div>
    </div>
  );
}
