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

export interface ReportSummaryView {
  totalEvents: number;
  totalActivated: number;
  uniqueExtensions: number;
  scenariosRun: string[];
  durationS: number;
  networkEvents: number;
  fileEvents: number;
  sensitiveEvents: number;
}

export interface ActivationReportView {
  reportId: string;
  reportVersion: number;
  summary: ReportSummaryView;
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
}
