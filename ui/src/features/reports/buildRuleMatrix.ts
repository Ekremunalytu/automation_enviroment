// Pure transform: report view-model → rule trigger matrix model.
//
// Dynamic side is fully data-driven from `detection.rulesExecuted` (one record per
// rule the engine ran, with fired/silent/error status) enriched by the matching
// fired findings. Static side starts from the in-house catalog universe and marks
// each rule fired (its rule_id appears in `staticReport.findings`) or silent (by
// exclusion); fired rules outside the catalog (e.g. external Semgrep) are surfaced
// from their finding. No backend activation data is fabricated here.

import type {
  ActivationReportView,
  DetectionFindingView,
  RuleExecutionRecordView,
  StaticFindingView,
} from "../../lib/types/view-models";
import {
  catalogEntries,
  ruleCatalogEntry,
  type RuleCatalogEntry,
  type RuleSeverity,
  type RuleStream,
} from "../../lib/rules/ruleCatalog";

export type RuleStatus = "fired" | "silent" | "error" | "unknown";

export interface CellDetail {
  title: string;
  description: string;
  mitigation: string | null;
  evidence: string[];
  evidenceCount: number;
}

export interface MatrixCell {
  ruleId: string;
  label: string;
  stream: RuleStream;
  family: string;
  techniques: string[];
  severity: RuleSeverity;
  status: RuleStatus;
  statusLabel: string;
  lifecycle: string | null;
  ruleVersion: string | null;
  findingCount: number;
  inCatalog: boolean;
  detail: CellDetail | null;
}

export interface ToolCell {
  tool: string;
  status: string;
  errorCount: number;
}

export interface FamilyGroup {
  family: string;
  cells: MatrixCell[];
}

export interface RuleMatrix {
  dynamic: FamilyGroup[];
  static: FamilyGroup[];
  toolCells: ToolCell[];
  hasStatic: boolean;
  counts: {
    dynamicFired: number;
    dynamicTotal: number;
    staticFired: number;
    staticTotal: number;
  };
}

const STATUS_LABEL: Record<RuleStatus, string> = {
  fired: "Fired",
  silent: "Silent",
  error: "Error",
  unknown: "Not run",
};

const SEVERITY_RANK: Record<RuleSeverity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

const STATUS_RANK: Record<RuleStatus, number> = {
  fired: 0,
  error: 1,
  silent: 2,
  unknown: 3,
};

function mitreTechniques(categories: string[]): string[] {
  return categories
    .filter((category) => category.startsWith("attack."))
    .map((category) => category.slice("attack.".length).toUpperCase());
}

function groupFindingsByRule<T extends { ruleId: string }>(findings: T[]): Map<string, T[]> {
  const byRule = new Map<string, T[]>();
  for (const finding of findings) {
    const existing = byRule.get(finding.ruleId);
    if (existing) existing.push(finding);
    else byRule.set(finding.ruleId, [finding]);
  }
  return byRule;
}

function dynamicDetail(
  finding: DetectionFindingView | null,
  record: RuleExecutionRecordView,
  catalog: RuleCatalogEntry | undefined,
): CellDetail | null {
  if (finding) {
    return {
      title: finding.title,
      description: finding.description,
      mitigation: finding.mitigationHint || null,
      evidence: finding.evidence.map((ref) => ref.summary).filter(Boolean),
      evidenceCount: finding.evidence.length,
    };
  }
  const base = catalog?.detail ?? catalog?.blurb ?? "";
  const description =
    record.status === "error" && record.errorDetail
      ? `${base}${base ? " " : ""}Execution error: ${record.errorDetail}`
      : base;
  if (!description) return null;
  return {
    title: catalog?.label ?? record.ruleId,
    description,
    mitigation: null,
    evidence: [],
    evidenceCount: 0,
  };
}

function staticDetail(
  finding: StaticFindingView | null,
  catalog: RuleCatalogEntry | undefined,
): CellDetail | null {
  if (finding) {
    return {
      title: finding.title,
      description: finding.description,
      mitigation: null,
      evidence: [],
      evidenceCount: finding.evidenceCount,
    };
  }
  if (catalog) {
    return {
      title: catalog.label,
      description: catalog.detail ?? catalog.blurb,
      mitigation: null,
      evidence: [],
      evidenceCount: 0,
    };
  }
  return null;
}

function buildDynamicCells(report: ActivationReportView): MatrixCell[] {
  const detection = report.detection;
  const records = detection?.rulesExecuted ?? [];
  const findingsByRule = groupFindingsByRule(detection?.findings ?? []);

  return records.map((record) => {
    const catalog = ruleCatalogEntry(record.ruleId);
    const status: RuleStatus =
      record.status === "fired" ? "fired" : record.status === "error" ? "error" : "silent";
    const finding = status === "fired" ? findingsByRule.get(record.ruleId)?.[0] ?? null : null;
    const techniques = finding
      ? mitreTechniques(finding.categories)
      : catalog?.techniques ?? [];
    return {
      ruleId: record.ruleId,
      label: catalog?.label ?? record.ruleId,
      stream: "dynamic",
      family: catalog?.family ?? "Other",
      techniques,
      severity: finding?.severity ?? catalog?.severity ?? "info",
      status,
      statusLabel: STATUS_LABEL[status],
      lifecycle: record.lifecycle || null,
      ruleVersion: record.ruleVersion || null,
      findingCount: record.findingIds.length,
      inCatalog: Boolean(catalog),
      detail: dynamicDetail(finding, record, catalog),
    };
  });
}

function buildStaticCells(report: ActivationReportView): MatrixCell[] {
  const staticReport = report.staticReport;
  if (!staticReport) return [];

  const findingsByRule = groupFindingsByRule(staticReport.findings);
  const cells: MatrixCell[] = [];
  const seen = new Set<string>();

  for (const catalog of catalogEntries("static")) {
    seen.add(catalog.ruleId);
    const fired = findingsByRule.get(catalog.ruleId);
    const finding = fired?.[0] ?? null;
    const status: RuleStatus = fired ? "fired" : "silent";
    cells.push({
      ruleId: catalog.ruleId,
      label: catalog.label,
      stream: "static",
      family: catalog.family,
      techniques: catalog.techniques,
      severity: finding?.severity ?? catalog.severity,
      status,
      statusLabel: STATUS_LABEL[status],
      lifecycle: null,
      ruleVersion: null,
      findingCount: fired?.length ?? 0,
      inCatalog: true,
      detail: staticDetail(finding, catalog),
    });
  }

  // Fired static rules outside the in-house catalog (external Semgrep/YARA/Trivy):
  // we can't enumerate their silent universe, but a rule that *fired* must be shown.
  for (const [ruleId, findings] of findingsByRule) {
    if (seen.has(ruleId)) continue;
    const finding = findings[0];
    cells.push({
      ruleId,
      label: finding.title || ruleId,
      stream: "static",
      family: "Tool rule",
      techniques: [],
      severity: finding.severity,
      status: "fired",
      statusLabel: STATUS_LABEL.fired,
      lifecycle: null,
      ruleVersion: null,
      findingCount: findings.length,
      inCatalog: false,
      detail: staticDetail(finding, undefined),
    });
  }

  return cells;
}

function cellSort(a: MatrixCell, b: MatrixCell): number {
  return (
    STATUS_RANK[a.status] - STATUS_RANK[b.status] ||
    SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity] ||
    a.label.localeCompare(b.label)
  );
}

function familyRank(group: FamilyGroup): number {
  const hasFired = group.cells.some((cell) => cell.status === "fired");
  const bestSeverity = Math.min(...group.cells.map((cell) => SEVERITY_RANK[cell.severity]));
  return (hasFired ? 0 : 100) + bestSeverity;
}

function groupByFamily(cells: MatrixCell[]): FamilyGroup[] {
  const byFamily = new Map<string, MatrixCell[]>();
  for (const cell of cells) {
    const existing = byFamily.get(cell.family);
    if (existing) existing.push(cell);
    else byFamily.set(cell.family, [cell]);
  }
  const groups: FamilyGroup[] = [...byFamily.entries()].map(([family, familyCells]) => ({
    family,
    cells: familyCells.sort(cellSort),
  }));
  groups.sort((a, b) => familyRank(a) - familyRank(b) || a.family.localeCompare(b.family));
  return groups;
}

export function buildRuleMatrix(report: ActivationReportView): RuleMatrix {
  const dynamicCells = buildDynamicCells(report);
  const staticCells = buildStaticCells(report);
  const toolCells: ToolCell[] = (report.staticReport?.toolStatuses ?? []).map((tool) => ({
    tool: tool.tool,
    status: tool.status,
    errorCount: tool.errorCount,
  }));

  return {
    dynamic: groupByFamily(dynamicCells),
    static: groupByFamily(staticCells),
    toolCells,
    hasStatic: report.staticReport != null,
    counts: {
      dynamicFired: dynamicCells.filter((cell) => cell.status === "fired").length,
      dynamicTotal: dynamicCells.length,
      staticFired: staticCells.filter((cell) => cell.status === "fired").length,
      staticTotal: staticCells.length,
    },
  };
}
