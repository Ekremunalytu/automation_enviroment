import type {
  AnalysisBundleDto,
  ActivationEntryDto,
  AutomationHealthDto,
  ActivationReportDto,
  AttributionSummaryDto,
  CoverageCapabilityDto,
  CoverageSummaryDto,
  CoverageTrackDto,
  EventAttemptDto,
  EventCoverageDto,
  EvidenceEventDto,
  EvidenceRefDto,
  EvidenceLinkDto,
  FileEventDto,
  LogHealthDto,
  LogStreamEntryDto,
  DetectionFindingDto,
  DetectionReportDto,
  PrerequisiteResultDto,
  NetworkEventDto,
  ProcessEventDto,
  RuleExecutionRecordDto,
  RiskSignalDto,
  RiskSummaryDto,
  ScenarioTraceDto,
  SkippedScenarioRecordDto,
  StimulusPassDto,
} from "../types/contracts";
import type {
  ActivationReportView,
  AttributionSummaryView,
  CoverageCapabilityView,
  CoverageSummaryView,
  CoverageTrackView,
  CoverageTracksView,
  DetectionEvidenceRefView,
  DetectionFindingView,
  DetectionReportView,
  EventAttemptView,
  EventCoverageView,
  EvidenceEventView,
  EvidenceInspectorView,
  EvidenceLinkView,
  LogEntryView,
  LogStreamsView,
  PrerequisiteResultView,
  RiskSignalView,
  RiskSummaryView,
  RuleExecutionRecordView,
  ReportSummaryView,
  StimulusPassView,
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

function parseAttributionConfidence(value?: number | null) {
  if (typeof value !== "number" || Number.isNaN(value)) return 0;
  return Number(value.toFixed(2));
}

function normalizeRunQuality(value: unknown): ReportSummaryView["runQuality"] {
  return value === "high" ||
    value === "medium" ||
    value === "low" ||
    value === "inconclusive"
    ? value
    : "inconclusive";
}

function normalizeAutomationHealthStatus(
  value: unknown,
): ReportSummaryView["automationHealthStatus"] {
  return value === "healthy" || value === "degraded" || value === "inconclusive"
    ? value
    : "inconclusive";
}

function buildAutomationHealth(
  dto?: AutomationHealthDto | null,
  summary?: Record<string, unknown>,
): {
  status: ReportSummaryView["automationHealthStatus"];
  reasons: string[];
  triggerRequested: boolean;
  triggerLoaded: boolean;
  triggerApplied: boolean;
  extensionHostLogPresent: boolean;
  extensionHostOutputPresent: boolean;
  targetStreamPresent: boolean;
  targetActivationCount: number;
  failedScenarios: string[];
  skippedScenarios: string[];
  legacyHealthFallback: boolean;
} {
  const legacySummary =
    typeof summary?.automation_health === "object" && summary.automation_health
      ? (summary.automation_health as AutomationHealthDto)
      : undefined;
  const source = dto || legacySummary;
  if (!source) {
    return {
      status: "inconclusive",
      reasons: ["legacy_report_missing_health_block"],
      triggerRequested: false,
      triggerLoaded: false,
      triggerApplied: false,
      extensionHostLogPresent: false,
      extensionHostOutputPresent: false,
      targetStreamPresent: false,
      targetActivationCount: 0,
      failedScenarios: [],
      skippedScenarios: [],
      legacyHealthFallback: true,
    };
  }
  return {
    status: normalizeAutomationHealthStatus(source.status),
    reasons: Array.isArray(source.reasons) ? source.reasons.map(String) : [],
    triggerRequested: Boolean(source.trigger_requested),
    triggerLoaded: Boolean(source.trigger_loaded),
    triggerApplied: Boolean(source.trigger_applied),
    extensionHostLogPresent: Boolean(source.extension_host_log_present),
    extensionHostOutputPresent: Boolean(source.extension_host_output_present),
    targetStreamPresent: Boolean(source.target_stream_present),
    targetActivationCount: Number(source.target_activation_count ?? 0),
    failedScenarios: Array.isArray(source.failed_scenarios)
      ? source.failed_scenarios.map(String)
      : [],
    skippedScenarios: Array.isArray(source.skipped_scenarios)
      ? source.skipped_scenarios.map(String)
      : [],
    legacyHealthFallback: false,
  };
}

function buildLogHealth(
  dto?: LogHealthDto | null,
  summary?: Record<string, unknown>,
): {
  extensionHostLogFound: boolean;
  extensionHostOutputPresent: boolean;
  targetExtensionLogEntries: number;
  totalActivationEntries: number;
} {
  const legacySummary =
    typeof summary?.log_health === "object" && summary.log_health
      ? (summary.log_health as LogHealthDto)
      : undefined;
  const source = dto || legacySummary;
  return {
    extensionHostLogFound: Boolean(source?.extension_host_log_found),
    extensionHostOutputPresent: Boolean(source?.extension_host_output_present),
    targetExtensionLogEntries: Number(source?.target_extension_log_entries ?? 0),
    totalActivationEntries: Number(source?.total_activation_entries ?? 0),
  };
}

function fromCanonicalEvent(event: EvidenceEventDto, index: number): EvidenceEventView {
  const artifact =
    event.path || event.host || event.destination_ip || event.extension_id || event.summary || "(no artifact)";
  const detail =
    event.activation_event || event.operation || event.protocol || event.collector || "(n/a)";
  const attributionStatus = event.attribution_status || "unattributed";
  const attributionConfidence = parseAttributionConfidence(event.attribution_confidence);
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
    attributionStatus,
    attributionStatusLabel: labelize(attributionStatus, "Unattributed"),
    attributionBasis: event.attribution_basis || "",
    attributionConfidence,
    attributionConfidencePct: Math.round(attributionConfidence * 100),
    isTargetExtensionEvent: Boolean(event.is_target_extension_event),
    noiseReason: event.noise_reason || "",
    artifactClass: event.artifact_class || "",
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
      extension_id: entry.related_extension_id || "",
      activation_event: entry.related_activation_event || "",
      attribution_status: entry.attribution_status || "unattributed",
      attribution_basis: entry.attribution_basis || "",
      attribution_confidence: entry.attribution_confidence ?? 0,
      is_target_extension_event: entry.is_target_extension_event ?? false,
      noise_reason: entry.noise_reason || "",
      summary: entry.summary || "",
      raw_context: {
        event_type: entry.event_type || "",
        source_ip: entry.source_ip || "",
        http_method: entry.http_method || "",
        http_status_code: entry.http_status_code ?? null,
        http_content_type: entry.http_content_type || "",
        request_body_sha256: entry.request_body_sha256 || "",
        request_body_preview: entry.request_body_preview || "",
        request_body_truncated: Boolean(entry.request_body_truncated),
        response_body_sha256: entry.response_body_sha256 || "",
        response_body_preview: entry.response_body_preview || "",
        response_body_truncated: Boolean(entry.response_body_truncated),
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
      attribution_status: entry.attribution_status || "unattributed",
      attribution_basis: entry.attribution_basis || "",
      attribution_confidence: entry.attribution_confidence ?? 0,
      is_target_extension_event: entry.is_target_extension_event ?? false,
      noise_reason: entry.noise_reason || "",
      artifact_class: entry.artifact_class || "",
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

function fromProcess(entry: ProcessEventDto, index: number): EvidenceEventView {
  return fromCanonicalEvent(
    {
      event_id: `process-${String(index + 1).padStart(4, "0")}`,
      kind: "process",
      timestamp: entry.timestamp || "",
      rel_time_s: entry.rel_time_s ?? null,
      collector: "strace",
      actor: entry.is_target_extension_event ? "extension" : "unknown",
      extension_id: entry.related_extension_id || "",
      activation_event: entry.related_activation_event || "",
      operation: entry.operation || "",
      attribution_status: entry.attribution_status || "unattributed",
      attribution_basis: entry.attribution_basis || "",
      attribution_confidence: entry.attribution_confidence ?? 0,
      is_target_extension_event: entry.is_target_extension_event ?? false,
      summary: entry.summary || "",
      raw_context: {
        pid: entry.pid ?? null,
        ppid: entry.ppid ?? null,
        command: entry.command || "",
        arguments_preview: entry.arguments_preview || "",
        cwd: entry.cwd || "",
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
  for (const [index, entry] of (report.process_events || []).entries()) events.push(fromProcess(entry, index));
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
  const automationHealth = buildAutomationHealth(report.automation_health, summary);
  const logHealth = buildLogHealth(report.log_health, summary);
  const signalSummary =
    typeof summary.signal_summary === "object" && summary.signal_summary
      ? (summary.signal_summary as Record<string, unknown>)
      : {};
  const signalSummaryLevel =
    typeof signalSummary.level === "string" ? signalSummary.level : "needs_review";
  const officialAttempted = Array.isArray(summary.attempted_capabilities)
    ? summary.attempted_capabilities.map(String)
    : Array.isArray(report.official_attempted_capabilities)
      ? report.official_attempted_capabilities.map(String)
      : Array.isArray(report.attempted_capabilities)
        ? report.attempted_capabilities.map(String)
      : [];
  const officialVerified = Array.isArray(summary.verified_capabilities)
    ? summary.verified_capabilities.map(String)
    : Array.isArray(report.official_verified_capabilities)
      ? report.official_verified_capabilities.map(String)
      : Array.isArray(report.verified_capabilities)
        ? report.verified_capabilities.map(String)
      : [];
  const skippedScenarioDetails = Array.isArray(report.skipped_scenarios)
    ? report.skipped_scenarios
        .map((entry: SkippedScenarioRecordDto) => ({
          name: String(entry?.name || ""),
          reasonCode: String(entry?.reason_code || ""),
          detail: String(entry?.detail || ""),
        }))
        .filter((entry) => entry.name && entry.reasonCode)
    : [];
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
    attemptedCapabilities: officialAttempted,
    verifiedCapabilities: officialVerified,
    uiBlockerCount: Number(summary.ui_blocker_count ?? report.log_streams?.ui_blockers?.length ?? 0),
    targetExtensionExpected: String(
      summary.target_extension_expected ?? report.target_extension_expected ?? "",
    ),
    targetExtensionObserved: Boolean(
      summary.target_extension_observed ?? report.target_extension_observed ?? false,
    ),
    triggerPlanApplied: Boolean(
      summary.trigger_plan_applied ?? report.trigger_plan_applied ?? false,
    ),
    triggerRequested: automationHealth.triggerRequested,
    triggerLoaded: automationHealth.triggerLoaded,
    verificationGap: Number(
      summary.verification_gap ?? report.verification_gap ?? 0,
    ),
    runQuality: normalizeRunQuality(summary.run_quality ?? report.run_quality),
    automationHealthStatus: automationHealth.status,
    automationHealthReasons: automationHealth.reasons,
    failedScenarios: automationHealth.failedScenarios,
    skippedScenarios: skippedScenarioDetails.length
      ? skippedScenarioDetails.map((entry) => entry.name)
      : automationHealth.skippedScenarios,
    skippedScenarioDetails,
    extensionHostLogPresent: automationHealth.extensionHostLogPresent,
    extensionHostLogFound: logHealth.extensionHostLogFound,
    extensionHostOutputPresent: automationHealth.extensionHostOutputPresent,
    targetStreamPresent: automationHealth.targetStreamPresent,
    targetActivationCount: automationHealth.targetActivationCount,
    legacyHealthFallback: automationHealth.legacyHealthFallback,
    signalSummaryLevel:
      signalSummaryLevel === "benign" ||
      signalSummaryLevel === "needs_review" ||
      signalSummaryLevel === "suspicious" ||
      signalSummaryLevel === "likely_malicious"
        ? signalSummaryLevel
        : "needs_review",
    signalSummaryScore: Number(signalSummary.score ?? 0),
    signalSummaryReasons: Array.isArray(signalSummary.reasons)
      ? signalSummary.reasons.map(String)
      : [],
    signalSummaryNote: typeof signalSummary.note === "string" ? signalSummary.note : "",
  };
}

function buildAttributionSummary(
  summary?: AttributionSummaryDto | null,
): AttributionSummaryView {
  return {
    targetActivationCount: Number(summary?.target_activation_count ?? 0),
    strongTargetFileEventCount: Number(summary?.strong_target_file_event_count ?? 0),
    strongTargetNetworkEventCount: Number(summary?.strong_target_network_event_count ?? 0),
    correlatedOnlyEventCount: Number(summary?.correlated_only_event_count ?? 0),
    targetBackgroundActivationCount: Number(
      summary?.target_background_activation_count ?? 0,
    ),
    competingExtensionEventCount: Number(
      summary?.competing_extension_event_count ?? 0,
    ),
    uiBlockerCount: Number(summary?.ui_blocker_count ?? 0),
  };
}

function buildCoverageSummary(
  summary?: CoverageSummaryDto | null,
  matrix: CoverageCapabilityDto[] = [],
): CoverageSummaryView {
  const fallbackMissing = matrix.filter((entry) => entry.status === "missing").map((entry) => entry.capability);
  return {
    covered: Number(summary?.covered ?? matrix.filter((entry) => entry.status === "covered").length),
    partial: Number(summary?.partial ?? matrix.filter((entry) => entry.status === "partial").length),
    missing: Number(summary?.missing ?? fallbackMissing.length),
    attempted: Number(summary?.attempted ?? 0),
    verified: Number(summary?.verified ?? 0),
    missingCapabilities: Array.isArray(summary?.missing_capabilities) ? summary?.missing_capabilities.map(String) : fallbackMissing,
    attemptedCapabilities: Array.isArray(summary?.attempted_capabilities) ? summary?.attempted_capabilities.map(String) : [],
    verifiedCapabilities: Array.isArray(summary?.verified_capabilities) ? summary?.verified_capabilities.map(String) : [],
  };
}

function fromCoverageCapability(entry: CoverageCapabilityDto): CoverageCapabilityView {
  const supportStatus = entry.support_status || entry.status || "unknown";
  const verificationStatus =
    entry.verification_status ||
    (entry.verified ? "verified" : entry.attempted ? "attempted_only" : "not_attempted");
  return {
    capability: entry.capability,
    capabilityLabel: labelize(entry.capability, "Capability"),
    status: verificationStatus,
    statusLabel: labelize(verificationStatus, "Unknown"),
    track: entry.track || "official",
    source: entry.source || "",
    supportStatus,
    supportStatusLabel: labelize(supportStatus, "Unknown"),
    verificationStatus,
    verificationStatusLabel: labelize(verificationStatus, "Unknown"),
    selectedScenarios: Array.isArray(entry.selected_scenarios) ? entry.selected_scenarios.map(String) : [],
    supportedScenarios: Array.isArray(entry.supported_scenarios) ? entry.supported_scenarios.map(String) : [],
    notes: entry.notes || "",
    attempted: Boolean(entry.attempted),
    verified: Boolean(entry.verified),
  };
}

function buildCoverageTrack(
  track?: CoverageTrackDto | null,
  fallbackSummary?: CoverageSummaryDto | null,
  fallbackMatrix: CoverageCapabilityDto[] = [],
): CoverageTrackView {
  const matrix = Array.isArray(track?.matrix) ? track.matrix : fallbackMatrix;
  return {
    source: track?.source || "",
    selectedScenarios: Array.isArray(track?.selected_scenarios)
      ? track.selected_scenarios.map(String)
      : [],
    summary: buildCoverageSummary(track?.summary || fallbackSummary, matrix),
    matrix: matrix.map(fromCoverageCapability),
  };
}

function buildCoverageTracks(dto: ActivationReportDto): CoverageTracksView {
  return {
    official: buildCoverageTrack(
      dto.coverage_tracks?.official,
      dto.coverage_summary,
      dto.coverage_matrix || [],
    ),
    heuristic: buildCoverageTrack(dto.coverage_tracks?.heuristic, undefined, []),
  };
}

function fromLogEntry(entry: LogStreamEntryDto): LogEntryView {
  return {
    timestamp: entry.timestamp || "",
    timestampDisplay: formatTimestamp(entry.timestamp || ""),
    relTimeS: parseRelTime(entry.rel_time_s),
    stream: entry.stream || "unknown",
    kind: entry.kind || "log",
    kindLabel: labelize(entry.kind || "log", "Log"),
    message: entry.message || "",
    extensionId: entry.extension_id || "",
    activationEvent: entry.activation_event || "",
    scenarioName: entry.scenario_name || "",
    status: entry.status || "",
    statusLabel: labelize(entry.status || "unknown", "Unknown"),
    isTargetExtension: Boolean(entry.is_target_extension),
  };
}

function fromRiskSignal(entry: RiskSignalDto, index: number): RiskSignalView {
  const confidence = parseAttributionConfidence(entry.confidence);
  return {
    signalId: entry.signal_id || `signal-${index + 1}`,
    category: entry.category || "risk_signal",
    categoryLabel: labelize(entry.category || "risk_signal", "Risk Signal"),
    severity: entry.severity || "medium",
    severityLabel: labelize(entry.severity || "medium", "Medium"),
    confidence,
    confidencePct: Math.round(confidence * 100),
    evidenceEventIds: Array.isArray(entry.evidence_event_ids) ? entry.evidence_event_ids.map(String) : [],
    summary: entry.summary || "",
  };
}

function buildRiskSummary(summary?: RiskSummaryDto | null): RiskSummaryView {
  return {
    totalSignals: Number(summary?.total_signals ?? 0),
    critical: Number(summary?.critical ?? 0),
    high: Number(summary?.high ?? 0),
    medium: Number(summary?.medium ?? 0),
    low: Number(summary?.low ?? 0),
    categories: Array.isArray(summary?.categories) ? summary?.categories.map(String) : [],
  };
}

function buildLogStreams(dto: ActivationReportDto): LogStreamsView {
  return {
    targetExtensionHost: (dto.log_streams?.target_extension_host || []).map(fromLogEntry),
    otherExtensionHost: (dto.log_streams?.other_extension_host || []).map(fromLogEntry),
    automation: (dto.log_streams?.automation || []).map(fromLogEntry),
    uiBlockers: (dto.log_streams?.ui_blockers || []).map(fromLogEntry),
  };
}

function fromStimulusPass(entry: StimulusPassDto): StimulusPassView {
  return {
    passId: entry.pass_id || "",
    label: entry.label || entry.pass_id || "",
    order: Number(entry.order ?? 0),
    startedAt: typeof entry.started_at === "number" ? entry.started_at : null,
    endedAt: typeof entry.ended_at === "number" ? entry.ended_at : null,
    status: entry.status || "planned",
    triggerMethod: entry.trigger_method || "",
  };
}

function fromPrerequisiteResult(entry: PrerequisiteResultDto): PrerequisiteResultView {
  return {
    prerequisiteId: entry.prerequisite_id || "",
    key: entry.key || "",
    label: entry.label || entry.key || "",
    status: entry.status || "planned",
    materializer: entry.materializer || "",
    passName: entry.pass_name || "",
    attemptIds: Array.isArray(entry.attempt_ids) ? entry.attempt_ids.map(String) : [],
    detail: entry.detail || "",
  };
}

function fromEventAttempt(entry: EventAttemptDto): EventAttemptView {
  const status = entry.status || "planned";
  const verificationStatus = entry.verification_status || "not_attempted";
  return {
    attemptId: entry.attempt_id || "",
    declaredEvent: entry.declared_event || entry.activation_event || "",
    activationEvent: entry.activation_event || "",
    eventFamily: entry.event_family || "",
    eventValue: entry.event_value || "",
    track: entry.track || "official",
    selectedBy: entry.selected_by || "",
    selectionReasons: Array.isArray(entry.selection_reasons) ? entry.selection_reasons.map(String) : [],
    passName: entry.pass_name || "",
    backfillPassName: entry.backfill_pass_name || "",
    prerequisiteKeys: Array.isArray(entry.prerequisite_keys) ? entry.prerequisite_keys.map(String) : [],
    verificationContract: Array.isArray(entry.verification_contract) ? entry.verification_contract.map(String) : [],
    triggerMethod: entry.trigger_method || "",
    fallbackTriggerMethod: entry.fallback_trigger_method || "",
    executorAction: entry.executor_action || "",
    backfillExecutorAction: entry.backfill_executor_action || "",
    legacyScenarios: Array.isArray(entry.legacy_scenarios) ? entry.legacy_scenarios.map(String) : [],
    capabilityTags: Array.isArray(entry.capability_tags) ? entry.capability_tags.map(String) : [],
    status,
    statusLabel: labelize(status, "Planned"),
    triggerMethodUsed: entry.trigger_method_used || "",
    attemptedPasses: Array.isArray(entry.attempted_passes) ? entry.attempted_passes.map(String) : [],
    evidence: Array.isArray(entry.evidence) ? entry.evidence.map(String) : [],
    verificationStatus,
    verificationStatusLabel: labelize(verificationStatus, "Not Attempted"),
    failureReasonCode: entry.failure_reason_code || "",
    blockedReasonCode: entry.blocked_reason_code || "",
    resultDetails: entry.result_details || "",
    official: Boolean(entry.official),
    heuristic: Boolean(entry.heuristic),
    uiPath: entry.ui_path || "",
    harnessFallback: entry.harness_fallback || "",
  };
}

function buildEventCoverage(summary?: EventCoverageDto | null): EventCoverageView {
  return {
    track: summary?.track || "official",
    declared: Number(summary?.declared ?? 0),
    verified: Number(summary?.verified ?? 0),
    attemptedOnly: Number(summary?.attempted_only ?? 0),
    failed: Number(summary?.failed ?? 0),
    blocked: Number(summary?.blocked ?? 0),
    unresolved: Number(summary?.unresolved ?? 0),
    declaredEvents: Array.isArray(summary?.declared_events) ? summary?.declared_events.map(String) : [],
  };
}

function buildDetectionEvidenceRef(ref: EvidenceRefDto): DetectionEvidenceRefView {
  return {
    eventId: ref.event_id || "",
    type: ref.type || "event",
    summary: ref.summary || ref.event_id || "Linked evidence event",
  };
}

function buildDetectionFinding(finding: DetectionFindingDto): DetectionFindingView {
  return {
    id: finding.id || "",
    ruleId: finding.rule_id || "",
    ruleVersion: finding.rule_version || "",
    ruleLifecycle: finding.rule_lifecycle || "draft",
    title: finding.title || "",
    description: finding.description || "",
    categories: Array.isArray(finding.categories) ? finding.categories.map(String) : [],
    severity: finding.severity || "info",
    severityLabel: labelize(finding.severity, "Unknown"),
    confidence: finding.confidence || "low",
    confidenceLabel: labelize(finding.confidence, "Unknown"),
    adversaryClass: finding.adversary_class || "N/A",
    evidence: (finding.evidence || []).map(buildDetectionEvidenceRef),
    mitigationHint: finding.mitigation_hint || "",
  };
}

function buildRuleExecutionRecord(record: RuleExecutionRecordDto): RuleExecutionRecordView {
  return {
    ruleId: record.rule_id || "",
    ruleVersion: record.rule_version || "",
    lifecycle: record.lifecycle || "draft",
    status: record.status || "silent",
    statusLabel: labelize(record.status || "silent", "Unknown"),
    findingIds: Array.isArray(record.finding_ids) ? record.finding_ids.map(String) : [],
    errorDetail: record.error_detail || "",
  };
}

function buildDetectionReport(
  dto?: DetectionReportDto | null,
): DetectionReportView | null {
  if (!dto) return null;
  return {
    verdict: dto.verdict,
    verdictLabel: labelize(dto.verdict, "Unknown"),
    verdictRationale: dto.verdict_rationale || "",
    findings: (dto.findings || []).map(buildDetectionFinding),
    rulesExecuted: (dto.rules_executed || []).map(buildRuleExecutionRecord),
  };
}

export function adaptReport(dto: ActivationReportDto, reportId: string): ActivationReportView {
  const summary = dto.summary || {};
  const coverageTracks = buildCoverageTracks(dto);
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
    detection: null,
    attributionSummary: buildAttributionSummary(
      dto.attribution_summary ||
        (typeof summary["attribution_summary"] === "object"
          ? (summary["attribution_summary"] as AttributionSummaryDto)
          : undefined),
    ),
    riskSignals: (dto.risk_signals || []).map(fromRiskSignal),
    riskSummary: buildRiskSummary(
      dto.risk_summary ||
        (typeof summary["risk_summary"] === "object"
          ? (summary["risk_summary"] as RiskSummaryDto)
          : undefined),
    ),
    coverageSummary: coverageTracks.official.summary,
    coverageMatrix: coverageTracks.official.matrix,
    coverageTracks,
    stimulusPasses: (dto.stimulus_passes || []).map(fromStimulusPass),
    prerequisiteResults: (dto.prerequisite_results || []).map(fromPrerequisiteResult),
    eventAttempts: (dto.event_attempts || []).map(fromEventAttempt),
    officialEventCoverage: buildEventCoverage(dto.official_event_coverage),
    heuristicWorkflowCoverage: buildEventCoverage(dto.heuristic_workflow_coverage),
    logStreams: buildLogStreams(dto),
    evidence,
    evidenceLinks,
    hostOutput: dto.extension_host_output || "",
    hostOutputLines: dto.extension_host_output_lines || 0,
    metadataFilename: dto._metadata?.filename || reportId,
  };
}

export function adaptBundle(dto: AnalysisBundleDto, reportId: string): ActivationReportView {
  const report = adaptReport(dto.activation_report, reportId);
  return {
    ...report,
    detection: buildDetectionReport(dto.detection_report),
  };
}

type Risk = "low" | "medium" | "high";

function eventRiskHeuristic(event: EvidenceEventView): Risk {
  if (event.sensitive) return "high";
  if (event.kind === "network") return "medium";
  if (event.attributionStatus === "strong") return "medium";
  return "low";
}

export type ReportInteractionGraph = {
  rootLabel: string;
  rootMeta?: string;
  groups: Array<{
    id: string;
    label: string;
    count: number;
    pct?: number;
    axis: "network" | "fs" | "activation" | "secret" | "process";
    description?: string;
    children: Array<{
      id: string;
      label: string;
      count: number;
      meta?: string;
      risk?: Risk;
    }>;
  }>;
  _synthetic: boolean;
};

export function buildInteractionGraph(report: ActivationReportView): ReportInteractionGraph {
  const events = report.evidence;
  const total = events.length || 1;
  const network = events.filter((event) => event.kind === "network");
  const file = events.filter((event) => event.kind === "file");
  const activation = events.filter((event) => event.kind === "activation");
  const process = events.filter((event) => event.kind === "process");

  const networkChildren = uniqueByKey(network, (event) => event.host || event.path || event.eventId)
    .slice(0, 6)
    .map((event, index) => ({
      id: `net-${index}`,
      label: event.host || event.path || event.eventId,
      count: countByKey(network, (entry) => entry.host || entry.path || entry.eventId, event.host || event.path || event.eventId),
      meta: event.protocol ? event.protocol.toUpperCase() : undefined,
      risk: eventRiskHeuristic(event),
    }));

  const fileChildren = uniqueByKey(file, (event) => event.path || event.eventId)
    .slice(0, 6)
    .map((event, index) => ({
      id: `file-${index}`,
      label: event.path || event.eventId,
      count: countByKey(file, (entry) => entry.path || entry.eventId, event.path || event.eventId),
      meta: event.operation || undefined,
      risk: eventRiskHeuristic(event),
    }));

  const activationChildren = uniqueByKey(activation, (event) => event.activationEvent || event.eventId)
    .slice(0, 6)
    .map((event, index) => ({
      id: `act-${index}`,
      label: event.activationEvent || event.eventId,
      count: countByKey(
        activation,
        (entry) => entry.activationEvent || entry.eventId,
        event.activationEvent || event.eventId,
      ),
      meta: event.extensionId || undefined,
      risk: eventRiskHeuristic(event),
    }));

  const processChildren = uniqueByKey(process, (event) => event.summary || event.eventId)
    .slice(0, 4)
    .map((event, index) => ({
      id: `proc-${index}`,
      label: event.summary || event.eventId,
      count: 1,
      meta: event.actor || undefined,
      risk: eventRiskHeuristic(event),
    }));

  const groups: ReportInteractionGraph["groups"] = [];
  if (network.length) {
    groups.push({
      id: "network",
      label: "Outgoing · Network",
      count: network.length,
      pct: Math.round((network.length / total) * 100),
      axis: "network",
      description: "Outbound hosts and paths observed during the run.",
      children: networkChildren,
    });
  }
  if (file.length) {
    groups.push({
      id: "fs",
      label: "Filesystem · I/O",
      count: file.length,
      pct: Math.round((file.length / total) * 100),
      axis: "fs",
      description: "Files read or written by the target extension.",
      children: fileChildren,
    });
  }
  if (activation.length) {
    groups.push({
      id: "activation",
      label: "Activation · Triggers",
      count: activation.length,
      pct: Math.round((activation.length / total) * 100),
      axis: "activation",
      description: "Extension activation hooks consumed during automation.",
      children: activationChildren,
    });
  }
  if (process.length) {
    groups.push({
      id: "process",
      label: "Processes",
      count: process.length,
      pct: Math.round((process.length / total) * 100),
      axis: "process",
      description: "Subprocess events spawned by the extension.",
      children: processChildren,
    });
  }

  return {
    rootLabel: report.metadataFilename.replace(/\.json$/u, ""),
    rootMeta: "extension",
    groups,
    _synthetic: true,
  };
}

export type ReportRiskRadar = {
  threat: number;
  exfil: number;
  persistence: number;
  privesc: number;
  defense: number;
  resource: number;
  Threat: number;
  Exfil: number;
  Persistence: number;
  Privesc: number;
  Defense: number;
  Resource: number;
  _synthetic: true;
};

export function buildRiskRadar(report: ActivationReportView): ReportRiskRadar {
  const events = report.evidence;
  const networkCount = events.filter((event) => event.kind === "network").length;
  const fileCount = events.filter((event) => event.kind === "file").length;
  const sensitiveCount = events.filter((event) => event.sensitive).length;
  const processCount = events.filter((event) => event.kind === "process").length;
  const activationCount = events.filter((event) => event.kind === "activation").length;
  const totalSignals = report.riskSummary.totalSignals ?? events.length;
  const denom = Math.max(totalSignals, 1);

  const threat = clampScore((sensitiveCount / Math.max(events.length, 1)) * 100 + (report.riskSummary.high ?? 0) * 20);
  const exfil = clampScore((networkCount / Math.max(events.length, 1)) * 110 + (report.riskSummary.medium ?? 0) * 12);
  const persistence = clampScore((activationCount / denom) * 70 + (report.riskSignals.length ?? 0) * 8);
  const privesc = clampScore((processCount / denom) * 90);
  const defense = clampScore(100 - (report.coverageSummary.covered ?? 0) * 12);
  const resource = clampScore((fileCount / Math.max(events.length, 1)) * 90 + (report.riskSummary.low ?? 0) * 5);

  return {
    threat,
    exfil,
    persistence,
    privesc,
    defense,
    resource,
    Threat: threat,
    Exfil: exfil,
    Persistence: persistence,
    Privesc: privesc,
    Defense: defense,
    Resource: resource,
    _synthetic: true,
  };
}

function clampScore(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

function uniqueByKey<T>(items: ReadonlyArray<T>, key: (item: T) => string): T[] {
  const seen = new Set<string>();
  const out: T[] = [];
  for (const item of items) {
    const k = key(item);
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(item);
  }
  return out;
}

function countByKey<T>(items: ReadonlyArray<T>, key: (item: T) => string, value: string): number {
  let count = 0;
  for (const item of items) {
    if (key(item) === value) count += 1;
  }
  return count;
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
