export interface EvidenceEventView {
  eventId: string;
  kind: string;
  kindLabel: string;
  timestamp: string;
  relTimeS: number | null;
  collector: string;
  collectorLabel: string;
  actor: string;
  actorLabel: string;
  scenarioName: string;
  scenarioLabel: string;
  extensionId: string;
  activationEvent: string;
  operation: string;
  protocol: string;
  host: string;
  path: string;
  destinationIp: string;
  destinationPort: number | null;
  attributionStatus: string;
  attributionStatusLabel: string;
  attributionBasis: string;
  attributionConfidence: number;
  attributionConfidencePct: number;
  isTargetExtensionEvent: boolean;
  noiseReason: string;
  artifactClass: string;
  sensitive: boolean;
  summary: string;
  summaryDisplay: string;
  artifact: string;
  artifactShort: string;
  detail: string;
  rawContext: Record<string, unknown>;
  timestampDisplay: string;
}

export interface EvidenceLinkView {
  fromEventId: string;
  toEventId: string;
  linkType: string;
  linkLabel: string;
  confidence: number;
  confidencePct: number;
  confidenceLabel: string;
  reason: string;
}

export interface DetectionEvidenceRefView {
  eventId: string;
  type: string;
  summary: string;
}

export interface DetectionFindingView {
  id: string;
  ruleId: string;
  ruleVersion: string;
  ruleLifecycle: string;
  title: string;
  description: string;
  categories: string[];
  severity: "critical" | "high" | "medium" | "low" | "info";
  severityLabel: string;
  confidence: "high" | "medium" | "low";
  confidenceLabel: string;
  adversaryClass: string;
  evidence: DetectionEvidenceRefView[];
  mitigationHint: string;
}

export interface RuleExecutionRecordView {
  ruleId: string;
  ruleVersion: string;
  lifecycle: string;
  status: "fired" | "silent" | "error";
  statusLabel: string;
  findingIds: string[];
  errorDetail: string;
}

export interface DetectionReportView {
  verdict:
    | "malicious"
    | "suspicious"
    | "clean_with_notes"
    | "clean"
    | "inconclusive";
  verdictLabel: string;
  verdictRationale: string;
  findings: DetectionFindingView[];
  rulesExecuted: RuleExecutionRecordView[];
}

export interface ReportSummaryView {
  totalEvents: number;
  totalActivated: number;
  uniqueExtensions: number;
  scenariosRun: string[];
  durationS: number;
  networkEvents: number;
  fileEvents: number;
  sensitiveEvents: number;
  attemptedCapabilities: string[];
  verifiedCapabilities: string[];
  uiBlockerCount: number;
  targetExtensionExpected: string;
  targetExtensionObserved: boolean;
  triggerPlanApplied: boolean;
  triggerRequested: boolean;
  triggerLoaded: boolean;
  verificationGap: number;
  runQuality: "high" | "medium" | "low" | "inconclusive";
  automationHealthStatus: "healthy" | "degraded" | "inconclusive";
  automationHealthReasons: string[];
  failedScenarios: string[];
  skippedScenarios: string[];
  skippedScenarioDetails: { name: string; reasonCode: string; detail: string }[];
  extensionHostLogPresent: boolean;
  extensionHostLogFound: boolean;
  extensionHostOutputPresent: boolean;
  targetStreamPresent: boolean;
  targetActivationCount: number;
  legacyHealthFallback: boolean;
  signalSummaryLevel: "benign" | "needs_review" | "suspicious" | "likely_malicious";
  signalSummaryScore: number;
  signalSummaryReasons: string[];
  signalSummaryNote: string;
}

export interface AttributionSummaryView {
  targetActivationCount: number;
  strongTargetFileEventCount: number;
  strongTargetNetworkEventCount: number;
  correlatedOnlyEventCount: number;
  backgroundActivationCount: number;
  competingCandidateCount: number;
  uiBlockerCount: number;
}

export interface RiskSignalView {
  signalId: string;
  category: string;
  categoryLabel: string;
  severity: string;
  severityLabel: string;
  confidence: number;
  confidencePct: number;
  evidenceEventIds: string[];
  summary: string;
}

export interface RiskSummaryView {
  totalSignals: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  categories: string[];
}

export interface CoverageSummaryView {
  covered: number;
  partial: number;
  missing: number;
  attempted: number;
  verified: number;
  missingCapabilities: string[];
  attemptedCapabilities: string[];
  verifiedCapabilities: string[];
}

export interface CoverageCapabilityView {
  capability: string;
  capabilityLabel: string;
  status: string;
  statusLabel: string;
  track: string;
  source: string;
  supportStatus: string;
  supportStatusLabel: string;
  verificationStatus: string;
  verificationStatusLabel: string;
  selectedScenarios: string[];
  supportedScenarios: string[];
  notes: string;
  attempted: boolean;
  verified: boolean;
}

export interface CoverageTrackView {
  source: string;
  selectedScenarios: string[];
  summary: CoverageSummaryView;
  matrix: CoverageCapabilityView[];
}

export interface CoverageTracksView {
  official: CoverageTrackView;
  heuristic: CoverageTrackView;
}

export interface StimulusPassView {
  passId: string;
  label: string;
  order: number;
  startedAt: number | null;
  endedAt: number | null;
  status: string;
  triggerMethod: string;
}

export interface PrerequisiteResultView {
  prerequisiteId: string;
  key: string;
  label: string;
  status: string;
  materializer: string;
  passName: string;
  attemptIds: string[];
  detail: string;
}

export interface EventAttemptView {
  attemptId: string;
  declaredEvent: string;
  activationEvent: string;
  eventFamily: string;
  eventValue: string;
  track: string;
  selectedBy: string;
  selectionReasons: string[];
  passName: string;
  backfillPassName: string;
  prerequisiteKeys: string[];
  verificationContract: string[];
  triggerMethod: string;
  fallbackTriggerMethod: string;
  executorAction: string;
  backfillExecutorAction: string;
  legacyScenarios: string[];
  capabilityTags: string[];
  status: string;
  statusLabel: string;
  triggerMethodUsed: string;
  attemptedPasses: string[];
  evidence: string[];
  verificationStatus: string;
  verificationStatusLabel: string;
  failureReasonCode: string;
  blockedReasonCode: string;
  resultDetails: string;
  official: boolean;
  heuristic: boolean;
  uiPath: string;
  harnessFallback: string;
}

export interface EventCoverageView {
  track: string;
  declared: number;
  verified: number;
  attemptedOnly: number;
  failed: number;
  blocked: number;
  unresolved: number;
  declaredEvents: string[];
}

export interface LogEntryView {
  timestamp: string;
  timestampDisplay: string;
  relTimeS: number | null;
  stream: string;
  kind: string;
  kindLabel: string;
  message: string;
  extensionId: string;
  activationEvent: string;
  scenarioName: string;
  status: string;
  statusLabel: string;
  isTargetExtension: boolean;
}

export interface LogStreamsView {
  targetExtensionHost: LogEntryView[];
  otherExtensionHost: LogEntryView[];
  automation: LogEntryView[];
  uiBlockers: LogEntryView[];
}

export interface ActivationReportView {
  reportId: string;
  reportVersion: number;
  summary: ReportSummaryView;
  detection: DetectionReportView | null;
  attributionSummary: AttributionSummaryView;
  riskSignals: RiskSignalView[];
  riskSummary: RiskSummaryView;
  coverageSummary: CoverageSummaryView;
  coverageMatrix: CoverageCapabilityView[];
  coverageTracks: CoverageTracksView;
  stimulusPasses: StimulusPassView[];
  prerequisiteResults: PrerequisiteResultView[];
  eventAttempts: EventAttemptView[];
  officialEventCoverage: EventCoverageView;
  heuristicWorkflowCoverage: EventCoverageView;
  logStreams: LogStreamsView;
  evidence: EvidenceEventView[];
  evidenceLinks: EvidenceLinkView[];
  hostOutput: string;
  hostOutputLines: number;
  metadataFilename: string;
}

export interface EvidenceInspectorView {
  event: EvidenceEventView;
  outgoing: Array<EvidenceLinkView & { peerEvent?: EvidenceEventView }>;
  incoming: Array<EvidenceLinkView & { peerEvent?: EvidenceEventView }>;
  related: Array<EvidenceLinkView & { peerEvent?: EvidenceEventView; direction: "incoming" | "outgoing" }>;
}

export interface RuleDraftView {
  title: string;
  severity: "low" | "medium" | "high";
  confidence: number;
  scope: Record<string, unknown>;
  conditions: Array<{ field: string; operator: string; value: unknown }>;
  rationale: string;
  labels: string[];
  suspiciousReasons: string[];
}

export interface SimulationViewModel {
  jobId: string;
  title: string;
  status: string;
  progressLabel: string;
  currentStepLabel: string;
  progressPct: number;
  warmupCopy: string;
  lastUpdatedLabel: string;
  recentMessages: string[];
  reportError: string | null;
}
