import type { FormEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { MarketplaceResultCard } from "../../components/marketplace/MarketplaceResultCard";
import { EmptyState } from "../../components/ui/EmptyState";
import { Panel, PanelHeader } from "../../components/ui/Panel";
import { rememberJobId } from "../simulation/jobStorage";
import { ApiError } from "../../lib/api/http";
import { apiClient } from "../../lib/api/client";

function artifactKey({
  publisher,
  name,
  version,
}: {
  publisher: string;
  name: string;
  version: string;
}) {
  return `${publisher}.${name}@${version}`;
}

export function MarketplacePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryParam = searchParams.get("q") || "";
  const [query, setQuery] = useState(queryParam);
  const [ready, setReady] = useState<Record<string, boolean>>({});
  const [downloadsInFlight, setDownloadsInFlight] = useState<Record<string, boolean>>({});
  const [actionError, setActionError] = useState<string | null>(null);
  const downloadsInFlightRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    setQuery(queryParam);
  }, [queryParam]);

  const searchQuery = useQuery({
    enabled: Boolean(queryParam),
    queryKey: ["marketplace-search", queryParam],
    queryFn: () => apiClient.searchMarketplace(queryParam),
  });

  const downloadMutation = useMutation({
    mutationFn: ({ publisher, name, version }: { publisher: string; name: string; version: string }) =>
      apiClient.downloadMarketplaceExtension(publisher, name, version),
  });

  const analyzeMutation = useMutation({
    mutationFn: ({ publisher, name, version }: { publisher: string; name: string; version: string }) =>
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

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    setActionError(null);
    const next = new URLSearchParams(searchParams);
    if (query.trim()) next.set("q", query.trim());
    else next.delete("q");
    setSearchParams(next, { replace: true });
  };

  const setDownloadPending = (key: string, pending: boolean) => {
    if (pending) downloadsInFlightRef.current.add(key);
    else downloadsInFlightRef.current.delete(key);

    setDownloadsInFlight((current) => {
      if (pending) {
        return { ...current, [key]: true };
      }

      if (!current[key]) {
        return current;
      }

      const next = { ...current };
      delete next[key];
      return next;
    });
  };

  const onDownload = (publisher: string, name: string, version: string) => {
    const key = artifactKey({ publisher, name, version });
    if (downloadsInFlightRef.current.has(key)) {
      return;
    }

    setActionError(null);
    setDownloadPending(key, true);
    downloadMutation.mutate(
      { publisher, name, version },
      {
        onSuccess: (result) => {
          setReady((current) => ({
            ...current,
            [artifactKey(result)]: true,
          }));
        },
        onError: (error) => {
          setActionError(error instanceof ApiError ? error.message : "Download failed.");
        },
        onSettled: () => {
          setDownloadPending(key, false);
        },
      },
    );
  };

  const activeAnalyzeKey =
    analyzeMutation.isPending && analyzeMutation.variables ? artifactKey(analyzeMutation.variables) : null;

  return (
    <div className="space-y-6">
      <section className="page-header">
        <div className="space-y-3">
          <div className="eyebrow">Marketplace</div>
          <h1 className="page-title">Extension intake</h1>
          <p className="max-w-3xl text-sm leading-7 text-mute sm:text-base">
            Search the marketplace, shortlist a candidate, download it once, then jump straight into sandbox analysis.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="info-chip">VS Code catalog</span>
          {queryParam ? <span className="info-chip">Query: {queryParam}</span> : null}
        </div>
      </section>

      <section className="toolbar-surface">
        <form className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-end" onSubmit={onSubmit}>
          <label className="space-y-2">
            <span className="micro-label">Search marketplace</span>
            <input
              className="field-control h-[58px] text-base"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="python, eslint, prettier, github copilot…"
              value={query}
            />
          </label>

          <button className="solid-button h-[58px] min-w-[140px]" type="submit">
            Search
          </button>
        </form>
      </section>

      {queryParam ? (
        <div className="grid gap-3 md:grid-cols-3">
          <SignalTile body={`Results for “${queryParam}”`} title="Search state" />
          <SignalTile body={searchQuery.isLoading ? "Searching…" : `${searchQuery.data?.length || 0} results`} title="Result count" />
          <SignalTile body="Download first, then run only the extension you actually want to inspect." title="Workflow" />
        </div>
      ) : null}

      {actionError ? (
        <div className="rounded-[16px] border border-danger/30 bg-danger/10 px-4 py-4 text-sm leading-6 text-danger">
          {actionError}
        </div>
      ) : null}

      {!queryParam ? (
        <EmptyState
          body="Search the Marketplace to populate downloadable results and launch the sandbox pipeline."
          eyebrow="Ready"
          title="No query yet"
        />
      ) : searchQuery.isLoading ? (
        <EmptyState eyebrow="Searching" body="Marketplace metadata is loading." title="Fetching results" />
      ) : searchQuery.isError ? (
        <EmptyState eyebrow="Error" body={String(searchQuery.error)} title="Marketplace request failed" />
      ) : !(searchQuery.data || []).length ? (
        <EmptyState eyebrow="Empty" body="The Marketplace returned no results for this query." title="Nothing matched" />
      ) : (
        <Panel className="overflow-hidden p-0">
          <div className="border-b border-line px-5 py-5">
            <PanelHeader
              description="Results for review. Download a candidate once, then promote it into the sandbox when you are ready."
              title={`Results for “${queryParam}”`}
            />
          </div>

          <div className="divide-y divide-line px-5">
            {(searchQuery.data || []).map((extension) => {
              const key = artifactKey(extension);
              const busy = Boolean(downloadsInFlight[key]) || activeAnalyzeKey === key;
              return (
                <MarketplaceResultCard
                  busy={busy}
                  extension={extension}
                  key={key}
                  onAnalyze={() =>
                    analyzeMutation.mutate({
                      publisher: extension.publisher,
                      name: extension.name,
                      version: extension.version,
                    })
                  }
                  onDownload={() =>
                    onDownload(extension.publisher, extension.name, extension.version)
                  }
                  readyToAnalyze={ready[key] || false}
                />
              );
            })}
          </div>
        </Panel>
      )}
    </div>
  );
}

function SignalTile({ title, body }: { title: string; body: string }) {
  return (
    <div className="metric-tile">
      <div className="micro-label">{title}</div>
      <div className="mt-3 text-sm leading-6 text-ink">{body}</div>
    </div>
  );
}
