import type { CSSProperties, FormEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";

import {
  Badge,
  Dialog,
  EmptyState,
  Eyebrow,
  GhostButton,
  PageTitle,
  SectionTitle,
  SolidButton,
  V3,
} from "../../components/v3";
import { rememberJobId } from "../simulation";
import { ApiError } from "../../lib/api/http";
import { apiClient } from "../../lib/api/client";
import type {
  MarketplaceDownloadResponseDto,
  MarketplaceExtensionDto,
  VsixExtractionMetricsDto,
  VsixThresholdBreachDetail,
} from "../../lib/types/contracts";

function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GiB`;
  }
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MiB`;
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(1)} KiB`;
  }
  return `${bytes} B`;
}

function formatBreachLabel(kind: VsixThresholdBreachDetail["breach_kind"]): string {
  switch (kind) {
    case "entry_count":
      return "File count";
    case "uncompressed_size":
      return "Uncompressed size";
    case "compression_ratio":
      return "Compression ratio";
  }
}

function formatBreachValue(
  kind: VsixThresholdBreachDetail["breach_kind"],
  value: number,
): string {
  if (kind === "uncompressed_size") return formatBytes(value);
  if (kind === "compression_ratio") return `${value.toFixed(1)}:1`;
  return value.toLocaleString();
}

function isThresholdBreach(detail: unknown): detail is VsixThresholdBreachDetail {
  if (!detail || typeof detail !== "object") return false;
  const obj = detail as Record<string, unknown>;
  return obj.error === "vsix_threshold_breach" && typeof obj.breach_kind === "string";
}

type ArtifactKey = { publisher: string; name: string; version: string };

function artifactKey({ publisher, name, version }: ArtifactKey) {
  return `${publisher}.${name}@${version}`;
}

function fmtInstalls(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1).replace(/\.0$/u, "")}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

const QUICK_QUERIES = ["python", "copilot", "eslint", "prettier"];

export function MarketplacePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryParam = searchParams.get("q") || "";
  const [query, setQuery] = useState(queryParam);
  const [ready, setReady] = useState<Record<string, boolean>>({});
  const [downloadsInFlight, setDownloadsInFlight] = useState<Record<string, boolean>>({});
  const [actionError, setActionError] = useState<string | null>(null);
  const [breachDetail, setBreachDetail] = useState<VsixThresholdBreachDetail | null>(
    null,
  );
  const [lastDownload, setLastDownload] = useState<
    | {
        artifact: string;
        metrics: VsixExtractionMetricsDto;
      }
    | null
  >(null);
  const downloadsInFlightRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    setQuery(queryParam);
  }, [queryParam]);

  const searchQuery = useQuery({
    enabled: Boolean(queryParam),
    queryKey: ["marketplace-search", queryParam],
    queryFn: ({ signal }) => apiClient.searchMarketplace(queryParam, signal),
  });

  const downloadMutation = useMutation({
    mutationFn: ({ publisher, name, version }: ArtifactKey) =>
      apiClient.downloadMarketplaceExtension(publisher, name, version),
  });

  const analyzeMutation = useMutation({
    mutationFn: ({ publisher, name, version }: ArtifactKey) =>
      apiClient.startAnalysisJob(publisher, name, version),
    onSuccess: (job) => {
      setActionError(null);
      rememberJobId(job.job_id);
      navigate(`/simulation?job=${job.job_id}&tab=live`);
    },
    onError: (error) => {
      setActionError(error instanceof ApiError ? error.message : "Analysis could not be started.");
    },
  });

  const submit = (rawQuery: string) => {
    setActionError(null);
    const next = new URLSearchParams(searchParams);
    const trimmed = rawQuery.trim();
    if (trimmed) next.set("q", trimmed);
    else next.delete("q");
    setSearchParams(next, { replace: true });
  };

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    submit(query);
  };

  const setDownloadPending = (key: string, pending: boolean) => {
    if (pending) downloadsInFlightRef.current.add(key);
    else downloadsInFlightRef.current.delete(key);

    setDownloadsInFlight((current) => {
      if (pending) return { ...current, [key]: true };
      if (!current[key]) return current;
      const next = { ...current };
      delete next[key];
      return next;
    });
  };

  const onDownload = (publisher: string, name: string, version: string) => {
    const key = artifactKey({ publisher, name, version });
    if (downloadsInFlightRef.current.has(key)) return;

    setActionError(null);
    setDownloadPending(key, true);
    downloadMutation.mutate(
      { publisher, name, version },
      {
        onSuccess: (result: MarketplaceDownloadResponseDto) => {
          setReady((current) => ({
            ...current,
            [artifactKey(result)]: true,
          }));
          if (result.vsix_metrics) {
            setLastDownload({
              artifact: artifactKey(result),
              metrics: result.vsix_metrics,
            });
          }
        },
        onError: (error) => {
          // Threshold-breach 422 → render the dedicated popup instead of
          // dumping the structured detail JSON into the inline banner.
          if (error instanceof ApiError && isThresholdBreach(error.detail)) {
            setBreachDetail(error.detail);
            return;
          }
          setActionError(
            error instanceof ApiError ? error.message : "Download failed.",
          );
        },
        onSettled: () => {
          setDownloadPending(key, false);
        },
      },
    );
  };

  const activeAnalyzeKey =
    analyzeMutation.isPending && analyzeMutation.variables ? artifactKey(analyzeMutation.variables) : null;

  const results = searchQuery.data ?? [];
  const matchCount = results.length;
  const sectionTitle = !queryParam
    ? "Awaiting query"
    : searchQuery.isLoading
      ? `Searching “${queryParam}”…`
      : matchCount === 0
        ? `No matches for “${queryParam}”`
        : `Results for “${queryParam}” · ${matchCount} match${matchCount === 1 ? "" : "es"}`;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 40 }}>
      <header style={{ paddingBottom: 24, borderBottom: `1px solid ${V3.rule2}` }}>
        <Eyebrow>Extension intake</Eyebrow>
        <PageTitle style={{ marginTop: 14 }}>Find, download, analyze.</PageTitle>
        <p
          style={{
            fontSize: 15,
            color: V3.ink3,
            marginTop: 14,
            maxWidth: 580,
            lineHeight: 1.6,
          }}
        >
          Search the VS Code marketplace, shortlist a candidate, then hand it to the sandbox.
          Each download adds one entry to the local catalog.
        </p>
      </header>

      <section>
        <Eyebrow style={{ marginBottom: 12 }}>Search marketplace</Eyebrow>
        <form
          onSubmit={onSubmit}
          style={{
            display: "grid",
            gridTemplateColumns: "auto minmax(0, 1fr) auto",
            gap: 0,
            alignItems: "stretch",
            maxWidth: 720,
            border: `1px solid ${V3.ink}`,
            borderRadius: 0,
            background: V3.card,
          }}
        >
          <div
            style={{
              padding: "0 14px",
              display: "flex",
              alignItems: "center",
              borderRight: `1px solid ${V3.rule}`,
              background: V3.paper2,
            }}
          >
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                color: V3.ink3,
              }}
            >
              find ›
            </span>
          </div>
          <input
            placeholder="python, eslint, prettier, github copilot…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            style={{
              background: "transparent",
              border: "none",
              outline: "none",
              padding: "14px 16px",
              fontSize: 15,
              color: V3.ink,
              fontFamily: "'JetBrains Mono', monospace",
              fontVariantLigatures: "none",
            }}
          />
          <button
            type="submit"
            style={{
              background: V3.ink,
              color: V3.paper,
              border: "none",
              padding: "0 22px",
              fontSize: 13,
              fontWeight: 500,
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            Search ↵
          </button>
        </form>

        <div style={{ marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 11,
              color: V3.ink3,
              marginRight: 4,
              alignSelf: "center",
            }}
          >
            try:
          </span>
          {QUICK_QUERIES.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => {
                setQuery(q);
                submit(q);
              }}
              style={{
                background: V3.paper2,
                border: `1px solid ${V3.rule}`,
                borderRadius: 0,
                padding: "4px 10px",
                fontSize: 11.5,
                color: V3.ink2,
                cursor: "pointer",
                fontFamily: "'JetBrains Mono', monospace",
                transition: "all 140ms",
              }}
              onMouseEnter={(event) => {
                event.currentTarget.style.borderColor = V3.ink;
                event.currentTarget.style.background = V3.card;
              }}
              onMouseLeave={(event) => {
                event.currentTarget.style.borderColor = V3.rule;
                event.currentTarget.style.background = V3.paper2;
              }}
            >
              {q}
            </button>
          ))}
        </div>
      </section>

      <section>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            marginBottom: 16,
            gap: 16,
            flexWrap: "wrap",
          }}
        >
          <div>
            <Eyebrow>Results</Eyebrow>
            <SectionTitle style={{ marginTop: 10 }}>{sectionTitle}</SectionTitle>
          </div>
          {queryParam && matchCount > 0 ? (
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                color: V3.ink3,
              }}
            >
              sorted by installs
            </span>
          ) : null}
        </div>

        {actionError ? (
          <div
            style={{
              border: `1px solid ${V3.coral}`,
              background: V3.dangerBg,
              color: V3.coral,
              padding: "12px 16px",
              fontSize: 13,
              fontFamily: "'JetBrains Mono', monospace",
              marginBottom: 16,
            }}
            role="alert"
          >
            {actionError}
          </div>
        ) : null}

        {lastDownload ? (
          <VsixIntegrityBanner
            artifact={lastDownload.artifact}
            metrics={lastDownload.metrics}
            onDismiss={() => setLastDownload(null)}
          />
        ) : null}

        {!queryParam ? (
          <EmptyState
            eyebrow="Ready"
            title="No query yet"
            body="Enter an extension name or keyword above to populate results from the marketplace catalog."
          />
        ) : searchQuery.isLoading ? (
          <EmptyState eyebrow="Searching" title="Fetching results" body="Marketplace metadata is loading." />
        ) : searchQuery.isError ? (
          <EmptyState eyebrow="Error" title="Marketplace request failed" body={String(searchQuery.error)} />
        ) : matchCount === 0 ? (
          <EmptyState eyebrow="Empty" title="Nothing matched" body="Try a different keyword." />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {results.map((extension) => {
              const key = artifactKey(extension);
              const isReady = Boolean(ready[key]);
              const busy = Boolean(downloadsInFlight[key]) || activeAnalyzeKey === key;
              return (
                <ResultCard
                  key={key}
                  extension={extension}
                  isReady={isReady}
                  busy={busy}
                  onDownload={() => onDownload(extension.publisher, extension.name, extension.version)}
                  onAnalyze={() =>
                    analyzeMutation.mutate({
                      publisher: extension.publisher,
                      name: extension.name,
                      version: extension.version,
                    })
                  }
                />
              );
            })}
          </div>
        )}
      </section>

      <Dialog
        open={breachDetail !== null}
        onClose={() => setBreachDetail(null)}
        eyebrow="Threshold breach"
        title={
          breachDetail
            ? `${breachDetail.publisher}.${breachDetail.name}@${breachDetail.version} exceeds ${formatBreachLabel(breachDetail.breach_kind).toLowerCase()}`
            : ""
        }
        tone="danger"
        actions={
          <>
            <GhostButton onClick={() => setBreachDetail(null)}>Dismiss</GhostButton>
            <SolidButton
              onClick={() => {
                setBreachDetail(null);
                navigate("/settings?section=security");
              }}
            >
              Open Security settings
            </SolidButton>
          </>
        }
      >
        {breachDetail ? (
          <>
            <p style={{ margin: 0 }}>
              The download was rejected before extraction completed. The VSIX
              archive trips the configured{" "}
              <strong style={{ color: V3.ink }}>
                {formatBreachLabel(breachDetail.breach_kind).toLowerCase()}
              </strong>{" "}
              guard, which protects against zip-bomb / DoS extraction patterns.
              Raise the threshold from{" "}
              <strong style={{ color: V3.ink }}>Settings → Security</strong> if
              you trust this publisher and want to proceed.
            </p>
            <dl
              style={{
                margin: "18px 0 0",
                display: "grid",
                gridTemplateColumns: "auto 1fr",
                rowGap: 8,
                columnGap: 18,
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
              }}
            >
              <dt style={{ color: V3.ink3 }}>Threshold</dt>
              <dd style={{ margin: 0, color: V3.ink }}>
                {formatBreachLabel(breachDetail.breach_kind)} ({breachDetail.threshold_name})
              </dd>
              <dt style={{ color: V3.ink3 }}>Configured limit</dt>
              <dd style={{ margin: 0, color: V3.ink }}>
                {formatBreachValue(breachDetail.breach_kind, breachDetail.threshold_value)}
              </dd>
              <dt style={{ color: V3.ink3 }}>Observed</dt>
              <dd style={{ margin: 0, color: V3.coral }}>
                {formatBreachValue(breachDetail.breach_kind, breachDetail.observed_value)}
              </dd>
            </dl>
          </>
        ) : null}
      </Dialog>
    </div>
  );
}

type VsixIntegrityBannerProps = {
  artifact: string;
  metrics: VsixExtractionMetricsDto;
  onDismiss: () => void;
};

function VsixIntegrityBanner({ artifact, metrics, onDismiss }: VsixIntegrityBannerProps) {
  // The banner is the post-download mirror of the threshold-breach popup
  // — both surfaces flag VSIX-side risk, so we keep the accent rail in
  // the coral/danger family rather than the green/ok family. Future
  // refinement (FOLLOWUP vsix-banner-proximity-coloring) can downgrade
  // to amber/green when metrics sit comfortably below the configured
  // thresholds.
  return (
    <div
      role="status"
      style={{
        border: `1px solid ${V3.rule}`,
        borderLeft: `3px solid ${V3.coral}`,
        background: V3.paper2,
        padding: "12px 16px",
        marginBottom: 16,
        display: "flex",
        gap: 16,
        alignItems: "center",
        flexWrap: "wrap",
      }}
    >
      <div style={{ flex: "1 1 auto", minWidth: 240 }}>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: V3.coral,
          }}
        >
          ● VSIX integrity
        </div>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: V3.ink2,
            marginTop: 4,
          }}
        >
          {artifact}: {metrics.file_count.toLocaleString()} entries ·{" "}
          {formatBytes(metrics.uncompressed_size)} uncompressed ·{" "}
          {metrics.compression_ratio.toFixed(2)}:1 ratio
          {metrics.rejected_entry_count > 0
            ? ` · ${metrics.rejected_entry_count} entries skipped`
            : ""}
        </div>
      </div>
      <GhostButton onClick={onDismiss}>Dismiss</GhostButton>
    </div>
  );
}

type ResultCardProps = {
  extension: MarketplaceExtensionDto;
  isReady: boolean;
  busy: boolean;
  onDownload: () => void;
  onAnalyze: () => void;
};

function ResultCard({ extension, isReady, busy, onDownload, onAnalyze }: ResultCardProps) {
  const [hover, setHover] = useState(false);

  return (
    <article
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "space-between",
        gap: 20,
        alignItems: "flex-start",
        padding: "18px 20px",
        background: V3.card,
        border: `1px solid ${hover ? V3.rule2 : V3.rule}`,
        borderRadius: 0,
        transition: "border-color 140ms",
      }}
    >
      <div style={{ minWidth: 0, flex: "1 1 320px" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
          <div
            style={{
              fontFamily: "'Manrope', sans-serif",
              fontSize: 22,
              fontWeight: 600,
              color: V3.ink,
              letterSpacing: 0,
            }}
          >
            {extension.displayName}
          </div>
          {isReady ? <Badge tone="ok">Ready</Badge> : <Badge tone="neutral">Marketplace</Badge>}
        </div>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11.5,
            color: V3.ink3,
            marginTop: 6,
          }}
        >
          {extension.publisher}.{extension.name}
        </div>
        <p
          style={{
            fontSize: 13.5,
            color: V3.ink2,
            lineHeight: 1.55,
            marginTop: 10,
            maxWidth: 600,
          }}
        >
          {extension.description}
        </p>

        <div style={{ marginTop: 12, display: "flex", gap: 0, alignItems: "center", flexWrap: "wrap" }}>
          <Meta k="version" v={`v${extension.version}`} />
          <Divider />
          <Meta k="installs" v={fmtInstalls(extension.installs)} />
          <Divider />
          <Meta k="rating" v={`${extension.rating.toFixed(1)} / 5`} />
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8, alignItems: "flex-end", flexShrink: 0, marginLeft: "auto" }}>
        {!isReady ? (
          <SolidButton disabled={busy} onClick={onDownload}>
            {busy ? "Downloading…" : "Download"}
          </SolidButton>
        ) : (
          <SolidButton disabled={busy} onClick={onAnalyze}>
            {busy ? "Starting…" : "Analyze"}
          </SolidButton>
        )}
        {isReady ? (
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              color: V3.ok,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
            }}
          >
            ● in catalog
          </span>
        ) : null}
      </div>
    </article>
  );
}

const META_STYLE: CSSProperties = {
  display: "inline-flex",
  flexDirection: "column",
  gap: 2,
  padding: "0 14px 0 0",
};

function Meta({ k, v }: { k: string; v: string }) {
  return (
    <span style={META_STYLE}>
      <span
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          fontWeight: 500,
          letterSpacing: "0.18em",
          textTransform: "uppercase",
          color: V3.ink3,
        }}
      >
        {k}
      </span>
      <span
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 12.5,
          color: V3.ink,
          fontWeight: 500,
        }}
      >
        {v}
      </span>
    </span>
  );
}

function Divider() {
  return (
    <span
      aria-hidden
      style={{
        width: 1,
        height: 24,
        background: V3.rule,
        margin: "0 14px 0 0",
      }}
    />
  );
}
