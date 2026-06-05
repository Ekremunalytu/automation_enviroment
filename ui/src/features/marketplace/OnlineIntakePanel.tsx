import type { FormEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";

import {
  Badge,
  Eyebrow,
  EmptyState,
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
import type { ArtifactKey } from "./format";
import { artifactKey, isThresholdBreach } from "./format";
import {
  Divider,
  Meta,
  ThresholdBreachDialog,
  VsixIntegrityBanner,
} from "./shared";

function fmtInstalls(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1).replace(/\.0$/u, "")}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

const QUICK_QUERIES = ["python", "copilot", "eslint", "prettier"];

export function OnlineIntakePanel() {
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

      <ThresholdBreachDialog
        breachDetail={breachDetail}
        onClose={() => setBreachDetail(null)}
      />
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
