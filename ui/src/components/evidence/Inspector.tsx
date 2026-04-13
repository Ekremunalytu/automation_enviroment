import type { EvidenceInspectorView, RuleDraftView } from "../../lib/types/view-models";
import { toRuleJson, toRuleYaml } from "../../lib/rules/draft";
import { ReactECharts } from "../../lib/charts/core";
import { Badge } from "../ui/Badge";
import { Panel, PanelHeader } from "../ui/Panel";
import { SegmentedTabs } from "../ui/SegmentedTabs";

type InspectorTab = "provenance" | "relations" | "rule";

export function Inspector({
  activeTab,
  onTabChange,
  inspector,
  ruleDraft,
}: {
  activeTab: InspectorTab;
  onTabChange: (next: InspectorTab) => void;
  inspector: EvidenceInspectorView | null;
  ruleDraft: RuleDraftView | null;
}) {
  const tabs = (
    <SegmentedTabs
      onChange={(next) => onTabChange(next as InspectorTab)}
      options={[
        { value: "provenance", label: "Provenance" },
        { value: "relations", label: "Relations" },
        { value: "rule", label: "Rule Draft" },
      ]}
      value={activeTab}
    />
  );

  if (activeTab === "rule") {
    return (
      <Panel className="overflow-hidden p-0 xl:sticky xl:top-24">
        <div className="border-b border-line px-5 py-5">
          <PanelHeader
            description="Portable rule output derived from the current evidence selection."
            right={tabs}
            title="Rule Draft"
          />
        </div>

        {ruleDraft ? (
          <div className="space-y-5 px-5 py-5">
            <div className="grid gap-3 sm:grid-cols-2">
              <Meta label="Title" value={ruleDraft.title} />
              <Meta label="Severity" value={ruleDraft.severity.toUpperCase()} />
              <Meta label="Confidence" value={`${Math.round(ruleDraft.confidence * 100)}%`} />
              <Meta label="Conditions" value={String(ruleDraft.conditions.length)} />
            </div>

            <section className="panel-alt p-4">
              <div className="micro-label">Rule Export</div>
              <p className="mt-3 text-sm leading-6 text-mute">{ruleDraft.rationale}</p>
            </section>

            <section>
              <div className="micro-label">Labels</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {ruleDraft.labels.map((label) => (
                  <Badge key={label} tone="accent">
                    {label}
                  </Badge>
                ))}
              </div>
            </section>

            <section>
              <div className="micro-label">Conditions</div>
              <div className="mt-3 space-y-2">
                {ruleDraft.conditions.map((condition) => (
                  <div key={`${condition.field}-${condition.operator}-${String(condition.value)}`} className="panel-alt px-3 py-3 text-sm text-ink">
                    <span className="font-mono text-accentSoft">{condition.field}</span>
                    <span className="mx-2 text-mute">{condition.operator}</span>
                    <span className="font-mono text-ink">{JSON.stringify(condition.value)}</span>
                  </div>
                ))}
              </div>
            </section>

            <DualCodeBlock json={toRuleJson(ruleDraft)} yaml={toRuleYaml(ruleDraft)} />
          </div>
        ) : (
          <div className="px-5 py-6 text-sm text-mute">Select an event to generate a rule draft.</div>
        )}
      </Panel>
    );
  }

  if (activeTab === "relations") {
    return (
      <Panel className="overflow-hidden p-0 xl:sticky xl:top-24">
        <div className="border-b border-line px-5 py-5">
          <PanelHeader
            description="Visualize how the focused event connects to peers instead of scanning a repetitive chain list."
            right={tabs}
            title="Relations"
          />
        </div>

        {inspector ? (
          <div className="space-y-5 px-5 py-5">
            <div className="grid gap-3 sm:grid-cols-2">
              <Meta label="Selected Event" value={inspector.event.artifactShort} />
              <Meta label="Linked Events" value={String(inspector.related.length)} />
            </div>

            {inspector.related.length ? (
              <>
                <div className="rounded-[16px] border border-line bg-panelAlt p-4">
                  <div className="micro-label">Connection Map</div>
                  <ReactECharts className="mt-3 h-[260px] w-full" option={buildRelationGraphOption(inspector)} />
                </div>

                <div className="space-y-3">
                  <div className="micro-label">Connection Summary</div>
                  <div className="space-y-2">
                    {buildRelationSummary(inspector).map((item) => (
                      <div key={`${item.label}-${item.target}`} className="metric-tile">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <div className="text-sm font-medium text-ink">
                              {item.label} → {item.target}
                            </div>
                            <div className="mt-1 text-sm leading-6 text-mute">{item.reason}</div>
                          </div>
                          <Badge tone={item.confidence >= 80 ? "success" : item.confidence >= 50 ? "warning" : "danger"}>
                            {item.confidence}%
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="rounded-[16px] border border-dashed border-lineStrong px-4 py-5 text-sm text-mute">
                No explicit evidence links are available for the selected event.
              </div>
            )}
          </div>
        ) : (
          <div className="px-5 py-6 text-sm text-mute">Select an event to visualize its related evidence.</div>
        )}
      </Panel>
    );
  }

  return (
    <Panel className="overflow-hidden p-0 xl:sticky xl:top-24">
      <div className="border-b border-line px-5 py-5">
        <PanelHeader
          description="Focused event context and attribution metadata without the noisy repeated relation chain."
          right={tabs}
          title="Provenance"
        />
      </div>

      {inspector ? (
        <div className="space-y-5 px-5 py-5">
          <section className="panel-alt p-4">
            <div className="micro-label">Event Summary</div>
            <div className="mt-3 text-2xl font-semibold tracking-tight text-ink">{inspector.event.artifactShort}</div>
            <p className="mt-3 text-sm leading-6 text-mute">{inspector.event.summaryDisplay}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge tone="accent">{inspector.event.kindLabel}</Badge>
              <Badge tone="cyan">{inspector.event.collectorLabel}</Badge>
              <Badge tone="lime">{inspector.event.actorLabel}</Badge>
              {inspector.event.sensitive ? <Badge tone="rose">Sensitive</Badge> : null}
            </div>
          </section>

          <section>
            <div className="micro-label">Attribution Metadata</div>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <Meta label="Timestamp" value={inspector.event.timestampDisplay} />
              <Meta label="Scenario" value={inspector.event.scenarioLabel} />
              <Meta label="Extension" value={inspector.event.extensionId || "(unattributed)"} />
              <Meta label="Host / Path" value={inspector.event.host || inspector.event.path || "(n/a)"} />
              <Meta
                label="Destination"
                value={
                  inspector.event.destinationIp
                    ? `${inspector.event.destinationIp}${inspector.event.destinationPort ? `:${inspector.event.destinationPort}` : ""}`
                    : "(n/a)"
                }
              />
              <Meta label="Operation" value={inspector.event.detail || "(n/a)"} />
            </div>
          </section>

          <section className="panel-alt p-4">
            <div className="micro-label">Link Status</div>
            <div className="mt-3 text-sm leading-6 text-mute">
              {inspector.related.length
                ? `${inspector.related.length} related evidence links are available in the Relations tab.`
                : "No related evidence links are available for the selected event."}
            </div>
          </section>
        </div>
      ) : (
        <div className="px-5 py-6 text-sm text-mute">Select an event from the table or timeline to populate the inspector.</div>
      )}
    </Panel>
  );
}

function buildRelationSummary(inspector: EvidenceInspectorView) {
  const groups = new Map<string, { label: string; target: string; reason: string; confidence: number; count: number }>();

  for (const link of inspector.related) {
    const key = `${link.linkLabel}-${link.peerEvent?.kindLabel || "Unknown"}`;
    const existing = groups.get(key);
    if (existing) {
      existing.count += 1;
      existing.confidence = Math.max(existing.confidence, link.confidencePct);
      continue;
    }
    groups.set(key, {
      label: link.linkLabel,
      target: link.peerEvent?.kindLabel || "Unknown",
      reason: link.reason,
      confidence: link.confidencePct,
      count: 1,
    });
  }

  return Array.from(groups.values()).map((item) => ({
    ...item,
    reason: item.count > 1 ? `${item.reason} (${item.count} linked events)` : item.reason,
  }));
}

function buildRelationGraphOption(inspector: EvidenceInspectorView) {
  const centerId = inspector.event.eventId;
  const nodes = [
    {
      id: centerId,
      name: inspector.event.artifactShort,
      category: 0,
      symbolSize: 58,
      value: inspector.event.kindLabel,
    },
    ...inspector.related.map((link) => ({
      id: link.peerEvent?.eventId || `${link.linkType}-${link.direction}`,
      name: link.peerEvent?.artifactShort || link.linkLabel,
      category: link.peerEvent?.kind === "file" ? 1 : link.peerEvent?.kind === "network" ? 2 : 3,
      symbolSize: 30 + Math.round(link.confidencePct / 8),
      value: link.peerEvent?.kindLabel || "Unknown",
    })),
  ];

  const edges = inspector.related.map((link) => ({
    source: centerId,
    target: link.peerEvent?.eventId || `${link.linkType}-${link.direction}`,
    label: {
      show: true,
      formatter: link.linkLabel,
      color: "#A19A8B",
      fontSize: 10,
    },
    lineStyle: {
      color: link.confidencePct >= 80 ? "#7BC47F" : link.confidencePct >= 50 ? "#D3A35F" : "#D9776B",
      width: 1.5 + link.confidencePct / 40,
      opacity: 0.9,
    },
  }));

  return {
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: "#1A2126",
      borderColor: "#2B3640",
      textStyle: { color: "#F4F0E8" },
    },
    legend: {
      top: 0,
      textStyle: { color: "#A19A8B" },
      data: ["Selected", "File", "Network", "Other"],
    },
    series: [
      {
        type: "graph",
        layout: "force",
        roam: false,
        draggable: false,
        label: {
          show: true,
          color: "#F4F0E8",
          fontSize: 11,
        },
        force: {
          repulsion: 170,
          edgeLength: 110,
        },
        categories: [
          { name: "Selected", itemStyle: { color: "#9EC6B3" } },
          { name: "File", itemStyle: { color: "#D3A35F" } },
          { name: "Network", itemStyle: { color: "#7BC47F" } },
          { name: "Other", itemStyle: { color: "#A19A8B" } },
        ],
        data: nodes,
        links: edges,
      },
    ],
  };
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-tile">
      <div className="micro-label">{label}</div>
      <div className="mt-3 break-words text-sm leading-6 text-ink">{value}</div>
    </div>
  );
}

function DualCodeBlock({ json, yaml }: { json: string; yaml: string }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-[16px] border border-line bg-canvas p-4">
        <div className="micro-label">JSON</div>
        <pre className="mt-3 max-h-[320px] overflow-auto whitespace-pre-wrap break-all font-mono text-xs leading-6 text-accentSoft scroll-thin">
          {json}
        </pre>
      </div>
      <div className="rounded-[16px] border border-line bg-canvas p-4">
        <div className="micro-label">YAML</div>
        <pre className="mt-3 max-h-[320px] overflow-auto whitespace-pre-wrap break-all font-mono text-xs leading-6 text-ink scroll-thin">
          {yaml}
        </pre>
      </div>
    </div>
  );
}
