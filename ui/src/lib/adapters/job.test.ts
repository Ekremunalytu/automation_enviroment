import { adaptJob, adaptStaticReport, computeProgressPct } from "./job";
import { DEFAULT_TIME_ZONE, setTimeZone } from "../settings/presentation";
import type {
  AnalyzeJobStatusDto,
  AnalyzeJobStepDto,
  StaticAnalysisReportDto,
} from "../types/contracts";

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

  it("credits the static pre-check segment off zero before any step runs", () => {
    // Static gate already landed while the sandbox is still resetting: the bar
    // should leave 0% even with no step progress. 10 / (100 + 10) ≈ 9%.
    expect(computeProgressPct([], { staticDone: true })).toBe(9);
    const resetting = canonicalSteps({ reset_sandbox: { status: "running" } });
    expect(computeProgressPct(resetting, { staticDone: true })).toBe(9);
  });

  it("still reaches 100% when every step plus the static pre-check is done", () => {
    const steps = canonicalSteps({
      reset_sandbox: { status: "completed" },
      install_extension: { status: "completed" },
      build_triggers: { status: "completed" },
      run_monitoring: { status: "completed" },
      finalize_report: { status: "completed" },
    });
    // (100 + 10) / (100 + 10) = 100.
    expect(computeProgressPct(steps, { staticDone: true })).toBe(100);
  });

  it("falls back to the step-only denominator when static is pending/absent", () => {
    // A run that never carries a static report must still top out at 100% on the
    // step weights alone — staticDone:false keeps the legacy denominator of 100.
    const steps = canonicalSteps({
      reset_sandbox: { status: "completed" },
      install_extension: { status: "completed" },
      build_triggers: { status: "completed" },
      run_monitoring: { status: "completed" },
      finalize_report: { status: "completed" },
    });
    expect(computeProgressPct(steps, { staticDone: false })).toBe(100);
    expect(computeProgressPct(steps, { staticDone: false })).toBe(computeProgressPct(steps));
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

  it("leaves staticReport null when the job carries no static_report", () => {
    const model = adaptJob(baseDto());
    expect(model.staticReport).toBeNull();
    // No static report → progress stays on the step-only denominator (0% while
    // every step is still pending).
    expect(model.progressPct).toBe(0);
  });

  it("lifts warmup progress off zero once a static_report is attached", () => {
    const staticReport: StaticAnalysisReportDto = {
      detection_report: {},
      gate_outcome: { decision: "allow" },
    };
    // Sandbox still resetting (all steps pending) but the static gate landed:
    // 10 / (100 + 10) ≈ 9%.
    const model = adaptJob(baseDto({ static_report: staticReport }));
    expect(model.progressPct).toBe(9);
  });

  it("adapts an attached static_report (ES-5) into the view-model", () => {
    const dto: StaticAnalysisReportDto = {
      detection_report: {
        findings: [
          {
            id: "01HZ",
            rule_id: "extrace.s2.typosquat",
            rule_version: "1.0.0",
            rule_lifecycle: "production",
            categories: ["attack.T1036"],
            severity: "high",
            confidence: "medium",
            title: "Typosquat",
            description: "near a popular publisher",
            evidence: [
              {
                type: "manifest",
                relative_path: "package.json",
                tool: "inhouse",
              },
            ],
          },
        ],
      },
      gate_outcome: {
        decision: "warn",
        warned_by: ["extrace.s2.typosquat"],
      },
    };
    const model = adaptJob(baseDto({ status: "completed", static_report: dto }));
    expect(model.staticReport).not.toBeNull();
    expect(model.staticReport?.decision).toBe("warn");
    expect(model.staticReport?.decisionLabel).toBe("Warn");
    expect(model.staticReport?.warnedBy).toEqual(["extrace.s2.typosquat"]);
    expect(model.staticReport?.findings).toHaveLength(1);
    expect(model.staticReport?.findings[0].severityLabel).toBe("High");
    expect(model.staticReport?.findings[0].evidenceCount).toBe(1);
  });
});

describe("adaptStaticReport", () => {
  it("flags partial coverage when a tool degraded", () => {
    const dto: StaticAnalysisReportDto = {
      detection_report: {
        findings: [],
        partial: true,
        tool_executions: [
          {
            tool: "semgrep",
            version: "1.164.0",
            rules_loaded: 4,
            findings_emitted: 0,
            duration_ms: 10,
            status: "timeout",
            error_count: 1,
          },
        ],
      },
      gate_outcome: { decision: "allow", allow_reason: "clean" },
    };
    const view = adaptStaticReport(dto);
    expect(view.partial).toBe(true);
    expect(view.decision).toBe("allow");
    expect(view.allowReason).toBe("clean");
    expect(view.toolStatuses[0].status).toBe("timeout");
    expect(view.toolStatuses[0].errorCount).toBe(1);
  });

  it("maps a BLOCK decision with blockedBy rule ids", () => {
    const dto: StaticAnalysisReportDto = {
      detection_report: {
        findings: [
          {
            id: "01HZBLOCK",
            rule_id: "extrace.s2.typosquat",
            rule_version: "1.0.0",
            rule_lifecycle: "production",
            categories: ["attack.T1036"],
            severity: "high",
            confidence: "medium",
            title: "Typosquat of a popular publisher",
            description: "near a popular publisher",
            evidence: [],
          },
        ],
      },
      gate_outcome: {
        decision: "block",
        blocked_by: ["extrace.s2.typosquat"],
      },
    };
    const view = adaptStaticReport(dto);
    expect(view.decision).toBe("block");
    expect(view.decisionLabel).toBe("Block");
    expect(view.blockedBy).toEqual(["extrace.s2.typosquat"]);
    expect(view.warnedBy).toEqual([]);
    expect(view.allowReason).toBeNull();
    expect(view.findings).toHaveLength(1);
    expect(view.findings[0].severityLabel).toBe("High");
  });

  it("tolerates a minimal report with all optional fields omitted", () => {
    const dto: StaticAnalysisReportDto = {
      detection_report: {},
      gate_outcome: { decision: "allow" },
    };
    const view = adaptStaticReport(dto);
    expect(view.decision).toBe("allow");
    expect(view.blockedBy).toEqual([]);
    expect(view.warnedBy).toEqual([]);
    expect(view.allowReason).toBeNull();
    expect(view.partial).toBe(false);
    expect(view.toolStatuses).toEqual([]);
    expect(view.findings).toEqual([]);
  });
});

describe("time-zone wiring (presentation store -> lastUpdatedLabel)", () => {
  // 2026-04-13T10:00:00Z — mid-day so neither zone wraps past midnight.
  const UTC_EPOCH = 1713002400;

  afterEach(() => {
    // The store is a module singleton; reset so the default-zone tests in this
    // file (which assume the browser-local zone) are unaffected by order.
    setTimeZone(DEFAULT_TIME_ZONE);
  });

  it("formats lastUpdatedLabel in the store's selected time zone", () => {
    setTimeZone("UTC");
    const utc = adaptJob(baseDto({ updated_at: UTC_EPOCH })).lastUpdatedLabel;

    setTimeZone("Asia/Tokyo");
    const tokyo = adaptJob(baseDto({ updated_at: UTC_EPOCH })).lastUpdatedLabel;

    // Same instant, different wall-clock: UTC 10:00 vs Tokyo (+9) 19:00.
    expect(utc.startsWith("10")).toBe(true);
    expect(tokyo.startsWith("19")).toBe(true);
    // Regression guard: drop `timeZone: resolveTimeZone()` from formatDate and
    // both collapse to the browser-local zone, so this inequality breaks.
    expect(utc).not.toBe(tokyo);
  });
});
