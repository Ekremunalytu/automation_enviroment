import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { RulesPage } from "./RulesPage";
import { apiClient } from "../../lib/api/client";
import type { AnalysisBundleDto } from "../../lib/types/contracts";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    getLatestReportBundle: vi.fn(),
  },
}));

function renderPage(entry = "/rules") {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[entry]}>
        <Routes>
          <Route element={<RulesPage />} path="/rules" />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function bundleWithRules(rules: NonNullable<AnalysisBundleDto["detection_report"]["rules_executed"]>): AnalysisBundleDto {
  return {
    activation_report: {
      report_version: 2,
      target_extension_expected: "publisher.tool",
      signal_summary: {},
      target_extension_observed: true,
      trigger_plan_applied: true,
      verification_gap: 0,
      run_quality: "high",
      evidence_events: [
        {
          event_id: "file-1",
          kind: "file",
          timestamp: "2026-04-13T10:00:06Z",
          rel_time_s: 6,
          collector: "strace",
          actor: "extension",
          extension_id: "publisher.tool",
          path: "/workspace/.env",
          operation: "read",
          sensitive: true,
          summary: "Sensitive file read",
        },
      ],
    },
    detection_report: {
      schema_version: "1",
      activation_report_ref: "activation_report_demo.json",
      analyzed_extension: {
        publisher: "publisher",
        name: "tool",
        version: "1.0.0",
      },
      findings: rules.length
        ? [
            {
              id: "finding-1",
              rule_id: "extrace.a1.credential_read",
              rule_version: "1.0.0",
              rule_lifecycle: "production",
              categories: ["attack.T1555"],
              severity: "critical",
              confidence: "high",
              title: "Credential file read",
              description: "The extension read a credential-bearing path.",
              evidence: [
                {
                  type: "filesystem_read",
                  event_id: "file-1",
                  summary: "Sensitive file read",
                },
              ],
              adversary_class: "A1",
              mitigation_hint: "Rotate credentials and remove the extension.",
            },
          ]
        : [],
      verdict: rules.length ? "malicious" : "clean",
      verdict_rationale: rules.length ? "critical finding with high confidence" : "no rules fired",
      rules_executed: rules,
      generated_at: "2026-04-20T09:00:00Z",
    },
  } as AnalysisBundleDto;
}

describe("RulesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the header while loading", () => {
    vi.mocked(apiClient.getLatestReportBundle).mockReturnValue(new Promise<AnalysisBundleDto>(() => undefined));

    renderPage();

    expect(screen.getByText("Detection registry")).toBeInTheDocument();
    expect(screen.getByText("Loading rules")).toBeInTheDocument();
  });

  it("renders an empty state when the bundle has no rulesExecuted", async () => {
    vi.mocked(apiClient.getLatestReportBundle).mockResolvedValue(bundleWithRules([]));

    renderPage();

    expect(await screen.findByText("No rules executed")).toBeInTheDocument();
  });

  it("renders rule rows when the bundle includes rules", async () => {
    vi.mocked(apiClient.getLatestReportBundle).mockResolvedValue(
      bundleWithRules([
        {
          rule_id: "extrace.a1.credential_read",
          rule_version: "1.0.0",
          lifecycle: "production",
          status: "fired",
          finding_ids: ["finding-1"],
        },
        {
          rule_id: "extrace.audit.noop",
          rule_version: "1.0.0",
          lifecycle: "draft",
          status: "silent",
          finding_ids: [],
        },
      ]),
    );

    renderPage();

    expect(await screen.findByText("Credential file read")).toBeInTheDocument();
    expect(screen.getAllByText(/extrace.audit.noop/u).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: /credential file read/iu }));
    expect(screen.getByText("Mitigation hint")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open evidence file-1" })).toBeInTheDocument();
  });

  it("renders Registry/Draft mode tabs and shows the empty draft state without ?from", async () => {
    vi.mocked(apiClient.getLatestReportBundle).mockResolvedValue(bundleWithRules([]));

    renderPage("/rules?tab=draft");

    expect(await screen.findByRole("tab", { name: "Registry" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Draft" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Draft" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("No event selected")).toBeInTheDocument();
  });

  it("renders the Draft preview with copy buttons and a disabled save-to-file stub", async () => {
    vi.mocked(apiClient.getLatestReportBundle).mockResolvedValue(
      bundleWithRules([
        {
          rule_id: "extrace.a1.credential_read",
          rule_version: "1.0.0",
          lifecycle: "production",
          status: "fired",
          finding_ids: ["finding-1"],
        },
      ]),
    );
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    renderPage("/rules?tab=draft&from=file-1");

    await screen.findByText("YAML preview");
    expect(screen.getByText("JSON preview")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Copy YAML" }));
    expect(writeText).toHaveBeenCalled();
    const yamlPayload = writeText.mock.calls[0]?.[0] as string;
    expect(yamlPayload).toContain("severity:");

    const saveButton = screen.getByRole("button", { name: /save to file/i });
    expect(saveButton).toBeDisabled();
    expect(saveButton).toHaveAttribute("data-feature-stub", "rule-save");
  });
});
