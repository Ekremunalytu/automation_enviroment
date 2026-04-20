import type { AnalyzeJobStatusDto } from "../types/contracts";
import type { SimulationViewModel } from "../types/view-models";

const STEP_TITLES: Record<string, string> = {
  reset_sandbox: "Resetting sandbox state",
  install_extension: "Installing extension in sandbox",
  build_triggers: "Resolving trigger coverage",
  run_monitoring: "Running Playwright automation",
  finalize_report: "Collecting report output",
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

export function adaptJob(dto: AnalyzeJobStatusDto): SimulationViewModel {
  const steps = dto.steps ?? [];
  const completedSteps = steps.filter((step) => step.status === "completed").length;
  const progressPct = steps.length ? Math.round((completedSteps / steps.length) * 100) : 0;
  const warmupCopy =
    dto.status === "running" && !dto.report_path
      ? "Executor is still warming up. Trigger resolution and report bootstrapping are in flight."
      : dto.status === "queued"
        ? "Job is queued and waiting for the sandbox pipeline to start."
        : "Live evidence will start appearing here as soon as the report begins streaming.";

  return {
    jobId: dto.job_id,
    title: `${dto.publisher}.${dto.name}@${dto.version}`,
    status: dto.status,
    progressLabel: `${completedSteps}/${steps.length} steps complete`,
    currentStepLabel: formatStep(dto.current_step || steps.find((step) => step.status === "running")?.name || null),
    progressPct,
    warmupCopy,
    lastUpdatedLabel: formatDate(dto.updated_at),
    recentMessages: steps.map((step) => `${formatStep(step.name)}: ${step.message}`).slice(-4),
  };
}
