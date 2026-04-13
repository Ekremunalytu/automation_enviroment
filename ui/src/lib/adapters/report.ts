import type {
  ActivationEntryDto,
  ActivationReportDto,
  EvidenceEventDto,
  EvidenceLinkDto,
  FileEventDto,
  NetworkEventDto,
  ScenarioTraceDto,
} from "../types/contracts";
import type {
  ActivationReportView,
  EvidenceEventView,
  EvidenceInspectorView,
  EvidenceLinkView,
  ReportSummaryView,
} from "../types/view-models";

function labelize(value: string, fallback = "Unknown") {
  if (!value) return fallback;
  return value.replaceAll("_", " ").trim().replace(/\b\w/g, (part) => part.toUpperCase());
}

function short(value: string, width = 68) {
  if (!value) return "(none)";
  return value.length <= width ? value : `...${value.slice(-(width - 3))}`;
}

function formatTimestamp(value: string) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return value;
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    fractionalSecondDigits: 3,
    hour12: false,
  });
}

function formatEpoch(value?: number | null) {
  if (!value) return "";
  return new Date(value * 1000).toISOString();
}

function parseRelTime(value?: number | null) {
  if (typeof value !== "number" || Number.isNaN(value)) return null;
  return value;
}

function fromCanonicalEvent(event: EvidenceEventDto, index: number): EvidenceEventView {
  const artifact =
    event.path || event.host || event.destination_ip || event.extension_id || event.summary || "(no artifact)";
  const detail =
    event.activation_event || event.operation || event.protocol || event.collector || "(n/a)";
  return {
    eventId: event.event_id || `event-${index + 1}`,
    kind: event.kind || "event",
    kindLabel: labelize(event.kind || "event", "Event"),
    timestamp: event.timestamp || "",
    relTimeS: parseRelTime(event.rel_time_s),
    collector: event.collector || "unknown",
    collectorLabel: labelize(event.collector || "unknown"),
    actor: event.actor || "unknown",
    actorLabel: labelize(event.actor || "unknown"),
    scenarioName: event.scenario_name || "",
    scenarioLabel: event.scenario_name || "No scenario",
    extensionId: event.extension_id || "",
    activationEvent: event.activation_event || "",
    operation: event.operation || "",
    protocol: event.protocol || "",
    host: event.host || "",
    path: event.path || "",
    destinationIp: event.destination_ip || "",
    destinationPort: typeof event.destination_port === "number" ? event.destination_port : null,
    sensitive: Boolean(event.sensitive),
    summary: event.summary || "",
    summaryDisplay: event.summary || "(no summary)",
    artifact,
    artifactShort: short(artifact),
    detail,
    rawContext: event.raw_context || {},
    timestampDisplay: formatTimestamp(event.timestamp || ""),
  };
}

function fromActivation(entry: ActivationEntryDto, index: number): EvidenceEventView {
  return fromCanonicalEvent(
    {
      event_id: `activation-${String(index + 1).padStart(4, "0")}`,
      kind: "activation",
      timestamp: entry.timestamp || "",
      collector: entry.source || "log",
      actor: "extension",
      extension_id: entry.extension_id || "",
      activation_event: entry.activation_event || "",
      summary: `Activation ${entry.extension_id || "unknown"}${entry.activation_event ? ` via ${entry.activation_event}` : ""}`,
      raw_context: {
        duration_ms: entry.duration_ms ?? null,
        success: entry.success ?? true,
      },
    },
    index,
  );
}

function fromNetwork(entry: NetworkEventDto, index: number): EvidenceEventView {
  return fromCanonicalEvent(
    {
      event_id: `network-${String(index + 1).padStart(4, "0")}`,
      kind: "network",
      timestamp: entry.timestamp || "",
      rel_time_s: entry.rel_time_s ?? null,
      collector: "tshark",
      actor: "unknown",
      protocol: entry.protocol || "",
      host: entry.host || "",
      path: entry.path || "",
      destination_ip: entry.destination_ip || "",
      destination_port: entry.destination_port ?? null,
      summary: entry.summary || "",
      raw_context: {
        event_type: entry.event_type || "",
        source_ip: entry.source_ip || "",
      },
    },
    index,
  );
}

function fromFile(entry: FileEventDto, index: number): EvidenceEventView {
  return fromCanonicalEvent(
    {
      event_id: `file-${String(index + 1).padStart(4, "0")}`,
      kind: "file",
      timestamp: entry.timestamp || "",
      rel_time_s: entry.rel_time_s ?? null,
      collector: entry.observer || "unknown",
      actor: entry.source || "unknown",
      scenario_name: entry.scenario_name || "",
      extension_id: entry.related_extension_id || "",
      activation_event: entry.related_activation_event || "",
      operation: entry.operation || "",
      path: entry.path || "",
      sensitive: Boolean(entry.sensitive),
      summary: entry.summary || "",
      raw_context: {
        secondary_path: entry.secondary_path || "",
        flags: entry.flags || "",
      },
    },
    index,
  );
}

function fromScenario(entry: ScenarioTraceDto, index: number): EvidenceEventView {
  return fromCanonicalEvent(
    {
      event_id: `scenario-${String(index + 1).padStart(4, "0")}`,
      kind: "scenario",
      timestamp: formatEpoch(entry.started_at),
      collector: "automation",
      actor: "automation",
      scenario_name: entry.name || "",
      summary: `Scenario ${entry.name || "unknown"} ${entry.status || "running"}`,
      raw_context: {
        status: entry.status || "running",
        started_at: entry.started_at ?? null,
        ended_at: entry.ended_at ?? null,
      },
    },
    index,
  );
}

function buildLegacyEvents(report: ActivationReportDto) {
  const events: EvidenceEventView[] = [];
  for (const [index, entry] of (report.activated || []).entries()) events.push(fromActivation(entry, index));
  for (const [index, entry] of (report.network_events || []).entries()) events.push(fromNetwork(entry, index));
  for (const [index, entry] of (report.file_events || []).entries()) events.push(fromFile(entry, index));
  for (const [index, entry] of (report.scenario_traces || []).entries()) events.push(fromScenario(entry, index));
  return events;
}

function fromLink(link: EvidenceLinkDto): EvidenceLinkView {
  const confidence = typeof link.confidence === "number" ? link.confidence : 0;
  return {
    fromEventId: link.from_event_id || "",
    toEventId: link.to_event_id || "",
    linkType: link.link_type || "link",
    linkLabel: labelize(link.link_type || "link", "Link"),
    confidence,
    confidencePct: Math.round(confidence * 100),
    confidenceLabel: confidence >= 0.8 ? "High" : confidence >= 0.5 ? "Medium" : "Low",
    reason: link.reason || "",
  };
}

function buildLegacyLinks(events: EvidenceEventView[]) {
  const scenarioByName = new Map(
    events.filter((event) => event.kind === "scenario" && event.scenarioName).map((event) => [event.scenarioName, event.eventId]),
  );
  const activationByExtension = new Map(
    events.filter((event) => event.kind === "activation" && event.extensionId).map((event) => [event.extensionId, event.eventId]),
  );
  const links: EvidenceLinkView[] = [];

  for (const event of events) {
    if (event.kind !== "scenario" && event.scenarioName && scenarioByName.has(event.scenarioName)) {
      links.push(
        fromLink({
          from_event_id: event.eventId,
          to_event_id: scenarioByName.get(event.scenarioName) || "",
          link_type: "occurred_in_scenario",
          confidence: 1,
          reason: `Legacy report tagged event with scenario ${event.scenarioName}.`,
        }),
      );
    }
    if (event.kind === "file" && event.extensionId && activationByExtension.has(event.extensionId)) {
      links.push(
        fromLink({
          from_event_id: event.eventId,
          to_event_id: activationByExtension.get(event.extensionId) || "",
          link_type: "candidate_owner",
          confidence: 0.6,
          reason: "Legacy report linked file activity to an activation record.",
        }),
      );
    }
  }

  return links;
}

function buildSummary(report: ActivationReportDto, events: EvidenceEventView[]): ReportSummaryView {
  const summary = report.summary || {};
  return {
    totalEvents: events.length,
    totalActivated: Number(summary.total_activated ?? events.filter((event) => event.kind === "activation").length),
    uniqueExtensions: Number(
      summary.unique_extensions ??
        new Set(events.map((event) => event.extensionId).filter(Boolean)).size,
    ),
    scenariosRun: Array.isArray(summary.scenarios_run)
      ? summary.scenarios_run.map(String)
      : [...new Set(events.map((event) => event.scenarioName).filter(Boolean))],
    durationS: Number(summary.monitoring_duration_s ?? 0),
    networkEvents: Number(summary.network_events ?? events.filter((event) => event.kind === "network").length),
    fileEvents: Number(summary.file_events ?? events.filter((event) => event.kind === "file").length),
    sensitiveEvents: Number(
      summary.sensitive_file_events ?? events.filter((event) => event.sensitive).length,
    ),
  };
}

export function adaptReport(dto: ActivationReportDto, reportId: string): ActivationReportView {
  const evidence =
    dto.evidence_events?.length
      ? dto.evidence_events.map(fromCanonicalEvent)
      : buildLegacyEvents(dto);

  evidence.sort((left, right) => {
    const leftTime = left.relTimeS ?? Number.MAX_SAFE_INTEGER;
    const rightTime = right.relTimeS ?? Number.MAX_SAFE_INTEGER;
    if (leftTime !== rightTime) return leftTime - rightTime;
    return left.eventId.localeCompare(right.eventId);
  });

  const evidenceLinks =
    dto.evidence_links?.length
      ? dto.evidence_links.map(fromLink)
      : buildLegacyLinks(evidence);

  return {
    reportId,
    reportVersion: dto.report_version || 1,
    summary: buildSummary(dto, evidence),
    evidence,
    evidenceLinks,
    hostOutput: dto.extension_host_output || "",
    hostOutputLines: dto.extension_host_output_lines || 0,
    metadataFilename: dto._metadata?.filename || reportId,
  };
}

export function getInspectorView(report: ActivationReportView, eventId?: string | null): EvidenceInspectorView | null {
  const event = report.evidence.find((item) => item.eventId === eventId);
  if (!event) return null;
  const eventMap = new Map(report.evidence.map((item) => [item.eventId, item]));

  const outgoing = report.evidenceLinks
    .filter((link) => link.fromEventId === event.eventId)
    .map((link) => ({ ...link, peerEvent: eventMap.get(link.toEventId) }));
  const incoming = report.evidenceLinks
    .filter((link) => link.toEventId === event.eventId)
    .map((link) => ({ ...link, peerEvent: eventMap.get(link.fromEventId) }));

  const related = [
    ...outgoing.map((link) => ({ ...link, direction: "outgoing" as const })),
    ...incoming.map((link) => ({ ...link, direction: "incoming" as const })),
  ].sort((left, right) => right.confidence - left.confidence);

  return { event, outgoing, incoming, related };
}
