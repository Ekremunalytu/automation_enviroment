import type {
  AnalyzeJobStatusDto,
  AnalyzeJobStepDto,
  StaticAnalysisReportDto,
  StaticDetectionFindingDto,
} from "../types/contracts";
import type {
  SimulationViewModel,
  StaticFindingView,
  StaticReportView,
} from "../types/view-models";
import { resolveTimeZone } from "../settings/presentation";

const STEP_TITLES: Record<string, string> = {
  reset_sandbox: "Resetting sandbox state",
  install_extension: "Installing extension in sandbox",
  build_triggers: "Resolving trigger coverage",
  run_monitoring: "Running Playwright automation",
  finalize_report: "Collecting report output",
};

const STEP_WEIGHTS: Record<string, number> = {
  reset_sandbox: 5,
  install_extension: 10,
  build_triggers: 10,
  run_monitoring: 70,
  finalize_report: 5,
};

// Static pre-check (ES-5) runs before the sandbox pipeline and lands as a single
// `static_report` gate (ALLOW/WARN/INCONCLUSIVE/BLOCK), not as an incremental step.
// When folded into progress it counts as one fixed-weight segment that is 100%
// complete the moment the static report is attached, so the bar leaves 0% during
// early warmup instead of sitting at zero while the sandbox resets.
const STATIC_WEIGHT = 10;

function formatStep(stepName?: string | null) {
  if (!stepName) return "Queued";
  return STEP_TITLES[stepName] || stepName.replaceAll("_", " ");
}

function formatDate(epoch?: number | null) {
  if (!epoch) return "Awaiting updates";
  return new Date(epoch * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone: resolveTimeZone(),
  });
}

function stepFraction(step: AnalyzeJobStepDto): number {
  if (step.status === "completed" || step.status === "skipped") return 1;
  if (
    step.status === "running" &&
    step.progress &&
    step.progress.total > 0 &&
    step.progress.completed >= 0
  ) {
    return Math.min(1, step.progress.completed / step.progress.total);
  }
  return 0;
}

const TOTAL_STEP_WEIGHT = Object.values(STEP_WEIGHTS).reduce((a, b) => a + b, 0);

export function computeProgressPct(
  steps: AnalyzeJobStepDto[],
  opts?: { staticDone?: boolean },
): number {
  // The static pre-check is folded into the bar only once it has actually
  // landed: both the numerator and the denominator grow by STATIC_WEIGHT at the
  // same time, which keeps progress monotonic and lets a run that never carries
  // a static report still reach 100% on the step weights alone. A pending/absent
  // static report keeps the legacy step-only denominator.
  const includeStatic = opts?.staticDone === true;
  const total = TOTAL_STEP_WEIGHT + (includeStatic ? STATIC_WEIGHT : 0);
  if (total <= 0) return 0;
  if (!steps.length && !includeStatic) return 0;
  let weighted = includeStatic ? STATIC_WEIGHT : 0;
  for (const step of steps) {
    const weight = STEP_WEIGHTS[step.name] ?? 0;
    weighted += weight * stepFraction(step);
  }
  const pct = Math.round((weighted / total) * 100);
  return Math.min(100, Math.max(0, pct));
}

function buildProgressLabel(steps: AnalyzeJobStepDto[]): string {
  if (!steps.length) return "Awaiting steps";
  const total = steps.length;
  const completedCount = steps.filter((step) => step.status === "completed").length;
  if (completedCount === total) return "All steps complete";
  const settledCount = steps.filter(
    (step) => step.status === "completed" || step.status === "skipped",
  ).length;
  if (settledCount === total) return "All applicable steps complete";

  const terminalIdx = steps.findIndex(
    (step) => step.status === "failed" || step.status === "cancelled",
  );
  if (terminalIdx >= 0) {
    return `Step ${terminalIdx + 1} of ${total} ${steps[terminalIdx].status}`;
  }

  const runningIdx = steps.findIndex((step) => step.status === "running");
  if (runningIdx >= 0) {
    const step = steps[runningIdx];
    const sub =
      step.progress && step.progress.total > 0
        ? ` · scenario ${step.progress.completed}/${step.progress.total}`
        : "";
    return `Step ${runningIdx + 1} of ${total}${sub}`;
  }

  return `Step 1 of ${total}`;
}

function titleCase(value: string): string {
  if (!value) return value;
  return value
    .split("_")
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(" ");
}

function adaptStaticFinding(
  finding: StaticDetectionFindingDto,
): StaticFindingView {
  return {
    id: finding.id ?? finding.rule_id,
    ruleId: finding.rule_id,
    title: finding.title,
    description: finding.description,
    severity: finding.severity,
    severityLabel: titleCase(finding.severity),
    confidence: finding.confidence,
    confidenceLabel: titleCase(finding.confidence),
    evidenceCount: (finding.evidence ?? []).length,
  };
}

// ES-5 (ADR 0016): map the static pre-check report DTO to its view-model. The
// `partial` flag and per-tool `status` are surfaced so a degraded scan (a
// swallowed rule error / Semgrep timeout) reads as incomplete coverage rather
// than a confidently clean ALLOW.
export function adaptStaticReport(
  dto: StaticAnalysisReportDto,
): StaticReportView {
  const gate = dto.gate_outcome;
  const detection = dto.detection_report;
  return {
    decision: gate.decision,
    decisionLabel: titleCase(gate.decision),
    blockedBy: gate.blocked_by ?? [],
    warnedBy: gate.warned_by ?? [],
    inconclusiveReasons: gate.inconclusive_reasons ?? [],
    allowReason: gate.allow_reason ?? null,
    partial: detection.partial ?? false,
    coverage: {
      filesDiscovered: detection.coverage?.files_discovered ?? 0,
      filesScanned: detection.coverage?.files_scanned ?? 0,
      filesParsed: detection.coverage?.files_parsed ?? 0,
      reasons: detection.coverage?.coverage_reasons ?? [],
    },
    toolStatuses: (detection.tool_executions ?? []).map((record) => ({
      tool: record.tool,
      status: record.status ?? "ok",
      errorCount: record.error_count ?? 0,
    })),
    findings: (detection.findings ?? []).map(adaptStaticFinding),
  };
}

export function adaptJob(dto: AnalyzeJobStatusDto): SimulationViewModel {
  const steps = dto.steps ?? [];
  const progressPct = computeProgressPct(steps, { staticDone: Boolean(dto.static_report) });
  const monitoringStep = steps.find((step) => step.name === "run_monitoring");
  const monitoringSubLine =
    monitoringStep && monitoringStep.status === "running" && monitoringStep.progress
      ? `${formatStep(monitoringStep.name)}: scenario ${monitoringStep.progress.completed}/${monitoringStep.progress.total}`
      : null;
  const warmupCopy =
    dto.status === "completed" && dto.static_report && !dto.report_path
      ? "Static analysis completed. Dynamic sandbox analysis was skipped because it is disabled."
      : dto.status === "running" && !dto.report_path
      ? "Executor is still warming up. Trigger resolution and report bootstrapping are in flight."
      : dto.status === "queued"
        ? "Job is queued and waiting for the sandbox pipeline to start."
        : dto.status === "cancelled"
          ? "Run was cancelled. Partial logs and the report-so-far are preserved for inspection."
          : "Live evidence will start appearing here as soon as the report begins streaming.";

  const baseMessages = steps
    .map((step) => `${formatStep(step.name)}: ${step.message}`)
    .slice(-4);
  const recentMessages = monitoringSubLine
    ? [...baseMessages, monitoringSubLine].slice(-4)
    : baseMessages;

  return {
    jobId: dto.job_id,
    title: `${dto.publisher}.${dto.name}@${dto.version}`,
    status: dto.status,
    progressLabel: buildProgressLabel(steps),
    currentStepLabel:
      dto.status === "completed"
        ? "Complete"
        : formatStep(
            dto.current_step ||
              steps.find((step) => step.status === "running")?.name ||
              null,
          ),
    progressPct,
    warmupCopy,
    lastUpdatedLabel: formatDate(dto.updated_at),
    recentMessages,
    reportError: dto.report_error ?? null,
    staticReport: dto.static_report ? adaptStaticReport(dto.static_report) : null,
  };
}
