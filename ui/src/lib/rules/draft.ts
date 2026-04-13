import type { EvidenceInspectorView, RuleDraftView } from "../types/view-models";

export function buildRuleDraft(inspector: EvidenceInspectorView | null): RuleDraftView | null {
  if (!inspector) return null;
  const { event, related } = inspector;

  const conditions: RuleDraftView["conditions"] = [
    { field: "kind", operator: "eq", value: event.kind },
    { field: "actor", operator: "eq", value: event.actor },
    { field: "collector", operator: "eq", value: event.collector },
  ];

  const scope: Record<string, unknown> = {
    kind: event.kind,
    actor: event.actor,
    collector: event.collector,
    attribution_status: event.attributionStatus,
  };

  if (event.extensionId) {
    conditions.push({ field: "extension_id", operator: "eq", value: event.extensionId });
    scope.extension_id = event.extensionId;
  }
  if (event.scenarioName) {
    conditions.push({ field: "scenario_name", operator: "eq", value: event.scenarioName });
    scope.scenario_name = event.scenarioName;
  }
  if (event.kind === "network") {
    if (event.host) conditions.push({ field: "host", operator: "eq", value: event.host });
    if (event.protocol) conditions.push({ field: "protocol", operator: "eq", value: event.protocol });
    if (event.destinationIp) conditions.push({ field: "destination_ip", operator: "eq", value: event.destinationIp });
    if (typeof event.destinationPort === "number") {
      conditions.push({
        field: "destination_port",
        operator: "eq",
        value: event.destinationPort,
      });
    }
  }
  if (event.kind === "file") {
    if (event.operation) conditions.push({ field: "operation", operator: "eq", value: event.operation });
    if (event.path) conditions.push({ field: "path", operator: "contains", value: event.path });
    if (event.sensitive) conditions.push({ field: "sensitive", operator: "eq", value: true });
  }
  if (event.kind === "activation" && event.activationEvent) {
    conditions.push({
      field: "activation_event",
      operator: "eq",
      value: event.activationEvent,
    });
  }

  const topConfidence = related[0]?.confidence ?? 0.4;
  if (related.length) {
    scope.evidence_links = [...new Set(related.map((link) => link.linkType))];
  }
  if (event.attributionBasis) scope.attribution_basis = event.attributionBasis;
  if (event.attributionConfidence) scope.attribution_confidence = event.attributionConfidence;
  if (event.artifactClass) scope.artifact_class = event.artifactClass;

  const labels = [...new Set(
    [
      event.kind,
      event.actor,
      event.collector,
      ...(event.sensitive ? ["sensitive-path"] : []),
      event.attributionStatus,
      ...related.map((link) => link.linkType),
    ].filter(Boolean),
  )];

  const suspiciousReasons = [
    event.attributionBasis,
    event.noiseReason,
    ...related.slice(0, 3).map((link) => link.reason),
  ].filter(Boolean);

  return {
    title: `${event.kindLabel} Watch: ${event.artifactShort}`,
    severity:
      event.isTargetExtensionEvent && (event.sensitive || topConfidence >= 0.8)
        ? "high"
        : event.kind === "scenario"
          ? "low"
          : "medium",
    confidence: Number(topConfidence.toFixed(2)),
    scope,
    conditions,
    rationale: [event.summaryDisplay, ...related.slice(0, 3).map((link) => link.reason)].join(" "),
    labels,
    suspiciousReasons,
  };
}

export function toRuleJson(rule: RuleDraftView) {
  return JSON.stringify(rule, null, 2);
}

export function toRuleYaml(rule: RuleDraftView) {
  const lines: string[] = [];
  function write(value: unknown, indent = 0, label?: string) {
    const pad = " ".repeat(indent);
    if (Array.isArray(value)) {
      if (label) lines.push(`${pad}${label}:`);
      for (const item of value) {
        if (typeof item === "object" && item !== null) {
          lines.push(`${pad}-`);
          write(item, indent + 2);
        } else {
          lines.push(`${pad}- ${JSON.stringify(item)}`);
        }
      }
      return;
    }
    if (typeof value === "object" && value !== null) {
      if (label) lines.push(`${pad}${label}:`);
      for (const [key, nested] of Object.entries(value)) {
        write(nested, indent + (label ? 2 : 0), key);
      }
      return;
    }
    lines.push(`${pad}${label}: ${JSON.stringify(value)}`);
  }

  write(rule);
  return lines.join("\n");
}
