import type {
  ReportBundleDto,
  ActivationReportDto,
  AnalyzeJobStatusDto,
  ExecutorPreferencesResponseDto,
  ExecutorPreferencesUpdateRequestDto,
  MarketplaceDownloadResponseDto,
  MarketplaceExtensionDto,
  OfflineExtensionDto,
  ReportListItemDto,
  StaticReportArtifactDto,
  SystemHealthResponseDto,
  VsixThresholdsResponseDto,
  VsixThresholdsUpdateRequestDto,
} from "../types/contracts";
import { requestJson } from "./http";

export interface BlacklistDomainsDto {
  /** Shipped baseline denylist (read-only, not operator-removable). */
  seed: string[];
  /** Operator-added domains (editable / removable). */
  operator: string[];
  /** seed ∪ operator — what the detection rules actually use. */
  effective: string[];
  count: number;
}

export interface WhitelistDomainDto {
  domain: string;
  organization_id: string;
  organization: string;
  organization_kind: string;
  purpose: string;
  source_url: string | null;
}

export interface WhitelistOrganizationDto {
  id: string;
  name: string;
  kind: string;
  publishers: string[];
  extensions: string[];
}

export interface WhitelistDto {
  domains: WhitelistDomainDto[];
  organizations: WhitelistOrganizationDto[];
  extension_identities: string[];
  domain_filtered_rule_ids: string[];
  domain_count: number;
  organization_count: number;
  publisher_count: number;
  extension_count: number;
}

export const apiClient = {
  listReports(signal?: AbortSignal) {
    return requestJson<ReportListItemDto[]>("/api/activations", { signal });
  },
  getLatestReport(signal?: AbortSignal) {
    return requestJson<ActivationReportDto>("/api/activations/latest", { signal });
  },
  getReportByName(name: string, signal?: AbortSignal) {
    return requestJson<ActivationReportDto>(`/api/activations/${name}`, { signal });
  },
  getReportBundleByName(name: string, signal?: AbortSignal) {
    return requestJson<ReportBundleDto>(`/api/activations/${name}/bundle`, { signal });
  },
  async getLatestReportBundle(signal?: AbortSignal) {
    const latest = await requestJson<ActivationReportDto>("/api/activations/latest", {
      signal,
    });
    const filename = latest._metadata?.filename;
    if (!filename) {
      throw new Error("Latest activation report did not include a filename.");
    }
    return requestJson<ReportBundleDto>(`/api/activations/${filename}/bundle`, {
      signal,
    });
  },
  getLatestStaticReport(signal?: AbortSignal) {
    return requestJson<StaticReportArtifactDto>("/api/activations/static/latest", {
      signal,
    });
  },
  searchMarketplace(query: string, signal?: AbortSignal) {
    const params = new URLSearchParams({ query, page_size: "18" });
    return requestJson<MarketplaceExtensionDto[]>(`/api/marketplace/search?${params.toString()}`, { signal });
  },
  downloadMarketplaceExtension(
    publisher: string,
    name: string,
    version: string,
    signal?: AbortSignal,
  ) {
    return requestJson<MarketplaceDownloadResponseDto>("/api/marketplace/download", {
      method: "POST",
      body: JSON.stringify({ publisher, name, version }),
      signal,
    });
  },
  startAnalysisJob(
    publisher: string,
    name: string,
    version: string,
    signal?: AbortSignal,
  ) {
    return requestJson<AnalyzeJobStatusDto>("/api/marketplace/analyze/start", {
      method: "POST",
      body: JSON.stringify({ publisher, name, version }),
      signal,
    });
  },
  listOfflineExtensions(signal?: AbortSignal) {
    return requestJson<OfflineExtensionDto[]>("/api/marketplace/offline/list", {
      signal,
    });
  },
  ingestOfflineExtension(filename: string, signal?: AbortSignal) {
    return requestJson<MarketplaceDownloadResponseDto>(
      "/api/marketplace/offline/ingest",
      {
        method: "POST",
        body: JSON.stringify({ filename }),
        signal,
      },
    );
  },
  getAnalysisJob(jobId: string, signal?: AbortSignal) {
    return requestJson<AnalyzeJobStatusDto>(`/api/marketplace/analyze/${jobId}`, {
      signal,
    });
  },
  cancelAnalysisJob(jobId: string, signal?: AbortSignal) {
    return requestJson<AnalyzeJobStatusDto>(
      `/api/marketplace/analyze/${jobId}/cancel`,
      { method: "POST", signal },
    );
  },
  getHealth(signal?: AbortSignal) {
    return requestJson<{ status: string; service: string }>("/api/health", { signal });
  },
  getSystemHealth(signal?: AbortSignal) {
    return requestJson<SystemHealthResponseDto>("/api/system/health", { signal });
  },
  getBlacklistDomains(signal?: AbortSignal) {
    return requestJson<BlacklistDomainsDto>("/api/rules/blacklist-domains", { signal });
  },
  getWhitelist(signal?: AbortSignal) {
    return requestJson<WhitelistDto>("/api/rules/whitelist", { signal });
  },
  addBlacklistDomain(domain: string, signal?: AbortSignal) {
    return requestJson<BlacklistDomainsDto>("/api/rules/blacklist-domains", {
      method: "POST",
      body: JSON.stringify({ domain }),
      signal,
    });
  },
  removeBlacklistDomain(domain: string, signal?: AbortSignal) {
    return requestJson<BlacklistDomainsDto>(
      `/api/rules/blacklist-domains/${encodeURIComponent(domain)}`,
      { method: "DELETE", signal },
    );
  },
  getSecurityThresholds(signal?: AbortSignal) {
    return requestJson<VsixThresholdsResponseDto>(
      "/api/settings/security/thresholds",
      { signal },
    );
  },
  updateSecurityThresholds(
    payload: VsixThresholdsUpdateRequestDto,
    signal?: AbortSignal,
  ) {
    return requestJson<VsixThresholdsResponseDto>(
      "/api/settings/security/thresholds",
      {
        method: "PUT",
        body: JSON.stringify(payload),
        signal,
      },
    );
  },
  getExecutorPreferences(signal?: AbortSignal) {
    return requestJson<ExecutorPreferencesResponseDto>(
      "/api/settings/executor/preferences",
      { signal },
    );
  },
  updateExecutorPreferences(
    payload: ExecutorPreferencesUpdateRequestDto,
    signal?: AbortSignal,
  ) {
    return requestJson<ExecutorPreferencesResponseDto>(
      "/api/settings/executor/preferences",
      {
        method: "PUT",
        body: JSON.stringify(payload),
        signal,
      },
    );
  },
};
