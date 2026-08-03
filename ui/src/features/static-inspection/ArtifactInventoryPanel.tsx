import { useDeferredValue, useMemo, useState } from "react";

import { Badge, Eyebrow, Field, FONT_MONO, V3 } from "../../components/v3";
import type { StaticArtifactInventoryEntryDto } from "../../lib/types/contracts";

const PAGE_SIZE = 50;

function titleCase(value: string): string {
  return value
    .split("_")
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(" ");
}

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KiB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MiB`;
}

export function ArtifactInventoryPanel({
  entries,
}: {
  entries: StaticArtifactInventoryEntryDto[];
}) {
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("all");
  const [disposition, setDisposition] = useState("all");
  const [page, setPage] = useState(1);
  const deferredSearch = useDeferredValue(search.trim().toLowerCase());
  const { counts, roles } = useMemo(() => {
    const roleSet = new Set<StaticArtifactInventoryEntryDto["role"]>();
    const nextCounts = { deep: 0, inventory: 0, skipped: 0, vendor: 0, minified: 0 };
    for (const entry of entries) {
      roleSet.add(entry.role);
      if (entry.disposition === "deep_scan") nextCounts.deep += 1;
      if (entry.disposition === "inventory_only") nextCounts.inventory += 1;
      if (entry.disposition === "skipped") nextCounts.skipped += 1;
      if (entry.is_vendor) nextCounts.vendor += 1;
      if (entry.is_minified) nextCounts.minified += 1;
    }
    return { counts: nextCounts, roles: [...roleSet].sort() };
  }, [entries]);
  const filtered = useMemo(
    () =>
      entries.filter((entry) => {
        if (role !== "all" && entry.role !== role) return false;
        if (disposition !== "all" && entry.disposition !== disposition) return false;
        if (!deferredSearch) return true;
        return [
          entry.relative_path,
          entry.dependency_owner ?? "",
          entry.role,
          entry.format,
          entry.disposition,
          entry.disposition_reasons.join(" "),
        ]
          .join(" ")
          .toLowerCase()
          .includes(deferredSearch);
      }),
    [deferredSearch, disposition, entries, role],
  );
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const visible = useMemo(
    () => filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE),
    [filtered, safePage],
  );
  function resetPage(): void {
    setPage(1);
  }

  return (
    <section aria-labelledby="artifact-inventory-title">
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
          <Eyebrow>Selection evidence</Eyebrow>
          <h2
            id="artifact-inventory-title"
            style={{ margin: "7px 0 0", color: V3.ink, fontSize: 25, lineHeight: 1.1 }}
          >
            Artifact inventory
          </h2>
        </div>
        <Badge tone="neutral">{entries.length.toLocaleString()} discovered</Badge>
      </div>

      <div
        aria-label="Artifact inventory summary"
        style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 14 }}
      >
        <Badge tone="ok">Deep scan {counts.deep}</Badge>
        <Badge tone="neutral">Inventory only {counts.inventory}</Badge>
        <Badge tone={counts.skipped ? "warn" : "neutral"}>Skipped {counts.skipped}</Badge>
        <Badge tone="neutral">Vendor {counts.vendor}</Badge>
        <Badge tone="neutral">Minified {counts.minified}</Badge>
      </div>

      <div
        style={{
          display: "grid",
          gap: 10,
          marginTop: 14,
          padding: 14,
          border: `1px solid ${V3.rule}`,
          background: V3.paper3,
        }}
        className="static-inventory-filterbar"
      >
        <Field
          label="Search artifact inventory"
          placeholder="path, owner, role, reason…"
          value={search}
          onChange={(value) => {
            setSearch(value);
            resetPage();
          }}
          mono
        />
        <label style={{ color: V3.ink3, fontSize: 10, fontFamily: FONT_MONO }}>
          Artifact role
          <select
            aria-label="Artifact role"
            value={role}
            onChange={(event) => {
              setRole(event.target.value);
              resetPage();
            }}
            style={{ width: "100%", minHeight: 43, marginTop: 6 }}
          >
            <option value="all">All roles</option>
            {roles.map((item) => (
              <option key={item} value={item}>
                {titleCase(item)}
              </option>
            ))}
          </select>
        </label>
        <label style={{ color: V3.ink3, fontSize: 10, fontFamily: FONT_MONO }}>
          Artifact disposition
          <select
            aria-label="Artifact disposition"
            value={disposition}
            onChange={(event) => {
              setDisposition(event.target.value);
              resetPage();
            }}
            style={{ width: "100%", minHeight: 43, marginTop: 6 }}
          >
            <option value="all">All dispositions</option>
            <option value="deep_scan">Deep scan</option>
            <option value="inventory_only">Inventory only</option>
            <option value="skipped">Skipped</option>
          </select>
        </label>
      </div>

      <div style={{ maxWidth: "100%", overflowX: "auto", marginTop: 12 }}>
        <table
          aria-label="Artifact inventory"
          style={{ width: "100%", minWidth: 860, borderCollapse: "collapse" }}
        >
          <thead>
            <tr>
              {[
                "Path",
                "Role / format",
                "Size",
                "Owner",
                "Reachability",
                "Disposition / reason",
              ].map((heading) => (
                <th
                  key={heading}
                  scope="col"
                  style={{
                    padding: "10px 12px",
                    border: `1px solid ${V3.rule}`,
                    color: V3.ink3,
                    fontFamily: FONT_MONO,
                    fontSize: 9,
                    textAlign: "left",
                  }}
                >
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((entry) => (
              <tr key={entry.relative_path}>
                <td style={cellStyle} title={entry.relative_path}>
                  <code style={pathStyle}>{entry.relative_path}</code>
                </td>
                <td style={cellStyle}>
                  {titleCase(entry.role)} · {titleCase(entry.format)}
                  {entry.is_vendor ? " · vendor" : ""}
                  {entry.is_minified ? " · minified" : ""}
                </td>
                <td style={cellStyle}>{formatBytes(entry.size_bytes)}</td>
                <td style={cellStyle}>{entry.dependency_owner ?? "—"}</td>
                <td style={cellStyle}>{titleCase(entry.entrypoint_reachability ?? "unknown")}</td>
                <td style={cellStyle}>
                  <strong>{titleCase(entry.disposition)}</strong>
                  <div style={{ marginTop: 4, color: V3.ink3 }}>
                    {entry.disposition_reasons.map(titleCase).join(" · ")}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {visible.length === 0 ? (
        <div role="status" style={{ padding: 18, color: V3.ink3 }}>
          No artifact matches the active inventory filters.
        </div>
      ) : null}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 10,
          marginTop: 12,
        }}
      >
        <span style={{ color: V3.ink3, fontFamily: FONT_MONO, fontSize: 10 }}>
          {filtered.length.toLocaleString()} matching · page {safePage}/{pageCount}
        </span>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            type="button"
            disabled={safePage <= 1}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
          >
            Previous inventory page
          </button>
          <button
            type="button"
            disabled={safePage >= pageCount}
            onClick={() => setPage((current) => Math.min(pageCount, current + 1))}
          >
            Next inventory page
          </button>
        </div>
      </div>
    </section>
  );
}

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
