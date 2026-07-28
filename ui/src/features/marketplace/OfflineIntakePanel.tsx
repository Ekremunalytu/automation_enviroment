import { useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import {
  Badge,
  EmptyState,
  Eyebrow,
  GhostButton,
  SectionTitle,
  SolidButton,
  V3,
} from "../../components/v3";
import { rememberJobId } from "../simulation";
import { ApiError } from "../../lib/api/http";
import { apiClient } from "../../lib/api/client";
import type {
  MarketplaceDownloadResponseDto,
  OfflineExtensionDto,
  VsixExtractionMetricsDto,
  VsixThresholdBreachDetail,
} from "../../lib/types/contracts";
import type { ArtifactKey } from "./format";
import { artifactKey, formatBytes, isThresholdBreach } from "./format";
import {
  Divider,
  Meta,
  ThresholdBreachDialog,
  VsixIntegrityBanner,
} from "./shared";

export function OfflineIntakePanel({
  dynamicAnalysisEnabled = false,
}: {
  dynamicAnalysisEnabled?: boolean;
}) {
  const navigate = useNavigate();
  const [ingested, setIngested] = useState<Record<string, boolean>>({});
  const [ingestsInFlight, setIngestsInFlight] = useState<Record<string, boolean>>({});
  const [actionError, setActionError] = useState<string | null>(null);
  const [breachDetail, setBreachDetail] = useState<VsixThresholdBreachDetail | null>(
    null,
  );
  const [lastIngest, setLastIngest] = useState<
    | {
        artifact: string;
        metrics: VsixExtractionMetricsDto;
      }
    | null
  >(null);
  const ingestsInFlightRef = useRef<Set<string>>(new Set());

  const listQuery = useQuery({
    queryKey: ["marketplace-offline-list"],
    queryFn: ({ signal }) => apiClient.listOfflineExtensions(signal),
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
      setActionError(
        error instanceof ApiError ? error.message : "Analysis could not be started.",
      );
    },
  });

  const ingestMutation = useMutation({
    mutationFn: (filename: string) => apiClient.ingestOfflineExtension(filename),
  });

  const setIngestPending = (filename: string, pending: boolean) => {
    if (pending) ingestsInFlightRef.current.add(filename);
    else ingestsInFlightRef.current.delete(filename);

    setIngestsInFlight((current) => {
      if (pending) return { ...current, [filename]: true };
      if (!current[filename]) return current;
      const next = { ...current };
      delete next[filename];
      return next;
    });
  };

  const onIngest = (filename: string) => {
    if (ingestsInFlightRef.current.has(filename)) return;

    setActionError(null);
    setIngestPending(filename, true);
    ingestMutation.mutate(filename, {
      onSuccess: (result: MarketplaceDownloadResponseDto) => {
        setIngested((current) => ({ ...current, [filename]: true }));
        if (result.vsix_metrics) {
          setLastIngest({
            artifact: artifactKey(result),
            metrics: result.vsix_metrics,
          });
        }
        // Refresh so the server-side already_ingested flag reconciles with
        // the optimistic local flip.
        void listQuery.refetch();
        if (dynamicAnalysisEnabled) {
          analyzeMutation.mutate({
            publisher: result.publisher,
            name: result.name,
            version: result.version,
          });
        }
      },
      onError: (error) => {
        if (error instanceof ApiError && isThresholdBreach(error.detail)) {
          setBreachDetail(error.detail);
          return;
        }
        setActionError(error instanceof ApiError ? error.message : "Ingest failed.");
      },
      onSettled: () => {
        setIngestPending(filename, false);
      },
    });
  };

  const activeAnalyzeKey =
    analyzeMutation.isPending && analyzeMutation.variables
      ? artifactKey(analyzeMutation.variables)
      : null;

  const records = listQuery.data ?? [];
  const count = records.length;
  const sectionTitle = listQuery.isLoading
    ? "Scanning offline directory…"
    : listQuery.isError
      ? "Offline scan failed"
      : count === 0
        ? "No offline packages"
        : `${count} package${count === 1 ? "" : "s"} staged`;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 40 }}>
      <section>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            gap: 16,
            flexWrap: "wrap",
          }}
        >
          <div>
            <Eyebrow style={{ marginBottom: 10 }}>Offline intake</Eyebrow>
            <SectionTitle>{sectionTitle}</SectionTitle>
          </div>
          <GhostButton disabled={listQuery.isFetching} onClick={() => listQuery.refetch()}>
            {listQuery.isFetching ? "Scanning…" : "Rescan"}
          </GhostButton>
        </div>
        <p
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11.5,
            color: V3.ink3,
            marginTop: 12,
            lineHeight: 1.6,
            maxWidth: 620,
          }}
        >
          Drop <code>.vsix</code> packages into <code>extensions/offline/</code> on the
          host, then rescan. Each package is staged through the same VSIX hardening
          guards as a marketplace download — no network required.
        </p>
      </section>

      <section>
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

        {lastIngest ? (
          <VsixIntegrityBanner
            artifact={lastIngest.artifact}
            metrics={lastIngest.metrics}
            onDismiss={() => setLastIngest(null)}
          />
        ) : null}

        {listQuery.isLoading ? (
          <EmptyState
            eyebrow="Scanning"
            title="Reading offline directory"
            body="Enumerating staged .vsix packages."
          />
        ) : listQuery.isError ? (
          <EmptyState
            eyebrow="Error"
            title="Offline scan failed"
            body={String(listQuery.error)}
          />
        ) : count === 0 ? (
          <EmptyState
            eyebrow="Empty"
            title="No packages found"
            body="Copy one or more .vsix files into extensions/offline/, then press Rescan."
          />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {records.map((record) => {
              const key = artifactKey(record);
              const isReady = record.already_ingested || Boolean(ingested[record.filename]);
              const busy =
                Boolean(ingestsInFlight[record.filename]) || activeAnalyzeKey === key;
              return (
                <OfflineCard
                  key={record.filename}
                  record={record}
                  isReady={isReady}
                  busy={busy}
                  dynamicAnalysisEnabled={dynamicAnalysisEnabled}
                  onIngest={() => onIngest(record.filename)}
                  onAnalyze={() =>
                    analyzeMutation.mutate({
                      publisher: record.publisher,
                      name: record.name,
                      version: record.version,
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

type OfflineCardProps = {
  record: OfflineExtensionDto;
  isReady: boolean;
  busy: boolean;
  dynamicAnalysisEnabled: boolean;
  onIngest: () => void;
  onAnalyze: () => void;
};

function OfflineCard({
  record,
  isReady,
  busy,
  dynamicAnalysisEnabled,
  onIngest,
  onAnalyze,
}: OfflineCardProps) {
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
            {record.displayName}
          </div>
          {isReady ? <Badge tone="ok">Ready</Badge> : <Badge tone="neutral">Offline</Badge>}
        </div>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11.5,
            color: V3.ink3,
            marginTop: 6,
          }}
        >
          {record.publisher && record.name
            ? `${record.publisher}.${record.name}`
            : record.filename}
        </div>
        {record.description ? (
          <p
            style={{
              fontSize: 13.5,
              color: V3.ink2,
              lineHeight: 1.55,
              marginTop: 10,
              maxWidth: 600,
            }}
          >
            {record.description}
          </p>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 0, alignItems: "center", flexWrap: "wrap" }}>
          <Meta k="version" v={record.version ? `v${record.version}` : "—"} />
          <Divider />
          <Meta k="size" v={formatBytes(record.size_bytes)} />
          <Divider />
          <Meta k="file" v={record.filename} />
        </div>
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 8,
          alignItems: "flex-end",
          flexShrink: 0,
          marginLeft: "auto",
        }}
      >
        {!isReady ? (
          <SolidButton disabled={busy} onClick={onIngest}>
            {busy ? "Ingesting…" : "Ingest"}
          </SolidButton>
        ) : (
          <SolidButton
            disabled={busy || !dynamicAnalysisEnabled}
            onClick={onAnalyze}
          >
            {busy
              ? "Starting…"
              : dynamicAnalysisEnabled
                ? "Analyze"
                : "Dynamic scan off"}
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
            ● staged
          </span>
        ) : null}
      </div>
    </article>
  );
}
