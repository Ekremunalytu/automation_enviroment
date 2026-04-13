import { useMemo, useState } from "react";
import type {
  CoverageCapabilityView,
  CoverageSummaryView,
  LogStreamsView,
} from "../../lib/types/view-models";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { Panel, PanelHeader } from "../ui/Panel";
import { SegmentedTabs } from "../ui/SegmentedTabs";

type LogStreamTab = "target" | "other" | "automation" | "ui";

const STREAM_META: Record<
  LogStreamTab,
  { label: string; title: string; description: string }
> = {
  target: {
    label: "Target Triggers",
    title: "Target extension host triggers",
    description:
      "Activation lines for the extension under analysis stay isolated from general automation noise.",
  },
  other: {
    label: "Other Extensions",
    title: "Other extension host activity",
    description:
      "These activations happened in the same VS Code session but were not emitted by the target extension.",
  },
  automation: {
    label: "Automation",
    title: "Automation trace",
    description:
      "Scenario lifecycle, command launches, URI/task/walkthrough/custom-editor triggers.",
  },
  ui: {
    label: "UI Blockers",
    title: "Popup and modal blockers",
    description:
      "Notifications, popups, and modal interruptions are isolated here so verification gaps are visible.",
  },
};

export function LogStreamsPanel({
  coverageMatrix,
  coverageSummary,
  logStreams,
}: {
  coverageMatrix: CoverageCapabilityView[];
  coverageSummary: CoverageSummaryView;
  logStreams: LogStreamsView;
}) {
  const [activeTab, setActiveTab] = useState<LogStreamTab>("target");
  const activeEntries = useMemo(() => {
    if (activeTab === "other") return logStreams.otherExtensionHost;
    if (activeTab === "automation") return logStreams.automation;
    if (activeTab === "ui") return logStreams.uiBlockers;
    return logStreams.targetExtensionHost;
  }, [activeTab, logStreams]);

  const partialCapabilities = coverageMatrix.filter((item) => item.supportStatus === "partial");
  const attemptedOnly = coverageMatrix.filter((item) => item.verificationStatus === "attempted_only");

  return (
    <div className="space-y-4">
      <Panel className="overflow-hidden p-0">
        <div className="border-b border-line px-5 py-5">
          <PanelHeader
            description="The automation framework coverage is summarized here so missing VS Code API surfaces are visible next to the captured logs."
            title="Coverage audit"
          />
        </div>
        <div className="grid gap-4 px-5 py-5 lg:grid-cols-[repeat(3,minmax(0,1fr))]">
          <MetricTile title="Covered" value={String(coverageSummary.covered)} />
          <MetricTile title="Partial" value={String(coverageSummary.partial)} />
          <MetricTile title="Missing" value={String(coverageSummary.missing)} />
          <MetricTile title="Attempted" value={String(coverageSummary.attempted)} />
          <MetricTile title="Verified" value={String(coverageSummary.verified)} />
          <MetricTile title="Verification Gap" value={String(Math.max(coverageSummary.attempted - coverageSummary.verified, 0))} />
        </div>
        <div className="border-t border-line px-5 py-5">
          <div className="micro-label">Missing capabilities</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {coverageSummary.missingCapabilities.length ? (
              coverageSummary.missingCapabilities.map((item) => (
                <Badge key={item} tone="danger">
                  {item}
                </Badge>
              ))
            ) : (
              <span className="text-sm text-mute">No missing capabilities reported.</span>
            )}
          </div>
          {partialCapabilities.length ? (
            <div className="mt-4 text-sm leading-6 text-mute">
              Partial support:{" "}
              {partialCapabilities
                .slice(0, 4)
                .map((item) => item.capabilityLabel)
                .join(", ")}
              {partialCapabilities.length > 4 ? "..." : ""}
            </div>
          ) : null}
          {coverageSummary.attemptedCapabilities.length ? (
            <div className="mt-4 text-sm leading-6 text-mute">
              Attempted: {coverageSummary.attemptedCapabilities.join(", ")}
            </div>
          ) : null}
          {coverageSummary.verifiedCapabilities.length ? (
            <div className="mt-2 text-sm leading-6 text-mute">
              Verified: {coverageSummary.verifiedCapabilities.join(", ")}
            </div>
          ) : null}
          {attemptedOnly.length ? (
            <div className="mt-2 text-sm leading-6 text-warning">
              Attempted but not verified: {attemptedOnly.map((item) => item.capabilityLabel).join(", ")}
            </div>
          ) : null}
        </div>
      </Panel>

      <Panel className="overflow-hidden p-0">
        <div className="border-b border-line px-5 py-5">
          <PanelHeader
            description={STREAM_META[activeTab].description}
            right={
              <SegmentedTabs
                onChange={(next) => setActiveTab(next as LogStreamTab)}
                options={[
                  { value: "target", label: STREAM_META.target.label },
                  { value: "other", label: STREAM_META.other.label },
                  { value: "automation", label: STREAM_META.automation.label },
                  { value: "ui", label: STREAM_META.ui.label },
                ]}
                value={activeTab}
              />
            }
            title={STREAM_META[activeTab].title}
          />
        </div>

        {activeEntries.length ? (
          <div className="divide-y divide-line px-5">
            {activeEntries.map((entry, index) => (
              <article className="grid gap-3 py-4 md:grid-cols-[180px_minmax(0,1fr)]" key={`${entry.stream}-${entry.timestamp}-${index}`}>
                <div className="space-y-2 text-sm text-mute">
                  <div>{entry.timestampDisplay}</div>
                  <div>{entry.relTimeS !== null ? `${entry.relTimeS.toFixed(3)}s` : "--"}</div>
                </div>
                <div className="min-w-0 space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={entry.isTargetExtension ? "accent" : activeTab === "automation" ? "amber" : "default"}>
                      {entry.kindLabel}
                    </Badge>
                    {entry.status ? <Badge tone={entry.status === "failed" ? "danger" : entry.status === "completed" ? "success" : "warning"}>{entry.statusLabel}</Badge> : null}
                    {entry.extensionId ? <Badge>{entry.extensionId}</Badge> : null}
                    {entry.activationEvent ? <Badge tone="cyan">{entry.activationEvent}</Badge> : null}
                    {entry.scenarioName ? <Badge tone="warning">{entry.scenarioName}</Badge> : null}
                  </div>
                  <div className="text-sm leading-6 text-ink">{entry.message}</div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="px-5 py-5">
            <EmptyState
              body="No log lines were captured for the selected stream."
              eyebrow="Logs"
              title="Nothing in this stream"
            />
          </div>
        )}
      </Panel>
    </div>
  );
}

function MetricTile({ title, value }: { title: string; value: string }) {
  return (
    <div className="metric-tile">
      <div className="micro-label">{title}</div>
      <div className="mt-3 text-2xl font-semibold tracking-tight text-ink">{value}</div>
    </div>
  );
}
