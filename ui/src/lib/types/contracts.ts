export interface ReportListItemDto {
  filename: string;
  size_bytes: number;
  modified: number;
}

export interface EvidenceEventDto {
  event_id?: string;
  kind?: string;
  timestamp?: string;
  rel_time_s?: number | null;
  collector?: string;
  actor?: string;
  scenario_name?: string;
  extension_id?: string;
  activation_event?: string;
  operation?: string;
  protocol?: string;
  host?: string;
  path?: string;
  destination_ip?: string;
  destination_port?: number | null;
  sensitive?: boolean;
  summary?: string;
  raw_context?: Record<string, unknown>;
}

export interface EvidenceLinkDto {
  from_event_id?: string;
  to_event_id?: string;
  link_type?: string;
  confidence?: number;
  reason?: string;
}

export interface ActivationEntryDto {
  extension_id?: string;
  activation_event?: string;
  duration_ms?: number | null;
  timestamp?: string;
  success?: boolean;
  source?: string;
}

export interface NetworkEventDto {
  timestamp?: string;
  rel_time_s?: number | null;
  protocol?: string;
  event_type?: string;
  source_ip?: string;
  destination_ip?: string;
  destination_port?: number | null;
  host?: string;
  path?: string;
  summary?: string;
}

export interface FileEventDto {
  timestamp?: string;
  rel_time_s?: number | null;
  operation?: string;
  path?: string;
  secondary_path?: string;
  source?: string;
  observer?: string;
  scenario_name?: string;
  related_extension_id?: string;
  related_activation_event?: string;
  flags?: string;
  sensitive?: boolean;
  summary?: string;
}

export interface ScenarioTraceDto {
  name?: string;
  started_at?: number;
  ended_at?: number;
  status?: string;
}

export interface ActivationReportDto {
  report_version?: number;
  _metadata?: {
    filename?: string;
  };
  summary?: Record<string, unknown>;
  network_summary?: Record<string, unknown>;
  file_summary?: Record<string, unknown>;
  activated?: ActivationEntryDto[];
  running_extensions?: Array<Record<string, unknown>>;
  network_events?: NetworkEventDto[];
  file_events?: FileEventDto[];
  scenario_traces?: ScenarioTraceDto[];
  evidence_events?: EvidenceEventDto[];
  evidence_links?: EvidenceLinkDto[];
  extension_host_output?: string;
  extension_host_output_lines?: number;
  log_file?: string;
}

export interface MarketplaceExtensionDto {
  publisher: string;
  name: string;
  version: string;
  displayName: string;
  description: string;
  installs: number;
  rating: number;
}

export interface MarketplaceDownloadResponseDto {
  status: string;
  publisher: string;
  name: string;
  version: string;
  extension_dir: string;
  db_id?: number | null;
  message: string;
}

export interface AnalyzeJobStepDto {
  name: string;
  status: string;
  message: string;
}

export interface AnalyzeJobStatusDto {
  job_id: string;
  status: string;
  publisher: string;
  name: string;
  version: string;
  scenario?: string | null;
  current_step?: string | null;
  message: string;
  steps: AnalyzeJobStepDto[];
  report_path?: string | null;
  install_output?: string | null;
  automation_output?: string | null;
  error_detail?: string | null;
  created_at: number;
  started_at?: number | null;
  finished_at?: number | null;
  updated_at: number;
}
