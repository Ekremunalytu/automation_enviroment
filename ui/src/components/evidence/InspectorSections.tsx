import { ReactECharts } from "../../lib/charts/core";
import type { DetectionReportView, EvidenceInspectorView, RuleDraftView } from "../../lib/types/view-models";
import { toRuleJson, toRuleYaml } from "../../lib/rules/draft";
import { Badge } from "../ui/Badge";
import { V3 } from "../v3";

function attributionTone(status: string) {
  if (status === "target_attributed") return "success";
  if (status === "near_target_activation" || status === "competing_candidate") return "warning";
  if (status === "automation_noise") return "danger";
  if (status === "corroboration") return "accent";
  return "default";
}

function severityTone(severity: string) {
  if (severity === "critical" || severity === "high") return "danger";
  if (severity === "medium") return "warning";
  return "default";
}

export function SelectedEventHero({ inspector }: { inspector: EvidenceInspectorView }) {
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
      <section className="panel-alt p-4">
        <div className="micro-label">Selected Event</div>
        <div className="mt-3 break-words text-[24px] font-semibold leading-tight text-ink">{inspector.event.artifactShort}</div>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-mute">{inspector.event.summaryDisplay}</p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Badge tone="accent">{inspector.event.kindLabel}</Badge>
          <Badge tone="cyan">{inspector.event.collectorLabel}</Badge>
          <Badge tone="lime">{inspector.event.actorLabel}</Badge>
          <Badge tone={attributionTone(inspector.event.attributionStatus)}>
            {inspector.event.attributionStatusLabel}
          </Badge>
          {inspector.event.attributionConfidencePct ? (
            <Badge tone={inspector.event.attributionConfidencePct >= 80 ? "success" : inspector.event.attributionConfidencePct >= 50 ? "warning" : "default"}>
              {inspector.event.attributionConfidencePct}%
            </Badge>
          ) : null}
          {inspector.event.artifactClass ? <Badge tone="amber">{inspector.event.artifactClass.replaceAll("_", " ")}</Badge> : null}
          {inspector.event.sensitive ? <Badge tone="rose">Sensitive</Badge> : null}
        </div>
      </section>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
        <Meta label="Scenario" value={inspector.event.scenarioLabel} />
        <Meta label="Linked Events" value={String(inspector.related.length)} />
        <Meta label="Attribution" value={inspector.event.attributionStatusLabel} />
        <Meta
          label="Confidence"
          value={inspector.event.attributionConfidencePct ? `${inspector.event.attributionConfidencePct}%` : "Unscored"}
        />
      </div>
    </div>
  );
}

export function ProvenanceTab({ inspector }: { inspector: EvidenceInspectorView }) {
  const suspicionBody = inspector.event.attributionBasis || inspector.event.noiseReason
    || "No explicit suspicion rationale was derived for this event.";
  const linkBody = inspector.related.length
    ? `${inspector.related.length} related evidence links are available in the Relations view.`
    : "No related evidence links are available for the selected event.";
  return (
    <div className="space-y-4">
      <div>
        <div className="micro-label">Provenance</div>
        <h3 className="mt-3 text-xl font-semibold text-ink">Focused event context</h3>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-mute">
          Attribution metadata stays isolated here so the primary table and the relations graph do not compete for attention.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
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
            <ReactECharts className="mt-3 h-[260px] w-full" option={buildRelationGraphOption(inspector)} />
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

export function RulesTab({ ruleDraft }: { ruleDraft: RuleDraftView | null }) {
  if (!ruleDraft) {
    return (
      <div className="text-sm leading-6 text-mute">Select an event to generate a portable rule draft.</div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <div className="micro-label">Rule Draft</div>
        <h3 className="mt-3 text-xl font-semibold text-ink">Portable detection draft</h3>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-mute">
          Generate a shareable rule from the focused evidence without burying labels and conditions in the side column.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Meta label="Title" value={ruleDraft.title} />
        <Meta label="Severity" value={ruleDraft.severity.toUpperCase()} />
        <Meta label="Confidence" value={`${Math.round(ruleDraft.confidence * 100)}%`} />
        <Meta label="Conditions" value={String(ruleDraft.conditions.length)} />
      </div>

      <section className="panel-alt p-4">
        <div className="micro-label">Rule Export</div>
        <p className="mt-3 text-sm leading-6 text-mute">{ruleDraft.rationale}</p>
      </section>

      <section className="panel-alt p-4">
        <div className="micro-label">Why This Is Suspicious</div>
        <div className="mt-3 space-y-2 text-sm leading-6 text-mute">
          {ruleDraft.suspiciousReasons.length ? (
            ruleDraft.suspiciousReasons.map((reason) => <div key={reason}>{reason}</div>)
          ) : (
            <div>No additional suspicion rationale was derived.</div>
          )}
        </div>
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
        <div className="mt-3 grid gap-2 lg:grid-cols-2">
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
  );
}

export function RuleHitsTab({
  detection,
  inspector,
}: {
  detection: DetectionReportView | null;
  inspector: EvidenceInspectorView;
}) {
  const eventId = inspector.event.eventId;
  const eventFindings =
    detection?.findings.filter((finding) =>
      finding.evidence.some((evidence) => evidence.eventId === eventId),
    ) ?? [];
  const hitRuleIds = new Set(eventFindings.map((finding) => finding.ruleId));
  const rules = detection?.rulesExecuted ?? [];

  return (
    <div className="space-y-5">
      <section>
        <div className="micro-label">Rules</div>
        <h3 className="mt-3 text-xl font-semibold text-ink">Rule registry</h3>
        <div
          style={{
            marginTop: 12,
            border: `1px dashed ${V3.rule2}`,
            background: V3.paper2,
            padding: "16px 18px",
            color: V3.ink3,
            fontSize: 13,
            lineHeight: 1.6,
          }}
        >
          The full detection rule catalog will plug in here. This space is reserved as a placeholder for the upcoming registry + hits view.
        </div>
      </section>

      <section className="space-y-3">
        <div className="micro-label">Selected event hits</div>
        {eventFindings.length ? (
          <div className="space-y-2">
            {eventFindings.map((finding) => (
              <div key={finding.id} className="metric-tile">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="break-words text-sm font-medium text-ink">{finding.title}</div>
                    <div className="mt-1 break-all font-mono text-xs text-mute">{finding.ruleId}</div>
                  </div>
                  <Badge tone={severityTone(finding.severity)}>{finding.severityLabel}</Badge>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-none border border-line bg-panelAlt/50 px-4 py-4 text-sm leading-6 text-mute">
            No fired rule references this selected event.
          </div>
        )}
      </section>

      <section className="space-y-3">
        <div className="micro-label">Rule executions</div>
        {!detection ? (
          <div className="rounded-none border border-dashed border-lineStrong px-4 py-5 text-sm leading-6 text-mute">
            Detection rule execution data is unavailable for this report.
          </div>
        ) : rules.length ? (
          <div className="space-y-2">
            {rules.map((rule) => {
              const fired = rule.status === "fired";
              const linkedToSelection = hitRuleIds.has(rule.ruleId);
              return (
                <div
                  key={`${rule.ruleId}-${rule.ruleVersion}`}
                  className={`metric-tile ${linkedToSelection ? "border-accent" : ""}`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="break-all font-mono text-sm text-ink">{rule.ruleId}</div>
                      <div className="mt-1 font-mono text-xs text-mute">
                        v{rule.ruleVersion} · {rule.lifecycle.replaceAll("_", " ")}
                      </div>
                      {rule.errorDetail ? (
                        <div className="mt-2 text-sm leading-6 text-danger">{rule.errorDetail}</div>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap justify-end gap-2">
                      <Badge tone={rule.status === "error" ? "danger" : fired ? "success" : "default"}>
                        {rule.statusLabel}
                      </Badge>
                      <Badge tone={fired ? "accent" : "default"}>
                        {rule.findingIds.length} hit{rule.findingIds.length === 1 ? "" : "s"}
                      </Badge>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="rounded-none border border-line bg-panelAlt/50 px-4 py-4 text-sm leading-6 text-mute">
            No rule execution records were attached to this detection report yet.
          </div>
        )}
      </section>
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
        top: "4%",
        left: "8%",
        bottom: "4%",
        right: "28%",
        orient: "LR",
        roam: true,
        symbol: "circle",
        symbolSize: 12,
        edgeShape: "polyline",
        edgeForkPosition: "32%",
        label: {
          show: true,
          position: "left",
          align: "right",
          verticalAlign: "middle",
          color: "#f4f1ea",
          fontSize: 11,
        },
        leaves: {
          label: {
            position: "right",
            align: "left",
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

function DualCodeBlock({ json, yaml }: { json: string; yaml: string }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-none border border-line bg-canvas p-4">
        <div className="micro-label">JSON</div>
        <pre className="mt-3 max-h-[320px] overflow-auto whitespace-pre-wrap break-all font-mono text-xs leading-6 text-accentSoft scroll-thin">
          {json}
        </pre>
      </div>
      <div className="rounded-none border border-line bg-canvas p-4">
        <div className="micro-label">YAML</div>
        <pre className="mt-3 max-h-[320px] overflow-auto whitespace-pre-wrap break-all font-mono text-xs leading-6 text-ink scroll-thin">
          {yaml}
        </pre>
      </div>
    </div>
  );
}
