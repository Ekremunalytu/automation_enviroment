import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

import { ReactECharts } from "../../lib/charts/core";
import type { DetectionReportView, EvidenceInspectorView } from "../../lib/types/view-models";
import { Badge } from "../ui/Badge";
import { V3 } from "../v3";

export function ProvenanceTab({
  inspector,
  detection,
}: {
  inspector: EvidenceInspectorView;
  detection: DetectionReportView | null;
}) {
  const navigate = useNavigate();
  const suspicionBody = inspector.event.attributionBasis || inspector.event.noiseReason
    || "No explicit suspicion rationale was derived for this event.";
  const linkBody = inspector.related.length
    ? `${inspector.related.length} related evidence links are available in the Relations view.`
    : "No related evidence links are available for the selected event.";
  const eventFindings =
    detection?.findings.filter((finding) =>
      finding.evidence.some((evidence) => evidence.eventId === inspector.event.eventId),
    ) ?? [];
  const hitRules = Array.from(new Map(eventFindings.map((finding) => [finding.ruleId, { ruleId: finding.ruleId }])).values());
  return (
    <div className="space-y-4">
      <div>
        <div className="micro-label">Provenance</div>
        <h3 className="mt-3 text-xl font-semibold text-ink">Focused event context</h3>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-mute">
          Attribution metadata stays isolated here so the primary table and the relations graph do not compete for attention.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <Meta label="Timestamp" value={inspector.event.timestampDisplay} />
        <Meta label="Scenario" value={inspector.event.scenarioLabel} />
        <Meta label="Extension" value={inspector.event.extensionId || "(unattributed)"} />
        <Meta label="Attribution basis" value={inspector.event.attributionBasis || "(n/a)"} />
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

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <ContextBlock title="Link Status" body={linkBody} />
        <ContextBlock title="Why this is suspicious" body={suspicionBody} />
      </div>

      {hitRules.length ? (
        <section>
          <div className="micro-label">Hit rules · {hitRules.length}</div>
          <div className="mt-3 flex flex-col gap-2">
            {hitRules.map((rule) => (
              <button
                key={rule.ruleId}
                type="button"
                onClick={() => navigate(`/rules?rule=${encodeURIComponent(rule.ruleId)}&from=simulation`)}
                className="ghost-button justify-between"
              >
                <span className="font-mono text-xs">{rule.ruleId}</span>
                <span aria-hidden style={{ color: V3.ink4 }}>›</span>
              </button>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function ContextBlock({ title, body }: { title: string; body: string }) {
  return (
    <div style={{ borderTop: `1px solid ${V3.rule2}`, paddingTop: 12 }}>
      <div className="micro-label">{title}</div>
      <p style={{ marginTop: 6, color: V3.ink3, fontSize: 13, lineHeight: 1.6 }}>{body}</p>
    </div>
  );
}

export function RelationsTab({ inspector }: { inspector: EvidenceInspectorView }) {
  const clusters = buildRelationClusters(inspector);
  const visibleLinks = inspector.related.slice(0, 8);
  // Size the tree to its leaf count so rows never collapse on top of each other;
  // the dialog scrolls and the chart still supports roam/zoom for dense graphs.
  const leafRows = clusters.reduce(
    (sum, cluster) =>
      sum + cluster.kinds.reduce((s, kind) => s + kind.peers.length + (kind.hiddenPeers ? 1 : 0), 0),
    0,
  );
  const graphHeight = Math.min(640, Math.max(300, leafRows * 22 + 70));
  // echarts-for-react only re-fits on window resize, so a chart mounted inside the
  // dynamically-sized dialog lays its tree out against the wrong dimensions and
  // renders skewed until something triggers a resize (the user found zooming fixed
  // it). Observe the container and re-fit the instance whenever its box settles.
  const chartRef = useRef<{ resize: () => void } | null>(null);
  const chartHostRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const host = chartHostRef.current;
    if (!host || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => chartRef.current?.resize());
    observer.observe(host);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <div className="micro-label">Relations</div>
        <h3 className="mt-3 text-xl font-semibold text-ink">Interaction graph</h3>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-mute">
          Read the relation map as a hierarchy: selected event first, then relation groups, then target classes, then representative linked events.
        </p>
      </div>

      {inspector.related.length ? (
        <>
          <div className="rounded-none border border-line bg-panelAlt p-4">
            <div className="micro-label">Hierarchy Map</div>
            <div ref={chartHostRef} className="mt-3 w-full">
              <ReactECharts
                className="w-full"
                style={{ height: graphHeight }}
                option={buildRelationGraphOption(inspector)}
                onChartReady={(chart: { resize: () => void }) => {
                  chartRef.current = chart;
                  chart.resize();
                }}
              />
            </div>
          </div>

          <section className="space-y-3">
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
          </section>

          <section className="space-y-3">
            <div className="micro-label">Relation Groups</div>
            <div className="space-y-2">
              {clusters.map((cluster) => (
                <div key={cluster.key} className="metric-tile">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="text-sm font-medium text-ink">{cluster.heading}</div>
                      <div className="mt-1 text-sm leading-6 text-mute">
                        {cluster.kinds.map((kind) => `${kind.target} (${kind.count})`).join(" · ")}
                      </div>
                    </div>
                    <Badge tone="accent">{cluster.total}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-4">
              <div className="micro-label">Direct Links</div>
              {inspector.related.length > visibleLinks.length ? (
                <div className="text-xs text-mute">
                  Showing top {visibleLinks.length} of {inspector.related.length}
                </div>
              ) : null}
            </div>
            <div className="space-y-2">
              {visibleLinks.map((link) => (
                <div
                  key={`${link.direction}-${link.fromEventId}-${link.toEventId}-${link.linkType}`}
                  className="metric-tile"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="text-sm font-medium text-ink">
                        {link.direction === "incoming" ? "Incoming" : "Outgoing"} · {link.linkLabel}
                      </div>
                      <div className="mt-1 text-sm leading-6 text-mute">
                        {link.peerEvent?.artifactShort || "Unresolved event"} · {link.reason}
                      </div>
                    </div>
                    <Badge tone="accent">{link.confidenceLabel}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      ) : (
        <div className="rounded-none border border-dashed border-lineStrong px-4 py-5 text-sm text-mute">
          No explicit evidence links are available for the selected event.
        </div>
      )}
    </div>
  );
}

function buildRelationSummary(inspector: EvidenceInspectorView) {
  return buildRelationClusters(inspector)
    .flatMap((cluster) =>
      cluster.kinds.map((item) => ({
        label: cluster.label,
        target: item.target,
        reason: item.reason,
        confidence: item.confidence,
        count: item.count,
      })),
    )
    .map((item) => ({
      ...item,
      reason: item.count > 1 ? `${item.reason} (${item.count} linked events)` : item.reason,
    }));
}

function buildRelationClusters(inspector: EvidenceInspectorView) {
  const groups = new Map<
    string,
    {
      key: string;
      label: string;
      heading: string;
      total: number;
      kinds: Map<
        string,
        {
          target: string;
          count: number;
          confidence: number;
          reason: string;
          peers: Map<string, { name: string; count: number; confidence: number }>;
        }
      >;
    }
  >();

  for (const link of inspector.related) {
    const groupKey = `${link.direction}-${link.linkLabel}`;
    const heading = `${link.direction === "incoming" ? "Incoming" : "Outgoing"} · ${link.linkLabel}`;
    const cluster =
      groups.get(groupKey) ||
      {
        key: groupKey,
        label: link.linkLabel,
        heading,
        total: 0,
        kinds: new Map(),
      };

    cluster.total += 1;
    const target = link.peerEvent?.kindLabel || "Unknown";
    const kindBucket =
      cluster.kinds.get(target) ||
      {
        target,
        count: 0,
        confidence: 0,
        reason: link.reason,
        peers: new Map(),
      };

    kindBucket.count += 1;
    kindBucket.confidence = Math.max(kindBucket.confidence, link.confidencePct);
    const peerName = link.peerEvent?.artifactShort || "Unresolved event";
    const peer =
      kindBucket.peers.get(peerName) || {
        name: peerName,
        count: 0,
        confidence: 0,
      };
    peer.count += 1;
    peer.confidence = Math.max(peer.confidence, link.confidencePct);

    kindBucket.peers.set(peerName, peer);
    cluster.kinds.set(target, kindBucket);
    groups.set(groupKey, cluster);
  }

  return Array.from(groups.values()).map((cluster) => ({
    key: cluster.key,
    label: cluster.label,
    heading: cluster.heading,
    total: cluster.total,
    kinds: Array.from(cluster.kinds.values())
      .sort((left, right) => right.count - left.count || right.confidence - left.confidence)
      .map((kind) => ({
        target: kind.target,
        count: kind.count,
        confidence: kind.confidence,
        reason: kind.reason,
        peers: Array.from(kind.peers.values())
          .sort((left, right) => right.count - left.count || right.confidence - left.confidence)
          .slice(0, 6),
        hiddenPeers: Math.max(0, kind.peers.size - 6),
      })),
  }));
}

function buildRelationGraphOption(inspector: EvidenceInspectorView) {
  const hierarchy = {
    name: inspector.event.artifactShort,
    value: inspector.related.length,
    children: buildRelationClusters(inspector).map((cluster) => ({
      name: `${cluster.heading} (${cluster.total})`,
      value: cluster.total,
      children: cluster.kinds.map((kind) => ({
        name: `${kind.target} (${kind.count})`,
        value: kind.count,
        children: [
          ...kind.peers.map((peer) => ({
            name: peer.count > 1 ? `${peer.name} (${peer.count})` : peer.name,
            value: peer.count,
          })),
          ...(kind.hiddenPeers
            ? [
                {
                  name: `+${kind.hiddenPeers} more`,
                  value: kind.hiddenPeers,
                },
              ]
            : []),
        ],
      })),
    })),
  };

  return {
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: "#141414",
      borderColor: "#2b2b2b",
      textStyle: { color: "#f4f1ea" },
    },
    series: [
      {
        type: "tree",
        data: [hierarchy],
        top: "3%",
        left: "12%",
        bottom: "3%",
        right: "26%",
        orient: "LR",
        // Pan/zoom stays enabled. The skewed-until-you-zoom bug was the chart
        // initialising before the dialog settled its size; the ResizeObserver in
        // RelationsTab now re-fits the instance once the box is final, so it lands
        // correctly on open and the user can still roam.
        roam: true,
        initialTreeDepth: -1,
        symbol: "circle",
        symbolSize: 10,
        edgeShape: "polyline",
        edgeForkPosition: "32%",
        label: {
          show: true,
          position: "left",
          align: "right",
          verticalAlign: "middle",
          color: "#f4f1ea",
          fontSize: 11,
          formatter: (node: { name: string }) =>
            node.name.length > 30 ? `${node.name.slice(0, 29)}…` : node.name,
        },
        leaves: {
          label: {
            position: "right",
            align: "left",
            formatter: (node: { name: string }) =>
              node.name.length > 34 ? `${node.name.slice(0, 33)}…` : node.name,
          },
        },
        emphasis: {
          focus: "descendant",
        },
        itemStyle: {
          color: "#ff5c42",
          borderColor: "#2b2b2b",
          borderWidth: 1,
        },
        lineStyle: {
          color: "#5a5750",
          width: 1.5,
          curveness: 0.5,
        },
        expandAndCollapse: false,
        animationDuration: 300,
        animationDurationUpdate: 300,
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
