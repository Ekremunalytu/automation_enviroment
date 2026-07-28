import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { RulesPage } from "./RulesPage";
import { apiClient } from "../../lib/api/client";
import type { AnalysisBundleDto } from "../../lib/types/contracts";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    getLatestReportBundle: vi.fn(),
    getBlacklistDomains: vi.fn(),
    addBlacklistDomain: vi.fn(),
    removeBlacklistDomain: vi.fn(),
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
    vi.mocked(apiClient.getBlacklistDomains).mockResolvedValue({
      seed: ["evil.example"],
      operator: ["custom.test"],
      effective: ["custom.test", "evil.example"],
      count: 2,
    });
  });

  it("renders the header while loading", () => {
    vi.mocked(apiClient.getLatestReportBundle).mockReturnValue(new Promise<AnalysisBundleDto>(() => undefined));

    renderPage();

    expect(screen.getByText("Detection registry")).toBeInTheDocument();
    expect(screen.queryByText("Rules")).not.toBeInTheDocument();
    expect(screen.queryByText(/^Findings ·/u)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Fired ·/u)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Errored ·/u)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Review rule execution/u),
    ).not.toBeInTheDocument();
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
    expect(screen.getByText("Registry controls")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Rule id or title")).toBeInTheDocument();
    expect(screen.getByRole("tablist", { name: "Stream filter" })).toBeInTheDocument();
    expect(screen.getByRole("tablist", { name: "Severity filter" })).toBeInTheDocument();
    expect(screen.getByRole("tablist", { name: "Status filter" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /credential file read/iu }));
    expect(screen.getByText("Mitigation hint")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open evidence file-1" })).toBeInTheDocument();
  });

  it("lists static pre-check rules with a Static stream label", async () => {
    const bundle = bundleWithRules([]);
    (bundle as unknown as { static_report: unknown }).static_report = {
      detection_report: {
        findings: [
          {
            rule_id: "extrace.s8.exfil_webhook",
            rule_version: "1.0.0",
            rule_lifecycle: "production",
            categories: ["attack.T1567"],
            severity: "high",
            confidence: "high",
            title: "Exfiltration webhook",
            description: "Hardcoded Discord webhook ingestion endpoint.",
          },
        ],
        tool_executions: [
          { tool: "inhouse", version: "1.0.0", rules_loaded: 12, findings_emitted: 1, duration_ms: 5, status: "ok" },
        ],
      },
      gate_outcome: { decision: "warn", warned_by: ["extrace.s8.exfil_webhook"] },
    };
    vi.mocked(apiClient.getLatestReportBundle).mockResolvedValue(bundle);

    renderPage();

    // The fired static rule renders by title even though there are no dynamic rules…
    expect(await screen.findByText("Exfiltration webhook")).toBeInTheDocument();
    // …a silent static catalog rule (no finding) is enumerated too…
    expect(screen.getByText("Crypto address awareness")).toBeInTheDocument();
    // …and static rows carry a stream label (rendered uppercase via CSS; DOM text is lowercase).
    expect(screen.getAllByText("static").length).toBeGreaterThan(0);
  });

  it("renders the editable blacklist panel in its own tab", async () => {
    vi.mocked(apiClient.getLatestReportBundle).mockResolvedValue(bundleWithRules([]));

    renderPage("/rules?tab=blacklist");

    expect(await screen.findByRole("tab", { name: "Blacklist" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(await screen.findByText("Blacklist domains")).toBeInTheDocument();
    // Seed baseline chip + operator-added chip both render.
    expect(await screen.findByText("evil.example")).toBeInTheDocument();
    expect(screen.getByText("custom.test")).toBeInTheDocument();
    expect(screen.getByText(/2 domains effective/u)).toBeInTheDocument();
    // Operator chips are removable; seed chips are not.
    expect(screen.getByRole("button", { name: "Remove custom.test" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Remove evil.example" })).not.toBeInTheDocument();
    // The default bundle has no blacklist finding -> no "observed" badge.
    expect(screen.queryByText("Observed in latest report")).not.toBeInTheDocument();
  });

  it("adds an operator blacklist domain via the panel input", async () => {
    vi.mocked(apiClient.getLatestReportBundle).mockResolvedValue(bundleWithRules([]));
    vi.mocked(apiClient.addBlacklistDomain).mockResolvedValue({
      seed: ["evil.example"],
      operator: ["custom.test", "mal.test"],
      effective: ["custom.test", "evil.example", "mal.test"],
      count: 3,
    });

    renderPage("/rules?tab=blacklist");
    await screen.findByText("Blacklist domains");

    fireEvent.change(screen.getByPlaceholderText("e.g. evil.example"), {
      target: { value: "mal.test" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add blacklist domain" }));

    await waitFor(() =>
      expect(apiClient.addBlacklistDomain).toHaveBeenCalledWith("mal.test"),
    );
  });

  it("removes an operator blacklist domain via its chip", async () => {
    vi.mocked(apiClient.getLatestReportBundle).mockResolvedValue(bundleWithRules([]));
    vi.mocked(apiClient.removeBlacklistDomain).mockResolvedValue({
      seed: ["evil.example"],
      operator: [],
      effective: ["evil.example"],
      count: 1,
    });

    renderPage("/rules?tab=blacklist");
    await screen.findByText("Blacklist domains");

    fireEvent.click(await screen.findByRole("button", { name: "Remove custom.test" }));

    await waitFor(() =>
      expect(apiClient.removeBlacklistDomain).toHaveBeenCalledWith("custom.test"),
    );
  });

  it("names the observed blacklisted domains when a finding fires", async () => {
    const bundle = bundleWithRules([
      {
        rule_id: "extrace.a7.blacklisted_domain",
        rule_version: "1.0.0",
        lifecycle: "production",
        status: "fired",
        finding_ids: ["bl-1"],
      },
    ]);
    bundle.detection_report.findings = [
      {
        id: "bl-1",
        rule_id: "extrace.a7.blacklisted_domain",
        rule_version: "1.0.0",
        rule_lifecycle: "production",
        categories: ["attack.T1071"],
        severity: "high",
        confidence: "high",
        title: "Outbound connection to a blacklisted domain",
        description:
          "The extension contacted blacklisted domain(s) custom.test (observed host(s): c2.custom.test).",
        evidence: [],
        adversary_class: "A7",
        mitigation_hint: "Block the connection.",
      },
    ];
    vi.mocked(apiClient.getLatestReportBundle).mockResolvedValue(bundle);

    renderPage("/rules?tab=blacklist");

    expect(await screen.findByText("Observed in latest report")).toBeInTheDocument();
    // custom.test is named both in the observed section and the operator chip list.
    expect(screen.getAllByText("custom.test").length).toBeGreaterThan(1);
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
