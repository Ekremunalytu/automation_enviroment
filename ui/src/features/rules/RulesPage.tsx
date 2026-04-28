import { startTransition, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
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

type SeverityFilter = "all" | "critical" | "high" | "medium" | "low";
type StatusFilter = "all" | "fired" | "not_fired" | "error";

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
      if (!value || value === "all") next.delete(key);
      else next.set(key, value);
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
    </div>
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
