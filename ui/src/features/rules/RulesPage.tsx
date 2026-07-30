import { startTransition, useMemo, useState, type CSSProperties } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";

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
import {
  catalogEntries,
  type RuleCatalogEntry,
  type RuleSeverity,
  type RuleStream,
} from "../../lib/rules/ruleCatalog";
import { RuleDraftSection } from "./RuleDraftSection";

type RulesMode = "registry" | "draft" | "blacklist";
type SeverityFilter = "all" | "critical" | "high" | "medium" | "low";
type StreamFilter = "all" | "dynamic" | "static";

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

const STREAM_TABS: TabSpec<StreamFilter>[] = [
  { value: "all", label: "All streams" },
  { value: "dynamic", label: "Dynamic" },
  { value: "static", label: "Static" },
];

type RuleRow = {
  ruleId: string;
  stream: RuleStream;
  title: string;
  family: string;
  severity: RuleSeverity;
  description: string;
  categories: string[];
};

function normalizeSeverity(value: string | null): SeverityFilter {
  if (value === "critical" || value === "high" || value === "medium" || value === "low") return value;
  return "all";
}

function normalizeStream(value: string | null): StreamFilter {
  if (value === "dynamic" || value === "static") return value;
  return "all";
}

function severityTone(severity?: RuleSeverity | null): V3Tone {
  if (severity === "critical" || severity === "high") return "danger";
  if (severity === "medium") return "warn";
  if (severity === "low") return "ok";
  return "neutral";
}

function severityColor(severity?: RuleSeverity | null) {
  if (severity === "critical" || severity === "high") return V3.coral;
  if (severity === "medium") return V3.warn;
  if (severity === "low") return V3.ok;
  return V3.rule2;
}

function catalogRow(catalog: RuleCatalogEntry): RuleRow {
  return {
    ruleId: catalog.ruleId,
    stream: catalog.stream,
    title: catalog.label,
    family: catalog.family,
    severity: catalog.severity,
    description: catalog.detail || catalog.blurb,
    categories: catalog.techniques.map((technique) => `attack.${technique}`),
  };
}

function buildRows(): RuleRow[] {
  return [...catalogEntries("dynamic"), ...catalogEntries("static")].map(catalogRow);
}

function conditionRows(row: RuleRow) {
  return [
    { k: "rule_id", op: "=", v: row.ruleId },
    { k: "stream", op: "=", v: row.stream },
    { k: "family", op: "=", v: row.family },
    { k: "severity", op: "=", v: row.severity },
  ];
}

export function RulesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get("tab");
  const mode: RulesMode =
    tabParam === "draft" ? "draft" : tabParam === "blacklist" ? "blacklist" : "registry";
  const fromEventId = searchParams.get("from");
  const search = searchParams.get("q") || "";
  const severity = normalizeSeverity(searchParams.get("severity"));
  const stream = normalizeStream(searchParams.get("stream"));
  const selectedRuleId = searchParams.get("rule");

  const reportQuery = useQuery({
    queryKey: ["report", "latest"],
    queryFn: async ({ signal }) => {
      const dto = await apiClient.getLatestReportBundle(signal);
      return adaptBundle(dto, "latest");
    },
    enabled: mode === "draft",
  });

  const report = reportQuery.data;
  const rows = useMemo(() => buildRows(), []);
  const filteredRows = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return rows.filter((row) => {
      if (severity !== "all" && row.severity !== severity) return false;
      if (stream !== "all" && row.stream !== stream) return false;
      if (!needle) return true;
      const haystack = [
        row.ruleId,
        row.stream,
        row.family,
        row.severity,
        row.title,
        row.description,
        row.categories.join(" "),
      ].join(" ").toLowerCase();
      return haystack.includes(needle);
    });
  }, [rows, search, severity, stream]);

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
        <PageTitle style={{ fontSize: 44, lineHeight: 1 }}>Detection registry</PageTitle>
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
        <BlacklistDomainsPanel />
      ) : (
        <RegistryMode
          rows={rows}
          filteredRows={filteredRows}
          search={search}
          severity={severity}
          stream={stream}
          selectedRuleId={selectedRuleId}
          setParam={setParam}
          toggleRule={toggleRule}
        />
      )}
    </div>
  );
}

function RegistryMode({
  rows,
  filteredRows,
  search,
  severity,
  stream,
  selectedRuleId,
  setParam,
  toggleRule,
}: {
  rows: RuleRow[];
  filteredRows: RuleRow[];
  search: string;
  severity: SeverityFilter;
  stream: StreamFilter;
  selectedRuleId: string | null;
  setParam: (key: string, value: string) => void;
  toggleRule: (ruleId: string) => void;
}) {
  return (
    <>
      <Panel
        label="Registry controls"
        right={
          <Eyebrow>
            {filteredRows.length} / {rows.length} visible
          </Eyebrow>
        }
      >
        <div
          style={{
            display: "grid",
            gap: 18,
          }}
        >
          <Field
            label="Find rule"
            mono
            placeholder="Rule id or title"
            value={search}
            onChange={(value) => setParam("q", value)}
            style={{ maxWidth: 520 }}
          />
          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(min(100%, 240px), 1fr))",
              gap: 12,
            }}
          >
            <FilterStrip<StreamFilter>
              label="Stream"
              ariaLabel="Stream filter"
              tabs={STREAM_TABS}
              value={stream}
              onChange={(next) => setParam("stream", next)}
            />
            <FilterStrip<SeverityFilter>
              label="Severity"
              ariaLabel="Severity filter"
              tabs={SEVERITY_TABS}
              value={severity}
              onChange={(next) => setParam("severity", next)}
            />
          </div>
        </div>
      </Panel>

      <Panel bodyStyle={{ padding: 0 }} label="Rule list">
        {!rows.length ? (
          <EmptyState eyebrow="Rules" title="No registry entries" body="The detection catalog is empty." style={{ border: "none" }} />
        ) : !filteredRows.length ? (
          <EmptyState eyebrow="Rules" title="No rules match" body="Adjust search, severity, or stream filters." style={{ border: "none" }} />
        ) : (
          <div style={{ display: "flex", flexDirection: "column" }}>
            {filteredRows.map((row, index) => (
              <RuleEntry
                key={`${row.stream}-${row.ruleId}`}
                row={row}
                expanded={selectedRuleId === row.ruleId}
                isLast={index === filteredRows.length - 1}
                onToggle={() => toggleRule(row.ruleId)}
              />
            ))}
          </div>
        )}
      </Panel>
    </>
  );
}

function FilterStrip<V extends string>({
  label,
  ariaLabel,
  tabs,
  value,
  onChange,
}: {
  label: string;
  ariaLabel: string;
  tabs: TabSpec<V>[];
  value: V;
  onChange: (value: V) => void;
}) {
  return (
    <div
      style={{
        minWidth: 0,
        border: `1px solid ${V3.rule}`,
        background: V3.paper,
      }}
    >
      <div
        style={{
          padding: "9px 11px",
          borderBottom: `1px solid ${V3.rule}`,
          background: V3.paper3,
        }}
      >
        <Eyebrow>{label}</Eyebrow>
      </div>
      <div
        role="tablist"
        aria-label={ariaLabel}
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${tabs.length}, minmax(0, 1fr))`,
        }}
      >
        {tabs.map((tab, index) => {
          const active = tab.value === value;
          return (
            <button
              key={tab.value}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => onChange(tab.value)}
              style={{
                minWidth: 0,
                padding: "10px 3px",
                border: "none",
                borderRight:
                  index < tabs.length - 1
                    ? `1px solid ${V3.rule}`
                    : "none",
                background: active ? V3.coral : "transparent",
                color: active ? V3.paper : V3.ink3,
                cursor: "pointer",
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 8.5,
                fontWeight: active ? 700 : 500,
                letterSpacing: "0.04em",
                lineHeight: 1.25,
                textTransform: "uppercase",
                whiteSpace: "nowrap",
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

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

function BlacklistDomainsPanel() {
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

  return (
    <Panel label="Blacklist domains">
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

function RuleEntry({
  row,
  expanded,
  isLast,
  onToggle,
}: {
  row: RuleRow;
  expanded: boolean;
  isLast: boolean;
  onToggle: () => void;
}) {
  const leftColor = severityColor(row.severity);

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
            {row.title}
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
            {row.ruleId}
          </div>
        </div>
        <StreamTag stream={row.stream} />
        <Badge tone={severityTone(row.severity)}>{row.severity}</Badge>
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
              {row.description}
            </p>
          </section>

          <section>
            <div className="micro-label">Threat family</div>
            <div style={{ marginTop: 8, color: V3.ink3, fontSize: 13 }}>
              {row.family}
            </div>
          </section>

          {row.categories.length ? (
            <section>
              <div className="micro-label">Categories</div>
              <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 6 }}>
                {row.categories.map((category) => (
                  <Badge key={`${row.ruleId}-${category}`} tone="neutral">{category}</Badge>
                ))}
              </div>
            </section>
          ) : null}

          <section>
            <div className="micro-label">Conditions</div>
            <div style={{ marginTop: 10, border: `1px solid ${V3.rule}`, background: V3.paper, padding: "8px 12px" }}>
              {conditionRows(row).map((condition, index, conditions) => (
                <div
                  key={`${row.ruleId}-${condition.k}`}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "130px 56px minmax(0, 1fr)",
                    gap: 10,
                    padding: "6px 0",
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 11,
                    color: V3.ink3,
                    borderBottom:
                      index === conditions.length - 1 ? "none" : `1px dashed ${V3.rule2}`,
                  }}
                >
                  <span style={{ color: V3.ink2 }}>{condition.k}</span>
                  <span>{condition.op}</span>
                  <span style={{ color: V3.ink, wordBreak: "break-all" }}>{condition.v}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </article>
  );
}

function StreamTag({ stream }: { stream: RuleStream }) {
  return (
    <span
      style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 9.5,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        color: V3.ink2,
        border: `1px solid ${V3.rule2}`,
        padding: "2px 6px",
        whiteSpace: "nowrap",
      }}
    >
      {stream}
    </span>
  );
}
