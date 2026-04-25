import type { AnalyzeJobStatusDto, AnalyzeJobStepDto } from "../types/contracts";
import type { SimulationViewModel } from "../types/view-models";

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
  });
}

function stepFraction(step: AnalyzeJobStepDto): number {
  if (step.status === "completed") return 1;
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

export function computeProgressPct(steps: AnalyzeJobStepDto[]): number {
  if (!steps.length) return 0;
  let weighted = 0;
  for (const step of steps) {
    const weight = STEP_WEIGHTS[step.name] ?? 0;
    weighted += weight * stepFraction(step);
  }
  if (TOTAL_STEP_WEIGHT <= 0) return 0;
  const pct = Math.round((weighted / TOTAL_STEP_WEIGHT) * 100);
  return Math.min(100, Math.max(0, pct));
}

function buildProgressLabel(steps: AnalyzeJobStepDto[]): string {
  if (!steps.length) return "Awaiting steps";
  const total = steps.length;
  const completedCount = steps.filter((step) => step.status === "completed").length;
  if (completedCount === total) return "All steps complete";

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

export function adaptJob(dto: AnalyzeJobStatusDto): SimulationViewModel {
  const steps = dto.steps ?? [];
  const progressPct = computeProgressPct(steps);
  const monitoringStep = steps.find((step) => step.name === "run_monitoring");
  const monitoringSubLine =
    monitoringStep && monitoringStep.status === "running" && monitoringStep.progress
      ? `${formatStep(monitoringStep.name)}: scenario ${monitoringStep.progress.completed}/${monitoringStep.progress.total}`
      : null;
  const warmupCopy =
    dto.status === "running" && !dto.report_path
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
    currentStepLabel: formatStep(dto.current_step || steps.find((step) => step.status === "running")?.name || null),
    progressPct,
    warmupCopy,
    lastUpdatedLabel: formatDate(dto.updated_at),
    recentMessages,
    reportError: dto.report_error ?? null,
  };
}
