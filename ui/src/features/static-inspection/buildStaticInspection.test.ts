import type { StaticAnalysisReportDto } from "../../lib/types/contracts";
import {
  buildStaticInspection,
  evidenceLocation,
  filterStaticFindings,
} from "./buildStaticInspection";

const report: StaticAnalysisReportDto = {
  detection_report: {
    findings: [
      {
        rule_id: "extrace.s10.reverse_shell",
        rule_version: "1.1.0",
        rule_lifecycle: "production",
        categories: ["attack.T1059"],
        severity: "critical",
        confidence: "high",
        title: "Reverse shell",
        description: "Connected shell and socket bridge.",
        evidence: [
          {
            type: "source_file",
            relative_path: "dist/extension.js",
            line_number: 44,
            snippet: "socket.pipe(proc.stdin)",
            tool: "inhouse",
          },
        ],
      },
      {
        rule_id: "extrace.s3.embedded_native_binary",
        rule_version: "1.2.0",
        rule_lifecycle: "production",
        categories: ["inventory"],
        severity: "info",
        confidence: "low",
        title: "Native inventory",
        description: "Native artifact present.",
        evidence: [
          {
            type: "binary_file",
            relative_path: "bin/helper.node",
            tool: "inhouse",
          },
        ],
      },
    ],
    tool_executions: [
      {
        tool: "inhouse",
        version: "1",
        rules_loaded: 26,
        findings_emitted: 2,
        duration_ms: 12,
        status: "ok",
      },
      {
        tool: "semgrep",
        version: "1",
        rules_loaded: 16,
        findings_emitted: 0,
        duration_ms: 1100,
        status: "timeout",
      },
    ],
    coverage: {
      files_discovered: 10,
      files_selected: 9,
      files_eligible: 8,
      files_scanned: 9,
      files_parsed: 8,
      bytes_considered: 4000,
      bytes_read: 3500,
    },
  },
  gate_outcome: { decision: "block", blocked_by: ["extrace.s10.reverse_shell"] },
};

describe("buildStaticInspection", () => {
  it("derives honest findings, coverage, evidence, and tool statistics", () => {
    const summary = buildStaticInspection(report);

    expect(summary.severityCounts.critical).toBe(1);
    expect(summary.severityCounts.info).toBe(1);
    expect(summary.actionableFindings).toBe(1);
    expect(summary.evidenceCount).toBe(2);
    expect(summary.firedRules).toBe(2);
    expect(summary.coveragePct).toBe(90);
    expect(summary.parsePct).toBe(89);
    expect(summary.healthyTools).toBe(1);
    expect(summary.evidenceFiles[0]).toEqual({
      path: "bin/helper.node",
      count: 1,
    });
  });

  it("filters by severity and searches rule, content, and evidence paths", () => {
    const findings = report.detection_report.findings ?? [];

    expect(filterStaticFindings(findings, "critical", "")).toHaveLength(1);
    expect(filterStaticFindings(findings, "all", "helper.node")[0]?.severity).toBe(
      "info",
    );
    expect(filterStaticFindings(findings, "all", "t1059")[0]?.rule_id).toBe(
      "extrace.s10.reverse_shell",
    );
  });

  it("formats evidence locations without inventing a line number", () => {
    const evidence = report.detection_report.findings?.[0]?.evidence?.[0];
    expect(evidence && evidenceLocation(evidence)).toBe("dist/extension.js:44");
    expect(
      evidenceLocation({
        type: "binary_file",
        relative_path: "bin/helper.node",
        tool: "inhouse",
      }),
    ).toBe("bin/helper.node");
  });
});
