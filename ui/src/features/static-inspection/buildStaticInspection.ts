import type {
  SeverityDto,
  StaticAnalysisReportDto,
  StaticDetectionFindingDto,
  StaticEvidenceRefDto,
} from "../../lib/types/contracts";

export const STATIC_SEVERITIES: SeverityDto[] = [
  "critical",
  "high",
  "medium",
  "low",
  "info",
];

export interface StaticInspectionSummary {
  findings: StaticDetectionFindingDto[];
  severityCounts: Record<SeverityDto, number>;
  evidenceCount: number;
  evidenceFiles: Array<{ path: string; count: number }>;
  firedRules: number;
  actionableFindings: number;
  healthyTools: number;
  totalTools: number;
  filesDiscovered: number;
  filesSelected: number;
  filesEligible: number;
  filesScanned: number;
  filesParsed: number;
  bytesConsidered: number;
  bytesRead: number;
  coveragePct: number;
  parsePct: number;
}

function boundedCount(value?: number): number {
  return Math.max(0, value ?? 0);
}

export function buildStaticInspection(
  report: StaticAnalysisReportDto,
): StaticInspectionSummary {
  const detection = report.detection_report;
  const findings = detection.findings ?? [];
  const severityCounts: Record<SeverityDto, number> = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    info: 0,
  };
  const evidenceByFile = new Map<string, number>();
  let evidenceCount = 0;

  for (const finding of findings) {
    severityCounts[finding.severity] += 1;
    for (const evidence of finding.evidence ?? []) {
      evidenceCount += 1;
      evidenceByFile.set(
        evidence.relative_path,
        (evidenceByFile.get(evidence.relative_path) ?? 0) + 1,
      );
    }
  }

  const coverage = detection.coverage;
  const filesDiscovered = boundedCount(coverage?.files_discovered);
  const filesScanned = boundedCount(coverage?.files_scanned);
  const filesParsed = boundedCount(coverage?.files_parsed);
  const tools = detection.tool_executions ?? [];

  return {
    findings,
    severityCounts,
    evidenceCount,
    evidenceFiles: [...evidenceByFile.entries()]
      .map(([path, count]) => ({ path, count }))
      .sort((a, b) => b.count - a.count || a.path.localeCompare(b.path)),
    firedRules: new Set(findings.map((finding) => finding.rule_id)).size,
    actionableFindings: findings.filter((finding) => finding.severity !== "info")
      .length,
    healthyTools: tools.filter((tool) => (tool.status ?? "ok") === "ok").length,
    totalTools: tools.length,
    filesDiscovered,
    filesSelected: boundedCount(coverage?.files_selected),
    filesEligible: boundedCount(coverage?.files_eligible),
    filesScanned,
    filesParsed,
    bytesConsidered: boundedCount(coverage?.bytes_considered),
    bytesRead: boundedCount(coverage?.bytes_read),
    coveragePct: filesDiscovered
      ? Math.min(100, Math.round((filesScanned / filesDiscovered) * 100))
      : 0,
    parsePct: filesScanned
      ? Math.min(100, Math.round((filesParsed / filesScanned) * 100))
      : 0,
  };
}

export function filterStaticFindings(
  findings: StaticDetectionFindingDto[],
  severity: SeverityDto | "all",
  search: string,
): StaticDetectionFindingDto[] {
  const needle = search.trim().toLocaleLowerCase();
  return findings.filter((finding) => {
    if (severity !== "all" && finding.severity !== severity) return false;
    if (!needle) return true;
    const evidenceText = (finding.evidence ?? [])
      .map((evidence) => `${evidence.relative_path} ${evidence.snippet ?? ""}`)
      .join(" ");
    return [
      finding.rule_id,
      finding.title,
      finding.description,
      finding.categories.join(" "),
      evidenceText,
    ]
      .join(" ")
      .toLocaleLowerCase()
      .includes(needle);
  });
}

export function evidenceLocation(evidence: StaticEvidenceRefDto): string {
  return evidence.line_number
    ? `${evidence.relative_path}:${evidence.line_number}`
    : evidence.relative_path;
}
