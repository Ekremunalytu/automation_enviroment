import type {
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
