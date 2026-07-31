import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { RulesPage } from "./RulesPage";
import { apiClient } from "../../lib/api/client";
import type { AnalysisBundleDto } from "../../lib/types/contracts";

vi.mock("../../lib/api/client", () => ({
  apiClient: {
    getLatestReportBundle: vi.fn(),
    getWhitelist: vi.fn(),
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
    vi.mocked(apiClient.getWhitelist).mockResolvedValue({
      domains: [
        {
          domain: "vscode-cdn.net",
          organization_id: "microsoft-vscode",
          organization: "Microsoft / Visual Studio Code",
          organization_kind: "company",
          purpose: "Visual Studio Code CDN",
          source_url: "https://code.visualstudio.com/docs/setup/network",
        },
        {
          domain: "registry.npmjs.org",
          organization_id: "npm",
          organization: "npm",
          organization_kind: "company",
          purpose: "Official npm public package registry",
          source_url: "https://docs.npmjs.com/cli/v7/using-npm/registry/",
        },
      ],
      organizations: [
        {
          id: "microsoft-vscode",
          name: "Microsoft / Visual Studio Code",
          kind: "company",
          publishers: ["ms-python", "ms-vscode"],
          extensions: ["ms-python.python"],
        },
        {
          id: "npm",
          name: "npm",
          kind: "company",
          publishers: [],
          extensions: [],
        },
      ],
      extension_identities: ["ms-python.python"],
      domain_filtered_rule_ids: [
        "extrace.a1.credential_read_then_network",
        "extrace.a2.startup_network_beacon",
        "extrace.a4.workspace_exfil",
        "extrace.a8.reverse_shell",
      ],
      domain_count: 2,
      organization_count: 2,
      publisher_count: 2,
      extension_count: 1,
    });
  });

  it("renders the complete catalog without requesting the latest scan", () => {
    renderPage();

    expect(screen.getByText("Detection registry")).toBeInTheDocument();
    expect(screen.getByText("35 / 35 visible")).toBeInTheDocument();
    expect(screen.getByText("Wildcard activation")).toBeInTheDocument();
    expect(screen.getByText("Credential read → network")).toBeInTheDocument();
    expect(screen.queryByText("Not evaluated")).not.toBeInTheDocument();
    expect(screen.queryByText("No scan")).not.toBeInTheDocument();
    expect(screen.queryByText(/scan overlay/iu)).not.toBeInTheDocument();
    expect(apiClient.getLatestReportBundle).not.toHaveBeenCalled();
  });

  it("ignores legacy execution status parameters in the catalog view", () => {
    renderPage("/rules?status=fired");

    expect(screen.getByText("35 / 35 visible")).toBeInTheDocument();
    expect(screen.getByText("Wildcard activation")).toBeInTheDocument();
    expect(screen.getByText("Credential read → network")).toBeInTheDocument();
    expect(screen.queryByRole("tablist", { name: "Status filter" })).not.toBeInTheDocument();
    expect(screen.queryByText("Execution")).not.toBeInTheDocument();
  });

  it("lists the static catalog independently from static reports", () => {
    renderPage("/rules?stream=static");

    expect(screen.getByText("26 / 35 visible")).toBeInTheDocument();
    expect(screen.getByText("Wildcard activation")).toBeInTheDocument();
    expect(screen.getByText("RMM-as-RAT (BYOSC)")).toBeInTheDocument();
    expect(screen.queryByText("No rules match")).not.toBeInTheDocument();
    expect(apiClient.getLatestReportBundle).not.toHaveBeenCalled();
  });

  it("does not expose latest-report failures in the registry", () => {
    vi.mocked(apiClient.getLatestReportBundle).mockRejectedValue(
      new Error("latest bundle unavailable"),
    );

    renderPage("/rules?stream=static");

    expect(screen.getByText("26 / 35 visible")).toBeInTheDocument();
    expect(screen.getByText("Wildcard activation")).toBeInTheDocument();
    expect(screen.queryByText(/unavailable/iu)).not.toBeInTheDocument();
    expect(apiClient.getLatestReportBundle).not.toHaveBeenCalled();
  });

  it("renders catalog metadata instead of execution results", () => {
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

    expect(screen.getByText("Credential read → network")).toBeInTheDocument();
    expect(screen.queryByText("Credential file read")).not.toBeInTheDocument();
    expect(screen.queryByText(/extrace.audit.noop/u)).not.toBeInTheDocument();
    expect(screen.getByText("Registry controls")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Rule id or title")).toBeInTheDocument();
    expect(screen.getByRole("tablist", { name: "Stream filter" })).toBeInTheDocument();
    expect(screen.getByRole("tablist", { name: "Severity filter" })).toBeInTheDocument();
    expect(screen.queryByRole("tablist", { name: "Status filter" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /credential read → network/iu }));
    expect(screen.getByText("Threat family")).toBeInTheDocument();
    expect(screen.getAllByText("Credential Access").length).toBeGreaterThan(0);
    expect(screen.queryByText("Mitigation hint")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Open evidence file-1" })).not.toBeInTheDocument();
    expect(apiClient.getLatestReportBundle).not.toHaveBeenCalled();
  });

  it("lists static pre-check rules with a Static stream label", async () => {
    renderPage();

    expect(screen.getByText("Exfiltration webhook")).toBeInTheDocument();
    expect(screen.getByText("Crypto address awareness")).toBeInTheDocument();
    expect(screen.getAllByText("static").length).toBeGreaterThan(0);
    expect(screen.queryByText("Fired")).not.toBeInTheDocument();
    expect(apiClient.getLatestReportBundle).not.toHaveBeenCalled();
  });

  it("renders the editable blacklist panel in its own tab", async () => {
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
    expect(screen.queryByText("Observed in latest report")).not.toBeInTheDocument();
    expect(apiClient.getLatestReportBundle).not.toHaveBeenCalled();
  });

  it("renders the reviewed whitelist with domains, owners, and publisher scope", async () => {
    renderPage("/rules?tab=whitelist");

    expect(await screen.findByRole("tab", { name: "Whitelist" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(await screen.findByText("Whitelist scope")).toBeInTheDocument();
    expect(screen.getByText("vscode-cdn.net")).toBeInTheDocument();
    expect(screen.getAllByText("Microsoft / Visual Studio Code").length).toBeGreaterThan(0);
    expect(screen.getByText("registry.npmjs.org")).toBeInTheDocument();
    expect(screen.getByText("ms-python · ms-vscode")).toBeInTheDocument();
    expect(screen.getByText("extrace.a8.reverse_shell")).toBeInTheDocument();
    expect(screen.getByText(/provenance context only/iu)).toBeInTheDocument();
    expect(apiClient.getBlacklistDomains).not.toHaveBeenCalled();
    expect(apiClient.getLatestReportBundle).not.toHaveBeenCalled();
  });

  it("adds an operator blacklist domain via the panel input", async () => {
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

  it("keeps blacklist configuration independent from report findings", async () => {
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

    expect(await screen.findByText("Blacklist domains")).toBeInTheDocument();
    expect(screen.queryByText("Observed in latest report")).not.toBeInTheDocument();
    expect(await screen.findAllByText("custom.test")).toHaveLength(1);
    expect(apiClient.getLatestReportBundle).not.toHaveBeenCalled();
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
