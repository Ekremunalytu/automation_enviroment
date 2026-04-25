import { adaptJob, computeProgressPct } from "./job";
import type { AnalyzeJobStatusDto, AnalyzeJobStepDto } from "../types/contracts";

const CANONICAL_STEPS: AnalyzeJobStepDto[] = [
  { name: "reset_sandbox", status: "pending", message: "Waiting" },
  { name: "install_extension", status: "pending", message: "Queued" },
  { name: "build_triggers", status: "pending", message: "Waiting" },
  { name: "run_monitoring", status: "pending", message: "Waiting" },
  { name: "finalize_report", status: "pending", message: "Waiting" },
];

function canonicalSteps(
  overrides: Partial<Record<string, Partial<AnalyzeJobStepDto>>> = {},
): AnalyzeJobStepDto[] {
  return CANONICAL_STEPS.map((step) => ({ ...step, ...(overrides[step.name] ?? {}) }));
}

function baseDto(overrides: Partial<AnalyzeJobStatusDto> = {}): AnalyzeJobStatusDto {
  return {
    job_id: "job-1",
    status: "running",
    publisher: "ms",
    name: "lint",
    version: "1.0.0",
    message: "running",
    steps: canonicalSteps(),
    created_at: 1713002400,
    updated_at: 1713002410,
    ...overrides,
  };
}

describe("computeProgressPct", () => {
  it("returns 0 for an empty step list", () => {
    expect(computeProgressPct([])).toBe(0);
  });

  it("returns 100 when every canonical step is completed", () => {
    const steps = canonicalSteps({
      reset_sandbox: { status: "completed" },
      install_extension: { status: "completed" },
      build_triggers: { status: "completed" },
      run_monitoring: { status: "completed" },
      finalize_report: { status: "completed" },
    });
    expect(computeProgressPct(steps)).toBe(100);
  });

  it("does not stall at 60% during run_monitoring with sub-progress", () => {
    const steps = canonicalSteps({
      reset_sandbox: { status: "completed" },
      install_extension: { status: "completed" },
      build_triggers: { status: "completed" },
      run_monitoring: {
        status: "running",
        progress: { completed: 2, total: 5 },
      },
    });
    // Weights: 5 + 10 + 10 + 70 * 0.4 + 0 = 53
    expect(computeProgressPct(steps)).toBe(53);
  });

  it("treats running run_monitoring without sub-progress as zero contribution", () => {
    const steps = canonicalSteps({
      reset_sandbox: { status: "completed" },
      install_extension: { status: "completed" },
      build_triggers: { status: "completed" },
      run_monitoring: { status: "running" },
    });
    // No sub-progress → 5 + 10 + 10 = 25.
    expect(computeProgressPct(steps)).toBe(25);
  });

  it("ignores stale progress on a non-running step (failed/cancelled)", () => {
    // The backend clears progress when transitioning to terminal states, but
    // if a stale snapshot ever leaks through with a failed step still carrying
    // its last numerator/total, computeProgressPct must NOT count it as
    // partial credit — only `running` steps contribute sub-progress.
    const failed = canonicalSteps({
      reset_sandbox: { status: "completed" },
      install_extension: { status: "completed" },
      build_triggers: { status: "completed" },
      run_monitoring: {
        status: "failed",
        progress: { completed: 4, total: 5 },
      },
    });
    expect(computeProgressPct(failed)).toBe(25);

    const cancelled = canonicalSteps({
      reset_sandbox: { status: "completed" },
      install_extension: { status: "completed" },
      build_triggers: { status: "completed" },
      run_monitoring: {
        status: "cancelled",
        progress: { completed: 2, total: 5 },
      },
    });
    expect(computeProgressPct(cancelled)).toBe(25);
  });

  it("clamps sub-progress when completed exceeds total", () => {
    // Defense in depth — the heartbeat shouldn't emit completed > total, but
    // if it did (e.g. a duplicated scenario_traces entry), we want the bar
    // to top out at 100%, not overshoot.
    const steps = canonicalSteps({
      reset_sandbox: { status: "completed" },
      install_extension: { status: "completed" },
      build_triggers: { status: "completed" },
      run_monitoring: {
        status: "running",
        progress: { completed: 10, total: 5 },
      },
    });
    // run_monitoring contributes 70 * min(1, 10/5) = 70.
    // Total: 5 + 10 + 10 + 70 + 0 = 95.
    expect(computeProgressPct(steps)).toBe(95);
  });

  it("treats running step with total=0 as zero sub-progress (no NaN)", () => {
    const steps = canonicalSteps({
      reset_sandbox: { status: "completed" },
      install_extension: { status: "completed" },
      build_triggers: { status: "completed" },
      run_monitoring: {
        status: "running",
        progress: { completed: 0, total: 0 },
      },
    });
    expect(computeProgressPct(steps)).toBe(25);
  });

  it("gives unknown step names zero weight without crashing", () => {
    // If the backend ever introduces a new step name before the UI ships its
    // weight, the unknown step should silently contribute 0% rather than
    // throwing or skewing the bar.
    const steps: AnalyzeJobStepDto[] = [
      { name: "reset_sandbox", status: "completed", message: "ok" },
      { name: "future_step_we_have_not_shipped_yet", status: "completed", message: "ok" },
    ];
    // Only reset_sandbox (5 of 100) counts. 5 / 100 = 5.
    expect(computeProgressPct(steps)).toBe(5);
  });
});

describe("adaptJob", () => {
  it("builds warmup copy and weighted progress for running jobs without a report", () => {
    const model = adaptJob(
      baseDto({
        steps: canonicalSteps({
          reset_sandbox: { status: "completed", message: "Sandbox reset" },
          run_monitoring: {
            status: "running",
            message: "Monitoring in progress",
          },
        }),
      }),
    );

    expect(model.title).toBe("ms.lint@1.0.0");
    expect(model.progressPct).toBe(5);
    expect(model.currentStepLabel).toBe("Running Playwright automation");
    expect(model.warmupCopy).toContain("warming up");
  });

  it("surfaces sub-progress in recentMessages when run_monitoring is running", () => {
    const model = adaptJob(
      baseDto({
        steps: canonicalSteps({
          reset_sandbox: { status: "completed", message: "ok" },
          install_extension: { status: "completed", message: "ok" },
          build_triggers: { status: "completed", message: "ok" },
          run_monitoring: {
            status: "running",
            message: "Scenario 1/5",
            progress: { completed: 1, total: 5 },
          },
        }),
      }),
    );

    expect(model.progressPct).toBeGreaterThan(25);
    expect(model.progressPct).toBeLessThan(100);
    expect(
      model.recentMessages.some((line) => line.includes("scenario 1/5")),
    ).toBe(true);
  });

  it("sets the warmup copy for a cancelled run", () => {
    const model = adaptJob(baseDto({ status: "cancelled", report_path: null }));
    expect(model.status).toBe("cancelled");
    expect(model.warmupCopy.toLowerCase()).toContain("cancelled");
  });
});
