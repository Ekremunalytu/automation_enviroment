import type {
  ActivationReportDto,
  AnalyzeJobStatusDto,
  MarketplaceDownloadResponseDto,
  MarketplaceExtensionDto,
  ReportListItemDto,
} from "../types/contracts";
import { requestJson } from "./http";

export const apiClient = {
  listReports() {
    return requestJson<ReportListItemDto[]>("/api/activations");
  },
  getLatestReport() {
    return requestJson<ActivationReportDto>("/api/activations/latest");
  },
  getReportByName(name: string) {
    return requestJson<ActivationReportDto>(`/api/activations/${name}`);
  },
  searchMarketplace(query: string) {
    const params = new URLSearchParams({ query, page_size: "18" });
    return requestJson<MarketplaceExtensionDto[]>(`/api/marketplace/search?${params.toString()}`);
  },
  downloadMarketplaceExtension(publisher: string, name: string, version: string) {
    return requestJson<MarketplaceDownloadResponseDto>("/api/marketplace/download", {
      method: "POST",
      body: JSON.stringify({ publisher, name, version }),
    });
  },
  startAnalysisJob(publisher: string, name: string, version: string) {
    return requestJson<AnalyzeJobStatusDto>("/api/marketplace/analyze/start", {
      method: "POST",
      body: JSON.stringify({ publisher, name, version }),
    });
  },
  getAnalysisJob(jobId: string) {
    return requestJson<AnalyzeJobStatusDto>(`/api/marketplace/analyze/${jobId}`);
  },
};
