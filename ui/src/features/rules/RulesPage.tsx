import { startTransition, useMemo, useState, type CSSProperties } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";

import {
  Badge,
  EmptyState,
  Eyebrow,
  Field,
  GhostButton,
  PageTitle,
  Panel,
  Tabs,
  V3,
  type TabSpec,
  type V3Tone,
} from "../../components/v3";
import { apiClient } from "../../lib/api/client";
import { adaptBundle } from "../../lib/adapters/report";
import type {
  ActivationReportView,
  DetectionFindingView,
  RuleExecutionRecordView,
} from "../../lib/types/view-models";
import { RuleDraftSection } from "./RuleDraftSection";

type RulesMode = "registry" | "draft" | "blacklist";
type SeverityFilter = "all" | "critical" | "high" | "medium" | "low";
type StatusFilter = "all" | "fired" | "not_fired" | "error";

const MODE_TABS: TabSpec<RulesMode>[] = [
  { value: "registry", label: "Registry" },
  { value: "draft", label: "Draft" },
  { value: "blacklist", label: "Blacklist" },
];

const SEVERITY_TABS: TabSpec<SeverityFilter>[] = [
  { value: "all", label: "All" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

const STATUS_TABS: TabSpec<StatusFilter>[] = [
  { value: "all", label: "All" },
  { value: "fired", label: "Fired" },
  { value: "not_fired", label: "Not fired" },
  { value: "error", label: "Error" },
];

type RuleRow = {
  rule: RuleExecutionRecordView;
  findings: DetectionFindingView[];
  primaryFinding: DetectionFindingView | null;
  evidence: DetectionFindingView["evidence"];
};

function normalizeSeverity(value: string | null): SeverityFilter {
  if (value === "critical" || value === "high" || value === "medium" || value === "low") return value;
  return "all";
}

function normalizeStatus(value: string | null): StatusFilter {
  if (value === "fired" || value === "not_fired" || value === "error") return value;
  return "all";
}

function severityTone(severity?: DetectionFindingView["severity"]): V3Tone {
  if (severity === "critical" || severity === "high") return "danger";
  if (severity === "medium") return "warn";
  if (severity === "low") return "ok";
  return "neutral";
}

function statusTone(status: RuleExecutionRecordView["status"]): V3Tone {
  if (status === "error") return "danger";
  if (status === "fired") return "accent";
  return "neutral";
}

function severityColor(severity?: DetectionFindingView["severity"]) {
  if (severity === "critical" || severity === "high") return V3.coral;
  if (severity === "medium") return V3.warn;
  if (severity === "low") return V3.ok;
  return V3.rule2;
}

function buildRows(report: ActivationReportView): RuleRow[] {
  const detection = report.detection;
  if (!detection) return [];
  return detection.rulesExecuted.map((rule) => {
    const findings = detection.findings.filter((finding) => finding.ruleId === rule.ruleId);
    return {
      rule,
      findings,
      primaryFinding: findings[0] ?? null,
      evidence: findings.flatMap((finding) => finding.evidence),
    };
  });
}

function matchesStatus(rule: RuleExecutionRecordView, status: StatusFilter) {
  if (status === "all") return true;
  if (status === "not_fired") return rule.status === "silent";
  return rule.status === status;
}

function conditionRows(row: RuleRow) {
  return [
    { k: "rule_id", op: "=", v: row.rule.ruleId },
    { k: "version", op: "=", v: row.rule.ruleVersion || "(n/a)" },
    { k: "lifecycle", op: "=", v: row.rule.lifecycle || "(n/a)" },
    { k: "status", op: "=", v: row.rule.status },
  ];
}

export function RulesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const tabParam = searchParams.get("tab");
  const mode: RulesMode =
    tabParam === "draft" ? "draft" : tabParam === "blacklist" ? "blacklist" : "registry";
  const fromEventId = searchParams.get("from");
  const search = searchParams.get("q") || "";
  const severity = normalizeSeverity(searchParams.get("severity"));
  const status = normalizeStatus(searchParams.get("status"));
  const selectedRuleId = searchParams.get("rule");

  const reportQuery = useQuery({
    queryKey: ["report", "latest"],
    queryFn: async ({ signal }) => {
      const dto = await apiClient.getLatestReportBundle(signal);
      return adaptBundle(dto, "latest");
    },
  });

  const report = reportQuery.data;
  const rows = useMemo(() => (report ? buildRows(report) : []), [report]);
  const filteredRows = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return rows.filter((row) => {
      const finding = row.primaryFinding;
      if (severity !== "all" && finding?.severity !== severity) return false;
      if (!matchesStatus(row.rule, status)) return false;
      if (!needle) return true;
      const haystack = [
        row.rule.ruleId,
        row.rule.ruleVersion,
        row.rule.lifecycle,
        row.rule.statusLabel,
        finding?.title,
        finding?.description,
        finding?.categories.join(" "),
        row.evidence.map((item) => `${item.eventId} ${item.summary}`).join(" "),
      ].join(" ").toLowerCase();
      return haystack.includes(needle);
    });
  }, [rows, search, severity, status]);

  const findingsCount = report?.detection?.findings.length ?? 0;
  const firedCount = rows.filter((row) => row.rule.status === "fired").length;
  const errorCount = rows.filter((row) => row.rule.status === "error").length;

  const setParam = (key: string, value: string) => {
    startTransition(() => {
      const next = new URLSearchParams(searchParams);
      if (!value || value === "all" || (key === "tab" && value === "registry")) {
        next.delete(key);
      } else {
        next.set(key, value);
      }
      setSearchParams(next, { replace: true });
    });
  };

  const toggleRule = (ruleId: string) => {
    startTransition(() => {
      const next = new URLSearchParams(searchParams);
      if (selectedRuleId === ruleId) next.delete("rule");
      else next.set("rule", ruleId);
      setSearchParams(next, { replace: true });
    });
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <header style={{ paddingBottom: 24, borderBottom: `1px solid ${V3.rule}` }}>
        <Eyebrow>Rules</Eyebrow>
        <PageTitle style={{ marginTop: 14, fontSize: 44, lineHeight: 1 }}>Detection registry</PageTitle>
        <p style={{ fontSize: 13.5, color: V3.ink3, marginTop: 14, maxWidth: 720, lineHeight: 1.6 }}>
          Review rule execution, fired findings, and linked evidence without crowding the report or simulation inspector.
        </p>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 18 }}>
          <MonoMetric label="Findings" value={findingsCount} />
          <MonoMetric label="Fired" value={firedCount} />
          <MonoMetric label="Errored" value={errorCount} />
        </div>
      </header>

      <Tabs<RulesMode>
        ariaLabel="Rules mode"
        tabs={MODE_TABS}
        value={mode}
        onChange={(next) => setParam("tab", next)}
      />

      {mode === "draft" ? (
        <RuleDraftSection fromEventId={fromEventId} report={report ?? null} />
      ) : mode === "blacklist" ? (
        <BlacklistDomainsPanel report={report} />
      ) : (
        <RegistryMode
          reportQuery={reportQuery}
          report={report}
          rows={rows}
          filteredRows={filteredRows}
          search={search}
          severity={severity}
          status={status}
          selectedRuleId={selectedRuleId}
          setParam={setParam}
          toggleRule={toggleRule}
          navigate={navigate}
        />
      )}
    </div>
  );
}

function RegistryMode({
  reportQuery,
  report,
  rows,
  filteredRows,
  search,
  severity,
  status,
  selectedRuleId,
  setParam,
  toggleRule,
  navigate,
}: {
  reportQuery: { isLoading: boolean; isError: boolean; error: unknown };
  report: ActivationReportView | undefined;
  rows: RuleRow[];
  filteredRows: RuleRow[];
  search: string;
  severity: SeverityFilter;
  status: StatusFilter;
  selectedRuleId: string | null;
  setParam: (key: string, value: string) => void;
  toggleRule: (ruleId: string) => void;
  navigate: ReturnType<typeof useNavigate>;
}) {
  return (
    <>
      <Panel padded={false}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(260px, 1fr) minmax(0, 1.1fr)",
            gap: 18,
            alignItems: "end",
            padding: "16px 18px",
          }}
        >
          <Field
            label="Search"
            mono
            placeholder="search rule id / title"
            value={search}
            onChange={(value) => setParam("q", value)}
          />
          <div style={{ display: "flex", flexDirection: "column", gap: 12, minWidth: 0 }}>
            <Tabs<SeverityFilter>
              ariaLabel="Severity filter"
              tabs={SEVERITY_TABS}
              value={severity}
              onChange={(next) => setParam("severity", next)}
            />
            <Tabs<StatusFilter>
              ariaLabel="Status filter"
              tabs={STATUS_TABS}
              value={status}
              onChange={(next) => setParam("status", next)}
            />
          </div>
        </div>
      </Panel>

      <Panel bodyStyle={{ padding: 0 }} label="Rule list">
        {reportQuery.isLoading ? (
          <EmptyState eyebrow="Loading" title="Loading rules" body="Fetching latest report bundle." style={{ border: "none" }} />
        ) : reportQuery.isError ? (
          <EmptyState eyebrow="Error" title="Rules unavailable" body={String(reportQuery.error)} style={{ border: "none" }} />
        ) : !report?.detection ? (
          <EmptyState eyebrow="Rules" title="No detection report" body="The latest bundle did not include detection rule data." style={{ border: "none" }} />
        ) : !rows.length ? (
          <EmptyState eyebrow="Rules" title="No rules executed" body="The latest detection report did not include rule execution records." style={{ border: "none" }} />
        ) : !filteredRows.length ? (
          <EmptyState eyebrow="Rules" title="No rules match" body="Adjust search, severity, or status filters." style={{ border: "none" }} />
        ) : (
          <div style={{ display: "flex", flexDirection: "column" }}>
            {filteredRows.map((row, index) => (
              <RuleEntry
                key={`${row.rule.ruleId}-${row.rule.ruleVersion}`}
                row={row}
                expanded={selectedRuleId === row.rule.ruleId}
                isLast={index === filteredRows.length - 1}
                onToggle={() => toggleRule(row.rule.ruleId)}
                onEvidenceClick={(eventId) => navigate(`/reports?report=latest&tab=ledger&event=${encodeURIComponent(eventId)}`)}
              />
            ))}
          </div>
        )}
      </Panel>
    </>
  );
}

const BLACKLIST_STATIC_RULE_ID = "extrace.s4.blacklisted_domain";
const BLACKLIST_DYNAMIC_RULE_ID = "extrace.a7.blacklisted_domain";

const BLACKLIST_GRID: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "minmax(0, 1fr) 96px 96px",
  gap: 12,
  alignItems: "center",
  padding: "8px 12px",
};

function blacklistRowStyle(withBorder: boolean): CSSProperties {
  return {
    ...BLACKLIST_GRID,
    borderBottom: withBorder ? `1px solid ${V3.rule2}` : "none",
  };
}

function extractErrorReason(error: unknown): string {
  // requestJson surfaces the API's JSON detail in the thrown error message; show
  // the human reason if present, else the raw message.
  const message = error instanceof Error ? error.message : String(error);
  const match = message.match(/"reason"\s*:\s*"([^"]+)"/u);
  return match ? match[1] : message;
}

function BlacklistDomainsPanel({ report }: { report: ActivationReportView | undefined }) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["rules", "blacklist-domains"],
    queryFn: ({ signal }) => apiClient.getBlacklistDomains(signal),
  });
  const data = query.data;

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["rules", "blacklist-domains"] });

  const addMutation = useMutation({
    mutationFn: (domain: string) => apiClient.addBlacklistDomain(domain),
    onSuccess: () => {
      setDraft("");
      setError(null);
      void invalidate();
    },
    onError: (err) => setError(extractErrorReason(err)),
  });
  const removeMutation = useMutation({
    mutationFn: (domain: string) => apiClient.removeBlacklistDomain(domain),
    onSuccess: () => {
      setError(null);
      void invalidate();
    },
    onError: (err) => setError(extractErrorReason(err)),
  });
  const busy = addMutation.isPending || removeMutation.isPending;

  const submitAdd = () => {
    const domain = draft.trim();
    if (domain) addMutation.mutate(domain);
  };

  // Blacklist findings in the latest report, lowercased title+description, so we
  // can name which effective domains were actually observed/matched.
  const blacklistFindingTexts = [
    ...(report?.staticReport?.findings ?? []).filter(
      (f) => f.ruleId === BLACKLIST_STATIC_RULE_ID,
    ),
    ...(report?.detection?.findings ?? []).filter(
      (f) => f.ruleId === BLACKLIST_DYNAMIC_RULE_ID,
    ),
  ].map((f) => `${f.title} ${f.description}`.toLowerCase());
  const observed = blacklistFindingTexts.length > 0;
  const observedDomains = (data?.effective ?? []).filter((domain) =>
    blacklistFindingTexts.some((text) => text.includes(domain.toLowerCase())),
  );

  return (
    <Panel label="Blacklist domains">
      {observed ? (
        <div
          style={{
            marginBottom: 14,
            border: `1px solid ${V3.coral}`,
            background: V3.dangerBg,
            padding: "10px 12px",
          }}
        >
          <div className="micro-label" style={{ color: V3.coral }}>
            Observed in latest report
          </div>
          {observedDomains.length ? (
            <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 6 }}>
              {observedDomains.map((domain) => (
                <Badge key={domain} tone="danger">
                  {domain}
                </Badge>
              ))}
            </div>
          ) : (
            <div style={{ marginTop: 6, color: V3.ink3, fontSize: 12.5 }}>
              A blacklisted domain was matched — see the Rules registry for details.
            </div>
          )}
        </div>
      ) : null}

      <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <Field
            label="Add domain"
            mono
            placeholder="e.g. evil.example"
            value={draft}
            onChange={(value) => {
              setDraft(value);
              setError(null);
            }}
          />
        </div>
        <GhostButton
          ariaLabel="Add blacklist domain"
          onClick={submitAdd}
          disabled={busy || !draft.trim()}
        >
          Add
        </GhostButton>
      </div>
      {error ? (
        <div style={{ marginTop: 8, color: V3.coral, fontSize: 12.5, lineHeight: 1.5 }}>
          {error}
        </div>
      ) : null}

      {query.isLoading ? (
        <div style={{ marginTop: 12, color: V3.ink3, fontSize: 13 }}>Loading denylist…</div>
      ) : query.isError ? (
        <div style={{ marginTop: 12, color: V3.coral, fontSize: 13 }}>
          Blacklist unavailable: {String(query.error)}
        </div>
      ) : data ? (
        <div style={{ marginTop: 14 }}>
          <div style={{ border: `1px solid ${V3.rule}` }}>
            <div
              style={{
                ...blacklistRowStyle(true),
                background: V3.paper2,
                borderBottom: `1px solid ${V3.rule}`,
              }}
            >
              <span className="micro-label">Domain</span>
              <span className="micro-label">Source</span>
              <span className="micro-label" style={{ textAlign: "right" }}>
                Action
              </span>
            </div>
            {data.effective.map((domain, index) => {
              const isOperator =
                data.operator.includes(domain) && !data.seed.includes(domain);
              return (
                <div
                  key={domain}
                  style={blacklistRowStyle(index !== data.effective.length - 1)}
                >
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 12,
                      color: V3.ink,
                      wordBreak: "break-all",
                    }}
                  >
                    {domain}
                  </span>
                  <span>
                    <Badge tone={isOperator ? "warn" : "neutral"}>
                      {isOperator ? "operator" : "seed"}
                    </Badge>
                  </span>
                  <span style={{ textAlign: "right" }}>
                    {isOperator ? (
                      <GhostButton
                        ariaLabel={`Remove ${domain}`}
                        onClick={() => removeMutation.mutate(domain)}
                        disabled={busy}
                        style={{ padding: "4px 8px", fontSize: 11 }}
                      >
                        Remove
                      </GhostButton>
                    ) : (
                      <span
                        style={{
                          color: V3.ink4,
                          fontSize: 11,
                          fontFamily: "'JetBrains Mono', monospace",
                        }}
                      >
                        fixed
                      </span>
                    )}
                  </span>
                </div>
              );
            })}
          </div>
          <div
            style={{
              marginTop: 8,
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: V3.ink3,
              letterSpacing: "0.06em",
            }}
          >
            {data.count} domain{data.count === 1 ? "" : "s"} effective ({data.seed.length}{" "}
            seed + {data.operator.length} operator)
          </div>
        </div>
      ) : null}
    </Panel>
  );
}

function MonoMetric({ label, value }: { label: string; value: number }) {
  return (
    <span
      style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 11,
        color: V3.ink3,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
      }}
    >
      {label} · {value}
    </span>
  );
}

function RuleEntry({
  row,
  expanded,
  isLast,
  onToggle,
  onEvidenceClick,
}: {
  row: RuleRow;
  expanded: boolean;
  isLast: boolean;
  onToggle: () => void;
  onEvidenceClick: (eventId: string) => void;
}) {
  const finding = row.primaryFinding;
  const severityLabel = finding?.severityLabel || "No finding";
  const title = finding?.title || row.rule.ruleId;
  const leftColor = severityColor(finding?.severity);

  return (
    <article
      style={{
        borderBottom: isLast ? "none" : `1px solid ${V3.rule}`,
        borderLeft: `3px solid ${leftColor}`,
        background: expanded ? V3.paper2 : "transparent",
      }}
    >
      <button
        type="button"
        onClick={onToggle}
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1fr) auto auto auto",
          gap: 12,
          alignItems: "center",
          width: "100%",
          padding: "16px 18px",
          background: "transparent",
          border: "none",
          color: "inherit",
          textAlign: "left",
          cursor: "pointer",
        }}
      >
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: V3.ink, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {title}
          </div>
          <div
            style={{
              marginTop: 5,
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: V3.ink3,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {row.rule.ruleId} · v{row.rule.ruleVersion || "(n/a)"} · {row.rule.lifecycle.replaceAll("_", " ")}
          </div>
        </div>
        <Badge tone={severityTone(finding?.severity)}>{severityLabel}</Badge>
        <Badge tone={statusTone(row.rule.status)}>{row.rule.statusLabel}</Badge>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11,
            color: V3.ink3,
            whiteSpace: "nowrap",
          }}
        >
          {row.evidence.length} hits
          <span aria-hidden style={{ color: V3.ink4, transform: expanded ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 160ms" }}>
            ›
          </span>
        </span>
      </button>

      {expanded ? (
        <div style={{ padding: "0 18px 18px", display: "grid", gap: 16 }}>
          <section>
            <div className="micro-label">Description</div>
            <p style={{ margin: "8px 0 0", color: V3.ink3, fontSize: 13, lineHeight: 1.6 }}>
              {finding?.description || "This rule did not attach a finding description to the latest report."}
            </p>
          </section>

          <section>
            <div className="micro-label">Why this is suspicious</div>
            <div style={{ marginTop: 8, display: "grid", gap: 6 }}>
              {row.evidence.length ? (
                row.evidence.map((item) => (
                  <div key={`${row.rule.ruleId}-${item.eventId}`} style={{ color: V3.ink3, fontSize: 13, lineHeight: 1.5 }}>
                    {item.summary || item.eventId}
                  </div>
                ))
              ) : (
                <div style={{ color: V3.ink3, fontSize: 13 }}>No fired finding evidence was linked to this rule.</div>
              )}
            </div>
          </section>

          {finding?.categories.length ? (
            <section>
              <div className="micro-label">Categories</div>
              <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 6 }}>
                {finding.categories.map((category) => (
                  <Badge key={`${row.rule.ruleId}-${category}`} tone="neutral">{category}</Badge>
                ))}
              </div>
            </section>
          ) : null}

          {finding?.mitigationHint ? (
            <section style={{ border: `1px solid ${V3.rule}`, background: V3.paper3, padding: "12px 14px" }}>
              <div className="micro-label">Mitigation hint</div>
              <p style={{ margin: "8px 0 0", color: V3.ink3, fontSize: 13, lineHeight: 1.6 }}>{finding.mitigationHint}</p>
            </section>
          ) : null}

          <section>
            <div className="micro-label">Conditions</div>
            <div style={{ marginTop: 10, border: `1px solid ${V3.rule}`, background: V3.paper, padding: "8px 12px" }}>
              {conditionRows(row).map((condition) => (
                <div
                  key={`${row.rule.ruleId}-${condition.k}`}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "130px 56px minmax(0, 1fr)",
                    gap: 10,
                    padding: "6px 0",
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 11,
                    color: V3.ink3,
                    borderBottom: condition.k === "status" ? "none" : `1px dashed ${V3.rule2}`,
                  }}
                >
                  <span style={{ color: V3.ink2 }}>{condition.k}</span>
                  <span>{condition.op}</span>
                  <span style={{ color: V3.ink, wordBreak: "break-all" }}>{condition.v}</span>
                </div>
              ))}
            </div>
          </section>

          <section>
            <div className="micro-label">Linked findings · {row.findings.length}</div>
            <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
              {row.findings.length ? (
                row.findings.map((linkedFinding) => (
                  <div key={linkedFinding.id} style={{ border: `1px solid ${V3.rule}`, background: V3.paper, padding: "10px 12px" }}>
                    <div style={{ color: V3.ink, fontSize: 13, fontWeight: 600 }}>{linkedFinding.title}</div>
                    <div style={{ marginTop: 5, color: V3.ink3, fontSize: 12, lineHeight: 1.5 }}>
                      {linkedFinding.evidence.map((item) => item.summary || item.eventId).join(" · ") || "No evidence references."}
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ color: V3.ink3, fontSize: 13 }}>No detection finding linked to this rule execution.</div>
              )}
            </div>
          </section>

          {row.evidence.length ? (
            <section>
              <div className="micro-label">Linked evidence</div>
              <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 8 }}>
                {row.evidence.map((item) => (
                  <GhostButton
                    key={`${row.rule.ruleId}-${item.eventId}-link`}
                    ariaLabel={`Open evidence ${item.eventId}`}
                    onClick={() => onEvidenceClick(item.eventId)}
                    style={{ padding: "8px 10px", fontSize: 12 }}
                  >
                    {item.eventId}
                  </GhostButton>
                ))}
              </div>
            </section>
          ) : null}

          {row.rule.errorDetail ? (
            <section style={{ border: `1px solid ${V3.coral}`, background: V3.dangerBg, padding: "10px 12px", color: V3.coral, fontSize: 12, lineHeight: 1.5 }}>
              {row.rule.errorDetail}
            </section>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}
