import { ReportStatus } from "./index";

export interface Report {
  id: string;
  tenant_id: string;
  generated_by: string;
  title: string;
  period_start: string;
  period_end: string;
  terminal_ids: string[] | null;
  file_url: string | null;
  file_size_bytes: number | null;
  status: ReportStatus;
  created_at: string;
}

export interface ReportCreateRequest {
  title: string;
  period_start: string;
  period_end: string;
  terminal_ids?: string[];
  include_transcripts?: boolean;
  include_notes?: boolean;
  accent_color?: string;
}

export interface ReportDownloadResponse {
  download_url: string;
  expires_in: number;
}
