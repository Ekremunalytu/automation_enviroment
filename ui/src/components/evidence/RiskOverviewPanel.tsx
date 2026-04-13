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

function healthTone(value: ReportSummaryView["automationHealthStatus"]) {
  if (value === "healthy") return "success";
  if (value === "degraded") return "warning";
  return "danger";
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
  const degraded = summary.automationHealthStatus === "degraded";
  const legacyHealth = summary.legacyHealthFallback;

  return (
    <Panel className="overflow-hidden p-0">
      <div className="border-b border-line px-5 py-5">
        <PanelHeader description={description} title={title} />
      </div>
      <div className="space-y-5 px-5 py-5">
        {legacyHealth ? (
          <div className="rounded-[16px] border border-warning/25 bg-warning/10 px-4 py-4 text-sm leading-6 text-warning">
            Health metadata is unavailable for this legacy report, so automation reliability is treated as inconclusive.
          </div>
        ) : null}

        {inconclusive ? (
          <div className="rounded-[16px] border border-danger/25 bg-danger/10 px-4 py-4 text-sm leading-6 text-danger">
            This run is inconclusive because the target extension was not observed with enough confidence.
          </div>
        ) : null}

        {degraded ? (
          <div className="rounded-[16px] border border-warning/25 bg-warning/10 px-4 py-4 text-sm leading-6 text-warning">
            This run produced telemetry, but automation health is degraded and the evidence should not be treated as clean by default.
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
          <MetricTile title="Target observed" value={summary.targetExtensionObserved ? "Yes" : "No"} />
          <MetricTile title="Automation health" value={summary.automationHealthStatus.replaceAll("_", " ")} badgeTone={healthTone(summary.automationHealthStatus)} />
          <MetricTile title="Trigger applied" value={summary.triggerPlanApplied ? "Yes" : "No"} badgeTone={summary.triggerPlanApplied ? "success" : "warning"} />
          <MetricTile title="Target activations" value={String(summary.targetActivationCount)} />
          <MetricTile title="Host log present" value={summary.extensionHostLogPresent ? "Yes" : "No"} badgeTone={summary.extensionHostLogPresent ? "success" : "warning"} />
          <MetricTile title="Target stream" value={summary.targetStreamPresent ? "Yes" : "No"} badgeTone={summary.targetStreamPresent ? "success" : "warning"} />
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricTile title="Run quality" value={summary.runQuality.replaceAll("_", " ")} badgeTone={qualityTone(summary.runQuality)} />
          <MetricTile title="Verification gap" value={String(summary.verificationGap)} />
          <MetricTile title="Host output" value={summary.extensionHostOutputPresent ? "Present" : "Missing"} badgeTone={summary.extensionHostOutputPresent ? "success" : "warning"} />
          <MetricTile title="Correlative only" value={String(attributionSummary.correlatedOnlyEventCount)} />
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <MetricTile title="Background activations" value={String(attributionSummary.backgroundActivationCount)} />
          <MetricTile title="Strong file attribution" value={String(attributionSummary.strongTargetFileEventCount)} />
          <MetricTile title="Strong network attribution" value={String(attributionSummary.strongTargetNetworkEventCount)} />
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
              {summary.automationHealthStatus === "healthy"
                ? "No explicit risk signals were derived from this healthy run."
                : "No explicit risk signals were derived, but automation health was not healthy."}
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
