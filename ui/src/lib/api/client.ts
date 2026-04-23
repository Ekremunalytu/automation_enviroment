import type {
  AnalysisBundleDto,
  ActivationReportDto,
  AnalyzeJobStatusDto,
  MarketplaceDownloadResponseDto,
  MarketplaceExtensionDto,
  ReportListItemDto,
} from "../types/contracts";
import { requestJson } from "./http";

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
    return requestJson<AnalysisBundleDto>(`/api/activations/${name}/bundle`, { signal });
  },
  async getLatestReportBundle(signal?: AbortSignal) {
    const latest = await requestJson<ActivationReportDto>("/api/activations/latest", {
      signal,
    });
    const filename = latest._metadata?.filename;
    if (!filename) {
      throw new Error("Latest activation report did not include a filename.");
    }
    return requestJson<AnalysisBundleDto>(`/api/activations/${filename}/bundle`, {
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
  getAnalysisJob(jobId: string, signal?: AbortSignal) {
    return requestJson<AnalyzeJobStatusDto>(`/api/marketplace/analyze/${jobId}`, {
      signal,
    });
  },
};
