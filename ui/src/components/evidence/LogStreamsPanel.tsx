import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import type {
  CoverageTrackView,
  CoverageTracksView,
  EventAttemptView,
  EventCoverageView,
  LogStreamsView,
  StimulusPassView,
} from "../../lib/types/view-models";
import {
  Badge,
  EmptyState,
  Eyebrow,
  FONT_DISPLAY,
  FONT_MONO,
  Panel,
  Tabs,
  V3,
  type V3Tone,
} from "../v3";

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
  coverageTracks,
  officialEventCoverage,
  heuristicWorkflowCoverage,
  eventAttempts,
  stimulusPasses,
  logStreams,
}: {
  coverageTracks: CoverageTracksView;
  officialEventCoverage: EventCoverageView;
  heuristicWorkflowCoverage: EventCoverageView;
  eventAttempts: EventAttemptView[];
  stimulusPasses: StimulusPassView[];
  logStreams: LogStreamsView;
}) {
  const [activeTab, setActiveTab] = useState<LogStreamTab>("target");
  const activeEntries = useMemo(() => {
    if (activeTab === "other") return logStreams.otherExtensionHost;
    if (activeTab === "automation") return logStreams.automation;
    if (activeTab === "ui") return logStreams.uiBlockers;
    return logStreams.targetExtensionHost;
  }, [activeTab, logStreams]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <Panel padded={false}>
        <SectionHead
          title="Coverage audit"
          description="Official activation coverage and heuristic analyst-workflow coverage are separated here so coverage claims stay honest next to the captured logs."
        />
        <div style={cardGrid}>
          <CoverageAuditCard
            title="Official coverage"
            description="Coverage that maps to official VS Code activation semantics."
            track={coverageTracks.official}
          />
          <CoverageAuditCard
            title="Heuristic workflow coverage"
            description="Analyst workflow coverage that is useful operationally but is not an official activation claim."
            track={coverageTracks.heuristic}
          />
        </div>
        <div style={{ ...cardGrid, borderTop: `1px solid ${V3.rule}` }}>
          <EventCoverageCard
            title="Official event ledger"
            coverage={officialEventCoverage}
            attempts={eventAttempts.filter((item) => item.track === "official")}
            passes={stimulusPasses}
          />
          <EventCoverageCard
            title="Heuristic workflow ledger"
            coverage={heuristicWorkflowCoverage}
            attempts={eventAttempts.filter((item) => item.track === "heuristic")}
            passes={stimulusPasses}
          />
        </div>
      </Panel>

      <Panel padded={false}>
        <div
          style={{
            padding: "16px 18px",
            borderBottom: `1px solid ${V3.rule}`,
            background: V3.paper3,
            display: "flex",
            flexDirection: "column",
            gap: 14,
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <Eyebrow>{STREAM_META[activeTab].title}</Eyebrow>
            <div style={{ fontSize: 13, color: V3.ink3, lineHeight: 1.6, maxWidth: 820 }}>
              {STREAM_META[activeTab].description}
            </div>
          </div>
          <Tabs<LogStreamTab>
            tabs={[
              { value: "target", label: STREAM_META.target.label },
              { value: "other", label: STREAM_META.other.label },
              { value: "automation", label: STREAM_META.automation.label },
              { value: "ui", label: STREAM_META.ui.label },
            ]}
            value={activeTab}
            onChange={setActiveTab}
            style={{ borderBottom: "none" }}
          />
        </div>

        {activeEntries.length ? (
          <div>
            {activeEntries.map((entry, index) => (
              <article
                key={`${entry.stream}-${entry.timestamp}-${index}`}
                style={{
                  display: "grid",
                  gridTemplateColumns: "minmax(110px, 150px) minmax(0, 1fr)",
                  gap: 16,
                  padding: "14px 18px",
                  borderBottom: index < activeEntries.length - 1 ? `1px solid ${V3.rule}` : "none",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 4,
                    fontFamily: FONT_MONO,
                    fontSize: 11,
                    color: V3.ink3,
                  }}
                >
                  <span>{entry.timestampDisplay}</span>
                  <span>{entry.relTimeS !== null ? `${entry.relTimeS.toFixed(3)}s` : "--"}</span>
                </div>
                <div style={{ minWidth: 0, display: "flex", flexDirection: "column", gap: 10 }}>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <Badge tone={entry.isTargetExtension ? "accent" : activeTab === "automation" ? "warn" : "neutral"}>
                      {entry.kindLabel}
                    </Badge>
                    {entry.status ? (
                      <Badge tone={streamStatusTone(entry.status)}>{entry.statusLabel}</Badge>
                    ) : null}
                    {entry.extensionId ? <Badge tone="neutral">{entry.extensionId}</Badge> : null}
                    {entry.activationEvent ? <Badge tone="accent">{entry.activationEvent}</Badge> : null}
                    {entry.scenarioName ? <Badge tone="warn">{entry.scenarioName}</Badge> : null}
                  </div>
                  <div style={{ fontSize: 13, color: V3.ink2, lineHeight: 1.6 }}>{entry.message}</div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div style={{ padding: 18 }}>
            <EmptyState
              eyebrow="Logs"
              title="Nothing in this stream"
              body="No log lines were captured for the selected stream."
            />
          </div>
        )}
      </Panel>
    </div>
  );
}

const cardGrid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))",
  gap: 16,
  padding: 18,
} as const;

function SectionHead({ title, description }: { title: string; description: string }) {
  return (
    <div
      style={{
        padding: "16px 18px",
        borderBottom: `1px solid ${V3.rule}`,
        background: V3.paper3,
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}
    >
      <Eyebrow>{title}</Eyebrow>
      <div style={{ fontSize: 13, color: V3.ink3, lineHeight: 1.6, maxWidth: 820 }}>{description}</div>
    </div>
  );
}

function SubCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <div
      style={{
        border: `1px solid ${V3.rule}`,
        background: V3.card,
        padding: 16,
        display: "flex",
        flexDirection: "column",
        gap: 16,
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <Eyebrow>{title}</Eyebrow>
        {description ? (
          <div style={{ fontSize: 13, color: V3.ink3, lineHeight: 1.6 }}>{description}</div>
        ) : null}
      </div>
      {children}
    </div>
  );
}

function MetricTile({ label, value, tone = "neutral" }: { label: string; value: string; tone?: V3Tone }) {
  const color =
    tone === "danger" ? V3.coral : tone === "warn" ? V3.warn : tone === "ok" ? V3.ok : V3.ink;
  return (
    <div
      style={{
        border: `1px solid ${V3.rule}`,
        background: V3.paper3,
        padding: "12px 14px",
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      <Eyebrow>{label}</Eyebrow>
      <div
        style={{
          fontFamily: FONT_DISPLAY,
          fontSize: 26,
          fontWeight: 800,
          color,
          lineHeight: 1,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {value}
      </div>
    </div>
  );
}

function ChipRow({
  label,
  items,
  tone = "neutral",
  empty,
}: {
  label: string;
  items: string[];
  tone?: V3Tone;
  empty?: string;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <Eyebrow>{label}</Eyebrow>
      {items.length ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {items.map((item) => (
            <span
              key={item}
              title={item}
              style={{ maxWidth: 240, display: "inline-flex", minWidth: 0 }}
            >
              <Badge tone={tone} style={{ minWidth: 0, maxWidth: "100%", overflow: "hidden" }}>
                <span
                  style={{
                    minWidth: 0,
                    maxWidth: "100%",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    display: "inline-block",
                  }}
                >
                  {item}
                </span>
              </Badge>
            </span>
          ))}
        </div>
      ) : (
        <span style={{ fontSize: 13, color: V3.ink3 }}>{empty ?? "None reported."}</span>
      )}
    </div>
  );
}

function CoverageAuditCard({
  title,
  description,
  track,
}: {
  title: string;
  description: string;
  track: CoverageTrackView;
}) {
  const partialCapabilities = track.matrix
    .filter((item) => item.supportStatus === "partial")
    .map((item) => item.capabilityLabel);
  const attemptedOnly = track.matrix
    .filter((item) => item.verificationStatus === "attempted_only")
    .map((item) => item.capabilityLabel);
  const verificationGap = Math.max(track.summary.attempted - track.summary.verified, 0);

  return (
    <SubCard title={title} description={description}>
      <div style={metricGrid(3)}>
        <MetricTile label="Covered" value={String(track.summary.covered)} tone="ok" />
        <MetricTile
          label="Partial"
          value={String(track.summary.partial)}
          tone={track.summary.partial ? "warn" : "neutral"}
        />
        <MetricTile
          label="Missing"
          value={String(track.summary.missing)}
          tone={track.summary.missing ? "danger" : "neutral"}
        />
        <MetricTile label="Attempted" value={String(track.summary.attempted)} />
        <MetricTile label="Verified" value={String(track.summary.verified)} tone="ok" />
        <MetricTile
          label="Verification gap"
          value={String(verificationGap)}
          tone={verificationGap ? "warn" : "neutral"}
        />
      </div>
      <ChipRow
        label="Missing capabilities"
        items={track.summary.missingCapabilities}
        tone="danger"
        empty="No missing capabilities reported."
      />
      {partialCapabilities.length ? (
        <ChipRow label="Partial support" items={partialCapabilities} tone="warn" />
      ) : null}
      {track.summary.attemptedCapabilities.length ? (
        <ChipRow label="Attempted" items={track.summary.attemptedCapabilities} tone="neutral" />
      ) : null}
      {track.summary.verifiedCapabilities.length ? (
        <ChipRow label="Verified" items={track.summary.verifiedCapabilities} tone="ok" />
      ) : null}
      {attemptedOnly.length ? (
        <ChipRow label="Attempted but not verified" items={attemptedOnly} tone="warn" />
      ) : null}
    </SubCard>
  );
}

function EventCoverageCard({
  title,
  coverage,
  attempts,
  passes,
}: {
  title: string;
  coverage: EventCoverageView;
  attempts: EventAttemptView[];
  passes: StimulusPassView[];
}) {
  const unresolved = attempts.filter((item) => item.status !== "verified").slice(0, 6);
  const recentPasses = [...passes].sort((left, right) => left.order - right.order).slice(0, 5);

  return (
    <SubCard title={title}>
      <div style={metricGrid(2)}>
        <MetricTile label="Declared" value={String(coverage.declared)} />
        <MetricTile label="Verified" value={String(coverage.verified)} tone="ok" />
        <MetricTile
          label="Attempted only"
          value={String(coverage.attemptedOnly)}
          tone={coverage.attemptedOnly ? "warn" : "neutral"}
        />
        <MetricTile
          label="Unresolved"
          value={String(coverage.unresolved)}
          tone={coverage.unresolved ? "danger" : "neutral"}
        />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <Eyebrow>Pass timeline</Eyebrow>
        {recentPasses.length ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {recentPasses.map((passItem) => (
              <Badge key={passItem.passId} tone={passTone(passItem.status)}>
                {passItem.label}
              </Badge>
            ))}
          </div>
        ) : (
          <span style={{ fontSize: 13, color: V3.ink3 }}>No pass data in this report.</span>
        )}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <Eyebrow>Unresolved ledger</Eyebrow>
        {unresolved.length ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {unresolved.map((item) => (
              <div
                key={item.attemptId}
                style={{
                  border: `1px solid ${V3.rule}`,
                  background: V3.paper3,
                  padding: "10px 12px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 8,
                }}
              >
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <Badge tone={attemptTone(item.status)}>{item.statusLabel}</Badge>
                  <Badge tone="accent">{item.activationEvent || item.eventFamily}</Badge>
                  <Badge tone="neutral">{item.triggerMethodUsed || item.triggerMethod || "planned"}</Badge>
                </div>
                <div style={{ fontSize: 13, color: V3.ink2, lineHeight: 1.6 }}>
                  {item.resultDetails || item.selectionReasons[0] || "No additional detail."}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <span style={{ fontSize: 13, color: V3.ink3 }}>
            Every declared item in this track verified cleanly.
          </span>
        )}
      </div>
    </SubCard>
  );
}

function metricGrid(columns: number) {
  return {
    display: "grid",
    gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
    gap: 10,
  } as const;
}

function streamStatusTone(status: string): V3Tone {
  return status === "failed" ? "danger" : status === "completed" ? "ok" : "warn";
}

function passTone(status: string): V3Tone {
  return status === "failed" ? "danger" : status === "completed" ? "ok" : "warn";
}

function attemptTone(status: string): V3Tone {
  return status === "failed" ? "danger" : status === "blocked" ? "warn" : "neutral";
}
