import { useDeferredValue, useMemo, useState } from "react";

import { Badge, Eyebrow, Field, FONT_MONO, V3 } from "../../components/v3";
import type { StaticFindingDeduplicationRecordDto } from "../../lib/types/contracts";

const PAGE_SIZE = 25;

function titleCase(value: string): string {
  return value
    .split("_")
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(" ");
}

function location(path: string, line?: number | null): string {
  return line ? `${path}:${line}` : path;
}

export function FindingDeduplicationPanel({
  records,
  retainedFindings,
}: {
  records: StaticFindingDeduplicationRecordDto[];
  retainedFindings: number;
}) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const deferredSearch = useDeferredValue(search.trim().toLowerCase());
  const filteredRecords = useMemo(() => {
    if (!deferredSearch) return records;
    return records.filter((record) =>
      [
        record.rule_id,
        record.rule_version,
        record.reason,
        record.canonical_path,
        record.duplicate_path,
        record.evidence_fingerprint,
      ]
        .join(" ")
        .toLowerCase()
        .includes(deferredSearch),
    );
  }, [deferredSearch, records]);
  const pageCount = Math.max(1, Math.ceil(filteredRecords.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const pageRecords = filteredRecords.slice(
    safePage * PAGE_SIZE,
    (safePage + 1) * PAGE_SIZE,
  );

  return (
    <section aria-labelledby="finding-deduplication-title">
      <div
        style={{
          display: "flex",
          alignItems: "end",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 14,
          paddingBottom: 14,
          borderBottom: `1px solid ${V3.rule}`,
        }}
      >
        <div>
          <Eyebrow>Noise control evidence</Eyebrow>
          <h2
            id="finding-deduplication-title"
            style={{ margin: "7px 0 0", color: V3.ink, fontSize: 25, lineHeight: 1.1 }}
          >
            Finding deduplication
          </h2>
        </div>
        <div
          aria-label="Finding deduplication summary"
          style={{ display: "flex", flexWrap: "wrap", gap: 8 }}
        >
          <Badge tone="neutral">Retained {retainedFindings}</Badge>
          <Badge tone={records.length ? "ok" : "neutral"}>
            Suppressed {records.length}
          </Badge>
        </div>
      </div>

      {records.length ? (
        <>
          <div style={{ marginTop: 12, maxWidth: 420 }}>
            <Field
              label="Search deduplication evidence"
              value={search}
              onChange={(value) => {
                setSearch(value);
                setPage(0);
              }}
              placeholder="rule, reason, path, fingerprint…"
              mono
            />
          </div>
          {pageRecords.length ? (
            <div style={{ maxWidth: "100%", overflowX: "auto", marginTop: 12 }}>
              <table
                aria-label="Finding deduplication evidence"
                style={{ width: "100%", minWidth: 780, borderCollapse: "collapse" }}
              >
                <thead>
                  <tr>
                    {[
                      "Rule",
                      "Reason",
                      "Canonical evidence",
                      "Suppressed echo",
                      "Fingerprint",
                    ].map((heading) => (
                      <th key={heading} scope="col" style={headerStyle}>
                        {heading}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {pageRecords.map((record) => (
                    <tr key={record.evidence_fingerprint}>
                      <td style={cellStyle}>
                        <code style={pathStyle}>{record.rule_id}</code>
                        <div style={{ marginTop: 4, color: V3.ink3 }}>
                          v{record.rule_version}
                        </div>
                      </td>
                      <td style={cellStyle}>{titleCase(record.reason)}</td>
                      <td style={cellStyle}>
                        <code style={pathStyle}>
                          {location(record.canonical_path, record.canonical_line_number)}
                        </code>
                      </td>
                      <td style={cellStyle}>
                        <code style={pathStyle}>
                          {location(record.duplicate_path, record.duplicate_line_number)}
                        </code>
                      </td>
                      <td style={cellStyle} title={record.evidence_fingerprint}>
                        <code style={pathStyle}>
                          {record.evidence_fingerprint.slice(0, 12)}
                        </code>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div role="status" style={emptyStateStyle}>
              No deduplication evidence matches the current search.
            </div>
          )}
          {pageCount > 1 ? (
            <nav
              aria-label="Finding deduplication pagination"
              style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 12 }}
            >
              <button
                type="button"
                onClick={() => setPage((current) => Math.max(0, current - 1))}
                disabled={safePage === 0}
                aria-label="Previous deduplication page"
              >
                Previous
              </button>
              <span style={{ color: V3.ink3, fontSize: 11 }}>
                Page {safePage + 1} of {pageCount}
              </span>
              <button
                type="button"
                onClick={() =>
                  setPage((current) => Math.min(pageCount - 1, current + 1))
                }
                disabled={safePage >= pageCount - 1}
                aria-label="Next deduplication page"
              >
                Next
              </button>
            </nav>
          ) : null}
        </>
      ) : (
        <div role="status" style={emptyStateStyle}>
          No exact vendor or source-map finding echo was suppressed.
        </div>
      )}
    </section>
  );
}

const headerStyle = {
  padding: "10px 12px",
  border: `1px solid ${V3.rule}`,
  color: V3.ink3,
  fontFamily: FONT_MONO,
  fontSize: 9,
  textAlign: "left",
} as const;

const cellStyle = {
  padding: "11px 12px",
  border: `1px solid ${V3.rule}`,
  color: V3.ink2,
  fontSize: 10,
  lineHeight: 1.45,
  verticalAlign: "top",
} as const;

const pathStyle = {
  color: V3.ink2,
  fontFamily: FONT_MONO,
  fontSize: 10,
  overflowWrap: "anywhere",
} as const;

const emptyStateStyle = {
  marginTop: 12,
  border: `1px solid ${V3.rule}`,
  padding: "18px 16px",
  color: V3.ink3,
  fontSize: 12,
} as const;
