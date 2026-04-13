import { adaptJob } from "./job";
import type { AnalyzeJobStatusDto } from "../types/contracts";

describe("adaptJob", () => {
  it("builds warmup copy and progress for running jobs without a report", () => {
    const dto: AnalyzeJobStatusDto = {
      job_id: "job-1",
      status: "running",
      publisher: "ms",
      name: "lint",
      version: "1.0.0",
      message: "running",
      steps: [
        { name: "reset_sandbox", status: "completed", message: "Sandbox reset" },
        { name: "run_monitoring", status: "running", message: "Monitoring in progress" },
      ],
      created_at: 1713002400,
      updated_at: 1713002410,
    };

    const model = adaptJob(dto);

    expect(model.title).toBe("ms.lint@1.0.0");
    expect(model.progressPct).toBe(50);
    expect(model.currentStepLabel).toBe("Running Playwright automation");
    expect(model.warmupCopy).toContain("warming up");
  });
});
