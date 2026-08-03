import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";

import type {
  StaticArtifactInventoryEntryDto,
  StaticReportArtifactDto,
} from "../../lib/types/contracts";
import { StaticAnalysisInspectionSection } from "./StaticAnalysisInspectionSection";

const artifactInventory: StaticArtifactInventoryEntryDto[] = Array.from(
  { length: 52 },
  (_, index) => {
    if (index === 0) {
      return {
        relative_path: "node_modules/@scope/pkg/index.js",
        role: "dependency_runtime",
        format: "text",
        size_bytes: 512,
        dependency_owner: "@scope/pkg",
        is_vendor: true,
        is_minified: true,
        entrypoint_reachability: "none",
        disposition: "deep_scan",
        disposition_reasons: ["inhouse_finding_evidence"],
      };
    }
    if (index === 1) {
      return {
        relative_path: "dist/oversized.js",
        role: "first_party_runtime",
        format: "text",
        size_bytes: 40 * 1024 * 1024,
        entrypoint_reachability: "direct",
        disposition: "skipped",
        disposition_reasons: ["target_too_large"],
      };
    }
    return {
      relative_path: `docs/file-${String(index).padStart(2, "0")}-${"x".repeat(40)}.md`,
      role: "documentation",
      format: "text",
      size_bytes: index,
      entrypoint_reachability: "none",
      disposition: "inventory_only",
      disposition_reasons: ["non_runtime_artifact"],
    };
  },
);

const artifact: StaticReportArtifactDto = {
  filename: "static_report_inspection.json",
  modified: 1785497400,
  static_report: {
    gate_outcome: {
      decision: "block",
      blocked_by: ["extrace.s10.reverse_shell"],
    },
    detection_report: {
      partial: true,
      severity_counts: {
        critical: 1,
        high: 0,
        medium: 1,
        low: 0,
        info: 1,
      },
      coverage: {
        files_discovered: 12,
        files_selected: 11,
        files_eligible: 10,
        files_scanned: 11,
        files_parsed: 9,
        bytes_considered: 4096,
        bytes_read: 3584,
        manifest_status: "parsed",
        coverage_reasons: ["unsupported_suffix"],
      },
      tool_executions: [
        {
          tool: "inhouse",
          version: "1.0.0",
          rules_loaded: 26,
          findings_emitted: 2,
          duration_ms: 18,
          status: "ok",
        },
        {
          tool: "semgrep",
          version: "1.164.0",
          rules_loaded: 16,
          findings_emitted: 1,
          duration_ms: 1300,
          status: "partial",
          error_count: 1,
        },
      ],
      artifact_inventory: artifactInventory,
      findings: [
        {
          id: "finding-reverse-shell",
          rule_id: "extrace.s10.reverse_shell",
          rule_version: "1.1.0",
          rule_lifecycle: "production",
          categories: ["attack.T1059", "extrace.ext.reverse_shell"],
          severity: "critical",
          confidence: "high",
          title: "Connected reverse shell",
          description: "The same shell and socket variables form a two-way bridge.",
          evidence: [
            {
              type: "source_file",
              relative_path: "dist/extension.js",
              line_number: 44,
              snippet: "socket.pipe(proc.stdin)",
              tool: "inhouse",
            },
            {
              type: "source_file",
              relative_path: "dist/extension.js",
              line_number: 45,
              snippet: "proc.stdout.pipe(socket)",
              tool: "inhouse",
            },
          ],
        },
        {
          id: "finding-network",
          rule_id: "extrace.s5.network_indicators",
          rule_version: "1.2.0",
          rule_lifecycle: "production",
          categories: ["network"],
          severity: "medium",
          confidence: "medium",
          title: "Runtime endpoint",
          description: "Source binds an endpoint to a runtime request.",
          evidence: [
            {
              type: "source_file",
              relative_path: "src/client.ts",
              line_number: 12,
              snippet: "fetch(endpoint)",
              tool: "inhouse",
            },
          ],
        },
        {
          id: "finding-native",
          rule_id: "extrace.s3.embedded_native_binary",
          rule_version: "1.2.0",
          rule_lifecycle: "production",
          categories: ["inventory"],
          severity: "info",
          confidence: "low",
          title: "Native inventory",
          description: "A native helper is present for analyst inventory.",
          evidence: [
            {
              type: "binary_file",
              relative_path: "bin/helper.node",
              tool: "inhouse",
            },
          ],
        },
      ],
    },
  },
};

function renderPage() {
  return render(<StaticAnalysisInspectionSection artifact={artifact} />);
}

describe("StaticAnalysisInspectionSection", () => {
  it("renders measured gate, coverage, severity, and tool statistics", async () => {
    renderPage();

    expect(
      await screen.findByRole("heading", { name: "Static analysis inspection" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText(/static_report_inspection\.json/u),
    ).toBeInTheDocument();
    const gate = screen.getByLabelText("Static gate inspection");
    expect(within(gate).getByText("block")).toBeInTheDocument();
    expect(within(gate).getByText("2 actionable")).toBeInTheDocument();
    expect(screen.getByLabelText("Findings: 3")).toBeInTheDocument();
    expect(screen.getByLabelText("Evidence locations: 4")).toBeInTheDocument();
    expect(screen.getByLabelText("Files scanned: 11/12")).toBeInTheDocument();
    expect(
      screen.getByRole("img", {
        name: "11 of 12 discovered files scanned; 9 parsed",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("list", { name: "Static tool execution statistics" }),
    ).toHaveTextContent("Semgrep");
    expect(screen.getByRole("list", { name: "Static coverage gaps" })).toHaveTextContent(
      "Unsupported Suffix",
    );
  });

  it("filters findings by severity and evidence-path search", async () => {
    renderPage();

    const findings = await screen.findByRole("list", {
      name: "Static analysis findings",
    });
    expect(within(findings).getByText("Connected reverse shell")).toBeInTheDocument();
    expect(within(findings).getByText("Runtime endpoint")).toBeInTheDocument();
    expect(within(findings).getByText("Native inventory")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Info: 1 findings" }),
    );
    await waitFor(() => {
      expect(within(findings).queryByText("Connected reverse shell")).not.toBeInTheDocument();
    });
    expect(within(findings).getByText("Native inventory")).toBeInTheDocument();
    expect(within(findings).queryByText("Runtime endpoint")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
    fireEvent.change(screen.getByLabelText("Search findings"), {
      target: { value: "helper.node" },
    });
    await waitFor(() => {
      expect(within(findings).queryByText("Runtime endpoint")).not.toBeInTheDocument();
    });
    expect(within(findings).getByText("Native inventory")).toBeInTheDocument();
    expect(within(findings).queryByText("Connected reverse shell")).not.toBeInTheDocument();
  });

  it("opens exact source evidence without hiding the match snippet", async () => {
    renderPage();

    const disclosure = await screen.findByText("Inspect 2 evidence locations");
    fireEvent.click(disclosure);

    const evidence = screen.getByRole("list", {
      name: "Evidence for Connected reverse shell",
    });
    expect(within(evidence).getByText("dist/extension.js:44")).toBeInTheDocument();
    expect(within(evidence).getByText("socket.pipe(proc.stdin)")).toBeInTheDocument();
    expect(within(evidence).getByText("proc.stdout.pipe(socket)")).toBeInTheDocument();
  });

  it("filters and paginates the bounded artifact inventory", async () => {
    renderPage();

    const inventory = await screen.findByRole("table", {
      name: "Artifact inventory",
    });
    expect(screen.getByLabelText("Artifact inventory summary")).toHaveTextContent(
      "Deep scan 1",
    );
    expect(within(inventory).getByText("node_modules/@scope/pkg/index.js")).toBeInTheDocument();
    expect(within(inventory).queryByText(/file-51-/u)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Next inventory page" }));
    expect(await within(inventory).findByText(/file-51-/u)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Artifact disposition"), {
      target: { value: "skipped" },
    });
    await waitFor(() => {
      expect(within(inventory).getByText("dist/oversized.js")).toBeInTheDocument();
    });
    expect(within(inventory).queryByText("node_modules/@scope/pkg/index.js")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Artifact disposition"), {
      target: { value: "all" },
    });
    fireEvent.change(screen.getByLabelText("Search artifact inventory"), {
      target: { value: "@SCOPE/PKG" },
    });
    await waitFor(() => {
      expect(within(inventory).getByText("node_modules/@scope/pkg/index.js")).toBeInTheDocument();
    });
    expect(within(inventory).queryByText("dist/oversized.js")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search artifact inventory"), {
      target: { value: "" },
    });
    fireEvent.change(screen.getByLabelText("Artifact role"), {
      target: { value: "dependency_runtime" },
    });
    await waitFor(() => {
      expect(within(inventory).getByText("node_modules/@scope/pkg/index.js")).toBeInTheDocument();
    });
    expect(within(inventory).queryByText(/file-02-/u)).not.toBeInTheDocument();
  });

  it("renders a legacy static report with no artifact inventory", async () => {
    render(
      <StaticAnalysisInspectionSection
        artifact={{
          ...artifact,
          static_report: {
            ...artifact.static_report,
            detection_report: {
              ...artifact.static_report.detection_report,
              artifact_inventory: undefined,
            },
          },
        }}
      />,
    );

    expect(await screen.findByRole("heading", { name: "Artifact inventory" })).toBeInTheDocument();
    expect(screen.getByText("0 discovered")).toBeInTheDocument();
    expect(screen.getByText("No artifact matches the active inventory filters.")).toBeInTheDocument();
  });

});
