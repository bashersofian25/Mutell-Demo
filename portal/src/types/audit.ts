export interface AuditEntry {
  id: string;
  tenant_id: string | null;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  detail: Record<string, unknown>;
  ip_address: string | null;
  status_code: number | null;
  created_at: string;
}

export interface AuditLogParams {
  page?: number;
  per_page?: number;
  action?: string;
  date_from?: string;
  date_to?: string;
}

export interface AuditLogResponse {
  items: AuditEntry[];
  total: number;
  page: number;
  per_page: number;
}
